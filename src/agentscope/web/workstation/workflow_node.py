# -*- coding: utf-8 -*-
"""Workflow node opt."""
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import List, Any, Optional

from agentscope import msghub
from agentscope.agents import (
    DialogAgent,
    UserAgent,
    TextToImageAgent,
    DictDialogAgent,
    AgentBase,
)
from agentscope.message import Msg
from agentscope.models import read_model_configs
from agentscope.pipelines import (
    SequentialPipeline,
    ForLoopPipeline,
    WhileLoopPipeline,
    IfElsePipeline,
    SwitchPipeline,
    PipelineBase,
)
from agentscope.pipelines.functional import placeholder
from agentscope.web.workstation.workflow_utils import (
    kwarg_converter,
    deps_converter,
    dict_converter,
)

DEFAULT_FLOW_VAR = "flow"


def get_all_agents(
    pipeline: PipelineBase,
    seen_agents: Optional[set] = None,
) -> List:
    """
    Retrieve all unique agent objects from a pipeline.

    Recursively traverses the pipeline to collect all distinct agent-based
    participants. Prevents duplication by tracking already seen agents.

    Args:
        pipeline (PipelineBase): The pipeline from which to extract agents.
        seen_agents (set, optional): A set of agents that have already been
            seen to avoid duplication. Defaults to None.

    Returns:
        list: A list of unique agent objects found in the pipeline.
    """
    if seen_agents is None:
        seen_agents = set()

    all_agents = []

    for participant in pipeline.participants:
        if isinstance(participant, AgentBase):
            if participant not in seen_agents:
                all_agents.append(participant)
                seen_agents.add(participant)
        elif isinstance(participant, PipelineBase):
            nested_agents = get_all_agents(participant, seen_agents)
            all_agents.extend(nested_agents)

    return all_agents


class WorkflowNodeType(IntEnum):
    """Enum for workflow node."""

    MODEL = 0
    AGENT = 1
    PIPELINE = 2
    SERVICE = 3
    MESSAGE = 4
    COPY = 5


class WorkflowNode(ABC):
    """
    Abstract base class representing a generic node in a workflow.

    WorkflowNode is designed to be subclassed with specific logic implemented
    in the subclass methods. It provides an interface for initialization and
    execution of operations when the node is called.
    """

    node_type = None

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__()
        self.initialize(*args, **kwargs)

    def initialize(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Initialize nodes. Implement specific initialization logic in
        subclasses.
        """

    @abstractmethod
    def __call__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Performs the operations of the node. Implement specific logic in
        subclasses.
        """


class ModelNode(WorkflowNode):
    """
    A node that represents a model in a workflow.

    The ModelNode can be used to load and execute a model as part of the
    workflow pipeline. It initializes model configurations and performs
    model-related operations when called.
    """

    node_type = WorkflowNodeType.MODEL

    def initialize(self, **kwargs):  # type: ignore[no-untyped-def]
        self.kwargs = kwargs
        read_model_configs([kwargs])

    def __call__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return None

    def compile(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Compile ModelNode to python executable code dict
        """
        return {
            "imports": "from agentscope.models import read_model_configs",
            "inits": f"read_model_configs([{self.kwargs}])",
            "execs": "",
        }


class MsgNode(WorkflowNode):
    """
    A node that manages messaging within a workflow.

    MsgNode is responsible for handling messages, creating message objects,
    and performing message-related operations when the node is invoked.
    """

    node_type = WorkflowNodeType.MESSAGE

    def initialize(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.kwargs = kwargs
        self.msg = Msg(**kwargs)

    def __call__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self.msg

    def compile(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Compile ModelNode to python executable code dict
        """
        return {
            "imports": "from agentscope.message import Msg",
            "inits": f"{DEFAULT_FLOW_VAR} = Msg"
            f"({kwarg_converter(self.kwargs)})",
            "execs": "",
        }


class PlaceHolderNode(WorkflowNode):
    """
    A placeholder node within a workflow.

    This node acts as a placeholder and can be used to pass through information
    or data without performing any significant operation.
    """

    node_type = WorkflowNodeType.PIPELINE

    def __call__(self, x: dict = None) -> dict:
        return placeholder(x)

    def compile(self, var):  # type: ignore[no-untyped-def]
        """
        Compile PlaceHolderNode to python executable code dict
        """
        return {
            "imports": "from agentscope.pipelines.functional import "
            "placeholder",
            "inits": f"{var} = placeholder",
            "execs": f"{DEFAULT_FLOW_VAR} = {var}({DEFAULT_FLOW_VAR})",
        }


class MsgHubNode(WorkflowNode):
    """
    A node that serves as a messaging hub within a workflow.

    MsgHubNode is responsible for broadcasting announcements to participants
    and managing the flow of messages within a workflow's pipeline.
    """

    node_type = WorkflowNodeType.PIPELINE

    def initialize(  # type: ignore[no-untyped-def]
        self,
        deps: List,
        source: dict,
        **kwargs,
    ) -> None:
        self.source = source
        self.dep_vars = [x[1] for x in deps]
        deps = [x[0] for x in deps]
        self.announcement = Msg(
            name=kwargs["announcement"].get("name", "Host"),
            content=kwargs["announcement"].get("content", "Welcome!"),
            role="system",
        )
        self.kwargs = kwargs
        assert (
            isinstance(deps, list)
            and len(deps) == 1
            and hasattr(
                deps[0],
                "pipeline",
            )
        ), (
            "MsgHub members must be a list of length 1, with the first "
            "element being an instance of PipelineBaseNode"
        )

        self.pipeline = deps[0].pipeline
        self.participants = get_all_agents(self.pipeline)

    def __call__(self, x: dict = None) -> dict:
        with msghub(self.participants, announcement=self.announcement):
            x = self.pipeline(x)
        return x

    def compile(self, var: str) -> dict:
        """
        Compile SequentialPipelineNode to python executable code dict
        """
        announcement = (
            f'Msg(name="{self.kwargs["announcement"].get("name", "Host")}", '
            f'content="{self.kwargs["announcement"].get("content", "Host")}"'
            f', role="system")'
        )
        execs = f"""with msghub([], announcement={announcement}):
        {DEFAULT_FLOW_VAR} = {self.dep_vars[0]}({DEFAULT_FLOW_VAR})
        """
        return {
            "imports": "from agentscope.msghub import msghub\n"
            "from agentscope.message import Msg",
            "inits": "",
            "execs": execs,
        }


class SequentialPipelineNode(WorkflowNode):
    """
    A node representing a sequential pipeline within a workflow.

    SequentialPipelineNode executes a series of operators or nodes in a
    sequence, where the output of one node is the input to the next.
    """

    node_type = WorkflowNodeType.PIPELINE

    def initialize(  # type: ignore[no-untyped-def]
        self,
        deps: List,
        source: dict,
        **kwargs,
    ) -> None:
        self.source = source
        self.dep_vars = [x[1] for x in deps]
        self.deps = deps
        deps = [x[0] for x in deps]
        self.pipeline = SequentialPipeline(operators=deps)

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self, var: str) -> dict:
        """
        Compile SequentialPipelineNode to python executable code dict
        """
        return {
            "imports": "from agentscope.pipelines import SequentialPipeline",
            "inits": f"{var} = SequentialPipeline("
            f"{deps_converter(self.dep_vars)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {var}({DEFAULT_FLOW_VAR})",
        }


class ForLoopPipelineNode(WorkflowNode):
    """
    A node representing a for-loop structure in a workflow.

    ForLoopPipelineNode allows the execution of a pipeline node multiple times,
    iterating over a given set of inputs or a specified range.
    """

    node_type = WorkflowNodeType.PIPELINE

    def initialize(  # type: ignore[no-untyped-def]
        self,
        deps: List,
        source: dict,
        **kwargs,
    ) -> None:
        self.source = source
        self.dep_vars = [x[1] for x in deps]
        deps = [x[0] for x in deps]
        assert (
            len(deps) == 1
        ), "ForLoopPipelineNode can only contain one Pipeline Node."
        self.pipeline = ForLoopPipeline(loop_body_operators=deps[0], **kwargs)
        self.kwargs = kwargs

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self, var: str) -> dict:
        """
        Compile ForLoopPipelineNode to python executable code dict
        """
        return {
            "imports": "from agentscope.pipelines import ForLoopPipeline",
            "inits": f"{var} = ForLoopPipeline("
            f"loop_body_operators="
            f"{deps_converter(self.dep_vars)},"
            f" {kwarg_converter(self.source)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {var}({DEFAULT_FLOW_VAR})",
        }


class WhileLoopPipelineNode(WorkflowNode):
    """
    A node representing a while-loop structure in a workflow.

    WhileLoopPipelineNode enables conditional repeated execution of a pipeline
    node based on a specified condition.
    """

    node_type = WorkflowNodeType.PIPELINE

    def initialize(  # type: ignore[no-untyped-def]
        self,
        deps: List,
        source: dict,
        **kwargs,
    ) -> None:
        self.source = source
        self.dep_vars = [x[1] for x in deps]
        deps = [x[0] for x in deps]
        assert (
            len(deps) == 1
        ), "WhileLoopPipelineNode can only contain one Pipeline Node."
        self.pipeline = WhileLoopPipeline(
            loop_body_operators=deps[0],
            **kwargs,
        )
        self.kwargs = kwargs

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self, var: str) -> dict:
        """
        Compile WhileLoopPipeline to python executable code dict
        """
        return {
            "imports": "from agentscope.pipelines import WhileLoopPipeline",
            "inits": f"{var} = WhileLoopPipeline("
            f"loop_body_operators="
            f"{deps_converter(self.dep_vars)},"
            f" {kwarg_converter(self.source)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {var}({DEFAULT_FLOW_VAR})",
        }


class IfElsePipelineNode(WorkflowNode):
    """
    A node representing an if-else conditional structure in a workflow.

    IfElsePipelineNode directs the flow of execution to different pipeline
    nodes based on a specified condition.
    """

    node_type = WorkflowNodeType.PIPELINE

    def initialize(  # type: ignore[no-untyped-def]
        self,
        deps: List,
        source: dict,
        **kwargs,
    ) -> None:
        self.source = source
        self.dep_vars = [x[1] for x in deps]
        deps = [x[0] for x in deps]
        assert (
            0 < len(deps) <= 2
        ), "IfElsePipelineNode must contain one or two Pipeline Node."
        if len(deps) == 1:
            self.pipeline = IfElsePipeline(if_body_operators=deps[0], **kwargs)
        elif len(deps) == 2:
            self.pipeline = IfElsePipeline(
                if_body_operators=deps[0],
                else_body_operators=deps[1],
                **kwargs,
            )

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self, var: str) -> dict:
        """
        Compile IfElsePipelineNode to python executable code dict
        """
        imports = "from agentscope.pipelines import IfElsePipeline"
        execs = f"{DEFAULT_FLOW_VAR} = {var}({DEFAULT_FLOW_VAR})"
        if len(self.dep_vars) == 1:
            return {
                "imports": imports,
                "inits": f"{var} = IfElsePipeline("
                f"if_body_operators={self.dep_vars[0]})",
                "execs": execs,
            }
        elif len(self.dep_vars) == 2:
            return {
                "imports": imports,
                "inits": f"{var} = IfElsePipeline("
                f"if_body_operators={self.dep_vars[0]}, "
                f"else_body_operators={self.dep_vars[1]})",
                "execs": execs,
            }
        raise ValueError


class SwitchPipelineNode(WorkflowNode):
    """
    A node representing a switch-case structure within a workflow.

    SwitchPipelineNode routes the execution to different pipeline nodes
    based on the evaluation of a specified key or condition.
    """

    node_type = WorkflowNodeType.PIPELINE

    def initialize(  # type: ignore[no-untyped-def]
        self,
        deps: List,
        source: dict,
        **kwargs,
    ) -> None:
        self.source = source
        self.dep_vars = [x[1] for x in deps]

        deps = [x[0] for x in deps]
        assert 0 < len(deps), (
            "SwitchPipelineNode must contain at least " "one Pipeline Node."
        )
        case_operators = {}
        self.case_operators_var = {}

        if len(deps) == len(kwargs["cases"]):
            # No default_operators provided
            default_operators = placeholder
            self.default_var_name = "placeholder"
        elif len(deps) == len(kwargs["cases"]) + 1:
            # default_operators provided
            default_operators = deps.pop(-1)
            self.default_var_name = self.dep_vars.pop(-1)
        else:
            raise ValueError(
                f"SwitchPipelineNode node {deps} not matches "
                f"cases {kwargs['cases']}.",
            )

        for key, value, var in zip(kwargs["cases"], deps, self.dep_vars):
            case_operators[key] = value
            self.case_operators_var[key] = var
        kwargs.pop("cases")
        self.source.pop("cases")
        self.pipeline = SwitchPipeline(
            case_operators=case_operators,
            default_operators=default_operators,  # type: ignore[arg-type]
            **kwargs,
        )
        self.kwargs = kwargs

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self, var: str) -> dict:
        """
        Compile SwitchPipelineNode to python executable code dict
        """
        imports = (
            "from agentscope.pipelines import SwitchPipeline\n"
            "from agentscope.pipelines.functional import placeholder"
        )
        execs = f"{DEFAULT_FLOW_VAR} = {var}({DEFAULT_FLOW_VAR})"
        return {
            "imports": imports,
            "inits": f"{var} = SwitchPipeline(case_operators="
            f"{dict_converter(self.case_operators_var)}, "
            f"default_operators={self.default_var_name},"
            f" {kwarg_converter(self.source)})",
            "execs": execs,
        }


class CopyNode(WorkflowNode):
    """
    A node that duplicates the output of another node in the workflow.

    CopyNode is used to replicate the results of a parent node and can be
    useful in workflows where the same output is needed for multiple
    subsequent operations.
    """

    node_type = WorkflowNodeType.COPY

    def initialize(  # type: ignore[no-untyped-def]
        self,
        deps: List,
        **kwargs,
    ) -> None:
        self.dep_vars = [x[1] for x in deps]
        deps = [x[0] for x in deps]
        assert len(deps) == 1, "Copy Node can only have one parent!"
        self.pipeline = deps[0]

    def __call__(  # type: ignore[no-untyped-def]
        self,
        *args,
        **kwargs,
    ) -> Any:
        return self.pipeline(*args, **kwargs)

    def compile(self, var: str) -> dict:
        """
        Compile CopyNode to python executable code dict
        """
        return {
            "imports": "",
            "inits": "",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.dep_vars[0]}"
            f"({DEFAULT_FLOW_VAR})",
        }


NODE_NAME_MAPPING = {
    "dashscope_chat": (ModelNode, WorkflowNodeType.MODEL),
    "openai_chat": (ModelNode, WorkflowNodeType.MODEL),
    "post_api_chat": (ModelNode, WorkflowNodeType.MODEL),
    "Message": (MsgNode, WorkflowNodeType.MESSAGE),
    "DialogAgent": (DialogAgent, WorkflowNodeType.AGENT),
    "UserAgent": (UserAgent, WorkflowNodeType.AGENT),
    "TextToImageAgent": (TextToImageAgent, WorkflowNodeType.AGENT),
    "DictDialogAgent": (DictDialogAgent, WorkflowNodeType.AGENT),
    "Placeholder": (PlaceHolderNode, WorkflowNodeType.PIPELINE),
    "MsgHub": (MsgHubNode, WorkflowNodeType.PIPELINE),
    "SequentialPipeline": (SequentialPipelineNode, WorkflowNodeType.PIPELINE),
    "ForLoopPipeline": (ForLoopPipelineNode, WorkflowNodeType.PIPELINE),
    "WhileLoopPipeline": (WhileLoopPipelineNode, WorkflowNodeType.PIPELINE),
    "IfElsePipeline": (IfElsePipelineNode, WorkflowNodeType.PIPELINE),
    "SwitchPipeline": (SwitchPipelineNode, WorkflowNodeType.PIPELINE),
    "CopyNode": (CopyNode, WorkflowNodeType.COPY),
}
