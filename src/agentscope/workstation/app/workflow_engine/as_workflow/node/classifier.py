# -*- coding: utf-8 -*-
"""Module for classifier node related functions."""
import time
from typing import Dict, Any, Generator

from agentscope.message import Msg
from agentscope.parsers import RegexTaggedContentParser

from .node import Node
from .utils import NodeType
from ..utils.misc import get_model_instance
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class ClassifierNode(Node):
    """Class for classifier node related functions."""

    node_type: str = NodeType.CLASSIFIER.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        node_param = self.sys_args["node_param"]

        condition_dict = {}
        index = 0
        for condition in node_param["conditions"]:
            if condition.get("id") != "default":
                condition_dict[index] = condition
                index += 1
            else:
                condition_dict[-1] = condition

        source_to_target_map = {}
        for source, adjacency in kwargs["graph"].adj.items():
            for target, edges in adjacency.items():
                for k, data in edges.items():
                    if data.get("source_handle"):
                        source_handle = data.get("source_handle")
                        target_handle = data.get("target_handle")
                        if source_handle not in source_to_target_map:
                            source_to_target_map[source_handle] = []
                            source_to_target_map[source_handle].append(
                                target_handle,
                            )

        for key, value in condition_dict.items():
            source_handle = self.node_id + "_" + value["id"]
            if source_handle in source_to_target_map:
                value["target_id"] = source_to_target_map[source_handle]

        candidates_list = []
        for idx, condition in condition_dict.items():
            candidates_list.append(f"""{idx}. {condition["subject"]}""")

        candidates = "\n".join(candidates_list)

        sys_prompt_template = self._build_prompt(
            mode=node_param["mode_switch"],
            multi_decision=node_param.get("multi_decision", False),
        )
        sys_prompt = sys_prompt_template.format_map(
            {
                "candidates": candidates,
                "input_question": self.sys_args["input_params"][0]["value"],
                "instruction": node_param.get("instruction"),
                # "history": kwargs["inputs"].get("sys.historyList"),
            },
        )

        model = get_model_instance(node_param["model_config"])

        short_memory = node_param["short_memory"]
        short_memory_enabled = short_memory.get("enabled", False)
        # TODO: implement the following in a better way
        if short_memory_enabled:
            short_memory_type = short_memory.get("type", "custom")
            if short_memory_type == "custom":
                history_list = short_memory["param"]["value"]
                messages = (
                    [
                        {"role": "system", "content": sys_prompt},
                    ]
                    + history_list
                    + [
                        {
                            "role": "user",
                            "content": self.sys_args["input_params"][0][
                                "value"
                            ],
                        },
                    ]
                )
            elif short_memory_type == "self":
                short_memory_round = short_memory.get("round", 10)
                short_memory_messages = kwargs.get("global_cache", {}).get(
                    "memory",
                    [],
                )
                used_short_messages = short_memory_messages[
                    -short_memory_round:
                ]
                messages = [
                    {"role": "system", "content": sys_prompt},
                ]
                for short_message in used_short_messages:
                    if (
                        self.node_id
                        not in short_message["status"]["inter_results"]
                    ):
                        continue
                    messages.extend(
                        [
                            {
                                "role": "user",
                                "content": short_message["status"][
                                    "inter_results"
                                ][self.node_id]["results"][0]["input"],
                            },
                            {
                                "role": "assistant",
                                "content": "\n".join(
                                    [
                                        short_message["status"][
                                            "inter_results"
                                        ][self.node_id]["results"][0][
                                            "content"
                                        ][
                                            "thought"
                                        ],
                                        " ".join(
                                            short_message["status"][
                                                "inter_results"
                                            ][self.node_id]["results"][0][
                                                "content"
                                            ][
                                                "subject"
                                            ][
                                                0
                                            ],
                                        ),
                                    ],
                                ),
                            },
                        ],
                    )
                messages.append(
                    {
                        "role": "user",
                        "content": self.sys_args["input_params"][0]["value"],
                    },
                )
        else:
            messages = model.format(
                Msg(
                    name="system",
                    content=sys_prompt,
                    role="system",
                ),
            )
        response = model(messages)
        usages = [
            {
                "prompt_tokens": response.raw.usage.input_tokens,
                "completion_tokens": response.raw.usage.output_tokens,
                "total_tokens": response.raw.usage.total_tokens,
            },
        ]

        parser = RegexTaggedContentParser(
            tagged_content_pattern=r"✿(?P<name>[^✿]+)✿: (?P<content>[^\n]+)",
        )

        results = parser.parse(response).parsed

        subject, targets = [], []
        if not isinstance(results["Decision"], list):
            results["Decision"] = [results["Decision"]]
        for index in results["Decision"]:
            subject.append(condition_dict[index]["subject"])
            try:
                targets += condition_dict[index].get("target_id")
            except Exception:
                pass
        thought = results.get("Think", "")

        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"

        yield [
            WorkflowVariable(
                name="thought",
                content=thought,
                source=self.node_id,
                targets=targets,
                data_type=DataType.STRING,
                input={"input": {"messages": messages}},
                output={
                    "thought": thought,
                    "subject": subject[0],
                },
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                node_exec_time=node_exec_time,
                usages=usages,
            ),
            WorkflowVariable(
                name="subject",
                content=subject[0],
                source=self.node_id,
                targets=targets,
                data_type=DataType.STRING,
                input={"input": {"messages": messages}},
                output={
                    "thought": thought,
                    "subject": subject[0],
                },
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                node_exec_time=node_exec_time,
                usages=usages,
            ),
        ]

    def _mock_execute(self, **kwargs: Any) -> Generator:
        yield from self._execute(**kwargs)

    def compile(self) -> Dict[str, Any]:
        model_str = self.build_graph_var_str("model")

        node_param = self.sys_args["node_param"]
        config_str = self.node_kwargs["id"]
        model_config = node_param["modelConfig"]
        result = self.build_graph_var_str("result")

        model_response = self.build_graph_var_str("response")

        condition_dict = {}
        index = 0
        for condition in node_param["conditions"]:
            if condition.get("conditionId") != "default":
                condition_dict[index] = condition
                index += 1

        # Now construct the candidates string
        candidates_list = []
        for idx, condition in condition_dict.items():
            candidates_list.append(f"""{idx}. {condition["subject"]}""")

        candidates = "\n".join(candidates_list)

        sys_prompt_template = self._build_prompt(
            mode=node_param["modeSwitch"],
            multi_decision=node_param.get("multiDecision", False),
        )
        sys_prompt = sys_prompt_template.format_map(
            {
                "candidates": candidates,
                "input_question": self.sys_args["input_params"][0]["value"],
                "instruction": node_param.get("instruction") or "暂无",
                "history": "${sys.historyList}",
            },
        )

        import_list = [
            "import os",
            "from agentscope.manager import ModelManager",
            "from agentscope.parsers import RegexTaggedContentParser",
        ]

        init_str = f"""
ModelManager.get_instance().load_model_configs(
    [
        {{
            "api_key": os.getenv("DASHSCOPE_API_KEY"),
            "config_name": "{config_str}",
            "model_type": "dashscope_chat",
            "model_name": "{model_config["modelId"]}",
            "generate_args": {{
                "temperature": {model_config["params"]["temperature"]},
                "max_tokens": {model_config["params"]["maxTokens"]},
                "enable_search": {model_config["params"]["enable_search"]},
            }},
        }}
    ]
)
{model_str} = ModelManager.get_instance().get_model_by_config_name(
    "{config_str}",
)
{self.build_graph_var_str("parser")} = RegexTaggedContentParser(
    tagged_content_pattern=r"✿(?P<name>[^✿]+)✿: (?P<content>[^\\n]+)"
)
"""

        execs_str = f"""
{self.build_graph_var_str("sys_prompt")} = \
\"\"\"{self._add_prefix_to_lines(sys_prompt)}\"\"\"
messages = [
    dict(role="system", content={self.build_graph_var_str("sys_prompt")}),
]
{model_response} = {model_str}(messages)

{result} = \
{self.build_graph_var_str("parser")}.parse({model_response}).parsed
{self.build_graph_var_str("mapping_dict")} = \
{{'Decision': 'subject', 'Think': 'thought'}}
{result} = {{{self.build_graph_var_str('mapping_dict')}.get(k, k): \
v for k, v in {result}.items()}}
if "thought" not in {result}:
    {result}["thought"] = ""
{self.build_node_output_str(result, str)}
"""

        branches = self.sys_args["node_param"]["conditions"]

        sbj = f'{result}["subject"]'

        condition_ids = []
        condition_lines = []
        index_count = 0

        for index, branch in condition_dict.items():
            if branch.get("conditionId") == "default":
                index_count += 1
                continue

            condition_ids.append(f"condition_{branch.get('conditionId', '')}")

            if index == index_count:
                condition_expr = (
                    f"(isinstance({sbj}, int) and "
                    f"{sbj} == {index}) or (isinstance({sbj}, "
                    f"list) and ({index} in {sbj}))"
                )
                condition_lines.append(
                    f"{self.build_graph_var_str(condition_ids[-1])} = "
                    f"({condition_expr})",
                )
            else:
                condition_expr = (
                    f"(isinstance({sbj}, int) and {sbj} =="
                    f" {index}) or (isinstance({sbj}, "
                    f"list) and ({index} in {sbj}))"
                )
                previous_conditions = [f"not {x}" for x in condition_ids[:-1]]
                condition_expr = (
                    " and ".join(previous_conditions)
                    + f" and ({condition_expr})"
                )
                condition_lines.append(
                    f"{self.build_graph_var_str(condition_ids[-1])} = "
                    f"({condition_expr})",
                )

        # Default branch
        default_branch = next(
            (b for b in branches if b["conditionId"] == "default"),
            None,
        )
        if default_branch:
            previous_conditions = [f"not ({x})" for x in condition_ids]
            condition_expr = " and ".join(previous_conditions)
            condition_lines.append(
                f"{self.build_graph_var_str('condition_default')} = "
                f"({condition_expr})",
            )

        return {
            "imports": import_list,
            "inits": [init_str],
            "execs": [execs_str] + condition_lines,
            "increase_indent": False,
        }

    def _build_prompt(
        self,
        mode: str,
        multi_decision: bool,
        language: str = "en",
    ) -> str:
        # Define the base components of the prompts in Chinese and English
        base_prompt_cn = (
            "你是一个智能决策专家。你的任务是：给定一个输入问题/文本信息，以及一系列候选类别，"
            "判断该问题/文本属于候选类别中的哪一个。\n\n"
            "## 候选类别\n"
            "{candidates}\n\n"
            "### -1. 其他类别\n"
            "不属于以上类别中的任何一个。\n\n"
            "## 输出格式\n"
            "请严格按照以下'---'内的格式进行输出：\n"
            "---\n"
        )

        base_prompt_en = (
            "You are an intelligent decision expert. Your task is: given an "
            "input question/text information, determine which one of the "
            "candidate categories the input belongs to.\n\n"
            "## Candidate Categories\n"
            "{candidates}\n\n"
            "### -1. Other Categories\n"
            "Does not belong to any of the above categories.\n\n"
            "## Output Format\n"
            "Please strictly follow the format within '---' for output:\n"
            "---\n"
        )

        think_prompt_cn = "✿思考✿：对输入待分类信息的类别进行分析，请你一步一步进行思考。\n"
        think_prompt_en = (
            "✿Think✿: Analyze the category of the input "
            "information that needs classification, "
            "and please think step by step.\n"
        )

        single_decision_prompt_cn = (
            "✿决策✿：决策结果，即“候选类别”中的序号，必须是其中的一个。请输出序号，" "例如：0，绝不要回答问题，做出选择后即可终止。\n"
        )
        single_decision_prompt_en = (
            "✿Decision✿: The decision result, i.e., the number in the "
            "'Candidate Categories', must be one of them."
            " Please output the number, e.g., 0. Do not answer questions; "
            "terminate after making a choice.\n"
        )

        multi_decision_prompt_cn = (
            "✿决策✿：决策结果，即“候选类别”中的序号，必须是其中的一个或者几个。"
            "请用列表形式输出，使用','隔开，例如[1,3]，"
            "绝不要回答问题，做出选择后即可终止。\n"
        )
        multi_decision_prompt_en = (
            "✿Decision✿: The decision result, i.e., the numbers in the "
            "'Candidate Categories', must be one or several."
            " Please output in list form, separated by ',', e.g., [1,3]. Do "
            "not answer questions; terminate after making a choice.\n"
        )

        query_prompt_cn = (
            "---\n"
            "## 输入待分类问题\n"
            "{input_question}\n"
            "## 注意事项\n"
            "{instruction}\n"
            # "## 参考的历史信息\n"
            # "以下是本次问答的历史上下文信息，你可以参考其内容进行回答。\n"
            # "{history}\n"
        )
        query_prompt_en = (
            "---\n"
            "## Input Question for Classification\n"
            "{input_question}\n"
            "## Notes\n"
            "{instruction}\n"
            # "## Reference Historical Information\n"
            # "Below is the historical context information for this Q&A, "
            # "which you can refer to for answering.\n"
            # "{history}\n"
        )

        # Mapping modes to corresponding prompt formats in both languages
        if language == "cn":
            base_prompt = base_prompt_cn
            think_prompt = think_prompt_cn
            single_decision_prompt = single_decision_prompt_cn
            multi_decision_prompt = multi_decision_prompt_cn
            query_prompt = query_prompt_cn
        else:
            base_prompt = base_prompt_en
            think_prompt = think_prompt_en
            single_decision_prompt = single_decision_prompt_en
            multi_decision_prompt = multi_decision_prompt_en
            query_prompt = query_prompt_en

        prompt_mapping = {
            "advanced": {
                "multi": base_prompt
                + think_prompt
                + multi_decision_prompt
                + query_prompt,
                "single": base_prompt
                + think_prompt
                + single_decision_prompt
                + query_prompt,
            },
            "efficient": {
                "multi": base_prompt + multi_decision_prompt + query_prompt,
                "single": base_prompt + single_decision_prompt + query_prompt,
            },
        }

        # Validate mode and construct the prompt
        if mode not in prompt_mapping:
            raise ValueError(f"unknown mode {mode}")

        # Choose between single and multi decision prompts based on decision
        # parameter
        decision_type = "multi" if multi_decision else "single"

        return prompt_mapping[mode][decision_type]


class DecisionNode(ClassifierNode):
    """Class for decision node related functions."""

    node_type: str = NodeType.DECISION.value
