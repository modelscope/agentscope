# -*- coding: utf-8 -*-
"""The envs used to simulate an auction."""
import time
from typing import Any, Dict, Optional
from threading import Lock

from loguru import logger

from agentscope.environment import BasicEnv, event_func
from agentscope.message import Msg


class Item:
    """The item class."""

    def __init__(
        self,
        name: str,
        opening_price: int = 5,
        is_auctioned: bool = False,
    ) -> None:
        """Initialize the item."""
        self.name = name
        self.opening_price = opening_price
        self.is_auctioned = is_auctioned

    def to_dict(self) -> dict:
        """Convert the item to a dict."""
        return {
            "name": self.name,
            "opening_price": self.opening_price,
            "is_auctioned": self.is_auctioned,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        """Convert the item from a dict."""
        assert "name" in data
        return cls(
            name=data["name"],
            opening_price=data.get("opening_price", 5),
            is_auctioned=data.get("is_auctioned", False),
        )


class Auction(BasicEnv):
    """The auction env."""

    def __init__(
        self,
        name: str = None,
        waiting_time: float = 3.0,
    ) -> None:
        """Initialize the auction env.

        Args:
            name (`str`): The name of the Auction.
            waiting_time (`float`): The waiting time between bids.
        """
        super().__init__(
            name=name,
        )
        self.waiting_time = waiting_time
        self.end_time = 0
        self.cur_item = None
        self.cur_bid_info = None
        self.bid_lock = Lock()

    def get_bid_info(self) -> Optional[Dict[str, Any]]:
        """Get the bid info.
        Returns:
            `Dict[str, Any]`: The bid info.
        """
        return self.cur_bid_info

    @event_func
    def start(self, item: Item) -> None:
        """Start bidding for an item.
        Args:
            item (`Item`): The item.
        """
        self.cur_item = item
        self.cur_bid_info = None
        self.end_time = time.time() + self.waiting_time
        logger.chat(
            Msg(name="Auction", role="system", content="Auction starts!"),
        )

    def run(self, item: Item) -> None:
        """Run bidding for an item.
        Args:
            item (`Item`): The item.
        """
        self.start(item)
        while time.time() < self.end_time:
            time.sleep(1)
        logger.chat(
            Msg(name="Auction", role="system", content="Auction ends!"),
        )
        if self.cur_bid_info is None:
            self.fail()
        else:
            self.sold()

    @event_func
    def bid(self, bidder_name: str, item: Item, bid: int) -> bool:
        """Bid for the auction.
        Args:
            bidder_name (`str`): The name of the bidder.
            item (`Item`): The item.
            bid (`int`): The bid of the bidder.

        Returns:
            `bool`: Whether the bid was successful.
        """
        with self.bid_lock:
            if (
                self.cur_item.is_auctioned
                or bid < item.opening_price
                or (self.cur_bid_info and bid <= self.cur_bid_info["bid"])
            ):
                return False
            self.cur_bid_info = {"bidder": bidder_name, "bid": bid}
            self.end_time = time.time() + self.waiting_time
            return True

    def fail(self) -> None:
        """Pass the auction. (No bid for the item)"""
        self.cur_item.is_auctioned = True
        logger.chat(
            Msg(
                name="Auction",
                role="system",
                content=f"{self.cur_item.name} is not sold",
            ),
        )

    def sold(self) -> None:
        """Sold the item."""
        self.cur_item.is_auctioned = True
        logger.chat(
            Msg(
                name="Auction",
                role="system",
                content=(
                    f"{self.cur_item.name} is sold to "
                    f"{self.cur_bid_info['bidder']} "  # type: ignore[index]
                    f"for {self.cur_bid_info['bid']}"  # type: ignore[index]
                ),
            ),
        )
