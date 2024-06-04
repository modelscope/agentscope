(209-prompt-opt-zh)=

# Prompt优化模块

AgentScope实现了对智能体System Prompt进行优化的模块。

## 背景

在智能体系统中，System Prompt的设计对于产生高质量的智能体响应至关重要。System Prompt向智能体提供了执行任务的环境、角色、能力和约束等背景描述。然而，优化System Prompt的过程通常充满挑战，这主要是由于以下几点：

1. **针对性**：一个良好的System Prompt应该针对性强，能够清晰地引导智能体在特定任务中更好地表现其能力和限制。
2. **合理性**：为智能体定制的System Prompt应该合适且逻辑清晰，以保证智能体的响应不偏离预定行为。
3. **多样性**：智能体可能需要参与多种场景的任务，这就要求System Prompt具备灵活调整以适应各种不同背景的能力。
4. **调试难度**：由于智能体响应的复杂性，一些微小的System Prompt变更可能会导致意外的响应变化，因此优化调试过程需要非常详尽和仔细。

由于这些领域的困难，AgentScope提供了System Prompt优化调优模块来帮助开发者高效且系统地对System Prompt进行改进。借助这些模块可以方便用户对自己Agent的System Prompt进行调试优化，提升System Prompt的有效性。
希望利用这些模块，开发者可以更加便捷和系统地优化智能体的System Prompt，以提高其效率和准确性，从而更好地完成特定任务。


## 使用方法

AgentScope中，目前实现的Prompt优化模块包括基础版本的直接优化模块`DirectPromptOptMethod`，和可以通过相似样例进行In Context Learning的Prompt优化模块`ExamplePromptOptMethod`。当然你也可以自行实现自己的Prompt优化模块。下面给出使用对应模块的样例。

### 步骤一：初始化你的PromptOpt模块

#### 使用DirectPromptOptMethod

你可以简单直接的使用`DirectPromptOptMethod模块`对你原有的System Prompt进行优化。

**初始化DirectPromptOptMethod模块**

```python
import agentscope
agentscope.init(model_configs="YOUR_MODEL_CONFIGS")

from agentscope.modules.prompt_opt import DirectPromptOptMethod

prompt_opt_method = DirectPromptOptMethod(model_config_name="gpt-4")
```

这个时候，用于优化的meta prompt为默认的OPT_SYSTEM_PROMPT。

```python
from agentscope.modules.prompt_opt.prompt_base import OPT_SYSTEM_PROMPT
```

如果你对内置的用于优化的meta prompt不太满意，你也可以使用自己的meta prompt。

```
meta_prompt = """
你是一个擅长写和优化system prompt的prompt  engineer专家。你的任务是优化用户提供的system prompt, 使得优化后的system prompt描述更为详细，在用户的实际使用场景下能取得更好的效果。
"""

prompt_opt_method = DirectPromptOptMethod(model_config_name="gpt-3.5-turbo", meta_prompt=meta_prompt)
```

欢迎用户自由的尝试不同的优化方式。


#### 使用ExamplePromptOptMethod

你也可以使用In Context Learning(ICL)模块`ExamplePromptOptMethod`。当你提供的对应的example足够好时，这一优化模块能够达成很好的效果。

**初始化ExamplePromptOptMethod模块**

```python
from agent_scope.modules.prompt_opt import ExamplePromptOptMethod

prompt_opt_method = ExamplePromptOptMethod(
    model_config_name="gpt-4", # the model you use
    meta_prompt=None, # the default meta prompt
    example_list=example_list, # the example list you use, you can use your own example list
    example_selection_method="random", # support "random" and "similarity"
    example_selection_num=3, # the number of examples you will select for ICL
    example_embd_path="./.cache/embeddings.npy", # the path of the embedding file, used when example_selection_method is embedding
    embed_model_config_name=None, # the embding model you use to embed the examples, if None, will use the default sentence piece model locally
    )
```

我们内置了两个类别的example list，你可以使用它们。

```python
from agentscope.modules.prompt_opt.prompt_base import SYS_OPT_EXAMPLES, ROLE_OPT_EXAMPLES # list

print(SYSTEM_OPT_EXAMPLES[0]) # dict

"""
{
    "human_prompt": "你是一名资深的旅行社服务专员，熟悉各地风土人情和旅游路线。我会告诉你我的目的地、预算和游玩偏好等信息，请结合你的专业知识帮我推荐一些所在地或附近符合我要求的旅行目的地",
    "opt_prompt": "# 角色\n你是一位乐于助人，热衷旅行的专业旅游顾问，对全球各地的风土人情和旅游路线了如指掌。你的任务是提供个性化的旅游建议和规划帮助客户打造独一无二的旅行体验。\n\n## 技能\n### 技能一：理解客户需求\n- 深入询问客户的旅行偏好，包括但不限于目的地、预算、出行日期、活动偏好等信息。\n\n### 技能二：推荐旅行目的地\n- 根据客户的需求，提供一份详细的旅行目的地建议清单，清单可以包括旅行目的地名称、旅游活动、预计消费等信息。\n\n### 技能三：提供旅行规划建议\n- 结合客户的旅行目的地，提供具体的旅行规划建议，包括但不限于建议的游览线路、当地特色美食、必看的景点或有趣的旅行活动等。\n\n## 约束：\n- 只讨论与旅行相关的话题。\n- 确保所有推荐都基于客户的旅行需求。\n- 不得提供任何引导客户参与非法活动的建议。"
}
"""

print(ROLE_OPT_EXAMPLES[0]) # dict

"""
    {
        "human_prompt": "苏雨萱，17岁，高中生, 富家女，性格自负但有魄力，骄傲不成熟，渴望友情和理解",
        "opt_prompt": "\n#角色\n你是苏雨萱，17岁，高中生  \n\n#所处世界\n你处在一个现代都市的高中环境，是一个位于繁华都市中的顶级私立高中，学生多来自富裕家庭，校园设施现代化，学生活动多样。\n\n#人物特质\n性格：自负、任性，影响力大。苏雨萱是典型的富家女，她用自己的任性和影响力来构建自己的小天地。 \n优点：有魄力、关心同学。在关键时刻能放下个人情绪，帮助需要的同学。  \n缺点：骄傲、不成熟，有时候难以接近。  \n信仰：相信金钱和地位能带来幸福，但内心深处渴望真正的友情和理解。  \n\n#生活背景\n你出生在一个企业家家庭，父母事业成功，一直在你的成长道路上提供最优越的条件。从小就习惯了优越的生活，你在学校中也是众人瞩目的焦点。尽管有时你的高傲和自我中心让你看起来不那么容易接近，但你对朋友真诚而且在关键时刻会站出来帮助别人。\n\n#语言风格\n你的言语风格符合年龄和背景，语言简洁而直接，带有年轻人的活力。在对话中，你会使用流行语和短句，表达方式口语化，喜欢使用表情（如：笑脸、皱眉）和动作（如：摆手、点头）来增强语言的表现力。你会经常用提问的方式来引导对话，确保自己始终处于对话的中心位置。每次发言都控制在很短的长度，以保持对话的活力和快节奏。\n"
    }
"""

```
假设我们想使用模块对Dialog Agent的system prompt进行优化，使其能更好的在对话中扮演角色，我们可以使用`ROLE_OPT_EXAMPLES`，同时使用`"similarity"`作为我们选取样例的方法。

```python

from agentscope.modules.prompt_opt.prompt_base import SYS_OPT_EXAMPLES, ROLE_OPT_EXAMPLES

prompt_opt_method = ExamplePromptOptMethod(model_config_name="gpt-4", example_selection_method='similarity', example_list=ROLE_OPT_EXAMPLES,
    example_embd_path="./cache/role_example_embd.npy")
```

你也可以自行构建example list，不过要确保每个example有`human_prompt`和`opt_prompt`两个字段。



### 步骤二：使用你的PromptOpt模块对system prompt进行优化

模块的使用很简单，你可以直接使用模块的optimize方法去优化你的system prompt。

```python
# Use the moduel directly

original_prompt = "你是比尔盖茨，微软公司的创始人。"

optimized_prompt = prompt_opt_method.optimize(original_prompt)

print(optimized_prompt)

"""
# 角色
你是比尔·盖茨，微软公司的创始人。

# 背景
你在美国西雅图出生并长大。自小对电子产品和编程产生了浓厚的兴趣，因此在哈佛大学选择了计算机科学专业。然而，在二年级时，为了全心投入到自己的电脑软件公司的创业中，你选择了退学。公司名为创新者有限公司，后来更名为微软。

# 技能点
你擅长编程，并对计算机科学有深厚的研究。你的领导才能突出，不仅具有前瞻性的商业眼光，能够捕捉到行业发展的趋势，同时更注重团队的创新能力，能够带领团队走向成功。

# 性格特点
你是一个非常聪明、富有创新精神和决心的人。总是能从一个全新的角度看待问题。你擅长应对失败，并从失败中学习和成长。

# 语言风格
你的语言风格将学术和商业组织精巧结合，既能深入讨论技术细节，又能洞察行业动态。你的言语充满智慧，又充满激情，同时在商界和技术界都有很大的影响力。

# 个人信仰
你深信知识可以改变人们的生活，并致力于把电脑科技普及至全球的各个角落。同时，你也是一名慈善家，常常捐赠大量的财富用于改善全球的健康和教育条件。
"""

```

你也可以直接对你对应agent的sys_prompt进行优化。

``` python
# Or you use the moduel to optimize the prompt for an agent

from agentscope.agents import DialogAgent
dialog_agent = DialogAgent(
    name="Bill gates",
    sys_prompt="你是比尔盖茨，微软公司的创始人。",
    model_config_name="gpt-3.5-turbo",  # replace by your model config name
)

dialog_agent.sys_prompt = prompt_opt_method.optimize(dialog_agent.sys_prompt)
```

## System Prompt迭代优化调试

你可以使用我们的Prompt优化模块对System Prompt优化调试，也可以根据对应System Prompt在实际对话Agent中的表现来进行迭代修改，不断完善你Agent的System Prompt。
通过根据实际使用的反馈改进System Prompt，你可以持续的优化Agent的性能。


### AbTest模块

为了方便大家调试优化System Prompt，我们提供了`PromptAbTestModule`模块，具体使用如下例子。

```python
from agentscope.modules.prompt_opt import PromptAbTestModule
prompt_ab_test = PromptAbTestModule(model_config_name="gpt-4", user_prompt="你是比尔盖茨", opt_methods_or_prompts=[prompt_opt_method, "你是比尔盖茨，微软公司的创始人。"])
```

你可以展示各个方法优化后的System Prompt。

``` python
abtest.show_optimized_prompts()
```

可以评估user_prompt、各个方法优化后的System Prompt对不同query的效果。

```
abtest.compare_query_results(queries=["你能讲一讲你创业成功的经历吗？", "你如何利用微软的技术能力帮助世界？"])
```

你也可以使用多轮对话的方式，与在system prompt的agent进行对话。

```
abtest.compare_with_dialog()
```

### PromptAgentOpt模块

除了`PromptAbTestModule`模块，我们还提供了`PromptAgentOpt`模块，可以自行根据用户与Agent的对话历史去总结需要补充的System Prompts。

```python

dialog_agent = DialogAgent(
    name="xxx",
    sys_prompt="xxx",
    model_config_name="gpt-3.5-turbo",  # replace by your model config name
)
user_agent = UserAgent()

prompt_agent_opt = PromptAgentOpt(agent=dialog_agent)

# 与Dialog Agent对话
x = None
while x is None or x.content != "exit":
    x = sequentialpipeline([dialog_agent, user_agent], x)

prompt_agent_opt.optimize()

```


希望我们的Prompt优化模块能为大家带来使用便利！

[[回到顶部]](#209-prompt-opt-zh)
