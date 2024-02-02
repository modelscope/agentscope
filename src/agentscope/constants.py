# -*- coding: utf-8 -*-
""" Some constants used in the project"""
from numbers import Number
from enum import IntEnum

PACKAGE_NAME = "agentscope"
MSG_TOKEN = f"[{PACKAGE_NAME}_msg]"


# default values

# for file manager
_DEFAULT_DIR = "./runs"
_DEFAULT_LOG_LEVEL = "INFO"
_DEFAULT_SUBDIR_CODE = "code"
_DEFAULT_SUBDIR_FILE = "file"
_DEFAULT_SUBDIR_INVOKE = "invoke"
_DEFAULT_CFG_NAME = ".config"
_DEFAULT_IMAGE_NAME = "image_{}_{}.png"
_DEFAULT_SQLITE_DB_PATH = "agentscope.db"


# for model wrapper
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_MESSAGES_KEY = "inputs"
_DEFAULT_RETRY_INTERVAL = 1
_DEFAULT_API_BUDGET = None
# for execute python
_DEFAULT_PYPI_MIRROR = "http://mirrors.aliyun.com/pypi/simple/"
_DEFAULT_TRUSTED_HOST = "mirrors.aliyun.com"
# for monitor
_DEFAULT_MONITOR_TABLE_NAME = "monitor_metrics"
# for summarization
_DEFAULT_SUMMARIZATION_PROMPT = """
TEXT: {}
"""
_DEFAULT_SYSTEM_PROMPT = """
You are a helpful agent to summarize the text.
You need to keep all the key information of the text in the summary.
"""
_DEFAULT_TOKEN_LIMIT_PROMPT = """
Summarize the text after TEXT in less than {} tokens:
"""

# typing
Embedding = list[Number]


# enums
class ResponseFormat(IntEnum):
    """Enum for model response format."""

    NONE = 0
    JSON = 1


class ShrinkPolicy(IntEnum):
    """Enum for shrink strategies when the prompt is too long."""

    TRUNCATE = 0
    SUMMARIZE = 1
