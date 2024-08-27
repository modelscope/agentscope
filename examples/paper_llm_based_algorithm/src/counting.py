# -*- coding: utf-8 -*-
"""Functions and classes for the counting task"""
import time
import string
import re
from typing import Any
import random
import numpy as np

from src.alg_agents import ProblemSolver
from src.utils import calculate_latency_parallel


def generate_request_counting(config: dict) -> tuple:
    """Generate a request of counting"""
    n = config["n"]
    n_max = config["n_max"]

    prob_digit = np.random.rand() * 0.4 + 0.3  # Unif[0.3, 0.7]
    mask_digit = np.random.rand(n_max) <= prob_digit
    lst_rs = np.random.choice(
        list(string.ascii_lowercase + string.ascii_uppercase),
        n_max,
    )
    lst_digit = np.random.choice(list(string.digits), n_max)
    lst_rs[mask_digit] = lst_digit[mask_digit]

    lst_rs = lst_rs[:n]

    request_string = "".join(lst_rs)
    true_count = sum(1 for c in request_string if c.isdigit())

    return request_string, true_count


class CountingSolver(ProblemSolver):
    """Solver class for the counting task"""

    def __init__(self, config: dict) -> None:
        super().__init__(config=config)

    def solve_directly(
        self,
        request_string: str,
        request_agent: Any,
        dialog_agent: Any,
    ) -> int:
        """Solve directly"""

        nsamples = self.config["nsamples"]

        # Format prompt with request_agent
        content = self.prompt_counting(request_string)
        x_request = request_agent(x=None, content=content)

        # Ask dialog_agent to solve it and parse output (for multiple times)
        candidate_solutions = [0 for _ in range(nsamples)]
        for i in range(nsamples):
            x = self.invoke_llm_call(x_request, dialog_agent)
            candidate_solutions[i] = self.parse_llm_response_counting(
                x.content,
            )  # int

        solution = max(
            set(candidate_solutions),
            key=candidate_solutions.count,
        )  # majority vote
        return solution

    def solve_decomposition(self, request_string: str) -> dict:
        """Solve by parallel decomposition"""

        m = int(self.config["m"])
        self.reset_cost_metrics()

        # Main algorithm: parallel decomposition
        if m <= 0 or m > len(request_string):
            m = len(request_string)
        k = len(request_string) // m
        if k * m < len(request_string):
            k += 1
        sub_strings = [
            request_string[i * m : min((i + 1) * m, len(request_string))]
            for i in range(k)
        ]

        request_agent = self.spawn_request_agent()
        dialog_agent = self.spawn_dialog_agent()
        sub_solutions = [0 for _ in range(k)]
        sub_latencies = [0.0 for _ in range(k)]
        for i in range(k):
            time_start = time.time()
            sub_solutions[i] = self.solve_directly(
                sub_strings[i],
                request_agent,
                dialog_agent,
            )
            sub_latencies[i] = time.time() - time_start

        solution = sum(sub_solutions)
        result = {
            "solution": solution,
            "sub_latencies": sub_latencies,
        }
        return result

    def parse_llm_response_counting(self, llm_response: str) -> int:
        """Parser"""

        found_digits = re.findall(r"\d+", llm_response)
        if len(found_digits) >= 2:
            print(
                "WARNING: found more than one digit sequences "
                "in LLM's response.",
            )
        if len(found_digits) == 0:
            print("WARNING: no digit sequence found in LLM's response.")
            found_digits = ["0"]
        return int(found_digits[-1])

    def prompt_counting(self, request_string: str) -> str:
        """Prompter"""

        prompt = (
            "User input: Count the number of digits "
            "in the following string:\n\n"
        )
        prompt += request_string
        prompt += (
            "\n\nAnswer in the following format: "
            "'There are {answer} digits in the given string.' "
        )
        prompt += "Do NOT output anything else.\n"
        return prompt


def trial_counting(config: dict, seed: Any = None) -> dict:
    """One trial for one config."""

    # Generate random request (with controlled seed)
    random.seed(seed)
    np.random.seed(seed)
    request_string, true_count = generate_request_counting(config)
    random.seed(None)
    np.random.seed(None)

    print("\n/// Counting request:///")
    print(request_string)
    print("//////\n")

    # Solve the counting problem and measure metrics
    time_start = time.time()
    solver = CountingSolver(config=config)
    solver.reset_cost_metrics()
    result = solver.solve_decomposition(request_string)
    latency = time.time() - time_start

    solution = result["solution"]
    error_count = np.abs(solution - true_count)
    error_count_normalized = error_count / len(request_string)

    sub_latencies = result["sub_latencies"]
    latency_ideal_parallel = max(sub_latencies)
    latency_finite_parallel = calculate_latency_parallel(
        sub_latencies,
        config["sim_parallel_degree"],
    )

    trial_result = {
        "solution": solution,
        "true_solution": int(true_count),
        "error_count": int(error_count),
        "error_count_normalized": float(error_count_normalized),
        "latency": float(latency),
        "latency_ideal_parallel": float(latency_ideal_parallel),
        "latency_finite_parallel": float(latency_finite_parallel),
    }
    trial_result.update(solver.cost_metrics)
    return trial_result
