# -*- coding: utf-8 -*-
"""Run prompts against an external ACP agent through AgentScope."""

import argparse
import asyncio
from pathlib import Path
from typing import Any

from acp.schema import AgentMessageChunk, RequestPermissionRequest

from agentscope.acp import ACPClient


async def show_update(_session_id: str, update: Any) -> None:
    """Print text chunks and preserve other updates as structured output."""
    if isinstance(update, AgentMessageChunk) and update.content.type == "text":
        print(update.content.text, end="", flush=True)
    else:
        print(f"\n{update.model_dump_json(exclude_none=True)}", flush=True)


async def cancel_permission(request: RequestPermissionRequest) -> None:
    """Show required approval without choosing on behalf of the user."""
    print(
        f"\nPermission required: {request.tool_call.title}\n"
        f"This example cancels permission requests. Supply on_permission "
        f"in your application to ask the user and return an offered ID.",
        flush=True,
    )


async def main() -> None:
    """Launch the given command and reuse one session for all prompts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--prompt", action="append", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("Provide an ACP agent command after --")
    async with ACPClient(
        command=command[0],
        args=command[1:],
        cwd=args.cwd,
        on_update=show_update,
        on_permission=cancel_permission,
    ) as client:
        for prompt in args.prompt:
            print(f"\nYou: {prompt}\nAgent: ", end="", flush=True)
            result = await client.prompt(prompt)
            print(f"\nStop reason: {result.stop_reason}")


if __name__ == "__main__":
    asyncio.run(main())
