# -*- coding: utf-8 -*-
import argparse
import os
import sys
import threading
import time
from collections import defaultdict
from typing import List
import traceback
from multiprocessing import Event
from agentscope.web_ui.utils import (
    enable_web_ui,
    send_player_msg,
    send_player_input,
    get_chat_msg,
    SYS_MSG_PREFIX,
    ResetException,
    cycle_dots,
    check_uuid,
    send_chat_msg,
    generate_image_from_name,
    send_reset_msg,
    audio2text,
)

import gradio as gr
import modelscope_studio as mgr
import re

enable_web_ui()

MAX_NUM_DISPLAY_MSG = 20
FAIL_COUNT_DOWN = 30


def init_uid_list():
    return []


def init_uid_dict():
    return {}


glb_history_dict = defaultdict(init_uid_list)
glb_doing_signal_dict = defaultdict(init_uid_dict)
glb_end_choosing_index_dict = defaultdict(lambda: -1)


glb_signed_user = []
is_init = Event()


def reset_glb_var(uid):
    global glb_history_dict, glb_doing_signal_dict, glb_end_choosing_index_dict
    glb_history_dict[uid] = init_uid_list()
    glb_doing_signal_dict[uid] = init_uid_dict()
    glb_end_choosing_index_dict[uid] = -1


def get_chat(uid) -> List[List]:
    uid = check_uuid(uid)
    global glb_history_dict
    global glb_doing_signal_dict
    global glb_end_choosing_index_dict
    line = get_chat_msg(uid=uid)
    # TODO: Optimize the display effect, currently there is a problem of
    #  output display jumping
    if line is not None:
        if line[1] and line[1]["text"] == "**speak**":
            line[1]["text"] = "I am thinking"
            glb_doing_signal_dict[uid] = line
        elif line[1] and line[1]["text"] == "**end_choosing**":
            for idx in range(
                len(glb_history_dict[uid]) - 1,
                glb_end_choosing_index_dict[uid],
                -1,
            ):
                if (
                    glb_history_dict[uid][idx][1]
                    and "select-box" in glb_history_dict[uid][idx][1]["text"]
                ):
                    pattern = re.compile(r"(<select-box[^>]*?)>")
                    replacement_text = r'\1 disabled="True">'
                    glb_history_dict[uid][idx][1]["text"] = pattern.sub(
                        replacement_text,
                        glb_history_dict[uid][idx][1]["text"],
                    )
            glb_end_choosing_index_dict[uid] = len(glb_history_dict[uid]) - 1

        else:
            glb_history_dict[uid] += [line]
            glb_doing_signal_dict[uid] = []
    dial_msg, sys_msg = [], []
    for line in glb_history_dict[uid]:
        _, msg = line
        if isinstance(msg, dict):
            if SYS_MSG_PREFIX not in msg.get("text", ""):
                dial_msg.append(line)
            else:
                sys_msg.append(line)
        else:
            # User chat, format: (msg, None)
            dial_msg.append(line)
    if glb_doing_signal_dict[uid]:
        if glb_doing_signal_dict[uid][0]:
            text = cycle_dots(glb_doing_signal_dict[uid][0]["text"])
            glb_doing_signal_dict[uid][0]["text"] = text
        elif glb_doing_signal_dict[uid][1]:
            text = cycle_dots(glb_doing_signal_dict[uid][1]["text"])
            glb_doing_signal_dict[uid][1]["text"] = text

        dial_msg.append(glb_doing_signal_dict[uid])

    return dial_msg[-MAX_NUM_DISPLAY_MSG:]


def transcribe(audio_term, uid):
    uid = check_uuid(uid)
    content = audio2text(audio_path=audio_term)
    send_player_input(content, uid=uid)
    msg = f"""{content}
    <audio src="{audio_term}"></audio>"""
    send_player_msg(msg, "Me", uid=uid, avatar=None)
    return content


def send_image(image_term, uid):
    uid = check_uuid(uid)
    send_player_input(image_term, uid=uid)

    msg = f"""<img src="{image_term}"></img>"""
    avatar = generate_image_from_name("Me")
    send_player_msg(msg, "Me", uid=uid, avatar=avatar)


def fn_choice(data: gr.EventData, uid):
    uid = check_uuid(uid)
    send_player_input(data._data["value"], uid=uid)


def run_app():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=str, help="Script file to run")
    args = parser.parse_args()

    # Make sure script_path is an absolute path
    script_path = os.path.abspath(args.script)

    # Get the directory where the script is located
    script_dir = os.path.dirname(script_path)
    # Save the current working directory
    old_cwd = os.getcwd()
    # Change the current working directory to the directory where
    # script_path is located.
    os.chdir(script_dir)

    def import_function_from_path(
        module_path,
        function_name,
        module_name=None,
    ):
        import importlib.util

        script_dir = os.path.dirname(os.path.abspath(module_path))

        # Temporarily add a script directory to sys.path
        original_sys_path = sys.path[:]
        sys.path.insert(0, script_dir)

        try:
            # If a module name is not provided, you can use the filename (
            # without extension) as the module name
            if module_name is None:
                module_name = os.path.splitext(os.path.basename(module_path))[
                    0
                ]
            # Creating module specifications and loading modules
            spec = importlib.util.spec_from_file_location(
                module_name,
                module_path,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Getting a function from a module
            function = getattr(module, function_name)
        finally:
            # Restore the original sys.path
            sys.path = original_sys_path

        return function

    def check_for_new_session(uid):
        uid = check_uuid(uid)
        if uid not in glb_signed_user:
            glb_signed_user.append(uid)
            print("==========Signed User==========")
            print(f"Total number of users: {len(glb_signed_user)}")
            game_thread = threading.Thread(
                target=start_game,
                name=uid,
            )
            game_thread.start()

    def start_game():
        # is_init.wait()
        uid = threading.currentThread().name
        main = import_function_from_path(script_path, "main")

        while True:
            try:
                print("-----")
                main()
            except ResetException:
                print(f"Reset Successfully：{uid} ")
            except Exception as e:
                trace_info = "".join(
                    traceback.TracebackException.from_exception(e).format(),
                )
                for i in range(FAIL_COUNT_DOWN, 0, -1):
                    send_chat_msg(
                        f"{SYS_MSG_PREFIX}发生错误 {trace_info}, 即将在{i}秒后重启",
                        uid=uid,
                    )
                    time.sleep(1)
            reset_glb_var(uid)

    with gr.Blocks(css="assets/app.css") as demo:
        uuid = gr.Textbox(label="modelscope_uuid", visible=False)
        # uid = None
        # start_game(args, uuid)

        game_tabs = gr.Tabs(visible=True)

        with game_tabs:
            main_tab = gr.Tab("Main", id=0)
            with main_tab:
                with gr.Row():
                    chatbot = mgr.Chatbot(
                        elem_classes="app-chatbot",
                        label="Dialog",
                        show_label=False,
                        bubble_full_width=False,
                        visible=True,
                    )
            # with gr.Column():
            #     start_button = gr.Button(value="Start")

            with gr.Column():
                user_chat_input = gr.Textbox(
                    label="user_chat_input",
                    placeholder="Say something here",
                    show_label=False,
                )
                send_button = gr.Button(value="📣Send")
            with gr.Row():
                audio = gr.Accordion("Audio input", open=False)
                with audio:
                    audio_term = gr.Audio(
                        visible=True,
                        type="filepath",
                        format="wav",
                    )
                    submit_audio_button = gr.Button(value="Send Audio")
                image = gr.Accordion("Image input", open=False)
                with image:
                    image_term = gr.Image(
                        visible=True,
                        height=300,
                        interactive=True,
                        type="filepath",
                    )
                    submit_image_button = gr.Button(value="Send Image")

        def send_message(msg, uid):
            uid = check_uuid(uid)
            print("uid=", uid)
            send_player_input(msg, uid=uid)
            avatar = generate_image_from_name("Me")
            send_player_msg(msg, "Me", uid=uid, avatar=avatar)
            return ""

        def send_reset_message(uid):
            uid = check_uuid(uid)
            send_reset_msg("**Reset**", uid=uid)
            return ""

        # start_button.click(send_reset_message, inputs=[uuid]).then(
        #     check_for_new_session,
        #     inputs=[uuid],
        # )

        # submit message
        send_button.click(
            send_message,
            [user_chat_input, uuid],
            user_chat_input,
        )
        user_chat_input.submit(
            send_message,
            [user_chat_input, uuid],
            user_chat_input,
        )

        submit_audio_button.click(transcribe, inputs=[audio_term, uuid])

        submit_image_button.click(send_image, inputs=[image_term, uuid])

        chatbot.custom(fn=fn_choice, inputs=[uuid])

        demo.load(
            check_for_new_session,
            inputs=[uuid],
            every=0.5,
        )

        demo.load(
            get_chat,
            inputs=[uuid],
            outputs=[chatbot],
            every=0.5,
        )
    demo.queue()
    demo.launch()


if __name__ == "__main__":
    run_app()
