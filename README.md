# skillet

[![CI](https://github.com/thekevinscott/skillet/actions/workflows/test.yml/badge.svg)](https://github.com/thekevinscott/skillet/actions/workflows/test.yml)
[![License](https://img.shields.io/github/license/thekevinscott/skillet)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Evaluation-driven Claude Code skill development.

## Install

```bash
pip install skillet
```

## Why

Anthropic recommends building evaluations before writing skills:

> Create evaluations BEFORE writing extensive documentation. This ensures your Skill solves real problems rather than documenting imagined ones.

But they don't provide tooling:

> We do not currently provide a built-in way to run these evaluations.

skillet fills that gap.

## Workflow

### 1. Capture gaps with `/gap`

When Claude does something wrong, capture it:

```
> Write a code review comment for this SQL query...

● This code has a SQL injection vulnerability...

> /gap

● What did you expect instead?

> Should start with **issue** (blocking): using conventional comments format

● Gap saved to ~/.skillet/gaps/conventional-comments/001.yaml
```

### 2. Run baseline eval

```bash
skillet eval conventional-comments
```

```
Eval Results (baseline, no skill)
==================================
Gaps: 5
Iterations: 3 per gap
Total runs: 15

Pass rate: 0% (0/15)
```

### 3. Create the skill

```bash
skillet new conventional-comments
```

```
Found 5 gaps for 'conventional-comments', drafting SKILL.md...

Created plugins/conventional-comments/
├── .claude-plugin/
│   └── plugin.json
└── skills/conventional-comments/
    └── SKILL.md (draft from 5 gaps)
```

### 4. Eval with skill

```bash
skillet eval conventional-comments --skill plugins/conventional-comments
```

```
Eval Results (with skill)
=========================
Skill: plugins/conventional-comments
Gaps: 5
Iterations: 3 per gap
Total runs: 15

Pass rate: 80% (12/15)
```

### 5. Iterate

Edit SKILL.md, re-run eval, repeat.

## Commands

```bash
skillet eval <name>                    # baseline eval (no skill)
skillet eval <name> --skill <path>     # eval with skill
skillet new <name>                     # create skill from gaps
```

## Gaps

Gaps are stored in `~/.skillet/gaps/<name>/`:

```yaml
# ~/.skillet/gaps/conventional-comments/001.yaml
timestamp: 2025-01-15T10:30:00Z
prompt: "Write a code review comment for..."
actual: "This code has a SQL injection..."
expected: "Should start with **issue** (blocking):"
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for future ideas and planned features.

## License

MIT
