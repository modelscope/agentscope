# -*- coding: utf-8 -*-
"""
Post for removing background from images using a web API.
"""

import os
from typing import Union, Tuple
from io import BytesIO

import json5
from PIL import Image
import requests

from agentscope.message import Msg
from agentscope.studio.tools.utils import is_url, is_local_file


def web_post(
    url: str,
    output_path: str = "",
    output_type: str = "image",
    msg: Msg = None,
    image_path_or_url: str = None,
    data: Union[str, dict] = None,
    headers: dict = None,
    json: dict = False,
    **kwargs: dict,
) -> Msg:
    """
    Send an HTTP POST request, upload an image and process the response.

    :param url: URL to send the request to
    :param output_path: Path to save the output image
    :param output_type: Type of the output, can be "image" or "text" or
        "audio" or "video"
    :param msg: Msg object containing the image URL
    :param image_path_or_url: Local path or URL of the image
    :param data: Data to send, can be a string or a dictionary
    :param headers: Headers to send with the request
    :param json: JSON data to send
    :param kwargs: Additional request parameters
    :return: Path to the saved output image
    """
    # Parse image source
    image_url, image_path = parse_image_source(msg, image_path_or_url)

    if data and isinstance(data, str):
        data = json5.loads(data)

    if json and isinstance(json, str):
        json = json5.loads(json)

    if headers and isinstance(headers, str):
        headers = json5.loads(headers)

    # Update the data or kwargs parameters
    if image_url:
        if isinstance(data, dict):
            data["image_url"] = image_url
    elif image_path:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        kwargs["files"] = {
            "image_file": (
                os.path.basename(image_path),
                image_data,
            ),
        }

    response = requests.post(
        url,
        data=data,
        json=json,
        headers=headers,
        **kwargs,
    )
    return process_response(response, output_path, output_type)


def parse_image_source(msg: Msg, image_path_or_url: str) -> Tuple[str, str]:
    """
    Parse the image source from msg or image_path_or_url.

    :param msg: Msg object containing the image URL
    :param image_path_or_url: Local path or URL of the image
    :return: Tuple containing image_url and image_path
    """
    image_url = ""
    image_path = ""

    if msg and msg.url:
        if isinstance(msg.url, list):
            image_url = msg.url[0]
        else:
            image_url = msg.url
    if image_path_or_url:
        if is_url(image_path_or_url):
            image_url = image_path_or_url
        elif is_local_file(image_path_or_url):
            image_path = image_path_or_url

    return image_url, image_path


def process_response(
    response: requests.Response,
    output_path: str,
    output_type: str = "image",
) -> Msg:
    """
    Process the HTTP response and save the image if successful.

    :param response: HTTP response object
    :param output_path: Path to save the output image
    :param output_type: Type of the output, can be "image" or "text" or
        "audio" or "video"
    :return: Path to the saved output image
    """
    if response.status_code == requests.codes.ok:
        if output_type == "image":
            # Read the response content into a BytesIO object
            img = Image.open(BytesIO(response.content))

            # Display the image
            img.show()

            # Save the image
            if output_path:
                img.save(output_path)
        # TODO: Handle other output types
        elif output_type == "text":
            # Save the text content to a file
            if output_path:
                with open(output_path, "w", encoding="utf-8") as text_file:
                    text_file.write(response.text)
        elif output_type in ["audio", "video"]:
            # Save the audio or video content to a file
            if output_path:
                with open(output_path, "wb") as media_file:
                    media_file.write(response.content)
        else:
            raise ValueError(f"Unsupported output type: {output_type}")
    else:
        # Print the error message
        print("Error:", response.status_code, response.text)

    return Msg(
        name="Post",
        role="assistant",
        content=output_path,
        url=output_path,
        echo=True,
    )
