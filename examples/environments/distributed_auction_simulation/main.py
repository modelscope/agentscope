# -*- coding: utf-8 -*-
""" A large-scale social simulation experiment """
# pylint: disable=E1123

import argparse
import math
from concurrent import futures
from loguru import logger

from agents import Auctioneer, Bidder, RandomBidder
from env import Item, Auction
from listeners import StartListener, BidListener, BidTimerListener

import agentscope
from agentscope.server import RpcAgentServerLauncher


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--role",
        choices=["server", "main"],
        default="main",
    )
    parser.add_argument("--bidder-num", type=int, default=5)
    parser.add_argument(
        "--agent-type",
        choices=["random", "llm"],
        default="random",
    )
    parser.add_argument("--waiting-time", type=float, default=3.0)
    parser.add_argument(
        "--hosts",
        type=str,
        nargs="+",
        default=["localhost"],
    )
    parser.add_argument("--base-port", type=int, default=12010)
    parser.add_argument(
        "--server-per-host",
        type=int,
    )
    parser.add_argument("--model-per-host", type=int, default=1)
    return parser.parse_args()


def setup_agent_server(host: str, port: int) -> None:
    """Set up agent server"""
    agentscope.init(
        project="distributed_auction_simulation",
        name="server",
        runtime_id=str(port),
        save_code=False,
        save_api_invoke=False,
        model_configs="configs/model_configs.json",
        use_monitor=False,
    )
    assistant_server_launcher = RpcAgentServerLauncher(
        host=host,
        port=port,
        max_pool_size=16384,
        custom_agent_classes=[RandomBidder, Bidder, Auctioneer, Auction],
    )
    assistant_server_launcher.launch(in_subprocess=False)
    assistant_server_launcher.wait_until_terminate()


def run_main_process(
    hosts: list[str],
    base_port: int,
    server_per_host: int,
    model_per_host: int,
    bidder_num: int = 5,
    agent_type: str = "random",
    waiting_time: float = 3.0,
) -> None:
    """Run main process"""
    agentscope.init(
        project="distributed_auction_simulation",
        name="main",
        save_code=False,
        save_api_invoke=False,
        model_configs="configs/model_configs.json",
        use_monitor=False,
    )
    host_num = len(hosts)
    total_agent_server_num = server_per_host * host_num
    bidder_per_agent_server = math.ceil(
        bidder_num / total_agent_server_num,
    )

    auction = Auction("auction", to_dist={"host": hosts[0], "port": base_port})

    configs = []
    logger.info(f"init {bidder_num} {agent_type} bidder agents...")
    # build init configs of bidders
    for i in range(bidder_num):
        idx = i // bidder_per_agent_server
        host_id = idx // server_per_host
        port_id = idx % server_per_host
        model_id = i % model_per_host
        host = hosts[host_id]
        port = base_port + port_id
        config_name = f"model_{model_id + 1}"
        if agent_type == "random":
            configs.append(
                {
                    "host": host,
                    "port": port,
                },
            )
        else:
            configs.append(
                {
                    "model_config_name": config_name,
                    "host": host,
                    "port": port,
                },
            )

    auctioneer = Auctioneer(
        "auctioneer",
        auction,
        waiting_time=waiting_time,
        to_dist={"host": hosts[0], "port": base_port},
    )

    # init bidders
    bidders = []
    tasks = []
    with futures.ThreadPoolExecutor() as executor:
        for i in range(bidder_num):
            if agent_type == "random":
                tasks.append(
                    executor.submit(
                        RandomBidder,
                        name=f"bidder_{i}",
                        to_dist={
                            "host": configs[i]["host"],
                            "port": configs[i]["port"],
                        },
                    ),
                )
            else:
                tasks.append(
                    executor.submit(
                        Bidder,
                        name=f"bidder_{i}",
                        model_config_name=configs[i]["model_config_name"],
                        to_dist={
                            "host": configs[i]["host"],
                            "port": configs[i]["port"],
                        },
                    ),
                )
        for task in tasks:
            bidders.append(task.result())

    start_listeners = [
        StartListener(f"start_{i}", bidders[i]) for i in range(bidder_num)
    ]
    bid_timer_listener = [BidTimerListener("bid_timer", auctioneer)]
    bid_listeners = [
        BidListener(f"bid_{i}", bidders[i]) for i in range(bidder_num)
    ]
    listeners = {
        "start": start_listeners,
        "bid": bid_timer_listener + bid_listeners,
    }
    for target_event, listeners in listeners.items():
        for listener in listeners:
            auction.add_listener(target_event, listener)

    item = Item("oil_painting", opening_price=10)
    auction.start(item)


if __name__ == "__main__":
    args = parse_args()
    if args.role == "server":
        setup_agent_server(args.hosts[0], args.base_port)
    elif args.role == "main":
        run_main_process(
            hosts=args.hosts,
            base_port=args.base_port,
            server_per_host=args.server_per_host,
            model_per_host=args.model_per_host,
            bidder_num=args.bidder_num,
            agent_type=args.agent_type,
            waiting_time=args.waiting_time,
        )
