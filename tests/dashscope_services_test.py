# -*- coding: utf-8 -*-
"""Dashscope Multi-Modality Service Test."""


import unittest
from unittest.mock import patch, MagicMock, mock_open


from agentscope.service import ServiceResponse, ServiceExecStatus
from agentscope.service import (
    dashscope_image_to_text,
    dashscope_text_to_image,
    dashscope_text_to_audio,
)


class TestDashScopeServices(unittest.TestCase):
    """Test DashScope Multi-Modality Services."""

    @patch(
        (
            "agentscope.service.multi_modality.dashscope_services."
            "DashScopeImageSynthesisWrapper"
        ),
    )
    @patch(
        "agentscope.service.multi_modality.dashscope_services.os.makedirs",
    )
    @patch(
        "agentscope.service.multi_modality.dashscope_services.os.path.exists",
    )
    @patch(
        "agentscope.service.multi_modality.dashscope_services.shutil.move",
    )
    def test_dashscope_text_to_image(
        self,
        mock_shutil_move: MagicMock,
        mock_os_path_exists: MagicMock,
        mock_os_makedirs: MagicMock,
        mock_wrapper_cls: MagicMock,
    ) -> None:
        """Test DashScope Image to Text Service."""
        # Configure the mocks
        mock_os_path_exists.return_value = False

        mock_instance = mock_wrapper_cls.return_value
        mock_response = MagicMock()
        mock_response.image_urls = [
            "RESULT_URL1",
            "RESULT_URL2",
            "RESULT_URL3",
            "RESULT_URL4",
        ]
        mock_instance.return_value = mock_response

        # Call the function under test
        prompt = "fake-query-prompt"
        api_key = "fake-api"
        number_of_images = 4
        size = "1024x1024"
        model = "fake-model"
        saved_dir = "fake-dir"
        results = dashscope_text_to_image(
            prompt,
            api_key,
            number_of_images,
            size,
            model,
            saved_dir,
        )

        # Verify the wrapper call
        mock_wrapper_cls.assert_called_once_with(
            config_name="dashscope-text-to-image-service",
            model_name=model,
            api_key=api_key,
        )
        mock_instance.assert_called_once_with(
            prompt=prompt,
            n=number_of_images,
            size=size,
            save_local=True,
        )

        # Verify the file operations
        mock_os_makedirs.assert_called_once_with(saved_dir)
        self.assertEqual(mock_shutil_move.call_count, 4)

        # Expected result
        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content={
                "fig_paths": [
                    f"{saved_dir}/{prompt[:10]}_0.png",
                    f"{saved_dir}/{prompt[:10]}_1.png",
                    f"{saved_dir}/{prompt[:10]}_2.png",
                    f"{saved_dir}/{prompt[:10]}_3.png",
                ],
            },
        )

        self.assertEqual(results.status, expected_result.status)
        self.assertEqual(results.content, expected_result.content)

    @patch(
        (
            "agentscope.service.multi_modality.dashscope_services."
            "DashScopeImageSynthesisWrapper"
        ),
    )
    @patch("agentscope.service.multi_modality.dashscope_services.os.makedirs")
    @patch(
        "agentscope.service.multi_modality.dashscope_services.os.path.exists",
    )
    def test_dashscope_text_to_image_failure(
        self,
        mock_os_path_exists: MagicMock,
        mock_os_makedirs: MagicMock,
        mock_wrapper_cls: MagicMock,
    ) -> None:
        """Test DashScope Image to Text Service failure."""
        # Configure the mocks
        mock_os_path_exists.return_value = False

        mock_instance = mock_wrapper_cls.return_value
        mock_instance.return_value.image_urls = (
            None  # Simulate failure by not returning URLs
        )

        # Call the function under test
        prompt = "fake-query-prompt"
        api_key = "fake-api"
        results = dashscope_text_to_image(prompt, api_key)

        # Verify the wrapper call
        mock_wrapper_cls.assert_called_once_with(
            config_name="dashscope-text-to-image-service",
            model_name="wanx-v1",
            api_key=api_key,
        )
        mock_instance.assert_called_once_with(
            prompt=prompt,
            n=1,
            size="1024*1024",
            save_local=True,
        )

        # Verify no directory creation for failure
        mock_os_makedirs.assert_not_called()

        # Expected result
        expected_result = ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": "Failed to generate images"},
        )

        self.assertEqual(results.status, expected_result.status)
        self.assertEqual(results.content, expected_result.content)

    @patch(
        (
            "agentscope.service.multi_modality.dashscope_services."
            "DashScopeMultiModalWrapper"
        ),
    )
    @patch(
        "agentscope.service.multi_modality.dashscope_services.os.path.abspath",
    )
    def test_dashscope_image_to_text_success(
        self,
        mock_abspath: MagicMock,
        mock_wrapper_cls: MagicMock,
    ) -> None:
        """Test successful image to text conversion."""
        # Configure the mocks
        mock_abspath.side_effect = lambda x: f"/abs/path/{x}"
        mock_instance = mock_wrapper_cls.return_value
        mock_response = MagicMock()
        mock_response.text = "A beautiful sunset in the mountains"
        mock_instance.return_value = mock_response

        # Call the function under test
        image_urls = "image1.jpg"
        prompt = "Describe the image"
        api_key = "fake-api"
        model = "qwen-vl-plus"
        results = dashscope_image_to_text(image_urls, prompt, api_key, model)

        # Verify the wrapper call
        mock_wrapper_cls.assert_called_once_with(
            config_name="dashscope-image-to-text-service",
            model_name=model,
            api_key=api_key,
        )
        mock_instance.assert_called_once()
        self.assertTrue(mock_abspath.called)

        # Expected result
        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="A beautiful sunset in the mountains",
        )

        self.assertEqual(results.status, expected_result.status)
        self.assertEqual(results.content, expected_result.content)

    @patch(
        (
            "agentscope.service.multi_modality.dashscope_services."
            "DashScopeMultiModalWrapper"
        ),
    )
    @patch(
        "agentscope.service.multi_modality.dashscope_services.os.path.abspath",
    )
    def test_dashscope_image_to_text_failure(
        self,
        mock_abspath: MagicMock,
        mock_wrapper_cls: MagicMock,
    ) -> None:
        """Test failure in image to text conversion."""
        # Configure the mocks
        mock_abspath.side_effect = lambda x: f"/abs/path/{x}"
        mock_instance = mock_wrapper_cls.return_value
        mock_instance.return_value.text = (
            None  # Simulate failure by returning None
        )

        # Call the function under test
        image_urls = "image1.jpg"
        prompt = "Describe the image"
        api_key = "fake-api"
        model = "qwen-vl-plus"
        results = dashscope_image_to_text(image_urls, prompt, api_key, model)

        # Verify the wrapper call
        mock_wrapper_cls.assert_called_once_with(
            config_name="dashscope-image-to-text-service",
            model_name=model,
            api_key=api_key,
        )
        mock_instance.assert_called_once()
        self.assertTrue(mock_abspath.called)

        # Expected result
        expected_result = ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": "Failed to generate text"},
        )

        self.assertEqual(results.status, expected_result.status)
        self.assertEqual(results.content, expected_result.content)

    @patch(
        (
            "agentscope.service.multi_modality.dashscope_services."
            "SpeechSynthesizer"
        ),
    )
    @patch("agentscope.service.multi_modality.dashscope_services.os.makedirs")
    @patch(
        "agentscope.service.multi_modality.dashscope_services.os.path.exists",
    )
    @patch("builtins.open", new_callable=mock_open)
    def test_dashscope_text_to_audio_success(
        self,
        mock_open_func: MagicMock,
        mock_os_path_exists: MagicMock,
        mock_os_makedirs: MagicMock,
        mock_synthesizer_cls: MagicMock,
    ) -> None:
        """Test successful text to audio conversion."""
        # Configure the mocks
        mock_os_path_exists.return_value = False

        mock_instance = mock_synthesizer_cls.return_value
        mock_response = MagicMock()
        mock_response.get_audio_data.return_value = b"fake_audio_data"
        mock_instance.return_value = mock_response

        # Call the function under test
        text = "hello?"
        api_key = "fake-api-key"
        model = "sambert-zhichu-v1"
        sample_rate = 48000
        saved_dir = "./audio"
        results = dashscope_text_to_audio(
            text,
            api_key,
            model,
            sample_rate,
            saved_dir,
        )

        # Verify the wrapper call
        mock_synthesizer_cls.call.assert_called_once_with(
            model=model,
            text=text,
            sample_rate=sample_rate,
        )

        # Verify the file operations
        mock_os_makedirs.assert_called_once_with(saved_dir)
        mock_open_func.assert_called_once_with(f"{saved_dir}/{text}.wav", "wb")

        # Expected result
        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content={"audio_path": f"{saved_dir}/{text}.wav"},
        )

        self.assertEqual(results.status, expected_result.status)
        self.assertEqual(results.content, expected_result.content)


if __name__ == "__main__":
    unittest.main()
