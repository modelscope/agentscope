# -*- coding: utf-8 -*-
"""
Unit tests for rpc agent classes
"""
import unittest
import time
import shutil
from loguru import logger

import agentscope
from agentscope.agents import AgentBase, DistConf
from agentscope.agents.rpc_agent import RpcAgentServerLauncher
from agentscope.message import Msg
from agentscope.message import PlaceholderMessage
from agentscope.message import deserialize
from agentscope.msghub import msghub
from agentscope.pipelines import sequentialpipeline
from agentscope.utils import MonitorFactory, QuotaExceededError


class DemoRpcAgent(AgentBase):
    """A demo Rpc agent for test usage."""

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
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
        msg = Msg(
            name=self.name,
            content={"mem_size": self.memory.size()},
            role="assistant",
        )
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


class DemoGeneratorAgent(AgentBase):
    """A demo agent to generate a number"""

    def __init__(self, name: str, value: int) -> None:
        super().__init__(name)
        self.value = value

    def reply(self, _: dict = None) -> dict:
        time.sleep(1)
        return Msg(
            name=self.name,
            role="assistant",
            content={
                "value": self.value,
            },
        )


class DemoGatherAgent(AgentBase):
    """A demo agent to gather value"""

    def __init__(
        self,
        name: str,
        agents: list[DemoGeneratorAgent],
        to_dist: dict = None,
    ) -> None:
        super().__init__(name, to_dist=to_dist)
        self.agents = agents

    def reply(self, _: dict = None) -> dict:
        result = []
        stime = time.time()
        for agent in self.agents:
            result.append(agent())
        value = 0
        for r in result:
            value += r.content["value"]
        etime = time.time()
        return Msg(
            name=self.name,
            role="assistant",
            content={
                "value": value,
                "time": etime - stime,
            },
        )


class DemoErrorAgent(AgentBase):
    """A demo Rpc agent that raise Error"""

    def reply(self, x: dict = None) -> dict:
        raise RuntimeError("Demo Error")


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
        agent_a = DemoRpcAgent(
            name="a",
            to_dist=True,
        )
        self.assertIsNotNone(agent_a)
        msg = Msg(
            name="System",
            content={"text": "hello world"},
            role="system",
        )
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
            placeholder_result["name"],  # type: ignore[call-overload]
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
        msg = agent_a(msg_result)  # type: ignore[arg-type]
        self.assertEqual(msg.id, 1)

    def test_connect_to_an_existing_rpc_server(self) -> None:
        """test connecting to an existing server"""
        launcher = RpcAgentServerLauncher(
            # choose port automatically
            host="127.0.0.1",
            port=12010,
            local_mode=False,
            custom_agents=[DemoRpcAgent],
        )
        launcher.launch()
        agent_a = DemoRpcAgent(
            name="a",
        ).to_dist(
            host="127.0.0.1",
            port=launcher.port,
        )
        msg = Msg(
            name="System",
            content={"text": "hello world"},
            role="system",
        )
        result = agent_a(msg)
        # get name without waiting for the server
        self.assertEqual(result.name, "a")
        # waiting for server
        self.assertEqual(result.content, msg.content)
        # test dict usage
        msg = Msg(
            name="System",
            content={"text": "hi world"},
            role="system",
        )
        result = agent_a(msg)
        # get name without waiting for the server
        self.assertEqual(result["name"], "a")
        # waiting for server
        self.assertEqual(result["content"], msg.content)
        # test to_str
        msg = Msg(
            name="System",
            content={"text": "test"},
            role="system",
        )
        result = agent_a(msg)
        self.assertEqual(result.to_str(), "a: {'text': 'test'}")
        launcher.shutdown()

    def test_multi_rpc_agent(self) -> None:
        """test setup multi rpc agent"""
        agent_a = DemoRpcAgentAdd(
            name="a",
        ).to_dist(
            lazy_launch=False,
        )
        agent_b = DemoRpcAgentAdd(
            name="b",
        ).to_dist(
            lazy_launch=False,
        )
        agent_c = DemoRpcAgentAdd(
            name="c",
        ).to_dist(
            lazy_launch=False,
        )

        # test sequential
        msg = Msg(
            name="System",
            content={"value": 0},
            role="system",
        )
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
        msg = Msg(
            name="System",
            content={"value": -1},
            role="system",
        )
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
        agent_a = DemoRpcAgentAdd(
            name="a",
        ).to_dist(
            lazy_launch=False,
        )
        # local agent b
        agent_b = DemoLocalAgentAdd(
            name="b",
        )
        # rpc agent c
        agent_c = DemoRpcAgentAdd(  # pylint: disable=E1123
            name="c",
            to_dist=DistConf(
                lazy_launch=False,
            ),
        )
        msg = Msg(
            name="System",
            content={"value": 0},
            role="system",
        )

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
            to_dist=True,
        )
        participants = [agent_a, agent_b, agent_c]
        annonuncement_msgs = [
            Msg(name="System", content="Announcement 1", role="system"),
            Msg(name="System", content="Announcement 2", role="system"),
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
        # rpc agent a
        agent_a = DemoRpcAgentWithMonitor(
            name="a",
        ).to_dist(
            lazy_launch=False,
        )
        # local agent b
        agent_b = DemoRpcAgentWithMonitor(
            name="b",
        ).to_dist(
            lazy_launch=False,
        )
        msg = Msg(name="System", content={"msg_num": 0}, role="system")
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

    def test_multi_agent_in_same_server(self) -> None:
        """test agent server with multi agent"""
        launcher = RpcAgentServerLauncher(
            host="127.0.0.1",
            port=12010,
            local_mode=False,
            custom_agents=[DemoRpcAgentWithMemory],
        )
        launcher.launch()
        # although agent1 and agent2 connect to the same server
        # they are different instances with different memories
        agent1 = DemoRpcAgentWithMemory(
            name="a",
        )
        oid = agent1.agent_id
        agent1 = agent1.to_dist(
            host="127.0.0.1",
            port=launcher.port,
        )
        self.assertEqual(oid, agent1.agent_id)
        self.assertEqual(oid, agent1.client.agent_id)
        agent2 = DemoRpcAgentWithMemory(  # pylint: disable=E1123
            name="a",
            to_dist={
                "host": "127.0.0.1",
                "port": launcher.port,
            },
        )
        # agent3 has the same agent id as agent1
        # so it share the same memory with agent1
        agent3 = DemoRpcAgentWithMemory(
            name="a",
        ).to_dist(
            host="127.0.0.1",
            port=launcher.port,
        )
        agent3._agent_id = agent1.agent_id  # pylint: disable=W0212
        agent3.client.agent_id = agent1.client.agent_id
        msg1 = Msg(name="System", content="First Msg for agent1")
        res1 = agent1(msg1)
        self.assertEqual(res1.content["mem_size"], 1)
        msg2 = Msg(name="System", content="First Msg for agent2")
        res2 = agent2(msg2)
        self.assertEqual(res2.content["mem_size"], 1)
        msg3 = Msg(name="System", content="First Msg for agent3")
        res3 = agent3(msg3)
        self.assertEqual(res3.content["mem_size"], 3)
        msg4 = Msg(name="System", content="Second Msg for agent2")
        res4 = agent2(msg4)
        self.assertEqual(res4.content["mem_size"], 3)
        # delete existing agent
        agent2.client.delete_agent()
        msg2 = Msg(name="System", content="First Msg for agent2")
        res2 = agent2(msg2)
        self.assertRaises(ValueError, res2.__getattr__, "content")

        # should override remote default parameter(e.g. name field)
        agent4 = DemoRpcAgentWithMemory(
            name="b",
        ).to_dist(
            host="127.0.0.1",
            port=launcher.port,
        )
        msg5 = Msg(name="System", content="Second Msg for agent4")
        res5 = agent4(msg5)
        self.assertEqual(res5.name, "b")
        self.assertEqual(res5.content["mem_size"], 1)
        launcher.shutdown()

    def test_clone_instances(self) -> None:
        """Test the clone_instances method of RpcAgent"""
        agent = DemoRpcAgentWithMemory(
            name="a",
        ).to_dist()
        # lazy launch will not init client
        self.assertIsNone(agent.client)
        # generate two agents (the first is it self)
        agents = agent.clone_instances(2)
        self.assertEqual(len(agents), 2)
        agent1 = agents[0]
        agent2 = agents[1]
        self.assertTrue(agent1.agent_id.startswith("DemoRpcAgentWithMemory"))
        self.assertTrue(agent2.agent_id.startswith("DemoRpcAgentWithMemory"))
        self.assertTrue(
            agent1.client.agent_id.startswith("DemoRpcAgentWithMemory"),
        )
        self.assertTrue(
            agent2.client.agent_id.startswith("DemoRpcAgentWithMemory"),
        )
        self.assertNotEqual(agent1.agent_id, agent2.agent_id)
        self.assertEqual(agent1.agent_id, agent1.client.agent_id)
        self.assertEqual(agent2.agent_id, agent2.client.agent_id)
        # clone instance will init client
        self.assertIsNotNone(agent.client)
        self.assertEqual(agent.agent_id, agent1.agent_id)
        self.assertNotEqual(agent1.agent_id, agent2.agent_id)
        self.assertIsNotNone(agent.server_launcher)
        self.assertIsNotNone(agent1.server_launcher)
        self.assertIsNone(agent2.server_launcher)
        msg1 = Msg(name="System", content="First Msg for agent1")
        res1 = agent1(msg1)
        self.assertEqual(res1.content["mem_size"], 1)
        msg2 = Msg(name="System", content="First Msg for agent2")
        res2 = agent2(msg2)
        self.assertEqual(res2.content["mem_size"], 1)
        new_agents = agent.clone_instances(2, including_self=False)
        agent3 = new_agents[0]
        agent4 = new_agents[1]
        self.assertEqual(len(new_agents), 2)
        self.assertNotEqual(agent3.agent_id, agent.agent_id)
        self.assertNotEqual(agent4.agent_id, agent.agent_id)
        self.assertIsNone(agent3.server_launcher)
        self.assertIsNone(agent4.server_launcher)
        msg3 = Msg(name="System", content="First Msg for agent3")
        res3 = agent3(msg3)
        self.assertEqual(res1.content["mem_size"], 1)
        msg4 = Msg(name="System", content="First Msg for agent4")
        res4 = agent4(msg4)
        self.assertEqual(res3.content["mem_size"], 1)
        self.assertEqual(res4.content["mem_size"], 1)

    def test_error_handling(self) -> None:
        """Test error handling"""
        agent = DemoErrorAgent(name="a").to_dist()
        x = agent()
        self.assertRaises(RuntimeError, x.__getattr__, "content")

    def test_agent_nesting(self) -> None:
        """Test agent nesting"""
        host = "localhost"
        launcher1 = RpcAgentServerLauncher(
            # choose port automatically
            host=host,
            port=12010,
            local_mode=False,
            custom_agents=[DemoGatherAgent, DemoGeneratorAgent],
        )
        launcher2 = RpcAgentServerLauncher(
            # choose port automatically
            host=host,
            port=12011,
            local_mode=False,
            custom_agents=[DemoGatherAgent, DemoGeneratorAgent],
        )
        launcher1.launch()
        launcher2.launch()
        agents = []
        for i in range(8):
            if i % 2:
                agents.append(
                    DemoGeneratorAgent(name=f"a_{i}", value=i).to_dist(
                        host=host,
                        port=launcher1.port,
                    ),
                )
            else:
                agents.append(
                    DemoGeneratorAgent(name=f"a_{i}", value=i).to_dist(
                        host=host,
                        port=launcher2.port,
                    ),
                )
        gather1 = DemoGatherAgent(  # pylint: disable=E1123
            name="g1",
            agents=agents[:4],
            to_dist=DistConf(
                host=host,
                port=launcher1.port,
            ),
        )
        gather2 = DemoGatherAgent(  # pylint: disable=E1123
            name="g2",
            agents=agents[4:],
            to_dist={
                "host": host,
                "port": launcher2.port,
            },
        )
        r1 = gather1()
        r2 = gather2()
        self.assertEqual(r1.content["value"], 6)
        self.assertEqual(r2.content["value"], 22)
        self.assertTrue(0.5 < r1.content["time"] < 2)
        self.assertTrue(0.5 < r2.content["time"] < 2)
        launcher1.shutdown()
        launcher2.shutdown()
