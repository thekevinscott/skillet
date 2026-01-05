# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- E2E test: pirate skill tuning validation with calibrated evals
- Tune display: live progress with per-eval pass/fail symbols and pass rate percentages
- DSPy integration for skill tuning with MIPROv2-inspired instruction optimization
- `TuneConfig` and `TuneCallbacks` dataclasses for cleaner tune API
- `ClaudeAgentLM` - Custom DSPy language model using Claude Agent SDK
- `SkilletMIPRO` - MIPROv2 wrapper with callback hooks for progress reporting
- `propose_instruction` function for DSPy-powered instruction generation
- Security: `--trust` flag for eval command to skip script confirmation prompt
- Security: Interactive confirmation prompt when evals contain setup/teardown scripts
- Static analysis: mccabe complexity (C90) and pylint refactor (PLR) rules in ruff config
- Shared `get_rate_color()` helper for consistent pass rate color coding

### Changed
- Removed `notes/` folder from version control (now gitignored)
- **BREAKING:** CLI flag `--gaps/-g` renamed to `--max-evals/-m` for consistency
- Renamed `skillet/gaps/` module to `skillet/evals/` for terminology consistency
- Renamed `get_cached_results_for_gap` to `get_cached_results_for_eval`

### Fixed
- Resource leaks: use `TemporaryDirectory` context manager instead of manual cleanup
- File operations now have proper error handling with `SkillError` exceptions
- Judge now uses structured JSON output instead of text parsing for reliable pass/fail detection
- Critical exceptions (KeyboardInterrupt, SystemExit) now propagate instead of being suppressed
- Setup/teardown scripts now have a 30-second timeout to prevent hanging
- `asyncio.run()` in DSPy metric no longer fails in async contexts
- Race condition in parallel cache access using file locking
- Docs site body text now uses Inter font instead of JetBrains Mono
- Docs navigation uses flat pages (removed group labels, matches agentskills.io)
- Docs footer removed (matches agentskills.io)
- Mintlify docs.json navigation schema updated to object format

### Changed
- Docs accent color changed to warm taupe (#8B7355) for brand identity
- Docs headings use Plus Jakarta Sans font for visual distinction
- Refactored `cli/commands/` to folder structure with helper functions in separate files
- Extracted prompts from Python code into colocated `.txt` files with `${var}` templating
- Refactored `eval/` module to split `run.py` into `evaluate.py`, `isolated_home.py`, `run_script.py`, `run_prompt.py`
- Refactored `compare/` module to split `run.py` into `compare.py`, `calculate_pass_rate.py`, `get_cached_results_for_eval.py`
- Migrated documentation from VitePress to Mintlify platform
- Bump actions/checkout from v4 to v6 in CI workflows

### Added
- `docs/components/reactive-docs/` - Reactive documentation system with [Show me] automation
- `docs/components/ReactiveDocsLayout` - Split-pane layout with docs panel and terminal
- `docs/components/DocsPanel` - Tutorial step display with progress indicator
- `Terminal` component now exposes `executeCommand` via ref for programmatic control
- `docs/components/UnifiedTerminal` - Unified LLM interface with seamless backend switching
- `docs/components/llm/` - Unified LLM backend interface abstracting over Claude API and WebLLM
- `docs/components/LocalLLMTerminal` - Browser-based LLM using WebLLM for zero-friction onboarding
- `docs/components/webllm.ts` - WebLLM client wrapper with same interface as Claude client
- `docs/components/ClaudeTerminal` - Terminal with Claude AI integration for interactive docs
- `docs/components/ApiKeyInput` - BYOK (Bring Your Own Key) component for Anthropic API key
- `docs/components/claude.ts` - Lightweight Claude client for browser environments
- `docs/components/Terminal` - React component with xterm.js and WebContainer for interactive docs
- Unit tests for cache, gaps/load, tune/improve, compare/run, eval/judge, cli/display, eval/run, cli/commands/tune, cli/commands/compare, sdk modules (coverage raised to 55%)
- Comprehensive unit tests for eval/run, eval/judge, tune/run, tune/improve, skill/create, skill/draft, cli/main, cli/commands/compare (coverage raised to 77%)
- Tool call capture in eval results - judge now sees which tools Claude used
- `--skip-cache` flag for eval command to ignore cached results
- `TuneResult` dataclass with full iteration history (inspired by DSPy)
- `--output` flag for tune command to save results JSON
- DSPy integration: `skillet.optimize` module with metric adapter for prompt optimization
- `SkillModule` class for wrapping skills as DSPy modules
- `load_evals` function replaces `load_gaps` (breaking change for direct imports)
- `evals_to_trainset()` function to convert skillet evals to DSPy Examples
- `optimize_skill()` function for DSPy-based skill optimization (BootstrapFewShot, MIPROv2)
- Unit tests for `skillet.optimize` module (100% coverage)
- `notes/` folder for project documentation and strategy discussions

### Changed
- Tune no longer modifies original skill file - uses tmpfile during tuning
- Tune returns `TuneResult` with all rounds, evals, and best skill content
- Tune output now compares against baseline (round 1) instead of 100% target
- Tune auto-saves results to `~/.skillet/tunes/{eval_name}/{timestamp}.json` by default

### Removed
- Duplicate output in tune command (finalize was printing after live display)

### Fixed
- Tune now accepts direct .md file paths (not just directories with SKILL.md)
- Tune display now shows all evals from the start of each round (was only showing first few)
- Tune evals now run correctly (was crashing due to env=None passed to SDK)
- Capture and display stderr output from Claude CLI during evals
- Symlink ~/.claude to isolated HOME so evals can access credentials

### Documentation
- CLAUDE.md: Always run worktree setup steps, never give user commands to run

### Changed
- Renamed "Gaps" to "Evals" in CLI output
- Renamed eval files with descriptive suffixes (e.g., `001.yaml` → `001-ask-expectation.yaml`)
- **Nightly releases are now patch-only.** Minor releases are triggered manually via the "Minor Release" workflow. This prevents version inflation from mislabeled commits.
- Renamed `version-bump.yml` to `patch-release.yml` for clarity
- Updated commit type guidelines in CLAUDE.md with clearer distinction between `feat:`, `test:`, and `chore:`

### Added
- `minor-release.yml` workflow for manual minor version bumps
- Single eval file support (`skillet eval ./evals/my-skill/001.yaml`)
- ROADMAP.md with planned features
- CLAUDE.md guidelines: check uv.lock for versions, verify commands in docs
- 7 folder-suggestion evals for `/skillet:add` command testing
- Recursive eval loading (supports subdirectories in eval folders)
- Container development docs in CLAUDE.md (use `/.venv` for isolated venv)
- Isolated HOME environment for every eval execution
- Optional `setup` and `teardown` scripts in eval YAML for pre/post test hooks
- Git worktree workflow documentation in CLAUDE.md
- RELEASING.md documenting the fully automated release process
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

### Changed
- Consolidated release workflow into nightly workflow (fully automated, no manual trigger needed)
- Fixed README install command (`skillet` → `pyskillet`)
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

### Fixed
- `load_gaps` now accepts paths (e.g., `./evals/add-command/`) in addition to names
- Cache normalizes paths to directory name for consistent caching
- Eval CLI live display now updates in real-time during execution
- Release workflow permissions for checkout
- Nightly release tag check now uses remote refs instead of local (semantic-release creates local tags)
- Removed redundant commit/tag step since semantic-release already creates them
- Release workflow now uses `fetch-depth: 0` so hatch-vcs can read tags for versioning
- semantic-release config to update pyproject.toml version

### Removed
- `GapError` exception (use `EvalError` instead)
- Separate `release.yml` workflow (now part of nightly workflow)
- GitHub Pages deployment from release workflow (not needed)

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
