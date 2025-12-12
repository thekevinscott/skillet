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

# Run tests
test *args:
    uv run pytest {{args}}

# Run tests with coverage
test-cov:
    uv run pytest --cov --cov-report=term-missing

# Install pre-commit hooks
hooks:
    uv run pre-commit install

# Check changelog was updated (for CI)
check-changelog base_ref='origin/main':
    #!/usr/bin/env bash
    if git diff --name-only {{base_ref}}...HEAD | grep -q '^CHANGELOG.md$'; then
        echo "CHANGELOG.md was updated"
    else
        echo "Error: CHANGELOG.md was not updated"
        exit 1
    fi
