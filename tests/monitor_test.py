# -*- coding: utf-8 -*-
"""
Unit tests for Monitor classes
"""

import unittest
import os
import shutil
from pathlib import Path

import agentscope
from agentscope.manager import MonitorManager, ASManager


class MonitorManagerTest(unittest.TestCase):
    """Test class for MonitorManager"""

    def setUp(self) -> None:
        """Set up the test environment."""
        agentscope.init(
            use_monitor=True,
            save_dir="./test_runs",
        )

        self.monitor = MonitorManager.get_instance()

    def test_monitor(self) -> None:
        """Test get monitor method of MonitorManager."""
        usage = self.monitor.print_llm_usage()

        self.assertDictEqual(
            usage,
            {
                "text_and_embedding": [],
                "image": [],
            },
        )

        self.monitor.update_text_and_embedding_tokens(
            model_name="gpt-4",
            prompt_tokens=10,
            completion_tokens=20,
        )

        self.monitor.update_text_and_embedding_tokens(
            model_name="gpt-4",
            prompt_tokens=1,
            completion_tokens=2,
        )

        self.monitor.update_image_tokens(
            model_name="dall_e_3",
            resolution="standard-1024*1024",
            image_count=4,
        )

        self.monitor.update_image_tokens(
            model_name="dall_e_3",
            resolution="hd-1024*1024",
            image_count=1,
        )

        usage = self.monitor.print_llm_usage()
        self.assertDictEqual(
            usage,
            {
                "text_and_embedding": [
                    {
                        "model_name": "gpt-4",
                        "times": 2,
                        "prompt_tokens": 11,
                        "completion_tokens": 22,
                        "total_tokens": 33,
                    },
                ],
                "image": [
                    {
                        "model_name": "dall_e_3",
                        "resolution": "hd-1024*1024",
                        "times": 1,
                        "image_count": 1,
                    },
                    {
                        "model_name": "dall_e_3",
                        "resolution": "standard-1024*1024",
                        "times": 1,
                        "image_count": 4,
                    },
                ],
            },
        )

    def tearDown(self) -> None:
        """Tear down the test environment."""
        ASManager.get_instance().flush()
        shutil.rmtree("./test_runs")


class DisableMonitorTest(unittest.TestCase):
    """Test class for DummyMonitor"""

    def setUp(self) -> None:
        agentscope.init(
            project="test",
            name="monitor",
            save_dir="./test_runs",
            save_log=True,
            use_monitor=False,
        )
        self.monitor = MonitorManager.get_instance()

    def test_disabled_monitor(self) -> None:
        """Test disabled monitor"""
        self.monitor.update_text_and_embedding_tokens(
            model_name="gpt-4",
            prompt_tokens=10,
            completion_tokens=20,
        )

        self.monitor.update_text_and_embedding_tokens(
            model_name="gpt-4",
            prompt_tokens=1,
            completion_tokens=2,
        )

        self.monitor.update_image_tokens(
            model_name="dall_e_3",
            resolution="standard-1024*1024",
            image_count=4,
        )

        self.assertDictEqual(
            self.monitor.print_llm_usage(),
            {
                "text_and_embedding": [],
                "image": [],
            },
        )

        # Check if the path is correct
        self.assertTrue(
            self.monitor.path_db.startswith(
                str(Path("./test_runs").resolve()),
            ),
        )
        # Check if the database doesn't exist
        self.assertTrue(not os.path.exists(self.monitor.path_db))

    def tearDown(self) -> None:
        """Tear down the test environment."""
        ASManager.get_instance().flush()
        shutil.rmtree("./test_runs")


if __name__ == "__main__":
    unittest.main()
