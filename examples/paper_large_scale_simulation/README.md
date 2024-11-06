# Very Large-Scale Multi-Agent Simulation in AgentScope

> **WARNING:**
>
> **This example will consume a huge amount of tokens.**
> **Using paid model API with this example can introduce a high cost.**
> **Users with powerful GPUs (A100 or better) can use local inference services (such as vLLM) to run this example,**

The code under this folder is the experiment of the paper [Very Large-Scale Multi-Agent Simulation in AgentScope](https://arxiv.org/abs/2407.17789).

In the experiment, we set up a large number of agents to participate in the classic game "guess the 2/3 of the average", where each agent reports a real number between 0 and 100 and the agent who reports a number closest to 2
3 of the average of all the reported numbers wins the game.

## Tested Models

Only vLLM local inference service is tested for this example.

This example will consume a huge amount of tokens. Please do not use model API that requires payment.

## Prerequisites

- Have multiple machines (Linux system) with powerful GPUs (A100 or better)
- The distribute version of AgentScope is installed on all machines.
- The v0.4.3 or higher versions of [vLLM](https://github.com/vllm-project/vllm) is installed on all machines.

## Usage

## How to Run

### Step 1: start local inference service

> If you only have one machine and don't have a powerful GPU (A800 or better), you can ignore this step.

You can use `start_vllm.sh` to start vllm inference services on each of your machines.
Before running the script, please set `gpu_num`, `model_path`, `gpu_per_model` and `base_port` properly.

- `gpu_num`: number of GPUs for this machine.
- `model_path`: the model checkpoint path.
- `gpu_per_model`: number of GPUs required for each model
- `base_port`: the starting point of the port number used by the local inference services.

For example, if `base_port` is `8010`, `gpu_num` is `8` and `gpu_per_model` is `4`, 2 inference services will be started, and the port numbers are `8010`, `8014` respectively.

vLLM inference services start slowly, so you need to wait for these servers to actually start before proceeding to the next step.

> The above configuration requires that the model checkpoint can be loaded by a single GPU.
> If you need to use a model that must be loaded by multiple GPUs, you need to modify the script.

### Step 2: Configure the Experiment

Modify the following files according to your environment:

- `configs/model_configs.json`: set the model configs for your experiment. Note that the `config_name` field should follow the format `{model_name}_{model_per_machine}_{model_id}`, where `model_name` is the name of the model, `model_per_machine` is the number of models per machine, and `model_id` is the id of the model (starting from 1).

- `configs/experiment.csv`: set the test cases for your experiment.

- `scripts/start_all_server.sh`: activate your python environment properly in this script.

### Step 3: Run the Experiment

Suppose you have 4 machines whose hostnames are `worker1`, `worker2`, `worker3` and `worker4`, respectively, you can run all your experiment cases by the following command:

```
python benchmark.py -name large_scale -config experiment --hosts worker1 worker2 worker3 worker4
```

### Step 4: View the Results

All results will be saved in `./result` folder, and organized as follows:

```text
result
`-- <benchmark_name>
    `-- <model_name>
        `-- <settings>
            |-- <timestamp>
            |   |-- result_<round_num>.json  # the raw text result of round <round_num>
            |   `-- result_<round_num>.pdf  # the distribution histogram of round <round_num>
            `-- <timestamp>
                |-- result_<round_num>.json
                `-- result_<round_num>.pdf
```

And during the experiment, you can also view the experiment results on the command line.

```text
2024-08-13 07:24:00.118 | INFO     | participants:_generate_participant_configs:546 - init 100 llm participant agents...
2024-08-13 07:24:00.119 | INFO     | participants:_init_env:595 - init 1 envs...
2024-08-13 07:24:02.560 | INFO     | participants:_init_env:624 - [init takes 2.4416518211364746 s]
Moderator: The average value of round 1 is 19.52 [takes 42.809 s]
Moderator: The average value of round 2 is 15.75 [takes 56.072 s]
Moderator: The average value of round 3 is 13.53 [takes 61.641 s]
Moderator: Save result to ./result/studio/qwen2_72b/1-2-100-1-0.667/2024-08-13-07:26:43
```

```text
2024-08-13 07:35:40.925 | INFO     | participants:_generate_participant_configs:548 - init 100 random participant agents...
2024-08-13 07:35:40.926 | INFO     | participants:_init_env:597 - init 1 envs...
2024-08-13 07:35:41.071 | INFO     | participants:_init_env:626 - [init takes 0.1457688808441162 s]
Moderator: The average value of round 1 is 50.51 [takes 1.139 s]
Moderator: The average value of round 2 is 45.15 [takes 1.143 s]
Moderator: The average value of round 3 is 48.32 [takes 1.134 s]
Moderator: Save result to ./result/studio/random/1-2-100-1-0.667/2024-08-13-07:35:44
```

## References

```
@article{agentscope_simulation,
      title={Very Large-Scale Multi-Agent Simulation in AgentScope},
      author={Xuchen Pan and
              Dawei Gao and
              Yuexiang Xie
              and Yushuo Chen
              and Zhewei Wei and
              Yaliang Li and
              Bolin Ding and
              Ji-Rong Wen and
              Jingren Zhou},
      journal = {CoRR},
      volume  = {abs/2407.17789},
      year    = {2024},
}
```
