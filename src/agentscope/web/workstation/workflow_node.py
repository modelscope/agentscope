# -*- coding: utf-8 -*-
"""Workflow node opt."""
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import List, Optional

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

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        """
        Initialize nodes. Implement specific initialization logic in
        subclasses.
        """
        self.node_id = node_id
        self.opt_kwargs = opt_kwargs
        self.source_kwargs = source_kwargs
        self.dep_opts = dep_opts
        self.dep_vars = [opt.var_name for opt in self.dep_opts]
        self.var_name = f"{self.node_type.name.lower()}_{self.node_id}"

    def __call__(self, x: dict = None):  # type: ignore[no-untyped-def]
        """
        Performs the operations of the node. Implement specific logic in
        subclasses.
        """

    @abstractmethod
    def compile(self) -> dict:
        """
        Compile Node to python executable code dict
        """
        return {
            "imports": "",
            "inits": "",
            "execs": "",
        }


class ModelNode(WorkflowNode):
    """
    A node that represents a model in a workflow.

    The ModelNode can be used to load and execute a model as part of the
    workflow pipeline. It initializes model configurations and performs
    model-related operations when called.
    """

    node_type = WorkflowNodeType.MODEL

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        read_model_configs([self.opt_kwargs])

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.models import read_model_configs",
            "inits": f"read_model_configs([{self.opt_kwargs}])",
            "execs": "",
        }


class MsgNode(WorkflowNode):
    """
    A node that manages messaging within a workflow.

    MsgNode is responsible for handling messages, creating message objects,
    and performing message-related operations when the node is invoked.
    """

    node_type = WorkflowNodeType.MESSAGE

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        self.msg = Msg(**self.opt_kwargs)

    def __call__(self, x: dict = None) -> dict:
        return self.msg

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.message import Msg",
            "inits": f"{DEFAULT_FLOW_VAR} = Msg"
            f"({kwarg_converter(self.opt_kwargs)})",
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

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.pipelines.functional import "
            "placeholder",
            "inits": f"{self.var_name} = placeholder",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class DialogAgentNode(WorkflowNode):
    """
    A node representing a DialogAgent within a workflow.
    """

    node_type = WorkflowNodeType.AGENT

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        self.pipeline = DialogAgent(**self.opt_kwargs)

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.agents import DialogAgent",
            "inits": f"{self.var_name} = DialogAgent("
            f"{kwarg_converter(self.opt_kwargs)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class UserAgentNode(WorkflowNode):
    """
    A node representing a UserAgent within a workflow.
    """

    node_type = WorkflowNodeType.AGENT

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        self.pipeline = UserAgent(**self.opt_kwargs)

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.agents import UserAgent",
            "inits": f"{self.var_name} = UserAgent("
            f"{kwarg_converter(self.opt_kwargs)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class TextToImageAgentNode(WorkflowNode):
    """
    A node representing a TextToImageAgent within a workflow.
    """

    node_type = WorkflowNodeType.AGENT

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        self.pipeline = TextToImageAgent(**self.opt_kwargs)

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.agents import TextToImageAgent",
            "inits": f"{self.var_name} = TextToImageAgent("
            f"{kwarg_converter(self.opt_kwargs)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class DictDialogAgentNode(WorkflowNode):
    """
    A node representing a DictDialogAgent within a workflow.
    """

    node_type = WorkflowNodeType.AGENT

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        self.pipeline = DictDialogAgent(**self.opt_kwargs)

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.agents import DictDialogAgent",
            "inits": f"{self.var_name} = DictDialogAgent("
            f"{kwarg_converter(self.opt_kwargs)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class MsgHubNode(WorkflowNode):
    """
    A node that serves as a messaging hub within a workflow.

    MsgHubNode is responsible for broadcasting announcements to participants
    and managing the flow of messages within a workflow's pipeline.
    """

    node_type = WorkflowNodeType.PIPELINE

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        self.announcement = Msg(
            name=self.opt_kwargs["announcement"].get("name", "Host"),
            content=self.opt_kwargs["announcement"].get("content", "Welcome!"),
            role="system",
        )
        assert (
            isinstance(self.dep_opts, list)
            and len(self.dep_opts) == 1
            and hasattr(
                self.dep_opts[0],
                "pipeline",
            )
        ), (
            "MsgHub members must be a list of length 1, with the first "
            "element being an instance of PipelineBaseNode"
        )

        self.pipeline = self.dep_opts[0].pipeline
        self.participants = get_all_agents(self.pipeline)

    def __call__(self, x: dict = None) -> dict:
        with msghub(self.participants, announcement=self.announcement):
            x = self.pipeline(x)
        return x

    def compile(self) -> dict:
        announcement = (
            f'Msg(name="'
            f'{self.opt_kwargs["announcement"].get("name", "Host")}", '
            f'content="'
            f'{self.opt_kwargs["announcement"].get("content", "Host")}"'
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

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        self.pipeline = SequentialPipeline(operators=self.dep_opts)

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.pipelines import SequentialPipeline",
            "inits": f"{self.var_name} = SequentialPipeline("
            f"{deps_converter(self.dep_vars)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class ForLoopPipelineNode(WorkflowNode):
    """
    A node representing a for-loop structure in a workflow.

    ForLoopPipelineNode allows the execution of a pipeline node multiple times,
    iterating over a given set of inputs or a specified range.
    """

    node_type = WorkflowNodeType.PIPELINE

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        assert (
            len(self.dep_opts) == 1
        ), "ForLoopPipelineNode can only contain one Pipeline Node."
        self.pipeline = ForLoopPipeline(
            loop_body_operators=self.dep_opts[0],
            **self.opt_kwargs,
        )

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.pipelines import ForLoopPipeline",
            "inits": f"{self.var_name} = ForLoopPipeline("
            f"loop_body_operators="
            f"{deps_converter(self.dep_vars)},"
            f" {kwarg_converter(self.source_kwargs)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class WhileLoopPipelineNode(WorkflowNode):
    """
    A node representing a while-loop structure in a workflow.

    WhileLoopPipelineNode enables conditional repeated execution of a pipeline
    node based on a specified condition.
    """

    node_type = WorkflowNodeType.PIPELINE

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        assert (
            len(self.dep_opts) == 1
        ), "WhileLoopPipelineNode can only contain one Pipeline Node."
        self.pipeline = WhileLoopPipeline(
            loop_body_operators=self.dep_opts[0],
            **self.opt_kwargs,
        )

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "from agentscope.pipelines import WhileLoopPipeline",
            "inits": f"{self.var_name} = WhileLoopPipeline("
            f"loop_body_operators="
            f"{deps_converter(self.dep_vars)},"
            f" {kwarg_converter(self.source_kwargs)})",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.var_name}"
            f"({DEFAULT_FLOW_VAR})",
        }


class IfElsePipelineNode(WorkflowNode):
    """
    A node representing an if-else conditional structure in a workflow.

    IfElsePipelineNode directs the flow of execution to different pipeline
    nodes based on a specified condition.
    """

    node_type = WorkflowNodeType.PIPELINE

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        assert (
            0 < len(self.dep_opts) <= 2
        ), "IfElsePipelineNode must contain one or two Pipeline Node."
        if len(self.dep_opts) == 1:
            self.pipeline = IfElsePipeline(
                if_body_operators=self.dep_opts[0],
                **self.opt_kwargs,
            )
        elif len(self.dep_opts) == 2:
            self.pipeline = IfElsePipeline(
                if_body_operators=self.dep_opts[0],
                else_body_operators=self.dep_opts[1],
                **self.opt_kwargs,
            )

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        imports = "from agentscope.pipelines import IfElsePipeline"
        execs = f"{DEFAULT_FLOW_VAR} = {self.var_name}({DEFAULT_FLOW_VAR})"
        if len(self.dep_vars) == 1:
            return {
                "imports": imports,
                "inits": f"{self.var_name} = IfElsePipeline("
                f"if_body_operators={self.dep_vars[0]})",
                "execs": execs,
            }
        elif len(self.dep_vars) == 2:
            return {
                "imports": imports,
                "inits": f"{self.var_name} = IfElsePipeline("
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

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        assert 0 < len(self.dep_opts), (
            "SwitchPipelineNode must contain at least " "one Pipeline Node."
        )
        case_operators = {}
        self.case_operators_var = {}

        if len(self.dep_opts) == len(self.opt_kwargs["cases"]):
            # No default_operators provided
            default_operators = placeholder
            self.default_var_name = "placeholder"
        elif len(self.dep_opts) == len(self.opt_kwargs["cases"]) + 1:
            # default_operators provided
            default_operators = self.dep_opts.pop(-1)
            self.default_var_name = self.dep_vars.pop(-1)
        else:
            raise ValueError(
                f"SwitchPipelineNode node {self.dep_opts} not matches "
                f"cases {self.opt_kwargs['cases']}.",
            )

        for key, value, var in zip(
            self.opt_kwargs["cases"],
            self.dep_opts,
            self.dep_vars,
        ):
            case_operators[key] = value
            self.case_operators_var[key] = var
        self.opt_kwargs.pop("cases")
        self.source_kwargs.pop("cases")
        self.pipeline = SwitchPipeline(
            case_operators=case_operators,
            default_operators=default_operators,  # type: ignore[arg-type]
            **self.opt_kwargs,
        )

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        imports = (
            "from agentscope.pipelines import SwitchPipeline\n"
            "from agentscope.pipelines.functional import placeholder"
        )
        execs = f"{DEFAULT_FLOW_VAR} = {self.var_name}({DEFAULT_FLOW_VAR})"
        return {
            "imports": imports,
            "inits": f"{self.var_name} = SwitchPipeline(case_operators="
            f"{dict_converter(self.case_operators_var)}, "
            f"default_operators={self.default_var_name},"
            f" {kwarg_converter(self.source_kwargs)})",
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

    def __init__(
        self,
        node_id: str,
        opt_kwargs: dict,
        source_kwargs: dict,
        dep_opts: list,
    ) -> None:
        super().__init__(node_id, opt_kwargs, source_kwargs, dep_opts)
        assert len(self.dep_opts) == 1, "Copy Node can only have one parent!"
        self.pipeline = self.dep_opts[0]

    def __call__(self, x: dict = None) -> dict:
        return self.pipeline(x)

    def compile(self) -> dict:
        return {
            "imports": "",
            "inits": "",
            "execs": f"{DEFAULT_FLOW_VAR} = {self.dep_vars[0]}"
            f"({DEFAULT_FLOW_VAR})",
        }


# TODO: remove this mapping
NODE_NAME_MAPPING = {
    "dashscope_chat": ModelNode,
    "openai_chat": ModelNode,
    "post_api_chat": ModelNode,
    "Message": MsgNode,
    "DialogAgent": DialogAgentNode,
    "UserAgent": UserAgentNode,
    "TextToImageAgent": TextToImageAgentNode,
    "DictDialogAgent": DictDialogAgentNode,
    "Placeholder": PlaceHolderNode,
    "MsgHub": MsgHubNode,
    "SequentialPipeline": SequentialPipelineNode,
    "ForLoopPipeline": ForLoopPipelineNode,
    "WhileLoopPipeline": WhileLoopPipelineNode,
    "IfElsePipeline": IfElsePipelineNode,
    "SwitchPipeline": SwitchPipelineNode,
    "CopyNode": CopyNode,
}