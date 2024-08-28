# -*- coding: utf-8 -*-
""" Unit test for logger chat"""
import json
import os
import shutil
import time
import unittest

from loguru import logger

from agentscope.logging import setup_logger
from agentscope.manager import ASManager
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

        # url
        msg2 = Msg("abc", "def", "assistant", url="https://xxx.png")
        msg2.id = 2
        msg2.timestamp = 2

        # urls
        msg3 = Msg(
            "abc",
            "def",
            "assistant",
            url=["https://yyy.png", "https://xxx.png"],
        )
        msg3.id = 3
        msg3.timestamp = 3

        # html labels
        msg4 = Msg("Bob", "<red>abc</div", "system")
        msg4.id = 4
        msg4.timestamp = 4

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

        for line, ground_truth in zip(
            lines,
            [
                '{"__module__": "agentscope.message.msg", "__name__": '
                '"Msg", "role": "assistant", "url": null, "metadata": null, '
                '"timestamp": 1, "id": 1, "content": "def", "name": "abc"}\n',
                '{"__module__": "agentscope.message.msg", "__name__": '
                '"Msg", "role": "assistant", "url": "https://xxx.png", '
                '"metadata": null, "timestamp": 2, "id": 2, "content": "def", '
                '"name": "abc"}\n',
                '{"__module__": "agentscope.message.msg", "__name__": "Msg", '
                '"role": "assistant", "url": ["https://yyy.png", '
                '"https://xxx.png"], "metadata": null, "timestamp": 3, '
                '"id": 3, "content": "def", "name": "abc"}\n',
                '{"__module__": "agentscope.message.msg", "__name__": "Msg", '
                '"role": "system", "url": null, "metadata": null, '
                '"timestamp": 4, "id": 4, "content": "<red>abc</div", '
                '"name": "Bob"}\n',
            ],
        ):
            self.assertDictEqual(json.loads(line), json.loads(ground_truth))

    def tearDown(self) -> None:
        """Tear down for LoggerTest."""
        ASManager.get_instance().flush()
        if os.path.exists(self.run_dir):
            shutil.rmtree(self.run_dir)


if __name__ == "__main__":
    unittest.main()
