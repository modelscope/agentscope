# -*- coding: utf-8 -*-
"""Regression tests for nullable usage counters (issue #3444).

An Anthropic-compatible endpoint may omit ``usage.input_tokens`` or
return it as ``null``; the SDK's non-strict parsing then produces
``None``, which ``ChatUsage`` (a plain dataclass) carries unchecked
into the agent.  A successfully generated reply must not be aborted
just because its usage statistics are incomplete: unavailable primary
counters are normalized to zero at the agent boundaries, following
the existing handling of the nullable cache counters.
"""
from unittest.async_case import IsolatedAsyncioTestCase

from utils import MockModel

from agentscope.agent import Agent, ContextConfig
from agentscope.event import ModelCallEndEvent
from agentscope.message import AssistantMsg, TextBlock, UserMsg
from agentscope.model import ChatResponse, ChatUsage, StructuredResponse
from agentscope.state import AgentState
from agentscope.tool import Toolkit


def _make_agent(usage: ChatUsage) -> Agent:
    """Build an agent whose mock model returns one reply with ``usage``."""
    model = MockModel()
    model.set_responses(
        [
            [
                ChatResponse(
                    content=[TextBlock(text="Hello")],
                    is_last=True,
                    usage=usage,
                ),
            ],
        ],
    )
    return Agent(name="test", system_prompt="Be helpful.", model=model)


class AgentNullableUsageTest(IsolatedAsyncioTestCase):
    """The nullable usage counter test case."""

    async def test_reply_stream_with_null_input_tokens(self) -> None:
        """A null input counter must not abort a streamed reply."""
        agent = _make_agent(
            ChatUsage(input_tokens=None, output_tokens=5, time=0.1),
        )
        end_event = None
        async for event in agent.reply_stream(UserMsg("user", "Hi")):
            if isinstance(event, ModelCallEndEvent):
                end_event = event
        self.assertIsNotNone(end_event)
        self.assertEqual(end_event.input_tokens, 0)
        self.assertEqual(end_event.output_tokens, 5)
        # The reply is also saved to the context with normalized usage.
        saved_usage = agent.state.context[-1].usage
        self.assertIsNotNone(saved_usage)
        self.assertEqual(saved_usage.input_tokens, 0)
        self.assertEqual(saved_usage.output_tokens, 5)

    async def test_save_to_context_with_nullable_counters(self) -> None:
        """The save boundary tolerates every missing/null combination."""
        cases = [
            (None, 5, 0, 5),
            (5, None, 5, 0),
            (None, None, 0, 0),
            (0, 0, 0, 0),
            (7, 9, 7, 9),
        ]
        for raw_in, raw_out, want_in, want_out in cases:
            with self.subTest(input_tokens=raw_in, output_tokens=raw_out):
                agent = _make_agent(
                    ChatUsage(input_tokens=7, output_tokens=9, time=0.1),
                )
                agent._save_to_context(
                    [TextBlock(text="Hello")],
                    ChatUsage(
                        input_tokens=raw_in,
                        output_tokens=raw_out,
                        time=0.1,
                    ),
                )
                saved_usage = agent.state.context[-1].usage
                self.assertIsNotNone(saved_usage)
                self.assertEqual(saved_usage.input_tokens, want_in)
                self.assertEqual(saved_usage.output_tokens, want_out)

    async def test_context_compression_with_null_usage_counters(
        self,
    ) -> None:
        """Compression records a null primary counter as zero.

        The compression call is not covered by the model call events;
        its usage is appended to the last retained message through a
        separate ``Usage`` construction in the agent, which must
        tolerate the same incomplete usage as the reply path.
        """
        model = MockModel(context_size=100)
        agent = Agent(
            name="Friday",
            system_prompt="".join(["0" for _ in range(20 * 4)]),
            model=model,
            context_config=ContextConfig(
                trigger_ratio=0.7,
                reserve_ratio=0.4,
            ),
            state=AgentState(
                session_id="123",
                context=[
                    UserMsg(
                        "User",
                        "".join(["1" for _ in range(30 * 4)]),
                        id="1",
                    ),
                    AssistantMsg(
                        "Friday",
                        "".join(["2" for _ in range(10 * 4)]),
                        id="2",
                    ),
                    UserMsg(
                        "User",
                        "".join(["3" for _ in range(10 * 4)]),
                        id="3",
                    ),
                ],
            ),
            toolkit=Toolkit(),
        )
        model.set_structured_response(
            StructuredResponse(
                content={
                    "task_overview": "1",
                    "current_state": "2",
                    "important_discoveries": "3",
                    "next_steps": "4",
                    "context_to_preserve": "5",
                },
                usage=ChatUsage(
                    input_tokens=None,
                    output_tokens=45,
                    time=0.1,
                    cache_input_tokens=6,
                    cache_creation_input_tokens=7,
                ),
            ),
        )

        await agent.compress_context()

        self.assertEqual(len(agent.state.context), 2)
        recorded_usage = agent.state.context[-1].usage
        self.assertIsNotNone(recorded_usage)
        self.assertEqual(recorded_usage.input_tokens, 0)
        self.assertEqual(recorded_usage.output_tokens, 45)
        self.assertEqual(recorded_usage.cache_input_tokens, 6)
        self.assertEqual(recorded_usage.cache_creation_input_tokens, 7)

    async def test_reply_stream_preserves_valid_counters(self) -> None:
        """Valid (including zero) counters pass through unchanged."""
        for raw_in, raw_out in [(7, 9), (0, 0)]:
            with self.subTest(input_tokens=raw_in, output_tokens=raw_out):
                agent = _make_agent(
                    ChatUsage(
                        input_tokens=raw_in,
                        output_tokens=raw_out,
                        time=0.1,
                    ),
                )
                end_event = None
                async for event in agent.reply_stream(UserMsg("user", "Hi")):
                    if isinstance(event, ModelCallEndEvent):
                        end_event = event
                self.assertIsNotNone(end_event)
                self.assertEqual(end_event.input_tokens, raw_in)
                self.assertEqual(end_event.output_tokens, raw_out)
