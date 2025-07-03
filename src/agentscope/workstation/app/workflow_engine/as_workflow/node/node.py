# -*- coding: utf-8 -*-
"""Node in workflow"""
from typing import Tuple, Any, Optional, Dict, Type
from collections.abc import Iterator

import json5
from dashscope.common.error import InvalidTask

from .node_types import NodeType
from ..constant import DO_NOT_INDENT_SIGN
from ..utils.misc import identify_and_convert_expr
from ...core.nodes import WorkflowBaseNode
from ...core.utils.error import (
    is_workflow_error,
    ThrottleError,
    ModelCallError,
    UnknownError,
)
from ...core.utils.misc import (
    replace_placeholders,
    remove_placeholders,
    find_value_placeholders,
)
from ...core.constant import PATTERN


class Node(WorkflowBaseNode):
    """Node"""

    node_type = None
    mock_time = 0
    special_keys = []  # These keys will not substitute the placeholders,
    # we might should support sub-keys

    def __init__(
        self,
        node_id: str,
        node_kwargs: dict,
        params: dict,
        glb_custom_args: dict,
        persistent_instance: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize nodes with specific arguments and system setup.
        """
        super().__init__(node_id, node_kwargs, **kwargs)
        self.node_kwargs = node_kwargs
        self.glb_custom_args = glb_custom_args
        self.node_name = self.node_kwargs.get("name", self.node_id)
        self.params = params

        # Parse the params
        self.stream = self.params.get("stream", False)
        self.sys_args = {
            **self.node_kwargs.get("config", {}),
            **self.glb_custom_args,
        }

        # Set up the persistent instance
        if persistent_instance is not None:
            self._persistent_instance = persistent_instance
        else:
            self.create_instance()

    def create_instance(self) -> None:
        """
        Create a persistent instance for the Node with `config` field .
        """
        self._persistent_instance = None

    @property
    def persistent_instance(self) -> Any:
        """
        Get the persistent instance.
        """
        return self._persistent_instance

    def _preprocess_inputs(self, *args: Any, **kwargs: Any) -> Tuple[Any, Any]:
        """
        Replace placeholders in sys_args.
        """

        # Always rebuild sys_args, since modifications might happen...
        self.sys_args = {
            **self.node_kwargs.get("config", {}),
            **self.glb_custom_args,
        }

        inputs = kwargs.get("inputs", {})
        for key in list(self.sys_args.keys()):
            if key in self.special_keys:
                continue

            self.sys_args[key] = replace_placeholders(
                self.sys_args[key],
                inputs,
                pattern=PATTERN,
            )
        for key in list(self.sys_args.keys()):
            if key in self.special_keys:
                continue

            self.sys_args[key] = replace_placeholders(
                self.sys_args[key],
                self.sys_args,
                pattern=PATTERN,
            )

        for key in list(self.sys_args.keys()):
            if key in self.special_keys:
                continue

            if find_value_placeholders(
                self.sys_args[key],
                pattern=PATTERN,
            ):
                self.sys_args[key] = remove_placeholders(
                    self.sys_args[key],
                    pattern=PATTERN,
                )

        return args, kwargs

    def evaluate_exception(
        self,
        exception: Exception,
    ) -> Tuple[Exception, bool]:
        """
        Evaluate the given exception to determine if it should be converted
        and if a retry is necessary.
        """
        should_retry = False

        if is_workflow_error(exception):
            if isinstance(exception, ThrottleError):
                return exception, True
            return exception, False
        elif isinstance(exception, InvalidTask):
            try:
                error_details = json5.loads(
                    str(exception).split(":", 1)[-1].strip(),
                )
                status_code, code = error_details.get(
                    "status_code",
                ), error_details.get("code")
                should_retry = status_code == 429 and code in [
                    "Throttling",
                    "Throttling.RateQuota",
                ]
            except ValueError:
                pass
            if should_retry:
                return ThrottleError(str(exception)), True

            return ModelCallError(str(exception)), False

        return UnknownError(str(exception)), False

    def build_graph_var_str(self, key: str) -> str:
        """
        Constructs a string representation of a graph variable using the
            provided key.

        Parameters:
        - key (str): The key to be combined with the node_id to form the
            variable string.

        Returns:
        - str: A string in the format "${node_id.key}".
        """
        return f"${{{self.node_id}.{key}}}"

    # pylint: disable=too-many-return-statements
    def build_var_str(self, param: Dict[str, Any]) -> str:
        """
        Constructs a string representation of a variable based on the
            provided parameter dictionary.

        Parameters:
        - param (Dict[str, Any]): A dictionary containing keys 'value',
            'type', and 'valueFrom' to determine the variable format.

        Returns:
        - str: A string representation of the variable according to its
            type and source.

        Raises:
        - ValueError: If an unsupported variable type is encountered.
        """
        value = param.get("value", "")
        value_type = param.get("type", "String")
        value_from = param.get("valueFrom", "input")

        if value_from == "refer":
            return value

        # WARNING: input type may be always String when value_from is `input`
        if value_type == "String":
            # if isinstance(value, str):
            #     return value
            return f'"{str(value)}"'
        elif value_type == "Number":
            return str(value)
        elif value_type == "Boolean":
            return '"True"' if value else '"False"'
        elif value_type == "Object":
            return str(value)
        elif value_type == "Array<String>":
            return "[" + ", ".join(f'"{str(v)}"' for v in value) + "]"
        elif value_type == "Array<Number>":
            return "[" + ", ".join(str(v) for v in value) + "]"
        elif value_type == "Array<Boolean>":
            return (
                "["
                + ", ".join('"True"' if v else '"False"' for v in value)
                + "]"
            )
        elif value_type == "Array<Object>":
            return "[" + ", ".join(str(v) for v in value) + "]"
        else:
            raise ValueError(f"Unsupported variable type: {value_type}")

    def compile(self) -> Dict[str, Any]:
        return {
            "imports": [],
            "inits": [],
            "execs": [],
            "increase_indent": False,
        }

    def _evaluate_condition(
        self,
        left_item: Dict[str, Any],
        operator: str,
        right_item: Dict[str, Any],
    ) -> Any:
        """
        Evaluates a condition based on the left and right items
        and the operator provided.

        Parameters:
        - left_item (Dict[str, Any]): The dictionary containing the type and
            value of the left operand.
        - operator (str): The operator used to form the condition.
        - right_item (Dict[str, Any]): The dictionary containing the type,
            value, and valueFrom of the right operand.

        Returns:
        - Any: The evaluated result of the condition.

        Note:
        - The left item is always a reference ('refer'), ensuring its type
            is accurate.
        - The right item can be either an 'input' or a 'refer', meaning its
            type might not be accurate.
        - If the right item is an 'input', the type is converted based on
            expression evaluation.
        - Handles various data types including String, Number, Boolean,
            Object, and Array.
        """
        # TODO: make sure the left data type is accurate
        left_type = left_item.get("type", "String")
        left_value = left_item.get("value", "")

        right_type = right_item.get("type", "String")
        right_from = right_item.get("valueFrom", "input")
        right_value = right_item.get("value", "")

        # Try to fix the right item
        if right_from == "input" and right_type == "String":
            right_type, right_value = identify_and_convert_expr(right_value)
            right_item = {
                "type": right_type,
                "value": right_value,
                "from": right_from,
            }

        if left_type == "String":
            operator_map = {
                "equals": lambda left, right: left == str(right),
                "notEquals": lambda left, right: left != str(right),
                "isNull": lambda left, right: left is None,
                "isNotNull": lambda left, right: left is not None,
                "lengthEquals": lambda left, right: (
                    len(left) == len(right)
                    if right_type != "Number"
                    else len(left) == right
                ),
                "lengthGreater": lambda left, right: (
                    len(left) > len(right)
                    if right_type != "Number"
                    else len(left) > right
                ),
                "lengthGreaterAndEqual": lambda left, right: (
                    len(left) >= len(right)
                    if right_type != "Number"
                    else len(left) >= right
                ),
                "lengthLessAndEqual": lambda left, right: (
                    len(left) <= len(right)
                    if right_type != "Number"
                    else len(left) <= right
                ),
                "lengthLess": lambda left, right: (
                    len(left) < len(right)
                    if right_type != "Number"
                    else len(left) < right
                ),
                "contains": lambda left, right: (
                    right in left
                    if right_type == "String"
                    else str(right) in left
                ),
                "notContains": lambda left, right: (
                    right not in left
                    if right_type == "String"
                    else str(right) not in left
                ),
            }
        elif left_type == "Number":
            operator_map = {
                "equals": lambda left, right: (
                    left == right
                    if right_type == "Number"
                    else left == float(right)
                ),
                "notEquals": lambda left, right: (
                    left != right
                    if right_type == "Number"
                    else left != float(right)
                ),
                "greater": lambda left, right: (
                    left > right
                    if right_type == "Number"
                    else left > float(right)
                ),
                "less": lambda left, right: (
                    left < right
                    if right_type == "Number"
                    else left < float(right)
                ),
                "greaterAndEqual": lambda left, right: (
                    left >= right
                    if right_type == "Number"
                    else left >= float(right)
                ),
                "lessAndEqual": lambda left, right: (
                    left <= right
                    if right_type == "Number"
                    else left <= float(right)
                ),
                "isNull": lambda left, right: left is None,
                "isNotNull": lambda left, right: left is not None,
            }

        elif left_type == "Boolean":
            operator_map = {
                "equals": lambda left, right: (
                    left == right
                    if right_type == "Boolean"
                    else left == bool(right)
                ),
                "notEquals": lambda left, right: (
                    left != right
                    if right_type == "Boolean"
                    else left != bool(right)
                ),
                "isNull": lambda left, right: left is None,
                "isNotNull": lambda left, right: left is not None,
                "isTrue": lambda left, right: left is True,
                "isFalse": lambda left, right: left is False,
            }
        elif "Array" in left_type:
            operator_map = {
                "isNull": lambda left, right: left is None,
                "isNotNull": lambda left, right: left is not None,
                "lengthEquals": lambda left, right: (
                    len(left) == len(right)
                    if right_type != "Number"
                    else len(left) == right
                ),
                "lengthGreater": lambda left, right: (
                    len(left) > len(right)
                    if right_type != "Number"
                    else len(left) > right
                ),
                "lengthGreaterAndEqual": lambda left, right: (
                    len(left) >= len(right)
                    if right_type != "Number"
                    else len(left) >= right
                ),
                "lengthLessAndEqual": lambda left, right: (
                    len(left) <= len(right)
                    if right_type != "Number"
                    else len(left) <= right
                ),
                "lengthLess": lambda left, right: (
                    len(left) < len(right)
                    if right_type != "Number"
                    else len(left) < right
                ),
                "contains": lambda left, right: right in left,
                "notContains": lambda left, right: right not in left,
            }
        elif left_type == "Object":
            operator_map = {
                "isNull": lambda left, right: left is None,
                "isNotNull": lambda left, right: left is not None,
                "contains": lambda left, right: right in left,
                "notContains": lambda left, right: right not in left,
            }
        else:
            raise ValueError(f"Unsupported left type: {left_type}")

        return operator_map[operator](
            left=left_value,
            right=right_item.get("value"),
        )

    def _compile_condition(
        self,
        left_item: Dict[str, Any],
        operator: str,
        right_item: Dict[str, Any],
    ) -> str:
        """
        Compiles a condition string based on the left and right items and
        the operator provided.

        Parameters:
        - left_item (Dict[str, Any]): The dictionary containing the type and
            value of the left operand.
        - operator (str): The operator used to form the condition.
        - right_item (Dict[str, Any]): The dictionary containing the type,
            value, and valueFrom of the right operand.

        Returns:
        - str: A string representing the compiled condition.

        Note:
        - The left item is always a reference ('refer'), ensuring its type
            is accurate.
        - The right item can be either an 'input' or a 'refer', meaning its
            type might not be accurate.
        - If the right item is an 'input', the type is converted based on
            expression evaluation.
        - Handles various data types including String, Number, Boolean,
            Object, and Array.
        """
        left_type = left_item.get("type", "String")
        left_value = left_item.get("value", "")

        right_type = right_item.get("type", "String")
        right_from = right_item.get("valueFrom", "input")
        right_value = right_item.get("value", "")

        # Try to fix the right item
        if right_from == "input" and right_type == "String":
            right_type, right_value = identify_and_convert_expr(right_value)
            right_item = {
                "type": right_type,
                "value": right_value,
                "from": right_from,
            }

        if left_type == "String":
            operator_map = {
                "equals": "{left} == str({right})",
                "notEquals": "{left} != str({right})",
                "isNull": "{left}",
                "isNotNull": "not {left}",
                "lengthEquals": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthGreater": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthGreaterAndEqual": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthLessAndEqual": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthLess": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "contains": (
                    "{right} in {left}"
                    if right_type == "String"
                    else "str({right}) in {left}"
                ),
                "notContains": (
                    "{right} not in {left}"
                    if right_type == "String"
                    else "str({right}) not in {left}"
                ),
            }
        elif left_type == "Number":
            operator_map = {
                "equals": (
                    "{left} == {right}"
                    if right_type == "Number"
                    else "{left} == float({right})"
                ),
                "notEquals": (
                    "{left} != {right}"
                    if right_type == "Number"
                    else "{left} != float({right})"
                ),
                "greater": (
                    "{left} > {right}"
                    if right_type == "Number"
                    else "{left} > float({right})"
                ),
                "less": (
                    "{left} < {right}"
                    if right_type == "Number"
                    else "{left} < float({right})"
                ),
                "greaterAndEqual": (
                    "{left} >= {right}"
                    if right_type == "Number"
                    else "{left} >= float({right})"
                ),
                "lessAndEqual": (
                    "{left} <= {right}"
                    if right_type == "Number"
                    else "{left} <= float({right})"
                ),
                "isNull": "{left} is None",
                "isNotNull": "{left} is not None",
            }
        elif left_type == "Boolean":
            operator_map = {
                "equals": (
                    "{left} == {right}"
                    if right_type == "Boolean"
                    else "{left} == bool({right})"
                ),
                "notEquals": (
                    "{left} != {right}"
                    if right_type == "Boolean"
                    else "{left} != bool({right})"
                ),
                "isNull": "{left} is None",
                "isNotNull": "{left} is not None",
                "isTrue": "{left} is True",
                "isFalse": "{left} is False",
            }
        elif "Array" in left_type:
            operator_map = {
                "isNull": "{left} is None",
                "isNotNull": "{left} is not None",
                "lengthEquals": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthGreater": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthGreaterAndEqual": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthLessAndEqual": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "lengthLess": (
                    "len({left}) == len({right})"
                    if right_type != "Number"
                    else "len({left}) == {right}"
                ),
                "contains": "{right} in {left}",
                "notContains": "{right} not in {left}",
            }
        elif left_type == "Object":
            operator_map = {
                "isNull": "{left} is None",
                "isNotNull": "{left} is not None",
                "contains": "{right} in {left}",
                "notContains": "{right} not in {left}",
            }
        else:
            raise ValueError(f"Unsupported left type: {left_type}")

        return operator_map.get(operator, operator).format(
            left=left_value,
            right=self.build_var_str(right_item),
        )

    def _add_prefix_to_lines(
        self,
        content: Any,
        prefix: str = DO_NOT_INDENT_SIGN,
    ) -> str:
        """
        Adds a specified prefix to each line of the input string.

        Parameters:
        - content (str): The input string to which the prefix will be added.
        - prefix (str): The prefix to add to each line. Defaults to
            DO_NOT_INDENT_SIGN.

        Returns:
        - str: The modified string with each line prefixed.
        """
        lines = str(content).splitlines()
        modified_lines = [f"{prefix}{line}" for line in lines]
        return "\n".join(modified_lines)

    def build_node_output_str(
        self,
        var_name: str,
        var_type: Type,
        sub_attr: Optional[str] = None,
    ) -> str:
        """
        Builds a string for node output based on the variable name, type,
        and optional sub-attribute.

        Parameters:
        - var_name (str): The variable name to be used in the output.
        - var_type (Type): The type of the variable, used to determine
            behavior.
        - sub_attr (Optional[str]): An optional sub-attribute to append to
            the variable name.

        Returns:
        - str: A formatted string representing the node's output.
        """

        def yield_dummy() -> str:
            return f"""yield {var_name}{sub_attr if sub_attr else ""}"""

        def yield_result() -> str:
            return f"""
yield  {{
    "result": {var_name}{sub_attr if sub_attr else ""},
    "node_id": "{self.node_id}",
    "node_type": "{self.node_type}",
    "node_name": "{self.node_name}",
}}
"""

        def yield_result_from_iterable() -> str:
            return f"""
for res in {var_name}:
    yield {{
        "result": res{sub_attr if sub_attr else ""},
        "node_id": "{self.node_id}",
        "node_type": "{self.node_type}",
        "node_name": "{self.node_name}",
    }}
"""

        if self.stream:
            if issubclass(var_type, Iterator):
                return yield_result_from_iterable()
            else:
                return yield_result()
        else:
            if self.node_type in [
                NodeType.END.value,
                NodeType.ITERATOR_END.value,
            ]:
                return yield_dummy()
            else:
                return ""
