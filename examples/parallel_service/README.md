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
2024-09-04 17:53:11.758 | INFO     | agentscope.manager._model:load_model_configs:115 - Load configs for model wrapper: dash
2024-09-04 17:53:12.227 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
2024-09-04 17:53:22.262 | WARNING  | agentscope.service.web.web_digest:load_web:149 - HTTPSConnectionPool(host='en.wikipedia.org', port=443): Max retries exceeded with url: /wiki/Journey_to_the_West (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x312feadb0>, 'Connection to en.wikipedia.org timed out. (connect timeout=5)'))
2024-09-04 17:53:22.895 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
2024-09-04 17:53:39.086 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
2024-09-04 17:53:49.254 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
2024-09-04 17:53:50.603 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
2024-09-04 17:53:59.729 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
2024-09-04 17:54:00.785 | WARNING  | agentscope.service.web.web_digest:load_web:149 - HTTPSConnectionPool(host='x.com', port=443): Max retries exceeded with url: /mcclanjr81 (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x16d348a70>: Failed to establish a new connection: [Errno 9] Bad file descriptor'))
2024-09-04 17:54:00.978 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
2024-09-04 17:54:07.338 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
len(execute_results) = 10, duration = 55.64 s
2024-09-04 17:54:07.872 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
```

Another example output of `python parallel_service.py --api-key [google-api-key] --cse-id [google-cse-id] --use-dist`:

```
2024-09-04 17:54:22.810 | INFO     | agentscope.manager._model:load_model_configs:115 - Load configs for model wrapper: dash
2024-09-04 17:54:26.427 | INFO     | agentscope.rpc.rpc_meta:register_class:160 - Class with name [RpcService] already exists.
2024-09-04 17:54:26.436 | INFO     | agentscope.server.launcher:_setup_agent_server_async:234 - agent server [Y74mXkmO] at localhost:50369 started successfully
2024-09-04 17:54:26.436 | INFO     | agentscope.server.launcher:_launch_in_sub:450 - Launch agent server at [localhost:50369] success
2024-09-04 17:54:26.449 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
2024-09-04 17:54:26.450 | INFO     | agentscope.server.servicer:create_agent:231 - create agent instance <RpcService>[f4632be278874121a79fe8b6671f265c]
2024-09-04 17:54:26.460 | WARNING  | agentscope.service.web.web_digest:load_web:149 - HTTPSConnectionPool(host='x.com', port=443): Max retries exceeded with url: /mcclanjr81 (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x312592f90>: Failed to establish a new connection: [Errno 9] Bad file descriptor'))
2024-09-04 17:54:26.746 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
2024-09-04 17:54:26.766 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
2024-09-04 17:54:26.791 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
2024-09-04 17:54:26.791 | WARNING  | agentscope.service.web.web_digest:load_web:140 - Fail to load web page, status code 403
2024-09-04 17:54:27.221 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
2024-09-04 17:54:27.414 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
2024-09-04 17:54:28.099 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
2024-09-04 17:54:30.540 | INFO     | agentscope.service.web.web_digest:parse_html_to_text:172 - extracting text information from tags: ['p', 'div', 'h1', 'li']
2024-09-04 17:54:36.492 | WARNING  | agentscope.service.web.web_digest:load_web:149 - HTTPSConnectionPool(host='en.wikipedia.org', port=443): Max retries exceeded with url: /wiki/Journey_to_the_West (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x311c5af60>, 'Connection to en.wikipedia.org timed out. (connect timeout=5)'))
len(execute_results) = 10, duration = 13.80 s
2024-09-04 17:54:40.452 | INFO     | agentscope.server.launcher:_setup_agent_server_async:242 - Stopping agent server at [localhost:50369]
2024-09-04 17:54:41.448 | INFO     | agentscope.server.launcher:_setup_agent_server_async:246 - agent server [Y74mXkmO] at localhost:50369 stopped successfully
```