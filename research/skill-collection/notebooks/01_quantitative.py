"""Content shape analysis of skill files."""

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md("""# An Analysis of public SKILL.md files on Github

    This notebook examines the structural properties of skill file content: size, markdown structure, frontmatter adoption, and how these vary between organic repos and skill collections.

    [Data comes from Kaggle](https://www.kaggle.com/datasets/thekevinscott/github-skill-files/data)
    """)
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    import altair as alt
    import numpy as np
    import polars as pl

    alt.data_transformers.disable_max_rows()

    _data_dir = __import__("pathlib").Path("data")
    _features_path = _data_dir / "analyzed" / "content_features.parquet"
    _files_path = _data_dir / "github-skill-files" / "files.parquet"

    if not _features_path.exists():
        mo.stop(
            True,
            mo.md(
                "**Missing data.** Run `python -m analyze_skills.extract_features` first "
                f"to generate `{_features_path}`."
            ),
        )

    features = pl.read_parquet(_features_path)

    # Filter to skill.md files only (case-insensitive)
    features = features.filter(pl.col("url").str.to_lowercase().str.ends_with("/skill.md"))

    # Join with files.parquet to get repo_key
    if _files_path.exists():
        _files = pl.read_parquet(_files_path, columns=["url", "repo_key"])
        features = features.join(_files, on="url", how="left")
    else:
        # Fallback: parse repo_key from URL
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

    _n_total = features.shape[0]
    _n_repos = features["repo_key"].n_unique()
    _median_bytes = features["bytes"].median()
    _median_words = (
        features["prose_words"].median()
        if "prose_words" in features.columns
        else features["words"].median()
    )
    _median_lines = features["lines"].median()
    _fm_count = features.filter(pl.col("has_frontmatter")).shape[0]
    _fm_pct = _fm_count / _n_total
    _has_code = features.filter(pl.col("code_block_count") > 0).shape[0]
    _code_pct = _has_code / _n_total
    _has_headings = features.filter(pl.col("heading_count") > 0).shape[0]
    _heading_pct = _has_headings / _n_total

    mo.md(f"""## Dataset Overview

    | Metric | Value |
    |--------|-------|
    | Total files | {_n_total:,} |
    | Unique repos | {_n_repos:,} |
    | Median size | {_median_words:.0f} prose words / {_median_lines:.0f} lines |
    | With frontmatter | {_fm_pct:.0%} |
    | With headings | {_heading_pct:.0%} |
    | With code blocks | {_code_pct:.0%} |
    """)
    return alt, features, np, pl


@app.cell(hide_code=True)
def _(features, mo):
    # Deduplication overview
    _total = features.shape[0]
    _exact_unique = features["content_hash"].n_unique()
    _norm_unique = features["normalized_hash"].n_unique()
    _exact_dupes = _total - _exact_unique
    _norm_dupes = _total - _norm_unique

    mo.md(f"""## Deduplication

    The raw dataset contains **duplicate content** across repos (forks, collections
    that aggregate skills from other repositories, etc.).

    | Method | Total Files | Unique | Duplicates | Dedup Rate |
    |--------|------------|--------|------------|------------|
    | Exact (content_hash) | {_total:,} | {_exact_unique:,} | {_exact_dupes:,} | {_exact_dupes / _total:.1%} |
    | Normalized (normalized_hash) | {_total:,} | {_norm_unique:,} | {_norm_dupes:,} | {_norm_dupes / _total:.1%} |

    **Note:** Normalization strips frontmatter, so skills with identical body text but different metadata (name, tags) are treated as duplicates. This is appropriate for structural analysis but may undercount distinct skills for semantic analysis.
    """)
    return


@app.cell(hide_code=True)
def _(features, mo, pl):
    # Most duplicated skills
    _clusters = (
        features.group_by("normalized_hash")
        .agg(
            [
                pl.len().alias("cluster_size"),
                pl.col("url").first().alias("example_url"),
                pl.col("words").first().alias("words"),
            ]
        )
        .sort("cluster_size", descending=True)
        .head(10)
    )

    _rows_md = []
    for _row in _clusters.iter_rows(named=True):
        _url = _row["example_url"]
        _rel = _url.replace("https://github.com/", "")
        _rows_md.append(f"| {_row['cluster_size']:,} | {_row['words']} | [{_rel[:60]}]({_url}) |")

    _table = "\n    ".join(_rows_md)

    # Show full content of most-duplicated skill
    _top = _clusters.row(0, named=True)
    _content_dir = __import__("pathlib").Path("data/content")
    _top_rel = _top["example_url"].replace("https://github.com/", "")
    _top_path = _content_dir / _top_rel
    _top_text = _top_path.read_text(errors="replace") if _top_path.exists() else "(not found)"
    import html as _html

    _top_escaped = _html.escape(_top_text)

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_top_escaped}</pre>'

    mo.vstack(
        [
            mo.md(f"""#### Most Duplicated Skills

    | Copies | Words | Example URL |
    |--------|-------|-------------|
    {_table}

    ##### Most-duplicated skill ({_top["cluster_size"]:,} copies, {_top["words"]} words)

    [{_top_rel}]({_top["example_url"]})
    """),
            mo.Html(_pre),
        ]
    )
    return


@app.cell(hide_code=True)
def _(features, mo):
    # Produce the deduped `skills` dataframe
    # One representative per normalized_hash; sort by URL for deterministic selection
    skills = features.sort("url").group_by("normalized_hash").first()

    _n_after = skills.shape[0]
    _reduction = (features.shape[0] - _n_after) / features.shape[0]

    mo.md(f"""Using normalized deduplication: **{_n_after:,}** unique skills ({_reduction:.0%} reduction). All analysis below uses this deduplicated set.
    """)
    return (skills,)


@app.cell(hide_code=True)
def _(mo, pl, skills):
    # Summary statistics table with Anthropic comparison
    _anthropic = skills.filter(pl.col("url").str.starts_with("https://github.com/anthropics/"))

    _metrics = {
        "bytes": "File size (bytes)",
        "words": "Word count (total)",
        "prose_words": "Prose words",
        "code_words": "Code words",
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
                "Anthropic Mean": round(float(_a.mean()), 1) if _a.len() > 0 else None,
                "P25": int(_s.quantile(0.25)),
                "P75": int(_s.quantile(0.75)),
                "P95": int(_s.quantile(0.95)),
                "Max": int(_s.max()),
            }
        )

    _summary = pl.DataFrame(_rows)

    _n_anthropic = _anthropic.shape[0]
    _caveat = " *(small sample -- interpret with caution)*" if _n_anthropic < 30 else ""

    mo.vstack(
        [
            mo.md(f"""## Summary Statistics

    Anthropic column: median across **{_n_anthropic}** skills from the `anthropics/` GitHub org.{_caveat}
    """),
            mo.ui.table(_summary.to_pandas(), selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, np, pl, skills):
    # Prose word count distribution — clipped at 2000, pre-aggregated
    _cutoff = 2000
    _excluded = skills.filter(pl.col("prose_words") > _cutoff).shape[0]
    _excluded_pct = _excluded / skills.shape[0]
    _vals = skills.filter(pl.col("prose_words") <= _cutoff)["prose_words"].to_numpy()
    _counts, _edges = np.histogram(_vals, bins=50)
    _hist = pl.DataFrame(
        {"bin_start": _edges[:-1], "bin_end": _edges[1:], "count": _counts}
    ).to_pandas()

    _chart = (
        alt.Chart(_hist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", bin="binned", title="Prose Words"),
            x2="bin_end:Q",
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Prose Word Count Distribution", width=600, height=300)
    )

    _median = skills["prose_words"].median()
    _p75 = skills["prose_words"].quantile(0.75)
    _p95 = skills["prose_words"].quantile(0.95)

    mo.vstack(
        [
            mo.md(f"""## Size Distributions

    ### Prose Word Count

    Prose words exclude tokens inside code blocks. Chart clipped at {_cutoff:,}; **{_excluded:,}** skills ({_excluded_pct:.1%}) exceed the cutoff.

    Median: **{int(_median)}** | P75: **{int(_p75)}** | P95: **{int(_p95)}** | Max: **{int(skills["prose_words"].max()):,}**
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, pl, skills):
    # Show a skill near the median prose word count
    _median_words = int(skills["prose_words"].median())
    _near_median = skills.filter(pl.col("prose_words") == _median_words).head(1)
    if _near_median.shape[0] == 0:
        _near_median = skills.filter(
            (pl.col("prose_words") >= _median_words - 5)
            & (pl.col("prose_words") <= _median_words + 5)
        ).head(1)

    _content_dir = __import__("pathlib").Path("data/content")
    _row = _near_median.row(0, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _rel_short = __import__("re").sub(r"/blob/[0-9a-f]+/", "/.../", _rel)
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    import html as _html

    _escaped = _html.escape(_text)

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.accordion(
        {
            f"Example: a {_row['words']}-word skill (median) — `{_rel_short}`": mo.Html(_pre),
        }
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, np, pl, skills):
    # Line count distribution — clipped at 200, pre-aggregated
    _cutoff = 200
    _excluded = skills.filter(pl.col("lines") > _cutoff).shape[0]
    _excluded_pct = _excluded / skills.shape[0]
    _vals = skills.filter(pl.col("lines") <= _cutoff)["lines"].to_numpy()
    _counts, _edges = np.histogram(_vals, bins=50)
    _hist = pl.DataFrame(
        {"bin_start": _edges[:-1], "bin_end": _edges[1:], "count": _counts}
    ).to_pandas()

    _chart = (
        alt.Chart(_hist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", bin="binned", title="Lines"),
            x2="bin_end:Q",
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Line Count Distribution", width=600, height=300)
    )

    _median = skills["lines"].median()
    _p75 = skills["lines"].quantile(0.75)
    _p95 = skills["lines"].quantile(0.95)

    mo.vstack(
        [
            mo.md(f"""### Line Count

    Chart clipped at {_cutoff}; **{_excluded:,}** skills ({_excluded_pct:.1%}) exceed the cutoff.

    Median: **{int(_median)}** | P75: **{int(_p75)}** | P95: **{int(_p95)}** | Max: **{int(skills["lines"].max()):,}**
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

    _content_dir = __import__("pathlib").Path("data/content")
    _row = _near_median.row(0, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _rel_short = __import__("re").sub(r"/blob/[0-9a-f]+/", "/.../", _rel)
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    import html as _html

    _escaped = _html.escape(_text)

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.accordion(
        {
            f"Example: a {_row['lines']}-line skill (median) — `{_rel_short}`": mo.Html(_pre),
        }
    )
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
    # Code block count histogram — clipped at 40, value_counts (already small)
    _cutoff = 40
    _excluded = skills.filter(pl.col("code_block_count") > _cutoff).shape[0]
    _excluded_pct = _excluded / skills.shape[0]
    _code_counts = (
        skills.filter(pl.col("code_block_count") <= _cutoff)["code_block_count"]
        .value_counts()
        .sort("code_block_count")
        .to_pandas()
    )

    _chart = (
        alt.Chart(_code_counts)
        .mark_bar()
        .encode(
            x=alt.X(
                "code_block_count:Q", title="Code Blocks per Skill", scale=alt.Scale(domainMin=0)
            ),
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Code Block Count Distribution", width=600, height=300)
    )

    _median = skills["code_block_count"].median()
    _max = int(skills["code_block_count"].max())
    _has_code = skills.filter(pl.col("code_block_count") > 0).shape[0]
    _total = skills.shape[0]

    mo.vstack(
        [
            mo.md(f"""### Code Blocks

    {_has_code:,} / {_total:,} ({_has_code / _total:.1%}) skills have at least one code block.
    Chart clipped at {_cutoff}; **{_excluded:,}** skills ({_excluded_pct:.1%}) exceed the cutoff.

    Median: **{int(_median)}** | Max: **{_max}**
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
    _content_dir = __import__("pathlib").Path("data/content")

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
                try:
                    _parsed = urllib.parse.urlparse(_href)
                    _domains[_parsed.netloc] += 1
                except ValueError:
                    pass
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
def _(mo):
    mo.callout(
        mo.md("""## Language Detection

**Placeholder.** The `langdetect`-based approach is unreliable for mixed-language content
(e.g., English headings with Chinese body text, code-heavy files with minimal prose).
Accurate language classification requires an LLM-based workflow — to be added in a future pass.
"""),
        kind="warn",
    )
    return


@app.cell(hide_code=True)
def _(mo, pl, skills):
    _repos_path = __import__("pathlib").Path("data/github-skill-files/repos.parquet")
    if not _repos_path.exists():
        mo.stop(
            True,
            mo.md("**Missing data.** `data/github-skill-files/repos.parquet` not found."),
        )

    repos = pl.read_parquet(_repos_path)

    _skills_per_repo = skills.group_by("repo_key").agg(pl.len().alias("skill_count"))
    repo_skills = _skills_per_repo.join(repos, on="repo_key", how="left")

    _n_repos_with_skills = repo_skills.shape[0]
    _n_repos_total = repos.shape[0]
    _median_skills = repo_skills["skill_count"].median()
    _p75 = repo_skills["skill_count"].quantile(0.75)
    _p95 = repo_skills["skill_count"].quantile(0.95)
    _max_skills = int(repo_skills["skill_count"].max())

    mo.md(f"""## Repository Analysis

    Analysis of the {_n_repos_with_skills:,} repos that contain deduplicated skills (out of {_n_repos_total:,} repos in the dataset).

    | Metric | Value |
    |--------|-------|
    | Repos with skills | {_n_repos_with_skills:,} |
    | Median skills/repo | {int(_median_skills)} |
    | P75 | {int(_p75)} |
    | P95 | {int(_p95)} |
    | Max | {_max_skills:,} |
    """)
    return repo_skills, repos


@app.cell(hide_code=True)
def _(alt, mo, np, pl, repo_skills):
    # Skills per repo distribution — clipped at 50, pre-aggregated
    _cutoff = 50
    _excluded = repo_skills.filter(pl.col("skill_count") > _cutoff).shape[0]
    _excluded_pct = _excluded / repo_skills.shape[0]
    _vals = repo_skills.filter(pl.col("skill_count") <= _cutoff)["skill_count"].to_numpy()
    _counts, _edges = np.histogram(_vals, bins=50)
    _hist = pl.DataFrame(
        {"bin_start": _edges[:-1], "bin_end": _edges[1:], "count": _counts}
    ).to_pandas()

    _chart = (
        alt.Chart(_hist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", bin="binned", title="Skills per Repo"),
            x2="bin_end:Q",
            y=alt.Y("count:Q", title="Repos"),
        )
        .properties(title="Skills per Repository Distribution", width=600, height=300)
    )

    _median = repo_skills["skill_count"].median()
    _p75 = repo_skills["skill_count"].quantile(0.75)
    _p95 = repo_skills["skill_count"].quantile(0.95)

    mo.vstack(
        [
            mo.md(f"""### Skills per Repository

    Most repos contain just one or two skills; a small number of "collection" repos aggregate hundreds or thousands. Chart clipped at {_cutoff}; **{_excluded:,}** repos ({_excluded_pct:.1%}) exceed the cutoff.

    Median: **{int(_median)}** | P75: **{int(_p75)}** | P95: **{int(_p95)}** | Max: **{int(repo_skills["skill_count"].max()):,}**
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, repo_skills):
    # Top 20 repos by skill count
    _top = repo_skills.sort("skill_count", descending=True).head(20)

    _rows_md = []
    for _row in _top.iter_rows(named=True):
        _rk = _row["repo_key"]
        _url = f"https://github.com/{_rk}"
        _stars = _row["stars"] if _row["stars"] is not None else 0
        _lang = _row["language"] if _row["language"] is not None else "—"
        _rows_md.append(f"| [{_rk}]({_url}) | {_row['skill_count']:,} | {_stars:,} | {_lang} |")

    _table = "\n    ".join(_rows_md)

    mo.md(f"""### Top 20 Repos by Skill Count

    | Repository | Skills | Stars | Language |
    |------------|--------|-------|----------|
    {_table}
    """)
    return


@app.cell(hide_code=True)
def _(alt, mo, np, pl, repo_skills):
    # Stars distribution — clipped at 100, pre-aggregated
    _cutoff = 100
    _stars_col = repo_skills["stars"].drop_nulls()
    _excluded = _stars_col.filter(_stars_col > _cutoff).len()
    _excluded_pct = _excluded / _stars_col.len()
    _vals = _stars_col.filter(_stars_col <= _cutoff).to_numpy()
    _counts, _edges = np.histogram(_vals, bins=50)
    _hist = pl.DataFrame(
        {"bin_start": _edges[:-1], "bin_end": _edges[1:], "count": _counts}
    ).to_pandas()

    _chart = (
        alt.Chart(_hist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", bin="binned", title="GitHub Stars"),
            x2="bin_end:Q",
            y=alt.Y("count:Q", title="Repos"),
        )
        .properties(title="Stars Distribution (repos with skills)", width=600, height=300)
    )

    _median = int(_stars_col.median())
    _p75 = int(_stars_col.quantile(0.75))
    _p95 = int(_stars_col.quantile(0.95))
    _zero_pct = _stars_col.filter(_stars_col == 0).len() / _stars_col.len()

    mo.vstack(
        [
            mo.md(f"""### Repo Metadata

    #### Stars Distribution

    The vast majority of repos with skills have zero or very few stars. Chart clipped at {_cutoff}; **{_excluded:,}** repos ({_excluded_pct:.1%}) exceed the cutoff. **{_zero_pct:.0%}** of repos have 0 stars.

    Median: **{_median}** | P75: **{_p75}** | P95: **{_p95}** | Max: **{int(_stars_col.max()):,}**
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, pl, repo_skills):
    # Primary language and license breakdown
    _lang_counts = (
        repo_skills.filter(pl.col("language").is_not_null())["language"]
        .value_counts()
        .sort("count", descending=True)
        .head(15)
    )

    _lang_chart = (
        alt.Chart(_lang_counts.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Repos"),
            y=alt.Y("language:N", sort="-x", title="Primary Language"),
        )
        .properties(title="Top 15 Primary Languages", width=400, height=350)
    )

    _license_counts = (
        repo_skills.filter(pl.col("license").is_not_null() & (pl.col("license") != "NOASSERTION"))[
            "license"
        ]
        .value_counts()
        .sort("count", descending=True)
        .head(10)
    )

    _no_license = repo_skills.filter(
        pl.col("license").is_null() | (pl.col("license") == "NOASSERTION")
    ).shape[0]
    _total = repo_skills.shape[0]

    _license_chart = (
        alt.Chart(_license_counts.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Repos"),
            y=alt.Y("license:N", sort="-x", title="License"),
        )
        .properties(title="Top 10 Licenses", width=400, height=250)
    )

    mo.vstack(
        [
            mo.md(f"""#### Language & License

    {_no_license:,} / {_total:,} ({_no_license / _total:.0%}) repos have no license or NOASSERTION.
    """),
            mo.hstack([_lang_chart, _license_chart]),
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, pl, repos, skills):
    # Skills vs repo popularity: skill characteristics by star bucket
    _with_stars = skills.join(
        repos.select(["repo_key", "stars"]), on="repo_key", how="left"
    ).filter(pl.col("stars").is_not_null())

    _bucketed = _with_stars.with_columns(
        pl.when(pl.col("stars") == 0)
        .then(pl.lit("0"))
        .when(pl.col("stars") <= 10)
        .then(pl.lit("1\u201310"))
        .when(pl.col("stars") <= 100)
        .then(pl.lit("11\u2013100"))
        .when(pl.col("stars") <= 1000)
        .then(pl.lit("101\u20131k"))
        .otherwise(pl.lit("1k+"))
        .alias("star_bucket")
    )

    _summary = _bucketed.group_by("star_bucket").agg(
        [
            pl.col("prose_words").median().alias("median_prose_words"),
            pl.col("has_frontmatter").mean().alias("frontmatter_pct"),
            pl.col("code_block_count").median().alias("median_code_blocks"),
            pl.len().alias("n_skills"),
        ]
    )

    _order = ["0", "1\u201310", "11\u2013100", "101\u20131k", "1k+"]

    _prose_chart = (
        alt.Chart(_summary.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("star_bucket:N", sort=_order, title="Repo Stars"),
            y=alt.Y("median_prose_words:Q", title="Median Prose Words"),
        )
        .properties(title="Median Prose Words by Repo Stars", width=300, height=250)
    )

    _fm_chart = (
        alt.Chart(_summary.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("star_bucket:N", sort=_order, title="Repo Stars"),
            y=alt.Y(
                "frontmatter_pct:Q",
                title="Frontmatter Adoption",
                axis=alt.Axis(format=".0%"),
            ),
        )
        .properties(title="Frontmatter Adoption by Repo Stars", width=300, height=250)
    )

    _rows_md = []
    for _bucket in _order:
        _row = _summary.filter(pl.col("star_bucket") == _bucket)
        if _row.shape[0] == 0:
            continue
        _r = _row.row(0, named=True)
        _rows_md.append(
            f"| {_bucket} | {_r['n_skills']:,} | {int(_r['median_prose_words'])} "
            f"| {_r['frontmatter_pct']:.0%} | {int(_r['median_code_blocks'])} |"
        )
    _table = "\n    ".join(_rows_md)

    mo.vstack(
        [
            mo.md(f"""### Skills vs Repo Popularity

    Do skills in popular repos differ structurally from those in low-star repos?

    | Star Bucket | Skills | Median Prose Words | Frontmatter % | Median Code Blocks |
    |-------------|--------|--------------------|---------------|--------------------|
    {_table}
    """),
            mo.hstack([_prose_chart, _fm_chart]),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, pl, skills):
    _history_path = __import__("pathlib").Path("data/github-skill-files/history.parquet")
    if not _history_path.exists():
        mo.stop(
            True,
            mo.md("**Missing data.** `data/github-skill-files/history.parquet` not found."),
        )

    _raw_history = pl.read_parquet(_history_path)

    # Parse commit_date strings to proper dates
    _raw_history = _raw_history.with_columns(
        pl.col("commit_date")
        .str.replace(r"\+00:00$", "Z")
        .str.to_datetime(format="%Y-%m-%dT%H:%M:%SZ")
        .dt.date()
        .alias("date")
    )

    # Join with deduplicated skills to only analyze unique skills
    _skill_urls = skills.select("url")
    history = _raw_history.join(_skill_urls, on="url", how="inner")

    _n_commits = history.shape[0]
    _n_skills_with_history = history["url"].n_unique()
    _n_skills_total = skills.shape[0]

    mo.md(f"""## File History

    Commit history for skill files, joined with the deduplicated skill set.

    | Metric | Value |
    |--------|-------|
    | Total commits | {_n_commits:,} |
    | Skills with history | {_n_skills_with_history:,} / {_n_skills_total:,} |
    """)
    return (history,)


@app.cell(hide_code=True)
def _(alt, history, mo, np, pl):
    # Commits per skill — histogram
    _commit_counts = history.group_by("url").agg(pl.len().alias("commits"))
    _vals = _commit_counts["commits"].to_numpy()

    _median = int(np.median(_vals))
    _p75 = int(np.percentile(_vals, 75))
    _p95 = int(np.percentile(_vals, 95))
    _max = int(np.max(_vals))

    # Clip for visualization
    _cutoff = int(np.percentile(_vals, 99))
    _clipped = _vals[_vals <= _cutoff]
    _excluded = len(_vals) - len(_clipped)

    _counts, _edges = np.histogram(_clipped, bins=50)
    _hist = pl.DataFrame(
        {"bin_start": _edges[:-1], "bin_end": _edges[1:], "count": _counts}
    ).to_pandas()

    _chart = (
        alt.Chart(_hist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", bin="binned", title="Commits per Skill"),
            x2="bin_end:Q",
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Commits per Skill", width=600, height=300)
    )

    mo.vstack(
        [
            mo.md(f"""### Commits per Skill

    Most skills have very few commits. Chart clipped at P99 ({_cutoff}); **{_excluded}** skills exceed the cutoff.

    Median: **{_median}** | P75: **{_p75}** | P95: **{_p95}** | Max: **{_max:,}**
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, history, mo, pl):
    # Skill creation timeline — cumulative growth by month
    import datetime

    _cutoff_date = datetime.date(2024, 6, 1)

    _created = (
        history.group_by("url")
        .agg(pl.col("date").min().alias("created"))
        .filter(pl.col("created") >= _cutoff_date)
    )

    # Bin by month (truncate to first of month)
    _created = _created.with_columns(pl.col("created").dt.truncate("1mo").alias("month"))

    _monthly = _created.group_by("month").agg(pl.len().alias("new_skills")).sort("month")

    # Cumulative sum
    _monthly = _monthly.with_columns(pl.col("new_skills").cum_sum().alias("cumulative"))

    _monthly_pd = _monthly.to_pandas()

    _line = (
        alt.Chart(_monthly_pd)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("cumulative:Q", title="Cumulative Skills"),
        )
        .properties(title="Skill Creation Timeline (cumulative)", width=600, height=300)
    )

    _bar = (
        alt.Chart(_monthly_pd)
        .mark_bar(opacity=0.4)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("new_skills:Q", title="New Skills"),
        )
    )

    _total_since = _created.shape[0]
    _before = (
        history.group_by("url")
        .agg(pl.col("date").min().alias("created"))
        .filter(pl.col("created") < _cutoff_date)
        .shape[0]
    )

    mo.vstack(
        [
            mo.md(f"""### Skill Creation Timeline

    First commit date per skill, binned by month. Filtered to 2024-06 onwards (when Claude Code skills were introduced).
    **{_before:,}** skills have first commits before this cutoff (likely not Claude Code skills, or repos reorganized retroactively).
    """),
            alt.layer(_bar, _line).resolve_scale(y="independent"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, history, mo, np, pl):
    # Update frequency — time span between first and last commit for multi-commit skills
    _spans = (
        history.group_by("url")
        .agg(
            [
                pl.col("date").min().alias("first_commit"),
                pl.col("date").max().alias("last_commit"),
                pl.len().alias("commits"),
            ]
        )
        .filter(pl.col("commits") > 1)
        .with_columns(
            (pl.col("last_commit") - pl.col("first_commit")).dt.total_days().alias("span_days")
        )
    )

    _n_multi = _spans.shape[0]
    _n_total = history["url"].n_unique()
    _vals = _spans["span_days"].to_numpy()

    _median = int(np.median(_vals))
    _p75 = int(np.percentile(_vals, 75))
    _p95 = int(np.percentile(_vals, 95))
    _max = int(np.max(_vals))

    _counts, _edges = np.histogram(_vals, bins=50)
    _hist = pl.DataFrame(
        {"bin_start": _edges[:-1], "bin_end": _edges[1:], "count": _counts}
    ).to_pandas()

    _chart = (
        alt.Chart(_hist)
        .mark_bar()
        .encode(
            x=alt.X("bin_start:Q", bin="binned", title="Days Between First and Last Commit"),
            x2="bin_end:Q",
            y=alt.Y("count:Q", title="Skills"),
        )
        .properties(title="Update Span (skills with >1 commit)", width=600, height=300)
    )

    mo.vstack(
        [
            mo.md(f"""### Update Frequency

    Of **{_n_total:,}** skills with history, **{_n_multi:,}** ({_n_multi / _n_total:.1%}) have more than one commit.
    For these, the span between first and last commit:

    Median: **{_median} days** | P75: **{_p75} days** | P95: **{_p95} days** | Max: **{_max:,} days**
    """),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(alt, history, mo, pl):
    # Commit message patterns — top 20 most common messages
    _messages = (
        history.select("commit_message")
        .filter(pl.col("commit_message").is_not_null())
        .with_columns(pl.col("commit_message").str.strip_chars().alias("commit_message"))
        .filter(pl.col("commit_message") != "")
    )

    _msg_counts = _messages["commit_message"].value_counts().sort("count", descending=True).head(20)

    _msg_pd = _msg_counts.to_pandas()
    # Truncate long messages for display
    _msg_pd["label"] = _msg_pd["commit_message"].str[:60]

    _chart = (
        alt.Chart(_msg_pd)
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Occurrences"),
            y=alt.Y("label:N", sort="-x", title=None),
        )
        .properties(title="Top 20 Commit Messages", width=500, height=450)
    )

    _total_commits = _messages.shape[0]
    _top_count = int(_msg_counts["count"].head(1).item())
    _top_msg = _msg_counts["commit_message"].head(1).item()

    mo.vstack(
        [
            mo.md(f"""### Commit Message Patterns

    Most common commit message: **"{_top_msg[:80]}"** ({_top_count:,} / {_total_commits:,} commits).
    """),
            _chart,
        ]
    )
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
    _content_dir = __import__("pathlib").Path("data/content")
    _row = skills.sample(1, seed=1).row(0, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _rel_short = __import__("re").sub(r"/blob/[0-9a-f]+/", "/.../", _rel)
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    import html as _html

    _escaped = _html.escape(_text)

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.accordion(
        {
            f"Sample 1: {_row['words']} words | {_row['lines']} lines | {_row['code_block_count']} code blocks | {'FM' if _row['has_frontmatter'] else 'no FM'} — `{_rel_short}`": mo.Html(
                _pre
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo, skills):
    _content_dir = __import__("pathlib").Path("data/content")
    _row = skills.sample(1, seed=2).row(0, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _rel_short = __import__("re").sub(r"/blob/[0-9a-f]+/", "/.../", _rel)
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    import html as _html

    _escaped = _html.escape(_text)

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.accordion(
        {
            f"Sample 2: {_row['words']} words | {_row['lines']} lines | {_row['code_block_count']} code blocks | {'FM' if _row['has_frontmatter'] else 'no FM'} — `{_rel_short}`": mo.Html(
                _pre
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo, skills):
    _content_dir = __import__("pathlib").Path("data/content")
    _row = skills.sample(1, seed=3).row(0, named=True)
    _rel = _row["url"].replace("https://github.com/", "")
    _rel_short = __import__("re").sub(r"/blob/[0-9a-f]+/", "/.../", _rel)
    _path = _content_dir / _rel
    _text = _path.read_text(errors="replace") if _path.exists() else "(not found)"
    import html as _html

    _escaped = _html.escape(_text)

    _pre = f'<pre style="max-height:400px;overflow:auto;padding:12px;font-size:12px;border-radius:6px;border:1px solid var(--border-color, #ddd)">{_escaped}</pre>'

    mo.accordion(
        {
            f"Sample 3: {_row['words']} words | {_row['lines']} lines | {_row['code_block_count']} code blocks | {'FM' if _row['has_frontmatter'] else 'no FM'} — `{_rel_short}`": mo.Html(
                _pre
            ),
        }
    )
    return


@app.cell
def _(features, mo, pl, skills):
    # Key findings summary
    _n_skills = skills.shape[0]
    _n_repos = skills["repo_key"].n_unique()
    _n_total = features.shape[0]
    _dedup_pct = (_n_total - _n_skills) / _n_total

    _median_prose = int(skills["prose_words"].median())
    _median_lines = int(skills["lines"].median())

    _fm_count = skills.filter(pl.col("has_frontmatter")).shape[0]
    _fm_pct = _fm_count / _n_skills

    _heading_count = skills.filter(pl.col("heading_count") > 0).shape[0]
    _heading_pct = _heading_count / _n_skills

    _code_count = skills.filter(pl.col("code_block_count") > 0).shape[0]
    _code_pct = _code_count / _n_skills

    mo.md(f"""## Key Findings

    - **Dataset**: {_n_skills:,} unique skills across {_n_repos:,} repos after deduplication ({_dedup_pct:.0%} reduction)
    - **Typical skill**: {_median_prose} prose words, {_median_lines} lines, {_fm_pct:.0%} have frontmatter
    - **Structure**: {_heading_pct:.0%} use headings, {_code_pct:.0%} include code blocks
    - **Limitations**: Normalized hash may over-deduplicate; GitHub search introduces selection bias
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Questions for Next Pass

    1. **Template detection** -- Which skills are clearly from templates/generators?
    2. **Content taxonomy** -- Can we cluster skills by purpose (code gen, debugging, docs)?
    3. **Instruction patterns** -- What imperative structures appear in skill text?
    4. **Frontmatter semantics** -- What do tag/name values look like across the dataset?
    5. **Repo enrichment** -- Do stars/language predict skill structure?
    6. **Quality scoring** -- Can LLMs rate skill quality at scale?
    """)
    return


if __name__ == "__main__":
    app.run()
