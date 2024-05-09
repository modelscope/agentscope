from agentscope.agents import UserAgent, DictDialogAgent
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
    "one question at a time, but if the user ask to generate all requirements "
    "at once, just follow user's request. \n"
)

discuss_parser = MarkdownJsonDictParser(
    content_hint="""{
        "speak": "what you speak to the user",
        "finish": true/false, once you finish asking questions and ready to generate requirements list, set to true, otherwise false,
    }""",
    required_keys=["speak", "finish"],
    keys_to_speak="speak",
    keys_to_others=["speak", "finish"],
)

generate_parser = MultiTaggedContentParser(
    TaggedContent(
        "requirements",
        "[requirements]",
        "1. {requirement title}: {description}\n2. {requirement title}: {description}\n...",
        "[/requirements]",
    ),
)

from init import *

user = UserAgent()
manager = DictDialogAgent(
    name="Manager",
    sys_prompt=SYSTEM_PROMPT.format(name="Manager"),
    model_config_name="qwen"
)

manager.set_parser(discuss_parser)

x = None
while True:
    x = user(x)
    if x == "exit":
        break
    x = manager(x)
    if x.content.get("finish", False):
        break

msg = Msg(
    "system",
    "Now generate the requirements list based on the discussion. "
    "Note each requirement takes one line.",
    "system",
    echo=True,
)
manager.set_parser(generate_parser)

res = manager(msg)


print(res.content)
