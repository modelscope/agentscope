#!/bin/bash
sphinx-apidoc -f -o en/source ../../src/agentscope -t template -e
sphinx-apidoc -f -o zh_CN/source ../../src/agentscope -t template -e
make clean all