# -*- coding: utf-8 -*-
"""OpenAI services test module."""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import shutil

from agentscope.manager import ASManager
from agentscope.service.multi_modality.openai_services import (
    openai_audio_to_text,
    openai_text_to_audio,
    openai_text_to_image,
    openai_image_to_text,
    openai_edit_image,
    openai_create_image_variation,
)
from agentscope.service import ServiceExecStatus
from agentscope.service.multi_modality.openai_services import _audio_filename


class TestOpenAIServices(unittest.TestCase):
    """Test the OpenAI services functions."""

    def setUp(self) -> None:
        """Set up the test"""
        self.save_dir = os.path.join(os.path.dirname(__file__), "test_dir")
        os.makedirs(self.save_dir, exist_ok=True)
        self.maxDiff = None

    def tearDown(self) -> None:
        """Tear down the test"""
        ASManager.get_instance().flush()
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

    @patch(
        "agentscope.service.multi_modality.openai_services.OpenAIDALLEWrapper",
    )
    @patch("agentscope.service.multi_modality.openai_services._download_file")
    def test_openai_text_to_image_success(
        self,
        _: MagicMock,
        mock_dalle_wrapper: MagicMock,
    ) -> None:
        """Test the openai_text_to_image function with a valid prompt."""
        # Mock the OpenAIDALLEWrapper response
        mock_response = MagicMock()
        mock_response.image_urls = [
            "https://example.com/image1.png",
            "https://example.com/image2.png",
        ]
        mock_instance = MagicMock()
        mock_instance.return_value = mock_response
        mock_dalle_wrapper.return_value = mock_instance

        # Call the function with a valid prompt
        result = openai_text_to_image(
            prompt="A futuristic city skyline at sunset",
            api_key="fake_api_key",
            n=2,
            model="dall-e-2",
            size="256x256",
            quality="standard",
            style="vivid",
            save_dir=self.save_dir,
        )

        self.assertEqual(result.status, ServiceExecStatus.SUCCESS)
        expected_urls = [
            os.path.join(self.save_dir, "image1.png"),
            os.path.join(self.save_dir, "image2.png"),
        ]
        self.assertEqual(result.content, {"image_urls": expected_urls})

        # Ensure the wrapper and response methods are called correctly
        mock_dalle_wrapper.assert_called_once_with(
            config_name="text_to_image_service_call",
            model_name="dall-e-2",
            api_key="fake_api_key",
        )
        mock_instance.assert_called_once_with(
            prompt="A futuristic city skyline at sunset",
            n=2,
            size="256x256",
            quality="standard",
            style="vivid",
        )

    @patch(
        "agentscope.service.multi_modality.openai_services.OpenAIDALLEWrapper",
    )
    def test_openai_text_to_image_api_error(
        self,
        mock_dalle_wrapper: MagicMock,
    ) -> None:
        """Test the openai_text_to_image function with an API error."""
        # Mock an API failure response
        mock_instance = MagicMock()
        mock_instance.side_effect = Exception("API Error: Invalid request")
        mock_dalle_wrapper.return_value = mock_instance

        # Call the function with a prompt that causes an API error
        result = openai_text_to_image(
            prompt="An invalid prompt",
            api_key="fake_api_key",
            n=1,
            model="dall-e-2",
            size="256x256",
            quality="standard",
            style="vivid",
        )

        self.assertEqual(result.status, ServiceExecStatus.ERROR)
        self.assertIn("API Error", result.content)

        # Ensure the wrapper and response methods are called correctly
        mock_dalle_wrapper.assert_called_once_with(
            config_name="text_to_image_service_call",
            model_name="dall-e-2",
            api_key="fake_api_key",
        )
        mock_instance.assert_called_once_with(
            prompt="An invalid prompt",
            n=1,
            size="256x256",
            quality="standard",
            style="vivid",
        )

    @patch(
        "agentscope.service.multi_modality.openai_services.OpenAIDALLEWrapper",
    )
    @patch("agentscope.service.multi_modality.openai_services._download_file")
    def test_openai_text_to_image_service_error(
        self,
        mock_download_file: MagicMock,
        mock_dalle_wrapper: MagicMock,
    ) -> None:
        """Test the openai_text_to_image function with a service error."""

        mock_response = MagicMock()
        mock_response.image_urls = None
        mock_instance = MagicMock()
        mock_instance.return_value = mock_response
        mock_dalle_wrapper.return_value = mock_instance

        # Call the function with a valid prompt but simulate an internal error
        result = openai_text_to_image(
            prompt="A futuristic city skyline at sunset",
            api_key="fake_api_key",
            n=2,
            model="dall-e-2",
            size="256x256",
            quality="standard",
            style="vivid",
            save_dir=self.save_dir,
        )

        self.assertEqual(result.status, ServiceExecStatus.ERROR)
        self.assertIn("Error: Failed to generate images", result.content)

        # Ensure the wrapper and response methods are called correctly
        mock_dalle_wrapper.assert_called_once_with(
            config_name="text_to_image_service_call",
            model_name="dall-e-2",
            api_key="fake_api_key",
        )
        mock_instance.assert_called_once_with(
            prompt="A futuristic city skyline at sunset",
            n=2,
            size="256x256",
            quality="standard",
            style="vivid",
        )

        # Ensure _download_file is not called in case of service error
        mock_download_file.assert_not_called()

    @patch("openai.OpenAI")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=b"mock_audio_data",
    )
    def test_openai_audio_to_text_success(
        self,
        _: MagicMock,
        mock_openai: MagicMock,
    ) -> None:
        """Test the openai_audio_to_text function with a valid audio file."""
        # Mocking the OpenAI API response
        mock_transcription = (
            mock_openai.return_value.audio.transcriptions.create.return_value
        )
        mock_transcription.text = "This is a test transcription."

        # Test audio file path within the save_dir
        audio_file_url = os.path.join(self.save_dir, "test_audio.mp3")

        # Create the test file in the save_dir
        with open(audio_file_url, "wb") as f:
            f.write(b"mock_audio_data")

        # Call the function
        result = openai_audio_to_text(audio_file_url, "mock_api_key")

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(
            result.content,
            {"transcription": "This is a test transcription."},
        )

    @patch("openai.OpenAI")
    @patch("builtins.open", new_callable=mock_open)
    def test_openai_audio_to_text_error(
        self,
        _: MagicMock,
        mock_openai: MagicMock,
    ) -> None:
        """Test the openai_audio_to_text function with an API error."""
        # Mocking an OpenAI API error
        mock_openai.return_value.audio.transcriptions.create.side_effect = (
            Exception("API Error")
        )

        # Test audio file path within the save_dir
        audio_file_url = os.path.join(self.save_dir, "test_audio.mp3")

        # Call the function (the mock_file_open will handle the file opening)
        result = openai_audio_to_text(audio_file_url, "mock_api_key")

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.ERROR)
        self.assertIn(
            "Error: Failed to transcribe audio API Error",
            result.content,
        )

    @patch("openai.OpenAI")
    def test_successful_audio_generation(self, mock_openai: MagicMock) -> None:
        """Test the openai_text_to_audio function with a valid text."""
        # Mocking the OpenAI API response
        mock_response = (
            mock_openai.return_value.audio.speech.create.return_value
        )

        # Sample text and expected audio path
        text = "Hello, this is a test."
        save_dir = self.save_dir
        expected_audio_path = os.path.join(
            save_dir,
            f"{_audio_filename(text)}.mp3",
        )

        # Call the function
        result = openai_text_to_audio(text, "mock_api_key", save_dir)

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(result.content["audio_path"], expected_audio_path)
        mock_response.stream_to_file.assert_called_once_with(
            expected_audio_path,
        )  # Check file save

    @patch("openai.OpenAI")
    def test_api_error_text_to_audio(self, mock_openai: MagicMock) -> None:
        """Test the openai_text_to_audio function with an API error."""
        # Mocking an OpenAI API error
        mock_openai.return_value.audio.speech.create.side_effect = Exception(
            "API Error",
        )

        # Call the function
        result = openai_text_to_audio(
            "Hello, this is a test.",
            "mock_api_key",
            self.save_dir,
        )

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.ERROR)
        self.assertIn(
            "Error: Failed to generate audio. API Error",
            result.content,
        )

    @patch(
        "agentscope.service.multi_modality.openai_services.OpenAIChatWrapper",
    )
    def test_openai_image_to_text_success(
        self,
        mock_openai_chat_wrapper: MagicMock,
    ) -> None:
        """Test the openai_image_to_text function with a valid image URL."""
        # Mock the OpenAIChatWrapper
        mock_wrapper_instance = MagicMock()
        mock_openai_chat_wrapper.return_value = mock_wrapper_instance

        # Mock the response
        mock_response = MagicMock()
        mock_response.text = "This is a description of the image."
        mock_wrapper_instance.return_value = mock_response

        # Test with single image URL
        result = openai_image_to_text(
            "https://example.com/image.jpg",
            "fake_api_key",
        )

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(result.content, "This is a description of the image.")

        mock_openai_chat_wrapper.assert_called_once_with(
            config_name="image_to_text_service_call",
            model_name="gpt-4o",
            api_key="fake_api_key",
        )

        mock_wrapper_instance.format.assert_called_once()
        formatted_message = mock_wrapper_instance.format.call_args[0][0]
        self.assertEqual(formatted_message.name, "service_call")
        self.assertEqual(formatted_message.role, "user")
        self.assertEqual(formatted_message.content, "Describe the image")
        self.assertEqual(
            formatted_message.url,
            "https://example.com/image.jpg",
        )

    @patch(
        "agentscope.service.multi_modality.openai_services.OpenAIChatWrapper",
    )
    def test_openai_image_to_text_error(
        self,
        mock_openai_chat_wrapper: MagicMock,
    ) -> None:
        """Test the openai_image_to_text function with an API error."""
        # Mock the OpenAIChatWrapper to raise an exception
        mock_wrapper_instance = MagicMock()
        mock_openai_chat_wrapper.return_value = mock_wrapper_instance
        mock_wrapper_instance.side_effect = Exception("API Error")

        # Test with single image URL
        result = openai_image_to_text(
            "https://example.com/image.jpg",
            "fake_api_key",
        )

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.ERROR)
        self.assertEqual(result.content, "API Error")

    @patch("openai.OpenAI")
    @patch("agentscope.service.multi_modality.openai_services._parse_url")
    @patch(
        (
            "agentscope.service.multi_modality.openai_services"
            "._handle_openai_img_response"
        ),
    )
    def test_openai_edit_image_success(
        self,
        mock_handle_response: MagicMock,
        mock_parse_url: MagicMock,
        mock_openai: MagicMock,
    ) -> None:
        """Test the openai_edit_image function with a valid image URL."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_client.images.edit.return_value = mock_response

        # Mock _parse_url function
        mock_parse_url.side_effect = lambda x: f"parsed_{x}"

        # Mock _handle_openai_img_response function
        mock_handle_response.return_value = [
            "edited_image_url1",
            "edited_image_url2",
        ]

        # Call the function
        result = openai_edit_image(
            image_url="original_image.png",
            prompt="Add a sun to the sky",
            api_key="fake_api_key",
            mask_url="mask_image.png",
            n=2,
            size="512x512",
            save_dir=None,
        )

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(
            result.content,
            {"image_urls": ["edited_image_url1", "edited_image_url2"]},
        )

        # Check if OpenAI client was called correctly
        mock_client.images.edit.assert_called_once_with(
            model="dall-e-2",
            image="parsed_original_image.png",
            mask="parsed_mask_image.png",
            prompt="Add a sun to the sky",
            n=2,
            size="512x512",
        )

        # Check if _handle_openai_img_response was called
        mock_handle_response.assert_called_once_with(
            mock_response.model_dump(),
            None,
        )

    @patch("openai.OpenAI")
    @patch("agentscope.service.multi_modality.openai_services._parse_url")
    def test_openai_edit_image_error(
        self,
        mock_parse_url: MagicMock,
        mock_openai: MagicMock,
    ) -> None:
        """Test the openai_edit_image function with an API error."""
        # Mock OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.images.edit.side_effect = Exception("API Error")

        # Mock _parse_url function
        mock_parse_url.side_effect = lambda x: f"parsed_{x}"

        # Call the function
        result = openai_edit_image(
            image_url="original_image.png",
            prompt="Add a sun to the sky",
            api_key="fake_api_key",
        )

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.ERROR)
        self.assertEqual(result.content, "API Error")

        # Check if OpenAI client was called
        mock_client.images.edit.assert_called_once_with(
            model="dall-e-2",
            image="parsed_original_image.png",
            prompt="Add a sun to the sky",
            n=1,
            size="256x256",
        )

    @patch("openai.OpenAI")
    @patch("agentscope.service.multi_modality.openai_services._parse_url")
    @patch(
        (
            "agentscope.service.multi_modality.openai_services"
            "._handle_openai_img_response"
        ),
    )
    def test_openai_create_image_variation_success(
        self,
        mock_handle_response: MagicMock,
        mock_parse_url: MagicMock,
        mock_openai: MagicMock,
    ) -> None:
        """Test the openai_create_image_variation with a valid image URL."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_client.images.create_variation.return_value = mock_response

        # Mock _parse_url function
        mock_parse_url.return_value = "parsed_image.png"

        # Mock _handle_openai_img_response function
        mock_handle_response.return_value = [
            "variation_url1",
            "variation_url2",
        ]

        # Call the function
        result = openai_create_image_variation(
            image_url="original_image.png",
            api_key="fake_api_key",
            n=2,
            size="512x512",
            save_dir=None,
        )

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(
            result.content,
            {"image_urls": ["variation_url1", "variation_url2"]},
        )

        # Check if OpenAI client was called correctly
        mock_client.images.create_variation.assert_called_once_with(
            model="dall-e-2",
            image="parsed_image.png",
            n=2,
            size="512x512",
        )

        # Check if _handle_openai_img_response was called
        mock_handle_response.assert_called_once_with(
            mock_response.model_dump(),
            None,
        )

    @patch("openai.OpenAI")
    @patch("agentscope.service.multi_modality.openai_services._parse_url")
    def test_openai_create_image_variation_error(
        self,
        mock_parse_url: MagicMock,
        mock_openai: MagicMock,
    ) -> None:
        """Test the openai_create_image_variation with an API error."""
        # Mock OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.images.create_variation.side_effect = Exception(
            "API Error",
        )

        # Mock _parse_url function
        mock_parse_url.return_value = "parsed_image.png"

        # Call the function
        result = openai_create_image_variation(
            image_url="original_image.png",
            api_key="fake_api_key",
        )

        # Assertions
        self.assertEqual(result.status, ServiceExecStatus.ERROR)
        self.assertEqual(result.content, "API Error")

        # Check if OpenAI client was called
        mock_client.images.create_variation.assert_called_once_with(
            model="dall-e-2",
            image="parsed_image.png",
            n=1,
            size="256x256",
        )


if __name__ == "__main__":
    unittest.main()
