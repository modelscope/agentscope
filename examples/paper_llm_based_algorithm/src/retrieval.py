# -*- coding: utf-8 -*-
"""Functions and classes for the retrieval task"""
import time
import random
import re
from typing import Union, Any
import numpy as np

from src.alg_agents import ProblemSolver
from src.utils import calculate_latency_parallel


def generate_request_needle_in_needles(
    config: dict,
    no_needle: bool = False,
) -> tuple:
    """Generate a request of retrieval"""

    n = config["n"]

    # dict of passcodes for all colored objects
    colors = ["red", "green", "blue", "purple", "black", "white"]
    objects = ["door", "lock", "safe", "laptop"]
    dict_passcodes = {}
    for color in colors:
        for obj in objects:
            color_object = color + " " + obj
            random_passcode = "".join(
                [random.choice("0123456789") for _ in range(6)],
            )
            dict_passcodes[color_object] = random_passcode

    # generate main text and key message, combine into request_string
    target_object = random.choice(list(dict_passcodes.keys()))
    question = f"What is the 6-digit passcode to the {target_object}?"

    if no_needle:
        true_solution = "null"
        target_sentence = ""
    else:
        true_solution = dict_passcodes[target_object]
        target_sentence = (
            f"The passcode to the {target_object} is {true_solution}. "
        )

    noise_objects = [obj for obj in dict_passcodes if obj != target_object]

    length_total = len(target_sentence)
    sentences = []
    fraction_split = (
        np.random.rand() * 0.5 + 0.05
    )  # [0.05, 0.55], for difficulty
    while length_total < n:
        obj = random.choice(noise_objects)
        s = f"The passcode to the {obj} is {dict_passcodes[obj]}. "
        length_total += len(s)
        if length_total >= n:
            break  # keep total length equal to or below n
        sentences.append(s)
    idx_split = int(np.floor(fraction_split * len(sentences)))
    sentences = (
        sentences[:idx_split] + [target_sentence] + sentences[idx_split:]
    )
    request_string = "".join(sentences)

    return request_string, question, true_solution


class RetrievalSolver(ProblemSolver):
    """Solver class for retrieval"""

    def __init__(self, config: dict) -> None:
        super().__init__(config=config)

    def solve_directly(
        self,
        request_string: str,
        question: str,
        request_agent: Any,
        dialog_agent: Any,
    ) -> Union[str, None]:
        """Solve directly"""

        content = self.prompt_retrieval(request_string, question)
        x_request = request_agent(x=None, content=content)
        x = self.invoke_llm_call(x_request, dialog_agent)
        solution = self.parse_llm_response_retrieval(x.content)
        return solution

    def solve_decomposition(self, request_string: str, question: str) -> dict:
        """Solve by parallel decomposition"""
        m = self.config["m"]
        self.reset_cost_metrics()

        step_size = np.ceil(0.5 * m)
        n = len(request_string)

        if (m > n) or (m <= 0):
            m = n
            print("WARNING: reset m = n.")

        # Divide into sub-tasks
        sub_requests = []
        idx0, idx1 = 0, m
        while idx1 <= n:
            sub_requests.append(request_string[round(idx0) : round(idx1)])
            if idx1 == n:
                break
            idx0 = idx0 + step_size
            idx1 = min(idx1 + step_size, n)

        print("/// request_string: ///")
        print(request_string)
        print("\n" + "=" * 20)

        # Solve each sub-task
        request_agent = self.spawn_request_agent()
        dialog_agent = self.spawn_dialog_agent()
        sub_solutions = ["" for _ in range(len(sub_requests))]
        sub_latencies = [0.0 for _ in range(len(sub_requests))]
        for i, sr in enumerate(sub_requests):
            time_start = time.time()

            sub_solutions[i] = self.solve_directly(
                sr,
                question,
                request_agent,
                dialog_agent,
            )
            # HOTFIX for ollama: add latency between LLM calls,
            # to mitigate memory issue
            if self.config["llm_model"] == "ollama_llama3_8b":
                print("(Pause for 3 seconds between LLM calls...)")
                time.sleep(3)

            sub_latencies[i] = time.time() - time_start

        print("\n/// sub_solutions: ///")
        print(sub_solutions)
        print("\n" + "=" * 20)

        # Aggregate results for the final solution
        candidate_solutions = [ss for ss in sub_solutions if ss is not None]
        random.shuffle(
            candidate_solutions,
        )  # for random selection if multiple max-frequency candidates
        if len(candidate_solutions) == 0:
            solution = ["null"]
        else:
            items = list(set(candidate_solutions))
            dict_item_count = {
                item: candidate_solutions.count(item) for item in items
            }
            counts = list(dict_item_count.values())
            solution = [
                key
                for key in dict_item_count.keys()
                if dict_item_count[key] == max(counts)
            ]

        result = {
            "solution": solution,  # List of length >= 1
            "sub_latencies": sub_latencies,
        }
        return result

    def prompt_retrieval(self, request_string: str, question: str) -> str:
        """Prompter"""

        PROMPT_PRE = "User input: Please read the following text:\n\n"
        PROMPT_POST = (
            f"\n\nQuestion: {question}\n\n"
            + "If the answer can be inferred from the given text, "
            + "please answer in the following format: "
            + "'The answer is {answer}'. "
            + "Otherwise, you should be faithful and answer 'I don't know'. "
            + "Keep your answer concise, and do NOT output anything else.\n"
        )
        prompt = PROMPT_PRE + "..." + request_string + "..." + PROMPT_POST
        return prompt

    def parse_llm_response_retrieval(
        self,
        llm_response: str,
    ) -> Union[str, None]:
        """Parser"""

        found_digits = re.findall(r"\d+", llm_response)
        if len(found_digits) >= 2:
            print(
                "WARNING: found more than one digit sequences "
                "in LLM's response.",
            )
        if len(found_digits) == 0:
            print("No digit sequence found in LLM's response.")
            found_digits = [None]
        return found_digits[-1]


def trial_retrieval(
    config: dict,
    seed: Any = None,
    no_needle: bool = False,
) -> dict:
    """One trial for one config"""

    # Generate random request (with controlled seed)
    random.seed(seed)
    np.random.seed(seed)
    (
        request_string,
        question,
        true_solution,
    ) = generate_request_needle_in_needles(config, no_needle)
    random.seed(None)
    np.random.seed(None)

    # Solve the problem and measure metrics
    time_start = time.time()
    solver = RetrievalSolver(config=config)
    solver.reset_cost_metrics()
    result = solver.solve_decomposition(request_string, question)
    latency = time.time() - time_start

    print("\n" + "=" * 60)
    print("\n///result of overall algorithm: ///")
    print(result)
    print("\n" + "=" * 60)

    solution = result["solution"]  # List of length >= 1
    if true_solution in solution:
        error_EM = 1.0 - 1.0 / len(solution)
    else:
        error_EM = 1.0

    sub_latencies = result["sub_latencies"]
    latency_ideal_parallel = max(sub_latencies)
    latency_finite_parallel = calculate_latency_parallel(
        sub_latencies,
        config["sim_parallel_degree"],
    )

    trial_result = {
        "solution": solution,
        "true_solution": true_solution,
        "error_EM": float(error_EM),
        "latency": float(latency),
        "latency_ideal_parallel": float(latency_ideal_parallel),
        "latency_finite_parallel": float(latency_finite_parallel),
    }
    trial_result.update(solver.cost_metrics)
    return trial_result
