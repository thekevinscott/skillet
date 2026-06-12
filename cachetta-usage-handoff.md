# Handoff: cachetta usage review

**Date:** 2026-06-12
**Scope:** Compare skillet's use of [`cachetta`](https://github.com/thekevinscott/cachetta) against the patterns prescribed in `docs/llm/python/index.md`, and flag cleanups.
**Method:** Read the doc (via fetched summary) and verified the API against the **installed source** of `cachetta` 0.6.x (ground truth), then traced skillet's full cache stack.

---

## TL;DR

We use a **valid, prescribed recipe** at the leaf (custom path lambda), and the `read_cache`/`write_cache` calls are correct. But we bypass most of what cachetta offers — it's effectively reduced to an atomic-pickle (de)serializer with a hand-built key/dir layer on top. Nothing is broken *because* of cachetta, but there are three concrete cleanups plus one latent bug found while tracing.

**Verdict: partially as prescribed.**

---

## What cachetta prescribes

### Setup pattern: central root cache + scoped sub-caches
```python
# config.py
cache = Cachetta(path=Path.home() / '.cache' / 'my-lib')
# elsewhere
function_cache = cache / 'my-function'   # `/` preserves duration etc. via dataclass replace()
```

### Three leaf recipes
1. **Fixed path** — `Cachetta(path="x.cache")`, one named file.
2. **Hashed by args** — `Cachetta(path="dir/x.cache")` + pass args to `read`/`write`; cachetta auto-hashes the args (`json.dumps` → sha256, first 16 hex) into the filename. *(cachetta source: `cachetta.py` `_get_path`)*
3. **Custom path lambda** — `Cachetta(path=lambda ...: ...)` to build the path from *selected* args, dropping clients/loggers/knobs like `temperature`.

### Capabilities the index page undersells (in the linked reference)
- `duration` (default **7 days**), `lru_size`, `stale_duration` (stale-while-revalidate), `condition`
- Atomic, corrupt-tolerant writes (tempfile + `os.replace`; corrupt reads yield `None`)
- **Async variants**: `async_read_cache` / `async_write_cache` (delegate disk I/O to threads)
- Lifecycle helpers: `invalidate`/`clear`, `exists`, `age`, `info` (+ async)
- Decorator usage: `@Cachetta(path=...)`, `.wrap(fn)`, `.copy(**kwargs)`

---

## What skillet actually does

The only real `Cachetta` instance is one leaf cache (`skillet/_internal/cache/get_cached_iterations.py:8`):
```python
_iter_cache = Cachetta(
    path=lambda cache_dir, iteration: cache_dir / f"iter-{iteration}.cache",
    duration=timedelta(days=36500),
)
```
Used via `write_cache(_iter_cache, result, cache_dir, iteration)` (`save_iteration.py:12`) and
`read_cache(_iter_cache, cache_dir, iteration)` (`get_cached_iterations.py:22`).

Everything else is hand-rolled around it:
- `~/.skillet/cache/<name>/<eval-key>/{baseline,skills/<hash>}` tree built by hand in `get_cache_dir.py`, `get_all_cached_results.py`, `get_cached_results_for_eval.py`
- Key hashing: `eval_cache_key.py`, `hash_content.py`, `hash_directory.py`, `hash_file.py`, `normalize_cache_name.py`
- Base dir: `config.CACHE_DIR` is a plain `Path` (`config.py:5`)
- File enumeration via `glob("iter-*.cache")`
- Cross-worker coordination via `skillet/_internal/lock.py` (`cache_lock`)

---

## Aligned vs. deviations

**Aligned**
- Leaf cache uses the **custom-path-lambda recipe**.
- `write_cache` / `read_cache` pass args through to the lambda correctly (context-manager usage matches the docs).

**Deviations**

| # | Deviation | Justified? | Action |
|---|-----------|-----------|--------|
| 1 | **No central root cache / no `/` operator.** `config.CACHE_DIR` is a plain `Path`; dir tree built by hand in 3 places; lambda is trivial (`dir / filename`). cachetta is reduced to a pickle (de)serializer. | Spirit deviation — works, but skips the prescribed setup pattern. | Optional larger refactor (own PR). |
| 2 | **Reinvents key hashing** (`eval_cache_key`, `hash_content`, `hash_directory`) vs. cachetta's auto-arg-hashing. | *Partly justified*: skillet needs **content-addressed** hashing of skill **directory contents**. cachetta's auto-hash does `json.dumps(args, default=str)`, so a `Path` arg hashes the path **string**, not its contents — it can't detect skill edits. `hash_directory` is genuinely needed; only the eval-key string hashing overlaps. | Leave as-is; document rationale. |
| 3 | **`duration=timedelta(days=36500)`** (100 yrs) to fake "never expire". | Skillet is content-addressed (inputs change → path changes → stale entries are never looked up), so TTL is the wrong axis and "no expiry" is correct — but the magic number is a smell. cachetta has no `duration=None` sentinel. | Add a comment explaining it, and/or file an upstream request for a no-expiry sentinel. |
| 4 | **Sync `read_cache`/`write_cache` inside `async run_single_eval`** (`run_single_eval.py:40,122`). Blocks the event loop on pickle I/O; cachetta ships `async_read_cache`/`async_write_cache` for exactly this. | Low-risk perf win, esp. with parallel workers. | Quick win — switch to async variants. |
| 5 | **Unused lifecycle API.** Manual `cache_dir.exists()` + `glob` instead of `exists()`/`info()`/`invalidate()`. | Fine, just not leveraged. | Optional. |

---

## Latent bug found while tracing (not cachetta-related)

**Writer normalizes the name; one reader doesn't.**
- Writer: `get_cache_dir.py:17` → `config.CACHE_DIR / normalize_cache_name(name) / eval_key`
- Reader: `get_all_cached_results.py:17` → `normalize_cache_name(name)` ✅
- Reader: `compare/get_cached_results_for_eval.py:16` → `config.CACHE_DIR / name / eval_key` ❌ (raw `name`)

`normalize_cache_name` rewrites a name to its resolved dir basename **when the name is an existing path** (`normalize_cache_name.py:9`). So passing a path-like `name` makes the compare flow read `…/<full-path>/…` while results were written to `…/<basename>/…` → **silent cache miss**.

**Fix:** use `normalize_cache_name(name)` in `get_cached_results_for_eval.py`. Add a regression test that passes a path-like `name`.

---

## Coverage note

`tests/integration/conftest.py:118` fully mocks cachetta ("avoid depending on its pickle serialization"). So real cachetta is only exercised in unit/e2e tests — consistent with the "mock external deps in integration" rule, just noting the coverage shape.

---

## Recommended next steps (prioritized)

1. **Quick PR** — switch `run_single_eval` to `async_read_cache`/`async_write_cache` (#4) **and** fix the `normalize_cache_name` reader/writer mismatch (#3 bug above). Both self-contained; add tests + changelog (or `skip-changelog` for the async-internal part).
2. **Tiny** — comment the `duration=timedelta(days=36500)` rationale; consider an upstream `duration=None` request (#3).
3. **Optional larger refactor (own PR)** — adopt the root-cache + `/` sub-cache pattern (#1), moving path/key construction into cachetta where it doesn't conflict with content-addressing (#2 caveat).

---

## Key file references

**skillet**
- `skillet/config.py:5` — `CACHE_DIR`
- `skillet/_internal/cache/get_cached_iterations.py:8,22` — `_iter_cache`, read
- `skillet/_internal/cache/save_iteration.py:12` — write
- `skillet/_internal/cache/get_cache_dir.py:17` — normalized writer path
- `skillet/_internal/cache/get_all_cached_results.py:17` — normalized reader
- `skillet/compare/get_cached_results_for_eval.py:16` — **un-normalized reader (bug)**
- `skillet/_internal/cache/normalize_cache_name.py:9` — normalization logic
- `skillet/eval/evaluate/run_single_eval.py:40,122` — sync cache calls in async fn
- `tests/integration/conftest.py:118` — cachetta mocked

**cachetta 0.6.x (installed source)**
- `cachetta/cachetta.py` — `Cachetta` dataclass, `_get_path` (auto-hash), `__truediv__` (`/`), `duration` default 7d
- `cachetta/read_cache.py` — `read_cache`, `async_read_cache`, stale reads
- `cachetta/write_cache.py` — `write_cache` (atomic), `write_cache_ctx`, async variants
