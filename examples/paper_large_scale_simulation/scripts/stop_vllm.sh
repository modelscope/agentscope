#!/bin/bash

if [ ! -f .vllm_pid ]; then
    echo "PID file not found. Are the servers running?"
    exit 1
fi

while read pid; do
    kill -9 $pid
    if [ $? -eq 0 ]; then
        echo "Killed vllm server with PID $pid"
    else
        echo "Failed to kill vllm server with PID $pid"
    fi
done < .vllm_pid

rm .vllm_pid

echo "All vllm servers stopped."