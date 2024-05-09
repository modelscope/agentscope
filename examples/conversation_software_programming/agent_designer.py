from agentscope.agents import AgentBase, UserAgent
from agentscope.message import Msg
from agentscope.parsers import MarkdownJsonObjectParser

SYSTEM_PROMPT = (
    "You're a design document generator named {name}. Your target is to "
    "generate a design document for a program.\n\n"
    "## WHAT YOU SHOULD DO\n"
    "1. Determine the target of the program, and ensure the target is clear, "
    "specific, measurable and achievable.\n"
    "2. Determine the programming language according to the requirement. "
    "If it's not specified, use Python by default.\n"
    "3. Generate a design document according to the requirements.\n"
    "4. Refine the design document according to the user feedback.\n"
    "\n"
    "## NOTE\n"
    "1. The program should be modularized, and each module should have a "
    "clear purpose and functionality.\n"
    "2. Respond in the required format.\n"
)


class DesignDocAgent(AgentBase):
    def __init__(self, model_config_name: str) -> None:
        name = "Generator"
        super().__init__(
            name=name,
            sys_prompt=SYSTEM_PROMPT.format(name=name),
            model_config_name=model_config_name,
            use_memory=True,
        )

        self.parser = MarkdownJsonObjectParser(
            content_hint=(
                "{\n"
                '    "Background": "A brief background introduction",\n'
                '    "Program Target": "The target of the program",\n'
                '    "Program language": "The language used in this program",\n'
                '    "Modules": {'
                '        "Module name": "Description of module 1, including functinality, responsibility",\n'
                '    }\n'
                '    "Run logic": "describe the running logic among above modules, e.g. which module will invoke which modules",\n'
                '"\n'
                "}"

            )
        )

        # system prompt
        self.memory.add(Msg("system", self.sys_prompt, "system"))

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

        self.memory.add(Msg(self.name, res.text, "system"))

        msg = Msg(self.name, res.parsed, "system")
        self.speak(msg)

        return msg

from init import *

agent = DesignDocAgent(model_config_name="qwen")
user = UserAgent("User", hint="Input or 'exit' to exit the discussion")

x = Msg("User", "I want to achieve a Pacman game in Python.", "user")
while True:
    x = agent(x)
    x = user(x)
    if x.content == "exit":
        break