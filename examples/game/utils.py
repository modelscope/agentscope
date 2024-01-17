# -*- coding: utf-8 -*-
import enum
import os
import pickle
from typing import Optional
from datetime import datetime
from customer import Customer
from agentscope.message import Msg
from colorist import BgBrightColor


class StagePerNight(enum.IntEnum):
    """Enum for customer status."""

    INVITED_CHAT = 0
    CASUAL_CHAT_FOR_MEAL = 1
    MAKING_INVITATION = 2


class GameCheckpoint:
    def __init__(
            self,
            stage_per_night: StagePerNight,
            customers: list[Customer],
            cur_plots: list,
            done_plots: list,
            invited_customers: list[Customer],
    ):
        self.stage_per_night = stage_per_night
        self.customers = customers
        self.cur_plots = cur_plots
        self.done_plots = done_plots
        self.invited_customers = invited_customers


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
        curr_done: Optional[int]) -> tuple[list[str], list[int]]:
    # insure all plots have been added 'state'
    for p in plots:
        if "state" not in p:
            p["state"] = "non-active"
    to_be_activated = []
    active_plots = []

    if curr_done is not None:
        plots[curr_done]["state"] = "done"

    # activate those with dependencies and the dependencies are done
    for idx, p in enumerate(plots):
        # activate all plots has no dependency and not done yet
        if p["predecessor_plots"] is None and p["state"] == "non-active":
            to_be_activated.append(p["main_role"])
            p["state"] = "active"
            active_plots.append(idx)
        elif p["predecessor_plots"] is not None:
            to_activate = all([plots[pre_p]["state"] == "done"
                               for pre_p in p["predecessor_plots"]])

            if to_activate:
                p["state"] = "active"
                to_be_activated.append(p["main_role"])
                active_plots.append(idx)
        elif p['state'] == "active":
            active_plots.append(idx)

    return to_be_activated, active_plots
