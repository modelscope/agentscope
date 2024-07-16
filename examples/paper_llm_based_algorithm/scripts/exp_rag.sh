#!/bin/bash

# config of each experiment:
# - task
# - llm_model ("gpt-4-turbo" / "gpt-3.5-turbo" / "ollama_llama3_8b" / "vllm_llama3_70b")
# - variable_name, lst_variable, n_base (n for vary-m, n_max for vary-n)
# - misc configs for exp (save_results, ntrials)

# for RAG, choose m = 2 * n / (k + 1), k = 1, 2, 3, ...
# note: ollama_llama3_8b doesn't follow instructions well in this task


# ================= rag, vllm_llama3_70b =================

python3 run_exp_single_variable.py \
    --task rag \
    --llm_model vllm_llama3_70b \
    --variable_name n \
    --lst_variable 20000 16000 12000 8000 4000 2000 1000 \
    --n_base 20000 \
    --save_results True \
    --ntrials 20

python3 run_exp_single_variable.py \
    --task rag \
    --llm_model vllm_llama3_70b \
    --variable_name m \
    --lst_variable 20000 13340 10000 8000 6680 5000 4000 2000 1000  \
    --n_base 20000 \
    --save_results True \
    --ntrials 10
