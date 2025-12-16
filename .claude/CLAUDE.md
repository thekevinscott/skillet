# Skillet Development

## Workflow
- Work in git worktrees under `.worktrees/` folder, tie PRs to GitHub issues
- Before pushing: `just lint && just test-unit`
- After pushing: monitor CI checks

### Git Worktrees
All development work should happen in git worktrees, not on the main branch directly:

```bash
# Create a new worktree for a feature branch
git worktree add .worktrees/my-feature -b feat/my-feature

# Work in the worktree
cd .worktrees/my-feature

# When done, remove the worktree
git worktree remove .worktrees/my-feature
```

## Project Structure
- `.claude-template/` - Source templates with `{{SKILLET_DIR}}` placeholders
- `.claude/commands/` - Generated (gitignored), built from templates
- `scripts/build_claude_config.py` - Template builder
- `tests/e2e/` - End-to-end tests using Claude Agent SDK

## Testing
- E2E tests auto-build `.claude/commands/` via conftest.py
- `Conversation` helper for multi-turn test flows
- `setting_sources=["project"]` loads slash commands from `.claude/commands/`
- Commands in subdirs get namespaced: `skillet/add.md` -> `/skillet:add`

## Key Commands
```bash
just build-claude    # Build .claude/commands/ from templates
just test-e2e        # Run e2e tests
just test-unit       # Run unit tests
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

## Commit Convention

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/) format:

- `fix: ...` → patch release
- `feat: ...` → patch release (default)
- `chore:`, `docs:`, `refactor:`, `test:`, etc. → patch release
- `[minor]` in commit body → minor release (0.1.0 → 0.2.0)
- `BREAKING CHANGE:` in commit body → major release (0.1.0 → 1.0.0)

**Releases default to patch.** Minor and major releases require explicit markers in the commit body.

### Commit Type Guidelines

Use the correct type for your change:

| Type | Use for | Examples |
|------|---------|----------|
| `feat:` | New user-facing functionality | New CLI command, new API endpoint, new config option |
| `fix:` | Bug fixes | Fixing broken behavior, correcting errors |
| `test:` | Test additions/changes | New test files, test infrastructure, eval additions |
| `chore:` | Internal tooling, CI, maintenance | CI workflow changes, dependency updates, build scripts |
| `refactor:` | Code restructuring without behavior change | Renaming, reorganizing, extracting functions |
| `docs:` | Documentation only | README updates, code comments, docstrings |

**Key distinction:** `feat:` is for significant user-facing features, not internal improvements. Adding tests, evals, or CI infrastructure should use `test:` or `chore:`.

### Triggering Minor/Major Releases

To trigger a minor release, include `[minor]` in the commit body:

```
feat: add new export format

Adds CSV export capability to the CLI.

[minor]
```

To trigger a major release, include `BREAKING CHANGE:` in the commit body:

```
feat: redesign configuration API

BREAKING CHANGE: config.yaml format has changed, see migration guide.
```

Releases run nightly at 2am UTC. All commits since the last release are batched together.
