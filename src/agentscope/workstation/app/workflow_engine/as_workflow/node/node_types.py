# -*- coding: utf-8 -*-
"""Node types"""
from enum import Enum


class NodeType(Enum):
    """Node type enum"""

    START = "Start"
    END = "End"
    LLM = "LLM"
    RETRIEVAL = "Retrieval"
    API = "API"
    CLASSIFIER = "Classifier"
    TEXT_CONVERTER = "TextConverter"
    SCRIPT = "Script"
    JUDGE = "Judge"
    VARIABLE = "Variable"
    ITERATOR = "Iterator"
    ITERATOR_START = "IteratorStart"
    ITERATOR_END = "IteratorEnd"
    VARIABLE_ASSIGN = "VariableAssign"
    SESSION_PARAMS = "SessionParams"
    PARAMETER_EXTRACTOR = "ParameterExtractor"
    INPUT = "Input"
    OUTPUT = "Output"
    PARALLEL = "Parallel"
    PARALLEL_START = "ParallelStart"
    PARALLEL_END = "ParallelEnd"
    VARIABLE_HANDLE = "VariableHandle"

    # Multi-Agent
    AGENT = "AppCustom"
    AGENT_GROUP = "AgentGroup"
    APP_REFER = "AppRefer"
    WORKFLOW_REFER = "WorkflowRefer"
    DECISION = "Decision"

    # AGENTSCOPE
    PAUSE = "Pause"
    WORKFLOW = "Workflow"
    WORKFLOW_START = "WorkflowStart"
    WORKFLOW_END = "WorkflowEnd"

    # Unsupported Nodes
    PLUGIN = "Plugin"
    FC = "FC"
    APPFLOW = "AppFlow"
    MCP = "MCP"
