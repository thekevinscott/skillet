# Skill Analysis

Analysis notebooks for exploring skill data.

## Data

Dataset lives in `data/` (gitignored). Download with:

```bash
uvx kaggle datasets download thekevinscott/github-skill-files -p data/ --unzip
```

Three parquet files:
- `files.parquet` — 42k+ SKILL.md files with URLs, paths, repo keys
- `repos.parquet` — 6.5k+ repos with stars, language, topics, license
- `history.parquet` — commit history per file (first/last commit, total commits)

Load with:
```python
import polars as pl
files = pl.read_parquet("data/files.parquet")
repos = pl.read_parquet("data/repos.parquet")
history = pl.read_parquet("data/history.parquet")
df = files.join(repos, on="repo_key")
```

## Marimo Notebooks

Analysis notebooks are in `notebooks/`.

### Running the Server

For remote access (e.g., via Tailscale), bind to all interfaces:

```bash
uv run marimo edit notebooks/ --port 2718 --watch --host 0.0.0.0
```

- `--host 0.0.0.0`: Required for remote access (default is localhost only)
- `--watch`: Auto-reload when notebook files change on disk
- `--port 2718`: Custom port to avoid conflicts

### Capturing Notebook Output for Claude

Use the `/marimo-screenshot` skill to capture rendered notebook output (charts, tables) as a PNG that Claude can analyze.

See: `.claude/skills/marimo-screenshot/SKILL.md`

### Verification Rule

**After every change to a marimo notebook:**

1. **Verify syntax:**
   ```bash
   python -m py_compile notebooks/<notebook>.py
   ```

2. **Verify rendered output** (check for runtime errors like output size limits):
   ```bash
   pkill -f "marimo run.*2719" 2>/dev/null; true
   uv run marimo run notebooks/<notebook>.py --port 2719 --headless &
   sleep 15
   npx playwright screenshot --viewport-size="1280,3000" --wait-for-timeout 15000 \
     "http://localhost:2719" /tmp/notebook_check.png
   # Read /tmp/notebook_check.png to verify no errors
   pkill -f "marimo run.*2719"
   ```

Common runtime errors to watch for:
- **"Your output is too large"** - Sample data for charts (max ~5000 rows)
- **MaxRowsError** - Add `alt.data_transformers.disable_max_rows()`
- **Blank sections** - Check cell return values

### Variable Naming Convention

Marimo requires unique variable names across all cells. Use underscore-prefixed names (`_fig`, `_ax`, `_colors`) for local variables that don't need to be exported to other cells.
