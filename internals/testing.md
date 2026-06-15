# Testing

## Red/Green Development

Follow **red/green** (test-first) methodology:

1. **Write the test first** — it must capture the desired behavior
2. **Run it and confirm it fails (RED)** — do NOT proceed until the test turns red reliably. A test that passes before implementation proves nothing.
3. **Make the minimal change to pass (GREEN)** — only then write the implementation
4. Refactor if needed, keeping tests green

## TDD Order: Outside-In

Tests are written **before** implementation, starting from the outermost layer:

1. **E2E test first** — proves the feature works from the user's perspective, using real LLMs (slow but most accurate)
2. **Integration test** — proves internal modules compose correctly, with mocked LLMs (much faster, potential for dependency issues)
3. **Unit tests** — written as you implement each piece (least important testing layer)

A feature is not done until the e2e and integration tests pass and cover the new functionality.

## When to Write What

**Does the commit change the public-facing API (CLI, SDK, config)?**
- Yes → **e2e test + integration test required**, plus unit tests as you go
- No → Check if adequate e2e/integration coverage already exists:
  - Adequate → unit tests only
  - Gaps → add the missing e2e/integration tests, plus unit tests

**Always write unit tests.** The question is whether you also need e2e and integration tests.

## Test Locations
- **Unit tests**: Colocate with source files (`foo.py` → `foo_test.py` in same directory)
- **Integration tests**: `tests/integration/`
- **E2E tests**: `tests/e2e/`, auto-build `.claude/commands/` via conftest.py

## Enforcing colocated unit tests

The colocated-unit-test rule is machine-enforced by [`testing-conventions`](https://github.com/thekevinscott/testing-conventions) (a dev dependency), so a new source file without a sibling test fails CI rather than slipping through. Run it locally with:

```bash
uv run just check-test-conventions
```

It fails if any source file under `skillet/` lacks a sibling `*_test.py` (`__init__.py` is exempt). The check runs in the `lint` workflow and in the `just ci` / `just ci-local` aggregates, alongside the one-public-callable-per-file convention check.

## Test Infrastructure
- `Conversation` helper for multi-turn e2e test flows
- Use `@pytest.mark.parametrize` when testing multiple inputs/outputs for the same logic
- Mock all imports in unit tests, to establish isolated coverage
- Mock external dependencies in integration tests, but avoid mocking anything internal
- Do not mock anything in e2e tests
- **Always prefer `pytest.fixture` over inline `with patch(...)`** — use `autouse=True` when the mock applies to all tests in scope
- **Never use pytest's `monkeypatch` fixture** — patch with `unittest.mock.patch` / `patch.object` / `patch.dict` wrapped in a `pytest.fixture`, usually with `autouse=True`. For environment variables, use `patch.dict(os.environ, {...})`
- **Mock placement**: integration-level mocks shared across tests belong in `tests/integration/conftest.py`; unit-test mocks belong in the specific test file, inside the describe block that uses them
- **Prefer small hand-rolled fake classes for collaborator objects** (typed via `cast(RealType, FakeThing())`), with `MagicMock` reserved for individual methods whose calls are asserted — don't pass a bare `MagicMock()` as a whole object (convention from thekevinscott/gbnf, e.g. its `MockGraph`)
- **Avoid patching module globals to inject configuration** (e.g., setting `skillet.config.CACHE_DIR` to a tmp path) — any consumer that did `from skillet.config import CACHE_DIR` copied the value at import time and silently ignores the patch

## Mocking with pytest-describe

The canonical mock is an autouse fixture wrapping `unittest.mock.patch`, targeting the name in the *consuming* module, with defaults passed directly to `patch(...)` ([convention from thekevinscott/gbnf](https://github.com/thekevinscott/GBNF/blob/3a2560bcb694dec26717abfa0b22090adc4b665f/packages/gbnf/python/gbnf/grammar_graph/get_serialized_rule_key_test.py#L11)):

```python
@pytest.fixture(autouse=True)
def mock_is_rule_end():
    with patch(
        "gbnf.grammar_graph.get_serialized_rule_key.is_rule_end",
        return_value=False,
    ) as mock:
        yield mock
```

Use the same shape inside a describe block when the mock is scoped to it. Pass fixture as function parameter (not `self`):

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

## Test Fixtures for File Content

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
