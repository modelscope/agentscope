# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""A agent that optimize system prompt given user dialog history."""
from agentscope.message import Msg
from agentscope.agents.agent import AgentBase


OPT_PROMPT_TEMPLATE = """
你是一个优秀的Prompt Engineer，现在你要通过添加note的方式对一个Agent的system prompt进行优化。

用户提供的原始system prompt是：
{system_prompt}

用户与之交互的dialog history是：
{dialog_history}

现在，你要
1. 判断用户与agent交互的dialog history中，是否包含显式的错误（如函数调用错误、没有遵循输入输出格式），对用户意图的误解等。
2. 对发生错误的原因进行详细分析，并且寻找对于对应错误的解决方案。
3. 根据错误原因和用户意图，写一条或几条可以添加在用户system prompt后面的注意事项note，或者exmaple形式的note，使之不要再犯同样的错误。
如果要添加的note包含example，需要格外小心，如果不确定添加的example是否正确，可以先不添加。
你添加的note应该包含在tag [prompt_note]中，例如 [prompt_note] 请注意输出仅包含json格式 [/prompt_note]。如果dialog history没有明显问题，则不需要添加任何note。
"""  # noqa

# TODO 添加example prompt：下面是几个对话示例，如何对System Prompt进行修改。


class SystemPromptOptimizationAgent(AgentBase):
    """A simple agent that optimize system prompt given user dialog history."""

    def __init__(
        self,
        name: str,
        model_config_name: str,
    ) -> None:
        """Initialize the direct prompt optimization agent.

        Arguments:
            name (`str`):
                The name of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.

        Note:
            Adding the output optimized note to the system prompt may not
            always solve the issue. It depends on the specific task
            and the model.
        """
        super().__init__(
            name=name,
            model_config_name=model_config_name,
        )

    def reply(self, x: dict = None) -> dict:
        """
        Replying to the input.

        Arguments:
            x(`Msg`): the input prompt to optimize. The input prompt
                should be a `Msg` object. The `content` field should be a dict,
                which contains the following fields:
                    - system_prompt(`str`): the system prompt to optimize.
                    - dialog_history(`str` or List[Msg]):
                    the dialog history of the user and the agent.

        Returns:
            msg(`Msg`): the output message. In the output message,
                the `content` field is the optimized prompt.

        Note:
            The output optimized prompt may not always works better than the
            original prompt. It depends on the specific task and the model.
        """
        # get the system prompt and dialog history
        assert isinstance(
            x.content,
            dict,
        ), "The input prompt should be a dict."
        assert (
            "dialog_history" in x.content and "system_prompt" in x.content
        ), "The input should have 'dialog_history' amd 'system_prompt' fields."

        system_prompt = x.content["system_prompt"]
        dialog_history = x.content["dialog_history"]

        assert type(dialog_history) in [
            str,
            list,
        ], "The input 'dialog_history' should be a str or list."
        assert isinstance(
            system_prompt,
            str,
        ), "The input 'system_prompt' should be a str."

        # query the llm using prompt template
        # call llm and generate response
        prompt = self.model.format(
            Msg(
                "user",
                OPT_PROMPT_TEMPLATE.format(
                    system_prompt=system_prompt,
                    dialog_history=dialog_history,
                ),
                role="user",
            ),
        )
        response = self.model(prompt).text

        # Print/speak the message in this agent's voice
        self.speak(
            Msg(self.name, "Optimizing System Prompt", role="assistant"),
        )
        msg = Msg(self.name, response, role="assistant")
        self.speak(msg)
        # get all the notes and return
        return Msg(
            self.name,
            self.get_all_tagged_notes(response),
            role="assistant",
        )

    def get_all_tagged_notes(self, response_text: str) -> list:
        """Get all the notes in the response text."""
        notes = []
        start_tag = "[prompt_note]"
        end_tag = "[/prompt_note]"
        start_index = response_text.find(start_tag)
        while start_index != -1:
            end_index = response_text.find(
                end_tag,
                start_index + len(start_tag),
            )
            if end_index != -1:
                note = response_text[start_index + len(start_tag) : end_index]
                notes.append(note)
                start_index = response_text.find(
                    start_tag,
                    end_index + len(end_tag),
                )
            else:
                break
        return notes
