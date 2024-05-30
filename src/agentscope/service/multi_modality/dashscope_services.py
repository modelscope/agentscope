# -*- coding: utf-8 -*-
"""Use DashScope API to generate images,
convert text to audio, and convert images to text.
Please refer to the official documentation for more details:
https://dashscope.aliyun.com/
"""

from typing import Union, Tuple, Optional

import os
import warnings
import shutil

import dashscope
from dashscope.audio.tts import SpeechSynthesizer

from agentscope.models import (
    DashScopeImageSynthesisWrapper,
    DashScopeMultiModalWrapper,
)

# SpeechSynthesizerWrapper is current not available


from agentscope.service.service_response import (
    ServiceResponse,
    ServiceExecStatus,
)


DASH_SCOPE_API_KEY: Optional[str] = None


def set_api_key(provided_api_key: Optional[str]) -> None:
    """Set the api key for the DashScope API.

    Args:
        api_key (`str`): The api key for the DashScope API.
    """
    global DASH_SCOPE_API_KEY
    if DASH_SCOPE_API_KEY is not None:
        return
    if provided_api_key is None:
        DASH_SCOPE_API_KEY = os.getenv("DASH_SCOPE_API_KEY")
        if DASH_SCOPE_API_KEY is None:
            raise ValueError(
                "Dashscope API key is not set.\
                             Please either set it\
                             as an environment variable\
                             or pass it as an argument\
                             When Calling the first time.",
            )
    else:
        DASH_SCOPE_API_KEY = provided_api_key
        warnings.warn(
            "We recommend setting the API key as an environment variable.",
        )


def dashscope_text_to_image(
    prompt: str,
    api_key: Optional[str] = None,
    number_of_images: int = 1,
    size: str = "1024*1024",
    model: str = "wanx-v1",
    saved_dir: Optional[str] = "./figs",
) -> ServiceResponse:
    """Generate an image based on a text prompt.

    Args:
        prompt (`str`): the text prompt.
        api_key (`Optional[str]`): The api key for the dashscope api.
        number_of_images (`int`, defaults to `1`): the number of images
        to generate.
        size (`str`, defaults to `1024*1024`): size of the image
        model (`str`, defaults to 'wanx-v1'): the model to use.
        saved_dir (`Optional[str]`, defaults to './figs'):
        the directory to save the
        generated images. If not specified, will return the web urls.
    Returns:
        ServiceResponse:
        A dictionary with two variables: `status` and`content`.
        If `status` is ServiceExecStatus.SUCCESS,
        the `content` is a dict with key 'fig_paths" and
        value is a list of the paths to the generated images.
    Example:
        prompt = "A beautiful sunset in the mountains"
        print( dashscope_text_to_image(prompt)) gives:
        {'status': 'SUCCESS',
        'content': {'fig_paths':
            ['FIG_RELATEIVE_PATH1',
            'FIG_RELATEIVE_PATH2']}}
    """
    set_api_key(api_key)
    assert DASH_SCOPE_API_KEY is not None, "API key is not set"
    text2img = DashScopeImageSynthesisWrapper(
        config_name="dashscope-text-to-image-service",
        model_name=model,
        api_key=DASH_SCOPE_API_KEY,
    )
    try:
        res = text2img(
            prompt=prompt,
            n=number_of_images,
            size=size,
            save_local=bool(saved_dir),
        )
        urls = res.image_urls
        if urls is not None:
            if saved_dir:
                if not os.path.exists(saved_dir):
                    os.makedirs(saved_dir)
                # move images to saved_dir
                if urls is not None:
                    new_urls = [
                        f"{saved_dir}/{prompt}_{i}.png"
                        for i in range(len(urls))
                    ]
                    for i, url in enumerate(urls):
                        shutil.move(url, new_urls[i])
                    urls = new_urls
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                {"fig_paths": urls},
            )
        else:
            return ServiceResponse(
                ServiceExecStatus.ERROR,
                {"error": "Failed to generate images"},
            )
    except Exception as e:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            {"error": str(e)},
        )


def dashscope_image_to_text(
    image_urls: Union[str, Tuple[str, ...]],
    prompt: str = "Describe the image",
    api_key: Optional[str] = None,
    model: str = "qwen-vl-plus",
) -> ServiceResponse:
    """Generate text based on an image.

    Args:
        image_urls (`str`): the url of single or multiple images.
        query_prompt (`str`, defaults to 'Describe the image' ):
        the text prompt.
        api_key (`Optional[str]`): The api key for the dashscope api.
        model (`str`, defaults to 'qwen-vl-plus'): the model to use.
    Returns:
        ServiceResponse:
        A dictionary with two variables: `status` and`content`.
        If `status` is ServiceExecStatus.SUCCESS,
        the `content` is the generated text.
    Example:
        image_url = "image.jpg"
        query_prompt = "Describe the image"
        print(image_to_text(image_url, query_prompt)) gives:
        {'status': 'SUCCESS', 'content': 'A beautiful sunset in the mountains'}
    """

    set_api_key(api_key)
    assert DASH_SCOPE_API_KEY is not None, "API key is not set"
    img2text = DashScopeMultiModalWrapper(
        config_name="dashscope-image-to-text-service",
        model_name=model,
        api_key=DASH_SCOPE_API_KEY,
    )
    if not isinstance(image_urls, tuple):
        image_urls = (image_urls,)
    try:
        img_abs_urls = [os.path.abspath(url) for url in image_urls]
    except Exception as e:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            {"error": str(e)},
        )
    contents = img2text.convert_url(img_abs_urls)
    contents.append({"text": prompt})
    # currently only support one round of conversation
    # if multiple rounds of conversation are needed,
    # it would be better to implement an Agent class
    sys_message = {
        "role": "system",
        "content": [{"text": "You are a helpful assistant"}],
    }
    user_message = {
        "role": "user",
        "content": contents,
    }
    messages = [sys_message, user_message]
    try:
        res = img2text(messages, stream=False)
        description = res.text
        if description is not None:
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                description,
            )
        else:
            return ServiceResponse(
                ServiceExecStatus.ERROR,
                {"error": "Failed to generate text"},
            )
    except Exception as e:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            {"error": str(e)},
        )


def dashscope_text_to_audio(
    text: str,
    api_key: Optional[str] = None,
    model: str = "sambert-zhichu-v1",
    sample_rate: int = 48000,
    saved_dir: str = "./audio",
) -> ServiceResponse:
    """Convert text to audio.

    Args:
        text (`str`): the text to convert.
        api_key (`Optional[str]`): The api key for the dashscope api.
        model (`str`, defaults to 'sambert-zhichu-v1'): the model to use.
        sample_rate (`int`, defaults to 48000): samplerate of the audio.
        saved_dir (`str`, defaults to './audio'): the directory
        to save the generated audio.
    Returns:
        ServiceResponse:
        A dictionary with two variables: `status` and`content`.
        If `status` is ServiceExecStatus.SUCCESS,
        the `content` contains a dictionary with key "audio_path" and
        and value is the path to the generated audio.
    Example:
        text = "How is the weather today?"
        print(text_to_audio(text)) gives:
        {'status': 'SUCCESS',
        'content': {"audio_path": "AUDIO_RELATEIVE_PATH"}}
    """
    set_api_key(api_key)
    assert DASH_SCOPE_API_KEY is not None, "API key is not set"
    dashscope.api_key = DASH_SCOPE_API_KEY

    res = SpeechSynthesizer.call(
        model=model,
        text=text,
        sample_rate=sample_rate,
    )
    audio_data = res.get_audio_data()
    if audio_data is not None:
        print("Audio data is not None, proceeding with file operations.")
        if not os.path.exists(saved_dir):
            os.makedirs(saved_dir)
        text = text[0:15] if len(text) > 15 else text
        audio_path = f"{saved_dir}/{text}.wav"
        with open(audio_path, "wb") as f:
            f.write(audio_data)
        return ServiceResponse(
            ServiceExecStatus.SUCCESS,
            {"audio_path": audio_path},
        )
    else:
        print("Audio data is None, returning error.")
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            {"error": "Failed to generate audio"},
        )
