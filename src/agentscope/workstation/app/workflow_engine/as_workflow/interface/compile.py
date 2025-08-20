# -*- coding: utf-8 -*-
"""Interface for compile workflow to python code."""
import copy
import logging as logger
from typing import Generator, Any

from ..graph_builder import GraphBuilder
from ...core.status import Status


def compiler(
    params: dict,
    dsl_config: dict,
    subgraph_mode: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Compiles a workflow configuration into an executable graph.

    Args:
        params (dict): The parameters dictionary containing running parameters.
        dsl_config (dict): The DSL configuration dictionary containing
            workflow information. subgraph_mode (bool, optional): Determines if
            the compilation is in subgraph mode. Defaults to False.
        subgraph_mode (bool, optional): Determines if the compilation is
            subgraph mode. Defaults to False.
        **kwargs: Additional keyword arguments, such as 'request_id' and
            'stream'.

    Returns:
        Any: The compiled graph object ready for execution.
    """
    dsl_config = copy.deepcopy(dsl_config)
    workflow_config = dsl_config["workflow"]["graph"]

    graph_builder = GraphBuilder(
        config=workflow_config,
        params=params,
        logger=logger,
        request_id=kwargs.get("request_id"),
    )
    return graph_builder.compile(subgraph_mode=subgraph_mode)


def exec_compiler(**kwargs: Any) -> Generator:
    """
    A generator function for compiling workflow config to python code.
    """
    yield [
        {
            "role": "system",
            "content": "Code generation succeed!",
            "status": {
                "task_status": Status.SUCCEEDED.value,
                "code": compiler(**kwargs),
            },
        },
    ]
