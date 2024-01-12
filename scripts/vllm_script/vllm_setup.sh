#!/bin/bash

# pip3 install vllm

model_name_or_path="llama-2"
port=8000

while getopts "m:p:" flag
do
    # shellcheck disable=SC2220
    case "${flag}" in
        m) model_name_or_path=${OPTARG};;
        p) port=${OPTARG};;
    esac
done

python -m vllm.entrypoints.openai.api_server --model "${model_name_or_path}" \
  --port "${port}" --enforce-eager
