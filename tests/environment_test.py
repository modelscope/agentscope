# -*- coding: utf-8 -*-
"""Unit tests for environment"""
import unittest
from typing import Any

from agentscope.environment import (
    Attribute,
    BasicAttribute,
    EventListener,
    Environment,
)


class Recorder:
    """Recorder class for test usage"""

    def __init__(self) -> None:
        self.value = None

    def record(self, value: Any) -> None:
        """record the value"""
        self.value = value


class SimpleListener(EventListener):
    """A simple listener who record the input"""

    def __init__(self, name: str, rec: Recorder) -> None:
        super().__init__(name)
        self.rec = rec

    def __call__(
        self,
        attr: Attribute,
        target_event: str,
        kwargs: dict,
    ) -> None:
        self.rec.record(
            {"attr": attr, "target_event": target_event, "kwargs": kwargs},
        )


class AttributeTest(unittest.TestCase):
    """Test cases for attribute"""

    def test_basic_attribute(self) -> None:
        """Test cases for basic attribute"""
        attribute = BasicAttribute(name="root", default=0)
        get_rec_1 = Recorder()
        get_rec_2 = Recorder()
        set_rec_1 = Recorder()
        set_rec_2 = Recorder()
        self.assertTrue(
            attribute.add_listener(
                "get",
                SimpleListener("getlistener1", get_rec_1),
            ),
        )
        self.assertTrue(
            attribute.add_listener(
                "set",
                SimpleListener("setlistener1", set_rec_1),
            ),
        )
        # test get
        self.assertEqual(attribute.get(), 0)
        self.assertEqual(
            get_rec_1.value["attr"],  # type: ignore [index]
            attribute,
        )
        self.assertEqual(
            get_rec_1.value["target_event"],  # type: ignore [index]
            "get",
        )
        self.assertEqual(
            get_rec_1.value["kwargs"],  # type: ignore [index]
            None,
        )
        self.assertEqual(get_rec_2.value, None)
        self.assertEqual(set_rec_1.value, None)
        self.assertEqual(set_rec_2.value, None)
        # test set
        self.assertEqual(attribute.set(1), True)
        self.assertEqual(
            set_rec_1.value["attr"],  # type: ignore [index]
            attribute,
        )
        self.assertEqual(
            set_rec_1.value["target_event"],  # type: ignore [index]
            "set",
        )
        self.assertEqual(
            set_rec_1.value["kwargs"],  # type: ignore [index]
            {"value": 1},
        )
        self.assertEqual(set_rec_2.value, None)
        # test multiple listeners
        self.assertFalse(
            attribute.add_listener(
                "get",
                SimpleListener("getlistener1", get_rec_1),
            ),
        )
        self.assertTrue(
            attribute.add_listener(
                "get",
                SimpleListener("getlistener2", get_rec_2),
            ),
        )
        self.assertFalse(
            attribute.add_listener(
                "set",
                SimpleListener("setlistener1", set_rec_1),
            ),
        )
        self.assertTrue(
            attribute.add_listener(
                "set",
                SimpleListener("setlistener2", set_rec_2),
            ),
        )
        self.assertEqual(attribute.get(), 1)
        self.assertEqual(
            get_rec_1.value["attr"],  # type: ignore [index]
            get_rec_2.value["attr"],  # type: ignore [index]
        )
        self.assertEqual(
            get_rec_1.value["target_event"],  # type: ignore [index]
            get_rec_2.value["target_event"],  # type: ignore [index]
        )
        self.assertEqual(
            get_rec_1.value["kwargs"],  # type: ignore [index]
            get_rec_2.value["kwargs"],  # type: ignore [index]
        )
        self.assertTrue(attribute.set(10))
        self.assertEqual(
            set_rec_2.value["attr"],  # type: ignore [index]
            attribute,
        )
        self.assertEqual(
            set_rec_2.value["target_event"],  # type: ignore [index]
            "set",
        )
        self.assertEqual(
            set_rec_2.value["kwargs"],  # type: ignore [index]
            {"value": 10},
        )
        # test register non existing event
        self.assertFalse(
            attribute.add_listener(
                "non_existing_event",
                SimpleListener("non_existing_event", get_rec_2),
            ),
        )

    def test_basic_environment(self) -> None:
        """Test cases for basic environment"""
        attr1 = BasicAttribute(
            name="l0",
            default=0,
            children=[
                BasicAttribute(
                    name="l1_0",
                    default=1,
                    children=[
                        BasicAttribute(name="l2_0", default=3),
                        BasicAttribute(name="l2_1", default=4),
                    ],
                ),
                BasicAttribute(
                    name="l1_1",
                    default=2,
                    children=[
                        BasicAttribute(name="l2_2", default=5),
                        BasicAttribute(name="l2_3", default=6),
                    ],
                ),
            ],
        )
        attr2 = BasicAttribute(name="a1", default=10)
        attr3 = BasicAttribute(name="a2", default=20)
        env1 = Environment("test1", attr1)
        self.assertFalse(env1.add_attr(attr1))
        self.assertTrue(env1.add_attr(attr2))
        self.assertEqual(env1.get("l0"), 0)
        self.assertEqual(env1.get(["l0"]), 0)
        self.assertEqual(env1.get(["l0", "l1_0"]), 1)
        self.assertEqual(env1.get(["l0", "l1_1"]), 2)
        self.assertEqual(env1.get(["l0", "l1_0", "l2_0"]), 3)
        self.assertEqual(env1.get(["l0", "l1_1", "l2_3"]), 6)
        env2 = Environment("test2", [attr2, attr3])
        self.assertFalse(env2.add_attr(attr2))
        self.assertFalse(env2.add_attr(attr3))
