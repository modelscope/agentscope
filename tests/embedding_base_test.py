# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Tests for usage accounting when embedding batches are merged."""
from unittest import TestCase

from agentscope.embedding import (
    EmbeddingModelBase,
    EmbeddingResponse,
    EmbeddingUsage,
)


class EmbeddingMergeUsageTest(TestCase):
    """An incomplete token sum must remain unknown."""

    def test_unknown_tokens_are_not_treated_as_zero(self) -> None:
        """Unknown batches invalidate the total in either position."""
        cases: tuple[list[int | None], ...] = (
            [None, None],
            [7, None],
            [None, 7],
            [3, None, 5],
        )
        for counts in cases:
            with self.subTest(counts=counts):
                result = EmbeddingModelBase._merge_responses(
                    [
                        EmbeddingResponse(
                            embeddings=[[float(index)]],
                            usage=EmbeddingUsage(tokens=count, time=0.25),
                        )
                        for index, count in enumerate(counts)
                    ],
                )
                self.assertIsNone(result.usage.tokens)
                self.assertEqual(len(result.embeddings), len(counts))

    def test_missing_usage_leaves_total_unknown(self) -> None:
        """A batch without a usage object also makes the sum incomplete."""
        for usages in (
            [None, EmbeddingUsage(tokens=7, time=0.5)],
            [EmbeddingUsage(tokens=7, time=0.5), None],
        ):
            with self.subTest(usages=usages):
                result = EmbeddingModelBase._merge_responses(
                    [
                        EmbeddingResponse(embeddings=[[1.0]], usage=usages[0]),
                        EmbeddingResponse(embeddings=[[2.0]], usage=usages[1]),
                    ],
                )
                self.assertIsNone(result.usage.tokens)
                self.assertEqual(result.usage.time, 0.5)
                self.assertEqual(result.embeddings, [[1.0], [2.0]])

    def test_known_tokens_include_real_zeroes(self) -> None:
        """Reported zeroes and cache-hit zeroes can be summed normally."""
        for counts, expected in (([0, 0], 0), ([2, 3], 5), ([0, 4], 4)):
            with self.subTest(counts=counts):
                result = EmbeddingModelBase._merge_responses(
                    [
                        EmbeddingResponse(
                            embeddings=[[float(index)]],
                            usage=EmbeddingUsage(tokens=count, time=0.25),
                            source="cache" if count == 0 else "api",
                        )
                        for index, count in enumerate(counts)
                    ],
                )
                self.assertEqual(result.usage.tokens, expected)
                self.assertEqual(result.usage.time, 0.5)
                self.assertEqual(result.embeddings, [[0.0], [1.0]])
