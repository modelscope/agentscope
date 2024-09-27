# -*- coding: utf-8 -*-
"""Functions and classes for the RAG task"""
import time
import random
import re
from typing import Any
import numpy as np

from src.alg_agents import ProblemSolver
from src.utils import calculate_latency_parallel, divide_string_into_chunks


def generate_request_multi_needles_in_haystack(config: dict) -> tuple:
    """Generate a request of RAG"""

    n = config["n"]  # length of text
    len_passcode = config["len_passcode"]  # also number of needles

    def get_pos_num_str(num: int) -> str:
        """Get suffix for each number (no larger than 10)"""
        if num == 1:
            return "st"
        elif num == 2:
            return "nd"
        elif num == 3:
            return "rd"
        else:
            return "th"

    # dict of passcodes for all colored objects
    colors = ["red", "green", "blue", "purple", "black", "white"]
    objects = ["door", "lock", "safe", "laptop"]
    dict_passcodes = {}
    for color in colors:
        for obj in objects:
            color_object = color + " " + obj
            random_passcode = "".join(
                [random.choice("123456789") for _ in range(len_passcode)],
            )  # omit 0
            dict_passcodes[color_object] = random_passcode

    # generate main text and key message, combine into request_string
    target_object = random.choice(list(dict_passcodes.keys()))
    true_solution = dict_passcodes[target_object]
    question = (
        f"What is the {len_passcode}-digit passcode to the {target_object}?"
    )

    insert_positions_relative = 0.05 + 0.9 * np.random.rand(
        len_passcode,
    )  # [0.05, 0.95]

    target_sentences = []
    for i in range(len_passcode):
        pos_num_str = get_pos_num_str(i + 1)
        target_sentences.append(
            f"The {i + 1}-{pos_num_str} digit of the passcode "
            f"to the {target_object} is {true_solution[i]}. ",
        )
    random.shuffle(target_sentences)

    length_total = sum(len(s) for s in target_sentences)

    sentences = []
    noise_objects = [obj for obj in dict_passcodes if obj != target_object]
    while length_total < n:
        obj = random.choice(noise_objects)
        pc = dict_passcodes[obj]
        idx = random.choice(range(len_passcode))
        pos_num_str = get_pos_num_str(idx + 1)
        s = (
            f"The {idx + 1}-{pos_num_str} digit of the passcode "
            f"to the {obj} is {pc[idx]}. "
        )
        length_total += len(s)
        if length_total >= n:
            break
        sentences.append(s)

    # random.shuffle(sentences)
    insert_positions = np.floor(insert_positions_relative * len(sentences))
    for i in range(len_passcode):
        sentences.insert(int(insert_positions[i]), target_sentences[i])
    request_string = "".join(sentences)

    return request_string, question, true_solution


class RAGSolver(ProblemSolver):
    """Solver class for RAG"""

    def __init__(self, config: dict) -> None:
        super().__init__(config=config)

    def solve(self, request_string: str, question: str) -> dict:
        """Solve by parallel decomposition"""

        m = self.config["m"]
        llm_to_dist = self.config["llm_to_dist"]

        self.reset_cost_metrics()

        n = len(request_string)
        if (m > n) or (m <= 0):
            m = n
            print("WARNING: reset m = n.")

        step_size = np.ceil(0.5 * m)
        sub_requests = divide_string_into_chunks(
            request_string=request_string,
            window_size=m,
            step_size=step_size,
        )

        print("/// request_string: ///")
        print(request_string)
        print("\n" + "=" * 60)

        # Solve each sub-task

        if llm_to_dist:  # TODO: make it actually work with parallelism...
            # time_start = time.time()
            # request_agent = self.spawn_request_agent()
            # dialog_agent = self.spawn_dialog_agent()
            # dialog_agents = []
            # for _ in range(len(sub_requests)):
            #     dialog_agents.append(
            #         self.spawn_dialog_agent().to_dist(lazy_launch=False),
            #     )
            # lst_x = [{} for _ in range(len(sub_requests))]
            # for i, sr in enumerate(sub_requests):
            #     content = self.prompt_retrieve_relevant_sentences(
            #         sr, question
            #         )
            #     x_request = request_agent(x=None, content=content)
            #     lst_x[i] = self.invoke_llm_call(x_request, dialog_agents[i])
            # sub_contents = [x.content for x in lst_x]
            # sub_solutions = ["" for _ in range(len(sub_requests))]
            # for i in range(len(sub_solutions)):
            #     ss = self.parse_llm_response_retrieve_relevant_sentences(
            #         sub_contents[i],
            #     )
            #     sub_solutions[i] = ss
            # sub_latencies = [time.time() - time_start]

            raise NotImplementedError(
                "Distributed algorithm is not yet implemented!",
            )

        request_agent = self.spawn_request_agent()
        dialog_agent = self.spawn_dialog_agent()

        sub_solutions = ["" for _ in range(len(sub_requests))]
        sub_latencies = [0.0 for _ in range(len(sub_requests))]
        for i, sr in enumerate(sub_requests):
            time_start = time.time()
            content = self.prompt_retrieve_relevant_sentences(sr, question)
            x_request = request_agent(x=None, content=content)
            x = self.invoke_llm_call(x_request, dialog_agent)
            ss = self.parse_llm_response_retrieve_relevant_sentences(
                x.content,
            )
            sub_solutions[i] = ss
            sub_latencies[i] = time.time() - time_start

        print("\n/// sub_solutions: ///")
        for ss in sub_solutions:
            print(ss)
        print("\n" + "=" * 60)

        sub_solutions = [
            ss for ss in sub_solutions if len(re.findall(r"\d+", ss)) > 0
        ]

        print("\n/// sub_solutions, filtered: ///")
        for ss in sub_solutions:
            print(ss)
        print("\n" + "=" * 60)

        # Aggregate results for the final solution
        time_start = time.time()
        context = " ... ".join(sub_solutions)
        content = self.prompt_generate_final_answer(context, question)
        x_request = request_agent(x=None, content=content)
        x = self.invoke_llm_call(x_request, dialog_agent)
        solution = self.parse_llm_response_generate_final_answer(x.content)
        final_step_latency = time.time() - time_start

        result = {
            "solution": solution,
            "sub_latencies": sub_latencies,
            "final_step_latency": final_step_latency,
        }
        return result

    def prompt_retrieve_relevant_sentences(
        self,
        request_string: str,
        question: str,
    ) -> str:
        """Prompter for retrieving relevant sentences"""

        prompt = (
            "User input: Your task is to retrieve, "
            "from a given piece of text, "
            "sentences that are relevant to a certain question.\n\n"
        )
        prompt += "## Below is the given text: \n\n"
        prompt += request_string
        prompt += "\n\n## Below is the question:\n\n"
        prompt += '"' + question + '"\n\n'
        prompt += (
            "Please read the text carefully, then retrieve "
            "all and only sentences that can be useful for "
            "answering the given question. "
        )
        prompt += (
            "The retrieved sentences must be exact copies "
            "of those in the original text. "
        )
        prompt += (
            "Keep your response concise, and make sure that "
            "no irrelevant sentence is retrieved. "
        )
        prompt += (
            "Orgaize your response as a single string; for example, "
            "if multiple sentences are retrieved, you may "
            'connect them with "..." in your response.\n'
        )
        prompt += (
            "Make sure that your response is formatted as follows: "
            "'Below are the sentences that can be useful for "
            'answering the question: "{the retrieved sentences '
            "as a single string}\".'. "
        )
        prompt += (
            "If there is no relevant sentence, "
            'your answer should be "None".\n'
        )
        return prompt

    def parse_llm_response_retrieve_relevant_sentences(
        self,
        llm_response: str,
    ) -> str:
        """Parser for retrieving relevant sentences"""

        pattern = "question:"
        idx = llm_response.rfind(pattern)
        if idx == -1:
            return "None"
        return llm_response[idx + len(pattern) :]

    def prompt_generate_final_answer(
        self,
        request_string: str,
        question: str,
    ) -> str:
        """Prompter for generating the final answer"""

        prompt = (
            "User input: Your task is to answer a question "
            "based on some given information.\n\n"
        )
        prompt += "## Below is the given information:\n\n"
        prompt += request_string
        prompt += "\n\n## Below is the question:\n\n"
        prompt += '"' + question + '"\n\n'
        prompt += "Please answer the question based on the given information. "
        prompt += (
            "Figure out each digit of the passcode, and format your "
            "final answer as a list of digits. Make sure that "
            'your response concludes as follows: "The answer to the '
            'question is [{the first digit}, {the second digit}, ...].". '
            "If there are any unknown digits, set them to 0.\n"
        )
        return prompt

    def parse_llm_response_generate_final_answer(
        self,
        llm_response: str,
    ) -> str:
        """Parser for generating the final answer"""

        idx1, idx2 = llm_response.rfind("["), llm_response.rfind("]")
        llm_response = llm_response[idx1 : (idx2 + 1)]
        lst_char = ["?", "x", "X"]
        for c in lst_char:
            llm_response = llm_response.replace(
                c,
                "0",
            )  # hotfix (when LLM doesn't follow instruction well)
        found_digits = re.findall(r"\d+", llm_response)
        len_passcode = self.config["len_passcode"]
        if len(found_digits) == 0:
            print("WARNING: No digit sequence found in LLM's response.")
            found_digits = ["0" for _ in range(len_passcode)]
        if len(found_digits) > len_passcode:
            found_digits = found_digits[:len_passcode]
        if len(found_digits) < len_passcode:
            found_digits = found_digits + [
                "0" for _ in range(len_passcode - len(found_digits))
            ]
        return "".join(
            found_digits,
        )  # guaranteed to have length match len_passcode


def calculate_passcode_normalized_wrong_digits(
    pc: str,
    pc_truth: str,
) -> float:
    """Calculate the normalized number of wrong digits"""

    assert len(pc) == len(pc_truth), "Lengths of passcodes do not match!"
    diff = [int(pc[i]) - int(pc_truth[i]) for i in range(len(pc))]
    return sum(d != 0 for d in diff) / len(pc)


def trial_rag(config: dict, seed: Any = None) -> dict:
    """One trial for one config"""

    # Generate random request (with controlled seed)
    random.seed(seed)
    np.random.seed(seed)
    (
        request_string,
        question,
        true_solution,
    ) = generate_request_multi_needles_in_haystack(config)
    random.seed(None)
    np.random.seed(None)

    # Solve the problem and measure metrics
    time_start = time.time()
    solver = RAGSolver(config=config)
    solver.reset_cost_metrics()
    result = solver.solve(request_string, question)
    latency = time.time() - time_start

    print("\n///result of overall algorithm: ///")
    print(result)
    print("\n" + "=" * 60)

    solution = result["solution"]
    error_EM = 0.0 if solution == true_solution else 1.0
    error_wrong_digits_normalized = calculate_passcode_normalized_wrong_digits(
        solution,
        true_solution,
    )

    sub_latencies = result["sub_latencies"]
    latency_ideal_parallel = max(sub_latencies)
    latency_finite_parallel = calculate_latency_parallel(
        sub_latencies,
        config["sim_parallel_degree"],
    )

    final_step_latency = result["final_step_latency"]
    latency_ideal_parallel += final_step_latency
    latency_finite_parallel += final_step_latency

    trial_result = {
        "solution": solution,
        "true_solution": true_solution,
        "error_EM": float(error_EM),
        "error_wrong_digits_normalized": float(error_wrong_digits_normalized),
        "latency": float(latency),
        "latency_ideal_parallel": float(latency_ideal_parallel),
        "latency_finite_parallel": float(latency_finite_parallel),
    }
    trial_result.update(solver.cost_metrics)
    return trial_result
