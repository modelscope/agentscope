# -*- coding: utf-8 -*-
import copy
from typing import Any, Union, Tuple
import re
import json
import random
import numpy as np
from loguru import logger

from enums import CustomerConv, CustomerPlot
from agentscope.agents import StateAgent, DialogAgent
from agentscope.message import Msg
from relationship import Relationship
from utils import (
    send_chat_msg,
    send_clue_msg,
    get_a_random_avatar,
    send_pretty_msg,
    replace_names_in_messages,
    SYS_MSG_PREFIX,
    get_clue_image_b64_url,
    extract_keys_from_dict,
    send_story_msg,
)

HISTORY_WINDOW = 10
# TODO: for debug, set the score bars to be lower
MIN_BAR_RECEIVED_CONST = 4
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
        # self.friendship = int(self.config.get("friendship", 60))
        self.is_satisfied = False
        self.relationship = Relationship(
            self.config.get("relationship", "陌生"),
            MIN_BAR_RECEIVED_CONST,
        )
        self.preferred_info = ''
        self.cur_state = CustomerConv.WARMING_UP
        # TODO: A customer can be in at most one plot in the current version
        self.active_plots = []
        self.prev_active_plots = []

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
        self.all_clues = copy.deepcopy(self.config.get("clue", None))
        if self.unexposed_clues is None:
            raise ValueError("No clue is provided for this customer.")

        self.hidden_plot = {}
        for item in self.unexposed_clues:
            if item["plot"] in self.hidden_plot.keys():
                self.hidden_plot[item["plot"]] += "\n" + item["content"]
            else:
                self.hidden_plot[item["plot"]] = item["content"]

        # For initialization
        send_clue_msg(
            None,
            unexposed_num=len(self.unexposed_clues),
            uid=self.uid,
            role=self.name,
        )
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
            logger.debug(f"plot {p}, {active_plots}")
            if (
                    p in self.hidden_plot and len(self.active_plots) == 0
            ):
                self.active_plots = [p]
            elif p in self.hidden_plot:
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
        self.prev_active_plots = [self.active_plots[0]]
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
        send_chat_msg("**speak**", role=self.name, uid=self.uid,
                      avatar=self.avatar)
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
                'preferred_info': self.preferred_info,
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
            [extract_keys_from_dict(message, MESSAGE_KEYS)],
            parse_func=_parse_score,
            fault_handler=_default_score,
            max_retries=3,
        )

        satisfied_str = "不满意"
        is_satisfied = False
        if self.relationship.is_satisfied(score):
            satisfied_str = "满意"
            is_satisfied = True
        text = satisfied_str + "，" + text

        prev_relationship = self.relationship.to_string()
        self.relationship.update(score)
        cur_relationship = self.relationship.to_string()
        chat_text = f" {SYS_MSG_PREFIX} {self.name}感觉{food}{satisfied_str}, "

        if prev_relationship != cur_relationship:
            chat_text += f"你们的关系从{prev_relationship}变得{cur_relationship}了"
        else:
            chat_text += f"你们的关系没变化，依旧是{prev_relationship}。"

        send_chat_msg(
            chat_text,
            uid=self.uid,
        )

        if is_satisfied or (
                score >= MIN_BAR_RECEIVED_CONST
                # and self.friendship >= MIN_BAR_FRIENDSHIP_CONST
        ):
            self.transition(CustomerConv.AFTER_MEAL_CHAT)
            print("---", self.cur_state)
        self.preorder_itr_count = 0

        return Msg(
            role="assistant",
            name=self.name,
            content=text,
            score=score,
            is_satisfied=is_satisfied,
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
                "hidden_plot": self.hidden_plot[self.active_plots[0]],
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

    def _preferred_food(self, x: dict) -> dict:
        walkin_msg = Msg(
            role="user",
            name=self.name,
            content=f"{self.name}走进餐厅...",
        )
        send_pretty_msg(
            walkin_msg,
            uid=self.uid,
            avatar=self.avatar,
        )
        send_chat_msg(
            "**speak**",
            role=self.name,
            uid=self.uid,
            avatar=self.avatar,
        )

        ingredients_dict = x['content']
        # breakpoint()
        ingredients_list = [
            item
            for sublist in ingredients_dict.values()
            for item in sublist
        ]
        ingredients = "、".join(ingredients_list)

        system_prompt = self.game_config["preferred_food_prompt"].format_map(
            {
                "name": self.config["name"],
                "food_preference": self.config["character_setting"][
                    "food_preference"],
                "ingredients": ingredients,
            },
        )
        system_msg = Msg(role="user", name="system", content=system_prompt)
        # prepare prompt
        prompt = self.engine.join(
            self._validated_history_messages(recent_n=HISTORY_WINDOW),
            system_msg)
        logger.debug(system_prompt)

        reply = self.model(replace_names_in_messages(prompt))
        self.preferred_info = reply
        reply_msg = Msg(role="assistant", name=self.name, content=reply)
        self.memory.add(reply_msg)
        return reply_msg

    def _pre_meal_chat(self, x: dict) -> dict:
        if "food" in x:
            return self._recommendation_to_score(x)

        return self._preferred_food(x)

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
        if self.prev_active_plots:
            plot = self.hidden_plot[self.prev_active_plots[0]]
        else:
            plot = "无"

        update_prompt = self.game_config["update_background"].format_map(
            {
                "background": self.background,
                "plot": plot,
                "name": self.name,
            },
        )
        update_msg = Msg(role="user", name="system", content=update_prompt)
        new_background = self.model(
            [extract_keys_from_dict(update_msg, MESSAGE_KEYS)]
        )

        bg_msg = f" {SYS_MSG_PREFIX}根据剧情，{self.name}的背景更新为：" + new_background
        send_chat_msg(bg_msg, uid=self.uid, flushing=True)

        self.background = new_background

    def _validated_history_messages(self, recent_n: int = 10):
        hist_mem = self.memory.get_memory(recent_n=recent_n)
        if len(hist_mem) > 0:
            hist_mem[0]["role"], hist_mem[-1]["role"] = "user", "user"
        return hist_mem

    def add_plot_done_memory(
            self,
            done_condition=None,
            main_role_names=[],
            is_player_done=False,
    ):
        if self.name in main_role_names:
            if not is_player_done:
                content = f"我是{self.name}，很遗憾餐馆老板没有帮助到我，但是我调查到了结果:" \
                          f" {done_condition}。"
            else:
                content = f"我是{self.name}，很高兴餐馆老板帮助我，很感谢老板的帮助，最后调查到了结果" \
                          f":{done_condition}。"
        else:
            if not is_player_done:
                content = f"我是{self.name}，很遗憾餐馆老板没有帮助到" \
                          f"{'、'.join(main_role_names)}解决问题，" \
                          f"但是在{'、'.join(main_role_names)}的努力下，事件得到揭露" \
                          f":{done_condition}。"
            else:
                content = f"我是{self.name}，很高兴在餐馆老板的努力下，事件得到揭露:{done_condition}。"

        msg = Msg(
            role="user",
            name=self.name,
            content=content,
        )
        self.memory.add(msg)

    def generate_pov_story(
            self,
            recent_n: int = 20,
    ) -> None:
        related_mem = self._validated_history_messages(recent_n)
        conversation = ""
        for mem in related_mem:
            if "name" in mem:
                conversation += mem["name"] + ": " + mem["content"]
            else:
                conversation += "背景" + ": " + mem["content"]
        background = self.background

        background += self.hidden_plot[self.prev_active_plots[0]]
        logger.debug(background)

        pov_prompt = self.game_config["pov_story"].format_map(
            {
                "name": self.name,
                "background": background,
                "conversation": conversation,
            },
        )
        msg = Msg(name="system", role="user", content=pov_prompt)
        send_chat_msg(
            "**speak**",
            role=self.name,
            uid=self.uid,
            avatar=self.avatar, )
        pov_story = self.model(
            [extract_keys_from_dict(msg, MESSAGE_KEYS)]
        )
        send_story_msg(pov_story, role=self.name, uid=self.uid)
        print("*" * 20)
        send_chat_msg(
            pov_story,
            role=self.name,
            uid=self.uid,
            avatar=self.avatar,
        )
        print("*" * 20)
        send_chat_msg(
            f"{SYS_MSG_PREFIX}💡发现{self.name}的新故事（请查看故事栏）。",
            uid=self.uid)

    def _gen_plot_related_prompt(self) -> str:
        """
        generate prompt depending on the state and friendship of the customer
        """
        prompt = self.game_config["basic_background_prompt"].format_map(
            {
                "name": self.config["name"],
                "character_description": self.background,
            },
        )

        if (
                self.plot_stage == CustomerPlot.ACTIVE
        ):
            # get the clues related to the current plot
            hidden_plot_list = self._relation_to_clues()
            hidden_plot = "/n".join([c["content"] for c in hidden_plot_list])
            # -> prompt for the main role in the current plot
            prompt += self.game_config["hidden_main_plot_prompt"].format_map(
                {
                    "hidden_plot": hidden_plot,
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
        logger.debug(prompt)
        return prompt

    def _relation_to_clues(self):
        curr_clues = []
        for c in self.all_clues:
            if c["plot"] == self.active_plots[0]:
                curr_clues.append(c)
        if self.relationship.is_max():
            logger.debug(f"reveal clue to: all")
            clues = [c for c in curr_clues]
        else:
            end_idx = len(curr_clues) // 3 * \
                      self.relationship.level.value
            logger.debug(f"reveal clue to: {end_idx}")
            clues = [c for c in curr_clues[:end_idx]]
            logger.debug(f"reveal clues: {[c['name'] for c in clues]}")

        return clues

    def talk(self, content, is_display=True, flushing=True):
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
                    flushing=flushing,
                )
            return msg

    def update_clues(self, content):

        if len(self.unexposed_clues) == 0:
            return

        # only reveal active clues
        curr_clues = self._relation_to_clues()
        curr_clues_name = [c['name'] for c in curr_clues]
        curr_unexposed_clues = []
        curr_to_unexpo_idx = {}
        for idx, x in enumerate(self.unexposed_clues):
            if x['name'] in curr_clues_name:
                curr_unexposed_clues.append(x)
                curr_to_unexpo_idx[len(curr_unexposed_clues) - 1] = idx

        prompt = self.game_config["clue_detect_prompt"].format_map(
            {
                "content": content,
                "clue": curr_unexposed_clues,
                "name": self.name,
            }
        )

        message = Msg(name="system", content=prompt, role="user")
        exposed_clues = self.model(
            [extract_keys_from_dict(message, MESSAGE_KEYS)],
            parse_func=json.loads,
            fault_handler=lambda response: [],
            max_retries=self.retry_time,
        )

        logger.debug(exposed_clues)
        logger.debug(self.unexposed_clues)
        indices_to_pop = []
        found_clue = []
        if not isinstance(exposed_clues, list):
            return

        for clue in exposed_clues:
            if not isinstance(clue, dict):
                continue
            clue_index = clue.get("index", -1)
            if clue_index not in curr_to_unexpo_idx:
                continue
            index = curr_to_unexpo_idx[clue.get("index", -1)]
            summary = clue.get("summary", -1)
            if len(self.unexposed_clues) > index >= 0:
                indices_to_pop.append(index)
                # TODO: get index and summary separately can be more stable
                found_clue.append(
                    {
                        "name": self.unexposed_clues[index]["name"],
                        "summary": summary,  # Use new summary
                        "image": get_clue_image_b64_url(
                            customer=self.name,
                            clue_name=self.unexposed_clues[index]["name"],
                            uid=self.uid,
                            content=summary,
                        )
                    }
                )
        indices_to_pop.sort(reverse=True)
        logger.debug(indices_to_pop)
        for index in indices_to_pop:
            element = self.unexposed_clues.pop(index)
            self.exposed_clues.append(element)

        for i, clue in enumerate(found_clue):
            send_chat_msg(
                f"{SYS_MSG_PREFIX}💡发现{self.name}的新线索（请查看线索栏）："
                f"《{clue['name']}》{clue['summary']} "
                f"\n\n剩余未发现线索数量:"
                f"{len(self.unexposed_clues) + len(found_clue) - i - 1}",
                uid=self.uid)
            send_clue_msg(
                clue,
                unexposed_num=len(self.unexposed_clues),
                uid=self.uid,
                role=self.name,
            )

    def expose_all_clues(self, plot):
        send_chat_msg(
            f"{SYS_MSG_PREFIX}💡成功解锁 {self.name} "
            f"的所有线索，请查看线索栏（画面生成可能存在延迟，请耐心等待）。",
            uid=self.uid)
        indices_to_pop = []
        for i, item in enumerate(self.unexposed_clues):
            if item["plot"] == plot:
                indices_to_pop.append(i)

        indices_to_pop.sort(reverse=True)
        for index in indices_to_pop:
            element = self.unexposed_clues.pop(index)
            self.exposed_clues.append(element)
            clue = {
                "name": element["name"],
                "summary": element["content"],  # Use new summary
                "image": get_clue_image_b64_url(
                    customer=self.name,
                    clue_name=element["name"],
                    uid=self.uid,
                    content=element["content"],
                    use_assets=True,
                )
            }
            send_clue_msg(
                clue,
                unexposed_num=len(self.unexposed_clues),
                uid=self.uid,
                role=self.name,
            )

    def expose_one_clue(self):
        if len(self.active_plots) > 0:
            plot = self.active_plots[0]
        else:
            return
        indices_to_pop = []
        curr_clues = self._relation_to_clues()
        curr_clue_names = set([c["name"] for c in curr_clues])
        for i, item in enumerate(self.unexposed_clues):
            if item["plot"] == plot and item["name"] in curr_clue_names:
                indices_to_pop.append(i)
        logger.debug(f"clues can be random exposed"
                     f"{[self.unexposed_clues[i]['name'] for i in indices_to_pop]}")

        indices_to_pop.sort(reverse=True)

        element = self.unexposed_clues.pop(indices_to_pop[-1])
        self.exposed_clues.append(element)
        clue = {
            "name": element["name"],
            "summary": element["content"],  # Use new summary
            "image": get_clue_image_b64_url(
                customer=self.name,
                clue_name=element["name"],
                uid=self.uid,
                content=element["content"],
            )
        }
        # generate prompt to adjust for random plot reveal
        expose_clue_prompt = self.game_config[
            "random_clue_expose_prompt"].format_map({
            "name": self.name,
            "background": self.background,
            "clue": element["content"],
        })
        msg = Msg(
            role="user",
            name="user",
            content=expose_clue_prompt,
        )
        logger.debug([extract_keys_from_dict(msg, MESSAGE_KEYS)])
        expose_talk = self.model(
            [extract_keys_from_dict(msg, MESSAGE_KEYS)],
            # parse_func=json.loads,
            # fault_handler=lambda _: {"talk": ""},
            # max_retries=self.retry_time,
        )

        send_chat_msg(
            expose_talk,
            role=self.name,
            uid=self.uid,
            avatar=self.avatar
        )

        msg = Msg(role="user", name=self.name, content=expose_clue_prompt,)
        self.memory.add(msg)

        # system notification
        send_chat_msg(
            f"{SYS_MSG_PREFIX}💡成功解锁 {self.name} 的一条随机线索，请查看线索栏。",
            uid=self.uid)
        send_clue_msg(
            clue,
            unexposed_num=len(self.unexposed_clues),
            uid=self.uid,
            role=self.name,
        )
