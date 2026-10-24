# -*- coding: utf-8 -*-
"""Regression tests: a per-call ``dimensions`` must override the instance
default on the OpenAI embedding path.

``EmbeddingModelBase.__call__`` documents ``**kwargs`` as options forwarded
to the provider call, and the OpenAI embeddings API takes ``dimensions`` as
a standard per-request parameter (the sibling providers honor it per call:
``GeminiEmbeddingModel`` routes ``output_dimensionality`` and
``OllamaEmbeddingModel``/``DashScopeEmbeddingModel`` merge their instance
``dimension`` *before* ``**kwargs``).

``OpenAIEmbeddingModel._call_api`` instead spreads ``**kwargs`` first and
then overwrites the key — ``api_kwargs["dimensions"] = self.dimensions`` —
so with the default ``pass_dimensions=True`` a per-call ``dimensions`` is
silently discarded and the request is sent with the instance value.
"""
import json
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import httpx
import openai

from agentscope.credential import OpenAICredential
from agentscope.embedding import OpenAIEmbeddingModel


class _Recorder:
    """Capture embedding requests and answer with a canned payload."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": "text-embedding-3-small",
                "data": [
                    {"object": "embedding", "index": 0, "embedding": [0.1]},
                ],
                "usage": {"prompt_tokens": 1, "total_tokens": 1},
            },
        )


def _make_model(**kwargs: Any) -> OpenAIEmbeddingModel:
    return OpenAIEmbeddingModel(
        credential=OpenAICredential(api_key="test-key"),
        model="text-embedding-3-small",
        dimensions=2,
        max_retries=0,
        **kwargs,
    )


class OpenAIEmbeddingPerCallDimensionsTest(IsolatedAsyncioTestCase):
    """The instance ``dimensions`` is a default, not a floor."""

    async def test_per_call_dimensions_wins(self) -> None:
        """``model(["x"], dimensions=3)`` must send 3, not the instance 2."""
        recorder = _Recorder()
        async with openai.AsyncClient(
            api_key="test-key",
            base_url="https://embedding.invalid/v1",
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(recorder.handler),
            ),
            max_retries=0,
        ) as client:
            with patch("openai.AsyncClient", return_value=client):
                model = _make_model()

            await model(["hello"], dimensions=3)

        self.assertEqual(len(recorder.requests), 1)
        self.assertEqual(recorder.requests[0].get("dimensions"), 3)

    async def test_instance_dimensions_is_the_default(self) -> None:
        """Without a per-call override the instance value is sent."""
        recorder = _Recorder()
        async with openai.AsyncClient(
            api_key="test-key",
            base_url="https://embedding.invalid/v1",
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(recorder.handler),
            ),
            max_retries=0,
        ) as client:
            with patch("openai.AsyncClient", return_value=client):
                model = _make_model()

            await model(["hello"])

        self.assertEqual(len(recorder.requests), 1)
        self.assertEqual(recorder.requests[0].get("dimensions"), 2)

    async def test_pass_dimensions_false_still_forwards_per_call(self) -> None:
        """With ``pass_dimensions=False`` only a per-call value is sent."""
        recorder = _Recorder()
        async with openai.AsyncClient(
            api_key="test-key",
            base_url="https://embedding.invalid/v1",
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(recorder.handler),
            ),
            max_retries=0,
        ) as client:
            with patch("openai.AsyncClient", return_value=client):
                model = _make_model(pass_dimensions=False)

            await model(["hello"], dimensions=3)

        self.assertEqual(len(recorder.requests), 1)
        self.assertEqual(recorder.requests[0].get("dimensions"), 3)

    async def test_pass_dimensions_false_omits_the_parameter(self) -> None:
        """No instance default and no per-call value means no parameter."""
        recorder = _Recorder()
        async with openai.AsyncClient(
            api_key="test-key",
            base_url="https://embedding.invalid/v1",
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(recorder.handler),
            ),
            max_retries=0,
        ) as client:
            with patch("openai.AsyncClient", return_value=client):
                model = _make_model(pass_dimensions=False)

            await model(["hello"])

        self.assertEqual(len(recorder.requests), 1)
        self.assertNotIn("dimensions", recorder.requests[0])
