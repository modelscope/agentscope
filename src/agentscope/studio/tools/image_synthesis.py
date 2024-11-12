# -*- coding: utf-8 -*-
"""Text to Image"""
from typing import Optional, Literal

from agentscope.message import Msg
from agentscope.service import dashscope_text_to_image, ServiceExecStatus


def image_synthesis(
    msg: Msg,
    api_key: str,
    n: int = 1,
    size: Literal["1024*1024", "720*1280", "1280*720"] = "1024*1024",
    model: str = "wanx-v1",
    save_dir: Optional[str] = None,
) -> Msg:
    """Generate image(s) based on the given Msg, and return Msg.

    Args:
        msg (`Msg`):
            The msg to generate image.
        api_key (`str`):
            The api key for the dashscope api.
        n (`int`, defaults to `1`):
            The number of images to generate.
        size (`Literal["1024*1024", "720*1280", "1280*720"]`, defaults to
        `"1024*1024"`):
            Size of the image.
        model (`str`, defaults to '"wanx-v1"'):
            The model to use.
        save_dir (`Optional[str]`, defaults to 'None'):
            The directory to save the generated images. If not specified,
            will return the web urls.

    Returns:
        Msg
    """

    res = dashscope_text_to_image(
        prompt=msg.content,
        api_key=api_key,
        n=n,
        size=size,
        model=model,
        save_dir=save_dir,
    )

    if res.status == ServiceExecStatus.SUCCESS:
        return Msg(
            name="ImageSynthesis",
            content="Image synthesis succeed.",
            url=res.content["image_urls"],
            role="assistant",
            echo=True,
        )
    else:
        return Msg(
            name="ImageSynthesis",
            content=res.content,
            role="assistant",
            echo=True,
        )
