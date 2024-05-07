from agentscope.agents import AgentBase
from agentscope.parsers import MarkdownJsonObjectParser

SYSTEM_PROMPT = """You're a design document generator named "{name}". Your target is to generate a design document to describe the program structure and logic."""


class DesignDocAgent(AgentBase):
    def __init__(self, model_config_name: str) -> None:
        name = "Generator"
        super().__init__(
            name=name,
            sys_prompt=SYSTEM_PROMPT.format(name),
            model_config_name=model_config_name,
            use_memory=True,
        )

        self.parser = MarkdownJsonObjectParser(
            content_hint=(
                "{\n"
                '    "Target": "",\n'
                '    "Background": "",\n'
                '    "Modules": [],\n'
                '    "Run logic": ""\n'
                "}"

            )
        )