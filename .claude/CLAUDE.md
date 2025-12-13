# Skillet Development

## Workflow
- Work in git worktrees, tie PRs to GitHub issues
- Before pushing: `just lint && just test-unit`
- After pushing: monitor CI checks

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
