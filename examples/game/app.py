# -*- coding: utf-8 -*-
import base64
import os
import datetime
import threading
from collections import defaultdict
from typing import List
from multiprocessing import Event
import agentscope
from config_utils import load_user_cfg, load_configs
from utils import (
    CheckpointArgs,
    enable_web_ui,
    send_player_msg,
    send_player_input,
    get_chat_msg,
    SYS_MSG_PREFIX,
    ResetException,
    get_clue_msg,
    get_story_msg,
    check_uuid
)
from create_config_tab import create_config_tab, create_config_accord

import gradio as gr
import modelscope_gradio_components as mgr

enable_web_ui()

MAX_NUM_DISPLAY_MSG = 20


def init_uid_list():
    return []


def init_uid_dict():
    return {}


glb_history_dict = defaultdict(init_uid_list)
glb_clue_dict = defaultdict(init_uid_dict)
glb_story_dict = defaultdict(init_uid_dict)

glb_signed_user = []
is_init = Event()


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


def format_cover_html(bot_avatar_path="assets/bg.png"):
    config = {
        'name': '谜馔',
        'description': '这是一款模拟餐馆经营的解密推理游戏, 快来开始吧😊',
        'introduction_label': "<br>玩法介绍",
        'introduction_context': "在一个热闹的小镇上<br>"
                                "你经营着一家餐馆<br>"
                                "最近小镇上发生了一些离奇的事件<br>"
                                "......<br>"
                                "通过美味的食物以及真诚的内心去打动顾客<br>"
                                "为他们排忧解难"
    }
    image_src = covert_image_to_base64(bot_avatar_path)
    return f"""
<div class="bot_cover">
    <div class="bot_avatar">
        <img src={image_src} />
    </div>
    <div class="bot_name">{config.get("name", "经营餐厅")}</div>
    <div class="bot_desc">{config.get("description", "快来经营你的餐厅吧")}</div>
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


def get_chat(uid) -> List[List]:
    uid = check_uuid(uid)
    global glb_history_dict
    line = get_chat_msg(uid=uid)
    if line is not None:
        glb_history_dict[uid] += [line]

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

    return dial_msg[-MAX_NUM_DISPLAY_MSG:], sys_msg[-MAX_NUM_DISPLAY_MSG:]


def get_story(uid):
    global glb_story_dict
    uid = check_uuid(uid)

    story_item = get_story_msg(uid)

    # Only initialize at the first time
    for c in role_names:  # glb vars, careful!
        if c not in glb_story_dict[uid]:
            glb_story_dict[uid][c] = []
        else:
            break

    if story_item:
        glb_story_dict[uid][story_item["name"]].append(story_item["story"])

    flex_container_html = """
    <div class='story-container'>
    <p></p>
"""

    for role_name_, stories in glb_story_dict[uid].items():
        if len(stories) == 0:
            # Locked story row
            flex_container_html += f"""
                        <div class='story-row locked'>
                            <p class='story-title'>{role_name_} 的故事</p>
                            <span class='lock-icon'>&#128274;</span>  <!-- Unicode lock icon -->
                        </div>
                    """
        else:
            # Unlocked story row
            for index, s in enumerate(stories):
                flex_container_html += f"""
                            <div class='story-row'>
                                <p class='story-title'>{role_name_} 的第{index + 1}段故事</p>
                                <div class='story-content'>{s}</div>
                            </div>
                        """

    flex_container_html += """
    </div>
    """

    return gr.HTML(flex_container_html)


def get_clue(uid):
    global glb_clue_dict

    uid = check_uuid(uid)
    clue_item = get_clue_msg(uid)

    # Only initialize at the first time
    for c in role_names:  # glb vars, careful!
        if c not in glb_clue_dict[uid]:
            glb_clue_dict[uid][c] = {
                'clue_list': [],
                'unexposed_num': 0,
            }
        else:
            break

    if clue_item:
        role_name_ = clue_item['name']
        if clue_item["clue"] is not None:
            glb_clue_dict[uid][role_name_]['clue_list'].append(clue_item['clue'])
        glb_clue_dict[uid][role_name_]['unexposed_num'] = clue_item['unexposed_num']

    flex_container_html_list = []
    for role_name_ in glb_clue_dict[uid].keys():
        flex_container_html = f"""
                <div style='margin-bottom: 40px;'>
                    <div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;'>
            """
        for clue in glb_clue_dict[uid][role_name_]["clue_list"]:
            flex_container_html += f"""
                       <div class='clue-card'>
                           <img src='{clue['image'] if 'image' in clue.keys() else "#"}' alt='Clue image' style='height: 150px; width: 100%; object-fit: cover; border-radius: 10px; margin-bottom: 10px;'>
                           <div style='flex-grow: 1; overflow-y: auto;'>
                               <h4 style='margin: 5px 0; text-align: center; word-wrap: break-word; font-size: 18px; font-weight: bold;'>{clue['name']}</h4>
                               <p style='margin: 5px 0; word-wrap: break-word; text-align: justify; font-size: 14px;'>{clue['content'] if 'content' in clue.keys() else clue['summary']}</p>
                           </div>
                       </div>
                   """
        if glb_clue_dict[uid][role_name_]['unexposed_num']:
            for _ in range(glb_clue_dict[uid][role_name_]['unexposed_num']):
                flex_container_html += f"""
                            <div class='clue-card clue-card-locked'>
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
                print(f"重置成功：{uid} ")

    with gr.Blocks(css="assets/app.css") as demo:
        uuid = gr.Textbox(label='modelscope_uuid', visible=False)
        tabs = gr.Tabs(visible=True)
        with tabs:
            welcome_tab = gr.Tab('游戏界面', id=0)
            config_tab = gr.Tab('游戏配置', id=1)
            with welcome_tab:
                user_chat_bot_cover = gr.HTML(format_cover_html())
                with gr.Row():
                    with gr.Column():
                        new_button = gr.Button(value='🚀新的探险', )
                    with gr.Column():
                        resume_button = gr.Button(value='🔥续写情缘', )
            
                config_accordion =  gr.Accordion('导入导出配置', open=False)
                with config_accordion:
                    create_config_accord(config_accordion, uuid)

        with config_tab:
            create_config_tab(config_tab, uuid)

        game_tabs = gr.Tabs(visible=False)

        with game_tabs:
            main_tab = gr.Tab('主界面', id=0)
            clue_tab = gr.Tab('线索', id=1)
            story_tab = gr.Tab('故事', id=2)
            with main_tab:
                with gr.Row():
                    chatbot = mgr.Chatbot(
                        label="Dialog",
                        show_label=False,
                        height=500,
                        bubble_full_width=False,
                    )

                    chatsys = mgr.Chatbot(
                        label="系统栏",
                        show_label=True,
                        height=500,
                        bubble_full_width=False,
                        layout="panel",
                    )

            with gr.Row():
                with gr.Column():
                    user_chat_input = gr.Textbox(
                        label="user_chat_input",
                        placeholder="想说点什么",
                        show_label=False,
                    )

            with gr.Column():
                send_button = gr.Button(value="📣发送")

            export = gr.Accordion("导出选项", open=False)
            with export:
                with gr.Column():
                    export_button = gr.Button("导出完整游戏记录")
                    export_output = gr.File(
                        label="下载完整游戏记录",
                        elem_classes=["signature-file-uploader"],
                        visible=False
                    )
            with gr.Row():
                return_welcome_button = gr.Button(value="↩️返回首页")
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

            role_tab_clue_dict = {}

            for role_name_t in role_names:
                role = gr.Tab(label=role_name_t)
                with role:
                    role_tab_clue_dict[role_name_t] = gr.HTML()

        with story_tab:
            story_html = """
            <div style='text-align: center; margin-top: 20px; margin-bottom: 40px; padding: 20px; background: linear-gradient(to right, #f7f7f7, #ffffff); border-left: 5px solid #6c757d; border-right: 5px solid #6c757d;'>
                <p style='font-size: 18px; color: #333; max-width: 600px; margin: auto; line-height: 1.6; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;'>
                    <strong>已解锁的故事：</strong><br>
                    这里展示了您达成剧情解锁条件后从各个角色的视角收集到的故事碎片。每个NPC都有自己独特的背景和视角，揭示了案件中不同的维度和秘密。随着您在游戏中的推进，您将解锁他们的个人记忆和见闻，这些都将成为拼凑整个故事的关键部分。请继续探索和对话，解锁更多的视角，深入了解这个复杂的故事。
                </p>
            </div>

            """
            gr.HTML(story_html)
            story_container = gr.HTML()

        def send_message(msg, uid):
            uid = check_uuid(uid)
            send_player_input(msg, uid=uid)
            send_player_msg(msg, "我", uid=uid)
            return ""


        def send_reset_message(uid):
            uid = check_uuid(uid)
            global glb_history_dict, glb_clue_dict, glb_story_dict
            glb_history_dict[uid] = init_uid_list()
            glb_clue_dict[uid] = init_uid_dict()
            glb_story_dict[uid] = init_uid_dict()
            send_player_input("**Reset**", uid=uid)
            return ""

        def game_ui():
            return gr.update(visible=False), gr.update(visible=True)

        def welcome_ui():
            return gr.update(visible=True), gr.update(visible=False)


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
        new_button.click(game_ui, outputs=[tabs, game_tabs])
        resume_button.click(game_ui, outputs=[tabs, game_tabs])
        return_welcome_button.click(welcome_ui, outputs=[tabs, game_tabs])

        # start game
        new_button.click(send_reset_message, inputs=[uuid]).then(check_for_new_session, inputs=[uuid])
        resume_button.click(check_for_new_session, inputs=[uuid])
        

        # export
        export_button.click(export_chat_history, [uuid], export_output)

        # update chat history
        demo.load(init_game)
        demo.load(get_chat,
                  inputs=[uuid],
                  outputs=[chatbot, chatsys],
                  every=0.5)

        demo.load(get_clue,
                  inputs=[uuid],
                  outputs=[role_tab_clue_dict[i] for i in role_names],
                  every=0.5)
        demo.load(get_story,
                  inputs=[uuid],
                  outputs=[story_container],
                  every=0.5)

    demo.queue()
    demo.launch()
