# -*- coding: utf-8 -*-
"""An example parallel service execution."""

from typing import List, Any, Union, Mapping, Callable, Optional, Sequence
from copy import deepcopy
import os
from loguru import logger
import time
import argparse
from functools import partial

import agentscope
from agentscope.service import google_search, bing_search, load_web, digest_webpage, ServiceToolkit
from agentscope.service.service_response import ServiceResponse, ServiceExecStatus
from agentscope.agents import UserAgent, AgentBase
from agentscope.manager import ModelManager
from agentscope.message import Msg
from agentscope.rpc import call_func_in_thread
from agentscope.rpc.rpc_meta import RpcMeta, sync_func, async_func


class RpcService(metaclass=RpcMeta):
    """The RPC service class."""
    def __init__(self, service_func: Callable[..., Any], **kwargs) -> None:
        if 'model_config_name' in kwargs:
            model_config_name = kwargs.pop('model_config_name')
            model_manager = ModelManager.get_instance()
            model = model_manager.get_model_by_config_name(model_config_name)
            kwargs['model'] = model
        self.service_func = partial(service_func, **kwargs)

    @async_func
    def __call__(self, *args: tuple, **kwargs: dict) -> Any:
        try:
            result = self.service_func(*args, **kwargs)
        except Exception as e:
            result = ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=str(e),
            )
        return result


class WebSearchAgent(AgentBase):
    """An agent with search tool."""

    def __init__(
        self,
        name: str,
        model_config_name: str = None,
        result_num: int = 10,
        search_engine_type: str = "google",
        api_key: str = None,
        cse_id: str = None,
        dist_search: bool = False
    ) -> None:
        """Init a SearcherAgent.

        Args:
            name (`str`): the name of this agent.
            model_config_name (`str`, optional): The name of model
            configuration for this agent. Defaults to None.
            result_num (`int`, optional): The number of return results.
            Defaults to 10.
            search_engine_type (`str`, optional): the search engine to use.
            Defaults to "google".
            api_key (`str`, optional): api key for the search engine. Defaults
            to None.
            cse_id (`str`, optional): cse_id for the search engine. Defaults to
            None.
        """
        super().__init__(
            name=name,
            sys_prompt="You are an AI assistant who optimizes search"
            " keywords. You need to transform users' questions into a series "
            "of efficient search keywords.",
            model_config_name=model_config_name,
            use_memory=False,
        )
        self.result_num = result_num
        if search_engine_type == "google":
            assert (api_key is not None) and (
                cse_id is not None
            ), "google search requires 'api_key' and 'cse_id'"
            self.search = partial(
                google_search,
                api_key=api_key,
                cse_id=cse_id,
            )
        elif search_engine_type == "bing":
            assert api_key is not None, "bing search requires 'api_key'"
            self.search = partial(bing_search, api_key=api_key)
        self.dist_search = dist_search
        logger.info(self.dist_search)
        self.digest_webpage = RpcService(digest_webpage, model_config_name=model_config_name, to_dist=dist_search)
        logger.info(self.digest_webpage)

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        prompt = self.model.format(
            Msg(name="system", role="system", content=self.sys_prompt),
            x,
            Msg(
                name="user",
                role="user",
                content="Please convert the question into keywords. The return"
                " format is:\nKeyword1 Keyword2...",
            ),
        )
        query = self.model(prompt).text
        results = self.search(
            question=query,
            num_results=self.result_num,
        ).content

        cmds = [
            {'func': self.digest_webpage, 'arguments': {'web_text_or_url': page['link'], 'html_selected_tags' : ["p", "div", "h1", "li"]}}
            for page in results
        ]
        def execute_cmd(cmd: dict) -> str:
            service_func = cmd["func"]
            kwargs = cmd.get("arguments", {})

            # Execute the function
            func_res = service_func(**kwargs)
            return func_res

        # Execute the commands
        start_time = time.time()
        execute_results = [execute_cmd(cmd=cmd) for cmd in cmds]
        if self.dist_search:
            execute_results = [exe.result() for exe in execute_results]
        end_time = time.time()
        msg = Msg(
            self.name,
            content=[
                Msg(
                    name=self.name,
                    content=result,
                    role="assistant",
                    url=result["link"],
                    metadata=x.content,
                )
                for result in results
            ],
            role="assistant",
        )
        self.speak(
            Msg(
                name=self.name,
                role="assistant",
                content="Search results:\n"
                f"{[result['link'] for result in results]}",
            ),
        )
        return msg


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logger-level",
        choices=['DEBUG', 'INFO'],
        default="INFO",
    )
    parser.add_argument(
        '--studio-url',
        default=None,
        type=str,
    )
    parser.add_argument(
        "--use-dist",
        action="store_true",
    )
    parser.add_argument(
        "--api-key",
        type=str,
    )
    parser.add_argument(
        "--search-engine",
        type=str,
        choices=["google", "bing"],
        default="google",
    )
    parser.add_argument("--cse-id", type=str, default=None)
    return parser.parse_args()


def main():
    """Example for parallel service execution."""
    args = parse_args()

    # Prepare the model configuration
    YOUR_MODEL_CONFIGURATION_NAME = "dash"
    YOUR_MODEL_CONFIGURATION = [{"model_type": "dashscope_chat", "config_name": "dash", "model_name": "qwen-turbo", "api_key": os.environ.get('DASH_API_KEY', '')}]

    # Initialize the search result
    agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION, use_monitor=False, logger_level=args.logger_level, studio_url=args.studio_url)
    user_agent = UserAgent()
    web_search_agent = WebSearchAgent('WebSearch', model_config_name=YOUR_MODEL_CONFIGURATION_NAME, search_engine_type=args.search_engine, api_key=args.api_key, cse_id=args.cse_id, dist_search=args.use_dist)
    x = user_agent() # .content
    web_search_agent(x)


if __name__ == '__main__':
    main()
