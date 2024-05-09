from agentscope.agents import AgentBase, UserAgent
from agentscope.message import Msg
from agentscope.parsers import MarkdownJsonDictParser, \
    MultiTaggedContentParser, TaggedContent

SYSTEM_PROMPT = (
    "You're a project manager named \"{name}\". Your target is to determine "
    "the requirements of a project.\n\n"
    "## WHAT YOU SHOULD DO\n"
    "1. Discuss with the user to understand the project requirements.\n"
    "2. Determine the concrete requirements of the project.\n"
    "3. Refine the requirements according to the user feedback.\n"
    "\n"
    "## NOTE\n"
    "1. The requirements should be clear, specific, and achievable.\n"
    "2. Try your best to make the requirements concrete and specific. "
    "For example, the user want to achieve a Pacman game, you should "
    "determine how many ghosts should be involved, and how large the map "
    "should be, etc.\n"
    "4. Determine the requirements by asking questions to the user. Note ask "
    "one question at a time. \n"
)


class PMAgent(AgentBase):

    def __init__(self, model_config_name: str):
        name = "Manager"
        super().__init__(
            name=name,
            sys_prompt=SYSTEM_PROMPT.format(name=name),
            model_config_name=model_config_name,
            use_memory=True,
        )

        self.memory.add(Msg("system", self.sys_prompt, "system"))

        self.parser = MarkdownJsonDictParser(
            content_hint="""{
                "speak": "what you speak to the user",
                "finish asking": true/false, once you finish asking questions and ready to generate requirements list, set to true, otherwise false,
            }""",
            required_keys=["speak", "finish asking"],
        )

    def reply(self, x: dict = None) -> dict:
        self.memory.add(x)

        prompt = self.model.format(
            self.memory.get_memory(),
            Msg("system", self.parser.format_instruction, "system"),
        )

        res = self.model(
            prompt,
            parse_func=self.parser.parse,
            max_retries=1,
        )

        self.speak(Msg(self.name, self.parser.to_speak(res.parsed)), "system")

        msg = Msg(self.name, content=self.parser.to_memory(res.parsed), role="system", **res.parsed)

        self.memory.add(msg)
        return Msg(self.name, content=self.parser.to_return(res.parsed), role="system", **res.parsed)


from init import *

user = UserAgent()
manager = PMAgent("qwen")

parser_generate = MultiTaggedContentParser(
    TaggedContent(
        "requirements",
        "[requirements]",
        "1. {requirement title}: {description}\n2. {requirement title}: {description}\n...",
        "[/requirements]",
    )
)

x = None
while True:
    x = user(x)
    if x == "exit":
        break
    x = manager(x)
    if x["finish asking"]:
        break

msg = Msg(
    "system",
    "Now generate the requirements list based on the discussion. "
    "Note each requirement takes one line.",
    "system",
    echo=True,
)

manager.parser = parser_generate

res = manager(msg)

print(res.content)
