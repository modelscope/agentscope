# -*- coding: utf-8 -*-
# pylint: disable=unused-argument, protected-access
"""Unittests for agent hooks."""
import unittest
from typing import Optional, Union, Tuple, Any, Dict
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
        self.agent2 = _TestAgent()

    def test_reply_hook(self) -> None:
        """Test the reply hook."""

        def pre_reply_hook(
            self: AgentBase,
            args: Tuple[Any, ...],
            kwargs: Dict[str, Any],
        ) -> Union[Tuple[Tuple[Msg, ...], Dict[str, Any]], None]:
            """Pre-reply hook."""
            if len(args) > 0 and isinstance(args[0], Msg):
                args[0].content = "-1, " + args[0].content
                return args, kwargs
            return None

        def pre_reply_hook_without_change(
            self: AgentBase,
            args: Tuple[Any, ...],
            kwargs: Dict[str, Any],
        ) -> None:
            """Pre-reply hook without returning, so that the message is not
            changed."""
            if len(args) > 0 and isinstance(args[0], Msg):
                args[0].content = "-2, " + x.content

        def post_reply_hook(
            self: AgentBase,
            args: Tuple[Any, ...],
            kwargs: Dict[str, Any],
            x: Msg,
        ) -> Msg:
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
        self.agent.register_hook("pre_reply", "first_pre_hook", pre_reply_hook)
        x = self.agent(msg_test)
        self.assertEqual("-1, 0", x.content)

        # Test with one pre and one post hook
        self.agent.register_hook(
            "post_reply",
            "first_post_hook",
            post_reply_hook,
        )
        x = self.agent(msg_test)
        self.assertEqual("-1, 0, 1", x.content)

        # Test with two pre hooks and one post hook
        self.agent.register_hook(
            "pre_reply",
            "second_pre_hook",
            pre_reply_hook,
        )
        x = self.agent(msg_test)
        self.assertEqual("-1, -1, 0, 1", x.content)

        # Test removing one pre hook
        self.agent.remove_hook("pre_reply", "first_pre_hook")
        x = self.agent(msg_test)
        self.assertEqual("-1, 0, 1", x.content)

        # Test removing one post hook
        self.agent.remove_hook("post_reply", "first_post_hook")
        x = self.agent(msg_test)
        self.assertEqual("-1, 0", x.content)

        # Test clearing all pre hooks
        self.agent.clear_hooks("pre_reply")
        x = self.agent(msg_test)
        self.assertEqual("0", x.content)

        # Test with three pre hooks, change -> not change -> change
        self.agent.register_hook("pre_reply", "first_pre_hook", pre_reply_hook)
        self.agent.register_hook(
            "pre_reply",
            "second_pre_hook",
            pre_reply_hook_without_change,
        )
        self.agent.register_hook("pre_reply", "third_pre_hook", pre_reply_hook)
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

        self.agent.register_hook(
            "pre_speak",
            "first_pre_hook",
            pre_speak_hook_change,
        )
        self.agent.register_hook(
            "pre_speak",
            "second_pre_hook",
            pre_speak_hook_change2,
        )
        self.agent.register_hook(
            "pre_speak",
            "third_pre_hook",
            pre_speak_hook_without_change,
        )
        self.agent.register_hook(
            "post_speak",
            "first_post_hook",
            post_speak_hook,
        )
        self.agent.register_hook(
            "post_speak",
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

        self.agent.register_hook(
            "pre_observe",
            "first_pre_hook",
            pre_observe_hook_change,
        )
        self.agent.register_hook(
            "pre_observe",
            "second_pre_hook",
            pre_observe_hook_not_change,
        )
        self.agent.register_hook(
            "post_observe",
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

    def test_class_and_object_pre_reply_hook(self) -> None:
        """Test the class and object hook."""

        def pre_reply_hook_1(
            self: AgentBase,
            args: Tuple[Any, ...],
            kwargs: Dict[str, Any],
        ) -> Union[Tuple[Tuple[Msg, ...], Dict[str, Any]], None]:
            """Pre-reply hook."""
            args[0].content = "-1, " + args[0].content
            return args, kwargs

        def pre_reply_hook_2(
            self: AgentBase,
            args: Tuple[Any, ...],
            kwargs: Dict[str, Any],
        ) -> Union[Tuple[Tuple[Msg, ...], Dict[str, Any]], None]:
            """Pre-reply hook."""
            args[0].content = "-2, " + args[0].content
            return args, kwargs

        AgentBase.register_class_hook(
            "pre_reply",
            "first_hook",
            pre_reply_hook_1,
        )

        self.assertListEqual(
            list(self.agent._class_hooks_pre_reply.keys()),
            ["first_hook"],
        )
        self.assertListEqual(
            list(self.agent2._class_hooks_pre_reply.keys()),
            ["first_hook"],
        )
        AgentBase.clear_all_class_hooks()

        self.agent.register_hook(
            "pre_reply",
            "second_hook",
            pre_reply_hook_1,
        )
        self.assertListEqual(
            list(self.agent._hooks_pre_reply.keys()),
            ["second_hook"],
        )
        self.assertListEqual(
            list(self.agent2._class_hooks_pre_reply.keys()),
            [],
        )

        AgentBase.register_class_hook(
            "pre_reply",
            "third_hook",
            pre_reply_hook_2,
        )

        msg_test = Msg("user", "0", "user")

        res = self.agent(msg_test)
        self.assertEqual(res.content, "-2, -1, 0")

        res = self.agent2(msg_test)
        self.assertEqual(res.content, "-2, 0")

    def test_class_and_object_post_reply_hook(self) -> None:
        """Test the class and object hook."""

        def post_reply_hook_1(
            self: AgentBase,
            args: Tuple[Any, ...],
            kwargs: Dict[str, Any],
            output: Msg,
        ) -> Union[None, Msg]:
            """Post-reply hook."""
            return Msg("assistant", output.content + ", 1", "assistant")

        def post_reply_hook_2(
            self: AgentBase,
            args: Tuple[Any, ...],
            kwargs: Dict[str, Any],
            output: Msg,
        ) -> Union[None, Msg]:
            """Post-reply hook."""
            return Msg("assistant", output.content + ", 2", "assistant")

        AgentBase.register_class_hook(
            "post_reply",
            "first_hook",
            post_reply_hook_1,
        )

        self.assertListEqual(
            list(self.agent._class_hooks_post_reply.keys()),
            ["first_hook"],
        )
        self.assertListEqual(
            list(self.agent2._class_hooks_post_reply.keys()),
            ["first_hook"],
        )
        AgentBase.clear_all_class_hooks()

        self.agent.register_hook(
            "post_reply",
            "second_hook",
            post_reply_hook_1,
        )
        self.assertListEqual(
            list(self.agent._hooks_post_reply.keys()),
            ["second_hook"],
        )
        self.assertListEqual(
            list(self.agent2._class_hooks_post_reply.keys()),
            [],
        )

        AgentBase.register_class_hook(
            "post_reply",
            "third_hook",
            post_reply_hook_2,
        )

        msg_test = Msg("user", "0", "user")

        res = self.agent(msg_test)
        self.assertEqual(res.content, "0, 1, 2")

        res = self.agent2(msg_test)
        self.assertEqual(res.content, "0, 2")

    def test_class_and_object_pre_observe_hook(self) -> None:
        """Test the class and object hook."""

        def pre_observe_hook_1(self: AgentBase, x: Msg) -> Msg:
            """Pre-observe hook."""
            return Msg("assistant", "-1, " + x.content, "assistant")

        def pre_observe_hook_2(self: AgentBase, x: Msg) -> Msg:
            """Pre-observe hook."""
            return Msg("assistant", "-2, " + x.content, "assistant")

        AgentBase.register_class_hook(
            "pre_observe",
            "first_hook",
            pre_observe_hook_1,
        )

        self.assertListEqual(
            list(self.agent._class_hooks_pre_observe.keys()),
            ["first_hook"],
        )
        self.assertListEqual(
            list(self.agent2._class_hooks_pre_observe.keys()),
            ["first_hook"],
        )
        AgentBase.clear_all_class_hooks()

        self.agent.register_hook(
            "pre_observe",
            "second_hook",
            pre_observe_hook_1,
        )
        self.assertListEqual(
            list(self.agent._hooks_pre_observe.keys()),
            ["second_hook"],
        )
        self.assertListEqual(
            list(self.agent2._class_hooks_pre_observe.keys()),
            [],
        )

        AgentBase.register_class_hook(
            "pre_observe",
            "third_hook",
            pre_observe_hook_2,
        )

        msg_test = Msg("user", "0", "user")

        self.agent.observe(msg_test)
        self.assertEqual(
            "-2, -1, 0",
            self.agent.memory.get_memory()[0].content,
        )

        self.agent2.observe(msg_test)
        self.assertEqual(
            "-2, 0",
            self.agent2.memory.get_memory()[0].content,
        )

    @patch("agentscope.agents._agent.log_msg")
    def test_class_and_object_pre_speak_hook(
        self,
        mock_log_msg: MagicMock,
    ) -> None:
        """Test the class and object hook."""

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

        AgentBase.register_class_hook(
            "pre_speak",
            "first_hook",
            pre_speak_hook_change,
        )

        self.assertListEqual(
            list(self.agent._class_hooks_pre_speak.keys()),
            ["first_hook"],
        )
        self.assertListEqual(
            list(self.agent2._class_hooks_pre_speak.keys()),
            ["first_hook"],
        )

        self.agent.register_hook(
            "pre_speak",
            "first_obj_hook",
            pre_speak_hook_change2,
        )

        msg_test = Msg("user", "0", "user")

        self.agent(msg_test)
        self.assertEqual("-1, -2, 0", mock_log_msg.call_args[0][0].content)

        self.agent2(msg_test)
        self.assertEqual("-1, 0", mock_log_msg.call_args[0][0].content)

    def tearDown(self) -> None:
        """Tear down the test."""
        self.agent.clear_all_obj_hooks()
        self.agent2.clear_all_obj_hooks()

        AgentBase.clear_all_class_hooks()
        self.agent.memory.clear()
