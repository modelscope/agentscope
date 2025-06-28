# -*- coding: utf-8 -*-
"""workflow related schemas"""

from typing import Any, Optional, List, Dict, Union

from pydantic import BaseModel
from sqlmodel import SQLModel


class InputInfo(SQLModel):
    """input info"""

    key: str
    source: Optional[str]
    value: Union[str, int, float, bool, dict] = None
    desc: Optional[str] = None
    required: Optional[bool] = False


class TaskRunRequest(SQLModel):
    """task input"""

    app_id: str
    version: Optional[str] = None
    session_id: Optional[str] = None
    inputs: list[InputInfo]


class TaskGetRequest(SQLModel):
    """
    task get request
    """

    task_id: str


class CommonParam(BaseModel):
    """
    Common Param for InputParams and OutputParams
    """

    # key is the name of the param
    key: Optional[str] = None
    # type is the type of the param
    type: Optional[str] = None

    # desc is the description of the param
    desc: Optional[str] = None

    # value is the value of the param
    value: Optional[Any] = None

    # valueFrom is the source of the value, such as infer and input
    value_from: Optional[str] = None

    # required is the required of the param, true is required, false is not
    # required
    required: Optional[bool] = None

    # defaultValue is the default value of the param
    default_value: Optional[Any] = None


class InputParam(CommonParam):
    """
    Input Param for InputParams
    """

    pass


class OutputParam(CommonParam):
    """
    Output Param for OutputParams
    """

    properties: Optional[List["OutputParam"]] = None


class NodeCustomConfig(BaseModel):
    """
    Node Config params
    """

    input_params: Optional[List[InputParam]] = None
    output_params: Optional[List[OutputParam]] = None
    node_param: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class Position(BaseModel):
    """
    Position of the node
    """

    x: Optional[int] = None
    y: Optional[int] = None


class Node(BaseModel):
    """
    Node of the graph
    """

    id: str
    name: str
    position: Position
    width: int
    type: str
    desc: Optional[str] = None
    config: Optional[NodeCustomConfig] = None


class Edge(BaseModel):
    """
    Edge of The Graph
    """

    id: Optional[str] = None

    # source node id of the edge
    source: Optional[str] = None

    # If the source node has multiple outgoing connection points,
    # sourceHandle is formatted as {source}_{connectionPointId};
    # Otherwise (if there's only one connection point), sourceHandle simply
    # uses {source}.
    source_handle: Optional[str] = None

    # target node id of the edge
    target: Optional[str] = None

    # If the target node has multiple incoming connection points,
    # targetHandle is formatted as {target}_{connectionPointId};
    # Otherwise (if there's only one connection point), targetHandle simply
    # uses {target}.
    target_handle: Optional[str] = None


class HistoryConfig(BaseModel):
    """
    history config
    """

    # history switch
    history_switch: bool = False

    # history max round
    history_max_round: int = 5


class VariableConfig(BaseModel):
    """
    variable config
    """

    # session params
    session_params: List[CommonParam] = []


class GlobalConfig(BaseModel):
    """
    global config
    """

    history_config: Optional[HistoryConfig] = None
    variable_config: Optional[VariableConfig] = None


class WorkflowConfig(BaseModel):
    """
    workflow config
    """

    # nodes
    nodes: List[Node] = []

    # edges
    edges: List[Edge] = []

    # global config
    global_config: Optional[GlobalConfig] = None


class InitQuery(BaseModel):
    """
    init query
    """

    app_id: str
    version: Optional[str] = "latest"


class ResumeTaskQuery(BaseModel):
    """
    resume task query
    """

    app_id: str
    task_id: str
    resume_node_id: str
    session_id: Optional[str] = None
    input_params: Optional[List] = None
