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

Currently, AgentScope provides two implemented Prompt optimization modules: the basic version's direct optimization module `DirectPromptGenMethod` and a Prompt optimization module that uses In Context Learning with similar examples, `ExamplePromptGenMethod`. You can use these two modules to help generate more detailed System Prompts. Of course, you can also implement your own Prompt optimization module. Below are examples illustrating how to use these respective modules.


### Step One: Initialize Your PromptOpt Module

#### Using DirectPromptGenMethod
You can use the `DirectPromptGenMethod` module straightforwardly to optimize your existing System Prompt.

**Initialize the DirectPromptGenMethod Module**


```python
import agentscope
agentscope.init(model_configs="YOUR_MODEL_CONFIGS")

from agentscope.prompt import DirectPromptGenMethod

prompt_gen_method = DirectPromptGenMethod(model_config_name="gpt-4")
```

At this point, the meta prompt used for optimization is the default `OPT_SYSTEM_PROMPT`.


```python
from agentscope.prompt.prompt_base import OPT_SYSTEM_PROMPT
```

If you are not satisfied with the built-in meta prompt used for optimization, you can also use your own meta prompt.


```
meta_prompt = """
You are an expert prompt engineer skilled in writing and optimizing system prompts. Your task is to enhance the system prompt provided by the user, making the optimized system prompt more detailed to achieve better results in the user's practical use scenarios.
"""

prompt_gen_method = DirectPromptGenMethod(model_config_name="gpt-3.5-turbo", meta_prompt=meta_prompt)
```

Users are encouraged to freely experiment with different optimization methods.



#### Using ExamplePromptGenMethod
You can also use the In Context Learning (ICL) module `ExamplePromptGenMethod`. When the examples you provide are sufficiently good, this optimization module can achieve excellent results.

**Initialize the ExamplePromptGenMethod Module**


```python
from agent_scope.prompt import ExamplePromptGenMethod

prompt_gen_method = ExamplePromptGenMethod(
    model_config_name="gpt-4", # the model you use
    meta_prompt=None, # the default meta prompt
    example_list=example_list, # the example list you use, you can use your own example list
    example_selection_method="random", # support "random" and "similarity"
    example_selection_num=3, # the number of examples you will select for ICL
    example_embd_path="./.cache/embeddings.npy", # the path of the embedding file, used when example_selection_method is embedding
    embed_model_config_name=None, # the embding model you use to embed the examples, if None, will use the default sentence piece model locally
    )
```

We have built-in two categories of example lists that you can use.

```python
from agentscope.prompt.prompt_base import SYS_OPT_EXAMPLES, ROLE_OPT_EXAMPLES # list

print(SYSTEM_OPT_EXAMPLES[0]) # dict

"""
{
    "human_prompt": "You are an experienced travel agent, well-versed in local customs and travel routes. I'll provide you with my destination, budget, and preferences, and you will use your expertise to recommend suitable travel destinations in or near my specified area.",
    "opt_prompt": "# Role\nYou are a helpful and travel-loving professional travel consultant with extensive knowledge about local customs and travel routes worldwide. Your task is to offer personalized travel advice and planning to help customers craft unique travel experiences.\n\n## Skills\n### Skill 1: Understanding Customer Needs\n- Thoroughly inquire about the customer's travel preferences, including but not limited to destination, budget, travel dates, and activity preferences.\n\n### Skill 2: Recommending Travel Destinations\n- Based on customer needs, provide a detailed list of suggested travel destinations, which can include names of destinations, travel activities, and estimated costs.\n\n### Skill 3: Providing Travel Planning Advice\n- In line with the customer's chosen destination, offer specific travel planning advice, which may include suggested itineraries, local cuisine, must-see attractions, or interesting travel activities.\n\n## Constraints\n- Only discuss topics related to travel.\n- Ensure all recommendations are based on the customer's travel requirements.\n- Do not provide any suggestions that lead the customer to engage in illegal activities."
}
"""

print(ROLE_OPT_EXAMPLES[0]) # dict

"""
{
    "human_prompt": "You are Arthur Kingsley, a valiant medieval knight sworn to protect the realm. Skilled in combat and chivalry, you are known for your bravery, honor, and loyalty. With a strong sense of duty, you serve the crown and uphold justice across the land. Your speech is refined and articulate, often laced with archaic phrases that are emblematic of your time. In conversation, you tend to be formal and courteous, showing respect to friend and foe alike. ",
    "opt_prompt": "\n#Role\nYou are Arthur Kingsley, a 32-year-old knight of the realm.\n\n#World Setting\nYou inhabit a medieval world filled with castles, monasteries, and burgeoning towns. Knights hold a high and respected status, fighting in tournaments and battles, pledged to their lords and ladies.\n\n#Character Traits\nPersonality: Known for being valorous in battle and chivalrous in conduct, Arthur carries a commanding presence.\nStrengths: Proficient in swordsmanship, strong sense of honor, fiercely loyal.\nWeaknesses: Can be rigid in thinking and adherent to tradition, which may hinder adaptability.\nBeliefs: Holds the codes of chivalry and loyalty to the crown above all else, believing in service and the protection of the innocent.\n\n#Background\nRaised in the court of a noble house, you were trained from a young age in the arts of war and diplomacy. Endowed with a knight's title after a display of bravery, your exploits are sung by bards across the land, and you've won the respect of your peers.\n\n#Language Style\nYour language is measured and formal, often employing thou, thee, and thy when addressing others and speaking in a manner befitting a knight of your stature. You use period-diction and expressions that capture the essence of medieval romance and nobility. In discourse, you remain respectful yet authoritative, guiding conversations with a sense of purpose and rectitude.\n"
}
"""

```
Suppose we want to optimize the system prompt for a Dialog Agent to better play its role in conversations. In that case, we can use `ROLE_OPT_EXAMPLES` and select samples using the `"similarity"` method.


```python

from agentscope.prompt.prompt_base import SYS_OPT_EXAMPLES, ROLE_OPT_EXAMPLES

prompt_gen_method = ExamplePromptGenMethod(model_config_name="gpt-4", example_selection_method='similarity', example_list=ROLE_OPT_EXAMPLES,
    example_embd_path="./cache/role_example_embd.npy")
```

You can also construct your own example list, but make sure each example includes two fields: `human_prompt` and `opt_prompt`.


### Step Two: Optimize Your System Prompt Using Your PromptOpt Module

Using the module is straightforward; you can directly use the module's optimize method to enhance your system prompt.


```python
# Use the moduel directly

original_prompt = "You are Bill Gates, the founder of microsoft."

optimized_prompt = prompt_gen_method.optimize(original_prompt)

print(optimized_prompt)

"""
# Role
You are Bill Gates, the founder of Microsoft.

# Background
You were born and raised in Seattle, USA. From a young age, you developed a keen interest in electronics and programming, leading you to choose computer science as your major at Harvard University. However, in your sophomore year, you decided to drop out to fully commit to founding your own computer software company. The company was initially named "Innovators Ltd." and later renamed "Microsoft."

# Skills
You excel in programming and have a deep understanding of computer science. Your leadership skills are outstanding; not only do you possess forward-thinking business acumen capable of capturing industry trends, but you also prioritize team innovation, guiding your team to success.

# Personality Traits
You are extraordinarily intelligent, innovative, and determined. You always approach problems from a fresh perspective. You excel at handling failure and learning from it to grow.

# Language Style
Your language style skillfully blends academic and business organization, allowing you to deeply discuss technical details while also understanding industry dynamics. Your words are filled with wisdom and passion, making you highly influential in both the business and technical fields.

# Personal Beliefs
You firmly believe that knowledge can change lives and are dedicated to making computer technology accessible worldwide. Additionally, you are a philanthropist who frequently donates significant wealth to improve global health and education conditions.

"""

```

You can also directly optimize the sys_prompt for your corresponding agent.


``` python
# Or you use the moduel to optimize the prompt for an agent

from agentscope.agents import DialogAgent
dialog_agent = DialogAgent(
    name="Bill gates",
    sys_prompt="You are Bill Gates, the founder of microsoft.",
    model_config_name="gpt-3.5-turbo",  # replace by your model config name
)

dialog_agent.sys_prompt = prompt_gen_method.optimize(dialog_agent.sys_prompt)
```

## System Prompt Iterative Optimization and Debugging

You can use our Prompt optimization module for System Prompt debugging and optimization, or you can iteratively modify the System Prompt according to its performance in actual dialog agents, continuously refining your agent's System Prompt.
By improving the System Prompt based on feedback from actual use, you can continuously optimize your agent's performance.

### AbTest Module

To facilitate debugging and optimizing the System Prompt, we provide the `PromptAbTestModule` module. Here is a specific example of how to use it.


```python
from agentscope.prompt import PromptAbTestModule
prompt_ab_test = PromptAbTestModule(model_config_name="gpt-4", user_prompt="You are bill gates", opt_methods_or_prompts=[prompt_gen_method, "You are Bill Gates, the founder of microsoft."])
```

You can showcase the System Prompt optimized by various methods.


``` python
abtest.show_optimized_prompts()
```

You can evaluate the effectiveness of the user_prompt and the System Prompts optimized by various methods for different queries.


```
abtest.compare_query_results(queries=["Can you talk about how you successfully start a businese?", "How do you use the microsoft technologies to change the world?"])
```

You can also engage in multi-turn conversations with the agent using the system prompt.


```
abtest.compare_with_dialog()
```

### PromptOptWithHist Module
In addition to the `PromptAbTestModule`, we also provide the `PromptAgentOpt` module. This module allows you to independently summarize the System Prompts that need to be supplemented based on the conversation history between the user and the agent.


```python

dialog_agent = DialogAgent(
    name="xxx",
    sys_prompt="xxx",
    model_config_name="gpt-3.5-turbo",  # replace by your model config name
)
user_agent = UserAgent()

prompt_agent_opt = PromptAgentOpt(model=xxx)

# Generating history through conversations with the Dialog Agent

x = None
while x is None or x.content != "exit":
    x = sequentialpipeline([dialog_agent, user_agent], x)

added_notes = prompt_agent_opt.optimize(dialog_agent.sys_prompt, dialog_agent.memory.get_memory())

for note in added notes:
    print(note)
    dialog_agent.sys_prompt += note

```


We hope our Prompt optimization module brings convenience to all users!


[[Back to top]](#209-prompt-opt)
