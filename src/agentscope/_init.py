# -*- coding: utf-8 -*-
"""The init function for the package."""
import json
import os
import shutil
from typing import Optional, Union, Sequence
from agentscope import agents
from .agents import AgentBase
from ._runtime import _runtime
from .file_manager import file_manager
from .utils.logging_utils import LOG_LEVEL, setup_logger
from .utils.monitor import MonitorFactory
from .models import read_model_configs
from .constants import _DEFAULT_DIR
from .constants import _DEFAULT_LOG_LEVEL

# init setting
_INIT_SETTINGS = {}


def init(
    model_configs: Optional[Union[dict, str, list]] = None,
    project: Optional[str] = None,
    name: Optional[str] = None,
    save_dir: str = _DEFAULT_DIR,
    save_log: bool = True,
    save_code: bool = True,
    save_api_invoke: bool = True,
    logger_level: LOG_LEVEL = _DEFAULT_LOG_LEVEL,
    agent_configs: Optional[Union[str, list, dict]] = None,
) -> Sequence[AgentBase]:
    """A unified entry to initialize the package, including model configs,
    runtime names, saving directories and logging settings.

    Args:
        model_configs (`Optional[Union[dict, str, list]]`, defaults to `None`):
            A dict, a list of dicts, or a path to a json file containing
            model configs.
        project (`Optional[str]`, defaults to `None`):
            The project name, which is used to identify the project.
        name (`Optional[str]`, defaults to `None`):
            The name for runtime, which is used to identify this runtime.
        save_dir (`str`, defaults to `./runs`):
            The directory to save logs, files, codes, and api invocations.
            If `dir` is `None`, when saving logs, files, codes, and api
            invocations, the default directory `./runs` will be created.
        save_log (`bool`, defaults to `False`):
            Whether to save logs locally.
        save_code (`bool`, defaults to `False`):
            Whether to save codes locally.
        save_api_invoke (`bool`, defaults to `False`):
            Whether to save api invocations locally, including model and web
            search invocation.
        logger_level (`LOG_LEVEL`, defaults to `"INFO"`):
            The logging level of logger.
        agent_configs (`Optional[Union[str, list, dict]]`, defaults to `None`):
            The config dict(s) of agents or the path to the config file,
            which can be loaded by json.loads(). One agent config should
            cover the required arguments to initialize a specific agent
            object, otherwise the default values will be used.
    """
    init_process(
        model_configs=model_configs,
        project=project,
        name=name,
        save_dir=save_dir,
        save_api_invoke=save_api_invoke,
        save_log=save_log,
        logger_level=logger_level,
    )

    # save init settings for subprocess
    _INIT_SETTINGS["model_configs"] = model_configs
    _INIT_SETTINGS["project"] = project
    _INIT_SETTINGS["name"] = name
    _INIT_SETTINGS["runtime_id"] = _runtime.runtime_id
    _INIT_SETTINGS["save_dir"] = save_dir
    _INIT_SETTINGS["save_api_invoke"] = save_api_invoke
    _INIT_SETTINGS["save_log"] = save_log
    _INIT_SETTINGS["logger_level"] = logger_level

    # Save code if needed
    if save_code:
        # Copy python file in os.path.curdir into runtime directory
        cur_dir = os.path.abspath(os.path.curdir)
        for filename in os.listdir(cur_dir):
            if filename.endswith(".py"):
                file_abs = os.path.join(cur_dir, filename)
                shutil.copy(file_abs, str(file_manager.dir_code))

    # Load config and init agent by configs
    if agent_configs is not None:
        if isinstance(agent_configs, str):
            with open(agent_configs, "r", encoding="utf-8") as file:
                configs = json.load(file)
        elif isinstance(agent_configs, dict):
            configs = [agent_configs]
        else:
            configs = agent_configs

        # setup agents
        agent_objs = []
        for config in configs:
            agent_cls = getattr(agents, config["class"])
            agent_args = config["args"]
            agent = agent_cls(**agent_args)
            agent_objs.append(agent)
        return agent_objs
    return []


def init_process(
    model_configs: Optional[Union[dict, str, list]] = None,
    project: Optional[str] = None,
    name: Optional[str] = None,
    runtime_id: Optional[str] = None,
    save_dir: str = _DEFAULT_DIR,
    save_api_invoke: bool = False,
    save_log: bool = False,
    logger_level: LOG_LEVEL = _DEFAULT_LOG_LEVEL,
) -> None:
    """An entry to initialize the package in a process.

    Args:
        project (`Optional[str]`, defaults to `None`):
            The project name, which is used to identify the project.
        name (`Optional[str]`, defaults to `None`):
            The name for runtime, which is used to identify this runtime.
        runtime_id (`Optional[str]`, defaults to `None`):
            The id for runtime, which is used to identify this runtime.
        save_dir (`str`, defaults to `./runs`):
            The directory to save logs, files, codes, and api invocations.
            If `dir` is `None`, when saving logs, files, codes, and api
            invocations, the default directory `./runs` will be created.
        save_api_invoke (`bool`, defaults to `False`):
            Whether to save api invocations locally, including model and web
            search invocation.
        model_configs (`Optional[Sequence]`, defaults to `None`):
            A sequence of pre-init model configs.
        save_log (`bool`, defaults to `False`):
            Whether to save logs locally.
        logger_level (`LOG_LEVEL`, defaults to `"INFO"`):
            The logging level of logger.
    """
    # Init logger
    dir_log = str(file_manager.dir_log) if save_log else None
    setup_logger(dir_log, logger_level)

    # Load model configs if needed
    if model_configs is not None:
        read_model_configs(model_configs)

    # Init the runtime
    if project is not None:
        _runtime.project = project
    if name is not None:
        _runtime.name = name
    if runtime_id is not None:
        _runtime.runtime_id = runtime_id

    # Init file manager and save configs by default
    file_manager.init(save_dir, save_api_invoke)

    # Init monitor
    _ = MonitorFactory.get_monitor(db_path=file_manager.path_db)
