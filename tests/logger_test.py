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
        print(lines)
        for line, ground_truth in zip(
            lines,
            [
                '{"__module__": "agentscope.message.msg", '
                '"__name__": "Msg", "id": 1, "name": "abc", '
                '"role": "assistant", '
                '"content": "def", '
                '"metadata": null, "timestamp": 1}\n',
                '{"__module__": "agentscope.message.msg", '
                '"__name__": "Msg", "id": 2, "name": "abc", '
                '"role": "assistant", '
                '"content": [{"type": "text", "text": "def"}, '
                '{"type": "image", "url": "https://xxx.png"}], '
                '"metadata": null, "timestamp": 2}\n',
                '{"__module__": "agentscope.message.msg", '
                '"__name__": "Msg", "id": 3, "name": "abc", '
                '"role": "assistant", '
                '"content": [{"type": "text", "text": "def"}, '
                '{"type": "image", "url": "https://yyy.png"}, '
                '{"type": "image", "url": "https://xxx.png"}], '
                '"metadata": null, "timestamp": 3}\n',
                '{"__module__": "agentscope.message.msg", '
                '"__name__": "Msg", "id": 4, "name": "Bob", '
                '"role": "system", '
                '"content": "<red>abc</div", "metadata": null, '
                '"timestamp": 4}\n',
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
