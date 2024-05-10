# -*- coding: utf-8 -*-
"""The base class for model response parser."""
from abc import ABC, abstractmethod
from typing import Union, Sequence

from loguru import logger

from agentscope.exception import TagNotFoundError
from agentscope.models import ModelResponse


class ParserBase(ABC):
    """The base class for model response parser."""

    @abstractmethod
    def parse(self, response: ModelResponse) -> ModelResponse:
        """Parse the response text to a specific object, and stored in the
        parsed field of the response object."""

    def _extract_first_content_by_tag(
        self,
        response: ModelResponse,
        tag_start: str,
        tag_end: str,
    ) -> str:
        """Extract the first text content between the tag_start and tag_end
        in the response text. Note this function does not support nested.

        Args:
            response (`ModelResponse`):
                The response object.
            tag_start (`str`):
                The start tag.
            tag_end (`str`):
                The end tag.

        Returns:
            `str`: The extracted text content.
        """
        text = response.text

        index_start = text.find(tag_start)

        # Avoid the case that tag_begin contains tag_end, e.g. ```json and ```
        if index_start == -1:
            index_end = text.find(tag_end, 0)
        else:
            index_end = text.find(tag_end, index_start + len(tag_start))

        if index_start == -1 or index_end == -1:
            missing_tags = []
            if index_start == -1:
                missing_tags.append(tag_start)
            if index_end == -1:
                missing_tags.append(tag_end)

            raise TagNotFoundError(
                f"Missing "
                f"tag{'' if len(missing_tags)==1 else 's'} "
                f"{' and '.join(missing_tags)} in response: {text}",
                raw_response=text,
                missing_begin_tag=index_start == -1,
                missing_end_tag=index_end == -1,
            )

        extract_text = text[
            index_start + len(tag_start) : index_end  # noqa: E203
        ]

        return extract_text


class _DictFilterMixin:
    """A mixin class to filter the parsed response by keys. It allows users
    to set keys to be filtered during speaking, storing in memory, and
    returning in the agent reply function.
    """

    def __init__(
        self,
        keys_to_memory: Union[str, Sequence[str]],
        keys_to_content: Union[str, Sequence[str]],
        keys_to_control: Union[str, Sequence[str]],
    ) -> None:
        """Initialize the mixin class with the keys to be filtered during
        speaking, storing in memory, and returning in the agent reply function.

        Args:
            keys_to_memory (`Union[str, Sequence[str]]`):
                The key or keys to be filtered during storing in memory. If
                a single key is provided, the corresponding value will be
                returned. Otherwise, a filtered dictionary will be returned.
            keys_to_content (`Union[str, Sequence[str]]`):
                The key or keys that will be exposed to other agents in the
                returned message content field. If a single key is provided,
                the corresponding value will be returned. Otherwise, a filtered
                dictionary will be returned.
            keys_to_control (`Union[str, Sequence[str]]`):
                The key or keys that will be fed into the returned message
                object, it will be used to control the application workflow but
                not exposed to other agents.
        """
        self.keys_to_memory = keys_to_memory
        self.keys_to_content = keys_to_content
        self.keys_to_control = keys_to_control

    def to_memory(
        self,
        parsed_response: dict,
        allow_missing: bool = False,
    ) -> Union[str, dict]:
        """Filter the fields that will be stored in memory."""
        return self._filter_content_by_names(
            parsed_response,
            self.keys_to_memory,
            allow_missing=allow_missing,
        )

    def to_content(
        self,
        parsed_response: dict,
        allow_missing: bool = False,
    ) -> Union[str, dict]:
        """Filter the fields that will be fed into the content field in the
        returned message, which will be exposed to other agents.
        """
        return self._filter_content_by_names(
            parsed_response,
            self.keys_to_content,
            allow_missing=allow_missing,
        )

    def to_control(
        self,
        parsed_response: dict,
        allow_missing: bool = False,
    ) -> Union[str, dict]:
        """Filter the fields that will be fed into the returned message
        directly to control the application workflow."""
        return self._filter_content_by_names(
            parsed_response,
            self.keys_to_control,
            allow_missing=allow_missing,
        )

    def _filter_content_by_names(
        self,
        parsed_response: dict,
        keys: Union[str, Sequence[str]],
        allow_missing: bool = False,
    ) -> Union[str, dict]:
        """Filter the parsed response by keys. If only one key is provided, the
        returned content will be a single corresponding value. Otherwise,
        the returned content will be a dictionary with the filtered keys and
        their corresponding values.

        Args:
            keys (`Union[str, Sequence[str]]`):
                The key or keys to be filtered. If a single key
                is provided, the parsed response will be filtered by the key,
                and the corresponding value will be returned. Otherwise, the
                parsed response will be filtered by the keys, and the
                corresponding values will be returned as a dictionary.
            allow_missing (`bool`, defaults to `False`):
                Whether to allow missing keys in the response. If set to
                `True`, the method will skip the missing keys in the response.
                Otherwise, it will raise a `ValueError` when a key is missing.

        Returns:
            `Union[str, dict]`: The filtered content.
        """
        if keys is None:
            return parsed_response

        if isinstance(keys, str):
            return parsed_response[keys]

        # check if the required names are in the response
        for name in keys:
            if name not in parsed_response:
                if allow_missing:
                    logger.warning(
                        f"Content name {name} not found in the response. Skip "
                        f"it.",
                    )
                else:
                    raise ValueError(f"Name {name} not found in the response.")
        return {
            name: parsed_response[name]
            for name in keys
            if name in parsed_response
        }
