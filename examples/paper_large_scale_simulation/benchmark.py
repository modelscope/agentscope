# -*- coding: utf-8 -*-
"""Run benchmark"""
# pylint: disable=C0301,W1514,C0116,W0622
import time
import os
import csv
import argparse

RUN_DIR = f"./{os.uname().nodename}"


def setup_agent_server(
    agent_server_num: int,
    env_server_num: int,
    hosts: list,
) -> None:
    """Start agent servers"""
    os.system(
        f"./scripts/start_cluster_server.sh {','.join(hosts)}"
        f" {agent_server_num} {env_server_num}",
    )
    time.sleep(10)


def clean_environment(hosts: list) -> None:
    """Clean the environment of the last run"""
    os.system(f"./scripts/stop_cluster_server.sh {','.join(hosts)}")


def simulation(
    participant_num: int,
    agent_server_num: int,
    env_server_num: int,
    model_per_host: int,
    model_name: str,
    sys_id: int,
    usr_id: int,
    exp_name: str,
    hosts: list,
    round: int,
    ratio: str,
    agent_type: str,
) -> None:
    """Run the simulation."""
    hosts = " ".join(hosts)
    os.system(
        f"python main.py --role main --hosts {hosts} --base-port 12330 --participant-num {participant_num} --agent-server-per-host {agent_server_num} --env-server-per-host {env_server_num} --model-per-host {model_per_host} --agent-type {agent_type} --max-value 100 --model-name {model_name} --sys-id {sys_id} --usr-id {usr_id} --exp-name {exp_name} --ratio {ratio} --round {round}",  # noqa
    )


def run_case(
    participant_num: int,
    agent_server_num: int,
    env_server_num: int,
    model_per_host: int,
    model_name: str,
    sys_id: int,
    usr_id: int,
    exp_name: str,
    hosts: list,
    round: int,
    ratio: str,
    agent_type: str,
) -> None:
    """Run an experiment case."""
    clean_environment(hosts=hosts)
    setup_agent_server(agent_server_num, env_server_num, hosts)
    simulation(
        participant_num=participant_num,
        agent_server_num=agent_server_num,
        env_server_num=env_server_num,
        model_per_host=model_per_host,
        model_name=model_name,
        sys_id=sys_id,
        usr_id=usr_id,
        exp_name=exp_name,
        hosts=hosts,
        round=round,
        ratio=ratio,
        agent_type=agent_type,
    )


def load_exp_config(cfg_path: str) -> list:
    configs = []
    with open(cfg_path, "r") as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            row_dict = {
                key: int(value) if value.isdigit() else value
                for key, value in row.items()
            }
            configs.append(row_dict)
    return configs


def main(
    name: str = None,
    hosts: list[str] = None,
    config: str = None,
) -> None:
    """The main function of the benchmark"""
    configs = load_exp_config(config)
    for cfg in configs:
        run_case(
            participant_num=cfg["participant_num"],
            agent_server_num=cfg["agent_server_num"],
            env_server_num=cfg["env_server_num"],
            model_per_host=cfg["model_per_host"],
            model_name=cfg["model_name"],
            sys_id=cfg["sys_id"],
            usr_id=cfg["usr_id"],
            hosts=hosts[: cfg["host_num"]],
            exp_name=name,
            round=cfg["round"],
            ratio=cfg["ratio"],
            agent_type=cfg["agent_type"],
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", "-n", type=str, default="simulation")
    parser.add_argument("--config", "-c", type=str, default="experiment")
    parser.add_argument(
        "--hosts",
        type=str,
        nargs="+",
        default=["worker1", "worker2", "worker3", "worker4"],
    )
    args = parser.parse_args()
    main(
        name=args.name,
        hosts=args.hosts,
        config=os.path.join("./configs", f"{args.config}.csv"),
    )
