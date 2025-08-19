import asyncio
import contextlib
import json
import os

from agentscope.agent import ReActAgent, UserAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.mcp import StdIOStatefulClient, HttpStatefulClient
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_python_code, execute_shell_command

from Meta_toolkit import CategoryManager, MetaManager


def init_meta_tool_from_intact_file(
    model_config_name: str,
    file_path: str = "Meta_tool_config.json",
    global_toolkit: Toolkit = None,
):
    """
    Initialize a meta manager from a complete tool configuration file.

    All tools from the global toolkit are added to their respective category
    managers, inheriting group information from the global toolkit. Within each
    category manager, only tools whose groups are marked as active in the global
    toolkit are visible, following the same visibility mechanism as in
    AgentScope.
    """

    current_dir = os.path.dirname(os.path.realpath(__file__))
    meta_tool_config_path = os.path.join(current_dir, file_path)
    with open(meta_tool_config_path, "r") as f:
        meta_tool_config = json.load(f)

    meta_manager = MetaManager()

    model = DashScopeChatModel(
        model_name=model_config_name,
        api_key=os.environ["DASHSCOPE_API_KEY"],
        stream=True,
    )

    for category_name, category_config in meta_tool_config.items():
        category_manager = CategoryManager(
            category_name=category_name,
            category_description=category_config["description"],
            tool_usage_notes=category_config["tool_usage_notes"],
            model=model,
            formatter=DashScopeChatFormatter(),
        )
        for tool_name in category_config["tools"]:
            if tool_name not in global_toolkit.tools:
                print(f"Tool {tool_name} not found in global toolkit")
                continue

            tool_func_obj = global_toolkit.tools[tool_name]
            if tool_func_obj.group == "basic":
                category_manager.add_internal_func_obj(
                    func_obj=tool_func_obj,
                )
            else:
                category_manager.add_internal_func_obj(
                    func_obj=tool_func_obj,
                    tool_group=global_toolkit.groups[tool_func_obj.group],
                )

        if not category_manager.internal_toolkit.tools:
            print(f"Category {category_name} has no tools, skip it")
            continue

        meta_manager.add_category_manager(category_manager=category_manager)

    return meta_manager


async def main():
    # Create global toolkit with your tools
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(execute_shell_command)

    toolkit.create_tool_group(
        "map_tools", "Tools related to Gaode map", active=True
    )
    # If a group's 'active' flag is set to False, its tools will be registered
    # to toolkit but remain hidden

    gaode_client = HttpStatefulClient(
        name="amap-sse",
        transport="sse",
        url="https://mcp.amap.com/sse?key={YOUR_AMAP_API_KEY}",
        # get your own API keys from Gaode MCP servers
    )
    bing_client = HttpStatefulClient(
        name="bing-cn-mcp-server",
        transport="sse",
        url="https://mcp.api-inference.modelscope.net/{YOUR_BING_API_KEY}/sse",
        # get your own API keys from Modelscope's Bing MCP servers
    )
    train_client = HttpStatefulClient(
        name="12306-mcp",
        transport="sse",
        url="https://mcp.api-inference.modelscope.net/{YOUR_12306_API_KEY}/sse",
        # get your own API keys from Modelscope's train 12306 MCP servers
    )
    try:
        try:
            await gaode_client.connect()
            await toolkit.register_mcp_client(
                gaode_client, group_name="map_tools"
            )
            print("Gaode MCP client connected successfully")
        except Exception as e:
            print(f"Failed to connect Gaode MCP client: {e}")

        try:
            await bing_client.connect()
            await toolkit.register_mcp_client(bing_client)
            print("Bing MCP client connected successfully")
        except Exception as e:
            print(f"Failed to connect Bing MCP client: {e}")

        try:
            await train_client.connect()
            await toolkit.register_mcp_client(train_client)
            print("12306 MCP client connected successfully")
        except Exception as e:
            print(f"Failed to connect 12306 MCP client: {e}")

        # Initialize meta manager from configuration
        meta_manager = init_meta_tool_from_intact_file(
            model_config_name="qwen-max",
            global_toolkit=toolkit,
        )

        # Use meta_manager directly as toolkit for ReActAgent
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You're a helpful assistant named Friday.",
            model=DashScopeChatModel(
                model_name="qwen-max",
                api_key=os.environ["DASHSCOPE_API_KEY"],
                stream=True,
            ),
            memory=InMemoryMemory(),
            formatter=DashScopeChatFormatter(),
            toolkit=meta_manager,  # Direct replacement for traditional toolkit
        )

        user = UserAgent(name="user")

        msg = None
        try:
            while True:
                msg = await agent(msg)
                msg = await user(msg)
                if msg.get_text_content() == "exit":
                    break
        except Exception as e:
            print(f"Error: {e}")

        return

    finally:
        with contextlib.suppress(Exception):
            await train_client.close()
        with contextlib.suppress(Exception):
            await bing_client.close()
        with contextlib.suppress(Exception):
            await gaode_client.close()


if __name__ == "__main__":
    asyncio.run(main())
