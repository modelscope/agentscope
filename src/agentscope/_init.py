# -*- coding: utf-8 -*-
"""The init function for the package."""
import json
import os
import shutil
from typing import Optional, Union, Sequence

from agentscope import agents
from .agents import AgentBase
from ._runtime import Runtime
from .file_manager import file_manager
from .utils.logging_utils import LOG_LEVEL, setup_logger
from .models import read_model_configs

_DEFAULT_DIR = "./runs"
_DEFAULT_LOG_LEVEL = "INFO"
_INIT_SETTINGS = {}


def init(
    model_configs: Optional[Union[dict, str, list]] = None,
    project: Optional[str] = None,
    name: Optional[str] = None,
    save_dir: str = _DEFAULT_DIR,
    save_log: bool = False,
    save_code: bool = False,
    save_api_invoke: bool = False,
    logger_level: LOG_LEVEL = _DEFAULT_LOG_LEVEL,
    agent_configs: Optional[Union[str, list, dict]] = None,
) -> Sequence[AgentBase]:
    """A unified entry to initialize the package, including model configs,
    runtime names, saving directories and logging settings.

    Args:
        model_configs (`Optional[Union[dict, str, list]]`, defaults to `None`):
            A dict, a list of dicts, or a path to a json file containing
            model configs.
        project (`Optional[str]`, defaults to `None`):
            The project name, which is used to identify the project.
        name (`Optional[str]`, defaults to `None`):
            The name for runtime, which is used to identify this runtime.
        save_dir (`str`, defaults to `./runs`):
            The directory to save logs, files, codes, and api invocations.
            If `dir` is `None`, when saving logs, files, codes, and api
            invocations, the default directory `./runs` will be created.
        save_log (`bool`, defaults to `False`):
            Whether to save logs locally.
        save_code (`bool`, defaults to `False`):
            Whether to save codes locally.
        save_api_invoke (`bool`, defaults to `False`):
            Whether to save api invocations locally, including model and web
            search invocation.
        logger_level (`LOG_LEVEL`, defaults to `"INFO"`):
            The logging level of logger.
        agent_configs (`Optional[Union[str, list, dict]]`, defaults to `None`):
            The config dict(s) of agents or the path to the config file,
            which can be loaded by json.loads(). One agent config should
            cover the required arguments to initialize a specific agent
            object, otherwise the default values will be used.
    """

    # TODO: add support to set quota for monitor

    # Load model configs if needed
    if model_configs is not None:
        read_model_configs(model_configs)

    # Init the runtime
    Runtime.project = project
    Runtime.name = name

    # Init file manager
    file_manager.init(save_dir, save_api_invoke)

    # Save code if needed
    if save_code:
        # Copy python file in os.path.curdir into runtime directory
        cur_dir = os.path.abspath(os.path.curdir)
        for filename in os.listdir(cur_dir):
            if filename.endswith(".py"):
                file_abs = os.path.join(cur_dir, filename)
                shutil.copy(file_abs, str(file_manager.dir_code))

    # Set logger and level
    dir_log = str(file_manager.dir_log) if save_log else None
    setup_logger(dir_log, logger_level)

    # Load config and init agent by configs
    if agent_configs is not None:
        if isinstance(agent_configs, str):
            with open(agent_configs, "r", encoding="utf-8") as file:
                configs = json.load(file)
        elif isinstance(agent_configs, dict):
            configs = [agent_configs]
        else:
            configs = agent_configs

        # setup agents
        agent_objs = []
        for config in configs:
            agent_cls = getattr(agents, config["class"])
            agent_args = config["args"]
            agent = agent_cls(**agent_args)
            agent_objs.append(agent)
        return agent_objs

    # save init settings globally, will be used to init child process
    _INIT_SETTINGS["model_configs"] = model_configs
    _INIT_SETTINGS["project"] = project
    _INIT_SETTINGS["name"] = name
    _INIT_SETTINGS["save_dir"] = save_dir
    _INIT_SETTINGS["save_log"] = save_log
    _INIT_SETTINGS["save_code"] = save_code
    _INIT_SETTINGS["save_api_invoke"] = save_api_invoke
    _INIT_SETTINGS["logger_level"] = logger_level
    _INIT_SETTINGS["agent_configs"] = agent_configs

    return []
