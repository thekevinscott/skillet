# Default recipe - show available commands
default:
    @just --list

# Run the CLI
run *args:
    uv run skillet {{args}}

# Run linter
lint:
    uv run ruff check .

# Run formatter check
format-check:
    uv run ruff format --check .

# Format code
format:
    uv run ruff format .

# Fix auto-fixable lint issues
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info

# Build package
build: clean
    uv build

# Install pre-commit hooks
hooks:
    uv run pre-commit install

# Check changelog was updated (for CI)
# Skip if only docs/ files changed
check-changelog base_ref='origin/main':
    #!/usr/bin/env bash
    changed_files=$(git diff --name-only {{base_ref}}...HEAD)

    # Check if all changed files are in docs/
    non_docs_changes=$(echo "$changed_files" | grep -v '^docs/' || true)
    if [ -z "$non_docs_changes" ]; then
        echo "Only docs/ files changed - skipping changelog check"
        exit 0
    fi

    if echo "$changed_files" | grep -q '^CHANGELOG.md$'; then
        echo "CHANGELOG.md was updated"
    else
        echo "Error: CHANGELOG.md was not updated"
        exit 1
    fi

# Run security scan
# B404, B603, B607: subprocess used for running setup/teardown scripts in evals
security:
    uv run bandit -r skillet/ --skip B101,B105,B311,B324,B404,B603,B607 -x '*_test.py'

# Run type checker
typecheck:
    uv run ty check skillet/

# Build .claude/commands/ from templates
build-claude:
    uv run python scripts/build_claude_config.py

# Run unit tests
test-unit *args:
    uv run pytest {{args}}

# Run tests with coverage (fails if under threshold)
test-cov:
    uv run pytest --cov --cov-report=term-missing

# Run tests with coverage for CI (outputs XML)
test-ci:
    uv run pytest --cov --cov-report=xml


# Run integration tests
test-integration:
    uv run pytest tests/integration/

# Run e2e tests
test-e2e:
    uv run pytest tests/e2e/

# Watch unit tests only
test-unit-watch *args:
    uv run ptw --now skillet skillet/ {{args}}

# Watch integration tests only
test-integration-watch *args:
    uv run ptw --now tests/integration tests/integration/ {{args}}

# Watch e2e tests only
test-e2e-watch *args:
    uv run ptw --now tests/e2e tests/e2e/ {{args}}
