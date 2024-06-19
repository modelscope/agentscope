# -*- coding: utf-8 -*-
"""
Wrap OpenAI API calls as services. Refer the official OpenAI API documentation
for more details.
https://platform.openai.com/docs/overview
"""

import os
from typing import Literal, Optional, Union, Sequence
from openai import OpenAI
from openai.types import ImagesResponse
from openai._types import NotGiven
from agentscope.service.service_response import (
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.models.openai_model import (
    OpenAIDALLEWrapper,
    OpenAIChatWrapper,
)
from agentscope.utils.tools import _download_file


from agentscope.message import MessageBase


def _handle_openai_img_response(
    response: ImagesResponse,
    save_dir: Optional[str] = None,
) -> Union[str, Sequence[str]]:
    """Handle the response from OpenAI image generation API."""
    raw_response = response.model_dump()
    if "data" not in raw_response:
        if "error" in raw_response:
            error_msg = raw_response["error"]["message"]
        else:
            error_msg = raw_response
        raise ValueError(f"Error in OpenAI API call:\n{error_msg}")

    images = raw_response["data"]
    urls = [_["url"] for _ in images]
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        urls_local = []
        for url in urls:
            image_name = url.split("/")[-1]
            image_path = os.path.abspath(
                os.path.join(save_dir, image_name),
            )
            _download_file(url, image_path)
            urls_local.append(image_path)
        return urls_local
    else:
        return urls


def openai_text_to_image(
    prompt: str,
    api_key: str,
    n: int = 1,
    model: Literal["dalle-e-2", "dalle-e-3"] = "dalle-e-2",
    size: Literal[
        "256x256",
        "512x512",
        "1024x1024",
        "1792x1024",
        "1024x1792",
    ] = "256x256",
    quality: Literal["standard", "hdr"] = "standard",
    style: Optional[Literal["vivid", "natural"]] = None,
    save_dir: Optional[str] = None,
) -> ServiceResponse:
    """
    Generate image(s) based on the given prompt, and return image URL(s) or
    save them locally.

    Args:
        prompt (`str`):
            The text prompt to generate images.
        api_key (`str`):
            The API key for the OpenAI API.
        n (`int`, defaults to `1`):
            The number of images to generate.
        model (`Literal["dalle-e-2", "dalle-e-3"]`, defaults to `"dalle-e-2"`):
            The model to use for image generation.
        size (`Literal["256x256", "512x512", "1024x1024", "1792x1024",
        "1024x1792"]`, defaults to `"256x256"`):
            The size of the generated image(s).
        quality (`Literal["standard", "hdr"]`, defaults to `"standard"`):
            The quality of the generated images.
        style (`Optional[Literal["vivid", "natural"]]`, defaults to `None`):
            The style of the generated images.
        save_dir (`Optional[str]`, defaults to `None`):
            The directory to save the generated images. If not specified, will
            return the web URLs.

    Returns:
        `ServiceResponse`:
            A dictionary with two variables: `status` and `content`.
            If `status` is `ServiceExecStatus.SUCCESS`,
            the `content` is a dict with key 'image_urls' and
            value is a list of the paths to the generated images or URLs.

    Example:

        .. code-block:: python

            prompt = "A futuristic city skyline at sunset"
            print(openai_text_to_image(prompt, "{api_key}"))

        > {
        >     'status': 'SUCCESS',
        >     'content': {'image_urls': ['IMAGE_URL1', 'IMAGE_URL2']}
        > }
    """
    dalle_wrapper = OpenAIDALLEWrapper(
        config_name="text_to_image_service_call",
        model_name=model,
        api_key=api_key,
    )
    try:
        response = dalle_wrapper(
            prompt=prompt,
            n=n,
            size=size,
            quality=quality,
            style=style,
        )
        urls = response.image_urls
        if urls is None:
            return ServiceResponse(
                ServiceExecStatus.ERROR,
                "Error: Failed to generate images",
            )
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            urls_local = []
            for url in urls:
                image_name = url.split("/")[-1]
                image_path = os.path.abspath(
                    os.path.join(save_dir, image_name),
                )
                _download_file(url, image_path)
                urls_local.append(image_path)
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                {"image_urls": urls_local},
            )
        else:
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                {"image_urls": urls},
            )
    except Exception as e:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            str(e),
        )


def openai_edit_image(
    image_url: str,
    mask_url: str,
    prompt: str,
    api_key: str,
    n: int = 1,
    size: Literal[
        "256x256",
        "512x512",
        "1024x1024",
    ] = "256x256",
    save_dir: Optional[str] = None,
) -> ServiceResponse:
    """
    Edit an image based on the provided mask and prompt, and return the edited
    image URL(s) or save them locally.

    Args:
        image_url (`str`):
            The file path or URL to the image that needs editing.
        mask_url (`str`):
            The file path or URL to the mask image that specifies the regions
            to be edited.
        prompt (`str`):
            The text prompt describing the edits to be made to the image.
        api_key (`str`):
            The API key for the OpenAI API.
        n (`int`, defaults to `1`):
            The number of edited images to generate.
        size (`Literal["256x256", "512x512", "1024x1024"]`, defaults to
        `"256x256"`):
            The size of the edited images.
        save_dir (`Optional[str]`, defaults to `None`):
            The directory to save the edited images. If not specified, will
            return the web URLs.

    Returns:
        `ServiceResponse`:
            A dictionary with two variables: `status` and `content`.
            If `status` is `ServiceExecStatus.SUCCESS`,
            the `content` is a dict with key 'image_urls' and
            value is a list of the paths to the edited images or URLs.

    Example:

        .. code-block:: python

            image_url = "/path/to/original_image.png"
            mask_url = "/path/to/mask_image.png"
            prompt = "Add a sun to the sky"
            api_key = "YOUR_API_KEY"
            print(openai_edit_image(image_url, mask_url, prompt, api_key))

        > {
        >     'status': 'SUCCESS',
        >     'content': {'image_urls': ['EDITED_IMAGE_URL1',
        'EDITED_IMAGE_URL2']}
        > }
    """
    os.environ["OPENAI_API_KEY"] = api_key
    client = OpenAI()
    # convert relative path to absolute path
    image_url = os.path.abspath(image_url)
    mask_url = os.path.abspath(mask_url)
    with open(image_url, "rb") as img, open(mask_url, "rb") as mask:
        response = client.images.edit(
            model="dall-e-2",
            image=img,
            mask=mask,
            prompt=prompt,
            n=n,
            size=size,
        )
    try:
        urls = _handle_openai_img_response(response, save_dir)
        return ServiceResponse(
            ServiceExecStatus.SUCCESS,
            {"image_urls": urls},
        )
    except Exception as e:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            str(e),
        )


def openai_create_image_variation(
    image_url: str,
    api_key: str,
    n: int = 1,
    size: Literal[
        "256x256",
        "512x512",
        "1024x1024",
    ] = "256x256",
    save_dir: Optional[str] = None,
) -> ServiceResponse:
    """
    Create variations of an image and return the image URL(s) or save them
    locally.

    Args:
        image_url (`str`):
            The file path or URL to the image from which variations will be
            generated.
        api_key (`str`):
            The API key for the OpenAI API.
        n (`int`, defaults to `1`):
            The number of image variations to generate.
        size (`Literal["256x256", "512x512", "1024x1024"]`, defaults to `
        "256x256"`):
            The size of the generated image variations.
        save_dir (`Optional[str]`, defaults to `None`):
            The directory to save the generated image variations. If not
            specified, will return the web URLs.

    Returns:
        `ServiceResponse`:
            A dictionary with two variables: `status` and `content`.
            If `status` is `ServiceExecStatus.SUCCESS`,
            the `content` is a dict with key 'image_urls' and
            value is a list of the paths to the generated images or URLs.

    Example:

        .. code-block:: python

            image_url = "/path/to/image.png"
            api_key = "YOUR_API_KEY"
            print(openai_create_image_variation(image_url, api_key))

        > {
        >     'status': 'SUCCESS',
        >     'content': {'image_urls': ['VARIATION_URL1', 'VARIATION_URL2']}
        > }
    """
    os.environ["OPENAI_API_KEY"] = api_key
    client = OpenAI()
    image_url = os.path.abspath(image_url)
    with open(image_url, "rb") as img:
        response = client.images.create_variation(
            model="dall-e-2",
            image=img,
            n=n,
            size=size,
        )
    try:
        urls = _handle_openai_img_response(response, save_dir)
        return ServiceResponse(
            ServiceExecStatus.SUCCESS,
            {"image_urls": urls},
        )
    except Exception as e:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            str(e),
        )


def openai_image_to_text(
    image_urls: Union[str, Sequence[str]],
    api_key: str,
    prompt: str = "Describe the image",
    model: Literal["gpt-4o", "gpt-4-turbo"] = "gpt-4o",
) -> ServiceResponse:
    """
    Generate descriptive text for given image(s) using a specified model, and
    return the generated text.

    Args:
        image_urls (`Union[str, Sequence[str]]`):
            The URL or list of URLs pointing to the images that need to be
            described.
        api_key (`str`):
            The API key for the OpenAI API.
        prompt (`str`, defaults to `"Describe the image"`):
            The prompt that instructs the model on how to describe
            the image(s).
        model (`Literal["gpt-4o", "gpt-4-turbo"]`, defaults to `"gpt-4o"`):
            The model to use for generating the text descriptions.

    Returns:
        `ServiceResponse`:
            A dictionary with two variables: `status` and `content`.
            If `status` is `ServiceExecStatus.SUCCESS`,
            the `content` contains the generated text description(s).

    Example:

        .. code-block:: python

            image_url = "https://example.com/image.jpg"
            api_key = "YOUR_API_KEY"
            print(openai_image_to_text(image_url, api_key))

        > {
        >     'status': 'SUCCESS',
        >     'content': "A detailed description of the image..."
        > }
    """
    openai_chat_wrapper = OpenAIChatWrapper(
        config_name="image_to_text_service_call",
        model_name=model,
        api_key=api_key,
    )
    messages = MessageBase(
        name="service_call",
        role="user",
        content=prompt,
        url=image_urls,
    )
    openai_messages = openai_chat_wrapper.format(messages)
    try:
        response = openai_chat_wrapper(openai_messages)
        return ServiceResponse(ServiceExecStatus.SUCCESS, response.text)
    except Exception as e:
        return ServiceResponse(ServiceExecStatus.ERROR, str(e))


def openai_text_to_audio(
    text: str,
    api_key: str,
    save_dir: str,
    model: Literal["tts-1", "tts-1-hd"] = "tts-1",
    voice: Literal[
        "alloy",
        "echo",
        "fable",
        "onyx",
        "nova",
        "shimmer",
    ] = "alloy",
    speed: float = 1.0,
    res_format: Literal[
        "mp3",
        "wav",
        "opus",
        "aac",
        "flac",
        "wav",
        "pcm",
    ] = "mp3",
) -> ServiceResponse:
    """
    Convert text to an audio file using a specified model and voice, and save
    the audio file locally.

    Args:
        text (`str`):
            The text to convert to audio.
        api_key (`str`):
            The API key for the OpenAI API.
        save_dir (`str`):
            The directory where the generated audio file will be saved.
        model (`Literal["tts-1", "tts-1-hd"]`, defaults to `"tts-1"`):
            The model to use for text-to-speech conversion.
        voice (`Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]`,
        defaults to `"alloy"`):
            The voice to use for the audio output.
        speed (`float`, defaults to `1.0`):
            The speed of the audio playback. A value of 1.0 is normal speed.
        res_format (`Literal["mp3", "wav", "opus", "aac", "flac",
        "wav", "pcm"]`,
        defaults to `"mp3"`):
            The format of the audio file.

    Returns:
        `ServiceResponse`:
            A dictionary with two variables: `status` and `content`.
            If `status` is `ServiceExecStatus.SUCCESS`,
            the `content` is a dict with key 'audio_path' and
            value is the path to the generated audio file.

    Example:

        .. code-block:: python

            text = "Hello, welcome to the text-to-speech service!"
            api_key = "YOUR_API_KEY"
            save_dir = "./audio_files"
            print(openai_text_to_audio(text, api_key, save_dir))

        > {
        >     'status': 'SUCCESS',
        >     'content': {'audio_path': './audio_files/Hello,_welco.mp3'}
        > }
    """
    os.environ["OPENAI_API_KEY"] = api_key
    client = OpenAI()
    save_name = text[:15] if len(text) > 15 else text
    save_path = os.path.join(save_dir, f"{save_name}.{format}")
    try:
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            speed=speed,
            input=text,
            response_format=res_format,
        )
        response.stream_to_file(save_path)
        return ServiceResponse(
            ServiceExecStatus.SUCCESS,
            {"audio_path": save_path},
        )
        # stream_to_file method is deprecated.
        # But you still get the right output.
    except Exception as e:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            f"Error: Failed to generate audio. {str(e)}",
        )


def openai_audio_to_text(
    audio_file_url: str,
    api_key: str,
    language: Union[str, NotGiven] = NotGiven(),
    temperature: float = 0.2,
) -> ServiceResponse:
    """
    Convert an audio file to text using OpenAI's transcription service.

    Args:
        audio_file_url (`str`):
            The file path or URL to the audio file that needs to be
            transcribed.
        api_key (`str`):
            The API key for the OpenAI API.
        language (`Union[str, NotGiven]`, defaults to `NotGiven()`):
            The language of the audio. If not specified, the language will
            be auto-detected.
        temperature (`float`, defaults to `0.2`):
            The temperature for the transcription, which affects the
            randomness of the output.

    Returns:
        `ServiceResponse`:
            A dictionary with two variables: `status` and `content`.
            If `status` is `ServiceExecStatus.SUCCESS`,
            the `content` contains a dictionary with key 'transcription' and
            value as the transcribed text.

    Example:

        .. code-block:: python

            audio_file_url = "/path/to/audio.mp3"
            api_key = "YOUR_API_KEY"
            print(openai_audio_to_text(audio_file_url, api_key))

        > {
        >     'status': 'SUCCESS',
        >     'content': {'transcription': 'This is the transcribed text from
        the audio file.'}
        > }
    """
    os.environ["OPENAI_API_KEY"] = api_key
    client = OpenAI()
    audio_file_url = os.path.abspath(audio_file_url)
    with open(audio_file_url, "rb") as audio_file:
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper=1",
                file=audio_file,
                language=language,
                temperature=temperature,
            )
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                {"transcription": transcription.text},
            )
        except Exception as e:
            return ServiceResponse(
                ServiceExecStatus.ERROR,
                f"Error: Failed to transcribe audio {str(e)}",
            )
