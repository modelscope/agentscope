# -*- coding: utf-8 -*-
"""Simulation benchmark

Please install pytest and pytest-benchmark to run this benchmark.
"""

import pytest  # pylint: disable=W0611
from participant import Moderator, RandomParticipant, LLMParticipant
from main import run_main_process  # pylint: disable=E0611
import agentscope
from agentscope.server import RpcAgentServerLauncher


def test_simulation(benchmark):  # type: ignore[no-untyped-def]
    """A single benchmark for the simulation"""
    base_port = 23300
    par_server_num = 4
    mod_server_num = 1
    agentscope.init(
        project="simulation",
        name="server",
        save_code=False,
        save_api_invoke=False,
        model_configs="configs/model_configs.json",
        use_monitor=False,
    )
    launchers = []
    for i in range(par_server_num + mod_server_num):
        launcher = RpcAgentServerLauncher(
            host="localhost",
            port=base_port + i,
            custom_agents=[Moderator, RandomParticipant, LLMParticipant],
        )
        launcher.launch()
        launchers.append(launcher)
    benchmark(
        run_main_process,
        hosts=["localhost"],
        base_port=23300,
        server_per_host=4,
        model_per_host=1,
        participant_num=400,
        moderator_per_host=1,
        agent_type="random",
        max_value=100,
        sleep_time=1.0,
    )
    for launcher in launchers:
        launcher.shutdown()
