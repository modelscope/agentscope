#!/bin/bash

IFS=',' read -r -a HOSTS <<< "$1"

script_path=$(readlink -f "$0")
script_dir=$(dirname "$script_path")

for HOST in "${HOSTS[@]}"; do
    echo "Stopping server on $HOST"
    ssh root@$HOST "cd $script_dir && ./stop_all_server.sh"
done

echo "All servers stopped."