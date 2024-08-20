# -*- coding: utf-8 -*-
"""An auction simulation."""
import argparse

from agents import Auctioneer, Bidder, RandomBidder
from env import Item, Auction
from listeners import StartListener, BidListener, BidTimerListener

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
    return parser.parse_args()


def main(
    bidder_num: int = 5,
    agent_type: str = "random",
    waiting_time: float = 3.0,
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

    auctioneer = Auctioneer("auctioneer", auction, waiting_time=waiting_time)
    if agent_type == "random":
        bidders = [RandomBidder(f"bidder_{i}") for i in range(bidder_num)]
    else:
        bidders = [
            Bidder(f"bidder_{i}", model_config_name="model")
            for i in range(bidder_num)
        ]

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
    main(
        bidder_num=args.bidder_num,
        agent_type=args.agent_type,
        waiting_time=args.waiting_time,
    )
