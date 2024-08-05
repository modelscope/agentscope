(207-monitor-en)=

# Monitor

AgentScope supports to monitor the usage of model APIs.
Users can disable the monitor by setting `use_monitor=False` in `agentscope.init` if they don't need this feature.

To monitor the detailed usage, we provide two functions, `agentscope.state_dict` and `agentscope.print_llm_usage`,
to get the current state of the monitor and print the usage of the model APIs respectively.

The example code is as follows:

```python

import agentscope

# ...

# Get the current state of the monitor
state_dict = agentscope.state_dict()

# Print the usage of the model APIs
agentscope.print_llm_usage()
```

An example `state_dict` is shown as follows:

```json
{
    "project": "zSZ0pO",
    "name": "7def6u",
    "run_id": "run_20240731-104527_7def6u",
    "pid": 24727,
    "timestamp": "2024-07-31 10:45:27",
    "disable_saving": false,
    "file": {
        "save_log": false,
        "save_code": false,
        "save_api_invoke": false,
        "base_dir": null,
        "run_dir": "/xxx/runs/run_20240731-104527_7def6u",
        "cache_dir": "/Users/xxx/.cache/agentscope"
    },
    "model": {
        "model_configs": {}
    },
    "logger": {
        "level": "INFO"
    },
    "studio": {
        "active": false,
        "studio_url": null
    },
    "monitor": {
        "use_monitor": true,
        "path_db": "/.../runs/run_20240731-104527_7def6u/agentscope.db"
    }
}
```

- When calling `agentscope.print_llm_usage`, AgentScope will print model usages as follows:

```text
2024-08-05 15:21:54.889 | INFO     | agentscope.manager._monitor:_print_table:117 - Text & Embedding Model:
2024-08-05 15:21:54.889 | INFO     | agentscope.manager._monitor:_print_table:127 - |  MODEL NAME | TIMES | PROMPT TOKENS | COMPLETION TOKENS | TOTAL TOKENS |
2024-08-05 15:21:54.890 | INFO     | agentscope.manager._monitor:_print_table:127 - | gpt-4-turbo |   1   |       15      |         20        |      35      |
2024-08-05 15:21:54.890 | INFO     | agentscope.manager._monitor:_print_table:127 - |    gpt-4o   |   1   |       43      |         34        |      77      |
2024-08-05 15:21:54.890 | INFO     | agentscope.manager._monitor:_print_table:127 - |   qwen-max  |   2   |      129      |        172        |     301      |
2024-08-05 15:21:54.890 | INFO     | agentscope.manager._monitor:_print_table:117 - Image Model:
2024-08-05 15:21:54.890 | INFO     | agentscope.manager._monitor:_print_table:127 - | MODEL NAME |     RESOLUTION     | TIMES | IMAGE COUNT |
2024-08-05 15:21:54.891 | INFO     | agentscope.manager._monitor:_print_table:127 - |  dall-e-3  |    hd_1024*1024    |   1   |      2      |
2024-08-05 15:21:54.891 | INFO     | agentscope.manager._monitor:_print_table:127 - |  dall-e-3  | standard_1024*1024 |   2   |      7      |
2024-08-05 15:21:54.891 | INFO     | agentscope.manager._monitor:_print_table:127 - |  qwen-vl   |     1024*1024      |   1   |      4      |
```

- You can also get the usage of the model APIs in JSON format as follows:

```python
# print(json.dumps(agentscope.print_llm_usage(), indent=4))
{
    "text_and_embedding": [
        {
            "model_name": "gpt-4-turbo",
            "times": 1,
            "prompt_tokens": 15,
            "completion_tokens": 20,
            "total_tokens": 35
        },
        {
            "model_name": "gpt-4o",
            "times": 1,
            "prompt_tokens": 43,
            "completion_tokens": 34,
            "total_tokens": 77
        },
        {
            "model_name": "qwen-max",
            "times": 2,
            "prompt_tokens": 129,
            "completion_tokens": 172,
            "total_tokens": 301
        }
    ],
    "image": [
        {
            "model_name": "dall-e-3",
            "resolution": "hd_1024*1024",
            "times": 1,
            "image_count": 2
        },
        {
            "model_name": "dall-e-3",
            "resolution": "standard_1024*1024",
            "times": 2,
            "image_count": 7
        },
        {
            "model_name": "qwen-vl",
            "resolution": "1024*1024",
            "times": 1,
            "image_count": 4
        }
    ]
}
```


[[Return to the top]](#207-monitor-en)
