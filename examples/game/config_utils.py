import os
import shutil

import yaml
from compress import get_hash, ZipCompressor
DEFAULT_AGENT_DIR = "/tmp/as_game/"
DEFAULT_CFG_DIR = os.path.join(DEFAULT_AGENT_DIR, "config")
CUSTOMER_CFG_NAME = "customer_config.yaml"
PLOT_CFG_NAME = "plot_config.yaml"
SIGNATURE_DIR = os.path.join(DEFAULT_AGENT_DIR, "signature")
SUFFIX = '.zip'

def load_configs(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        configs = yaml.safe_load(f)
    return configs


def save_configs(configs, config_file):
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(configs, f, allow_unicode=True)


def get_user_dir(uuid=""):
    user_dir = DEFAULT_CFG_DIR
    user_dir = user_dir.replace("config", "config/user")
    if uuid != "":
        user_dir = user_dir.replace("user", uuid)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_user_cfg_file(cfg_name=CUSTOMER_CFG_NAME, uuid="", use_default=False):
    cfg_dir = get_user_dir(uuid=uuid)
    cfg_file = os.path.join(cfg_dir, cfg_name)
    if not os.path.exists(cfg_file) or use_default:
        # copy the template to the address
        cfg_file_temp = f"./config/{cfg_name}"

        if cfg_file_temp != cfg_file:
            shutil.copy(cfg_file_temp, cfg_file)

    return cfg_file


def load_default_cfg(cfg_name=CUSTOMER_CFG_NAME, uuid=""):
    cfg_file = get_user_cfg_file(cfg_name=cfg_name, uuid=uuid, use_default=True)
    config = load_configs(cfg_file)
    return config


def load_user_cfg(cfg_name=CUSTOMER_CFG_NAME, uuid=""):
    cfg_file = get_user_cfg_file(cfg_name=cfg_name, uuid=uuid)
    # print(f'load from {cfg_file}')
    config = load_configs(cfg_file)
    return config


def save_user_cfg(config, cfg_name=CUSTOMER_CFG_NAME, uuid=""):
    cfg_file = get_user_cfg_file(cfg_name=cfg_name, uuid=uuid)
    # print(f'save to {cfg_file}')
    if uuid != "" and not os.path.exists(os.path.dirname(cfg_file)):
        os.makedirs(os.path.dirname(cfg_file))
    save_configs(config, cfg_file)

def get_signature_dir():
    os.makedirs(SIGNATURE_DIR, exist_ok=True)
    return SIGNATURE_DIR

def compress(uuid=""):
    signature_dir = get_signature_dir()
    user_dir = get_user_dir(uuid=uuid)
    signature = get_hash(user_dir)
    zip_file = os.path.join(signature_dir, signature) + SUFFIX
    ZipCompressor.compress(user_dir, zip_file)
    return signature, zip_file


def decompress_with_signature(signature, uuid=""):
    signature_dir = get_signature_dir()
    user_dir = get_user_dir(uuid=uuid)
    zip_file = os.path.join(signature_dir, signature) + SUFFIX
    ZipCompressor.decompress(zip_file, user_dir)
    return zip_file

def decompress_with_file(zip_file, uuid=""):
    user_dir = get_user_dir(uuid=uuid)
    ZipCompressor.decompress(zip_file, user_dir)
    return zip_file
