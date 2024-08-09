# -*- coding: utf-8 -*-
""" A large-scale social simulation experiment """

import argparse
import os

import agentscope
from agentscope.agents import AgentBase
from agentscope.agents.rpc_agent import RpcAgentServerLauncher

from utils.participant import (
    RandomParticipant,
    LLMParticipant,
    ParserAgent,
    GuessTwoThirdGame,
)


SAVE_DIR = f"./runs/{os.uname().nodename}"

RATIO_MAP = {
    "1/2": 1 / 2,
    "2/3": 2 / 3,
    "3/5": 3 / 5,
    "51/100": 51 / 100,
    "67/100": 67 / 100,
}


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--role",
        choices=["participant", "main"],
        default="participant",
    )
    parser.add_argument(
        "--agent-type",
        choices=["random", "llm"],
        default="random",
    )
    parser.add_argument("--max-value", type=int, default=100)
    parser.add_argument("--sleep-time", type=float, default=1.0)
    parser.add_argument(
        "--hosts",
        type=str,
        nargs="+",
        default=["localhost"],
    )
    parser.add_argument("--participant-num", type=int, default=100)
    parser.add_argument("--base-port", type=int, default=12010)
    parser.add_argument(
        "--server-per-host",
        type=int,
    )
    parser.add_argument("--model-per-host", type=int, default=1)
    parser.add_argument("--moderator-per-host", type=int, default=1)
    parser.add_argument("--ann-id", type=str, default="1")
    parser.add_argument("--pmt-id", type=str, default="3")
    parser.add_argument("--model-name", type=str, default="llama3_8b")
    parser.add_argument("--exp-name", type=str, default="simulation")
    parser.add_argument("--ratio", type=str, default="2/3")
    parser.add_argument("--round", type=int, default=1)
    return parser.parse_args()


def setup_participant_agent_server(host: str, port: int) -> None:
    """Set up agent server"""
    agentscope.init(
        project="simulation",
        name="server",
        runtime_id=f"server_{host}_{port}",
        save_code=False,
        save_api_invoke=False,
        model_configs="configs/model_configs.json",
        use_monitor=False,
        logger_level="ERROR",
        save_dir=SAVE_DIR,
    )
    assistant_server_launcher = RpcAgentServerLauncher(
        host=host,
        port=port,
        max_pool_size=16384,
        custom_agents=[
            Moderator,
            RandomParticipant,
            LLMParticipant,
            ParserAgent,
        ],
    )
    assistant_server_launcher.launch(in_subprocess=False)
    assistant_server_launcher.wait_until_terminate()


def init_moderator(
    name: str,
    configs: list[dict],
    host: str,
    port: int,
    agent_type: str,
    max_value: int,
    sleep_time: float,
    usr_id: str,
) -> AgentBase:
    """Init moderator"""
    return Moderator(  # pylint: disable=E1123
        name=name,
        part_configs=configs,
        agent_type=agent_type,
        max_value=max_value,
        sleep_time=sleep_time,
        to_dist={
            "host": host,
            "port": port,
        },
        usr_id=usr_id,
    )


if __name__ == "__main__":
    args = parse_args()
    if args.role == "participant":
        setup_participant_agent_server(args.hosts[0], args.base_port)
    elif args.role == "main":
        GuessTwoThirdGame(
            hosts=args.hosts,
            base_port=args.base_port,
            participant_num=args.participant_num,
            server_per_host=args.server_per_host,
            model_per_host=args.model_per_host,
            env_per_host=args.moderator_per_host,
            agent_type=args.agent_type,
            sleep_time=args.sleep_time,
            max_value=args.max_value,
            model_name=args.model_name,
            sys_id=args.sys_id,
            usr_id=args.usr_id,
            exp_name=args.exp_name,
            ratio=args.ratio,
            round=args.round,
        ).run()
