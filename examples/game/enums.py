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


    @classmethod
    def to_list(cls):
        _descriptions = {
        cls.CASUAL_CHAT_FOR_MEAL: "营业环节",
        cls.MAKING_INVITATION: "解密环节"
    }
        """Return a list of description tuples sorted by enum value."""        
        return list(_descriptions.values())