# -*- coding: utf-8 -*-
"""
Similarity functions for retrieval
"""
try:
    import numpy as np
except ImportError:
    np = None

from agentscope.service.service_status import ServiceExecStatus
from agentscope.service.service_response import ServiceResponse
from agentscope.constants import Embedding


def cos_sim(
    a: Embedding,
    b: Embedding,
) -> ServiceResponse:
    """Compute the cosine similarity between two different embeddings

    Args:
        a (`Embedding`):
            Embedding
        b (`Embedding`):
            Embedding

    Returns:
        `ServiceResponse`: A float.
    """
    if not len(a) == len(b):
        return ServiceResponse(
            ServiceExecStatus.ERROR,
            "embedding length not equal",
        )
    a, b = np.array(a), np.array(b)
    return ServiceResponse(
        ServiceExecStatus.SUCCESS,
        np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)),
    )
