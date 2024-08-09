#!/bin/bash


cd /mnt/data/panxuchen.pxc/distributed_simulation


ps -ef | grep "participant" | grep -v grep | awk '{print $2}' | xargs kill -9

sleep 1

rm -rf /root/distributed_simulation/runs

echo "remote old runs"