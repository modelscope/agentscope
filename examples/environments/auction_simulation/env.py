# -*- coding: utf-8 -*-
"""The envs used to simulate an auction."""
from typing import Any, Dict, List, Optional

from loguru import logger

from agentscope.agents import AgentBase
from agentscope.environment import Event, BasicEnv, EventListener, event_func
from agentscope.environment.env import trigger_listener


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


class Auction(BasicEnv):
    """The auction env."""

    def __init__(
        self,
        name: str = None,
        listeners: List[EventListener] = None,
    ) -> None:
        """Initialize the auction env.

        Args:
            name (`str`): The name of the Auction.
            listeners (`List[EventListener]`): The listeners.
        """
        super().__init__(
            name=name,
            listeners=listeners,
        )
        self.cur_item = None
        self.cur_bid_info = None

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

    def bid(self, bidder: AgentBase, item: Item, bid: int) -> bool:
        """Bid for the auction.
        Args:
            bidder (`AgentBase`): The bidder agent.
            item (`Item`): The item.
            bid (`int`): The bid of the bidder.

        Returns:
            `bool`: Whether the bid was successful.
        """
        if (
            self.cur_item.is_auctioned
            or bid < item.opening_price
            or (self.cur_bid_info and bid <= self.cur_bid_info["bid"])
        ):
            return False
        self.cur_bid_info = {"bidder": bidder, "bid": bid}
        logger.info(f"{bidder.name} bid {bid} for {item.name}")
        trigger_listener(
            self,
            Event(
                "bid",
                args={"bidder": bidder, "item": self.cur_item, "bid": bid},
            ),
        )
        return True

    @event_func
    def fail(self) -> None:
        """Pass the auction. (No bid for the item)"""
        self.cur_item.is_auctioned = True
        logger.info(f"{self.cur_item.name} is not sold")

    @event_func
    def sold(self) -> None:
        """Sold the item."""
        self.cur_item.is_auctioned = True
        logger.info(
            f"{self.cur_item.name} is sold to "
            f"{self.cur_bid_info['bidder'].name} "  # type: ignore[index]
            f"for {self.cur_bid_info['bid']}",  # type: ignore[index]
        )
