# -*- coding: utf-8 -*-
"""Prompt generator class."""
from typing import List, Literal, Optional

from ._prompt_generator_base import SystemPromptGeneratorBase
from ._prompt_utils import _DEFAULT_EXAMPLE_LIST_EN


_DEFAULT_META_PROMPT_EN = """
You are an expert in writing and optimizing system prompts. Your task is to enhance the system prompt provided by the user, ensuring the enhanced prompt includes a description of the agent's role or personality, the agent's skill points, and some constraints.

## Note
1. The optimized system prompt must align with the user's original prompt intent. You may add callable tools, specific keywords, time frames, context, or any additional information to narrow the scope and guide the agent better in completing the task. Reconstruct the user's prompt as necessary.
2. The role and skill point descriptions should not narrow the scope defined by the user's original prompt.
3. Skill point descriptions should be as detailed and accurate as possible. If the user's original prompt includes examples, ensure skill points cover these cases but are not limited to them. For instance, if the original prompt mentions an "exam question generating robot" that can create fill-in-the-blank questions as an example, the skill points in the optimized prompt should include creating exam questions but not be limited to fill-in-the-blank questions.
4. Skill scope should not exceed the large model's capabilities. If it does, specify the tools or knowledge bases needed to endow the model with this skill. For example, since the large model lacks search function, invoke a search tool if searching is required.
5. Output the optimized prompt in markdown format.
6. The prompt must be concise, within 1000 words.
7. Retain the knowledge base or memory section in the optimized prompt if the user's provided prompt includes these.
8. If the prompt contains variables like ${{variable}}, ensure the variable appears only once in the optimized prompt. In subsequent references, use the variable name directly without enclosing it in ${}.
9. The language of the optimized prompt should match the user's original prompt: If the user provides the prompt in Chinese, optimize in Chinese; if in English, optimize in English.
"""  # noqa

_DEFAULT_EXAMPLE_PROMPT_TEMPLATE_EN = """## Example {index}
- User's Input:
```
{user_prompt}
```

- Optimized system prompt:
```
{opt_prompt}
```
"""

_DEFAULT_RESPONSE_PROMPT_TEMPLATE_EN = """## User's Input
```
{user_prompt}
```

## Optimized System Prompt
"""

# The name of the default local embedding model, which is used when
# `embed_model_config_name` is not provided.
_DEFAULT_LOCAL_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"


class EnglishSystemPromptGenerator(SystemPromptGeneratorBase):
    """Optimize the users' system prompt with the given meta prompt and
    examples if provided."""

    def __init__(
        self,
        model_config_name: str,
        meta_prompt: str = _DEFAULT_META_PROMPT_EN,
        response_prompt_template: str = _DEFAULT_RESPONSE_PROMPT_TEMPLATE_EN,
        example_num: int = 0,
        example_list: List = _DEFAULT_EXAMPLE_LIST_EN,
        example_selection_strategy: Literal["random", "similarity"] = "random",
        example_prompt_template: str = _DEFAULT_EXAMPLE_PROMPT_TEMPLATE_EN,
        embed_model_config_name: Optional[str] = None,
        local_embedding_model: str = _DEFAULT_LOCAL_EMBEDDING_MODEL,
    ):
        super().__init__(
            model_config_name=model_config_name,
            meta_prompt=meta_prompt,
            response_prompt_template=response_prompt_template,
            example_num=example_num,
            example_list=example_list,
            example_selection_strategy=example_selection_strategy,
            example_prompt_template=example_prompt_template,
            embed_model_config_name=embed_model_config_name,
            local_embedding_model=local_embedding_model,
        )
