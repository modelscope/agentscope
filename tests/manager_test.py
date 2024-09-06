# -*- coding: utf-8 -*-
"""Test for manager module."""
import os
import shutil
from unittest import TestCase

import agentscope
from agentscope.manager import ASManager
from agentscope.constants import _DEFAULT_CACHE_DIR
from agentscope._version import __version__


class ManagerTest(TestCase):
    """Test cases for manager module."""

    def test_serialize(self) -> None:
        """Test the serialize function."""
        self.maxDiff = None
        agentscope.init(
            model_configs={
                "model_type": "ollama_chat",
                "config_name": "my_openai_chat",
                "model_name": "llama2",
            },
            project="project",
            name="name",
            disable_saving=True,
            logger_level="DEBUG",
        )

        manager = ASManager.get_instance()
        data = manager.state_dict()

        self.assertDictEqual(
            data,
            {
                "agentscope_version": __version__,
                "project": "project",
                "name": "name",
                "disable_saving": True,
                "run_id": manager.run_id,
                "pid": manager.pid,
                "timestamp": manager.timestamp,
                "file": {
                    "save_log": False,
                    "save_code": False,
                    "save_api_invoke": False,
                    "base_dir": None,
                    "run_dir": None,
                    "cache_dir": _DEFAULT_CACHE_DIR,
                },
                "model": {
                    "model_configs": {
                        "my_openai_chat": {
                            "config_name": "my_openai_chat",
                            "model_type": "ollama_chat",
                            "model_name": "llama2",
                        },
                    },
                },
                "logger": {"level": "DEBUG"},
                "studio": {"active": False, "studio_url": None},
                "monitor": {
                    "use_monitor": False,
                    "path_db": None,
                },
            },
        )

        # Flush the manager
        manager.flush()
        state_dict = manager.state_dict()
        self.assertDictEqual(
            state_dict,
            {
                "agentscope_version": __version__,
                "project": "",
                "name": "",
                "disable_saving": True,
                "run_id": "",
                "pid": -1,
                "timestamp": "",
                "file": {
                    "save_log": False,
                    "save_code": False,
                    "save_api_invoke": False,
                    "base_dir": None,
                    "run_dir": None,
                    "cache_dir": None,
                },
                "model": {"model_configs": {}},
                "logger": {"level": "INFO"},
                "studio": {"active": False, "studio_url": None},
                "monitor": {"path_db": None, "use_monitor": False},
            },
        )

        manager.load_dict(data)

        self.assertDictEqual(
            manager.state_dict(),
            data,
        )

        # If the file/directory created and copied successfully
        agentscope.init(
            save_api_invoke=True,
            save_code=True,
            save_log=True,
            save_dir="./runs",
            use_monitor=True,
        )

        self.assertTrue(os.path.exists(os.path.join(manager.file.run_dir)))
        self.assertSetEqual(
            set(os.listdir(manager.file.run_dir)),
            {
                ".config",
                "agentscope.db",
                "logging.chat",
                "logging.log",
                "code",
            },
        )

    def tearDown(self) -> None:
        """Clean up the manager."""
        ASManager.get_instance().flush()
        # Remove the dir
        shutil.rmtree("./runs")
