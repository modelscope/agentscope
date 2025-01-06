#!/bin/bash

if [ -z "$DASHSCOPE_API_KEY" ]; then
  echo "DASHSCOPE_API_KEY is not set" > debug.txt
else
  echo "DASHSCOPE_API_KEY is set" > debug.txt
fi

sphinx-build -M html source build