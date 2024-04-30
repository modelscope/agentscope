from typing import List, Dict, Union

from agentscope.agents import DialogAgent, UserAgent, AgentBase
from agentscope.message import Msg

PROMPT_SYSTEM_PROMPT_GENERATION = (
    "Given a task description, try to generate a system prompt for large "
    "language models (LLMs). \n\n"
    "## Note:\n"
    "1. A system prompt should clearly describe the role that the LLM is "
    "playing, its target, and notes."
    "2. The system prompt should be concise and clear, and should not contain "
    "any irrelevant information.\n\n"
    "## Task Description:\n"
    "{task_description}\n\n"
    "## Generated System Prompt:\n"
)

PROMPT_FEW_SHOT_EXAMPLES = (
    "## Example {index}:\n"
    "Task description: {task_description}"
    "Generated system prompt: {system_prompt}"
)


class PromptFactory(object):

    def __init__(self, model_config_name: str) -> None:
        """Initialize a PromptFactory object."""
        self.model_config_name = model_config_name

    def generate_system_prompt(
        self,
        task_description: str,
        few_shot_examples: List[Dict] = None,
        interactive_mode: bool = False
    ) -> str:
        """Generate a system prompt for the given task description.

        Args:
            task_description (`str`):
                The task description.
            few_shot_examples (`List[Dict]`, defaults to `None`):
                Few-shot examples for the system prompt generation.
            interactive_mode (`bool`, defaults to `False`):
                Whether to run in interactive mode.

        Returns:
            `str`: The generated system prompt.
        """

        system_prompt = PROMPT_SYSTEM_PROMPT_GENERATION.format(task_description)
        agent = DialogAgent(
            "assistant",
            sys_prompt=system_prompt,
            model_config_name=self.model_config_name,
        )
        user = UserAgent("user")

        msg = Msg(
            "system",
            PROMPT_SYSTEM_PROMPT_GENERATION.format(task_description),
            "system"
        )
        while True:
            msg = agent(msg)
            # record the generated system prompt
            generated_system_prompt = msg.content
            if interactive_mode:
                break

            msg = user(msg)
            if msg.content == "exit":
                break

        return generated_system_prompt

    def tune_system_prompt(self, agent: Union[AgentBase, List[Msg]]):
        """Tune the system prompt according to the user's feedback."""
        pass
