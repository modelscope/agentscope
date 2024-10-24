# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""
This script demonstrates task solving with a data interpreter pipeline
formed by multiple agents, each specialized in one aspect of problem solving.
"""
import csv
import os
from typing import Any, List, Dict, Optional
from dotenv import load_dotenv, find_dotenv
from di_agents import (
    PlannerAgent,
    VerifierAgent,
    SynthesizerAgent,
    ReplanningAgent,
)
import agentscope
from agentscope.agents import ReActAgent
from agentscope.message import Msg
from agentscope.service import (
    ServiceToolkit,
    execute_python_code,
    list_directory_content,
    get_current_directory,
    execute_shell_command,
)

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


def read_csv_file(file_path: str) -> ServiceResponse:
    """
    Read and parse a CSV file.

    Args:
        file_path (`str`):
            The path to the CSV file to be read.

    Returns:
        `ServiceResponse`: Where the boolean indicates success, the
        Any is the parsed CSV content (typically a list of rows),
        and the str contains an error message if any, including
        the error type.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            data: List[List[str]] = list(reader)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=data,
        )
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {e}"
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )


def write_csv_file(
    file_path: str,
    data: List[List[Any]],
    overwrite: bool = False,
) -> ServiceResponse:
    """
    Write data to a CSV file.

    Args:
        file_path (`str`):
            The path to the file where the CSV data will be written.
        data (`List[List[Any]]`):
            The data to write to the CSV file (each inner list represents a row).
        overwrite (`bool`):
            Whether to overwrite the file if it already exists.

    Returns:
        `ServiceResponse`: where the boolean indicates success, and the
        str contains an error message if any, including the error type.
    """
    if not overwrite and os.path.exists(file_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileExistsError: The file already exists.",
        )
    try:
        with open(file_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(data)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Success",
        )
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {e}"
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )


_ = load_dotenv(find_dotenv())  # read local .env file

openai_api_key = os.getenv("OPENAI_API_KEY")
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")


STRUCTUAL_PROMPT = """
    # overall_task: {overall_task}

    # solved_sub_tasks: {solved_sub_tasks}

    # current_sub_task: {current_sub_task}

    # Instruction
    - Conditioning on `overall_task` and `solved_sub_tasks`, solve `current_sub_task` with the appropriate tools provided. Note that you should only use `overall_task` and `solved_sub_tasks` as context as opposed to solving them. DO NOT attempt to solve `overall_task` or `solved_sub_tasks`.
    - When using tools, ALWAYS prioritize using the tool mentioned in `tool_info` over other tool or code for solving `current_sub_task`.
    - While some concise thoughts are helpful, code is required, unless other tools are used. If certain python libraries are not installed, use `execute_shell_command` to install them.
    - At each step, if some data is fetched/generated, it is a good practice to save it.

    # Output Instruction
    - Always output one and only one code block in your response. The code block must be self-contained, i.e., does not rely on previously generated code to be executed successfully, because the execution environments do not persist between calls of `execute_python_code`. Always use print statement on the final solution. E.g., if `res` is the final output, use `print(res)` at the end of your code. Output the code itself if the task at hand is to generate that code. After that, use `execute_python_code` to execute your code. Based on the result from code execution or tool using, determine if `current_sub_task` is solved.
    - After `current_sub_task` is solved, return explicitly the result(s) for `current_sub_task` that is/are needed in the subsequent subtasks. If certain code are needed for the subsequent tasks, OUTPUT THE COMPLETE CODE. If the code is long, save it in txt or json format, and output the path for next round's use. If the result(s) contain(s) a lof of data, save the result(s) locally, output the path before proceed.
    - DO NOT USE `finish` tool before executing the code if code execution is required. If the result involves a lot of data, save the data as csv, txt, json file(s) etc. for the ease of processing in the following subtasks.
    """


def problem_solving(task: str) -> str:
    """
    Solves a given complex task by decomposing it into subtasks, planning,
    solving, verifying, and synthesizing the final answer.

    Args:
        task (str): The overall task description to solve.

    Returns:
        str: The final synthesized answer to the overall task.

    This function orchestrates the problem-solving process by:
    - Using the planner agent to decompose the task into manageable subtasks.
    - Iteratively processing each subtask:
        - Solving the subtask using the solver agent.
        - Verifying the solution with the verifier agent.
        - If verification fails, invoking the replanning agent
          to adjust the plan.
    - Once all subtasks are successfully solved, synthesizing the results
      using the synthesizer agent to produce the final answer.
    """

    task_msg: Msg = Msg(name="Planner", role="system", content=task)
    subtasks: List[Dict[str, Any]] = planner_agent(task_msg)
    solved_dependent_sub_tasks: str = ""

    subtask_index: int = 0
    while subtask_index < len(subtasks):
        print("current subtask:", subtasks[subtask_index]["instruction"])
        if subtask_index > 0:
            solved_dependent_sub_tasks += str(subtasks[subtask_index - 1])
        prompt: str = STRUCTUAL_PROMPT.format(
            overall_task=task,
            solved_sub_tasks=solved_dependent_sub_tasks,
            current_sub_task=subtasks[subtask_index],
        )
        msg: Msg = Msg(name="Planner", role="system", content=prompt)

        verdict: str = "non"
        failure_count: int = 0
        max_failure: int = 1  # Adjust as needed
        result: Optional[Msg] = None
        while "True" not in verdict[-5:]:
            if verdict != "non":
                msg = Msg(
                    name="Planner",
                    role="system",
                    content=prompt + " VERDICT: " + verdict,
                )
                failure_count += 1
            if failure_count > max_failure:
                # Call the replanning agent
                result_content: str = (
                    result.content if "result" in locals() else ""
                )
                msg_replan: Msg = Msg(
                    name="replanner",
                    role="system",
                    content=(
                        "overall_task: "
                        + task
                        + "\nsolved_dependent_sub_tasks: "
                        + solved_dependent_sub_tasks
                        + "\ncurrent_sub_task: "
                        + subtasks[subtask_index]["instruction"]
                        + "\nresult: "
                        + result_content
                        + "\nVERDICT: "
                        + verdict
                        + "\nall_subtasks: "
                        + str(subtasks)
                    ),
                )
                decision: str
                output: Any
                decision, output = replanning_agent(msg_replan)
                if decision == "decompose_subtask":
                    # Recursively solve the decomposed sub-subtasks
                    print(
                        "Decomposing current subtask into sub-subtasks...",
                    )
                    subtask_instruction: str = subtasks[subtask_index][
                        "instruction"
                    ]
                    # Call problem_solving recursively
                    subtask_result: str = problem_solving(
                        subtask_instruction,
                    )
                    # Store the result
                    subtasks[subtask_index]["result"] = subtask_result
                    # Increment subtask_index to move to the next subtask
                    subtask_index += 1
                    # Break out of the failure loop
                    break
                if decision == "replan_subtask":
                    # Update subtasks with the new plan
                    print("Replanning current and subsequent subtasks...")
                    # Replace current and subsequent subtasks
                    subtasks = subtasks[:subtask_index] + output
                    # subtask_index remains the same to retry solving the current subtask
                    # Break out to restart processing with the new plan
                    break
                raise ValueError(
                    "Unknown decision from replanning_agent.",
                )
            # Proceed with solving the subtask
            result = solver_agent(msg)
            msg_verifier: Msg = Msg(
                name="Verifier",
                role="system",
                content=(
                    "overall_task: "
                    + task
                    + "\nsolved_dependent_sub_tasks: "
                    + solved_dependent_sub_tasks
                    + "\ncurrent_sub_task: "
                    + subtasks[subtask_index]["instruction"]
                    + "\nresult: "
                    + result.content
                ),
            )
            verdict = verifier_agent(msg_verifier).content

        # Store the result if verification passed
        if "True" in verdict[-5:]:
            subtasks[subtask_index]["result"] = result.content
            subtask_index += 1  # Move to the next subtask
        else:
            # Handle the case where verification never passed
            print("Unable to solve subtask after replanning.")
            break  # Exit if unable to solve even after replanning

    # Once all subtasks are solved, synthesize the final answer
    msg_synthesizer: Msg = Msg(
        name="synthesizer",
        role="system",
        content="overall_task: " + task + "\nsubtasks: " + str(subtasks),
    )
    final_answer: str = synthesizer_agent(msg_synthesizer).content
    return final_answer


agentscope.init(
    model_configs=[
        {
            "config_name": "gpt_config",
            "model_type": "openai_chat",
            # "model_name": "chatgpt-4o-latest",
            # "model_name": "gpt-4o-mini",
            "model_name": "o1-mini",
            "api_key": openai_api_key,
            # "generate_args": {
            #     "temperature": 0.0,
            # },
        },
        {
            "config_name": "dashscope",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max-1201",
            "api_key": dashscope_api_key,
            "generate_args": {
                "temperature": 0.0,
            },
        },
        {
            "config_name": "lite_llm_claude",
            "model_type": "litellm_chat",
            "model_name": "claude-3-5-sonnet-20240620",
            "generate_args": {
                # "max_tokens": 4096,
                "temperature": 0.0,
            },
        },
        {
            "model_type": "post_api_chat",
            "config_name": "my_post_api",
            "api_url": "https://xxx",
            "headers": {},
        },
    ],
    project="Multi-Agent Conversation",
    save_api_invoke=True,
)

# Create a ServiceToolkit instance
service_toolkit = ServiceToolkit()
# Add your tools to the service_toolkit here if needed
service_toolkit.add(
    execute_python_code,
)
service_toolkit.add(
    list_directory_content,
)
service_toolkit.add(
    get_current_directory,
)
service_toolkit.add(
    execute_shell_command,
)

# Init the DataInterpreterAgent
planner_agent = PlannerAgent(
    name="planner",
    sys_prompt="You're a helpful assistant.",
    model_config_name="lite_llm_claude",
    service_toolkit=service_toolkit,
)

solver_agent = ReActAgent(
    name="solver",
    sys_prompt="You're a helpful assistant.",
    model_config_name="lite_llm_claude",
    service_toolkit=service_toolkit,
)

verifier_agent = VerifierAgent(
    name="verifier",
    sys_prompt="You're a helpful assistant.",
    model_config_name="lite_llm_claude",
    service_toolkit=service_toolkit,
)

synthesizer_agent = SynthesizerAgent(
    name="synthesizer",
    sys_prompt="You're a helpful assistant.",
    model_config_name="lite_llm_claude",
)

replanning_agent = ReplanningAgent(
    name="reviser",
    sys_prompt="You're a helpful assistant.",
    model_config_name="lite_llm_claude",
    service_toolkit=service_toolkit,
)

input_task = "Solve this math problem: The greatest common divisor of positive integers m and n is 6. The least common multiple of m and n is 126. What is the least possible value of m + n?"

#     template = "https://arxiv.org/list/{tag}/pastweek?skip=0&show=50"
#     tags = ["cs.ai", "cs.cl", "cs.ls", "cs.se"]
#     # tags = ["cs.AI"]
#     urls = [template.format(tag=tag) for tag in tags]
#     task = f"""This is a collection of arxiv urls: '{urls}' .
# Record each article, remove duplicates by title (they may have multiple tags), filter out papers related to
# large language model / agent / llm, print top 10 and visualize the word count of the titles"""

# sd_url = "http://your.sd.service.ip:port"
# task = (
#     f"I want to generate an image of a beautiful girl using the stable diffusion text2image tool, sd_url={sd_url}"
# )

# task = "Create a Snake game. Players need to control the movement of the snake to eat food and grow its body, while avoiding the snake's head touching their own body or game boundaries. Games need to have basic game logic, user interface. During the production process, please consider factors such as playability, beautiful interface, and convenient operation of the game. Note: pyxel environment already satisfied"

#     task = """
# Get products data from website https://scrapeme.live/shop/ and save it as a csv file.
# **Notice: Firstly parse the web page encoding and the text HTML structure;
# The first page product name, price, product URL, and image URL must be saved in the csv;**
# """
#     task = """"
# Get data from `paperlist` table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
# and save it to a csv file. paper title must include `multiagent` or `large language model`. *notice: print key variables*
# Don't fetch too much data at a time due to context window size."""

# task = "Run data analysis on sklearn Iris dataset, include a plot"

# WINE_REQ = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."

# DATA_DIR = "path/to/your/data"
# # sales_forecast data from https://www.kaggle.com/datasets/aslanahmedov/walmart-sales-forecast/data
# SALES_FORECAST_REQ = f"""Train a model to predict sales for each department in every store (split the last 40 weeks records as validation dataset, the others is train dataset), include plot total sales trends, print metric and plot scatter plots of
# groud truth and predictions on validation data. Dataset is {DATA_DIR}/train.csv, the metric is weighted mean absolute error (WMAE) for test data. Notice: *print* key variables to get more information for next task step.
# """

# REQUIREMENTS = {"wine": WINE_REQ, "sales_forecast": SALES_FORECAST_REQ}

# task = REQUIREMENTS["wine"]

# task = "This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '/Users/zhangzeyu/Documents/agentscope/04_titanic/split_train.csv', eval data path: '/Users/zhangzeyu/Documents/agentscope/04_titanic/split_eval.csv'."

# task = "Create a Snake game. Players need to control the movement of the snake to eat food and grow its body, while avoiding the snake's head touching their own body or game boundaries. Games need to have basic game logic, user interface. During the production process, please consider factors such as playability, beautiful interface, and convenient operation of the game. Note: pyxel environment already satisfied"
# task = "Get products data from website https://scrapeme.live/shop/ and save it as a csv file. Notice: Firstly parse the web page encoding and the text HTML structure; The first page product name, price, product URL, and image URL must be saved in the csv;"

final_solution = problem_solving(input_task)
print("final solution: ", final_solution)
