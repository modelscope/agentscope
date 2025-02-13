# -*- coding: utf-8 -*-
""" Functional counterpart for Pipeline """
from typing import (
    Callable,
    Sequence,
    Optional,
    Union,
    Any,
    Mapping,
)
import re

from .utils import format_dependency, topological_sort
from ..agents.operator import Operator
from ..message.msg import Msg
from ..agents import DialogAgent


# A single Operator or a Sequence of Operators
Operators = Union[Operator, Sequence[Operator]]


def placeholder(x: dict = None) -> dict:
    r"""A placeholder that do nothing.

    Acts as a placeholder in branches that do not require any operations in
    flow control like if-else/switch
    """
    return x


def sequentialpipeline(
    operators: Sequence[Operator],
    x: Optional[dict] = None,
) -> dict:
    """Functional version of SequentialPipeline.

    Args:
        operators (`Sequence[Operator]`):
            Participating operators.
        x (`Optional[dict]`, defaults to `None`):
            The input dictionary.

    Returns:
        `dict`: the output dictionary.
    """
    if len(operators) == 0:
        raise ValueError("No operators provided.")

    msg = operators[0](x)
    for operator in operators[1:]:
        msg = operator(msg)
    return msg


def _operators(operators: Operators, x: Optional[dict] = None) -> dict:
    """Syntactic sugar for executing a single operator or a sequence of
    operators."""
    if isinstance(operators, Sequence):
        return sequentialpipeline(operators, x)
    else:
        return operators(x)


def ifelsepipeline(
    condition_func: Callable,
    if_body_operators: Operators,
    else_body_operators: Operators = placeholder,
    x: Optional[dict] = None,
) -> dict:
    """Functional version of IfElsePipeline.

    Args:
        condition_func (`Callable`):
            A function that determines whether to execute `if_body_operator`
            or `else_body_operator` based on x.
        if_body_operator (`Operators`):
            Operators executed when `condition_func` returns True.
        else_body_operator (`Operators`, defaults to `placeholder`):
            Operators executed when condition_func returns False,
            does nothing and just return the input by default.
        x (`Optional[dict]`, defaults to `None`):
            The input dictionary.

    Returns:
        `dict`: the output dictionary.
    """
    if condition_func(x):
        return _operators(if_body_operators, x)
    else:
        return _operators(else_body_operators, x)


def switchpipeline(
    condition_func: Callable[[Any], Any],
    case_operators: Mapping[Any, Operators],
    default_operators: Operators = placeholder,
    x: Optional[dict] = None,
) -> dict:
    """Functional version of SwitchPipeline.


    Args:
        condition_func (`Callable[[Any], Any]`):
            A function that determines which case_operator to execute based
            on the input x.
        case_operators (`Mapping[Any, Operator]`):
            A dictionary containing multiple operators and their
            corresponding trigger conditions.
        default_operators (`Operators`, defaults to `placeholder`):
            Operators that are executed when the actual condition do not
            meet any of the case_operators, does nothing and just return the
            input by default.
        x (`Optional[dict]`, defaults to `None`):
            The input dictionary.

    Returns:
        dict: the output dictionary.
    """
    target_case = condition_func(x)
    if target_case in case_operators:
        return _operators(case_operators[target_case], x)
    else:
        return _operators(default_operators, x)


def forlooppipeline(
    loop_body_operators: Operators,
    max_loop: int,
    break_func: Callable[[dict], bool] = lambda _: False,
    x: Optional[dict] = None,
) -> dict:
    """Functional version of ForLoopPipeline.

    Args:
        loop_body_operators (`Operators`):
            Operators executed as the body of the loop.
        max_loop (`int`):
            maximum number of loop executions.
        break_func (`Callable[[dict], bool]`):
            A function used to determine whether to break out of the loop
            based on the output of the loop_body_operator, defaults to
            `lambda _: False`
        x (`Optional[dict]`, defaults to `None`):
            The input dictionary.

    Returns:
        `dict`: The output dictionary.
    """
    for _ in range(max_loop):
        # loop body
        x = _operators(loop_body_operators, x)
        # check condition
        if break_func(x):
            break
    return x  # type: ignore[return-value]


def whilelooppipeline(
    loop_body_operators: Operators,
    condition_func: Callable[[int, Any], bool] = lambda _, __: False,
    x: Optional[dict] = None,
) -> dict:
    """Functional version of WhileLoopPipeline.

    Args:
        loop_body_operators (`Operators`): Operators executed as the body of
            the loop.
        condition_func (`Callable[[int, Any], bool]`, optional): A function
            that determines whether to continue executing the loop body based
            on the current loop number and output of the loop_body_operator,
            defaults to `lambda _,__: False`
        x (`Optional[dict]`, defaults to `None`):
            The input dictionary.

    Returns:
        `dict`: the output dictionary.
    """
    i = 0
    while condition_func(i, x):
        # loop body
        x = _operators(loop_body_operators, x)
        # check condition
        i += 1
    return x  # type: ignore[return-value]


def schedulerpipeline(
    planner_model_config_name: str,
    operators: Operators,
    desc_list: list[str],
    x: Optional[dict],
) -> Msg:
    """Functional version of schedulerpipeline.

    Args:
        planner_model_config_name (`str`): The model config name for
            Planner agent.
        operators (`Operators`): Operators executed as the body of
            the pipeline.
        desc_list (`list[str]`): Descriptions corresponding to each operator.
        x (`Optional[dict]`, defaults to `None`):
            The input dictionary.

    Returns:
        `Msg`: the output message.
    """
    assert len(operators) == len(
        desc_list,
    ), "The number of operators and descriptions must be the same."
    desc_dict = {}
    candidates = ""
    for i, operator in enumerate(operators):
        desc_dict[operator.name] = operator
        candidates += f"""
### {operator.name}
{desc_list[i]}"""

    candidates = candidates.strip()

    planner_agent = DialogAgent(
        name="planner",
        sys_prompt=f"""
You are an intelligent agent planning expert.
Your task is to create a plan that uses candidate agents to progressively solve a given problem based on the user's questions/tasks. Each step of the plan should utilize one agent to solve a subtask.

## Candidate Agents
{candidates}
### Basic Agent
This is a foundational agent based on Chat LLM that can perform basic natural language generation tasks.

## Output Format Requirements
Please output the plan content in the following format, using Chinese, and do not include any other content:
# Step-1:
<Subtask>: The main content of this step/subtask
<Agent>: The agent designated to solve this subtask, must be one of the candidate agents ({candidates}) from the list
<Dependency>: The sequence number of the preceding subtask(s) it depends on, if multiple, separate with ', '
# Step-2:
...

## Reference Examples
Below are some examples, please note that the agents used in the examples may not be available for the current task.

User Question: Help me write an email to Morgen promoting Alibaba Cloud
# Step-1:
<Subtask>: Gather the latest updates on Alibaba Cloud products
<Agent>: Intelligent Retrieval Assistant
<Dependency Information>: None
# Step-2:
<Subtask>: Based on the latest updates, write and send an email to Morgen
<Agent>: Intelligent Email Assistant
<Dependency>: 1
""",  # noqa
        model_config_name=planner_model_config_name,
    )

    agent_sys_prompt_with_context = """
Please refer to the task background and context information to complete the given subtask.

Please note:
- The "Task Background" is for reference only; the response should focus on the subtask.

## Task Background (i.e., the overall task that needs to be addressed)
{task}

## Context Information
Please keep the following information in mind, as it will help in answering the question.
{context}

## Please complete the following subtask
{subtask}
"""  # noqa

    agent_sys_prompt_without_context = """
Please refer to the task background and context information to complete the given subtask.

Please note:
- The "Task Background" is for reference only; the response should focus on the subtask.

## Task Background (i.e., the overall task that needs to be addressed)
{task}

## Please complete the following subtask
{subtask}
"""  # noqa

    planner_result = planner_agent(x).content
    step_pattern = re.compile(
        r"# Step-(\d+):\n<Subtask>: (.*?)\n<Agent>: (.*?)\n<Dependency>: ("
        r".*?)(?=\n# Step|\n$|$)",
        re.DOTALL,
    )
    matches = step_pattern.findall(planner_result)

    dependence = format_dependency(matches)

    matches, dependent_dict = topological_sort(matches)
    agent_names = [planner_agent.name]
    agent_results = [planner_result]

    context_dict = {}

    for _, subtask, agent_name, _ in matches:
        dependencies = dependent_dict[agent_name]
        context = "\n".join(
            "\n".join(context_dict[d])
            for d in dependencies
            if d in context_dict
        )
        if context:
            prompt = agent_sys_prompt_with_context.format(
                task=x.content,
                context=context,
                subtask=subtask,
            )
        else:
            prompt = agent_sys_prompt_without_context.format(
                task=x.content,
                subtask=subtask,
            )
        msg = Msg(role="assistant", name=agent_name, content=prompt)
        app_res = desc_dict[agent_name](msg).content
        context_dict.setdefault(agent_name, []).append(app_res)
        agent_names.append(agent_name)
        agent_results.append(app_res)
    details = "\n".join(
        f"## {name}\n### Generation Results\n{result}\n"
        for name, result in zip(agent_names, agent_results)
    )
    agProgress = f"""# User Goal
{x.content}

# Planning Steps
{dependence}

# Execution Details
{details}

# Execution Results
{agent_results[-1]}
"""
    result = {"Progress": agProgress, "Result": agent_results[-1]}

    return Msg(
        role="assistant",
        name="schedulerpipeline",
        content=agent_results[-1],
        metadata=result,
    )
