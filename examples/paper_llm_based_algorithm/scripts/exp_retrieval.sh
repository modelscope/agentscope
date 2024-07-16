#!/bin/bash

# config of each experiment:
# - task
# - llm_model ("gpt-4-turbo" / "gpt-3.5-turbo" / "ollama_llama3_8b" / "vllm_llama3_70b")
# - variable_name, lst_variable, n_base (n for vary-m, n_max for vary-n)
# - misc configs for exp (save_results, ntrials)

# for retrieval, choose m = 2 * n / (k + 1), k = 1, 2, 3, ...
# theoretical minimizer for latency with p = 4 is m = 0.4 * n


# ================= retrieval, ollama_llama3_8b =================

# vary-n
python3 run_exp_single_variable.py \
    --task retrieval \
    --llm_model ollama_llama3_8b \
    --variable_name n \
    --lst_variable 10000 8000 6000 4000 2000 1000 \
    --n_base 10000 \
    --save_results True \
    --ntrials 20

# vary-n, no-needle
python3 run_exp_single_variable.py \
    --task retrieval_no_needle \
    --llm_model ollama_llama3_8b \
    --variable_name n \
    --lst_variable 4000 2000 1000 500 200 100\
    --n_base 4000 \
    --save_results True \
    --ntrials 20

# vary-m, small n
python3 run_exp_single_variable.py \
    --task retrieval \
    --llm_model ollama_llama3_8b \
    --variable_name m \
    --lst_variable 10000 6670 5000 4000 3340 2500 2000 1000 500 \
    --n_base 10000 \
    --save_results True \
    --ntrials 10

# vary-m, large n
python3 run_exp_single_variable.py \
    --task retrieval \
    --llm_model ollama_llama3_8b \
    --variable_name m \
    --lst_variable 20000 13340 10000 8000 6680 5000 4000 2000 1000 \
    --n_base 20000 \
    --save_results True \
    --ntrials 10


# ================= retrieval, vllm_llama3_70b =================

# vary-n
python3 run_exp_single_variable.py \
    --task retrieval \
    --llm_model vllm_llama3_70b \
    --variable_name n \
    --lst_variable 10000 8000 6000 4000 2000 1000 \
    --n_base 10000 \
    --save_results True \
    --ntrials 20

# vary-n, no-needle
python3 run_exp_single_variable.py \
    --task retrieval_no_needle \
    --llm_model vllm_llama3_70b \
    --variable_name n \
    --lst_variable 4000 2000 1000 500 200 100\
    --n_base 4000 \
    --save_results True \
    --ntrials 20

# vary-m, small n
python3 run_exp_single_variable.py \
    --task retrieval \
    --llm_model vllm_llama3_70b \
    --variable_name m \
    --lst_variable 10000 6670 5000 4000 3340 2500 2000 1000 500 \
    --n_base 10000 \
    --save_results True \
    --ntrials 10

# vary-m, large n
python3 run_exp_single_variable.py \
    --task retrieval \
    --llm_model vllm_llama3_70b \
    --variable_name m \
    --lst_variable 20000 13340 10000 8000 6680 5000 4000 2000 1000 \
    --n_base 20000 \
    --save_results True \
    --ntrials 10
