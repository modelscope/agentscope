# -*- coding: utf-8 -*-
""" Tools for agentscope """
import base64
import datetime
import json
import secrets
import string
from typing import Any

from urllib.parse import urlparse

import requests
from loguru import logger


def extract_json_str(json_str: str) -> str:
    """Extract json from the string and try to fix its format manually."""
    # Start index of character '{'
    try:
        start_index = json_str.index("{")
    except ValueError:
        json_str = "{" + json_str
        start_index = 0

    # End index of character '}'
    try:
        end_index = json_str.rindex("}")
    except ValueError:
        json_str += "}"
        end_index = len(json_str) - 1

    json_str = json_str[: end_index + 1]

    return json_str[start_index:]


def _get_timestamp(
    format_: str = "%Y-%m-%d %H:%M:%S",
    time: datetime.datetime = None,
) -> str:
    """Get current timestamp."""
    if time is None:
        return datetime.datetime.now().strftime(format_)
    else:
        return time.strftime(format_)


def to_openai_dict(item: dict) -> dict:
    """Convert `Msg` to `dict` for OpenAI API."""
    clean_dict = {}

    if "name" in item:
        clean_dict["name"] = item["name"]

    if "role" in item:
        clean_dict["role"] = item["role"]
    else:
        clean_dict["role"] = "assistant"

    if "content" in item:
        clean_dict["content"] = item["content"]
    else:
        logger.warning(
            f"Message {item} doesn't have `content` field for " f"OpenAI API.",
        )

    return clean_dict


def to_dialog_str(item: dict) -> str:
    """Convert a dict into string prompt style."""
    speaker = item.get("name", None) or item.get("role", None)
    content = item.get("content", None)

    if content is None:
        return str(item)

    if speaker is None:
        return content
    else:
        return f"{speaker}: {content}"


def _to_openai_image_url(url: str) -> str:
    """Convert an image url to openai format. If the given url is a local
    file, it will be converted to base64 format. Otherwise, it will be
    returned directly.

    Args:
        url (`str`):
            The local or public url of the image.
    """
    # See https://platform.openai.com/docs/guides/vision for details of
    # support image extensions.
    image_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
    )

    parsed_url = urlparse(url)

    # Checking for HTTP(S) image links
    if parsed_url.scheme in ["http", "https"]:
        lower_path = parsed_url.path.lower()
        if lower_path.endswith(image_extensions):
            return url

    # Check if it is a local file
    elif parsed_url.scheme == "file" or not parsed_url.scheme:
        if parsed_url.path.lower().endswith(image_extensions):
            with open(parsed_url.path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode(
                    "utf-8",
                )
            extension = parsed_url.path.lower().split(".")[-1]
            mime_type = f"image/{extension}"
            return f"data:{mime_type};base64,{base64_image}"

    raise TypeError(f"{url} should be end with {image_extensions}.")


def _download_file(url: str, path_file: str, max_retries: int = 3) -> bool:
    """Download file from the given url and save it to the given path.

    Args:
        url (`str`):
            The url of the file.
        path_file (`str`):
            The path to save the file.
        max_retries (`int`, defaults to `3`)
            The maximum number of retries when fail to download the file.
    """
    for n_retry in range(1, max_retries + 1):
        response = requests.get(url, stream=True)
        if response.status_code == requests.codes.ok:
            with open(path_file, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return True
        else:
            logger.warning(
                f"Failed to download file from {url} (status code: "
                f"{response.status_code}). Retry {n_retry}/{max_retries}.",
            )
    return False


def _generate_random_code(
    length: int = 6,
    uppercase: bool = True,
    lowercase: bool = True,
    digits: bool = True,
) -> str:
    """Get random code."""
    characters = ""
    if uppercase:
        characters += string.ascii_uppercase
    if lowercase:
        characters += string.ascii_lowercase
    if digits:
        characters += string.digits
    return "".join(secrets.choice(characters) for i in range(length))


def _is_json_serializable(obj: Any) -> bool:
    """Check if the given object is json serializable."""
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False
