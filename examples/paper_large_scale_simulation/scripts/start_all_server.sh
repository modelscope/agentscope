#!/bin/bash

# default values
base_port=12330
host_name="localhost"
env_server_num=4

# get number of server
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <agent-server-num>"
    exit 1
fi

if [ "$#" -ge 2 ]; then

    if ! [[ "$2" =~ ^[0-9]+$ ]]; then
        echo "Usage: $0 <agent-server-num> [<env-server-num> <hostname>]"
        exit 1
    fi

    env_server_num=$2
fi

if [ "$#" -ge 3 ]; then
    host_name=$3
fi

agent_server_num=$1

# create files for pid
script_path=$(readlink -f "$0")
script_dir=$(dirname "$script_path")
upper_dir=$(dirname "$script_dir")
cd $upper_dir
touch .pid

# activate your environment
source /mnt/conda/miniconda3/bin/activate as

# start all agent servers
for ((i=0; i<(agent_server_num + env_server_num); i++)); do
    port=$((base_port + i))
    python main.py --role participant --hosts ${host_name} --base-port ${port} > log/$port 2>&1 &
    echo $! >> .pid
    echo "Started agent server on ${host_name}:${port} with PID $!"
done

echo "All servers started"