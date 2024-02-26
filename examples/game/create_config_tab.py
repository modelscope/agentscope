# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

import gradio as gr
import modelscope_studio as mgr

import tempfile
from runtime import RuntimeVer
from config_utils import (
    PLOT_CFG_NAME,
    compress,
    decompress_with_file,
    decompress_with_signature,
    get_user_dir,
    get_signature_dir,
    load_default_cfg,
    load_user_cfg,
    save_user_cfg,
)
from enums import StagePerNight
from generate_image import generate_user_logo_file
from relationship import Familiarity
from utils import check_uuid
from game_builder import GameBuilder


def convert_to_ds(samples):
    return [[str(sample).strip()] for sample in samples if sample] or None


def convert_to_list(samples):
    return [sample[0] for sample in samples if sample[0]] or None


def get_role_by_name(name, uuid, roles=None):
    uuid = check_uuid(uuid)
    roles = roles or load_user_cfg(uuid=uuid)
    for role in roles:
        if role["name"] == name:
            return role
    return None


def get_role_names(uuid, roles=None):
    uuid = check_uuid(uuid)
    roles = roles or load_user_cfg(uuid=uuid)
    names = [role["name"] for role in roles]
    return names


def get_plot_by_id(plot_id, uuid, plots=None):
    uuid = check_uuid(uuid)
    plots = plots or load_user_cfg(cfg_name=PLOT_CFG_NAME, uuid=uuid)
    for plot in plots:
        if plot["plot_id"] == plot_id:
            return plot
    return None


def get_plot_ids(uuid, plots=None):
    uuid = check_uuid(uuid)
    plots = plots or load_user_cfg(cfg_name=PLOT_CFG_NAME, uuid=uuid)
    plot_ids = [plot["plot_id"] for plot in plots]
    return plot_ids


def share_cfg_dir(uuid):
    uuid = check_uuid(uuid)
    try:
        signature, zip_file = compress(uuid=uuid)
        return signature, gr.update(value=zip_file)
    except Exception as e:
        gr.Warning(str(e))
        return "", gr.update(value=None)


def upload_zip_file(zip_file, uuid):
    uuid = check_uuid(uuid)
    try:
        decompress_with_file(zip_file, uuid=uuid)
        gr.Info("✅上传配置成功")
    except Exception as e:
        gr.Warning("上传文件格式不正确， 请输入zip压缩格式。")
    return "", gr.update(value=None)


def load_from_signature(signature, uuid="other_user"):
    uuid = check_uuid(uuid)
    try:
        zip_file = decompress_with_signature(signature, uuid=uuid)
        gr.Info("✅加载签名成功")
    except Exception as e:
        gr.Warning("签名配置不存在或不正确")
    return gr.update(value=None)


def clean_config_dir(uuid):
    uuid = check_uuid(uuid)
    try:
        user_dir = get_user_dir(uuid)
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
            gr.Info(f"✅清理完成：{user_dir}")
    except Exception as e:
        gr.Warning("签名配置不存在或不正确")
    return "", gr.update(value=None)


def check_passwd(passwd):
    if  passwd == os.environ.get("TONGYI_API_KEY", ""):
        gr.Info("密码正确")
        return gr.update(visible=False), gr.update(visible=True)
    else:
        gr.Info("密码错误")
        return gr.update(visible=True), gr.update(visible=False)


def quit_shell_cmd():
    return '', gr.update(visible=True), gr.update(visible=False)


def run_shell_cmd(cmd, msg):
    cmd_args = cmd.split()
    try:
        output = subprocess.run(cmd_args, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return '\n'.join([msg,f'===command===\n{cmd}\n===outputs===', output.stdout])
    except Exception as e:
        gr.Warning("命令不正确，请检查。")
    return msg


def run_shell_file(cmd, msg):
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='w+t') as tfile:
            tfile.write(cmd)
            tfile.flush()
            os.fchmod(tfile.fileno(), 0o755)
            tfile.close()
            output = subprocess.run(
                [tfile.name],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            result = '\n'.join([msg, '===outputs===', output.stdout])
        os.remove(tfile.name)
        return result

    except Exception as e:
        gr.Warning("命令不正确，请检查。")
    return msg


def create_config_accord(ver, uuid):
    uuid = check_uuid(uuid)
    with gr.Row():
        signature = gr.Textbox(
            label="用于分享或加载", placeholder="可加载朋友分享的签名或者点击分享生成签名", show_copy_button=True
        )
        signature_file = gr.File(
            label="用于分享下载", interactive=False, elem_classes=["signature-file-uploader"]
        )
    with gr.Row():
        load_button = gr.Button(
            value="🔏加载签名",
        )
        upload_button = gr.UploadButton(
            label="⬆️上传配置",
        )
        share_button = gr.Button(
            value="🔗分享/⬇️下载",
        )
        clean_button = gr.Button(
            value="🧹清除缓存",
        )

    with gr.Accordion("超级管理员", open=False, visible=(ver==RuntimeVer.Root)):
        passwd_group = gr.Group()
        with passwd_group:
            with gr.Row():
                passwd = gr.Textbox(
                        label="超级管理员密码", placeholder="输入超级管理员密码",type= 'password',
                    )
                passwd_button = gr.Button(
                    value="🔓进入管理"
                )
        execute_group = gr.Group(visible=False)
        with execute_group:
            with gr.Row():
                with gr.Column():
                    execute_cmd = gr.TextArea(
                        label="命令内容",
                        placeholder='请输入你要执行的命令',
                        value="#!/bin/bash\n",
                    )
                    with gr.Row():
                        exectue_button = gr.Button(value="🚀 执行命令")
                        cancel_button = gr.Button(value="↩️退出管理")
                execute_res = gr.Textbox(
                    label="命令输出"
                )

    passwd_button.click(check_passwd, inputs=passwd, outputs=[passwd_group, execute_group])
    exectue_button.click(run_shell_file, inputs=[execute_cmd,execute_res], outputs=execute_res)
    cancel_button.click(quit_shell_cmd, outputs=[passwd, passwd_group, execute_group])
    load_button.click(
        load_from_signature, inputs=[signature, uuid], outputs=[signature_file]
    )
    upload_button.upload(
        upload_zip_file,
        inputs=[upload_button, uuid],
        outputs=[signature, signature_file],
    )
    share_button.click(
        share_cfg_dir, inputs=[uuid], outputs=[signature, signature_file]
    )
    clean_button.click(
        clean_config_dir, inputs=[uuid], outputs=[signature, signature_file]
    )


def create_config_tab(config_tab, ver, uuid):
    tabs = gr.Tabs(visible=True)
    with tabs:
        plot_tab = gr.Tab("剧情配置", id=0)
        role_tab = gr.Tab("角色配置", id=1)
        builder_tab = gr.Tab("编剧助手", id=2)
    with plot_tab:
        plot_selector, on_plot_tab_select = config_plot_tab(plot_tab, uuid=uuid)
    with role_tab:
        role_selector, on_role_tab_select = config_role_tab(role_tab, ver, uuid=uuid)
    with builder_tab:
        config_builder_tab(builder_tab, uuid=uuid)

    config_tab.select(on_role_tab_select, inputs=[uuid], outputs=role_selector)
    config_tab.select(on_plot_tab_select, inputs=[uuid], outputs=plot_selector)


def get_agent_id(uuid):
    return "builder_agent_" + uuid

def init_builder(uuid, state, force=False):
    try:
        agent_id = get_agent_id(uuid)
        if force or agent_id not in state:
            builder_agent = GameBuilder()
            state[agent_id] = builder_agent
    except Exception as e:
        gr.Error("初始化编剧助手失败：${e}")
    return state

def config_builder_tab(builder_tab, uuid):
    import random
    draw_seed = random.randint(0, 1000000000)
    state = gr.State({'session_seed': draw_seed}) 
    with gr.Row():
        with gr.Column():
            start_text = '欢迎使用AI编剧小助手，我可以协助您生成充满惊奇与挑战的文字探险解密故事剧情。' \
                '告诉我一些你脑海中的点子，或者创建全新的故事。'
            builder_chatbot = mgr.Chatbot(
                show_label=False,
                value=[[None, start_text]],
                flushing=False,
                show_copy_button=True,
                )
            builder_chat_input = mgr.MultimodalInput(
                label="输入",
                placeholder="请输入您的消息",
                interactive=True,
                upload_button_props=dict(visible=False),
                submit_button_props=dict(
                    label="发送"))
            with gr.Row():
                builder_clear_btn = gr.Button('重新配置')
                builder_save_btn = gr.Button('发布配置')
            
        with gr.Column():
            builder_plot_config = gr.Json(label="剧情配置预览",value={})
            builder_role_config = gr.Json(label="角色配置预览",value=[])

    def create_send_message(chatbot, input, _state, uuid):
        uuid = check_uuid(uuid)
        agent_id = get_agent_id(uuid)
        builder_agent = _state[agent_id]
        chatbot.append([{'text': input.text, 'files': input.files}, None])
        yield {
            builder_chatbot: chatbot,
            builder_chat_input: None,
        }
        
        answer, plot_config, role_config = builder_agent.build(input.text)
        chatbot[-1][1] = answer
        yield {
            builder_chatbot: chatbot,
            builder_plot_config: plot_config,
            builder_role_config: role_config
        }

    builder_chat_input.submit(
        create_send_message,
        inputs=[builder_chatbot, builder_chat_input, state, uuid],
        outputs=[
            builder_chatbot, builder_chat_input, builder_plot_config, builder_role_config])

    def save_builder_config(uuid, plot_config, role_config):
        uuid = check_uuid(uuid)

        # 
        new_plot = {}

        if not plot_config:
            gr.Error('剧情配置为空')

        plot_id = int(plot_config.get("plot_id", 1))
        max_attempts = int(plot_config.get("max_attempts", 2))
        max_unblock_plots = int(plot_config.get("max_unblock_plots", 1))
        main_roles = plot_config.get("main_roles", [])
        supporting_roles = plot_config.get("supporting_roles", [])
        if isinstance(main_roles, str):
            main_roles = [main_roles]

        new_plot["plot_id"] = plot_id
        new_plot["plot_stages"] = [0,1]
        new_plot["max_attempts"] = max_attempts
        new_plot["main_roles"] = main_roles
        new_plot["supporting_roles"] = supporting_roles
        new_plot["max_unblock_plots"] = max_unblock_plots
        unblock_following_plots = plot_config.get("unblock_following_plots", [[0, 1]])
        unblock_following_plots = [{"unblock_chk_func": "always", "unblock_plot": int(p[1])} for p in unblock_following_plots if p[1]]

        if len(unblock_following_plots) > max_unblock_plots:
            gr.Warning(f"解锁剧情数量超过最大的解锁限制[{max_unblock_plots}]")
            unblock_following_plots = unblock_following_plots[:max_unblock_plots]

        predecessor_plots = plot_config.get("predecessor_plots", [[None]])
        new_plot["unblock_following_plots"] = unblock_following_plots or None
        new_plot["predecessor_plots"] = [int(p[0]) for p in predecessor_plots if p[0]] or None
        
        plot_descriptions = plot_config.get("plot_descriptions", dict()) or dict()
        task_name = plot_config.get("task", '')
        plot_descriptions["task"] = task_name

        plot_descriptions["openings"] = plot_config.get("openings", '')
        plot_descriptions["npc_openings"] = plot_config.get("npc_openings", '')
        plot_descriptions["npc_quit_openings"] = plot_config.get("npc_quit_openings", '')
        plot_descriptions["opening_image"] = plot_config.get("opening_image", '')

        user_openings_option = plot_config.get("user_openings_option", [])
        plot_descriptions["user_openings_option"] = {
            idx: it for idx, it in enumerate(user_openings_option)
        } or None
        plot_descriptions["done_hint"] = plot_config.get("done_hint", '')
        plot_descriptions["done_condition"] = plot_config.get("done_condition", '')
        new_plot["plot_descriptions"] = plot_descriptions

        if not role_config:
            gr.Error('角色配置为空')
        roles = []
        for role in role_config:
            new_role = dict()
            new_role["avatar"] = None
            new_role["avatar_desc"] = role.get('avatar_desc', '')
            new_role["name"] = role.get('name', '角色')
            new_role["relationship"] = role.get('relationship', '陌生')
            new_role["use_memory"] = True
            new_role["model"] = "post_api"
            new_role["clue"] = role.get('clues', []) or None
            character_setting = dict()
            character_setting["food_preference"] = role.get('food_preference', '')
            character_setting["background"] = role.get('background', '')
            character_setting["hidden_plot"] = None
            character_setting["plugin_background"] = None
            new_role["character_setting"] = character_setting
            roles.append(new_role)

        role_names = get_role_names(uuid=uuid, roles=roles)
        plot_role_names = new_plot["main_roles"] + new_plot["supporting_roles"]
        incomplete_role_name = []
        for name in plot_role_names:
            if name not in role_names:
                incomplete_role_name.append(name)
        
        if incomplete_role_name:
            gr.Warning(f'角色配置不完整，请补充{incomplete_role_name}')
            return 

        save_user_cfg([new_plot], cfg_name=PLOT_CFG_NAME, uuid=uuid)
        save_user_cfg(roles, uuid=uuid)
        gr.Info('发布成功，可查看剧情配置页面')
    
    
    def clear_builder(uuid, _state):
        uuid = check_uuid(uuid)
        init_builder(uuid, _state,force=True)
        return {
            builder_chatbot: [[None, start_text]],
            builder_plot_config: {},
            builder_role_config: []
        }

    def on_configure_tab_select(uuid, _state):
        uuid = check_uuid(uuid)
        init_builder(uuid, _state, force=False)

    builder_save_btn.click(save_builder_config, inputs=[uuid, builder_plot_config, builder_role_config])
    builder_clear_btn.click(clear_builder, inputs=[uuid, state], outputs=[builder_chatbot, builder_plot_config, builder_role_config])
    builder_tab.select(on_configure_tab_select, inputs=[uuid, state])

def config_plot_tab(plot_tab, uuid):
    cfg_name = PLOT_CFG_NAME
    plot_stage_choices = StagePerNight.to_list()
    with gr.Row():
        plot_selector = gr.Dropdown(label="选择剧情id查看或者编辑剧情")
        create_plot_button = gr.Button("🆕创建剧情")
        del_plot_button = gr.Button("🧹删除剧情")
        save_plot_button = gr.Button("🛄保存剧情")
        restore_plot_button = gr.Button("🔄恢复默认")
    with gr.Row():
        plot_id = gr.Textbox(label="剧情id")
        plot_stages = gr.Dropdown(
            label="剧情环节选择",
            value=0,
            multiselect=True,
            type="index",
            choices=plot_stage_choices,
            allow_custom_value=True,
        )
        task_name = gr.Textbox(label="剧情任务")
        max_attempts = gr.Textbox(scale=1, label="尝试次数")

    with gr.Row():
        predecessor_plots = gr.Dataframe(
            label="配置前置剧情",
            show_label=True,
            datatype=["str"],
            headers=["前置剧情id"],
            type="array",
            wrap=True,
            col_count=(1, "fixed"),
        )
        main_roles = gr.Dataframe(
            label="配置主角",
            show_label=True,
            datatype=["str"],
            headers=["主角名字"],
            type="array",
            wrap=True,
            col_count=(1, "fixed"),
        )
        supporting_roles = gr.Dataframe(
            label="配置配角",
            show_label=True,
            datatype=["str"],
            headers=["配角名字"],
            type="array",
            wrap=True,
            col_count=(1, "fixed"),
        )

    with gr.Row():
        max_unblock_plots = gr.Textbox(scale=1, label="最多解锁剧情数")
        unblock_following_plots = gr.Dataframe(
            scale=2,
            label="设置解锁剧情",
            show_label=True,
            datatype=["str", "str"],
            headers=["解锁方式", "解锁剧情ID"],
            type="array",
            wrap=True,
            col_count=(2, "fixed"),
        )
    with gr.Row():
        with gr.Column():
            done_hint = gr.Textbox(label="剧情完成的提示词")
        with gr.Column():
            done_condition = gr.Textbox(label="剧情完成条件")

    with gr.Row():
        with gr.Column():
            openings = gr.Textbox(label="系统开场白")
            opening_image = gr.Textbox(label="NPC进场配图描述")
        with gr.Column():
            npc_openings = gr.Textbox(label="NPC进场台词")
            npc_quit_openings = gr.Textbox(label="NPC退场台词")

    with gr.Row():
        user_openings_option = gr.Dataframe(
            label="用户开场白选项",
            show_label=True,
            datatype=["str", "str"],
            headers=["编号", "用户选择项"],
            type="array",
            wrap=True,
            col_count=(2, "fixed"),
        )

    plot_config_options = [
        plot_id,
        plot_stages,
        task_name,
        max_attempts,
        predecessor_plots,
        main_roles,
        supporting_roles,
        max_unblock_plots,
        unblock_following_plots,
        openings,
        npc_openings,
        npc_quit_openings,
        opening_image,
        user_openings_option,
        done_hint,
        done_condition,
    ]

    def on_plot_tab_select(uuid):
        uuid = check_uuid(uuid)
        plot_ids = get_plot_ids(uuid=uuid)
        if len(plot_ids) < 1:
            gr.Warning("配置中没有发现剧情，可以点击恢复默认")
            return gr.Dropdown()
        return gr.Dropdown(value=plot_ids[0], choices=plot_ids)

    def configure_plot(id, uuid):
        uuid = check_uuid(uuid)
        plot = get_plot_by_id(plot_id=id, uuid=uuid)
        attempts = plot.get("max_attempts", 2)

        cfg_main_roles = plot.get("main_roles", []) or []
        cfg_main_roles = convert_to_ds(cfg_main_roles)

        cfg_supporting_roles = plot.get("supporting_roles", []) or []
        cfg_supporting_roles = convert_to_ds(cfg_supporting_roles)

        cfg_predecessor_plots = plot.get("predecessor_plots", []) or []
        cfg_predecessor_plots = convert_to_ds(cfg_predecessor_plots)
        cfg_max_unblock_plots = plot.get("max_unblock_plots", 1)

        cfg_unblock_following_plots = plot.get("unblock_following_plots", dict()) or dict()
        cfg_unblock_following_plots = [[p["unblock_chk_func"], str(p["unblock_plot"])] for p in cfg_unblock_following_plots if p] or None

        plot_descriptions = plot.get("plot_descriptions", dict()) or dict()

        cfg_user_openings_option = plot_descriptions.get("user_openings_option", dict()) or dict()
        cfg_user_openings_option = [[k, v.strip()] for k, v in cfg_user_openings_option.items()] or None

        cfg_plot_stages = plot.get("plot_stages", []) or []
        cfg_plot_stages = [plot_stage_choices[stage] for stage in cfg_plot_stages] or None
        return {
            plot_id: plot["plot_id"],
            plot_stages: gr.Dropdown(value=cfg_plot_stages),
            task_name: plot["plot_descriptions"]["task"].strip(),
            max_attempts: attempts,
            predecessor_plots: cfg_predecessor_plots,
            main_roles: cfg_main_roles,
            supporting_roles: cfg_supporting_roles,
            max_unblock_plots: cfg_max_unblock_plots,
            unblock_following_plots: cfg_unblock_following_plots,
            openings: plot_descriptions.get("openings", "").strip(),
            npc_openings: plot_descriptions.get("npc_openings", "").strip(),
            npc_quit_openings: plot_descriptions.get("npc_quit_openings", "").strip(),
            opening_image: plot_descriptions.get("opening_image", "").strip(),
            user_openings_option: cfg_user_openings_option,
            done_hint: plot_descriptions.get("done_hint", "").strip(),
            done_condition: plot_descriptions.get("done_condition", "").strip(),
        }

    def create_plot():
        return {
            plot_id: "",
            plot_stages: gr.Dropdown(value=plot_stage_choices[0]),
            task_name: "",
            max_attempts: 2,
            predecessor_plots: None,
            main_roles: None,
            supporting_roles: None,
            max_unblock_plots: 1,
            unblock_following_plots: None,
            openings: "",
            npc_openings: "",
            npc_quit_openings: "",
            opening_image: "",
            user_openings_option: None,
            done_hint: "",
            done_condition: "",
        }

    def delete_plot(plot_id, uuid):
        uuid = check_uuid(uuid)
        plots = load_user_cfg(cfg_name=cfg_name, uuid=uuid)
        plot_id = int(plot_id)
        del_plot = get_plot_by_id(plot_id=plot_id, uuid=uuid, plots=plots)

        if del_plot in plots and len(plots) >= 2:
            plots.pop(plots.index(del_plot))
        elif not del_plot:
            gr.Warning("没有找到的剧情id")
        else:
            gr.Warning("最少需要保留一个剧情。")
        save_user_cfg(plots, cfg_name=cfg_name, uuid=uuid)
        plot_ids = get_plot_ids(uuid=uuid)
        return gr.Dropdown(value=plot_ids[0], choices=plot_ids)

    def save_plot(
        plot_id,
        plot_stages,
        task_name,
        max_attempts,
        predecessor_plots,
        main_roles,
        supporting_roles,
        max_unblock_plots,
        unblock_following_plots,
        openings,
        npc_openings,
        npc_quit_openings,
        opening_image,
        user_openings_option,
        done_hint,
        done_condition,
        uuid,
    ):
        uuid = check_uuid(uuid)
        plot_id = int(plot_id)
        max_attempts = int(max_attempts)
        max_unblock_plots = int(max_unblock_plots)
        if plot_id == "":
            gr.Warning("必须给一个新剧情设置一个id")
            return gr.Dropdown()

        plots = load_user_cfg(cfg_name=cfg_name, uuid=uuid)
        new_plot = get_plot_by_id(plot_id=plot_id, uuid=uuid, plots=plots) or dict()

        if new_plot not in plots:
            plots.append(new_plot)

        new_plot["plot_id"] = plot_id
        new_plot["plot_stages"] = sorted(plot_stages) if plot_stages else None
        new_plot["max_attempts"] = max_attempts
        new_plot["main_roles"] = convert_to_list(main_roles)
        new_plot["supporting_roles"] = convert_to_list(supporting_roles)
        new_plot["max_unblock_plots"] = max_unblock_plots
        unblock_following_plots = [{"unblock_chk_func": "always", "unblock_plot": int(p[1])} for p in unblock_following_plots if p[1]]

        if len(unblock_following_plots) > max_unblock_plots:
            gr.Warning(f"解锁剧情数量超过最大的解锁限制[{max_unblock_plots}]")
            unblock_following_plots = unblock_following_plots[:max_unblock_plots]
        new_plot["unblock_following_plots"] = unblock_following_plots or None
        new_plot["predecessor_plots"] = [int(p[0]) for p in predecessor_plots if p[0]] or None

        plot_descriptions = new_plot.get("plot_descriptions", dict()) or dict()
        plot_descriptions["task"] = task_name

        plot_descriptions["openings"] = openings
        plot_descriptions["npc_openings"] = npc_openings
        plot_descriptions["npc_quit_openings"] = npc_quit_openings
        plot_descriptions["opening_image"] = opening_image
        plot_descriptions["user_openings_option"] = {
            it[0]: it[1] for it in user_openings_option if all(it)
        } or None
        plot_descriptions["done_hint"] = done_hint
        plot_descriptions["done_condition"] = done_condition
        new_plot["plot_descriptions"] = plot_descriptions
        save_user_cfg(plots, cfg_name=cfg_name, uuid=uuid)
        plot_ids = get_plot_ids(uuid=uuid, plots=plots)
        return gr.Dropdown(value=plot_id, choices=plot_ids)

    def restore_default_cfg(uuid):
        uuid = check_uuid(uuid)
        plots = load_default_cfg(cfg_name=cfg_name, uuid=uuid)
        plot_ids = get_plot_ids(uuid=uuid, plots=plots)
        return gr.Dropdown(value=plot_ids[0], choices=plot_ids)

    plot_selector.change(
        configure_plot, inputs=[plot_selector, uuid], outputs=plot_config_options
    )

    restore_plot_button.click(
        restore_default_cfg, inputs=[uuid], outputs=plot_selector
    ).then(configure_plot, inputs=[plot_selector, uuid], outputs=plot_config_options)

    del_plot_button.click(delete_plot, inputs=[plot_id, uuid], outputs=[plot_selector])

    save_plot_button.click(
        save_plot, inputs=plot_config_options + [uuid], outputs=plot_selector
    )

    create_plot_button.click(create_plot, outputs=plot_config_options)
    plot_tab.select(on_plot_tab_select, inputs=[uuid], outputs=plot_selector).then(configure_plot, inputs=[plot_selector, uuid], outputs=plot_config_options
    )
    return plot_selector, on_plot_tab_select


def config_role_tab(role_tab, ver, uuid):
    relationship_list = Familiarity.to_list()
    with gr.Row():
        role_selector = gr.Dropdown(label="选择角色查看或者编辑")
        create_role_button = gr.Button("🆕创建角色")
        del_role_button = gr.Button("🧹删除角色")
        save_role_button = gr.Button("🛄保存角色")
        restore_role_button = gr.Button("🔄恢复默认")
    with gr.Row():
        avatar_file = gr.Image(
            label="头像",
            sources=["upload"],
            interactive=True,
            type="filepath",
            scale=1,
            width=200,
            height=200,
        )

        with gr.Column(scale=2):
            avatar_desc = gr.Textbox(
                label="头像描述",
                placeholder="请用一句话描述角色头像，若不输入则使用人物背景描述生成",
            )
            gen_avatar_button = gr.Button(value="生成头像")
        with gr.Column(scale=2):
            with gr.Column():
                role_name = gr.Textbox(
                    label="角色名称",
                    placeholder="请输入角色名称",
                )
                relationship = gr.Dropdown(label="初始熟悉程度", choices=relationship_list)
            with gr.Row(visible=(ver in [RuntimeVer.Root])):
                use_memory = gr.Checkbox(label="记忆功能", info="是否开启角色记忆功能")
                model_name = gr.Textbox(label="模型设置")

    with gr.Accordion(label="角色特征", open=True):
        food_preference = gr.Textbox(label="食物偏好", placeholder="请输入喜欢的食物")
        background = gr.Textbox(label="背景介绍", placeholder="请输入角色背景")

        plot_clues = gr.Dataframe(
            label="线索卡",
            show_label=True,
            datatype=["str", "str", "str"],
            column_widths=["10%", "10%", "80%"],
            headers=["剧情ID", "线索名", "线索详情"],
            type="array",
            wrap=True,
            col_count=(3, "fixed"),
        )

    def configure_role(name, uuid):
        uuid = check_uuid(uuid)
        role = get_role_by_name(name=name, uuid=uuid)

        character_setting = role["character_setting"]
        clues = role.get("clue", []) or []
        clues = [[str(clue["plot"]), clue["name"], clue["content"].strip()]for clue in clues] or None

        return {
            avatar_file: gr.Image(value=role["avatar"], interactive=True),
            role_name: role["name"],
            relationship: gr.Dropdown(value=role.get("relationship", "陌生")),
            avatar_desc: role.get("avatar_desc", ""),
            use_memory: gr.Checkbox(value=role["use_memory"]),
            model_name: role["model"],
            food_preference: character_setting["food_preference"].strip(),
            background: character_setting["background"].strip(),
            plot_clues: clues,
        }

    role_config_options = [
        avatar_file,
        role_name,
        relationship,
        avatar_desc,
        use_memory,
        model_name,
        food_preference,
        background,
        plot_clues,
    ]

    def on_role_tab_select(uuid):
        uuid = check_uuid(uuid)
        role_names = get_role_names(uuid=uuid)
        if len(role_names) < 1:
            gr.Warning("配置中没有发现角色，可以点击恢复默认")
            return gr.Dropdown()
        return gr.Dropdown(value=role_names[0], choices=role_names)

    def create_role():
        return {
            avatar_file: gr.Image(value=None),
            role_name: "",
            relationship: gr.Dropdown(value="陌生"),
            avatar_desc: "",
            use_memory: gr.Checkbox(label="是否开启记忆功能"),
            model_name: "",
            food_preference: "",
            background: "",
            plot_clues: None,
        }

    def delete_role(name, uuid):
        uuid = check_uuid(uuid)
        roles = load_user_cfg(uuid=uuid)
        del_role = get_role_by_name(name=name, uuid=uuid, roles=roles)

        if del_role in roles and len(roles) >= 2:
            roles.pop(roles.index(del_role))
        elif not del_role:
            gr.Warning("没有找到角色")
        else:
            gr.Warning("最少需要保留一名角色。")
        save_user_cfg(roles, uuid=uuid)
        role_names = [role["name"] for role in roles]
        return gr.Dropdown(value=role_names[0], choices=role_names)

    def save_role(
        avatar_file,
        name,
        relationship,
        avatar_desc,
        use_memory,
        model_name,
        food_preference,
        background,
        clues,
        uuid,
    ):
        uuid = check_uuid(uuid)
        roles = load_user_cfg(uuid=uuid)
        if name == "":
            gr.Warning("必须给新角色起一个名字")
            return gr.Dropdown()

        new_role = get_role_by_name(name=name, uuid=uuid, roles=roles) or dict()

        if new_role not in roles:
            roles.append(new_role)

        new_role["avatar"] = avatar_file
        new_role["avatar_desc"] = avatar_desc
        new_role["name"] = name
        new_role["relationship"] = relationship
        new_role["use_memory"] = use_memory
        new_role["model"] = model_name
        new_role["clue"] = [
            {"plot": int(clue[0]), "name": clue[1], "content": clue[2]}
            for clue in clues
            if all(clue)
        ] or None
        character_setting = new_role.get("character_setting", dict())
        character_setting["food_preference"] = food_preference
        character_setting["background"] = background
        new_role["character_setting"] = character_setting
        save_user_cfg(roles, uuid=uuid)
        role_names = [role["name"] for role in roles]
        if name not in role_names:
            name = role_names[0]
        return gr.Dropdown(value=name, choices=role_names)

    def restore_default_cfg(uuid):
        uuid = check_uuid(uuid)
        roles = load_default_cfg(uuid=uuid)
        role_names = get_role_names(uuid=uuid, roles=roles)
        return gr.Dropdown(value=role_names[0], choices=role_names)

    def genarate_avatar_file(desc, name, uuid):
        uuid = check_uuid(uuid)
        if desc == "":
            role = get_role_by_name(name=name, uuid=uuid)
            if role:
                desc = role["character_setting"]["background"]
        gen_avatar_file = generate_user_logo_file(desc, name, uuid)
        if not gen_avatar_file:
            gr.Warning("生成头像失败")
            gen_avatar_file = role["avatar"]
        return gr.Image(value=gen_avatar_file)

    role_selector.change(
        configure_role, inputs=[role_selector, uuid], outputs=role_config_options
    )

    gen_avatar_button.click(
        genarate_avatar_file, inputs=[avatar_desc, role_name, uuid], outputs=avatar_file
    )

    restore_role_button.click(
        restore_default_cfg, inputs=[uuid], outputs=role_selector
    ).then(configure_role, inputs=[role_selector, uuid], outputs=role_config_options)

    del_role_button.click(
        delete_role, inputs=[role_name, uuid], outputs=[role_selector]
    )

    save_role_button.click(
        save_role, inputs=role_config_options + [uuid], outputs=role_selector
    )

    create_role_button.click(create_role, outputs=role_config_options)
    role_tab.select(on_role_tab_select, inputs=[uuid], outputs=role_selector).then(configure_role, inputs=[role_selector, uuid], outputs=role_config_options)
    return role_selector, on_role_tab_select
