# -*- coding: utf-8 -*-
"""Module for node utils related functions."""
from typing import Type

from .node_types import NodeType
from .node import Node
from .dummy import (
    StartNode,
    EndNode,
    TextConverterNode,
    IteratorStartNode,
    IteratorEndNode,
    VariableNode,
    WorkflowStartNode,
    WorkflowEndNode,
    InputNode,
    OutputNode,
    ParallelStartNode,
    ParallelEndNode,
)
from .retrieval import RetrievalNode
from .llm import LLMNode
from .api import APINode
from .mcp import MCPNode
from .script import ScriptNode
from .judge import JudgeNode
from .agent import AgentNode
from .refer import AppReferNode, WorkflowReferNode
from .agent_group import AgentGroupNode
from .classifier import ClassifierNode, DecisionNode
from .subgraph import IteratorNode, WorkflowNode
from .subgraph.parallel import ParallelNode
from .unsupported import UnsupportedNode, PluginNode, FCNode, AppFlowNode
from .variable_assign import VariableAssignNode
from .session_params import SessionParamsNode
from .parameter_extractor import ParameterExtractorNode
from .variable_handle import VariableHandleNode


NODE_NAME_MAPPING = {
    NodeType.START.value: StartNode,
    NodeType.END.value: EndNode,
    NodeType.LLM.value: LLMNode,
    NodeType.RETRIEVAL.value: RetrievalNode,
    NodeType.API.value: APINode,
    NodeType.CLASSIFIER.value: ClassifierNode,
    NodeType.TEXT_CONVERTER.value: TextConverterNode,
    NodeType.SCRIPT.value: ScriptNode,
    NodeType.JUDGE.value: JudgeNode,
    NodeType.VARIABLE.value: VariableNode,
    NodeType.ITERATOR.value: IteratorNode,
    NodeType.ITERATOR_START.value: IteratorStartNode,
    NodeType.ITERATOR_END.value: IteratorEndNode,
    NodeType.PLUGIN.value: PluginNode,
    NodeType.FC.value: FCNode,
    NodeType.APPFLOW.value: AppFlowNode,
    NodeType.AGENT.value: AgentNode,
    NodeType.AGENT_GROUP.value: AgentGroupNode,
    NodeType.APP_REFER.value: AppReferNode,
    NodeType.WORKFLOW_REFER.value: WorkflowReferNode,
    NodeType.DECISION.value: DecisionNode,
    NodeType.WORKFLOW.value: WorkflowNode,
    NodeType.WORKFLOW_START.value: WorkflowStartNode,
    NodeType.WORKFLOW_END.value: WorkflowEndNode,
    NodeType.VARIABLE_ASSIGN.value: VariableAssignNode,
    NodeType.SESSION_PARAMS.value: SessionParamsNode,
    NodeType.PARAMETER_EXTRACTOR.value: ParameterExtractorNode,
    NodeType.MCP.value: MCPNode,
    NodeType.INPUT.value: InputNode,
    NodeType.OUTPUT.value: OutputNode,
    NodeType.PARALLEL_START.value: ParallelStartNode,
    NodeType.PARALLEL_END.value: ParallelEndNode,
    NodeType.PARALLEL.value: ParallelNode,
    NodeType.VARIABLE_HANDLE.value: VariableHandleNode,
}


def get_node_class(node_name: str) -> Type[Node]:
    """
    Fetches the node class associated with the given node name.

    Args:
        node_name (str): The name of the node type.

    Returns:
        Type[Node]: The class corresponding to the node name, or
        UnsupportedNode if not found or invalid.
    """
    node_cls = NODE_NAME_MAPPING.get(node_name)

    if node_cls and node_cls is not Ellipsis and issubclass(node_cls, Node):
        return node_cls
    else:
        return UnsupportedNode
