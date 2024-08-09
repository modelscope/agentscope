# -*- coding: utf-8 -*-
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
        f"./start_cluster_server.sh {','.join(hosts)} {agent_server_num} {env_server_num}",
    )
    time.sleep(10)


def clean_environment(hosts: list) -> None:
    """Clean the environment of the last run"""
    os.system(f"./stop_cluster_server.sh {','.join(hosts)}")


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
    use_llm: bool,
) -> None:
    """Run the simulation."""
    hosts = " ".join(hosts)
    os.system(
        f"python main.py --role main --hosts {hosts} --base-port 12330 --participant-num {participant_num} --server-per-host {agent_server_num} --moderator-per-host {env_server_num} --model-per-host {model_per_host} --agent-type {'llm' if use_llm else 'random'} --max-value 100 --model-name {model_name} --ann-id {sys_id} --pmt-id {usr_id} --exp-name {exp_name} --ratio {ratio} --round {round}",  # noqa
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
    use_llm: bool,
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
        use_llm=use_llm,
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


def main(name: str = None, config: str = None):
    hosts = ["worker1", "worker2", "worker3", "worker4"]
    configs = load_exp_config(config)
    for cfg in configs:
        run_case(
            participant_num=cfg["pariticipant_num"],
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
            use_llm=cfg["use_llm"],
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", "-n", type=str, default="simulation")
    parser.add_argument("--exp", "-c", type=str, default="exp")
    parser.add_argument(
        "--hosts",
        type=str,
        nargs="+",
        default=["worker1", "worker2", "worker3", "worker4"],
    )
    args = parser.parse_args()
    main(name=args.name, config=os.path.join("./configs", f"{args.exp}.csv"))
