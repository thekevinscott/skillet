# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
