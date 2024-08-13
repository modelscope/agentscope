# -*- coding: utf-8 -*-
"""The Web Server of the AgentScope Studio."""
import json
import os
import re
import subprocess
import tempfile
import threading
import traceback
from datetime import datetime
from typing import Tuple, Union, Any, Optional
from pathlib import Path
from random import choice

from flask import (
    Flask,
    request,
    jsonify,
    session,
    render_template,
    Response,
    abort,
    send_file,
)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room

from ..constants import (
    _DEFAULT_SUBDIR_CODE,
    _DEFAULT_SUBDIR_INVOKE,
    FILE_SIZE_LIMIT,
    FILE_COUNT_LIMIT,
)
from ._studio_utils import _check_and_convert_id_type
from ..utils.tools import (
    _is_process_alive,
    _is_windows,
    _generate_new_runtime_id,
)
from ..rpc.rpc_agent_client import RpcAgentClient


_app = Flask(__name__)

# Set the cache directory
_cache_dir = Path.home() / ".cache" / "agentscope-studio"
_cache_db = _cache_dir / "agentscope.db"
os.makedirs(str(_cache_dir), exist_ok=True)

if _is_windows():
    _app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{str(_cache_db)}"
else:
    _app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:////{str(_cache_db)}"

_db = SQLAlchemy(_app)

_socketio = SocketIO(_app)

# This will enable CORS for all routes
CORS(_app)

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


class _RunTable(_db.Model):  # type: ignore[name-defined]
    """Runtime object."""

    run_id = _db.Column(_db.String, primary_key=True)
    project = _db.Column(_db.String)
    name = _db.Column(_db.String)
    timestamp = _db.Column(_db.String)
    run_dir = _db.Column(_db.String)
    pid = _db.Column(_db.Integer)
    status = _db.Column(_db.String, default="finished")


class _ServerTable(_db.Model):  # type: ignore[name-defined]
    """Server object."""

    id = _db.Column(_db.String, primary_key=True)
    host = _db.Column(_db.String)
    port = _db.Column(_db.Integer)
    create_time = _db.Column(_db.DateTime, default=datetime.now)


class _MessageTable(_db.Model):  # type: ignore[name-defined]
    """Message object."""

    id = _db.Column(_db.String, primary_key=True)
    run_id = _db.Column(
        _db.String,
        _db.ForeignKey("run_table.run_id"),
        nullable=False,
    )
    name = _db.Column(_db.String)
    role = _db.Column(_db.String)
    content = _db.Column(_db.String)
    url = _db.Column(_db.String)
    meta = _db.Column(_db.String)
    timestamp = _db.Column(_db.String)


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


def _remove_file_paths(error_trace: str) -> str:
    """
    Remove the real traceback when exception happens.
    """
    path_regex = re.compile(r'File "(.*?)(?=agentscope|app\.py)')
    cleaned_trace = re.sub(path_regex, 'File "[hidden]/', error_trace)

    return cleaned_trace


def _convert_to_py(  # type: ignore[no-untyped-def]
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
        return "False", _remove_file_paths(
            f"Error: {e}\n\n" f"Traceback:\n" f"{traceback.format_exc()}",
        )


@_app.route("/workstation")
def _workstation() -> str:
    """Render the workstation page."""
    return render_template("workstation.html")


@_app.route("/api/runs/register", methods=["POST"])
def _register_run() -> Response:
    """Registers a running instance of an agentscope application."""

    # Extract the input data from the request
    data = request.json
    run_id = data.get("run_id")

    # check if the run_id is already in the database
    if _RunTable.query.filter_by(run_id=run_id).first():
        abort(400, f"RUN_ID {run_id} already exists")

    # Add into the database
    _db.session.add(
        _RunTable(
            run_id=run_id,
            project=data.get("project"),
            name=data.get("name"),
            timestamp=data.get("timestamp"),
            run_dir=data.get("run_dir"),
            pid=data.get("pid"),
            status="running",
        ),
    )
    _db.session.commit()

    return jsonify(status="ok")


@_app.route("/api/servers/register", methods=["POST"])
def _register_server() -> Response:
    """
    Registers an agent server.
    """
    data = request.json
    server_id = data.get("server_id")
    host = data.get("host")
    port = data.get("port")

    if _ServerTable.query.filter_by(id=server_id).first():
        _app.logger.error(f"Server id {server_id} already exists.")
        abort(400, f"run_id [{server_id}] already exists")

    _db.session.add(
        _ServerTable(id=server_id, host=host, port=port),
    )
    _db.session.commit()

    _app.logger.info(f"Register server id {server_id}")
    return jsonify(status="ok")


@_app.route("/api/servers/all", methods=["GET"])
def _get_all_servers() -> Response:
    """Get all servers."""
    servers = _ServerTable.query.all()

    return jsonify(
        [
            {
                "id": server.id,
                "host": server.host,
                "port": server.port,
                "create_time": server.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                ),
            }
            for server in servers
        ],
    )


@_app.route("/api/servers/status/<server_id>", methods=["GET"])
def _get_server_status(server_id: str) -> Response:
    server = _ServerTable.query.filter_by(id=server_id).first()
    status = RpcAgentClient(
        host=server.host,
        port=server.port,
    ).get_server_info()
    if not status or status["id"] != server_id:
        return jsonify({"status": "dead"})
    else:
        return jsonify(
            {
                "status": "running",
                "cpu": status["cpu"],
                "mem": status["mem"],
                "size": status["size"],
            },
        )


@_app.route("/api/servers/delete", methods=["POST"])
def _delete_server() -> Response:
    server_id = request.json.get("server_id")
    stop_server = request.json.get("stop", False)
    server = _ServerTable.query.filter_by(id=server_id).first()
    if stop_server:
        RpcAgentClient(host=server.host, port=server.port).stop()
    _ServerTable.query.filter_by(id=server_id).delete()
    _db.session.commit()
    return jsonify({"status": "ok"})


@_app.route("/api/servers/agent_info/<server_id>", methods=["GET"])
def _get_server_agent_info(server_id: str) -> Response:
    _app.logger.info(f"Get info of server [{server_id}]")
    server = _ServerTable.query.filter_by(id=server_id).first()
    agents = RpcAgentClient(
        host=server.host,
        port=server.port,
    ).get_agent_list()
    return jsonify(agents)


@_app.route("/api/servers/agents/delete", methods=["POST"])
def _delete_agent() -> Response:
    server_id = request.json.get("server_id")
    agent_id = request.json.get("agent_id", None)
    server = _ServerTable.query.filter_by(id=server_id).first()
    # delete all agents if agent_id is None
    if agent_id is not None:
        ok = RpcAgentClient(host=server.host, port=server.port).delete_agent(
            agent_id,
        )
    else:
        ok = RpcAgentClient(
            host=server.host,
            port=server.port,
        ).delete_all_agent()
    return jsonify(status="ok" if ok else "fail")


@_app.route("/api/servers/agents/memory", methods=["POST"])
def _agent_memory() -> Response:
    server_id = request.json.get("server_id")
    agent_id = request.json.get("agent_id")
    server = _ServerTable.query.filter_by(id=server_id).first()
    mem = RpcAgentClient(host=server.host, port=server.port).get_agent_memory(
        agent_id,
    )
    if isinstance(mem, dict):
        mem = [mem]
    return jsonify(mem)


@_app.route("/api/servers/alloc", methods=["GET"])
def _alloc_server() -> Response:
    # TODO: check the server is still running
    # TODO: support to alloc multiple servers in one call
    # TODO: use hints to decide which server to allocate
    # TODO: allocate based on server's cpu and memory usage
    # currently random select a server
    servers = _ServerTable.query.all()
    server = choice(servers)
    return jsonify(
        {
            "host": server.host,
            "port": server.port,
        },
    )


@_app.route("/api/messages/push", methods=["POST"])
def _push_message() -> Response:
    """Receive a message from the agentscope application, and display it on
    the web UI."""
    _app.logger.debug("Flask: receive push_message")
    data = request.json

    run_id = data["run_id"]
    msg_id = data["id"]
    name = data["name"]
    role = data["role"]
    content = data["content"]
    metadata = data["metadata"]
    timestamp = data["timestamp"]
    url = data["url"]

    # First check if the message exists in the database, if exists, we update
    # it, otherwise, we add it.
    _MessageTable.query.filter_by(id=msg_id).delete()
    _db.session.commit()
    try:
        new_message = _MessageTable(
            id=msg_id,
            run_id=run_id,
            name=name,
            role=role,
            content=content,
            # Before storing into the database, we need to convert the url into
            # a string
            meta=json.dumps(metadata, ensure_ascii=False),
            url=json.dumps(url, ensure_ascii=False),
            timestamp=timestamp,
        )
        _db.session.add(new_message)
        _db.session.commit()
    except Exception as e:
        abort(400, "Fail to put message with error: " + str(e))

    data = {
        "id": msg_id,
        "run_id": run_id,
        "name": name,
        "role": role,
        "content": content,
        "url": url,
        "metadata": metadata,
        "timestamp": timestamp,
    }

    _socketio.emit(
        "display_message",
        data,
        room=run_id,
    )
    _app.logger.debug("Flask: send display_message")
    return jsonify(status="ok")


@_app.route("/api/messages/run/<run_id>", methods=["GET"])
def _get_messages(run_id: str) -> Response:
    """Get the history messages of specific run_id."""
    # From registered runtime instances
    if len(_RunTable.query.filter_by(run_id=run_id).all()) > 0:
        messages = _MessageTable.query.filter_by(run_id=run_id).all()
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
            return jsonify(msgs)


@_app.route("/api/runs/get/<run_id>", methods=["GET"])
def _get_run(run_id: str) -> Response:
    """Get a specific run's detail."""
    run = _RunTable.query.filter_by(run_id=run_id).first()
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


@_app.route("/api/runs/all", methods=["GET"])
def _get_all_runs() -> Response:
    """Get all runs."""
    # Update the status of the registered runtimes
    # Note: this is only for the applications running on the local machine
    for run in _RunTable.query.filter(
        _RunTable.status.in_(["running", "waiting"]),
    ).all():
        if not _is_process_alive(run.pid, run.timestamp):
            _RunTable.query.filter_by(run_id=run.run_id).update(
                {"status": "finished"},
            )
            _db.session.commit()

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
        for _ in _RunTable.query.all()
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


@_app.route("/api/invocation", methods=["GET"])
def _get_invocations() -> Response:
    """Get all API invocations in a run instance."""
    run_dir = request.args.get("run_dir")
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


@_app.route("/api/code", methods=["GET"])
def _get_code() -> Response:
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


@_app.route("/api/file", methods=["GET"])
def _get_file() -> Any:
    """Get the local file via the url."""
    file_path = request.args.get("path", None)

    if file_path is not None:
        try:
            file = send_file(file_path)
            return file
        except FileNotFoundError:
            return jsonify({"error": "File not found."})
    return jsonify({"error": "File not found."})


@_app.route("/convert-to-py", methods=["POST"])
def _convert_config_to_py() -> Response:
    """
    Convert json config to python code and send back.
    """
    content = request.json.get("data")
    status, py_code = _convert_to_py(content)
    return jsonify(py_code=py_code, is_success=status)


def _cleanup_process(proc: subprocess.Popen) -> None:
    """Clean up the process for running application started by workstation."""
    proc.wait()
    _app.logger.debug(f"The process with pid {proc.pid} is closed")


@_app.route("/convert-to-py-and-run", methods=["POST"])
def _convert_config_to_py_and_run() -> Response:
    """
    Convert json config to python code and run.
    """
    content = request.json.get("data")
    studio_url = request.url_root.rstrip("/")
    run_id = _generate_new_runtime_id()
    status, py_code = _convert_to_py(
        content,
        runtime_id=run_id,
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
                proc = subprocess.Popen(  # pylint: disable=R1732
                    ["python", tmp.name],
                )
                threading.Thread(target=_cleanup_process, args=(proc,)).start()
        except Exception as e:
            status, py_code = "False", _remove_file_paths(
                f"Error: {e}\n\n" f"Traceback:\n" f"{traceback.format_exc()}",
            )
    return jsonify(py_code=py_code, is_success=status, run_id=run_id)


@_app.route("/read-examples", methods=["POST"])
def _read_examples() -> Response:
    """
    Read tutorial examples from local file.
    """
    lang = request.json.get("lang")
    file_index = request.json.get("data")

    if not os.path.exists(
        os.path.join(
            _app.root_path,
            "static",
            "workstation_templates",
            f"{lang}{file_index}.json",
        ),
    ):
        lang = "en"

    with open(
        os.path.join(
            _app.root_path,
            "static",
            "workstation_templates",
            f"{lang}{file_index}.json",
        ),
        "r",
        encoding="utf-8",
    ) as jf:
        data = json.load(jf)
    return jsonify(json=data)


@_app.route("/save-workflow", methods=["POST"])
def _save_workflow() -> Response:
    """
    Save the workflow JSON data to the local user folder.
    """
    user_login = session.get("user_login", "local_user")
    user_dir = os.path.join(_cache_dir, user_login)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    data = request.json
    overwrite = data.get("overwrite", False)
    filename = data.get("filename")
    workflow_str = data.get("workflow")
    if not filename:
        return jsonify({"message": "Filename is required"})

    filepath = os.path.join(user_dir, f"{filename}.json")

    try:
        workflow = json.loads(workflow_str)
        if not isinstance(workflow, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        return jsonify({"message": "Invalid workflow data"})

    workflow_json = json.dumps(workflow, ensure_ascii=False, indent=4)
    if len(workflow_json.encode("utf-8")) > FILE_SIZE_LIMIT:
        return jsonify(
            {
                "message": f"The workflow file size exceeds "
                f"{FILE_SIZE_LIMIT/(1024*1024)} MB limit",
            },
        )

    user_files = [
        f
        for f in os.listdir(user_dir)
        if os.path.isfile(os.path.join(user_dir, f))
    ]

    if len(user_files) >= FILE_COUNT_LIMIT and not os.path.exists(filepath):
        return jsonify(
            {
                "message": f"You have reached the limit of "
                f"{FILE_COUNT_LIMIT} workflow files, please "
                f"delete some files.",
            },
        )

    if overwrite:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(workflow, f, ensure_ascii=False, indent=4)
    else:
        if os.path.exists(filepath):
            return jsonify({"message": "Workflow file exists!"})
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(workflow, f, ensure_ascii=False, indent=4)

    return jsonify({"message": "Workflow file saved successfully"})


@_app.route("/delete-workflow", methods=["POST"])
def _delete_workflow() -> Response:
    """
    Deletes a workflow JSON file from the user folder.
    """
    user_login = session.get("user_login", "local_user")
    user_dir = os.path.join(_cache_dir, user_login)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    data = request.json
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Filename is required"})

    filepath = os.path.join(user_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"})

    try:
        os.remove(filepath)
        return jsonify({"message": "Workflow file deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})


@_app.route("/list-workflows", methods=["POST"])
def _list_workflows() -> Response:
    """
    Get all workflow JSON files in the user folder.
    """
    user_login = session.get("user_login", "local_user")
    user_dir = os.path.join(_cache_dir, user_login)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    files = [file for file in os.listdir(user_dir) if file.endswith(".json")]
    return jsonify(files=files)


@_app.route("/load-workflow", methods=["POST"])
def _load_workflow() -> Response:
    """
    Reads and returns workflow data from the specified JSON file.
    """
    user_login = session.get("user_login", "local_user")
    user_dir = os.path.join(_cache_dir, user_login)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    data = request.json
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    filepath = os.path.join(user_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    with open(filepath, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    return jsonify(json_data)


@_app.route("/")
def _home() -> str:
    """Render the home page."""
    return render_template("index.html")


@_socketio.on("request_user_input")
def _request_user_input(data: dict) -> None:
    """Request user input"""
    _app.logger.debug("Flask: receive request_user_input")

    run_id = data["run_id"]
    agent_id = data["agent_id"]

    # Change the status into waiting
    _db.session.query(_RunTable).filter_by(run_id=run_id).update(
        {"status": "waiting"},
    )
    _db.session.commit()

    # Record into the queue
    _UserInputRequestQueue.add_request(run_id, agent_id, data)

    # Ask for user input from the web ui
    _socketio.emit(
        "enable_user_input",
        data,
        room=run_id,
    )

    _app.logger.debug("Flask: send enable_user_input")


@_socketio.on("user_input_ready")
def _user_input_ready(data: dict) -> None:
    """Get user input and send to the agent"""
    _app.logger.debug(f"Flask: receive user_input_ready: {data}")

    run_id = data["run_id"]
    agent_id = data["agent_id"]
    content = data["content"]
    url = data["url"]

    _db.session.query(_RunTable).filter_by(run_id=run_id).update(
        {"status": "running"},
    )
    _db.session.commit()

    # Return to AgentScope application
    _socketio.emit(
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
        _socketio.emit(
            "enable_user_input",
            new_request,
            room=run_id,
        )

    _app.logger.debug("Flask: send fetch_user_input")


@_socketio.on("connect")
def _on_connect() -> None:
    """Execute when a client is connected."""
    _app.logger.info("New client connected")


@_socketio.on("disconnect")
def _on_disconnect() -> None:
    """Execute when a client is disconnected."""
    _app.logger.info("Client disconnected")


@_socketio.on("join")
def _on_join(data: dict) -> None:
    """Join a websocket room"""
    run_id = data["run_id"]
    join_room(run_id)

    new_request = _UserInputRequestQueue.fetch_a_request(run_id)
    if new_request is not None:
        _socketio.emit(
            "enable_user_input",
            new_request,
            room=run_id,
        )


@_socketio.on("leave")
def _on_leave(data: dict) -> None:
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
    with _app.app_context():
        _db.create_all()

    if debug:
        _app.logger.setLevel("DEBUG")
    else:
        _app.logger.setLevel("INFO")

    # To be compatible with the old table schema, we need to check and convert
    # the id column of the message_table from INTEGER to VARCHAR.
    _check_and_convert_id_type(str(_cache_db), "message_table")

    _socketio.run(
        _app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
