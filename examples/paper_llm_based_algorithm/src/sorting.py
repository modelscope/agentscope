# -*- coding: utf-8 -*-
"""Functions and classes for the sorting task"""
import time
import random
from typing import Union, Any
import numpy as np

from src.alg_agents import ProblemSolver
from src.utils import calculate_latency_parallel


def generate_request_sorting(config: dict) -> tuple:
    """Generate a request of sorting"""

    n = config["n"]
    ndigits = config["ndigits"]
    n_max = config["n_max"]

    def format_list2str(lst: Union[list, np.array], ndigits: int) -> str:
        """Format a list as a string"""
        lst = np.array(lst).round(decimals=ndigits)
        formatter = r"{:." + str(ndigits) + r"f}"
        list_of_str = [formatter.format(num) for num in lst]
        list_as_str = "[" + ", ".join(list_of_str) + "]"
        return list_as_str

    list_to_sort = np.random.rand(n_max).round(decimals=ndigits)
    list_to_sort = list_to_sort[:n]
    list_as_str = format_list2str(list_to_sort, ndigits)
    true_solution = np.sort(list_to_sort)

    return list_to_sort, list_as_str, true_solution


class SortingSolver(ProblemSolver):
    """Solver class for the sorting task"""

    def __init__(self, config: dict) -> None:
        super().__init__(config=config)

    def solve_directly(
        self,
        request_string: str,
        request_agent: Any,
        dialog_agent: Any,
    ) -> Union[list, np.array]:
        """Solve directly"""

        content = self.prompt_sorting(request_string)
        x_request = request_agent(x=None, content=content)
        x = self.invoke_llm_call(x_request, dialog_agent)
        solution = self.parse_llm_response_sorting(x.content)
        return solution

    def merge_two_sorted_lists(
        self,
        list1: Union[list, np.array],
        list2: Union[list, np.array],
        request_agent: Any = None,
        dialog_agent: Any = None,
    ) -> Union[list, np.array]:
        """Merge two non-empty sorted lists or np.arrays into one"""

        merge_by_llm = self.config["merge_by_llm"]

        if merge_by_llm is False:
            len1, len2 = len(list1), len(list2)
            idx1, idx2 = 0, 0
            idx = 0
            solution = np.zeros(len1 + len2)
            while idx < len1 + len2:
                if idx1 == len1:
                    val = list2[idx2]
                    idx2 += 1
                elif idx2 == len2:
                    val = list1[idx1]
                    idx1 += 1
                else:
                    val1, val2 = list1[idx1], list2[idx2]
                    if val1 <= val2:
                        val = val1
                        idx1 += 1
                    else:
                        val = val2
                        idx2 += 1
                solution[idx] = val
                idx += 1
        else:
            request_string = str(list(list1)) + "\n" + str(list(list2))
            content = self.prompt_merging(request_string)
            x_request = request_agent(x=None, content=content)
            x = self.invoke_llm_call(x_request, dialog_agent)
            solution = self.parse_llm_response_sorting(x.content)

        return solution

    def merge_sorted_lists_incremental(
        self,
        lists: list,
        request_agent: Any = None,
        dialog_agent: Any = None,
    ) -> Union[list, np.array]:
        """
        lists: a list of sorted lists/arrays
        CAUTION: lists will be changed by this function
        """
        for _ in range(len(lists) - 1):
            list1 = lists.pop()
            list2 = lists.pop()
            solution = self.merge_two_sorted_lists(
                list1,
                list2,
                request_agent,
                dialog_agent,
            )
            lists.append(solution)
        return lists[0]  # i.e. solution

    def merge_sorted_lists_hierarchical(
        self,
        lists: list,
        request_agent: Any = None,
        dialog_agent: Any = None,
    ) -> Union[list, np.array]:
        """
        lists: a list of sorted lists/arrays
        CAUTION: lists will be changed by this function
        """
        while len(lists) > 1:
            niters = len(lists) // 2
            for _ in range(niters):
                list1 = lists.pop(0)
                list2 = lists.pop(0)
                solution = self.merge_two_sorted_lists(
                    list1,
                    list2,
                    request_agent,
                    dialog_agent,
                )
                lists.append(solution)
        return lists[0]

    def solve_decomposition(self, request_string: str) -> dict:
        """Solve by parallel decomposition"""

        m = int(self.config["m"])
        merge_method = self.config["merge_method"]
        self.reset_cost_metrics()

        # Main algorithm: sort blocks, then merge
        request_list = eval(request_string)
        list_len = len(request_list)

        if m <= 0 or m > list_len:
            m = list_len
        k = list_len // m
        if k * m < list_len:
            k += 1

        request_agent = self.spawn_request_agent()
        dialog_agent = self.spawn_dialog_agent()
        sub_strings = [
            str(request_list[i * m : min((i + 1) * m, len(request_list))])
            for i in range(k)
        ]

        # Step 1: sort each sub-list
        sub_solutions = [[] for _ in range(k)]
        sub_latencies = [0.0 for _ in range(k)]
        for i in range(k):
            time_start = time.time()
            sub_solutions[i] = self.solve_directly(
                sub_strings[i],
                request_agent,
                dialog_agent,
            )
            sub_latencies[i] = time.time() - time_start

        # Step 2: merge sorted sub-lists
        lists = sub_solutions
        error_monotonicity_total = sum(
            calculate_monotonicity_error(lst) for lst in lists
        )

        if merge_method == "hierarchical":
            solution = self.merge_sorted_lists_hierarchical(
                lists,
                request_agent,
                dialog_agent,
            )
        elif merge_method == "incremental":
            solution = self.merge_sorted_lists_incremental(
                lists,
                request_agent,
                dialog_agent,
            )
        else:
            raise ValueError("Invalid config['merge_method']!")

        result = {
            "solution": solution,
            "sub_latencies": sub_latencies,
            "error_monotonicity_total": float(error_monotonicity_total),
        }
        return result

    def parse_llm_response_sorting(self, llm_response: str) -> np.array:
        """Parser"""

        idx_low, idx_high = llm_response.rfind("["), llm_response.rfind("]")
        if (idx_low == -1) or (idx_high == -1):
            print("WARNING: unable to parse LLM's response.")
            llm_solution = "[]"
        else:
            llm_solution = llm_response[idx_low : (idx_high + 1)]
        list_llm_solution = np.array(eval(llm_solution))
        return list_llm_solution

    def prompt_sorting(self, request_string: str) -> str:
        """Prompter for sorting"""

        PROMPT_PRE = (
            "User input: Sort the following list in ascending order:\n"
        )
        PROMPT_POST = (
            "\nFormat your answer as a list in one line. "
            "Do NOT output anything else.\n"
        )
        return PROMPT_PRE + request_string + PROMPT_POST

    def prompt_merging(self, request_string: str) -> str:
        """Prompter for merging"""

        PROMPT_PRE = (
            "User input: Merge the following two (approximately) "
            "sorted lists into one single sorted list:\n"
        )
        PROMPT_POST = (
            "\n"
            + "Format your answer as a list. Do NOT output anything else.\n"
        )
        return PROMPT_PRE + request_string + PROMPT_POST


def trial_sorting(config: dict, seed: Any = None) -> dict:
    """One trial for one config"""

    # Generate a random request
    random.seed(seed)
    np.random.seed(seed)
    list_to_sort, list_as_str, true_solution = generate_request_sorting(config)
    random.seed(None)
    np.random.seed(None)

    print(f"///\nSorting problem instance:\n{list_to_sort}\n///\n")

    # Solve the problem and measure metrics
    time_start = time.time()
    solver = SortingSolver(config=config)
    solver.reset_cost_metrics()
    result = solver.solve_decomposition(request_string=list_as_str)
    latency = time.time() - time_start

    solution = result["solution"]
    error_monotonicity_total = result["error_monotonicity_total"]
    error_monotonicity_final = calculate_monotonicity_error(solution)
    error_L1_normalized = calculate_sorting_error(
        true_solution=true_solution,
        solution=solution,
        option="L1_normalized",
    )
    error_L1_normalized_fuzzy = calculate_sorting_error(
        true_solution=true_solution,
        solution=solution,
        option="L1_normalized_fuzzy",
    )
    error_Linf = calculate_sorting_error(
        true_solution=true_solution,
        solution=solution,
        option="Linf",
    )
    error_Linf_fuzzy = calculate_sorting_error(
        true_solution=true_solution,
        solution=solution,
        option="Linf_fuzzy",
    )
    error_EM = 0 if error_Linf < 1e-6 else 1
    error_list_length_normalized = np.abs(
        len(true_solution) - len(solution),
    ) / len(true_solution)

    sub_latencies = result["sub_latencies"]
    latency_ideal_parallel = max(sub_latencies)
    latency_finite_parallel = calculate_latency_parallel(
        sub_latencies,
        config["sim_parallel_degree"],
    )

    # Return result
    # Note: solution and true_solution can be long, hence omit here
    trial_result = {
        "error_L1_normalized": float(error_L1_normalized),
        "error_L1_normalized_fuzzy": float(error_L1_normalized_fuzzy),
        "error_Linf": float(error_Linf),
        "error_Linf_fuzzy": float(error_Linf_fuzzy),
        "error_EM": int(error_EM),
        "error_list_length_normalized": float(error_list_length_normalized),
        "error_monotonicity_total": float(error_monotonicity_total),
        "error_monotonicity_final": float(error_monotonicity_final),
        "latency": float(latency),
        "latency_ideal_parallel": float(latency_ideal_parallel),
        "latency_finite_parallel": float(latency_finite_parallel),
    }
    trial_result.update(solver.cost_metrics)
    return trial_result


# utils for sorting task


def calculate_sorting_error(
    true_solution: Union[np.array, list],
    solution: Union[np.array, list],
    option: str,
) -> Any:
    """
    option: "L1_normalized" / "L1_normalized_fuzzy" / "Linf" / "Linf_fuzzy"

    Assumption for "L1_normalized" and "Linf":
    true_solution and solution have range [0, 1], hence max error is 1.0
    """

    if isinstance(true_solution, list):
        true_solution = np.array(true_solution)
    if isinstance(solution, list):
        solution = np.array(solution)

    # "L1_normalized", "Linf"
    if option == "L1_normalized":
        if len(true_solution) == len(solution):
            ans = np.mean(np.abs(true_solution - solution))
        else:
            ans = 1.0
        return ans
    if option == "Linf":
        if len(true_solution) == len(solution):
            ans = np.max(np.abs(true_solution - solution))
        else:
            ans = 1.0
        return ans

    # Fuzzy versions
    if len(solution) < len(true_solution):  # extend solution
        appended_part = np.array(
            [solution[-1] for _ in range(len(true_solution) - len(solution))],
        )
        solution = np.concatenate((solution, appended_part))
    elif len(solution) > len(true_solution):  # truncate solution
        solution = solution[: len(true_solution)]

    if option == "L1_normalized_fuzzy":
        ans = np.mean(np.abs(solution - true_solution))
    elif option == "Linf_fuzzy":
        ans = np.max(np.abs(solution - true_solution))
    return ans


def calculate_monotonicity_error(solution: Union[np.array, list]) -> Any:
    """Calculate non-monotonicity error metric"""

    if isinstance(solution, list):
        solution = np.array(solution)
    n = len(solution)
    diff = (
        solution[0 : n - 1] - solution[1:n]
    )  # if monotone: should be all negative or zero
    diff[diff <= 0.0] = 0.0
    return np.sum(np.abs(diff))
