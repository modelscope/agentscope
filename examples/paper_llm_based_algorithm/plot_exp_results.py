# -*- coding: utf-8 -*-
"""Plot results of single-variable experiments and save figures"""

import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt


FIGSIZE = (3.0, 3.0)


def load_data(folder: str) -> list:
    """Load data from file"""
    lst = []
    configs_results_folder = os.path.join(folder, "data")
    for filename in os.scandir(configs_results_folder):
        with open(filename.path, "r", encoding="utf-8") as file:
            print("/// filename: ", filename.name, " ///")
            if "json" in filename.name:
                config_result = json.load(file)
                lst.append(config_result)
    return lst


def preprocess_metrics_data(
    configs_results: list,
    metric_names: list,
    variable_name: str,
) -> tuple:
    """Preprocess data of metrics"""
    lst_variable = []
    metrics_mean = {name: [] for name in metric_names}
    metrics_std = {name: [] for name in metric_names}

    for config_result in configs_results:
        config = config_result["config"]
        lst_variable.append(config[variable_name])

        trials_results = config_result["trials_results"]
        for name in metric_names:
            lst = [rst[name] for rst in trials_results]
            metrics_mean[name].append(np.mean(lst))
            metrics_std[name].append(np.std(lst))

    idx_sort = np.argsort(lst_variable)
    lst_variable = np.array(lst_variable)[idx_sort]
    for name in metric_names:
        metrics_mean[name] = np.array(metrics_mean[name])[idx_sort]
        metrics_std[name] = np.array(metrics_std[name])[idx_sort]
    return lst_variable, metrics_mean, metrics_std


def plot_cost_metrics(
    folder: str,
    variable_name: str,
) -> None:
    """Plot cost metrics, which are task-agnostic"""
    dict_cost_metrics = {
        # Non latency
        "llm_calls": "LLM calls",
        "prefilling_tokens_total": "Prefilling tokens",
        "decoding_tokens_total": "Decoding tokens",
        # Latency
        "latency": "Latency (sec)",
        "latency_finite_parallel": "Latency, p=4 (sec)",
        "latency_ideal_parallel": r"Latency, p=$\infty$ (sec)",
    }
    cost_metric_names = list(dict_cost_metrics.keys())

    # Preprocess data
    configs_results = load_data(folder)
    (
        lst_variable,
        cost_metrics_mean,
        cost_metrics_std,
    ) = preprocess_metrics_data(
        configs_results,
        cost_metric_names,
        variable_name,
    )

    # Plot
    if variable_name == "n":
        name_xlabel = "Task size $n$"
    elif variable_name == "m":
        name_xlabel = "Sub-task size $m$"

    for name in cost_metric_names:
        _, _ = plt.subplots(figsize=FIGSIZE)
        plt.plot(lst_variable, cost_metrics_mean[name], "-o", color="r")
        plt.fill_between(
            lst_variable,
            cost_metrics_mean[name] - cost_metrics_std[name],
            cost_metrics_mean[name] + cost_metrics_std[name],
            alpha=0.2,
            facecolor="r",
        )
        plt.grid(True)
        plt.ylabel(dict_cost_metrics[name])
        plt.xlabel(name_xlabel)
        plt.tight_layout()
        fig_path = folder + f"/{name}.pdf"
        plt.savefig(fig_path, format="pdf")


dict_error_metrics_counting = {
    "error_count": "Counting error",
    "error_count_normalized": "Normalized counting error",
}

dict_error_metrics_sorting = {
    "error_EM": "Exact-match error",
    "error_L1_normalized_fuzzy": r"Fuzzy normalized $\ell_1$ error",
    "error_Linf_fuzzy": r"Fuzzy $\ell_{\infty}$ error",
    "error_list_length_normalized": "Length-mismatch error",
    "error_monotonicity_final": "Non-monotonicity error",
}

dict_error_metrics_retrieval = {
    "error_EM": "Exact-match error",
}

dict_error_metrics_rag = {
    "error_EM": "Exact-match error",
    "error_wrong_digits_normalized": "Fraction of wrong digits",
}

dict_error_metrics_all_tasks = {
    "counting": dict_error_metrics_counting,
    "sorting": dict_error_metrics_sorting,
    "retrieval": dict_error_metrics_retrieval,
    "rag": dict_error_metrics_rag,
}


def plot_error_metrics(
    folder: str,
    variable_name: str,
    task: str,
) -> None:
    """Plot error metrics, both task-agnostic and task-specific figures"""
    dict_error_metrics = dict_error_metrics_all_tasks[task]
    error_metric_names = list(dict_error_metrics.keys())

    # Preprocess data
    configs_results = load_data(folder)
    (
        lst_variable,
        error_metrics_mean,
        error_metrics_std,
    ) = preprocess_metrics_data(
        configs_results,
        error_metric_names,
        variable_name,
    )

    # Plot
    if variable_name == "n":
        name_xlabel = "Task size $n$"
    elif variable_name == "m":
        name_xlabel = "Sub-task size $m$"

    # 1. Task-agnostic part
    for name in error_metric_names:
        _, _ = plt.subplots(figsize=FIGSIZE)
        plt.plot(lst_variable, error_metrics_mean[name], "-o", color="b")
        plt.fill_between(
            lst_variable,
            error_metrics_mean[name] - error_metrics_std[name],
            error_metrics_mean[name] + error_metrics_std[name],
            alpha=0.2,
            facecolor="b",
        )
        plt.grid(True)
        plt.ylabel(dict_error_metrics[name])
        plt.xlabel(name_xlabel)
        plt.tight_layout()
        fig_path = folder + f"/{name}.pdf"
        plt.savefig(fig_path, format="pdf")

    # 2. Task-specific part
    if task == "sorting":
        # special plot: error_L1_normalized_fuzzy and error_Linf_fuzzy
        _, _ = plt.subplots(figsize=FIGSIZE)
        name = "error_Linf_fuzzy"
        plt.plot(
            lst_variable,
            error_metrics_mean[name],
            "-o",
            color="b",
            label=r"Fuzzy $\ell_{\infty}$",
        )
        plt.fill_between(
            lst_variable,
            error_metrics_mean[name] - error_metrics_std[name],
            error_metrics_mean[name] + error_metrics_std[name],
            alpha=0.2,
            facecolor="b",
        )
        name = "error_L1_normalized_fuzzy"
        plt.plot(
            lst_variable,
            error_metrics_mean[name],
            "--*",
            color="m",
            label=r"Fuzzy normalized $\ell_1$",
        )
        plt.fill_between(
            lst_variable,
            error_metrics_mean[name] - error_metrics_std[name],
            error_metrics_mean[name] + error_metrics_std[name],
            alpha=0.2,
            facecolor="m",
        )
        plt.grid(True)
        plt.ylabel("Error")
        plt.xlabel(name_xlabel)
        plt.legend()
        plt.tight_layout()
        fig_path = folder + "/error_fuzzy_L1_Linf.pdf"
        plt.savefig(fig_path, format="pdf")

    elif task == "rag":
        # special plot: error_EM and error_wrong_digits_normalized
        _, _ = plt.subplots(figsize=FIGSIZE)
        name = "error_EM"
        plt.plot(
            lst_variable,
            error_metrics_mean[name],
            "-o",
            color="b",
            label="Exact-match error",
        )
        plt.fill_between(
            lst_variable,
            error_metrics_mean[name] - error_metrics_std[name],
            error_metrics_mean[name] + error_metrics_std[name],
            alpha=0.2,
            facecolor="b",
        )
        name = "error_wrong_digits_normalized"
        plt.plot(
            lst_variable,
            error_metrics_mean[name],
            "--*",
            color="m",
            label="Fraction of wrong digits",
        )
        plt.fill_between(
            lst_variable,
            error_metrics_mean[name] - error_metrics_std[name],
            error_metrics_mean[name] + error_metrics_std[name],
            alpha=0.2,
            facecolor="m",
        )
        plt.grid(True)
        plt.ylabel("Error")
        plt.xlabel(name_xlabel)
        plt.legend()
        plt.tight_layout()
        fig_path = folder + "/error_EM_wrong_digits.pdf"
        plt.savefig(fig_path, format="pdf")


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()

    parser.add_argument("--folder", type=str)

    return parser.parse_args()


def get_task_from_folder(folder: str) -> str:
    """Get task name from folder name"""
    if "counting" in folder:
        task = "counting"
    elif "sorting" in folder:
        task = "sorting"
    elif "retrieval" in folder:
        task = "retrieval"
    elif "rag" in folder:
        task = "rag"
    return task


def get_variable_name_from_folder(folder: str) -> str:
    """Get variable name from folder name"""
    if "vary_n" in folder:
        variable_name = "n"
    elif "vary_m" in folder:
        variable_name = "m"
    return variable_name


if __name__ == "__main__":
    args_main = parse_args()
    folder_main = args_main.folder

    task_main = get_task_from_folder(folder_main)
    variable_name_main = get_variable_name_from_folder(folder_main)

    plot_cost_metrics(folder_main, variable_name_main)
    plot_error_metrics(folder_main, variable_name_main, task_main)
