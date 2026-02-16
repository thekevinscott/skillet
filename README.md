# skillet

[![CI](https://github.com/thekevinscott/skillet/actions/workflows/test.yml/badge.svg)](https://github.com/thekevinscott/skillet/actions/workflows/test.yml)
[![License](https://img.shields.io/github/license/thekevinscott/skillet)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Evaluation-driven Claude Code skill development.

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

## Workflow

### 1. Capture evals with `/skillet:add`

When Claude does something wrong, capture it:

```
> Write a code review comment for this SQL query...

Claude: This code has a SQL injection vulnerability...

> /skillet:add

Claude: What did you expect instead?

> Should start with **issue** (blocking): using conventional comments format

Claude: Eval saved to ~/.skillet/evals/conventional-comments/001.yaml
```

### 2. Run baseline eval

```bash
skillet eval conventional-comments
```

```
Eval Results (baseline, no skill)
==================================
Evals: 5
Samples: 3 per eval
Total runs: 15

Pass rate: 0% (0/15)
```

### 3. Create the skill

```bash
skillet create conventional-comments
```

```
Found 5 evals for 'conventional-comments', drafting SKILL.md...

Created ~/.claude/skills/conventional-comments/
└── SKILL.md (draft from 5 evals)
```

### 4. Eval with skill

```bash
skillet eval conventional-comments ~/.claude/skills/conventional-comments
```

```
Eval Results (with skill)
=========================
Skill: ~/.claude/skills/conventional-comments
Evals: 5
Samples: 3 per eval
Total runs: 15

Pass rate: 80% (12/15)
```

### 5. Tune the skill

```bash
skillet tune conventional-comments ~/.claude/skills/conventional-comments
```

```
Round 1/5: Pass rate 80% (12/15)
  Improving skill...
Round 2/5: Pass rate 93% (14/15)
  Improving skill...
Round 3/5: Pass rate 100% (15/15)
  Target reached!

Best skill saved to ~/.claude/skills/conventional-comments/SKILL.md
```

## Commands

```bash
skillet eval <name> [skill]         # run evals (baseline or with skill)
skillet create <name>               # create skill from evals
skillet tune <name> <skill>         # iteratively improve skill
skillet compare <name> <skill>      # compare baseline vs skill from cache
skillet show <name>                 # inspect cached eval results
skillet lint <path>                 # lint a SKILL.md for common issues
skillet generate-evals <skill>      # generate candidate evals from a skill
```

## Evals

Evals are stored in `~/.skillet/evals/<name>/`:

```yaml
# ~/.skillet/evals/conventional-comments/001.yaml
timestamp: 2025-01-15T10:30:00Z
name: conventional-comments
prompt: "Write a code review comment for..."
expected: "Should start with **issue** (blocking):"
```

## Python API

```python
import asyncio
from pathlib import Path
from skillet import evaluate

async def main():
    # Baseline (no skill)
    baseline = await evaluate("conventional-comments")
    print(f"Baseline: {baseline['pass_rate']}%")

    # With skill
    result = await evaluate(
        "conventional-comments",
        skill_path=Path("~/.claude/skills/conventional-comments").expanduser(),
    )
    print(f"With skill: {result['pass_rate']}%")

asyncio.run(main())
```

Tune a skill programmatically:

```python
from skillet import tune
from skillet.tune import TuneConfig

result = await tune(
    "conventional-comments",
    Path("~/.claude/skills/conventional-comments").expanduser(),
    config=TuneConfig(max_rounds=10, target_pass_rate=90.0),
)
print(f"Final pass rate: {result.result.final_pass_rate}%")
```

See the [Python API reference](https://skillet.run/reference/python-api) for all functions and options.

## Documentation

Full documentation available at the [docs site](https://skillet.run):

- [Getting Started](https://skillet.run/getting-started)
- [Concepts](https://skillet.run/concepts/skills-vs-agents) — Skills vs agents, capability vs regression, balanced problem sets
- [CLI Reference](https://skillet.run/reference/cli)
- [Eval Format](https://skillet.run/reference/eval-format)
- [Python API](https://skillet.run/reference/python-api)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for future ideas and planned features.

## License

MIT
