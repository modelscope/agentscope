# -*- coding: utf-8 -*-
""" Test for record api invocation."""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import agentscope
from agentscope.models import OpenAIChatWrapper
from agentscope._runtime import _Runtime
from agentscope.file_manager import _FileManager, file_manager
from agentscope.utils.monitor import MonitorFactory


def flush() -> None:
    """
    ** Only for unittest usage. Don't use this function in your code. **
    Clear the runtime dir and destroy all singletons.
    """
    _Runtime._flush()  # pylint: disable=W0212
    _FileManager._flush()  # pylint: disable=W0212
    MonitorFactory.flush()


class RecordApiInvocation(unittest.TestCase):
    """
    Test for record api invocation.
    """

    def setUp(self) -> None:
        """Init for RecordApiInvocation."""

        self.dummy_response = {"content": "dummy_response"}

        flush()

    @patch("openai.OpenAI")
    def test_record_model_invocation_with_init(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test record model invocation with calling init function."""
        # prepare mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.model_dump.return_value = self.dummy_response
        mock_response.usage.model_dump.return_value = {}

        # link mock response to mock client
        mock_openai_instance = mock_client.return_value
        mock_openai_instance.chat.completions.create.return_value = (
            mock_response
        )

        # test
        agentscope.init(save_api_invoke=True)
        model = OpenAIChatWrapper(
            config_name="gpt-4",
            api_key="xxx",
            organization="xxx",
        )

        _ = model(messages=[])

        # assert
        self.assert_invocation_record()

    def assert_invocation_record(self) -> None:
        """Assert invocation record."""
        run_dir = file_manager.dir_root
        records = [
            _
            for _ in os.listdir(
                os.path.join(run_dir, "invoke"),
            )
            if _.startswith("model_OpenAIChatWrapper_")
        ]

        # only one record is here
        self.assertEqual(len(records), 1)

        filename = records[0]
        timestamp = filename.split("_")[2]

        with open(
            os.path.join(run_dir, "invoke", filename),
            "r",
            encoding="utf-8",
        ) as file:
            self.assertEqual(
                json.load(file),
                {
                    "model_class": "OpenAIChatWrapper",
                    "timestamp": timestamp,
                    "arguments": {
                        "model": "gpt-4",
                        "messages": [],
                    },
                    "response": {
                        "content": "dummy_response",
                    },
                },
            )

    def tearDown(self) -> None:
        """Tear down for RecordApiInvocation."""
        flush()
