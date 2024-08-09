#!/bin/bash

# default values
gpu_num=8
model_per_gpu=1
model_path="/home/data/shared/checkpoints/llama3/llama3-8b-instruct"
base_port=8010

touch .vllm_pid
mkdir -p log

for ((i=0; i < ${gpu_num}; i=i+{model_per_gpu})); do
    port=$((base_port + i))
    export CUDA_VISIBLE_DEVICES=$i
    python -m vllm.entrypoints.openai.api_server --model "${model_path}" --port ${port} --enforce-eager > log/vllm-${port}.log 2>&1 &
    echo $! >> .vllm_pid
    echo "Started vllm server on port ${port} with PID $!"
done

echo "All vllm server started"