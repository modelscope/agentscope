# -*- coding: utf-8 -*-
"""
Service for text processing
"""

from agentscope.models import ModelWrapperBase, OpenAIWrapper
from agentscope.service.service_status import ServiceExecStatus
from agentscope.service.service_response import ServiceResponse
from agentscope.message import Msg
from agentscope.constants import _DEFAULT_SUMMARIZATION_PROMPT
from agentscope.constants import _DEFAULT_SYSTEM_PROMPT
from agentscope.constants import _DEFAULT_TOKEN_LIMIT_PROMPT


def summarization(
    model: ModelWrapperBase,
    text: str,
    system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    summarization_prompt: str = _DEFAULT_SUMMARIZATION_PROMPT,
    max_return_token: int = -1,
    token_limit_prompt: str = _DEFAULT_TOKEN_LIMIT_PROMPT,
) -> ServiceResponse:
    """Summarize the input text.

    Summarization function (Notice: curent version of token limitation is
    built with Open AI API)

    Args:
        model (`ModelWrapperBase`):
            Model used to summarize provided text.
        text (`str`):
            Text to be summarized by the model.
        system_prompt (`str`, defaults to `_DEFAULT_SYSTEM_PROMPT`):
            Prompts as instruction for the system, typically used in Open AI
            API. See the following example for more details.
        summarization_prompt (`str`, defaults to \
            `_DEFAULT_SUMMARIZATION_PROMPT`):
            Prompts for the beginning of the user provided text to be
            summarized. See the following example for more details.
        max_return_token (`int`, defaults to `-1`):
            Whether provide additional prompting instruction to limit the
            number of tokens in summarization returned by the model.
        token_limit_prompt (`str`, defaults to `_DEFAULT_TOKEN_LIMIT_PROMPT`):
            Prompt to instruct the model follow token limitation.

    Returns:
        `ServiceResponse`: If the model successfully summarized the text, and
        the summarization satisfies the provided token limitation, return
        `ServiceResponse` with `ServiceExecStatus.SUCCESS`; otherwise return
        `ServiceResponse` with `ServiceExecStatus.ERROR` (if the summary is
        return successfully but exceed the token limits, the content
        contains the summary as well).

    Example:

    With Open AI models, the default message with a $STR_TEXT and Open AI API::

        [
            {
                "role": "system",
                "content": "You are a helpful agent to summarizethe text.\\
                You need to keep all the key information of the text in the\\
                summary."
            },
            {
                "role": "user",
                "content": "TEXT: {$STR_TEXT} \\n"
            },
        ]
    """
    prompt = summarization_prompt.format(text)
    if max_return_token > 0:
        system_prompt += token_limit_prompt.format(max_return_token)
    if isinstance(model, OpenAIWrapper):
        try:
            msgs = [
                Msg(name="system", content=system_prompt),
                Msg(name="user", content=prompt),
            ]
            model_output = model(messages=msgs)
            summary = model_output.choices[0].message.content
            if max_return_token > -1:
                return_tokens = model_output.usage.completion_tokens
                if return_tokens > max_return_token:
                    # When the number of tokens in summary is larger than
                    # required, return ERROR but also has the too-long summary
                    return ServiceResponse(
                        ServiceExecStatus.ERROR,
                        content={
                            "error_msg": f"Summarization by model has "
                            f"{return_tokens } tokens, more than "
                            f"required {max_return_token}",
                            "summary": summary,
                        },
                    )
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                content=summary,
            )
        except ValueError:
            return ServiceResponse(
                ServiceExecStatus.ERROR,
                content="Summarization by model fails",
            )
    else:
        try:
            prompt = system_prompt + prompt
            model_output = model(messages=prompt)
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                content=model_output,
            )
        except ValueError:
            return ServiceResponse(
                ServiceExecStatus.ERROR,
                content=f"Fail to get summary from model the with the "
                f"'response' key from the output of {model.model_name}",
            )
