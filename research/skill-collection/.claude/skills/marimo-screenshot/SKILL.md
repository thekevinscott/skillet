---
name: marimo-screenshot
description: Capture rendered marimo notebook output as a screenshot for analysis
---

# Marimo Screenshot

Capture a marimo notebook's rendered output (charts, tables, markdown) as a PNG screenshot that Claude can view and analyze.

## Usage

When the user wants you to see notebook output, or when you need to analyze charts/visualizations in a marimo notebook.

## Workflow

1. **Start the notebook in run mode** (executes cells, serves rendered output):
   ```bash
   uv run marimo run notebooks/<notebook>.py --port 2719 --headless &
   ```

2. **Wait for server to start:**
   ```bash
   sleep 10
   ```

3. **Take screenshot with JS render time** (Altair/Vega charts need ~15s):
   ```bash
   npx playwright screenshot --wait-for-timeout 15000 --full-page \
     "http://localhost:2719" /tmp/marimo_output.png
   ```

4. **Read the screenshot** using the Read tool:
   ```
   Read /tmp/marimo_output.png
   ```

5. **Kill the server when done:**
   ```bash
   pkill -f "marimo run.*2719"
   ```

## Key Details

- Use `marimo run` (not `edit`) - this executes cells and renders output
- `--headless` runs server-only without opening a browser
- `--wait-for-timeout 15000` gives charts time to render via JavaScript
- `--full-page` captures the entire scrollable notebook
- Port 2719 avoids conflict with the user's edit server on 2718

## Troubleshooting

**Charts not appearing:**
- Cells must *return* their output (e.g., `mo.vstack([chart])` as the last expression)
- If inside if/else, ensure all branches return a value

**Blank screenshot:**
- Increase `--wait-for-timeout` to 20000 or more
- Check that the notebook runs without errors: `uv run marimo run notebook.py`

**Port in use:**
- Kill existing process: `pkill -f "marimo run.*2719"`
- Or use a different port
