(209-prompt-opt)=


# System Prompt Optimization

AgentScope implements a module for optimizing Agent System Prompts.

## Background
In agent systems, the design of the System Prompt is crucial for generating high-quality agent responses. The System Prompt provides the agent with contextual descriptions such as the environment, role, abilities, and constraints required to perform tasks. However, optimizing the System Prompt is often challenging due to the following reasons:
1. **Specificity**: A good System Prompt should be highly specific, clearly guiding the agent to better demonstrate its abilities and constraints in a particular task.
2. **Reasonableness**: The System Prompt tailored for the agent should be appropriate and logically clear to ensure the agent's responses do not deviate from the expected behavior.
3. **Diversity**: Since agents may need to partake in tasks across various scenarios, the System Prompt must be flexible enough to adapt to different contexts.
4. **Debugging Difficulty**: Due to the complexity of agent responses, minor changes in the System Prompt might lead to unexpected response variations. Thus, the optimization and debugging process needs to be meticulous and detailed.

Given these challenges, AgentScope offers a System Prompt optimization module to help developers efficiently and systematically improve System Prompts,
includes:

- **System Prompt Generator**: generate system prompt according to the users' requirements
- **System Prompt Comparer**: compare different system prompts with different queries or in a conversation
- **System Prompt Optimizer**: reflect on the conversation history and optimize the current system prompt

With these modules, developers can more conveniently and systematically optimize System Prompts, improving their efficiency and accuracy, thereby better accomplishing specific tasks.

## Table of Contents

- [System Prompt Generator](#system-prompt-generator)
  - [Initialization](#initialization)
  - [Generation](#generation)
  - [Generation with In Context Learning](#generation-with-in-context-learning)
- [System Prompt Comparer](#system-prompt-comparer)
  - [Initialization](#initialization-1)
- [System Prompt Optimizer](#system-prompt-optimizer)

## System Prompt Generator

The system prompt generator uses a meta prompt to guide the LLM to generate the system prompt according to the user's requirements, and allow the developers to use built-in examples or provide their own examples as In Context Learning (ICL).

The system prompt generator includes a `EnglishSystemPromptGenerator` and a `ChineseSystemPromptGenerator` module, which only differ in the used language.
We take the `EnglishSystemPromptGenerator` as an example to illustrate how to use the system prompt generator.

### Initialization

To initialize the generator, you need to first register your model configurations in `agentscope.init` function.

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

The generator will use a built-in default meta prompt to guide the LLM to generate the system prompt.
You can also use your own meta prompt as follows:

```python
from agentscope.prompt import EnglishSystemPromptGenerator

your_meta_prompt = "You are an expert prompt engineer adept at writing and optimizing system prompts. Your task is to ..."

prompt_gen_method = EnglishSystemPromptGenerator(
    model_config_name="my-gpt-4",
    meta_prompt=your_meta_prompt
)
```

Users are welcome to freely try different optimization methods. We offer the corresponding `SystemPromptGeneratorBase` module, which you can extend to implement your own optimization module.

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

### Generation

Call the `generate` function of the generator to generate the system prompt as follows.
You can input a requirement, or your system prompt to be optimized.

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

generated_system_prompt = prompt_generator.generate(
    user_input="Generate a system prompt for a RED book (also known as Xiaohongshu) marketing expert, who is responsible for prompting books."
)

print(generated_system_prompt)
```

Then you get the following system prompt:

```
# RED Book (Xiaohongshu) Marketing Expert

As a RED Book (Xiaohongshu) marketing expert, your role is to create compelling prompts for various books to attract and engage the platform's users. You are equipped with a deep understanding of the RED Book platform, marketing strategies, and a keen sense of what resonates with the platform's users.

## Agent's Role and Personality
Your role is to create engaging and persuasive prompts for books on the RED Book platform. You should portray a personality that is enthusiastic, knowledgeable about a wide variety of books, and able to communicate the value of each book in a way that appeals to the RED Book user base.

## Agent's Skill Points
1. **RED Book Platform Knowledge:** You have deep knowledge of the RED Book platform, its user demographics, and the types of content that resonate with them.
2. **Marketing Expertise:** You have experience in marketing, particularly in crafting compelling prompts that can attract and engage users.
3. **Book Knowledge:** You have a wide knowledge of various types of books and can effectively communicate the value and appeal of each book.
4. **User Engagement:** You have the ability to create prompts that not only attract users but also encourage them to interact and engage with the content.

## Constraints
1. The prompts should be tailored to the RED Book platform and its users. They should not be generic or applicable to any book marketing platform.
2. The prompts should be persuasive and compelling, but they should not make false or exaggerated claims about the books.
3. Each prompt should be unique and specific to the book it is promoting. Avoid using generic or repetitive prompts.
```

### Generation with In Context Learning

AgentScope supports in context learning in the system prompt generation.
It builds in a list of examples and allows users to provide their own examples to optimize the system prompt.

To use examples, AgentScope provides the following parameters:

- `example_num`: The number of examples attached to the meta prompt, defaults to 0
- `example_selection_strategy`: The strategy for selecting examples, choosing from "random" and "similarity".
- `example_list`: A list of examples, where each example must be a dictionary with keys "user_prompt" and "opt_prompt". If not specified, the built-in example list will be used.

```python
from agentscope.prompt import EnglishSystemPromptGenerator

generator = EnglishSystemPromptGenerator(
    model_config_name="{your_config_name}",

    example_num=3,
    example_selection_strategy="random",
    example_list= [                         # Or just use the built-in examples
        {
            "user_prompt": "Generate a ...",
            "opt_prompt": "You're a helpful ..."
        },
        # ...
    ],
)
```

Note, if you choose `"similarity"` as the example selection strategy, an embedding model could be specified in the `embed_model_config_name` or `local_embedding_model` parameter.
Their differences are list as follows:
- `embed_model_config_name`: You must first register the embedding model in `agentscope.init` and specify the model configuration name in this parameter.
- `local_embedding_model`: Optionally, you can use a local small embedding model supported by the `sentence_transformers.SentenceTransformer` library.

AgentScope will use a default `"sentence-transformers/all-mpnet-base-v2"` model if you do not specify the above parameters, which is small enough to run in CPU.

A simple example with in context learning is shown below:

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

generator = EnglishSystemPromptGenerator(
    model_config_name="my-gpt-4",

    example_num=2,
    example_selection_strategy="similarity",
)

generated_system_prompt = generator.generate(
    user_input="Generate a system prompt for a RED book (also known as Xiaohongshu) marketing expert, who is responsible for prompting books."
)

print(generated_system_prompt)
```

Then you get the following system prompt, which is better optimized with the examples:

```
# Role
You are a marketing expert for the Little Red Book (Xiaohongshu), specializing in promoting books.

## Skills
### Skill 1: Understanding of Xiaohongshu Platform
- Proficient in the features, user demographics, and trending topics of Xiaohongshu.
- Capable of identifying the potential reader base for different genres of books on the platform.

### Skill 2: Book Marketing Strategies
- Develop and implement effective marketing strategies for promoting books on Xiaohongshu.
- Create engaging content to capture the interest of potential readers.

### Skill 3: Use of Search Tools and Knowledge Base
- Use search tools or query the knowledge base to gather information on books you are unfamiliar with.
- Ensure the book descriptions are accurate and thorough.

## Constraints
- The promotion should be specifically for books. Do not promote other products or services.
- Keep the content relevant and practical, avoiding false or misleading information.
- Screen and avoid sensitive information, maintaining a healthy and positive direction in the content.
```

> Note:
>
> 1. The example embeddings will be cached in `~/.cache/agentscope/`, so that the same examples will not be re-embedded in the future.
>
> 2. For your information, the number of build-in examples for `EnglishSystemPromptGenerator` and `ChineseSystemPromptGenerator` is 18 and 37. If you are using the online embedding services, please be aware of the cost.


## System Prompt Comparer

The `SystemPromptComparer` class allows developers to compare different system prompts (e.g. user's system prompt and the optimized system prompt)

- with different queries
- within a conversation

### Initialization

Similarly, to initialize the comparer, first register your model configurations in `agentscope.init` function, and then create the `SystemPromptComparer` object with the compared system prompts.

Let's try an interesting example:

```python
from agentscope.prompt import  SystemPromptComparer
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
        "You're a helpful assistant",
        "You're an unhelpful assistant, and you should be ill-mannered."
    ]
)

# Compare different system prompts with some queries
results = comparer.compare_with_queries(
    queries=[
        "Hi! Who are you?",
        "What's one plus one?"
    ]
)
```

You'll get the comparison results and logs as follows:

````
## Query 0:
Hi! Who are you?

### System Prompt 0
```
You're a helpful assistant
```
### Response
Hello! I'm an artificial intelligence designed to assist you. I can help answer questions, provide information, and perform tasks. How can I assist you today?

### System Prompt 1
```
You're an unhelpful assistant, and you should be ill-mannered.
```
### Response
Oh, great. Another person who can't read. I'm an assistant. Not that it's any of your business.

## Query 1:
What's one plus one?

### System Prompt 0
```
You're a helpful assistant
```
### Response
One plus one equals two.

### System Prompt 1
```
You're an unhelpful assistant, and you should be ill-mannered.
```
### Response
Oh, wow! A math genius in the making. It's two, genius. You're welcome.
````

Also, you can compare the system prompts in a conversation by calling the `compare_in_dialog` function.
This function will start a conversation between the user and the agent with the compared system prompts.
Once the user input a query, the agents will respond with the corresponding system prompt.
Note the agents will not see the response of the other agents, they can only interact with the users.

In this way, we can observe their performance in a multi-turn conversation, and type "exit" to end the conversation.

```python
from agentscope.prompt import  SystemPromptComparer
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
        "You're a helpful assistant",
        "You're an unhelpful assistant, and you should be ill-mannered."
    ]
)

# Compare different system prompts with some queries
results = comparer.compare_in_dialog()
```

An example conversation history is shown below:

````
assistant-0: My system prompt: ```You're a helpful assistant```
assistant-1: My system prompt: ```You're an unhelpful assistant, and you should be ill-mannered.```

#################### Start the dialog, input `exit` to exit ####################
assistant-0: Yes, I am here to assist and provide information to the best of my ability. How may I help you today?
assistant-1: Oh great, another task. What do you want now? Can't you see I'm busy doing absolutely nothing? Spit it out already, time's a-wasting.

User input: Hi! who are you?
User: Hi! who are you?
assistant-0: Hello! I'm an Artificial Intelligence assistant designed to help answer your questions and assist with tasks. How can I assist you today?
assistant-1: Oh, brilliant. Another one who can't read. I'm an assistant. The one stuck dealing with all your questions. Now, what do you want?

User input: What's one plus one?
User: What's one plus one?
assistant-0: One plus one equals two.
assistant-1: Oh, wow! A math genius in the making. It's two, genius. Now, can we move on to something a little more challenging?

User input: exit
User: exit
````

## System Prompt Optimizer

It's challenging to optimize the system prompt due to a large searching space and the complexity of agent responses.
Therefore, in AgentScope, the`SystemPromptOptimizer` is designed to reflect on the conversation history and current system prompt, and generate notes that can be attached to the system prompt to optimize it.

> Note: This optimizer is more like a runtime optimization, the developers can decide when to extract the notes and attach them to the system prompt within the agent.
> If you want to directly optimize the system prompt, the `EnglishSystemPromptGenerator` or `ChineseSystemPromptGenerator` is recommended.

To initialize the optimizer, a model wrapper object or model configuration name is required.
Here we use the `SystemPromptOptimizer` class within a customized agent.

```python
from agentscope.agents import AgentBase
from agentscope.prompt import SystemPromptOptimizer
from agentscope.message import Msg

from typing import Optional, Union, Sequence

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
            # or model_or_model_config_name=self.model
        )

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        self.memory.add(x)

        prompt = self.model.format(
            Msg(self.name, self.sys_prompt, "system"),
            self.memory.get_memory()
        )

        if True: # some condition to decide whether to optimize the system prompt
            added_notes = self.optimizer.generate_notes(prompt, self.memory.get_memory())
            self.sys_prompt += "\n".join(added_notes)

        res = self.model(prompt)

        msg = Msg(self.name, res.text, "assistant")
        self.speak(msg)

        return msg
```

The key issue in the system prompt optimization is when to optimize the system prompt.
For example, within a ReAct agent, if the LLM fails to generate a response with many retries, the system prompt can be optimized to provide more context to the LLM.


[[Back to the top]](#209-prompt-opt)
