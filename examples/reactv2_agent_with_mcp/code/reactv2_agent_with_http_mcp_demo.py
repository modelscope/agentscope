import os
from agentscope.agents import ReActAgentV2
import agentscope
from agentscope.formatters import OpenAIFormatter
from agentscope.service import ServiceToolkit
from agentscope.message import Msg


# Model name
model_name = "qwen-plus"

# Load model configs
agentscope.init(
    model_configs=[
        {
            "config_name": "my_config",
            "model_type": "dashscope_chat",
            "model_name": "qwen-plus",
            # When using ReActAgentV2, streaming (i.e., setting "stream": True) is not supported.
            # "stream": False,
        },
        # Or you can use an OpenAI-compatible API, but note that non-OpenAI models
        # need to be added to OpenAIFormatter later.
        # {
        #     "config_name": "my_config",
        #     "client_args": {
        #         "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",  # specify the base URL of the API
        #     },
        #     "api_key": os.environ.get("DASHSCOPE_API_KEY"),
        #     "model_type": "openai_chat",
        #     "model_name": model_name,
        # }
    ]
)
# If you choose to use the OpenAI-compatible API and if the model is not an OpenAI model,
# make sure to append the model name to OpenAIFormatter.
# OpenAIFormatter.supported_model_regexes.append(model_name)

# Add MCP servers
toolkit = ServiceToolkit()
toolkit.add_mcp_servers(
    {
        "mcpServers": {
            "add-tool": {
                "type": "sse",
                "url": "http://127.0.0.1:8001/sse_app/sse"
            },
            "multiply-tool": {
                "type": "streamable_http",
                "url": "http://127.0.0.1:8001/streamable_http_app/mcp/"
            }
        }
    }
)

agent = ReActAgentV2(
    name="Friday",
    max_iters=3,
    model_config_name="my_config",
    service_toolkit=toolkit,
    sys_prompt="You're a helpful assistant named Friday.",
)

if __name__ == "__main__":
    # start the mcp servers before running this script
    res_msg = agent(Msg("user", "Calculate 2345 multiplied by 3456, then add 4567 to the result, what is the final outcome?", "user"))
    print(f"The final answer is: \n\t{res_msg.content}")