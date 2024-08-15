#!/bin/bash

# default values
base_port=12330
host_name="localhost"

# get number of server
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <number-of-server-for-bidders>"
    exit 1
fi

bidder_server_num=$1

# create files for pid
>> .pid
# create log dir
mkdir -p log

# start all agent servers
for ((i=0; i<bidder_server_num; i++)); do
    port=$((base_port + i))
    python main.py --role server --hosts ${host_name} --base-port ${port} > log/${port}.log 2>&1 &
    echo $! >> .pid
    echo "Started agent server on ${host_name}:${port} with PID $!"
done

echo "All servers started"