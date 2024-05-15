(203-parser-zh)=

# 模型结果解析

## 目录

- [背景](#背景)
- [解析器模块](#解析器模块)
  - [功能说明](#功能说明)
  - [字符串类型](#字符串str类型)
    - [MarkdownCodeBlockParser](#markdowncodeblockparser)
      - [初始化](#初始化)
      - [响应格式模版](#响应格式模版)
      - [解析函数](#解析函数)
  - [字典类型](#字典dict类型)
    - [MarkdownJsonDictParser](#markdownjsondictparser)
      - [初始化 & 响应格式模版](#初始化--响应格式模版)
    - [MultiTaggedContentParser](#multitaggedcontentparser)
      - [初始化 & 响应格式模版](#初始化--响应格式模版-1)
      - [解析函数](#解析函数-1)
  - [JSON / Python 对象类型](#json--python-对象类型)
    - [MarkdownJsonObjectParser](#markdownjsonobjectparser)
      - [初始化 & 响应格式模版](#初始化--响应格式模版-2)
      - [解析函数](#解析函数-2)
- [典型使用样例](#典型使用样例)
  - [狼人杀游戏](#狼人杀游戏)
  - [ReAct 智能体和工具使用](#react-智能体和工具使用)
- [自定义解析器](#自定义解析器)


## 背景

利用LLM构建应用的过程中，将 LLM 产生的字符串解析成指定的格式，提取出需要的信息，是一个非常重要的环节。
但同时由于下列原因，这个过程也是一个非常复杂的过程：

1. **多样性**：解析的目标格式多种多样，需要提取的信息可能是一段特定文本，一个JSON对象，或者是一个复杂的数据结构。
2. **复杂性**：结果解析不仅仅是将 LLM 产生的文本转换成目标格式，还涉及到提示工程（提醒 LLM 应该产生什么格式的输出），错误处理等一些列问题。
3. **灵活性**：同一个应用中，不同阶段也可能需要智能体产生不同格式的输出。

为了让开发者能够便捷、灵活的地进行结果解析，AgentScope设计并提供了解析器模块（Parser）。利用该模块，开发者可以通过简单的配置，实现目标格式的解析，同时可以灵活的切换解析的目标格式。

AgentScope中，解析器模块的设计原则是：
1. **灵活**：开发者可以灵活设置所需返回格式、灵活地切换解析器，实现不同格式的解析，而无需修改智能体类的代码，即具体的“目标格式”与智能体类内`reply`函数的处理逻辑解耦
2. **自由**：用户可以自由选择是否使用解析器。解析器所提供的响应格式提示、解析结果等功能都是在`reply`函数内显式调用的，用户可以自由选择使用解析器或是自己实现代码实现结果解析
3. **透明**：利用解析器时，提示（prompt）构建的过程和结果在`reply`函数内对开发者完全可见且透明，开发者可以精确调试自己的应用。

## 解析器模块

### 功能说明

解析器模块（Parser）的主要功能包括：

1. 提供“响应格式说明”（format instruction），即提示 LLM 应该在什么位置产生什么输出，例如

````
You should generate python code in a fenced code block as follows
```python
{your_python_code}
```
````


2. 提供解析函数（parse function），直接将 LLM 产生的文本解析成目标数据格式

3. 针对字典格式的后处理功能。在将文本解析成字典后，其中不同的字段可能有不同的用处

AgentScope提供了多种不同解析器，开发者可以根据自己的需求进行选择。

| 目标格式              | 解析器                        | 说明                                                                          |
|-------------------|----------------------------|-----------------------------------------------------------------------------|
| 字符串(`str`)类型      | `MarkdownCodeBlockParser`  | 要求 LLM 将指定的文本生成到Markdown中以 ``` 标识的代码块中，解析结果为字符串。                            |
| 字典(`dict`)类型      | `MarkdownJsonDictParser`   | 要求 LLM 在 \```json 和 \``` 标识的代码块中产生指定内容的字典，解析结果为 Python 字典。                  |
|                   | `MultiTaggedContentParser` | 要求 LLM 在多个标签中产生指定内容，这些不同标签中的内容将一同被解析成一个 Python 字典，并填入不同的键值对中。               |
| JSON / Python对象类型 | `MarkdownJsonObjectParser` | 要求 LLM 在 \```json 和 \``` 标识的代码块中产生指定的内容，解析结果将通过 `json.loads` 转换成 Python 对象。 |

> **NOTE**: 相比`MarkdownJsonDictParser`，`MultiTaggedContentParser`更适合于模型能力不强，以及需要 LLM 返回内容过于复杂的情况。例如 LLM 返回 Python 代码，如果直接在字典中返回代码，那么 LLM 需要注意特殊字符的转义（\t,\n,...），`json.loads`读取时对双引号和单引号的区分等问题。而`MultiTaggedContentParser`实际是让大模型在每个单独的标签中返回各个键值，然后再将它们组成字典，从而降低了LLM返回的难度。

下面我们将根据不同的目标格式，介绍这些解析器的用法。

### 字符串（`str`）类型

#### MarkdownCodeBlockParser

##### 初始化

- `MarkdownCodeBlockParser`采用 Markdown 代码块的形式，要求 LLM 将指定文本产生到指定的代码块中。可以通过`language_name`参数指定不同的语言，从而利用大模型代码能力产生对应的输出。例如要求大模型产生 Python 代码时，初始化如下：

    ```python
    from agentscope.parsers import MarkdownCodeBlockParser

    parser = MarkdownCodeBlockParser(language_name="python", content_hint="your python code")
    ```

##### 响应格式模版

- `MarkdownCodeBlockParser`类提供如下的“响应格式说明”模版，在用户调用`format_instruction`属性时，会将`{language_name}`替换为初始化时输入的字符串：

  ````
  You should generate {language_name} code in a {language_name} fenced code block as follows:
  ```{language_name}
  {content_hint}
  ```
  ````

- 例如上述对`language_name`为`"python"`的初始化，调用`format_instruction`属性时，会返回如下字符串：

  ```python
  print(parser.format_instruction)
  ```

  ````
  You should generate python code in a python fenced code block as follows
  ```python
  your python code
  ```
  ````

##### 解析函数

- `MarkdownCodeBlockParser`类提供`parse`方法，用于解析LLM产生的文本，返回的是字符串。

    ````python
    res = parser.parse(
        ModelResponse(
            text="""The following is generated python code
    ```python
    print("Hello world!")
    ```
    """
        )
    )

    print(res.parsed)
    ````

    ```
    print("hello world!")
    ```

### 字典（`dict`）类型

与字符串和一般的 JSON / Python 对象不同，作为LLM应用中常用的数据格式，AgentScope为字典类型提供了额外的后处理功能。初始化解析器时，可以通过额外设置`keys_to_content`，`keys_to_memory`，`keys_to_metadata`三个参数，从而实现在调用`parser`的`to_content`，`to_memory`和`to_metadata`方法时，对字典键值对的过滤。
其中
  - `keys_to_content` 指定的键值对将被放置在返回`Msg`对象中的`content`字段，这个字段内容将会被返回给其它智能体，参与到其他智能体的提示构建中，同时也会被`self.speak`函数调用，用于显式输出
  - `keys_to_memory` 指定的键值对将被存储到智能体的记忆中
  - `keys_to_metadata` 指定的键值对将被放置在`Msg`对象的`metadata`字段，可以用于应用的控制流程判断，或挂载一些不需要返回给其它智能体的信息。

三个参数接收布尔值、字符串和字符串列表。其值的含义如下：
- `False`: 对应的过滤函数将返回`None`。
- `True`: 整个字典将被返回。
- `str`: 对应的键值将被直接返回，注意返回的会是对应的值而非字典。
- `List[str]`: 根据键值对列表返回过滤后的字典。

AgentScope中，`keys_to_content` 和 `keys_to_memory` 默认为 `True`，即整个字典将被返回。`keys_to_metadata` 默认为 `False`，即对应的过滤函数将返回 `None`。

下面是狼人杀游戏的样例，在白天讨论过程中 LLM 扮演狼人产生的字典。在这个例子中，
- `"thought"`字段不应该返回给其它智能体，但是应该存储在智能体的记忆中，从而保证狼人策略的延续；
- `"speak"`字段应该被返回给其它智能体，并且存储在智能体记忆中；
- `"finish_discussion"`字段用于应用的控制流程中，判断讨论是否已经结束。为了节省token，该字段不应该被返回给其它的智能体，同时也不应该存储在智能体的记忆中。

  ```python
  {
      "thought": "The others didn't realize I was a werewolf. I should end the discussion soon.",
      "speak": "I agree with you.",
      "finish_discussion": True
  }
  ```

AgentScope中，我们通过调用`to_content`，`to_memory`和`to_metadata`方法实现后处理功能，示意代码如下：

- 应用中的控制流代码，创建对应的解析器对象并装载

  ```python
  from agentscope.parsers import MarkdownJsonDictParser

  # ...

  agent = DictDialogAgent(...)

  # 以MarkdownJsonDictParser为例
  parser = MarkdownJsonDictParser(
      content_hint={
          "thought": "what you thought",
          "speak": "what you speak",
          "finish_discussion": "whether the discussion is finished"
      },
      keys_to_content="speak",
      keys_to_memory=["thought", "speak"],
      keys_to_metadata=["finish_discussion"]
  )

  # 装载解析器，即相当于指定了要求的相应格式
  agent.set_parser(parser)

  # 讨论过程
  while True:
      # ...
      x = agent(x)
      # 根据metadata字段，获取LLM对当前是否应该结束讨论的判断
      if x.metadata["finish_discussion"]:
          break
  ```


- 智能体内部`reply`函数内实现字典的过滤

  ```python
      # ...
      def reply(x: dict = None) -> None:

          # ...
          res = self.model(prompt, parse_func=self.parser.parse)

          # 过滤后拥有 thought 和 speak 字段的字典，存储到智能体记忆中
          self.memory.add(
              Msg(
                  self.name,
                  content=self.parser.to_memory(res.parsed),
                  role="assistant",
              )
          )

          # 存储到content中，同时存储到metadata中
          msg = Msg(
            self.name,
            content=self.parser.to_content(res.parsed),
            role="assistant",
            metadata=self.parser.to_metadata(res.parsed),
          )
          self.speak(msg)

          return msg
  ```




> **Note**: `keys_to_content`，`keys_to_memory`和`keys_to_metadata`参数可以是列表，字符串，也可以是布尔值。
> - 如果是`True`，则会直接返回整个字典，即不进行过滤
> - 如果是`False`，则会直接返回`None`值
> - 如果是字符串类型，则`to_content`，`to_memory`和`to_metadata`方法将会把字符串对应的键值直接放入到对应的位置，例如`keys_to_content="speak"`，则`to_content`方法将会把`res.parsed["speak"]`放入到`Msg`对象的`content`字段中，`content`字段会是字符串而不是字典。
> - 如果是列表类型，则`to_content`，`to_memory`和`to_metadata`方法实现的将是过滤功能，对应过滤后的结果是字典
>   ```python
>     parser = MarkdownJsonDictParser(
>        content_hint={
>            "thought": "what you thought",
>            "speak": "what you speak",
>        },
>        keys_to_content="speak",
>        keys_to_memory=["thought", "speak"],
>     )
>
>     example_dict = {"thought": "abc", "speak": "def"}
>     print(parser.to_content(example_dict))  # def
>     print(parser.to_memory(example_dict))   # {"thought": "abc", "speak": "def"}
>     print(parser.to_metadata(example_dict)) # None
>   ```
>   ```
>   def
>   {"thought": "abc", "speak": "def"}
>   None
>   ```

下面我们具体介绍两种字典类型的解析器。

#### MarkdownJsonDictParser

##### 初始化 & 响应格式模版

- `MarkdownJsonDictParser`要求 LLM 在 \```json 和 \``` 标识的代码块中产生指定内容的字典。
- 除了`to_content`，`to_memory`和`to_metadata`参数外，可以通过提供 `content_hint` 参数提供响应结果样例和说明，即提示LLM应该产生什么样子的字典，该参数可以是字符串，也可以是字典，在构建响应格式提示的时候将会被自动转换成字符串进行拼接。

  ```python
  from agentscope.parsers import MarkdownJsonDictParser

  # 字典
  MarkdownJsonDictParser(
      content_hint={
        "thought": "what you thought",
        "speak": "what you speak",
      }
  )
  # 或字符串
  MarkdownJsonDictParser(
      content_hint="""{
    "thought": "what you thought",
    "speak": "what you speak",
  }"""
  )
  ```
    - 对应的`instruction_format`属性

  ````
  You should respond a json object in a json fenced code block as follows:
  ```json
  {content_hint}
  ```
  ````

#### MultiTaggedContentParser

`MultiTaggedContentParser`要求 LLM 在多个指定的标签对中产生指定的内容，这些不同标签的内容将一同被解析为一个 Python 字典。使用方法与`MarkdownJsonDictParser`类似，只是初始化方法不同，更适合能力较弱的LLM，或是比较复杂的返回内容。

##### 初始化 & 响应格式模版

`MultiTaggedContentParser`中，每一组标签将会以`TaggedContent`对象的形式传入，其中`TaggedContent`对象包含了
- 标签名（`name`），即返回字典中的key值
- 开始标签（`tag_begin`）
- 标签内容提示（`content_hint`）
- 结束标签（`tag_end`)
- 内容解析功能（`parse_json`），默认为`False`。当置为`True`时，将在响应格式提示中自动添加提示，并且提取出的内容将通过`json.loads`解析成 Python 对象

```python
from agentscope.parsers import MultiTaggedContentParser, TaggedContent
parser = MultiTaggedContentParser(
  TaggedContent(
    name="thought",
    tag_begin="[THOUGHT]",
    content_hint="what you thought",
    tag_end="[/THOUGHT]"
  ),
  TaggedContent(
    name="speak",
    tag_begin="[SPEAK]",
    content_hint="what you speak",
    tag_end="[/SPEAK]"
  ),
  TaggedContent(
    name="finish_discussion",
    tag_begin="[FINISH_DISCUSSION]",
    content_hint="true/false, whether the discussion is finished",
    tag_end="[/FINISH_DISCUSSION]",
    parse_json=True,         # 我们希望这个字段的内容直接被解析成 True 或 False 的 Python 布尔值
  )
)

print(parser.format_instruction)
```

```
Respond with specific tags as outlined below, and the content between [FINISH_DISCUSSION] and [/FINISH_DISCUSSION] MUST be a JSON object:
[THOUGHT]what you thought[/THOUGHT]
[SPEAK]what you speak[/SPEAK]
[FINISH_DISCUSSION]true/false, whether the discussion is finished[/FINISH_DISCUSSION]
```

##### 解析函数

- `MultiTaggedContentParser`的解析结果为字典，其中key为`TaggedContent`对象的`name`的值，以下是狼人杀中解析 LLM 返回的样例：

```python
res_dict = parser.parse(
    ModelResponse(text="""As a werewolf, I should keep pretending to be a villager
[THOUGHT]The others didn't realize I was a werewolf. I should end the discussion soon.[/THOUGHT]
[SPEAK]I agree with you.[/SPEAK]
[FINISH_DISCUSSION]true[/FINISH_DISCUSSION]
"""
    )
)

print(res_dict)
```

```
{
  "thought": "The others didn't realize I was a werewolf. I should end the discussion soon.",
  "speak": "I agree with you.",
  "finish_discussion": true
}
```

### JSON / Python 对象类型

#### MarkdownJsonObjectParser

`MarkdownJsonObjectParser`同样采用 Markdown 的\```json和\```标识，但是不限制解析的内容的类型，可以是列表，字典，数值，字符串等可以通过`json.loads`进行解析字符串。

##### 初始化 & 响应格式模版

```python
from agentscope.parsers import MarkdownJsonObjectParser

parser = MarkdownJsonObjectParser(
  content_hint="{A list of numbers.}"
)

print(parser.format_instruction)
```

````
You should respond a json object in a json fenced code block as follows:
```json
{a list of numbers}
```
````

##### 解析函数

````python
res = parser.parse(
    ModelResponse(text="""Yes, here is the generated list
```json
[1,2,3,4,5]
```
"""
    )
)

print(type(res))
print(res)
````

```
<class 'list'>
[1, 2, 3, 4, 5]
```

## 典型使用样例

### 狼人杀游戏

狼人杀（Werewolf）是字典解析器的一个经典使用场景，在游戏的不同阶段内，需要同一个智能体在不同阶段产生除了`"thought"`和`"speak"`外其它的标识字段，例如是否结束讨论，预言家是否使用能力，女巫是否使用解药和毒药，投票等。

AgentScope中已经内置了[狼人杀](https://github.com/modelscope/agentscope/tree/main/examples/game_werewolf)的样例，该样例采用`DictDialogAgent`类，配合不同的解析器，实现了灵活的目标格式切换。同时利用解析器的后处理功能，实现了“想”与“说”的分离，同时控制游戏流程的推进。
详细实现请参考狼人杀[源码](https://github.com/modelscope/agentscope/tree/main/examples/game_werewolf)。

### ReAct 智能体和工具使用

`ReActAgent`是AgentScope中为了工具使用构建的智能体类，基于 ReAct 算法进行搭建，可以配合不同的工具函数进行使用。其中工具的调用，格式解析，采用了和解析器同样的实现思路。详细实现请参考[代码](https://github.com/modelscope/agentscope/blob/main/src/agentscope/agents/react_agent.py)。


## 自定义解析器

AgentScope中提供了解析器的基类`ParserBase`，开发者可以通过继承该基类，并实现其中的`format_instruction`属性和`parse`方法来实现自己的解析器。

针对目标格式是字典类型的解析，可以额外继承`agentscope.parser.DictFilterMixin`类实现对字典类型的后处理。

```python
from abc import ABC, abstractmethod

from agentscope.models import ModelResponse


class ParserBase(ABC):
    """The base class for model response parser."""

    format_instruction: str
    """The instruction for the response format."""

    @abstractmethod
    def parse(self, response: ModelResponse) -> ModelResponse:
        """Parse the response text to a specific object, and stored in the
        parsed field of the response object."""

    # ...
```
