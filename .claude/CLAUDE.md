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
export UV_PROJECT_ENVIRONMENT=.venv-container
uv sync --all-extras
uv run pytest tests/ -v
```

This prevents the host's `.venv` from being invalidated when switching contexts.

## Commit Convention

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/) format for automatic version bumping:

- `fix: ...` → patch release (0.1.0 → 0.1.1)
- `feat: ...` → minor release (0.1.0 → 0.2.0)
- `feat!: ...` or `BREAKING CHANGE:` in body → major release (0.1.0 → 1.0.0)
- `chore:`, `docs:`, `refactor:`, `test:`, etc. → patch release

Releases run nightly at 2am UTC. All commits since the last release are batched together, and the highest-priority bump type wins (breaking > feat > fix).
