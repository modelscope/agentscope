# -*- coding: utf-8 -*-
import json
import os
import yaml
import inquirer
import random
import argparse
from loguru import logger
from typing import Optional

import agentscope
from agentscope.message import Msg
from agentscope.msghub import msghub
from customer import Customer, MIN_BAR_FRIENDSHIP_CONST
from enums import CustomerConv, StagePerNight
from ruled_user import RuledUser
from plot import parse_plots, GamePlot, check_active_plot


from utils import (
    GameCheckpoint,
    load_game_checkpoint,
    save_game_checkpoint,
    send_chat_msg,
    send_pretty_msg,
    query_answer,
    CheckpointArgs,
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
    send_chat_msg("【系统】群聊开始", uid=uid)
    send_chat_msg(f"老板今天邀请了{invited_names}，大家一起聊聊", uid=uid)
    announcement = {"role": "user", "content": "今天老板邀请大家一起来聚聚。"}
    with msghub(invited_customer + [player], announcement=announcement):
        for _ in range(10):
            questions = [
                inquirer.List(
                    "ans",
                    message="【系统】：你要发言吗？",
                    choices=["是", "否", "结束邀请对话"],
                ),
            ]

            choose_during_chatting = f"""【系统】你要发言吗？ <select-box shape="card"
                                type="checkbox" item-width="auto" options=
                               '
                               {json.dumps(["是", "否", "结束邀请对话"])}'
                               select-once></select-box>"""

            send_chat_msg(choose_during_chatting, flushing=False, uid=uid)
            end_flag = False
            while True:
                answer = query_answer(questions, "ans", uid=uid)
                if isinstance(answer, str):
                    send_chat_msg("【系统】请在列表中选择。", uid=uid)
                    continue
                elif answer == ["是"]:
                    msg = player(announcement)
                elif answer == ["否"]:
                    msg = None
                elif answer == ["结束邀请对话"]:
                    end_flag = True
                break
            if end_flag:
                break
            else:
                for c in invited_customer:
                    msg = c(msg)
                    send_pretty_msg(msg, uid=uid, avatar=c.avatar)

    invited_names.sort()

    for idx in cur_plots_indices:
        correct_names = [c.name for c in all_plots[idx].main_roles]
        # if there is no main roles in the current plot, it is a endless plot
        if len(correct_names) == 0:
            return None
        correct_names.sort()

        # TODO: decided by multi factor: chat history of msghub, correct_names
        if invited_names == correct_names:
            send_chat_msg("===== 剧情解锁成功 =======", uid=uid)
            questions = [
                inquirer.List(
                    "ans",
                    message="【系统】：需要以哪位角色的视角生成一段完整故事吗？",
                    choices=invited_names + ["跳过"],
                ),
            ]

            choose_role_story = f"""【系统】：需要以哪位角色的视角生成一段完整故事吗？: <select-box
            shape="card"
                        item-width="auto" type="checkbox" options=
                        '{json.dumps(invited_names + ["跳过"])}'
                        select-once></select-box>"""

            send_chat_msg(choose_role_story, flushing=False, uid=uid)

            while True:
                answer = query_answer(questions, "ans", uid=uid)
                if isinstance(answer, str):
                    send_chat_msg("【系统】请在列表中选择。", uid=uid)
                    continue
                break
            for c in invited_customer:
                if c.name == answer[0]:
                    c.generate_pov_story()
            for c in invited_customer:
                c.refine_background()
            return idx
    return None


def one_on_one_loop(customers, player, uid):
    visit_customers = [c for c in customers if c.visit()]
    # random.shuffle(visit_customers)

    with open(
        "config/ingredients.yaml",
        "r",
        encoding="utf-8",
    ) as ingredients_file:
        ingredients = yaml.safe_load(ingredients_file)

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
    ingr = "\n".join(
        f"{key}: {value}" for key, value in ingredient_today.items()
    )
    send_chat_msg(f"【系统】今天拥有的食材是：\n {ingr}", uid=uid)

    player.set_ingredients(ingredient_today)

    if not visit_customers:
        send_chat_msg("【系统】今天没有出现客人，请增加与客人的好感度以增大出现概率", uid=uid)
    else:
        send_chat_msg(
            f"【系统】今天出现的客人: {[c.name for c in visit_customers]}",
            uid=uid,
        )
    for customer in visit_customers:
        send_chat_msg(
            f"【系统】顾客{customer.name} 进入餐馆 (当前好感度为: {customer.friendship})",
            uid=uid,
        )
        msg = player({"content": "游戏开始"})
        while True:
            msg = customer(msg)
            if "score" in msg:
                send_chat_msg(
                    f"【系统】{customer.name}（顾客）接受了你的菜。\n"
                    f" 顾客对菜本身的评价：{msg['content']}\n"
                    f" {customer.name}（顾客）享用完之后，"
                    f"综合满意度为{msg['score']}\n",
                    uid=uid,
                )
                break

            send_pretty_msg(msg, uid=uid, avatar=customer.avatar)
            send_chat_msg(
                "【系统】请输入“做菜”启动做菜程序，它会按所选定食材产生菜品。 \n"
                " 对话轮次过多会使得顾客综合满意度下降。 \n"
                " 若不输入任何内容直接按回车键，顾客将离开餐馆。",
                uid=uid,
            )
            msg = player(msg)
            if len(msg["content"]) == 0 or "[TERMINATE]" in msg["content"]:
                break

        if isinstance(msg, dict):
            if len(msg["content"]) == 0 or msg["score"] < 4:
                send_chat_msg(f"【系统】顾客{customer.name} 离开餐馆", uid=uid)
                continue

        questions = [
            inquirer.List(
                "ans",
                message="【系统】：接下来你会说些什么吗？",
                choices=[
                    "感谢您的今天来我们这里消费。这里是赠送的果盘，请您享用。还有什么是我能为您做的呢？",
                    "感谢您的光顾。(结束与该顾客的当天对话)",
                ],
            ),
        ]

        choose_after_meal = f"""【系统】接下来你会说些什么吗？
            <select-box shape="card" item-width="auto" type="checkbox" options=
            '{json.dumps(["感谢您的今天来我们这里消费。这里是赠送的果盘，"
                                    "请您享用。还有什么是我能为您做的呢？",
                                 "感谢您的光顾。(结束与该顾客的当天对话)", "自定义输入"])}'
                                 select-once></select-box>"""

        send_chat_msg(choose_after_meal, flushing=False, uid=uid)

        while True:
            answer = query_answer(questions, "ans", uid=uid)
            if isinstance(answer, str):
                send_chat_msg(
                    "【系统】请在列表中选择。",
                    uid=uid,
                )
                continue
            break

        answer = answer[0]

        if answer == "感谢您的光顾。(结束与该顾客的当天对话)":
            continue
        elif answer == "自定义输入":
            answer = player({"content": answer})["content"]
        msg = Msg(role="user", name="餐馆老板", content=answer)
        player.observe(msg)
        while True:
            msg = customer(msg)
            # print(f"{customer_reply.name}（顾客）:" + customer_reply.content)

            send_pretty_msg(msg, uid=uid, avatar=customer.avatar)
            send_chat_msg("【系统】若不输入任何内容直接按回车键，顾客将离开餐馆。", uid=uid)
            msg = player(msg)
            if len(msg["content"]) == 0:
                send_chat_msg(f"【系统】顾客{customer.name} 离开餐馆", uid=uid)
                break
    return visit_customers


def invite_customers(customers, uid):
    available_customers = [
        c.name for c in customers if c.friendship >= MIN_BAR_FRIENDSHIP_CONST
    ]
    invited_customers = []

    if len(available_customers) == 0:
        send_chat_msg("【系统】：您目前无法邀请任何一个顾客（所有顾客好感度均低于80）。", uid=uid)

    select_customer = [
        inquirer.List(
            "invited",
            message="【系统】今天就没有更多顾客了，您明天有什么邀请计划吗？",
            choices=available_customers,
        ),
    ]

    choose_available_customers = f"""【系统】今天就没有更多顾客了，您明天有什么邀请计划吗？:
    <select-box shape="card"  type="checkbox" item-width="auto" options=
                '{json.dumps(available_customers)}' select-once
                submit-text="确定"></select-box>"""

    send_chat_msg(choose_available_customers, flushing=False, uid=uid)

    while True:
        answer = query_answer(select_customer, "invited", uid=uid)
        if isinstance(answer, str):
            send_chat_msg("【系统】请在列表中选择。", uid=uid)
            continue
        else:
            invited_customers = answer
            return invited_customers


def main(args) -> None:
    game_description = """
    【系统】
    这是一款模拟餐馆经营的文字冒险游戏。
    玩家扮演餐馆老板，通过与顾客互动来经营餐馆并解锁剧情。
    游戏分为四个阶段：选择食材做菜，随意聊天，一对一互动以及邀请对话。
    玩家需要根据顾客的喜好和需求来挑选食材做菜，通过顾客对用餐的满意度来获取好感度并解锁剧情。
    在游戏中，玩家需要经营餐厅、与顾客互动并决定邀请哪些顾客参与对话，以推动故事剧情的发展。
    通过与顾客的互动，玩家可以解锁剧情并发展餐馆的故事，体验不同的情节和结局。
    """
    send_chat_msg(game_description, uid=args.uid)

    with open(
        "config/customer_config.yaml",
        "r",
        encoding="utf-8",
    ) as customer_file:
        customer_configs = yaml.safe_load(customer_file)

    with open("config/user.yaml", "r", encoding="utf-8") as user_file:
        user_configs = yaml.safe_load(user_file)

    customers = [
        Customer(
            name=cfg["name"],
            config=cfg,
            game_config=args.game_config,
            model=cfg["model"],
            use_memory=True,
            uid=args.uid,
        )
        for cfg in customer_configs
    ]
    user_configs["uid"] = args.uid
    player = RuledUser(**user_configs)

    with open("config/plot_config.yaml", "r", encoding="utf-8") as plot_file:
        plot_config = yaml.safe_load(plot_file)

    all_plots = parse_plots(plot_config, customers)

    if args.load_checkpoint is not None:
        checkpoint = load_game_checkpoint(args.load_checkpoint)
        logger.debug(
            "load checkpoint\n"
            + str(checkpoint.stage_per_night)
            + str(checkpoint.cur_plots),
        )
    else:
        invited_customers = []
        stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
        checkpoint = GameCheckpoint(
            stage_per_night=stage_per_night,
            all_plots=all_plots,
            cur_plots=[],
            customers=customers,
            invited_customers=invited_customers,
            visit_customers=[],
        )

    # initialize main role of current plot cur_state
    checkpoint.cur_plots = check_active_plot(
        checkpoint.all_plots, checkpoint.cur_plots, None
    )
    logger.debug("initially active plots: " + str(checkpoint.cur_plots))

    while True:
        # daily loop
        if checkpoint.stage_per_night == StagePerNight.INVITED_CHAT:
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
            if done_plot_idx is not None:
                # once successful finish a current plot...
                # deactivate the active roles in the done plot
                checkpoint.all_plots[done_plot_idx].deactivate_roles()

                # find the roles and plot to be activated
                checkpoint.cur_plots = check_active_plot(
                    checkpoint.all_plots,
                    checkpoint.cur_plots,
                    done_plot_idx,
                )
                logger.debug("---active_plots:", checkpoint.cur_plots)
            checkpoint.stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
        elif checkpoint.stage_per_night == StagePerNight.CASUAL_CHAT_FOR_MEAL:
            # ==========  one-on-one loop =================
            # the remaining not invited customers show up with probability
            rest_customers = [
                c
                for c in customers
                if c.name not in checkpoint.invited_customers
            ]
            checkpoint.visit_customers = one_on_one_loop(
                rest_customers,
                player,
                args.uid,
            )
            checkpoint.stage_per_night = StagePerNight.MAKING_INVITATION
        elif checkpoint.stage_per_night == StagePerNight.MAKING_INVITATION:
            # ============ making invitation decision =============
            # player make invitation
            invited = invite_customers(checkpoint.visit_customers, args.uid)
            checkpoint.stage_per_night = StagePerNight.INVITED_CHAT
            invited_customers = [c for c in customers if c.name in invited]
            checkpoint.invited_customers = invited_customers

        for c in customers:
            # reset all customer cur_state to pre-meal
            c.transition(CustomerConv.WARMING_UP)
        save_game_checkpoint(checkpoint, args.save_checkpoint)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Game init", description="")
    parser.add_argument("--load_checkpoint", type=str, default=None)
    parser.add_argument(
        "--save_checkpoint",
        type=str,
        default="./checkpoints/cp-",
    )
    args = parser.parse_args()
    with open("./config/game_config.yaml", "r", encoding="utf-8") as file:
        GAME_CONFIG = yaml.safe_load(file)

    TONGYI_CONFIG = {
        "type": "tongyi",
        "name": "tongyi_model",
        "model_name": "qwen-max-1201",
        "api_key": os.environ.get("TONGYI_API_KEY"),
    }

    agentscope.init(model_configs=[TONGYI_CONFIG], logger_level="DEBUG")
    args = CheckpointArgs()
    args.game_config = GAME_CONFIG
    args.uid = None
    main(args)
