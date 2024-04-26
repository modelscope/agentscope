# -*- coding: utf-8 -*-
"""Parser for model response."""
import json
from typing import Optional, Sequence, Any

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
    parsed: Optional[Any] = None

    def __init__(
        self,
        text: str = None,
        embedding: Sequence = None,
        image_urls: Sequence[str] = None,
        raw: Any = None,
        parsed: Any = None,
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
            parsed (`Any`, optional):
                The parsed data returned by the model.
        """
        self.text = text
        self.embedding = embedding
        self.image_urls = image_urls
        self.raw = raw
        self.parsed = parsed

    def __getattribute__(self, item: str) -> Any:
        """Warning for the deprecated json attribute."""
        if item == "json":
            logger.warning(
                "The json attribute in ModelResponse class is deprecated. Use"
                " parsed attribute instead.",
            )

        return super().__getattribute__(item)

    def __setattr__(self, key: str, value: Any) -> Optional[Any]:
        """Warning for the deprecated json attribute."""
        if key == "json":
            logger.warning(
                "The json attribute in ModelResponse class is deprecated. Use"
                " parsed attribute instead.",
            )

        return super().__setattr__(key, value)

    def __str__(self) -> str:
        if _is_json_serializable(self.raw):
            raw = self.raw
        else:
            raw = str(self.raw)

        serialized_fields = {
            "text": self.text,
            "embedding": self.embedding,
            "image_urls": self.image_urls,
            "parsed": self.parsed,
            "raw": raw,
        }
        return json.dumps(serialized_fields, indent=4, ensure_ascii=False)
