# -*- coding: utf-8 -*-
"""The client for AgentScope Studio."""
from threading import Event
from typing import Optional, Union
import requests

import socketio
from loguru import logger

from agentscope.message import Msg


class _WebSocketClient:
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
            logger.debug("Establish a websocket connection with Studio.")
            self.sio.emit(
                "join",
                {"run_id": self.run_id, "agent_id": self.agent_id},
            )

        @self.sio.event
        def disconnect() -> None:
            logger.debug("Disconnected the websocket connection from Studio")
            self.sio.emit(
                "leave",
                {"run_id": self.run_id, "agent_id": self.agent_id},
            )

        @self.sio.on("fetch_user_input")
        def on_fetch_user_input(data: dict) -> None:
            self.user_input = data
            self.input_event.set()

        self.sio.connect(f"{self.studio_url}")

    def get_user_input(
        self,
        require_url: bool,
        required_keys: list[str],
    ) -> Optional[dict]:
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
                "require_url": require_url,
                "required_keys": required_keys,
            },
        )
        self.input_event.wait()
        return self.user_input

    def close(self) -> None:
        """Close the websocket connection."""
        self.sio.disconnect()


class StudioClient:
    """A client in AgentScope applications, used to register, push messages to
    an AgentScope Studio backend, and obtain user inputs from the studio."""

    active: bool = False
    """Whether the client is active."""

    studio_url: str = None
    """The URL of the AgentScope Studio."""

    runtime_id: str

    websocket_mapping: dict = {}
    """A mapping of websocket clients to user agents."""

    def initialize(self, runtime_id: str, studio_url: str) -> None:
        """Initialize the client with the studio URL."""
        self.runtime_id = runtime_id
        self.studio_url = studio_url

    def register_running_instance(
        self,
        project: str,
        name: str,
        timestamp: str,
        run_dir: Optional[str],
        pid: int,
    ) -> None:
        """Register a running instance to the AgentScope Studio."""
        url = f"{self.studio_url}/api/runs/register"
        response = requests.post(
            url,
            json={
                "run_id": self.runtime_id,
                "project": project,
                "name": name,
                "timestamp": timestamp,
                "run_dir": run_dir,
                "pid": pid,
            },
            timeout=10,
        )

        if response.status_code == 200:
            self.active = True
            logger.info(
                "Successfully registered to AgentScope Studio.\n"
                "View your application at:\n"
                "\n"
                f"    * {self.get_run_detail_page_url()}\n",
            )
        else:
            raise RuntimeError(f"Fail to register to studio: {response.text}")

    def push_message(
        self,
        message: Msg,
    ) -> None:
        """Push the message to the flask server (studio) for display.

        Args:
            message (`Msg`):
                The message to be pushed.
        """
        send_url = f"{self.studio_url}/api/messages/push"
        response = requests.post(
            send_url,
            json={
                "run_id": self.runtime_id,
                "id": message.id,
                "name": message.name,
                "role": message.role,
                "content": str(message.content),
                "timestamp": message.timestamp,
                "metadata": message.metadata,
                "url": message.url,
            },
            timeout=10,
        )

        if response.status_code != 200:
            logger.error(f"Fail to push message to studio: {response.text}")

    def get_user_input(
        self,
        agent_id: str,
        name: str,
        require_url: bool,
        required_keys: Optional[Union[list[str], str]] = None,
    ) -> dict:
        """Get user input from the studio.

        Args:
            agent_id (`str`):
                The ID of the agent.
            name (`str`):
                The name of the agent.
            require_url (`bool`):
                Whether the input requires a URL.
            required_keys (`Optional[Union[list[str], str]]`, defaults to
            `None`):
                The required keys for the input, which will be combined into a
                dict in the content field.

        Returns:
            `dict`: A dict with the user input and an url if required.
        """

        if agent_id not in self.websocket_mapping:
            self.websocket_mapping[agent_id] = _WebSocketClient(
                self.studio_url,
                self.runtime_id,
                name,
                agent_id,
            )

        return self.websocket_mapping[agent_id].get_user_input(
            require_url=require_url,
            required_keys=required_keys,
        )

    def get_run_detail_page_url(self) -> str:
        """Get the URL of the run detail page."""
        return f"{self.studio_url}/?run_id={self.runtime_id}"

    def alloc_server(self) -> dict:
        """Allocate a list of servers.

        Returns:
            `dict`: A dict with host and port field.
        """
        send_url = f"{self.studio_url}/api/servers/alloc"
        try:
            response = requests.get(
                send_url,
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Fail to allocate servers: {e}")
            return {}
        if response.status_code != 200:
            logger.error(f"Fail to allocate servers: {response.text}")
            return {}
        return response.json()

    def flush(self) -> None:
        """Flush the client."""
        self.studio_url = None
        self.active = False
        self.websocket_mapping = {}

    def state_dict(self) -> dict:
        """Serialize the client."""
        return {
            "active": self.active,
            "studio_url": self.studio_url,
        }

    def load_dict(self, data: dict) -> None:
        """Load the client from a dictionary."""
        assert "active" in data, "Key `active` not found in data."
        assert "studio_url" in data, "Key `studio_url` not found in data."

        self.active = data["active"]
        self.studio_url = data["studio_url"]


_studio_client = StudioClient()
