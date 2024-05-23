# -*- coding: utf-8 -*-
"""The main entry point of the web UI."""
import json
import os
import uuid
from datetime import datetime

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
        print(f"run id {run_id} already exists.")
        abort(400, f"run_id [{run_id}] already exists")
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
    return get_history_messages(run_id=run_id)


@app.route("/api/runs/all", methods=["GET"])
def get_all_runs() -> list:
    """Get all runs."""
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
    file_path = request.args.get("url")
    try:
        file = send_file(file_path)
        return file
    except FileNotFoundError:
        return jsonify({"error": "File not found."})


@app.route("/studio/<run_id>", methods=["GET"])
def studio_page(run_id: str) -> str:
    """Studio page."""
    if Run.query.filter_by(id=run_id).first() is None:
        return jsonify(status="error", msg="run_id not exists")
    messages = Message.query.filter_by(run_id=run_id).all()
    return render_template("chat.html", messages=messages, run_id=run_id)


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
