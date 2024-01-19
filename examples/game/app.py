# -*- coding: utf-8 -*-
from typing import List
import os
import yaml
import datetime

import agentscope

from utils import (
    CheckpointArgs,
    enable_web_ui,
    send_chat_msg,
    send_player_input,
    get_chat_msg,
    get_suggests,
    ResetException,
)

import gradio as gr
from gradio_groupchat import GroupChat

enable_web_ui()

glb_history_chat = []
MAX_NUM_DISPLAY_MSG = 20

import base64
# 图片本地路径转换为 base64 格式
def covert_image_to_base64(image_path):
    # 获得文件后缀名
    ext = image_path.split('.')[-1]
    if ext not in ['gif', 'jpeg', 'png']:
        ext = 'jpeg'

    with open(image_path, 'rb') as image_file:
        # Read the file
        encoded_string = base64.b64encode(image_file.read())

        # Convert bytes to string
        base64_data = encoded_string.decode('utf-8')

        # 生成base64编码的地址 
        base64_url = f'data:image/{ext};base64,{base64_data}'
        return base64_url

def format_cover_html(config: dict, bot_avatar_path='assets/bg.png'):
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

def export_chat_history():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_filename = f"chat_history_{timestamp}.txt"

    with open(export_filename, "w", encoding="utf-8") as file:
        for role, message in glb_history_chat:
            file.write(f"{role}: {message}\n")

    return gr.update(value=export_filename, visible=True)


def get_chat() -> List[List]:
    """Load the chat info from the queue, and put it into the history

    Returns:
        `List[List]`: The parsed history, list of tuple, [(role, msg), ...]

    """
    global glb_history_chat
    line = get_chat_msg()
    if line is not None:
        glb_history_chat += [line]

    return glb_history_chat[-MAX_NUM_DISPLAY_MSG:]


if __name__ == "__main__":

    def start_game():
        with open("./config/game_config.yaml", "r", encoding="utf-8") as file:
            GAME_CONFIG = yaml.safe_load(file)
        TONGYI_CONFIG = {
            "type": "tongyi",
            "name": "tongyi_model",
            "model_name": "qwen-max-1201",
            "api_key": os.environ.get("TONGYI_API_KEY"),
        }

        agentscope.init(model_configs=[TONGYI_CONFIG], logger_level="INFO")
        args = CheckpointArgs()
        args.game_config = GAME_CONFIG
        from main import main

        while True:
            try:
                main(args)
            except ResetException:
                print("重置成功")

    with gr.Blocks(css='assets/app.css') as demo:
        # Users can select the interested exp

        welcome = {
            "name": "饮食男女",
            "description": "这是一款模拟餐馆经营的文字冒险游戏, 快来开始吧😊"
        }
        
        user_chat_bot_cover = gr.HTML(format_cover_html(welcome))
        chatbot = GroupChat(label="Dialog", show_label=False, height=600, visible=False)

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

            user_chat_bot_suggest = gr.Dataset(
                label="选择一个",
                components=[user_chat_input],
                samples=[],
                visible=False,
            )

            user_chat_bot_suggest.select(
                lambda evt: evt[0],
                inputs=[user_chat_bot_suggest],
                outputs=[user_chat_input],
            )

        with gr.Column():
            send_button = gr.Button(
                value="📣发送",
                visible=False
            )

        export = gr.Accordion("导出选项", open=False, visible=False)
        with export:
            with gr.Column():
                export_button = gr.Button("导出完整游戏记录")
                export_output = gr.File(label="下载完整游戏记录", visible=False)

        return_welcome_button = gr.Button(
            value="↩️返回首页",
            visible=False,
        )
        
        def send_message(msg):
            send_player_input(msg)
            send_chat_msg(msg, "你")
            return ""

        def send_reset_message():
            global glb_history_chat
            glb_history_chat = []
            send_player_input("**Reset**")
            return ""

        def update_suggest():
            msg, samples = get_suggests()
            if msg is not None:
                return gr.Dataset(
                    label=msg,
                    samples=samples,
                    visible=True,
                    components=[user_chat_input],
                )
            else:
                return gr.Dataset(
                    label="选择一个",
                    components=[user_chat_input],
                    samples=[],
                    visible=True,
                )

        def game_ui():
            visible = True
            invisible = False
            return {chatbot:GroupChat(visible=visible), 
                    user_chat_input: gr.Text(visible=visible), 
                    send_button: gr.Button(visible=visible),
                    new_button: gr.Button(visible=invisible),
                    resume_button: gr.Button(visible=invisible),
                    return_welcome_button: gr.Button(visible=visible),
                    user_chat_bot_suggest: gr.Dataset(
                                                components=[user_chat_input],
                                                visible=visible,
                                            ),
                    export: gr.Accordion(visible=visible),
                    user_chat_bot_cover:gr.HTML(visible=invisible)}

        def welcome_ui():
            visible = True
            invisible = False
            return {chatbot:GroupChat(visible=invisible), 
                    user_chat_input: gr.Text(visible=invisible), 
                    send_button: gr.Button(visible=invisible),
                    new_button: gr.Button(visible=visible),
                    resume_button: gr.Button(visible=visible),
                    return_welcome_button: gr.Button(visible=invisible),
                    user_chat_bot_suggest: gr.Dataset(
                                                components=[user_chat_input],
                                                visible=invisible,
                                            ),
                    export: gr.Accordion(visible=invisible),
                    user_chat_bot_cover:gr.HTML(visible=visible)}

        outputs = [chatbot, user_chat_input, send_button, new_button, resume_button,return_welcome_button, user_chat_bot_suggest, export, user_chat_bot_cover]
       
        # submit message
        send_button.click(send_message, user_chat_input, user_chat_input)
        user_chat_input.submit(send_message, user_chat_input, user_chat_input)

        # change ui 
        new_button.click(game_ui, outputs=outputs)
        resume_button.click(game_ui, outputs=outputs)
        return_welcome_button.click(welcome_ui, outputs=outputs)

        # start game 
        new_button.click(send_reset_message)
        new_button.click(start_game)
        resume_button.click(start_game)
        
        # export 
        export_button.click(export_chat_history, [], export_output)

        # update chat history
        demo.load(get_chat, outputs=chatbot, every=0.5)
        demo.load(update_suggest, outputs=user_chat_bot_suggest, every=0.5)

    demo.queue()
    demo.launch()
