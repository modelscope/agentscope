# -*- coding: utf-8 -*-
from typing import Any, Union
import re
import enum
import numpy as np
from loguru import logger

from agentscope.agents import DialogAgent
from agentscope.message import Msg


HISTORY_WINDOW = 10


class CustomerConv(enum.IntEnum):
    """Enum for customer status."""

    WARMING_UP = 0
    AFTER_MEAL_CHAT = 1
    INVITED_GROUP_PLOT = 2


class CustomerPlot(enum.IntEnum):
    """Enum for customer plot active or not."""

    ACTIVE = 1
    NOT_ACTIVE = 0


class Customer(DialogAgent):
    def __init__(self, game_config: dict, **kwargs: Any):
        super().__init__(**kwargs)
        self.game_config = game_config
        self.max_itr_preorder = 5
        self.preorder_itr_count = 0
        self.background = self.config["character_setting"]["background"]

        self.plot_stage = CustomerPlot.NOT_ACTIVE
        self.stage = CustomerConv.WARMING_UP

    def visit(self):
        return (
            np.random.binomial(
                n=1,
                p=self.config.get("visit_prob", 0.99),
            )
            > 0
        )

    def activate_plot(self):
        self.plot_stage = CustomerPlot.ACTIVE

    def reset_stage(self):
        self.stage = CustomerConv.WARMING_UP

    def set_invited_stage(self):
        self.stage = CustomerConv.INVITED_GROUP_PLOT

    def reply(self, x: dict = None) -> Union[dict, tuple]:
        # TODO:
        # not sure if it is some implicit requirement of the tongyi chat api,
        # the first/last message must have role 'user'.
        x["role"] = "user"

        if self.stage == CustomerConv.WARMING_UP and "推荐" in x["content"]:
            self.stage = CustomerConv.AFTER_MEAL_CHAT
            return self._recommendation_to_score(x)
        elif self.stage == CustomerConv.WARMING_UP:
            return self._pre_meal_chat(x)
        elif (
            self.stage == CustomerConv.AFTER_MEAL_CHAT
            or self.stage == CustomerConv.INVITED_GROUP_PLOT
        ):
            return self._main_plot_chat(x)

    def _recommendation_to_score(self, x: dict) -> dict:
        food = x["content"]
        food_judge_prompt = self.game_config["food_judge_prompt"]
        food_judge_prompt = food_judge_prompt.format_map(
            {
                "food_preference": self.config["character_setting"][
                    "food_preference"
                ],
                "food": food,
            },
        )
        message = Msg(name="user", content=food_judge_prompt, role="user")

        def _parse_score(text: Any) -> (float, Any):
            score = re.search("([0-9]+)分", str(text)).groups()[0]
            return float(score), text

        def _default_score(_: str) -> float:
            return 2.0

        score, text = self.model(
            messages=[message],
            parse_func=_parse_score,
            fault_handler=_default_score,
            max_retries=3,
        )

        score_discount = 1 - self.preorder_itr_count / self.max_itr_preorder
        score_discount = score_discount if score_discount > 0 else 0
        score = score * score_discount
        if score > 4:
            self.stage = CustomerConv.AFTER_MEAL_CHAT
        self.preorder_itr_count = 0
        return text, score

    def _pre_meal_chat(self, x: dict) -> dict:
        self.preorder_itr_count += 1
        system_prompt = self.game_config["order_prompt"].format_map(
            {
                "name": self.config["name"],
                "character_description": self.background
                + self.config["character_setting"]["food_preference"],
            },
        )
        system_msg = Msg(role="user", name="system", content=system_prompt)
        # prepare prompt
        prompt = self.engine.join(
            self._validated_history_messages(recent_n=HISTORY_WINDOW),
            system_msg,
            x,
        )
        if x is not None:
            self.memory.add(x)
        reply = self.model(messages=prompt)
        reply_msg = Msg(role="assistant", name=self.name, content=reply)
        self.memory.add(reply_msg)
        return reply_msg

    def _main_plot_chat(self, x: dict) -> dict:
        """
        _main_plot_chat
        :param x:
        :return:
        Stages of the customer defines the prompt past to the LLM
        1. Customer is a main role in the current plot
            1.1 the customer has hidden plot
            1.2 the customer has no hidden plot (help with background)
        2. Customer is not a main role in the current plot
        """

        prompt = self.game_config["basic_background_prompt"].format_map(
            {
                "name": self.config["name"],
                "character_description": self.background,
            },
        )
        if self.plot_stage == CustomerPlot.ACTIVE:
            # -> prompt for the main role in the current plot
            prompt += self.game_config["hidden_main_plot_prompt"].format_map(
                {
                    "hidden_plot": self.config["character_setting"][
                        "hidden_plot"
                    ],
                },
            )
            if self.stage == CustomerConv.AFTER_MEAL_CHAT:
                prompt += self.game_config["hidden_main_plot_after_meal"]
            else:
                prompt += self.game_config["hidden_main_plot_discussion"]
        else:
            # -> prompt for the helper or irrelvant roles in the current plot
            if self.stage == CustomerConv.AFTER_MEAL_CHAT:
                prompt += self.game_config["regular_after_meal_prompt"]
            else:
                prompt += self.game_config["invited_chat_prompt"]

        logger.debug(f"{self.name} system prompt: {prompt}")

        system_msg = Msg(role="user", name="system", content=prompt)

        # prepare prompt
        prompt = self.engine.join(
            self._validated_history_messages(recent_n=HISTORY_WINDOW),
            system_msg,
        )

        logger.debug(f"{self.name} history prompt: {prompt}")

        if x is not None:
            messages = prompt + [x]
            self.memory.add(x)
        else:
            messages = prompt

        reply = self.model(messages=messages)

        reply_msg = Msg(role="assistant", name=self.name, content=reply)
        self.memory.add(reply_msg)
        return reply_msg

    def refine_background(self) -> None:
        background_prompt = self.game_config[
            "basic_background_prompt"
        ].format_map(
            {
                "name": self.config["name"],
                "character_description": self.background,
            },
        )
        background_prompt += self.game_config[
            "hidden_main_plot_prompt"
        ].format_map(
            {
                "hidden_plot": self.config["character_setting"]["hidden_plot"],
            },
        )
        analysis_prompt = background_prompt + self.game_config["analysis_conv"]

        system_msg = Msg(role="user", name="system", content=analysis_prompt)

        prompt = self.engine.join(
            self._validated_history_messages(recent_n=HISTORY_WINDOW * 2),
            system_msg,
        )

        analysis = self.model(messages=prompt)
        logger.info(f"聊完之后，{self.name}在想:" + analysis)

        update_prompt = self.game_config["update_background"].format_map(
            {
                "analysis": analysis,
                "background": self.background,
                "name": self.name,
            },
        )
        update_msg = Msg(role="user", name="system", content=update_prompt)
        new_background = self.model(messages=[update_msg])
        logger.info(f"根据对话，{self.name}的背景更新为：" + new_background)
        self.background = new_background

    def _validated_history_messages(self, recent_n: int = 10):
        hist_mem = self.memory.get_memory(recent_n=recent_n)
        if len(hist_mem) > 0:
            hist_mem[0]["role"], hist_mem[-1]["role"] = "user", "user"
        return hist_mem

    def generate_pov_story(self, recent_n: int = 20):
        related_mem = self._validated_history_messages(recent_n)
        conversation = ""
        for mem in related_mem:
            if "name" in mem:
                conversation += mem["name"] + ": " + mem["content"]
            else:
                print("debug:", mem)
                conversation += "背景" + ": " + mem["content"]
        background = self.background
        if self.plot_stage == CustomerPlot.ACTIVE:
             background += self.config["character_setting"]["hidden_plot"]

        pov_prompt = self.game_config["pov_story"].format_map({
            "name": self.name,
            "background": background,
            "conversation": conversation,
        })
        msg = Msg(name="system", role="user", content=pov_prompt)
        pov_story = self.model(messages=[msg])
        print("*" * 20)
        print(pov_story)
        print("*" * 20)
