(204-service-zh)=

# 工具

服务函数（Service function）是可以增强智能体能力工具，例如执行Python代码、网络搜索、
文件操作等。本教程概述了AgentScope中可用的服务功能，同时介绍如何使用它们来增强智能体的能力。

## Service函数概览

下面的表格按照类型概述了各种Service函数。以下函数可以通过`agentscope.service.{函数名}`进行调用。

| Service场景  | Service函数名称           | 描述                                      |
|------------|-----------------------|-----------------------------------------|
| 代码         | `execute_python_code` | 执行一段 Python 代码，可选择在 Docker <br/>容器内部执行。 |
| 检索         | `retrieve_from_list`  | 根据给定的标准从列表中检索特定项目。                      |
|            | `cos_sim`             | 计算2个embedding的余弦相似度。                    |
| SQL查询      | `query_mysql`         | 在 MySQL 数据库上执行 SQL 查询并返回结果。             |
|            | `query_sqlite`        | 在 SQLite 数据库上执行 SQL 查询并返回结果。            |
|            | `query_mongodb`       | 对 MongoDB 集合执行查询或操作。                    |
| 文本处理       | `summarization`       | 使用大型语言模型总结一段文字以突出其主要要点。                 |
| 网络         | `bing_search`         | 使用bing搜索。                               |
|            | `google_search`       | 使用google搜索。                             |
|            | `arxiv_search`        | 使用arxiv搜索。                              |
|            | `download_from_url`   | 从指定的 URL 下载文件。                          |
|            | `load_web`            | 爬取并解析指定的网页链接 （目前仅支持爬取 HTML 页面）          |
|            | `digest_webpage`      | 对已经爬取好的网页生成摘要信息（目前仅支持 HTML 页面
|            | `dblp_search_publications`      | 在dblp数据库里搜索文献。
|            | `dblp_search_authors`      | 在dblp数据库里搜索作者。                          |
|            | `dblp_search_venues`      | 在dblp数据库里搜索期刊，会议及研讨会。                   |
| 文件处理       | `create_file`         | 在指定路径创建一个新文件，并可选择添加初始内容。                |
|            | `delete_file`         | 删除由文件路径指定的文件。                           |
|            | `move_file`           | 将文件从一个路径移动或重命名到另一个路径。                   |
|            | `create_directory`    | 在指定路径创建一个新的目录。                          |
|            | `delete_directory`    | 删除一个目录及其所有内容。                           |
|            | `move_directory`      | 将目录从一个路径移动或重命名到另一个路径。                   |
|            | `read_text_file`      | 读取并返回文本文件的内容。                           |
|            | `write_text_file`     | 向指定路径的文件写入文本内容。                         |
|            | `read_json_file`      | 读取并解析 JSON 文件的内容。                       |
|            | `write_json_file`     | 将 Python 对象序列化为 JSON 并写入到文件。            |
| 多模态        | `dashscope_text_to_image`  | 使用 DashScope API 将文本生成图片。               |
|            | `dashscope_image_to_text`  | 使用 DashScope API 根据图片生成文字。              |
|            | `dashscope_text_to_audio`  | 使用 DashScope API 根据文本生成音频。             |
|                             | `openai_text_to_image`     | 使用 OpenAI API根据文本生成图片。
|                             | `openai_edit_image`        | 使用 OpenAI API 根据提供的遮罩和提示编辑图像。
|                             | `openai_create_image_variation`        | 使用 OpenAI API 创建图像的变体。
|                             | `openai_image_to_text` | 使用 OpenAI API 根据图片生成文字。
|                             | `openai_text_to_audio` | 使用 OpenAI API 根据文本生成音频。
|                             | `openai_audio_to_text` | 使用OpenAI API将音频转换为文本。
| *更多服务即将推出* |                       | 正在开发更多服务功能，并将添加到 AgentScope 以进一步增强其能力。  |

关于详细的参数、预期输入格式、返回类型，请参阅[API文档](https://modelscope.github.io/agentscope/)。

## 使用Service函数

AgentScope为Service函数提供了两个服务类，分别是`ServiceToolkit`和`ServiceResponse`。

### 关于ServiceToolkit

大模型使用工具函数通常涉及以下5个步骤：

1. **准备工具函数**。即开发者通过提供必要的参数（例如api key、用户名、密码等）将工具函数预处理成大模型能直接调用的形式。
2. **为大模型准备工具描述**。即一份详细的函数功能描述，以便大模型能够正确理解工具函数。
3. **约定函数调用格式**。提供一份说明来告诉大模型如何调用工具函数，即调用格式。
4. **解析大模型返回值**。从大模型获取返回值之后，需要按照第三步中的调用格式来解析字符串。
5. **调用函数并处理异常**。实际调用函数，返回结果，并处理异常。

为了简化上述步骤并提高复用性，AgentScope引入了ServiceToolkit模块。它可以
- 注册python函数为工具函数
- 生成字符串和JSON schema格式的工具函数说明
- 内置一套工具函数的调用格式
- 解析模型响应、调用工具功能，并处理异常


#### 如何使用

按照以下步骤使用ServiceToolkit:

1. 初始化一个ServiceToolkit对象并注册服务函数及其必要参数。例如，以下Bing搜索功能。

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
我们通过提供`api_key`和`num_results`作为必要参数，在`ServiceToolkit`对象中注册bing_search函数。

```python
from agentscope.service import ServiceToolkit

service_toolkit = ServiceToolkit()

service_toolkit.add(
    bing_search,
    api_key="xxx",
    num_results=3
)
```

2. 在提示中使用`tools_instruction`属性指导LLM，或使用`json_schemas`属性获取JSON schema格式的说明，以构建自定义格式的函数说明或直接在模型API中使用（例如OpenAI Chat API）。


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

3. 通过`tools_calling_format`属性指导LLM如何使用工具函数。ServiceToolkit中默认大模型
需要返回一个JSON格式的列表，列表中包含若干个字典，每个字典即为一个函数调用。必须包含name和
arguments两个字段，其中name为函数名，arguments为函数参数。arguments键值对应的值是从
“参数名”映射到“参数值”的字典。

```text
>> print(service_toolkit.tools_calling_format)
[{"name": "{function name}", "arguments": {"{argument1 name}": xxx, "{argument2 name}": xxx}}]
```

4. 通过`parse_and_call_func`方法解析大模型生成的字符串，并调用函数。此函数可以接收字符串或解析后符合格式要求的字典作为输入。
- 当输入为字符串时，此函数将相应地解析字符串并使用解析后的参数执行函数。
- 而如果输入为解析后的字典，则直接调用函数。


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

关于ServiceToolkit的具体使用样例，可以参考`agentscope.agents`中`ReActAgent`类。

#### 创建新的Service函数

新的Service函数必须满足以下要求才能被ServiceToolkit正常使用：
1. 具有格式化的函数说明（推荐Google风格），以便ServiceToolkit提取函数说明。
2. 函数名称应该是自解释的，这样智能体可以理解函数并正确使用它。
3. 在定义函数时应提供参数的类型（例如`def func(a: int, b: str, c: bool)`），以便大模型
能够给出类型正确的参数。


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

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
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
