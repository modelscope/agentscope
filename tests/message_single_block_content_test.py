# -*- coding: utf-8 -*-
"""Message constructors accept a single content block as well as a list."""
from unittest import TestCase

from agentscope.message import (
    AssistantMsg,
    Base64Source,
    DataBlock,
    SystemMsg,
    TextBlock,
    UserMsg,
)


class SingleBlockContentTest(TestCase):
    """A lone TextBlock/DataBlock is normalized into a one-element list."""

    def test_user_msg_single_text_block(self):
        msg = UserMsg(name="user", content=TextBlock(text="hello"))
        self.assertEqual(len(msg.content), 1)
        self.assertIsInstance(msg.content[0], TextBlock)
        self.assertEqual(msg.content[0].text, "hello")

    def test_user_msg_single_data_block(self):
        msg = UserMsg(
            name="user",
            content=DataBlock(
                source=Base64Source(data="aGVsbG8=", media_type="image/png"),
            ),
        )
        self.assertEqual(len(msg.content), 1)
        self.assertIsInstance(msg.content[0], DataBlock)

    def test_assistant_msg_single_text_block(self):
        msg = AssistantMsg(name="assistant", content=TextBlock(text="hi"))
        self.assertEqual(len(msg.content), 1)
        self.assertEqual(msg.content[0].text, "hi")

    def test_system_msg_single_text_block(self):
        msg = SystemMsg(name="system", content=TextBlock(text="be nice"))
        self.assertEqual(len(msg.content), 1)
        self.assertEqual(msg.content[0].text, "be nice")

    def test_list_content_still_accepted(self):
        msg = UserMsg(
            name="user",
            content=[TextBlock(text="look"), TextBlock(text="at this")],
        )
        self.assertEqual([b.text for b in msg.content], ["look", "at this"])

    def test_plain_string_still_accepted(self):
        msg = UserMsg(name="user", content="hello")
        self.assertEqual([b.text for b in msg.content], ["hello"])
