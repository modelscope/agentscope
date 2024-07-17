#!/bin/bash

# each group: task, llm_model ("gpt-4-turbo" / "gpt-3.5-turbo" / "ollama_llama3_8b" / "vllm_llama3_70b")


# ================= retrieval, ollama_llama3_8b =================

python3 plot_exp_results.py \
    --folder ./out/retrieval/exp_retrieval_vary_n_model_ollama_llama3_8b-2024-06-19-19-20-17-vjmixh

python3 plot_exp_results.py \
    --folder ./out/retrieval_no_needle/exp_retrieval_no_needle_vary_n_model_ollama_llama3_8b-2024-06-19-19-27-49-hdleoj

python3 plot_exp_results.py \
    --folder ./out/retrieval/exp_retrieval_vary_m_model_ollama_llama3_8b_n_10000-2024-06-27-18-26-51-tobsjs

python3 plot_exp_results.py \
    --folder ./out/retrieval/exp_retrieval_vary_m_model_ollama_llama3_8b_n_20000-2024-06-27-20-25-44-aclfgy


# ================= retrieval, vllm_llama3_70b =================

python3 plot_exp_results.py \
    --folder ./out/retrieval/exp_retrieval_vary_n_model_vllm_llama3_70b-2024-06-20-17-50-57-ufibkw

python3 plot_exp_results.py \
    --folder ./out/retrieval_no_needle/exp_retrieval_no_needle_vary_n_model_vllm_llama3_70b-2024-06-20-18-02-27-pyrcla

python3 plot_exp_results.py \
    --folder ./out/retrieval/exp_retrieval_vary_m_model_vllm_llama3_70b_n_10000-2024-06-20-19-38-45-olqreb

python3 plot_exp_results.py \
    --folder ./out/retrieval/exp_retrieval_vary_m_model_vllm_llama3_70b_n_20000-2024-06-20-18-29-44-pswqhc

