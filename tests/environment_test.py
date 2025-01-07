# -*- coding: utf-8 -*-
"""Unit tests for environment"""
import os
import sys
import unittest
from typing import Any

from agentscope.rpc import RpcObject

from agentscope.environment import (
    Env,
    Event,
    EventListener,
)

from agentscope.exception import (
    EnvAlreadyExistError,
    EnvTypeError,
)

from agentscope.agents import AgentBase
from agentscope.message import Msg

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_dir = os.path.join(parent_dir, "examples", "environments", "chatroom")
sys.path.append(env_dir)

from envs import (  # pylint: disable=C0413,C0411 # noqa: E402
    ChatRoom,
    MutableEnv,
    Map2D,
    Point2D,
    EnvWithPoint2D,
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
        env: Env,
        event: Event,
    ) -> None:
        self.rec.record(
            {"env": env, "event_name": event.name, "event_args": event.args},
        )


class AgentWithChatRoom(AgentBase):
    """A agent with chat room"""

    def __init__(  # pylint: disable=W0613
        self,
        name: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name)
        self.room = None
        self.introduction = ""
        self.event_list = []

    def join(self, room: ChatRoom) -> bool:
        """Join a room"""
        self.room = room
        return room.join(self)

    def reply(self, x: Msg = None) -> Msg:
        if "event" in x.content:
            event = x.content["event"]
            self.event_list.append(event)
            return Msg(name=self.name, content="", role="assistant")
        else:
            history = self.room.get_history(self.name)
            msg = Msg(name=self.name, content=len(history), role="assistant")
            self.room.speak(msg)
            return msg

    def get_event(self, idx: int) -> Event:
        """Get the specific event."""
        return self.event_list[idx]

    def chatroom(self) -> Env:
        """Get the chatroom"""
        return self.room


class EnvTest(unittest.TestCase):
    """Test cases for env"""

    def test_basic_env(self) -> None:
        """Test cases for basic env"""
        env = MutableEnv(name="root", value=0)
        get_rec_1 = Recorder()
        get_rec_2 = Recorder()
        set_rec_1 = Recorder()
        set_rec_2 = Recorder()
        self.assertTrue(
            env.add_listener(
                "get",
                SimpleListener("getlistener1", get_rec_1),
            ),
        )
        self.assertTrue(
            env.add_listener(
                "set",
                SimpleListener("setlistener1", set_rec_1),
            ),
        )
        # test get
        self.assertEqual(env.get(), 0)
        self.assertEqual(
            get_rec_1.value["env"],  # type: ignore [index]
            env,
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
        self.assertEqual(env.set(1), True)
        self.assertEqual(
            set_rec_1.value["env"],  # type: ignore [index]
            env,
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
            env.add_listener(
                "get",
                SimpleListener("getlistener1", get_rec_1),
            ),
        )
        self.assertTrue(
            env.add_listener(
                "get",
                SimpleListener("getlistener2", get_rec_2),
            ),
        )
        self.assertFalse(
            env.add_listener(
                "set",
                SimpleListener("setlistener1", set_rec_1),
            ),
        )
        self.assertTrue(
            env.add_listener(
                "set",
                SimpleListener("setlistener2", set_rec_2),
            ),
        )
        self.assertEqual(env.get(), 1)
        self.assertEqual(
            get_rec_1.value["env"],  # type: ignore [index]
            get_rec_2.value["env"],  # type: ignore [index]
        )
        self.assertEqual(
            get_rec_1.value["event_name"],  # type: ignore [index]
            get_rec_2.value["event_name"],  # type: ignore [index]
        )
        self.assertEqual(
            get_rec_1.value["event_args"],  # type: ignore [index]
            get_rec_2.value["event_args"],  # type: ignore [index]
        )
        self.assertTrue(env.set(10))
        self.assertEqual(
            set_rec_2.value["env"],  # type: ignore [index]
            env,
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
            env.add_listener(
                "non_existing_event",
                SimpleListener("non_existing_event", get_rec_2),
            ),
        )

    def test_get_set_child_item(self) -> None:
        """Test cases for child related operation"""
        env1 = MutableEnv(
            name="l0",
            value=0,
            children=[
                MutableEnv(
                    name="l1_0",
                    value=1,
                    children=[
                        MutableEnv(name="l2_0", value=3),
                        MutableEnv(name="l2_1", value=4),
                    ],
                ),
                MutableEnv(
                    name="l1_1",
                    value=2,
                    children=[
                        MutableEnv(name="l2_2", value=5),
                        MutableEnv(name="l2_3", value=6),
                    ],
                ),
            ],
        )
        env2 = MutableEnv(name="a1", value=10)
        env3 = MutableEnv(name="a2", value=20)
        self.assertEqual(env1["l1_0"].get(), 1)
        self.assertEqual(env1["l1_0"]["l2_0"].get(), 3)
        self.assertEqual(env1["l1_1"].get(), 2)
        self.assertEqual(env1["l1_1"]["l2_2"].get(), 5)
        env1["a3"] = env3
        self.assertEqual(env1["a3"], env3)
        env1["l1_1"]["a2"] = env2
        self.assertEqual(env1["l1_1"]["a2"], env2)

    def test_map2d_env(self) -> None:
        """Test cases for Map2d env"""
        m = Map2D(name="map")
        p1 = Point2D(
            name="p1",
            x=0,
            y=0,
        )
        p2 = EnvWithPoint2D(
            name="p2",
            value={},
            x=0,
            y=-1,
        )
        p3 = EnvWithPoint2D(
            name="p3",
            value={},
            x=3,
            y=4,
        )
        b1 = MutableEnv(name="b1", value="hi")
        m.register_point(p1)
        m.register_point(p2)
        m.register_point(p3)
        self.assertRaises(EnvTypeError, m.register_point, b1)
        self.assertRaises(EnvAlreadyExistError, m.register_point, p1)
        self.assertRaises(EnvTypeError, Map2D, "map", [b1])

        class InRangeListener(EventListener):
            """A listener that listens to in range events"""

            def __init__(self, name: str, owner: Env) -> None:
                super().__init__(name)
                self.owner = owner

            def __call__(self, env: Env, event: Event) -> None:
                self.owner._value[event.args["env_name"]] = event

        class OutRangeListener(EventListener):
            """A listener that listen to out of range events"""

            def __init__(self, name: str, owner: Env) -> None:
                super().__init__(name)
                self.owner = owner

            def __call__(self, env: Env, event: Event) -> None:
                if event.args["env_name"] in self.owner._value:
                    self.owner._value.pop(event.args["env_name"])

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
        m.move_child_to("p3", 2, 3)
        self.assertEqual(len(p3.get()), 1)
        self.assertTrue("p1" in p3.get())
        m.move_child_to("p3", 3, 3)
        self.assertEqual(len(p3.get()), 0)
        m.move_child_to("p1", 1, 3)
        self.assertEqual(len(p3.get()), 1)
        self.assertTrue("p1" in p3.get())
        self.assertEqual(len(p2.get()), 0)
        m.move_child_to("p2", 2, 3)
        self.assertEqual(len(p2.get()), 2)
        self.assertTrue("p1" in p2.get())
        self.assertTrue("p3" in p2.get())
        self.assertEqual(len(p3.get()), 2)
        self.assertTrue("p1" in p3.get())
        self.assertTrue("p2" in p3.get())

    def test_chatroom(self) -> None:
        """Test cases for chatroom env"""

        class Listener(EventListener):
            """Listener to record events"""

            def __init__(self, name: str, agent: AgentBase) -> None:
                super().__init__(name)
                self.agent = agent

            def __call__(self, env: Env, event: Event) -> None:
                self.agent(
                    Msg(
                        name="system",
                        role="system",
                        content={"event": event},
                    ),
                )

        ann = Msg(name="system", content="announce", role="system")
        r = ChatRoom(name="chat", announcement=ann)
        master = AgentWithChatRoom("master")
        master.join(r)
        self.assertTrue(
            r.add_listener("speak", Listener("speak_listener", master)),
        )
        self.assertTrue(
            r.add_listener("join", Listener("join_listener", master)),
        )
        self.assertTrue(
            r.add_listener("leave", Listener("leave_listener", master)),
        )
        self.assertTrue(
            r.add_listener("get_history", Listener("get_listener", master)),
        )
        self.assertTrue(
            r.add_listener(
                "set_announcement",
                Listener("set_announcement_listener", master),
            ),
        )
        self.assertTrue(
            r.add_listener(
                "get_announcement",
                Listener("get_announcement_listener", master),
            ),
        )

        # test join
        a1 = AgentWithChatRoom("a1")
        a1.join(r)
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
        self.assertEqual(master.event_list[-2].args["agent_name"], a1.name)
        self.assertEqual(r1.content, 0)

        a2 = AgentWithChatRoom("a2")
        a2.join(r)
        self.assertEqual(master.event_list[-1].name, "join")
        self.assertEqual(master.event_list[-1].args["agent"], a2)
        r2 = a2(Msg(name="user", role="user", content="hello"))
        self.assertEqual(master.event_list[-1].name, "speak")
        self.assertEqual(master.event_list[-1].args["message"], r2)
        self.assertEqual(master.event_list[-2].name, "get_history")
        self.assertEqual(master.event_list[-2].args["agent_name"], a2.name)
        self.assertEqual(r2.content, 0)

        # test history_idx
        self.assertEqual(r[a1.name].history_idx, 0)
        self.assertEqual(r[a2.name].history_idx, 1)


class AgentWithMutableEnv(AgentBase):
    """Agent with a mutable env"""

    def __init__(self, name: str, cnt: Env) -> None:
        super().__init__(name)
        self.cnt = cnt

    def reply(self, x: Msg = None) -> Msg:
        msg = Msg(name=self.name, role="assistant", content=self.cnt.get())
        if x is not None and x.content is not None:
            self.cnt.set(x.content)
        return msg


class RpcEnvTest(unittest.TestCase):
    """Test rpc version of env"""

    def test_mutable_env(self) -> None:
        """Test basic env"""
        cnt1 = MutableEnv(
            name="cnt1",
            value={
                "count": 0,
            },
        ).to_dist()
        self.assertTrue(isinstance(cnt1, RpcObject))
        cnt2 = MutableEnv(  # pylint: disable=E1123
            name="cnt2",
            value={
                "count": 1,
            },
            children=[cnt1],
            to_dist=True,
        )
        self.assertTrue(isinstance(cnt2, RpcObject))
        child = cnt2["cnt1"]
        self.assertEqual(child.get(), cnt1.get())
        agent1 = AgentWithMutableEnv(name="local_agent", cnt=cnt1)
        agent2 = AgentWithMutableEnv(
            name="remote_agent",
            cnt=cnt2,
        ).to_dist()
        self.assertTrue(isinstance(cnt2, RpcObject))
        self.assertTrue(cnt1.set(1))
        self.assertTrue(cnt2.set(2))
        self.assertEqual(cnt1.get(), 1)
        self.assertEqual(cnt2.get(), 2)
        r1 = agent1(Msg(name="user", role="user", content=3))
        r2 = agent2(Msg(name="user", role="user", content=-1))
        self.assertEqual(r1.content, 1)
        self.assertEqual(r2.content, 2)
        self.assertEqual(cnt1.get(), 3)
        self.assertEqual(cnt2.get(), -1)

    def test_chatroom(self) -> None:  # pylint: disable=R0915
        """Test chat room."""

        class Listener(EventListener):
            """Listener to record events"""

            def __init__(self, name: str, agent: AgentBase) -> None:
                super().__init__(name)
                self.agent = agent

            def __call__(self, env: Env, event: Event) -> None:
                msg = self.agent(
                    Msg(
                        name="system",
                        role="system",
                        content={"event": event},
                    ),
                )
                msg._fetch_result()

        ann = Msg(name="system", content="announce", role="system")
        r = ChatRoom(  # pylint: disable=E1123
            name="chat",
            announcement=ann,
            to_dist=True,
        )
        master = AgentWithChatRoom("master", to_dist=True)
        master.join(r)
        self.assertTrue(
            r.add_listener("speak", Listener("speak_listener", master)),
        )
        self.assertTrue(
            r.add_listener("join", Listener("join_listener", master)),
        )
        self.assertTrue(
            r.add_listener("leave", Listener("leave_listener", master)),
        )
        self.assertTrue(
            r.add_listener("get_history", Listener("get_listener", master)),
        )
        self.assertTrue(
            r.add_listener(
                "set_announcement",
                Listener("set_announcement_listener", master),
            ),
        )
        self.assertTrue(
            r.add_listener(
                "get_announcement",
                Listener("get_announcement_listener", master),
            ),
        )

        # test join
        a1 = AgentWithChatRoom("a1", to_dist=True)
        a1.join(r)
        self.assertEqual(master.get_event(-1).name, "join")
        event_agent_name = master.get_event(-1).args["agent"].name
        self.assertEqual(event_agent_name, a1.name)
        self.assertEqual(
            master.get_event(-1).args["agent"].agent_id,
            a1.agent_id,
        )

        # test announcement
        self.assertEqual(r.get_announcement(), ann)
        self.assertEqual(master.get_event(-1).name, "get_announcement")
        rann = Msg(name="system", content="Hello", role="system")
        r.set_announcement(rann)
        self.assertEqual(master.get_event(-1).name, "set_announcement")
        self.assertEqual(master.get_event(-1).args["announcement"], rann)

        # test speak
        r1 = a1(Msg(name="user", role="user", content="hello"))
        self.assertEqual(r1.content, 0)
        event = master.get_event(-1)
        self.assertEqual(event.name, "speak")
        self.assertEqual(event.args["message"].id, r1.id)
        self.assertEqual(event.args["message"].name, r1.name)
        self.assertEqual(event.args["message"].role, r1.role)
        self.assertEqual(event.args["message"].content, r1.content)
        event = master.get_event(-2)
        self.assertEqual(event.name, "get_history")
        self.assertEqual(event.args["agent_name"], a1.name)

        # test mix of rpc agent and local agent
        a2 = AgentWithChatRoom("a2")
        a2.join(r)
        event = master.get_event(-1)
        self.assertEqual(event.name, "join")
        self.assertEqual(event.args["agent"].name, a2.name)
        r2 = a2(Msg(name="user", role="user", content="hello"))
        self.assertEqual(r2.content, 0)
        self.assertEqual(master.get_event(-1).name, "speak")
        self.assertEqual(master.get_event(-1).args["message"], r2)
        self.assertEqual(master.get_event(-2).name, "get_history")

        # test rpc type
        ra1 = r[a1.name].agent
        self.assertTrue(isinstance(ra1, RpcObject))
        self.assertEqual(ra1.agent_id, a1.agent_id)
        rr = a1.chatroom()
        self.assertTrue(isinstance(rr, RpcObject))
        self.assertEqual(r._oid, rr._oid)  # pylint: disable=W0212

        # test history_idx
        self.assertEqual(r[a1.name].history_idx, 0)
        self.assertEqual(r[a2.name].history_idx, 1)
