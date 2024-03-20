# -*- coding: utf-8 -*-
"""Prompt engineering module."""
from typing import Any, Optional, Union, List
from enum import IntEnum

from agentscope.models import OpenAIWrapperBase, ModelWrapperBase
from agentscope.utils.tools import to_openai_dict, to_dialog_str


class PromptType(IntEnum):
    """Enum for prompt types."""

    STRING = 0
    LIST = 1


class OpenAIFormatter:
    @classmethod
    def to_prompt(cls, unit: Any):
        if isinstance(unit, str):
            return cls.str_to_prompt(unit)
        elif isinstance(unit, dict):
            return cls.dict_to_prompt(unit)
        else:
            raise TypeError(
                f"Prompt unit should be a string or a dictionary, but got {type(unit)}"
            )

    @classmethod
    def str_to_prompt(cls, index: int, unit: str):
        return {"role": "assistant", "content": unit}




    @classmethod
    def dict_to_prompt(cls, index: int, unit: dict):
        # Content field
        if "content" not in unit:
            return {"role": "assistant", "content": str(unit)}

        # Role field
        openai_msg = {}
        if "role" in unit:
            openai_msg["role"] = unit["role"]
        else:
            # Set role according to name, which requires the name to be
            # strictly "user", "system" or "assistant", otherwise, the role
            # will be set to "assistant" by default.
            if "name" in unit:
                unit_name = str(unit["name"]).lower()
                if unit_name == "user":
                    openai_msg["role"] = "user"
                elif unit_name == "system":
                    openai_msg["role"] = "system"
                elif unit_name == "assistant":
                    openai_msg["role"] = "assistant"

        # Name field
        if "name" in unit:
            openai_msg["name"] = unit["name"]


class DashScopeFormatter:
    _version: str = "2024/03/20"

    roles: List[str] = ["system", "user", "assistant", "tool"]

    contents:




    @classmethod
    def str_to_prompt(cls, index: int, unit: str):
        return {"content": unit}

    @classmethod
    def dict_to_prompt(self, index: int, unit: str):



class PromptEngine:
    """A module that combines (a list of) dicts, strings, into a
    prompt with specified format.

    Note:
        It's challenging to fit different prompt requirements of different
        models in a single module. Therefore, this prompt engine only
        provide several basic strategies, and the user should be
        aware of and handle the prompt requirements of the target model.

    First, users should ensure the final prompt format is a string or a list
    of dictionaries. We provide two interfaces to transfer the input units to
    the target format, which are `dict_to_prompt`, and `str_to_prompt`.

    If the input unit is a dictionary, it will be processed by
    `dict_to_prompt` function. If the input unit is a string, it will be
    processed by `str_to_prompt` function.
    """

    def __init__(
        self,
        model: ModelWrapperBase,
    ) -> None:
        """

        Args:
            model (`ModelWrapperBase`):
                The target model for prompt engineering.

        Note:
            1. TODO: Shrink function is still under development.
            2. If the argument `max_length` and `prompt_type` are not given,
            they will be set according to the given model.
            3. `shrink_policy` is used when the prompt is too long, it can
            be set to `ShrinkPolicy.TRUNCATE` or `ShrinkPolicy.SUMMARIZE`.
                a. `ShrinkPolicy.TRUNCATE` will truncate the prompt to the
                desired length.
                b. `ShrinkPolicy.SUMMARIZE` will summarize partial of the
                dialog history to save space. The summarization model
                defaults to `model` if not given.

        Example:
            With prompt engine, we encapsulate different operations for
            string- and list-style prompt, and block the prompt engineering
            process from the user.
            As a user, you can just combine you prompt as follows.

            ```python
            # prepare the component
            system_prompt = "You're a helpful assistant ..."
            hint_prompt = "You should response in Json format."
            prefix = "assistant: "

            # initialize the prompt engine and join the prompt
            engine = PromptEngine(model)
            prompt = engine.join(system_prompt, memory.get_memory(),
            hint_prompt, prefix)
            ```
        """
        self.model = model
        self.shrink_policy = shrink_policy
        self.max_length = max_length or model.max_length

        if prompt_type is None:
            if isinstance(model, OpenAIWrapperBase):
                self.prompt_type = PromptType.LIST
            else:
                self.prompt_type = PromptType.STRING
        else:
            self.prompt_type = prompt_type

        self.max_summary_length = max_summary_length

        if summarize_model is None:
            self.summarize_model = model

    def join(
        self,
        *args: Any,
        format_map: Optional[dict] = None,
    ) -> Union[str, list[dict]]:
        """Join prompt components according to its type. The join function can
        accept any number and type of arguments. If prompt type is
        `PromptType.STRING`, the arguments will be joined by `"\\\\n"`. If
        prompt type is `PromptType.LIST`, the string arguments will be
        converted to `Msg` from `system`.
        """
        # TODO: achieve the summarize function

        # Filter `None`
        args = [_ for _ in args if _ is not None]

        if isinstance(self.model, OpenAIWrapperBase):
            for
            prompt_unit = OpenAIFormatter.str_to_prompt()


    def join_to_str(self, *args: Any, format_map: Union[dict, None]) -> str:
        """Join prompt components to a string."""
        prompt = []
        for item in args:
            if isinstance(item, list):
                items_str = self.join_to_str(*item, format_map=None)
                prompt += [items_str]
            elif isinstance(item, dict):
                prompt.append(to_dialog_str(item))
            else:
                prompt.append(str(item))
        prompt_str = "\n".join(prompt)

        if format_map is not None:
            prompt_str = prompt_str.format_map(format_map)

        return prompt_str

    def join_to_list(self, *args: Any, format_map: Union[dict, None]) -> list:
        """Join prompt components to a list of `Msg` objects."""
        prompt = []
        for item in args:
            if isinstance(item, list):
                # nested processing
                prompt.extend(self.join_to_list(*item, format_map=None))
            elif isinstance(item, dict):
                prompt.append(to_openai_dict(item))
            else:
                prompt.append(to_openai_dict({"content": str(item)}))

        if format_map is not None:
            format_prompt = []
            for msg in prompt:
                format_prompt.append(
                    {
                        k.format_map(format_map): v.format_map(format_map)
                        for k, v in msg.items()
                    },
                )
            prompt = format_prompt

        return prompt
