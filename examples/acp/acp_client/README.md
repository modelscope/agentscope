# ACP Client

Run prompts against an external agent using Agent Client Protocol over stdio.
Install and authenticate your agent first; a regular chat CLI may not support ACP.

From the repository root:

```sh
python -m pip install -e ".[acp]"
python examples/acp/acp_client/main.py --prompt "Describe this project" --prompt "Explain its entry point" -- your-acp-agent
```

Replace `your-acp-agent` with your agent's ACP command and arguments.
Add `--cwd "/path/to/project"` before `--` to set the working directory;
it defaults to the current directory.

- Repeat `--prompt` for sequential prompts in the same session.
- Text responses stream to the terminal; other updates print as JSON.
- Permission requests are cancelled. To enable approvals, adapt
  `on_permission` to ask the user and return an offered option ID.
- This is a command-line example, not an interactive chat console.
  It does not use `launch_console` or provide client-side file/terminal tools.

The Web UI's native Codex/Qoder integrations are separate from this example.
