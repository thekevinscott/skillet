# Python API

Programmatic interface for Skillet.

## Installation

```bash
pip install pyskillet
```

## Quick Start

```python
import asyncio
from skillet import evaluate, tune, create_skill

# Run evals
results = asyncio.run(evaluate("my-skill"))
print(f"Pass rate: {results['pass_rate']}%")
```

## Functions

### evaluate()

Run evaluations against a baseline or with a skill.

```python
async def evaluate(
    name: str,
    skill_path: Path | None = None,
    samples: int = 3,
    max_evals: int | None = None,
    allowed_tools: list[str] | None = None,
    parallel: int = 3,
    on_status: Callable | None = None,
    skip_cache: bool = False,
) -> dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Eval set name or path |
| `skill_path` | Path | None | Path to skill (None for baseline) |
| `samples` | int | 3 | Iterations per eval |
| `max_evals` | int | None | Max evals to run (random sample) |
| `allowed_tools` | list | None | Restrict available tools |
| `parallel` | int | 3 | Parallel workers |
| `on_status` | Callable | None | Progress callback |
| `skip_cache` | bool | False | Ignore cached results |

**Returns:**

```python
{
    "results": list[dict],      # Per-iteration results
    "tasks": list[dict],        # Original task definitions
    "pass_rate": float,         # Percentage (0-100)
    "total_runs": int,
    "total_pass": int,
    "cached_count": int,
    "fresh_count": int,
    "total_evals": int,
    "sampled_evals": int,
}
```

**Example:**

```python
import asyncio
from pathlib import Path
from skillet import evaluate

async def main():
    # Baseline
    baseline = await evaluate("conventional-comments")
    print(f"Baseline: {baseline['pass_rate']}%")

    # With skill
    with_skill = await evaluate(
        "conventional-comments",
        skill_path=Path("~/.claude/skills/conventional-comments").expanduser(),
    )
    print(f"With skill: {with_skill['pass_rate']}%")

asyncio.run(main())
```

### tune()

Iteratively improve a skill using DSPy optimization.

```python
async def tune(
    name: str,
    skill_path: Path,
    config: TuneConfig | None = None,
    callbacks: TuneCallbacks | None = None,
) -> TuneResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Eval set name |
| `skill_path` | Path | required | Path to skill |
| `config` | TuneConfig | None | Tuning options |
| `callbacks` | TuneCallbacks | None | Progress callbacks |

**TuneConfig:**

```python
from dataclasses import dataclass

@dataclass
class TuneConfig:
    max_rounds: int = 5
    target_pass_rate: float = 100.0
    samples: int = 1
    parallel: int = 3
```

**TuneResult:**

```python
@dataclass
class TuneResult:
    metadata: TuneMetadata       # Timestamps, paths
    config: TuneConfig           # Input config
    result: TuneResultSummary    # Success, final pass rate
    original_skill: str          # Original content
    best_skill: str              # Best found
    rounds: list[RoundResult]    # All rounds
```

**Example:**

```python
import asyncio
from pathlib import Path
from skillet import tune
from skillet.tune import TuneConfig

async def main():
    result = await tune(
        "conventional-comments",
        Path("~/.claude/skills/conventional-comments").expanduser(),
        config=TuneConfig(
            max_rounds=10,
            target_pass_rate=90.0,
        ),
    )
    print(f"Final pass rate: {result.result.best_pass_rate}%")
    print(f"Rounds: {len(result.rounds)}")

asyncio.run(main())
```

### create_skill()

Generate a skill from captured evals.

```python
async def create_skill(
    name: str,
    output_dir: Path,
    extra_prompt: str | None = None,
    overwrite: bool = False,
) -> dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Eval set name |
| `output_dir` | Path | required | Base directory for skill |
| `extra_prompt` | str | None | Additional generation instructions |
| `overwrite` | bool | False | Replace existing skill |

**Returns:**

```python
{
    "skill_dir": Path,         # Created skill directory
    "skill_content": str,      # Generated SKILL.md content
    "eval_count": int,         # Evals used
}
```

**Example:**

```python
import asyncio
from pathlib import Path
from skillet import create_skill

async def main():
    result = await create_skill(
        "conventional-comments",
        Path.home(),  # Creates ~/.claude/skills/conventional-comments/
        extra_prompt="Be concise, max 30 lines",
    )
    print(f"Created: {result['skill_dir']}")

asyncio.run(main())
```

## Exceptions

```python
from skillet import (
    SkilletError,           # Base exception
    EvalError,              # Eval loading/processing error
    EvalValidationError,    # Invalid eval format
    EmptyFolderError,       # No evals found
    SkillError,             # Skill creation error
)
```

**Example:**

```python
from skillet import evaluate, SkilletError

try:
    results = await evaluate("nonexistent")
except SkilletError as e:
    print(f"Skillet error: {e}")
```

## Callbacks

### Progress Callback for evaluate()

```python
async def on_status(task: dict, state: str, result: dict | None):
    """
    task: The eval task being run
    state: "cached", "running", or "done"
    result: Result dict when state is "done"
    """
    if state == "running":
        print(f"Running: {task['eval_source']}")
    elif state == "done":
        status = "PASS" if result["pass"] else "FAIL"
        print(f"  {status}: {result['judgment']['reasoning'][:50]}")
```

### Callbacks for tune()

```python
from skillet.tune import TuneCallbacks

callbacks = TuneCallbacks(
    on_round_start=lambda round, total: print(f"Round {round}/{total}"),
    on_round_complete=lambda round, rate, results: print(f"  Pass rate: {rate}%"),
    on_improved=lambda instruction, path: print(f"  Improved: {path}"),
    on_complete=lambda path: print(f"Done! Best skill: {path}"),
)
```
