# LLM-based algorithms

This folder contains the source code for reproducing the experiment results in our arXiv preprint "On the Design and Analysis of LLM-Based Algorithms".

Our work initiates a formal investigation into the design and analysis of LLM-based algorithms,
i.e. algorithms that contain one or multiple calls of large language models (LLMs) as sub-routines and critically rely on the capabilities of LLMs.
With some key abstractions identified, we provide analytical study for the accuracy and efficiency of generic LLM-based algorithms as well as diverse concrete tasks, which is validated by extensive experiments.

Within this folder, you can find our implementation for the key abstractions,
the LLM-based algorithms in four concrete examples,
and the experiments for validating our analysis in the manuscript.

## Tested Models

The following models have been tested, which are also listed in `model_configs.json`:
GPT-4 Turbo,
GPT-3.5 Turbo,
Llama3-8B (with ollama),
Llama3-70B (with vLLM).

## Prerequisites

1. Install AgentScope from source with `pip`, according to the [official instruction](../../README.md).
2. Install matplotlib: `pip install matplotlib`.
3. Change directory: `cd examples/paper_llm_based_algorithm`.
4. Set up LLM model configs in `model_configs.json`.

## Usage

### Run experiments

To run experiments for a certain task:

```bash
bash ./scripts/exp_{task}.sh
```

or copy a piece of scripts therein, modify the parameters, and run it in the terminal, for example:

```bash
python3 run_exp_single_variable.py \
    --task counting \
    --llm_model ollama_llama3_8b \
    --variable_name n \
    --lst_variable 200 150 100 50 20 10 \
    --n_base 200 \
    --save_results True \
    --ntrials 10
```

Parameters:

- `task`: name of the task, {"counting", "sorting", "retrieval", "retrieval_no_needle", "rag"}.
- `llm_model`: name of the LLM model, i.e. `config_name` in `model_configs.json`.
- `variable_name`: "n" for problem size, or "m" for sub-task size.
- `lst_variable`: list of values for the variable.
- `n_base`: the maximum of `lst_variable` (if `variable_name` is "n"), or the value of "n" (if `variable_name` is "m").
- `save_results`: if `True`, experiment results will be saved to `./out`; otherwise, results will be plotted and shown at the end of the experiment, and won't be saved.
- `ntrials`: number of independent trials for each experiment config, i.e. each entry of `lst_variable`.

### Plot results

To plot experiment results that have been saved:

```bash
bash ./scripts/plot_{task}.sh
```

or copy a piece of scripts therein and run it in the terminal, for example:

```bash
python3 plot_exp_results.py \
    --folder ./out/counting/exp_counting_vary_n_model_ollama_llama3_8b-2024-06-19-11-11-13-kkwrhc
```

The path to the experiment results need to be replaced with the actual one generated during your own experiment.
The generated figures will be saved to the same folder.

## Reference

For more details, please refer to our arXiv preprint:

```
@article{llm_based_algorithms,
  author       = {Yanxi Chen and
                  Yaliang Li and
                  Bolin Ding and
                  Jingren Zhou},
  title        = {On the Design and Analysis of LLM-Based Algorithms},
  journal      = {CoRR},
  volume       = {abs/2407.14788},
  year         = {2024},
}
```
