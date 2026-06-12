# Repo-wide conventions

Cross-cutting rules for the Skillet repo. Day-to-day workflow lives in [`workflow.md`](workflow.md), testing in [`testing.md`](testing.md), code style in [`style.md`](style.md), and releases in [`shipping.md`](shipping.md).

## Project Structure
- `.claude-template/` - Source templates with `{{SKILLET_DIR}}` placeholders
- `.claude/commands/` - Generated (gitignored), built from templates
- `scripts/build_claude_config.py` - Template builder
- `tests/e2e/` - End-to-end tests using Claude Agent SDK

## Documentation

There is a README.md and a docs/ folder (using vitepress) that builds to https://skillet.run.

The README.md should stay concise, but should be useful and contain information about major features. It is the primary way PyPI consumers will discover the library.

For more in-depth documentation, ensure the docs cover all public-facing features.

## PR Scope
- **Keep PRs minimal but complete** - each PR should deliver one useful, self-contained piece of functionality
- Don't add code that isn't used until a future PR (e.g., an error class with no callers)
- If a task is too large for one PR, split it into GitHub sub-issues (or a task list on the parent issue) - one per PR
- Every PR must include tests per the TDD Order (see [`testing.md`](testing.md)): e2e first if touching public API, integration tests, then unit tests
- **Changelog (REQUIRED)**: Every PR must either update `CHANGELOG.md` or have the `skip-changelog` label. CI will fail without one of these. Add the changelog entry in the same commit as the code change — do not forget this. User-facing changes go under the appropriate heading (Added/Changed/Fixed/Removed). For purely internal changes (no API/CLI/docs impact), add the `skip-changelog` label instead

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
