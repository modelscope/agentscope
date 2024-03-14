# -*- coding: utf-8 -*-
""" Test for record api invocation."""
import json
import os
import shutil
import unittest
from unittest.mock import patch, MagicMock

import agentscope
from agentscope.models import OpenAIChatWrapper


class RecordApiInvocation(unittest.TestCase):
    """
    Test for record api invocation.
    """

    def setUp(self) -> None:
        """Init for RecordApiInvocation."""

        self.dummy_response = {"content": "dummy_response"}

        if os.path.exists("./runs"):
            shutil.rmtree("./runs")

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
        sub_dirs = list(os.listdir("./runs"))

        # only one runtime dir is here
        self.assertEqual(len(sub_dirs), 1)

        sub_dir = sub_dirs[0]

        records = [
            _
            for _ in os.listdir(
                os.path.join("./runs", sub_dir, "invoke"),
            )
            if _.startswith("model_OpenAIChatWrapper_")
        ]

        # only one record is here
        self.assertEqual(len(records), 1)

        filename = records[0]
        timestamp = filename.split("_")[2]

        with open(
            os.path.join("./runs/", sub_dir, "invoke", filename),
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
        if os.path.exists("./runs"):
            shutil.rmtree("./runs")
