# -*- coding: utf-8 -*-
"""Use DashScope API to generate images,
convert text to audio, and convert images to text.
Please refer to the official documentation for more details:
https://dashscope.aliyun.com/
"""
from http import HTTPStatus
from typing import Union, Tuple

import os
import requests
import nest_asyncio

import dashscope
from dashscope.audio.tts import SpeechSynthesizer


from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


def dashscope_text_to_image(
    prompt: str,
    api_key: str,
    number_of_images: int = 1,
    size: str = "1024*1024",
    model: str = "wanx-v1",
    saved_dir: str = "./figs",
) -> ServiceResponse:
    """Generate an image based on a text prompt.

    Args:
        prompt (`str`): the text prompt.
        api_key (`str`): The api key for the dashscope api.
        number_of_images (`int`, defaults to `1`): the number of images
        to generate.
        size (`str`, defaults to `1024*1024`): size of the image
        model (`str`, defaults to 'wanx-v1'): the model to use.
        saved_dir (`str`, defaults to './figs'): the directory to save the
        generated images.
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

    dashscope.api_key = api_key
    res = dashscope.ImageSynthesis.call(
        model=model,
        prompt=prompt,
        n=number_of_images,
        size=size,
    )
    if res.status_code == HTTPStatus.OK:
        if res.output.task_status == "SUCCEEDED":
            results = res.output.results
            # write iamge to disk
            # if saved_dir does not exist, create it
            fig_paths = []
            if not os.path.exists(saved_dir):
                os.makedirs(saved_dir)
            for i, result in enumerate(results):
                fig_path = f"{saved_dir}/{prompt}_{i}.png"
                with open(fig_path, "wb+") as f:
                    f.write(requests.get(result.url).content)
                fig_paths.append(fig_path)
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                {"file_paths": fig_paths},
            )
        else:
            err_msg = f"Task failed with status {res.output.task_status}"
            err_msg += res.message
            return ServiceResponse(
                ServiceExecStatus.ERROR,
                {"error": err_msg},
            )
    else:
        err_msg = f"Error in calling the API: {res.status_code}"
        err_msg += res.message
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            {"error": err_msg},
        )


def dashscope_image_to_text(
    image_urls: Union[str, Tuple[str, ...]],
    prompt: str,
    api_key: str,
    model: str = "qwen-vl-plus",
) -> ServiceResponse:
    """Generate text based on an image.

    Args:
        image_urls (`str`): the url of single or multiple images.
        query_prompt (`str`): the text prompt.
        api_key (`str`): The api key for the dashscope api.
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
    dashscope.api_key = api_key
    if not isinstance(image_urls, tuple):
        image_urls = (image_urls,)
    contents = []
    for image_url in image_urls:
        # check image url is local content or remote content
        if not image_url.startswith(("http://", "https://")):
            # check if the file exists
            if not os.path.exists(image_url):
                return ServiceResponse(
                    ServiceExecStatus.ERROR,
                    {"error": f"File {image_url} does not exist"},
                )
            image_path = str(os.path.abspath(image_url))
            image_url = f"file://{image_path}"
            contents.append(
                {
                    "image": image_url,
                },
            )
    contents.append(
        {
            "text": prompt,
        },
    )
    # currently only support one round of conversation
    # if multiple rounds of conversation are needed,
    # it would be better to implement an Agent class
    sys_message = {
        "role": "system",
        "content": [
            {
                "text": "You are a helpful assistant",
            },
        ],
    }
    user_message = {
        "role": "user",
        "content": contents,
    }
    messages = [sys_message, user_message]
    res = dashscope.MultiModalConversation.call(
        model=model,
        messages=messages,
    )
    if res.status_code == HTTPStatus.OK:
        description = res.output.choices[0].message.content[0]["text"]
        return ServiceResponse(
            ServiceExecStatus.SUCCESS,
            description,
        )
    else:
        err_msg = f"Error in calling the API: {res.status_code}"
        err_msg += res.message
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            {"error": err_msg},
        )


def dashscope_text_to_audio(
    text: str,
    api_key: str,
    model: str = "sambert-zhichu-v1",
    sample_rate: int = 48000,
    saved_dir: str = "./audio",
) -> ServiceResponse:
    """Convert text to audio.

    Args:
        text (`str`): the text to convert.
        api_key (`str`): The api key for the dashscope api.
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
    dashscope.api_key = api_key
    # if nested_asyncio is not applied,
    # error will occur when calling the API
    nest_asyncio.apply()
    res = SpeechSynthesizer.call(
        model=model,
        text=text,
        sample_rate=sample_rate,
    )
    if res.get_audio_data() is not None:
        if not os.path.exists(saved_dir):
            os.makedirs(saved_dir)

        audio_path = f"{saved_dir}/{text}.wav"
        with open(audio_path, "wb") as f:
            f.write(res.get_audio_data())
        return ServiceResponse(
            ServiceExecStatus.SUCCESS,
            {"audio_path": audio_path},
        )
    else:
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            {"error": "Failed to generate audio"},
        )
