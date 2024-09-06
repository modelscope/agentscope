# -*- coding: utf-8 -*-
# pylint: disable=W0212
"""
Unit tests for rpc agent classes
"""
import unittest
import os
import time
import shutil
from typing import Optional, Union, Sequence
from unittest.mock import MagicMock, PropertyMock, patch

from loguru import logger

import agentscope
from agentscope.agents import AgentBase, DistConf, DialogAgent
from agentscope.manager import MonitorManager, ASManager
from agentscope.serialize import deserialize, serialize
from agentscope.server import RpcAgentServerLauncher
from agentscope.message import Msg
from agentscope.message import PlaceholderMessage
from agentscope.msghub import msghub
from agentscope.pipelines import sequentialpipeline
from agentscope.rpc.rpc_agent_client import RpcAgentClient
from agentscope.agents.rpc_agent import RpcAgent
from agentscope.exception import AgentCallError, QuotaExceededError


class DemoRpcAgent(AgentBase):
    """A demo Rpc agent for test usage."""

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        self.id = 0

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """Response after 2s"""
        x.id = self.id
        self.id += 1
        time.sleep(2)
        return x


class DemoRpcAgentAdd(AgentBase):
    """A demo Rpc agent for test usage"""

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """add the value, wait 1s"""
        x.content["value"] += 1
        time.sleep(1)
        return x


class DemoLocalAgentAdd(AgentBase):
    """A demo local agent for test usage"""

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """add the value, wait 1s"""
        x.content["value"] += 1
        time.sleep(1)
        return x


class DemoRpcAgentWithMemory(AgentBase):
    """A demo Rpc agent that count its memory"""

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
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

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        monitor = MonitorManager.get_instance()
        try:
            monitor.update({"msg_num": 1})
        except QuotaExceededError:
            x.content["quota_exceeded"] = True
            logger.chat(
                Msg(self.name, "quota_exceeded", "assistant"),
            )
            return x
        x.content["msg_num"] = monitor.get_value("msg_num")
        logger.chat(
            Msg(self.name, f"msg_num {x.content['msg_num']}", "assistant"),
        )
        time.sleep(0.2)
        return x


class DemoGeneratorAgent(AgentBase):
    """A demo agent to generate a number"""

    def __init__(self, name: str, value: int) -> None:
        super().__init__(name)
        self.value = value

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
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

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
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

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        raise RuntimeError("Demo Error")


class FileAgent(AgentBase):
    """An agent returns a file"""

    def reply(self, x: Msg = None) -> Msg:
        image_path = os.path.abspath(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "data",
                "image.png",
            ),
        )
        return Msg(
            name=self.name,
            role="assistant",
            content="Image",
            url=image_path,
        )


class BasicRpcAgentTest(unittest.TestCase):
    """Test cases for Rpc Agent"""

    def setUp(self) -> None:
        """Init for Rpc Agent Test"""
        agentscope.init(
            project="test",
            name="rpc_agent",
            model_configs=os.path.abspath(
                os.path.join(
                    os.path.abspath(os.path.dirname(__file__)),
                    "custom",
                    "test_model_config.json",
                ),
            ),
            save_dir="./.unittest_runs",
            save_log=True,
        )
        self.assertTrue(os.path.exists("./.unittest_runs"))

    def tearDown(self) -> None:
        """Tear down the test environment."""
        ASManager.get_instance().flush()
        shutil.rmtree("./.unittest_runs")

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

        # The deserialization without accessing the attributes will generate
        # a PlaceholderMessage instance.
        js_placeholder_result = serialize(result)
        placeholder_result = deserialize(js_placeholder_result)
        self.assertTrue(isinstance(placeholder_result, PlaceholderMessage))

        # Fetch the attribute from distributed agent
        self.assertTrue(result._is_placeholder)
        self.assertEqual(result.name, "System")
        self.assertFalse(result._is_placeholder)

        # wait to get content
        self.assertEqual(result.content, msg.content)
        self.assertEqual(result.id, 0)

        # The second time to fetch the attributes from the distributed agent
        self.assertTrue(
            placeholder_result._is_placeholder,
        )
        self.assertEqual(placeholder_result.content, msg.content)
        self.assertFalse(
            placeholder_result._is_placeholder,
        )
        self.assertEqual(placeholder_result.id, 0)

        # check msg
        js_msg_result = serialize(result)
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
            custom_agent_classes=[DemoRpcAgent],
        )
        launcher.launch()
        client = RpcAgentClient(host=launcher.host, port=launcher.port)
        self.assertTrue(client.is_alive())
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
        self.assertEqual(result.name, "System")
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
        self.assertEqual(result.name, "System")
        # waiting for server
        self.assertEqual(result.content, msg.content)
        # test to_str
        msg = Msg(
            name="System",
            content={"text": "test"},
            role="system",
        )
        result = agent_a(msg)
        self.assertEqual(result.formatted_str(), "System: {'text': 'test'}")
        launcher.shutdown()

    def test_multi_rpc_agent(self) -> None:
        """test setup multi rpc agent"""
        agent_a = DemoRpcAgentAdd(
            name="a",
        ).to_dist()
        agent_b = DemoRpcAgentAdd(
            name="b",
        ).to_dist()
        agent_c = DemoRpcAgentAdd(
            name="c",
        ).to_dist()

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
        ).to_dist()
        # local agent b
        agent_b = DemoLocalAgentAdd(
            name="b",
        )
        # rpc agent c
        agent_c = DemoRpcAgentAdd(  # pylint: disable=E1123
            name="c",
            to_dist=True,
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

    def test_multi_agent_in_same_server(self) -> None:
        """test agent server with multi-agent"""
        launcher = RpcAgentServerLauncher(
            host="127.0.0.1",
            port=-1,
            local_mode=False,
            custom_agent_classes=[DemoRpcAgentWithMemory],
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
        agent3._agent_id = agent1.agent_id
        agent3.client.agent_id = agent1.client.agent_id
        msg1 = Msg(
            name="System",
            content="First Msg for agent1",
            role="system",
        )
        res1 = agent1(msg1)
        self.assertEqual(res1.content["mem_size"], 1)
        msg2 = Msg(
            name="System",
            content="First Msg for agent2",
            role="system",
        )
        res2 = agent2(msg2)
        self.assertEqual(res2.content["mem_size"], 1)
        msg3 = Msg(
            name="System",
            content="First Msg for agent3",
            role="system",
        )
        res3 = agent3(msg3)
        self.assertEqual(res3.content["mem_size"], 3)
        msg4 = Msg(
            name="System",
            content="Second Msg for agent2",
            role="system",
        )
        res4 = agent2(msg4)
        self.assertEqual(res4.content["mem_size"], 3)
        # delete existing agent
        agent2.client.delete_agent(agent2.agent_id)
        msg2 = Msg(
            name="System",
            content="First Msg for agent2",
            role="system",
        )
        res2 = agent2(msg2)
        self.assertRaises(ValueError, res2.update_value)

        # should override remote default parameter(e.g. name field)
        agent4 = DemoRpcAgentWithMemory(
            name="b",
        ).to_dist(
            host="127.0.0.1",
            port=launcher.port,
        )
        msg5 = Msg(
            name="System",
            content="Second Msg for agent4",
            role="system",
        )
        res5 = agent4(msg5)
        self.assertEqual(res5.name, "b")
        self.assertEqual(res5.content["mem_size"], 1)
        launcher.shutdown()

    def test_clone_instances(self) -> None:
        """Test the clone_instances method of RpcAgent"""
        agent = DemoRpcAgentWithMemory(
            name="a",
        ).to_dist(lazy_launch=True)
        # lazy launch will not init client
        self.assertIsNone(agent.client)
        # generate two agents (the first is it self)
        agents = agent.clone_instances(2)
        self.assertEqual(len(agents), 2)
        agent1 = agents[0]
        agent2 = agents[1]
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
        msg1 = Msg(
            name="System",
            content="First Msg for agent1",
            role="system",
        )
        res1 = agent1(msg1)
        self.assertEqual(res1.content["mem_size"], 1)
        msg2 = Msg(
            name="System",
            content="First Msg for agent2",
            role="system",
        )
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
        msg3 = Msg(
            name="System",
            content="First Msg for agent3",
            role="system",
        )
        res3 = agent3(msg3)
        self.assertEqual(res1.content["mem_size"], 1)
        msg4 = Msg(
            name="System",
            content="First Msg for agent4",
            role="system",
        )
        res4 = agent4(msg4)
        self.assertEqual(res3.content["mem_size"], 1)
        self.assertEqual(res4.content["mem_size"], 1)

    def test_error_handling(self) -> None:
        """Test error handling"""
        agent = DemoErrorAgent(name="a").to_dist()
        x = agent()
        self.assertRaises(AgentCallError, x.update_value)

    def test_agent_nesting(self) -> None:
        """Test agent nesting"""
        host = "localhost"
        launcher1 = RpcAgentServerLauncher(
            # choose port automatically
            host=host,
            port=12010,
            local_mode=False,
            custom_agent_classes=[DemoGatherAgent, DemoGeneratorAgent],
        )
        launcher2 = RpcAgentServerLauncher(
            # choose port automatically
            host=host,
            port=12011,
            local_mode=False,
            custom_agent_classes=[DemoGatherAgent, DemoGeneratorAgent],
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

    def test_agent_server_management_funcs(self) -> None:
        """Test agent server management functions"""
        launcher = RpcAgentServerLauncher(
            host="localhost",
            port=12010,
            local_mode=False,
            custom_agent_classes=[DemoRpcAgentWithMemory, FileAgent],
        )
        launcher.launch()
        client = RpcAgentClient(host="localhost", port=launcher.port)
        agent_lists = client.get_agent_list()
        self.assertEqual(len(agent_lists), 0)
        memory_agent = DemoRpcAgentWithMemory(
            name="demo",
            to_dist={
                "host": "localhost",
                "port": launcher.port,
            },
        )
        resp = memory_agent(Msg(name="test", content="first msg", role="user"))
        resp.update_value()
        memory = client.get_agent_memory(memory_agent.agent_id)
        self.assertEqual(len(memory), 2)
        self.assertEqual(memory[0].content, "first msg")
        self.assertEqual(memory[1].content["mem_size"], 1)
        agent_lists = client.get_agent_list()
        self.assertEqual(len(agent_lists), 1)
        self.assertEqual(agent_lists[0]["agent_id"], memory_agent.agent_id)
        agent_info = agent_lists[0]
        logger.info(agent_info)
        server_info = client.get_server_info()
        logger.info(server_info)
        self.assertTrue("pid" in server_info)
        self.assertTrue("id" in server_info)
        self.assertTrue("cpu" in server_info)
        self.assertTrue("mem" in server_info)
        # test download file
        file_agent = FileAgent("File").to_dist(
            host="localhost",
            port=launcher.port,
        )
        file = file_agent()
        remote_file_path = os.path.abspath(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "data",
                "image.png",
            ),
        )
        local_file_path = file.url
        self.assertEqual(remote_file_path, local_file_path)
        with open(remote_file_path, "rb") as rf:
            remote_content = rf.read()
        with open(local_file_path, "rb") as lf:
            local_content = lf.read()
        self.assertEqual(remote_content, local_content)
        agent_lists = client.get_agent_list()
        self.assertEqual(len(agent_lists), 2)
        # test existing model config
        DialogAgent(
            name="dialogue",
            sys_prompt="You are a helful assistant.",
            model_config_name="qwen",
            to_dist={
                "host": "localhost",
                "port": launcher.port,
            },
        )
        # model not exists error
        self.assertRaises(
            Exception,
            DialogAgent,
            name="dialogue",
            sys_prompt="You are a helful assistant.",
            model_config_name="my_openai",
            to_dist={
                "host": "localhost",
                "port": launcher.port,
            },
        )
        # set model configs
        client.set_model_configs(
            [
                {
                    "model_type": "openai_chat",
                    "config_name": "my_openai",
                    "model_name": "gpt-3.5-turbo",
                    "api_key": "xxx",
                    "organization": "xxx",
                    "generate_args": {
                        "temperature": 0.5,
                    },
                },
                {
                    "model_type": "post_api_chat",
                    "config_name": "my_postapi",
                    "api_url": "https://xxx",
                    "headers": {},
                },
            ],
        )
        # create agent after set model configs
        dia_agent = DialogAgent(  # pylint: disable=E1123
            name="dialogue",
            sys_prompt="You are a helful assistant.",
            model_config_name="my_openai",
            to_dist={
                "host": "localhost",
                "port": launcher.port,
            },
        )
        self.assertIsNotNone(dia_agent)
        self.assertTrue(client.delete_all_agent())
        self.assertEqual(len(client.get_agent_list()), 0)
        # client.stop()
        # time.sleep(1)
        # self.assertFalse(client.is_alive())
        launcher.shutdown()

    @patch("agentscope.studio._client.StudioClient.alloc_server")
    @patch(
        "agentscope.studio._client.StudioClient.active",
        new_callable=PropertyMock,
    )
    def test_server_auto_alloc(
        self,
        mock_active: PropertyMock,
        mock_alloc: MagicMock,
    ) -> None:
        """Test the auto allocation of server"""
        mock_active.return_value = True
        host = "localhost"
        launcher = RpcAgentServerLauncher(
            # choose port automatically
            host=host,
            local_mode=False,
            custom_agent_classes=[DemoRpcAgentWithMemory],
            agent_dir=os.path.abspath(
                os.path.join(
                    os.path.abspath(os.path.dirname(__file__)),
                    "custom",
                ),
            ),
        )
        launcher.launch()
        port = launcher.port
        mock_alloc.return_value = {"host": host, "port": port}

        # test auto allocation
        a1 = DemoRpcAgentWithMemory(name="Auto1", to_dist=True)
        a2 = DemoRpcAgentWithMemory(name="Auto2").to_dist()
        self.assertEqual(a1.host, host)
        self.assertEqual(a1.port, port)
        self.assertEqual(a2.host, host)
        self.assertEqual(a2.port, port)
        client = RpcAgentClient(host=host, port=port)
        al = client.get_agent_list()
        self.assertEqual(len(al), 2)

        # test not alive server
        mock_alloc.return_value = {"host": "not_exist", "port": 1234}
        a3 = DemoRpcAgentWithMemory(name="Auto3", to_dist=True)
        self.assertEqual(a3.host, "localhost")
        nclient = RpcAgentClient(host=a3.host, port=a3.port)
        nal = nclient.get_agent_list()
        self.assertEqual(len(nal), 1)

        # test agent dir loading
        custom_agent_id = "custom_test"
        self.assertTrue(
            client.create_agent(
                agent_configs={
                    "args": (),
                    "kwargs": {"name": "custom"},
                    "class_name": "CustomAgent",
                },
                agent_id=custom_agent_id,
            ),
        )
        ra = RpcAgent(
            name="custom",
            host=launcher.host,
            port=launcher.port,
            agent_id=custom_agent_id,
            connect_existing=True,
        )
        resp = ra(Msg(name="sys", role="user", content="Hello"))
        self.assertEqual(resp.name, "custom")
        self.assertEqual(resp.content, "Hello world")
        al = client.get_agent_list()
        self.assertEqual(len(al), 3)

        launcher.shutdown()
