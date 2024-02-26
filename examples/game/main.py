# -*- coding: utf-8 -*-
import json
import os
import re
import time

import yaml
import inquirer
import random
import argparse
from loguru import logger
from typing import Optional

import agentscope
from agentscope.message import Msg
from agentscope.msghub import msghub
from config_utils import load_user_cfg, load_configs, PLOT_CFG_NAME
from customer import Customer
from enums import CustomerConv, StagePerNight
from ruled_user import RuledUser
from plot import parse_plots, GamePlot, check_active_plot


from utils import (
    GameCheckpoint,
    load_game_checkpoint,
    save_game_checkpoint,
    send_chat_msg,
    query_answer,
    SYS_MSG_PREFIX,
    CheckpointArgs,
    REVISION_ROUND,
    get_next_element,
    get_riddle_input,
)


def invited_group_chat(
    invited_customer: list[Customer],
    player: RuledUser,
    cur_plots_indices: list[int],
    all_plots: dict[int, GamePlot],
    uid: int,
) -> Optional[int]:
    logger.debug("\n---active_plots:" + str(cur_plots_indices))
    if len(invited_customer) == 0:
        return None
    invited_names = [c.name for c in invited_customer]
    # send_chat_msg(f"{SYS_MSG_PREFIX}群聊开始", uid=uid)
    if len(invited_names) > 1:
        send_chat_msg(f"现在有{'、'.join(invited_names)}在店里了...", uid=uid)
    announcement = {"role": "user", "content": "今天老板邀请大家一起来谈事情。"}
    with msghub(invited_customer + [player], announcement=announcement):
        for i in range(10):
            questions = [
                inquirer.List(
                    "ans",
                    message=f"{SYS_MSG_PREFIX}：你想要说些什么吗？（"
                            f"请直接输入想要说的话，若不输入任何内容直接按回车键将跳过该轮发言，"
                            f"如果你认为任务已经完成或想终止对话，请点击'结束对话'。）",
                    choices=["结束对话"],
                ),
            ]

            choose_during_chatting = f"""
            {SYS_MSG_PREFIX}你想要说些什么吗？（请直接输入想要说的话，若不输入任何内容直接按回车键将跳过该轮发言，如果你认为任务已经完成或想终止对话，请点击'结束对话'。） 
            <select-box shape="card"
                                type="checkbox" item-width="auto" options=
                               '{json.dumps(["结束对话"], ensure_ascii=False)}'
                               select-once></select-box>"""

            send_chat_msg(choose_during_chatting, flushing=False, uid=uid,
                          id=str(i))
            end_flag = False
            while True:
                answer = query_answer(questions, "ans", uid=uid)
                if isinstance(answer, str):
                    msg = player.talk(answer)
                elif answer == "\n":
                    msg = None
                elif answer == ["结束对话"]:
                    player.talk("今天谢谢大家🙏", is_display=True)
                    end_flag = True
                break
            send_chat_msg("**end_choosing**", uid=uid)
            if end_flag:
                break
            else:
                for c in invited_customer:
                    msg = c(msg)

    invited_names.sort()

    for idx in cur_plots_indices:
        # if there is no main roles in the current plot, it is a endless plot
        if len(all_plots[idx].main_roles) == 0:
            return None

        is_done, unblock_ids = all_plots[idx].check_plot_condition_done(
            invited_customer, all_plots, player, announcement
        )

        if is_done:
            involved_roles = all_plots[idx].main_roles + all_plots[idx].supporting_roles

            send_chat_msg(f"{SYS_MSG_PREFIX}💡恭喜你，剧情解锁成功！\n\n正确的答案是: "
                          f"{all_plots[idx].plot_description['done_condition']}",
                          uid=uid)
            for c in involved_roles:
                c.expose_all_clues(plot=idx)

            for c in involved_roles:
                c.add_plot_done_memory(
                    done_condition=all_plots[idx].plot_description[
                        "done_condition"],
                    main_role_names=[c.name for c in all_plots[idx].main_roles],
                    is_player_done=True,
                )

            for c in invited_customer:
                player.talk(f"我想听听{c.name}的故事", is_display=True)
                c.generate_pov_story()
            for c in involved_roles:
                c.refine_background()

            send_chat_msg(
                f" 💡剧情 {all_plots[idx].plot_description['task']} "
                f"已完成，请不要输入任何内容，即将进入下一个剧情...",
                uid=uid,
            )

            return idx

    send_chat_msg(f"{SYS_MSG_PREFIX} 剧情解锁失败，未满足剧情解锁条件。", uid=uid)
    for idx in cur_plots_indices:
        all_plots[idx].max_attempts -= 1
        involved_roles = all_plots[idx].main_roles + all_plots[idx].supporting_roles
        if all_plots[idx].max_attempts <= 0:
            restart_plot_choice=['继续游戏', '再次挑战']
            restart_plot = [
                inquirer.List(
                    "ans",
                    message=f"{SYS_MSG_PREFIX} 剧情解锁失败，剧情已结束，可以先复盘一下, 再次挑战。",
                    choices=restart_plot_choice
                ),
            ]

            choose_restart = f"""{SYS_MSG_PREFIX} 剧情解锁失败，剧情已结束，可以先复盘一下, 再次挑战。 <select-box
            shape="card"
                        item-width="auto" type="checkbox" options=
                        '{json.dumps(restart_plot_choice, ensure_ascii=False)}'
                        select-once></select-box>"""
            send_chat_msg(choose_restart, flushing=False, uid=uid)

            while True:
                answer = query_answer(restart_plot, "ans", uid=uid)
                if isinstance(answer, str):
                    send_chat_msg(f"{SYS_MSG_PREFIX}请在列表中选择。", uid=uid)
                    continue
                break
            send_chat_msg("**end_choosing**", uid=uid)
            if answer == ["继续游戏"]:
                send_chat_msg(f"{SYS_MSG_PREFIX}十分抱歉，你没有帮助到"
                              f"{all_plots[idx].main_roles[0].name}，任务失败，你触发了坏结局😟",
                              uid=uid)

                for c in involved_roles:
                    c.expose_all_clues(plot=idx)

                for c in involved_roles:
                    c.add_plot_done_memory(
                        done_condition=all_plots[idx].plot_description[
                            "done_condition"],
                        main_role_names=[c.name for c in all_plots[idx].main_roles],
                        is_player_done=False,
                    )

                for c in invited_customer:
                    player.talk(f"我想听听{c.name}的故事", is_display=True)
                    c.generate_pov_story()
                for c in involved_roles:
                    c.refine_background()

                send_chat_msg(
                    f" 💡剧情 {all_plots[idx].plot_description['task']} "
                    f"已完成，请不要输入任何内容，即将进入下一个剧情...",
                    uid=uid,
                )

                return idx
            else:
                # send_chat_msg("**end_choosing**", uid=uid)
                send_chat_msg(f"{SYS_MSG_PREFIX} 再次挑战开始", uid=uid)
                from utils import ResetException
                raise ResetException

    send_chat_msg(
        f"进入新的一天的营业时间",
        uid=uid)
    return None


def one_on_one_loop(customers, player, uid, checkpoint):
    contect_chances = 2
    visit_customers = [c for c in customers if c.visit()]
    # random.shuffle(visit_customers)

    ingredients = load_configs("config/ingredients.yaml")
    ingredient_today = {}
    for category, items in ingredients.items():
        ingredient_today[category] = (
            random.sample(items, 3)
            if len(
                items,
            )
            >= 3
            and category not in ["调味品", "其他辅料"]
            else items
        )
    # ingr = "\n".join(
    #     f"\n{key}: {' '.join([str(i) for i in value])}" for key, value in
    #     ingredient_today.items()
    # )
    # send_chat_msg(f"{SYS_MSG_PREFIX}今天拥有的食材是：\n{ingr}", uid=uid)

    player.set_ingredients(ingredient_today)

    if not visit_customers:
        send_chat_msg(f"{SYS_MSG_PREFIX}今天没有出现客人，请增加与客人的好感度以增大出现概率", uid=uid)
    # else:
    #     send_chat_msg(
    #         f"{SYS_MSG_PREFIX}今天出现的客人: {' '.join([c.name for c in visit_customers])}",
    #         uid=uid,
    #     )
    for customer in visit_customers:
        send_chat_msg(
            f"{SYS_MSG_PREFIX}顾客{customer.name} 进入餐馆 (当前熟悉程度为:"
            f"{customer.relationship.to_string()}）\n\n"
            f"通过提供令顾客满意的菜品来增加熟悉度，从而在对话中更容易获得有线索！",
            #", 好感度为: {round(# customer.friendship,2)})",
            uid=uid,
        )

        # cook for customer 
        customer({'content': ingredient_today})
        food = player.cook()

        if food == "跳过":
            send_chat_msg(f"{SYS_MSG_PREFIX}顾客{customer.name} 离开餐馆", uid=uid)
            continue

        msg = Msg(
            player.name,
            role="user",
            content=food,
            food=food,
        )

        msg = customer(msg)
        send_chat_msg(
            f"{SYS_MSG_PREFIX}{customer.name}（顾客）品尝了你的菜。\n"
            f" 顾客对菜本身的评价：{msg['content']}\n"
            f" {customer.name}（顾客)，"
            f"现在你们的关系为{msg['relationship']}了\n",
            uid=uid,
        )
            
        if not msg["is_satisfied"]:
            send_chat_msg(f"{SYS_MSG_PREFIX}顾客{customer.name} 离开餐馆", uid=uid)
            continue

        # expose a clue by order
        customer.expose_one_clue()
        #  继续挖掘线索
        questions = [
            inquirer.List(
                "ans",
                message=f"{SYS_MSG_PREFIX}：接下来你会说些什么吗？(客人熟悉程度提升了，你可以通过与他对话继续挖掘线索)",
                choices=[
                    "很高兴今天能让您满意！我能向您打听点事情吗？",
                    "感谢您的光顾。(结束与该顾客的当天对话)",
                ],
            ),
        ]

        choose_after_meal = f"""{SYS_MSG_PREFIX} 接下来你会说些什么吗？(客人熟悉程度提升了，你可以通过与他对话继续挖掘线索)
            <select-box shape="card" item-width="auto" type="checkbox" options=
            '{json.dumps(["很高兴今天能让您满意！我能向您打听点事情吗？",
                                 "感谢您的光顾。(结束与该顾客的当天对话)", "自定义输入"], ensure_ascii=False)}'
                                 select-once></select-box>"""

        send_chat_msg(choose_after_meal, flushing=False, uid=uid)

        answer = query_answer(questions, "ans", uid=uid)
        send_chat_msg("**end_choosing**", uid=uid)

        if isinstance(answer, str):
            answer = player.talk(answer, ruled=True)
        else:
            answer = answer[0]

            if answer == "感谢您的光顾。(结束与该顾客的当天对话)":
                player.talk("感谢您的光顾，再见👋", is_display=True)
                continue
            elif answer == "自定义输入":
                answer = player({"content": answer})["content"]
            else:
                player.talk("很高兴今天能让您满意！我能向您打听点事情吗？",
                            is_display=True)
        msg = Msg(role="user", name="餐馆老板", content=answer)
        player.observe(msg)
        while True:
            msg = customer(msg)
            # print(f"{customer_reply.name}（顾客）:" + customer_reply.content)

            send_chat_msg(f"{SYS_MSG_PREFIX}若不输入任何内容直接按回车键，顾客将离开餐馆。", uid=uid)
            msg = player(msg)
            if len(msg["content"]) == 0:
                send_chat_msg(f"{SYS_MSG_PREFIX}顾客{customer.name} 离开餐馆", uid=uid)
                break

        # Disable confirm_with_main_role for the current version.
        # Because group chat somehow provide the similar functionality.
        # confirm_with_main_role(uid, player, checkpoint)
    return visit_customers


def confirm_with_main_role(uid, player, checkpoint):
    contact_chances = {}
    for p_idx in checkpoint.cur_plots:
        cur_chances = checkpoint.all_plots[p_idx].contact_chances
        if cur_chances > 0:
            contact_chances[checkpoint.all_plots[p_idx].main_roles[0].name] = (p_idx, cur_chances)
    if len(contact_chances) < 1:
        return

    questions = [
        inquirer.List(
            "ans",
            message=f"{SYS_MSG_PREFIX}：需要联系以下角色吗？",
            choices=[
                f"{k} （剩余机会{v[1]}）" for k, v in contact_chances.items()
            ] + [f"不需要",]
        ),
    ]
    contect_main_role = f"""{SYS_MSG_PREFIX}：需要联系以下角色吗？？
        <select-box shape="card" item-width="auto" type="checkbox" options=
        '{json.dumps(
        [
                f"{k} （剩余机会{v[1]}）" for k, v in contact_chances.items()
        ] + [f"不需要",], ensure_ascii=False)}'
        select-once></select-box>"""

    send_chat_msg(contect_main_role, flushing=False, uid=uid)

    while True:
        answer = query_answer(questions, "ans", uid=uid)
        if isinstance(answer, str):
            send_chat_msg(
                f"{SYS_MSG_PREFIX}请在列表中选择。",
                uid=uid,
            )
            continue
        break
    send_chat_msg("**end_choosing**", uid=uid)

    answer = answer[0]

    if answer == "不需要":
        return

    main_role = None
    for choice, (p_idx, _) in contact_chances.items():
        main_role_name = choice.split()[0]
        if checkpoint.all_plots[p_idx].main_roles[0].name == main_role_name:
            main_role = checkpoint.all_plots[p_idx].main_roles[0]
            checkpoint.all_plots[p_idx].contact_chances -= 1
            break
    assert main_role is not None

    r = 0
    msg = {"role": "user", "content": f"联系{main_role}"}
    # todo: more elegant way?
    main_role.transition(CustomerConv.OPENING)
    while r < REVISION_ROUND:
        send_chat_msg(
            f"{SYS_MSG_PREFIX}若不输入任何内容直接按回车键，中止和{main_role.name}对话。"
            f"（当前机会剩余发言机会 {REVISION_ROUND - r}）",
            uid=uid
        )
        msg = player(msg)
        if len(msg["content"]) == 0:
            send_chat_msg(f"{SYS_MSG_PREFIX}结束与{main_role.name}联系",
                          uid=uid)
            break
        msg = main_role(msg)
        r += 1


def invite_customers(customers, uid, checkpoint):
    available_customers = [c.name for c in customers]

    p_idx = checkpoint.cur_plots[0]

    if len(checkpoint.cur_plots) > 1:
        tasks = [checkpoint.all_plots[i].plot_description['task'] for i in
                 checkpoint.cur_plots]

        task_prompt = f"{SYS_MSG_PREFIX} 当前有多个任务在进行中，请选择你想要完成的任务。"
        select_task = [
            inquirer.List(
                "task",
                message=task_prompt,
                choices=tasks,
            ),
        ]

        choose_task = task_prompt + f"""
            \n\n
            <select-box shape="card"  type="checkbox" item-width="auto" options=
                        '{json.dumps(tasks, ensure_ascii=False)}' select-once></select-box>
            """

        send_chat_msg(choose_task, flushing=False, uid=uid)

        while True:
            answer = query_answer(select_task, "task", uid=uid)
            if isinstance(answer, str):
                send_chat_msg(f"{SYS_MSG_PREFIX}请在列表中选择。", uid=uid)
                continue
            else:
                try:
                    p_idx = checkpoint.cur_plots[tasks.index(answer[0])]
                except ValueError:
                    pass
                send_chat_msg("**end_choosing**", uid=uid)
                break

    prompt = f"{SYS_MSG_PREFIX} " \
             f"《{checkpoint.all_plots[p_idx].plot_description['task'].rstrip()}》 "
    main_role = checkpoint.all_plots[p_idx].main_roles[0].name
    if "done_hint" in checkpoint.all_plots[p_idx].plot_description:
        prompt += checkpoint.all_plots[p_idx].plot_description['done_hint']

    # available_customers.insert(0, main_role)
    if len(checkpoint.all_plots[p_idx].plot_stages) > 1:
        available_customers.insert(0, "跳过")
        available_customers.insert(1, "只与主角对话")
    else:
        # not allow to skip
        available_customers.insert(0, "只与主角对话")

    if len(available_customers) > 1:
        select_customer = [
            inquirer.List(
                "invited",
                message=prompt + "今天就没有更多顾客了，您明天有什么邀请计划吗？",
                choices=available_customers,
            ),
        ]
        choose_available_customers = prompt + f"""
        \n\n 你可以选择与主角{main_role}和其他角色一起讨论，收集更多线索（当前任务剩余机会 
        {checkpoint.all_plots[p_idx].max_attempts}）
        <select-box shape="card"  type="checkbox" item-width="auto" options=
                    '{json.dumps(available_customers, ensure_ascii=False)}' select-once
                    submit-text="确定"></select-box>
        """

        send_chat_msg(choose_available_customers, flushing=False, uid=uid)

        while True:
            answer = query_answer(select_customer, "invited", uid=uid)
            logger.debug(answer)
            if isinstance(answer, str):
                send_chat_msg(f"{SYS_MSG_PREFIX}请在列表中选择。", uid=uid)
                continue
            elif answer[0] == "跳过":
                send_chat_msg(f"{SYS_MSG_PREFIX}==== 跳过此环节，进入下一天。"
                              f" ====", uid=uid)
                send_chat_msg("**end_choosing**", uid=uid)
                return []
            else:
                invited_customers = [main_role] + \
                                    [item for item in answer if item != '只与主角对话']
                send_chat_msg("**end_choosing**", uid=uid)
                return invited_customers
    else:
        # for special case, only has a main role in the plot
        send_chat_msg(f"{SYS_MSG_PREFIX} {prompt}（"
                      f"当前任务剩余机会{checkpoint.all_plots[p_idx].max_attempts}天）。", uid=uid)
        invited_customers = [main_role]
        send_chat_msg("**end_choosing**", uid=uid)
        return invited_customers


def riddle_success_detect(uid, player, checkpoint):
    riddle_input = get_riddle_input(uid=uid)
    if riddle_input:
        riddle_input = riddle_input[0]

        # Sent from opening stage
        pattern = r'\*\*plot_(\d+)_riddle_success\*\*'
        match = re.match(pattern, riddle_input)
        if match:
            is_done, idx = True, int(match.group(1))
        else:
            is_done, idx = player.riddle_success_detector(riddle_input, checkpoint)

        if is_done:
            involved_roles = checkpoint.all_plots[idx].main_roles + \
                             checkpoint.all_plots[idx].supporting_roles
            involved_roles_names = [c.name for c in involved_roles]
            send_chat_msg(f"{SYS_MSG_PREFIX}💡恭喜你，剧情解锁成功！\n\n正确的答案是: "
                          f"{checkpoint.all_plots[idx].plot_description['done_condition']}",
                          uid=uid)

            for c in involved_roles:
                c.expose_all_clues(plot=idx)

            # Update inner state
            checkpoint.all_plots[idx].check_plot_condition_done(
                involved_roles, checkpoint.all_plots, player, {},
                force_done=True,
            )

            for c in involved_roles:
                c.add_plot_done_memory(
                    done_condition=checkpoint.all_plots[idx].plot_description[
                        "done_condition"],
                    main_role_names=[c.name for c in
                                     checkpoint.all_plots[idx].main_roles],
                    is_player_done=True,
                )

            for c in involved_roles:
                player.talk(f"我想听听{c.name}的故事", is_display=True)
                c.generate_pov_story()

            for c in involved_roles:
                c.refine_background()

            send_chat_msg(
                f" 💡剧情 {checkpoint.all_plots[idx].plot_description['task']} "
                f"已完成，请不要输入任何内容，即将进入下一个剧情...",
                uid=uid,
            )

            # New openings, update cur_plots
            checkpoint.cur_plots = check_active_plot(
                player,
                checkpoint.all_plots,
                checkpoint.cur_plots,
                idx,
            )
            logger.debug(f"---active_plots:{checkpoint.cur_plots}")

            # Reset stages
            if len(checkpoint.cur_plots) == 1:
                checkpoint.stage_per_night = checkpoint.all_plots[
                    checkpoint.cur_plots[0]].plot_stages[0]
            else:
                # Use min index of plot as start
                tmp_stage = []
                for plot_id in checkpoint.cur_plots:
                    tmp_stage += checkpoint.all_plots[plot_id].plot_stages
                if tmp_stage:
                    checkpoint.stage_per_night = min(tmp_stage)
                else:
                    checkpoint.stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
            return True
        else:
            send_chat_msg(f"{SYS_MSG_PREFIX}玩家的最终答案：“{riddle_input}”，"
                          f"解谜失败，请继续加油！\n\n",
                          uid=uid)

        return False


def main(args) -> None:
    # game_description = f"""
    # {SYS_MSG_PREFIX}
    # 这是一款模拟餐馆经营的文字冒险游戏。
    # 玩家扮演餐馆老板，通过与顾客互动来经营餐馆并解锁剧情。
    # 游戏分为四个阶段：选择食材做菜，随意聊天，一对一互动以及邀请对话。
    # 玩家需要根据顾客的喜好和需求来挑选食材做菜，通过顾客对用餐的满意度来获取好感度并解锁剧情。
    # 在游戏中，玩家需要经营餐厅、与顾客互动并决定邀请哪些顾客参与对话，以推动故事剧情的发展。
    # 通过与顾客的互动，玩家可以解锁剧情并发展餐馆的故事，体验不同的情节和结局。
    # """
    # send_chat_msg(game_description, uid=args.uid)
    customer_configs = load_user_cfg(uuid=args.uid)
    user_configs = load_configs("config/user.yaml")

    customers = [
        Customer(
            name=cfg["name"],
            config=cfg,
            game_config=args.game_config,
            model=os.environ.get("HTTP_LLM_MODEL") if cfg["model"] == "post_api" else cfg["model"],
            use_memory=True,
            uid=args.uid,
        )
        for cfg in customer_configs
    ]

    plot_config = load_user_cfg(cfg_name=PLOT_CFG_NAME,uuid=args.uid)

    all_plots = parse_plots(plot_config, customers)

    user_configs["uid"] = args.uid
    user_configs["model"] = os.environ.get("HTTP_LLM_MODEL") if user_configs["model"] == "post_api" else user_configs["model"]
    user_configs["all_plots"] = all_plots
    player = RuledUser(**user_configs)

    if args.load_checkpoint is not None:
        checkpoint = load_game_checkpoint(args.load_checkpoint)
        logger.debug(
            "load checkpoint\n"
            + str(checkpoint.stage_per_night)
            + str(checkpoint.cur_plots),
        )
    else:
        invited_customers = []
        checkpoint = GameCheckpoint(
            stage_per_night=None,
            all_plots=all_plots,
            cur_plots=[],
            customers=customers,
            invited_customers=invited_customers,
            visit_customers=[],
        )

    # initialize main role of current plot cur_state
    checkpoint.cur_plots = check_active_plot(
        player, checkpoint.all_plots, checkpoint.cur_plots, None
    )

    if checkpoint.stage_per_night is None:
        if len(checkpoint.cur_plots) == 1:
            checkpoint.stage_per_night = checkpoint.all_plots[
                checkpoint.cur_plots[0]].plot_stages[0]
        else:
            # Use min index of plot as start
            tmp_stage = []
            for plot_id in checkpoint.cur_plots:
                tmp_stage += checkpoint.all_plots[plot_id].plot_stages
            checkpoint.stage_per_night = min(tmp_stage)

    logger.debug("initially active plots: " + str(checkpoint.cur_plots))

    uid = player.uid
    while True:
        done = riddle_success_detect(uid=uid, player=player, checkpoint=checkpoint)
        if done:
            continue
        logger.debug(f"active plots: {checkpoint.cur_plots}")
        logger.debug(f"current stage: {checkpoint.stage_per_night}")
        # daily loop
        daily_plot_stages = []
        if len(checkpoint.cur_plots) == 1:
            daily_plot_stages = checkpoint.all_plots[checkpoint.cur_plots[0]].plot_stages
        elif len(checkpoint.cur_plots) > 1:
            # multi-plot will act by order
            for plot_id in checkpoint.cur_plots:
                plot_stages = checkpoint.all_plots[plot_id].plot_stages
                for stage in plot_stages:
                    if stage not in daily_plot_stages:
                        daily_plot_stages.append(stage)
            daily_plot_stages.sort()
        else:
            daily_plot_stages = [StagePerNight.CASUAL_CHAT_FOR_MEAL]

        logger.debug(f"daily_plot_stages: {daily_plot_stages}")
        logger.debug(f"checkpoint.stage_per_night: {checkpoint.stage_per_night}")
        check_explore_all(checkpoint, uid)

        if checkpoint.stage_per_night == StagePerNight.CASUAL_CHAT_FOR_MEAL:
            # ==========  one-on-one loop =================
            # the remaining not invited customers show up with probability
            central_roles = []
            for p_idx in checkpoint.cur_plots:
                central_roles.append(checkpoint.all_plots[p_idx].main_roles[0].name)
            unavailable_roles = central_roles + checkpoint.invited_customers
            rest_customers = [
                c
                for c in customers
                if c.name not in unavailable_roles
            ]
            checkpoint.visit_customers = one_on_one_loop(
                rest_customers,
                player,
                args.uid,
                checkpoint,
            )
        elif checkpoint.stage_per_night == StagePerNight.MAKING_INVITATION:
            # ============ making invitation decision =============
            # player make invitation
            invited = invite_customers(checkpoint.visit_customers, args.uid,
                                       checkpoint)
            invited_customers = [c for c in customers if c.name in invited]
            checkpoint.invited_customers = invited_customers
            # ============ invited multi-agent loop ===============
            # invitation loop, 1) chat in msghub 2) plot unlock success check
            for c in checkpoint.invited_customers:
                # set customer to invited discussion cur_state
                c.transition(CustomerConv.INVITED_GROUP_PLOT)
            # initial cur_state of the
            done_plot_idx = invited_group_chat(
                checkpoint.invited_customers,
                player,
                checkpoint.cur_plots,
                checkpoint.all_plots,
                args.uid,
            )
            logger.debug(f"done plot: {done_plot_idx}")
            if done_plot_idx is not None:
                # find the roles and plot to be activated
                # Opening happen in this stage
                checkpoint.cur_plots = check_active_plot(
                    player,
                    checkpoint.all_plots,
                    checkpoint.cur_plots,
                    done_plot_idx,
                )
                logger.debug(f"---active_plots:{checkpoint.cur_plots}")

        checkpoint.stage_per_night = get_next_element(daily_plot_stages, checkpoint.stage_per_night)

        for c in customers:
            # reset all customer cur_state to pre-meal
            c.transition(CustomerConv.WARMING_UP)
        check_explore_all(checkpoint, uid)
        save_game_checkpoint(checkpoint, args.save_checkpoint)


def check_explore_all(checkpoint: GameCheckpoint, uid: int = None):
    if len(checkpoint.cur_plots) == 0:
        checkpoint.stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
        send_chat_msg(f"{SYS_MSG_PREFIX}恭喜你，你已经完成全部剧情！"
                      f"可以重新开始游戏，否则将进入饭店日常。",
                      uid=uid)
        for i in range(10, 0, -1):
            time.sleep(1)
            send_chat_msg(f"{SYS_MSG_PREFIX}{i}秒后进入饭店日常。",
                          uid=uid)
