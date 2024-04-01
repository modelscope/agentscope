# Distributed Basic

This example run a assistant agent and a user agent as seperate processes and use rpc to communicate between them.

Before running the example, please install the distributed version of Agentscope, fill in your model configuration correctly in `configs/model_configs.json`, and modify the `model_config_name` field in `distributed_dialog.py` accordingly.

Then, use the following command to start the assistant agent.

```
cd examples/distributed
python distributed_dialog.py --role assistant --assistant-host localhost --assistant-port 12010
# Please make sure the port is available.
# If the assistant agent and the user agent are started on different machines,
# please fill in the ip address of the assistant agent in the host field
```

Then, run the user agent.

```
python distributed_dialog.py --role user --assistant-host localhost --assistant-port 12010
# If the assistant agent is started on another machine,
# please fill in the ip address of the assistant agent in the host field
```

Now, you can chat with the assistant agent using the command line.
