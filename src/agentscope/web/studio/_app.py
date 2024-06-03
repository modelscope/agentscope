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
from typing import Tuple, Union

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

from agentscope.constants import _DEFAULT_SUBDIR_CODE, _DEFAULT_SUBDIR_INVOKE

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agentscope.db"
db = SQLAlchemy(app)
socketio = SocketIO(app)
CORS(app)  # This will enable CORS for all routes


_RUNS_DIRS = []


class Run(db.Model):  # type: ignore[name-defined]
    """Run object."""

    run_id = db.Column(db.String, primary_key=True)
    project = db.Column(db.String)
    name = db.Column(db.String)
    timestamp = db.Column(db.String)
    run_dir = db.Column(db.String)
    pid = db.Column(db.String)
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
    run_id = db.Column(db.String, db.ForeignKey("run.run_id"), nullable=False)
    name = db.Column(db.String)
    role = db.Column(db.String)
    content = db.Column(db.String)
    # todo: support list of url in future versions
    url = db.Column(db.String)
    meta = db.Column(db.String)
    timestamp = db.Column(db.String)


def _get_all_runs_from_dir() -> dict:
    """Get all runs from the directory."""
    global _RUNS_DIRS
    runtime_configs_from_dir = {}
    for runs_dir in set(_RUNS_DIRS):
        for runtime_dir in os.listdir(runs_dir):
            path_runtime = os.path.join(runs_dir, runtime_dir)
            path_config = os.path.join(path_runtime, ".config")
            if os.path.exists(path_config):
                with open(path_config, "r") as file:
                    runtime_config = json.load(file)

                    # TODO: judge if the runtime ends
                    runtime_config["status"] = "finished"

                    if "run_dir" not in runtime_config:
                        runtime_config["run_dir"] = path_runtime

                    if "id" in runtime_config:
                        runtime_config["run_id"] = runtime_config["id"]
                        del runtime_config["id"]

                    runtime_id = runtime_config.get("run_id")
                    runtime_configs_from_dir[runtime_id] = runtime_config

    return runtime_configs_from_dir


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

@app.route("/workstation")
def workstation() -> str:
    """Render the workstation page."""
    return render_template("workstation.html")


@app.route("/api/runs/register", methods=["POST"])
def register_run() -> Response:
    """Registers a running instance of an agentscope application."""

    # Extract the input data from the request
    data = request.json
    run_id = data.get("run_id")

    # check if the run_id is already in the database
    if Run.query.filter_by(run_id=run_id).first():
        print(f"Run id {run_id} already exists.")
        abort(400, f"RUN_ID {run_id} already exists")

    # Add into the database
    db.session.add(
        Run(
            run_id=run_id,
            project=data.get("project"),
            name=data.get("name"),
            timestamp=data.get("timestamp"),
            run_dir=data.get("run_dir"),
            pid=data.get("pid"),
            status="running",
        ),
    )
    db.session.commit()

    return jsonify(status="ok")


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
    return jsonify(status="ok")


@app.route("/api/messages/push", methods=["POST"])
def _push_message() -> Response:
    """Receive a message from the agentscope application, and display it on
    the web UI."""
    data = request.json

    run_id = data["run_id"]
    name = data["name"]
    role = data["role"]
    content = data["content"]
    metadata = json.dumps(data["metadata"])
    timestamp = data["timestamp"]
    url = data["url"]

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
    return jsonify(status="ok")


@app.route("/api/messages/run/<run_id>", methods=["GET"])
def get_messages(run_id: str) -> Response:
    """Get the history messages of specific run_id."""

    print("Require messages from " + run_id)

    # From registered runtime instances
    if len(Run.query.filter_by(run_id=run_id).all()) >= 0:
        messages = Message.query.filter_by(run_id=run_id).all()
        msgs = [
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
        return jsonify(msgs)

    # From the local file
    run_dir = request.args.get("run_dir", default=None, type=str)

    # Search the run_dir from the registered runtime instances if not provided
    if run_dir is None:
        runtime_configs_from_dir = _get_all_runs_from_dir()
        if run_id in runtime_configs_from_dir.keys():
            run_dir = runtime_configs_from_dir[run_id]["run_dir"]

    # Load the messages from the local file
    path_messages = os.path.join(run_dir, "logging.chat")
    if run_dir is None or not os.path.exists(path_messages):
        return jsonify([])
    else:
        with open(path_messages, "r") as file:
            msgs = [json.loads(_) for _ in file.readlines()]
            return jsonify(msgs)


@app.route("/api/runs/all", methods=["GET"])
def _get_all_runs() -> Response:
    """Get all runs."""
    # From directory
    runtime_configs_from_dir = _get_all_runs_from_dir()

    # From web connection
    runtime_configs_from_register = {_.run_id: {
        "run_id": _.run_id,
        "project": _.project,
        "name": _.name,
        "timestamp": _.timestamp,
        "run_dir": _.run_dir,
        "pid": _.pid,
        "status": _.status,
    } for _ in Run.query.all()}

    # Remove duplicates between two sources
    clean_runtimes = {**runtime_configs_from_dir, **runtime_configs_from_register}

    runs = list(clean_runtimes.values())

    return jsonify(runs)


# TODO: what's this for?
@app.route("/api/runs/new", methods=["GET"])
def get_available_run_id() -> Response:
    """Get an available run id."""
    return jsonify({"run_id": uuid.uuid4().hex})


@app.route("/api/invocation", methods=["GET"])
def get_invocations() -> Response:
    """Get all API invocations in a run instance."""
    run_dir = request.args.get("run_dir")
    print(run_dir)

    path_invocations = os.path.join(run_dir, _DEFAULT_SUBDIR_INVOKE)

    invocations = []
    if os.path.exists(path_invocations):
        for filename in os.listdir(path_invocations):
            with open(os.path.join(path_invocations, filename), "r") as file:
                invocations.append(json.load(file))
    return jsonify(invocations)


@app.route("/api/code", methods=["GET"])
def get_code() -> Response:
    """Get the python code from the run directory."""
    run_dir = request.args.get("run_dir")

    dir_code = os.path.join(run_dir, _DEFAULT_SUBDIR_CODE)

    codes = {}
    if os.path.exists(dir_code):
        for filename in os.listdir(dir_code):
            with open(os.path.join(dir_code, filename), "r") as file:
                codes[filename] = "".join(file.readlines())
    return jsonify(codes)


@app.route("/api/file", methods=["GET"])
def get_file() -> Response:
    """Get the local file via the url."""
    file_path = request.args.get("path", None)

    if file_path is not None:
        try:
            file = send_file(file_path)
            return file
        except FileNotFoundError:
            return jsonify({"error": "File not found."})


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


@socketio.on("request_user_input")
def request_user_input(data: dict) -> None:
    """Request user input"""
    print("request user input")
    run_id = data["run_id"]
    name = data["name"]
    agent_id = data["agent_id"]
    require_url = data["require_url"]
    required_keys = data["required_keys"]

    db.session.query(Run).filter_by(run_id=run_id).update({"status": "waiting"})
    db.session.commit()

    print(Run.query.filter_by(run_id=run_id).all())
    print("ALL", Run.query.all())

    # Ask for user input from the web ui
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
    db.session.query(Run).filter_by(run_id=run_id).update({"status": "running"})
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

    # Query if the runtime that is waiting for user input
    runs = Run.query.filter_by(run_id=run_id).all()

    if len(runs) != 0:
        run = runs[0]
        if run.status == "waiting":
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
    run_dirs: Union[str, list[str]] = [],
    cache_dir: str = "",
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
) -> None:
    """Start the web UI."""

    if isinstance(run_dirs, str):
        run_dirs = [run_dirs]

    global _RUNS_DIRS

    _RUNS_DIRS = run_dirs

    with app.app_context():
        db.create_all()

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    init("/Users/david/Downloads/agentscope/examples/game_werewolf/runs", debug=True)
