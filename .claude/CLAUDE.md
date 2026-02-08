# Skillet Development

## Workflow
- Work in git worktrees under `.worktrees/` folder, tie PRs to GitHub issues
- **NEVER commit directly to main** - always create a PR
- **Before pushing, run the same checks CI runs:**
  ```bash
  uv run just lint && uv run just format-check && uv run just typecheck && uv run just test-unit
  ```
- After pushing: monitor CI checks and fix any failures immediately
- **After a PR is merged**: pull main in the root repository to keep worktrees in sync

### PR Scope
- **Keep PRs minimal but complete** - each PR should deliver one useful, self-contained piece of functionality
- Don't add code that isn't used until a future PR (e.g., an error class with no callers)
- If a task is too large for one PR, create child beads under the parent bead - one per PR
- Every PR must include tests per the TDD Order (see Testing section): e2e first if touching public API, integration tests, then unit tests
- **Changelog**: Update `CHANGELOG.md` for user-facing changes. For purely internal changes (no API/CLI/docs impact), add the `skip-changelog` label to bypass the CI check

### Git Worktrees
All development work should happen in git worktrees, not on the main branch directly.

**IMPORTANT: When creating/switching worktrees, always run the setup steps yourself:**

```bash
# Create a new worktree for a feature branch
git worktree add .worktrees/my-feature -b feat/my-feature

# Work in the worktree - ALWAYS run these setup steps:
cd .worktrees/my-feature
uv sync --all-extras                          # Install all dependencies including dev tools
uv run python scripts/build_claude_config.py  # Build .claude/commands/

# When done, remove the worktree
cd ../..
git worktree remove .worktrees/my-feature
```

**Never give the user commands to run - execute them yourself.** Each worktree has its own `.venv` that needs dependencies installed. The `.claude/commands/` directory is gitignored and must be rebuilt in each worktree.

## Project Structure
- `.claude-template/` - Source templates with `{{SKILLET_DIR}}` placeholders
- `.claude/commands/` - Generated (gitignored), built from templates
- `scripts/build_claude_config.py` - Template builder
- `tests/e2e/` - End-to-end tests using Claude Agent SDK

## Documentation

There is a README.md and a docs/ folder (using vitepress) that builds to https://skillet.run.

The README.md should stay concise, but should be useful and contain information about major features. It is the primary way PyPI consumers will discover the library.

For more in-depth documentation, ensure the docs cover all public-facing features.

## Testing

### TDD Order: Outside-In

Tests are written **before** implementation, starting from the outermost layer:

1. **E2E test first** — proves the feature works from the user's perspective, using real LLMs (slow but most accurate)
2. **Integration test** — proves internal modules compose correctly, with mocked LLMs (much faster, potential for dependency issues)
3. **Unit tests** — written as you implement each piece (least important testing layer)

A feature is not done until the e2e and integration tests pass and cover the new functionality.

### When to Write What

**Does the commit change the public-facing API (CLI, SDK, config)?**
- Yes → **e2e test + integration test required**, plus unit tests as you go
- No → Check if adequate e2e/integration coverage already exists:
  - Adequate → unit tests only
  - Gaps → add the missing e2e/integration tests, plus unit tests

**Always write unit tests.** The question is whether you also need e2e and integration tests.

### Test Locations
- **Unit tests**: Colocate with source files (`foo.py` → `foo_test.py` in same directory)
- **Integration tests**: `tests/integration/`
- **E2E tests**: `tests/e2e/`, auto-build `.claude/commands/` via conftest.py

### Test Infrastructure
- `Conversation` helper for multi-turn e2e test flows
- Use `@pytest.mark.parametrize` when testing multiple inputs/outputs for the same logic
- Mock all imports in unit tests, to establish isolated coverage
- Mock external dependencies in integration tests, but avoid mocking anything internal
- Do not mock anything in e2e tests
- **Always prefer `pytest.fixture` over inline `with patch(...)`** — use `autouse=True` when the mock applies to all tests in scope

### Mocking with pytest-describe

Use `@pytest.fixture(autouse=True)` for shared mocks within a describe block. Pass fixture as function parameter (not `self`):

```python
def describe_my_function():
    @pytest.fixture(autouse=True)
    def mock_dependency():
        with patch("module.dependency", new_callable=AsyncMock) as mock:
            mock.return_value = default_value
            yield mock

    @pytest.mark.asyncio
    async def it_does_something(mock_dependency):
        mock_dependency.return_value = specific_value
        result = await my_function()
        assert result == expected
```

If a fixture is used in multiple describe blocks, move it to the top level rather than duplicating it across describe blocks.

### Test Fixtures for File Content

Use readable multi-line strings for file content. Either module-level constants or inline `dedent()` — never escaped `\n` strings:

```python
# Good - module-level constant
VALID_SKILL = """\
---
name: test
---
"""

def it_does_something(tmp_path):
    skill.write_text(VALID_SKILL)

# Good - inline dedent
def it_does_something(tmp_path):
    skill.write_text(dedent("""\
        ---
        name: test
        ---
        """))

# Bad - hard to read
def it_does_something(tmp_path):
    skill.write_text("---\nname: test\n---\n")
```

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

## Code Style

### Docstrings
- **Skip `Args:`, `Returns:`, `Raises:` sections** - these are statically analyzable from type hints
- Use docstrings for *why* and *what*, not *how* the signature works
- One-liner docstrings for simple functions; multi-line only when behavior needs explanation

### Type Hints
- **Prefer fixing type issues over `# type: ignore`** - investigate the root cause first

```python
# Good
def query_structured[T: BaseModel](prompt: str, model: type[T]) -> T:
    """Query Claude and return a validated Pydantic model."""

# Avoid
def query_structured[T: BaseModel](prompt: str, model: type[T]) -> T:
    """Query Claude and return a validated Pydantic model.

    Args:
        prompt: The prompt to send
        model: A Pydantic model class

    Returns:
        An instance of the model
    """
```

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
