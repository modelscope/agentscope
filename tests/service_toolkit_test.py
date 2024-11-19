# -*- coding: utf-8 -*-
""" Unit test for service toolkit. """
import json
import unittest
from typing import Literal

import agentscope
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.parsers import MultiTaggedContentParser, TaggedContent
from agentscope.service import (
    bing_search,
    execute_python_code,
    retrieve_from_list,
    query_mysql,
    summarization,
)
from agentscope.service import ServiceToolkit


class ServiceToolkitTest(unittest.TestCase):
    """
    Unit test for service toolkit.
    """

    def setUp(self) -> None:
        """Init for ExampleTest."""
        agentscope.init(disable_saving=True)

        self.maxDiff = None

        self.json_schema_bing_search1 = {
            "type": "function",
            "function": {
                "name": "bing_search",
                "description": (
                    "Search question in Bing Search API and "
                    "return the searching results"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "num_results": {
                            "type": "number",
                            "description": (
                                "The number of search " "results to return."
                            ),
                            "default": 10,
                        },
                        "question": {
                            "type": "string",
                            "description": "The search query string.",
                        },
                    },
                    "required": [
                        "question",
                    ],
                },
            },
        }

        self.json_schema_bing_search2 = {
            "type": "function",
            "function": {
                "name": "bing_search",
                "description": (
                    "Search question in Bing Search API and "
                    "return the searching results"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The search query string.",
                        },
                    },
                    "required": ["question"],
                },
            },
        }

        self.json_schema_func = {
            "type": "function",
            "function": {
                "name": "func",
                "description": "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "c": {"default": "test"},
                        "d": {
                            "type": "typing.Literal",
                            "enum": [1, "abc", "d"],
                            "default": 1,
                        },
                        "b": {},
                        "a": {"type": "string"},
                    },
                    "required": ["a", "b"],
                },
            },
        }

        self.json_schema_execute_python_code = {
            "type": "function",
            "function": {
                "name": "execute_python_code",
                "description": """Execute a piece of python code.

This function can run Python code provided in string format. It has the
option to execute the code within a Docker container to provide an
additional layer of security, especially important when running
untrusted code.

WARNING: If `use_docker` is set to `False`, the `code` will be run
directly in the host system's environment. This poses a potential
security risk if the code is untrusted. Only disable Docker if you are
confident in the safety of the code being executed.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": (
                                "The Python code to be " "executed."
                            ),
                        },
                    },
                    "required": ["code"],
                },
            },
        }

        self.json_schema_retrieve_from_list = {
            "type": "function",
            "function": {
                "name": "retrieve_from_list",
                "description": """Retrieve data in a list.

Memory retrieval with user-defined score function. The score function is
expected to take the `query` and one of the element in 'knowledge' (a
list). This function retrieves top-k elements in 'knowledge' with
HIGHEST scores. If the 'query' is a dict but has no embedding,
we use the embedding model to embed the query.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "Any",
                            "description": "A message to be retrieved.",
                        },
                    },
                    "required": [
                        "query",
                    ],
                },
            },
        }

        self.json_schema_query_mysql = {
            "type": "function",
            "function": {
                "name": "query_mysql",
                "description": "Execute query within MySQL database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute.",
                        },
                    },
                    "required": [
                        "query",
                    ],
                },
            },
        }

        self.json_schema_summarization = {
            "type": "function",
            "function": {
                "name": "summarization",
                "description": (
                    "Summarize the input text.\n"
                    "\n"
                    "Summarization function (Notice: current version "
                    "of token limitation is\n"
                    "built with Open AI API)"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to be summarized by the "
                            "model.",
                        },
                    },
                    "required": [
                        "text",
                    ],
                },
            },
        }

    def test_bing_search(self) -> None:
        """Test bing_search."""
        # api_key is specified by developer, while question and num_results
        # are specified by model
        _, doc_dict = ServiceToolkit.get(bing_search, api_key="xxx")
        print(json.dumps(doc_dict, indent=4))
        self.assertDictEqual(
            doc_dict,
            self.json_schema_bing_search1,
        )

        # Set num_results by developer rather than model
        _, doc_dict = ServiceToolkit.get(
            bing_search,
            num_results=3,
            api_key="xxx",
        )

        self.assertDictEqual(
            doc_dict,
            self.json_schema_bing_search2,
        )

    def test_enum(self) -> None:
        """Test enum in service toolkit."""

        def func(  # type: ignore
            a: str,
            b,
            c="test",
            d: Literal[1, "abc", "d"] = 1,
        ) -> None:
            print(a, b, c, d)

        _, doc_dict = ServiceToolkit.get(func)

        self.assertDictEqual(
            doc_dict,
            self.json_schema_func,
        )

    def test_exec_python_code(self) -> None:
        """Test execute_python_code in service toolkit."""
        _, doc_dict = ServiceToolkit.get(
            execute_python_code,
            timeout=300,
            use_docker=True,
            maximum_memory_bytes=None,
        )

        self.assertDictEqual(
            doc_dict,
            self.json_schema_execute_python_code,
        )

    def test_retrieval(self) -> None:
        """Test retrieval in service toolkit."""
        _, doc_dict = ServiceToolkit.get(
            retrieve_from_list,
            knowledge=[1, 2, 3],
            score_func=lambda x, y: 1.0,
            top_k=10,
            embedding_model=10,
            preserve_order=True,
        )

        self.assertDictEqual(
            doc_dict,
            self.json_schema_retrieve_from_list,
        )

    def test_sql_query(self) -> None:
        """Test sql_query in service toolkit."""
        _, doc_dict = ServiceToolkit.get(
            query_mysql,
            database="test",
            host="localhost",
            user="root",
            password="xxx",
            port=3306,
            allow_change_data=False,
            maxcount_results=None,
        )

        self.assertDictEqual(
            doc_dict,
            self.json_schema_query_mysql,
        )

    def test_summary(self) -> None:
        """Test summarization in service toolkit."""
        _, doc_dict = ServiceToolkit.get(
            summarization,
            model=ModelWrapperBase("abc", "model_name"),
            system_prompt="",
            summarization_prompt="",
            max_return_token=-1,
            token_limit_prompt="",
        )

        print(json.dumps(doc_dict, indent=4))

        self.assertDictEqual(
            doc_dict,
            self.json_schema_summarization,
        )

    def test_service_toolkit(self) -> None:
        """Test the object of ServiceToolkit."""
        service_toolkit = ServiceToolkit()

        service_toolkit.add(bing_search, api_key="xxx", num_results=3)
        service_toolkit.add(
            execute_python_code,
            timeout=300,
            use_docker=True,
            maximum_memory_bytes=None,
        )

        self.assertEqual(
            service_toolkit.tools_instruction,
            """## Tool Functions:
The following tool functions are available in the format of
```
{index}. {function name}: {function description}
{argument1 name} ({argument type}): {argument description}
{argument2 name} ({argument type}): {argument description}
...
```

1. bing_search: Search question in Bing Search API and return the searching results
	question (string): The search query string.
2. execute_python_code: Execute a piece of python code.

This function can run Python code provided in string format. It has the
option to execute the code within a Docker container to provide an
additional layer of security, especially important when running
untrusted code.

WARNING: If `use_docker` is set to `False`, the `code` will be run
directly in the host system's environment. This poses a potential
security risk if the code is untrusted. Only disable Docker if you are
confident in the safety of the code being executed.
	code (string): The Python code to be executed.
""",  # noqa
        )
        self.assertDictEqual(
            service_toolkit.json_schemas,
            {
                "bing_search": self.json_schema_bing_search2,
                "execute_python_code": self.json_schema_execute_python_code,
            },
        )

    def test_multi_tagged_content(self) -> None:
        """Test multi tagged content"""

        parser = MultiTaggedContentParser(
            TaggedContent(
                "thought",
                "[THOUGHT]",
                "what you think",
                "[/THOUGHT]",
            ),
            TaggedContent("speak", "[SPEAK]", "what you speak", "[/SPEAK]"),
            TaggedContent(
                "function",
                "[FUNCTION]",
                '{"function name": "xxx", "args": {"arg name": "xxx"}}',
                "[/FUNCTION]",
                parse_json=True,
            ),
        )

        target_format_instruction = (
            "Respond with specific tags as outlined below, and the content "
            "between [FUNCTION] and [/FUNCTION] MUST be a JSON object:\n"
            "[THOUGHT]what you think[/THOUGHT]\n"
            "[SPEAK]what you speak[/SPEAK]\n"
            '[FUNCTION]{"function name": "xxx", "args": {"arg name": "xxx"}}'
            "[/FUNCTION]"
        )

        self.assertEqual(parser.format_instruction, target_format_instruction)

        response = ModelResponse(
            text=(
                "This is a test\n[THOUGHT]I think this is a good idea"
                "[/THOUGHT]\n[SPEAK]I am speaking now[/SPEAK]\n[FUNCTION]"
                '{"function name": "bing_search", "args": {"query": "news of '
                'today"}}[/FUNCTION]'
            ),
        )
        res = parser.parse(response)

        self.assertDictEqual(
            res.parsed,
            {
                "thought": "I think this is a good idea",
                "speak": "I am speaking now",
                "function": {
                    "function name": "bing_search",
                    "args": {"query": "news of today"},
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
