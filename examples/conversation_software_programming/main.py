import agentscope
from agentscope.agents import AgentBase, UserAgent, DialogAgent
from agentscope.message import Msg
from agentscope.parsers import MultiTaggedContentParser, TaggedContent, \
    MarkdownCodeBlockParser

SYSTEM_PROMPT = """You're an assistant named "{}". Your target is to write Python program to satisfy the input requirements.

## Note
1. Focus on implementing the required functionality. 
2. DO NOT generate example usage, test, etc.
3. The input arguments should have typing hints. 
"""

SYSTEM_PROMPT = """Generate a design document to describe the program structure and logic. The design document should include the following sections:

Target: Implement a python program to implement a Pacman game. 

Background: The purpose and description of the program.
Modules: What modules are needed. 
Run logic: The calling relationships and calling sequence between modules.
"""


class ProgramAgent(AgentBase):

    def __init__(self, model_config_name: str) -> None:
        name = "Programmer"
        super().__init__(
            name=name,
            sys_prompt=SYSTEM_PROMPT.format(name),
            model_config_name=model_config_name,
            use_memory=True,
        )

        self.memory.add(Msg("system", self.sys_prompt, "system"))

        # Init parser
        self.parser = MultiTaggedContentParser(
            TaggedContent("thought", "[THOUGHT]", "What you thought", "[/THOUGHT]"),
            TaggedContent("code", "```python\n", "your_python_code", "```"),
        )

    def reply(self, x: dict = None) -> dict:
        self.memory.add(x)

        prompt = self.model.format(
            self.memory.get_memory(),
            # Msg("system", self.parser.format_instruction, "system"),
        )

        print(prompt)

        res = self.model(
            prompt,
            parse_func=self.parser.parse,
            max_retries=1,
        )

        msg = Msg(self.name, res.text, "system")
        self.memory.add(msg)

        self.speak(msg)

        return msg


agentscope.init(model_configs=[
    {
        "model_type": "dashscope_chat",
        "config_name": "qwen",

        "model_name": "qwen-max",
        "api_key": "sk-7cee068707fe4885890ee272c8b14175"
    },
    {
        "model_type": "post_api_chat",
        "config_name": "gpt-4",

        "api_url": "https://api.mit-spider.alibaba-inc.com/chatgpt/api/ask",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjIyNTE4NiIsInBhc3N3b3JkIjoiMjI1MTg2IiwiZXhwIjoyMDA2OTMzNTY1fQ.wHKJ7AdJ22yPLD_-1UHhXek4b7uQ0Bxhj_kJjjK0lRM"
        },
        "json_args": {
            "model": "gpt-4",
            "temperature": 0.0,
        },
        "messages_key": "messages"
    },
    {
        "model_type": "ollama_chat",
        "config_name": "ollama",

        "model_name": "llama2",
    },
])

agent = ProgramAgent(model_config_name="qwen")
user = UserAgent("user")


# Make a plan
Planner = DialogAgent(
    name="assistant",
    sys_prompt="",
    model_config_name="qwen",
)






# Implement a python module
msg = None
while True:
    msg = agent.reply(msg)
    msg = user.reply(msg)
    if msg.content == "exit":
        break

