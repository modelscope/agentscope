(207-monitor-zh)=

# 监控

AgentScope 支持模型 API 使用情况的监控。
用户可以通过在 `agentscope.init` 中设置 `use_monitor=False` 来禁用监控功能。

AgentScope 提供了 `agentscope.state_dict` 和 `agentscope.print_llm_usage` 两个函数，用于获取当前 AgentScope 状态和打印模型 API 的使用情况。

示例代码如下：

```python

import agentscope

# ...

# 获取当前监控状态
state_dict = agentscope.state_dict()

# 打印模型 API 的使用情况
agentscope.print_llm_usage()
```

以下是一个 `state_dict` 的示例：

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

- 调用 `agentscope.print_llm_usage` 时，AgentScope 将打印模型使用情况如下：

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

- 同时还可以获得 JSON 格式的模型 API 使用情况，如下所示：

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

[[Return to the top]](#207-monitor-zh)
