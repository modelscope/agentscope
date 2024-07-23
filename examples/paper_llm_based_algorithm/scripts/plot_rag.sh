#!/bin/bash

# each group: task, llm_model ("gpt-4-turbo" / "gpt-3.5-turbo" / "ollama_llama3_8b" / "vllm_llama3_70b")


# ================= rag, vllm_llama3_70b =================

python3 plot_exp_results.py \
    --folder ./out/rag/exp_rag_vary_n_model_vllm_llama3_70b-2024-06-21-14-05-46-caedxr

python3 plot_exp_results.py \
    --folder ./out/rag/exp_rag_vary_m_model_vllm_llama3_70b_n_20000-2024-06-21-15-58-44-lppwcm

