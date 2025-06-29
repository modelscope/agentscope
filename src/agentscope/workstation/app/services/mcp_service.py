# -*- coding: utf-8 -*-
"""The MCP related services"""
import json
import uuid
from typing import Literal, Union, Sequence, Dict, Any

from sqlmodel import Session

from app.dao.mcp_dao import MCPDAO

from app.models.mcp import MCP
from app.services.base_service import BaseService
from app.services.storage_service import StorageService


def validate_mcp_config(config: dict) -> tuple[bool, str]:
    """Validate MCP config."""
    if "mcpServers" not in config:
        return False, "There must be a key of 'mcpServers'."

    if not isinstance(config["mcpServers"], dict):
        return False, "'mcpServers' config wrong."

    if len(config["mcpServers"]) != 1:
        return False, "'mcpServers' must contain only one server."

    return True, ""


def generate_server_code() -> str:
    """Generate server code."""
    return str(uuid.uuid4())


class MCPService(BaseService[MCPDAO]):
    """Service layer for MCP."""

    _dao_cls = MCPDAO

    def __init__(
        self,
        session: Session,
        account_id: str,
    ) -> None:
        super().__init__(session)
        self.dao = self._dao_cls(session=session)
        self.session = session
        self._storage_service = StorageService()
        self.account_id = account_id

    def transform_config(self, config_str: str) -> dict:
        from urllib.parse import urlparse

        try:
            # Parsing JSON data
            config_data = json.loads(config_str)
            flag, message = validate_mcp_config(config_data)
            if not flag:
                raise Exception(message)
            server_key = next(iter(config_data["mcpServers"]))
            url = config_data["mcpServers"][server_key]["url"]
            parsed_url = urlparse(url)
            new_config = {
                "remote_endpoint": parsed_url.path + "?" + parsed_url.query,
                "install_config": json.dumps(config_data),
                "remote_address": f"{parsed_url.scheme}://{parsed_url.netloc}",
            }

            # return results
            return new_config

        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Error processing config: {e}")

    def create(self, obj_in: Dict[str, Any]) -> MCP:
        """Create mcp"""
        server_code = (generate_server_code(),)
        obj_in["server_code"] = server_code
        obj_in["creator_id"] = self.account_id
        deploy_config = self.transform_config(obj_in["deploy_config"])
        obj_in["deploy_config"] = json.dumps(deploy_config)
        mcp = self.dao.create(obj_in)
        return mcp

    def set_mcp_status(
        self,
        mcp_id: int,
        status: bool,
    ) -> None:
        """Set mcp status"""
        self.dao.set_mcp_status(
            account_id=self.account_id,
            mcp_id=mcp_id,
            status=status,
        )

    async def get_mcp_server_code(
        self,
        server_code: str,
        need_tools: bool = False,
    ) -> dict:
        """Get mcp server code"""
        return await self.dao.get_mcp_server_code(
            server_code=server_code,
            need_tools=need_tools,
        )

    def update_mcp_info(
        self,
        mcp_id: int,
        **update_data: Any,
    ) -> None:
        """Update mcp info"""
        if "deploy_config" in update_data:
            deploy_config = self.transform_config(update_data["deploy_config"])
            update_data["deploy_config"] = json.dumps(deploy_config)
        self.dao.update_mcp_info(
            account_id=self.account_id,
            mcp_id=mcp_id,
            **update_data,
        )

    def delete_mcp(
        self,
        mcp_id: int,
    ) -> None:
        """Delete mcp"""
        self.dao.delete_mcp(
            mcp_id=mcp_id,
        )

    async def get_mcp(
        self,
        mcp_id: int,
        need_tools: bool = False,
    ) -> dict:
        """Get mcp"""
        return await self.dao.get_mcp(
            mcp_id=mcp_id,
            need_tools=need_tools,
        )

    async def list_mcp_servers(
        self,
        current: int,
        size: int,
        total: Union[None, int] = None,
        status: Union[None, int] = None,
        name: Union[None, str] = None,
        need_tools: bool = False,
    ) -> tuple[int, Sequence[MCP]]:
        """List mcp servers"""

        num = self.dao.list_mcp_servers_num()
        mcp_list = await self.dao.list_mcp_servers(
            current=current,
            size=size,
            status=status,
            total=total,
            name=name,
            need_tools=need_tools,
        )
        return num, mcp_list

    async def list_mcp_servers_by_codes(
        self,
        server_codes: list[str],
        need_tools: bool = False,
    ) -> Sequence[dict]:
        """List mcp servers by codes"""

        mcp_list = await self.dao.list_mcp_servers_by_codes(
            server_codes=server_codes,
            need_tools=need_tools,
        )
        return mcp_list

    async def debug_tools(
        self,
        server_code: str,
        tool_name: str,
        tool_params: dict,
    ) -> dict:
        """Debug tools"""
        res = await self.dao.debug_tools(
            server_code=server_code,
            tool_name=tool_name,
            tool_params=tool_params,
        )
        return res
