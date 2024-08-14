import json
import traceback
from agentscope.web.workstation.workflow_dag import build_dag
from agentscope.studio._app import _remove_file_paths
from typing import Tuple


def convert_to_py(content: str, **kwargs) -> Tuple:
    """
    Convert json config to python code.
    """
    try:
        cfg = json.loads(content)
        print(cfg)
        return "True", build_dag(cfg).compile(**kwargs)
    except Exception as e:
        return "False", _remove_file_paths(
            f"Error: {e}\n\n" f"Traceback:\n" f"{traceback.format_exc()}",
        )


def test_convert_to_py():
    # 测试正确的输入
    content = ("{'2': {'data': {'args': {'api_key': 'qweqweqweqw', 'config_name': 'qwen', 'messages_key': 'input', "
               "'model_name': 'qwen-max', 'model_type': 'dashscope_chat', 'seed': 0, 'temperature': '0.1'}}, "
               "'inputs': {}, 'name': 'dashscope_chat', 'outputs': {}}, '3': {'data': {'args': {'name': 'User'}}, "
               "'inputs': {'input_1': {'connections': []}}, 'name': 'UserAgent', "
               "'outputs': {'output_1': {'connections': [{'node': '4', 'output': 'input_1'}]}}}, "
               "'4': {'data': {'args': {'model_config_name': 'qwen', 'name': 'Assistant', "
               "'sys_prompt': 'You are an assistant'}}, 'inputs': {'input_1': "
               "{'connections': [{'input': 'output_1', 'node': '3'}]}}, 'name': 'DialogAgent', "
               "'outputs': {'output_1': {'connections': []}}}}")

    result = convert_to_py(content, runtime_id=12312312, studio_url="test")
    print(result)
    assert result[0] == "True"
    assert "dashscope_chat" in result[1]
    assert "api_key" in result[1]

    # 测试错误的输入
    content = '{"invalid": "json"}'
    result = convert_to_py(content)
    assert result[0] == "False"
    assert "Error: " in result[1]
    assert "Traceback" in result[1]


def test_json_load():
    import json

    data = {
        "4": {
            "data": {
                "elements": [
                    "5",
                    "6"
                ]
            },
            "inputs": {
                "input_1": {
                    "connections": []
                }
            },
            "name": "SequentialPipeline",
            "outputs": {
                "output_1": {
                    "connections": []
                }
            }
        },
        "5": {
            "data": {
                "args": {
                    "variables": "{'a': 1, 'b': 2, 'c': 3}"
                }
            },
            "inputs": {
                "input_1": {
                    "connections": []
                }
            },
            "name": "StartNode",
            "outputs": {
                "output_1": {
                    "connections": []
                }
            }
        },
        "6": {
            "data": {
                "args": {
                    "variable_names": "a",
                }
            },
            "inputs": {
                "input_1": {
                    "connections": []
                }
            },
            "name": "EndNode",
            "outputs": {
                "output_1": {
                    "connections": []
                }
            }
        }
    }

    content = json.dumps(data)

    print(content)
    result = convert_to_py(content, runtime_id=12312312, studio_url="test")
    print(result)
    assert result[0] == "True"
    assert "a" in result[1]


def test_json_load_file():
    with open('test.json', 'r') as file:
        data = json.load(file)

    content = json.dumps(data)

    print(content)
    result = convert_to_py(content, runtime_id=12312312, studio_url="test")
    print(result)
    assert result[0] == "True"
    assert "a" in result[1]


# 运行测试
test_json_load_file()
