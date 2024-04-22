#!/bin/bash
sphinx-apidoc -f -o en/source ../../src/agentscope -t template
sphinx-apidoc -f -o zh_CN/source ../../src/agentscope -t template
make clean all