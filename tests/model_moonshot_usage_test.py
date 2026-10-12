# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Unit tests for the cache-token accounting of ``MoonshotChatModel``.

Kimi reports cached prompt tokens as ``usage.prompt_tokens_details.
cached_tokens``, which the OpenAI SDK parses into the nested
``PromptTokensDetails`` model. The fixtures below are therefore real
SDK objects validated from documented Kimi payloads instead of
``MagicMock`` instances, so an attribute the SDK never defines cannot
silently appear on the fixture.
"""
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from openai.types.chat import ChatCompletion, ChatCompletionChunk
from utils import AnyValue

from agentscope.credential import MoonshotCredential
from agentscope.model import MoonshotChatModel


def _expected_usage(cache_input_tokens: int) -> dict[str, Any]:
    """The whole ``ChatUsage`` a Kimi response should report."""
    return {
        "input_tokens": 1000,
        "output_tokens": 20,
        "time": AnyValue(),
        "cache_creation_input_tokens": 0,
        "cache_input_tokens": cache_input_tokens,
        "type": "chat",
        "metadata": None,
    }


KIMI_USAGE_WITH_CACHE: dict[str, Any] = {
    "prompt_tokens": 1000,
    "completion_tokens": 20,
    "total_tokens": 1020,
    "prompt_tokens_details": {"cached_tokens": 832},
}

KIMI_USAGE_WITHOUT_DETAILS: dict[str, Any] = {
    "prompt_tokens": 1000,
    "completion_tokens": 20,
    "total_tokens": 1020,
}


def _make_model(stream: bool = False) -> MoonshotChatModel:
    """Build a model instance with a placeholder key."""
    return MoonshotChatModel(
        credential=MoonshotCredential(api_key="test"),
        model="kimi-k2-5",
        stream=stream,
        context_size=131_072,
    )


def _make_completion(usage: dict[str, Any]) -> ChatCompletion:
    """Build a non-streaming Kimi response from its wire payload."""
    return ChatCompletion.model_validate(
        {
            "id": "kimi-1",
            "object": "chat.completion",
            "created": 1,
            "model": "kimi-k2-5",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "Hi"},
                },
            ],
            "usage": usage,
        },
    )


def _make_text_chunk() -> ChatCompletionChunk:
    """Build a streamed text delta chunk."""
    return ChatCompletionChunk.model_validate(
        {
            "id": "kimi-2",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "kimi-k2-5",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": "Hi"},
                },
            ],
        },
    )


def _make_usage_chunk(usage: dict[str, Any]) -> ChatCompletionChunk:
    """Build the trailing usage-only chunk Kimi emits."""
    return ChatCompletionChunk.model_validate(
        {
            "id": "kimi-2",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "kimi-k2-5",
            "choices": [],
            "usage": usage,
        },
    )


class _MockAsyncStream:
    """Mock async stream (context manager + async iterator)."""

    def __init__(self, chunks: list) -> None:
        self._chunks = chunks
        self._index = 0

    async def __aenter__(self) -> "_MockAsyncStream":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    def __aiter__(self) -> "_MockAsyncStream":
        return self

    async def __anext__(self) -> Any:
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk


class TestMoonshotCacheTokens(IsolatedAsyncioTestCase):
    """Kimi cached tokens must reach ``ChatUsage.cache_input_tokens``."""

    def setUp(self) -> None:
        """Prepare a model with a mocked OpenAI-compatible client."""
        self.model = _make_model()
        self.mock_client = MagicMock()
        self.model.client = self.mock_client

    async def test_non_stream_cached_tokens(self) -> None:
        """A documented Kimi payload reports its cached prompt tokens."""
        self.mock_client.chat.completions.create = AsyncMock(
            return_value=_make_completion(KIMI_USAGE_WITH_CACHE),
        )

        res = await self.model([])

        self.assertEqual(dict(res.usage), _expected_usage(832))

    async def test_stream_cached_tokens(self) -> None:
        """The streaming path reports the same cached prompt tokens."""
        self.model = _make_model(stream=True)
        self.model.client = self.mock_client
        self.mock_client.chat.completions.create = AsyncMock(
            return_value=_MockAsyncStream(
                [
                    _make_text_chunk(),
                    _make_usage_chunk(KIMI_USAGE_WITH_CACHE),
                ],
            ),
        )

        gen = await self.model([])
        responses = [r async for r in gen]

        self.assertEqual(len(responses), 2)
        self.assertEqual(dict(responses[-1].usage), _expected_usage(832))

    async def test_non_stream_without_prompt_tokens_details(self) -> None:
        """A payload without the nested details object still accounts."""
        self.mock_client.chat.completions.create = AsyncMock(
            return_value=_make_completion(KIMI_USAGE_WITHOUT_DETAILS),
        )

        res = await self.model([])

        self.assertEqual(dict(res.usage), _expected_usage(0))
