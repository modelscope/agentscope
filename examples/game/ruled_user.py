# -*- coding: utf-8 -*-
import time
import json
import random
from enum import Enum
from typing import Optional, Union, Any, Callable
from loguru import logger

import inquirer
import re

from agentscope.agents import AgentBase
from agentscope.message import Msg
from utils import (
    send_chat_msg,
    query_answer,
    get_player_input,
    ResetException,
    generate_picture,
    send_player_msg,
    SYS_MSG_PREFIX,
    extract_keys_from_dict,
)


class FoodQuality(Enum):
    DELICIOUS = "美味的"
    BURNT = "烧焦的"
    FRESH = "新鲜的"
    STALE = "不新鲜的"
    SPICY = "辣的"
    BLAND = "清淡的"
    SWEET = "甜的"
    SOUR = "酸的"
    BITTER = "苦的"
    SALTY = "咸的"
    SAVORY = "鲜美的"
    CRISPY = "脆的"
    TENDER = "嫩的"
    JUICY = "多汁的"
    RICH = "浓郁的"
    FRAGRANT = "香的"
    SMOKY = "烟熏味的"

MESSAGE_KEYS = ["name", "role", "content"]


class RuledUser(AgentBase):
    """User agent under rules"""

    def __init__(
        self,
        name: str = "User",
        model: Optional[Union[Callable[..., Any], str]] = None,
        sys_prompt: Optional[str] = None,
        ingredients_dict: Optional[dict] = None,
        cook_prompt: Optional[str] = None,
        success_detector_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a RuledUser object."""
        super().__init__(name=name, model=model, sys_prompt=sys_prompt)
        self.retry_time = 3
        self.ingredients_dict = ingredients_dict
        self.cook_prompt = cook_prompt
        self.success_detector_prompt = success_detector_prompt
        self.uid = kwargs.get("uid", None)

    def reply(
        self,
        x: dict = None,
        required_keys: Optional[Union[list[str], str]] = None,
    ) -> dict:
        """
        Processes the input provided by the user and stores it in memory,
        potentially formatting it with additional provided details.
        """
        if x is not None:
            self.memory.add(x)

        # TODO: To avoid order confusion, because `input` print much quicker
        #  than logger.chat
        time.sleep(0.5)
        while True:
            try:
                content = get_player_input(self.name, uid=self.uid)
                if x == {"content": "游戏开始"} and content == "":
                    send_chat_msg(f" {SYS_MSG_PREFIX}有顾客光临，请接待。", uid=self.uid)
                    continue
                elif isinstance(x, dict):
                    if x.get("content") == "今天老板邀请大家一起来聚聚。" and content == "":
                        content = "大家好"
                    elif x.get("content") == "自定义输入" and content == "":
                        content = "你好"

                if not hasattr(self, "model") or len(content) == 0:
                    break

                ruler_res = self.is_content_valid(content)
                if ruler_res.get("allowed") == "true":
                    break

                send_chat_msg(
                    f" {SYS_MSG_PREFIX}输入被规则禁止"
                    f" {ruler_res.get('reason', '未知原因')}\n"
                    f"请重试",
                    uid=self.uid,
                )
            except ResetException:
                raise
            except Exception as e:
                logger.debug(e)
                send_chat_msg(f" {SYS_MSG_PREFIX}无效输入，请重试！", uid=self.uid)

        kwargs = {}
        if required_keys is not None:
            if isinstance(required_keys, str):
                required_keys = [required_keys]

            for key in required_keys:
                kwargs[key] = get_player_input(key, uid=self.uid)

        # Add additional keys
        msg = Msg(
            self.name,
            role="user",
            content=content,
            **kwargs,  # type: ignore[arg-type]
        )

        # Add to memory
        self.memory.add(msg)

        return msg

    def is_content_valid(self, content):
        prompt = self.sys_prompt.format_map({"content": content})
        message = Msg(name="user", content=prompt, role="user")
        ruler_res = self.model(
            [extract_keys_from_dict(message, MESSAGE_KEYS)],
            parse_func=json.loads,
            fault_handler=lambda *_: {"allow": "false"},
            max_retries=self.retry_time,
        )
        return ruler_res

    def collect_mem_until_announcement(self, announcement):
        chat_log = []
        for i in range(self.memory.size() - 1, -1, -1):
            # TODO: avoid use `_content`
            if self.memory._content[i].get("content", None) == announcement.get("content"):
                break
            # TODO: avoid use `_content`
            chat_log.append(self.memory._content[i])
        chat_log.reverse()
        return chat_log

    def success_detector(self, condition, announcement):
        chat_log = self.collect_mem_until_announcement(announcement)
        chat_log = "\n".join([f"{d['name']}: {d['content']}" for d in chat_log])
        logger.debug(chat_log)
        prompt = self.success_detector_prompt.format_map(
            {
                "condition": condition,
                "chat_log": chat_log,
            }
        )
        message = Msg(name="user", content=prompt, role="user")
        success_res = self.model(
            [extract_keys_from_dict(message, MESSAGE_KEYS)],
            parse_func=json.loads,
            fault_handler=lambda *_: {"finish": "false"},
            max_retries=self.retry_time,
        )
        if success_res.get("finish") == "true":
            return True
        else:
            send_chat_msg(
                f" {SYS_MSG_PREFIX}未达成游戏完成条件，请继续加油！",
                uid=self.uid,
            )
            logger.debug(f"未达成游戏完成条件，{success_res.get('reason', '未知原因')}")
            return False

    def set_ingredients(self, ingredients_dict):
        self.ingredients_dict = ingredients_dict

    def cook(self):
        ingredients_list = [
            item
            for sublist in self.ingredients_dict.values()
            for item in sublist
        ]

        ingredients_list = ["跳过"] + ingredients_list

        cook_list = []
        questions = [
            inquirer.List(
                "ingredient",
                message="以下是今天拥有的食材是，请选择您需要使用的食材，完成后按回车键",
                choices=ingredients_list,
            ),
        ]

        choose_ingredient = f""" {SYS_MSG_PREFIX}请选择需要的食材: <select-box shape="card"
                     type="checkbox" item-width="auto"
                    options='{json.dumps(ingredients_list)}' select-once
                    submit-text="确定"></select-box>"""

        send_chat_msg(
            choose_ingredient,
            flushing=False,
            uid=self.uid,
        )
        while True:
            sel_ingr = query_answer(questions, "ingredient", uid=self.uid)
            if isinstance(sel_ingr, str):
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            cook_list = sel_ingr
            break
        send_chat_msg("**end_choosing**", uid=self.uid)

        print(cook_list)
        if "跳过" in cook_list:
            send_player_msg("不好意思，小店今天暂不接待。", uid=self.uid)
            return "跳过"

        prompt = self.cook_prompt.format_map(
            {"ingredient": "+".join(cook_list)},
        )
        message = Msg(name="user", content=prompt, role="user")
        food = self.model([extract_keys_from_dict(message, MESSAGE_KEYS)])
        food = re.sub(r'^[\'"`@!]+|[\'"`@!]+$', '', food)
        # random_quality = random.choice(list(FoodQuality)).value
        # food = random_quality + food
        picture_prompt = f"请根据菜品《{food}》, 生成一幅与之对应的色香味巨全，让人有食欲的图。"
        send_player_msg("**i_am_cooking**", uid=self.uid)
        picture_url = generate_picture(picture_prompt)
        send_player_msg(
            f" 撸袖挥勺，热浪腾空。一番烹饪后，一道《{food}》出现在客人眼前。"
            f"![image]({picture_url})",
            uid=self.uid,
        )

        return food

    def talk(self, content, is_display=False, ruled=False):
        if content is None:
            return None

        if ruled:
            ruler_res = self.is_content_valid(content)
            if ruler_res.get("allowed") != "true":
                send_chat_msg(
                    f"{SYS_MSG_PREFIX}输入被规则禁止"
                    f"{ruler_res.get('reason', '未知原因')}\n"
                    "请重试",
                    uid=self.uid,
                )
                return None

        msg = Msg(
            self.name,
            role="user",
            content=content,
        )
        self.memory.add(msg)

        if is_display:
            send_player_msg(content, uid=self.uid)

        return msg
