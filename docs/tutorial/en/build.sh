#!/bin/bash

echo "Start ..."
if [ -n "$DASHSCOPE_API_KEY" ]; then
    echo "DASHSCOPE_API_KEY is set and not empty"
    echo "DASHSCOPE_API_KEY=$DASHSCOPE_API_KEY"
else
    echo "DASHSCOPE_API_KEY is not set or is empty"
fi
echo "Done"

sphinx-build -M html source build