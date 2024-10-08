#!/bin/bash

IFS=',' read -r -a HOSTS <<< "$1"

agent_server_num=$2
env_server_num=$3

script_path=$(readlink -f "$0")
script_dir=$(dirname "$script_path")

for HOST in "${HOSTS[@]}"; do
    echo "Starting server on $HOST"
    ssh root@$HOST "cd $script_dir; ./start_all_server.sh $agent_server_num $env_server_num $HOST" &
done

echo "All servers started."