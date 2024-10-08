# -*- coding: utf-8 -*-
"""An auction simulation."""
import argparse
from multiprocessing import Event

from agents import Auctioneer, Bidder, RandomBidder
from env import Item, Auction
from listeners import StartListener, BidListener, BidTimerListener

import agentscope
from agentscope.server import RpcAgentServerLauncher


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--bidder-num", type=int, default=5)
    parser.add_argument(
        "--agent-type",
        choices=["random", "llm"],
        default="random",
    )
    parser.add_argument("--waiting-time", type=float, default=3.0)
    parser.add_argument("--use-dist", action="store_true")
    return parser.parse_args()


def main(
    bidder_num: int = 5,
    agent_type: str = "random",
    waiting_time: float = 3.0,
    use_dist: bool = False,
) -> None:
    """The main function."""
    agentscope.init(
        project="auction_simulation",
        name="main",
        save_code=False,
        save_api_invoke=False,
        model_configs="configs/model_configs.json",
        use_monitor=False,
    )

    auction = Auction("auction")

    if agent_type == "random":
        bidders = [RandomBidder(f"bidder_{i}") for i in range(bidder_num)]
    else:
        bidders = [
            Bidder(f"bidder_{i}", model_config_name="model")
            for i in range(bidder_num)
        ]

    if use_dist:
        stop_event = Event()
        env_server_launcher = RpcAgentServerLauncher()
        env_server_launcher.stop_event = stop_event
        env_server_launcher.launch()
        auction = auction.to_dist(
            host=env_server_launcher.host,
            port=env_server_launcher.port,
        )

        bidders = [bidder.to_dist() for bidder in bidders]
        auctioneer = Auctioneer(
            "auctioneer",
            auction,
            waiting_time=waiting_time,
        ).to_dist()
    else:
        auctioneer = Auctioneer(
            "auctioneer",
            auction,
            waiting_time=waiting_time,
        )

    # Set up listeners
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

    if use_dist:
        stop_event.wait()  # need to manually shut down in dist mode


if __name__ == "__main__":
    args = parse_args()
    main(
        bidder_num=args.bidder_num,
        agent_type=args.agent_type,
        waiting_time=args.waiting_time,
        use_dist=args.use_dist,
    )
