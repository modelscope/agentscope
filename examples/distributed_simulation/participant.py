# -*- coding: utf-8 -*-
"""A general dialog agent."""
import random
import time
import re
from typing import Optional, Union, Sequence
import concurrent.futures

from loguru import logger

from agentscope.message import Msg
from agentscope.agents import AgentBase


class RandomParticipant(AgentBase):
    """A fake participant who generates number randomly."""

    def __init__(
        self,
        name: str,
        max_value: int = 100,
        sleep_time: float = 1.0,
    ) -> None:
        """Initialize the participant."""
        super().__init__(
            name=name,
        )
        self.max_value = max_value
        self.sleep_time = sleep_time

    def generate_random_response(self) -> str:
        """generate a random int"""
        time.sleep(self.sleep_time)
        return str(random.randint(0, self.max_value))

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """Generate a random value"""
        # generate a response in content
        response = self.generate_random_response()
        msg = Msg(self.name, content=response, role="assistant")
        return msg


class LLMParticipant(AgentBase):
    """A participant agent who generates number using LLM."""

    def __init__(
        self,
        name: str,
        model_config_name: str,
        max_value: int = 100,
    ) -> None:
        """Initialize the participant."""
        super().__init__(
            name=name,
            model_config_name=model_config_name,
            use_memory=True,
        )
        self.max_value = max_value
        self.prompt = Msg(
            name="system",
            role="system",
            content="You are participating in a game where everyone "
            f"provides a number between 0 and {max_value}. The person "
            "closest to the average will win.",
        )

    def parse_value(self, txt: str) -> str:
        """Parse the number from the response."""
        numbers = re.findall(r"\d+", txt)
        if len(numbers) == 0:
            logger.warning(
                f"Fail to parse value from [{txt}], use "
                f"{self.max_value // 2} instead.",
            )
            return str(self.max_value // 2)
        else:
            return numbers[-1]

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """Generate a value by LLM"""
        if self.memory:
            self.memory.add(x)

        # prepare prompt
        prompt = self.model.format(self.prompt, self.memory.get_memory())

        # call llm and generate response
        response = self.model(prompt).text

        response = self.parse_value(response)

        msg = Msg(self.name, response, role="assistant")

        # Record the message in memory
        if self.memory:
            self.memory.add(msg)

        return msg


class Moderator(AgentBase):
    """A Moderator to collect values from participants."""

    def __init__(
        self,
        name: str,
        part_configs: list[dict],
        agent_type: str = "random",
        max_value: int = 100,
        sleep_time: float = 1.0,
    ) -> None:
        super().__init__(name)
        self.max_value = max_value
        def create_llm_participant(config):
            return LLMParticipant(
                    name=config["name"],
                    model_config_name=config["model_config_name"],
                    max_value=max_value,
                ).to_dist(
                    host=config["host"],
                    port=config["port"],
                )

        def create_random_participant(config):
            return RandomParticipant(
                name=config["name"],
                max_value=max_value,
                sleep_time=sleep_time,
            ).to_dist(
                host=config["host"],
                port=config["port"],
            )
        create_participant = {"random": create_random_participant, "llm": create_llm_participant}[agent_type]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(create_participant, config) for config in part_configs}

            self.participants = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                self.participants.append(result)

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        msg = Msg(
            name="moderator",
            role="user",
            content=f"Now give a number between 0 and {self.max_value}.",
        )
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(lambda p: p(msg), p) for p in self.participants}
            futures_2 = {executor.submit(lambda r: int(r.content), future.result()) for future in concurrent.futures.as_completed(futures)}
            summ = sum(future.result() for future in concurrent.futures.as_completed(futures_2))
        return Msg(
            name=self.name,
            role="assistant",
            content={"sum": summ, "cnt": len(self.participants)},
        )
