# -*- coding: utf-8 -*-
""" Service response module """
from typing import Any

from agentscope.service.service_status import ServiceExecStatus


class ServiceResponse(dict):
    """Used to wrap the execution results of the services"""

    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

    def __init__(
        self,
        status: ServiceExecStatus,
        content: Any,
    ):
        """Constructor of ServiceResponse

        Args:
            status (`ServiceExeStatus`):
                The execution status of the service.
            content (`Any`)
                If the argument`status` is `SUCCESS`, `content` is the
                response. We use `object` here to support various objects,
                e.g. str, dict, image, video, etc.
                Otherwise, `content` is the error message.
        """
        self.status = status
        self.content = content
