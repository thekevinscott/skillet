# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Template-based command system for `{{SKILLET_DIR}}` substitution
- `scripts/build_claude_config.py` for building `.claude/commands/` from templates
- `just build-claude` command for template building
- E2E test helpers with `Conversation` class for multi-turn testing
- Auto-build of commands in e2e test conftest
- 13 eval files for testing `/skillet:add` command behavior
- Multi-turn conversation support in eval system
- Session resumption for sequential prompts in evals
- Automated nightly release workflow (2am UTC) triggered by git tags
- Manual trigger for release workflow (workaround for GITHUB_TOKEN limitation)
- Skip release if tag already exists (prevents duplicate tag errors)

### Fixed
- Release workflow permissions for checkout
- Nightly release tag check now uses remote refs instead of local (semantic-release creates local tags)
- Removed redundant commit/tag step since semantic-release already creates them
- Release workflow now uses `fetch-depth: 0` so hatch-vcs can read tags for versioning

### Removed
- GitHub Pages deployment from release workflow (not needed)

### Fixed
- semantic-release config to update pyproject.toml version

### Changed
- Switched to dynamic versioning via `hatch-vcs` (version derived from git tags at build time)
- Simplified nightly release workflow to only create/push tags (no commits to main needed)
- Simplified release workflow to always publish (removed unnecessary changes detection)
- Renamed PyPI package from `skillet` to `pyskillet` (name was taken)
- Renamed `/skillet:gap` command to `/skillet:add`
- Increased `max_turns` from 3 to 10 for complex command workflows
- Reorganized codebase into domain modules (eval/, compare/, tune/, skill/, gaps/)
- Separated CLI layer from core API logic
- Renamed public API functions: `run_eval` -> `evaluate`, `run_compare` -> `compare`, `run_tune` -> `tune`
- Moved internal utilities to `_internal/` module

### Added
- Initial CLI with `eval`, `new`, `tune`, and `compare` commands
- Gap capture via `/skillet:gap` Claude Code command
- Evaluation caching system
- LLM-as-judge for response validation
- Live display with spinner animation for parallel evals
- Python linting with Ruff
- pytest testing infrastructure with pytest-describe
- Pre-commit hooks for linting and tests
- CI workflows for lint, test, and build
- PR monitor for CI gating
- PEP 561 py.typed marker for type checking support
