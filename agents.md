# Agents

## Detecting the runtime environment

Claude Code sets the environment variable `CLAUDE_CODE_REMOTE=true` whenever it runs as a remote/cloud session (for example, Claude Code on the web or any Managed Agents container). A companion variable `CLAUDE_CODE_REMOTE_SESSION_ID` is set to the cloud session's ID.

To check whether you are running remotely, inspect `CLAUDE_CODE_REMOTE`:

```bash
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
  # Running in a remote/managed environment
fi
```

## When operating in a remote environment

When `CLAUDE_CODE_REMOTE=true` (i.e., when running as a managed agent or any other remote Claude Code session), **read [`notes/environments/remote.md`](notes/environments/remote.md) before doing any work**. That file documents the workflow rules that apply specifically to remote runs (issue tracking, PR requirements, CI gating, merge-readiness).

If you are running locally (`CLAUDE_CODE_REMOTE` unset or not `true`), follow the standard workflow described in `.claude/CLAUDE.md`.

## Code conventions

- **Prefer relative imports** within the `skillet` package when possible — e.g. `from .parse_launcher_output import parse_launcher_output`, not `from skillet._internal.sdk.run_launcher.parse_launcher_output import ...`. This applies to colocated tests too (they import as part of the package). Reach for an absolute import only when a relative one would be unwieldy or cross far-apart packages.
- Other code-style conventions (one function per file, docstrings, type hints) live in [`.claude/CLAUDE.md`](.claude/CLAUDE.md).
