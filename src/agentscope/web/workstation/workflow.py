# -*- coding: utf-8 -*-
""" Workflow"""
import argparse
import json

from loguru import logger
from agentscope.web.workstation.workflow_utils import build_dag


def load_config(config_path: str) -> dict:
    """Load a JSON configuration file.

    Args:
        config_path: A string path to the JSON configuration file.

    Returns:
        A dictionary containing the loaded configuration.
    """
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    return config


def start_workflow(config: dict) -> None:
    """Start the application workflow based on the given configuration.

    Args:
        config: A dictionary containing the application configuration.

    This function will initialize and launch the application.
    """
    logger.info("Launching...")

    dag = build_dag(config)
    dag.run()

    logger.info("Finished.")


def main() -> None:
    """Parse command-line arguments and launch the application workflow.

    This function sets up command-line argument parsing and checks if a
    configuration file path is provided. If the configuration file is
    found, it proceeds to load it and start the workflow.

    If no configuration file is provided, a FileNotFoundError is raised.
    """
    parser = argparse.ArgumentParser(description="AgentScope Launcher")
    parser.add_argument(
        "cfg",
        type=str,
        help="Path to the config file.",
        nargs="?",
    )
    args = parser.parse_args()
    if args.cfg:
        config = load_config(args.cfg)
        start_workflow(config)
    else:
        raise FileNotFoundError("Please provide config file.")


if __name__ == "__main__":
    main()
