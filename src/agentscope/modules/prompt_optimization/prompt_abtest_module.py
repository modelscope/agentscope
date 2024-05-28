# -*- coding: utf-8 -*-
from typing import Any, Union, List
from .prompt_opt_method import PromptOptMethodBase

from loguru import logger

from agentscope.models import load_model_by_config_name
from agentscope.message import Msg
from agentscope.web.studio.utils import user_input

class PromptAbTestModule:
    def __init__(
        self,
        model_config_name:str,
        user_prompt: str,
        opt_methods_or_prompts: List[Union[PromptOptMethodBase, str]],
        save_dir: str = None,
    ) -> None:
        self.model = load_model_by_config_name(model_config_name)
        self.user_prompt = user_prompt
        assert isinstance(opt_methods_or_prompts, list)
        self.ab_prompt_list = []
        for item in opt_methods_or_prompts:
            if isinstance(item, str):
                self.ab_prompt_list.append(item)
            elif isinstance(item, PromptOptMethodBase):
                self.ab_prompt_list.append(item.optimize(user_prompt))
            else:
                raise ValueError(
                    "The provide opt methods or prompts "
                    "should either be an optimized str "
                    "or a prompt optimization method "
                    "that inherit `PromptOptMethodBase`",
                )
        self.save_dir = save_dir

    def show_optimized_prompts(self):
        for index, opt_prompt in enumerate(self.ab_prompt_list, start=1):
            logger.chat(f"\n## Generated System Prompt of Method {index}\n")
            logger.chat(opt_prompt)
            logger.chat("===" * 10 + "\n")  # 打印一个空行以增加可读性

    def infer_with_system_prompt(self, user_query, system_prompt):

        prompt = self.model.format([
            Msg(name="system", content=system_prompt, role="system"),
            Msg(name="user", content=user_query, role="user"),
        ])
        response = self.model(prompt).text

        return response

    def compare_query_results(self, queries: List[str]):
        for index, query in enumerate(queries, start=1):
            logger.chat(f"## Query {index}:\n")
            logger.chat(query)
            for m_index, opt_prompt in enumerate(self.ab_prompt_list, start=1):
                logger.chat(f"\n## Method {m_index}\n")
                res = self.infer_with_system_prompt(query, opt_prompt)
                logger.chat(res + "\n")