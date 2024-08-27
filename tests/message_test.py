# -*- coding: utf-8 -*-
"""The unit test for message module."""

import unittest

from agentscope.message import Msg


class MessageTest(unittest.TestCase):
    """The test cases for message module."""

    def test_msg(self) -> None:
        """Test the basic attributes in Msg object."""
        msg = Msg(name="A", content="B", role="assistant")
        self.assertEqual(msg.name, "A")
        self.assertEqual(msg.content, "B")
        self.assertEqual(msg.role, "assistant")
        self.assertEqual(msg.metadata, None)
        self.assertEqual(msg.url, None)

    def test_formatted_msg(self) -> None:
        """Test the formatted message."""
        msg = Msg(name="A", content="B", role="assistant")
        self.assertEqual(
            msg.formatted_str(),
            "A: B",
        )
        self.assertEqual(
            msg.formatted_str(colored=True),
            "\x1b[95mA\x1b[0m: B",
        )

    def test_serialize(self) -> None:
        """Test the serialization and deserialization of Msg object."""
        msg = Msg(name="A", content="B", role="assistant")
        serialized_msg = msg.to_dict()
        deserialized_msg = Msg.from_dict(serialized_msg)
        self.assertEqual(msg.id, deserialized_msg.id)
        self.assertEqual(msg.name, deserialized_msg.name)
        self.assertEqual(msg.content, deserialized_msg.content)
        self.assertEqual(msg.role, deserialized_msg.role)
        self.assertEqual(msg.metadata, deserialized_msg.metadata)
        self.assertEqual(msg.url, deserialized_msg.url)
        self.assertEqual(msg.timestamp, deserialized_msg.timestamp)
