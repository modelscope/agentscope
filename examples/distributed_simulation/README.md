# Distributed Large Scale Simulation

> **WARNING:**
> **This example will consume a huge amount of tokens.**
> **Using paid model API with this example can introduce a high cost.**
> **Users with powerful GPUs (A800 or better) can use local inference services (such as vLLM) to run this example,**
> **while CPU inference services such as ollama is not recommended.**

This example is a large scale simulation to demonstrate the scalability of AgentScope's distributed mode. From this example, you can learn:

- How to run a large number of agent servers in a GPU cluster.
- How to connect to those agent servers and run a huge number of agents in them.

> Based on this example, we deploy 64,000 agents evenly on 4 machines, and each machine has 64 CPU cores and 8 A100 GPUs. The running time is about 30s (excluding initialization time).

## Background

This example simulates the following scenario:

A large number of people participate in a game in which the moderator asks each participant to provide a number between 0 and N. The moderator will calculate the average of all numbers and announce it. The person closest to the average will win.

## Tested Models

Only vLLM local inference service is tested for this example.

This example will consume a huge amount of tokens. Please do not use model API that requires payment.

## Prerequisites

- The distribute version of AgentScope is installed
- Use MacOS or Linux (Windows requires some modifiations to the scripts)
- [Optional] Have multiple machines with powerful GPUs (A800 or better) and install [vLLM](https://github.com/vllm-project/vllm)

## How to Run

### Step 1: start local inference service

> If you only have one machine and don't have a powerful GPU (A800 or better), you can ignore this step.

You can use `start_vllm.sh` to start vllm inference services on each of your machines.
Before running the script, please set `gpu_num`, `model_path` and `base_port` properly.

- `gpu_num`: number of GPUs for this machine.
- `model_path`: the model checkpoint path.
- `base_port`: The starting point of the port number used by the local inference services.

For example, if `base_port` is `8010` and `gpu_num` is `4`, 4 inference services will be started, and the port numbers are `8010`, `8011`, `8012` and `8013` respectively.

vLLM inference services start slowly, so you need to wait for these servers to actually start before proceeding to the next step.

> The above configuration requires that the model checkpoint can be loaded by a single GPU.
> If you need to use a model that must be loaded by multiple GPUs, you need to modify the script.

### Step 2: start agent server

> If you only have one machine and don't have a powerful GPU, you can just use the default setting of the scripts.

You can use `start_all_server.sh` to start multiple agent servers on each of your machine.
Before running the script, please set `base_port`, `host_name` and `moderator_num` properly.

- `base_port`: The starting point of the port number used by the agent servers.
- `host_name`: The hostname of this machine, and must be accessible to other machines in the cluster (The default value `localhost` is only used for single machine scenario).
- `moderator_num`: Number of moderators. When the number of participants is large, this value needs to be expanded to avoid bottlenecks.

After setting the above values correctly, you can use the script to start multiple agent server on your machine. The following command will start 10 agent servers on your machine with port numbers starting from `base_port` to `base_port + 9`, and will also start `moderator_num` agent servers for moderators with port numbers starting from `base_port + 10` to `base_port + moderator_num + 9`.

```shell
#./start_all_server.sh <number_of_server_per_host>
./start_all_server.sh 10
```

If you have multiple machines, please make sure the `base_port` and `moderator_num` parameters are exactly the same on all machines, and start the same number of agent servers.

### Step 3: run simulation

You can use `run_simulation.sh` to start the simulation.
Before running the script, please set the following setting correctly:

- `base_port`: the base port for agent servers, must be the same as used in Step 2.
- `hosts`: hostnames of all machines. If you only have one machine, use the default value `localhost`.
- `moderator_per_host`: Consistent with `moderator_num` in Step 2.
- `agent_type`: `random` or `llm`. Please use `random` if you don't have local inference service.
- `max_value`: The upper bound of numbers generated in the game.

The command below will run a simulation with 1000 participant agents and evenly distributed those agents to the 10 agent servers started in Step 2.

```shell
#./run_simulation.sh <number_of_server_per_host> <total_number_of_participant>
./run_simulation.sh 10 1000
```

The following is sample output from a single-machine (16 CPU cores) simulation scenario:

```log
2024-04-16 10:31:53.786 | INFO     | agentscope.models:read_model_configs:178 - Load configs for model wrapper: model_1, model_2, model_3, model_4, model_5, model_6, model_7, model_8
2024-04-16 10:31:53.822 | INFO     | agentscope.utils.monitor:_create_monitor_table:343 - Init [monitor_metrics] as the monitor table
2024-04-16 10:31:53.822 | INFO     | agentscope.utils.monitor:_create_monitor_table:344 - Init [monitor_metrics_quota_exceeded] as the monitor trigger
2024-04-16 10:31:53.822 | INFO     | agentscope.utils.monitor:__init__:313 - SqliteMonitor initialization completed at [./runs/run_20240416-103153_h0xuo5/agentscope.db]
2024-04-16 10:31:53.829 | INFO     | __main__:run_main_process_new:106 - init 1000 random participant agents...
2024-04-16 10:31:53.829 | INFO     | __main__:run_main_process_new:139 - init 4 moderator agents...
2024-04-16 10:31:54.211 | INFO     | __main__:run_main_process_new:163 - [init takes 0.38274645805358887 s]
Moderator: The average value is 49.561 [takes 4.197571277618408 s]
```
