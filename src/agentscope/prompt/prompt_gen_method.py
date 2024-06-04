# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""Methods for prompt optimization."""
import random
from types import SimpleNamespace
from typing import Union, List, Literal, Dict, Any

import numpy as np
from loguru import logger
from scipy.spatial.distance import cdist

from agentscope.models import load_model_by_config_name
from agentscope.message import Msg

from .prompt_base import (
    OPT_SYSTEM_PROMPT,
    OPT_PROMPT_TEMPLATE,
    PromptGeneratorBase,
    SYS_OPT_EXAMPLES,
)


class DirectPromptGenMethod(PromptGeneratorBase):
    """Directly optimize the user prompt."""

    def __init__(
        self,
        model_config_name: str,
        meta_prompt: str = OPT_SYSTEM_PROMPT,
    ) -> None:
        super().__init__()

        self.model = load_model_by_config_name(model_config_name)
        self.meta_prompt = meta_prompt

    def optimize(self, user_prompt: str) -> str:
        formatted_prompt = self.meta_prompt + OPT_PROMPT_TEMPLATE.format(
            user_prompt=user_prompt,
        )
        prompt = self.model.format(
            Msg(
                "user",
                formatted_prompt,
                role="user",
            ),
        )
        response = self.model(prompt).text
        return response


class SentencePieceEmbeddingModel:
    """The embedding model using sentence piece"""

    def __init__(self) -> None:
        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"

        from sentence_transformers import SentenceTransformer

        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        logger.debug(f"Loaded model: {self.SELECT_MODEL}")

    def __call__(self, queries: Union[str, List[str]]) -> Any:
        logger.debug(f"Embedding queries: {queries}")
        embedding = self.bert_model.encode(queries)
        return SimpleNamespace(**{"embedding": [embedding]})


def get_example_promt(examples: dict) -> str:
    """get prompt with examples"""
    EXAMPLE_PROMPT = """
    以下是一些例子：
    """
    for example in examples:
        EXAMPLE_PROMPT += f"优化前的prompt：{example['human_prompt']}\n"
        EXAMPLE_PROMPT += f"优化后的prompt{example['opt_prompt']}\n"
        EXAMPLE_PROMPT += "\n"
    return EXAMPLE_PROMPT


def find_top_k_embeddings(
    query_embedding: List,
    list_embeddings: List,
    k: int,
) -> List:
    """
    :param query_embedding:
    :param list_embeddings:
    :param k:
    :return: List of List: each element is (index, embedding, score)
    """
    # Compute cosine similarity between the query and the list of embeddings.
    # cdist returns the distance of 2-dimension arrays,
    # so we subtract from 1 to get similarity.
    # Cosine distance is defined as 1.0 minus the cosine similarity.

    similarities = (
        1 - cdist([query_embedding], list_embeddings, "cosine").flatten()
    )

    # Get the top k indices sorted by similarity (in descending order).
    top_k_indices = np.argsort(similarities)[::-1][:k]

    # Get the top k embeddings and their corresponding similarity scores.
    top_k_embeddings = [list_embeddings[i] for i in top_k_indices]
    top_k_scores = [similarities[i] for i in top_k_indices]

    # Return the top k embeddings, similarity scores, and their indices.
    return list(
        zip(
            top_k_indices,
            top_k_embeddings,
            top_k_scores,
        ),
    )


class ExamplePromptGenMethod(PromptGeneratorBase):
    """Optimize the user prompt."""

    def __init__(
        self,
        model_config_name: str = None,
        meta_prompt: Union[str, None] = None,
        example_list: List = None,
        example_selection_method: Literal["random", "similarity"] = "random",
        example_selection_num: int = 3,
        example_embd_path: str = "./.cache/embeddings.npy",
        embed_model_config_name: str = None,
    ) -> None:
        super().__init__()

        if model_config_name is not None:
            self.model = load_model_by_config_name(model_config_name)
        else:
            raise ValueError("model_config_name must be provided.")

        if meta_prompt is not None:
            self.meta_prompt = meta_prompt
        else:
            self.meta_prompt = OPT_SYSTEM_PROMPT
        if example_list is None:
            example_list = SYS_OPT_EXAMPLES
        self.example_list = example_list
        self.example_embd_path = example_embd_path
        self.example_selection_method = example_selection_method
        self.example_selection_num = example_selection_num
        if embed_model_config_name is not None:
            self.embd_model = load_model_by_config_name(
                embed_model_config_name,
            )
        else:
            self.embd_model = self.embd_model = SentencePieceEmbeddingModel()

        if self.example_selection_method == "similarity":
            try:
                self.sample_embeddings = np.load(self.example_embd_path)
            except FileNotFoundError:
                logger.debug(
                    f"Embeddings file path {self.example_embd_path} not found."
                    " Generating embeddings...",
                )
                self.sample_embeddings = self.generate_embeddings()

    def select_example(self, human_query: str) -> dict:
        """Selector the similary examples with human query"""
        logger.debug(f"selecting example for query{human_query}")
        if self.example_selection_method == "random":
            return self.random_selection_method()
        elif self.example_selection_method == "similarity":
            return self.similarity_selection_method(human_query)
        else:
            raise NotImplementedError("Invalid example selection method")

    def similarity_selection_method(self, human_query: str) -> dict:
        """select the examples using embedding similarity"""
        # get the human query embd using the embd model
        human_query_embd = self.embd_model(human_query).embedding[0]

        selection_results = find_top_k_embeddings(
            human_query_embd,
            self.sample_embeddings,
            self.example_selection_num,
        )

        selected_examples = [
            self.example_list[item[0]] for item in selection_results
        ]

        return {
            "ids": [int(item[0]) for item in selection_results],
            "selected_examples": selected_examples,
        }

    def random_selection_method(self) -> Dict[str, List[Any]]:
        """selector the example randomly"""
        example_list = self.example_list
        selected_indices = random.sample(
            range(len(example_list)),
            self.example_selection_num,
        )

        selected_examples = [example_list[index] for index in selected_indices]

        return {
            "ids": selected_indices,
            "selected_examples": selected_examples,
        }

    def generate_embeddings(self) -> List:
        """Generate embeddings for the example samples."""

        sample_embeddings = []
        for sample in self.example_list:
            sample_embeddings.append(
                self.embd_model(sample["human_prompt"]).embedding[0],
            )
        assert len(sample_embeddings) == len(self.example_list)

        print(sample_embeddings)
        np.save(self.example_embd_path, sample_embeddings)
        return sample_embeddings

    def optimize(self, user_prompt: str) -> str:
        examples = self.select_example(user_prompt)["selected_examples"]
        logger.debug(f"    selected examples: {examples}")
        formatted_prompt = (
            self.meta_prompt
            + get_example_promt(examples)
            + OPT_PROMPT_TEMPLATE.format(user_prompt=user_prompt)
        )
        prompt = self.model.format(
            Msg(
                "user",
                formatted_prompt,
                role="user",
            ),
        )
        logger.chat(
            f"Optimizing user prompt, original prompt: \n{user_prompt} \n",
        )
        response = self.model(prompt).text
        logger.chat(f"Optimized prompt: \n {response} \n")

        return response
