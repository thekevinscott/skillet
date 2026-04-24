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

# Install git hooks (pre-commit and pre-push)
hooks:
    #!/usr/bin/env bash
    set -euo pipefail
    uv run pre-commit install
    hooks_dir="$(git rev-parse --git-common-dir)/hooks"
    cp scripts/hooks/pre-push "$hooks_dir/pre-push"
    chmod +x "$hooks_dir/pre-push"
    echo "Installed pre-push hook"

# Check changelog was updated (for CI)
# Skillet does not strictly follow semver, so every change requires a CHANGELOG entry.
# Escape hatch: add a `Skip-Changelog:` trailer to any commit in the PR.
check-changelog base_ref='origin/main':
    #!/usr/bin/env bash
    set -euo pipefail

    if git log --format='%(trailers:only=true)' {{base_ref}}..HEAD | grep -qi '^skip-changelog:'; then
        echo "Skipping changelog check (Skip-Changelog trailer present on a commit)"
        exit 0
    fi

    changed_files=$(git diff --name-only {{base_ref}}...HEAD)
    if echo "$changed_files" | grep -q '^CHANGELOG.md$'; then
        echo "CHANGELOG.md was updated"
    else
        echo "Error: CHANGELOG.md was not updated. Add an entry under [Unreleased], or include a 'Skip-Changelog: <reason>' trailer on a commit if this PR is genuinely changelog-irrelevant."
        exit 1
    fi

# Check MIGRATIONS.md was updated when the CHANGELOG diff adds a breaking-change entry.
# Heuristic: any added bullet in CHANGELOG.md starting with `- **Breaking` (case-
# insensitive) requires a corresponding MIGRATIONS.md edit. Mention the word
# "breaking" elsewhere in prose does not trigger.
# Escape hatch: add a `Skip-Migrations:` trailer to any commit in the PR when a
# breaking bullet genuinely needs no consumer-facing migration guidance.
check-migrations base_ref='origin/main':
    #!/usr/bin/env bash
    set -euo pipefail

    added_breaking=$(git diff {{base_ref}}...HEAD -- CHANGELOG.md | grep -ciE '^\+- \*\*breaking' || true)
    if [ "$added_breaking" = "0" ]; then
        echo "No '- **Breaking' bullets added to CHANGELOG.md — skipping migration check"
        exit 0
    fi

    if git log --format='%(trailers:only=true)' {{base_ref}}..HEAD | grep -qi '^skip-migrations:'; then
        echo "Skipping migration check (Skip-Migrations trailer present on a commit)"
        exit 0
    fi

    changed_files=$(git diff --name-only {{base_ref}}...HEAD)
    if echo "$changed_files" | grep -q '^MIGRATIONS.md$'; then
        echo "CHANGELOG.md adds a '- **Breaking' bullet and MIGRATIONS.md was updated"
    else
        echo "Error: CHANGELOG.md adds a '- **Breaking' bullet but MIGRATIONS.md was not updated. Add an entry under [Unreleased] in MIGRATIONS.md using the template at the bottom of that file, or include a 'Skip-Migrations: <reason>' trailer on a commit if consumers genuinely need no migration guidance."
        exit 1
    fi

# Run security scan
# B603, B607 scoped to inline nosec in run_script.py
security:
    uv run bandit -r skillet/ --skip B101,B105,B311,B404 -x '*_test.py'

# Check one-callable-per-file convention
check-conventions:
    uv run python scripts/check_one_function_per_file.py

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

# Run local CI checks (pre-push hook). Lint/format/typecheck in parallel, then unit tests.
# Integration tests run only on GitHub CI to keep local pushes fast.
ci:
    #!/usr/bin/env bash
    set -euo pipefail
    just lint &
    just format-check &
    just typecheck &
    just check-conventions &
    wait
    just test-unit

# Run full local CI including integration tests (no e2e)
ci-local:
    #!/usr/bin/env bash
    set -euo pipefail
    just lint &
    just format-check &
    just typecheck &
    just check-conventions &
    wait
    just test-unit &
    just test-integration &
    wait

# Run full local CI including e2e (slow, hits real LLMs)
ci-full:
    just ci-local
    just test-e2e

# Watch unit tests only
test-unit-watch *args:
    uv run ptw --now skillet skillet/ {{args}}

# Watch integration tests only
test-integration-watch *args:
    uv run ptw --now tests/integration tests/integration/ {{args}}

# Watch e2e tests only
test-e2e-watch *args:
    uv run ptw --now tests/e2e tests/e2e/ {{args}}
