# -*- coding: utf-8 -*-
"""A simple example of agent that can perform
SQL queries through natural language conversation.
"""
from sql_utils import (
    DailSQLPromptGenerator,
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
        db_id: str = None,
        db_path: str = None,
        model_config_name: str = "gpt-4",
    ) -> None:
        super().__init__(
            name=name,
            model_config_name=model_config_name,
            use_memory=False,
        )
        self.db_id = db_id
        self.db_path = db_path
        self.max_retries = 3
        self.prompt_helper = DailSQLPromptGenerator(self.db_id, self.db_path)
        self.self_intro = f"""Hi, I am an agent able to preform SQL querys
        base on natual language instructions.
        Below is a description of the database {self.db_id} provided."""
        self.start_intro = (
            f"Is there any you want to ask about the database {self.db_id}?"
        )

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

    def answer_question_given_execution_result(
        self,
        question: str,
        response_text: str,
    ) -> str:
        """Answer the user question in natural language"""
        prompt = f"""Given the sql query and and the result,
        answer the user's question.
        \n User question: {question} \n {response_text}"""
        messages = [{"role": "user", "content": prompt}]
        answer = self.model(messages).text
        return answer

    def reply(self, x: dict = None) -> dict:
        # this means that here is the first call
        # and we should describe the database for user
        if x is None:
            describe_prompt = self.prompt_helper.describe_sql()
            messages = [{"role": "user", "content": describe_prompt}]
            response = [
                self.self_intro,
                self.model(messages).text,
                self.start_intro,
            ]
            response = "\n\n".join(response)
            msg = Msg(self.name, response, role="sql assistant")
            self.speak(msg)
            return msg

        is_sql_prompt = self.prompt_helper.is_sql_question_prompt(x["content"])
        messages = [{"role": "user", "content": is_sql_prompt}]
        is_sql_response = self.model(messages).text
        if is_sql_response.lower() != "yes":
            response_text = is_sql_response
            result = response_text
            msg = Msg(self.name, result, role="sql assistant")
            self.speak(msg)
            return msg

        prepared_prompt = self.prompt_helper.generate_prompt(x)

        attempt = 0
        result = None

        while attempt < self.max_retries:
            try:
                sql_response = self.get_response_from_prompt(
                    prepared_prompt["prompt"],
                )
                # msg = Msg(self.name, response, role="sql assistant")
                # self.speak(msg)
                exec_result = execute_query(sql_response, path_db=self.db_path)
                response_text = f"""Generated SQL query is: {sql_response} \n
                The execution result is: {exec_result}"""
                response_text += (
                    "\n\n"
                    + self.answer_question_given_execution_result(
                        x["content"],
                        response_text,
                    )
                )
                result = response_text
                msg = Msg(self.name, result, role="sql assistant")
                self.speak(msg)
                break
            except Exception:
                print(
                    f"We fail to execute the generated query."
                    f"Attempt {attempt+1} of {self.max_retries} "
                    f"failed. Retrying!",
                )
                attempt += 1

        if result is None:
            print(
                "Sorry, the agent failed to execute query after",
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
    mss = None
    while True:
        mss = sql_agent(mss)
        mss = user_agent(mss)

        if mss.content == "exit":
            print("Exiting the conversation.")
            break
