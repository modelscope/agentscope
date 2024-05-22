# -*- coding: utf-8 -*-
"""run agentscope studio server"""
import argparse
import os
import sys
import threading
import time
from collections import defaultdict
from typing import Optional, Callable
import traceback

from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)


@app.route("/", methods=["GET"])
def index() -> Response:
    """_summary_

    Returns:
        Response: _description_
    """
    return render_template("index.html")
