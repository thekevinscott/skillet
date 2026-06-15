# Development workflow

## Workflow
- Work in git worktrees under `.worktrees/` folder, tie PRs to GitHub issues
- **NEVER commit directly to main** - always create a PR
- **Before pushing**: the pre-push hook runs `uv run just ci` automatically (lint, format, typecheck, unit tests in parallel). Integration tests run only on GitHub CI to keep pushes fast
- **After pushing**: run `gh pr checks <number> --watch` to monitor CI. Fix any failures immediately before moving on
- **After a PR is merged** (both steps, in order):
  1. Pull main in the root repository to keep worktrees in sync
  2. Remove the worktree if no longer needed (see safe removal procedure below)

## Git Worktrees
All development work should happen in git worktrees, not on the main branch directly.

### Creating a Worktree

```bash
git worktree add .worktrees/my-feature -b feat/my-feature
cd .worktrees/my-feature
uv sync --all-extras                          # Install all dependencies including dev tools
uv run python scripts/build_claude_config.py  # Build .claude/commands/
```

**Never give the user commands to run - execute them yourself.** Each worktree has its own `.venv` that needs dependencies installed. The `.claude/commands/` directory is gitignored and must be rebuilt in each worktree.

### Removing a Worktree

**DANGER: removing a worktree while your shell CWD is inside it permanently breaks the shell.** No command will work afterward — not `cd`, not `echo`, not even `ls`. `git -C /path` does NOT help because the shell itself cannot resolve its CWD before git even runs. If this happens, the session is unrecoverable.

The ONLY safe procedure — every step is mandatory:

```bash
# Step 1: Move CWD to the root repository FIRST (not optional, not replaceable with -C)
cd /path/to/skillet   # the root repo, NOT the worktree

# Step 2: Now remove the worktree
git worktree remove .worktrees/my-feature
```

**Do NOT skip step 1. Do NOT substitute `git -C` for `cd`. They are not equivalent.**

## Key Commands

`just` is installed via uv as `rust-just`, so run it with `uv run just`:

```bash
uv run just build-claude    # Build .claude/commands/ from templates
uv run just test-e2e        # Run e2e tests
uv run just test-integration        # Run integration tests
uv run just test-unit       # Run unit tests
```

## Container Development
When running inside a Docker container with the project mounted, use a separate venv to avoid conflicts with the host:

```bash
export UV_PROJECT_ENVIRONMENT=/.venv
uv sync --all-extras
uv run pytest tests/ -v
```

This prevents the host's `.venv` from being invalidated when switching contexts.

## Guidelines
- Check `uv.lock` for dependency versions - don't ask the user for info you can look up
- Don't make up installation commands - verify in docs or source code first
- **Do not chain commands** (e.g., `cmd1 && cmd2`, `cmd1 ; cmd2`, `cmd1 | cmd2`). Chained commands break the permissions system — each command must be run separately so permissions can be evaluated individually
