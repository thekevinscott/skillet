# Skillet Development

## Workflow
- Work in git worktrees under `.worktrees/` folder, tie PRs to GitHub issues
- **NEVER commit directly to main** - always create a PR
- Before pushing: `just lint && just test-unit`
- After pushing: monitor CI checks
- **After a PR is merged**: pull main in the root repository to keep worktrees in sync

### Git Worktrees
All development work should happen in git worktrees, not on the main branch directly.

**IMPORTANT: When creating/switching worktrees, always run the setup steps yourself:**

```bash
# Create a new worktree for a feature branch
git worktree add .worktrees/my-feature -b feat/my-feature

# Work in the worktree - ALWAYS run these setup steps:
cd .worktrees/my-feature
uv run python scripts/build_claude_config.py  # Build .claude/commands/

# When done, remove the worktree
cd ../..
git worktree remove .worktrees/my-feature
```

**Never give the user commands to run - execute them yourself.** The `.claude/commands/` directory is gitignored and must be rebuilt in each worktree.

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
- Use `@pytest.mark.parametrize` when testing multiple inputs/outputs for the same logic
- Mock external dependencies (like `get_rate_color`) to isolate unit tests

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

| Type | Use for | Examples |
|------|---------|----------|
| `feat:` | New user-facing functionality | New CLI command, new API endpoint, new config option |
| `fix:` | Bug fixes | Fixing broken behavior, correcting errors |
| `test:` | Test additions/changes | New test files, test infrastructure, eval additions |
| `chore:` | Internal tooling, CI, maintenance | CI workflow changes, dependency updates, build scripts |
| `refactor:` | Code restructuring without behavior change | Renaming, reorganizing, extracting functions |
| `docs:` | Documentation only | README updates, code comments, docstrings |

**Key distinction:** `feat:` is for significant user-facing features, not internal improvements. Adding tests, evals, or CI infrastructure should use `test:` or `chore:`.

### Releases

- **Patch releases** run nightly at 2am UTC (automatic)
- **Minor releases** are triggered manually via GitHub Actions → "Minor Release"
- **Major releases** are done manually by creating a tag
