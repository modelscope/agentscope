# Multi-Agent Copilot Search

## Introduction

This example application converts the user's questions into keywords to call the search engine, and then retrieves a series of web pages to find answers. It involves three types of Agents, namely the UserAgent for the user, the SearcherAgent responsible for searching, and the AnswererAgent responsible for retrieves web pages.

There are many web page links returned by the search engine. To improve performance, multiple instances of AnswererAgent need to run together. However, with the traditional single-process mode, even if there are multiple AnswererAgent instances, they can only obtain web page and answer questions one by one on a single CPU.

But, with AgentScope's distributed mode, you can automatically make these AnswererAgent instances run at the same time to improve performance.

From this example, you can learn:

- how to run multiple agents in different processes,
- how to make multiple agents run in parallel automatically,
- how to convert a single-process version AgentScope application into a multi-processes version.

## How to Run

### Step 0: Install AgentScope distributed version

This example requires the distributed version of AgentScope.

```bash
# On windows
pip install -e .[distribute]
# On mac / linux
pip install -e .\[distribute\]
```

### Step 1: Prepare your model and search engine API configuration

For the model configuration, please fill your model configurations in `configs/model_configs.json`.
Here we give an example.

> Dashscope models, e.g. qwen-max, and openai models, e.g. gpt-3.5-turbo and gpt-4 are tested for this example.
> Other models may require certain modification to the code.

```json
[
    {
        "config_name": "my_model",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
        "api_key": "your_api_key",
        "generate_args": {
            "temperature": 0.5
        },
        "messages_key": "input"
    }
]
```

For search engines, this example now supports two types of search engines, google and bing. The configuration items for each of them are as follows:

- google
  - `api-key`
  - `cse-id`
- bing
  - `api-key`

### Step 2: Run the example

Use the `main.py` script to run the example. The following are the parameters required to run the script:

- `--num-workers`: The number of AnswererAgent instances.
- `--use-dist`: Enable distributed mode.
- `--search-engine`: The search engine used, currently supports `google` or `bing`.
- `--api-key`: API key for google or bing.
- `--cse-id`: CSE id for google (If you use bing, ignore this parameter).

For example, if you want to start the example application in distributed mode with 10 AnswererAgents and use the bing search engine, you can use the following command

```shell
python main.py --num-workers 10 --search-engine bing --api-key xxxxx --use-dist
```

And if you want to run the above case in a traditional single-process mode, you can use the following command.

```shell
python main.py --num-workers 10 --search-engine bing --api-key xxxxx
```

You can ask the same question in both modes to compare the difference in runtime. For examples, answer a question with 10 workers only takes 13.2s in distributed mode, while it takes 51.3s in single-process mode.
