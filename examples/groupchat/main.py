# -*- coding: utf-8 -*-
""" A group chat where user can talk any time implemented by agentscope. """
from groupchat_utils import (
    select_next_one,
    filter_names,
)

import agentscope
from agentscope.agents import UserAgent
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.utils.common import timer

USER_TIME_TO_SPEAK = 10


def main() -> None:
    """group chat"""
    npc_agents = agentscope.init(
        model_configs="./configs/model_configs.json",
        agent_configs="./configs/agent_configs.json",
    )

    user = UserAgent()

    agents = list(npc_agents) + [user]

    hint = Msg(
        name="Host",
        content="This is a chat room and you can speak freely.",
    )

    rnd = 0
    speak_list = []
    with msghub(agents, announcement=hint):
        while True:
            try:
                with timer(USER_TIME_TO_SPEAK):
                    x = user()
            except TimeoutError:
                x = {"content": ""}
                print("\n")

            speak_list += filter_names(x.get("content", ""), npc_agents)

            if len(speak_list) > 0:
                next_agent = speak_list.pop(0)
                x = next_agent()
            else:
                next_agent = select_next_one(npc_agents, rnd)
                x = next_agent()

            speak_list += filter_names(x.content, npc_agents)

            rnd += 1


if __name__ == "__main__":
    main()
