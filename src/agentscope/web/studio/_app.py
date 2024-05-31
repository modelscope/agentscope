# -*- coding: utf-8 -*-
"""The main entry point of the web UI."""
import json
import os
import re
import subprocess
import tempfile
import traceback
import uuid
from datetime import datetime
from typing import Tuple

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    Response,
    abort,
    send_file,
)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agentscope.db"
db = SQLAlchemy(app)
socketio = SocketIO(app)
CORS(app)  # This will enable CORS for all routes

PATH_SAVE = ""


class Run(db.Model):  # type: ignore[name-defined]
    """Run object."""

    id = db.Column(db.String, primary_key=True)
    project = db.Column(db.String)
    name = db.Column(db.String)
    script_path = db.Column(db.String)
    run_dir = db.Column(db.String)
    create_time = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String, default="finished")


class Server(db.Model):  # type: ignore[name-defined]
    """Server object."""

    id = db.Column(db.String, primary_key=True)
    host = db.Column(db.String)
    port = db.Column(db.Integer)
    create_time = db.Column(db.DateTime, default=datetime.now)


class Message(db.Model):  # type: ignore[name-defined]
    """Message object."""

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.String, db.ForeignKey("run.id"), nullable=False)
    name = db.Column(db.String)
    role = db.Column(db.String)
    content = db.Column(db.String)
    # todo: support list of url in future versions
    url = db.Column(db.String)
    meta = db.Column(db.String)
    timestamp = db.Column(db.String)


def get_history_messages(run_id: str) -> list:
    """Interface to get history messages. (Query from database for now)"""
    messages = Message.query.filter_by(run_id=run_id).all()
    return [
        {
            "name": message.name,
            "role": message.role,
            "content": message.content,
            "url": message.url,
            "metadata": json.loads(message.meta),
            "timestamp": message.timestamp,
        }
        for message in messages
    ]


def get_runs() -> list:
    """Interface to get all runs. (Query from database for now)"""
    runs = Run.query.all()
    return [
        {
            "id": run.id,
            "project": run.project,
            "name": run.name,
            "script_path": run.script_path,
            "run_dir": run.run_dir,
            "create_time": run.create_time.isoformat(),
            "status": run.status,
        }
        for run in runs
    ]


def remove_file_paths(error_trace: str) -> str:
    """
    Remove the real traceback when exception happens.
    """
    path_regex = re.compile(r'File "(.*?)(?=agentscope|app\.py)')
    cleaned_trace = re.sub(path_regex, 'File "[hidden]/', error_trace)

    return cleaned_trace


def convert_to_py(  # type: ignore[no-untyped-def]
    content: str,
    **kwargs,
) -> Tuple:
    """
    Convert json config to python code.
    """
    from agentscope.web.workstation.workflow_dag import build_dag

    try:
        cfg = json.loads(content)
        return "True", build_dag(cfg).compile(**kwargs)
    except Exception as e:
        return "False", remove_file_paths(
            f"Error: {e}\n\n" f"Traceback:\n" f"{traceback.format_exc()}",
        )

@app.route("/api/invocation/run/<run_id>", methods=["GET"])
def get_invocations(run_id: str):
    """Get all API invocations in a run instance."""
    return [
        {"model wrapper": "PostAPIChatWrapper", "timestamp": "20240513-212234"},
        {"model wrapper": "PostAPIChatWrapper", "timestamp": "20240713-212234"},
        {"model wrapper": "PostAPIChatWrapper", "timestamp": "20240313-212234"},
    ]


@app.route("/workstation")
def workstation() -> str:
    """Render the workstation page."""
    return render_template("workstation.html")


@app.route("/api/runs/register", methods=["POST"])
def register_run() -> Response:
    """
    Registers a run of an agentscope application.
    The running process will then be displayed as a page.
    """
    # Extract the input data from the request
    data = request.json
    run_id = data.get("run_id")
    project = data.get("project")
    name = data.get("name")
    run_dir = data.get("run_dir")
    # check if the run_id is already in the database
    if Run.query.filter_by(id=run_id).first():
        print(f"Run id {run_id} already exists.")
        abort(400, f"RUN_ID {run_id} already exists")
    db.session.add(
        Run(
            id=run_id,
            project=project,
            name=name,
            run_dir=run_dir,
            status="running",
        ),
    )
    db.session.commit()
    print(f"Register Run id {run_id}.")
    return jsonify(status="ok", msg="")


@app.route("/api/servers/register", methods=["POST"])
def register_server() -> Response:
    """
    Registers an agent server.
    """
    data = request.json
    server_id = data.get("server_id")
    host = data.get("host")
    port = data.get("port")

    if Server.query.filter_by(id=server_id).first():
        print(f"server id {server_id} already exists.")
        abort(400, f"run_id [{server_id}] already exists")
    db.session.add(
        Server(
            id=server_id,
            host=host,
            port=port,
        ),
    )
    db.session.commit()
    print(f"Register server id {server_id}")
    return jsonify(status="ok", msg="")


@app.route("/api/messages/put", methods=["POST"])
def put_message() -> Response:
    """
    Used by the application to speak a message to the Hub.
    """
    data = request.json
    run_id = data["run_id"]
    name = data["name"]
    role = data["role"]
    content = data["content"]
    metadata = json.dumps(data["metadata"])
    timestamp = data["timestamp"]
    url = data.get("url", None)
    try:
        new_message = Message(
            run_id=run_id,
            name=name,
            role=role,
            content=content,
            meta=metadata,
            url=url,
            timestamp=timestamp,
        )
        db.session.add(new_message)
        db.session.commit()
    except Exception as e:
        print(e)
        abort(400, "Fail to put message")
    socketio.emit(
        "display_message",
        {
            "run_id": run_id,
            "name": name,
            "role": role,
            "content": content,
            "url": url,
            "metadata": metadata,
            "timestamp": timestamp,
        },
        room=run_id,
    )
    return jsonify(status="ok", msg="")


@app.route("/api/messages/run/<run_id>", methods=["GET"])
def get_messages(run_id: str) -> list:
    """Get the history messages of specific run_id."""
    return [
        {"id": "84f76f86ef224927b6380bc2137d3f1a",
         "timestamp": "2024-05-15 17:47:50", "name": "Moderator",
         "content": "Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "f6ad3dddfcc84c0cbda0ff31380160bc",
         "timestamp": "2024-05-15 17:48:01", "name": "Player1",
         "content": "I think we should consider Player3. They've been pretty quiet, which could mean they're trying to hide something.",
         "role": "assistant", "url": None,
         "metadata": {"finish_discussion": True}},
        {"id": "f5add15699764a68887e0d6e6d148a37",
         "timestamp": "2024-05-15 17:48:10", "name": "Player2",
         "content": "I agree with your observation about Player3, but we should also consider Player4. They've been actively participating in the discussions, which could mean they're trying to lead the villagers. What do you think?",
         "role": "assistant", "url": None,
         "metadata": {"finish_discussion": False}},
        {"id": "4ac699252e9d459ea72d9901aa10a777",
         "timestamp": "2024-05-15 17:48:19", "name": "Player1",
         "content": "You make a good point about Player4, but I still have a feeling about Player3. Let's go with Player3 tonight.",
         "role": "assistant", "url": None,
         "metadata": {"finish_discussion": True}},
        {"id": "f5447ca72da14b8a89b48054568d41ff",
         "timestamp": "2024-05-15 17:48:27", "name": "Player2",
         "content": "Alright, let's go with Player3 tonight.",
         "role": "assistant", "url": None,
         "metadata": {"finish_discussion": True}},
        {"id": "568575c7829a4737851d014cb264ff0c",
         "timestamp": "2024-05-15 17:48:27", "name": "Moderator",
         "content": "Which player do you vote to kill?", "role": "assistant",
         "url": None, "metadata": None},
        {"id": "9c83e19dd40a4a1da77f28da9b157e2c",
         "timestamp": "2024-05-15 17:48:36", "name": "Player1",
         "content": "Player3", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "8abe18958bb7480b8d69f42278f54f20",
         "timestamp": "2024-05-15 17:48:41", "name": "Player2",
         "content": "Player3", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "5bb86c9731214a808de79f2af50a5f63",
         "timestamp": "2024-05-15 17:48:41", "name": "Moderator",
         "content": "The player with the most votes is Player3.",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "caadc33d0286411e9b23e33c39ba1a5f",
         "timestamp": "2024-05-15 17:48:41", "name": "Moderator",
         "content": "Player6, you're the witch. Tonight Player3 is eliminated. Would you like to resurrect Player3?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "28f7ea3e134f4ae8a58f82762beae80a",
         "timestamp": "2024-05-15 17:48:57", "name": "Player6",
         "content": "I'm sorry for Player3, but I think it's too early to make any drastic moves. We should be careful and strategic about our decisions.",
         "role": "assistant", "url": None, "metadata": {"resurrect": False}},
        {"id": "3f22417d73dd4296b6ed5be324ea1341",
         "timestamp": "2024-05-15 17:48:57", "name": "Moderator",
         "content": "The witch has chosen not to resurrect the player.",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "ce247cd872a649b880847bbeb5d01206",
         "timestamp": "2024-05-15 17:48:57", "name": "Moderator",
         "content": "Would you like to eliminate one player?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "f04fe02757824cfcaac6d6c2360770c8",
         "timestamp": "2024-05-15 17:49:04", "name": "Player6",
         "content": "I think we should continue the game and gather more information before making any drastic decisions.",
         "role": "assistant", "url": None, "metadata": {"eliminate": False}},
        {"id": "f00fce2cef784f3cbed985986657bf1e",
         "timestamp": "2024-05-15 17:49:04", "name": "Moderator",
         "content": "Player5, you're the seer. Which player in Player1, Player2, Player3, Player4, Player5 and Player6 would you like to check tonight?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "f752bb8cf2924a75a734d3e0b0010165",
         "timestamp": "2024-05-15 17:49:09", "name": "Player5",
         "content": "Player1", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "4eb565c3d68f48c3914efc1555367b86",
         "timestamp": "2024-05-15 17:49:09", "name": "Moderator",
         "content": "Okay, the role of Player1 is a werewolf.",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "a8c85d4654104beeb36267b33531c05c",
         "timestamp": "2024-05-15 17:49:09", "name": "Moderator",
         "content": "The day is coming, all the players open your eyes. Last night, the following player(s) has been eliminated: Player3.",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "fce4b04723c34a618484edc6756bff53",
         "timestamp": "2024-05-15 17:49:09", "name": "Moderator",
         "content": "Now the alive players are Player1, Player2, Player4, Player5 and Player6. Given the game rules and your role, based on the situation and the information you gain, to vote a player eliminated among alive players and to win the game, what do you want to say to others? You can decide whether to reveal your role. ",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "d9da349086cf4d3e9713748885b6391e",
         "timestamp": "2024-05-15 17:49:23", "name": "Player1",
         "content": "I found it strange that Player4 was so active in the discussions yesterday. It's almost as if they were trying to lead the villagers. What do you all think?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "8ecc37affd74427f8b8eea9e5a44bcc3",
         "timestamp": "2024-05-15 17:49:39", "name": "Player2",
         "content": "I agree with Player1. Player4 was indeed very active in the discussions. It's possible they were trying to manipulate the villagers. I vote for Player4.",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "d75191a4a44841e2aeb771be4ea24cd9",
         "timestamp": "2024-05-15 17:49:56", "name": "Player4",
         "content": "I understand your concerns, Player1 and Player2. But I assure you, I'm not a werewolf. I was active in the discussions because I'm trying to help the villagers win. I think we should focus on Player5, who has been very quiet. Maybe they're trying to avoid suspicion?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "f3872c71a89d48bab2fc5b51cd3b98d5",
         "timestamp": "2024-05-15 17:50:05", "name": "Player5",
         "content": "I understand your concerns, Player1 and Player2. But I think we should also consider Player6. They've been very quiet, which is suspicious. Maybe they're trying to avoid drawing attention to themselves?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "fead811509f444958485564fe0f75793",
         "timestamp": "2024-05-15 17:50:20", "name": "Player6",
         "content": "I understand your concerns, Player5. But I assure you, I'm not a werewolf. I've been quiet because I'm trying to observe and understand the dynamics of the group. I agree with Player1 and Player2 that Player4 has been very active in the discussions. Maybe they're trying to manipulate the villagers?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "871f7bd6fde64bcbbedfe62402bf63db",
         "timestamp": "2024-05-15 17:50:20", "name": "Moderator",
         "content": "Given the game rules and your role, based on the situation and the information you gain, to win the game, it's time to vote one player eliminated among the alive players. Which player do you vote to kill?",
         "role": "assistant", "url": None, "metadata": None},
        {"id": "83de10a5c6fb4c63a23b726a9c822b35",
         "timestamp": "2024-05-15 17:50:27", "name": "Player1",
         "content": "Player4", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "55bbfde651844bcc8ca82c1f2e826b76",
         "timestamp": "2024-05-15 17:50:35", "name": "Player2",
         "content": "Player4", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "a8c403b442ba48938e25852c0ce55380",
         "timestamp": "2024-05-15 17:50:40", "name": "Player4",
         "content": "Player5", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "40cba9a86f7e48a0b914f651fdb9ce22",
         "timestamp": "2024-05-15 17:50:44", "name": "Player5",
         "content": "Player4", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "65c5602e2db74712a512f80fb9f1b25d",
         "timestamp": "2024-05-15 17:50:52", "name": "Player6",
         "content": "Player4", "role": "assistant", "url": None,
         "metadata": None},
        {"id": "08607502b7b84320b5b0f79b975a2c85",
         "timestamp": "2024-05-15 17:50:52", "name": "Moderator",
         "content": "Player4 has been voted out.", "role": "assistant",
         "url": None, "metadata": None},
        {"id": "f29eaef8564d4d509c97edec9eac0077",
         "timestamp": "2024-05-15 17:50:52", "name": "Moderator",
         "content": "The werewolves have prevailed and taken over the village. Better luck next time!",
         "role": "assistant", "url": None, "metadata": None},
    ]
    return get_history_messages(run_id=run_id)


@app.route("/api/runs/all", methods=["GET"])
def get_all_runs() -> list:
    """Get all runs."""
    return [
        {
            'id': "123",
            'project': "werewolf",
            'name': "test1",
            'script_path': "/Users/david/Downloads/agentscope/examples/game_werewolf/runs/run_20240513-213745_sravxb/code",
            'run_dir': "123",
            "create_time": "2021-09-01T00:00:00",
            'status': "running",
        }
    ]
    return get_runs()


@app.route("/api/runs/new", methods=["GET"])
def get_available_run_id() -> Response:
    """Get an available run id."""
    return jsonify({"run_id": uuid.uuid4().hex})


@app.route("/api/runs/finish", methods=["POST"])
def finish_run() -> Response:
    """Finish a run."""
    run_id = request.json["run_id"]
    db.session.query(Run).filter_by(id=run_id).update({"status": "finished"})
    db.session.commit()
    return jsonify(status="ok")


@app.route("/file")
def get_local_file() -> Response:
    """Get the local file via the url."""
    file_path = request.args.get("url", None)
    code_dir = request.args.get("code", None)

    if file_path is not None:
        try:
            file = send_file(file_path)
            return file
        except FileNotFoundError:
            return jsonify({"error": "File not found."})

    if code_dir is not None:
        codes = {}
        if os.path.exists(code_dir):
            for filename in os.listdir(code_dir):
                code_path = os.path.join(code_dir, filename)
                if os.path.isfile(code_path) and filename.endswith(".py"):
                    with open(code_path, "r") as file:
                        codes[filename] = "".join(file.readlines())
        print("Return ", codes.keys())
        return jsonify(codes)


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


@app.route("/convert-to-py", methods=["POST"])
def convert_config_to_py() -> Response:
    """
    Convert json config to python code and send back.
    """
    content = request.json.get("data")
    status, py_code = convert_to_py(content)
    return jsonify(py_code=py_code, is_success=status)


@app.route("/convert-to-py-and-run", methods=["POST"])
def convert_config_to_py_and_run() -> Response:
    """
    Convert json config to python code and run.
    """
    content = request.json.get("data")
    uid = json.loads(get_available_run_id().get_data())["run_id"]
    studio_url = request.url_root.rstrip("/")
    status, py_code = convert_to_py(
        content,
        runtime_id=uid,
        studio_url=studio_url,
    )

    if status == "True":
        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".py",
                mode="w+t",
            ) as tmp:
                tmp.write(py_code)
                tmp.flush()
                subprocess.Popen(  # pylint: disable=R1732
                    ["python", tmp.name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
        except Exception as e:
            status, py_code = "False", remove_file_paths(
                f"Error: {e}\n\n" f"Traceback:\n" f"{traceback.format_exc()}",
            )
    return jsonify(py_code=py_code, is_success=status, uid=uid)


@app.route("/read-examples", methods=["POST"])
def read_examples() -> Response:
    """
    Read tutorial examples from local file.
    """
    lang = request.json.get("lang")
    file_index = request.json.get("data")

    if not os.path.exists(
        os.path.join(
            app.root_path,
            "static",
            "workstation_templates",
            f"{lang}{file_index}.json",
        ),
    ):
        lang = "en"

    with open(
        os.path.join(
            app.root_path,
            "static",
            "workstation_templates",
            f"{lang}{file_index}.json",
        ),
        "r",
        encoding="utf-8",
    ) as jf:
        data = json.load(jf)
    return jsonify(json=data)


@app.route("/")
def home() -> str:
    """Render the home page."""
    return render_template("index.html")


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


@socketio.on("request_user_input")
def request_user_input(data: dict) -> None:
    """Request user input"""
    print("request user input")
    run_id = data["run_id"]
    name = data["name"]
    agent_id = data["agent_id"]
    db.session.query(Run).filter_by(id=run_id).update({"status": "waiting"})
    db.session.commit()
    socketio.emit(
        "enable_user_input",
        {
            "run_id": run_id,
            "name": name,
            "agent_id": agent_id,
        },
        room=run_id,
    )


@socketio.on("user_input_ready")
def user_input_ready(data: dict) -> None:
    """Get user input and send to the agent"""
    print("user input ready")
    run_id = data["run_id"]
    content = data["content"]
    url = data.get("url", None)
    db.session.query(Run).filter_by(id=run_id).update({"status": "running"})
    db.session.commit()
    socketio.emit(
        "fetch_user_input",
        {
            "run_id": run_id,
            "content": content,
            "url": url,
        },
        room=run_id,
    )


@socketio.on("connect")
def on_connect() -> None:
    """Execute when a client is connected."""
    print("Client connected")


@socketio.on("disconnect")
def on_disconnect() -> None:
    """Execute when a client is disconnected."""
    print("Client disconnected")


@socketio.on("join")
def on_join(data: dict) -> None:
    """Join a websocket room"""
    run_id = data["run_id"]
    join_room(run_id)
    run = Run.query.filter_by(id=run_id).first()
    if run and run.status == "waiting":
        socketio.emit(
            "enable_user_input",
            {
                "run_id": run_id,
            },
            room=run_id,
        )


@socketio.on("leave")
def on_leave(data: dict) -> None:
    """Leave a websocket room"""
    run_id = data["run_id"]
    leave_room(run_id)


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
    with app.app_context():
        db.create_all()
    PATH_SAVE = path_save
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    init("/Users/david/Downloads/agentscope/examples/game_werewolf/runs", debug=True)
