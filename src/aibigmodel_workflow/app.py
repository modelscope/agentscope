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
from loguru import logger
import sqlite3

_app = Flask(__name__)

# Set the cache directory
_cache_dir = Path.home() / ".cache" / "agentscope-studio"
_cache_db = _cache_dir / "agentscope.db"
os.makedirs(str(_cache_dir), exist_ok=True)

def _check_and_convert_id_type(db_path: str, table_name: str) -> None:
    """Check and convert the type of the 'id' column in the specified table
    from INTEGER to VARCHAR.

    Args:
        db_path (str): The path of the SQLite database file.
        table_name (str): The name of the table to be checked and converted.
    """

    if not os.path.exists(db_path):
        return

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Obtain the table structure information
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        # Look for the type of the 'id' column
        id_column = [col for col in columns if col[1] == "id"]
        if not id_column:
            return

        id_type = id_column[0][2].upper()
        if id_type in ["VARCHAR", "TEXT"]:
            return

        if id_type == "INTEGER":
            # Temporary table name
            temp_table_name = table_name + "_temp"

            # Create a new table and change the type of the 'id' column to
            # VARCHAR
            create_table_sql = f"CREATE TABLE {temp_table_name} ("
            for col in columns:
                col_type = "VARCHAR" if col[1] == "id" else col[2]
                create_table_sql += f"{col[1]} {col_type}, "
            create_table_sql = create_table_sql.rstrip(", ") + ");"

            cursor.execute(create_table_sql)

            # Copy data and convert the value of the 'id' column to a string
            column_names = ", ".join([col[1] for col in columns])
            column_values = ", ".join(
                [
                    f"CAST({col[1]} AS VARCHAR)" if col[1] == "id" else col[1]
                    for col in columns
                ],
            )
            cursor.execute(
                f"INSERT INTO {temp_table_name} ({column_names}) "
                f"SELECT {column_values} FROM {table_name};",
            )

            # Delete the old table
            cursor.execute(f"DROP TABLE {table_name};")

            # Rename the new table
            cursor.execute(
                f"ALTER TABLE {temp_table_name} RENAME TO {table_name};",
            )

            conn.commit()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

def _is_windows() -> bool:
    """Check if the system is Windows."""
    return os.name == "nt"

if _is_windows():
    _app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{str(_cache_db)}"
else:
    _app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:////{str(_cache_db)}"

_db = SQLAlchemy(_app)

_socketio = SocketIO(_app)

# This will enable CORS for all routes
CORS(_app)

_RUNS_DIRS = []

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
        logger.info(f"cfg {cfg}")
        return "True", build_dag(cfg).compile(**kwargs)
    except Exception as e:
        return "False", _remove_file_paths(
            f"Error: {e}\n\n" f"Traceback:\n" f"{traceback.format_exc()}",
        )

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
    run_id = _runtime.generate_new_runtime_id()
    logger.info(f"Loading configs from {content}")
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

def init(
    host: str = "127.0.0.1",
    port: int = 5001,
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

    # TODO, 增加全局变量池，方便保存所有入参和出参变量

    _socketio.run(
        _app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    init()

    # 1. 所有节点的入参和出参，统一到一个全局变量池子里，并且初始化时能够正确串联。
    # 2. API节点和python节点的封装和定义，完备代码实现。