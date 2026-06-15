# skillet

[![CI](https://github.com/thekevinscott/skillet/actions/workflows/test.yml/badge.svg)](https://github.com/thekevinscott/skillet/actions/workflows/test.yml)
[![License](https://img.shields.io/github/license/thekevinscott/skillet)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Evaluation-driven Claude Code skill development.

Three levels of documentation:

1. This README — the concise overview, mirroring the structure below
2. [`docs/`](docs/) — full markdown documentation, shipped with the package
3. [skillet.run](https://skillet.run) — the rendered docs site, 1:1 with `docs/`

## Install

```bash
pip install pyskillet
```

## Why

Anthropic [recommends building evaluations before writing skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#build-evaluations-first):

> Create evaluations BEFORE writing extensive documentation. This ensures your Skill solves real problems rather than documenting imagined ones.

But they don't provide tooling:

> We do not currently provide a built-in way to run these evaluations.

skillet fills that gap.

## Quick Start

Capture failures with `/skillet:add` in Claude Code, then run the loop:

```bash
skillet eval my-skill                              # baseline
skillet create my-skill                            # generate skill from evals
skillet eval my-skill ~/.claude/skills/my-skill    # eval with skill
skillet tune my-skill ~/.claude/skills/my-skill    # iteratively improve
```

## Overview

Skillet captures failures, runs systematic evaluations, and iterates on skills with quantitative feedback. [→ `docs/index.md`](docs/index.md)

## Getting Started

End-to-end walkthrough from your first capture to a tuned skill. [→ `docs/getting-started.md`](docs/getting-started.md)

## Concepts

### Skills vs Agents

Skillet evaluates *skills* (instructions that shape behavior), not *agents* (the underlying capability). [→ `docs/concepts/skills-vs-agents.md`](docs/concepts/skills-vs-agents.md)

### Capability vs Regression

The same eval format serves two purposes: capability (`pass@k`, exploratory) during development, regression (`pass^k`, strict) in CI. [→ `docs/concepts/capability-vs-regression.md`](docs/concepts/capability-vs-regression.md)

### Balanced Problem Sets

A good eval suite needs negative cases — prompts where the skill should *not* trigger — to catch overtriggering. [→ `docs/concepts/balanced-problem-sets.md`](docs/concepts/balanced-problem-sets.md)

## Guides

### Capture with /skillet:add

Use `/skillet:add` in Claude Code to record failures as YAML eval files. [→ `docs/guides/capture-with-slash-command.md`](docs/guides/capture-with-slash-command.md)

### Linting

`skillet lint <path>` checks a `SKILL.md` against 14 rules covering naming, frontmatter, body length, and recommended fields. [→ `docs/guides/linting.md`](docs/guides/linting.md)

### Contributing

Development setup, testing strategy, code style, and PR conventions. [→ `docs/guides/contributing.md`](docs/guides/contributing.md)

## Reference

### CLI

`skillet` ships with `eval`, `create`, `tune`, `lint`, and `generate-evals`. [→ `docs/reference/cli.md`](docs/reference/cli.md)

### Eval Format

YAML schema for eval files: required `name`/`prompt`/`expected`, optional `domain`/`setup`/`teardown`. [→ `docs/reference/eval-format.md`](docs/reference/eval-format.md)

### Python API

Programmatic interface: `evaluate()`, `tune()`, `create_skill()`, `generate_evals()`, `lint_skill()`. [→ `docs/reference/python-api.md`](docs/reference/python-api.md)
