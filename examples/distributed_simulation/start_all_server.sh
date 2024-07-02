#!/bin/bash

# default values
base_port=12330
host_name="localhost"
moderator_num=4

# get number of server
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <number-of-server-for-participant>"
    exit 1
fi

participant_server_num=$1

# create files for pid
>> .pid
# create log dir
mkdir -p log

# start all agent servers
for ((i=0; i<(participant_server_num + moderator_num); i++)); do
    port=$((base_port + i))
    python main.py --role participant --hosts ${host_name} --base-port ${port} > log/${port}.log 2>&1 &
    echo $! >> .pid
    echo "Started agent server on ${host_name}:${port} with PID $!"
done

echo "All servers started"