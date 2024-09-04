# -*- coding: utf-8 -*-
"""An example parallel service execution."""

from typing import List, Any, Union, Mapping, Callable
from copy import deepcopy
import os
from loguru import logger
import time
import argparse
from functools import partial

import agentscope
from agentscope.service import google_search, bing_search, load_web, digest_webpage, ServiceToolkit
from agentscope.service.service_response import ServiceResponse, ServiceExecStatus
from agentscope.agents import UserAgent
from agentscope.manager import ModelManager
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logger-level",
        choices=['DEBUG', 'INFO'],
        default="INFO",
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
    agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION, use_monitor=False, logger_level=args.logger_level)
    if args.search_engine == "google":
        response = google_search("Journey to the West", args.api_key, args.cse_id).content
    else:
        response = bing_search("Journey to the West", args.api_key).content
    
    # Initialize the RPC service and commands
    func = RpcService(digest_webpage, model_config_name=YOUR_MODEL_CONFIGURATION_NAME, to_dist=args.use_dist)
    cmds = [
        {'func': func, 'arguments': {'web_text_or_url': page['link'], 'html_selected_tags' : ["p", "div", "h1", "li"]}}
        for page in response
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
    if args.use_dist:
        execute_results = [exe.result() for exe in execute_results]
    end_time = time.time()
    print(f'len(execute_results) = {len(execute_results)}, duration = {end_time - start_time:.2f} s')


if __name__ == '__main__':
    main()
