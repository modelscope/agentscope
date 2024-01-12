# -*- coding: utf-8 -*-
""" LearnableAgent agent class for Agent """
from abc import ABC
from typing import Optional, Union, Any, Callable, Type
from loguru import logger

from agentscope.message import Msg
from agentscope.memory import MemoryBase, TemporaryMemory
from agentscope.agents.agent import AgentBase
from agentscope.service.retrieval.similarity import cos_sim


VALUE_ASSESSMENT_PROMPT = (
    "Please carefully consider the following record and assess whether it "
    "contains information of sufficient value to be suitable for storage in "
    "a knowledge base. "
    "\nExample:\n"
    "'The dragon is the only creature in the Chinese Zodiac that is "
    "considered a divine animal.' → Answer 'yes' (because this is basic "
    "knowledge about Chinese culture with widespread reference value for "
    "understanding related topics)\n"
    "Following these guidelines, please respond with 'yes' or 'no' to the "
    "following record:\n\n"
    "{record}"
)

EXTRACTION_SUMMARY_PROMPT = (
    "Please read the following record, extract key knowledge points or "
    "question-answer pairs, and provide a concise and clear summary. "
    "\nExample:\n"
    "Record: 'Due to the rotation of the Earth, we experience the "
    "alternation of day and night. "
    "The Earth completes one rotation every 24 hours.'\n"
    "Summary: 'The Earth rotates once every 24 hours, which leads to the "
    "phenomenon of day and night alternation.'\n\n"
    "{record}"
)


class LearnableAgent(AgentBase, ABC):
    """Class for LearnableAgent"""

    def __init__(
        self,
        name: str,
        vdb_path: str,
        vdb_cls: Type[MemoryBase] = TemporaryMemory,
        config: Optional[dict] = None,
        sys_prompt: Optional[str] = None,
        model: Optional[Union[Callable[..., Any], str]] = None,
        embedding_model: Union[str, Callable] = None,
        metric: Callable = cos_sim,
        assess_prompt: str = VALUE_ASSESSMENT_PROMPT,
        extract_prompt: str = EXTRACTION_SUMMARY_PROMPT,
    ) -> None:
        super().__init__(name, config, sys_prompt, model)
        # Notice: [Memory] is for short-term, current conversation, and will
        # not persist after the agent is closed.
        # [Vector database] is considered long-term, will be reloaded whenever
        # agent is invoked
        # Build vector database for saving knowledge
        self.vdb = vdb_cls(
            config,
            embedding_model=embedding_model,
            vdb_path=vdb_path,
        )
        self.metric = lambda x, y: metric(x, y).content
        self.assess_prompt = assess_prompt
        self.extract_prompt = extract_prompt

    def reply(self, x: dict = None) -> dict:
        """Forward method for agent"""
        # defer the forward function implementation to example agents
        raise NotImplementedError

    def learn_from_chat(self) -> None:
        """
        Iterates through the messages in the learner's memory and processes
        each message to potentially learn from it. Messages originating
        from the learner itself are ignored. The memory is reset after
        processing.

        This function calls the `archive_valuable_msg` method on each message
        to decide whether to store the message information into the
        knowledge base.
        """
        if self.memory.size() > 0:
            for msg in self.memory:
                # Ignore msg from itselves to avoid duplication
                if msg.get("name") != self.name:
                    self.archive_valuable_msg(msg)
        self.memory.reset()

    def archive_valuable_msg(self, msg: dict) -> None:
        """
        Evaluates a single message to determine whether it should be stored
        in the knowledge base. The method generates prompts to assess the
        value of the message and to extract a summary if the message is
        deemed valuable.

        Args:
            msg (dict): A dictionary representing the message to be
                considered for storage. The dictionary typically contains
                keys such as 'name' and 'content'.
        """
        # Consider whether to deposit message into the knowledge base
        prompt = self.assess_prompt.format_map(
            {
                "record": msg.content,
            },
        )
        res = self.model([Msg(self.name, prompt)])

        logger.info(
            f"{self.name}:\n {msg.content} \n " f"accessing results: {res}.",
        )

        if "yes" in res.lower():
            prompt = self.extract_prompt.format_map(
                {
                    "record": msg.content,
                },
            )
            res = self.model([Msg(self.name, prompt)])
            emb = self._openai_embedding(res)
            self.vdb.add(Msg(self.name, res, embedding=emb), embed=False)
            logger.info(f"Saving {res} in {self.name}'s vdb.")

    def close(self) -> None:
        """
        Saves the current state of the vecter database (vdb) to a memory file.
        This method should be called before the termination of the program
        to ensure that learned information is not lost.
        """
        self.vdb.export()
