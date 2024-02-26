from __future__ import annotations
from typing import Optional, Callable, Any, Union
import enum
from loguru import logger
import inquirer
import json

from customer import Customer
from ruled_user import RuledUser
from utils import (
    send_chat_msg,
    query_answer,
    SYS_MSG_PREFIX,
    OPENING_ROUND,
    generate_picture,
    send_quest_msg,
)
from enums import CustomerConv, StagePerNight


def always_true(**kwargs) -> bool:
    return True


UNBLOCK_FUNCTION = {
    "always": always_true
}


class GamePlot:
    """
    GamePlot is used to represent
    1. the dependency relationships between plots
    2. how the plots are activated
    in the game
    """

    class PlotState(enum.IntEnum):
        """Enum for customer status."""

        NON_ACTIVE = 0
        ACTIVE = 1
        DONE = 2

    def __init__(
            self,
            plot_id: int,
            plot_descriptions: dict,
            max_attempts: int = 2,
            main_roles: Optional[list[Customer]] = None,
            supporting_roles: Optional[list[Customer]] = None,
            max_unblock_plots: Optional[int] = None,
            plot_stages: Optional[list[int]] = None,
    ) -> None:
        self.id = plot_id
        self.main_roles = main_roles or []
        self.supporting_roles = supporting_roles or []
        self.state = self.PlotState.NON_ACTIVE
        self.max_unblock_plots = max_unblock_plots
        self.plot_description = plot_descriptions

        self.predecessor_plots = []
        self.support_following_plots: list[
            tuple[int, Union[bool, Callable]]
        ] = []
        self.contact_chances = 1
        self.max_attempts = max_attempts
        self.plot_stages = plot_stages

    def register_following_plot_check(
            self, plot_id: int, check_func: str
    ) -> None:
        """
        """
        self.support_following_plots.append(
            (plot_id, UNBLOCK_FUNCTION[check_func])
        )

    def add_predecessors(self, predecessors: list[GamePlot]):
        self.predecessor_plots += predecessors

    def is_done(self) -> bool:
        return self.state == self.PlotState.DONE

    def is_active(self) -> bool:
        return self.state == self.PlotState.ACTIVE

    def activate_roles(self) -> None:
        for c in self.main_roles + self.supporting_roles:
            c.activate_plot([self.id])

    def deactivate_roles(self) -> None:
        for c in self.main_roles + self.supporting_roles:
            c.deactivate_plot()

    def activate(self, player) -> bool:
        # check whether this plot can be activated
        can_activate = True
        for pred in self.predecessor_plots:
            if not pred.is_done():
                # not to activate this plot if there is a predecessor plot
                # that is not done
                can_activate = False
                break
            for plot_id, state in pred.support_following_plots:
                if plot_id == self.id and state is not True:
                    # not activate this plot if the predecessor plot does not
                    # allow activate this branch of plots
                    can_activate = False
                    break

        # set state to active
        if can_activate:
            self.state = self.PlotState.ACTIVE
            logger.debug(f"activate plot {self.id}")
            # activate roles in the current plot
            for role in self.main_roles + self.supporting_roles:
                role.activate_plot([self.id])
                logger.debug(f"activate role {role.name} for "
                             f"plot {role.active_plots}")
            for role in self.main_roles:
                role.relationship.to_max()
            quest = (
                self.plot_description["task"],
                {
                    "done_hint": self.plot_description["done_hint"],
                    "status": False,
                },
            )
            send_quest_msg(quest, uid=player.uid)
            self._begin_task(player)
            return True
        else:
            return False

    def check_plot_condition_done(
        self,
        roles: list[Customer],
        all_plots: dict[int, GamePlot],
        player: RuledUser,
        announcement: dict,
        force_done: bool = False,
        **kwargs: Any
    ) -> tuple[bool, list[int]]:
        # when the invited roles are the same as the main roles of the plot,
        # this plot is considered done
        correct_names = set([r.name for r in self.main_roles])
        input_names = set([r.name for r in roles])
        force_plot_done = (self.max_attempts == 1)

        if force_done or force_plot_done:
            self.state = self.PlotState.DONE
        else:
            if correct_names <= input_names:
                logger.debug(f"Start detect Plot {self.id} is done")
                # send_chat_msg(f"{SYS_MSG_PREFIX}判断是否达成剧情完成条件中，请稍等。",
                #               uid=player.uid)
                is_plot_done = player.success_detector(
                    self.plot_description["done_condition"],
                    announcement,
                )
                if is_plot_done:
                    self.state = self.PlotState.DONE
                else:
                    return False, []
            else:
                return False, []

        unblock_ids = []
        for i in range(len(self.support_following_plots)):
            unblock = self.support_following_plots[i][1](**kwargs)
            logger.debug(f"{i}, {unblock}, {self.max_unblock_plots}")
            if unblock and self.max_unblock_plots > 0:
                self.support_following_plots[i] = (
                    self.support_following_plots[i][0],
                    True
                )
                self.max_unblock_plots -= 1
                unblock_plot = all_plots[self.support_following_plots[i][0]]
                unblock_ids.append(unblock_plot.id)
                logger.debug(f"unblock plot {unblock_plot.id}")
        self.deactivate_roles()
        self.state = self.PlotState.DONE
        # Finish this quest
        quest = (
            self.plot_description["task"],
            {
                "done_hint": self.plot_description["done_hint"],
                "status": True,
            },
        )
        send_quest_msg(quest, uid=player.uid)

        return True, unblock_ids

    def _begin_task(self, player):
        openings = self.plot_description
        # by default, the first main role will trigger the task
        main_role = self.main_roles[0]
        uid = player.uid
        send_chat_msg(f"{SYS_MSG_PREFIX}{openings['openings']}", uid=uid)

        # send_chat_msg(f"{SYS_MSG_PREFIX}{openings['openings']}", uid=uid)
        opening_prompt = openings["npc_openings"]
        if "opening_image" in openings and len(openings["opening_image"]) > 0:
            send_chat_msg("**speak**", role=main_role.name, uid=main_role.uid,
                          avatar=main_role.avatar)
            picture_url = generate_picture(openings["opening_image"])
            opening_prompt += "\n" + f"![image]({picture_url})"
            main_role.talk(opening_prompt, is_display=True, flushing=False)
        else:
            main_role.talk(opening_prompt, is_display=True)
        send_chat_msg(f"{SYS_MSG_PREFIX}📜开启主线任务： {openings['task']} "
                      f"\n\n 任务描述：{openings['done_hint']}", uid=uid)
        msg = {"content": "开场"}
        main_role.transition(CustomerConv.OPENING)
        if openings.get("user_openings_option", None):
            choices = list(openings["user_openings_option"].values()) + [
                "自定义"]
        else:
            choices = None

        i = 0
        while i < OPENING_ROUND:
            if choices:
                questions = [
                    inquirer.List(
                        "ans",
                        message=f"{SYS_MSG_PREFIX}：你想要问什么？(剩余询问次数{OPENING_ROUND - i}，若不输入任何内容直接按回车键，当前对话人物将直接离开) ",
                        choices=choices,
                    ),
                ]

                choose_during_chatting = f"""{SYS_MSG_PREFIX}你想要问什么？(剩余询问次数{OPENING_ROUND - i}，若不输入任何内容直接按回车键，当前对话人物将直接离开) 
                <select-box shape="card"
                                                type="checkbox" item-width="auto" options=
                                               '
                                               {json.dumps(choices, ensure_ascii=False)}'
                                               select-once></select-box>"""

                send_chat_msg(
                    choose_during_chatting,
                    flushing=False,
                    uid=player.uid,
                )
                answer = query_answer(questions, "ans", uid=player.uid)
                send_chat_msg("**end_choosing**", uid=player.uid)

                if isinstance(answer, str):
                    if answer == "":
                        break
                    else:
                        msg = player.talk(answer, ruled=True)
                        # send_chat_msg("**end_choosing**", uid=player.uid)
                        if msg is None:
                            continue

                elif isinstance(answer, list) and len(answer):
                    if answer[0] in choices:
                        if answer[0] == "自定义":
                            msg = player(msg)
                        else:
                            msg = player.talk(answer[0], is_display=True)
                    # send_chat_msg("**end_choosing**", uid=player.uid)
                else:  # Walk away
                    # send_chat_msg("**end_choosing**", uid=player.uid)
                    break
            else:
                msg = player(msg)
            i += 1
            player.plot_riddle_success_detector(
                msg.get("content", "无"),
                self.plot_description["done_condition"],
                p_idx=self.id,
            )
            msg = main_role(msg)
        main_role.talk(openings["npc_quit_openings"], is_display=True)
        main_role.transition(CustomerConv.WARMING_UP)

def parse_plots(
        plot_configs: list[dict],
        roles: list[Customer]) -> dict[int, GamePlot]:
    """
    Parse the plot dependency from the plot config
    """
    roles_map = {r.name: r for r in roles}
    plots: dict[int, GamePlot] = {}
    # init GamePlots
    for cfg in plot_configs:
        gplot = GamePlot(
            int(cfg["plot_id"]),
            plot_descriptions=cfg["plot_descriptions"],
            main_roles=[roles_map[r] for r in cfg["main_roles"] or []],
            supporting_roles=[roles_map[r] for r in cfg["supporting_roles"] or []],
            max_attempts=cfg.get("max_attempt", 2),
            plot_stages=cfg.get("plot_stages", [x for x in range(len(StagePerNight))]),
        )
        if "max_unblock_plots" in cfg:
            gplot.max_unblock_plots = int(cfg["max_unblock_plots"])
        else:
            gplot.max_unblock_plots = 0
        plots[gplot.id] = gplot

    # add dependencies
    for cfg in plot_configs:
        plot_id = int(cfg["plot_id"])
        if cfg["predecessor_plots"] is not None:
            plots[plot_id].add_predecessors(
                [plots[p] for p in cfg["predecessor_plots"]]
            )
        if cfg["unblock_following_plots"] is not None:
            for sub_cfg in cfg["unblock_following_plots"]:
                plots[plot_id].register_following_plot_check(
                    int(sub_cfg["unblock_plot"]),
                    sub_cfg["unblock_chk_func"]
                )

    return plots


def check_active_plot(
        player: RuledUser,
        all_plots: dict[int, GamePlot],
        prev_active: list[int],
        curr_done: Optional[int],
) -> list[int]:
    """
    params: plots: list of plots
    params: prev_active: list of plots in active mode
    params: curr_done: current done plot index
    return
    active_plots: list of active plots
    """
    logger.debug(f"curr_done:{curr_done} prev_active: {prev_active}")
    if curr_done is None:
        active_plots = []
        for id, plot in all_plots.items():
            print(id, plot.main_roles)
            if plot.activate(player):
                active_plots.append(id)
    else:
        prev_active.remove(curr_done)
        active_plots = prev_active
        logger.debug(f"active_plots {active_plots}")
        for p_id, unlock in all_plots[curr_done].support_following_plots:
            # iterate all downstream plot of the current done plot
            logger.debug(f"{p_id}, {unlock}, {all_plots[curr_done].is_done()}")
            if unlock and all_plots[p_id].activate(player):
                active_plots.append(p_id)

    return active_plots
