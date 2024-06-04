# -*- coding: utf-8 -*-
"""The Abtest module to show how different system prompt performs"""
from typing import Union, List
from loguru import logger

from agentscope.models import load_model_by_config_name
from agentscope.message import Msg
from agentscope.agents import DialogAgent, UserAgent
from .prompt_gen_method import PromptGeneratorBase


class PromptAbTestModule:
    """The Abtest module to show how different system prompts perform"""

    def __init__(
        self,
        model_config_name: str,
        user_prompt: str,
        opt_methods_or_prompts: List[Union[PromptGeneratorBase, str]],
    ) -> None:
        """
        Init the Abtest module, the model config name, user prompt,
        and a list of prompt optimization methods or prompts are required.

        Args:
            model_config_name (`str`):
                The model config for the model to be used to generate
                and compare prompts.
            user_prompt (`str`):
                The origial user prompt to be compared with.
            opt_methods_or_prompts (`List[Union[PromptOptMethodBase, str]]`):
                A list of prompt optimization methods or prompts. If the prompt
                optimization method is provided, the method will be called
                to get the optimized prompt during the init.

        """
        self.model_config_name = model_config_name
        self.model = load_model_by_config_name(model_config_name)
        self.user_prompt = user_prompt
        assert isinstance(opt_methods_or_prompts, list)
        self.ab_prompt_list = []
        for index, item in enumerate(opt_methods_or_prompts, start=1):
            if isinstance(item, str):
                self.ab_prompt_list.append(item)
            elif isinstance(item, PromptGeneratorBase):
                logger.chat(f"Calling the optimize method {index}")
                self.ab_prompt_list.append(item.optimize(user_prompt))
            else:
                raise ValueError(
                    "The provide opt methods or prompts "
                    "should either be an optimized str "
                    "or a prompt optimization method "
                    "that inherit `PromptOptMethodBase`",
                )
            logger.chat(
                f"The system prompt for method {index} is: "
                f"{self.ab_prompt_list[-1]}",
            )

    def show_optimized_prompts(self) -> None:
        """Show all the optimzed prompts"""
        for index, opt_prompt in enumerate(self.ab_prompt_list, start=1):
            logger.chat(f"\n## Generated System Prompt of Method {index}\n")
            logger.chat(opt_prompt)
            logger.chat("===" * 10 + "\n")  # 打印一个空行以增加可读性

    def infer_with_system_prompt(
        self,
        user_query: str,
        system_prompt: str,
    ) -> str:
        """Send query with system prompt"""
        prompt = self.model.format(
            [
                Msg(name="system", content=system_prompt, role="system"),
                Msg(name="user", content=user_query, role="user"),
            ],
        )
        response = self.model(prompt).text

        return response

    def compare_query_results(self, queries: List[str]) -> None:
        """Show the query results under different system prompts"""
        for index, query in enumerate(queries, start=1):
            logger.chat(f"## Query {index}:\n")
            logger.chat(query)
            logger.chat(("\n## Using Original Prompt\n"))
            res = self.infer_with_system_prompt(query, self.user_prompt)
            logger.chat(res + "\n")
            for m_index, opt_prompt in enumerate(self.ab_prompt_list, start=1):
                logger.chat(f"\n## Using Method {m_index} Prompt\n")
                res = self.infer_with_system_prompt(query, opt_prompt)
                logger.chat(res + "\n")

    def compare_with_dialog(self) -> None:
        """
        Compare how different system prompt perform with dialog
        press `exit` to finish
        """
        user_prompt_dialog_agent = DialogAgent(
            "assistant",
            sys_prompt=self.user_prompt,
            model_config_name=self.model_config_name,
        )
        opt_prompt_dialog_agent_list = []
        for opt_prompt in self.ab_prompt_list:
            opt_prompt_dialog_agent_list.append(
                DialogAgent(
                    "assistatn",
                    sys_prompt=opt_prompt,
                    model_config_name=self.model_config_name,
                ),
            )
        user_agent = UserAgent()
        x = None
        while x is None or x.content != "exit":
            logger.chat(("\n## Using Original Prompt\n"))
            user_prompt_dialog_agent(x)
            for index, opt_dialog_agent in enumerate(
                opt_prompt_dialog_agent_list,
                start=1,
            ):
                logger.chat(f"\n## Using Method {index} Prompt\n")
                opt_dialog_agent(x)
            x = user_agent()
