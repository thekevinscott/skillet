---
name: git-commit-messages
description: Rules and workflow guidance for writing git commit messages across all repositories. Use when creating or reviewing commit messages, deciding commit granularity, or enforcing message format and prohibited patterns.
---

# Git Commit Messages

## Overview

Define the required format, style, and granularity for git commit messages.

## Rules

- Use English only.
- Use `type: summary` or `type(scope): summary`.
- Allow optional scope in parentheses when helpful (e.g., `feat(backend): ...`).
- Use only these types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`.
- Keep the message to a single line whenever possible.
- Ensure the change itself is small enough to be described by a single-line message.
- Start with a lowercase letter.
- Do not use emojis.
- Do not use `WIP` (uppercase or lowercase) in git commit messages.
- Allow `wip` only for `jj` change descriptions.

## Repository Scope and VCS Behavior

- Apply these rules to all repositories.
- If a repository has a `.jj` directory, agents must prefer `jj` for operations.
- Humans may continue to use `git` even when `.jj` exists.

## Examples

- `feat: add wezterm title bar controls`
- `fix(backend): handle nil config`
- `docs: update setup notes`
- `refactor: simplify config loading`
