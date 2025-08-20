# -*- coding: utf-8 -*-
"""Make request"""
import time
from enum import Enum
from typing import Union, Optional, Generator
import base64
import json
import httpx


class AuthTypeEnum(str, Enum):
    """Auth type for make request"""

    NO_AUTH = "NoAuth"
    BASIC_AUTH = "BasicAuth"
    BEARER_AUTH = "BearerAuth"


class BearerAuth(httpx.Auth):
    """An authentication class for Bearer token-based authentication."""

    def __init__(self, token: str) -> None:
        self.token = token

    def auth_flow(self, request: httpx.Request) -> Generator:
        """Modifies the outgoing HTTP request to include a Bearer token in
        the Authorization header."""
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


def create_timeout_config(
    timeout_settings: dict,
    default_connect: int = 3,
    default_read: int = 4,
    default_write: int = 5,
) -> httpx.Timeout:
    """
    Creates an httpx.Timeout object based on provided timeout settings
    dictionary and default values.

    Parameters:
    - timeout_settings: A dictionary containing the timeout settings for
    'connect', 'read', and 'write'.
    - default_connect: Default timeout value for connection attempts.
    - default_read: Default timeout value for reading data.
    - default_write: Default timeout value for writing data.

    Returns:
    - An httpx.Timeout object configured with the specified timeouts.
    """
    connect_timeout = timeout_settings.get("connect", default_connect)
    read_timeout = timeout_settings.get("read", default_read)
    write_timeout = timeout_settings.get("write", default_write)

    return httpx.Timeout(
        None,
        connect=connect_timeout,
        read=read_timeout,
        write=write_timeout,
    )


# pylint: disable=too-many-branches
def make_request(
    url: str,
    method: str = "post",
    auth: Optional[Union[BearerAuth, tuple]] = None,
    headers: dict = None,
    body_type: str = "json",
    body: Optional[Union[str, bytes, bytearray, dict]] = None,
    params: dict = None,
    timeout_config: dict = None,
    max_retries: int = 1,
    retry_delay: int = None,
) -> str:
    """
    Send an HTTP request to a specified URL with optional parameters.
    """

    method = method.lower()
    timeout = create_timeout_config(timeout_config)
    attempts = 0
    last_exception = None

    while attempts < max_retries:
        try:
            with httpx.Client(timeout=timeout) as client:
                request_method = getattr(client, method, None)
                if not request_method:
                    raise AttributeError(f"Unsupported method: {method}")

                if method in ["get", "head"]:
                    response = request_method(
                        url,
                        headers=headers,
                        auth=auth,
                        params=params,
                    )
                else:
                    if body_type == "json":
                        if isinstance(body, (str, bytes, bytearray)):
                            try:
                                body = json.loads(body)
                            except json.JSONDecodeError:
                                pass
                    response = request_method(
                        url,
                        headers=headers,
                        auth=auth,
                        json=body if body_type == "json" else None,
                        data=body if body_type != "json" else None,
                        params=params,
                    )

                response_dict = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "history": [str(res.url) for res in response.history],
                    "cookies": dict(response.cookies),
                }
                try:
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        response_dict["body"] = response.json()
                    elif "text" in content_type or "html" in content_type:
                        response_dict["body"] = response.text
                    else:
                        response_dict["body"] = base64.b64encode(
                            response.content,
                        ).decode(
                            "utf-8",
                        )
                except ValueError as e:
                    response_dict["body"] = base64.b64encode(
                        response.content,
                    ).decode(
                        "utf-8",
                    )
                    response_dict["error"] = str(e)
                return json.dumps(response_dict)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_exception = e
            attempts += 1
            if attempts < max_retries and retry_delay is not None:
                time.sleep(retry_delay / 1000)
    error_dict = {
        "status_code": 0,
        "error": (
            str(last_exception)
            if last_exception
            else "Request failed after maximum retries"
        ),
        "url": url,
    }
    raise ValueError(json.dumps(error_dict))
