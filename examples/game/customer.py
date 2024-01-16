# -*- coding: utf-8 -*-
from typing import Any, Union, Tuple
import re
import enum
import numpy as np
from loguru import logger

from agentscope.agents import StateAgent, DialogAgent
from agentscope.message import Msg


HISTORY_WINDOW = 10
MIN_BAR_RECEIVED_CONST = 4


class CustomerConv(enum.IntEnum):
    """Enum for customer status."""

    WARMING_UP = 0
    AFTER_MEAL_CHAT = 1
    INVITED_GROUP_PLOT = 2


class CustomerPlot(enum.IntEnum):
    """Enum for customer plot active or not."""

    ACTIVE = 1
    NOT_ACTIVE = 0


class Customer(StateAgent, DialogAgent):
    def __init__(self, game_config: dict, **kwargs: Any):
        super().__init__(**kwargs)
        self.game_config = game_config
        self.max_itr_preorder = 5
        self.preorder_itr_count = 0
        self.background = self.config["character_setting"]["background"]
        self.friendship = int(self.config.get("friendship", 60))

        self.cur_state = CustomerConv.WARMING_UP

        self.register_state(
            state=CustomerConv.WARMING_UP,
            handler=self._pre_meal_chat,
        )
        self.register_state(
            state=CustomerConv.AFTER_MEAL_CHAT,
            handler=self._main_plot_chat,
        )
        self.register_state(
            state=CustomerConv.INVITED_GROUP_PLOT,
            handler=self._main_plot_chat,
        )

        # TODO: refactor to a sub-state
        self.plot_stage = CustomerPlot.NOT_ACTIVE

    def visit(self):
        return (
            np.random.binomial(
                n=1,
                p=min(self.friendship / 100, 1.0),
            )
            > 0
        )

    def activate_plot(self) -> None:
        # Note: once activate, never deactivate
        if self.friendship >= 80:
            self.plot_stage = CustomerPlot.ACTIVE

    def reply(self, x: dict = None) -> Union[dict, tuple]:
        # TODO:
        # not sure if it is some implicit requirement of the tongyi chat api,
        # the first/last message must have role 'user'.
        if x is not None:
            x["role"] = "user"
        return StateAgent.reply(self, x=x)

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

        def _parse_score(text: Any) -> Tuple[float, Any]:
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

        if score > MIN_BAR_RECEIVED_CONST and self.friendship > 60:
            self.cur_state = CustomerConv.AFTER_MEAL_CHAT
        self.preorder_itr_count = 0

        change_in_friendship = score - MIN_BAR_RECEIVED_CONST
        self.friendship += change_in_friendship
        change_symbol = "+" if change_in_friendship >= 0 else ""
        logger.info(
            f"{self.name}: 好感度变化 {change_symbol}{change_in_friendship} "
            f"当前好感度为 {self.friendship}",
        )

        return Msg(role="assistant", name=self.name, content=text, score=score)

    def _pre_meal_chat(self, x: dict) -> dict:
        if "推荐" in x["content"]:
            self.transition(CustomerConv.AFTER_MEAL_CHAT)
            return self._recommendation_to_score(x)

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
            if self.cur_state == CustomerConv.AFTER_MEAL_CHAT:
                prompt += self.game_config["hidden_main_plot_after_meal"]
            else:
                prompt += self.game_config["hidden_main_plot_discussion"]
        else:
            # -> prompt for the helper or irrelvant roles in the current plot
            if self.cur_state == CustomerConv.AFTER_MEAL_CHAT:
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
                conversation += "背景" + ": " + mem["content"]
        background = self.background
        if self.plot_stage == CustomerPlot.ACTIVE:
            background += self.config["character_setting"]["hidden_plot"]

        pov_prompt = self.game_config["pov_story"].format_map(
            {
                "name": self.name,
                "background": background,
                "conversation": conversation,
            },
        )
        msg = Msg(name="system", role="user", content=pov_prompt)
        pov_story = self.model(messages=[msg])
        print("*" * 20)
        logger.info(pov_story)
        print("*" * 20)
