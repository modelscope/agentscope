# -*- coding: utf-8 -*-
""" Setup for installation."""
from __future__ import absolute_import, division, print_function

import re
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import sys
import site
import platform
import subprocess

import setuptools

# obtain version from src/agentscope/_version.py
with open("src/agentscope/_version.py", encoding="UTF-8") as f:
    VERSION = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        f.read(),
        re.MULTILINE,
    ).group(1)

NAME = "agentscope"
URL = "https://github.com/modelscope/agentscope"

rpc_requires = [
    "grpcio==1.60.0",
    "grpcio-tools==1.60.0",
    "protobuf==4.25.0",
    "expiringdict",
    "dill",
    "psutil",
]

service_requires = [
    "docker",
    "pymongo",
    "pymysql",
    "bs4",
    "beautifulsoup4",
    "feedparser",
]

doc_requires = [
    "sphinx",
    "sphinx-autobuild",
    "sphinx_rtd_theme",
    "myst-parser",
    "sphinxcontrib-mermaid",
]

test_requires = ["pytest", "pytest-cov", "pre-commit"]

gradio_requires = [
    "gradio==4.19.1",
    "modelscope_studio==0.0.5",
]

rag_requires = [
    "llama-index==0.10.30",
]

studio_requires = []

# released requires
minimal_requires = [
    "networkx",
    "black",
    "docstring_parser",
    "pydantic",
    "loguru==0.6.0",
    "tiktoken",
    "Pillow",
    "requests",
    "chardet",
    "inputimeout",
    "openai>=1.3.0",
    "numpy",
    "Flask==3.0.0",
    "Flask-Cors==4.0.0",
    "Flask-SocketIO==5.3.6",
    "flask_sqlalchemy",
    "flake8",
    # TODO: move into other requires
    "dashscope==1.14.1",
    "openai>=1.3.0",
    "ollama>=0.1.7",
    "google-generativeai>=0.4.0",
    "zhipuai",
    "litellm",
    "notebook",
    "nbclient",
    "nbformat",
    "psutil",
    "scipy",
    "pillow",
    "pybind11",
]

distribute_requires = minimal_requires + rpc_requires
cpp_distribute_requires = distribute_requires

dev_requires = minimal_requires + test_requires

full_requires = (
    minimal_requires
    + rpc_requires
    + service_requires
    + doc_requires
    + test_requires
    + gradio_requires
    + rag_requires
    + studio_requires
)

online_requires = full_requires + [
    "oss2",
    "flask_babel",
    "babel==2.15.0",
    "gunicorn",
]

with open("README.md", "r", encoding="UTF-8") as fh:
    long_description = fh.read()


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[], language='c++')
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        if platform.system() == "Windows":
            return
        from setuptools import Distribution
        distribution = Distribution()
        distribution.parse_config_files()
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " + ", ".join(e.name for e in self.extensions))

        self.env = os.environ.copy()
        for ext in self.extensions:
            self.build_extension(ext)
        super().run()

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPython3_EXECUTABLE=' + sys.executable,
                      '-Dpybind11_DIR=' + os.path.join(site.getsitepackages()[0], 'pybind11', 'share', 'cmake', 'pybind11')]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', '-B', 'build', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=self.env)
        subprocess.check_call(['cmake', '--build', 'build'] + build_args, cwd=self.build_temp, env=self.env)
        subprocess.check_call(['cmake', '--install', 'build'], cwd=self.build_temp, env=self.env)


setuptools.setup(
    name=NAME,
    version=VERSION,
    author="SysML team of Alibaba Tongyi Lab ",
    author_email="gaodawei.gdw@alibaba-inc.com",
    description="AgentScope: A Flexible yet Robust Multi-Agent Platform.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    download_url=f"{URL}/archive/v{VERSION}.tar.gz",
    keywords=["deep-learning", "multi agents", "agents"],
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    package_data={
        "agentscope.studio": ["static/**/*", "templates/**/*"],
        "agentscope.prompt": ["_prompt_examples.json"],
    },
    install_requires=minimal_requires,
    extras_require={
        "distribute": distribute_requires,
        "cpp_distribute": cpp_distribute_requires,
        "dev": dev_requires,
        "full": full_requires,
        "online": online_requires,
    },
    ext_modules=[CMakeExtension('agentscope.cpp_server.cpp_server')],
    cmdclass=dict(build_ext=CMakeBuild),
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "as_studio=agentscope.studio:init",
            "as_gradio=agentscope.web.gradio.studio:run_app",
            "as_workflow=agentscope.web.workstation.workflow:main",
            "as_server=agentscope.server.launcher:as_server",
        ],
    },
)
