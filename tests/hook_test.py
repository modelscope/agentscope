# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Unittests for agent hooks."""
import unittest
from typing import Optional, Union
from unittest.mock import patch, MagicMock

from agentscope.agents import AgentBase
from agentscope.message import Msg


class _TestAgent(AgentBase):
    """A test agent."""

    def __init__(self) -> None:
        """Initialize the test agent."""
        super().__init__(
            name="Friday",
            use_memory=True,
        )

    def reply(self, x: Optional[Union[Msg, list[Msg]]] = None) -> Msg:
        """Reply function."""
        if x is not None:
            self.speak(x)
        return x


cnt_post = 0


class AgentHooksTest(unittest.TestCase):
    """Unittests for agent hooks."""

    def setUp(self) -> None:
        """Set up the test."""
        self.agent = _TestAgent()

    def test_reply_hook(self) -> None:
        """Test the reply hook."""

        def pre_reply_hook(
            self: AgentBase,
            x: Optional[Union[Msg, list[Msg]]] = None,
        ) -> Union[None, Msg]:
            """Pre-reply hook."""
            if isinstance(x, Msg):
                return Msg(
                    "assistant",
                    "-1, " + x.content,
                    "assistant",
                )
            return None

        def pre_reply_hook_without_change(
            self: AgentBase,
            x: Optional[Union[Msg, list[Msg]]] = None,
        ) -> None:
            """Pre-reply hook without returning, so that the message is not
            changed."""
            if isinstance(x, Msg):
                x.content = "-2, " + x.content

        def post_reply_hook(self: AgentBase, x: Msg) -> Msg:
            """Post-reply hook."""
            return Msg(
                "assistant",
                x.content + ", 1",
                "assistant",
            )

        msg_test = Msg("user", "0", "user")

        # Test without hooks
        x = self.agent(msg_test)
        self.assertEqual("0", x.content)

        # Test with one pre hook
        self.agent.register_pre_reply_hook("first_pre_hook", pre_reply_hook)
        x = self.agent(msg_test)
        self.assertEqual("-1, 0", x.content)

        # Test with one pre and one post hook
        self.agent.register_post_reply_hook("first_post_hook", post_reply_hook)
        x = self.agent(msg_test)
        self.assertEqual("-1, 0, 1", x.content)

        # Test with two pre hooks and one post hook
        self.agent.register_pre_reply_hook("second_pre_hook", pre_reply_hook)
        x = self.agent(msg_test)
        self.assertEqual("-1, -1, 0, 1", x.content)

        # Test removing one pre hook
        self.agent.remove_pre_reply_hook("first_pre_hook")
        x = self.agent(msg_test)
        self.assertEqual("-1, 0, 1", x.content)

        # Test removing one post hook
        self.agent.remove_post_reply_hook("first_post_hook")
        x = self.agent(msg_test)
        self.assertEqual("-1, 0", x.content)

        # Test clearing all pre hooks
        self.agent.clear_pre_reply_hooks()
        x = self.agent(msg_test)
        self.assertEqual("0", x.content)

        # Test with three pre hooks, change -> not change -> change
        self.agent.register_pre_reply_hook("first_pre_hook", pre_reply_hook)
        self.agent.register_pre_reply_hook(
            "second_pre_hook",
            pre_reply_hook_without_change,
        )
        self.agent.register_pre_reply_hook("third_pre_hook", pre_reply_hook)
        x = self.agent(msg_test)
        self.assertEqual("-1, -1, 0", x.content)

        # Test with no input
        self.agent()

    @patch("agentscope.agents._agent.log_msg")
    def test_speak_hook(self, mock_log_msg: MagicMock) -> None:
        """Test the speak hook."""

        def pre_speak_hook_change(
            self: AgentBase,
            msg: Msg,
            stream: bool,
            last: bool,
        ) -> Msg:
            """Pre-speak hook."""
            msg.content = "-1, " + msg.content
            return msg

        def pre_speak_hook_change2(
            self: AgentBase,
            msg: Msg,
            stream: bool,
            last: bool,
        ) -> Msg:
            """Pre-speak hook."""
            msg.content = "-2, " + msg.content
            return msg

        def pre_speak_hook_without_change(
            self: AgentBase,
            msg: Msg,
            stream: bool,
            last: bool,
        ) -> None:
            """Pre-speak hook."""
            return None

        def post_speak_hook(self: AgentBase) -> None:
            """Post-speak hook."""
            if not hasattr(self, "cnt"):
                self.cnt = 0
            self.cnt += 1

        self.agent.register_pre_speak_hook(
            "first_pre_hook",
            pre_speak_hook_change,
        )
        self.agent.register_pre_speak_hook(
            "second_pre_hook",
            pre_speak_hook_change2,
        )
        self.agent.register_pre_speak_hook(
            "third_pre_hook",
            pre_speak_hook_without_change,
        )
        self.agent.register_post_speak_hook("first_post_hook", post_speak_hook)
        self.agent.register_post_speak_hook(
            "second_post_hook",
            post_speak_hook,
        )

        test_msg = Msg("user", "0", "user")

        x = self.agent(test_msg)
        # The speak function shouldn't affect the reply message
        self.assertEqual(x.content, "0")

        self.assertEqual("-2, -1, 0", mock_log_msg.call_args[0][0].content)
        self.assertEqual(2, self.agent.cnt)

    def test_observe_hook(self) -> None:
        """Test the observe hook."""

        def pre_observe_hook_change(self: AgentBase, msg: Msg) -> Msg:
            """Pre-observe hook with returning, where the message will be
            changed."""
            msg.content = "-1, " + msg.content
            return msg

        def pre_observe_hook_not_change(self: AgentBase, msg: Msg) -> None:
            """Pre-observe hook without returning, so that the message is not
            changed."""
            msg.content = "-2, " + msg.content

        global cnt_post
        cnt_post = 0

        def post_observe_hook(self: AgentBase) -> None:
            """Post-observe hook."""
            global cnt_post
            cnt_post += 1

        msg_test = Msg("user", "0", "user")
        msg_test2 = Msg("user", "0", "user")

        self.agent.observe(msg_test)
        self.assertEqual("0", self.agent.memory.get_memory()[0].content)

        self.agent.register_pre_observe_hook(
            "first_pre_hook",
            pre_observe_hook_change,
        )
        self.agent.register_pre_observe_hook(
            "second_pre_hook",
            pre_observe_hook_not_change,
        )
        self.agent.register_post_observe_hook(
            "first_post_hook",
            post_observe_hook,
        )

        self.agent.observe(msg_test2)
        # The reply should not be affected due to deep copy
        # The memory should be affected
        print(self.agent.memory.get_memory())
        self.assertEqual(
            "-1, 0",
            self.agent.memory.get_memory()[1].content,
        )
        self.assertEqual(1, cnt_post)

    def tearDown(self) -> None:
        """Tear down the test."""
        self.agent.clear_all_hooks()
        self.agent.memory.clear()
