# -*- coding: utf-8 -*-
"""web ui utils"""
import os
from typing import Optional
import hashlib
from multiprocessing import Queue
from collections import defaultdict

from PIL import Image
import gradio as gr

from dashscope.audio.asr import RecognitionCallback, Recognition

SYS_MSG_PREFIX = "【系统】"

USE_WEB_UI = False

MAX_ROLE_NUM = 20


def enable_web_ui() -> None:
    """Enables the web UI functionality."""
    global USE_WEB_UI
    USE_WEB_UI = True


def init_uid_queues() -> dict:
    """Initializes and returns a dictionary of user-specific queues."""
    return {
        "glb_queue_chat_msg": Queue(),
        "glb_queue_chat_input": Queue(),
        "glb_queue_reset_msg": Queue(),
    }


glb_uid_dict = defaultdict(init_uid_queues)


def send_chat_msg(
    msg: str,
    role: Optional[str] = None,
    uid: Optional[str] = None,
    flushing: bool = False,
    avatar: Optional[str] = None,
    msg_id: Optional[str] = None,
) -> None:
    """Sends a chat message to the web UI."""
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    glb_queue_chat_msg.put(
        [
            None,
            {
                "text": msg,
                "name": role,
                "flushing": flushing,
                "avatar": avatar,
                "id": msg_id,
            },
        ],
    )


def send_player_msg(
    msg: str,
    role: str = "Me",
    uid: Optional[str] = None,
    flushing: bool = False,
    avatar: Optional[str] = None,
) -> None:
    """Sends a player message to the web UI."""
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    glb_queue_chat_msg.put(
        [
            {
                "text": msg,
                "name": role,
                "flushing": flushing,
                "avatar": avatar,
            },
            None,
        ],
    )


def get_chat_msg(uid: Optional[str] = None) -> list:
    """Retrieves the next chat message from the queue, if available."""
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    if not glb_queue_chat_msg.empty():
        line = glb_queue_chat_msg.get(block=False)
        if line is not None:
            return line
    return []


def send_player_input(msg: str, uid: Optional[str] = None) -> None:
    """Sends player input to the web UI."""
    global glb_uid_dict
    glb_queue_chat_input = glb_uid_dict[uid]["glb_queue_chat_input"]
    glb_queue_chat_input.put([None, msg])


def get_player_input(
    uid: Optional[str] = None,
) -> list[str]:
    """Gets player input from the web UI or command line."""
    global glb_uid_dict
    glb_queue_chat_input = glb_uid_dict[uid]["glb_queue_chat_input"]
    content = glb_queue_chat_input.get(block=True)[1]
    if content == "**Reset**":
        glb_uid_dict[uid] = init_uid_queues()
        raise ResetException
    return content


def send_reset_msg(msg: str, uid: Optional[str] = None) -> None:
    """Sends a reset message to the web UI."""
    global glb_uid_dict
    glb_queue_reset_msg = glb_uid_dict[uid]["glb_queue_reset_msg"]
    glb_queue_reset_msg.put([None, msg])


def get_reset_msg(uid: Optional[str] = None) -> None:
    """Retrieves a reset message from the queue, if available."""
    global glb_uid_dict
    glb_queue_reset_msg = glb_uid_dict[uid]["glb_queue_reset_msg"]
    if not glb_queue_reset_msg.empty():
        content = glb_queue_reset_msg.get(block=True)[1]
        if content == "**Reset**":
            glb_uid_dict[uid] = init_uid_queues()
            raise ResetException


class ResetException(Exception):
    """Custom exception to signal a reset action in the application."""


def check_uuid(uid: Optional[str]) -> str:
    """Checks whether a UUID is provided or generates a default one."""
    if not uid or uid == "":
        if os.getenv("MODELSCOPE_ENVIRONMENT") == "studio":
            raise gr.Error("Please login first")
        uid = "local_user"
    return uid


def generate_image_from_name(name: str) -> str:
    """Generates an image based on the hash of the given name."""
    from agentscope.file_manager import file_manager

    # Using hashlib to generate a hash of the name
    hash_func = hashlib.md5()
    hash_func.update(name.encode("utf-8"))
    hash_value = hash_func.hexdigest()

    # Extract the first 6 characters of the hash value as the hexadecimal
    # representation of the color
    # generate a color value between #000000 and #ffffff
    color_hex = "#" + hash_value[:6]
    color_rgb = Image.new("RGB", (1, 1), color_hex).getpixel((0, 0))

    image_filepath = os.path.join(file_manager.dir_root, f"{name}_image.png")

    # Check if the image already exists
    if os.path.exists(image_filepath):
        return image_filepath

    # If the image does not exist, generate and save it
    width, height = 200, 200
    image = Image.new("RGB", (width, height), color_rgb)

    image.save(image_filepath)

    return image_filepath


def audio2text(audio_path: str) -> str:
    """Converts audio file at the given path to text using ASR."""
    # dashscope.api_key = ""
    callback = RecognitionCallback()
    rec = Recognition(
        model="paraformer-realtime-v1",
        format="wav",
        sample_rate=16000,
        callback=callback,
    )

    result = rec.call(audio_path)
    return " ".join([s["text"] for s in result["output"]["sentence"]])
