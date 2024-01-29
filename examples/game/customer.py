# -*- coding: utf-8 -*-
from typing import Any, Union, Tuple
import re
import json
import numpy as np
from loguru import logger

from enums import CustomerConv, CustomerPlot
from agentscope.agents import StateAgent, DialogAgent
from agentscope.message import Msg
from relationship import Relationship
from utils import (
    send_chat_msg,
    send_clue,
    get_a_random_avatar,
    send_pretty_msg,
    replace_names_in_messages,
    SYS_MSG_PREFIX,
)

HISTORY_WINDOW = 10
# TODO: for debug, set the score bars to be lower
MIN_BAR_RECEIVED_CONST = 4
MIN_BAR_FRIENDSHIP_CONST = 30
MESSAGE_KEYS = ["name", "role", "content"]


class Customer(StateAgent, DialogAgent):
    def __init__(self, game_config: dict, **kwargs: Any):
        self.uid = kwargs.pop("uid")
        super().__init__(**kwargs)
        self.retry_time = 3
        self.game_config = game_config
        self.max_itr_preorder = 5
        self.preorder_itr_count = 0
        self.avatar = self.config.get("avatar", get_a_random_avatar())
        self.background = self.config["character_setting"]["background"]
        self.friendship = int(self.config.get("friendship", 60))
        self.relationship = Relationship(
            self.config.get("relationship", "陌生"),
            MIN_BAR_RECEIVED_CONST,
        )
        self.cur_state = CustomerConv.WARMING_UP
        # TODO: A customer can be in at most one plot in the current version
        self.active_plots = []

        self.register_state(
            state=CustomerConv.OPENING,
            handler=self._opening_chat,
        )

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

        # Clues: `unexposed_clues` & `exposed_clues`
        self.unexposed_clues = self.config.get("clue", None)
        if self.unexposed_clues is None:
            self.unexposed_clues = self.build_clues()
        self.exposed_clues = []

    def visit(self) -> np.array:
        # TODO: for debug, set the visit prob to be 0.9
        return np.random.binomial(n=1, p=0.9) > 0
        # return (
        #     np.random.binomial(
        #         n=1,
        #         p=min(self.friendship / 100, 1.0),
        #     )
        #     > 0
        # )

    def activate_plot(self, active_plots: list[int]) -> None:
        # when the customer is the main role in a plot, it will be activated
        self.plot_stage = CustomerPlot.ACTIVE
        for p in active_plots:
            if (
                str(p) in self.config["character_setting"]["hidden_plot"]
                and len(self.active_plots) == 0
            ):
                self.active_plots = [str(p)]
            elif str(p) in self.config["character_setting"]["hidden_plot"]:
                raise ValueError(
                    "A customer can be in at most one plot in the current "
                    "version",
                )
            else:
                logger.error(f"Plot {p} is not defined in the hidden_plot")
                raise ValueError

    def deactivate_plot(self) -> None:
        # when the plot in which the customer is a main role is over, the
        # customer will be deactivated
        self.plot_stage = CustomerPlot.NOT_ACTIVE
        self.active_plots = []

    def reply(self, x: dict = None) -> Union[dict, tuple]:
        # TODO:
        # not sure if it is some implicit requirement of the tongyi chat api,
        # the first/last message must have role 'user'.
        if x is not None:
            x["role"] = "user"
        logger.debug(
            f"{self.name} state: {self.cur_state} {self.plot_stage}"
            f" {self.active_plots}",
        )
        msg = StateAgent.reply(self, x=x)
        send_pretty_msg(msg, uid=self.uid, avatar=self.avatar)
        return msg

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
            [
                {
                    key: getattr(message, key)
                    for key in MESSAGE_KEYS
                    if hasattr(message, key)
                },
            ],
            parse_func=_parse_score,
            fault_handler=_default_score,
            max_retries=3,
        )

        # score_discount = 1 - self.preorder_itr_count / self.max_itr_preorder
        # score_discount = score_discount if score_discount > 0 else 0
        # score = score * score_discount

        # change_in_friendship = score - MIN_BAR_RECEIVED_CONST
        # self.friendship += change_in_friendship
        # change_symbol = "+" if change_in_friendship >= 0 else ""
        # send_chat_msg(
        #     f" {SYS_MSG_PREFIX}{self.name}: 好感度变化 "
        #     f"{change_symbol}{round(change_in_friendship, 2)} "
        #     f"当前好感度为 {round(self.friendship, 2)}",
        #     uid=self.uid,
        # )

        satisfied = "不满意"
        if self.relationship.is_satisfied(score):
            satisfied = "满意"
        text = satisfied + "，" + text

        prev_relationship = self.relationship.to_string()
        self.relationship.update(score)
        cur_relationship = self.relationship.to_string()
        chat_text = f" {SYS_MSG_PREFIX} {self.name}感觉{food}{satisfied}, "

        if prev_relationship != cur_relationship:
            chat_text += f"你们的关系从{prev_relationship}变得{cur_relationship}了"
        else:
            chat_text += f"你们的关系没变化，依旧是{prev_relationship}。"

        send_chat_msg(
            chat_text,
            uid=self.uid,
        )

        if self.relationship.is_satisfied(score) or (
                score >= MIN_BAR_RECEIVED_CONST
                and self.friendship >= MIN_BAR_FRIENDSHIP_CONST
        ):
            self.transition(CustomerConv.AFTER_MEAL_CHAT)
            print("---", self.cur_state)
        self.preorder_itr_count = 0

        return Msg(
            role="assistant",
            name=self.name,
            content=text,
            score=score,
            relationship=cur_relationship,
        )

    def _opening_chat(self, x: dict) -> dict:
        system_prompt = self.game_config["basic_background_prompt"].format_map(
            {
                "name": self.config["name"],
                "character_description": self.background
            }
        ) + self.game_config[
                            "hidden_main_plot_prompt"
                        ].format_map(
            {
                "hidden_plot": self.config["character_setting"]["hidden_plot"],
            },
        )
        if x is not None:
            self.memory.add(x)

        system_msg = Msg(role="user", name="system", content=system_prompt)
        prompt = self.engine.join(
            self._validated_history_messages(recent_n=HISTORY_WINDOW),
            system_msg,
            x,
        )

        logger.debug(prompt)

        reply = self.model(replace_names_in_messages(prompt))
        reply_msg = Msg(role="assistant", name=self.name, content=reply)
        self.memory.add(reply_msg)

        self.update_clues(reply_msg.content)

        return reply_msg

    def _pre_meal_chat(self, x: dict) -> dict:
        if "food" in x:
            return self._recommendation_to_score(x)

        self.preorder_itr_count += 1
        system_prompt = self.game_config["order_prompt"].format_map(
            {
                "name": self.config["name"],
                "character_description": self.background
                                         + self.config["character_setting"][
                                             "food_preference"],
            },
        )
        system_msg = Msg(role="user", name="system", content=system_prompt)
        # prepare prompt
        prompt = self.engine.join(
            self._validated_history_messages(recent_n=HISTORY_WINDOW),
            system_msg,
            x,
        )
        logger.debug(system_prompt)
        if x is not None:
            self.memory.add(x)

        reply = self.model(replace_names_in_messages(prompt))
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
        prompt = self._gen_plot_related_prompt()

        logger.debug(f"{self.name} system prompt: {prompt}")

        system_msg = Msg(role="user", name="system", content=prompt)

        join_args = [
            self._validated_history_messages(recent_n=HISTORY_WINDOW),
            system_msg,
        ]

        if x is not None:
            join_args.append(x)
            self.memory.add(x)

        prompt = self.engine.join(*join_args)

        logger.debug(f"{self.name} history prompt: {prompt}")

        reply = self.model(replace_names_in_messages(prompt))

        reply_msg = Msg(role="assistant", name=self.name, content=reply)
        self.memory.add(reply_msg)

        self.update_clues(reply_msg.content)

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

        analysis = self.model(replace_names_in_messages(prompt))
        analysis_msg = Msg(
            role="user",
            name=self.name,
            content=f"聊完之后，{self.name}在想:" + analysis,
        )
        send_pretty_msg(
            analysis_msg,
            uid=self.uid,
            avatar=self.avatar,
        )

        update_prompt = self.game_config["update_background"].format_map(
            {
                "analysis": analysis,
                "background": self.background,
                "name": self.name,
            },
        )
        update_msg = Msg(role="user", name="system", content=update_prompt)
        new_background = self.model(
            [
                {
                    key: getattr(update_msg, key)
                    for key in MESSAGE_KEYS
                    if hasattr(update_msg, key)
                },
            ],
        )
        bg_msg = Msg(
            role="user",
            name=self.name,
            content=f" {SYS_MSG_PREFIX}根据对话，{self.name}的背景更新为："
            + new_background,
        )
        send_chat_msg(
            bg_msg,
            uid=self.uid,
            avatar=self.avatar,
        )
        self.background = new_background

    def _validated_history_messages(self, recent_n: int = 10):
        hist_mem = self.memory.get_memory(recent_n=recent_n)
        if len(hist_mem) > 0:
            hist_mem[0]["role"], hist_mem[-1]["role"] = "user", "user"
        return hist_mem

    def generate_pov_story(self, recent_n: int = 20) -> None:
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
        pov_story = self.model(
            [
                {
                    key: getattr(msg, key)
                    for key in MESSAGE_KEYS
                    if hasattr(msg, key)
                },
            ],
        )
        print("*" * 20)
        send_chat_msg(pov_story, uid=self.uid)
        print("*" * 20)

    def _gen_plot_related_prompt(self) -> str:
        """
        generate prompot depending on the state and friendship of the customer
        """
        prompt = self.game_config["basic_background_prompt"].format_map(
            {
                "name": self.config["name"],
                "character_description": self.background,
            },
        )
        if (
            self.plot_stage == CustomerPlot.ACTIVE
            and self.friendship > MIN_BAR_FRIENDSHIP_CONST
        ):
            # -> prompt for the main role in the current plot
            prompt += self.game_config["hidden_main_plot_prompt"].format_map(
                {
                    "hidden_plot": self.config["character_setting"][
                        "hidden_plot"
                    ][self.active_plots[0]],
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

        prompt += self.game_config[self.relationship.prompt]

        return prompt

    def talk(self, content, is_display=True):
        if content is not None:
            msg = Msg(
                role="user",
                name=self.name,
                content=content,
            )
            self.memory.add(msg)
            if is_display:
                send_chat_msg(
                    content,
                    role=self.name,
                    uid=self.uid,
                    avatar=self.avatar,
                    flushing=True,
                )
            return msg

    def build_clues(self):
        # Get all hidden plot
        send_chat_msg(f"{SYS_MSG_PREFIX}初始化NPC {self.name}..."
                      f"（这可能需要一些时间）", uid=self.uid)

        all_plot = ""
        for i in self.config["character_setting"]["hidden_plot"].values():
            all_plot += (i + "\n")

        clue_parse_prompt = self.game_config["clue_parse_prompt"] + all_plot
        message = Msg(name="system", role="user", content=clue_parse_prompt)

        clues = self.model(
            [
                {
                    key: getattr(message, key)
                    for key in MESSAGE_KEYS
                    if hasattr(message, key)
                },
            ],
            parse_func=json.loads,
            max_retries=self.retry_time,
        )
        logger.debug(clues)
        send_chat_msg(f"{SYS_MSG_PREFIX}初始化NPC {self.name}完成！", uid=self.uid)
        return clues

    def update_clues(self, content):

        if len(self.unexposed_clues) == 0:
            return

        prompt = self.game_config["clue_detect_prompt"].format_map(
            {
                "content": content,
                "clue": self.unexposed_clues,
                "name": self.name,
            }
        )
        message = Msg(name="system", content=prompt, role="user")
        exposed_clues = self.model(
            [
                {
                    key: getattr(message, key)
                    for key in MESSAGE_KEYS
                    if hasattr(message, key)
                },
            ],
            parse_func=json.loads,
            max_retries=self.retry_time,
        )
        logger.debug(exposed_clues)
        indices_to_pop = []
        found_clue = []
        for clue in exposed_clues:
            index = clue.get("index", -1)
            summary = clue.get("summary", -1)
            if index < len(self.unexposed_clues) and index:
                indices_to_pop.append(index)
                found_clue.append(summary)
        indices_to_pop.sort(reverse=True)
        for index in indices_to_pop:
            element = self.unexposed_clues.pop(index)
            self.exposed_clues.append(element)

        for clue_str in found_clue:
            send_chat_msg(f"【发现线索】{clue_str} \n\n剩余未线索:"
                          f"{len(self.unexposed_clues)}", uid=self.uid)
            send_clue(
                clue_str,
                unexposed_num=len(self.unexposed_clues),
                uid=self.uid,
                role=self.name,
            )