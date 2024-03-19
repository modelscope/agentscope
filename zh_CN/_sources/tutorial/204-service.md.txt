(204-service-zh)=

# 服务函数

服务函数（Service function）是可以增强智能体能力工具，例如执行Python代码、网络搜索、
文件操作等。本教程概述了AgentScope中可用的服务功能，同时介绍如何使用它们来增强智能体的能力。

## Service函数概览

下面的表格按照类型概述了各种Service函数。以下函数可以通过`agentscope.service.{函数名}`进行调用。

| Service场景  | Service函数名称           | 描述                                                |
|------------|-----------------------| ------------------------------------------------------------ |
| 代码         | `execute_python_code` | 执行一段 Python 代码，可选择在 Docker <br/>容器内部执行。 |
| 检索         | `retrieve_from_list`  | 根据给定的标准从列表中检索特定项目。 |
| SQL查询      | `query_mysql`         | 在 MySQL 数据库上执行 SQL 查询并返回结果。 |
|            | `query_sqlite`        | 在 SQLite 数据库上执行 SQL 查询并返回结果。 |
|            | `query_mongodb`       | 对 MongoDB 集合执行查询或操作。 |
| 文本处理       | `summarization`       | 使用大型语言模型总结一段文字以突出其主要要点。 |
| 网络搜索       | `web_search`          | 使用指定的搜索引擎（当前支持 Google 和 Bing）执行网络搜索。 |
| 文件处理       | `create_file`         | 在指定路径创建一个新文件，并可选择添加初始内容。 |
|            | `delete_file`         | 删除由文件路径指定的文件。       |
|            | `move_file`           | 将文件从一个路径移动或重命名到另一个路径。 |
|            | `create_directory`    | 在指定路径创建一个新的目录。 |
|            | `delete_directory`    | 删除一个目录及其所有内容。     |
|            | `move_directory`      | 将目录从一个路径移动或重命名到另一个路径。 |
|            | `read_text_file`      | 读取并返回文本文件的内容。    |
|            | `write_text_file`     | 向指定路径的文件写入文本内容。 |
|            | `read_json_file`      | 读取并解析 JSON 文件的内容。 |
|            | `write_json_file`     | 将 Python 对象序列化为 JSON 并写入到文件。 |
| *更多服务即将推出* |                       | 正在开发更多服务功能，并将添加到 AgentScope 以进一步增强其能力。 |

关于详细的参数、预期输入格式、返回类型，请参阅[API文档](https://modelscope.github.io/agentscope/)。

## 使用Service函数

AgentScope为Service函数提供了两个服务类，分别是`ServiceFactory`和`ServiceResponse`。

- `ServiceFactory`的主要作用是将一般的Python函数编程大模型可以直接使用的形式，同时自动生成函数说明。
- `ServiceResponse`是一个字典的子类，为所有Service函数提供了统一的调用结果接口。

### 关于ServiceFactory

智能体使用的工具一般是函数类型，开发者需要准备大模型能够直接调用的函数，并且需要提供函数的说明。
但是一般的函数往往需要开发者提供部分参数（例如秘钥，用户名，特定的网址等），然后大模型才能够
使用。同时为多个函数生成特定格式的说明也是一件繁琐的事情。

为了解决上述问题，AgentScope提出了`ServiceFactory`，对于给定的Service
函数，它允许开发者指定部分参数，生成一个大模型可以直接调用的函数，并且自动根据Docstring生成函数说明。
以Bing网络搜索函数为例。

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

上述函数中，`question`是大模型填写的字段，而`api_key`，`num_results`是开发者需要提供的参数。
我们利用`ServiceFactory`的`get`函数进行处理：

```python
from agentscope.service import ServiceFactory

func, func_intro = ServiceFactory.get(
    bing_search,
    api_key="xxx",
    num_results=3)
```

上述代码中，ServiceFactory生成的func和下面的函数是等价的：

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

生成的JSON Schema格式说明如下，该格式的函数说明可以直接用于OpenAI API中的tools字段。
用户也可以根据自己的需求进行二次修改。

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

**注意**：`ServiceFactory`生成的函数和参数说明（包括描述，类型，默认值）是从函数的docstring
中自动提取的，因此建议原函数的docstring应该按照Google风格进行书写，以便更好的提取函数说明。

**建议**：

- Service函数的名称应该是自解释的，这样智能体可以理解函数并正确使用它。
- 在定义函数时应提供参数的类型（例如`def func(a: int, b: str, c: bool)`），以便智能体正确指定参数。

### 关于ServiceResponse

`ServiceResponse`是对调用的结果的封装，包含了`status`和`content`两个字段。
当Service函数正常运行结束时，`status`为`ServiceExecStatus.
SUCCESS`，`content`为函数的返回值。而当运行出现错误时，`status`为`ServiceExecStatus.
Error`，`content`内为错误信息。

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

    # ... [为简洁起见省略代码]

```

## 示例

```python
import json
import inspect
from agentscope.service import ServiceResponse
from agentscope.agents import AgentBase


def create_file(file_path: str, content: str = "") -> ServiceResponse:
    """
    创建文件并向其中写入内容。

    Args:
        file_path (str): 将要创建文件的路径。
        content (str): 要写入文件的内容。

    Returns:
        ServiceResponse: 其中布尔值指示成功与否，字符串包含任何错误消息（如果有），包括错误类型。
    """
    # ... [为简洁起见省略代码]


class YourAgent(AgentBase):
    # ... [为简洁起见省略代码]

    def reply(self, x: dict = None) -> dict:
        # ... [为简洁起见省略代码]

        # 构造提示，让代理提供 JSON 格式的参数
        prompt = (
            f"To complete the user request\n```{x['content']}```\n"
            "Please provide the necessary parameters in JSON format for the "
            "function:\n"
            f"Function: {create_file.__name__}\n"
            "Description: Create a file and write content to it.\n"
        )

        # 添加关于函数参数的详细信息
        sig = inspect.signature(create_file)
        parameters = sig.parameters.items()
        params_prompt = "\n".join(
            f"- {name} ({param.annotation.__name__}): "
            f"{'(default: ' + json.dumps(param.default) + ')'if param.default is not inspect.Parameter.empty else ''}"
            for name, param in parameters
        )
        prompt += params_prompt

        # 获取模型响应
        model_response = self.model(prompt).text

        # 解析模型响应并调用 create_file 函数
        # 可能需要额外的提取函数
        try:
            kwargs = json.loads(model_response)
            create_file(**kwargs)
        except:
            # 错误处理
            pass

        # ... [为简洁起见省略代码]
```

[[返回顶部]](#204-service-zh)
