# -*- coding: utf-8 -*-
"""The data access object layer for MCP."""
import asyncio
import json
from typing import Union, List
from datetime import datetime, timezone
from sqlmodel import Session, select, func, update

from app.utils.mcp_utils import MCPSessionHandler
from app.dao.base_dao import BaseDAO
from app.models.mcp import MCP


class MCPDAO(BaseDAO):
    """Data access object layer for MCP."""

    _model_class = MCP

    def __init__(self, session: Session):
        self.session = session
        self.model = self._model_class

    async def process_mcp(self, mcp: MCP, need_tools: bool) -> dict:
        """Process MCP."""
        mcp_dict = mcp.model_dump()
        config = json.loads(mcp.deploy_config)
        install_config = json.loads(config["install_config"])
        mcp_dict["deploy_config"] = json.dumps(install_config)
        if need_tools:
            mcp_dict["tools"] = await self.get_tools(install_config)
        return mcp_dict

    def set_mcp_status(
        self,
        account_id: str,
        mcp_id: int,
        status: bool,
    ) -> None:
        """Set MCP status."""
        update_values = {"enabled": status, "updater_id": account_id}

        if not status:
            update_values["disable_time"] = datetime.now(timezone.utc)

        self.session.execute(
            update(self._model_class)
            .where(self._model_class.id == mcp_id)
            .values(**update_values),
        )

        self.session.commit()

    def update_mcp_info(
        self,
        account_id: str,  # pylint: disable=unused-argument
        mcp_id: int,
        **update_data: dict,
    ) -> None:
        """Update MCP info."""
        query = select(MCP).where(MCP.id == mcp_id)
        mcp = self.session.exec(query).first()

        for key, value in update_data.items():
            if hasattr(mcp, key) and value != getattr(mcp, key):
                setattr(mcp, key, value)
        self.session.commit()

    def delete_mcp(
        self,
        mcp_id: int,
    ) -> None:
        """Delete MCP."""
        query = select(self._model_class).where(self._model_class.id == mcp_id)
        mcp = self.session.exec(query).first()
        if mcp:
            self.session.delete(mcp)
            self.session.commit()

    async def get_mcp(
        self,
        mcp_id: int,
        need_tools: bool = False,
    ) -> dict:
        """Get MCP."""
        query = select(self.model).where(self.model.id == mcp_id)
        mcp = self.session.exec(query).first()
        tasks = [self.process_mcp(mcp, need_tools)]
        results = await asyncio.gather(*tasks)
        return results[0]

    async def fetch_tools(self, local_configs: dict) -> list[dict]:
        """Fetch tools"""
        mcp_session_handler = MCPSessionHandler(
            "amap-amap-sse",
            local_configs["mcpServers"]["amap-amap-sse"],
        )
        await mcp_session_handler.initialize()
        tools = await mcp_session_handler.list_tools()
        list_tools = []
        for tool in tools:
            list_tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema or {},
                },
            )
        return list_tools

    async def get_tools(self, local_configs: dict) -> list[dict]:
        """Get tools"""
        tools = await self.fetch_tools(local_configs)
        return tools

    async def get_mcp_server_code(
        self,
        server_code: str,
        need_tools: bool = False,
    ) -> dict:
        """Get MCP server code."""
        query = select(self.model).where(self.model.server_code == server_code)
        mcp = self.session.exec(query).first()
        tasks = [self.process_mcp(mcp, need_tools)]
        results = await asyncio.gather(*tasks)
        return results[0]

    async def list_mcp_servers(
        self,
        current: int,
        size: int,
        sort_by: str = "id",
        sort_order: str = "desc",
        total: Union[None, int] = None,
        status: Union[None, int] = None,
        name: Union[None, str] = None,
        need_tools: bool = False,
    ) -> List[MCP]:
        """List MCP servers"""

        query = select(MCP)
        if name is not None:
            query = query.where(MCP.name.contains(name))

        if status is not None:
            query = query.where(MCP.status == status)

        sort_column = getattr(MCP, sort_by, None)
        if sort_column is None:
            raise ValueError(f"Invalid sort_by parameter：{sort_by}")
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        if total is not None:
            result = self.session.execute(
                select(func.count()).select_from(query),
            )
            total_count = result.scalar_one()
            if total != total_count:
                raise ValueError(
                    f"The provided total {total} does not match the actual "
                    f"total {total_count}",
                )

        query = query.offset((current - 1) * size).limit(size)

        # Execute the query and get the results
        result = self.session.execute(query)
        mcp_list = result.scalars().all()

        # Use asyncio.gather to concurrently handle MCP
        tasks = [self.process_mcp(mcp, need_tools) for mcp in mcp_list]
        result = await asyncio.gather(*tasks)

        return result

    async def list_mcp_servers_by_codes(
        self,
        server_codes: list[str],
        need_tools: bool = False,
    ) -> List[dict]:
        """List MCP servers by codes."""

        query = select(MCP)
        query = query.where(MCP.server_code.in_(server_codes))
        mcp_list = self.session.exec(query).all()
        tasks = [self.process_mcp(mcp, need_tools) for mcp in mcp_list]
        result = await asyncio.gather(*tasks)

        return result

    async def debug_tools(
        self,
        server_code: str,
        tool_name: str,
        tool_params: dict,
    ) -> dict:
        """debug tools."""
        try:
            query = select(MCP).where(MCP.server_code == server_code)
            mcp = self.session.exec(query).first()
            if not mcp:
                raise ValueError("MCP not found")
            config = json.loads(mcp.deploy_config)
            install_config = json.loads(config["install_config"])
            mcp_session_handler = MCPSessionHandler(
                "amap-amap-sse",
                install_config["mcpServers"]["amap-amap-sse"],
            )

            async def execute_tool_async() -> dict:
                # Asynchronous session initialization
                await mcp_session_handler.initialize()

                # Invoke the tool and get the results
                result = await mcp_session_handler.call_tool(
                    tool_name,
                    tool_params,
                )
                return result.model_dump()

            tasks = [execute_tool_async()]
            result = await asyncio.gather(*tasks)
            return result[0]
        except Exception as e:
            raise ValueError(f"Error encountered: {str(e)}") from e

    def list_mcp_servers_num(
        self,
    ) -> int:
        """List MCP servers num."""
        query = select(func.count(MCP.id))
        num = self.session.exec(query).one()
        return num
