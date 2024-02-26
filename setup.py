# -*- coding: utf-8 -*-
""" Setup for installation."""
from __future__ import absolute_import, division, print_function

import re

import setuptools

# obtain version from src/agentscope/_version.py
with open("src/agentscope/_version.py", encoding="UTF-8") as f:
    VERSION = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        f.read(),
        re.MULTILINE,
    ).group(1)

NAME = "agentscope"
URL = "https://github.com/alibaba/AgentScope"

rpc_requires = ["grpcio", "grpcio-tools", "expiringdict"]

service_requires = ["docker", "pymongo", "pymysql"]

doc_requires = ["sphinx", "sphinx-autobuild", "sphinx_rtd_theme"]

test_requires = ["pytest", "pytest-cov", "pre-commit"]

game_requires = ["inquirer", "colorist", "dashscope", "gradio", "pyyaml",
                 "pypinyin", "modelscope_studio", "oss2"]

# released requires
minimal_requires = [
    "loguru",
    "tiktoken",
    "Pillow",
    "requests",
    "openai",
    "numpy",
]

distribute_requires = minimal_requires + rpc_requires

dev_requires = minimal_requires + test_requires

full_requires = (
    minimal_requires
    + rpc_requires
    + service_requires
    + doc_requires
    + test_requires
    + game_requires
)

with open("README.md", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name=NAME,
    version=VERSION,
    author="SysML team of Alibaba Tongyi Lab ",
    author_email="gaodawei.gdw@alibaba-inc.com",
    description="An easy-to-use multi-agent platforms.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    download_url=f"{URL}/archive/{VERSION}.tar.gz",
    keywords=["deep-learning", "multi agents", "agents"],
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    install_requires=minimal_requires,
    extras_require={
        "game": game_requires,
        "distribute": distribute_requires,
        "dev": dev_requires,
        "full": full_requires,
    },
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
