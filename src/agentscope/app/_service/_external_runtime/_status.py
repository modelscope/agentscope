# -*- coding: utf-8 -*-
"""Discover local executables and inspect provider-owned account state."""

import asyncio
import os
import re

from . import resolve_command
from ._base import finish_cleanup
from ._codex import CodexRuntime


def detect_executable(provider: str, executable: str) -> dict:
    """Resolve the executable independently of the future chat directory."""
    try:
        command, _ = resolve_command(provider, executable.strip(), ".")
        return {"installed": True, "executable": command, "error": None}
    except (ValueError, OSError) as exc:
        return {"installed": False, "executable": None, "error": str(exc)}


async def check_account(provider: str, executable: str) -> dict:
    """Return public identity fields, never credentials or raw CLI output."""
    try:
        command, cwd = resolve_command(provider, executable.strip(), ".")
        if provider == "codex":
            return await _codex_account(command, cwd)
        return await _qoder_account(command, cwd)
    except TimeoutError:
        return {
            "status": "error",
            "account": None,
            "error": "Account detection timed out. Check the CLI and network.",
        }
    except Exception as exc:
        return {"status": "error", "account": None, "error": str(exc)}


async def _codex_account(command: str, cwd: str) -> dict:
    async def ignore(_event: dict) -> None:
        return None

    client = CodexRuntime(
        command=command,
        cwd=cwd,
        session_id=None,
        on_update=ignore,
        on_permission=ignore,
    )
    original: BaseException | None = None
    try:
        async with asyncio.timeout(15):
            result = await client.read_account()
        account = result.get("account")
        if account:
            return {
                "status": "authenticated",
                "account": {
                    key: account[key]
                    for key in ("type", "email", "planType")
                    if isinstance(account.get(key), str)
                },
                "error": None,
            }
        if result.get("requiresOpenaiAuth") is False:
            return {
                "status": "configured",
                "account": {"type": "customProvider"},
                "error": None,
            }
        return {"status": "not_authenticated", "account": None, "error": None}
    except BaseException as exc:
        original = exc
        raise
    finally:
        await finish_cleanup(
            asyncio.create_task(client.aclose()),
            original,
        )


async def _qoder_account(command: str, cwd: str) -> dict:
    if os.environ.get("QODER_PERSONAL_ACCESS_TOKEN"):
        # Presence is not proof of validity; do not claim authenticated.
        return {
            "status": "configured",
            "account": {"type": "accessToken"},
            "error": None,
        }
    process = await asyncio.create_subprocess_exec(
        command,
        "status",
        cwd=cwd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    output = asyncio.create_task(process.communicate())

    async def close() -> None:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        await asyncio.gather(output, return_exceptions=True)
        await process.wait()

    original: BaseException | None = None
    try:
        async with asyncio.timeout(10):
            stdout, _ = await asyncio.shield(output)
        if process.returncode != 0:
            raise RuntimeError(
                f"Qoder account detection failed (exit {process.returncode})",
            )
        # CLI versions can decorate the same status labels with ANSI colors.
        text = re.sub(r"\x1b\[[0-9;]*m", "", stdout.decode(errors="replace"))
        fields = {}
        for line in text.splitlines():
            label, separator, value = line.partition(":")
            if separator and label.strip().lower() in {
                "account",
                "username",
                "email",
            }:
                fields[label.strip().lower()] = value.strip()
        if not fields:
            raise RuntimeError("Qoder returned no recognizable account status")
        empty = {"", "not logged in", "not authenticated", "none", "n/a", "-"}
        fields = {
            key: value
            for key, value in fields.items()
            if value.lower() not in empty
        }
        if not fields:
            return {
                "status": "not_authenticated",
                "account": None,
                "error": None,
            }
        account = {"type": "qodercli"}
        for key in ("email", "username"):
            if fields.get(key):
                account[key] = fields[key]
        if "email" not in account and "@" in fields.get("account", ""):
            account["email"] = fields["account"]
        return {"status": "authenticated", "account": account, "error": None}
    except BaseException as exc:
        original = exc
        raise
    finally:
        await finish_cleanup(asyncio.create_task(close()), original)
