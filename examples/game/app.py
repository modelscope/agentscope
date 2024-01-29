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
from config_uitls import load_user_cfg, save_user_cfg, load_default_cfg, load_configs
from utils import (
    CheckpointArgs,
    enable_web_ui,
    send_player_msg,
    send_player_input,
    get_chat_msg,
    SYS_MSG_PREFIX,
    ResetException,
)
from generate_image import generate_user_logo_file

import gradio as gr
import modelscope_gradio_components as mgr

enable_web_ui()

role_hint_dict = {
    "王先生": {"current_hint": ["我丢了招财猫", "那天阿炳带着黑色的袋子"],
               "current_state_hint_num": 3,
            "total_hint_num": 10},
    "老许": {"current_hint": ["xxx", "yyy", "zzz"], "current_state_hint_num": 4,
            "total_hint_num": 11}
}


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
            hint_menu = gr.Accordion(label="角色线索",
                                     open=False,
                                     visible=False)
            with hint_menu:
                with gr.Column():
                    for name in role_hint_dict.keys():
                        label = (name + " "
                        + str(len(role_hint_dict[name]['current_hint']))
                        + '/'
                        + str(role_hint_dict[name]['current_state_hint_num'])
                        + '/'
                        + str(role_hint_dict[name]['total_hint_num']))
                        role = gr.Accordion(
                            label=label,
                            open=False)

                        with role:
                            text = '\n'.join(role_hint_dict[name][
                                                 'current_hint'])
                            gr.TextArea(
                                lines=len(role_hint_dict[name]['current_hint']),
                                label="已知线索",
                                placeholder=text,
                               )


        with config_tab:
            with gr.Row():
                role_selector = gr.Dropdown(label='选择角色查看或者编辑')
                create_role_button = gr.Button('🆕创建角色')
                del_role_button = gr.Button('🧹删除角色')
                save_role_button = gr.Button('🛄保存角色')
                restore_role_button = gr.Button('🔄恢复默认')
            with gr.Row():
                avatar_file = gr.Image(
                    label='头像',
                    sources=['upload'],
                    interactive=True,
                    type='filepath',
                    scale=1,
                    width=200,
                    height=200,
                )
                
                with gr.Column(scale=2):
                    avatar_desc = gr.Textbox(label='头像描述',
                                        placeholder='请用一句话描述角色头像，若不输入则使用人物背景描述生成',
                                        )   
                    gen_avatar_button = gr.Button(value='生成头像')
                with gr.Column(scale=2):
                    role_name = gr.Textbox(label='角色名称',
                                        placeholder='请输入角色名称',
                                        )
                    with gr.Row():
                        use_memory = gr.Checkbox(label='记忆功能',
                                                info='是否开启角色记忆功能')
                        model_name = gr.Textbox(label='模型设置')

            with gr.Accordion(label='角色特征', open=True):
                food_preference = gr.Textbox(label='食物偏好',
                                             placeholder='请输入喜欢的食物')
                background = gr.Textbox(label='背景介绍', placeholder='请输入角色背景')
                hidden_plot = gr.Dataframe(label='隐藏剧情设置',
                                           show_label=True,
                                           datatype=['str', 'str'],
                                           headers=['id', '剧情描述'],
                                           type='array',
                                           wrap=True,
                                           col_count=(2, 'fixed'),
                                           )
                plugin_background = gr.Dataframe(label='角色插件隐藏背景设置',
                                                 show_label=True,
                                                 datatype=['str'],
                                                 headers=['角色背景'],
                                                 type='array',
                                                 wrap=True,
                                                 col_count=(1, 'fixed'),
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
                chatbot: mgr.Chatbot(visible=visible),
                chatsys: mgr.Chatbot(visible=visible),
                user_chat_input: gr.Text(visible=visible),
                send_button: gr.Button(visible=visible),
                new_button: gr.Button(visible=invisible),
                resume_button: gr.Button(visible=invisible),
                return_welcome_button: gr.Button(visible=visible),
                export: gr.Accordion(visible=visible),
                user_chat_bot_cover: gr.HTML(visible=invisible),
                hint_menu: gr.Accordion(visible=visible)
            }

        def welcome_ui():
            visible = True
            invisible = False
            return {
                tabs: gr.Tabs(visible=visible),
                chatbot: mgr.Chatbot(visible=invisible),
                chatsys: mgr.Chatbot(visible=invisible),
                user_chat_input: gr.Text(visible=invisible),
                send_button: gr.Button(visible=invisible),
                new_button: gr.Button(visible=visible),
                resume_button: gr.Button(visible=visible),
                return_welcome_button: gr.Button(visible=invisible),
                export: gr.Accordion(visible=invisible),
                user_chat_bot_cover: gr.HTML(visible=visible),
                hint_menu: gr.Accordion(visible=invisible)
            }

        def configure_role(name, uid):
            uid = check_uuid(uid)
            roles = load_user_cfg(uid)
            role = None
            for r in roles:
                if r['name'] == name:
                    role = r

            character_setting = role['character_setting']

            hidden_plots = [
                [k, v] for k, v in character_setting['hidden_plot'].items()
            ]
            plugin_backgrounds = [
                [str] for str in character_setting['plugin_background']
            ]
            if role:
                return {
                    avatar_file: gr.Image(value=role['avatar'],
                                          interactive=True),
                    role_name: role['name'],
                    avatar_desc: role.get('avatar_desc', ''),
                    use_memory: gr.Checkbox(value=role['use_memory']),
                    model_name: role['model'],
                    food_preference: character_setting['food_preference'],
                    background: character_setting['background'],
                    hidden_plot: hidden_plots,
                    plugin_background: plugin_backgrounds,
                }
            else:
                return {
                    avatar_file: gr.Image(value=None, interactive=True),
                    role_name: '',
                    avatar_desc: '',
                    use_memory: gr.Checkbox(label='是否开启记忆功能'),
                    model_name: '',
                    food_preference: '',
                    background: '',
                    hidden_plot: None,
                    plugin_background: None
                }

        role_config_options = [
            avatar_file, role_name, avatar_desc, use_memory, model_name, food_preference,
            background, hidden_plot, plugin_background
        ]
        role_selector.change(configure_role,
                             inputs=[role_selector, uuid],
                             outputs=role_config_options)

        def on_config_tab_select(uid):
            uid = check_uuid(uid)
            roles = load_user_cfg(uid)
            role_names = [role['name'] for role in roles]
            if len(role_names) < 1:
                gr.Warning('配置中没有发现角色，可以点击恢复默认')
                return gr.Dropdown()
            return gr.Dropdown(value=role_names[0], choices=role_names)

        def create_role():
            return {
                avatar_file:
                gr.Image(value=None),
                role_name: '',
                avatar_desc: '',
                avatar_desc: '',
                use_memory: gr.Checkbox(label='是否开启记忆功能'),
                model_name: '',
                food_preference: '',
                background: '',
                hidden_plot: None,
                plugin_background: None
            }

        def delete_role(role_name, uid):
            uid = check_uuid(uid)
            roles = load_user_cfg(uid)
            del_role = None

            for role in roles:
                if role['name'] == role_name:
                    del_role = role
                    break

            if del_role in roles and len(roles) >= 2:
                roles.pop(roles.index(del_role))
            else:
                gr.Warning('最少需要保留一名角色。')
            save_user_cfg(roles, uid)
            role_names = [role['name'] for role in roles]
            return gr.Dropdown(value=role_names[0], choices=role_names)

        def save_role(avatar_file, role_name, avatar_desc, use_memory, model_name,
                      food_preference, background, hidden_plot,
                      plugin_background, uid):
            uid = check_uuid(uid)
            roles = load_user_cfg(uid)
            if role_name == '':
                gr.Warning('必须给一个新角色起一个名字')
                role_names = [role['name'] for role in roles]
                return gr.Dropdown(value=role_names[0], choices=role_names)

            new_role = dict()

            for role in roles:
                if role['name'] == role_name:
                    new_role = role
                    break
            if new_role in roles:
                roles.pop(roles.index(new_role))
            new_role = dict()
            new_role['avatar'] = avatar_file
            new_role['avatar_desc'] = avatar_desc
            new_role['name'] = role_name
            new_role['use_memory'] = use_memory
            new_role['model'] = model_name
            character_setting = new_role.get('character_setting', dict())
            character_setting['food_preference'] = food_preference
            character_setting['background'] = background
            character_setting['hidden_plot'] = {
                it[0]: it[1]
                for it in hidden_plot
            }
            character_setting['plugin_background'] = [
                it[0] for it in plugin_background
            ]
            new_role['character_setting'] = character_setting
            roles.append(new_role)
            save_user_cfg(roles, uid)
            role_names = [role['name'] for role in roles]
            return gr.Dropdown(value=role_name, choices=role_names)

        def restore_default_cfg(uid):
            uid = check_uuid(uid)
            roles = load_default_cfg(uid)
            role_names = [role['name'] for role in roles]
            return gr.Dropdown(value=role_names[0], choices=role_names)
        
        def genarate_avatar_file(desc, role_name, uid):
            uid = check_uuid(uid)
            if desc == '':
                role = get_role_by_name(role_name, uid)
                if role:
                    desc = role['character_setting']['background']
            gen_avatar_file = generate_user_logo_file(desc, role_name, uid)
            return gr.Image(value=gen_avatar_file)

        gen_avatar_button.click(genarate_avatar_file, inputs=[avatar_desc, role_name, uuid], outputs=avatar_file)

        restore_role_button.click(restore_default_cfg,
                                  inputs=[uuid],
                                  outputs=role_selector)
        del_role_button.click(delete_role,
                              inputs=[role_name, uuid],
                              outputs=[role_selector
                                       ])  #+ role_config_options )
        save_role_button.click(save_role,
                               inputs=role_config_options + [uuid],
                               outputs=role_selector)
        create_role_button.click(create_role, outputs=role_config_options)
        config_tab.select(on_config_tab_select,
                          inputs=[uuid],
                          outputs=role_selector)

        outputs = [
            tabs,
            chatbot,
            chatsys,
            user_chat_input,
            send_button,
            new_button,
            resume_button,
            return_welcome_button,
            export,
            user_chat_bot_cover,
            hint_menu
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
        new_button.click(send_reset_message, inputs=[uuid])
        resume_button.click(check_for_new_session, inputs=[uuid])

        # export
        export_button.click(export_chat_history, [uuid], export_output)

        # update chat history
        demo.load(init_game)
        demo.load(check_for_new_session, inputs=[uuid], every=0.1)

        demo.load(get_dial_chat,
                  inputs=[uuid],
                  outputs=chatbot,
                  every=0.5)
        demo.load(get_sys_chat,
                  inputs=[uuid],
                  outputs=chatsys,
                  every=0.5,)

    demo.queue()
    demo.launch()
