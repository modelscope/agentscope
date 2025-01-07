# -*- coding: utf-8 -*-
# pylint: disable=W0212
"""
Unit tests for rpc agent classes
"""
import unittest
import os
import time
import shutil
from typing import Optional, Union, Sequence, Callable
from unittest.mock import MagicMock, PropertyMock, patch

from loguru import logger
import cloudpickle as pickle


import agentscope
from agentscope.agents import AgentBase, DialogAgent
from agentscope.manager import MonitorManager, ASManager
from agentscope.server import RpcAgentServerLauncher
from agentscope.rpc import AsyncResult, RpcObject, DistConf
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.pipelines import sequentialpipeline
from agentscope.rpc import RpcClient, async_func
from agentscope.exception import (
    AgentCallError,
    QuotaExceededError,
    AgentCreationError,
)
from agentscope.rpc.retry_strategy import (
    RetryFixedTimes,
    RetryExpential,
)


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

    def raise_error(self) -> Msg:
        """Raise an error"""
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


class AgentWithCustomFunc(AgentBase):
    """An agent with custom function"""

    def __init__(  # type: ignore[no-untyped-def]
        self,
        name: str,
        judge_func: Callable[[str], bool],
        **kwargs,
    ) -> None:
        super().__init__(name, **kwargs)
        self.cnt = 0
        self.judge_func = judge_func

    def reply(self, x: Msg = None) -> Msg:
        return Msg(
            name=self.name,
            role="assistant",
            content="Hello",
        )

    def custom_func_with_msg(self, x: Msg = None) -> Msg:
        """A custom function with Msg input output"""
        return x

    def custom_func_with_basic(self, num: int) -> int:
        """A custom function with basic value input output"""
        return num

    def custom_judge_func(self, x: str) -> bool:
        """A custom function with basic value input output"""
        res = self.judge_func(x)
        return res

    @async_func
    def custom_async_func(self, num: int) -> int:
        """A custom function that executes in async"""
        time.sleep(num)
        self.cnt += num
        return self.cnt

    def custom_sync_func(self) -> int:
        """A custom function that executes in sync"""
        return self.cnt

    @async_func
    def long_running_func(self) -> int:
        """A custom function that executes in sync"""
        time.sleep(5)
        return 1


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
        self.assertTrue(not result._ready)  # pylint: disable=W0212
        # get name without waiting for the server
        js_placeholder_result = pickle.dumps(result)
        self.assertTrue(not result._ready)  # pylint: disable=W0212
        placeholder_result = pickle.loads(js_placeholder_result)
        self.assertTrue(isinstance(placeholder_result, AsyncResult))

        # Fetch the attribute from distributed agent
        self.assertTrue(not result._ready)
        self.assertEqual(result.name, "System")
        self.assertFalse(not result._ready)

        # wait to get content
        self.assertEqual(result.content, msg.content)
        self.assertEqual(result.id, 0)

        # The second time to fetch the attributes from the distributed agent
        self.assertTrue(
            not placeholder_result._ready,
        )
        self.assertEqual(placeholder_result.content, msg.content)
        self.assertFalse(
            not placeholder_result._ready,
        )
        self.assertEqual(placeholder_result.id, 0)

        # check msg
        js_msg_result = pickle.dumps(result)
        msg_result = pickle.loads(js_msg_result)
        self.assertTrue(isinstance(msg_result, Msg))
        self.assertEqual(msg_result.content, msg.content)
        self.assertEqual(msg_result.id, 0)
        # check id increase
        msg = agent_a(msg_result)  # type: ignore[arg-type]
        self.assertEqual(msg.id, 1)

    def test_connect_to_an_existing_rpc_server(self) -> None:
        """test connecting to an existing server"""
        from agentscope.utils.common import _find_available_port

        port = _find_available_port()
        launcher = RpcAgentServerLauncher(
            # choose port automatically
            host="127.0.0.1",
            port=port,
            local_mode=False,
            custom_agent_classes=[DemoRpcAgent],
        )
        launcher.launch()
        self.assertEqual(port, launcher.port)
        client = RpcClient(host=launcher.host, port=launcher.port)
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
        self.assertTrue(isinstance(msg, AsyncResult))
        msg = agent_b(msg)
        self.assertTrue(isinstance(msg, AsyncResult))
        msg = agent_c(msg)
        self.assertTrue(isinstance(msg, AsyncResult))
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
            # TODO: fix this test
            x_a = agent_a()
            x_b = agent_b(x_a)
            x_c = agent_c(x_b)
            self.assertGreaterEqual(x_a.content["mem_size"], 2)
            self.assertGreaterEqual(x_b.content["mem_size"], 3)
            self.assertGreaterEqual(x_c.content["mem_size"], 4)
            x_a = agent_a(x_c)
            self.assertGreaterEqual(x_a.content["mem_size"], 5)
            x_b = agent_b(x_a)
            self.assertGreaterEqual(x_b.content["mem_size"], 6)
            x_c = agent_c(x_b)
            self.assertGreaterEqual(x_c.content["mem_size"], 7)
            x_c = sequentialpipeline(participants, x_c)
            self.assertGreaterEqual(x_c.content["mem_size"], 10)

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
        oid = agent1._oid
        agent1 = agent1.to_dist(
            host="127.0.0.1",
            port=launcher.port,
        )
        self.assertEqual(oid, agent1._oid)
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
        agent3._oid = agent1._oid  # pylint: disable=W0212
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
        agent2.client.delete_agent(agent2._oid)
        msg2 = Msg(
            name="System",
            content="First Msg for agent2",
            role="system",
        )
        res = agent2(msg2)
        self.assertRaises(Exception, res.update_value)

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

    def test_error_handling(self) -> None:
        """Test error handling"""
        agent = DemoErrorAgent(name="a").to_dist()
        x = agent()
        self.assertRaises(AgentCallError, x._fetch_result)
        self.assertRaises(AgentCallError, agent.raise_error)

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
        client = RpcClient(host="localhost", port=launcher.port)
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
        resp._fetch_result()
        memory = client.get_agent_memory(memory_agent._oid)
        self.assertEqual(len(memory), 2)
        self.assertEqual(memory[0]["content"], "first msg")
        self.assertEqual(memory[1]["content"]["mem_size"], 1)
        agent_lists = client.get_agent_list()
        self.assertEqual(len(agent_lists), 1)
        self.assertEqual(agent_lists[0]["agent_id"], memory_agent._oid)
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
        self.assertNotEqual(remote_file_path, local_file_path)
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
        dialog = DialogAgent(  # pylint: disable=E1123
            name="dialogue",
            sys_prompt="You are a helful assistant.",
            model_config_name="my_openai",
            to_dist={
                "host": "localhost",
                "port": launcher.port,
            },
        )
        self.assertRaises(AgentCreationError, dialog._check_created)
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
        a1._check_created()  # pylint: disable=W0212
        a2._check_created()  # pylint: disable=W0212
        self.assertEqual(a1.host, host)
        self.assertEqual(a1.port, port)
        self.assertEqual(a2.host, host)
        self.assertEqual(a2.port, port)
        client = RpcClient(host=host, port=port)
        al = client.get_agent_list()
        self.assertEqual(len(al), 2)

        # test not alive server
        mock_alloc.return_value = {"host": "not_exist", "port": 1234}
        a3 = DemoRpcAgentWithMemory(name="Auto3", to_dist=True)
        self.assertEqual(a3.host, "localhost")
        nclient = RpcClient(host=a3.host, port=a3.port)
        a3._check_created()  # pylint: disable=W0212
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
                    "type": "agent",
                },
                agent_id=custom_agent_id,
            ),
        )
        ra = RpcObject(
            cls=AgentBase,
            host=launcher.host,
            port=launcher.port,
            oid=custom_agent_id,
            connect_existing=True,
        )
        resp = ra(Msg(name="sys", role="user", content="Hello"))
        self.assertEqual(resp.name, "custom")
        self.assertEqual(resp.content, "Hello world")
        al = client.get_agent_list()
        self.assertEqual(len(al), 3)

        launcher.shutdown()

    def test_custom_agent_func(self) -> None:
        """Test custom agent funcs"""
        agent = AgentWithCustomFunc(
            name="custom",
            judge_func=lambda x: "$PASS$" in x,
            to_dist={
                "max_timeout_seconds": 1,
                "retry_strategy": RetryFixedTimes(max_retries=2, delay=5),
            },
        )

        msg = agent.reply()
        self.assertEqual(msg.content, "Hello")
        r = agent.custom_func_with_msg(msg)
        self.assertEqual(r["content"], msg.content)
        r = agent.custom_func_with_basic(1)
        self.assertFalse(agent.custom_judge_func("diuafhsua$FAIL$"))
        self.assertTrue(agent.custom_judge_func("72354rfv$PASS$"))
        self.assertEqual(r, 1)
        start_time = time.time()
        r1 = agent.custom_async_func(1)
        r2 = agent.custom_async_func(1)
        r3 = agent.custom_sync_func()
        end_time = time.time()
        self.assertTrue(end_time - start_time < 1)
        self.assertEqual(r3, 0)
        self.assertTrue(isinstance(r1, AsyncResult))
        self.assertTrue(r1.result() <= 2)
        self.assertTrue(r2.result() <= 2)
        r4 = agent.custom_sync_func()
        self.assertEqual(r4, 2)
        r5 = agent.long_running_func()
        self.assertEqual(r5.result(), 1)

    def test_retry_strategy(self) -> None:
        """Test retry strategy"""
        max_retries = 3
        delay = 1
        max_delay = 2
        fix_retry = RetryFixedTimes(max_retries=max_retries, delay=delay)
        exp_retry = RetryExpential(
            max_retries=max_retries,
            base_delay=delay,
            max_delay=max_delay,
        )
        # Retry on exception
        mock_func = MagicMock(side_effect=Exception("Test exception"))
        st = time.time()
        self.assertRaises(TimeoutError, fix_retry.retry, mock_func)
        et = time.time()
        self.assertTrue(et - st > max_retries * delay * 0.5)
        self.assertTrue(et - st < max_retries * delay * 1.5 + 1)
        st = time.time()
        self.assertRaises(TimeoutError, exp_retry.retry, mock_func)
        et = time.time()
        self.assertTrue(
            et - st
            > min(delay * 0.5, max_delay)
            + min(delay * 2 * 0.5, max_delay)
            + min(delay * 4 * 0.5, max_delay),
        )
        self.assertTrue(
            et - st
            < min(delay * 1.5, max_delay)
            + min(delay * 2 * 1.5, max_delay)
            + min(delay * 4 * 1.5, max_delay)
            + 1,
        )
        # Retry on success
        mock_func = MagicMock(return_value="Success")
        st = time.time()
        result = fix_retry.retry(mock_func)
        et = time.time()
        self.assertTrue(et - st < 0.2)
        self.assertEqual(result, "Success")
        st = time.time()
        result = exp_retry.retry(mock_func)
        et = time.time()
        self.assertTrue(et - st < 0.2)
        self.assertEqual(result, "Success")
        # Mix Exception and Success
        mock_func = MagicMock(
            side_effect=[Exception("Test exception"), "Success"],
        )
        st = time.time()
        result = fix_retry.retry(mock_func)
        et = time.time()
        self.assertGreaterEqual(et - st, delay * 0.5)
        self.assertLessEqual(et - st, delay * 1.5 + 0.2)
        self.assertEqual(result, "Success")
        mock_func = MagicMock(
            side_effect=[Exception("Test exception"), "Success"],
        )
        st = time.time()
        result = exp_retry.retry(mock_func)
        et = time.time()
        self.assertGreaterEqual(et - st, delay * 0.5)
        self.assertLessEqual(et - st, delay * 1.5 + 0.2)
        self.assertEqual(result, "Success")
