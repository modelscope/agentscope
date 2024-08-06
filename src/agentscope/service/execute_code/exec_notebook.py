# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""Service for executing jupyter notebooks interactively
Partially referenced the implementation of https://github.com/geekan/MetaGPT/blob/main/metagpt/actions/di/execute_nb_code.py
"""  # noqa
import base64
import asyncio
from loguru import logger


try:
    from nbclient import NotebookClient
    from nbclient.exceptions import CellTimeoutError, DeadKernelError
    import nbformat
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    nbclient = ImportErrorReporter(import_error)
    nbformat = ImportErrorReporter(import_error)
    NotebookClient = ImportErrorReporter(import_error)

from ...manager import FileManager
from ..service_status import ServiceExecStatus
from ..service_response import ServiceResponse


class NoteBookExecutor:
    """
    Class for executing jupyter notebooks block interactively.
    To use the service function, you should first init the class, then call the
    run_code_on_notebook function.

    Example:

        ```ipython
        from agentscope.service.service_toolkit import *
        from agentscope.service.execute_code.exec_notebook import *
        nbe = NoteBookExecutor()
        code = "print('helloworld')"
        # calling directly
        nbe.run_code_on_notebook(code)

        >>> Executing function run_code_on_notebook with arguments:
        >>>     code: print('helloworld')
        >>> END

        # calling with service toolkit
        service_toolkit = ServiceToolkit()
        service_toolkit.add(nbe.run_code_on_notebook)
        input_obs = [{"name": "run_code_on_notebook", "arguments":{"code": code}}]
        res_of_string_input = service_toolkit.parse_and_call_func(input_obs)

        "1. Execute function run_code_on_notebook\n   [ARGUMENTS]:\n       code: print('helloworld')\n   [STATUS]: SUCCESS\n   [RESULT]: ['helloworld\\n']\n"

        ```
    """  # noqa

    def __init__(
        self,
        timeout: int = 300,
    ) -> None:
        """
        The construct function of the NoteBookExecutor.
        Args:
            timeout (Optional`int`):
                The timeout for each cell execution.
                Default to 300.
        """
        self.nb = nbformat.v4.new_notebook()
        self.nb_client = NotebookClient(nb=self.nb)
        self.timeout = timeout

        asyncio.run(self._start_client())

    def _output_parser(self, output: dict) -> str:
        """Parse the output of the notebook cell and return str"""
        if output["output_type"] == "stream":
            return output["text"]
        elif output["output_type"] == "execute_result":
            return output["data"]["text/plain"]
        elif output["output_type"] == "display_data":
            if "image/png" in output["data"]:
                file_path = self._save_image(output["data"]["image/png"])
                return f"Displayed image saved to {file_path}"
            else:
                return "Unsupported display type"
        elif output["output_type"] == "error":
            return output["traceback"]
        else:
            logger.info(f"Unsupported output encountered: {output}")
            return "Unsupported output encountered"

    async def _start_client(self) -> None:
        """start notebook client"""
        if self.nb_client.kc is None or not await self.nb_client.kc.is_alive():
            self.nb_client.create_kernel_manager()
            self.nb_client.start_new_kernel()
            self.nb_client.start_new_kernel_client()

    async def _kill_client(self) -> None:
        """kill notebook client"""
        if (
            self.nb_client.km is not None
            and await self.nb_client.km.is_alive()
        ):
            await self.nb_client.km.shutdown_kernel(now=True)
            await self.nb_client.km.cleanup_resources()

        self.nb_client.kc.stop_channels()
        self.nb_client.kc = None
        self.nb_client.km = None

    async def _restart_client(self) -> None:
        """Restart the notebook client"""
        await self._kill_client()
        self.nb_client = NotebookClient(self.nb, timeout=self.timeout)
        await self._start_client()

    async def _run_cell(self, cell_index: int) -> ServiceResponse:
        """Run a cell in the notebook by its index"""
        try:
            self.nb_client.execute_cell(self.nb.cells[cell_index], cell_index)
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=[
                    self._output_parser(output)
                    for output in self.nb.cells[cell_index].outputs
                ],
            )
        except DeadKernelError:
            await self.reset()
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content="DeadKernelError when executing cell, reset kernel",
            )
        except CellTimeoutError:
            assert self.nb_client.km is not None
            await self.nb_client.km.interrupt_kernel()
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=(
                    "CellTimeoutError when executing cell"
                    ", code execution timeout"
                ),
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=str(e),
            )

    @property
    def cells_length(self) -> int:
        """return cell length"""
        return len(self.nb.cells)

    async def async_run_code_on_notebook(self, code: str) -> ServiceResponse:
        """
        Run the code on interactive notebook
        """
        self.nb.cells.append(nbformat.v4.new_code_cell(code))
        cell_index = self.cells_length - 1
        return await self._run_cell(cell_index)

    def run_code_on_notebook(self, code: str) -> ServiceResponse:
        """
        Run the code on interactive jupyter notebook.

        Args:
            code (`str`):
                The Python code to be executed in the interactive notebook.

        Returns:
            `ServiceResponse`: whether the code execution was successful,
            and the output of the code execution.
        """
        return asyncio.run(self.async_run_code_on_notebook(code))

    def reset_notebook(self) -> ServiceResponse:
        """
        Reset the notebook
        """
        asyncio.run(self._restart_client())
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Reset notebook",
        )

    def _save_image(self, image_base64: str) -> str:
        """Save image data to a file.
        The image name is generated randomly here"""
        image_data = base64.b64decode(image_base64)
        file_manager = FileManager.get_instance()
        return file_manager.save_image(image_data)
