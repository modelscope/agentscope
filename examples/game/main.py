# -*- coding: utf-8 -*-
import os
import yaml
import inquirer
import random
import argparse
from loguru import logger

import agentscope
from agentscope.message import Msg
from agentscope.msghub import msghub
from customer import Customer, CustomerConv, MIN_BAR_FRIENDSHIP_CONST
from ruled_user import RuledUser


from utils import (
    StagePerNight,
    GameCheckpoint,
    load_game_checkpoint,
    save_game_checkpoint,
    speak_print,
    check_active_plot,
)


def invited_group_chat(invited_customer, player, cur_plots_indices):
    logger.debug("\n---active_plots:" + str(cur_plots_indices))
    if len(invited_customer) == 0:
        return cur_plots_indices
    invited_names = [c.name for c in invited_customer]
    print("===== invited group chat ====")
    print(f"老板今天邀请了{invited_names}，大家一起聊聊")
    annoucement = {"role": "user", "content": "今天老板邀请大家一起来聚聚。"}
    with msghub(invited_customer + [player], announcement=annoucement):
        for _ in range(10):
            questions = [
                inquirer.List(
                    "ans",
                    message="【系统】：你要发言吗？",
                    choices=["是", "否", "结束邀请对话"],
                ),
            ]
            answer = inquirer.prompt(questions)["ans"]
            if answer == "是":
                msg = player(annoucement)
            elif answer == "否":
                msg = None
            elif answer == "结束邀请对话":
                break
            for c in invited_customer:
                msg = c(msg)
                speak_print(msg)

    invited_names.sort()
    print(cur_plots_indices)
    for idx in cur_plots_indices:
        correct_names = [GAME_CONFIG["plots"][idx]["main_role"]] + GAME_CONFIG[
            "plots"
        ][idx]["supporting_roles"]
        correct_names.sort()
        print("current names", correct_names)

        # TODO: decided by multi factor: chat history of msghub, correct_names
        if invited_names == correct_names:
            print("===== successfully unlock a plot =======")
            questions = [
                inquirer.List(
                    "ans",
                    message="【系统】：需要以哪位角色的视角生成一段完整故事吗？",
                    choices=invited_names + ["跳过"],
                ),
            ]
            answer = inquirer.prompt(questions)["ans"]
            for c in invited_customer:
                if c.name == answer:
                    c.generate_pov_story()
            for c in invited_customer:
                c.refine_background()
            return idx
    return None


def one_on_one_loop(customers, player):
    visit_customers = [c for c in customers if c.visit()]
    random.shuffle(visit_customers)

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
    print(f"今天拥有的食材是：{ingredient_today}")

    player.set_ingredients(ingredient_today)

    if not visit_customers:
        print("今天没有出现客人，请增加与客人的好感度以增大出现概率")
    else:
        print(f"今天出现的客人: {[c.name for c in visit_customers]}")
    for customer in visit_customers:
        print(
            f"顾客{customer.name} 进入餐馆 (当前好感度为: {customer.friendship})",
        )
        msg = player("游戏开始")
        while True:
            msg = customer(msg)
            if "score" in msg:
                print(
                    f"【系统】{customer.name}（顾客）接受了你的菜。\n"
                    f"【系统】顾客对菜本身的评价：{msg['content']}\n"
                    f"【系统】{customer.name}（顾客）享用完之后，"
                    f"综合满意度为{msg['score']}\n",
                )
                break
            speak_print(msg)
            print(
                "【提示】请输入“做菜”启动魔法锅，它会按所选定食材产生菜品。" " (对话轮次过多会使得顾客综合满意度下降。)",
            )
            msg = player(msg)
            if len(msg["content"]) == 0 or "[TERMINATE]" in msg["content"]:
                break

        if isinstance(msg, dict):
            if len(msg["content"]) == 0 or msg["score"] < 4:
                print(f"顾客{customer.name} 离开餐馆")
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

        answer = inquirer.prompt(questions)["ans"]
        if answer == "感谢您的光顾。(结束与该顾客的当天对话)":
            continue
        msg = Msg(role="user", name="餐馆老板", content=answer)
        player.observe(msg)
        while True:
            msg = customer(msg)
            # print(f"{customer_reply.name}（顾客）:" + customer_reply.content)
            speak_print(msg)
            print("【系统】输入`跳过`或者不输入终止对话。")
            msg = player(msg)
            if len(msg["content"]) == 0 or "跳过" in msg["content"]:
                print(f"顾客{customer.name} 离开餐馆")
                break
    return visit_customers


def invite_customers(customers):
    available_customers = [
        c.name for c in customers if c.friendship >= MIN_BAR_FRIENDSHIP_CONST
    ]
    invited_customers = []

    if len(available_customers) == 0:
        print("【系统】：您目前无法邀请任何一个顾客（所有顾客好感度均低于80）。")

    while len(available_customers) > 0:
        select_customer = [
            inquirer.List(
                "invited",
                message="系统：今天就没有更多顾客了，您明天有什么邀请计划吗？",
                choices=available_customers + ["END"],
            ),
        ]
        answer = inquirer.prompt(select_customer)["invited"]
        if answer == "END":
            break

        invited_customers.append(answer)
        available_customers.remove(answer)
    return invited_customers


def main() -> None:
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
            game_config=GAME_CONFIG,
            model=cfg["model"],
            use_memory=True,
        )
        for cfg in customer_configs
    ]

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
        stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
        cur_plots, done_plots = [], []
        checkpoint = GameCheckpoint(
            stage_per_night=stage_per_night,
            cur_plots=cur_plots,
            done_plots=done_plots,
            customers=customers,
            invited_customers=invited_customers,
        )

    # set current plot and done plots
    # initialize main role of current plot cur_state
    plots = GAME_CONFIG["plots"]
    for i in checkpoint.done_plots:
        plots[i]["state"] = "done"
    to_activate_customers, active_plots = check_active_plot(plots, None)
    checkpoint.cur_plots = active_plots
    logger.debug(str(to_activate_customers) + str(active_plots))
    to_activate_customers = set(to_activate_customers)
    for c in customers:
        if c.name in to_activate_customers:
            c.activate_plot()

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
            )
            if done_plot_idx is not None:
                next_active_roles, active_plots = check_active_plot(
                    plots,
                    done_plot_idx,
                )
                logger.debug("---active_plots:", active_plots)
                checkpoint.cur_plots = active_plots
                checkpoint.done_plots += [done_plot_idx]
                next_active_roles = set(next_active_roles)
                for c in checkpoint.customers:
                    if c.name in next_active_roles:
                        c.activate_plot()
            checkpoint.stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
        elif checkpoint.stage_per_night == StagePerNight.CASUAL_CHAT_FOR_MEAL:
            # ==========  one-on-one loop =================
            # the remaining not invited customers show up with probability
            rest_customers = [
                c
                for c in customers
                if c.name not in checkpoint.invited_customers
            ]
            visit_customers = one_on_one_loop(rest_customers, player)
            checkpoint.stage_per_night = StagePerNight.MAKING_INVITATION
        elif checkpoint.stage_per_night == StagePerNight.MAKING_INVITATION:
            # ============ making invitation decision =============
            # player make invitation
            invited = invite_customers(visit_customers)
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
    game_description = """
    这是一款模拟餐馆经营的文字冒险游戏，玩家扮演餐馆老板，通过与顾客互动来经营餐馆并解锁剧情。
    游戏分为四个阶段：选择食材做菜，随意聊天，一对一互动以及邀请对话。
    玩家需要根据顾客的喜好和需求来挑选食材做菜，通过顾客对用餐的满意度来获取好感度并解锁剧情。
    在游戏中，玩家需要经营餐厅、与顾客互动并决定邀请哪些顾客参与对话，以推动故事剧情的发展。
    通过与顾客的互动，玩家可以解锁剧情并发展餐馆的故事，体验不同的情节和结局。
    """
    logger.info(game_description)
    main()
