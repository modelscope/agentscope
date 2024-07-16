#!/bin/bash

# config of each experiment:
# - task
# - llm_model ("gpt-4-turbo" / "gpt-3.5-turbo" / "ollama_llama3_8b" / "vllm_llama3_70b")
# - variable_name, lst_variable, n_base (n for vary-m, n_max for vary-n)
# - misc configs for exp (save_results, ntrials)


# ================= counting, ollama_llama3_8b =================

python3 run_exp_single_variable.py \
    --task counting \
    --llm_model ollama_llama3_8b \
    --variable_name n \
    --lst_variable 200 150 100 50 20 10 \
    --n_base 200 \
    --save_results True \
    --ntrials 10

python3 run_exp_single_variable.py \
    --task counting \
    --llm_model ollama_llama3_8b \
    --variable_name m \
    --lst_variable 200 100 67 50 40 20 10 \
    --n_base 200 \
    --save_results True \
    --ntrials 10


# ================= counting, gpt-4-turbo =================

python3 run_exp_single_variable.py \
    --task counting \
    --llm_model gpt-4-turbo \
    --variable_name n \
    --lst_variable 200 150 100 50 20 10  \
    --n_base 200 \
    --save_results True \
    --ntrials 20

python3 run_exp_single_variable.py \
    --task counting \
    --llm_model gpt-4-turbo \
    --variable_name m \
    --lst_variable 200 100 67 50 40 20 10 \
    --n_base 200 \
    --save_results True \
    --ntrials 10

