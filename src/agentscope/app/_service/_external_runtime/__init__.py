# -*- coding: utf-8 -*-
"""Discover optional Python-packaged Codex and Qoder runtimes."""

import importlib
import os
import shutil
from pathlib import Path
from typing import Any

from ._base import NativeRuntime


def optional_sdk(provider: str) -> Any:
    """Load only the chosen provider, with an actionable installation hint."""
    name = "codex_cli_bin" if provider == "codex" else "qoder_agent_sdk"
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        raise ValueError(
            f'Install: pip install "agentscope[{provider}]"',
        ) from exc


def resolve_command(
    provider: str,
    executable: str,
    cwd: str,
) -> tuple[str, str]:
    """Prefer explicit paths, then SDK bundles, then standalone CLI tools."""
    if provider not in {"codex", "qoder"}:
        raise ValueError("Choose Codex or Qoder")
    directory = Path(cwd).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"Working directory does not exist: {directory}")
    candidate = None
    if not executable:
        try:
            sdk = optional_sdk(provider)
            if provider == "qoder":
                suffix = ".exe" if os.name == "nt" else ""
                candidate = (
                    Path(sdk.__file__).parent
                    / "_bundled"
                    / f"qodercli{suffix}"
                )
            else:
                candidate = Path(sdk.bundled_codex_path())
        except (ValueError, FileNotFoundError):
            pass
    if executable:
        found = shutil.which(str(Path(executable).expanduser()))
    elif candidate is not None and candidate.is_file():
        found = str(candidate)
    else:
        found = shutil.which("codex" if provider == "codex" else "qodercli")
    if not found:
        raise ValueError(
            f'Runtime not found. Run pip install "agentscope[{provider}]" '
            f"or configure a native executable.",
        )
    path = Path(found).resolve()
    if path.suffix.lower() in {".cmd", ".bat"}:
        raise ValueError("Choose the native executable, not a shell launcher")
    if provider == "codex" and any(
        part in {".vscode", ".vscode-insiders", ".cursor"}
        for part in path.parts
    ):
        raise ValueError(
            'Use pip install "agentscope[codex]" or a standalone Codex CLI, '
            "not an IDE extension's embedded executable",
        )
    return str(path), str(directory)


def create_runtime(provider: str, **kwargs: Any) -> NativeRuntime:
    """Keep provider dependencies out of native AgentScope startup."""
    if provider == "codex":
        module = importlib.import_module(f"{__name__}._codex")
        return module.CodexRuntime(**kwargs)
    if provider == "qoder":
        module = importlib.import_module(f"{__name__}._qoder")
        return module.QoderRuntime(**kwargs)
    raise ValueError("Choose Codex or Qoder")
