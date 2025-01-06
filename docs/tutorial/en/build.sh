#!/bin/bash

echo "Start ..."
python -c "import os; print('!!!' + os.environ['DASHSCOPE_API_KEY'] + '+++')"
echo "Done"

sphinx-build -M html source build