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

Download the dataset from Kaggle:

```bash
uvx kaggle datasets download thekevinscott/github-skill-files -p data/ --unzip
```

This creates `data/` with three parquet files (`files.parquet`, `repos.parquet`, `history.parquet`). See `data/README.md` after download for schema details.

Legacy analysis artifacts live in `results/` (gitignored).
