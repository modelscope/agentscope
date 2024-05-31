# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""A module that optimize agent system prompt given dialog history."""
from agentscope.message import Msg
from agentscope.agents.agent import AgentBase


OPT_PROMPT_TEMPLATE = """
你是一个优秀的Prompt Engineer，现在你要通过添加note的方式对一个Agent的system prompt进行优化。

用户提供的原始system prompt是：
```
{system_prompt}
```

用户与之交互的dialog history是：
```
{dialog_history}
```

现在，你要
1. 判断用户与agent交互的dialog history中，是否包含显式的错误（如函数调用错误、没有遵循输入输出格式），对用户意图的误解等。
2. 对发生错误的原因进行详细分析，并且寻找对于对应错误的解决方案。
3. 根据错误原因和用户意图，写一条或几条可以添加在用户system prompt后面的注意事项note，或者exmaple形式的note，使之不要再犯同样的错误。
如果要添加的note包含example，需要格外小心，如果不确定添加的example是否正确，可以先不添加。
你添加的note语言与用户提供的原始system prompt一致，即用户提供的原始system prompt是使用中文写的，你添加的note也必须是中文; 如果用户提供的原始system prompt是使用english写的，你添加的note也必须是english。
你添加的note应该包含在tag [prompt_note]中，例如 [prompt_note] 请注意输出仅包含json格式 [/prompt_note]。如果dialog history没有明显问题，则不需要添加任何note。
"""  # noqa


class PromptAgentOpt:
    """A module that optimize agent system prompt given dialog history."""

    def __init__(
        self,
        agent: AgentBase,
    ) -> None:
        self.agent = agent
        self.model = agent.model

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

    def optimize(self) -> None:
        """Optimize the system prompt of the agent, given its dialog history"""
        system_prompt = self.agent.sys_prompt
        dialog_history = self.model.format(self.agent.memory.get_memory())

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

        added_notes = self.get_all_tagged_notes(response)

        for note in added_notes:
            self.agent.sys_prompt += note
