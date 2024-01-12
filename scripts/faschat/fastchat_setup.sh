#!/bin/bash

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


python3 -m fastchat.serve.controller &
sleep 1
python3 -m fastchat.serve.model_worker --model-path "${model_name_or_path}" &
sleep 1
python3 -m fastchat.serve.openai_api_server --host localhost --port "${port}" &
