# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Regression coverage for nullable usage received from compatible models."""

from unittest import IsolatedAsyncioTestCase

from utils import MockModel

from agentscope.agent import Agent
from agentscope.event import ModelCallEndEvent
from agentscope.message import TextBlock, UserMsg
from agentscope.model import ChatResponse, ChatUsage


def _usage(input_tokens: int | None, output_tokens: int | None) -> ChatUsage:
    """Simulate SDK counters copied into an unchecked dataclass."""
    usage = ChatUsage(
        input_tokens=0,
        output_tokens=0,
        time=0.1,
        cache_input_tokens=3,
        cache_creation_input_tokens=2,
    )
    usage.input_tokens = input_tokens  # type: ignore[assignment]
    usage.output_tokens = output_tokens  # type: ignore[assignment]
    return usage


class AgentNullableUsageTest(IsolatedAsyncioTestCase):
    """Unknown counters must not discard a completed answer."""

    async def test_reply_stream_normalizes_nullable_counters(self) -> None:
        """Both model modes retain text, usage events and context."""
        for stream in (False, True):
            for input_tokens, output_tokens, expected_in, expected_out in (
                (None, 5, 0, 5),
                (10, None, 10, 0),
                (None, None, 0, 0),
                (0, 0, 0, 0),
                (10, 5, 10, 5),
            ):
                with self.subTest(
                    stream=stream,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                ):
                    model = MockModel()
                    usage = _usage(input_tokens, output_tokens)
                    response = ChatResponse(
                        content=[TextBlock(text="Hello")],
                        is_last=True,
                        usage=usage,
                    )
                    model.set_responses([[response] if stream else response])
                    agent = Agent(
                        name="test",
                        system_prompt="Be helpful.",
                        model=model,
                    )
                    events = [
                        event
                        async for event in agent.reply_stream(
                            UserMsg("user", "Hi"),
                        )
                    ]
                    ends = [
                        e for e in events if isinstance(e, ModelCallEndEvent)
                    ]
                    self.assertEqual(len(ends), 1)
                    expected = {
                        "input_tokens": expected_in,
                        "output_tokens": expected_out,
                        "cache_input_tokens": 3,
                        "cache_creation_input_tokens": 2,
                    }
                    self.assertEqual(
                        {key: getattr(ends[0], key) for key in expected},
                        expected,
                    )
                    saved = agent.state.context[-1]
                    self.assertEqual(saved.get_text_content(), "Hello")
                    self.assertEqual(saved.usage.model_dump(), expected)

    async def test_save_to_context_normalizes_nullable_counters(self) -> None:
        """The save boundary is independently safe if no end event is built."""
        agent = Agent(
            name="test",
            system_prompt="Be helpful.",
            model=MockModel(),
        )
        agent._save_to_context(
            [TextBlock(text="Hello")],
            _usage(None, None),
        )
        self.assertEqual(
            agent.state.context[-1].usage.model_dump(),
            {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_input_tokens": 3,
                "cache_creation_input_tokens": 2,
            },
        )

    async def test_reply_returns_normalized_usage(self) -> None:
        """The public reply result preserves the provider's known counter."""
        model = MockModel()
        model.set_responses(
            [
                ChatResponse(
                    content=[TextBlock(text="Hello")],
                    is_last=True,
                    usage=_usage(None, 5),
                ),
            ],
        )
        agent = Agent(name="test", system_prompt="Be helpful.", model=model)
        reply = await agent.reply(UserMsg("user", "Hi"))
        self.assertEqual(reply.get_text_content(), "Hello")
        self.assertEqual(
            reply.usage.model_dump(),
            {
                "input_tokens": 0,
                "output_tokens": 5,
                "cache_input_tokens": 3,
                "cache_creation_input_tokens": 2,
            },
        )
