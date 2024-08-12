# -*- coding: utf-8 -*-
"""
Utils and helpers for performing sql queries.
Referenced from https://github.com/BeachWang/DAIL-SQL.
"""
import sqlite3
import json
from typing import Union
from sqlite3 import Connection
import os
import numpy as np


def query_sqlite(
    queries: Union[list[str], str],
    path_db: str = None,
    cur: str = None,
) -> Union[list, str]:
    """Execute queries and return results."""
    assert not (
        path_db is None and cur is None
    ), "path_db and cur cannot be NoneType at the same time"
    con: Connection
    close_in_func = False
    if cur is None:
        con = sqlite3.connect(path_db)
        cur = con.cursor()
        close_in_func = True

    if isinstance(queries, str):
        results = cur.execute(queries).fetchall()
    elif isinstance(queries, list):
        results = []
        for query in queries:
            res = cur.execute(query).fetchall()
            results.append(res)
    else:
        raise TypeError(f"queries cannot be {type(queries)}")

    # close the connection if needed
    if close_in_func:
        con.close()

    return results


def create_sqlite_db_from_schema(schema_path: str, db_path: str) -> None:
    """Create a SQLite database file from a schema SQL file.

    Args:
        schema_path: The file path to the schema SQL file.
        db_path: The file path for the SQLite database to be created.
    """
    if os.path.exists(db_path):
        print(
            f"Database file '{db_path}' already exists. ",
        )
        return
    conn = sqlite3.connect(db_path)

    with open(schema_path, "r", encoding="utf-8") as schema_file:
        schema_sql = schema_file.read()

    cursor = conn.cursor()
    cursor.executescript(schema_sql)

    conn.commit()
    conn.close()


def get_table_names(path_db: str = None, cur: str = None) -> list:
    """Get names of all tables within the database,
    and reuse cur if it's not None"""
    table_names = query_sqlite(
        queries="SELECT name FROM sqlite_master WHERE type='table'",
        path_db=path_db,
        cur=cur,
    )
    table_names = [_[0] for _ in table_names]
    return table_names


def get_sql_for_database(path_db: str = None, cur: str = None) -> list:
    """
    Get sql table from database
    """
    close_in_func = False
    if cur is None:
        con = sqlite3.connect(path_db)
        cur = con.cursor()
        close_in_func = True

    table_names = get_table_names(path_db, cur)

    queries = [
        f"SELECT sql FROM sqlite_master WHERE tbl_name='{name}'"
        for name in table_names
    ]

    sqls = query_sqlite(queries, path_db, cur)

    if close_in_func:
        cur.close()

    return [_[0][0] for _ in sqls]


class SQLPrompt:
    """SQL prompt helper"""

    def __init__(self) -> None:
        self.template_info = "/* Given the following database schema: */\n{}"
        self.template_question = "/* Answer the following: {} */"
        self.template_agent_prompt = (
            "You are a helpful agent that preform"
            "SQL querys base on natual language instructions."
            "Please describe the database schema provided"
            "in a simple and understandable manner. "
        )
        self.is_sql_prompt = (
            "Please read the user's question below and "
            "determine whether the question is an appropriate "
            "query for the given SQL schema. \n"
            "If the question is indeed a query pertaining to the SQL schema, "
            'respond with "YES". '
            "If the question is not a query related to the SQL schema, "
            "provide a brief explanation to the user explaining why their "
            "question does not correspond to a SQL query within the "
            "context of the schema. "
            "The user's question is: "
        )

    def format_target(self, example: dict) -> str:
        """Format sql prompt"""
        return self.format_question(example) + "\nSELECT "

    def format_question(self, example: dict) -> str:
        """Format question"""
        sqls = get_sql_for_database(example["path_db"])
        prompt_info = self.template_info.format("\n\n".join(sqls))
        prompt_question = self.template_question.format(example["question"])
        prompt_components = [prompt_info, prompt_question]
        prompt = "\n\n".join(prompt_components)
        return prompt

    def describe_schema(self, db_path: str) -> str:
        """Describe SQL schema"""
        sqls = get_sql_for_database(db_path)
        prompt_info = self.template_info.format("\n\n".join(sqls))
        prompt_components = [
            self.template_agent_prompt,
            "DB schema info: ",
            prompt_info,
        ]
        prompt = "\n\n".join(prompt_components)
        return prompt

    def is_sql_question(self, example: dict) -> str:
        """whether the input is a sql question or not"""
        sqls = get_sql_for_database(example["path_db"])
        prompt_info = self.template_info.format("\n\n".join(sqls))
        prompt_components = [
            prompt_info,
            self.is_sql_prompt,
            example["question"],
        ]
        prompt = "\n".join(prompt_components)
        return prompt


class QuestionSqlExampleStyle:
    """Provide QA pair as examples"""

    def get_example_prefix(self) -> str:
        """get example prefix"""
        return (
            "/* Some SQL examples are provided based on similar problems: */\n"
        )

    def format_example(self, example: dict) -> str:
        """format example"""
        template_qa = "/* Answer the following: {} */\n{}"
        return template_qa.format(example["question"], example["query"])


class EuclideanDistanceExampleSelector:
    """Select similar sample question"""

    def __init__(self) -> None:
        self.train_json_path = "./database/train.json"
        with open(self.train_json_path, "r", encoding="utf-8") as file:
            self.train_json = json.load(file)
        self.train_questions = [_["question"] for _ in self.train_json]

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"

        from sentence_transformers import SentenceTransformer

        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        try:
            self.train_embeddings = np.load("./.cache/train_embeddings.npy")
        except FileNotFoundError:
            self.train_embeddings = self.bert_model.encode(
                self.train_questions,
            )
            np.save("./.cache/train_embeddings.npy", self.train_embeddings)

    def get_examples(
        self,
        target: dict,
        num_example: int,
    ) -> list:
        """Get similar question examples for few shot"""
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings),
        ).tolist()
        pairs = list(zip(distances, range(len(distances))))
        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = []
        for d, index in pairs_sorted:
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]


class DailSQLPromptGenerator:
    """Generate prompt given the dataset and question"""

    def __init__(
        self,
        db_path: str,
    ) -> None:
        self.db_path = db_path
        self.sql_prompt = SQLPrompt()
        self.question_selector = EuclideanDistanceExampleSelector()
        self.question_style = QuestionSqlExampleStyle()
        self.SEP_EXAMPLE = "\n\n"
        self.scope_factor = 100
        self.NUM_EXAMPLE = 9
        self.cross_domain = False

    def describe_schema(self) -> str:
        """Describe the sql"""
        return self.sql_prompt.describe_schema(self.db_path)

    def is_sql_question_prompt(self, question: str) -> str:
        """
        prompt for LLM to judge whether the question is appropriate
        """
        target = {
            "path_db": self.db_path,
            "question": question,
        }
        return self.sql_prompt.is_sql_question(target)

    def generate_prompt(self, question: str) -> dict:
        """
        Generate prompt given input question
        """
        target = {
            "path_db": self.db_path,
            "question": question,
        }
        prompt_target = self.sql_prompt.format_target(target)
        if self.NUM_EXAMPLE != 0:
            examples = self.question_selector.get_examples(
                target,
                self.NUM_EXAMPLE * self.scope_factor,
            )
            prompt_example = []
            example_prefix = self.question_style.get_example_prefix()
            for example in examples:
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
        }
