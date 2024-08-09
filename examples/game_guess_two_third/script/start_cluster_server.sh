#!/bin/bash

IFS=',' read -r -a SERVERS <<< "$1"

participant_server_num=$2
moderator_num=$3

for SERVER in "${SERVERS[@]}"; do
    echo "Starting server on $SERVER"
    ssh root@"$SERVER" 'zsh -s --' < /mnt/data/panxuchen.pxc/distributed_simulation/remote_start.sh $participant_server_num $moderator_num $SERVER &
done

echo "All servers started."