(204-service-en)=

# Tool

Service function is a set of multi-functional utility tools that can be
used to enhance the capabilities of agents, such as executing Python code,
web search, file operations, and more.
This tutorial provides an overview of the service functions available in
AgentScope and how to use them to enhance the capabilities of your agents.

## Built-in Service Functions

The following table outlines the various Service functions by type. These functions can be called using `agentscope.service.{function_name}`.

| Service Scene               | Service Function Name      | Description                                                                                                    |
|-----------------------------|----------------------------|----------------------------------------------------------------------------------------------------------------|
| Code                        | `execute_python_code`      | Execute a piece of Python code, optionally inside a Docker container.                                          |
|                             | `NoteBookExecutor.run_code_on_notebook`                  | Compute Execute a segment of Python code in the IPython environment of the NoteBookExecutor, adhering to the IPython interactive computing style.                                       |
| Retrieval                   | `retrieve_from_list`       | Retrieve a specific item from a list based on given criteria.                                                  |
|                             | `cos_sim`                  | Compute the cosine similarity between two different embeddings.                                                |
| SQL Query                   | `query_mysql`              | Execute SQL queries on a MySQL database and return results.                                                    |
|                             | `query_sqlite`             | Execute SQL queries on a SQLite database and return results.                                                   |
|                             | `query_mongodb`            | Perform queries or operations on a MongoDB collection.                                                         |
| Text Processing             | `summarization`            | Summarize a piece of text using a large language model to highlight its main points.                           |
| Web                         | `bing_search`              | Perform bing search                                                                                            |
|                             | `google_search`            | Perform google search                                                                                          |
|                             | `arxiv_search`             | Perform arXiv search                                                                                           |
|                             | `download_from_url`        | Download file from given URL.                                                                                  |
|                             | `load_web`                 | Load and parse the web page of the specified url (currently only supports HTML).                               |
|                             | `digest_webpage`           | Digest the content of a already loaded web page (currently only supports HTML).
|                             | `dblp_search_publications` | Search publications in the DBLP database
|                             | `dblp_search_authors`      | Search for author information in the DBLP database                                                             |
|                             | `dblp_search_venues`       | Search for venue information in the DBLP database                                                              |
| File                        | `create_file`              | Create a new file at a specified path, optionally with initial content.                                        |
|                             | `delete_file`              | Delete a file specified by a file path.                                                                        |
|                             | `move_file`                | Move or rename a file from one path to another.                                                                |
|                             | `create_directory`         | Create a new directory at a specified path.                                                                    |
|                             | `delete_directory`         | Delete a directory and all its contents.                                                                       |
|                             | `move_directory`           | Move or rename a directory from one path to another.                                                           |
|                             | `read_text_file`           | Read and return the content of a text file.                                                                    |
|                             | `write_text_file`          | Write text content to a file at a specified path.                                                              |
|                             | `read_json_file`           | Read and parse the content of a JSON file.                                                                     |
|                             | `write_json_file`          | Serialize a Python object to JSON and write to a file.                                                         |
| Multi Modality              | `dashscope_text_to_image`  | Convert text to image using Dashscope API.                                                                     |
|                             | `dashscope_image_to_text`  | Convert image to text using Dashscope API.                                                                     |
|                             | `dashscope_text_to_audio`  | Convert text to audio using Dashscope API.                                                                     |
|                             | `openai_text_to_image`     | Convert text to image using OpenAI API
|                             | `openai_edit_image`        | Edit an image based on the provided mask and prompt using  OpenAI API
|                             | `openai_create_image_variation`        | Create variations of an image using  OpenAI API
|                             | `openai_image_to_text` | Convert text to image using OpenAI API
|                             | `openai_text_to_audio` | Convert text to audio using OpenAI API
|                             | `openai_audio_to_text` | Convert audio to text using OpenAI API


| *More services coming soon* |                            | More service functions are in development and will be added to AgentScope to further enhance its capabilities. |

About each service function, you can find detailed information in the
[API document](https://modelscope.github.io/agentscope/).

## How to use Service Functions

AgentScope provides two classes for service functions,
`ServiceToolkit` and `ServiceResponse`.

### About Service Toolkit

The use of tools for LLM usually involves five steps:

1. **Prepare tool functions**. That is, developers should pre-process the
functions by providing necessary parameters, e.g. api key, username,
password, etc.
2. **Prepare instruction for LLM**. A detailed description for these tool
functions are required for the LLM to understand them properly.
3. **Guide LLM how to use tool functions**. A format description for calling
functions is required.
4. **Parse LLM response**. Once the LLM generates a response,
we need to parse it according to above format in the third step.
5. **Call functions and handle exceptions**. Calling the functions, return
the results, and handle exceptions.

To simplify the above steps and improve reusability, AgentScope introduces
`ServiceToolkit`. It can
- register python functions
- generate tool function descriptions in both string and JSON schema format
- generate usage instruction for LLM
- parse the model response, call the tool functions, and handle exceptions

#### How to use

Follow the steps below to use `ServiceToolkit`:

1. Init a `ServiceToolkit` object and register service functions with necessary
parameters. Take the following Bing search function as an example.

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

We register the function in a `ServiceToolkit` object by providing `api_key` and `num_results` as necessary parameters.

```python
from agentscope.service import ServiceToolkit

service_toolkit = ServiceToolkit()

service_toolkit.add(
    bing_search,
    api_key="xxx",
    num_results=3
)
```

2. Use the `tools_instruction` attribute to instruct LLM in prompt, or use the `json_schemas` attribute to get the JSON schema format descriptions to construct customized instruction or directly use in model APIs (e.g. OpenAI Chat API).

````text
>> print(service_toolkit.tools_instruction)
## Tool Functions:
The following tool functions are available in the format of
```
{index}. {function name}: {function description}
{argument1 name} ({argument type}): {argument description}
{argument2 name} ({argument type}): {argument description}
...
```

1. bing_search: Search question in Bing Search API and return the searching results
    question (str): The search query string.
````
````text
>> print(service_toolkit.json_schemas)
{
  "bing_search": {
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
}
````

3. Guide LLM how to use tool functions by the `tools_calling_format` attribute.
The ServiceToolkit module requires LLM to return a list of dictionaries in
JSON format, where each dictionary represents a function call. It must
contain two fields, `name` and `arguments`, where `name` is the function name
and `arguments` is a dictionary that maps from the argument name to the
argument value.


```text
>> print(service_toolkit.tools_calling_format)
[{"name": "{function name}", "arguments": {"{argument1 name}": xxx, "{argument2 name}": xxx}}]
```

4. Parse the LLM response and call functions by its `parse_and_call_func`
method. This function takes a string or a parsed dictionary as input.
- When the input is a string, this function will parse it accordingly and execute the function with the parsed arguments.
- While if the input is a parse dictionary, it will call the function directly.

```python
# a string input
string_input = '[{"name": "bing_search", "arguments": {"question": "xxx"}}]'
res_of_string_input = service_toolkit.parse_and_call_func(string_input)

# or a parsed dictionary
dict_input = [{"name": "bing_search", "arguments": {"question": "xxx"}}]
# res_of_dict_input is the same as res_of_string_input
res_of_dict_input = service_toolkit.parse_and_call_func(dict_input)

print(res_of_string_input)
```
```
1. Execute function bing_search
    [ARGUMENTS]:
        question: xxx
    [STATUS]: SUCCESS
    [RESULT]: ...
```

More specific examples refer to the `ReActAgent` class in `agentscope.agents`.

#### Create new Service Function

A new service function that can be used by `ServiceToolkit` should meet the following requirements:

1. Well-formatted docstring (Google style is recommended), so that the
`ServiceToolkit` can extract both the function descriptions.
2. The name of the service function should be self-explanatory,
so that the LLM can understand the function and use it properly.
3. The typing of the arguments should be provided when defining
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
from agentscope.message import Msg

from typing import Optional, Union, Sequence


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

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
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
