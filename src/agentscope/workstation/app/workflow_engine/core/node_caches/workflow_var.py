# -*- coding: utf-8 -*-
"""
This module defines classes for handling variables in a workflow.
"""
import copy
from enum import Enum
from typing import Optional, List, Any, Union, Dict


class DataType(Enum):
    """
    Enum representing various data types that a workflow variable can have.
    """

    Any = "Any"
    STRING = "String"
    IMAGE = "Image"
    VIDEO = "Video"
    AUDIO = "Audio"
    NUMBER = "Number"
    BOOLEAN = "Boolean"
    OBJECT = "Object"
    ARRAY_ANY = "Array<Any>"
    ARRAY_STRING = "Array<String>"
    ARRAY_IMAGE = "Array<Image>"
    ARRAY_VIDEO = "Array<Video>"
    ARRAY_AUDIO = "Array<Audio>"
    ARRAY_NUMBER = "Array<Number>"
    ARRAY_BOOLEAN = "Array<Boolean>"
    ARRAY_OBJECT = "Array<Object>"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: Union[str, "DataType"]) -> "DataType":
        """
        Converts a string value to a DataType enum.
            value: The string value to convert.
            Returns: A DataType enum corresponding to the input value.
            ValueError: If the input value does not correspond to any DataType.
        """
        for item in cls:
            if value in [item.value, item]:
                return item
        raise ValueError(f"{value} is not a valid value for {cls.__name__}")

    @classmethod
    def get_sub_type(cls, value: Union[str, "DataType"]) -> "DataType":
        """
        Get a DataType enum corresponding to the input value.
            value: The string value or DataType of a Array type.
            Returns: A DataType enum corresponding to the input value.
            ValueError: If the input value does not correspond to any DataType.
        """
        for item in cls:
            if value in [item.value, item]:
                if item.value.startswith("Array"):
                    return cls.from_value(
                        item.value.split("<")[1].split(">")[0],
                    )

        raise ValueError(
            f"{value} is not a valid or Array type for" f" {cls.__name__}",
        )


class WorkflowVariable(dict):
    """
    Represents a variable in a workflow, including its content, data type,
    and connections to sources and targets.

    Attributes:
        key (str): The key of the variable.
        content (Optional[Any]): The content of the variable.
        source (Optional[str]): The source from which this variable derives.
        targets (Optional[List[str]]): The targets that this variable affects.
        data_type (Optional[DataType]): The data type of this variable.
    """

    def __init__(
        self,
        name: str = "result",
        content: Optional[Any] = None,
        source: Optional[str] = None,
        targets: Optional[List[str]] = None,
        data_type: Union[str, DataType] = DataType.STRING,
        input: Optional[Any] = None,  # pylint: disable=redefined-builtin
        output: Optional[Any] = None,
        output_type: Optional[str] = "text",
        node_type: Optional[str] = None,
        node_name: Optional[str] = None,
        node_exec_time: Optional[str] = None,
        batches: list = None,
        is_batch: bool = False,
        is_multi_branch: bool = False,
        multi_branch_results: Optional[list] = None,
        usages: Optional[list] = None,
        sub_sorted_nodes: Optional[list] = None,
        try_catch: Optional[dict] = None,
    ) -> None:
        if batches is None:
            batches = []
        super().__init__(
            key=name if source is None else f"{source}.{name}",
            content=content if content is not None else "",
            source=source,
            targets=targets,
            data_type=data_type,
            name=name,
            input=input,
            output=output,
            output_type=output_type,
            node_type=node_type,
            node_name=node_name,
            node_exec_time=node_exec_time,
            batches=batches,
            is_batch=is_batch,
            is_multi_branch=is_multi_branch,
            multi_branch_results=multi_branch_results,
            usages=usages,
            sub_sorted_nodes=sub_sorted_nodes,
            try_catch=try_catch,
        )
        # self._validate_content_type()

    def _validate_content_type(self) -> None:
        """Validates that the content matches the specified data type."""
        type_map = {
            DataType.Any: Any,
            DataType.STRING: str,
            DataType.IMAGE: (str, bytes),
            DataType.VIDEO: (str, bytes),
            DataType.AUDIO: (str, bytes),
            DataType.NUMBER: (int, float),
            DataType.BOOLEAN: bool,
            DataType.OBJECT: dict,
            DataType.ARRAY_STRING: list,
            DataType.ARRAY_IMAGE: list,
            DataType.ARRAY_VIDEO: list,
            DataType.ARRAY_AUDIO: list,
            DataType.ARRAY_ANY: list,
            DataType.ARRAY_NUMBER: list,
            DataType.ARRAY_BOOLEAN: list,
            DataType.ARRAY_OBJECT: list,
        }

        if self["data_type"] not in type_map:
            self["data_type"] = DataType.from_value(self["data_type"])

        expected_type = type_map.get(self["data_type"])
        if not isinstance(expected_type, tuple):
            expected_type = (expected_type,)

        self["data_type"] = self["data_type"].value

        if not isinstance(self["content"], expected_type):
            raise TypeError(
                f"Content of type {type(self['content']).__name__} does not "
                f"match expected type {expected_type} for data_type"
                f" {self['data_type']}",
            )

    def __getattr__(self, item: str) -> Any:
        return self[item]

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __repr__(self) -> str:
        return (
            f"WorkflowVariable(content={self['content']}, targets"
            f"={self['targets']}, source='{self['source']}', key="
            f"'{self['key']}', data_type='{self['data_type']}')"
        )

    def __deepcopy__(self, memo: Dict[int, Any]) -> "WorkflowVariable":
        # Create a deep copy of the dictionary
        copied = WorkflowVariable(
            name=self["key"].split(".")[-1],
            content=copy.deepcopy(self["content"], memo),
            source=self["source"],
            targets=copy.deepcopy(self["targets"], memo),
            data_type=self["data_type"],
        )
        # Add the object to the memo dictionary
        memo[id(self)] = copied
        return copied
