# Skill Analysis Notebooks

Exploratory data analysis of skill file content from the GitHub skill files dataset.

## Quick Start

```bash
cd research/skill-collection

# Install dependencies
uv sync --extra notebooks

# Build content features (runs once, ~5 min for 417k files)
uv run python -m analyze_skills.extract_features

# Start notebook server
uv run marimo edit notebooks/ --port 2718 --host 0.0.0.0
```

## Data Pipeline

```
~/work/skills-dataset/data/content/   (417k .md files, raw skill content)
        │
        ▼
  analyze_skills/extract_features.py  (scan + compute metrics)
        │
        ▼
  data/content_features.parquet       (one row per file, structural metrics)
        │
        ▼
  notebooks/01_quantitative.py        (reads parquet, renders charts)
```

Optional: `data/repo_classification.parquet` enables organic-vs-collection splits.

## Notebooks

| Notebook | Status | Focus |
|----------|--------|-------|
| `01_quantitative.py` | Active | Content shape: size, structure, frontmatter, organic vs collection |
| `02_qualitative.py` | Stub | LLM-based: purpose taxonomy, quality scoring, archetypes |
| `03_evaluation.py` | Stub | Skillet eval integration: pass rates, feature correlations |

### 01_quantitative.py -- Content Shape Analysis

Deterministic metrics computed from file content:
- Summary statistics (bytes, words, lines, paragraphs, headings, code blocks, URLs)
- Size distributions (word count, line count histograms)
- Frontmatter adoption rate and field frequency
- Markdown structure breakdown
- Random sample viewer (full skill text for calibration)
- Organic vs collection comparison (requires `repo_classification.parquet`)

### 02_qualitative.py -- LLM-Based Analysis (stub)

Placeholder for analysis requiring LLM calls:
- Purpose taxonomy (automation, guidance, meta, enforcement)
- Quality/sophistication scoring (1-5 scale)
- Content pattern detection (has_examples, has_when_to_use)
- Archetype discovery via embeddings + clustering

### 03_evaluation.py -- Skillet Eval Integration (stub)

Placeholder for eval results analysis:
- Pass rates per skill
- Structural features vs effectiveness correlation
- Failure mode categorization

## Content Features Schema

| Column | Type | Description |
|--------|------|-------------|
| url | str | GitHub blob URL (join key) |
| bytes | int | File size in bytes |
| words | int | `len(text.split())` |
| lines | int | `text.count('\n') + 1` |
| paragraphs | int | Blank-line-delimited blocks |
| heading_count | int | Lines starting with `#` |
| max_heading_depth | int | Max `#` count (1-6) |
| code_block_count | int | Count of ``` pairs |
| url_count | int | Markdown link count |
| has_frontmatter | bool | Starts with `---` |
| frontmatter_fields | list[str] | YAML keys if frontmatter present |

## Conventions

- Use `_` prefix for cell-local variables (marimo requirement)
- Use Altair for charts (not matplotlib)
- Call `alt.data_transformers.disable_max_rows()` for large datasets
- Pre-aggregate data before charting (max ~5000 rows to browser)
- Verify with `python -m py_compile notebooks/<notebook>.py` after changes
