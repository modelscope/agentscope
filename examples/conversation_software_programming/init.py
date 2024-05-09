import agentscope
agentscope.init(model_configs=[
    {
        "model_type": "dashscope_chat",
        "config_name": "qwen",

        "model_name": "qwen-max",
        "api_key": "sk-7cee068707fe4885890ee272c8b14175"
    },
    {
        "model_type": "post_api_chat",
        "config_name": "gpt-4",

        "api_url": "https://api.mit-spider.alibaba-inc.com/chatgpt/api/ask",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjIyNTE4NiIsInBhc3N3b3JkIjoiMjI1MTg2IiwiZXhwIjoyMDA2OTMzNTY1fQ.wHKJ7AdJ22yPLD_-1UHhXek4b7uQ0Bxhj_kJjjK0lRM"
        },
        "json_args": {
            "model": "gpt-4",
            "temperature": 0.0,
        },
        "messages_key": "messages"
    },
    {
        "model_type": "ollama_chat",
        "config_name": "ollama",

        "model_name": "llama2",
    },
])