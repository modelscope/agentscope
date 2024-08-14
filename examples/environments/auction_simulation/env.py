# -*- coding: utf-8 -*-
"""The envs used to simulate an auction."""
from typing import List

from loguru import logger

from agents import Item, Bidder

from agentscope.environment.env import BasicEnv, EventListener
from agentscope.environment.event import Event, event_func


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

    @event_func
    def start(self, item: Item) -> None:
        """Start bidding for an item.
        Args:
            item (`Item`): The item.
        """
        self.cur_item = item
        self.cur_bid_info = None
        self._trigger_listener(
            Event("start", args={"item": item}),
        )

    @event_func
    def bid(self, bidder: Bidder, item: Item, bid: int) -> bool:
        """Bid for the auction.
        Args:
            bidder (`Bidder`): The bidder agent.
            item (`Item`): The item.
            bid (`int`): The bid of the bidder.

        Returns:
            `bool`: Whether the bid was successful.
        """
        if (
            item.is_auctioned
            or bid < item.opening_price
            or (self.cur_bid_info and bid <= self.cur_bid_info["bid"])
        ):
            return False
        self.cur_bid_info = {"bidder": bidder, "bid": bid}
        logger.info(f"{bidder.name} bid {bid} for {item.name}")
        self._trigger_listener(
            Event(
                "bid",
                args={"bidder": bidder, "item": item, "bid": bid},
            ),
        )
        return True

    @event_func
    def fail(self, item: Item) -> None:
        """Pass the auction. (No bid for the item)
        Args:
            item (`Item`): The item.
        """
        item.is_auctioned = True
        logger.info(f"{item.name} is not sold")
        self._trigger_listener(
            Event("failed", args={"item": item}),
        )

    @event_func
    def sold(self, bidder: Bidder, item: Item, price: int) -> None:
        """Sold the item.
        Args:
            bidder (`Bidder`): The bidder agent.
            item (`Item`): The item.
            price (`int`): The final price of the item.
        """
        item.is_auctioned = True
        logger.info(f"{item.name} is sold to {bidder.name} for {price}")
        self._trigger_listener(
            Event(
                "sold",
                args={"bidder": bidder, "item": item, "price": price},
            ),
        )
