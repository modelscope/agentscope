# -*- coding: utf-8 -*-
"""Listeners for the auction simulation."""
from agents import Bidder
from env import Auction

from loguru import logger
from agentscope.environment import Event, EventListener
from agentscope.message import Msg


class StartListener(EventListener):
    """A listener for starting bidding of an item."""

    def __init__(self, name: str, bidder: Bidder) -> None:
        """Initialize the listener.
        Args:
            name (`str`): The name of the listener.
            bidder (`Bidder`): The bidder.
        """
        super().__init__(name=name)
        self.bidder = bidder

    def __call__(
        self,
        env: Auction,
        event: Event,
    ) -> None:
        """Activate the listener.
        Args:
            env (`Auction`): The auction env.
            event (`Event`): The starting event.
        """
        item = event.args["item"]
        if not item.is_auctioned:
            logger.chat(
                Msg(
                    name="Listener",
                    role="system",
                    content=f"Notifying the bidder {self.bidder.name}...",
                ),
            )
            bid = self.bidder(
                Msg(
                    "auctioneer",
                    content={"item": item.to_dict()},
                    role="assistant",
                ),
            ).content
            if bid:
                env.bid(self.bidder.name, item, bid)


class BidListener(EventListener):
    """
    A listener of bidding of an item for other bidders
    to consider whether to bid.
    """

    def __init__(self, name: str, bidder: Bidder) -> None:
        """Initialize the listener.
        Args:
            name (`str`): The name of the listener.
            bidder (`Bidder`): The bidder.
        """
        super().__init__(name=name)
        self.bidder = bidder

    def __call__(
        self,
        env: Auction,
        event: Event,
    ) -> None:
        """Activate the listener.
        Args:
            env (`Auction`): The auction env.
            event (`Event`): The bidding event.
        """
        # skip failed biddings
        if not event.returns:
            return

        bidder = event.args["bidder_name"]
        item = event.args["item"]
        prev_bid = event.args["bid"]

        # skip the bidder itself to avoid infinite loop
        name = self.bidder.name
        if bidder == name:
            return

        if not item.is_auctioned:
            msg_content = {
                "item": item.to_dict(),
                "bidder_name": bidder,
                "bid": prev_bid,
            }
            logger.chat(
                Msg(
                    name="Listener",
                    role="system",
                    content=(
                        f"Bidder {bidder} bids {prev_bid} for {item.name}."
                        f" Notifying Bidder {name}"
                    ),
                ),
            )
            bid = self.bidder(
                Msg(
                    "auctioneer",
                    content=msg_content,
                    role="assistant",
                ),
            ).content
            if bid:
                env.bid(self.bidder.name, item, bid)
