# -*- coding: utf-8 -*-
"""
The entry point of the web UI that renders the log (can be still running).
"""

import re
from multiprocessing import Process, Queue

import time
from typing import Generator, List, Any


try:
    import gradio as gr
    from gradio_groupchat import GroupChat
except ImportError:
    gr = None
    GroupChat = Any

try:
    from agentscope.constants import MSG_TOKEN
except ImportError:
    PACKAGE_NAME = "agentscope"
    MSG_TOKEN = f"<{PACKAGE_NAME}_msg>"


def follow_read(
    logfile_path: str,
    skip_existing_content: bool = False,
) -> Generator:
    """Read a file in online and iterative manner

    Args:
        logfile_path (`str`):
            The file path to be read.
        skip_existing_content (`bool`, defaults to `False`):
            If True, read from the end, otherwise read from the beginning.

    Returns:
        One line string of the file content.
    """
    # in most unix file systems, the read operation is safe
    # for a file being target file of another "write process"
    with open(logfile_path, "r", encoding="utf-8", errors="ignore") as logfile:
        if skip_existing_content:
            # move to the file's end, similar to `tail -f`
            logfile.seek(0, 2)

        while True:
            line = logfile.readline()
            if not line:
                # no new line, wait to avoid CPU override
                time.sleep(0.1)
                continue
            yield line


# e.g., "2024-01-09 14:47:20.004 | DEBUG    | agentscope.msghub:
# __enter__:36 - Enter msghub with participants: Player1, Player2"
log_pattern = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| \w+ +\| .+$",
)

# e.g., ""Player1: some message by me""
chat_message_pattern = re.compile(r"^(?P<role>.+?): (?P<message>.+)$")


def is_chat_message_format(s: str) -> bool:
    """Check the string to be parsed, whether be a chat-message.

    Args:
        s (`str`): the message as string.

    Returns:
        `bool`: the indicator as a bool
    """
    if log_pattern.match(s):
        return False
    if chat_message_pattern.match(s):
        return True
    return False


# TODO:
#  - show image, audio, and data in other modality
#  - make the dialog box expensive to show detailed info


MAX_CHAT_SIZE = 20
FULL_LOG_MAX_LINE = 50
SKIP_HISTORY_LOG = False

glb_queue_chat_msg = Queue()
glb_queue_system_log = Queue()
glb_queue_file_name = Queue()
glb_current_file_name = None

glb_history_chat = []
glb_history_system_log = []


def put_file_name(file_name: str) -> str:
    """Store the file_name given by user, via the queue

    Args:
        file_name (`str`):
            The file_name given by user

    Returns:
        `str`: The given file name.
    """
    global glb_queue_file_name
    if file_name:
        glb_queue_file_name.put(file_name)
    return file_name


def get_chat() -> List[List]:
    """Load the chat info from the queue, and put it into the history

    Returns:
        `List[List]`: The parsed history, list of tuple, [(role, msg), ...]

    """
    global glb_history_chat, glb_queue_chat_msg
    if not glb_queue_chat_msg.empty():
        line = glb_queue_chat_msg.get(block=False)
        line = line.replace(MSG_TOKEN, "")
        match_res = chat_message_pattern.match(line)
        if match_res is not None:
            role = match_res.group("role")
            message = match_res.group("message")
            glb_history_chat += [[role, message]]
        glb_history_chat = glb_history_chat[:MAX_CHAT_SIZE]
    return glb_history_chat


def get_system_log() -> str:
    """Load the system log info from the queue, and collect the res into a str

    Returns:
        The collected string.
    """
    global glb_history_system_log, glb_queue_system_log
    if not glb_queue_system_log.empty():
        line = glb_queue_system_log.get(block=False)
        glb_history_system_log.append(line)
        glb_history_system_log = glb_history_system_log[:FULL_LOG_MAX_LINE]
        return "".join(glb_history_system_log)
    return "".join(glb_history_system_log)


def handle_file_selection(
    queue_file_name: Queue,
    queue_system_log: Queue,
    queue_chat: Queue,
) -> None:
    """

    Args:
        queue_file_name (`Queue`):
            The queue to store and pass `file_name` given by user.
        queue_system_log (`Queue`):
            The queue to store and pass system log within the file
        queue_chat (`Queue`):
            The queue to store and pass chat msg within the file
    """
    global glb_current_file_name
    total_msg_cnt = 0
    full_msg = ""
    while True:
        if glb_current_file_name:
            for line in follow_read(
                glb_current_file_name,
                skip_existing_content=SKIP_HISTORY_LOG,
            ):
                msg_cnt = line.count(MSG_TOKEN)
                total_msg_cnt += msg_cnt
                # print("line is: ", line)
                # print("total_msg_cnt is: ", total_msg_cnt)
                if msg_cnt % 2 == 0 and msg_cnt != 0:
                    # contain both begin and end <msg> in the same line
                    queue_chat.put(line)
                elif msg_cnt % 2 == 0 and total_msg_cnt % 2 == 1:
                    # no or paired msg token this line,
                    # but still waiting for the end of msg
                    full_msg += line.strip()
                elif msg_cnt % 2 == 1 and total_msg_cnt % 2 == 0:
                    # the left msg token, waiting for the end of the msg
                    parts = line.split(MSG_TOKEN)
                    full_msg += "".join(parts[1:])  # the right remaining parts
                elif msg_cnt % 2 == 1 and total_msg_cnt % 2 == 1:
                    # the right msg token
                    parts = line.split(MSG_TOKEN)
                    full_msg += "".join(parts[:-1])  # the left remaining parts
                    # reset the full_msg
                    queue_chat.put(full_msg)
                    full_msg = ""
                else:
                    queue_system_log.put(line)

                # using the up-to-date file name within the queue
                find_new_file_to_read = False
                while not queue_file_name.empty():
                    glb_current_file_name = queue_file_name.get(block=False)
                    find_new_file_to_read = True
                if find_new_file_to_read:
                    break
        else:
            # wait users to determine the log file
            time.sleep(1)
            while not queue_file_name.empty():
                glb_current_file_name = queue_file_name.get(block=False)


if __name__ == "__main__":
    with gr.Blocks() as demo:
        # Users can select the interested exp
        with gr.Row():
            file_selector = gr.FileExplorer(
                label="Choose your log file (the workdir is `.`)",
                file_count="single",
                show_label=True,
            )
        with gr.Row():
            output_area_log_f_name = gr.Textbox(
                label="Log File Name",
                show_label=True,
            )
        with gr.Row():
            chatbot = GroupChat(label="Dialog", show_label=True)
            output_area_sys_log = gr.Textbox(label="Full System Log")

        file_selector.change(
            put_file_name,
            inputs=file_selector,
            outputs=output_area_log_f_name,
        )
        demo.load(get_chat, inputs=None, outputs=chatbot, every=1)
        demo.load(
            get_system_log,
            inputs=None,
            outputs=output_area_sys_log,
            every=0.5,
        )

    Process(
        target=handle_file_selection,
        args=(glb_queue_file_name, glb_queue_system_log, glb_queue_chat_msg),
    ).start()

    demo.launch()
