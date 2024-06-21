#!/bin/bash

#PBS -q ai
#PBS -j oe
#PBS -l select=1:ncpus=1:ngpus=1
#PBS -l walltime=24:00:00
#PBS -P 11003841
#PBS -N ToolBenchCaller

cd $PBS_O_WORKDIR || exit $? 

# Load conda commands
eval "$(conda shell.bash hook)"

# Activate conda environment and check if successful
conda activate agentscope
if [ $? -eq 0 ]; then
    echo "Conda environment 'agentscope' activated successfully." > conda_status.txt
else
    echo "Failed to activate conda environment 'agentscope'." > conda_status.txt
    exit 1 # Exit the script if conda activation fails
fi

# Additional commands for debugging
python --version >> debug.txt
pwd >> debug.txt 

# Execute your script and capture output
# python load_finetune_huggingface_model.py >> debug.txt
echo "This is a test file created directly by bash." > bash_test_output.txt

python test.py > test.txt 2>&1

python small_llms_finetuning_ToolBenchCaller.py > ToolBenchCaller.txt 2>&1
