# -*- coding: utf-8 -*-
import os
import pickle
from typing import Optional, List
from datetime import datetime
from colorist import BgBrightColor
import inquirer
from multiprocessing import Queue
from dataclasses import dataclass
from agentscope.message import Msg
from enums import StagePerNight

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


def check_active_plot(
    plots: list[dict],
    curr_done: Optional[int],
) -> tuple[list[str], list[int]]:
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
            to_be_activated.append(p["main_role"])
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
                to_be_activated.append(p["main_role"])
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


glb_queue_chat_msg = Queue()
glb_queue_chat_input = Queue()
glb_queue_chat_suggests = Queue()


def send_chat_msg(msg, role="系统"):
    print(msg)
    if get_use_web_ui():
        glb_queue_chat_msg.put([role, msg])


def get_chat_msg():
    if not glb_queue_chat_msg.empty():
        line = glb_queue_chat_msg.get(block=False)
        if line is not None:
            return line
    return None


def send_player_input(msg, role="餐厅老板"):
    if get_use_web_ui():
        glb_queue_chat_input.put([role, msg])


def send_pretty_msg(msg):
    speak_print(msg)
    if get_use_web_ui():
        glb_queue_chat_msg.put([msg.name, msg.content])


def get_player_input(name=None):
    global glb_queue_chat_msg, glb_queue_chat_input, glb_queue_chat_suggests
    if get_use_web_ui():
        print("wait queue input")
        content = glb_queue_chat_input.get(block=True)[1]
        if content == "**Reset**":
            glb_queue_chat_msg = Queue()
            glb_queue_chat_input = Queue()
            glb_queue_chat_suggests = Queue()
            raise ResetException
    else:
        content = input(f"{name}: ")
    return content


def send_suggests(suggests):
    msg, _ = suggests

    while not glb_queue_chat_suggests.empty():
        try:
            glb_queue_chat_suggests.get_nowait()
        except glb_queue_chat_suggests.Empty:
            break

    if msg == "end":
        return
    else:
        glb_queue_chat_suggests.put(suggests)


def get_suggests():
    msg = None
    samples = None
    if not glb_queue_chat_suggests.empty():
        msg, samples = glb_queue_chat_suggests.get(block=False)
        glb_queue_chat_suggests.put((msg, samples))
    return msg, samples


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

    # 去除多余的空格
    formatted_choices = formatted_choices.rstrip()

    return formatted_choices


def query_answer(questions: List, key="ans"):
    if get_use_web_ui():
        suggests = questions[0]
        assert isinstance(suggests, inquirer.questions.List)
        suggests_msg = (
            suggests.message + "\n" + format_choices(suggests.choices)
        )
        print("suggests=", suggests)
        samples = [[choice] for choice in suggests.choices]
        msg = suggests.message
        send_chat_msg(suggests_msg)
        send_suggests((msg, samples))
        return get_player_input()
    else:
        answer = inquirer.prompt(questions)[key]
    return answer


def end_query_answer():
    if get_use_web_ui():
        send_suggests(("end", None))


@dataclass
class CheckpointArgs:
    load_checkpoint: str = None
    save_checkpoint: str = "./checkpoints/cp-"


class ResetException(Exception):
    pass
