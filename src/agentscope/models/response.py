# -*- coding: utf-8 -*-
"""Parser for model response."""
import inspect
import json
from typing import Optional, Sequence, Any, Callable

from loguru import logger

from agentscope.utils.tools import _is_json_serializable


class ModelResponse:
    """Encapsulation of data returned by the model.

    The main purpose of this class is to align the return formats of different
    models and act as a bridge between models and agents.
    """

    text: Optional[str] = None
    embedding: Optional[Sequence] = None
    raw: Optional[Any] = None
    image_urls: Optional[Sequence[str]] = None
    json: Optional[Any] = None

    def __init__(
        self,
        text: str = None,
        embedding: Sequence = None,
        image_urls: Sequence[str] = None,
        raw: Any = None,
    ) -> None:
        """Initialize the model response.

        Args:
            text (`str`, optional):
                The text field.
            embedding (`Sequence`, optional):
                The embedding returned by the model.
            image_urls (`Sequence[str]`, optional):
                The image URLs returned by the model.
            raw (`Any`, optional):
                The raw data returned by the model.
        """
        self.text = text
        self.embedding = embedding
        self.image_urls = image_urls
        self.raw = raw

    def __str__(self) -> str:
        if _is_json_serializable(self.raw):
            raw = self.raw
        else:
            raw = str(self.raw)

        serialized_fields = {
            "text": self.text,
            "embedding": self.embedding,
            "image_urls": self.image_urls,
            "json": self.json,
            "raw": raw,
        }
        return json.dumps(serialized_fields, indent=4, ensure_ascii=False)


class ResponseParser:
    """A class that contains several static methods to parse the response."""

    @classmethod
    def to_dict(cls, response: ModelResponse) -> ModelResponse:
        """Parse the response text to a dict, and feed it into the `json`
        field."""
        text = response.text
        if text is not None:
            logger.debug("Text before parsing", text)

            # extract from the first '{' to the last '}'
            index_start = max(text.find("{"), 0)
            index_end = min(text.rfind("}") + 1, len(text))

            text = text[index_start:index_end]
            logger.debug("Text after parsing", text)

            response.text = text
            response.json = json.loads(text)
            return response
        else:
            raise ValueError(
                f"The text field of the model response is None: {response}",
            )

    @classmethod
    def to_list(cls, response: ModelResponse) -> ModelResponse:
        """Parse the response text to a list, and feed it into the `json`
        field."""
        text = response.text
        if text is not None:
            logger.debug("Text before parsing", text)

            # extract from the first '{' to the last '}'
            index_start = max(text.find("["), 0)
            index_end = min(text.rfind("]") + 1, len(text))

            text = text[index_start:index_end]
            logger.debug("Text after parsing", text)

            response.text = text
            response.json = json.loads(text)
            return response
        else:
            raise ValueError(
                f"The text field of the model response is None: {response}",
            )


class ResponseParsingError(Exception):
    """Exception raised when parsing the response fails."""

    parse_func: str
    """The source code of the parsing function."""

    error_info: str
    """The detail information of the error."""

    response: ModelResponse
    """The response that fails to be parsed."""

    def __init__(
        self,
        *args: Any,
        parse_func: Callable,
        error_info: str,
        response: ModelResponse,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception.

        Args:
            parse_func (`str`):
                The source code of the parsing function.
            error_info (`str`):
                The detail information of the error.
            response (`ModelResponse`):
                The response that fails to be parsed.
        """
        super().__init__(*args, **kwargs)

        self.parse_func_code = inspect.getsource(parse_func)
        self.error_info = error_info
        self.response = response

    def __str__(self) -> str:
        return (
            f"Fail to parse response with the following parsing function:\n"
            f"## PARSE FUNCTION: \n"
            f"```python\n"
            f"{self.parse_func_code}"
            f"```\n\n"
            f"## ERROR INFO: \n"
            f"{self.error_info}\n\n"
            f"## INPUT RESPONSE: \n"
            f"{self.response}"
        )
