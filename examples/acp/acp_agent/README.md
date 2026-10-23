# Agent Client Protocol

Run an AgentScope agent as an ACP agent over stdio. This is the **Agent Client
Protocol**, not the former Agent Communication Protocol. No web service or
frontend is needed.

## Install

Use Python 3.11+ and install the optional SDK:

```bash
pip install -e '.[acp]'
```

Configure `DASHSCOPE_API_KEY` in your environment; optionally set
`AGENTSCOPE_MODEL` to override the example's default DashScope model.

## Try a complete conversation

From the repository root, run:

```bash
export DASHSCOPE_API_KEY="your-api-key"
python examples/acp/acp_agent/client.py
```

On Windows PowerShell, set the environment variable with
`$env:DASHSCOPE_API_KEY = "your-api-key"`, then run the same Python command.

The client starts `agent.py` automatically, initializes ACP, creates a session,
sends `hello`, and prints the streamed answer. It then closes the session and
agent process. This calls the real DashScope model using your key.
The final line is `[stop_reason: end_turn]` on normal completion.

You can supply another prompt and a project directory:

```bash
python examples/acp/acp_agent/client.py "Explain the project structure" --cwd /absolute/project
```

The default project directory is your current directory. If a tool needs
permission, the client asks in the terminal: enter `y` to allow once, or press
Enter to reject. EOF cancels the permission request. This client sends one
prompt per run; use QwenPaw for an ongoing conversation.

## Agent entry point

ACP clients such as QwenPaw can launch the agent directly:

```bash
python /absolute/path/to/agentscope/examples/acp/acp_agent/agent.py
```

It waits for ACP JSON-RPC on stdin, not interactive keyboard input. Stdout is
reserved for the protocol; logs and ordinary Python prints go to stderr.
Clients should continuously drain stderr or redirect it to a file.

## QwenPaw configuration

In QwenPaw's ACP runner configuration, enable a runner named `agentscope`:

| Field | Value |
| --- | --- |
| command | Absolute path to the Python interpreter containing `agentscope[acp]` |
| args | Absolute path to `examples/acp/acp_agent/agent.py`, as one argument |
| env | `DASHSCOPE_API_KEY` and optionally `AGENTSCOPE_MODEL` |
| trusted | `false` to forward permission choices to the user |

Use `python -c "import sys; print(sys.executable)"` in the installed environment
to find its interpreter. On Windows use that environment's `python.exe`; do
not prepend `cmd /c` when invoking Python directly. Keep paths and arguments
separate, including paths with spaces. The example checks `DASHSCOPE_API_KEY`
at startup and exits with an actionable error if it is missing.

Enable QwenPaw's `delegate_external_agent` tool, then start a delegation using
the `agentscope` runner. Continue with `message`, answer permissions with the
exact offered option ID via `respond`, and release the session using `close`.

The example creates a new Agent per ACP session and uses the client's `cwd`
as the project directory. File tools use absolute paths; shell tools receive
that cwd explicitly. No workspace metadata is created in the project root.
File tools operate on disk, so save editor buffers before asking for edits.
Shell commands receive EOF on stdin; interactive commands need explicit
non-interactive options or input supplied by the command itself.
This is a local process, not a sandbox; existing AgentScope tool permissions
apply.

## Supply your own agent

Use an async context manager accepting `ACPSessionContext`. Yield a **fresh**
Agent per invocation. Put application cleanup after the yield or in nested
context managers. Store cache/history outside the project cwd if needed.

```python
from contextlib import asynccontextmanager
from agentscope.acp import serve_acp


@asynccontextmanager
async def create_agent(context):
    agent = build_my_agent(project_dir=context.cwd)
    yield agent


# In an async main:
await serve_acp(create_agent)
```

An importable factory can also be launched without a custom main:

```bash
python -m agentscope.acp --factory my_application.acp:create_agent
```

The factory's resources and client-supplied MCP connections live until session
close or stdin EOF. Stateful MCP resources are entered and exited in the same
task. MCP tools are added to the session agent's always-active `basic` group
and removed on close; the model can use them without calling `reset_tools`.

Factory exit has a 30-second asynchronous timeout. Cleanup must propagate
`asyncio.CancelledError` and must not block the event loop. Swallowing
cancellation prevents the timeout from enforcing its limit. When the timeout
interrupts cleanup, resources may not be fully released; the server logs a
warning with the session ID and timeout duration.

## First-version capabilities

- ACP v1 initialization and independent, in-memory multi-turn sessions.
- Text and resource-link prompts, with links passed as `[name](uri)` text.
- Streamed text/thinking, tool input and status updates. The first output
  chunk is sent immediately; further output events
  send at most one snapshot per second per tool. Completion always sends
  the full result. There is no timer to flush trailing chunks: buffered output
  waits for another output event or completion. Builtin Bash/PowerShell return
  output only after the process finishes.
- Allow once, reject once, and session-local rule grants when suggested rules
  are available. Cancelling a permission prompt aborts the turn.
- Cancel during generation, tool execution, or permission waiting.
- Session-local stdio and Streamable HTTP MCP servers.
- `session/close` (an SDK extension), plus cleanup on disconnect.

Unsupported: history loading, mode/model switching, client file/terminal RPC,
legacy SSE MCP, image/audio/embedded-resource prompts, externally executed
tools and pipelines.
Unsupported prompt blocks are rejected, not silently discarded. Binary tool
results are represented by a MIME-type notice in this text-oriented MVP.
Do not share mutable Agent instances between session factories.

## Verification

Core adapter regression tests:

```bash
python -m pytest tests/acp_agent_test.py tests/acp_stdio_test.py -q
```

Tests use scripted models and in-process ACP clients; no model API key is
required. MCP startup failure coverage launches a local Python subprocess.
This ACP branch assumes the MCP cleanup fix from PR #3402 is included. The SDK dependency is constrained to the validated 0.10.x API used
by QwenPaw; SDK versions are distinct from ACP wire protocol v1.
