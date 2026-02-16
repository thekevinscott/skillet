# Contributing to Skillet

## Development Setup

Skillet uses [uv](https://docs.astral.sh/uv/) for dependency management and [just](https://github.com/casey/just) (via `uv run just`) as a task runner.

```bash
git clone https://github.com/thekevinscott/skillet.git
cd skillet
uv sync --all-extras
```

### Git Worktrees

All development happens in git worktrees, not on the main branch. Create one per feature:

```bash
git worktree add .worktrees/my-feature -b feat/my-feature
cd .worktrees/my-feature
uv sync --all-extras
```

When done, remove it from the repo root:

```bash
cd /path/to/skillet   # must be outside the worktree
git worktree remove .worktrees/my-feature
```

## Testing

Run tests with `uv run just`:

```bash
uv run just test-unit          # Unit tests (colocated *_test.py files)
uv run just test-integration   # Integration tests (tests/integration/)
uv run just test-e2e           # End-to-end tests (tests/e2e/)
uv run just test-cov           # Unit tests with coverage report
```

### Test Locations

- **Unit tests**: Colocated with source — `foo.py` has `foo_test.py` in the same directory
- **Integration tests**: `tests/integration/`
- **E2E tests**: `tests/e2e/`

### What to Test

If your change touches the public API (CLI, SDK, config), include e2e and integration tests. For internal changes with existing coverage, unit tests are sufficient.

## Code Style

- **One function per file** — `get_rate_color.py` contains `get_rate_color()`
- **Co-located tests** — `foo.py` → `foo_test.py` in the same directory
- **Type hints on all public functions**
- **Docstrings**: focus on *why* and *what*, skip `Args:`/`Returns:` sections (use type hints instead)

Linting and formatting are enforced by pre-push hooks:

```bash
uv run just lint       # Ruff linting
uv run just format     # Ruff formatting
uv run just typecheck  # ty type checking
```

## Pull Requests

- **Never commit directly to main** — always open a PR
- **Keep PRs focused** — one self-contained piece of functionality per PR
- **Changelog required** — update `CHANGELOG.md` under the appropriate heading (Added/Changed/Fixed/Removed), or add the `skip-changelog` label for purely internal changes

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Use for |
|------|---------|
| `feat:` | New user-facing functionality |
| `fix:` | Bug fixes |
| `test:` | Test additions/changes |
| `chore:` | Internal tooling, CI, maintenance |
| `refactor:` | Code restructuring without behavior change |
| `docs:` | Documentation only |

### CI

The pre-push hook runs linting, formatting, type checking, and unit tests. Integration and e2e tests run on GitHub CI.

## Project Structure

```
skillet/           # Source code (one function per file)
tests/
  integration/     # Integration tests
  e2e/             # End-to-end tests (uses Claude Agent SDK)
docs/              # VitePress documentation site
scripts/           # Build and maintenance scripts
```
