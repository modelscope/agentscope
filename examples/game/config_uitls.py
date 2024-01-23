import os
import shutil

import yaml

DEFAULT_AGENT_DIR = '/tmp/as_game/'
DEFAULT_BUILDER_CONFIG_DIR = os.path.join(DEFAULT_AGENT_DIR, 'config')
DEFAULT_BUILDER_CONFIG_FILE = os.path.join(DEFAULT_BUILDER_CONFIG_DIR,
                                           'customer_config.yaml')


def load_configs(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        configs = yaml.safe_load(f)
    return configs


def save_configs(configs, config_file):
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(configs, f, allow_unicode=True)


def get_user_dir(uuid_str=''):
    return os.path.join(DEFAULT_BUILDER_CONFIG_DIR, uuid_str)


def get_user_cfg_file(uuid_str='', use_default=False):
    cfg_file = DEFAULT_BUILDER_CONFIG_FILE
    cfg_file = cfg_file.replace('config/', 'config/user/')

    if uuid_str != '':
        cfg_file = cfg_file.replace('user', uuid_str)

    if not os.path.exists(cfg_file) or use_default:
        # create parents directory
        os.makedirs(os.path.dirname(cfg_file), exist_ok=True)
        # copy the template to the address
        cfg_file_temp = './config/customer_config.yaml'

        if cfg_file_temp != cfg_file:
            shutil.copy(cfg_file_temp, cfg_file)

    return cfg_file


def load_default_cfg(uuid_str=''):
    cfg_file = get_user_cfg_file(uuid_str=uuid_str, use_default=True)
    config = load_configs(cfg_file)
    return config


def load_user_cfg(uuid_str=''):
    cfg_file = get_user_cfg_file(uuid_str=uuid_str)
    config = load_configs(cfg_file)
    return config


def save_user_cfg(config, uuid_str=''):
    cfg_file = get_user_cfg_file(uuid_str)
    if uuid_str != '' and not os.path.exists(os.path.dirname(cfg_file)):
        os.makedirs(os.path.dirname(cfg_file))
    save_configs(config, cfg_file)
