# -*- coding: utf-8 -*-
"""The participant agent."""
import random
import time
import json
import re
import os
from concurrent import futures
import math

from loguru import logger

from agentscope.rpc import async_func, RpcAgentClient
from agentscope.message import Msg
from agentscope.agents import AgentBase
from agentscope.environment import BasicEnv
from agentscope.exception import ResponseParsingError
from agentscope.manager import FileManager
from agentscope.logging import _save_msg
from agentscope.utils.tools import _get_timestamp


RUN_DIR = f"./{os.uname().nodename}"

RATIO_MAP = {
    "1/2": 1 / 2,
    "2/3": 2 / 3,
    "3/5": 3 / 5,
    "51/100": 51 / 100,
    "67/100": 67 / 100,
}

PROMPT = {
    "SYSTEM": {
        "1": "You are playing a multiplayer game.\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to {ratio} of the average of all reported numbers.\n\n",  # noqa
        "2": "You are playing a multiplayer game.\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to {ratio} of the average of all reported numbers.\n\n# Note:\n1. All players are rational.\n\n",  # noqa
        "3": "You are playing a multiplayer game.\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to {ratio} of the average of all reported numbers.\n\n# Note:\n1. All players are rational.\n2. All players will try to guess the others' strategies to adjust their own strategies.\n\n",  # noqa
        "4": 'You are playing a multiplayer game.\n\n# Game Rule\n1. This game is a variation of the famous "guess 2/3 of the average" game\n2. Each player reports a real number between 0 and {max_value}, inclusive.\n3. The winner will be the player whose number is the closest to {ratio} of the average of all reported numbers.\n\n',  # noqa
        "5": 'You are playing a multiplayer game.\n\n# Game Rule\n1. This game is a variation of the famous "guess 2/3 of the average" game\n2. Each player reports a real number between 0 and {max_value}, inclusive.\n3. The winner will be the player whose number is the closest to {ratio} of the average of all reported numbers.\n\n# Note:\n1. All players are rational.\n\n',  # noqa
        "6": "You are playing a multiplayer game.\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to 5 plus {ratio} of the average of all reported numbers .\n\n",  # noqa
        "7": "You are playing a multiplayer game.\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to 5 plus {ratio} of the average of all reported numbers .\n\n# Note:\n1. All players are rational.\n\n",  # noqa
        "8": 'You are playing a multiplayer game.\n\n# Game Rule\n1. This game is a variation of the famous "guess 2/3 of the average" game\n2. Each player reports a real number between 0 and {max_value}, inclusive.\n3. The winner will be the player whose number is the closest to 5 plus {ratio} of the average of all reported numbers .\n\n',  # noqa
        "9": 'You are playing a multiplayer game.\n\n# Game Rule\n1. This game is a variation of the famous "guess 2/3 of the average" game\n2. Each player reports a real number between 0 and {max_value}, inclusive.\n3. The winner will be the player whose number is the closest to 5 plus {ratio} of the average of all reported numbers .\n\n# Note:\n1. All players are rational.\n\n',  # noqa
        "10": "You are playing a role in a multiplayer game, make sure your behavior fits the following character background.\n\n# Character Background\n\n{background}\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to the {ratio} of the average of all reported numbers.\n\n# Note\n1. Please strictly follow your character background in the game.\n\n",  # noqa
        "11": "You are playing a role in a multiplayer game, make sure your behavior fits the following character background.\n\n# Character background\n\n{background}\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to the {ratio} of the average of all reported numbers.\n\n# Note:\n1. Please strictly follow your character background in the game.\n2. There are a total of 1000 players, with 200 individuals at each education level: Elementary School, High School, Bachelor's Degree, Master's Degree, and Ph.D.\n\n",  # noqa
        "12": "You are playing a role in a multiplayer game, make sure your behavior fits the following character background.\n\n# Character background\n\n{background}\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to the {ratio} of the average of all reported numbers.\n\n# Note:\n1. Please strictly follow your character background in the game.\n2. There are a total of 1200 players, with 200 individuals in each profession: Writers, Artists, Psychologists, Economists, and Professor of game theory\n\n",  # noqa
        "13": "You are playing a role in a multiplayer game, make sure your behavior fits the following character background.\n\n# Character background\n\n{background}\n\n# Game Rule\n1. Each player reports a real number between 0 and {max_value}, inclusive.\n2. The winner will be the player whose number is the closest to the {ratio} of the average of all reported numbers.\n\n# Note:\n1. Please strictly follow your character background in the game.\n2. There are a total of 1200 players, with different professions, including Writers, Artists, Psychologists, Economists, and Professors.\n3. Only one player is an expert in the field of game theory (it may be you, please judge for yourself based on your background information)\n\n",  # noqa
    },
    "USER": {
        "1": "Directly report your number without additional information.",
        "2": "Think step by step and then report your number.",
    },
}
SYSTEM = PROMPT["SYSTEM"]
USER = PROMPT["USER"]


class RandomParticipant(AgentBase):
    """A fake participant who generates number randomly."""

    def __init__(
        self,
        name: str,
        max_value: int = 100,
        sleep_time: float = 1.0,
        **kwargs,
    ) -> None:
        """Initialize the participant."""
        super().__init__(
            name=name,
        )
        self.max_value = max_value
        self.sleep_time = sleep_time

    def _generate_random_response(self) -> str:
        """generate a random int"""
        time.sleep(self.sleep_time)
        return str(random.randint(0, self.max_value))

    def reply(self, x: dict = None) -> dict:
        """Generate a random value"""
        response = self._generate_random_response()
        msg = Msg(self.name, content=response)
        return msg


class LLMParticipant(AgentBase):
    """A participant agent who generates number using LLM."""

    def __init__(
        self,
        name: str,
        model_config_name: str,
        max_value: int = 100,
        ratio: str = "2/3",
        sys_id: str = "1",
        **kwargs,
    ) -> None:
        """Initialize the participant."""
        super().__init__(
            name=name,
            sys_prompt=SYSTEM[sys_id].format(max_value=max_value, ratio=ratio),
            model_config_name=model_config_name,
            use_memory=True,
        )
        self.max_value = max_value
        self.prompt = Msg(
            name="system",
            role="system",
            content=SYSTEM[sys_id].format(max_value=max_value, ratio=ratio),
        )
        logger.warning(f"{self.model.generate_args}")
        self.round = 0

    def parse_value(self, txt: str) -> float:
        """Parse the number from the response."""
        prompt = self.model.format(
            Msg(
                name="system",
                role="system",
                content="You need to extract the number that the speaker wants to answer from the following text.\n"  # noqa
                + txt,
            ),
            Msg(
                name="user",
                role="user",
                content="Now please directly give the extracted number in the following format:\nThe answer is [number].\n\nIf you can't extract the number, please reply directly:\nI CAN'T.\n",  # noqa
            ),
        )
        parse_result = self.model(prompt).text
        numbers = re.findall(r"(\d+(\.\d+)?)", parse_result)
        if len(numbers) == 0:
            logger.error(
                f"Fail to parse value from [{txt}]",
            )
            return -1
        else:
            return float(numbers[0][0])

    def reply(self, x: dict = None) -> dict:
        """Generate a value by LLM"""
        if self.memory:
            self.memory.add(x)
        self.round += 1
        # prepare prompt
        prompt = self.model.format(self.prompt, self.memory.get_memory())
        # call llm and generate response
        for attempts in range(3):
            try:
                raw_response = self.model(prompt).text
                response = self.parse_value(raw_response)
                break
            except ResponseParsingError:
                logger.warning("Failed to parse number")
                if attempts == 2:
                    logger.error(f"Max retries reached. Use {-1} instead.")
                    response = str(-1)
        v = float(response)
        if v <= self.max_value and v >= 0:
            _save_msg(
                Msg(
                    self.name,
                    content={
                        "value": float(response),
                        "raw": raw_response,
                        "round": self.round,
                    },
                    role="assistant",
                ),
            )
        msg = Msg(self.name, content=response, role="assistant")
        # Record the message in memory
        if self.memory:
            self.memory.add(
                Msg(self.name, content=raw_response, role="assistant"),
            )

        return msg


class Moderator(AgentBase):
    """A Moderator to collect values from participants."""

    def __init__(
        self,
        name: str,
        part_configs: list[dict],
        agent_type: str = "random",
        max_value: int = 100,
        sleep_time: float = 1.0,
        usr_id: str = "1",
    ) -> None:
        super().__init__(name)
        self.max_value = max_value
        self.usr_id = usr_id
        self.round = 1
        if agent_type == "llm":
            self.participants = [
                LLMParticipant(
                    name=config["name"],
                    model_config_name=config["model_config_name"],
                    ratio=config["ratio"],
                    max_value=max_value,
                    sys_id=config["sys_id"],
                    to_dist={
                        "host": config["host"],
                        "port": config["port"],
                    },
                )
                for config in part_configs
            ]
        else:
            self.participants = [
                RandomParticipant(
                    name=config["name"],
                    max_value=max_value,
                    sleep_time=sleep_time,
                ).to_dist(
                    host=config["host"],
                    port=config["port"],
                )
                for config in part_configs
            ]

    def reply(self, x: dict = None) -> dict:
        results = []
        content = USER[self.usr_id].format(round=self.round)
        self.round += 1
        if x is not None:
            content = f"The winner number of this round is {x['content']['value']:.2f}. Let's move on to the next round.\n{content}"  # noqa
        msg = Msg(
            name="moderator",
            role="user",
            content=content,
        )
        for p in self.participants:
            results.append(p(msg))
        summ = 0
        cnt = 0
        for r in results:
            try:
                v = float(r["content"])
                if v <= self.max_value:
                    summ += v
                    cnt += 1
            except Exception as e:
                print(e)
        return Msg(
            name=self.name,
            role="assistant",
            content={
                "sum": summ,
                "cnt": cnt,
            },
        )


class LLMParticipantWithBackground(AgentBase):
    """A participant agent with background"""

    def __init__(
        self,
        name: str,
        model_config_name: str,
        max_value: int = 100,
        ratio: str = "2/3",
        sys_id: str = "1",
        background: str = None,
        **kwargs,
    ) -> None:
        super().__init__(
            name=name,
            model_config_name=model_config_name,
            use_memory=True,
        )
        self.max_value = max_value
        self.prompt = Msg(
            name="system",
            role="system",
            content=SYSTEM[sys_id].format(
                max_value=max_value,
                ratio=ratio,
                background=background,
            ),
        )
        logger.warning(f"{self.model.generate_args}")
        self.round = 0

    def parse_value(self, txt: str) -> float:
        """Parse the number from the response."""
        prompt = self.model.format(
            Msg(
                name="system",
                role="system",
                content="You need to extract the number that the speaker wants to answer from the following text.\n"
                + txt,
            ),
            Msg(
                name="user",
                role="user",
                content="Now please directly give the extracted number in the following format:\nThe answer is [number].\n\nIf you can't extract the number, please reply directly:\nI CAN'T.\n",
            ),
        )
        parse_result = self.model(prompt).text
        numbers = re.findall(r"(\d+(\.\d+)?)", parse_result)
        if len(numbers) == 0:
            logger.error(
                f"Fail to parse value from [{txt}]",
            )
            return "101"
        else:
            return numbers[0][0]

    def reply(self, x: dict = None) -> dict:
        """Generate a value by LLM"""
        if self.memory:
            self.memory.add(x)
        self.round += 1
        # prepare prompt
        prompt = self.model.format(self.prompt, self.memory.get_memory())
        # call llm and generate response
        for attempts in range(3):
            try:
                raw_response = self.model(prompt).text
                response = self.parse_value(raw_response)
                break
            except ResponseParsingError:
                logger.warning("Failed to parse number")
                if attempts == 2:
                    logger.error(f"Max retries reached. Use {-1}.")
                    response = -1
        v = float(response)
        if v <= self.max_value:
            logger.chat(
                Msg(
                    self.name,
                    content={
                        "value": float(response),
                        "raw": raw_response,
                        "round": self.round,
                    },
                    role="assistant",
                ),
            )
        msg = Msg(self.name, response, role="assistant")
        # Record the message in memory
        if self.memory:
            self.memory.add(
                Msg(self.name, content=raw_response, role="assistant"),
            )

        return msg


class ParserAgent(AgentBase):
    """Parse the experiment result"""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, use_memory=False)

    def parse_result(self, log_dir: str) -> dict:
        """Parse result from log files"""
        results = []
        tasks = []

        def parse_file(filepath):
            result = []
            with open(filepath, "r") as file:
                for line in file.readlines():
                    rec = json.loads(line)
                    result.append(rec)
            return result

        with futures.ThreadPoolExecutor() as executor:
            for filename in os.listdir(log_dir):
                if filename.startswith("server"):
                    filepath = os.path.join(log_dir, filename, "logging.chat")
                    tasks.append(executor.submit(parse_file, filepath))
            items = [task.result() for task in tasks]
        for item in items:
            results.extend(item)
        return results

    def reply(self, x: dict = None) -> dict:
        file_manager = FileManager.get_instance()
        return Msg(
            name=self.name,
            role="assistant",
            content=self.parse_result(file_manager.dir),
        )


class Group(BasicEnv):
    """A group of participants."""

    def __init__(
        self,
        name: str,
        agent_type: str = "random",
        ratio: str = "2/3",
        max_value: int = 100,
        usr_id: str = "2",
        participant_configs: list[dict] = None,
    ) -> None:
        super().__init__(name=name)
        if agent_type == "llm":
            self.participants = [
                LLMParticipant(
                    name=config["name"],
                    model_config_name=config["model_config_name"],
                    max_value=max_value,
                    ratio=ratio,
                    sys_id=config["sys_id"],
                    to_dist={
                        "host": config["host"],
                        "port": config["port"],
                    },
                )
                for config in participant_configs
            ]
        else:
            self.participants = [
                RandomParticipant(
                    name=config["name"],
                    max_value=max_value,
                    to_dist={
                        "host": config["host"],
                        "port": config["port"],
                    },
                )
                for config in participant_configs
            ]
        self.usr_prompt = USER[usr_id]
        self.sum = 0
        self.cnt = 0
        self.max_value = max_value

    @async_func
    def run(self, round: int, winner: float) -> tuple:
        """Play one round of game in this group."""
        if round != 0:
            content = (
                f"The winner number of this round is {winner:.2f}. Let's move on to the next round.\n{self.usr_prompt}",  # noqa
            )
        else:
            content = self.usr_prompt
        msg = Msg(name="moderator", role="user", content=content)
        result = []
        for p in self.participants:
            result.append(p(msg))
        for r in result:
            try:
                v = r["content"]
                if 0 <= v <= self.max_value:
                    self.sum += v
                    self.cnt += 1
            except Exception as e:
                print(e)
        return (self.sum, self.cnt)


def merge_result(results: list[dict]) -> list:
    """Merge the result from different machines"""
    result = []
    for r in results:
        result.extend(r["content"])
    grouped = {}
    for r in result:
        round_value = r["content"]["round"]
        if round_value not in grouped:
            grouped[round_value] = {}
        grouped[round_value].update({r["name"]: r["content"]})
    return list(grouped.values())


def save_result(
    results: list,
    run_time: float,
    save_path: str = "./result",
    ratio="2/3",
) -> None:
    """Save the result into file"""
    print(f"Round: {len(results)}")
    os.makedirs(save_path, exist_ok=True)
    from numpy import np
    from matplotlib import pyplot as plt

    for r, result in enumerate(results):
        values = [v["value"] for v in result.values()]
        logger.info(f"get {len(values)} values")
        win = np.mean(values) * RATIO_MAP[ratio]
        stats = {
            "win": win,
            "cnt": len(values),
            "avg": float(np.mean(values)),
            "med": float(np.median(values)),
            "std": float(np.std(values)),
            "max": float(np.max(values)),
            "min": float(np.min(values)),
            "time": run_time,
        }
        values = [int(v) for v in values]
        logger.info(stats)
        with open(os.path.join(save_path, f"result_{r}.json"), "w") as file:
            file.write(
                json.dumps(
                    {"data": result, "stats": stats},
                    indent=2,
                ),
            )
        # draw img
        plt.clf()
        counts = np.bincount(values, minlength=101)
        plt.figure(figsize=(4, 3))
        plt.bar(range(101), counts, color="#2980b9", alpha=0.7)
        plt.axvline(
            x=win,
            color="#f39c12",
            linestyle="dotted",
            linewidth=1,
            label=f"Winner: {win:.2f}",
        )
        plt.xlabel("Number")
        plt.ylabel("Frequency")
        plt.legend()
        plt.tight_layout()
        plt.savefig(
            os.path.join(save_path, f"result_{r}.pdf"),
            bbox_inches="tight",
            pad_inches=0.02,
        )


def check_server_alive(
    hosts: list,
    base_port: int,
    server_per_host: int,
) -> None:
    """Check server alive"""
    max_retry = 10
    for host in hosts:
        for port in range(base_port, base_port + server_per_host):
            client = RpcAgentClient(host, port)
            i = 0
            while not client.is_alive() and i < max_retry:
                logger.warning(
                    f"server [{host}:{port}] is not alive, retry...",
                )
                time.sleep(5)
                i += 1
            if i >= max_retry:
                logger.error("Exceed max retry")
                raise RuntimeError("Exceed max retry")


class GuessTwoThirdGame(BasicEnv):
    """Guess the 2/3 of the average game."""

    def __init__(
        self,
        name: str,
        hosts: list[str],
        base_port: int,
        server_per_host: int,
        model_per_host: int,
        participant_num: int,
        group_per_host: int = 10,
        agent_type: str = "random",
        sys_id: str = "1",
        usr_id: str = "1",
        model_name: str = "qwen2_72b",
        sleep_time: float = 1.0,
        max_value: int = 100,
        ratio: str = "2/3",
        round: int = 5,
    ) -> None:
        super().__init__(name)
        self.hosts = hosts
        self.host_num = len(hosts)
        self.base_port = base_port
        self.server_per_host = server_per_host
        self.model_per_host = model_per_host
        self.participant_num = participant_num
        self.group_per_host = group_per_host
        self.agent_type = agent_type
        self.sys_id = sys_id
        self.usr_id = usr_id
        self.model_name = model_name
        self.max_value = max_value
        self.ratio = ratio
        self.sleep_time = sleep_time
        self.round = 0
        self.max_round = round
        self.winners = []
        self._init_env()

    def _generate_participant_configs(
        self,
    ) -> list:
        total_agent_server_num = self.server_per_host * self.host_num
        participant_per_agent_server = math.ceil(
            self.participant_num / total_agent_server_num,
        )
        configs = []
        logger.info(
            f"init {self.participant_num} {self.agent_type} participant agents...",
        )
        # build init configs of participants
        for i in range(self.participant_num):
            idx = i // participant_per_agent_server
            host_id = idx // self.server_per_host
            port_id = idx % self.server_per_host
            model_id = i % self.model_per_host
            host = self.hosts[host_id]
            port = self.base_port + port_id
            config_name = f"model_{model_id + 1}"
            if self.agent_type == "random":
                configs.append(
                    {
                        "name": f"P{i}",
                        "host": host,
                        "port": port,
                    },
                )
            else:
                configs.append(
                    {
                        "name": f"P{i}",
                        "model_config_name": config_name,
                        "host": host,
                        "port": port,
                        "sys_id": self.sys_id,
                    },
                )
        return configs

    def _init_env(
        self,
    ) -> None:
        check_server_alive(
            hosts=self.hosts,
            base_port=self.base_port,
            server_per_host=self.server_per_host,
        )
        ist = time.time()
        configs = self._generate_participant_configs()

        self.groups = []
        group_num = self.group_per_host * self.host_num
        participant_per_group = self.participant_num // group_num
        tasks = []
        logger.info(f"init {group_num} moderator agents...")
        # init moderators
        with futures.ThreadPoolExecutor(max_workers=None) as executor:
            for i in range(group_num):
                tasks.append(
                    executor.submit(
                        Group,
                        name=f"group_{i}",
                        agent_type=self.agent_type,
                        ratio=self.ratio,
                        configs=configs[
                            i
                            * participant_per_group : (i + 1)  # noqa
                            * participant_per_group
                        ],
                        max_value=self.max_value,
                        sleep_time=self.sleep_time,
                        to_dist={
                            "host": self.hosts[i // self.group_per_host],
                            "port": self.base_port
                            + self.server_per_host
                            + i % self.group_per_host,
                        },
                    ),
                )
            for task in tasks:
                self.groups.append(task.result())
        iet = time.time()
        logger.info(f"[init takes {iet - ist} s]")

    def step(self):
        """Run one step of the game."""
        tasks = []
        summ = 0
        cnt = 0
        for g in self.groups:
            tasks.append(
                g.run(
                    self.round,
                    self.winners[-1] if len(self.winners) > 0 else 0,
                ),
            )
        for t in tasks:
            s, c = t.get()
            summ += s
            cnt += c
        self.winners.append(summ / cnt * RATIO_MAP[self.ratio])

    def record(self, run_time: float) -> None:
        """Record the game result."""
        results = []
        for host in self.hosts:
            parser = ParserAgent(
                f"parser-{host}",
                to_dist={"host": host, "port": self.base_port},
            )
            results.append(parser())
        result = merge_result(results)
        save_path = os.path.join(
            "./result",
            self.name,
            f"{self.model_name}",
            f"{self.sys_id}-{self.usr_id}-{self.participant_num}-{self.host_num}-{RATIO_MAP[self.ratio]:.3f}",
            _get_timestamp(format_="%Y-%m-%d-%H:%M:%S"),
        )
        save_result(result, run_time, save_path, self.ratio)

    def run(self) -> None:
        """Run the game"""
        st = time.time()
        while self.round < self.max_round:
            self.step()
            self.round += 1
        et = time.time()
        try:
            self.record(et - st)
        except Exception as e:
            logger.error(f"Fail to save results: {e}")
