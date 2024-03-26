(204-service-en)=

# Service

Service function is a set of multi-functional utility tools that can be
used to enhance the capabilities of agents, such as executing Python code,
web search, file operations, and more.
This tutorial provides an overview of the service functions available in
AgentScope and how to use them to enhance the capabilities of your agents.

## Built-in Service Functions

The following table outlines the various Service functions by type. These functions can be called using `agentscope.service.{function_name}`.

| Service Scene | Service Function Name | Description                                                |
| -------------- | --------------------- | ------------------------------------------------------------ |
| Code           | `execute_python_code` | Execute a piece of Python code, optionally inside a Docker container. |
| Retrieval      | `retrieve_from_list`  | Retrieve a specific item from a list based on given criteria. |
| SQL Query      | `query_mysql`         | Execute SQL queries on a MySQL database and return results. |
|                | `query_sqlite`        | Execute SQL queries on a SQLite database and return results. |
|                | `query_mongodb`       | Perform queries or operations on a MongoDB collection. |
| Text Processing | `summarization`       | Summarize a piece of text using a large language model to highlight its main points. |
| Web Search      | `web_search`          | Perform a web search using a specified search engine (currently supports Google and Bing). |
| File           | `create_file`         | Create a new file at a specified path, optionally with initial content. |
|                | `delete_file`         | Delete a file specified by a file path.       |
|                | `move_file`           | Move or rename a file from one path to another. |
|                | `create_directory`    | Create a new directory at a specified path. |
|                | `delete_directory`    | Delete a directory and all its contents.     |
|                | `move_directory`      | Move or rename a directory from one path to another. |
|                | `read_text_file`      | Read and return the content of a text file.    |
|                | `write_text_file`     | Write text content to a file at a specified path. |
|                | `read_json_file`      | Read and parse the content of a JSON file. |
|                | `write_json_file`     | Serialize a Python object to JSON and write to a file. |
| *More services coming soon* |                       | More service functions are in development and will be added to AgentScope to further enhance its capabilities. |

About each service function, you can find detailed information in the
[API document](https://modelscope.github.io/agentscope/).

## How to use Service Functions

AgentScope provides two service classes for Service functions,
`ServiceFactory` and `ServiceResponse`.

- `ServiceFactory` is mainly used to convert general Python functions into
  a form that can be directly used by large-scale models, and automatically
  generate function descriptions in JSON schema format.
- `ServiceResponse` is a subclass of a dictionary, providing a unified call
  result interface for all Service functions.

### About Service Factory

The tools used by agents are generally of the function type. Developers
need to prepare functions that can be called directly by large models, and
provide descriptions of the functions. However, general functions often
require developers to provide some parameters (such as keys, usernames,
specific URLs, etc.), and then the large model can use them. At the same
time, it is also a tedious task to generate specific format descriptions
for multiple functions.

To tackle the above problems, AgentScope introduces `ServiceFactory`. For a
given Service function, it allows developers to specify some parameters,
generate a function that can be called directly by large models, and
automatically generate function descriptions based on the Docstring. Take
the Bing web search function as an example.

```python
def bing_search(
    question: str,
    api_key: str,
    num_results: int = 10,
    **kwargs: Any,
) -> ServiceResponse:
    """
    Search question in Bing Search API and return the searching results

    Args:
        question (`str`):
            The search query string.
        api_key (`str`):
            The API key provided for authenticating with the Bing Search API.
        num_results (`int`, defaults to `10`):
            The number of search results to return.
        **kwargs (`Any`):
            Additional keyword arguments to be included in the search query.
            For more details, please refer to
            https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/query-parameters

    [omitted for brevity]
    """
```

In the above function, `question` is the field filled in by the large model,
while `api_key` and `num_results` are the parameters that the developer needs to provide.
We use the `get` function of `ServiceFactory` to process it:

```python
from agentscope.service import ServiceFactory

func, func_intro = ServiceFactory.get(
    bing_search,
    api_key="xxx",
    num_results=3)
```

In the above code, the `func` generated by ServiceFactory is equivalent to the following function:

```python
def bing_search(question: str) -> ServiceResponse:
    """
    Search question in Bing Search API and return the searching results

    Args:
        question (`str`):
            The search query string.
    """
    return bing_search(question, api_key="xxx", num_results=3)
```

The generated JSON schema format is as follows, which can be directly used
in the `tools` field of the OpenAI API.

```python
# print(func_intro)
{
    "type": "function",
    "function": {
        "name": "bing_search",
        "description": "Search question in Bing Search API and return the searching results",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The search query string."
                }
            },
            "required": [
                "question"
            ]
        }
    }
}
```

**Note**:
The description of the function and arguments are extracted from
its docstring automatically, which should be well-formatted in
**Google style**. Otherwise, their descriptions in the returned
dictionary will be empty.

**Suggestions**:

1. The name of the service function should be self-explanatory,
so that the agent can understand the function and use it properly.
2. The typing of the arguments should be provided when defining
the function (e.g. `def func(a: int, b: str, c: bool)`), so that
the agent can specify the arguments properly.

### About ServiceResponse

`ServiceResponse` is a wrapper for the execution results of the services,
containing two fields, `status` and `content`. When the Service function
runs to completion normally, `status` is `ServiceExecStatus.SUCCESS`, and
`content` is the return value of the function. When an error occurs during
execution, `status` is `ServiceExecStatus.Error`, and `content` contains
the error message.

```python
class ServiceResponse(dict):
    """Used to wrap the execution results of the services"""

    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

    def __init__(
        self,
        status: ServiceExecStatus,
        content: Any,
    ):
        """Constructor of ServiceResponse

        Args:
            status (`ServiceExeStatus`):
                The execution status of the service.
            content (`Any`)
                If the argument`status` is `SUCCESS`, `content` is the
                response. We use `object` here to support various objects,
                e.g. str, dict, image, video, etc.
                Otherwise, `content` is the error message.
        """
        self.status = status
        self.content = content

    # [omitted for brevity]
```

## Example

```python
import json
import inspect
from agentscope.service import ServiceResponse
from agentscope.agents import AgentBase


def create_file(file_path: str, content: str = "") -> ServiceResponse:
    """
    Create a file and write content to it.

    Args:
        file_path (str): The path to the file to be created.
        content (str): The content to be written to the file.

    Returns:
        ServiceResponse: A boolean indicating success or failure, and a
        string containing any error message (if any), including the error type.
    """
    # ... [omitted for brevity]


class YourAgent(AgentBase):
    # ... [omitted for brevity]

    def reply(self, x: dict = None) -> dict:
        # ... [omitted for brevity]

        # construct a prompt to ask the agent to provide the parameters in JSON format
        prompt = (
            f"To complete the user request\n```{x['content']}```\n"
            "Please provide the necessary parameters in JSON format for the "
            "function:\n"
            f"Function: {create_file.__name__}\n"
            "Description: Create a file and write content to it.\n"
        )

        # add detailed information about the function parameters
        sig = inspect.signature(create_file)
        parameters = sig.parameters.items()
        params_prompt = "\n".join(
            f"- {name} ({param.annotation.__name__}): "
            f"{'(default: ' + json.dumps(param.default) + ')'if param.default is not inspect.Parameter.empty else ''}"
            for name, param in parameters
        )
        prompt += params_prompt

        # get the model response
        model_response = self.model(prompt).text

        # parse the model response and call the create_file function
        try:
            kwargs = json.loads(model_response)
            create_file(**kwargs)
        except:
            # Error handling
            pass

        # ... [omitted for brevity]
```

[[Return to Top]](#204-service-en)
