# -*- coding: utf-8 -*-
import time
import json
import random
from enum import Enum
from typing import Optional, Union, Any, Callable

import inquirer
from loguru import logger

from agentscope.agents import AgentBase
from agentscope.message import Msg


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


class RuledUser(AgentBase):
    """User agent under rules"""

    def __init__(
        self,
        name: str = "User",
        model: Optional[Union[Callable[..., Any], str]] = None,
        sys_prompt: Optional[str] = None,
        ingredients_dict: Optional[dict] = None,
        cook_prompt: Optional[str] = None,
    ) -> None:
        """Initialize a RuledUser object."""
        super().__init__(name=name, model=model, sys_prompt=sys_prompt)
        self.retry_time = 10
        self.ingredients_dict = ingredients_dict
        self.cook_prompt = cook_prompt

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
                content = input(f"{self.name}: ")

                if not hasattr(self, "model") or len(content) == 0:
                    break

                ruler_res = self.is_content_valid(content)
                if ruler_res.get("allowed") == "true":
                    break

                logger.warning(
                    f"Input is not allowed:"
                    f" {ruler_res.get('reason', 'Unknown reason')} "
                    f"【Please retry】",
                )
            except Exception as e:
                logger.warning(f"Input invalid: {e}. Please try again.")

        kwargs = {}
        if required_keys is not None:
            if isinstance(required_keys, str):
                required_keys = [required_keys]

            for key in required_keys:
                kwargs[key] = input(f"{key}: ")

        if content == "做菜":
            content = self.cook()
            kwargs["food"] = content

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
            messages=[message],
            parse_func=json.loads,
            max_retries=self.retry_time,
        )
        return ruler_res

    def set_ingredients(self, ingredients_dict):
        self.ingredients_dict = ingredients_dict

    def cook(self):
        ingredients_list = [
            item
            for sublist in self.ingredients_dict.values()
            for item in sublist
        ]

        ingredients_list = ["*清空*", "*结束*"] + ingredients_list
        cook_list = []
        questions = [
            inquirer.List(
                "ingredient",
                message="以下是今天拥有的食材是，请选择您需要使用的食材，完成后按回车键",
                choices=ingredients_list,
            ),
        ]
        while True:
            print(f"【系统】当前已选择的食材是{cook_list}。")
            sel_ingr = inquirer.prompt(questions)["ingredient"]

            if sel_ingr == "*结束*":
                if len(cook_list) > 0:
                    break
                print("【系统】你的魔法锅空空如也。")
            elif sel_ingr == "*清空*":
                cook_list.clear()
            else:
                cook_list.append(sel_ingr)

        prompt = self.cook_prompt.format_map(
            {"ingredient": "+".join(cook_list)},
        )
        message = Msg(name="user", content=prompt, role="user")
        food = self.model(
            messages=[message],
            parse_func=json.loads,
            max_retries=self.retry_time,
        )

        random_quality = random.choice(list(FoodQuality)).value
        food = random_quality + food

        print(
            f"【系统】魔法锅周围光芒四射，你听到了轻微的咔哒声。" f"当一切平静下来，一道《{food}》出现在你眼前。",
        )

        return food
