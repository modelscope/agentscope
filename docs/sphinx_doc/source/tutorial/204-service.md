(204-service)=

# Enhancing Agent Capabilities with Service Functions

**Service functions**, often referred to simply as **Service**, constitute a versatile suite of utility tools that can be used to enhance the functionality of agents. A service is designed to perform a specific task like web search, code interpretation, or file processing. Services can be invoked by agents and other components for reuse across different scenarios.

## ServiceResponse

The design behind `Service` distinguishes them from typical Python functions. In scenarios where execution is failed, service functions do not raise exceptions within the program. Instead, they return a `ServiceResponse` (a sub-class of dict).

```python
def demo_service() -> ServiceResponse:
    #do some specifc actions
    # ......
    res = ServiceResponse({status=status, content=content})
    return res


class ServiceResponse(dict):
    """Used to wrap the execution results of the services"""
    # ... [code omitted for brevity]

    def __init__(
        self,
        status: ServiceExecStatus,
        content: Any,
    ):
        self.status = status
        self.content = content
```

This object encapsulates `status` of the execution (`SUCCESS` or `ERROR`), which can indicate success or failure, and the `content`, which can either be the output of a successful execution or the error stack from a failure.

Here's why this design is beneficial:

- **Error Handling**: `Service` and `ServiceResponse` allows agents to flexibly handle errors. An agent can check the status of the response and decide on the next steps, whether to retry the operation, use fallback logic, or analyze the error stack and choose an appropriate strategy to make improvements.
- **Consistency**: Service functions provide a consistent interface for both successful outcomes and errors. This consistency simplifies the interaction model for agents that use these services.

## Overview of Service Functions

Below is a table outlining various service functions categorized by their primary domain. These services offer a range of capabilities to agents.

| Service Scenario  | Service Function Name | Description                                                  |
| --------------- | --------------------- | ------------------------------------------------------------ |
| Code            | `execute_python_code` | Execute a string of Python code, optionally inside a Docker container. |
| Retrieval       | `retrieve_from_list`  | Retrieve specific items from a list based on given criteria. |
| SQL Query       | `query_mysql`         | Execute a SQL query against a MySQL database and return results. |
|                 | `query_sqlite`        | Execute a SQL query against a SQLite database and return results. |
|                 | `query_mongodb`       | Perform a query or operation against a MongoDB collection.   |
| Text Processing | `summarization`       | Summarize a block of text to highlight the main points with LLM. |
| Web Search      | `web_search`          | Perform a web search using a specified search engine (currently supports Google and Bing). |
| File            | `create_file`         | Create a new file at a specified path with optional initial content. |
|                 | `delete_file`         | Delete a file specified by the file path.                    |
|                 | `move_file`           | Move or rename a file from one path to another.              |
|                 | `create_directory`    | Create a new directory at a specified path.                  |
|                 | `delete_directory`    | Delete a directory and all of its contents.                  |
|                 | `move_directory`      | Move or rename a directory from one path to another.         |
|                 | `read_text_file`      | Read and return the contents of a text file.                 |
|                 | `write_text_file`     | Write text content to a file at a specified path.            |
|                 | `read_json_file`      | Read and parse the contents of a JSON file.                  |
|                 | `write_json_file`     | Serialize a Python object to JSON and write it to a file.    |
| *More to Come*  |                       | Additional service functions are being developed and will be added to enhance the capabilities of AgentScope further. |

For details about each Service Function, please consult the API references, where the docstrings provide comprehensive information about the parameters, expected input formats, return types, and any additional options that can modify the behavior of the Service Function.

## Usage

In AgentScope, each Service Function comes with a meticulously crafted docstring and demonstrative test functions that provide detailed instructions on how to utilize it. To enhance the capabilities of your agents with these services, you can craft prompts for LLM to generate parameters for Service:

By composing appropriate prompts that align with the information detailed in the Service Functions' docstrings, you can guide an LLM to generate responses that match the required parameters of a `Service`.

```python
import json
import inspect
from agentscope.service import ServiceResponse
from agentscope.agents import AgentBase


def create_file(file_path: str, content: str = "") -> ServiceResponse:
    """
    Create a file and write content to it.

    Args:
        file_path (str): The path where the file will be created.
        content (str): Content to write into the file.

    Returns:
        ServiceResponse: where the boolean indicates success, and the
        str contains an error message if any, including the error type.
    """
    # ... [code omitted for brevity]


class YourAgent(AgentBase):
    # ... [code omitted for brevity]

    def reply(self, x: dict = None) -> dict:
        # ... [code omitted for brevity]

        # Construct the prompt for the agent to provide parameters in JSON
        # format
        prompt = (
            f"To complete the user request\n```{x['content']}```\n"
            "Please provide the necessary parameters in JSON format for the "
            "function:\n"
            f"Function: {create_file.__name__}\n"
            "Description: Create a file and write content to it.\n"
        )

        # Add details about the function parameters
        sig = inspect.signature(create_file)
        parameters = sig.parameters.items()
        params_prompt = "\n".join(
            f"- {name} ({param.annotation.__name__}): "
            f"{'(default: ' + json.dumps(param.default) + ')'if param.default is not inspect.Parameter.empty else ''}"
            for name, param in parameters
        )
        prompt += params_prompt

        # Get the model response
        model_response = self.model(prompt).text

        # Parse the model response and call the create_file function
        # Additional extraction functions might be necessary
        try:
            kwargs = json.loads(model_response)
            create_file(**kwargs)
        except:
            # Error handling
            pass

        # ... [code omitted for brevity]
```

[[Return to the top]](#enhancing-agent-capabilities-with-service-functions)
