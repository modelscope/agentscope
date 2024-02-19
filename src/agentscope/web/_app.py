# -*- coding: utf-8 -*-
"""The main entry point of the web UI."""
import json
import os

from flask import Flask, jsonify, render_template, Response
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app)  # This will enable CORS for all routes


PATH_SAVE = ""


@app.route("/getProjects", methods=["GET"])
def get_projects() -> Response:
    """Get all the projects in the runs directory."""
    cfgs = []
    for run_dir in os.listdir(PATH_SAVE):
        print(run_dir)
        path_cfg = os.path.join(PATH_SAVE, run_dir, ".config")
        if os.path.exists(path_cfg):
            with open(path_cfg, "r", encoding="utf-8") as file:
                cfg = json.load(file)
                cfg["dir"] = run_dir
                cfgs.append(cfg)

    # Filter the same projects
    project_names = list({_["project"] for _ in cfgs})

    return jsonify(
        {
            "names": project_names,
            "runs": cfgs,
        },
    )


@app.route("/")
def home() -> str:
    """Render the home page."""
    return render_template("home.html")


@app.route("/run/<run_dir>")
def run_detail(run_dir: str) -> str:
    """Render the run detail page."""
    path_run = os.path.join(PATH_SAVE, run_dir)

    # Find the logging and chat file by suffix
    path_log = os.path.join(path_run, "logging.log")
    path_dialog = os.path.join(path_run, "logging.chat")

    if os.path.exists(path_log):
        with open(path_log, "r", encoding="utf-8") as file:
            logging_content = ["".join(file.readlines())]
    else:
        logging_content = None

    if os.path.exists(path_dialog):
        with open(path_dialog, "r", encoding="utf-8") as file:
            dialog_content = file.readlines()
        dialog_content = [json.loads(_) for _ in dialog_content]
    else:
        dialog_content = []

    path_cfg = os.path.join(PATH_SAVE, run_dir, ".config")
    if os.path.exists(path_cfg):
        with open(path_cfg, "r", encoding="utf-8") as file:
            cfg = json.load(file)
    else:
        cfg = {
            "project": "-",
            "name": "-",
            "id": "-",
            "timestamp": "-",
        }

    logging_and_dialog = {
        "config": cfg,
        "logging": logging_content,
        "dialog": dialog_content,
    }

    return render_template("run.html", runInfo=logging_and_dialog)


@socketio.on("connect")
def on_connect() -> None:
    """Execute when a client is connected."""
    print("Client connected")


@socketio.on("disconnect")
def on_disconnect() -> None:
    """Execute when a client is disconnected."""
    print("Client disconnected")


def init(
    path_save: str,
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
) -> None:
    """Start the web UI."""
    global PATH_SAVE

    if not os.path.exists(path_save):
        raise FileNotFoundError(f"The path {path_save} does not exist.")

    PATH_SAVE = path_save
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
