# -*- coding: utf-8 -*-
"""An auction simulation."""
import argparse

from agents import Bidder, RandomBidder
from env import Item, Auction
from listeners import StartListener, BidListener

import agentscope


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

    auction = Auction("auction", waiting_time=waiting_time)

    if agent_type == "random":
        bidders = [RandomBidder(f"bidder_{i}") for i in range(bidder_num)]
    else:
        bidders = [
            Bidder(f"bidder_{i}", model_config_name="model")
            for i in range(bidder_num)
        ]

    # enable distributed mode
    if use_dist:
        auction = auction.to_dist()
        bidders = [bidder.to_dist() for bidder in bidders]

    # Set up listeners
    start_listeners = [
        StartListener(f"start_{i}", bidders[i]) for i in range(bidder_num)
    ]
    bid_listeners = [
        BidListener(f"bid_{i}", bidders[i]) for i in range(bidder_num)
    ]
    listeners = {
        "start": start_listeners,
        "bid": bid_listeners,
    }
    for target_event, listeners in listeners.items():
        for listener in listeners:
            auction.add_listener(target_event, listener)

    item = Item("oil_painting", opening_price=10)
    auction.run(item)


if __name__ == "__main__":
    args = parse_args()
    main(
        bidder_num=args.bidder_num,
        agent_type=args.agent_type,
        waiting_time=args.waiting_time,
        use_dist=args.use_dist,
    )
