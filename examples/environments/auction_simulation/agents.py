# -*- coding: utf-8 -*-
"""The agents used to simulate an auction."""
import random
import re
import threading
import time
from typing import Optional, Sequence, Union

from env import Auction, Item

from loguru import logger
from agentscope.agents import AgentBase
from agentscope.message import Msg


class Auctioneer(AgentBase):
    """The auctioneer agent."""

    def __init__(
        self,
        name: str,
        auction: Auction,
        waiting_time: float = 3.0,
    ) -> None:
        """Initialize the auctioneer agent.
        Args:
            name: The name of the auctioneer.
            auction: The auction.
            waiting_time: The waiting time for the auctioneer
                          to decide the winner.
        """
        super().__init__(name=name)
        self.auction = auction
        self.wating_time = waiting_time
        self.timer = None

    def start_timer(self) -> None:
        """Start the timer for the auctioneer to decide the winner."""
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(self.wating_time, self.decide_winner)
        self.timer.start()

    def decide_winner(self) -> None:
        """Decide the winner of the auction."""
        if self.auction.get_bid_info() is None:
            self.auction.fail()
        else:
            self.auction.sold()


class RandomBidder(AgentBase):
    """A fake bidder agent who bids randomly."""

    def __init__(
        self,
        name: str,
        money: int = 100,
        not_bid_ratio: float = 0.5,
        sleep_time: float = 1.0,
    ) -> None:
        """Initialize the bidder agent."""
        super().__init__(name=name)
        self.money = money
        self.not_bid_ratio = not_bid_ratio
        self.sleep_time = sleep_time

    def generate_random_response(self, start: int = 0) -> Optional[int]:
        """Generate a random bid or not to bid."""
        time.sleep(random.random() * self.sleep_time)
        if random.random() < self.not_bid_ratio:
            return None
        return random.randint(start, self.money)

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """Generate a random value"""
        item = Item.from_dict(x.content["item"])
        # generate a random bid or not to bid
        response = self.generate_random_response(item.opening_price)
        msg = Msg(self.name, content=response, role="assistant")
        return msg


class Bidder(AgentBase):
    """The bidder agent."""

    def __init__(
        self,
        name: str,
        model_config_name: str,
        money: int = 100,
    ) -> None:
        """Initialize the bidder agent."""
        super().__init__(
            name=name,
            model_config_name=model_config_name,
            use_memory=True,
        )
        self.money = money
        self.prompt = Msg(
            name="system",
            role="system",
            content="You are a bidder. You will be given an item. "
            f"You have {self.money} money. "
            "Please consider whether to bid for the item. "
            "If you want to bid, please provide the bid value "
            "(an integer between 1 and your money). "
            "If you don't want to bid, please provide 0.",
        )

    def parse_value(self, txt: str) -> Optional[int]:
        """Parse the bid from the response."""
        numbers = re.findall(r"\d+", txt)
        if len(numbers) == 0:
            logger.warning(
                f"Fail to parse value from [{txt}], use not bidding instead.",
            )
            return None
        elif int(numbers[-1]) > self.money:
            logger.warning(
                f"Try to bid more than {self.money}, "
                f"use {self.money} instead.",
            )
            return self.money
        else:
            return int(numbers[-1]) if numbers[-1] != "0" else None

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """Generate a value by LLM"""

        if self.memory:
            self.memory.add(x)

        item = Item.from_dict(x.content["item"])
        bidder_name = x.content.get("bidder_name", None)
        prev_bid = x.content.get("bid", None)
        content = (
            f"The item is {item.name} and "
            f"the opening price is {item.opening_price}."
        )
        if bidder_name and prev_bid:
            content += f" Now {bidder_name} bid {prev_bid} for the item."
        bid_info = Msg("assistant", content=content, role="assistant")

        # prepare prompt
        prompt = self.model.format(
            self.prompt,
            self.memory.get_memory(),
            bid_info,
        )

        # call llm and generate response
        response = self.model(prompt).text
        bid = self.parse_value(response)
        msg = Msg(self.name, bid, role="assistant")

        # Record the message in memory
        if self.memory:
            self.memory.add(msg)

        return msg
