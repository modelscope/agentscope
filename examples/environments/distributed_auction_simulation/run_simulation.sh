#!/bin/bash

# default values
base_port=12330
hosts="localhost" # or "server1 server2 server3 ..."
model_per_host=8
agent_type="random" # or "llm"
waiting_time=3.0

# check server-per-host
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <server-per-host> <bidder-num>"
    exit 1
fi

# check bidder-num
if ! [[ "$2" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <server-per-host> <bidder-num>"
    exit 1
fi

mkdir -p log

python main.py --role main --hosts ${hosts} --base-port ${base_port} --bidder-num $2 --server-per-host $1 --model-per-host ${model_per_host} --agent-type ${agent_type} --waiting-time ${waiting_time}
