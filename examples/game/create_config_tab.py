# -*- coding: utf-8 -*-

import gradio as gr

from config_utils import (PLOT_CFG_NAME, load_default_cfg, load_user_cfg,
                          save_user_cfg)
from generate_image import generate_user_logo_file
from utils import check_uuid


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
        if plot["plot_id"] == int(plot_id):
            return plot
    return None


def get_plot_ids(uuid, plots=None):
    uuid = check_uuid(uuid)
    plots = plots or load_user_cfg(cfg_name=PLOT_CFG_NAME, uuid=uuid)
    plot_ids = [plot["plot_id"] for plot in plots]
    return plot_ids


def create_config_tab(config_tab, uuid):
    uuid = check_uuid(uuid)
    tabs = gr.Tabs(visible=True)
    with tabs:
        plot_tab = gr.Tab("剧情配置", id=0)
        role_tab = gr.Tab("角色配置", id=1)
    with plot_tab:
        plot_selector, on_plot_tab_select = config_plot_tab(plot_tab, uuid=uuid)
    with role_tab:
        role_selector, on_role_tab_select = config_role_tab(role_tab, uuid=uuid)

    config_tab.select(on_role_tab_select, inputs=[uuid], outputs=role_selector)
    config_tab.select(on_plot_tab_select, inputs=[uuid], outputs=plot_selector)


def config_plot_tab(plot_tab, uuid):
    cfg_name = PLOT_CFG_NAME
    uuid = check_uuid(uuid)
    with gr.Row():
        plot_selector = gr.Dropdown(label="选择剧情id查看或者编辑剧情")
        create_plot_button = gr.Button("🆕创建剧情")
        del_plot_button = gr.Button("🧹删除剧情")
        save_plot_button = gr.Button("🛄保存剧情")
        restore_plot_button = gr.Button("🔄恢复默认")
    with gr.Row():
        plot_id = gr.Textbox(label="剧情id")
        task_name = gr.Textbox(label="剧情任务")
        max_attempts = gr.Textbox(scale=1, label="尝试次数")

    with gr.Row():
        predecessor_plots = gr.Dataframe(
            label="配置前置剧情",
            show_label=True,
            datatype=["number"],
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
            headers=["解锁方式", "解锁剧情"],
            type="array",
            wrap=True,
            col_count=(2, "fixed"),
        )
    with gr.Row():
        openings = gr.Textbox(label="系统开场白")
        npc_openings = gr.Textbox(label="NPC进场台词")
        npc_quit_openings = gr.Textbox(label="NPC退场台词")
    with gr.Row():
        user_openings_option = gr.Dataframe(
            label="用户开场白选项",
            show_label=True,
            datatype=["str", "str"],
            headers=["用户选择项"],
            type="array",
            wrap=True,
            col_count=(1, "fixed"),
            row_count=(3, "fixed"),
        )

    plot_config_options = [
        plot_id,
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
        user_openings_option,
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
        return {
            plot_id: plot["plot_id"],
            task_name: plot["plot_descriptions"]["task"].strip("\n"),
            max_attempts: attempts,
            predecessor_plots: None,
            main_roles: None,
            supporting_roles: None,
            max_unblock_plots: 1,
            unblock_following_plots: None,
            openings: "openings",
            npc_openings: "login",
            npc_quit_openings: "logout",
            user_openings_option: None,
        }

    def create_plot():
        return {
            plot_id: "",
            task_name: "",
            max_attempts: "",
            predecessor_plots: None,
            main_roles: None,
            supporting_roles: None,
            max_unblock_plots: "",
            unblock_following_plots: None,
            openings: "",
            npc_openings: "",
            npc_quit_openings: "",
            user_openings_option: None,
        }

    def delete_plot(plot_id, uuid):
        uuid = check_uuid(uuid)
        plots = load_user_cfg(cfg_name=cfg_name, uuid=uuid)
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
        user_openings_option,
        uuid,
    ):
        uuid = check_uuid(uuid)
        plot_id = int(plot_id)
        if plot_id == "":
            gr.Warning("必须给一个新剧情设置一个id")
            return gr.Dropdown()

        plots = load_user_cfg(cfg_name=cfg_name, uuid=uuid)
        new_plot = get_plot_by_id(plot_id=plot_id, uuid=uuid, plots=plots) or dict()

        if new_plot not in plots:
            plots.append(new_plot)

        new_plot["plot_id"] = plot_id
        new_plot["max_attempts"] = ""
        new_plot["main_roles"] = None
        new_plot["supporting_roles"] = None
        new_plot["max_unblock_plots"] = ""
        new_plot["unblock_following_plots"] = None

        plot_descriptions = new_plot.get("plot_descriptions", dict())
        plot_descriptions["task"] = task_name
        plot_descriptions["predecessor_plots"] = None
        plot_descriptions["openings"] = ""
        plot_descriptions["npc_openings"] = ""
        plot_descriptions["npc_quit_openings"] = ""
        plot_descriptions["openings"] = ""
        plot_descriptions["user_openings_option"] = None
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
    plot_tab.select(on_plot_tab_select, inputs=[uuid], outputs=plot_selector)

    return plot_selector, on_plot_tab_select


def config_role_tab(role_tab, uuid):
    uuid = check_uuid(uuid)
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
            label="设置隐藏剧情",
            show_label=True,
            datatype=["str", "str"],
            column_widths=["10%", "95%"],
            headers=["剧情ID", "剧情描述"],
            type="array",
            wrap=True,
            col_count=(2, "fixed"),
        )
        plugin_background = gr.Dataframe(
            label="设置角色插件隐藏背景",
            show_label=True,
            datatype=["str"],
            headers=["角色背景"],
            type="array",
            wrap=True,
            col_count=(1, "fixed"),
        )

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
        hidden_plots = character_setting["hidden_plot"]
        hidden_plots = [
            [str(k), v] for k, v in hidden_plots.items()
        ] if hidden_plots else None

        plugin_backgrounds = [[str] for str in character_setting["plugin_background"]]
        clues = role.get("clue", None)
        clues = [
            [str(clue["plot"]), clue["name"], clue["content"]] for clue in clues
        ] if clues else None

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
            plot_clues: clues
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
            avatar_desc: "",
            use_memory: gr.Checkbox(label="是否开启记忆功能"),
            model_name: "",
            food_preference: "",
            background: "",
            hidden_plot: None,
            plugin_background: None,
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
        avatar_desc,
        use_memory,
        model_name,
        food_preference,
        background,
        hidden_plot,
        plugin_background,
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
        new_role["use_memory"] = use_memory
        new_role["model"] = model_name
        new_role["clue"] = [
            {"plot": int(clue[0]), "name": clue[1], "content": clue[2]}
            for clue in clues
            if clue[0]
        ]
        hidden_plot = {int(it[0]): it[1] for it in hidden_plot if it[0]}
        character_setting = new_role.get("character_setting", dict())
        character_setting["food_preference"] = food_preference
        character_setting["background"] = background
        character_setting["hidden_plot"] = hidden_plot
        character_setting["plugin_background"] = [it[0] for it in plugin_background]
        new_role["character_setting"] = character_setting
        save_user_cfg(roles, uuid=uuid)
        role_names = [role["name"] for role in roles]
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
    role_tab.select(on_role_tab_select, inputs=[uuid], outputs=role_selector)
    return role_selector, on_role_tab_select
