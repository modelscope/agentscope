# -*- coding: utf-8 -*-
import enum


class CustomerConv(enum.IntEnum):
    """Enum for customer status."""

    OPENING = -1
    WARMING_UP = 0
    AFTER_MEAL_CHAT = 1
    INVITED_GROUP_PLOT = 2


class CustomerPlot(enum.IntEnum):
    """Enum for customer plot active or not."""

    ACTIVE = 1
    NOT_ACTIVE = 0


class StagePerNight(enum.Enum):
    """Enum for customer status."""

    CASUAL_CHAT_FOR_MEAL = 2
    MAKING_INVITATION = 3

    _descriptions = {
        CASUAL_CHAT_FOR_MEAL: "营业环节",
        MAKING_INVITATION: "解密环节"
    }

    @classmethod
    def to_list(cls):
        """Return a list of description tuples sorted by enum value."""
        return list(cls._descriptions.value.values())
