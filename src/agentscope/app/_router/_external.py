# -*- coding: utf-8 -*-
"""Runtime checks and live approvals for third-party chat agents."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..deps import (
    get_current_user_id,
    get_workspace_manager,
    get_message_bus,
    get_storage,
    get_resource_access_service,
)
from .._service._access import ResourceAccessService
from ..message_bus import MessageBus
from ..storage import StorageBase
from ..workspace_manager import LocalWorkspaceManager, WorkspaceManagerBase
from ..storage._model._agent import ExternalAgentConfig
from .._service._external_runtime._status import (
    check_account,
    detect_executable,
)
from .._service._external import (
    check_runtime,
    pending_permissions,
    resolve_permission,
)

external_router = APIRouter()


@external_router.get("/external/defaults")
async def external_defaults(
    _user_id: str = Depends(get_current_user_id),
    manager: WorkspaceManagerBase = Depends(get_workspace_manager),
) -> dict:
    """Describe the default local directory before an agent is created."""
    return {
        "workspace_path": manager.get_workdir("<agent_id>")
        if isinstance(manager, LocalWorkspaceManager)
        else None,
    }


class RuntimeCheck(BaseModel):
    """A predefined provider and its local connection settings."""

    backend: Literal["codex", "qoder"]
    external_config: ExternalAgentConfig


class ProviderProbe(BaseModel):
    """Provider inspection does not require a chat working directory."""

    backend: Literal["codex", "qoder"]
    executable: str = ""


@external_router.post("/external/detect")
async def detect_external(
    body: ProviderProbe,
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """Find a native executable without starting an agent session."""
    return detect_executable(body.backend, body.executable)


@external_router.post("/external/account")
async def inspect_external_account(
    body: ProviderProbe,
    request: Request,
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """Inspect the backend account used by the selected provider."""
    result = await check_account(body.backend, body.executable)
    if body.backend == "qoder" and result["status"] == "not_authenticated":
        error = request.app.state.qoder_login.error_for(body.executable)
        if error:
            return {"status": "error", "account": None, "error": error}
    return result


class QoderLoginRequest(BaseModel):
    """The previously detected native executable to use for login."""

    executable: str = ""


@external_router.post("/external/qoder/login")
async def start_qoder_login(
    body: QoderLoginRequest,
    request: Request,
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """Start CLI-owned browser authentication on the backend machine."""
    try:
        return request.app.state.qoder_login.start(body.executable)
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc


class PermissionChoice(BaseModel):
    """A displayed option ID; null declines the permission request."""

    option_id: str | None


@external_router.post("/external/check")
async def check_external(
    body: RuntimeCheck,
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """Test a preinstalled runtime using the backend's existing login."""
    return await check_runtime(body.backend, body.external_config)


async def _require_session(
    storage: StorageBase,
    user_id: str,
    agent_id: str,
    session_id: str,
) -> None:
    session = await storage.get_session(user_id, agent_id, session_id)
    if session is None:
        raise HTTPException(404, "Session not found")


@external_router.get("/{agent_id}/sessions/{session_id}/external/permissions")
async def list_external_permissions(
    agent_id: str,
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    storage: StorageBase = Depends(get_storage),
    bus: MessageBus = Depends(get_message_bus),
    access: ResourceAccessService = Depends(get_resource_access_service),
) -> dict:
    """Read only the authenticated user's live session approvals."""
    await access.resolve_agent(user_id, agent_id)
    await _require_session(storage, user_id, agent_id, session_id)
    return {"requests": await pending_permissions(bus, session_id)}


@external_router.post(
    "/{agent_id}/sessions/{session_id}/external/permissions/{request_id}",
)
async def answer_external_permission(
    agent_id: str,
    session_id: str,
    request_id: str,
    body: PermissionChoice,
    user_id: str = Depends(get_current_user_id),
    storage: StorageBase = Depends(get_storage),
    bus: MessageBus = Depends(get_message_bus),
    access: ResourceAccessService = Depends(get_resource_access_service),
) -> dict:
    """Deliver the selected option to the process owning this turn."""
    await access.resolve_agent(user_id, agent_id)
    await _require_session(storage, user_id, agent_id, session_id)
    await resolve_permission(bus, session_id, request_id, body.option_id)
    return {"accepted": True}
