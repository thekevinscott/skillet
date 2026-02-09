# Skill Analysis

Analysis notebooks for exploring skill data collected from GitHub.

## Setup

```bash
uv sync --all-extras
```

## Running Notebooks

Start the marimo server:

```bash
uv run marimo edit notebooks/ --port 2718 --watch
```

For remote access via Tailscale:

```bash
uv run marimo edit notebooks/ --port 2718 --watch --host 0.0.0.0
```

## Data

Analysis uses data in `results/` (gitignored, kept locally only).
