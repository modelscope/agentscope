# -*- coding: utf-8 -*-
"""Per-call ``output_dimensionality`` must reach the Gemini SDK config.

``GeminiEmbeddingModel`` documents ``**kwargs`` as "Merged into
``EmbedContentConfig``" and states that per-call options take precedence,
which ``embedding_gemini_test.py`` already pins for ``task_type``.
``output_dimensionality`` was the one config field also bound as a literal
keyword at the call site, so passing it raised ``TypeError`` instead.
"""
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from agentscope.credential import GeminiCredential
from agentscope.embedding import GeminiEmbeddingModel


def _model(name: str) -> GeminiEmbeddingModel:
    """Build a model with only the SDK client mocked."""
    with patch("google.genai.Client") as client:
        client.return_value.aio.models.embed_content = AsyncMock(
            return_value=MagicMock(embeddings=[MagicMock(values=[0.1, 0.2])]),
        )
        return GeminiEmbeddingModel(
            credential=GeminiCredential(api_key="offline-placeholder"),
            model=name,
            dimensions=2,
            max_retries=0,
        )


class GeminiPerCallDimensionsTest(IsolatedAsyncioTestCase):
    """A per-call dimension override must not double-bind the SDK config."""

    async def test_text_call_accepts_per_call_dimensions(self) -> None:
        """Text mode forwards the override into the request config."""
        model = _model("gemini-embedding-001")
        await model(["hello"], output_dimensionality=4)

        request = model.client.aio.models.embed_content.call_args.kwargs
        self.assertEqual(
            {
                **request,
                "config": request["config"].model_dump(exclude_none=True),
            },
            {
                "model": "gemini-embedding-001",
                "contents": ["hello"],
                "config": {"output_dimensionality": 4},
            },
        )

    async def test_text_call_keeps_configured_dimensions(self) -> None:
        """Without an override the configured dimension still applies."""
        model = _model("gemini-embedding-001")
        await model(["hello"])

        request = model.client.aio.models.embed_content.call_args.kwargs
        self.assertEqual(
            {
                **request,
                "config": request["config"].model_dump(exclude_none=True),
            },
            {
                "model": "gemini-embedding-001",
                "contents": ["hello"],
                "config": {"output_dimensionality": 2},
            },
        )

    async def test_multimodal_call_accepts_per_call_dimensions(self) -> None:
        """Multimodal mode forwards the override into the request config."""
        model = _model("gemini-embedding-2")
        await model(["hello"], output_dimensionality=4)

        request = model.client.aio.models.embed_content.call_args.kwargs
        self.assertEqual(
            {
                **request,
                "contents": [
                    type(item).__name__ for item in request["contents"]
                ],
                "config": request["config"].model_dump(exclude_none=True),
            },
            {
                "model": "gemini-embedding-2",
                "contents": ["Content"],
                "config": {"output_dimensionality": 4},
            },
        )

    async def test_configured_parameters_survive_the_override(self) -> None:
        """An override must not drop the configured non-dimensional options."""
        with patch("google.genai.Client") as client:
            client.return_value.aio.models.embed_content = AsyncMock(
                return_value=MagicMock(
                    embeddings=[MagicMock(values=[0.1, 0.2])],
                ),
            )
            model = GeminiEmbeddingModel(
                credential=GeminiCredential(api_key="offline-placeholder"),
                model="gemini-embedding-001",
                dimensions=2,
                parameters=GeminiEmbeddingModel.Parameters(
                    task_type="RETRIEVAL_QUERY",
                ),
                max_retries=0,
            )
        await model(["hello"], output_dimensionality=4)

        request = model.client.aio.models.embed_content.call_args.kwargs
        self.assertEqual(
            {
                **request,
                "config": request["config"].model_dump(exclude_none=True),
            },
            {
                "model": "gemini-embedding-001",
                "contents": ["hello"],
                "config": {
                    "task_type": "RETRIEVAL_QUERY",
                    "output_dimensionality": 4,
                },
            },
        )
