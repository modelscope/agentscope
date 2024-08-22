# -*- coding: utf-8 -*-
"""web ui utils"""
import os
import threading
from typing import Optional
import hashlib
from multiprocessing import Queue
from queue import Empty
from collections import defaultdict

from PIL import Image

from dashscope.audio.asr import RecognitionCallback, Recognition

SYS_MSG_PREFIX = "【SYSTEM】"

thread_local_data = threading.local()


def init_uid_queues() -> dict:
    """Initializes and returns a dictionary of user-specific queues."""
    return {
        "glb_queue_chat_msg": Queue(),
        "glb_queue_user_input": Queue(),
        "glb_queue_reset_msg": Queue(),
    }


glb_uid_dict = defaultdict(init_uid_queues)


def send_msg(
    msg: str,
    is_player: bool = False,
    role: Optional[str] = None,
    uid: Optional[str] = None,
    flushing: bool = False,
    avatar: Optional[str] = None,
    msg_id: Optional[str] = None,
) -> None:
    """Sends a message to the web UI."""
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    if is_player:
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
    else:
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
    glb_queue_user_input = glb_uid_dict[uid]["glb_queue_user_input"]
    glb_queue_user_input.put([None, msg])


def get_player_input(
    timeout: Optional[int] = None,
    uid: Optional[str] = None,
) -> str:
    """Gets player input from the web UI or command line."""
    global glb_uid_dict
    glb_queue_user_input = glb_uid_dict[uid]["glb_queue_user_input"]

    if timeout:
        try:
            content = glb_queue_user_input.get(block=True, timeout=timeout)[1]
        except Empty as exc:
            raise TimeoutError("timed out") from exc
    else:
        content = glb_queue_user_input.get(block=True)[1]
    if content == "**Reset**":
        glb_uid_dict[uid] = init_uid_queues()
        raise ResetException
    return content


def send_reset_msg(uid: Optional[str] = None) -> None:
    """Sends a reset message to the web UI."""
    uid = check_uuid(uid)
    global glb_uid_dict
    glb_queue_reset_msg = glb_uid_dict[uid]["glb_queue_reset_msg"]
    glb_queue_reset_msg.put([None, "**Reset**"])
    send_player_input("**Reset**", uid)


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
            import gradio as gr

            raise gr.Error("Please login first")
        uid = "local_user"
    return uid


def generate_image_from_name(name: str) -> str:
    """Generates an image based on the hash of the given name."""
    from agentscope.manager import FileManager

    file_manager = FileManager.get_instance()

    # Using hashlib to generate a hash of the name
    hash_func = hashlib.md5()
    hash_func.update(name.encode("utf-8"))
    hash_value = hash_func.hexdigest()

    # Extract the first 6 characters of the hash value as the hexadecimal
    # representation of the color
    # generate a color value between #000000 and #ffffff
    color_hex = "#" + hash_value[:6]
    color_rgb = Image.new("RGB", (1, 1), color_hex).getpixel((0, 0))

    # If the image does not exist, generate and save it
    width, height = 200, 200
    image = Image.new("RGB", (width, height), color_rgb)

    image_filepath = file_manager.save_image(image, f"{name}_image.png")

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


def cycle_dots(text: str, num_dots: int = 3) -> str:
    """display thinking dots before agent reply"""
    current_dots = len(text) - len(text.rstrip("."))
    next_dots = (current_dots + 1) % (num_dots + 1)
    if next_dots == 0:
        next_dots = 1
    return text.rstrip(".") + "." * next_dots


def user_input(
    prefix: str = "User input: ",
    timeout: Optional[int] = None,
) -> str:
    """get user input"""
    if hasattr(thread_local_data, "uid"):
        get_reset_msg(uid=thread_local_data.uid)
        content = get_player_input(
            timeout=timeout,
            uid=thread_local_data.uid,
        )
    else:
        if timeout:
            from inputimeout import inputimeout, TimeoutOccurred

            try:
                content = inputimeout(prefix, timeout=timeout)
            except TimeoutOccurred as exc:
                raise TimeoutError("timed out") from exc
        else:
            content = input(prefix)
    return content
