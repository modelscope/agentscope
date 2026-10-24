# -*- coding: utf-8 -*-
"""Regression tests: a per-call ``api_key`` must override the instance
credential on the DashScope text embedding path.

``EmbeddingModelBase.__call__`` documents ``**kwargs`` as "Additional
keyword arguments forwarded to ``_call_api``", and
``DashScopeEmbeddingModel._call_text`` documents its ``**kwargs`` as
"Forwarded to the API" — the DashScope SDK's ``TextEmbedding.call``
takes ``api_key`` as its standard per-request parameter.

The multimodal twin (``_call_multimodal``) merges the instance key into
``api_kwargs`` *before* ``**kwargs``, so a per-call ``api_key`` cleanly
overrides it.  The text path instead passes ``api_key=self.api_key`` as
an explicit keyword *next to* ``**api_kwargs`` — so a per-call
``api_key`` arrives twice and the SDK call raises
``TypeError: got multiple values for keyword argument 'api_key'``
instead of honoring the override.
"""
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from embedding_dashscope_test import _cred, _img, _text_resp

from agentscope.embedding import DashScopeEmbeddingModel


class DashScopePerCallApiKeyTest(IsolatedAsyncioTestCase):
    """The text and multimodal paths must both honor a per-call key."""

    @patch("dashscope.embeddings.TextEmbedding.call")
    async def test_text_call_honors_per_call_api_key(
        self,
        mock_api: Any,
    ) -> None:
        """``model(["x"], api_key=...)`` must reach the SDK once, winning."""
        mock_api.return_value = _text_resp([[0.1, 0.2]], 12)
        model = DashScopeEmbeddingModel(
            credential=_cred(),
            model="text-embedding-v4",
            dimensions=2,
        )

        await model(["hello"], api_key="sk-per-call")

        self.assertEqual(mock_api.call_count, 1)
        self.assertEqual(
            mock_api.call_args.kwargs["api_key"],
            "sk-per-call",
        )

    @patch("dashscope.MultiModalEmbedding.call")
    async def test_multimodal_call_honors_per_call_api_key(
        self,
        mock_api: Any,
    ) -> None:
        """Control: the multimodal twin already overrides correctly."""

        def _resp(**kwargs: Any) -> MagicMock:
            resp = MagicMock()
            resp.status_code = 200
            resp.output = {"embeddings": [{"embedding": [0.1]}]}
            resp.usage = {"image_tokens": 1, "input_tokens": 1}
            return resp

        mock_api.side_effect = _resp
        model = DashScopeEmbeddingModel(
            credential=_cred(),
            model="multimodal-embedding-v1",
            dimensions=1024,
        )

        await model([_img()], api_key="sk-per-call")

        self.assertEqual(mock_api.call_count, 1)
        self.assertEqual(
            mock_api.call_args.kwargs["api_key"],
            "sk-per-call",
        )

    @patch("dashscope.embeddings.TextEmbedding.call")
    async def test_per_call_api_key_stays_out_of_the_cache_identifier(
        self,
        mock_api: Any,
    ) -> None:
        """The cache key must not embed the per-call secret (rotation-safe)."""
        mock_api.return_value = _text_resp([[0.1, 0.2]], 12)

        cache = MagicMock()
        cache.retrieve = AsyncMock(return_value=None)
        cache.store = AsyncMock()

        model = DashScopeEmbeddingModel(
            credential=_cred(),
            model="text-embedding-v4",
            dimensions=2,
            embedding_cache=cache,
        )

        await model(["hello"], api_key="sk-per-call")

        self.assertEqual(mock_api.call_count, 1)
        retrieve_identifier = cache.retrieve.await_args.kwargs["identifier"]
        self.assertIn("input", retrieve_identifier)
        self.assertNotIn("api_key", retrieve_identifier)
