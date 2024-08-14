# -*- coding: utf-8 -*-
"""Listerners for the auction simulation."""
from agents import Auctioneer, Bidder
from env import Auction

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
            bid = self.bidder(
                Msg("auctioneer", content=item, role="assistant"),
            ).content
            if bid:
                env.bid(self.bidder, item, bid)


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
        bidder = event.args["bidder"]
        item = event.args["item"]
        prev_bid = event.args["bid"]
        if bidder == self.bidder:
            return

        if not item.is_auctioned:
            bid = self.bidder(
                Msg(
                    "auctioneer",
                    content=item,
                    bidder=bidder,
                    bid=prev_bid,
                    role="assistant",
                ),
            ).content
            if bid:
                env.bid(self.bidder, item, bid)


class BidTimerListener(EventListener):
    """
    A listener of bidding of an item for the auctioneer
    to start the timer.
    """

    def __init__(self, name: str, auctioneer: Auctioneer) -> None:
        """Initialize the listener.
        Args:
            name (`str`): The name of the listener.
            auctioneer (`Auctioneer`): The auctioneer.
        """
        super().__init__(name=name)
        self.auctioneer = auctioneer

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
        self.auctioneer.start_timer()
