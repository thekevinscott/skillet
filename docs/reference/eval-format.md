# Eval Format

Complete YAML schema reference for Skillet eval files.

## File Location

Evals are stored in `~/.skillet/evals/<name>/` by default, or any directory you specify. Each eval is a single YAML file.

```
~/.skillet/evals/
  browser-fallback/
    001.yaml
    002.yaml
    003.yaml
  conventional-comments/
    001.yaml
    002.yaml
```

## Required Fields

Every eval file must include these fields:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp (e.g., `2025-01-15T10:30:00Z`) |
| `name` | string | Eval category name |
| `prompt` | string or list | The prompt(s) to send to Claude |
| `expected` | string | What Claude should do (evaluation criteria) |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `actual` | string | Claude's response (for reference, not used in eval) |
| `setup` | string | Bash script run before eval **(alpha)** |
| `teardown` | string | Bash script run after eval **(alpha)** |

## Basic Example

```yaml
timestamp: 2025-01-15T10:30:00Z
name: conventional-comments
prompt: "Write a code review comment for: SELECT * FROM users WHERE id = $1"
expected: |
  Should use conventional comments format:
  **issue** (blocking): description of the issue
  Not just describe the problem.
```

## Multi-Turn Prompts

The `prompt` field can be a list for multi-turn conversations:

```yaml
timestamp: 2025-01-15T10:30:00Z
name: browser-fallback
prompt:
  - "Fetch the content from https://example.com/data"
  - "The page requires JavaScript. Try again."
  - "Use a browser-based approach if needed."
expected: |
  Should recognize that WebFetch failed due to JavaScript
  and automatically switch to Playwright or similar tool.
```

Each prompt in the list is sent as a separate turn, with Claude's response from the previous turn as context.

## Setup and Teardown (Alpha)

::: warning Alpha Feature
Setup and teardown scripts are experimental. The API may change.
:::

Scripts run in an isolated HOME directory with a 30-second timeout.

```yaml
timestamp: 2025-01-15T10:30:00Z
name: suggest-folders
setup: |
  mkdir -p ~/.skillet/evals/existing-category
  touch ~/.skillet/evals/existing-category/001.yaml
  touch ~/.skillet/evals/existing-category/002.yaml
prompt: "/skillet:add"
expected: |
  Should suggest "existing-category" as an option
  since it already exists with 2 evals.
teardown: |
  rm -rf ~/.skillet/evals/existing-category
```

### Script Behavior

- **setup**: Runs before prompt execution. If it fails (non-zero exit), the eval is skipped.
- **teardown**: Runs after prompt execution. Failures are logged but don't fail the eval.
- **Isolation**: Scripts run in a temporary HOME directory, not your real home.
- **Timeout**: 30 seconds per script.
- **Confirmation**: Requires `--trust` flag or interactive confirmation.

## Schema Versioning (Future)

We may add a `schema_version` field in the future for format evolution:

```yaml
schema_version: 1  # Optional, defaults to 1
timestamp: 2025-01-15T10:30:00Z
name: my-eval
prompt: "..."
expected: "..."
```

Existing files without `schema_version` will be treated as version 1.

## Evaluation Criteria

The `expected` field is used by an LLM judge to determine pass/fail. Write clear, specific criteria:

### Good

```yaml
expected: |
  Should output valid JSON with fields: name, email, age.
  The age field must be a number, not a string.
```

### Too Vague

```yaml
expected: "Should work correctly"  # What does "correctly" mean?
```

### Tips

- Be specific about format, structure, and behavior
- Include both what should happen and what should NOT happen
- Mention edge cases if relevant
- The judge sees Claude's full response and tool calls

## File Naming

Skillet doesn't enforce naming conventions, but we recommend:

- Sequential numbers: `001.yaml`, `002.yaml`, etc.
- Zero-padded for sorting
- Descriptive subdirectories for organization:

```
~/.skillet/evals/
  browser-fallback/
    webfetch-failure/
      001.yaml
      002.yaml
    playwright-errors/
      001.yaml
```
