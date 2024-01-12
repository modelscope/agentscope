# -*- coding: utf-8 -*-
""" An example of distributed debate """

import argparse
import json

import agentscope
from agentscope.msghub import msghub
from agentscope.agents.rpc_dialog_agent import RpcDialogAgent
from agentscope.agents.rpc_agent import RpcAgentServerLauncher
from agentscope.message import Msg
from agentscope.utils.logging_utils import logger

ANNOUNCEMENT = """
Welcome to the debate on whether Artificial General Intelligence (AGI) can be achieved using the GPT model framework. This debate will consist of three rounds. In each round, the affirmative side will present their argument first, followed by the negative side. After both sides have presented, the adjudicator will summarize the key points and analyze the strengths of the arguments.

The rules are as follows:

Each side must present clear, concise arguments backed by evidence and logical reasoning.
No side may interrupt the other while they are presenting their case.
After both sides have presented, the adjudicator will have time to deliberate and will then provide a summary, highlighting the most persuasive points from both sides.
The adjudicator's summary will not declare a winner for the individual rounds but will focus on the quality and persuasiveness of the arguments.
At the conclusion of the three rounds, the adjudicator will declare the overall winner based on which side won two out of the three rounds, considering the consistency and strength of the arguments throughout the debate.
Let us begin the first round. The affirmative side: please present your argument for why AGI can be achieved using the GPT model framework.
"""  # noqa


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--role",
        choices=["pro", "con", "judge", "main"],
        default="main",
    )
    parser.add_argument("--pro-host", type=str, default="localhost")
    parser.add_argument(
        "--pro-port",
        type=int,
        default=12011,
    )
    parser.add_argument("--con-host", type=str, default="localhost")
    parser.add_argument(
        "--con-port",
        type=int,
        default=12012,
    )
    parser.add_argument("--judge-host", type=str, default="localhost")
    parser.add_argument(
        "--judge-port",
        type=int,
        default=12013,
    )
    return parser.parse_args()


def setup_server(parsed_args: argparse.Namespace) -> None:
    """Setup rpc server for participant agent"""
    agentscope.init(
        model_configs="configs/model_configs.json",
    )
    with open(
        "configs/debate_agent_configs.json",
        "r",
        encoding="utf-8",
    ) as f:
        configs = json.load(f)
        config = configs[parsed_args.role]
        host = getattr(parsed_args, f"{parsed_args.role}_host")
        port = getattr(parsed_args, f"{parsed_args.role}_port")
        server_launcher = RpcAgentServerLauncher(
            host=host,
            port=port,
            local_mode=False,
            agent_class=RpcDialogAgent,
            **config,
        )
        server_launcher.launch()
        server_launcher.wait_until_terminate()


def run_main_process(parsed_args: argparse.Namespace) -> None:
    """Setup the main debate competition process"""
    agentscope.init(
        model_configs="configs/model_configs.json",
    )
    pro_agent = RpcDialogAgent(
        name="Pro",
        host=parsed_args.pro_host,
        port=parsed_args.pro_port,
        launch_server=False,
    )
    con_agent = RpcDialogAgent(
        name="Con",
        host=parsed_args.con_host,
        port=parsed_args.con_port,
        launch_server=False,
    )
    judge_agent = RpcDialogAgent(
        name="Judge",
        host=parsed_args.judge_host,
        port=parsed_args.judge_port,
        launch_server=False,
    )
    participants = [pro_agent, con_agent, judge_agent]
    hint = Msg(name="System", content=ANNOUNCEMENT)
    x = None
    with msghub(participants=participants, announcement=hint):
        for _ in range(3):
            pro_resp = pro_agent(x)
            logger.chat(pro_resp.update_value())
            con_resp = con_agent(pro_resp)
            logger.chat(con_resp.update_value())
            x = judge_agent(con_resp)
            logger.chat(x.update_value())
        x = judge_agent(x)
        logger.chat(x.update_value())


if __name__ == "__main__":
    args = parse_args()
    if args.role == "main":
        run_main_process(args)
    else:
        setup_server(args)
