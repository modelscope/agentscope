# -*- coding: utf-8 -*-
"""The user input module."""
import time
from abc import ABC, abstractmethod
from queue import Queue
from threading import Event
from typing import Optional, Any

import json5
import jsonschema
import requests
import shortuuid
import socketio
from loguru import logger
from pydantic import BaseModel

from ..message import ContentBlock, TextBlock


class UserInputData(BaseModel):
    """The user input data."""

    blocks_input: Optional[list[ContentBlock]] = None
    """The text input from the user."""

    structured_input: Optional[dict[str, Any]] = None
    """The structured input from the user."""


class UserInputBase(ABC):
    """The base class for user input."""

    @abstractmethod
    def __call__(
        self,
        agent_id: str,
        agent_name: str,
        *args: Any,
        structured_schema: Optional[BaseModel] = None,
        **kwargs: dict,
    ) -> UserInputData:
        """The input method.

        Args:
            agent_id (`str`):
                The identity of the agent.
            agent_name (`str`):
                The name of the agent.
            structured_schema (`Optional[BaseModel]`, defaults to `None`):
                The base model class of the structured input.

        Returns:
            `UserInputData`:
                The user input data.
        """


class StudioUserInput(UserInputBase):
    """The agentscope studio user input."""

    _websocket_namespace: str = "/python"

    def __init__(
        self,
        studio_url: str,
        run_id: str,
        max_retries: int = 3,
        reconnect_attempts: int = 3,
        reconnection_delay: int = 1,
        reconnection_delay_max: int = 5,
    ) -> None:
        """Initialize the StudioUserInput object.

        Args:
            studio_url (`str`):
                The URL of the AgentScope Studio.
            run_id (`str`):
                The current run identity.
            max_retries (`int`, defaults to `3`):
                The maximum number of retries to get user input.
        """
        self._is_connected = False
        self._is_reconnecting = False

        self.studio_url = studio_url
        self.run_id = run_id
        self.max_retries = max_retries

        # Init Websocket
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=reconnect_attempts,
            reconnection_delay=reconnection_delay,
            reconnection_delay_max=reconnection_delay_max,
        )
        self.input_queues = {}
        self.input_events = {}

        @self.sio.on("connect", namespace=self._websocket_namespace)
        def on_connect() -> None:
            self._is_connected = True
            logger.info(
                f"Connected to AgentScope Studio at {self.studio_url} with "
                f"run_id {run_id}",
            )

        @self.sio.on("disconnect", namespace=self._websocket_namespace)
        def on_disconnect() -> None:
            self._is_connected = False
            logger.info(
                f"Disconnected from AgentScope Studio at {self.studio_url}",
            )

        @self.sio.on("reconnect", namespace=self._websocket_namespace)
        def on_reconnect(attempt_number: int) -> None:
            self._is_connected = True
            self._is_reconnecting = False
            logger.info(
                f"Reconnected to AgentScope Studio at {self.studio_url} "
                f"with run_id {self.run_id} after {attempt_number} attempts",
            )

        @self.sio.on("reconnect_attempt", namespace=self._websocket_namespace)
        def on_reconnect_attempt(attempt_number: int) -> None:
            self._is_reconnecting = True
            logger.info(
                f"Attempting to reconnect to AgentScope Studio at "
                f"{self.studio_url} (attempt {attempt_number})",
            )

        @self.sio.on("reconnect_failed", namespace=self._websocket_namespace)
        def on_reconnect_failed() -> None:
            self._is_reconnecting = False
            logger.error(
                f"Failed to reconnect to AgentScope "
                f"Studio at {self.studio_url}",
            )

        @self.sio.on("reconnect_error", namespace=self._websocket_namespace)
        def on_reconnect_error(error: Any) -> None:
            logger.error(
                "Error while reconnecting to AgentScope Studio at "
                f"{self.studio_url}: {str(error)}",
            )

        # The AgentScope Studio backend send the "sendUserInput" event to
        # the current python run
        @self.sio.on("forwardUserInput", namespace=self._websocket_namespace)
        def receive_user_input(
            request_id: str,
            blocks_input: list[ContentBlock],
            structured_input: dict[str, Any],
        ) -> None:
            if request_id in self.input_queues:
                self.input_queues[request_id].put(
                    UserInputData(
                        blocks_input=blocks_input,
                        structured_input=structured_input,
                    ),
                )
                self.input_events[request_id].set()

        try:
            self.sio.connect(
                f"{self.studio_url}",
                namespaces=["/python"],
                auth={"run_id": self.run_id},
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to AgentScope Studio at {self.studio_url}",
            ) from e

    def _ensure_connected(
        self,
        timeout: float = 30.0,
        check_interval: float = 5.0,
    ) -> None:
        """Ensure the connection is established or wait for reconnection.

        Args:
            timeout (`float`):
                Maximum time to wait for reconnection in seconds. Defaults
                to 30.0.
            check_interval (`float`):
                Interval between connection checks in seconds. Defaults to 1.0.

        Raises:
            `RuntimeError`:
                If connection cannot be established within timeout.
        """
        if self._is_connected:
            return

        if self._is_reconnecting:
            start_time = time.time()
            while self._is_reconnecting:
                # Check timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    raise RuntimeError(
                        "Reconnection timeout after "
                        f"{elapsed_time:.1f} seconds",
                    )

                # Log status
                logger.info(
                    "Waiting for reconnection... "
                    f"({elapsed_time:.1f}s / {timeout}s)",
                )

                # Wait for next check
                time.sleep(check_interval)

            # After reconnection attempt completed, check final status
            if self._is_connected:
                return

        # Not connected and not reconnecting
        raise RuntimeError(
            f"Not connected to AgentScope Studio at {self.studio_url}",
        )

    def __call__(  # type: ignore[override]
        self,
        agent_id: str,
        agent_name: str,
        *args: Any,
        structured_schema: Optional[BaseModel] = None,
    ) -> UserInputData:
        """Get the user input from AgentScope Studio.

        Args:
            agent_id (`str`):
                The identity of the agent.
            agent_name (`str`):
                The name of the agent.
            structured_schema (`Optional[BaseModel]`, defaults to `None`):
                The base model class of the structured input.

        Raises:
            `RuntimeError`:
                Failed to get user input from AgentScope Studio.

        Returns:
            `UserInputData`:
                The user input.
        """
        self._ensure_connected()

        request_id = shortuuid.uuid()

        self.input_queues[request_id] = Queue()
        self.input_events[request_id] = Event()

        n_retry = 0
        while True:
            try:
                response = requests.post(
                    f"{self.studio_url}/trpc/requestUserInput",
                    json={
                        "requestId": request_id,
                        "runId": self.run_id,
                        "agentId": agent_id,
                        "agentName": agent_name,
                        "structuredInput": structured_schema,
                    },
                )
                response.raise_for_status()
                break
            except Exception as e:
                if n_retry < self.max_retries:
                    n_retry += 1
                    continue

                raise RuntimeError(
                    "Failed to get user input from AgentScope Studio",
                ) from e

        try:
            self.input_events[request_id].wait()
            response_data = self.input_queues[request_id].get()
            return response_data

        finally:
            self.input_queues.pop(request_id, None)
            self.input_events.pop(request_id, None)

    def __del__(self) -> None:
        """Cleanup socket connection when object it destroyed"""
        try:
            self.sio.disconnect()
        except Exception as e:
            logger.error(
                f"Failed to disconnect from AgentScope Studio at "
                f"{self.studio_url}: {str(e)}",
            )


class TerminalUserInput(UserInputBase):
    """The terminal user input."""

    def __init__(self, input_prefix: str = "User Input: ") -> None:
        """The terminal user input."""
        self.input_prefix = input_prefix

    def __call__(  # type: ignore[override]
        self,
        agent_id: str,
        agent_name: str,
        *args: Any,
        structured_schema: Optional[BaseModel] = None,
    ) -> UserInputData:
        """The input method for terminal."""

        text_input = input(self.input_prefix)

        structured_input = None
        if structured_schema is not None:
            structured_input = {}

            json_schema = structured_schema.model_json_schema()
            required = json_schema.get("required", [])
            print("Structured input (press Enter to skip for optional):)")

            for key, item in json_schema.get("properties").items():
                requirements = {**item}
                requirements.pop("title")

                while True:
                    res = input(f"\t{key} ({requirements}):")

                    if res == "":
                        if key in required:
                            print(f"Key {key} is required.")
                            continue

                        res = item.get("default", None)

                    if item.get("type").lower() == "integer":
                        res = json5.loads(res)

                    try:
                        jsonschema.validate(res, item)
                        structured_input[key] = res
                        break
                    except jsonschema.ValidationError as e:
                        logger.error(f"Validation error: {e}")

        return UserInputData(
            blocks_input=[TextBlock(type="text", text=text_input)],
            structured_input=structured_input,
        )
