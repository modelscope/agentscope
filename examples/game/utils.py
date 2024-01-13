import enum
import os
import pickle
from datetime import datetime
from customer import Customer
from agentscope.message import Msg
from colorist import BgBrightColor, Effect

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
            cur_plot: int,
            invited_customers: list[Customer]
    ):
        self.stage_per_night = stage_per_night
        self.customers = customers
        self.cur_plot = cur_plot
        self.invited_customers = invited_customers


def save_game_checkpoint(
        checkpoint: GameCheckpoint,
        checkpoint_prefix: str) -> None:
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_path = checkpoint_prefix + time_str
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint, f)


def load_game_checkpoint(checkpoint_path: str) -> GameCheckpoint:
    with open(checkpoint_path, "rb") as f:
        return pickle.load(f)


def speak_print(m: Msg):
    print(f"{BgBrightColor.BLUE}{m.name}{BgBrightColor.OFF}: {m.content}")