# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Regression tests for checkout wheel installation in live sandboxes."""

import posixpath
import shutil
import subprocess
import tempfile
import unittest
from functools import cache
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from zipfile import ZipFile

import sandbox_test_support as support
from sandbox_test_support._verify_wheel import verify_wheel

from agentscope.workspace import (
    AppleContainerWorkspace,
    BubblewrapWorkspace,
    DaytonaWorkspace,
    DockerWorkspace,
    E2BWorkspace,
    OpenSandboxWorkspace,
)
from agentscope.workspace._docker._make_dockerfile import prepare_build_context


class TestCheckoutWheelBuild(unittest.TestCase):
    """Build caching, failure handling, and skip behavior."""

    def setUp(self) -> None:
        """Use an isolated cache without invalidating real live-test wheels."""
        self.enterContext(
            patch.object(support.shutil, "which", return_value="/tools/uv"),
        )
        self.enterContext(
            patch.object(
                support,
                "checkout_wheel",
                cache(support.checkout_wheel.__wrapped__),
            ),
        )

    def test_build_once_from_worktree(self) -> None:
        """Stage actual checkout files and reuse the same wheel path."""
        cleanups = []

        def build(args: list[str], **_kwargs: object) -> None:
            """Produce one fake wheel after checking the staged source."""
            source = Path(args[-1])
            repo = Path(support.__file__).resolve().parents[2]
            self.assertEqual(
                (source / "src/agentscope/_version.py").read_bytes(),
                (repo / "src/agentscope/_version.py").read_bytes(),
            )
            self.assertEqual(args[0], "/tools/uv")
            self.assertEqual(
                {
                    name: (source / name).read_bytes()
                    for name in ("pyproject.toml", "README.md", "LICENSE")
                },
                {
                    name: (repo / name).read_bytes()
                    for name in ("pyproject.toml", "README.md", "LICENSE")
                },
            )
            output = Path(args[args.index("--out-dir") + 1])
            output.mkdir()
            with ZipFile(
                output / "agentscope-1.0-py3-none-any.whl",
                "w",
            ) as archive:
                archive.write(
                    source / "LICENSE",
                    "agentscope-1.0.dist-info/licenses/LICENSE",
                )

        support.checkout_wheel.cache_clear()
        with (
            patch.object(support.subprocess, "run", side_effect=build) as run,
            patch.object(
                support.atexit,
                "register",
                side_effect=cleanups.append,
            ),
        ):
            try:
                first = support.checkout_wheel()
                self.assertEqual(support.checkout_wheel(), first)
                self.assertEqual(run.call_count, 1)
                with ZipFile(first) as archive:
                    self.assertEqual(
                        archive.namelist(),
                        ["agentscope-1.0.dist-info/licenses/LICENSE"],
                    )
            finally:
                for cleanup in cleanups:
                    cleanup()
        self.assertFalse(first.exists())

    def test_missing_uv_skips_live_class_before_build(self) -> None:
        """A reachable Docker daemon alone is insufficient to build wheels."""

        class LiveDocker(support.CheckoutWheelTestCase):
            """An enabled Docker class with no host build tool."""

            workspace_type = DockerWorkspace

            async def test_live(self) -> None:
                """Never start a workspace without the build prerequisite."""
                self.fail("Missing uv should skip this class")

        with (
            patch.object(support.shutil, "which", return_value=None),
            patch.object(support.subprocess, "run") as run,
            patch.object(support.tempfile, "TemporaryDirectory") as directory,
        ):
            result = unittest.TestResult()
            unittest.defaultTestLoader.loadTestsFromTestCase(LiveDocker).run(
                result,
            )
        self.assertEqual(
            {
                "run": result.testsRun,
                "errors": result.errors,
                "failures": result.failures,
                "skip_reasons": [reason for _, reason in result.skipped],
            },
            {
                "run": 0,
                "errors": [],
                "failures": [],
                "skip_reasons": [
                    "Checkout wheel tests require uv on the host PATH",
                ],
            },
        )
        directory.assert_not_called()
        run.assert_not_called()

    def test_missing_or_changed_wheel_license_fails_build(self) -> None:
        """Reject incomplete artifacts even if the build command succeeded."""
        for content in (None, b"truncated license"):
            with self.subTest(content=content):

                def build(
                    args: list[str],
                    license_content: bytes | None = content,
                    **_kwargs: object,
                ) -> None:
                    """Produce an invalid wheel to exercise artifact checks."""
                    output = Path(args[args.index("--out-dir") + 1])
                    output.mkdir()
                    with ZipFile(
                        output / "agentscope-1.0-py3-none-any.whl",
                        "w",
                    ) as archive:
                        if license_content is not None:
                            archive.writestr(
                                "agentscope-1.0.dist-info/licenses/LICENSE",
                                license_content,
                            )

                with (
                    patch.object(support.subprocess, "run", side_effect=build),
                    patch.object(support.atexit, "register") as register,
                    self.assertRaisesRegex(RuntimeError, "complete LICENSE"),
                ):
                    support.checkout_wheel()
                register.assert_not_called()

    def test_build_failure_is_not_cached(self) -> None:
        """Build errors include diagnostics and can be retried."""
        support.checkout_wheel.cache_clear()
        error = subprocess.CalledProcessError(
            1,
            "uv",
            output="build output",
            stderr="build error",
        )
        with patch.object(
            support.subprocess,
            "run",
            side_effect=error,
        ) as run:
            for _ in range(2):
                with self.assertRaisesRegex(RuntimeError, "build error"):
                    support.checkout_wheel()
            self.assertEqual(run.call_count, 2)

    def test_skipped_class_does_not_build(self) -> None:
        """Unavailable live environments never pay the build cost."""

        @unittest.skip("No sandbox")
        class Skipped(support.CheckoutWheelTestCase):
            """A disabled live test."""

            async def test_live(self) -> None:
                """Never run."""

        with patch.object(support, "checkout_wheel") as build:
            result = unittest.TestResult()
            unittest.defaultTestLoader.loadTestsFromTestCase(Skipped).run(
                result,
            )
        self.assertEqual((result.testsRun, len(result.skipped)), (1, 1))
        build.assert_not_called()

    def test_docker_payload_changes_image_tag(self) -> None:
        """Same wheel filename with different bytes invalidates the image."""
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "agentscope-1.0-py3-none-any.whl"
            tags = []
            for data in (b"first", b"second", b"second"):
                wheel.write_bytes(data)
                context, tag, payloads = support.wheel_build_context(
                    prepare_build_context,
                    wheel,
                )
                self.addCleanup(support.shutil.rmtree, context)
                tags.append(tag)
                dockerfile = (context / "Dockerfile").read_text()
                self.assertEqual(payloads[wheel.name], data)
                self.assertEqual((context / wheel.name).read_bytes(), data)
                self.assertIn(
                    f"--no-deps --reinstall /tmp/{wheel.name}",
                    dockerfile,
                )
                self.assertNotIn('--no-deps "agentscope"', dockerfile)
                self.assertIn("python -I /tmp/_verify_wheel.py", dockerfile)
            self.assertNotEqual(tags[0], tags[1])
            self.assertEqual(tags[1], tags[2])

    def test_installed_bytes_must_match(self) -> None:
        """A same-version package with stale files fails verification."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "agentscope.whl"
            source = root / "agentscope/_version.py"
            source.parent.mkdir()
            source.write_bytes(b"checkout")
            with ZipFile(wheel, "w") as archive:
                archive.writestr("agentscope/_version.py", b"checkout")
            installed = Mock(locate_file=lambda name: root / name)
            with patch(
                "sandbox_test_support._verify_wheel.distribution",
                return_value=installed,
            ):
                verify_wheel(str(wheel))
                source.write_bytes(b"published")
                with self.assertRaisesRegex(RuntimeError, "_version.py"):
                    verify_wheel(str(wheel))

    def test_class_patches_are_restored(self) -> None:
        """Live-class adapters do not alter later production unit tests."""
        for workspace_type in (DockerWorkspace, E2BWorkspace):
            with self.subTest(workspace_type=workspace_type):
                original = workspace_type._setup_mcp_gateway
                prepare = support.docker_module.prepare_build_context

                class Live(support.CheckoutWheelTestCase):
                    """A live class whose patch scope is exercised directly."""

                Live.workspace_type = workspace_type
                with patch.object(
                    support,
                    "checkout_wheel",
                    return_value=Path("test.whl"),
                ):
                    try:
                        Live.setUpClass()
                        if workspace_type is DockerWorkspace:
                            self.assertIsNot(
                                support.docker_module.prepare_build_context,
                                prepare,
                            )
                        else:
                            self.assertIsNot(
                                workspace_type._setup_mcp_gateway,
                                original,
                            )
                    finally:
                        Live.doClassCleanups()
                self.assertIs(workspace_type._setup_mcp_gateway, original)
                self.assertIs(
                    support.docker_module.prepare_build_context,
                    prepare,
                )


class TestCheckoutGateway(unittest.IsolatedAsyncioTestCase):
    """Fresh and resumed gateways install before starting."""

    async def asyncSetUp(self) -> None:
        """Create a fake backend and a wheel artifact."""
        self.enterContext(
            patch.object(
                support,
                "uuid4",
                return_value=SimpleNamespace(hex="test"),
            ),
        )
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.wheel = Path(temporary.name) / "agentscope-1.0-py3-none-any.whl"
        self.wheel.write_bytes(b"checkout")
        self.events = []
        self.success = SimpleNamespace(
            ok=lambda: True,
            exit_code=0,
            stdout=b"",
            stderr=b"",
        )

        async def execute(args: list[str], **_kwargs: object) -> object:
            """Record execution order."""
            self.events.append(args)
            return self.success

        self.backend = SimpleNamespace(
            join_path=posixpath.join,
            exec_shell=AsyncMock(side_effect=execute),
            write_file=AsyncMock(),
            file_exists=AsyncMock(return_value=False),
        )
        self.workspace = E2BWorkspace()
        self.workspace._backend = self.backend

    async def test_fresh_and_resumed_install_before_launch(self) -> None:
        """Retain dependency commands only when bootstrap is needed."""
        original = self.workspace._bootstrap_commands()
        for ready in (False, True):
            with self.subTest(ready=ready):
                self.events.clear()
                self.backend.file_exists.return_value = ready

                async def launch(workspace: object) -> None:
                    """Assert bootstrap will not execute twice."""
                    self.assertEqual(workspace._bootstrap_commands(), [])
                    self.events.append("launch")

                await support.setup_checkout_gateway(
                    self.workspace,
                    self.wheel,
                    launch,
                )
                commands = [
                    entry[2]
                    for entry in self.events
                    if isinstance(entry, list) and entry[0] == "sh"
                ]
                self.assertEqual(
                    commands[:-1],
                    [] if ready else original[:-1],
                )
                self.assertEqual(
                    support.shlex.split(commands[-1].split(" && ")[0]),
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        self.workspace._gateway_python,
                        "--no-deps",
                        "--reinstall",
                        f"{self.workspace.workdir}/.checkout-wheel-test/"
                        f"{self.wheel.name}",
                    ],
                )
                self.assertIn(" -I ", commands[-1])
                self.assertEqual(self.events[-1], "launch")
                self.assertEqual(
                    self.workspace._bootstrap_commands(),
                    original,
                )

    async def test_install_failure_prevents_gateway_launch(self) -> None:
        """Never continue with a published or partially installed package."""
        self.backend.file_exists.return_value = True
        failure = SimpleNamespace(
            ok=lambda: False,
            exit_code=1,
            stdout=b"",
            stderr=b"install failed",
        )
        self.backend.exec_shell.side_effect = [self.success, failure, failure]
        launch = AsyncMock()
        with self.assertRaisesRegex(RuntimeError, "install failed"):
            await support.setup_checkout_gateway(
                self.workspace,
                self.wheel,
                launch,
            )
        launch.assert_not_awaited()
        self.backend.exec_shell.assert_awaited_with(
            [
                "rm",
                "-rf",
                f"{self.workspace.workdir}/.checkout-wheel-test",
            ],
        )

    async def test_upload_failure_prevents_gateway_launch(self) -> None:
        """Cleanup after a partial upload preserves the original failure."""
        self.backend.write_file.side_effect = [None, OSError("upload failed")]
        self.backend.exec_shell.side_effect = [
            self.success,
            OSError("cleanup failed"),
        ]
        launch = AsyncMock()
        with self.assertRaisesRegex(OSError, "upload failed"):
            await support.setup_checkout_gateway(
                self.workspace,
                self.wheel,
                launch,
            )
        launch.assert_not_awaited()
        self.backend.exec_shell.assert_awaited_with(
            [
                "rm",
                "-rf",
                f"{self.workspace.workdir}/.checkout-wheel-test",
            ],
        )

    async def test_upload_directory_creation_failure_stops_without_cleanup(
        self,
    ) -> None:
        """Never reuse or delete a directory that could not be created."""
        self.backend.exec_shell.side_effect = None
        self.backend.exec_shell.return_value = SimpleNamespace(
            ok=lambda: False,
        )
        launch = AsyncMock()
        with self.assertRaisesRegex(
            RuntimeError,
            "create checkout upload dir",
        ):
            await support.setup_checkout_gateway(
                self.workspace,
                self.wheel,
                launch,
            )
        self.backend.write_file.assert_not_awaited()
        self.backend.exec_shell.assert_awaited_once_with(
            ["mkdir", f"{self.workspace.workdir}/.checkout-wheel-test"],
        )
        launch.assert_not_awaited()

    async def test_same_named_user_files_survive_success_and_failure(
        self,
    ) -> None:
        """Only files in the exclusively created directory may be removed."""
        root = self.wheel.parent / "workspace"
        root.mkdir()
        expected = {
            self.wheel.name: b"user wheel",
            "_verify_wheel.py": b"user script",
        }
        for name, data in expected.items():
            (root / name).write_bytes(data)
        self.workspace.workdir = str(root)
        self.backend.file_exists.return_value = True
        self.backend.write_file.side_effect = lambda path, data: Path(
            path,
        ).write_bytes(data)

        async def execute(args: list[str], **_kwargs: object) -> object:
            """Use real file operations but keep package installation fake."""
            if args[0] == "mkdir":
                Path(args[1]).mkdir()
            elif args[0] == "rm":
                shutil.rmtree(args[-1])
            else:
                return self.backend.exec_shell.return_value
            return self.success

        self.backend.exec_shell.side_effect = execute
        failure = SimpleNamespace(
            ok=lambda: False,
            exit_code=1,
            stdout=b"",
            stderr=b"install failed",
        )
        for result in (self.success, failure):
            with self.subTest(install_ok=result.ok()):
                self.backend.exec_shell.return_value = result
                launch = AsyncMock()
                if result.ok():
                    await support.setup_checkout_gateway(
                        self.workspace,
                        self.wheel,
                        launch,
                    )
                    launch.assert_awaited_once()
                else:
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "install failed",
                    ):
                        await support.setup_checkout_gateway(
                            self.workspace,
                            self.wheel,
                            launch,
                        )
                    launch.assert_not_awaited()
                self.assertEqual(
                    {path.name: path.read_bytes() for path in root.iterdir()},
                    expected,
                )

    async def test_bubblewrap_uses_readiness_probe(self) -> None:
        """Persisted Bubblewrap environments still reinstall the wheel."""
        workspace = BubblewrapWorkspace()
        workspace._backend = self.backend
        with patch.object(
            workspace,
            "_bootstrap_is_ready",
            AsyncMock(return_value=True),
        ) as ready:
            await support.setup_checkout_gateway(
                workspace,
                self.wheel,
                AsyncMock(),
            )
        ready.assert_awaited_once()
        self.backend.file_exists.assert_not_awaited()
        self.assertEqual(len(self.events), 3)
        self.assertIn("--reinstall", self.events[1][2])

    async def test_provider_commands_preserve_paths_and_dependencies(
        self,
    ) -> None:
        """All remote providers keep their uv path and dependency commands."""
        for workspace in (
            OpenSandboxWorkspace(),
            AppleContainerWorkspace(),
            DaytonaWorkspace(),
        ):
            with self.subTest(provider=type(workspace).__name__):
                workspace._backend = self.backend
                if isinstance(workspace, DaytonaWorkspace):
                    workspace._user_home = "/home/test user"
                    workspace._gateway_home = "/home/test user/.agentscope"
                    workspace._uv_bin = "/home/test user/.local/bin/uv"
                    workspace.workdir = "/home/test user/workspace"
                original = workspace._bootstrap_commands()
                self.events.clear()
                await support.setup_checkout_gateway(
                    workspace,
                    self.wheel,
                    AsyncMock(),
                )
                commands = [
                    entry[2] for entry in self.events if entry[0] == "sh"
                ]
                self.assertEqual(commands[:-1], original[:-1])
                self.assertEqual(
                    support.shlex.split(commands[-1].split(" && ")[0]),
                    [
                        *support.shlex.split(original[-1])[:-1],
                        "--reinstall",
                        f"{workspace.workdir}/.checkout-wheel-test/"
                        f"{self.wheel.name}",
                    ],
                )
