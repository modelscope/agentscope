# -*- coding: utf-8 -*-
"""
Unit tests for rpc agent classes
"""
import unittest
import time
import shutil
from loguru import logger

import agentscope
from agentscope.agents import AgentBase
from agentscope.agents.rpc_agent import RpcAgentServerLauncher
from agentscope.message import Msg
from agentscope.message import PlaceholderMessage
from agentscope.message import deserialize
from agentscope.msghub import msghub
from agentscope.pipelines import sequentialpipeline
from agentscope.utils import MonitorFactory, QuotaExceededError


class DemoRpcAgent(AgentBase):
    """A demo Rpc agent for test usage."""

    def __init__(self, **kwargs) -> None:  # type: ignore [no-untyped-def]
        super().__init__(**kwargs)
        self.id = 0

    def reply(self, x: dict = None) -> dict:
        """Response after 2s"""
        x.id = self.id
        self.id += 1
        time.sleep(2)
        return x


class DemoRpcAgentAdd(AgentBase):
    """A demo Rpc agent for test usage"""

    def reply(self, x: dict = None) -> dict:
        """add the value, wait 1s"""
        x.content["value"] += 1
        time.sleep(1)
        return x


class DemoLocalAgentAdd(AgentBase):
    """A demo local agent for test usage"""

    def reply(self, x: dict = None) -> dict:
        """add the value, wait 1s"""
        x.content["value"] += 1
        time.sleep(1)
        return x


class DemoRpcAgentWithMemory(AgentBase):
    """A demo Rpc agent that count its memory"""

    def reply(self, x: dict = None) -> dict:
        self.memory.add(x)
        msg = Msg(name=self.name, content={"mem_size": self.memory.size()})
        self.memory.add(msg)
        time.sleep(1)
        return msg


class DemoRpcAgentWithMonitor(AgentBase):
    """A demo Rpc agent that use monitor"""

    def reply(self, x: dict = None) -> dict:
        monitor = MonitorFactory.get_monitor()
        try:
            monitor.update({"msg_num": 1})
        except QuotaExceededError:
            x.content["quota_exceeded"] = True
            logger.chat(
                {
                    "name": self.name,
                    "content": "quota_exceeded",
                },
            )
            return x
        x.content["msg_num"] = monitor.get_value("msg_num")
        logger.chat(
            {
                "name": self.name,
                "content": f"msg_num {x.content['msg_num']}",
            },
        )
        time.sleep(0.2)
        return x


class BasicRpcAgentTest(unittest.TestCase):
    "Test cases for Rpc Agent"

    def setUp(self) -> None:
        """Init for Rpc Agent Test"""
        agentscope.init(
            project="test",
            name="rpc_agent",
            save_dir="./test_runs",
            save_log=True,
        )

    def tearDown(self) -> None:
        MonitorFactory._instance = None  # pylint: disable=W0212
        logger.remove()
        shutil.rmtree("./test_runs")

    def test_single_rpc_agent_server(self) -> None:
        """test setup a single rpc agent"""
        host = "localhost"
        port = 12001
        agent_a = DemoRpcAgent(
            name="a",
        ).to_dist(
            host=host,
            port=port,
        )
        self.assertIsNotNone(agent_a)
        msg = Msg(name="System", content={"text": "hello world"})
        result = agent_a(msg)
        # get name without waiting for the server
        self.assertEqual(result.name, "a")
        self.assertEqual(result["name"], "a")
        js_placeholder_result = result.serialize()
        self.assertTrue(result._is_placeholder)  # pylint: disable=W0212
        placeholder_result = deserialize(js_placeholder_result)
        self.assertTrue(isinstance(placeholder_result, PlaceholderMessage))
        self.assertEqual(placeholder_result.name, "a")
        self.assertEqual(
            placeholder_result["name"],  # type: ignore [call-overload]
            "a",
        )
        self.assertTrue(
            placeholder_result._is_placeholder,  # pylint: disable=W0212
        )
        # wait to get content
        self.assertEqual(result.content, msg.content)
        self.assertFalse(result._is_placeholder)  # pylint: disable=W0212
        self.assertEqual(result.id, 0)
        self.assertTrue(
            placeholder_result._is_placeholder,  # pylint: disable=W0212
        )
        self.assertEqual(placeholder_result.content, msg.content)
        self.assertFalse(
            placeholder_result._is_placeholder,  # pylint: disable=W0212
        )
        self.assertEqual(placeholder_result.id, 0)
        # check msg
        js_msg_result = result.serialize()
        msg_result = deserialize(js_msg_result)
        self.assertTrue(isinstance(msg_result, Msg))
        self.assertEqual(msg_result.content, msg.content)
        self.assertEqual(msg_result.id, 0)
        # check id increase
        msg = agent_a(msg_result)  # type: ignore [arg-type]
        self.assertEqual(msg.id, 1)

    def test_connect_to_an_existing_rpc_server(self) -> None:
        """test connecting to an existing server"""
        launcher = RpcAgentServerLauncher(
            # choose port automatically
            agent_class=DemoRpcAgent,
            agent_kwargs={
                "name": "a",
            },
            local_mode=False,
            host="127.0.0.1",
            port=12010,
        )
        launcher.launch()
        agent_a = DemoRpcAgent(
            name="a",
        ).to_dist(
            host="127.0.0.1",
            port=launcher.port,
            launch_server=False,
        )
        msg = Msg(name="System", content={"text": "hello world"})
        result = agent_a(msg)
        # get name without waiting for the server
        self.assertEqual(result.name, "a")
        # waiting for server
        self.assertEqual(result.content, msg.content)
        # test dict usage
        msg = Msg(name="System", content={"text": "hi world"})
        result = agent_a(msg)
        # get name without waiting for the server
        self.assertEqual(result["name"], "a")
        # waiting for server
        self.assertEqual(result["content"], msg.content)
        # test to_str
        msg = Msg(name="System", content={"text": "test"})
        result = agent_a(msg)
        self.assertEqual(result.to_str(), "a: {'text': 'test'}")
        launcher.shutdown()

    def test_multi_rpc_agent(self) -> None:
        """test setup multi rpc agent"""
        host = "localhost"
        port1 = 12001
        port2 = 12002
        port3 = 12003
        agent_a = DemoRpcAgentAdd(
            name="a",
        ).to_dist(
            host=host,
            port=port1,
            lazy_launch=False,
        )
        agent_b = DemoRpcAgentAdd(
            name="b",
        ).to_dist(
            host=host,
            port=port2,
            lazy_launch=False,
        )
        agent_c = DemoRpcAgentAdd(
            name="c",
        ).to_dist(
            host=host,
            port=port3,
            lazy_launch=False,
        )

        # test sequential
        msg = Msg(name="System", content={"value": 0})
        start_time = time.time()
        msg = agent_a(msg)
        self.assertTrue(isinstance(msg, PlaceholderMessage))
        msg = agent_b(msg)
        self.assertTrue(isinstance(msg, PlaceholderMessage))
        msg = agent_c(msg)
        self.assertTrue(isinstance(msg, PlaceholderMessage))
        return_time = time.time()
        # should return directly
        self.assertTrue((return_time - start_time) < 1)
        self.assertEqual(msg.content["value"], 3)
        end_time = time.time()
        # need at least 3s to finish
        self.assertTrue((end_time - start_time) >= 3)

        # test parallel
        msg = Msg(name="System", content={"value": -1})
        start_time = time.time()
        msg_a = agent_a(msg)
        msg_b = agent_b(msg)
        msg_c = agent_c(msg)
        self.assertEqual(msg_a.content["value"], 0)
        self.assertEqual(msg_b.content["value"], 0)
        self.assertEqual(msg_c.content["value"], 0)
        end_time = time.time()
        # need 1s to finish
        self.assertTrue((end_time - start_time) < 1.5)

    def test_mix_rpc_agent_and_local_agent(self) -> None:
        """test to use local and rpc agent simultaneously"""
        host = "localhost"
        # use the same port, agents should choose available ports
        # automatically
        port1 = 12001
        port2 = 12001
        # rpc agent a
        agent_a = DemoRpcAgentAdd(
            name="a",
        ).to_dist(
            host=host,
            port=port1,
            lazy_launch=False,
        )
        # local agent b
        agent_b = DemoLocalAgentAdd(
            name="b",
        )
        # rpc agent c
        agent_c = DemoRpcAgentAdd(
            name="c",
        ).to_dist(
            host=host,
            port=port2,
            lazy_launch=False,
        )
        msg = Msg(name="System", content={"value": 0})

        while msg.content["value"] < 4:
            msg = agent_a(msg)
            msg = agent_b(msg)
            msg = agent_c(msg)
        self.assertEqual(msg.content["value"], 6)

    def test_msghub_compatibility(self) -> None:
        """test compatibility with msghub"""
        agent_a = DemoRpcAgentWithMemory(
            name="a",
        ).to_dist()
        agent_b = DemoRpcAgentWithMemory(
            name="b",
        ).to_dist()
        agent_c = DemoRpcAgentWithMemory(
            name="c",
        ).to_dist()
        participants = [agent_a, agent_b, agent_c]
        annonuncement_msgs = [
            Msg(name="System", content="Announcement 1"),
            Msg(name="System", content="Announcement 2"),
        ]
        with msghub(
            participants=participants,
            announcement=annonuncement_msgs,
        ):
            x_a = agent_a()
            x_b = agent_b(x_a)
            x_c = agent_c(x_b)
            self.assertEqual(x_a.content["mem_size"], 2)
            self.assertEqual(x_b.content["mem_size"], 3)
            self.assertEqual(x_c.content["mem_size"], 4)
            x_a = agent_a(x_c)
            self.assertEqual(x_a.content["mem_size"], 5)
            x_b = agent_b(x_a)
            self.assertEqual(x_b.content["mem_size"], 6)
            x_c = agent_c(x_b)
            self.assertEqual(x_c.content["mem_size"], 7)
            x_c = sequentialpipeline(participants, x_c)
            self.assertEqual(x_c.content["mem_size"], 10)

    def test_standalone_multiprocess_init(self) -> None:
        """test compatibility with agentscope.init"""
        monitor = MonitorFactory.get_monitor()
        monitor.register("msg_num", quota=10)
        host = "localhost"
        # automatically
        port1 = 12001
        port2 = 12002
        # rpc agent a
        agent_a = DemoRpcAgentWithMonitor(
            name="a",
        ).to_dist(
            host=host,
            port=port1,
            lazy_launch=False,
        )
        # local agent b
        agent_b = DemoRpcAgentWithMonitor(
            name="b",
        ).to_dist(
            host=host,
            port=port2,
            lazy_launch=False,
        )
        msg = Msg(name="System", content={"msg_num": 0})
        j = 0
        for _ in range(5):
            msg = agent_a(msg)
            self.assertEqual(msg["content"]["msg_num"], j + 1)
            msg = agent_b(msg)
            self.assertEqual(msg["content"]["msg_num"], j + 2)
            j += 2
        msg = agent_a(msg)
        logger.chat(msg)
        self.assertTrue(msg["content"]["quota_exceeded"])
        msg = agent_b(msg)
        logger.chat(msg)
        self.assertTrue(msg["content"]["quota_exceeded"])
