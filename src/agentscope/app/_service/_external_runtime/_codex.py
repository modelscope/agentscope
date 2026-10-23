# -*- coding: utf-8 -*-
"""Native Codex app-server transport and turn projection."""

import asyncio
import json
import time
from typing import Any

from ._base import NativeRuntime, approval
from ....types import ReplyFinishedReason


class CodexRuntime(NativeRuntime):
    """Correlate RPCs while approvals run independently of the reader."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.arguments = ["app-server", "--listen", "stdio://"]
        self.process: asyncio.subprocess.Process | None = None
        self.reader: asyncio.Task | None = None
        self.pending: dict[int, asyncio.Future] = {}
        self.requests: dict[Any, asyncio.Task] = {}
        self.events: asyncio.Queue = asyncio.Queue()
        self.sequence = 0
        self.turn_id: str | None = None
        self.turn_ready = asyncio.Event()
        self.outputs: dict[str, str] = {}
        self.progress_at: dict[str, float] = {}
        self.failure: Exception | None = None

    async def read_account(self) -> dict:
        """Initialize the protocol and read public account status."""
        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.arguments,
            cwd=self.cwd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=None,
            limit=50 * 1024 * 1024,
        )
        self.reader = asyncio.create_task(self._read())
        await self.rpc(
            "initialize",
            {
                "clientInfo": {
                    "name": "agentscope",
                    "version": "1",
                },
            },
        )
        await self._send({"method": "initialized", "params": {}})
        return await self.rpc("account/read", {"refreshToken": False})

    async def connect(self, probe: bool = False) -> None:
        account = await self.read_account()
        if account.get("requiresOpenaiAuth") and not account.get("account"):
            raise ValueError(
                "Codex is not authenticated. Run codex login first",
            )
        if probe:
            return
        params = {
            "cwd": self.cwd,
            "sandbox": "workspace-write",
            "approvalPolicy": "on-request",
        }
        if self.session_id:
            params["threadId"] = self.session_id
        result = await self.rpc(
            "thread/resume" if self.session_id else "thread/start",
            params,
        )
        remote_id = result["thread"]["id"]
        if self.session_id and remote_id != self.session_id:
            raise RuntimeError("Codex resumed a different conversation")
        self.session_id = remote_id

    async def _send(self, message: dict) -> None:
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("Codex process is not connected")
        self.process.stdin.write(json.dumps(message).encode() + b"\n")
        await self.process.stdin.drain()

    async def rpc(self, method: str, params: dict) -> dict:
        """Send an RPC without retrying potentially stateful operations."""
        if self.failure:
            raise self.failure
        self.sequence += 1
        request_id = self.sequence
        future = asyncio.get_running_loop().create_future()
        self.pending[request_id] = future
        try:
            await self._send(
                {
                    "id": request_id,
                    "method": method,
                    "params": params,
                },
            )
            async with asyncio.timeout(30):
                return await future
        finally:
            self.pending.pop(request_id, None)
            if not future.done():
                future.cancel()
            elif not future.cancelled():
                future.exception()

    async def _read(self) -> None:
        try:
            while line := await self.process.stdout.readline():
                message = json.loads(line)
                request_id = message.get("id")
                method = message.get("method")
                if request_id is not None and method is None:
                    future = self.pending.get(request_id)
                    if future is not None and not future.done():
                        if "error" in message:
                            future.set_exception(
                                RuntimeError(
                                    message["error"].get(
                                        "message",
                                        "Codex error",
                                    ),
                                ),
                            )
                        else:
                            future.set_result(message.get("result") or {})
                elif request_id is not None:
                    self.requests[request_id] = asyncio.create_task(
                        self._respond(message),
                    )
                elif method == "serverRequest/resolved":
                    resolved = message.get("params", {}).get("requestId")
                    task = self.requests.get(resolved)
                    if task:
                        task.cancel()
                else:
                    self.events.put_nowait(message)
            self.failure = RuntimeError("Codex app-server exited")
        except Exception as exc:
            self.failure = exc
        finally:
            error = self.failure or RuntimeError("Codex connection closed")
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(error)
            self.events.put_nowait(error)

    async def _respond(self, message: dict) -> None:
        request_id = message["id"]
        try:
            params = message.get("params") or {}
            method = message["method"]
            supported = method in {
                "item/commandExecution/requestApproval",
                "item/fileChange/requestApproval",
                "item/permissions/requestApproval",
            }
            foreign_turn = self.turn_id is not None and (
                params.get("turnId") != self.turn_id
            )
            if (
                not supported
                or foreign_turn
                or params.get("threadId") != self.session_id
            ):
                await self._send(
                    {
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": "Unsupported client request",
                        },
                    },
                )
                return
            is_permissions = method == "item/permissions/requestApproval"
            offered = params.get("availableDecisions")
            request = approval(
                params["itemId"],
                params.get("command") or params.get("reason") or method,
                params,
            )
            if offered is not None and "accept" not in offered:
                request["options"] = request["options"][1:]
            choice = await self.choose(request)
            if is_permissions:
                result = {
                    "permissions": params.get("permissions", {})
                    if choice == "allow"
                    else {},
                    "scope": "turn",
                }
            else:
                result = {
                    "decision": "accept" if choice == "allow" else "decline",
                }
            await self._send({"id": request_id, "result": result})
        except Exception as exc:
            self.failure = exc
            self.events.put_nowait(exc)
        finally:
            self.requests.pop(request_id, None)

    async def _prompt(self, text: str) -> ReplyFinishedReason:
        result = await self.rpc(
            "turn/start",
            {
                "threadId": self.session_id,
                "input": [{"type": "text", "text": text}],
            },
        )
        self.turn_id = result["turn"]["id"]
        self.turn_ready.set()
        while True:
            message = await self.events.get()
            if isinstance(message, Exception):
                raise message
            params = message.get("params") or {}
            if params.get("threadId") != self.session_id:
                continue
            turn_id = params.get("turnId") or params.get("turn", {}).get("id")
            if turn_id and turn_id != self.turn_id:
                continue
            if message["method"] == "turn/completed":
                self.completed = True
                turn = params["turn"]
                status = turn["status"]
                if status == "failed":
                    raise RuntimeError(
                        (turn.get("error") or {}).get(
                            "message",
                            "Codex turn failed",
                        ),
                    )
                if status in {"interrupted", "cancelled"}:
                    return ReplyFinishedReason.INTERRUPTED
                return ReplyFinishedReason.COMPLETED
            await self._project(message["method"], params)

    async def _project(self, method: str, params: dict) -> None:
        if method in {
            "item/agentMessage/delta",
            "item/reasoning/textDelta",
            "item/reasoning/summaryTextDelta",
            "item/plan/delta",
        }:
            await self.on_update(
                {
                    "kind": "text"
                    if method == "item/agentMessage/delta"
                    else "thought",
                    "text": params.get("delta", ""),
                },
            )
        elif method == "turn/plan/updated":
            await self.on_update(
                {
                    "kind": "plan",
                    "plan": [
                        {
                            "content": item["step"],
                            "status": {
                                "inProgress": "in_progress",
                            }.get(item["status"], item["status"]),
                        }
                        for item in params.get("plan", [])
                    ],
                },
            )
        elif method == "item/commandExecution/outputDelta":
            item_id = params["itemId"]
            self.outputs[item_id] = (
                self.outputs.get(item_id, "") + params["delta"]
            )
            # Send the first snapshot per window. The tail is flushed on
            # completion or the next delta, not by a separate timer.
            now = time.monotonic()
            if now - self.progress_at.get(item_id, 0) >= 0.5:
                self.progress_at[item_id] = now
                await self.on_update(
                    {
                        "kind": "tool",
                        "tool": {
                            "tool_call_id": item_id,
                            "raw_output": self.outputs[item_id],
                        },
                    },
                )
        elif method in {"item/started", "item/completed"}:
            item = params["item"]
            if item["type"] in {
                "agentMessage",
                "userMessage",
                "reasoning",
                "plan",
            }:
                return
            item_id = item["id"]
            done = method == "item/completed"
            await self.on_update(
                {
                    "kind": "tool",
                    "tool": {
                        "tool_call_id": item_id,
                        "title": item.get("command")
                        or item.get("tool")
                        or item["type"],
                        "status": (
                            "failed"
                            if item.get("status") in {"failed", "declined"}
                            else "completed"
                        )
                        if done
                        else "in_progress",
                        "raw_input": item,
                        "raw_output": item.get("aggregatedOutput")
                        or item.get("result")
                        or self.outputs.get(item_id, ""),
                    },
                },
            )

    async def interrupt(self) -> None:
        await self.turn_ready.wait()
        await self.rpc(
            "turn/interrupt",
            {
                "threadId": self.session_id,
                "turnId": self.turn_id,
            },
        )

    async def aclose(self) -> None:
        self.cancelled.set()
        tasks = list(self.requests.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        process = self.process
        if process is not None:
            if process.stdin:
                process.stdin.close()
            if process.returncode is None:
                try:
                    await asyncio.wait_for(process.wait(), 2)
                except TimeoutError:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), 2)
                    except TimeoutError:
                        process.kill()
                        await process.wait()
        if self.reader:
            self.reader.cancel()
            await asyncio.gather(self.reader, return_exceptions=True)
