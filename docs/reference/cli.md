# CLI Reference

Complete reference for Skillet command-line tools.

## eval

Run evaluations against a baseline or with a skill loaded.

```bash
skillet eval <name> [skill] [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Eval set name, directory path, or single `.yaml` file |
| `skill` | No | Path to skill directory (omit for baseline) |

The `name` argument accepts:
- A name: looks in `~/.skillet/evals/<name>/`
- A directory path: loads all `.yaml` files recursively
- A single `.yaml` file path

### Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--samples` | `-s` | int | 3 | Number of iterations per eval |
| `--max-evals` | `-m` | int | all | Maximum evals to run (randomly sampled) |
| `--tools` | `-t` | str | all | Comma-separated list of allowed tools |
| `--parallel` | `-p` | int | 3 | Number of parallel workers |
| `--skip-cache` | | bool | false | Skip reading from cache (still writes) |
| `--trust` | | bool | false | Skip confirmation for setup/teardown scripts |

### Examples

```bash
# Baseline eval (no skill)
skillet eval browser-fallback

# Eval with skill
skillet eval browser-fallback ~/.claude/skills/browser-fallback

# Single file
skillet eval ./evals/my-skill/001.yaml skill/

# More samples for statistical confidence
skillet eval my-skill -s 5

# Random sample of 5 evals
skillet eval my-skill -m 5

# More parallelism
skillet eval my-skill -p 5

# Force fresh runs (ignore cache)
skillet eval my-skill --skip-cache

# Skip script confirmation prompts
skillet eval my-skill --trust

# Restrict available tools
skillet eval my-skill -t "Read,Write,Bash"
```

## tune

Iteratively improve a skill until target pass rate or max rounds.

```bash
skillet tune <name> <skill> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Eval set name or path |
| `skill` | Yes | Path to skill directory |

### Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--rounds` | `-r` | int | 5 | Maximum tuning rounds |
| `--target` | `-t` | float | 100.0 | Target pass rate percentage |
| `--samples` | `-s` | int | 1 | Samples per eval per round |
| `--parallel` | `-p` | int | 3 | Number of parallel workers |
| `--output` | `-o` | path | auto | Custom output path for results JSON |

### How It Works

1. Runs all evals against the current skill
2. Records pass rate and failure details
3. If pass rate < target, uses DSPy optimization to generate improved skill
4. Writes improved skill to disk
5. Repeats until target reached or max rounds

Results are saved to `~/.skillet/tunes/<name>/<timestamp>.json` (or custom path with `-o`).

### Examples

```bash
# Default tuning (5 rounds, 100% target)
skillet tune conventional-comments ~/.claude/skills/conventional-comments

# Aim for 80% pass rate
skillet tune conventional-comments skill/ -t 80

# More rounds
skillet tune conventional-comments skill/ -r 10

# Custom output file
skillet tune conventional-comments skill/ -o results.json

# Multiple samples for more reliable pass rates
skillet tune conventional-comments skill/ -s 3
```

## create

Create a new skill from captured evals.

```bash
skillet create <name> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Eval set name (from `~/.skillet/evals/<name>/`) |

### Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--dir` | `-d` | path | `~` | Base directory for output |
| `--prompt` | `-p` | str | none | Extra prompt to customize generation |

Output is written to `<dir>/.claude/skills/<name>/SKILL.md`.

### Examples

```bash
# Create in home directory (default)
skillet create browser-fallback
# Creates ~/.claude/skills/browser-fallback/SKILL.md

# Create in current directory
skillet create browser-fallback -d .
# Creates ./.claude/skills/browser-fallback/SKILL.md

# Create in specific project
skillet create browser-fallback -d /path/to/project

# Add extra instructions
skillet create browser-fallback -p "Be concise, max 20 lines"
```

## generate-evals

Generate candidate eval files from a SKILL.md.

```bash
skillet generate-evals <skill> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `skill` | Yes | Path to skill directory or SKILL.md file |

### Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--output` | `-o` | path | auto | Output directory for candidate files |
| `--max` | `-m` | int | 5 | Max evals per category |

### Examples

```bash
# Generate from skill directory
skillet generate-evals ~/.claude/skills/browser-fallback

# Custom output location
skillet generate-evals skill/ -o ./my-evals/

# Limit to 3 per category
skillet generate-evals skill/ -m 3
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid arguments, missing files, etc.) |
