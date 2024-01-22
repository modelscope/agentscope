# -*- coding: utf-8 -*-
import base64
import os
import yaml
import datetime
import threading
from collections import defaultdict
from typing import List

import agentscope

from utils import (
    CheckpointArgs,
    enable_web_ui,
    send_chat_msg,
    send_player_msg,
    send_player_input,
    get_chat_msg,
    ResetException,
)

import gradio as gr
import modelscope_gradio_components as mgr

enable_web_ui()


def init_uid_list():
    return []


def check_uuid(uid):
    if not uid or uid == '':
        if os.getenv('MODELSCOPE_ENVIRONMENT') == 'studio':
            raise gr.Error('请登陆后使用! (Please login first)')
        else:
            uid = 'local_user'
    return uid


glb_history_dict = defaultdict(init_uid_list)
glb_signed_user = []
is_init = False
MAX_NUM_DISPLAY_MSG = 20


# 图片本地路径转换为 base64 格式
def covert_image_to_base64(image_path):
    # 获得文件后缀名
    ext = image_path.split(".")[-1]
    if ext not in ["gif", "jpeg", "png"]:
        ext = "jpeg"

    with open(image_path, "rb") as image_file:
        # Read the file
        encoded_string = base64.b64encode(image_file.read())

        # Convert bytes to string
        base64_data = encoded_string.decode("utf-8")

        # 生成base64编码的地址
        base64_url = f"data:image/{ext};base64,{base64_data}"
        return base64_url


def format_cover_html(config: dict, bot_avatar_path="assets/bg.png"):
    image_src = covert_image_to_base64(bot_avatar_path)
    return f"""
<div class="bot_cover">
    <div class="bot_avatar">
        <img src={image_src} />
    </div>
    <div class="bot_name">{config.get("name", "经营餐厅")}</div>
    <div class="bot_desp">{config.get("description", "快来经营你的餐厅吧")}</div>
</div>
"""


def export_chat_history(uid):
    uid = check_uuid(uid)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_filename = f"chat_history_{timestamp}.txt"

    with open(export_filename, "w", encoding="utf-8") as file:
        for role, message in glb_history_dict[uid]:
            file.write(f"{role}: {message}\n")

    return gr.update(value=export_filename, visible=True)


def get_chat(uid) -> List[List]:
    """Load the chat info from the queue, and put it into the history

    Returns:
        `List[List]`: The parsed history, list of tuple, [(role, msg), ...]

    """
    uid = check_uuid(uid)
    global glb_history_dict
    line = get_chat_msg(uid=uid)
    if line is not None:
        glb_history_dict[uid] += [line]
    return glb_history_dict[uid][-MAX_NUM_DISPLAY_MSG:]


def fn_choice(data: gr.EventData, uid):
    uid = check_uuid(uid)
    send_player_input(data._data["value"], uid=uid)


if __name__ == "__main__":

    def init_game():
        global is_init
        if not is_init:
            TONGYI_CONFIG = {
                "type": "tongyi",
                "name": "tongyi_model",
                "model_name": "qwen-max-1201",
                "api_key": os.environ.get("TONGYI_API_KEY"),
            }
            agentscope.init(model_configs=[TONGYI_CONFIG], logger_level="INFO")
            is_init = True

    def check_for_new_session(uid):
        uid = check_uuid(uid)
        if uid not in glb_signed_user:
            glb_signed_user.append(uid)
            print("==========Signed User==========")
            print(f"Total number of users: {len(glb_signed_user)}")
            game_thread = threading.Thread(target=start_game, args=(uid,))
            game_thread.start()

    def start_game(uid):
        uid = check_uuid(uid)
        with open("./config/game_config.yaml", "r", encoding="utf-8") as file:
            GAME_CONFIG = yaml.safe_load(file)

        args = CheckpointArgs()
        args.game_config = GAME_CONFIG
        args.uid = uid
        from main import main

        while True:
            try:
                main(args)
            except ResetException:
                print("重置成功")

    with gr.Blocks(css="assets/app.css") as demo:
        uuid = gr.Textbox(label='modelscope_uuid', visible=False)

        welcome = {
            "name": "饮食男女",
            "description": "这是一款模拟餐馆经营的文字冒险游戏, 快来开始吧😊",
        }

        user_chat_bot_cover = gr.HTML(format_cover_html(welcome))
        chatbot = mgr.Chatbot(
            label="Dialog",
            show_label=False,
            height=600,
            visible=False,
        )

        with gr.Row():
            with gr.Column():
                new_button = gr.Button(
                    value="🚀新的探险",
                )
            with gr.Column():
                resume_button = gr.Button(
                    value="🔥续写情缘",
                )

        with gr.Row():
            with gr.Column():
                user_chat_input = gr.Textbox(
                    label="user_chat_input",
                    placeholder="想说点什么",
                    show_label=False,
                    interactive=True,
                    visible=False,
                )

        with gr.Column():
            send_button = gr.Button(
                value="📣发送",
                visible=False,
            )

        export = gr.Accordion("导出选项", open=False, visible=False)
        with export:
            with gr.Column():
                export_button = gr.Button("导出完整游戏记录")
                export_output = gr.File(
                    label="下载完整游戏记录",
                    visible=False,
                )

        def send_message(msg, uid):
            uid = check_uuid(uid)
            send_player_input(msg, uid=uid)
            send_player_msg(msg, "你", uid=uid)
            return ""

        return_welcome_button = gr.Button(
            value="↩️返回首页",
            visible=False,
        )

        def send_reset_message(uid):
            uid = check_uuid(uid)
            global glb_history_dict
            glb_history_dict[uid] = init_uid_list()
            send_player_input("**Reset**", uid=uid)
            return ""

        def game_ui():
            visible = True
            invisible = False
            return {
                chatbot: mgr.Chatbot(visible=visible),
                user_chat_input: gr.Text(visible=visible),
                send_button: gr.Button(visible=visible),
                new_button: gr.Button(visible=invisible),
                resume_button: gr.Button(visible=invisible),
                return_welcome_button: gr.Button(visible=visible),
                export: gr.Accordion(visible=visible),
                user_chat_bot_cover: gr.HTML(visible=invisible),
            }

        def welcome_ui():
            visible = True
            invisible = False
            return {
                chatbot: mgr.Chatbot(visible=invisible),
                user_chat_input: gr.Text(visible=invisible),
                send_button: gr.Button(visible=invisible),
                new_button: gr.Button(visible=visible),
                resume_button: gr.Button(visible=visible),
                return_welcome_button: gr.Button(visible=invisible),
                export: gr.Accordion(visible=invisible),
                user_chat_bot_cover: gr.HTML(visible=visible),
            }

        outputs = [
            chatbot,
            user_chat_input,
            send_button,
            new_button,
            resume_button,
            return_welcome_button,
            export,
            user_chat_bot_cover,
        ]

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

        chatbot.custom(fn=fn_choice, inputs=[uuid])

        # change ui
        new_button.click(game_ui, outputs=outputs)
        resume_button.click(game_ui, outputs=outputs)
        return_welcome_button.click(welcome_ui, outputs=outputs)

        # start game
        new_button.click(send_reset_message, inputs=[uuid])
        resume_button.click(check_for_new_session, inputs=[uuid])

        # export
        export_button.click(export_chat_history, [uuid], export_output)

        # update chat history
        demo.load(init_game)
        demo.load(check_for_new_session, inputs=[uuid], every=0.1)
        demo.load(get_chat, inputs=[uuid], outputs=chatbot, every=0.5)

    demo.queue()
    demo.launch()
