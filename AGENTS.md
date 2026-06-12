# Agents

This file is the operating contract for AI agents working in this repo. It is the **canonical** source of agent instructions — `CLAUDE.md` (and `.claude/CLAUDE.md`) just import it, so every tool reads the same thing.

Detailed conventions live under [`internals/`](internals/). **Read the relevant doc there before making changes.**

## Detecting the runtime environment

Claude Code sets the environment variable `CLAUDE_CODE_REMOTE=true` whenever it runs as a remote/cloud session (for example, Claude Code on the web or any Managed Agents container). A companion variable `CLAUDE_CODE_REMOTE_SESSION_ID` is set to the cloud session's ID.

```bash
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
  # Running in a remote/managed environment
fi
```

- **Remote** (`CLAUDE_CODE_REMOTE=true`) — read [`notes/environments/remote.md`](notes/environments/remote.md) **before doing any work**. It documents the rules specific to remote runs: issue tracking, PR requirements, CI gating, merge-readiness.
- **Local** (`CLAUDE_CODE_REMOTE` unset or not `true`) — follow this contract and the `internals/` docs below.

## Where to read first

- [`internals/repo.md`](internals/repo.md) — project structure, documentation, PR scope, commit convention.
- [`internals/workflow.md`](internals/workflow.md) — worktrees, key commands, container development, day-to-day guardrails.
- [`internals/testing.md`](internals/testing.md) — red/green methodology, outside-in TDD order, test locations, mocking conventions.
- [`internals/style.md`](internals/style.md) — module organization, docstrings, type hints.
- [`internals/shipping.md`](internals/shipping.md) — release strategy and cutting releases.

## Workflow (the non-negotiables)

- Use `just` for local tasks — it's installed via uv, so run it as `uv run just` (e.g. `uv run just ci`, `uv run just test-unit`).
- **NEVER commit directly to `main`** — every change lands via a pull request.
- **Tests come first**, outside-in: e2e → integration → unit. See [`internals/testing.md`](internals/testing.md).
- **Changelog (REQUIRED):** every PR either updates `CHANGELOG.md` or carries the `skip-changelog` label — CI fails without one. See [`internals/repo.md`](internals/repo.md).
- Follow [Conventional Commits](https://www.conventionalcommits.org/).
- **Do not chain shell commands** (`cmd1 && cmd2`, `cmd1 ; cmd2`, `cmd1 | cmd2`). Each command must run separately so permissions are evaluated individually.

## Out of scope

- Don't add unsolicited refactors or speculative, hypothetical-future abstractions.
- Don't add code that isn't used until a future PR (e.g. an error class with no callers).
- Don't bypass hooks or CI gates without an explicit reason in the PR body.
