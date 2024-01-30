# -*- coding: utf-8 -*-
import base64
import os
import yaml
import datetime
import threading
from collections import defaultdict
from typing import List
from multiprocessing import Event
import agentscope
from config_utils import load_user_cfg, save_user_cfg, load_default_cfg, load_configs
from utils import (
    CheckpointArgs,
    enable_web_ui,
    send_player_msg,
    send_player_input,
    get_chat_msg,
    SYS_MSG_PREFIX,
    ResetException,
    get_clue
)
from create_config_tab import create_config_tab
from generate_image import generate_user_logo_file

import gradio as gr
import modelscope_gradio_components as mgr

enable_web_ui()

role_clue_dict = {}


def init_uid_list():
    return []


def check_uuid(uid):
    if not uid or uid == '':
        if os.getenv('MODELSCOPE_ENVIRONMENT') == 'studio':
            raise gr.Error('请登陆后使用! (Please login first)')
        else:
            uid = 'local_user'
    return uid

def get_role_by_name(name, uid):
    uid = check_uuid(uid)
    roles = load_default_cfg(uid)
    for role in roles:
        if role['name'] == role_name:
            return role
    return None 

glb_history_dict = defaultdict(init_uid_list)
glb_signed_user = []
is_init = Event()
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
    <div class="bot_intro_label">{config.get("introduction_label", "玩法介绍")}</div>
    <div class="bot_intro_ctx">
    {config.get("introduction_context", "玩法介绍")}</div>
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


def get_dial_chat(uid) -> List[List]:
    """Load the chat info from the queue, and put it into the history

    Returns:
        `List[List]`: The parsed history, list of tuple, [(role, msg), ...]

    """
    uid = check_uuid(uid)
    global glb_history_dict
    line = get_chat_msg(uid=uid)
    if line is not None:
        glb_history_dict[uid] += [line]

    dial_msg = []
    for line in glb_history_dict[uid]:
        _, msg = line
        if isinstance(msg, dict):
            if SYS_MSG_PREFIX not in msg.get("text", ""):
                dial_msg.append(line)
        else:
            # User chat, format: (msg, None)
            dial_msg.append(line)

    return dial_msg[-MAX_NUM_DISPLAY_MSG:]


def get_sys_chat(uid) -> List[List]:
    uid = check_uuid(uid)
    global glb_history_dict

    sys_msg = []
    for line in glb_history_dict[uid]:
        _, msg = line
        if isinstance(msg, dict):
            if SYS_MSG_PREFIX in msg.get("text", ""):
                sys_msg.append(line)

    return sys_msg[-MAX_NUM_DISPLAY_MSG:]


def update_role_clue_dict(uid):
    global role_clue_dict

    uid = check_uuid(uid)
    clue_item = get_clue(uid)
    if clue_item:
        role_name_ = clue_item['name']
        if clue_item["clue"] is not None:
            role_clue_dict[role_name_]['clue_list'].append(clue_item['clue'])
        role_clue_dict[role_name_]['unexposed_num'] = clue_item[
            'unexposed_num']

    flex_container_html_list = []
    for role_name_ in role_clue_dict.keys():
        flex_container_html = f"""
                <div style='margin-bottom: 40px;'>
                    <div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;'>
            """
        for clue in role_clue_dict[role_name_]["clue_list"]:
            flex_container_html += f"""
                    <div style='flex: 1; min-width: 200px; max-width: 200px; height: 300px; background-color: #fff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin: 10px; padding: 20px; border-radius: 15px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden;'>
                        <img src='{clue['image'] if 'image' in clue.keys() else "#"}' alt='Clue image' style='height: 150px; width: 100%; object-fit: cover; border-radius: 10px; margin-bottom: 10px;'>
                        <div style='flex-grow: 1; overflow-y: auto;'>
                            <h4 style='margin: 5px 0; text-align: center; word-wrap: break-word; font-size: 18px; font-weight: bold;'>{clue['name']}</h4>
                            <p style='margin: 5px 0; word-wrap: break-word; text-align: justify; font-size: 14px;'>{clue['content'] if 'content' in clue.keys() else clue['summary']}</p>
                        </div>
                    </div>
                """
        if role_clue_dict[role_name_]['unexposed_num']:
            for _ in range(role_clue_dict[role_name_]['unexposed_num']):
                flex_container_html += f"""
                            <div style='flex: 1; min-width: 200px; max-width: 200px; height: 300px; background: repeating-linear-gradient(45deg, #ccc, #ccc 10px, #ddd 10px, #ddd 20px); opacity: 0.8; margin: 10px; padding: 20px; border-radius: 15px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden;'>
                                <div style='flex-grow: 1; height: 150px; width: 100%; background-color: #bbb; border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center;'>
                                    <span style='color: #fff; font-weight: bold; font-size: 24px;'>?</span>
                                </div>
                                <h4 style='margin: 5px 0; text-align: center; word-wrap: break-word; font-size: 18px; font-weight: bold; color: #999;'>待发现</h4>
                            </div>
                        """
        flex_container_html += """
                                    </div>
                            """
        flex_container_html_list.append(flex_container_html)
    return [gr.HTML(x) for x in flex_container_html_list]


def fn_choice(data: gr.EventData, uid):
    uid = check_uuid(uid)
    send_player_input(data._data["value"], uid=uid)


if __name__ == "__main__":

    def init_game():
        if not is_init.is_set():
            TONGYI_CONFIG = {
                "type": "tongyi",
                "name": "tongyi_model",
                "model_name": "qwen-max-1201",
                "api_key": os.environ.get("TONGYI_API_KEY"),
            }
            HTTP_LLM_CONFIG = {
                "type": "post_api",
                "name": os.environ.get("HTTP_LLM_MODEL"),
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('HTTP_LLM_API_KEY')}"
                },
                "api_url": os.environ.get("HTTP_LLM_URL"),
                "messages_key": "messages",
                "json_args": {
                    "model": os.environ.get("HTTP_LLM_MODEL"),
                    "n": 1,
                    "temperature": 0.7,
                }

            }

            agentscope.init(model_configs=[TONGYI_CONFIG, HTTP_LLM_CONFIG],
                            logger_level="DEBUG")
            is_init.set()

    def check_for_new_session(uid):
        uid = check_uuid(uid)
        if uid not in glb_signed_user:
            glb_signed_user.append(uid)
            print("==========Signed User==========")
            print(f"Total number of users: {len(glb_signed_user)}")
            game_thread = threading.Thread(target=start_game, args=(uid,))
            game_thread.start()

    def start_game(uid):
        is_init.wait()
        uid = check_uuid(uid)
        GAME_CONFIG = load_configs("config/game_config.yaml")
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
            'name': '饮食男女',
            'description': '这是一款模拟餐馆经营的文字冒险游戏, 快来开始吧😊',
            'introduction_label': "<br>玩法介绍",
            'introduction_context': "在一个热闹的小镇上<br>"
                                    "你经营着一家餐馆<br>"
                                    "最近小镇上出现了一些有意思的事儿<br>"
                                    "......<br>"
                                    "通过美味的食物以及真诚的内心去打动顾客<br>"
                                    "为他们排忧解难"
        }
        tabs = gr.Tabs(visible=True)
        with tabs:
            welcome_tab = gr.Tab('游戏界面', id=0)
            config_tab = gr.Tab('游戏配置', id=1)
            with welcome_tab:
                user_chat_bot_cover = gr.HTML(format_cover_html(welcome))
                with gr.Row():
                    with gr.Column():
                        new_button = gr.Button(value='🚀新的探险', )
                    with gr.Column():
                        resume_button = gr.Button(value='🔥续写情缘', )

        with config_tab:
            create_config_tab(config_tab, uuid)

        game_tabs = gr.Tabs(visible=False)

        with game_tabs:
            main_tab = gr.Tab('主界面', id=0)
            clue_tab = gr.Tab('线索', id=1)
            with main_tab:
                with gr.Row():
                    chatbot = mgr.Chatbot(
                        label="Dialog",
                        show_label=False,
                        height=500,
                        visible=False,
                        bubble_full_width=False,
                    )

                    chatsys = mgr.Chatbot(
                        label="系统栏",
                        show_label=True,
                        height=500,
                        visible=False,
                        bubble_full_width=False,
                        layout="panel",
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

        with clue_tab:
            guild_html = """
            <div style='text-align: center; margin-top: 20px; margin-bottom: 40px; padding: 20px; background: linear-gradient(to right, #f7f7f7, #ffffff); border-left: 5px solid #007bff; border-right: 5px solid #007bff;'>
                <p style='font-size: 18px; color: #333; max-width: 600px; margin: auto; line-height: 1.6; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;'>
                    <strong>探索提示：</strong><br>
                    这些是您在调查过程中已经搜集到的线索卡。随着您与各位角色互动的增加，您对他们的了解将会提升，从而有可能获得更多线索卡。请继续与角色进行对话，探索他们的背景故事，并通过观察和推理揭开隐藏的秘密。
                </p>
            </div>
            """
            gr.HTML(guild_html)
            role_tabs = gr.Tabs(visible=False)
            roles = load_user_cfg()
            role_names = [role['name'] for role in roles]
            # role_names = ['王先生', '老许']
            # role_tab_list = []
            role_tab_clue_dict = {}
            i = 0

            for role_name_t in role_names:
                role_clue_dict[role_name_t] = {
                    "clue_list": [],
                    "unexposed_num": None,
                }
                role = gr.Tab(label=role_name_t, id=i)
                # role_tab_list.append(role_name)
                i += 1
                with role:
                    role_tab_clue_dict[role_name_t] = gr.HTML()


        def send_message(msg, uid):
            uid = check_uuid(uid)
            send_player_input(msg, uid=uid)
            send_player_msg(msg, "我", uid=uid)
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
                tabs: gr.Tabs(visible=invisible),
                game_tabs: gr.Tabs(visible=visible),
                role_tabs: gr.Tabs(visible=visible),
                chatbot: mgr.Chatbot(visible=visible),
                chatsys: mgr.Chatbot(visible=visible),
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
                tabs: gr.Tabs(visible=visible),
                game_tabs: gr.Tabs(visible=invisible),
                role_tabs: gr.Tabs(visible=invisible),
                chatbot: mgr.Chatbot(visible=invisible),
                chatsys: mgr.Chatbot(visible=invisible),
                user_chat_input: gr.Text(visible=invisible),
                send_button: gr.Button(visible=invisible),
                new_button: gr.Button(visible=visible),
                resume_button: gr.Button(visible=visible),
                return_welcome_button: gr.Button(visible=invisible),
                export: gr.Accordion(visible=invisible),
                user_chat_bot_cover: gr.HTML(visible=visible),
            }


        outputs = [
            tabs,
            game_tabs,
            role_tabs,
            chatbot,
            chatsys,
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
        chatsys.custom(fn=fn_choice, inputs=[uuid])

        # change ui
        new_button.click(game_ui, outputs=outputs)
        resume_button.click(game_ui, outputs=outputs)
        return_welcome_button.click(welcome_ui, outputs=outputs)

        # start game
        new_button.click(send_reset_message, inputs=[uuid]).then(check_for_new_session, inputs=[uuid])
        resume_button.click(check_for_new_session, inputs=[uuid])

        # export
        export_button.click(export_chat_history, [uuid], export_output)

        # update chat history
        demo.load(init_game)
        demo.load(get_dial_chat,
                  inputs=[uuid],
                  outputs=chatbot,
                  every=0.5)
        demo.load(get_sys_chat,
                  inputs=[uuid],
                  outputs=chatsys,
                  every=0.5, )

        demo.load(update_role_clue_dict,
                  inputs=[uuid],
                  outputs=[role_tab_clue_dict[i] for i in role_names],
                  every=0.5)

    demo.queue()
    demo.launch()
