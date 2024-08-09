#!/bin/bash

if [ ! -f .pid ]; then
    echo "PID file not found. Are the servers running?"
    exit 1
fi

while read pid; do
    kill -9 $pid
    if [ $? -eq 0 ]; then
        echo "Killed server with PID $pid"
    else
        echo "Failed to kill server with PID $pid"
    fi
done < .pid

rm .pid

echo "All servers stopped."