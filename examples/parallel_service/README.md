# Parallel Service Example

This example presents a methodology for converting the `service` function into a distributed version capable of running in parallel.

## Background

The original implementation of the `service` functions was executed locally. In scenarios where multiple independent `service` functions need to be executed concurrently, such as executing `web_digest` followed by the retrieved results on `google_search` to produce a summary of relevant webpage content, serial execution can lead to inefficiencies due to waiting for each result sequentially.

In this example, we will illustrate how to transform the `web_digest` function into a distributed version, enabling it to operate in a parallel fashion. This enhancement will not only improve the parallelism of the process but also significantly reduce the overall runtime.


## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- `dashscope_chat` with `qwen-turbo`
- gpt-4o


## Prerequisites

- Install the lastest version of AgentScope by

```bash
git clone https://github.com/modelscope/agentscope
cd agentscope
pip install -e .\[distribute\]
```

- Prepare an OpenAI API key or Dashscope API key

- For search engines, this example now supports two types of search engines, google and bing. The configuration items for each of them are as follows:

    - google
        - `api-key`
        - `cse-id`
    - bing
        - `api-key`


## Running the Example

First fill your OpenAI API key or Dashscope API key in `parallel_service.py` file.
The following are the parameters required to run the script:

- `--use-dist`: Enable distributed mode.
- `--search-engine`: The search engine used, currently supports `google` or `bing`.
- `--api-key`: API key for google or bing.
- `--cse-id`: CSE id for google (If you use bing, ignore this parameter).

For instance, if you wish to execute an example of `web_digest` sequentially, please use the following command:

```bash
python parallel_service.py --api-key [google-api-key] --cse-id [google-cse-id]
```

Conversely, if you intend to execute an example of parallel `web_digest`, you may use the following command:

```bash
python parallel_service.py --api-key [google-api-key] --cse-id [google-cse-id] --use-dist
```

Here is an example output of `python parallel_service.py --api-key [google-api-key] --cse-id [google-cse-id]`:

```
2024-09-06 11:25:10.435 | INFO     | agentscope.manager._model:load_model_configs:115 - Load configs for model wrapper: dash
2024-09-06 11:25:10.436 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
User input: Aside from the Apple Remote, what other device can control the program Apple Remote was originally designed to interact with?
User: Aside from the Apple Remote, what other device can control the program Apple Remote was originally designed to interact with?
...
system: You have failed to generate a response in the maximum iterations. Now generate a reply by summarizing the current situation.
assistant: Based on the search results, the iOS Remote Control for Apple TV is an alternative to the Apple Remote for interacting with devices like Apple TV. However, it has received mixed reviews, with some users suggesting adjustments to the touchpad sensitivity or using specific navigation techniques to improve the experience. If Zwift users are unsatisfied with the current remote functionality, they might consider exploring other platforms or hardware.
2024-09-06 11:27:24.135 | INFO     | __main__:main:184 - Time taken: 115.18411183357239 seconds
```

Another example output of `python parallel_service.py --api-key [google-api-key] --cse-id [google-cse-id] --use-dist`:

```
2024-09-06 11:36:55.235 | INFO     | agentscope.manager._model:load_model_configs:115 - Load configs for model wrapper: dash
2024-09-06 11:36:55.237 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
User input: Aside from the Apple Remote, what other device can control the program Apple Remote was originally designed to interact with?
User: Aside from the Apple Remote, what other device can control the program Apple Remote was originally designed to interact with?
...
system: You have failed to generate a response in the maximum iterations. Now generate a reply by summarizing the current situation.
assistant: Thought: The search has been conducted, but there seems to be an issue with retrieving the relevant tags. Despite this, I have found an affordable alternative to the Apple Remote called the aarooGo Remote Control, which can control Apple TV. This device is compatible with all Apple TV models and offers basic controls like power, volume, and mute without a touchpad, making it a cost-effective solution for controlling Apple TV.

Response: After conducting a search, I found an affordable alternative to the Apple Remote called the aarooGo Remote Control. This device can control Apple TV and is compatible with all Apple TV models. It offers basic controls like power, volume, and mute without a touchpad, making it a cost-effective solution for controlling your Apple TV.
2024-09-06 11:38:05.459 | INFO     | __main__:main:182 - Time taken: 63.02961325645447 seconds
```