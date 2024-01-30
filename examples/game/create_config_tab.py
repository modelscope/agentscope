# -*- coding: utf-8 -*-

import gradio as gr

from config_utils import load_default_cfg, load_user_cfg, save_user_cfg
from generate_image import generate_user_logo_file


def get_role_by_name(name, uuid):
    roles = load_default_cfg(uuid)
    for role in roles:
        if role["name"] == name:
            return role
    return None


def create_config_tab(config_tab, uuid):
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
            role_name = gr.Textbox(
                label="角色名称",
                placeholder="请输入角色名称",
            )
            with gr.Row():
                use_memory = gr.Checkbox(label="记忆功能", info="是否开启角色记忆功能")
                model_name = gr.Textbox(label="模型设置")

    with gr.Accordion(label="角色特征", open=True):
        food_preference = gr.Textbox(label="食物偏好", placeholder="请输入喜欢的食物")
        background = gr.Textbox(label="背景介绍", placeholder="请输入角色背景")
        hidden_plot = gr.Dataframe(
            label="隐藏剧情设置",
            show_label=True,
            datatype=["str", "str"],
            headers=["id", "剧情描述"],
            type="array",
            wrap=True,
            col_count=(2, "fixed"),
        )
        plugin_background = gr.Dataframe(
            label="角色插件隐藏背景设置",
            show_label=True,
            datatype=["str"],
            headers=["角色背景"],
            type="array",
            wrap=True,
            col_count=(1, "fixed"),
        )

    def configure_role(name, uuid):
        roles = load_user_cfg(uuid)
        role = None
        for r in roles:
            if r["name"] == name:
                role = r

        character_setting = role["character_setting"]

        hidden_plots = [[k, v] for k, v in character_setting["hidden_plot"].items()]
        plugin_backgrounds = [[str] for str in character_setting["plugin_background"]]
        if role:
            return {
                avatar_file: gr.Image(value=role["avatar"], interactive=True),
                role_name: role["name"],
                avatar_desc: role.get("avatar_desc", ""),
                use_memory: gr.Checkbox(value=role["use_memory"]),
                model_name: role["model"],
                food_preference: character_setting["food_preference"],
                background: character_setting["background"],
                hidden_plot: hidden_plots,
                plugin_background: plugin_backgrounds,
            }
        else:
            return {
                avatar_file: gr.Image(value=None, interactive=True),
                role_name: "",
                avatar_desc: "",
                use_memory: gr.Checkbox(label="是否开启记忆功能"),
                model_name: "",
                food_preference: "",
                background: "",
                hidden_plot: None,
                plugin_background: None,
            }

    role_config_options = [
        avatar_file,
        role_name,
        avatar_desc,
        use_memory,
        model_name,
        food_preference,
        background,
        hidden_plot,
        plugin_background,
    ]
    role_selector.change(
        configure_role, inputs=[role_selector, uuid], outputs=role_config_options
    )

    def on_config_tab_select(uuid):
        roles = load_user_cfg(uuid)
        role_names = [role["name"] for role in roles]
        if len(role_names) < 1:
            gr.Warning("配置中没有发现角色，可以点击恢复默认")
            return gr.Dropdown()
        return gr.Dropdown(value=role_names[0], choices=role_names)

    def create_role():
        return {
            avatar_file: gr.Image(value=None),
            role_name: "",
            avatar_desc: "",
            avatar_desc: "",
            use_memory: gr.Checkbox(label="是否开启记忆功能"),
            model_name: "",
            food_preference: "",
            background: "",
            hidden_plot: None,
            plugin_background: None,
        }

    def delete_role(role_name, uuid):
        roles = load_user_cfg(uuid)
        del_role = None

        for role in roles:
            if role["name"] == role_name:
                del_role = role
                break

        if del_role in roles and len(roles) >= 2:
            roles.pop(roles.index(del_role))
        else:
            gr.Warning("最少需要保留一名角色。")
        save_user_cfg(roles, uuid)
        role_names = [role["name"] for role in roles]
        return gr.Dropdown(value=role_names[0], choices=role_names)

    def save_role(
        avatar_file,
        role_name,
        avatar_desc,
        use_memory,
        model_name,
        food_preference,
        background,
        hidden_plot,
        plugin_background,
        uuid,
    ):
        roles = load_user_cfg(uuid)
        if role_name == "":
            gr.Warning("必须给一个新角色起一个名字")
            role_names = [role["name"] for role in roles]
            return gr.Dropdown(value=role_names[0], choices=role_names)

        new_role = dict()

        for role in roles:
            if role["name"] == role_name:
                new_role = role
                break
        if new_role not in roles:
            roles.append(new_role)

        new_role["avatar"] = avatar_file
        new_role["avatar_desc"] = avatar_desc
        new_role["name"] = role_name
        new_role["use_memory"] = use_memory
        new_role["model"] = model_name
        character_setting = new_role.get("character_setting", dict())
        character_setting["food_preference"] = food_preference
        character_setting["background"] = background
        character_setting["hidden_plot"] = {it[0]: it[1] for it in hidden_plot}
        character_setting["plugin_background"] = [it[0] for it in plugin_background]
        new_role["character_setting"] = character_setting
        save_user_cfg(roles, uuid)
        role_names = [role["name"] for role in roles]
        return gr.Dropdown(value=role_name, choices=role_names)

    def restore_default_cfg(uuid):
        roles = load_default_cfg(uuid)
        role_names = [role["name"] for role in roles]
        return gr.Dropdown(value=role_names[0], choices=role_names)

    def genarate_avatar_file(desc, role_name, uuid):
        if desc == "":
            role = get_role_by_name(role_name, uuid)
            if role:
                desc = role["character_setting"]["background"]
        gen_avatar_file = generate_user_logo_file(desc, role_name, uuid)
        return gr.Image(value=gen_avatar_file)

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
    config_tab.select(on_config_tab_select, inputs=[uuid], outputs=role_selector)
