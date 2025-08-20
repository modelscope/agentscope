# -*- coding: utf-8 -*-
"""
This module defines the Status enumeration used to represent the various
states that a workflow node or process can be in.
"""
from enum import Enum


class Status(Enum):
    """
    Enumeration for representing the status of workflow nodes or processes.
    """

    SUCCEEDED = "success"
    RUNNING = "executing"
    CANCELED = "CANCELED"
    FAILED = "fail"
    SKIP = "skip"
