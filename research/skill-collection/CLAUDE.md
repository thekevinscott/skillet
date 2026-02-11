# Skill Analysis

Analysis notebooks for exploring skill data.

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

### Verification Rule (MANDATORY)

**After every change to a marimo notebook, you MUST verify both syntax and rendered output before reporting success.** Do not skip this step. Use the `/marimo-screenshot` skill to capture and review the rendered notebook.

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

3. **Review the screenshot** — actually look at the PNG output. Check that:
   - Charts render with visible data (not blank or crushed)
   - No "Your output is too large" errors
   - No Python tracebacks
   - Layout looks reasonable

Common runtime errors to watch for:
- **"Your output is too large"** - Pre-aggregate data before passing to Altair (numpy histogram → small DataFrame). Never pass raw DataFrames with >5000 rows to Altair.
- **MaxRowsError** - Add `alt.data_transformers.disable_max_rows()`
- **Blank sections** - Check cell return values

### Variable Naming Convention

Marimo requires unique variable names across all cells. Use underscore-prefixed names (`_fig`, `_ax`, `_colors`) for local variables that don't need to be exported to other cells.
