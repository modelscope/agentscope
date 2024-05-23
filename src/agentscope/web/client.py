# -*- coding: utf-8 -*-
"""The client for agentscope platform."""
from threading import Event
from typing import Optional
import atexit
import requests

import socketio
from loguru import logger


class WebSocketClient:
    """WebSocket Client of AgentScope Studio, only used to obtain
    input messages from users."""

    def __init__(
        self,
        studio_url: str,
        run_id: str,
        name: str,
        agent_id: str,
    ) -> None:
        self.studio_url = studio_url
        self.run_id = run_id
        self.name = name
        self.agent_id = agent_id
        self.user_input = None
        self.sio = socketio.Client()
        self.input_event = Event()

        @self.sio.event
        def connect() -> None:
            logger.info("Connected to Studio")
            self.sio.emit("join", {"run_id": self.run_id})

        @self.sio.event
        def disconnect() -> None:
            logger.info("Disconnected from Studio")
            self.sio.emit("leave", {"run_id": self.run_id})

        @self.sio.on("fetch_user_input")
        def on_fetch_user_input(data: dict) -> None:
            self.user_input = data
            self.input_event.set()

        self.sio.connect(f"{self.studio_url}")

    def get_user_input(self) -> Optional[dict]:
        """Get user input from studio in real-time.

        Note:
            Only agents that requires user inputs should call this function.
            Calling this function will block the calling thread until the user
            input is received.
        """
        self.input_event.clear()
        self.sio.emit(
            "request_user_input",
            {
                "run_id": self.run_id,
                "name": self.name,
                "agent_id": self.agent_id,
            },
        )
        self.input_event.wait()
        return self.user_input

    def close(self) -> None:
        """Close the websocket connection."""
        self.sio.disconnect()


class HttpClient:
    """HTTP client for the AgentScope Studio, used to handle interactions with
    the Studio except for the user input (which need websocket connections)."""

    def __init__(
        self,
        studio_url: str,
        run_id: str,
    ) -> None:
        self.studio_url = studio_url
        self.run_id = run_id

    def generate_user_input_client(
        self,
        name: str,
        agent_id: str,
    ) -> WebSocketClient:
        """Generate a websocket client for a specifc user agent."""
        return WebSocketClient(
            self.studio_url,
            self.run_id,
            name=name,
            agent_id=agent_id,
        )

    def register_run(
        self,
        project: str,
        name: str,
        run_dir: str,
    ) -> bool:
        """Register a run to the AgentScope Studio."""
        url = f"{self.studio_url}/api/runs/register"
        resp = requests.post(
            url,
            json={
                "run_id": self.run_id,
                "project": project,
                "name": name,
                "run_dir": run_dir,
            },
            timeout=10,  # todo: configurable timeout
        )
        if resp.status_code != 200:
            logger.error(f"Fail to register to studio: {resp.text}")
            raise RuntimeError(f"Fail to register to studio: {resp.text}")

        def finish_run() -> None:
            requests.post(
                f"{self.studio_url}/api/runs/finish",
                json={"run_id": self.run_id},
                timeout=5,
            )

        atexit.register(finish_run)
        return True

    def send_message(
        self,
        name: str,
        role: str,
        content: str,
        timestamp: str = None,
        metadata: dict = None,
        url: str = None,
    ) -> bool:
        """Send a message to the studio."""
        send_url = f"{self.studio_url}/api/messages/put"
        resp = requests.post(
            send_url,
            json={
                "run_id": self.run_id,
                "name": name,
                "role": role,
                "content": content,
                "timestamp": timestamp,
                "metadata": metadata,
                "url": url,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        else:
            logger.error(f"Fail to send message to studio: {resp.text}")
            return False