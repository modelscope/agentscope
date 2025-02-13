# -*- coding: utf-8 -*-
"""utils for schedulerpipeline"""
from collections import defaultdict, deque


def format_dependency(steps: list[tuple]) -> str:
    """
        Formats a list of step tuples into a string that describes the
        dependency relationships among steps.

        Each step tuple is expected to contain:
        - step_number: The identifier for the step.
        - _: (Unused in this function) Can be used to pass additional
            information.
        - agent: The name of the agent responsible for the step.
        - dependency: The identifier(s) of the step(s) this step depends
            on, or "None" if there are no dependencies.

    Parameters:
        steps (list of tuples): A list of tuples where each tuple
            represents a step. Each tuple is formatted as (step_number, _,
            agent, dependency).

    Returns:
        str: A formatted string where each line represents a step and
            its dependencies. Each line is of the format
            "step_number.agent (dependent on dependency)" if there are
            dependencies, or "step_number.agent" if there are no
            dependencies.

    Example:
        Input: [(1, _, "AgentA", "None"), (2, _, "AgentB", "1")]
        Output:
            "1.AgentA
             2.AgentB (dependent on 1)"
    """
    formatted_dependency = []
    for step in steps:
        step_number, _, agent, dependency = step
        if dependency.strip() != "None":
            dependency_str = f"(dependent on {dependency})"
        else:
            dependency_str = ""
        formatted_dependence = f"{step_number}.{agent}{dependency_str}"
        formatted_dependency.append(formatted_dependence)
    return "\n".join(formatted_dependency)


def topological_sort(task_list: list[tuple]) -> tuple[list[tuple], dict]:
    """
    Performs a topological sort on a list of tasks to determine a
        feasible sequence of execution based on dependencies.

    Each task in the task_list is expected to be a tuple containing:
    - step_number: A unique identifier for the task.
    - _: (Unused in this function) Placeholder for additional information.
    - agent: The name of the agent responsible for executing the task.
    - dependencies: A string containing step_numbers this task depends
        on, separated by commas, or "None" if no dependencies.

    Parameters:
        task_list (List[Tuple[str, str, str, str]]): A list of tuples,
            where each tuple represents a task with its associated details.

    Returns:
        Tuple[List[Tuple], Dict[str, List[str]]]:
        - A list of tasks sorted in a feasible execution order based on
            the provided dependencies.
        - A dictionary where each key is an agent name,  and the value
            is a list of agent names that the key depends on, sorted in
            the order of execution.

    Raises:
        ValueError: If there is a circular dependency that prevents
            topological sorting or if a task has undefined dependencies.

    Example:
        Input: [
            ("1", "info", "AgentA", "None"),
            ("2", "info", "AgentB", "1"),
            ("3", "info", "AgentC", "2,1")
        ]
        Output: (
            [("1", "info", "AgentA", "None"), ("2", "info", "AgentB",
            "1"), ("3", "info", "AgentC", "2,1")],
            {"AgentA": [], "AgentB": ["AgentA"], "AgentC": ["AgentA",
            "AgentB"]}
        )
    """
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    task_map = {task[0]: task for task in task_list}
    dependency_dict = defaultdict(list)

    for step_number, _, _, dependencies in task_list:
        if dependencies.strip() != "None":
            dependent_numbers = dependencies.replace("，", ",").split(",")
            for dep in dependent_numbers:
                dep = dep.strip()
                if dep not in task_map:
                    raise ValueError(
                        f"Task {step_number} dependent on undefined "
                        f"task number {dep}",
                    )
                graph[dep].append(step_number)
                in_degree[step_number] += 1
                dependency_dict[step_number].append(dep)

    queue = deque([node for node in task_map if in_degree[node] == 0])

    sorted_list = []
    while queue:
        node = queue.popleft()
        sorted_list.append(node)
        for adjacent in graph[node]:
            in_degree[adjacent] -= 1
            if in_degree[adjacent] == 0:
                queue.append(adjacent)

    if len(sorted_list) != len(task_map):
        raise ValueError(
            "There is a circular dependency that prevents topological "
            "sorting",
        )

    index_map = {task_id: index for index, task_id in enumerate(sorted_list)}

    sorted_dependency_dict = {}
    for task_id in sorted_list:
        sorted_deps = sorted(
            dependency_dict[task_id],
            key=lambda d: index_map[d],
        )
        sorted_dependency_dict[task_map[task_id][2]] = [
            task_map[dep][2] for dep in sorted_deps
        ]

    sorted_tasks = [task_map[task_id] for task_id in sorted_list]
    return sorted_tasks, sorted_dependency_dict
