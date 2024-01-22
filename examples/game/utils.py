# -*- coding: utf-8 -*-
import os
import pickle
from typing import Optional, List
from datetime import datetime
from colorist import BgBrightColor
import inquirer
import random
from multiprocessing import Queue
from collections import defaultdict
from dataclasses import dataclass
from agentscope.message import Msg
from enums import StagePerNight
from pathlib import Path
from queue import Empty

import gradio as gr


USE_WEB_UI = False


class GameCheckpoint:
    def __init__(
        self,
        stage_per_night: StagePerNight,
        customers: list,
        cur_plots: list,
        done_plots: list,
        invited_customers: list,
        visit_customers: list,
    ):
        self.stage_per_night = stage_per_night
        self.customers = customers
        self.cur_plots = cur_plots
        self.done_plots = done_plots
        self.invited_customers = invited_customers
        self.visit_customers = visit_customers


def save_game_checkpoint(
    checkpoint: GameCheckpoint,
    checkpoint_prefix: str,
) -> None:
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_path = checkpoint_prefix + time_str
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint, f)


def load_game_checkpoint(checkpoint_path: str) -> GameCheckpoint:
    with open(checkpoint_path, "rb") as f:
        return pickle.load(f)


def speak_print(m: Msg):
    print(f"{BgBrightColor.BLUE}{m.name}{BgBrightColor.OFF}: {m.content}")


def get_avatar_files(assets_path="assets"):
    files = Path(assets_path).glob("*avatar*")
    return [str(file) for file in files]


def get_a_random_avatar():
    return random.choices(get_avatar_files())


def check_active_plot(
    plots: list[dict],
    curr_done: Optional[int],
) -> tuple[list[str], list[int]]:
    """
    params: plots: list of plots
    params: curr_done: current done plot index
    return
    to_be_activated: list of customers to be activate
    active_plots: list of active plots
    Current plots are list of dicts as following:
    [
        {
            "main_roles": ["customer1", "customer2"],
            "predecessor_plots": None,
            "supporting_roles": ["customer3", "customer4"]
        },
        {
            "main_roles": ["customer3", "customer4"],
            "predecessor_plots": [0],
            "supporting_roles": ["customer2", "customer5"],
        },
        ...
    ]
    """
    # insure all plots have been added 'state'
    for p in plots:
        if "state" not in p:
            p["state"] = "non-active"
    to_be_activated = []
    active_plots = []

    if curr_done is not None:
        if isinstance(curr_done, int):
            plots[curr_done]["state"] = "done"
        if isinstance(curr_done, list):
            for i in curr_done:
                plots[i]["state"] = "done"

    # activate those with dependencies and the dependencies are done
    for idx, p in enumerate(plots):
        # activate all plots has no dependency and not done yet
        if p["predecessor_plots"] is None and p["state"] == "non-active":
            to_be_activated += p["main_roles"]
            to_be_activated += (
                p["supporting_roles"]
                if p["supporting_roles"] is not None
                else []
            )
            p["state"] = "active"
            active_plots.append(idx)
        elif p["predecessor_plots"] is not None:
            to_activate = all(
                [
                    plots[pre_p]["state"] == "done"
                    for pre_p in p["predecessor_plots"]
                ],
            )

            if to_activate:
                p["state"] = "active"
                to_be_activated += p["main_roles"]
                to_be_activated += (
                    p["supporting_roles"]
                    if p["supporting_roles"] is not None
                    else []
                )
                active_plots.append(idx)
        elif p["state"] == "active":
            active_plots.append(idx)

    return to_be_activated, active_plots


def get_use_web_ui():
    global USE_WEB_UI
    return USE_WEB_UI


def disable_web_ui():
    global USE_WEB_UI
    USE_WEB_UI = False


def enable_web_ui():
    global USE_WEB_UI
    USE_WEB_UI = True


def init_uid_queues():
    return {
        "glb_queue_chat_msg": Queue(),
        "glb_queue_chat_input": Queue(),
    }


glb_uid_dict = defaultdict(init_uid_queues)


def send_chat_msg(
    msg, role="系统", uid=None, flushing=False, avatar="./assets/bot.jpg"
):
    print(msg)
    if get_use_web_ui():
        global glb_uid_dict
        glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
        glb_queue_chat_msg.put(
            [
                None,
                {
                    "text": msg,
                    "flushing": flushing,
                    "avatar": avatar,
                },
            ]
        )


def send_player_msg(
    msg, role="你", uid=None, flushing=False, avatar="./assets/user.jpg"
):
    print(msg)
    if get_use_web_ui():
        global glb_uid_dict
        glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
        glb_queue_chat_msg.put(
            [
                {
                    "text": msg,
                    "flushing": flushing,
                    "avatar": avatar,
                },
                None,
            ]
        )


def get_chat_msg(uid=None):
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    if not glb_queue_chat_msg.empty():
        line = glb_queue_chat_msg.get(block=False)
        if line is not None:
            return line
    return None


def send_player_input(msg, role="餐厅老板", uid=None):
    if get_use_web_ui():
        global glb_uid_dict
        glb_queue_chat_input = glb_uid_dict[uid]["glb_queue_chat_input"]
        glb_queue_chat_input.put([None, msg])


def send_pretty_msg(msg, uid=None, flushing=True, avatar="./assets/bot.jpg"):
    speak_print(msg)
    if get_use_web_ui():
        global glb_uid_dict
        send_chat_msg(
            msg.content,
            uid=uid,
            role=msg.name,
            flushing=flushing,
            avatar=avatar,
        )


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


def format_choices(choices):
    formatted_choices = ""
    line_length = 0

    for index, choice in enumerate(choices):
        choice_str = f"[{index + 1}]. {choice}  "
        choice_length = len(choice_str)

        if line_length + choice_length > 30:
            formatted_choices += "\n"
            line_length = 0

        formatted_choices += choice_str
        line_length += choice_length

    formatted_choices = formatted_choices.rstrip()

    return formatted_choices


def query_answer(questions: List, key="ans", uid=None):
    if get_use_web_ui():
        return get_player_input(uid=uid)
    else:
        answer = [inquirer.prompt(questions)[key]]  # return list
    return answer


@dataclass
class CheckpointArgs:
    load_checkpoint: str = None
    save_checkpoint: str = "./checkpoints/cp-"


class ResetException(Exception):
    pass
