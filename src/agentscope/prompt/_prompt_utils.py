# -*- coding: utf-8 -*-
"""Utility functions for prompt optimization."""
import json
from typing import List

from pathlib import Path
import numpy as np

from scipy.spatial.distance import cdist


def _find_top_k_embeddings(
    query_embedding: List[float],
    list_embeddings: List[List[float]],
    k: int,
) -> List:
    """
    Find the top k embeddings that are closed to the query embedding.

    Args:
        query_embedding (`List[float]`):
            the query to be searched.
        list_embeddings (`List[List[float]]`):
            the list of embeddings to be searched.
        k (`int`):
            the number of embeddings to be returned.
    Returns:
        `List`:
            the list of indices of the top k embeddings.
    """
    # Compute cosine similarity between the query and the list of embeddings.
    # cdist returns the distance of 2-dimension arrays,
    # so we subtract from 1 to get similarity.
    # Cosine distance is defined as 1.0 minus the cosine similarity.

    similarities = (
        1 - cdist([query_embedding], list_embeddings, "cosine").flatten()
    )

    # Get the top k indices sorted by similarity (in descending order).
    return list(np.argsort(similarities)[::-1][:k])


def _read_json_same_dir(file_name: str) -> dict:
    """Read the json file in the same dir"""
    current_file_path = Path(__file__)

    json_file_path = current_file_path.parent / file_name

    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


_examples = _read_json_same_dir("_prompt_examples.json")

_DEFAULT_EXAMPLE_LIST_EN = _examples["en"]

_DEFAULT_EXAMPLE_LIST_ZH = _examples["zh"]
