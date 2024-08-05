# -*- coding: utf-8 -*-
"""Unit tests for environment"""
import unittest
from typing import Any

from agentscope.environment import (
    Attribute,
    Event,
    EventListener,
    Environment,
    BasicAttribute,
    Point2D,
    AttributeWithPoint2D,
    Map2D,
)

from agentscope.exception import (
    EnvAttributeAlreadyExistError,
    EnvAttributeTypeError,
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
        event: Event,
    ) -> None:
        self.rec.record(
            {"attr": attr, "event_name": event.name, "event_args": event.args},
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
            get_rec_1.value["event_name"],  # type: ignore [index]
            "get",
        )
        self.assertEqual(
            get_rec_1.value["event_args"],  # type: ignore [index]
            {},
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
            set_rec_1.value["event_name"],  # type: ignore [index]
            "set",
        )
        self.assertEqual(
            set_rec_1.value["event_args"],  # type: ignore [index]
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
            get_rec_1.value["event_name"],  # type: ignore [index]
            get_rec_2.value["event_name"],  # type: ignore [index]
        )
        self.assertEqual(
            get_rec_1.value["event_args"],  # type: ignore [index]
            get_rec_2.value["event_args"],  # type: ignore [index]
        )
        self.assertTrue(attribute.set(10))
        self.assertEqual(
            set_rec_2.value["attr"],  # type: ignore [index]
            attribute,
        )
        self.assertEqual(
            set_rec_2.value["event_name"],  # type: ignore [index]
            "set",
        )
        self.assertEqual(
            set_rec_2.value["event_args"],  # type: ignore [index]
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

    def test_map2d_env(self) -> None:
        """Test cases for Map2d attribute"""
        m = Map2D(name="map")
        p1 = Point2D(
            name="p1",
            x=0,
            y=0,
        )
        p2 = AttributeWithPoint2D(
            name="p2",
            value={},
            x=0,
            y=-1,
        )
        p3 = AttributeWithPoint2D(
            name="p3",
            value={},
            x=3,
            y=4,
        )
        b1 = BasicAttribute(name="b1", default="hi")
        m.register_point(p1)
        m.register_point(p2)
        m.register_point(p3)
        self.assertRaises(EnvAttributeTypeError, m.register_point, b1)
        self.assertRaises(EnvAttributeAlreadyExistError, m.register_point, p1)
        self.assertRaises(EnvAttributeTypeError, Map2D, "map", [b1])

        class InRangeListener(EventListener):
            """A listener that listens to in range events"""

            def __init__(self, name: str, owner: Attribute) -> None:
                super().__init__(name)
                self.owner = owner

            def __call__(self, attr: Attribute, event: Event) -> None:
                self.owner.value[event.args["attr_name"]] = event

        class OutRangeListener(EventListener):
            """A listener that listen to out of range events"""

            def __init__(self, name: str, owner: Attribute) -> None:
                super().__init__(name)
                self.owner = owner

            def __call__(self, attr: Attribute, event: Event) -> None:
                if event.args["attr_name"] in self.owner.value:
                    self.owner.value.pop(event.args["attr_name"])

        m.in_range_of(
            "p2",
            listener=InRangeListener("in_p2_1_euc", p2),
            distance=1,
        )
        m.out_of_range_of(
            "p2",
            listener=OutRangeListener("out_p2_1_euc", p2),
            distance=1,
        )
        m.in_range_of(
            "p3",
            listener=InRangeListener("in_p3_1_euc", p3),
            distance=5,
            distance_type="manhattan",
        )
        m.out_of_range_of(
            "p3",
            listener=OutRangeListener("out_p3_1_euc", p3),
            distance=5,
            distance_type="manhattan",
        )
        self.assertEqual(len(p2.value), 1)
        self.assertTrue("p1" in p2.value)
        self.assertEqual(len(p3.value), 0)
        m.move_attr_to("p3", 2, 3)
        self.assertEqual(len(p3.value), 1)
        self.assertTrue("p1" in p3.value)
        m.move_attr_to("p3", 3, 3)
        self.assertEqual(len(p3.value), 0)
