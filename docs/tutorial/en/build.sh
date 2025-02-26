#!/bin/bash

set -e

# Generate the API rst files
sphinx-apidoc -o source/build_api ../../../src/agentscope -t ../_templates -e

# Build the html
sphinx-build -M html source build