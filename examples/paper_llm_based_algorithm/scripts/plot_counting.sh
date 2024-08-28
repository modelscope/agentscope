#!/bin/bash

# each group: task, llm_model ("gpt-4-turbo" / "gpt-3.5-turbo" / "ollama_llama3_8b" / "vllm_llama3_70b")


# ================= counting, ollama_llama3_8b =================

python3 plot_exp_results.py \
    --folder ./out/counting/exp_counting_vary_n_model_ollama_llama3_8b-2024-06-19-11-11-13-kkwrhc

python3 plot_exp_results.py \
    --folder ./out/counting/exp_counting_vary_m_model_ollama_llama3_8b_n_200-2024-06-19-11-11-56-qsdlvt



# ================= counting, gpt-4-turbo =================

python3 plot_exp_results.py \
    --folder ./out/counting/exp_counting_vary_n_model_gpt-4-turbo-2024-06-19-17-42-50-armqap

python3 plot_exp_results.py \
    --folder ./out/counting/exp_counting_vary_m_model_gpt-4-turbo_n_200-2024-06-19-16-48-59-kxeqjx

