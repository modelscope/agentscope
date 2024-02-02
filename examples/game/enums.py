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


class StagePerNight(enum.IntEnum):
    """Enum for customer status."""

    CASUAL_CHAT_FOR_MEAL = 0
    MAKING_INVITATION = 1
