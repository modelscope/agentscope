# -*- coding: utf-8 -*-
"""
Utils and helpers for performing sql querys
"""
import sqlite3
import json
from typing import Union
from sqlite3 import Connection
import numpy as np


def execute_query(
    queries: Union[list[str], str],
    path_db: str = None,
    cur: str = None,
) -> Union[list, str]:
    """Execute queries and return results. Reuse cur if it's not None."""
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


def get_table_names(path_db: str = None, cur: str = None) -> list:
    """Get names of all tables within the database,
    and reuse cur if it's not None"""
    table_names = execute_query(
        queries="SELECT name FROM sqlite_master WHERE type='table'",
        path_db=path_db,
        cur=cur,
    )
    table_names = [_[0] for _ in table_names]
    return table_names


def get_sql_for_database(path_db: str = None, cur: str = None) -> list:
    """
    get sql table from database
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

    sqls = execute_query(queries, path_db, cur)

    if close_in_func:
        cur.close()

    return [_[0][0] for _ in sqls]


class SQLPrompt:
    """SQL prompt helper"""

    def __init__(self) -> None:
        self.template_info = "/* Given the following database schema: */\n{}"
        self.template_question = "/* Answer the following: {} */"

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
        self.db_ids = [d["db_id"] for d in self.train_json]
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

    def domain_mask(self, candidates: list, db_id: str) -> list:
        """Get domain mask"""
        cross_domain_candidates = [
            candidates[i]
            for i in range(len(self.db_ids))
            if self.db_ids[i] != db_id
        ]
        return cross_domain_candidates

    def retrieve_index(self, indexes: list, db_id: str) -> list:
        """Retrieve index"""
        cross_domain_indexes = [
            i for i in range(len(self.db_ids)) if self.db_ids[i] != db_id
        ]
        retrieved_indexes = [cross_domain_indexes[i] for i in indexes]
        return retrieved_indexes

    def get_examples(
        self,
        target: dict,
        num_example: int,
        cross_domain: bool = False,
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
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]
