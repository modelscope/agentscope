# -*- coding: utf-8 -*-
import os
from typing import List

import gradio as gr

from colorist import BgBrightColor
import inquirer
from multiprocessing import Queue
from collections import defaultdict
from dashscope.audio.asr import RecognitionCallback, Recognition

import hashlib
from PIL import Image

SYS_MSG_PREFIX = "【系统】"
DEFAULT_AGENT_IMG_DIR = "/tmp/as_game/config/"
OPENING_ROUND = 3
REVISION_ROUND = 3

USE_WEB_UI = False

MAX_ROLE_NUM = 20


def get_use_web_ui() -> bool:
    global USE_WEB_UI
    return USE_WEB_UI


def disable_web_ui() -> None:
    global USE_WEB_UI
    USE_WEB_UI = False


def enable_web_ui() -> None:
    global USE_WEB_UI
    USE_WEB_UI = True


def init_uid_queues() -> dict:
    return {
        "glb_queue_chat_msg": Queue(),
        "glb_queue_chat_input": Queue(),
        "glb_queue_clue": Queue(),
        "glb_queue_story": Queue(),
        "glb_queue_reset_msg": Queue(),
    }


glb_uid_dict = defaultdict(init_uid_queues)


def send_chat_msg(
    msg,
    role=None,
    uid=None,
    flushing=False,
    avatar="./assets/bot.jpg",
    id=None,
) -> None:
    print("send_chat_msg:", msg)
    if get_use_web_ui():
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
                    "id": id,
                },
            ],
        )


def send_player_msg(
    msg,
    role="Me",
    uid=None,
    flushing=False,
    avatar="./assets/user.jpg",
):
    print("send_player_msg:", msg)
    if get_use_web_ui():
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


def get_chat_msg(uid=None):
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    if not glb_queue_chat_msg.empty():
        line = glb_queue_chat_msg.get(block=False)
        if line is not None:
            return line
    return None


def send_player_input(msg, role="Me", uid=None):
    if get_use_web_ui():
        global glb_uid_dict
        glb_queue_chat_input = glb_uid_dict[uid]["glb_queue_chat_input"]
        glb_queue_chat_input.put([None, msg])

def get_player_input(name=None, uid=None):
    global glb_uid_dict
    if get_use_web_ui():
        print("wait queue input")
        glb_queue_chat_input = glb_uid_dict[uid]["glb_queue_chat_input"]
        content = glb_queue_chat_input.get(block=True)[1]
        print(content)
        if content == "**Reset**":
            glb_uid_dict[uid] = init_uid_queues()
            raise ResetException
    else:
        content = input(f"{name}: ")
    return content


def send_reset_msg(msg, uid=None):
    if get_use_web_ui():
        global glb_uid_dict
        glb_queue_reset_msg = glb_uid_dict[uid]["glb_queue_reset_msg"]
        glb_queue_reset_msg.put([None, msg])


def get_reset_msg(name=None, uid=None):
    global glb_uid_dict
    if get_use_web_ui():
        print("wait queue input")
        glb_queue_reset_msg = glb_uid_dict[uid]["glb_queue_reset_msg"]
        if not glb_queue_reset_msg.empty():
            content = glb_queue_reset_msg.get(block=True)[1]
            print(content)
            if content == "**Reset**":
                glb_uid_dict[uid] = init_uid_queues()
                raise ResetException
    return None


def query_answer(questions: List, key="ans", uid=None):
    if get_use_web_ui():
        return get_player_input(uid=uid)
    else:
        answer = [inquirer.prompt(questions)[key]]  # return list
    return answer


class ResetException(Exception):
    pass


def cycle_dots(text: str, num_dots: int = 3) -> str:
    # Count the number of points at the end of the current sentence
    current_dots = len(text) - len(text.rstrip("."))
    # Calculate the number of points in the next state
    next_dots = (current_dots + 1) % (num_dots + 1)
    if next_dots == 0:
        # avoid '...0', should be '.'
        next_dots = 1
    # Remove the point at the end of the current sentence and add the point
    # of the next state
    return text.rstrip(".") + "." * next_dots


def check_uuid(uid):
    if not uid or uid == "":
        if os.getenv("MODELSCOPE_ENVIRONMENT") == "studio":
            raise gr.Error("Please login first")
        else:
            uid = "local_user"
    return uid


def generate_image_from_name(name):
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

    image_filepath = file_manager.path_db + f"{name}_image.png"

    # Check if the image already exists
    if os.path.exists(image_filepath):
        print(f"Image already exists at {image_filepath}")
        return image_filepath

    # If the image does not exist, generate and save it
    width, height = 200, 200
    image = Image.new("RGB", (width, height), color_rgb)

    image.save(image_filepath)

    return image_filepath


def audio2text(audio_path: str) -> str:
    """Convert audio to text."""
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
