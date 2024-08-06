# -*- coding: utf-8 -*-
"""Unit tests for environment"""
import unittest
from typing import Any, Union, Optional, Sequence

from agentscope.environment import (
    Attribute,
    Event,
    EventListener,
    Environment,
    MutableAttribute,
    Point2D,
    AttributeWithPoint2D,
    Map2D,
    ChatRoom,
)

from agentscope.exception import (
    EnvAttributeAlreadyExistError,
    EnvAttributeTypeError,
)

from agentscope.agents import AgentBase
from agentscope.message import Msg


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


class AgentWithChatRoom(AgentBase):
    """A agent with chat room"""

    def __init__(self, name: str, room: ChatRoom) -> None:
        super().__init__(name=name)
        self.room = room
        self.event_list = []
        self.room.join(self)

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        if "event" in x:
            event = x["event"]
            self.event_list.append(event)
            return Msg(name=self.name, content="", role="assistant")
        else:
            history = self.room.get_history(self)
            msg = Msg(name=self.name, content=len(history), role="assistant")
            self.room.speak(msg)
            return msg


class AttributeTest(unittest.TestCase):
    """Test cases for attribute"""

    def test_basic_attribute(self) -> None:
        """Test cases for basic attribute"""
        attribute = MutableAttribute(name="root", value=0)
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
        attr1 = MutableAttribute(
            name="l0",
            value=0,
            children=[
                MutableAttribute(
                    name="l1_0",
                    value=1,
                    children=[
                        MutableAttribute(name="l2_0", value=3),
                        MutableAttribute(name="l2_1", value=4),
                    ],
                ),
                MutableAttribute(
                    name="l1_1",
                    value=2,
                    children=[
                        MutableAttribute(name="l2_2", value=5),
                        MutableAttribute(name="l2_3", value=6),
                    ],
                ),
            ],
        )
        attr2 = MutableAttribute(name="a1", value=10)
        attr3 = MutableAttribute(name="a2", value=20)
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
        b1 = MutableAttribute(name="b1", value="hi")
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
                self.owner._value[event.args["attr_name"]] = event

        class OutRangeListener(EventListener):
            """A listener that listen to out of range events"""

            def __init__(self, name: str, owner: Attribute) -> None:
                super().__init__(name)
                self.owner = owner

            def __call__(self, attr: Attribute, event: Event) -> None:
                if event.args["attr_name"] in self.owner._value:
                    self.owner._value.pop(event.args["attr_name"])

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
        self.assertEqual(len(p2.get()), 1)
        self.assertTrue("p1" in p2.get())
        self.assertEqual(len(p3.get()), 0)
        m.move_attr_to("p3", 2, 3)
        self.assertEqual(len(p3.get()), 1)
        self.assertTrue("p1" in p3.get())
        m.move_attr_to("p3", 3, 3)
        self.assertEqual(len(p3.get()), 0)
        m.move_attr_to("p1", 1, 3)
        self.assertEqual(len(p3.get()), 1)
        self.assertTrue("p1" in p3.get())
        self.assertEqual(len(p2.get()), 0)
        m.move_attr_to("p2", 2, 3)
        self.assertEqual(len(p2.get()), 2)
        self.assertTrue("p1" in p2.get())
        self.assertTrue("p3" in p2.get())
        self.assertEqual(len(p3.get()), 2)
        self.assertTrue("p1" in p3.get())
        self.assertTrue("p2" in p3.get())

    def test_chatroom(self) -> None:
        """Test cases for chatroom attribute"""

        class Listener(EventListener):
            """Listener to record events"""

            def __init__(self, name: str, agent: AgentBase) -> None:
                super().__init__(name)
                self.agent = agent

            def __call__(self, attr: Attribute, event: Event) -> None:
                self.agent(Msg(name="system", content="", event=event))

        ann = Msg(name="system", content="announce", role="system")
        r = ChatRoom(announcement=ann)
        master = AgentWithChatRoom("master", r)
        r.add_listener("speak", Listener("speak_listener", master))
        r.add_listener("join", Listener("join_listener", master))
        r.add_listener("leave", Listener("leave_listener", master))
        r.add_listener("get_history", Listener("get_listener", master))
        r.add_listener(
            "set_announcement", Listener("set_announcement_listener", master)
        )
        r.add_listener(
            "get_announcement", Listener("get_announcement_listener", master)
        )

        # test join
        a1 = AgentWithChatRoom("a1", r)
        self.assertEqual(len(master.event_list), 1)
        self.assertEqual(master.event_list[-1].name, "join")
        self.assertEqual(master.event_list[-1].args["agent"], a1)

        # test announcement
        self.assertEqual(r.get_announcement(), ann)
        self.assertEqual(len(master.event_list), 2)
        self.assertEqual(master.event_list[-1].name, "get_announcement")
        rann = Msg(name="system", content="Hello", role="system")
        r.set_announcement(rann)
        self.assertEqual(master.event_list[-1].name, "set_announcement")
        self.assertEqual(master.event_list[-1].args["announcement"], rann)

        # test speak
        r1 = a1(Msg(name="user", role="user", content="hello"))
        self.assertEqual(master.event_list[-1].name, "speak")
        self.assertEqual(master.event_list[-1].args["message"], r1)
        self.assertEqual(master.event_list[-2].name, "get_history")
        self.assertEqual(master.event_list[-2].args["agent"], a1)
        self.assertEqual(r1.content, 0)

        a2 = AgentWithChatRoom("a2", r)
        self.assertEqual(master.event_list[-1].name, "join")
        self.assertEqual(master.event_list[-1].args["agent"], a2)
        r2 = a2(Msg(name="user", role="user", content="hello"))
        self.assertEqual(master.event_list[-1].name, "speak")
        self.assertEqual(master.event_list[-1].args["message"], r2)
        self.assertEqual(master.event_list[-2].name, "get_history")
        self.assertEqual(master.event_list[-2].args["agent"], a2)
        self.assertEqual(r2.content, 0)

        # test history_idx
        self.assertEqual(r[a1.agent_id].get()["history_idx"], 0)
        self.assertEqual(r[a2.agent_id].get()["history_idx"], 1)
