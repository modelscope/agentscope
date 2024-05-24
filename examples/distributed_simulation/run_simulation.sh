#!/bin/bash

# default values
base_port=12330
hosts="localhost" # or "server1 server2 server3 ..."
moderator_per_host=4
model_per_host=8
agent_type="random" # or "llm"
max_value=100

# check server-per-host
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <server-per-host> <participant-num>"
    exit 1
fi

# check participant-num
if ! [[ "$2" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <server-per-host> <participant-num>"
    exit 1
fi

mkdir -p log

python main.py --role main --hosts ${hosts} --base-port ${base_port} --participant-num $2 --server-per-host $1 --model-per-host ${model_per_host} --moderator-per-host ${moderator_per_host} --agent-type ${agent_type} --max-value ${max_value}
