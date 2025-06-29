# -*- coding: utf-8 -*-
"""Module for condition node related functions."""
import time
from typing import Dict, Any, Generator

from .node import Node
from .utils import NodeType
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class JudgeNode(Node):
    """
    Represents a node that evaluates conditions and determines the
    execution path based on predefined branches. Each branch can have
    multiple conditions with specific logical operators.
    """

    node_type: str = NodeType.JUDGE.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        node_param = self.sys_args["node_param"]
        conditions = node_param.get("branches", [])

        source_to_target_map = {}
        for source, adjacency in kwargs["graph"].adj.items():
            for target, edges in adjacency.items():
                for k, data in edges.items():
                    if data.get("source_handle"):
                        source_handle = data.get("source_handle")
                        target_handle = data.get("target_handle")
                        if source_handle not in source_to_target_map:
                            source_to_target_map[source_handle] = []
                            source_to_target_map[source_handle].append(
                                target_handle,
                            )

        for condition in conditions:
            source_handle = self.node_id + "_" + condition.get("id")
            condition["target_ids"] = source_to_target_map.get(
                source_handle,
                [],
            )

        targets = None
        condition_id = None
        for condition in conditions:
            if condition.get("id") == "default":
                default_targets = condition.get("target_ids", [])
                continue

            logic = condition.get("logic", "and").lower()
            sub_conditions = condition.get("conditions", [])

            if logic == "and":
                result = all(
                    self._evaluate_condition(
                        sub_cond["left"],
                        sub_cond["operator"],
                        sub_cond.get("right", {}),
                    )
                    for sub_cond in sub_conditions
                )
            elif logic == "or":
                result = any(
                    self._evaluate_condition(
                        sub_cond["left"],
                        sub_cond["operator"],
                        sub_cond.get("right", {}),
                    )
                    for sub_cond in sub_conditions
                )

            if result:
                targets = condition.get("target_ids", [])
                condition_id = condition.get("id")
                break

        if targets is None:
            condition_id = "default"
            targets = default_targets

        output_dict = {
            "output": f"命中分支目标节点为: {targets[0]}",
        }
        multi_branch_results = [
            {
                "condition_id": condition_id,
                "target_ids": targets,
            },
        ]

        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
        # TODO: make sure the content is targets
        yield [
            WorkflowVariable(
                name="output",
                content=targets,
                source=self.node_id,
                targets=targets,
                data_type=DataType.ARRAY_STRING,
                output=output_dict,
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                node_exec_time=node_exec_time,
                is_multi_branch=True,
                multi_branch_results=multi_branch_results,
            ),
        ]

    def _mock_execute(self, **kwargs: Any) -> Generator:
        yield from self._execute(**kwargs)

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the judge node into a structured dictionary, setting up
        conditions and logic for decision-making branches.

        Returns:
            A dictionary with sections for imports, inits, and execs.
        """
        node_param = self.sys_args["node_param"]
        branches = node_param["branches"]
        inits = []
        condition_ids = []
        index_count = 0

        for index, branch in enumerate(branches):
            if branch.get("id") == "default":
                index_count += 1
                continue

            conditions = []
            condition_ids.append(f"condition_{branch.get('id', '')}")

            for condition in branch.get("conditions", []):
                left = condition.get("left", {})
                right = condition.get("right", {})
                compiled_condition = self._compile_condition(
                    left,
                    condition.get("operator"),
                    right,
                )
                if compiled_condition:
                    conditions.append(compiled_condition)

            logic = branch.get("logic", "and").lower()
            condition_expr = f" {logic} ".join(conditions)

            if index == index_count:
                inits.append(
                    f"{self.build_graph_var_str(condition_ids[-1])} = "
                    f"({condition_expr})",
                )
            else:
                previous_conditions = [f"not {x}" for x in condition_ids[:-1]]
                condition_expr = (
                    " and ".join(previous_conditions)
                    + f" and ({condition_expr})"
                )
                inits.append(
                    f"{self.build_graph_var_str(condition_ids[-1])} = "
                    f"({condition_expr})",
                )

        # Default branch
        default_branch = next(
            (b for b in branches if b["id"] == "default"),
            None,
        )
        if default_branch:
            previous_conditions = [f"not {x}" for x in condition_ids]
            condition_expr = " and ".join(previous_conditions)
            inits.append(
                f"{self.build_graph_var_str('condition_default')} = "
                f"({condition_expr})",
            )

        return {
            "imports": [],
            "inits": inits,
            "execs": [],
            "increase_indent": False,
        }
