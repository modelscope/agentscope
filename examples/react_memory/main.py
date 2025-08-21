# -*- coding: utf-8 -*-
"""The main entry point of the ReActMemory example."""
import asyncio
import os

from typing import Literal

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit

from examples.react_memory._react_memory import ReActMemory
from examples.react_memory.config.prompts import (
    SUMMARIZE_WORKING_LOG_PROMPT_W_QUERY,
    SUMMARIZE_WORKING_LOG_PROMPT_v2,
    UPDATE_MEMORY_PROMPT_DEFAULT,
)
from examples.react_memory.vector_factories.qdrant import Qdrant


async def main() -> None:
    """The main entry point of the ReActMemory example."""

    toolkit = Toolkit()
    vector_store = Qdrant(
        collection_name="react_memory",
        embedding_model_dims=1024,
        path="/tmp/vector_store",
    )
    retrieve_type: Literal["source", "processed", "auto"] = "processed"
    # all the messages will be processed by llm and then store
    # in the vector store.
    # Another choices are "source" and "auto":
    react_memory = ReActMemory(
        model_config_name="qwen-max",
        embedding_model="text-embedding-v4",
        vector_store=vector_store,
        retrieve_type=retrieve_type,
        update_memory_prompt=UPDATE_MEMORY_PROMPT_DEFAULT,
        summary_working_log_prompt=SUMMARIZE_WORKING_LOG_PROMPT_v2,
        summary_working_log_w_query_prompt=(
            SUMMARIZE_WORKING_LOG_PROMPT_W_QUERY
        ),
        global_update_allowed=False,
        process_w_llm=False,
    )
    agent = ReActAgent(
        name="Friday",
        sys_prompt="You are a helpful assistant named Friday.",
        model=DashScopeChatModel(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            model_name="qwen-max",
            stream=True,
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        memory=react_memory,
    )
    query_1 = Msg(
        "user",
        "Please introduce Einstein",
        "user",
    )
    await agent(query_1)
    current_memory = await react_memory.get_memory()
    print(f"The memory after the first query is: {current_memory}")
    query_2 = Msg(
        "user",
        "What is his most renowned achievement?",
        "user",
    )
    await agent(query_2)
    current_memory = await react_memory.get_memory()
    print(f"The memory after the second query is: {current_memory}")


asyncio.run(main())
