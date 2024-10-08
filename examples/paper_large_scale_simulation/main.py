# -*- coding: utf-8 -*-
""" A large-scale social simulation experiment """
# pylint: disable=E0611,C0411
import argparse
import os

import agentscope
from agentscope.server import RpcAgentServerLauncher

from participants import (
    RandomParticipant,
    LLMParticipant,
    ParserAgent,
    Group,
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
        "--agent-server-per-host",
        type=int,
    )
    parser.add_argument("--model-per-host", type=int, default=1)
    parser.add_argument("--env-server-per-host", type=int, default=1)
    parser.add_argument("--sys-id", type=str, default="1")
    parser.add_argument("--usr-id", type=str, default="1")
    parser.add_argument("--model-name", type=str, default="llama3_8b")
    parser.add_argument("--exp-name", type=str, default="simulation")
    parser.add_argument("--ratio", type=str, default="2/3")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--participant")
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
        custom_agent_classes=[
            RandomParticipant,
            LLMParticipant,
            ParserAgent,
            Group,
        ],
    )
    assistant_server_launcher.launch(in_subprocess=False)
    assistant_server_launcher.wait_until_terminate()


if __name__ == "__main__":
    args = parse_args()
    if args.role == "participant":
        setup_participant_agent_server(args.hosts[0], args.base_port)
    elif args.role == "main":
        agentscope.init(
            project="simulation",
            name="main",
            runtime_id="main",
            save_code=False,
            save_api_invoke=False,
            use_monitor=False,
            logger_level="INFO",
            save_dir=SAVE_DIR,
        )
        GuessTwoThirdGame(
            hosts=args.hosts,
            base_port=args.base_port,
            participant_num=args.participant_num,
            agent_server_per_host=args.agent_server_per_host,
            env_server_per_host=args.env_server_per_host,
            model_per_host=args.model_per_host,
            agent_type=args.agent_type,
            sleep_time=args.sleep_time,
            max_value=args.max_value,
            model_name=args.model_name,
            sys_id=args.sys_id,
            usr_id=args.usr_id,
            name=args.exp_name,
            ratio=args.ratio,
            round=args.round,
        ).run()
