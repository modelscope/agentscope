from __future__ import annotations
from typing import Optional, Callable, Any, Union
import enum
from loguru import logger

from customer import Customer


def always_true() -> bool:
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
            main_roles: Optional[list[Customer]] = None,
            supporting_roles: Optional[list[Customer]] = None,
            max_unblock_plots: Optional[int] = None
    ) -> None:
        self.id = plot_id
        self.main_roles = main_roles or []
        self.supporting_roles = supporting_roles or []
        self.state = self.PlotState.NON_ACTIVE
        self.max_unblock_plots = max_unblock_plots

        self.predecessor_plots = []
        self.support_following_plots: list[
            tuple[int, Union[bool, Callable]]
        ] = []

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

    def activate(self) -> bool:
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
            # activate roles in the current plot
            for role in self.main_roles + self.supporting_roles:
                role.activate_plot([self.id])
            return True
        else:
            return False

    def check_plot_condition(
            self,
            roles: list[Customer],
            all_plots: dict[int, GamePlot],
            **kwargs: Any
    ) -> tuple[bool, list[int]]:
        # when the invited roles are the same as the main roles of the plot,
        # this plot is considered done
        if self.main_roles == roles:
            logger.debug(f"Plot {self.id} is done")
            self.state = self.PlotState.DONE
        else:
            return False, []

        unblock_ids = []
        for i in range(len(self.support_following_plots)):
            unblock = self.support_following_plots[i][1](roles, **kwargs)
            if unblock and self.max_unblock_plots > 0:
                self.support_following_plots[i] = (
                    self.support_following_plots[i][0],
                    True
                )
                self.max_unblock_plots -= 1
                unblock_plot = all_plots[self.support_following_plots[i][0]]
                unblock_ids.append(unblock_plot.id)

        return True, unblock_ids


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
            main_roles=[roles_map[r] for r in cfg["main_roles"] or []],
            supporting_roles=[roles_map[r] for r in cfg["supporting_roles"] or []],
        )
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
    if curr_done is None:
        active_plots = []
        for id, plot in all_plots.items():
            print(id, plot.main_roles)
            if plot.activate():
                active_plots.append(id)
    else:
        prev_active.remove(curr_done)
        active_plots = prev_active
        for p_id, unlock in all_plots[curr_done].support_following_plots:
            if unlock and all_plots[p_id].activate():
                active_plots.append(p_id)
    return active_plots


if __name__ == "__main__":
    plot = GamePlot(1)
