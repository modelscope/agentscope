#!/bin/bash

# each group: task, llm_model ("gpt-4-turbo" / "gpt-3.5-turbo" / "ollama_llama3_8b" / "vllm_llama3_70b")


# ================= sorting, vllm_llama3_70b =================

python3 plot_exp_results.py \
    --folder ./out/sorting/exp_sorting_vary_n_model_vllm_llama3_70b-2024-06-20-11-30-08-shovue

python3 plot_exp_results.py \
    --folder ./out/sorting/exp_sorting_vary_m_model_vllm_llama3_70b_n_200-2024-06-20-12-07-57-bpcwcm


# ================= sorting, gpt-4-turbo =================

python3 plot_exp_results.py \
    --folder ./out/sorting/exp_sorting_vary_n_model_gpt-4-turbo-2024-06-20-16-39-08-cwfmbh

python3 plot_exp_results.py \
    --folder ./out/sorting/exp_sorting_vary_m_model_gpt-4-turbo_n_200-2024-06-21-09-48-46-wiqgms

