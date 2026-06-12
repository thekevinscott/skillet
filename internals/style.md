# Code Style

## Module Organization

- **One function per file** — each `.py` file contains a single public function, named to match the file (`get_rate_color.py` contains `get_rate_color()`)
- **Multi-function files become packages** — when a file has multiple functions, promote it to a directory with `__init__.py` and one file per function
- **`__init__.py` exports only externally consumed symbols** — internal helpers stay unexported
- **Drop redundant suffixes inside packages** — `judge/format_prompt.py`, not `judge/format_prompt_for_judge.py`
- **Dataclass, type, model, and exception files are exempt** — grouping related types in a single file is fine
- **Co-located tests** — `foo.py` → `foo_test.py` in the same directory

## Docstrings
- **Skip `Args:`, `Returns:`, `Raises:` sections** - these are statically analyzable from type hints
- Use docstrings for *why* and *what*, not *how* the signature works
- One-liner docstrings for simple functions; multi-line only when behavior needs explanation

## Type Hints
- **Prefer fixing type issues over `# type: ignore`** - investigate the root cause first

```python
# Good
def query_structured[T: BaseModel](prompt: str, model: type[T]) -> T:
    """Query Claude and return a validated Pydantic model."""

# Avoid
def query_structured[T: BaseModel](prompt: str, model: type[T]) -> T:
    """Query Claude and return a validated Pydantic model.

    Args:
        prompt: The prompt to send
        model: A Pydantic model class

    Returns:
        An instance of the model
    """
```
