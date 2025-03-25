# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Unit test for serialization."""
import json
import unittest

from pydantic import BaseModel

from agentscope.message import Msg
from agentscope.serialization import Serializable, SerializeField
from agentscope.serialize import serialize, deserialize


class Details(BaseModel):
    """The details class."""

    salary: int
    location: str


class Job(Serializable):
    """Test class."""

    def __init__(self, job: str) -> None:
        """Initialize the serializable class."""
        super().__init__()

        self.name = SerializeField(job)

        self.details = SerializeField(
            Details(salary=1000, location="Beijing"),
            serialize_fn=lambda details: details.model_dump(),
            deserialize_fn=lambda _, data: Details.model_validate(data),
        )

        self.data = SerializeField(
            [1, 2, 3, 4, 5],
        )


class Person(Serializable):
    """Test class."""

    def __init__(self, name: str, age: int, job: str) -> None:
        """Initialize the serializable class."""
        super().__init__()

        self.name = SerializeField(name)
        self.age = SerializeField(age)
        self.job = Job(job)


class SerializationTest(unittest.TestCase):
    """The test cases for serialization."""

    def test_serializable_class(self) -> None:
        """Test the serializable class."""
        person = Person("Alice", 20, "Doctor")
        serialized_dict = person.to_dict()
        self.assertDictEqual(
            {
                "name": "Alice",
                "job": {
                    "name": "Doctor",
                    "details": {
                        "salary": 1000,
                        "location": "Beijing",
                    },
                    "data": [1, 2, 3, 4, 5],
                },
                "age": 20,
            },
            serialized_dict,
        )
        person.from_dict(
            {
                "name": "Bob",
                "job": {
                    "name": "Engineer",
                    "details": {
                        "salary": 2000,
                        "location": "Shanghai",
                    },
                    "data": [6, 7, 8],
                },
                "age": 30,
            },
        )
        print(person.to_dict())
        self.assertDictEqual(
            {
                "name": "Bob",
                "job": {
                    "name": "Engineer",
                    "details": {
                        "salary": 2000,
                        "location": "Shanghai",
                    },
                    "data": [6, 7, 8],
                },
                "age": 30,
            },
            person.to_dict(),
        )

    def test_serialize(self) -> None:
        """Test the serialization function."""

        msg1 = Msg("A", "A", "assistant")
        msg2 = Msg("B", "B", "assistant")

        serialized_msg1 = serialize(msg1)
        deserialized_msg1 = deserialize(serialized_msg1)
        self.assertTrue(isinstance(serialized_msg1, str))
        self.assertTrue(isinstance(deserialized_msg1, Msg))

        msg1_dict = json.loads(serialized_msg1)
        self.assertDictEqual(
            msg1_dict,
            {
                "id": msg1.id,
                "name": "A",
                "content": "A",
                "role": "assistant",
                "timestamp": msg1.timestamp,
                "metadata": None,
                "__module__": "agentscope.message.msg",
                "__name__": "Msg",
            },
        )

        serialized_list = serialize([msg1, msg2])
        deserialized_list = deserialize(serialized_list)
        self.assertTrue(isinstance(serialized_list, str))
        self.assertTrue(
            isinstance(deserialized_list, list)
            and len(deserialized_list) == 2
            and all(isinstance(msg, Msg) for msg in deserialized_list),
        )

        dict_list = json.loads(serialized_list)
        self.assertListEqual(
            dict_list,
            [
                {
                    "id": msg1.id,
                    "name": "A",
                    "content": "A",
                    "role": "assistant",
                    "timestamp": msg1.timestamp,
                    "metadata": None,
                    "__module__": "agentscope.message.msg",
                    "__name__": "Msg",
                },
                {
                    "id": msg2.id,
                    "name": "B",
                    "content": "B",
                    "role": "assistant",
                    "timestamp": msg2.timestamp,
                    "metadata": None,
                    "__module__": "agentscope.message.msg",
                    "__name__": "Msg",
                },
            ],
        )
