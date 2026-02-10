"""Content shape analysis of skill files."""

import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md("""# Content Shape Analysis

    What do these skills actually look like? This notebook examines the structural
    properties of skill file content: size, markdown structure, frontmatter adoption,
    and how these vary between organic repos and skill collections.

    **Data source:** `data/content_features.parquet` (built by `analyze_skills/extract_features.py`)
    """)
    return (mo,)


@app.cell
def _(mo):
    from pathlib import Path

    import altair as alt
    import numpy as np
    import polars as pl

    alt.data_transformers.disable_max_rows()

    _data_dir = Path("data")
    _features_path = _data_dir / "content_features.parquet"
    _repo_class_path = _data_dir / "repo_classification.parquet"

    if not _features_path.exists():
        mo.stop(
            True,
            mo.md(
                "**Missing data.** Run `python -m analyze_skills.extract_features` first "
                f"to generate `{_features_path}`."
            ),
        )

    features = pl.read_parquet(_features_path)

    # Extract repo_key from URL for joining
    features = (
        features.with_columns(
            pl.col("url")
            .str.replace("https://github.com/", "")
            .str.split_exact("/", 1)
            .struct.rename_fields(["_owner", "_rest"])
            .alias("_split1"),
        )
        .with_columns(
            pl.col("_split1")
            .struct.field("_rest")
            .str.split_exact("/", 1)
            .struct.rename_fields(["_repo", "_path"])
            .alias("_split2"),
        )
        .with_columns(
            (
                pl.col("_split1").struct.field("_owner")
                + "/"
                + pl.col("_split2").struct.field("_repo")
            ).alias("repo_key"),
        )
        .drop("_split1", "_split2")
    )

    # Join with repo classification if available
    has_classification = _repo_class_path.exists()
    if has_classification:
        _repo_class = pl.read_parquet(_repo_class_path)
        features = features.join(
            _repo_class.select("repo_key", "collection_score"),
            on="repo_key",
            how="left",
        ).with_columns(pl.col("collection_score").fill_null(0.0))
    else:
        features = features.with_columns(pl.lit(0.0).alias("collection_score"))

    _n_total = features.shape[0]
    _n_repos = features["repo_key"].n_unique()
    _n_organic = features.filter(pl.col("collection_score") <= 0.75).shape[0]
    _n_collection = features.filter(pl.col("collection_score") > 0.75).shape[0]

    _class_note = (
        ""
        if has_classification
        else "\n\n*repo_classification.parquet not found -- all files treated as organic.*"
    )

    mo.md(f"""## Dataset Overview

| Metric | Value |
|--------|-------|
| Total files | {_n_total:,} |
| Unique repos | {_n_repos:,} |
| Organic (score <= 0.75) | {_n_organic:,} |
| Collection (score > 0.75) | {_n_collection:,} |
{_class_note}
""")
    return alt, features, has_classification, np, pl


@app.cell
def _(alt, features, mo, np, pl):
    # Summary statistics table
    _metrics = {
        "bytes": "File size (bytes)",
        "words": "Word count",
        "lines": "Line count",
        "paragraphs": "Paragraph count",
        "heading_count": "Headings",
        "max_heading_depth": "Max heading depth",
        "code_block_count": "Code blocks",
        "url_count": "Markdown URLs",
    }

    _rows = []
    for _col, _label in _metrics.items():
        _s = features[_col]
        _rows.append(
            {
                "Metric": _label,
                "Median": int(_s.median()),
                "Mean": round(float(_s.mean()), 1),
                "P25": int(_s.quantile(0.25)),
                "P75": int(_s.quantile(0.75)),
                "P95": int(_s.quantile(0.95)),
                "Max": int(_s.max()),
            }
        )

    _summary = pl.DataFrame(_rows)

    mo.vstack(
        [
            mo.md("## Summary Statistics"),
            mo.ui.table(_summary.to_pandas(), selection=None),
        ]
    )
    return


@app.cell
def _(alt, features, mo, np, pl):
    # Word count distribution
    _vals = features["words"].clip(0, 2000).to_numpy()
    _bin_edges = np.linspace(0, 2000, 51)
    _hist_counts, _ = np.histogram(_vals, bins=_bin_edges)
    _word_dist = (
        pl.DataFrame(
            {
                "bin_start": _bin_edges[:-1],
                "count": _hist_counts,
            }
        )
        .filter(pl.col("count") > 0)
        .to_pandas()
    )

    _chart = (
        alt.Chart(_word_dist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", title="Word Count (clipped at 2000)"),
            y=alt.Y("count:Q", title="Files"),
        )
        .properties(title="Word Count Distribution", width=600, height=300)
    )

    _median = features["words"].median()
    _p75 = features["words"].quantile(0.75)
    _p95 = features["words"].quantile(0.95)

    mo.vstack(
        [
            mo.md(f"""## Size Distributions

### Word Count

Median: **{int(_median)}** words | P75: **{int(_p75)}** | P95: **{int(_p95)}**

Most skills are short. The long tail is clipped at 2000 words for readability.
"""),
            _chart,
        ]
    )
    return


@app.cell
def _(alt, features, mo, np, pl):
    # Line count distribution
    _vals = features["lines"].clip(0, 200).to_numpy()
    _bin_edges = np.linspace(0, 200, 51)
    _hist_counts, _ = np.histogram(_vals, bins=_bin_edges)
    _line_dist = (
        pl.DataFrame(
            {
                "bin_start": _bin_edges[:-1],
                "count": _hist_counts,
            }
        )
        .filter(pl.col("count") > 0)
        .to_pandas()
    )

    _chart = (
        alt.Chart(_line_dist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", title="Line Count (clipped at 200)"),
            y=alt.Y("count:Q", title="Files"),
        )
        .properties(title="Line Count Distribution", width=600, height=300)
    )

    _median = features["lines"].median()
    _p75 = features["lines"].quantile(0.75)

    mo.vstack(
        [
            mo.md(f"""### Line Count

Median: **{int(_median)}** lines | P75: **{int(_p75)}**
"""),
            _chart,
        ]
    )
    return


@app.cell
def _(alt, features, mo, pl):
    # Frontmatter adoption
    _has_fm = features.filter(pl.col("has_frontmatter")).shape[0]
    _no_fm = features.filter(~pl.col("has_frontmatter")).shape[0]
    _total = features.shape[0]
    _fm_pct = _has_fm / _total

    # Field frequency among files with frontmatter
    _fm_files = features.filter(pl.col("has_frontmatter"))
    _all_fields = _fm_files["frontmatter_fields"].explode().drop_nulls()
    _field_counts = _all_fields.value_counts().sort("count", descending=True).head(20)

    _chart = (
        alt.Chart(_field_counts.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Files"),
            y=alt.Y("frontmatter_fields:N", sort="-x", title="Field"),
        )
        .properties(title="Top 20 Frontmatter Fields", width=500, height=400)
    )

    mo.vstack(
        [
            mo.md(f"""## Frontmatter Analysis

| | Count | % |
|--|-------|---|
| Has frontmatter | {_has_fm:,} | {_fm_pct:.1%} |
| No frontmatter | {_no_fm:,} | {1 - _fm_pct:.1%} |

### Field Frequency (among files with frontmatter)
"""),
            _chart,
        ]
    )
    return


@app.cell
def _(alt, features, mo, np, pl):
    # Markdown structure breakdown
    _has_headings = features.filter(pl.col("heading_count") > 0).shape[0]
    _has_code = features.filter(pl.col("code_block_count") > 0).shape[0]
    _has_urls = features.filter(pl.col("url_count") > 0).shape[0]
    _total = features.shape[0]

    _struct_data = pl.DataFrame(
        {
            "Feature": ["Has headings", "Has code blocks", "Has URLs"],
            "Count": [_has_headings, _has_code, _has_urls],
            "Pct": [
                round(100 * _has_headings / _total, 1),
                round(100 * _has_code / _total, 1),
                round(100 * _has_urls / _total, 1),
            ],
        }
    )

    _chart = (
        alt.Chart(_struct_data.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("Pct:Q", title="% of Files"),
            y=alt.Y("Feature:N", sort="-x"),
        )
        .properties(title="Markdown Structure Adoption", width=500, height=150)
    )

    # Heading depth distribution
    _depth_vals = features.filter(pl.col("max_heading_depth") > 0)["max_heading_depth"]
    _depth_counts = _depth_vals.value_counts().sort("max_heading_depth")

    _depth_chart = (
        alt.Chart(_depth_counts.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("max_heading_depth:O", title="Max Heading Depth (#)"),
            y=alt.Y("count:Q", title="Files"),
        )
        .properties(title="Max Heading Depth (files with headings)", width=400, height=200)
    )

    mo.vstack(
        [
            mo.md("## Markdown Structure"),
            _chart,
            mo.md("### Heading Depth"),
            _depth_chart,
        ]
    )
    return


@app.cell
def _(features, mo, pl):
    # Random sample viewer
    import random

    _sample_size = 8
    _n = features.shape[0]
    _indices = random.sample(range(_n), min(_sample_size, _n))
    _sample = features[_indices]

    # Read actual content for the sampled files
    _content_dir = (
        __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"
    )
    _items = []
    for _row in _sample.iter_rows(named=True):
        _url = _row["url"]
        _rel = _url.replace("https://github.com/", "")
        _path = _content_dir / _rel
        if _path.exists():
            _text = _path.read_text(errors="replace")[:3000]
        else:
            _text = "(file not found on disk)"

        _items.append(
            mo.md(f"""### {_row["words"]} words | {_row["lines"]} lines | {"FM" if _row["has_frontmatter"] else "no FM"}

`{_rel}`

```markdown
{_text}
```
""")
        )

    mo.vstack(
        [
            mo.md(f"""## Random Sample ({_sample_size} skills)

These are randomly selected skills shown in full (truncated at 3000 chars).
Re-run the cell to get a different sample.
"""),
            *_items,
        ]
    )
    return


@app.cell
def _(alt, features, has_classification, mo, np, pl):
    # Collection score dimension -- split key metrics by organic vs collection
    if not has_classification:
        mo.stop(True, mo.md("*Skipping collection split -- no repo_classification.parquet.*"))

    features_labeled = features.with_columns(
        pl.when(pl.col("collection_score") > 0.75)
        .then(pl.lit("Collection"))
        .otherwise(pl.lit("Organic"))
        .alias("source")
    )

    _metrics = ["words", "lines", "heading_count", "code_block_count"]
    _rows = []
    for _col in _metrics:
        for _src in ["Organic", "Collection"]:
            _s = features_labeled.filter(pl.col("source") == _src)[_col]
            if _s.len() > 0:
                _rows.append(
                    {
                        "Metric": _col,
                        "Source": _src,
                        "Median": int(_s.median()),
                        "Mean": round(float(_s.mean()), 1),
                        "P75": int(_s.quantile(0.75)),
                    }
                )

    _comparison = pl.DataFrame(_rows)

    # Word count by source
    _org_words = (
        features_labeled.filter(pl.col("source") == "Organic")["words"].clip(0, 2000).to_numpy()
    )
    _coll_words = (
        features_labeled.filter(pl.col("source") == "Collection")["words"].clip(0, 2000).to_numpy()
    )

    _bin_edges = np.linspace(0, 2000, 41)

    _org_counts, _ = np.histogram(_org_words, bins=_bin_edges)
    _coll_counts, _ = np.histogram(_coll_words, bins=_bin_edges)

    _hist_df = (
        pl.concat(
            [
                pl.DataFrame(
                    {
                        "bin_start": _bin_edges[:-1],
                        "count": _org_counts,
                        "source": ["Organic"] * len(_org_counts),
                    }
                ),
                pl.DataFrame(
                    {
                        "bin_start": _bin_edges[:-1],
                        "count": _coll_counts,
                        "source": ["Collection"] * len(_coll_counts),
                    }
                ),
            ]
        )
        .filter(pl.col("count") > 0)
        .to_pandas()
    )

    _chart = (
        alt.Chart(_hist_df)
        .mark_bar(opacity=0.7)
        .encode(
            x=alt.X("bin_start:Q", title="Word Count"),
            y=alt.Y("count:Q", title="Files"),
            color="source:N",
        )
        .properties(title="Word Count: Organic vs Collection", width=600, height=300)
    )

    # Frontmatter adoption by source
    _org_total = features_labeled.filter(pl.col("source") == "Organic").shape[0]
    _org_fm = features_labeled.filter(
        (pl.col("source") == "Organic") & pl.col("has_frontmatter")
    ).shape[0]
    _coll_total = features_labeled.filter(pl.col("source") == "Collection").shape[0]
    _coll_fm = features_labeled.filter(
        (pl.col("source") == "Collection") & pl.col("has_frontmatter")
    ).shape[0]

    mo.vstack(
        [
            mo.md("""## Organic vs Collection

### Key Metrics by Source
"""),
            mo.ui.table(_comparison.to_pandas(), selection=None),
            mo.md(f"""### Frontmatter Adoption

| Source | Has FM | Total | Rate |
|--------|--------|-------|------|
| Organic | {_org_fm:,} | {_org_total:,} | {_org_fm / _org_total:.1%} |
| Collection | {_coll_fm:,} | {_coll_total:,} | {_coll_fm / _coll_total:.1%} |
"""),
            _chart,
        ]
    )
    return (features_labeled,)


@app.cell
def _(mo):
    mo.md("""## Questions for Next Pass

1. **Content quality** -- Can we score sophistication without an LLM? (e.g., has examples + has headings + word count > 100)
2. **Deduplication** -- How much content overlap exists? (SHA-based or fuzzy)
3. **Template detection** -- Which skills are clearly from templates/generators?
4. **Anthropic comparison** -- How do official Anthropic skills compare on these metrics?
5. **Minimum viable skill** -- What's the smallest skill that actually works?
""")
    return


if __name__ == "__main__":
    app.run()
