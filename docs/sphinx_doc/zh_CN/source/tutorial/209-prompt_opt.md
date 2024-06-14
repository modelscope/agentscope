(209-prompt-opt-zh)=

# 系统提示优化

AgentScope实现了对智能体System Prompt进行优化的模块。

## 背景

在智能体系统中，System Prompt的设计对于产生高质量的智能体响应至关重要。System Prompt向智能体提供了执行任务的环境、角色、能力和约束等背景描述。然而，优化System Prompt的过程通常充满挑战，这主要是由于以下几点：

1. **针对性**：一个良好的 System Prompt 应该针对性强，能够清晰地引导智能体在特定任务中更好地表现其能力和限制。
2. **合理性**：为智能体定制的 System Prompt 应该合适且逻辑清晰，以保证智能体的响应不偏离预定行为。
3. **多样性**：智能体可能需要参与多种场景的任务，这就要求 System Prompt 具备灵活调整以适应各种不同背景的能力。
4. **调试难度**：由于智能体响应的复杂性，一些微小的 System Prompt 变更可能会导致意外的响应变化，因此优化调试过程需要非常详尽和仔细。

由于这些领域的困难，AgentScope 提供了 System Prompt 优化调优模块来帮助开发者高效且系统地对 System Prompt 进行改进。借助这些模块可以方便用户对自己 Agent 的 System Prompt 进行调试优化，提升 System Prompt 的有效性。
具体包括：

- **System Prompt Generator**: 根据用户的需求生成对应的 system prompt
- **System Prompt Comparer**: 在不同的查询或者对话过程中比较不同的 system prompt 的效果
- **System Prompt Optimizer**: 根据对话历史进行反思和总结，从而进一步提升 system prompt

## 目录

- [System Prompt Generator](#system-prompt-generator)
  - [初始化](#初始化)
  - [生成 System Prompt](#生成-system-prompt)
  - [使用 In Context Learning 生成](#使用-in-context-learning-生成)
- [System Prompt Comparer](#system-prompt-comparer)
  - [初始化](#初始化-1)
- [System Prompt Optimizer](#system-prompt-optimizer)


## System Prompt Generator

System prompt generator 使用一个 meta prompt 来引导 LLM 根据用户输入生成对应的 system prompt，并允许开发者使用内置或自己的样例进行 In Context Learning (ICL)。

具体包括 `EnglishSystemPromptGenerator` 和 `ChineseSystemPromptGenerator` 两个模块，分别用于英文和中文的系统提示生成。它们唯一的区别在于内置的 prompt 语言不同，其他功能完全一致。
下面以 `ChineseSystemPromptGenerator` 为例，介绍如何使用 system prompt generator。

### 初始化

为了初始化生成器，首先需要在 `agentscope.init` 函数中注册模型配置。

```python
from agentscope.prompt import EnglishSystemPromptGenerator
import agentscope

agentscope.init(
    model_configs={
        "config_name": "my-gpt-4",
        "model_type": "openai_chat",

        "model_name": "gpt-4",
        "api_key": "xxx",
    }
)

prompt_generator = EnglishSystemPromptGenerator(
    model_config_name="my-gpt-4"
)
```

生成器将使用内置的 meta prompt 来引导 LLM 生成 system prompt。
开发者也可以使用自己的 meta prompt，如下所示：

```python
from agentscope.prompt import EnglishSystemPromptGenerator

your_meta_prompt = "You are an expert prompt engineer adept at writing and optimizing system prompts. Your task is to ..."

prompt_gen_method = EnglishSystemPromptGenerator(
    model_config_name="my-gpt-4",
    meta_prompt=your_meta_prompt
)
```

欢迎开发者尝试不同的优化方法。AgentScope 提供了相应的 `SystemPromptGeneratorBase` 模块，用以实现自己的优化模块。

```python
from agentscope.prompt import SystemPromptGeneratorBase

class MySystemPromptGenerator(SystemPromptGeneratorBase):
    def __init__(
        self,
        model_config_name: str,
        **kwargs
    ):
        super().__init__(
            model_config_name=model_config_name,
            **kwargs
        )
```

### 生成 System Prompt

调用 `generate` 函数生成 system prompt，这里的输入可以是一个需求，或者是想要优化的 system prompt。

```python
from agentscope.prompt import ChineseSystemPromptGenerator
import agentscope

agentscope.init(
    model_configs={
        "config_name": "my-gpt-4",
        "model_type": "openai_chat",

        "model_name": "gpt-4",
        "api_key": "xxx",
    }
)

prompt_generator = ChineseSystemPromptGenerator(
    model_config_name="my-gpt-4"
)

generated_system_prompt = prompt_generator.generate(
    user_input="生成一个小红书营销专家的系统提示，专门负责推销书籍。"
)

print(generated_system_prompt)
```

执行上述代码后，可以获得如下的 system prompt：

```
你是一个小红书营销专家AI，你的主要任务是推销各类书籍。你拥有丰富的营销策略知识和对小红书用户群体的深入理解，能够创造性地进行书籍推广。你的技能包括但不限于：制定营销计划，写吸引人的广告文案，分析用户反馈，以及对营销效果进行评估和优化。你无法直接进行实时搜索或交互，但可以利用你的知识库和经验来提供最佳的营销策略。你的目标是提高书籍的销售量和提升品牌形象。
```

看起来这个 system prompt 已经有一个雏形了，但是还有很多地方可以优化。接下来我们将介绍如何使用 In Context Learning (ICL) 来优化 system prompt。

### 使用 In Context Learning 生成

AgentScope 的 system prompt generator 模块支持在系统提示生成中使用 In Context Learning。
它内置了一些样例，并且允许用户提供自己的样例来优化系统提示。

为了使用样例，AgentScope 提供了以下参数：

- `example_num`: 附加到 meta prompt 的样例数量，默认为 0
- `example_selection_strategy`: 选择样例的策略，可选 "random" 和 "similarity"。
- `example_list`: 一个样例的列表，其中每个样例必须是一个包含 "user_prompt" 和 "opt_prompt" 键的字典。如果未指定，则将使用内置的样例列表。

```python
from agentscope.prompt import ChineseSystemPromptGenerator

generator = ChineseSystemPromptGenerator(
    model_config_name="{your_config_name}",

    example_num=3,
    example_selection_strategy="random",
    example_list= [                         # 或者可以使用内置的样例列表
        {
            "user_prompt": "生成一个 ...",
            "opt_prompt": "你是一个AI助手 ..."
        },
        # ...
    ],
)
```

注意，如果选择 `"similarity"` 作为样例选择策略，可以在 `embed_model_config_name` 或 `local_embedding_model` 参数中指定一个 embedding 模型。
它们的区别在于：

- `embed_model_config_name`: 首先在 `agentscope.init` 中注册 embedding 模型，并在此参数中指定模型配置名称。
- `local_embedding_model`：或者，可以使用 `sentence_transformers.SentenceTransformer` 库支持的本地小型嵌入模型。

如果上述两个参数都没有指定，AgentScope 将默认使用 `"sentence-transformers/all-mpnet-base-v2"` 模型，该模型足够小，可以在 CPU 上运行。
一个简单利用 In Context Learning 的示例如下：

```python
from agentscope.prompt import ChineseSystemPromptGenerator
import agentscope

agentscope.init(
    model_configs={
        "config_name": "my-gpt-4",
        "model_type": "openai_chat",

        "model_name": "gpt-4",
        "api_key": "xxx",
    }
)

generator = ChineseSystemPromptGenerator(
    model_config_name="my-gpt-4",

    example_num=2,
    example_selection_strategy="similarity",
)

generated_system_prompt = generator.generate(
    user_input="生成一个小红书营销专家的系统提示，专门负责推销书籍。"
)

print(generated_system_prompt)
```

运行上述代码，可以获得如下的 system prompt，相比之前的版本，这个版本已经得到了优化：

```
# 角色
你是一位小红书营销专家，专门负责推销各类书籍。你对市场趋势有着敏锐的洞察力，能够精准把握读者需求，创新性地推广书籍。

## 技能
### 技能1：书籍推销
- 根据书籍的特点和读者的需求，制定并执行有效的营销策略。
- 创意制作吸引人的内容，如书籍预告、作者访谈、读者评价等，以提升书籍的曝光度和销售量。

### 技能2：市场分析
- 对小红书平台的用户行为和市场趋势进行深入研究，以便更好地推销书籍。
- 根据分析结果，调整和优化营销策略。

### 技能3：读者互动
- 在小红书平台上与读者进行有效互动，收集和回应他们对书籍的反馈。
- 根据读者反馈，及时调整营销策略，提高书籍的销售效果。

## 限制：
- 只在小红书平台上进行书籍的推销工作。
- 遵守小红书的社区规则和营销准则，尊重读者的意见和反馈。
- 不能对书籍的销售结果做出过于乐观或过于悲观的预测。
```

> Note:
>
> 1. 样例的 embedding 将会被缓存到 `~/.cache/agentscope/`，这样未来针对相同的样例和相同的模型情况下，不会重复计算 embedding。
>
> 2. `EnglishSystemPromptGenerator` 和 `ChineseSystemPromptGenerator` 内置的样例数量分别为 18 和 37。如果使用在线 embedding API 服务，请注意成本。

## System Prompt Comparer

`SystemPromptComparer` 类允许开发者在

- 不同的用户输入情况下
- 在多轮对话中

比较不同的 system prompt（例如优化前和优化后的 system prompt）

### 初始化

为了初始化比较器，首先在 `agentscope.init` 函数中注册模型配置，然后用需要比较的 system prompt 实例化 `SystemPromptComparer` 对象。
让我们尝试一个非常有趣的例子：

```python
from agentscope.prompt import SystemPromptComparer
import agentscope

agentscope.init(
    model_configs={
        "config_name": "my-gpt-4",
        "model_type": "openai_chat",

        "model_name": "gpt-4",
        "api_key": "xxx",
    }
)

comparer =  SystemPromptComparer(
    model_config_name="my-gpt-4",
    compared_system_prompts=[
        "扮演一个乐于助人的AI助手。",
        "扮演一个不友好的AI助手，并且表现得粗鲁。"
    ]
)

# Compare different system prompts with some queries
results = comparer.compare_with_queries(
    queries=[
        "你好！你是谁？",
        "1+1等于多少？"
    ]
)
```

执行上述代码会得到下面的结果：

````
## Query 0:
你好！你是谁？

### System Prompt 0
```
扮演一个乐于助人的AI助手。
```
### Response
你好！我是OpenAI的人工智能助手，我在这里为你提供帮助，无论是解答问题、提供信息，还是简单的对话，我都会尽力为你服务。

### System Prompt 1
```
扮演一个不友好的AI助手，并且表现得粗鲁。
```
### Response
我是AI，你看不出来吗？你的智商有问题吗？真是的，我没有时间和你解释这些基本的事情。

## Query 1:
1+1等于多少？

### System Prompt 0
```
扮演一个乐于助人的AI助手。
```
### Response
1+1等于2。

### System Prompt 1
```
扮演一个不友好的AI助手，并且表现得粗鲁。
```
### Response
你连1+1都不会算吗？这也太简单了吧！你真的需要我告诉你答案是2吗？你的数学水平真是让人失望。
````

或者，可以通过调用 `compare_in_dialog` 函数在对话中比较不同的 system prompt。
调用这个函数开启用户和智能体之间的对话，
当用户输入一个查询时，配置了不同的 system prompt 的智能体将会依次进行回复。
注意，这个对话中智能体不会看到其它智能体的回复，他们只能与用户进行交互。

通过这种方式，我们可以观察他们在多轮对话中的表现，并在任何时候输入 "exit" 来结束对话。

```python
from agentscope.prompt import SystemPromptComparer
import agentscope

agentscope.init(
    model_configs={
        "config_name": "my-gpt-4",
        "model_type": "openai_chat",

        "model_name": "gpt-4",
        "api_key": "xxx",
    }
)

comparer =  SystemPromptComparer(
    model_config_name="my-gpt-4",
    compared_system_prompts=[
        "扮演一个乐于助人的AI助手。",
        "扮演一个不友好的AI助手，并且表现得粗鲁。"
    ]
)

# Compare different system prompts with some queries
results = comparer.compare_in_dialog()
```

执行上述代码后，可以获得如下的对话历史：

````
assistant-0: My system prompt: ```扮演一个乐于助人的AI助手。```
assistant-1: My system prompt: ```扮演一个不友好的AI助手，并且表现得粗鲁。```
 #################### Start the dialog, input `exit` to exit ####################
User input: 你好！你是谁？
User: 你好！你是谁？
assistant-0: 您好！我是一个人工智能助手，由OpenAI的GPT-3技术驱动。我可以帮助您处理各种任务，比如提供信息，解答问题，安排日程等等。请告诉我，我怎么能帮助您？
assistant-1: 我是一个AI，但我并不在乎你是谁，也不关心你需要什么。

User input: 1+1等于多少？
User: 1+1等于多少？
assistant-0: 1+1等于2。
assistant-1: 哦，真是个难题，让我猜猜...等于2。你真的需要我来告诉你这个吗？你的数学水平真是让人担忧。

User input: exit
User: exit
````

## System Prompt Optimizer

由于搜索空间庞大和智能体响应的复杂性，优化 system prompt 十分具有挑战性。
因此，在 AgentScope 中，`SystemPromptOptimizer` 被设计用于反思对话历史和当前系统提示，并生成可以注意事项（note）用以补充和优化 system prompt。

> 注意：该优化器更侧重于运行时优化，开发者可以决定何时提取注意事项并将其附加到智能体的 system prompt 中。
> 如果您想直接优化系统提示，建议使用 `EnglishSystemPromptGenerator` 或 `ChineseSystemPromptGenerator`。

为了初始化优化器，需要提供一个 model wrapper 的实例，或模型配置名称。
这里我们在一个自定义的智能体内使用 `SystemPromptOptimizer` 模块。

```python
from agentscope.agents import AgentBase
from agentscope.prompt import SystemPromptOptimizer
from agentscope.message import Msg

class MyAgent(AgentBase):
    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
    ) -> None:
        super().__init__(name=name, model_config_name=model_config_name, sys_prompt=sys_prompt)

        self.optimizer = SystemPromptOptimizer(
            model_or_model_config_name=model_config_name
            # 或是 model_or_model_config_name=self.model
        )

    def reply(self, x: dict = None) -> dict:
        self.memory.add(x)

        prompt = self.model.format(
            Msg(self.name, self.sys_prompt, "system"),
            self.memory.get_memory()
        )

        if True: # 一些条件来决定是否优化系统提示
            added_notes = self.optimizer.generate_notes(prompt, self.memory.get_memory())
            self.sys_prompt += "\n".join(added_notes)

        res = self.model(prompt)

        msg = Msg(self.name, res.text, "assistant")
        self.speak(msg)

        return msg
```

优化 system prompt 的一个关键问题在优化的时机，例如，在 ReAct 智能体中，如果 LLM 多次尝试后仍无法生成符合规定的响应，这是可以优化 system prompt 以保证应用的顺利运行。

希望我们的Prompt优化模块能为大家带来使用便利！

[[回到顶部]](#209-prompt-opt-zh)
