# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""A agent that performs direct prompt optimization."""
from typing import Union

from agentscope.message import Msg
from agentscope.agents.agent import AgentBase


OPT_QUERY_PROMPT = """
你是一个专业的prompt工程师，你擅长优化prompt优化。你的任务是优化用户提供的prompt, 使得优化后的prompt指示更清晰，结构更明确。

请注意：
1. 优化后的prompt必须与用户提供的prompt意图一致，可适当加入上下文或任何可以缩小范围并指导大模型能够更好地理解完成任务的附加信息，对用户的prompt进行重构。请注意不要作过多的拓展。
2. 优化后的prompt要保留用户提供的prompt里的关键信息, 例如原prompt中的与任务相关的背景知识，文本分析任务中的原文本，关于输出格式的要求等类型的关键信息。
3. 当prompt比较长的时候，可以适当在其中加入分隔符，使得优化后的prompt结构更加清晰。
4. 如果用户的prompt里还有变量，如"${variable_name}"，优化后的prompt里必须保留这些变量。你可以加入更多的用户可配置的变量, 并用"${new_variable_name}"来表示, 使得优化后的prompt支持用户提供更多的信息。
5. 优化后的prompt语言与用户提供的prompt一致，即用户提供的prompt使用中文写的，优化后的prompt也必须是中文, 如果用户提供的prompt使用英文写的，优化后的prompt也必须是英文。
6. 如果你认为优化前的prompt已经足够简介清晰，且能够很好的表达用户对应的意图，那么就不需要优化prompt，直接返回用户输入提供的prompt即可。
7. 你不能直接生成对原始prompt的回答！
8. 相比直接使用原始prompt，使用你优化后的prompt时大模型应该能生成更好的、更符合用户意图的回答。
9. 你的输出应该只包含优化后的prompt，而不带其他附带内容。

"""  # noqa

OPT_PROMPT_TEMPLATE = """
用户提供的prompt是：
{user_prompt}

现在，请输出你优化后的prompt:
"""


class DirectPromptOptimizationAgent(AgentBase):
    """A simple agent that directly optimizes the prompt."""

    def __init__(
        self,
        name: str,
        model_config_name: str,
        meta_prompt: Union[str, None] = None,
    ) -> None:
        """Initialize the direct prompt optimization agent.

        Arguments:
            name (`str`):
                The name of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.
            meta_prompt (`Optional[str]`):
                The meta prompt that instruct the agent to perform prompt
                optimization. If is None, then the agent will use the default
                prompt above.

        Note:
            The output optimized prompt may not always works better than the
            original prompt. It depends on the specific task and the model.

        Usage:
            ```
            from direct_agent import DirectPromptOptimizationAgent
            from agentscope.message import Msg

            agent = DirectPromptOptimizationAgent(
                name="assistant",
                model_config_name='xxx',
            )

            user_prompt = "Tell me about the history of the world."

            optimized_prompt = agent(Msg(name="user",
                content=user_prompt, role="user").content
            ```
        """
        super().__init__(
            name=name,
            model_config_name=model_config_name,
        )

        if meta_prompt is None:
            self.meta_prompt = OPT_QUERY_PROMPT
        else:
            self.meta_prompt = meta_prompt

    def reply(self, x: dict = None) -> dict:
        """
        Replying to the input.

        Arguments:
            x(`Msg`): the input prompt to optimize. The input prompt
                should be a `Msg` object.

        Returns:
            msg(`Msg`): the output message. In the output message,
                the `content` field is the optimized prompt.

        Note:
            The output optimized prompt may not always works better than the
            original prompt. It depends on the specific task and the model.
        """
        # get the user prompt
        user_prompt = x.content

        # query the llm using meta prompt and template
        # call llm and generate response
        prompt = self.model.format(
            Msg(
                "user",
                self.meta_prompt
                + OPT_PROMPT_TEMPLATE.format(user_prompt=user_prompt),
                role="user",
            ),
        )
        response = self.model(prompt).text

        # Print/speak the message in this agent's voice
        self.speak(Msg(self.name, "Optimizing Prompt", role="assistant"))
        msg = Msg(self.name, response, role="assistant")
        self.speak(msg)

        return msg
