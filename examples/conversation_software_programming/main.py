import agentscope
from agentscope.agents import AgentBase, UserAgent
from agentscope.message import Msg
from agentscope.parsers import MultiTaggedContentParser, TaggedContent, \
    MarkdownCodeBlockParser


class ProgramAgent(AgentBase):

    def __init__(self, model_config_name: str) -> None:
        super().__init__(
            name="Programmer",
            sys_prompt="",
            model_config_name=model_config_name,
            use_memory=True,
        )

        self.memory.add(Msg("system", self.sys_prompt, "system"))

        # Init parser
        self.parser = MarkdownCodeBlockParser(language_name="python")

    def reply(self, x: dict = None) -> dict:
        self.memory.add(x)

        prompt = self.model.format(
            self.memory.get_memory(),
            Msg("system", self.parser.format_instruction, "system"),
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

msg = None
while True:
    msg = agent.reply(msg)
    msg = user.reply(msg)
    if msg.content == "exit":
        break