"""Content shape analysis of skill files."""

import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md("""# An Analysis of public SKILL.md files on Github

    This notebook examines the structural properties of skill file content: size, markdown structure, frontmatter adoption, and how these vary between organic repos and skill collections.
    """)
    return (mo,)


@app.cell(hide_code=True)
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

    mo.md(f"""## Dataset Overview

    | Metric | Value |
    |--------|-------|
    | Total files | {_n_total:,} |
    | Unique repos | {_n_repos:,} |
    """)
    return alt, features, has_classification, np, pl


@app.cell(hide_code=True)
def _(alt, features, mo, pl):
    # Filename distribution
    _filenames = (
        features.with_columns(
            pl.col("url").str.split("/").list.last().alias("filename")
        )["filename"]
        .value_counts()
        .sort("count", descending=True)
    )

    _top = _filenames.head(25)

    _chart = (
        alt.Chart(_top.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Files"),
            y=alt.Y("filename:N", sort="-x", title="Filename"),
        )
        .properties(title="Top 25 Skill Filenames", width=600, height=500)
    )

    _total = features.shape[0]
    _top1 = _filenames.row(0, named=True)
    _n_unique = _filenames.shape[0]

    mo.vstack([
        mo.md(f"""### Filenames

    The [Agent Skills](https://agentskills.io) open standard requires skills to be
    defined in a file named exactly `SKILL.md` (case-sensitive). This convention is
    enforced by [Claude Code](https://code.claude.com/docs/en/skills),
    [OpenAI Codex](https://developers.openai.com/codex/skills),
    [VS Code Copilot](https://code.visualstudio.com/docs/copilot/customization/agent-skills),
    and other compatible tools.

    {_n_unique:,} distinct filenames across {_total:,} files.
    Most common: **{_top1["filename"]}** ({_top1["count"]:,} files, {_top1["count"] / _total:.1%}).
    The long tail of non-standard names likely reflects early adopters or tools that
    predated the standard.
    """),
        _chart,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Filtering

    There are two categories of repository: **collection repos** that aggregate
    skills from other repositories, and **organic repos** that do not.

    Additionally, there can be **duplicate content** across repos.

    This section identifies and removes both, producing a clean `skills` dataframe for analysis.
    """)
    return


@app.cell
def _(features, has_classification, mo, pl):
    # Organic vs Collection classification explanation
    if not has_classification:
        mo.stop(
            True,
            mo.md("*repo_classification.parquet not found -- all files treated as organic.*"),
        )

    _n_total = features.shape[0]
    _n_organic = features.filter(pl.col("collection_score") <= 0.75).shape[0]
    _n_collection = features.filter(pl.col("collection_score") > 0.75).shape[0]
    _n_repos = features["repo_key"].n_unique()
    _n_org_repos = (
        features.filter(pl.col("collection_score") <= 0.75)["repo_key"].n_unique()
    )
    _n_coll_repos = (
        features.filter(pl.col("collection_score") > 0.75)["repo_key"].n_unique()
    )

    mo.md(f"""### Organic vs Collection Repos

    Many repos in this dataset are **skill collections** -- aggregators that copy skills from
    other sources into a single repository. These inflate file counts and duplicate content.
    We classify each repo using a composite `collection_score` (0--1) based on three signals:

    - **File count** -- repos with hundreds or thousands of skill files are likely aggregators
    - **Keyword match** -- repo names containing "collection", "registry", "awesome", etc.
    - **Bulk commit ratio** -- fraction of files added in large batch commits (vs incremental authoring)

    Repos scoring above **0.75** are labeled "Collection"; the rest are "Organic" (authored in-place).

    _Note that this is not perfect - a spot check reveals some non-collection repos above 0.75 and collection repos below; but I think it's acceptable._

    | Source | Repos | Files | Avg files/repo |
    |--------|-------|-------|----------------|
    | Organic (score <= 0.75) | {_n_org_repos:,} | {_n_organic:,} | {_n_organic / _n_org_repos:.1f} |
    | Collection (score > 0.75) | {_n_coll_repos:,} | {_n_collection:,} | {_n_collection / _n_coll_repos:.1f} |
    | **Total** | **{_n_repos:,}** | **{_n_total:,}** | **{_n_total / _n_repos:.1f}** |

    Collection repos are {_n_coll_repos / _n_repos:.1%} of repos but contribute {_n_collection / _n_total:.1%} of files.
    """)
    return


@app.cell(hide_code=True)
def _(alt, features, has_classification, mo, np, pl):
    # Organic vs Collection detailed comparison
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
    _org_words = features_labeled.filter(
        (pl.col("source") == "Organic") & (pl.col("words") <= 2000)
    )["words"].to_numpy()
    _coll_words = features_labeled.filter(
        (pl.col("source") == "Collection") & (pl.col("words") <= 2000)
    )["words"].to_numpy()

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
            mo.md("""### Organic vs Collection Comparison

    #### Key Metrics by Source
    """),
            mo.ui.table(_comparison.to_pandas(), selection=None),
            mo.md(f"""#### Frontmatter Adoption

    | Source | Has FM | Total | Rate |
    |--------|--------|-------|------|
    | Organic | {_org_fm:,} | {_org_total:,} | {_org_fm / _org_total:.1%} |
    | Collection | {_coll_fm:,} | {_coll_total:,} | {_coll_fm / _coll_total:.1%} |
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(features, mo):
    # Deduplication overview
    _total = features.shape[0]
    _exact_unique = features["content_hash"].n_unique()
    _norm_unique = features["normalized_hash"].n_unique()
    _exact_dupes = _total - _exact_unique
    _norm_dupes = _total - _norm_unique

    mo.md(f"""### Deduplication

    Collection repos copy skills from other sources, so many files are duplicates.
    Two methods: exact byte-for-byte matching and normalized matching (strip frontmatter,
    collapse whitespace).

    | Method | Total Files | Unique | Duplicates | Dedup Rate |
    |--------|------------|--------|------------|------------|
    | Exact (content_hash) | {_total:,} | {_exact_unique:,} | {_exact_dupes:,} | {_exact_dupes / _total:.1%} |
    | Normalized (normalized_hash) | {_total:,} | {_norm_unique:,} | {_norm_dupes:,} | {_norm_dupes / _total:.1%} |
    """)
    return


@app.cell(hide_code=True)
def _(alt, features, mo, np, pl):
    # Cluster size distribution
    _clusters = (
        features.group_by("normalized_hash")
        .agg(pl.len().alias("cluster_size"))
    )
    _singletons = _clusters.filter(pl.col("cluster_size") == 1).shape[0]
    _duplicated = _clusters.filter(pl.col("cluster_size") > 1).shape[0]
    _large = _clusters.filter(pl.col("cluster_size") >= 10).shape[0]
    _total_clusters = _clusters.shape[0]

    # Histogram of cluster sizes (only duplicated, capped at 50 for readability)
    _dup_clusters = _clusters.filter(pl.col("cluster_size") > 1)
    _vals = _dup_clusters.filter(pl.col("cluster_size") <= 50)["cluster_size"].to_numpy()
    _bin_edges = np.arange(2, 52)
    _hist_counts, _ = np.histogram(_vals, bins=_bin_edges)
    _hist_df = (
        pl.DataFrame({"cluster_size": _bin_edges[:-1], "count": _hist_counts})
        .filter(pl.col("count") > 0)
        .to_pandas()
    )

    _chart = (
        alt.Chart(_hist_df)
        .mark_bar()
        .encode(
            x=alt.X("cluster_size:Q", title="Copies per Unique Skill (capped at 50)"),
            y=alt.Y("count:Q", title="Unique Skills"),
        )
        .properties(title="Cluster Size Distribution (duplicated skills only)", width=600, height=300)
    )

    mo.vstack([
        mo.md(f"""#### Cluster Size Distribution

    {_singletons:,} / {_total_clusters:,} ({_singletons / _total_clusters:.1%}) unique skills appear only once.
    {_large:,} ({_large / _total_clusters:.1%}) appear 10+ times.
    """),
        _chart,
    ])
    return


@app.cell(hide_code=True)
def _(features, mo, pl):
    # Deduplication by source (organic vs collection)
    _organic = features.filter(pl.col("collection_score") <= 0.75)
    _collection = features.filter(pl.col("collection_score") > 0.75)

    _org_total = _organic.shape[0]
    _org_unique = _organic["normalized_hash"].n_unique()
    _coll_total = _collection.shape[0]
    _coll_unique = _collection["normalized_hash"].n_unique()

    mo.md(f"""#### Deduplication by Source

    | Source | Files | Unique Hashes | Dedup Rate |
    |--------|-------|---------------|------------|
    | Organic (score <= 0.75) | {_org_total:,} | {_org_unique:,} | {(_org_total - _org_unique) / _org_total:.1%} |
    | Collection (score > 0.75) | {_coll_total:,} | {_coll_unique:,} | {(_coll_total - _coll_unique) / _coll_total:.1%} |

    Collection repos are expected to drive most duplication since they aggregate
    skills from other sources.
    """)
    return


@app.cell(hide_code=True)
def _(features, mo, pl):
    # Most duplicated skills
    _clusters = (
        features.group_by("normalized_hash")
        .agg([
            pl.len().alias("cluster_size"),
            pl.col("url").first().alias("example_url"),
            pl.col("words").first().alias("words"),
        ])
        .sort("cluster_size", descending=True)
        .head(10)
    )

    _rows_md = []
    for _row in _clusters.iter_rows(named=True):
        _url = _row["example_url"]
        _rel = _url.replace("https://github.com/", "")
        _rows_md.append(
            f"| {_row['cluster_size']:,} | {_row['words']} | [{_rel[:60]}]({_url}) |"
        )

    _table = "\n    ".join(_rows_md)

    # Show full content of most-duplicated skill
    _top = _clusters.row(0, named=True)
    _content_dir = (
        __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"
    )
    _top_rel = _top["example_url"].replace("https://github.com/", "")
    _top_path = _content_dir / _top_rel
    _top_text = _top_path.read_text(errors="replace") if _top_path.exists() else "(not found)"
    _top_escaped = _top_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_top_escaped}</pre>'

    mo.vstack([
        mo.md(f"""#### Most Duplicated Skills

    | Copies | Words | Example URL |
    |--------|-------|-------------|
    {_table}

    ##### Most-duplicated skill ({_top["cluster_size"]:,} copies, {_top["words"]} words)

    [{_top_rel}]({_top["example_url"]})
    """),
        mo.Html(_pre),
    ])
    return


@app.cell(hide_code=True)
def _(features, mo):
    # Filtering result: produce the deduped `skills` dataframe
    _n_before = features.shape[0]

    # One representative per normalized_hash, preferring organic sources (low collection_score)
    skills = (
        features.sort("collection_score")
        .group_by("normalized_hash")
        .first()
    )

    _n_after = skills.shape[0]
    _reduction = (_n_before - _n_after) / _n_before

    mo.md(f"""### Filtering Result

    After deduplication: **{_n_after:,}** unique skills (from {_n_before:,} total files, **{_reduction:.1%}** reduction).

    All analysis below uses this deduped `skills` dataframe. For each group of duplicates,
    the representative with the lowest `collection_score` is kept (preferring organic originals).
    """)
    return (skills,)


@app.cell(hide_code=True)
def _(mo, pl, skills):
    # Summary statistics table with Anthropic comparison
    _anthropic = skills.filter(pl.col("url").str.starts_with("https://github.com/anthropics/"))

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
        _s = skills[_col]
        _a = _anthropic[_col]
        _rows.append(
            {
                "Metric": _label,
                "Median": int(_s.median()),
                "Anthropic Median": int(_a.median()) if _a.len() > 0 else None,
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
            mo.md(f"""## Summary Statistics

    Anthropic column shows median across {_anthropic.shape[0]} skills from the `anthropics/` GitHub org.
    """),
            mo.ui.table(_summary.to_pandas(), selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, np, pl, skills):
    # Word count distribution
    _vals = skills.filter(pl.col("words") <= 2000)["words"].to_numpy()
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
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Word Count Distribution", width=600, height=300)
    )

    _median = skills["words"].median()
    _p75 = skills["words"].quantile(0.75)
    _p95 = skills["words"].quantile(0.95)

    mo.vstack(
        [
            mo.md(f"""## Size Distributions

    ### Word Count

    Median: **{int(_median)}** words | P75: **{int(_p75)}** | P95: **{int(_p95)}**

    Skills above 2000 words excluded from histogram.
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, pl, skills):
    # Show a skill near the median word count
    _median_words = int(skills["words"].median())
    _near_median = skills.filter(pl.col("words") == _median_words).head(1)
    if _near_median.shape[0] == 0:
        _near_median = skills.filter(
            (pl.col("words") >= _median_words - 5) & (pl.col("words") <= _median_words + 5)
        ).head(1)

    _content_dir = (
        __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"
    )
    _row = _near_median.row(0, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    _escaped = _text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.vstack([
        mo.md(f"""#### Example: a {_row["words"]}-word skill (median)

    `{_rel}`
    """),
        mo.Html(_pre),
    ])
    return


@app.cell(hide_code=True)
def _(alt, mo, np, pl, skills):
    # Line count distribution
    _vals = skills.filter(pl.col("lines") <= 200)["lines"].to_numpy()
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
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Line Count Distribution", width=600, height=300)
    )

    _median = skills["lines"].median()
    _p75 = skills["lines"].quantile(0.75)

    mo.vstack(
        [
            mo.md(f"""### Line Count

    Median: **{int(_median)}** lines | P75: **{int(_p75)}**
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, pl, skills):
    # Show a skill near the median line count
    _median_lines = int(skills["lines"].median())
    _near_median = skills.filter(pl.col("lines") == _median_lines).head(1)
    if _near_median.shape[0] == 0:
        _near_median = skills.filter(
            (pl.col("lines") >= _median_lines - 3) & (pl.col("lines") <= _median_lines + 3)
        ).head(1)

    _content_dir = (
        __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"
    )
    _row = _near_median.row(0, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    _escaped = _text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.vstack([
        mo.md(f"""#### Example: a {_row["lines"]}-line skill (median)

    `{_rel}`
    """),
        mo.Html(_pre),
    ])
    return


@app.cell(hide_code=True)
def _(alt, mo, pl, skills):
    # Frontmatter adoption
    _has_fm = skills.filter(pl.col("has_frontmatter")).shape[0]
    _no_fm = skills.filter(~pl.col("has_frontmatter")).shape[0]
    _total = skills.shape[0]
    _fm_pct = _has_fm / _total

    # Field frequency among files with frontmatter
    _fm_files = skills.filter(pl.col("has_frontmatter"))
    _all_fields = _fm_files["frontmatter_fields"].explode().drop_nulls()
    _field_counts = _all_fields.value_counts().sort("count", descending=True).head(20)

    _chart = (
        alt.Chart(_field_counts.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Skills"),
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

    ### Field Frequency (among skills with frontmatter)
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, pl, skills):
    # Markdown structure breakdown
    _has_headings = skills.filter(pl.col("heading_count") > 0).shape[0]
    _has_code = skills.filter(pl.col("code_block_count") > 0).shape[0]
    _has_urls = skills.filter(pl.col("url_count") > 0).shape[0]
    _total = skills.shape[0]

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
            x=alt.X("Pct:Q", title="% of Skills"),
            y=alt.Y("Feature:N", sort="-x"),
        )
        .properties(title="Markdown Structure Adoption", width=500, height=150)
    )

    # Heading depth distribution
    _depth_vals = skills.filter(pl.col("max_heading_depth") > 0)["max_heading_depth"]
    _depth_counts = _depth_vals.value_counts().sort("max_heading_depth")

    _depth_chart = (
        alt.Chart(_depth_counts.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("max_heading_depth:O", title="Max Heading Depth (#)"),
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Max Heading Depth (skills with headings)", width=400, height=200)
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


@app.cell(hide_code=True)
def _(alt, mo, pl, skills):
    # Code block count histogram
    _code_counts = (
        skills.filter(pl.col("code_block_count") <= 40)["code_block_count"]
        .value_counts()
        .sort("code_block_count")
    )

    _chart = (
        alt.Chart(_code_counts.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("code_block_count:O", title="Code Blocks per Skill"),
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Code Block Count Distribution (<=40)", width=600, height=300)
    )

    _median = skills["code_block_count"].median()
    _has_code = skills.filter(pl.col("code_block_count") > 0).shape[0]
    _total = skills.shape[0]

    mo.vstack(
        [
            mo.md(f"""### Code Blocks

    {_has_code:,} / {_total:,} ({_has_code / _total:.1%}) skills have at least one code block.
    Median: **{int(_median)}** code blocks.
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, pl, skills):
    # URL analysis -- sample files to extract actual link targets
    import re
    import urllib.parse
    from collections import Counter
    _URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    _content_dir = __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"

    _with_urls = skills.filter(pl.col("url_count") > 0)
    _sample = _with_urls.sample(min(1000, _with_urls.shape[0]), seed=42)

    _href_types = Counter()
    _domains = Counter()
    for _row in _sample.iter_rows(named=True):
        _rel = _row["url"].replace("https://github.com/", "")
        _path = _content_dir / _rel
        if not _path.exists():
            continue
        _text = _path.read_text(errors="replace")
        for _label, _href in _URL_RE.findall(_text):
            if _href.startswith("http"):
                _parsed = urllib.parse.urlparse(_href)
                _domains[_parsed.netloc] += 1
                _href_types["External"] += 1
            elif _href.startswith("#"):
                _href_types["Anchor (#)"] += 1
            elif _href.startswith("/") or _href.endswith(".md"):
                _href_types["Relative path"] += 1
            else:
                _href_types["Other"] += 1

    # URL type breakdown
    _type_df = pl.DataFrame(
        {"Type": list(_href_types.keys()), "Count": list(_href_types.values())}
    ).sort("Count", descending=True)

    _type_chart = (
        alt.Chart(_type_df.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("Count:Q", title="Links (sampled)"),
            y=alt.Y("Type:N", sort="-x"),
        )
        .properties(title="URL Types (sample of 1000 skills with URLs)", width=400, height=150)
    )

    # Top domains
    _top_domains = sorted(_domains.items(), key=lambda x: -x[1])[:20]
    _domain_df = pl.DataFrame(
        {"Domain": [d for d, _ in _top_domains], "Count": [c for _, c in _top_domains]}
    )

    _domain_chart = (
        alt.Chart(_domain_df.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("Count:Q", title="Links (sampled)"),
            y=alt.Y("Domain:N", sort="-x", title=None),
        )
        .properties(title="Top 20 External Domains", width=400, height=400)
    )

    _total_with = _with_urls.shape[0]
    _total = skills.shape[0]

    mo.vstack(
        [
            mo.md(f"""### URLs in Skills

    {_total_with:,} / {_total:,} ({_total_with / _total:.1%}) skills contain at least one markdown link.
    Most are relative paths (cross-references within repos) or documentation links.
    Based on a sample of 1,000 skills:
    """),
            mo.hstack([_type_chart, _domain_chart]),
        ]
    )
    return


@app.cell
def _(alt, mo, pl, skills):
    # Language distribution
    _lang_counts = (
        skills["language"]
        .value_counts()
        .sort("count", descending=True)
    )
    _total = skills.shape[0]
    _top_langs = _lang_counts.head(15)
    _english = _lang_counts.filter(pl.col("language") == "en")
    _en_count = _english["count"].item() if _english.shape[0] > 0 else 0
    _unknown = _lang_counts.filter(pl.col("language") == "unknown")
    _unk_count = _unknown["count"].item() if _unknown.shape[0] > 0 else 0

    _chart = (
        alt.Chart(_top_langs.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Skills"),
            y=alt.Y("language:N", sort="-x", title="Detected Language"),
        )
        .properties(title="Top 15 Detected Languages", width=500, height=350)
    )

    mo.vstack([
        mo.md(f"""## Language Detection

    Language detected from prose content (frontmatter and code blocks stripped, min 10 words).

    | | Count | % |
    |--|-------|---|
    | English | {_en_count:,} | {_en_count / _total:.1%} |
    | Unknown (< 10 words) | {_unk_count:,} | {_unk_count / _total:.1%} |
    | Non-English | {_total - _en_count - _unk_count:,} | {(_total - _en_count - _unk_count) / _total:.1%} |
    """),
        _chart,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Skills

    Three randomly selected skills from the deduped set. Re-run cells to get different samples.
    """)
    return


@app.cell(hide_code=True)
def _(mo, skills):
    import random as _random1

    _content_dir = (
        __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"
    )
    _idx = _random1.randint(0, skills.shape[0] - 1)
    _row = skills.row(_idx, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    _escaped = _text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.vstack([
        mo.md(f"""### Sample 1: {_row["words"]} words | {_row["lines"]} lines | {_row["code_block_count"]} code blocks | {"FM" if _row["has_frontmatter"] else "no FM"}

    `{_rel}`
    """),
        mo.Html(_pre),
    ])
    return


@app.cell(hide_code=True)
def _(mo, skills):
    import random as _random2

    _content_dir = (
        __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"
    )
    _idx = _random2.randint(0, skills.shape[0] - 1)
    _row = skills.row(_idx, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    _escaped = _text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.vstack([
        mo.md(f"""### Sample 2: {_row["words"]} words | {_row["lines"]} lines | {_row["code_block_count"]} code blocks | {"FM" if _row["has_frontmatter"] else "no FM"}

    `{_rel}`
    """),
        mo.Html(_pre),
    ])
    return


@app.cell(hide_code=True)
def _(mo, skills):
    import random as _random3

    _content_dir = (
        __import__("pathlib").Path.home() / "work" / "skills-dataset" / "data" / "content"
    )
    _idx = _random3.randint(0, skills.shape[0] - 1)
    _row = skills.row(_idx, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    _escaped = _text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.vstack([
        mo.md(f"""### Sample 3: {_row["words"]} words | {_row["lines"]} lines | {_row["code_block_count"]} code blocks | {"FM" if _row["has_frontmatter"] else "no FM"}

    `{_rel}`
    """),
        mo.Html(_pre),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Questions for Next Pass

    1. **Template detection** -- Which skills are clearly from templates/generators?
    """)
    return


if __name__ == "__main__":
    app.run()
