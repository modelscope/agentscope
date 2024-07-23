# -*- coding: utf-8 -*-
""" Unit test for logger chat"""
import os
import shutil
import time
import unittest

from loguru import logger

from agentscope.logging import setup_logger
from agentscope.message import Msg


class LoggerTest(unittest.TestCase):
    """
    Unit test for logger.
    """

    def setUp(self) -> None:
        """Setup for unit test."""
        self.run_dir = "./logger_runs/"

    def test_logger_chat(self) -> None:
        """Logger chat."""

        setup_logger(self.run_dir, level="INFO")

        msg1 = Msg("abc", "def", "assistant")
        msg1.id = 1
        msg1.timestamp = 1
        msg1._colored_name = "1"  # pylint: disable=protected-access

        # url
        msg2 = Msg("abc", "def", "assistant", url="https://xxx.png")
        msg2.id = 2
        msg2.timestamp = 2
        msg2._colored_name = "2"  # pylint: disable=protected-access

        # urls
        msg3 = Msg(
            "abc",
            "def",
            "assistant",
            url=["https://yyy.png", "https://xxx.png"],
        )
        msg3.id = 3
        msg3.timestamp = 3
        msg3._colored_name = "3"  # pylint: disable=protected-access

        # html labels
        msg4 = Msg("Bob", "<red>abc</div", "system")
        msg4.id = 4
        msg4.timestamp = 4
        msg4._colored_name = "4"  # pylint: disable=protected-access

        logger.chat(msg1)
        logger.chat(msg2)
        logger.chat(msg3)
        logger.chat(msg4)

        # To avoid that logging is not finished before the file is read
        time.sleep(2)

        with open(
            os.path.join(self.run_dir, "logging.chat"),
            "r",
            encoding="utf-8",
        ) as file:
            lines = file.readlines()

        ground_truth = [
            '{"id": 1, "timestamp": 1, "name": "abc", "content": "def", '
            '"role": "assistant", "url": null, "metadata": null, '
            '"_colored_name": "1"}\n',
            '{"id": 2, "timestamp": 2, "name": "abc", "content": "def", '
            '"role": "assistant", "url": "https://xxx.png", "metadata": null, '
            '"_colored_name": "2"}\n',
            '{"id": 3, "timestamp": 3, "name": "abc", "content": "def", '
            '"role": "assistant", "url": '
            '["https://yyy.png", "https://xxx.png"], "metadata": null, '
            '"_colored_name": "3"}\n',
            '{"id": 4, "timestamp": 4, "name": "Bob", "content": '
            '"<red>abc</div", "role": "system", "url": null, "metadata": '
            'null, "_colored_name": "4"}\n',
        ]

        self.assertListEqual(lines, ground_truth)

    def tearDown(self) -> None:
        """Tear down for LoggerTest."""
        logger.remove()
        if os.path.exists(self.run_dir):
            shutil.rmtree(self.run_dir)


if __name__ == "__main__":
    unittest.main()
