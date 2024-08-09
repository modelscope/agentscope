#!/bin/bash

IFS=',' read -r -a SERVERS <<< "$1"

for SERVER in "${SERVERS[@]}"; do
    echo "Stopping server on $SERVER"
    ssh root@"$SERVER" 'zsh -s --' < /mnt/data/panxuchen.pxc/distributed_simulation/remote_stop.sh "$SERVER"
done

echo "All servers stopped."