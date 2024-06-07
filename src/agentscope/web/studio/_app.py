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
from typing import Tuple, Union, Any, Optional

from appdirs import user_cache_dir
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
from agentscope.utils.tools import _is_process_alive

app = Flask(__name__)

# Set the cache directory
_cache_dir = user_cache_dir(appname="agentscope")
os.makedirs(_cache_dir, exist_ok=True)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"sqlite:////{_cache_dir}/agentscope.db"
db = SQLAlchemy(app)

socketio = SocketIO(app)

# This will enable CORS for all routes
CORS(app)


_RUNS_DIRS = []


class _UserInputRequestQueue:
    """A queue to store the user input requests."""

    _requests = {}
    """The user input requests in the queue."""

    @classmethod
    def add_request(cls, run_id: str, agent_id: str, data: dict) -> None:
        """Add a new user input request into queue.

        Args:
            run_id (`str`):
                The id of the runtime instance.
            agent_id (`str`):
                The id of the agent that requires user input.
            data (`dict`):
                The data of the user input request.
        """
        if run_id not in cls._requests:
            cls._requests[run_id] = {agent_id: data}
        else:
            # We ensure that the agent_id is unique here
            cls._requests[run_id][agent_id] = data

    @classmethod
    def fetch_a_request(cls, run_id: str) -> Optional[dict]:
        """Fetch a user input request from the queue.

        Args:
            run_id (`str`):
                The id of the runtime instance.
        """
        if run_id in cls._requests and len(cls._requests[run_id]) > 0:
            # Fetch the oldest request
            agent_id = list(cls._requests[run_id].keys())[0]
            return cls._requests[run_id][agent_id]
        else:
            return None

    @classmethod
    def close_a_request(cls, run_id: str, agent_id: str) -> None:
        """Close a user input request in the queue.

        Args:
            run_id (`str`):
                The id of the runtime instance.
            agent_id (`str`):
                The id of the agent that requires user input.
        """
        if run_id in cls._requests:
            cls._requests[run_id].pop(agent_id)


class Run(db.Model):  # type: ignore[name-defined]
    """Runtime object."""

    run_id = db.Column(db.String, primary_key=True)
    project = db.Column(db.String)
    name = db.Column(db.String)
    timestamp = db.Column(db.String)
    run_dir = db.Column(db.String)
    pid = db.Column(db.Integer)
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
    if _RUNS_DIRS is not None:
        for runs_dir in set(_RUNS_DIRS):
            for runtime_dir in os.listdir(runs_dir):
                path_runtime = os.path.join(runs_dir, runtime_dir)
                path_config = os.path.join(path_runtime, ".config")
                if os.path.exists(path_config):
                    with open(path_config, "r", encoding="utf-8") as file:
                        runtime_config = json.load(file)

                        # Default status is finished
                        # Note: this is only for local runtime instances
                        if "pid" in runtime_config and _is_process_alive(
                            runtime_config["pid"],
                            runtime_config["timestamp"],
                        ):
                            runtime_config["status"] = "running"
                        else:
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
    print("Flask: receive push_message")
    data = request.json

    run_id = data["run_id"]
    name = data["name"]
    role = data["role"]
    content = data["content"]
    metadata = json.dumps(data["metadata"])
    timestamp = data["timestamp"]
    url = json.dumps(data["url"])

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
    print("Flask: send display_message")
    return jsonify(status="ok")


@app.route("/api/messages/run/<run_id>", methods=["GET"])
def get_messages(run_id: str) -> Response:
    """Get the history messages of specific run_id."""

    print("Require messages from " + run_id)

    # From registered runtime instances
    if len(Run.query.filter_by(run_id=run_id).all()) > 0:
        messages = Message.query.filter_by(run_id=run_id).all()
        msgs = [
            {
                "name": message.name,
                "role": message.role,
                "content": message.content,
                "url": json.loads(message.url),
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
        if run_id in runtime_configs_from_dir:
            run_dir = runtime_configs_from_dir[run_id]["run_dir"]

    # Load the messages from the local file
    path_messages = os.path.join(run_dir, "logging.chat")
    if run_dir is None or not os.path.exists(path_messages):
        return jsonify([])
    else:
        with open(path_messages, "r", encoding="utf-8") as file:
            msgs = [json.loads(_) for _ in file.readlines()]
            print(msgs)
            return jsonify(msgs)


@app.route("/api/runs/get/<run_id>", methods=["GET"])
def get_run(run_id: str) -> Response:
    """Get a specific run's detail."""
    run = Run.query.filter_by(run_id=run_id).first()
    if not run:
        abort(400, f"run_id [{run_id}] not exists")
    return jsonify(
        {
            "run_id": run.run_id,
            "project": run.project,
            "name": run.name,
            "timestamp": run.timestamp,
            "run_dir": run.run_dir,
            "pid": run.pid,
            "status": run.status,
        },
    )


@app.route("/api/runs/all", methods=["GET"])
def _get_all_runs() -> Response:
    """Get all runs."""
    # Update the status of the registered runtimes
    # Note: this is only for the applications running on the local machine
    for run in Run.query.filter(Run.status.in_(["running", "waiting"])).all():
        if not _is_process_alive(run.pid, run.timestamp):
            Run.query.filter_by(run_id=run.run_id).update(
                {"status": "finished"},
            )
            db.session.commit()

    # From web connection
    runtime_configs_from_register = {
        _.run_id: {
            "run_id": _.run_id,
            "project": _.project,
            "name": _.name,
            "timestamp": _.timestamp,
            "run_dir": _.run_dir,
            "pid": _.pid,
            "status": _.status,
        }
        for _ in Run.query.all()
    }

    # From directory
    runtime_configs_from_dir = _get_all_runs_from_dir()

    # Remove duplicates between two sources
    clean_runtimes = {
        **runtime_configs_from_dir,
        **runtime_configs_from_register,
    }

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
            with open(
                os.path.join(path_invocations, filename),
                "r",
                encoding="utf-8",
            ) as file:
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
            with open(
                os.path.join(dir_code, filename),
                "r",
                encoding="utf-8",
            ) as file:
                codes[filename] = "".join(file.readlines())
    return jsonify(codes)


@app.route("/api/file", methods=["GET"])
def get_file() -> Any:
    """Get the local file via the url."""
    file_path = request.args.get("path", None)

    if file_path is not None:
        try:
            file = send_file(file_path)
            return file
        except FileNotFoundError:
            return jsonify({"error": "File not found."})
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
    print("Flask: receive request_user_input")
    run_id = data["run_id"]
    agent_id = data["agent_id"]

    # Change the status into waiting
    db.session.query(Run).filter_by(run_id=run_id).update(
        {"status": "waiting"},
    )
    db.session.commit()

    # Record into the queue
    _UserInputRequestQueue.add_request(run_id, agent_id, data)

    # Ask for user input from the web ui
    socketio.emit(
        "enable_user_input",
        data,
        room=run_id,
    )

    print("Flask: send enable_user_input")


@socketio.on("user_input_ready")
def user_input_ready(data: dict) -> None:
    """Get user input and send to the agent"""
    print("Flask: receive user_input_ready")

    run_id = data["run_id"]
    agent_id = data["agent_id"]
    content = data["content"]
    url = data["url"]

    db.session.query(Run).filter_by(run_id=run_id).update(
        {"status": "running"},
    )
    db.session.commit()

    # Return to AgentScope application
    socketio.emit(
        "fetch_user_input",
        {
            "agent_id": agent_id,
            "name": data["name"],
            "run_id": run_id,
            "content": content,
            "url": None if url in ["", []] else url,
        },
        room=run_id,
    )

    # Close the request in the queue
    _UserInputRequestQueue.close_a_request(run_id, agent_id)

    # Fetch a new user input request for this run_id if exists
    new_request = _UserInputRequestQueue.fetch_a_request(run_id)
    if new_request is not None:
        socketio.emit(
            "enable_user_input",
            new_request,
            room=run_id,
        )

    print("Flask: send fetch_user_input")


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

    new_request = _UserInputRequestQueue.fetch_a_request(run_id)
    if new_request is not None:
        socketio.emit(
            "enable_user_input",
            new_request,
            room=run_id,
        )


@socketio.on("leave")
def on_leave(data: dict) -> None:
    """Leave a websocket room"""
    run_id = data["run_id"]
    leave_room(run_id)


def init(
    host: str = "127.0.0.1",
    port: int = 5000,
    run_dirs: Optional[Union[str, list[str]]] = None,
    debug: bool = False,
) -> None:
    """Start the AgentScope Studio web UI with the given configurations.

    Args:
        host (str, optional):
            The host of the web UI. Defaults to "127.0.0.1"
        port (int, optional):
            The port of the web UI. Defaults to 5000.
        run_dirs (`Optional[Union[str, list[str]]]`, defaults to `None`):
            The directories to search for the history of runtime instances.
        debug (`bool`, optional):
            Whether to enable the debug mode. Defaults to False.
    """

    # Set the history directories
    if isinstance(run_dirs, str):
        run_dirs = [run_dirs]

    global _RUNS_DIRS
    _RUNS_DIRS = run_dirs

    # Create the cache directory
    with app.app_context():
        db.create_all()

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
