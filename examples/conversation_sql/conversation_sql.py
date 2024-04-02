# -*- coding: utf-8 -*-
"""A simple example of agent that can perform
SQL queries through natural language conversation.
"""
from sql_utils import (
    SQLPrompt,
    EuclideanDistanceExampleSelector,
    QuestionSqlExampleStyle,
    execute_query,
)

import agentscope
from agentscope.agents.user_agent import UserAgent

from agentscope.agents.agent import AgentBase
from agentscope.message import Msg


def process_duplication(sql: str) -> str:
    """
    Process sql duplication of results
    """
    sql = sql.strip().split("/*")[0]
    return sql


class SQLAgent(AgentBase):
    """An agent able to preform SQL tasks
    base on natual language instructions."""

    def __init__(
        self,
        name: str,
        db_id: str,
        db_path: str,
        model_config_name: str = "gpt-4",
    ) -> None:
        super().__init__(
            name=name,
            model_config_name=model_config_name,
            use_memory=False,
        )
        self.db_id = db_id
        self.db_path = db_path
        self.sql_prompt = SQLPrompt()
        self.question_selector = EuclideanDistanceExampleSelector()
        self.question_style = QuestionSqlExampleStyle()
        self.SEP_EXAMPLE = "\n\n"
        self.scope_factor = 100
        self.NUM_EXAMPLE = 9
        self.cross_domain = False
        self.max_retries = 3

    def generate_prompt(self, x: dict = None) -> dict:
        """
        Generate prompt given input question
        """
        question = x["content"]
        target = {
            "db_id": self.db_id,
            "path_db": self.db_path,
            "question": question,
        }
        prompt_target = self.sql_prompt.format_target(target)
        if self.NUM_EXAMPLE != 0:
            examples = self.question_selector.get_examples(
                target,
                self.NUM_EXAMPLE * self.scope_factor,
                cross_domain=self.cross_domain,
            )
            prompt_example = []
            question = target["question"]
            example_prefix = self.question_style.get_example_prefix()
            for example in examples:
                if self.cross_domain:
                    assert target["db_id"] != example["db_id"]

                example_format = self.question_style.format_example(example)

                prompt_example.append(example_format)

                if len(prompt_example) >= self.NUM_EXAMPLE:
                    break
            n_valid_example = len(prompt_example)
            if len(prompt_example) > 0:
                prompt = example_prefix + self.SEP_EXAMPLE.join(
                    prompt_example + [prompt_target],
                )
            else:
                prompt = self.SEP_EXAMPLE.join(
                    prompt_example + [prompt_target],
                )
        else:
            n_valid_example = 0
            prompt = prompt_target
        return {
            "prompt": prompt,
            "n_examples": n_valid_example,
            "db_id": target["db_id"],
        }

    def get_response_from_prompt(self, prompt: dict) -> str:
        """
        Generate response from prompt using LLM
        """
        messages = [{"role": "user", "content": prompt}]
        sql = self.model(messages).text
        # remove \n and extra spaces
        sql = " ".join(sql.replace("\n", " ").split())
        sql = process_duplication(sql)
        # python version should >= 3.8
        if sql.startswith("SELECT"):
            response = sql + "\n"
        elif sql.startswith(" "):
            response = "SELECT" + sql + "\n"
        else:
            response = "SELECT " + sql + "\n"
        return response

    def reply(self, x: dict = None) -> dict:
        if x is None:
            return {}

        prepared_prompt = self.generate_prompt(x)

        attempt = 0
        result = None

        while attempt < self.max_retries:
            try:
                response = self.get_response_from_prompt(
                    prepared_prompt["prompt"],
                )
                msg = Msg(self.name, response, role="sql assistant")
                self.speak(msg)
                result = execute_query(response, path_db=self.db_path)
                break
            except Exception:
                print(
                    f"Attempt {attempt+1} of {self.max_retries} "
                    f"failed. Retrying!",
                )
                attempt += 1

        if result is not None:
            print(f"Query result is: {result}")
        else:
            print(
                "Failed to execute query after",
                self.max_retries,
                "attempts",
            )
        return msg


if __name__ == "__main__":
    agentscope.init(
        model_configs="./configs/model_configs.json",
    )
    sql_agent = SQLAgent(
        name="sql agent",
        db_id="concert_singer",
        db_path="./database/concert_singer/concert_singer.sqlite",
        model_config_name="gpt-4",
    )
    user_agent = UserAgent()
    x = None
    while True:
        x = sql_agent(x)
        x = user_agent(x)

        if x.content == "exit":
            print("Exiting the conversation.")
            break
