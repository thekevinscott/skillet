# Getting Started

This guide walks you through installing Skillet and creating your first evaluation-driven skill.

## Installation

Install Skillet using pip:

```bash
pip install pyskillet
```

## Core Concepts

**Evals** are test cases that capture when Claude Code produces suboptimal results. Each eval contains:
- A prompt (what you asked)
- An expected behavior (what you wanted)

**Skills** are Claude Code SKILL.md files that provide context and instructions to improve Claude's responses.

**Tuning** is the iterative process of improving a skill based on eval results.

## Step 1: Capture Evals

When Claude Code does something wrong, capture it using the `/skillet:add` slash command:

```
> Write a code review comment for this SQL query...

Claude: This code has a SQL injection vulnerability...

> /skillet:add

Claude: What behavior or format did you expect?

> Should start with **issue** (blocking): using conventional comments format

Claude: Eval saved to ~/.skillet/evals/conventional-comments/001.yaml
```

Capture several examples (3-5 is a good starting point) before moving on.

## Step 2: Run Baseline Eval

Test how Claude performs without a skill:

```bash
skillet eval conventional-comments
```

```
Eval Results (baseline, no skill)
=================================
Evals: 5
Samples: 3 per eval
Total runs: 15

Pass rate: 0% (0/15)
```

## Step 3: Create a Skill

Generate a skill from your captured evals:

```bash
skillet create conventional-comments
```

```
Found 5 evals for 'conventional-comments', drafting SKILL.md...

Created ~/.claude/skills/conventional-comments/
└── SKILL.md (draft from 5 evals)
```

## Step 4: Eval with Skill

Test with the skill loaded:

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

## Step 5: Tune the Skill

Use `tune` to automatically improve the skill:

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

The `tune` command iteratively:
1. Runs evals against the current skill
2. Analyzes failures
3. Generates an improved skill
4. Repeats until target pass rate or max rounds

## Next Steps

- [CLI Reference](/reference/cli) — All commands and flags
- [Eval Format](/reference/eval-format) — YAML schema for eval files
- [Capture with /skillet:add](/guides/capture-with-slash-command) — Detailed guide on capturing evals
- [Python API](/reference/python-api) — Programmatic usage
