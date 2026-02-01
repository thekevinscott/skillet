import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # Quantitative Analysis of SKILL.md Files

    This notebook analyzes the structural features extracted from valid SKILL.md files.
    """)
    return


@app.cell
def _():
    import polars as pl
    import altair as alt
    from pathlib import Path

    results_dir = Path(__file__).parent.parent / "results"
    content_dir = results_dir / "content"
    df = pl.read_parquet(results_dir / "skill_features.parquet")
    print(f"Loaded {len(df)} skills")
    return alt, content_dir, df, pl


@app.cell
def _(mo):
    mo.md("""
## A1. Basic Statistics

The 45x gap between Anthropic's skills and the median is the headline here. Either the
community is doing it wrong, or Anthropic's document-processing skills are outliers.
Worth investigating: do the longer community skills (p95+) actually perform better?
""")
    return


@app.cell
def _(alt, df, mo, pl):
    # Clip to 95th percentile for readable histograms
    word_p95 = float(df["word_count"].quantile(0.95))
    line_p95 = float(df["line_count"].quantile(0.95))
    byte_p95 = float(df["byte_size"].quantile(0.95))

    chart_data = df.select(["word_count", "line_count", "byte_size"]).to_pandas()

    word_hist = alt.Chart(chart_data).mark_bar().encode(
        alt.X("word_count:Q", bin=alt.Bin(maxbins=30), title="Word Count", scale=alt.Scale(domain=[0, word_p95])),
        alt.Y("count()", title="Count"),
    ).properties(width=250, height=180, title=f"Word Count (clipped at p95={word_p95:.0f})")

    line_hist = alt.Chart(chart_data).mark_bar().encode(
        alt.X("line_count:Q", bin=alt.Bin(maxbins=30), title="Line Count", scale=alt.Scale(domain=[0, line_p95])),
        alt.Y("count()", title="Count"),
    ).properties(width=250, height=180, title=f"Line Count (clipped at p95={line_p95:.0f})")

    byte_hist = alt.Chart(chart_data).mark_bar().encode(
        alt.X("byte_size:Q", bin=alt.Bin(maxbins=30), title="Bytes", scale=alt.Scale(domain=[0, byte_p95])),
        alt.Y("count()", title="Count"),
    ).properties(width=250, height=180, title=f"File Size (clipped at p95={byte_p95:.0f})")

    charts = mo.hstack([word_hist, line_hist, byte_hist])

    # Summary statistics table
    stats_rows = []
    for col, name in [("word_count", "Words"), ("line_count", "Lines"), ("byte_size", "Bytes")]:
        data = df[col]
        stats_rows.append({
            "Metric": name,
            "Min": int(data.min()),
            "P25": int(data.quantile(0.25)),
            "Median": int(data.median()),
            "P75": int(data.quantile(0.75)),
            "Max": int(data.max()),
            "Mean": round(data.mean(), 1),
        })

    stats_md = mo.md(f"""
| Metric | Min | P25 | Median | P75 | Max | Mean |
|--------|-----|-----|--------|-----|-----|------|
| Words | {stats_rows[0]['Min']} | {stats_rows[0]['P25']} | {stats_rows[0]['Median']} | {stats_rows[0]['P75']} | {stats_rows[0]['Max']} | {stats_rows[0]['Mean']} |
| Lines | {stats_rows[1]['Min']} | {stats_rows[1]['P25']} | {stats_rows[1]['Median']} | {stats_rows[1]['P75']} | {stats_rows[1]['Max']} | {stats_rows[1]['Mean']} |
| Bytes | {stats_rows[2]['Min']} | {stats_rows[2]['P25']} | {stats_rows[2]['Median']} | {stats_rows[2]['P75']} | {stats_rows[2]['Max']} | {stats_rows[2]['Mean']} |
""")

    mo.vstack([charts, stats_md])
    return




@app.cell
def _(alt, df, mo, pl):
    # Word count buckets as bar chart
    word_buckets = df.select(
        pl.when(pl.col("word_count") < 50).then(pl.lit("< 50"))
        .when(pl.col("word_count") < 100).then(pl.lit("50-100"))
        .when(pl.col("word_count") < 250).then(pl.lit("100-250"))
        .when(pl.col("word_count") < 500).then(pl.lit("250-500"))
        .otherwise(pl.lit("> 500"))
        .alias("bucket")
    ).group_by("bucket").len()

    bucket_order = ["< 50", "50-100", "100-250", "250-500", "> 500"]
    bucket_chart = alt.Chart(word_buckets.to_pandas()).mark_bar().encode(
        alt.X("bucket:N", title="Word Count Range", sort=bucket_order),
        alt.Y("len:Q", title="Number of Skills"),
        tooltip=["bucket", "len"]
    ).properties(width=400, height=250, title="Skills by Word Count Bucket")

    mo.vstack([bucket_chart, mo.md("*Most skills are under 250 words*")])
    return


@app.cell
def _(mo):
    mo.callout(mo.md("""
**Comparison: Anthropic's Official Skills**

| Source | Words | Lines |
|--------|------:|------:|
| [anthropics/skills docx](https://github.com/anthropics/skills/blob/main/skills/docx/SKILL.md) | 1,847 | 250 |
| [anthropics/skills pdf](https://github.com/anthropics/skills/blob/main/skills/pdf/SKILL.md) | ~1,850 | ~420 |
| **Wild skills (median)** | **41** | **13** |
| Wild skills (p75) | ~150 | ~40 |

Anthropic's production skills are **~45x longer** than the median skill in the wild.
This suggests either most community skills are too minimal to be effective,
or Anthropic's examples are overengineered for document processing specifically.
"""), kind="warn")
    return


@app.cell
def _(mo):
    mo.md("""
## A2. Frontmatter Schema Analysis

People know they need frontmatter (76%) but aren't using the advanced features. Only 28%
are slash-command invocable, only 50% have triggers. Most skills are passive context that
Claude *might* pick up, not active tools. This is a UX problem - triggers are confusing.
""")
    return


@app.cell
def _(df, mo):
    total = len(df)
    frontmatter_stats = {
        "has_frontmatter": df["has_frontmatter"].sum(),
        "has_name": df["has_name"].sum(),
        "has_description": df["has_description"].sum(),
        "has_license": df["has_license"].sum(),
        "has_metadata": df["has_metadata"].sum(),
        "has_triggers": df["has_triggers"].sum(),
        "has_model": df["has_model"].sum(),
        "has_allowed_tools": df["has_allowed_tools"].sum(),
        "has_user_invocable": df["has_user_invocable"].sum(),
    }

    rows = [
        f"| {f} | {c} | {c/total*100:.1f}% |"
        for f, c in sorted(frontmatter_stats.items(), key=lambda x: x[1], reverse=True)
    ]

    mo.md(f"""
    ### Frontmatter Field Presence

    | Field | Count | % |
    |-------|-------|---|
    {chr(10).join(rows)}
    """)
    return


@app.cell
def _(df):
    # Frontmatter field count distribution
    field_count_dist = df.group_by("frontmatter_field_count").len().sort("frontmatter_field_count")
    field_count_dist
    return


@app.cell
def _(mo):
    mo.md("""
## A3. Content Structure Analysis

Only 34% have examples - this is the biggest missed opportunity. Examples are how you
actually teach Claude behavior. The "has_examples" detection might be too strict though;
worth spot-checking if skills have inline examples that aren't in code blocks.
""")
    return


@app.cell
def _(df, mo):
    total2 = len(df)
    content_stats = {
        "has_h1": df["has_h1"].sum(),
        "has_examples": df["has_examples"].sum(),
        "has_when_to_use": df["has_when_to_use"].sum(),
        "has_references": df["has_references"].sum(),
        "has_code_blocks": (df["code_block_count"] > 0).sum(),
        "has_external_urls": (df["external_url_count"] > 0).sum(),
    }

    rows2 = [
        f"| {f} | {c} | {c/total2*100:.1f}% |"
        for f, c in sorted(content_stats.items(), key=lambda x: x[1], reverse=True)
    ]

    mo.md(f"""
    ### Content Structure Presence

    | Feature | Count | % |
    |---------|-------|---|
    {chr(10).join(rows2)}
    """)
    return


@app.cell
def _(df):
    # Code block distribution
    code_block_dist = df.group_by("code_block_count").len().sort("code_block_count").head(15)
    code_block_dist
    return


@app.cell
def _(mo):
    mo.md("""
## Repository Analysis

Look for power users in the top 20 - these are people who've invested heavily in skills
and might have best practices worth studying. Also check if high-skill-count repos are
"skill libraries" vs monorepos that happen to have many skills.
""")
    return


@app.cell
def _(df):
    # Skills per owner
    skills_per_owner = df.group_by("owner").len().sort("len", descending=True).head(20)
    skills_per_owner
    return


@app.cell
def _(df):
    # Skills per repo
    skills_per_repo = df.group_by(["owner", "repo"]).len().sort("len", descending=True).head(20)
    skills_per_repo
    return


@app.cell
def _(mo):
    mo.md("""
## Quality Indicators

The bimodal distribution is interesting - people either dash off a quick note or invest
heavily. No middle ground. The scoring formula is rough (just counting booleans); a
better version would weight examples more heavily since they're the highest-signal feature.
""")
    return


@app.cell
def _(df, pl):
    # Create quality score
    df_quality = df.with_columns([
        (
            pl.col("has_frontmatter").cast(pl.Int32) +
            pl.col("has_name").cast(pl.Int32) +
            pl.col("has_description").cast(pl.Int32) +
            pl.col("has_h1").cast(pl.Int32) +
            pl.col("has_examples").cast(pl.Int32) +
            pl.col("has_when_to_use").cast(pl.Int32) +
            pl.col("has_references").cast(pl.Int32) +
            (pl.col("heading_count") > 2).cast(pl.Int32) +
            (pl.col("code_block_count") > 0).cast(pl.Int32)
        ).alias("quality_score")
    ])

    quality_dist = df_quality.group_by("quality_score").len().sort("quality_score")
    quality_dist
    return (df_quality,)


@app.cell
def _(df_quality, pl):
    # High quality skills
    top_quality = df_quality.filter(pl.col("quality_score") >= 7).sort("byte_size", descending=True)
    top_quality.select(["owner", "repo", "path", "quality_score", "byte_size"]).head(15)
    return (top_quality,)


@app.cell
def _(content_dir):
    def read_skill_content(row: dict, max_chars: int = 2000) -> str:
        """Read skill content from disk, truncating if needed."""
        url = row["url"]
        parts = url.replace("https://github.com/", "").split("/")
        owner, repo = parts[0], parts[1]
        ref = parts[3]
        path = "/".join(parts[4:])

        content_path = content_dir / owner / repo / "blob" / ref / path
        if content_path.exists():
            content = content_path.read_text()
            if len(content) > max_chars:
                return content[:max_chars] + f"\n\n... [truncated, {len(content)} total chars]"
            return content
        return f"[Content not found]"
    return (read_skill_content,)


@app.cell
def _(mo):
    mo.md("""
## Skill Excerpts

Ground truth check. Do the high-quality skills actually look good? Do the minimal ones
look useless or are they legitimately concise? The scoring might be penalizing
well-written short skills.
""")
    return


@app.cell
def _(mo, read_skill_content, top_quality):
    # Show top 3 high-quality skills
    excerpts = []
    for row in top_quality.head(3).iter_rows(named=True):
        content = read_skill_content(row, max_chars=1500)
        excerpts.append(mo.md(f"""
### {row['owner']}/{row['repo']}
**Path:** `{row['path']}`
**Size:** {row['byte_size']} bytes, {row['word_count']} words | **Quality Score:** {row['quality_score']}/9

```markdown
{content}
```
"""))
    mo.vstack([mo.md("### High-Quality Skills (score >= 7)")] + excerpts)
    return


@app.cell
def _(df_quality, mo, pl, read_skill_content):
    # Show minimal skills for contrast
    minimal_skills = df_quality.filter(
        (pl.col("quality_score") <= 2) &
        (pl.col("byte_size") < 200) &
        (pl.col("byte_size") > 50)
    ).sort("byte_size")

    minimal_excerpts = []
    for row in minimal_skills.head(3).iter_rows(named=True):
        content = read_skill_content(row, max_chars=500)
        minimal_excerpts.append(mo.md(f"""
### {row['owner']}/{row['repo']}
**Path:** `{row['path']}`
**Size:** {row['byte_size']} bytes, {row['word_count']} words | **Quality Score:** {row['quality_score']}/9

```markdown
{content}
```
"""))
    mo.vstack([mo.md("### Minimal Skills (score <= 2, < 200 bytes)")] + minimal_excerpts)
    return


@app.cell
def _(df, mo, pl):
    # Summary
    total3 = len(df)
    mo.md(f"""
    ## Summary Statistics

    | Metric | Value |
    |--------|-------|
    | Total skills | {total3:,} |
    | Unique owners | {df['owner'].n_unique():,} |
    | Unique repos | {df.select([pl.concat_str(['owner', 'repo'], separator='/')]).n_unique():,} |
    | Median words | {df['word_count'].median():.0f} |
    | Median lines | {df['line_count'].median():.0f} |
    | With frontmatter | {df['has_frontmatter'].sum()} ({df['has_frontmatter'].sum()/total3*100:.1f}%) |
    | With description | {df['has_description'].sum()} ({df['has_description'].sum()/total3*100:.1f}%) |
    """)
    return


if __name__ == "__main__":
    app.run()
