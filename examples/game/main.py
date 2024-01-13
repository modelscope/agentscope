import os, yaml, sys
import inquirer
import random
import argparse
from loguru import logger

import rich.pretty

from agentscope.models import read_model_configs, load_model_by_name
from agentscope.agents.user_agent import UserAgent
from agentscope.message import Msg
from agentscope.msghub import msghub
from customer import Customer
from utils import (
    StagePerNight,
    GameCheckpoint,
    load_game_checkpoint,
    save_game_checkpoint,
    speak_print,
)

def invited_group_chat(invited_customer, player, cur_plot):
    if len(invited_customer) == 0:
        return
    invited_names = [c.name for c in invited_customer]
    print("===== invited group chat ====")
    print(f"老板今天邀请了{invited_names}，大家一起聊聊")
    annoucement = {"role": "user", "content": "今天老板邀请大家一起来聚聚。"}
    with msghub(invited_customer + [player], announcement=annoucement):
        for i in range(10):
            questions = [
                inquirer.List('ans',
                              message="【系统】：你要发言吗？",
                              choices=['是','否','结束邀请对话'],
                              ),
            ]
            answer = inquirer.prompt(questions)['ans']
            if answer == "是":
                msg = player(annoucement)
            elif answer == '结束邀请对话':
                break
            for c in invited_customer:
                msg = c(msg)
                speak_print(msg)


    invited_names.sort()
    correct_names = GAME_CONFIG['plots'][cur_plot]
    correct_names.sort()
    if invited_names == correct_names:
        print("===== successfully unlock a plot =======")
        cur_plot += 1 # move to next plot
        for c in invited_customer:
            c.refine_background()
    return cur_plot

def one_on_one_loop(customers, player):
    visit_customers = [c for c in customers if c.visit()]
    random.shuffle(visit_customers)

    print("今天出现的客人：", [c.name for c in visit_customers])
    for customer in visit_customers:
        print(f"顾客{customer.name} 进入餐馆")
        msg = player("游戏开始")
        while True:
            msg = customer(msg)
            if isinstance(msg, tuple):
                print(
                    f"【系统】{customer.name}（顾客）接受了你的推荐。\n"
                    f"【系统】顾客对菜本身的评价：{msg[0]}\n"
                    f"【系统】{customer.name}（顾客）享用完之后，综合满意度为{msg[1]}"
                )
                break
            speak_print(msg)
            print(
                "【系统】如果想要最终推荐菜品，请说“推荐xxx”；否则请不要包含“推荐”关键词")
            msg = player(msg)
            if len(msg['content']) == 0 or "[TERMINATE]" in msg['content']:
                break

        if (isinstance(msg, tuple) and msg[1] < 4) or \
                (isinstance(msg, dict) and len(msg['content']) == 0):
            print(f"顾客{customer.name} 离开餐馆")
            continue

        questions = [
            inquirer.List('ans',
                          message="【系统】：接下来你会说些什么吗？",
                          choices=[
                              '这里是赠送的果盘，请您享用。还有什么是我能为您做的呢？',
                              '感谢您的光顾。(结束与该顾客的当天对话)',
                          ],
                          ),
        ]

        answer = inquirer.prompt(questions)['ans']
        if answer == '感谢您的光顾。(结束与该顾客的当天对话)':
            continue
        msg = Msg(role="user", name="餐馆老板", content=answer)
        player.observe(msg)
        while True:
            msg = customer(msg)
            # print(f"{customer_reply.name}（顾客）:" + customer_reply.content)
            speak_print(msg)
            msg = player(msg)
            if len(msg['content']) == 0 or "跳过" in msg['content']:
                break

def invite_customers(customers):
    available_customers = [c.name for c in customers]
    invited_customers = []
    while len(available_customers) > 0:
        select_customer = [
            inquirer.List('invited',
                          message="系统：今天就没有更多顾客了，您明天有什么邀请计划吗？",
                          choices=available_customers + ['END']
                          ),
        ]
        answer = inquirer.prompt(select_customer)['invited']
        if answer == "END":
            break
        else:
            invited_customers.append(answer)
            available_customers.remove(answer)
    return invited_customers

def main(args):
    model = load_model_by_name("tongyi_model")

    customer_configs = yaml.safe_load(open('config/customer_config.yaml'))

    customers = [
        Customer(
            name=cfg['name'], config=cfg, game_config=GAME_CONFIG, model=model,
            use_memory=True,
        ) for cfg in customer_configs
    ]

    player = UserAgent(name="餐馆老板")

    invited_customers = []
    stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
    cur_plot = 0

    if args.load_checkpoint is not None:
        checkpoint = load_game_checkpoint(args.load_checkpoint)
        customers = checkpoint.customers
        stage_per_night = checkpoint.stage_per_night
        cur_plot = checkpoint.cur_plot,
        invited_customers = checkpoint.invited_customers
        print("load checkpoint", checkpoint.stage_per_night, checkpoint.cur_plot)
    else:
        checkpoint = GameCheckpoint(
            stage_per_night=stage_per_night,
            cur_plot=cur_plot,
            customers=customers,
            invited_customers=invited_customers,
        )

    # initialize main role of current plot stage
    main_role = GAME_CONFIG["plots"][checkpoint.cur_plot][0]
    for c in customers:
        if c.name == main_role:
            c.activate_plot()

    while True:
        # daily loop
        if checkpoint.stage_per_night == StagePerNight.INVITED_CHAT:
            # ============ invitated multi-agent loop ===============
            # invitation loop, 1) chat in msghub 2) plot unlock success check
            for c in checkpoint.invited_customers:
                # set customer to invited discussion stage
                c.set_invited_stage()
            # initial stage of the
            checkpoint.cur_plot = invited_group_chat(
                checkpoint.invited_customers, player, checkpoint.cur_plot
            )
            checkpoint.stage_per_night = StagePerNight.CASUAL_CHAT_FOR_MEAL
        elif checkpoint.stage_per_night == StagePerNight.CASUAL_CHAT_FOR_MEAL:
            # ==========  one-on-one loop =================
            # the remaining not invited customers show up with probability
            rest_customers = [c for c in customers if c.name not in checkpoint.invited_customers]
            one_on_one_loop(rest_customers, player)
            checkpoint.stage_per_night = StagePerNight.MAKING_INVITATION
        elif checkpoint.stage_per_night == StagePerNight.MAKING_INVITATION:
            # ============ making invitation decision =============
            # player make invitation
            invited = invite_customers(customers)
            checkpoint.stage_per_night = StagePerNight.INVITED_CHAT
            invited_customers = [c for c in customers if c.name in invited]
            checkpoint.invited_customers = invited_customers

        for c in invited_customers:
            # reset all customer stage to pre-meal
            c.reset_stage()

        save_game_checkpoint(checkpoint, args.save_checkpoint)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Game init', description='',)
    parser.add_argument('--load_checkpoint', type=str, default=None)
    parser.add_argument('--save_checkpoint', type=str, default="./checkpoints/cp-")
    args = parser.parse_args()
    GAME_CONFIG = yaml.safe_load(open('./config/game_config.yaml'))

    logger.add(sys.stderr, level="INFO")

    TONGYI_CONFIG = {
        "type": "tongyi",
        'name': 'tongyi_model',
        'model_name': 'qwen-max-1201',
        'api_key': os.environ.get('TONGYI_API_KEY')
    }

    read_model_configs(TONGYI_CONFIG)
    main(args)