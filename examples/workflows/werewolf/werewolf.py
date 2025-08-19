# -*- coding: utf-8 -*-
"""A werewolf game implemented by agentscope."""
import asyncio
import os
from functools import partial
from typing import Any

from prompt import Prompts
from werewolf_utils import (
    check_winning,
    update_alive_players,
    majority_vote,
    extract_name_and_id,
    n2s,
    WolfDiscussionModel,
    VoteModel,
    WitchResurrectModel,
    WitchPoisonModel,
    SeerModel,
    collect_votes,
)
from agentscope.tool import Toolkit
from agentscope.agent import ReActAgent, AgentBase
from agentscope.formatter import DashScopeMultiAgentFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.message import Msg
from agentscope.pipeline import MsgHub, sequential_pipeline


class ModeratorAgent(AgentBase):
    """ModeratorAgent."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "Moderator"

    async def reply(self, msgs: Msg | list[Msg]) -> None:
        """Reply to the user's message."""
        if isinstance(msgs, Msg):
            msgs = [msgs]
        for msg in msgs:
            await self.print(msg)

    async def handle_interrupt(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Msg:
        """Handle interrupt."""

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Observe the user's message."""


# pylint: disable=too-many-statements, too-many-branches
async def main() -> None:
    """werewolf game"""
    # default settings
    moderator = ModeratorAgent()
    HostMsg = partial(Msg, name="Moderator", role="assistant")
    healing, poison = True, True
    MAX_WEREWOLF_DISCUSSION_ROUND = 3
    MAX_GAME_ROUND = 6
    roles = ["werewolf", "werewolf", "villager", "villager", "seer", "witch"]

    survivors = []

    for i in range(6):
        name = f"Player{i + 1}"
        survivors.append(
            ReActAgent(
                name=name,
                sys_prompt=Prompts.system_prompt_for_players.format(
                    player_name=name,
                    role=roles[i],
                ),
                model=DashScopeChatModel(
                    model_name="qwen-max",
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    stream=True,
                ),
                formatter=DashScopeMultiAgentFormatter(),
                toolkit=Toolkit(),
                memory=InMemoryMemory(),
            ),
        )

    wolves, witch, seer = survivors[:2], survivors[-1], survivors[-2]

    # start the game
    for _ in range(1, MAX_GAME_ROUND + 1):
        # night phase, werewolves discuss

        hint = HostMsg(content=Prompts.to_wolves.format(n2s(wolves)))
        await moderator(hint)
        async with MsgHub(wolves, announcement=hint) as hub:
            for _ in range(MAX_WEREWOLF_DISCUSSION_ROUND):
                x = None
                for wolf in wolves:
                    x = await wolf(x, structured_model=WolfDiscussionModel)
                if x.metadata.get("finish_discussion", False):
                    break

            # werewolves vote
            hint = HostMsg(content=Prompts.to_wolves_vote)
            await moderator(hint)

            votes = await collect_votes(wolves, hint, VoteModel)
            print("Werewolves vote: ", votes)

            # broadcast the result to werewolves
            dead_player: list = [majority_vote(votes)]
            vote_result = HostMsg(
                content=Prompts.to_wolves_res.format(
                    dead_player[0],
                ),
            )
            await hub.broadcast(vote_result)
            await moderator(vote_result)

        # witch
        healing_used_tonight = False
        if witch in survivors:
            if healing:
                hint = HostMsg(
                    content=Prompts.to_witch_resurrect.format_map(
                        {
                            "witch_name": witch.name,
                            "dead_name": dead_player[0],
                        },
                    ),
                )
                await moderator(hint)

                witch_result = await witch(
                    hint,
                    structured_model=WitchResurrectModel,
                )

                if witch_result.metadata.get("resurrect", False):
                    healing_used_tonight = True
                    dead_player.pop()
                    healing = False
                    witch_resurrect_result = HostMsg(
                        content=Prompts.to_witch_resurrect_yes,
                    )
                else:
                    witch_resurrect_result = HostMsg(
                        content=Prompts.to_witch_resurrect_no,
                    )
                await moderator(witch_resurrect_result)

            if poison and not healing_used_tonight:
                which_poison_msg = HostMsg(content=Prompts.to_witch_poison)
                await moderator(which_poison_msg)
                x = await witch(
                    which_poison_msg,
                    structured_model=WitchPoisonModel,
                )
                if x.metadata.get("poison", False):
                    dead_player.append(extract_name_and_id(x.metadata["name"]))
                    poison = False

        # seer
        if seer in survivors:
            hint = HostMsg(
                content=Prompts.to_seer.format(seer.name, n2s(survivors)),
            )
            await moderator(hint)

            x = await seer(hint, structured_model=SeerModel)

            player, idx = extract_name_and_id(x.metadata["name"])
            role = "werewolf" if roles[idx] == "werewolf" else "villager"
            hint = HostMsg(content=Prompts.to_seer_result.format(player, role))
            await moderator(hint)

            await seer.observe(hint)

        survivors, wolves = update_alive_players(
            survivors,
            wolves,
            dead_player,
        )

        wining_flag, msg = check_winning(survivors, wolves, "Moderator")
        if wining_flag:
            await moderator(msg)
            break

        # daytime discussion
        content = (
            Prompts.to_all_danger.format(n2s(dead_player))
            if dead_player
            else Prompts.to_all_peace
        )
        hints = [
            HostMsg(content=content),
            HostMsg(content=Prompts.to_all_discuss.format(n2s(survivors))),
        ]
        await moderator(hints)

        async with MsgHub(survivors, announcement=hints) as hub:
            # discuss
            await sequential_pipeline(survivors)

            # vote
            hint = HostMsg(content=Prompts.to_all_vote.format(n2s(survivors)))
            await moderator(hint)

            votes = await collect_votes(survivors, hint, VoteModel)
            print("Survivors votes list: ", votes)

            vote_res = majority_vote(votes)
            # broadcast the result to all players
            result = HostMsg(content=Prompts.to_all_res.format(vote_res))
            await moderator(result)
            await hub.broadcast(result)

            survivors, wolves = update_alive_players(
                survivors,
                wolves,
                vote_res,
            )

            wining_flag, msg = check_winning(survivors, wolves, "Moderator")
            if wining_flag:
                await moderator(msg)
                break

            continue_msg = HostMsg(content=Prompts.to_all_continue)
            await moderator(continue_msg)
            await hub.broadcast(continue_msg)


if __name__ == "__main__":
    asyncio.run(main())
