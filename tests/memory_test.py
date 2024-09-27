# -*- coding: utf-8 -*-
"""
Unit tests for memory classes and functions
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from agentscope.message import Msg
from agentscope.memory import TemporaryMemory
from agentscope.serialize import serialize


class TemporaryMemoryTest(unittest.TestCase):
    """
    Test cases for TemporaryMemory
    """

    def setUp(self) -> None:
        self.memory = TemporaryMemory()
        self.file_name_1 = "tmp_mem_file1.txt"
        self.file_name_2 = "tmp_mem_file2.txt"
        self.msg_1 = Msg("user", "Hello", role="user")
        self.msg_2 = Msg(
            "agent",
            "Hello! How can I help you?",
            role="assistant",
        )
        self.msg_3 = Msg(
            "user",
            "Translate the following sentence",
            role="assistant",
        )

        self.invalid = {"invalid_key": "invalid_value"}

    def tearDown(self) -> None:
        """Clean up before & after tests."""
        if os.path.exists(self.file_name_1):
            os.remove(self.file_name_1)
        if os.path.exists(self.file_name_2):
            os.remove(self.file_name_2)

    def test_add(self) -> None:
        """Test add different types of object"""
        # add msg
        self.memory.add(self.msg_1)
        self.assertEqual(
            self.memory.get_memory(),
            [self.msg_1],
        )

        # add list
        self.memory.add([self.msg_2, self.msg_3])
        self.assertEqual(
            self.memory.get_memory(),
            [self.msg_1, self.msg_2, self.msg_3],
        )

    @patch("loguru.logger.warning")
    def test_delete(self, mock_logging: MagicMock) -> None:
        """Test delete operations"""
        self.memory.add([self.msg_1, self.msg_2, self.msg_3])

        self.memory.delete(index=0)
        self.assertEqual(
            self.memory.get_memory(),
            [self.msg_2, self.msg_3],
        )

        # test invalid
        self.memory.delete(index=100)
        mock_logging.assert_called_once_with(
            "Skip delete operation for the invalid index [100]",
        )

    def test_invalid(self) -> None:
        """Test invalid operations for memory"""
        # test invalid add
        with self.assertRaises(Exception) as context:
            self.memory.add(self.invalid)
        self.assertTrue(
            f"Cannot add {type(self.invalid)} to memory, must be a Msg object."
            in str(context.exception),
        )

    def test_load_export(self) -> None:
        """
        Test load and export function of TemporaryMemory
        """
        memory = TemporaryMemory()
        user_input = Msg(name="user", content="Hello", role="user")
        agent_input = Msg(
            name="agent",
            content="Hello! How can I help you?",
            role="assistant",
        )
        memory.load([user_input, agent_input])
        retrieved_mem = memory.export(to_mem=True)
        self.assertEqual(
            retrieved_mem,
            [user_input, agent_input],
        )

        memory.export(file_path=self.file_name_1)
        memory.clear()
        self.assertEqual(
            memory.get_memory(),
            [],
        )
        memory.load(self.file_name_1)
        self.assertEqual(
            serialize(memory.get_memory()),
            serialize([user_input, agent_input]),
        )


if __name__ == "__main__":
    unittest.main()
