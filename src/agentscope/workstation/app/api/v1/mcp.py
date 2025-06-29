# -*- coding: utf-8 -*-
"""mcp base related APIs"""
from typing import Union

from fastapi import APIRouter
from app.models.mcp import (
    UpdateMCPForm,
    CreateMCPForm,
    DeBugToolsForm,
    QueryByCodesForm,
)

from app.api.deps import SessionDep, CurrentAccount
from app.schemas.response import mcp_response

from app.services.mcp_service import MCPService

router = APIRouter(tags=["mcp-server"])


@router.post("/mcp-servers")
def create_mcp(
    current_user: CurrentAccount,
    session: SessionDep,
    request: CreateMCPForm,
) -> dict:
    """Create mcp"""
    mcp_service = MCPService(
        account_id=current_user.account_id,
        session=session,
    )
    mcp = mcp_service.create(request.dict())
    return mcp_response(
        request_id=current_user.account_id,
        data=mcp.server_code,
    )


@router.put("/mcp-servers")
async def update_mcp(
    current_user: CurrentAccount,
    session: SessionDep,
    form: UpdateMCPForm,
) -> dict:
    """Update mcp"""
    mcp = MCPService(
        account_id=current_user.account_id,
        session=session,
    )
    mcp_dict = await mcp.get_mcp_server_code(server_code=form.server_code)
    if mcp_dict is None:
        return mcp_response(
            request_id=current_user.account_id,
            success=False,
            message="MCP not found.",
            data=None,
        )
    mcp_id = mcp_dict["id"]
    mcp.update_mcp_info(
        mcp_id=mcp_id,
        **form.dict(),
    )
    return mcp_response(
        request_id=current_user.account_id,
    )


@router.delete("/mcp-servers/{server_code}")
async def delete_mcp(
    current_user: CurrentAccount,
    session: SessionDep,
    server_code: str,
) -> dict:
    """Delete mcp"""
    mcp_service = MCPService(
        account_id=current_user.account_id,
        session=session,
    )
    mcp_dict = await mcp_service.get_mcp_server_code(server_code=server_code)
    if mcp_dict is None:
        return mcp_response(
            request_id=current_user.account_id,
            success=False,
            message="MCP not found.",
            data=None,
        )
    mcp_id = mcp_dict["id"]
    mcp_service.delete_mcp(mcp_id=mcp_id)
    return mcp_response(
        request_id=current_user.account_id,
    )


@router.get("/mcp-servers/{server_code}")
async def get_mcp_server(
    current_user: CurrentAccount,
    session: SessionDep,
    server_code: str,
    need_tools: bool = False,
) -> dict:
    """Get mcp server"""
    mcp_service = MCPService(
        account_id=current_user.account_id,
        session=session,
    )
    mcp_dict = await mcp_service.get_mcp_server_code(
        server_code=server_code,
        need_tools=need_tools,
    )
    if mcp_dict is None:
        return mcp_response(
            request_id=current_user.account_id,
            success=False,
            message="MCP not found.",
            data=None,
        )
    return mcp_response(
        data=mcp_dict,
    )


@router.get("/mcp-servers")
async def list_mcp_servers(
    current_user: CurrentAccount,
    session: SessionDep,
    current: int,
    size: int,
    total: Union[None, int] = None,
    status: Union[None, int] = None,
    name: Union[None, str] = None,
    need_tools: bool = False,
) -> dict:
    """Obtain the paginated list of MCP services."""
    mcp_service = MCPService(
        account_id=current_user.account_id,
        session=session,
    )
    total, mcp_servers = await mcp_service.list_mcp_servers(
        current=current,
        size=size,
        total=total,
        status=status,
        name=name,
        need_tools=need_tools,
    )

    return mcp_response(
        request_id=current_user.account_id,
        data={
            "current": current,
            "size": size,
            "total": total,
            "records": mcp_servers,
        },
    )


@router.post("/mcp-servers/query-by-codes")
async def query_by_codes(
    current_user: CurrentAccount,
    session: SessionDep,
    form: QueryByCodesForm,
) -> dict:
    """list mcp server by codes"""
    mcp_service = MCPService(
        account_id=current_user.account_id,
        session=session,
    )
    mcp_list = await mcp_service.list_mcp_servers_by_codes(
        server_codes=form.server_codes,
        need_tools=form.need_tools,
    )
    return mcp_response(
        request_id=current_user.account_id,
        data=mcp_list,
    )


@router.post("/mcp-servers/debug-tools")
async def debug_tools(
    current_user: CurrentAccount,
    session: SessionDep,
    request: DeBugToolsForm,
) -> dict:
    """Run a specific mcp tool"""
    mcp_service = MCPService(
        account_id=current_user.account_id,
        session=session,
    )
    try:
        res = await mcp_service.debug_tools(
            server_code=request.server_code,
            tool_name=request.tool_name,
            tool_params=request.tool_params,
        )

        return mcp_response(
            request_id=current_user.account_id,
            message="Operation succeeded",
            data={
                "tool_output": res,
                "status": "SUCCESS",
            },
        )
    except ValueError as ve:
        return mcp_response(
            request_id=current_user.account_id,
            success=False,
            code="InvalidParameter",
            message=str(ve),
        )
    except Exception as e:
        return mcp_response(
            request_id=current_user.account_id,
            success=False,
            code="InternalError",
            message=str(e),
        )
