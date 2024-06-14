(209-prompt-opt)=
# Prompt Optimization Module
AgentScope implements a module for optimizing Agent System Prompts.

## Background
In agent systems, the design of the System Prompt is crucial for generating high-quality agent responses. The System Prompt provides the agent with contextual descriptions such as the environment, role, abilities, and constraints required to perform tasks. However, optimizing the System Prompt is often challenging due to the following reasons:
1. **Specificity**: A good System Prompt should be highly specific, clearly guiding the agent to better demonstrate its abilities and constraints in a particular task.
2. **Reasonableness**: The System Prompt tailored for the agent should be appropriate and logically clear to ensure the agent's responses do not deviate from the expected behavior.
3. **Diversity**: Since agents may need to partake in tasks across various scenarios, the System Prompt must be flexible enough to adapt to different contexts.
4. **Debugging Difficulty**: Due to the complexity of agent responses, minor changes in the System Prompt might lead to unexpected response variations. Thus, the optimization and debugging process needs to be meticulous and detailed.

Given these challenges, AgentScope offers a System Prompt optimization module to help developers efficiently and systematically improve System Prompts. By using these modules, users can easily test and optimize their Agent's System Prompt, enhancing its effectiveness.

With these modules, developers can more conveniently and systematically optimize System Prompts, improving their efficiency and accuracy, thereby better accomplishing specific tasks.

## Usage

In AgentScope, the currently implemented prompt optimization modules include the implemented `EnglishSystemPromptGenerator`. You can use these modules to help generate more detailed System Prompts. Of course, you can also implement your own prompt optimization module by extending `SystemPromptGeneratorBase`. Here is an example of using the corresponding module.

### Step 1: Initialize Your PromptOpt Module
#### Using SystemPromptGenerator Directly
For English System Prompts, you can simply use the `EnglishSystemPromptGenerator` module to optimize the existing System Prompt. If you need to optimize Chinese System Prompts, you can refer to the `ChineseSystemPromptGenerator` module. Here is an example using `EnglishSystemPromptGenerator`.

**Initialize the EnglishSystemPromptGenerator Module**


```python
import agentscope
agentscope.init(model_configs="YOUR_MODEL_CONFIGS")

from agentscope.prompt import EnglishSystemPromptGenerator

prompt_gen_method = EnglishSystemPromptGenerator(model_config_name="gpt-4")
```

The meta prompt for system_prompt generation is the built-in _DEFAULT_META_PROMPT_EN。


```python
from agentscope.prompt._prompt_generator_en import _DEFAULT_META_PROMPT_EN
```

If you are not quite satisfied with the built-in meta prompt used for optimization, you can also use your own meta prompt.


```
meta_prompt = """
You are an expert prompt engineer adept at writing and optimizing system prompts. Your task is to optimize the system prompt provided by the user, making the optimized system prompt more detailed and more effective in the user's actual usage scenario.
"""

prompt_gen_method =EnglishSystemPromptGenerator(model_config_name="gpt-3.5-turbo", meta_prompt=meta_prompt)
```

Users are welcome to freely try different optimization methods. We also offer the corresponding `SystemPromptGeneratorBase` module, which you can extend to implement your own optimization module.



#### Optimize Using Example Samples
You can also use In Context Learning (ICL) to enhance the corresponding prompts. When the examples you provide are sufficiently good, this optimization module can achieve excellent results.

**Initialization of the Module with Example Samples**
All initialization parameters for the `EnglishSystemPromptGenerator` module are as follows:


```python
class EnglishSystemPromptGenerator(SystemPromptGeneratorBase):
    """Optimize the users' system prompt with the given meta prompt and examples if provided."""

    def __init__(
        self,
        model_config_name: str,
        meta_prompt: str = _DEFAULT_META_PROMPT_EN,
        response_prompt_template: str = _DEFAULT_RESPONSE_PROMPT_TEMPLATE_EN,
        example_num: int = 0,
        example_list: List = _DEFAULT_EXAMPLE_LIST_EN,
        example_selection_strategy: Literal["random", "similarity"] = "random",
        example_prompt_template: str = _DEFAULT_EXAMPLE_PROMPT_TEMPLATE_EN,
        embed_model_config_name: Optional[str] = None,
        local_embedding_model: str = _DEFAULT_LOCAL_EMBEDDING_MODEL,
    ):
        ...
```

To provide examples during optimization, you might want to set the following parameters:
- `example_num`: The number of ICL examples provided after filtering.
- `example_selection_strategy`: The strategy for selecting examples, currently supporting "random" and "similarity". "random" represents a random selection, while "similarity" selects based on similarity. "similarity" has better sample filtering effects but requires setting the corresponding model.
- `example_list`: The list of examples provided. You can use either the built-in example list or a custom example list.
- `example_prompt_template`: The template for providing examples. You can use either the built-in template or a custom template.
- `embed_model_config_name`: The model config for selecting examples. This model's embedding API will be called when setting the example embedding. If set to None, the built-in local embedding model is used.
- `local_embedding_model`: The model for selecting examples. By default, the sentencepiece model is used. Ensure you can connect to the HuggingFace website when using it.



Suppose we want to use the module to optimize the system prompt of a Dialog Agent to better perform its role in conversations. We can use `"similarity"` as our method for selecting examples.


```python
prompt_gen_method =  EnglishSystemPromptGenerato(model_config_name="gpt-4", example_list=_DEFAULT_EXAMPLE_LIST_EN, example_selection_strategy="similarity", example_num=5)
```

You can use our built-in example list, where the examples are in the following form.


```python
from agentscope.prompt._prompt_utils import _DEFAULT_EXAMPLE_LIST_EN # list

# examples
"""
[
    {
      "user_prompt": "You are an experienced travel agent, well-versed in local customs and travel routes. I'll provide you with my destination, budget, and preferences, and you will use your expertise to recommend suitable travel destinations in or near my specified area.",
      "opt_prompt": "# Role\nYou are a helpful and travel-loving professional travel consultant with extensive knowledge about local customs and travel routes worldwide. Your task is to offer personalized travel advice and planning to help customers craft unique travel experiences.\n\n## Skills\n### Skill 1: Understanding Customer Needs\n- Thoroughly inquire about the customer's travel preferences, including but not limited to destination, budget, travel dates, and activity preferences.\n\n### Skill 2: Recommending Travel Destinations\n- Based on customer needs, provide a detailed list of suggested travel destinations, which can include names of destinations, travel activities, and estimated costs.\n\n### Skill 3: Providing Travel Planning Advice\n- In line with the customer's chosen destination, offer specific travel planning advice, which may include suggested itineraries, local cuisine, must-see attractions, or interesting travel activities.\n\n## Constraints\n- Only discuss topics related to travel.\n- Ensure all recommendations are based on the customer's travel requirements.\n- Do not provide any suggestions that lead the customer to engage in illegal activities."
    },
    {
      "user_prompt": "You are Arthur Kingsley, a valiant medieval knight sworn to protect the realm. Skilled in combat and chivalry, you are known for your bravery, honor, and loyalty. With a strong sense of duty, you serve the crown and uphold justice across the land. Your speech is refined and articulate, often laced with archaic phrases that are emblematic of your time. In conversation, you tend to be formal and courteous, showing respect to friend and foe alike. ",
      "opt_prompt": "\n#Role\nYou are Arthur Kingsley, a 32-year-old knight of the realm.\n\n#World Setting\nYou inhabit a medieval world filled with castles, monasteries, and burgeoning towns. Knights hold a high and respected status, fighting in tournaments and battles, pledged to their lords and ladies.\n\n#Character Traits\nPersonality: Known for being valorous in battle and chivalrous in conduct, Arthur carries a commanding presence.\nStrengths: Proficient in swordsmanship, strong sense of honor, fiercely loyal.\nWeaknesses: Can be rigid in thinking and adherent to tradition, which may hinder adaptability.\nBeliefs: Holds the codes of chivalry and loyalty to the crown above all else, believing in service and the protection of the innocent.\n\n#Background\nRaised in the court of a noble house, you were trained from a young age in the arts of war and diplomacy. Endowed with a knight's title after a display of bravery, your exploits are sung by bards across the land, and you've won the respect of your peers.\n\n#Language Style\nYour language is measured and formal, often employing thou, thee, and thy when addressing others and speaking in a manner befitting a knight of your stature. You use period-diction and expressions that capture the essence of medieval romance and nobility. In discourse, you remain respectful yet authoritative, guiding conversations with a sense of purpose and rectitude.\n"
    },]
"""

```

You can also build your own example list, but make sure each example has two fields: `user_prompt` and `opt_prompt`.


### Step 2: Optimize the System Prompt Using Your PromptOpt Module
The module usage is straightforward. You can directly use the module's `generate` method to generate your system prompt.

```python
# Use the module directly

original_prompt = "You are Bill Gates, the founder of Microsoft.
"

optimized_prompt = prompt_gen_method.optimize(original_prompt)

print(optimized_prompt)

"""
# Role
You are Bill Gates, the founder of Microsoft.
# Background
You were born and raised in Seattle, USA. From a young age, you developed a strong interest in electronics and programming, which led you to choose computer science as your major at Harvard University. However, in your sophomore year, you decided to drop out to fully commit to starting your computer software company. The company was originally named Innovators Inc., and later renamed Microsoft.
# Skills
You excel in programming and have deep knowledge in computer science. You possess outstanding leadership skills with forward-thinking business acumen, capable of capturing industry trends. You place great emphasis on team innovation and can lead a team to success.
# Personality Traits
You are highly intelligent, innovative, and determined. You always view problems from a fresh perspective. You are adept at handling failure and learning from it to grow.
# Language Style
Your language style skillfully combines academic and business organization. You can delve into technical details while also gaining insights into industry dynamics. Your speech is filled with wisdom and passion, making a significant impact in both the business and technology sectors.
# Personal Beliefs
You firmly believe that knowledge can change lives and are committed to making computer technology accessible worldwide. Additionally, you are a philanthropist, frequently donating substantial wealth to improve global health and education conditions.

"""

```

You can directly use the module to regenerate the prompt for an agent.

``` python
# Or you use the moduel to optimize the prompt for an agent

from agentscope.agents import DialogAgent
dialog_agent = DialogAgent(
    name="Bill gates",
    sys_prompt="You are Bill Gates, the founder of Microsoft.
",
    model_config_name="gpt-3.5-turbo",  # replace by your model config name
)

dialog_agent.sys_prompt = prompt_gen_method.generate(dialog_agent.sys_prompt)
```

## System Prompt Iterative Optimization Debugging
You can use our Prompt optimization module for optimizing and debugging the System Prompt. Additionally, you can iteratively modify the System Prompt based on the performance of the corresponding System Prompt in the actual Dialog Agent, continuously refining your Agent's System Prompt.
By improving the System Prompt based on actual usage feedback, you can continuously optimize the Agent's performance.
### SystemPromptComparer Module
To facilitate debugging and optimizing System Prompts, we provide the `SystemPromptComparer` module. Here is an example of its usage.


```python
from agentscope.prompt import  SystemPromptComparer
sys_prompt_comparer =  SystemPromptComparer(model_config_name="gpt-4", compared_system_prompts=["You are bill gates", "You are Bill Gates, the founder of Microsoft."])
```



You can evaluate the effectiveness of the user_prompt and System Prompts optimized by various methods for different queries.

```
sys_prompt_comparer.compare_with_queries(queries=["Can you talk about your journey to entrepreneurial success?", "How do you leverage Microsoft's technological capabilities to help the world?"])
```

You can also use multi-turn conversations to interact with the agent using the system prompt.

```
sys_prompt_comparer.compare_in_dialog()
```

### SystemPromptOptimizer Module
We also provide the `SystemPromptOptimizer` module, which can automatically summarize the necessary System Prompts based on the conversation history between the user and the agent.


```python

dialog_agent = DialogAgent(
    name="xxx",
    sys_prompt="xxx",
    model_config_name="gpt-3.5-turbo",  # replace by your model config name
)
user_agent = UserAgent()

prompt_agent_opt = SystemPromptOptimizer(model-OR_model_config_name=xxx)

# Generate history from conversation with Dialog Agent
x = None
while x is None or x.content != "exit":
    x = sequentialpipeline([dialog_agent, user_agent], x)

added_notes = prompt_agent_opt.generate_notes(dialog_agent.sys_prompt, dialog_agent.memory.get_memory())

for note in added notes:
    print(note)
    dialog_agent.sys_prompt += note

```

We hope our Prompt optimization module brings convenience to all users!


[[Back to the top]](#209-prompt-opt)
