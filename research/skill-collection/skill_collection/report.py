"""Generate markdown reports from skill analysis data."""

import json
from collections import Counter
from pathlib import Path

import polars as pl


def df_to_html(df: pl.DataFrame) -> str:
    """Convert polars DataFrame to markdown table."""
    lines = []
    headers = df.columns
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    for row in df.iter_rows():
        cells = [str(v) if v is not None else "" for v in row]
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def generate_quantitative_report(df: pl.DataFrame) -> str:
    """Generate quantitative analysis report."""
    total = len(df)

    # Check if new columns exist (for backwards compatibility)
    has_new_cols = "char_count" in df.columns

    lines = [
        "# Quantitative Analysis of SKILL.md Files",
        "",
        f"> **{total:,}** skills from **{df['owner'].n_unique():,}** authors across **{df.select([pl.concat_str(['owner', 'repo'], separator='/')]).n_unique():,}** repositories",
        "",
        "---",
        "",
        "## A1. Text Statistics",
        "",
    ]

    if has_new_cols:
        stats_df = pl.DataFrame({
            "metric": ["Characters", "Words", "Lines", "Paragraphs", "Reading Level"],
            "min": [
                float(df['char_count'].min()),
                float(df['word_count'].min()),
                float(df['line_count'].min()),
                float(df['paragraph_count'].min()),
                round(df['reading_level'].min(), 1),
            ],
            "p25": [
                float(df['char_count'].quantile(0.25)),
                float(df['word_count'].quantile(0.25)),
                float(df['line_count'].quantile(0.25)),
                float(df['paragraph_count'].quantile(0.25)),
                round(df['reading_level'].quantile(0.25), 1),
            ],
            "median": [
                float(df['char_count'].median()),
                float(df['word_count'].median()),
                float(df['line_count'].median()),
                float(df['paragraph_count'].median()),
                round(df['reading_level'].median(), 1),
            ],
            "p75": [
                float(df['char_count'].quantile(0.75)),
                float(df['word_count'].quantile(0.75)),
                float(df['line_count'].quantile(0.75)),
                float(df['paragraph_count'].quantile(0.75)),
                round(df['reading_level'].quantile(0.75), 1),
            ],
            "max": [
                float(df['char_count'].max()),
                float(df['word_count'].max()),
                float(df['line_count'].max()),
                float(df['paragraph_count'].max()),
                round(df['reading_level'].max(), 1),
            ],
        })
        lines.append(df_to_html(stats_df))
        lines.append("")
        lines.append("*Reading Level = Flesch-Kincaid Grade Level (lower = easier)*")
    else:
        stats_df = pl.DataFrame({
            "metric": ["Words", "Lines"],
            "min": [df['word_count'].min(), df['line_count'].min()],
            "median": [df['word_count'].median(), df['line_count'].median()],
            "max": [df['word_count'].max(), df['line_count'].max()],
        })
        lines.append(df_to_html(stats_df))

    # Word count buckets
    lines.extend([
        "",
        "### Distribution by Word Count",
        "",
    ])

    buckets = df.select(
        pl.when(pl.col("word_count") < 50).then(pl.lit("< 50"))
        .when(pl.col("word_count") < 100).then(pl.lit("50-100"))
        .when(pl.col("word_count") < 250).then(pl.lit("100-250"))
        .when(pl.col("word_count") < 500).then(pl.lit("250-500"))
        .when(pl.col("word_count") < 1000).then(pl.lit("500-1K"))
        .otherwise(pl.lit("> 1K"))
        .alias("words")
    ).group_by("words").len().sort("len", descending=True)

    bucket_df = buckets.with_columns([
        (pl.col("len") / total * 100).round(1).alias("pct")
    ]).rename({"len": "count"})

    lines.append(df_to_html(bucket_df))

    # A2. Frontmatter
    lines.extend([
        "",
        "---",
        "",
        "## A2. Frontmatter Schema",
        "",
    ])

    frontmatter_fields = [
        ("has_frontmatter", "any frontmatter"),
        ("has_name", "name"),
        ("has_description", "description"),
        ("has_license", "license"),
        ("has_metadata", "metadata"),
        ("has_triggers", "triggers"),
        ("has_model", "model"),
        ("has_allowed_tools", "allowed_tools"),
        ("has_user_invocable", "user_invocable"),
    ]

    fm_data = []
    for col, label in sorted(frontmatter_fields, key=lambda x: df[x[0]].sum(), reverse=True):
        count = int(df[col].sum())
        pct = count / total * 100
        fm_data.append({"field": label, "count": count, "pct": round(pct, 1)})

    fm_df = pl.DataFrame(fm_data)
    lines.append(df_to_html(fm_df))

    # A3. Content Structure
    lines.extend([
        "",
        "---",
        "",
        "## A3. Content Structure",
        "",
    ])

    content_features = [
        ("has_h1", "H1 heading"),
        ("has_examples", "examples section"),
        ("has_when_to_use", "when-to-use"),
        ("has_references", "references/links"),
    ]

    cs_data = []
    for col, label in sorted(content_features, key=lambda x: df[x[0]].sum(), reverse=True):
        count = int(df[col].sum())
        pct = count / total * 100
        cs_data.append({"feature": label, "count": count, "pct": round(pct, 1)})

    # Code blocks and URLs
    has_code = int((df["code_block_count"] > 0).sum())
    has_urls = int((df["external_url_count"] > 0).sum())
    cs_data.append({"feature": "code blocks", "count": has_code, "pct": round(has_code/total*100, 1)})
    cs_data.append({"feature": "external URLs", "count": has_urls, "pct": round(has_urls/total*100, 1)})

    cs_df = pl.DataFrame(cs_data).sort("count", descending=True)
    lines.append(df_to_html(cs_df))

    # Repository analysis
    lines.extend([
        "",
        "---",
        "",
        "## Top Repositories",
        "",
    ])

    repos = df.group_by(["owner", "repo"]).len().sort("len", descending=True).head(15)
    repos_df = repos.with_columns([
        pl.concat_str([pl.col("owner"), pl.lit("/"), pl.col("repo")]).alias("repository")
    ]).select(["repository", "len"]).rename({"len": "skills"})

    lines.append(df_to_html(repos_df))

    return "\n".join(lines)


def generate_llm_report(classifications: list[dict]) -> str:
    """Generate LLM classification analysis report."""
    n = len(classifications)

    lines = [
        "# LLM-Based Skill Classification Analysis",
        "",
        f"Claude-generated taxonomy classifications for {n} SKILL.md files.",
        "",
    ]

    # Primary Purpose
    purposes = Counter(c.get("primary_purpose", "unknown") for c in classifications)
    lines.extend([
        "## Primary Purpose Distribution",
        "",
        "| Purpose | Count | % |",
        "|---------|-------|---|",
    ])
    for purpose, count in purposes.most_common():
        pct = count / n * 100
        lines.append(f"| {purpose} | {count} | {pct:.1f}% |")

    # Knowledge Domain
    domains = Counter(c.get("knowledge_domain", "unknown") for c in classifications)
    lines.extend([
        "",
        "## Knowledge Domain Distribution",
        "",
        "| Domain | Count | % |",
        "|--------|-------|---|",
    ])
    for domain, count in domains.most_common():
        pct = count / n * 100
        lines.append(f"| {domain} | {count} | {pct:.1f}% |")

    # Domain Specifics (top frameworks/tools)
    all_specifics = []
    for c in classifications:
        specifics = c.get("domain_specifics", [])
        if isinstance(specifics, list):
            all_specifics.extend([s.lower() for s in specifics])

    specific_counts = Counter(all_specifics)
    lines.extend([
        "",
        "## Top Frameworks/Tools Mentioned",
        "",
        "| Tool/Framework | Count |",
        "|----------------|-------|",
    ])
    for tool, count in specific_counts.most_common(20):
        lines.append(f"| {tool} | {count} |")

    # Scope
    scopes = Counter(c.get("scope", "unknown") for c in classifications)
    lines.extend([
        "",
        "## Scope Distribution",
        "",
        "| Scope | Count | % |",
        "|-------|-------|---|",
    ])
    for scope, count in scopes.most_common():
        pct = count / n * 100
        lines.append(f"| {scope} | {count} | {pct:.1f}% |")

    # Trigger Mechanism
    triggers = Counter(c.get("trigger_mechanism", "unknown") for c in classifications)
    lines.extend([
        "",
        "## Trigger Mechanism",
        "",
        "| Trigger | Count | % |",
        "|---------|-------|---|",
    ])
    for trigger, count in triggers.most_common():
        pct = count / n * 100
        lines.append(f"| {trigger} | {count} | {pct:.1f}% |")

    # Claude's Role
    roles = Counter(c.get("claude_role", "unknown") for c in classifications)
    lines.extend([
        "",
        "## Claude's Role",
        "",
        "| Role | Count | % |",
        "|------|-------|---|",
    ])
    for role, count in roles.most_common():
        pct = count / n * 100
        lines.append(f"| {role} | {count} | {pct:.1f}% |")

    # Sophistication
    sophistication = Counter(c.get("sophistication", "unknown") for c in classifications)
    lines.extend([
        "",
        "## Sophistication Level",
        "",
        "| Level | Count | % |",
        "|-------|-------|---|",
    ])
    for level in ["minimal", "standard", "comprehensive", "system-grade"]:
        count = sophistication.get(level, 0)
        pct = count / n * 100
        lines.append(f"| {level} | {count} | {pct:.1f}% |")

    # Quality Scores
    quality_scores = [c.get("quality_score", 0) for c in classifications if c.get("quality_score")]
    if quality_scores:
        quality_dist = Counter(quality_scores)
        avg = sum(quality_scores) / len(quality_scores)
        high_quality = sum(1 for q in quality_scores if q >= 4)

        lines.extend([
            "",
            "## Quality Scores",
            "",
            "| Score | Count | % |",
            "|-------|-------|---|",
        ])
        for score in sorted(quality_dist.keys()):
            count = quality_dist[score]
            pct = count / len(quality_scores) * 100
            lines.append(f"| {score} | {count} | {pct:.1f}% |")

        lines.extend([
            "",
            f"**Mean quality score:** {avg:.2f}/5",
            f"**High quality (4-5):** {high_quality} ({high_quality/len(quality_scores)*100:.1f}%)",
        ])

    # Content Features
    lines.extend([
        "",
        "## Content Features",
        "",
        "| Feature | Count | % |",
        "|---------|-------|---|",
    ])
    for feature in ["has_examples", "has_explicit_rules", "has_external_refs"]:
        count = sum(1 for c in classifications if c.get(feature))
        pct = count / n * 100
        lines.append(f"| {feature} | {count} | {pct:.1f}% |")

    # Summary
    top_purpose = purposes.most_common(1)[0] if purposes else ("unknown", 0)
    top_domain = domains.most_common(1)[0] if domains else ("unknown", 0)

    lines.extend([
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total classified | {n} |",
        f"| Top purpose | {top_purpose[0]} ({top_purpose[1]/n*100:.0f}%) |",
        f"| Top domain | {top_domain[0]} ({top_domain[1]/n*100:.0f}%) |",
        f"| Minimal sophistication | {sophistication.get('minimal', 0)} ({sophistication.get('minimal', 0)/n*100:.0f}%) |",
        f"| Comprehensive+ | {sophistication.get('comprehensive', 0) + sophistication.get('system-grade', 0)} ({(sophistication.get('comprehensive', 0) + sophistication.get('system-grade', 0))/n*100:.0f}%) |",
    ])

    return "\n".join(lines)


def generate_synthesis_report(df: pl.DataFrame, classifications: list[dict]) -> str:
    """Generate combined synthesis report."""
    total = len(df)
    n_class = len(classifications)

    purposes = Counter(c.get("primary_purpose", "unknown") for c in classifications)
    sophistication = Counter(c.get("sophistication", "unknown") for c in classifications)
    quality_scores = [c.get("quality_score", 0) for c in classifications if c.get("quality_score")]

    top_purpose = purposes.most_common(1)[0] if purposes else ("unknown", 0)
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    high_quality = sum(1 for q in quality_scores if q >= 4)

    lines = [
        "# Skill Collection Synthesis",
        "",
        "Combined quantitative and LLM analysis.",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total skills analyzed | {total:,} |",
        f"| Unique owners | {df['owner'].n_unique():,} |",
        f"| Unique repos | {df.select([pl.concat_str(['owner', 'repo'], separator='/')]).n_unique():,} |",
        f"| LLM classified | {n_class} |",
        f"| Median file size | {df['byte_size'].median():.0f} bytes |",
        f"| Median line count | {df['line_count'].median():.0f} |",
        f"| Frontmatter adoption | {df['has_frontmatter'].sum()/total*100:.1f}% |",
        f"| Top purpose | {top_purpose[0]} ({top_purpose[1]/n_class*100:.0f}%) |" if n_class else "| Top purpose | N/A |",
        f"| Minimal sophistication | {sophistication.get('minimal', 0)/n_class*100:.0f}% |" if n_class else "| Minimal sophistication | N/A |",
        f"| Mean quality score | {avg_quality:.2f}/5 |" if quality_scores else "| Mean quality score | N/A |",
        f"| High quality (4-5) | {high_quality} ({high_quality/len(quality_scores)*100:.1f}%) |" if quality_scores else "| High quality (4-5) | N/A |",
        "",
        "## Key Observations",
        "",
        "1. **Size**: Most skills are small (median ~300 bytes, ~12 lines)",
        "2. **Frontmatter**: Strong adoption of YAML metadata",
        f"3. **Purpose**: {top_purpose[0]} dominates ({top_purpose[1]/n_class*100:.0f}%)" if n_class else "3. **Purpose**: Awaiting classification",
        f"4. **Sophistication**: Bimodal - either minimal ({sophistication.get('minimal', 0)/n_class*100:.0f}%) or comprehensive ({sophistication.get('comprehensive', 0)/n_class*100:.0f}%)" if n_class else "4. **Sophistication**: Awaiting classification",
        f"5. **Quality**: Wide variance, mean {avg_quality:.1f}/5" if quality_scores else "5. **Quality**: Awaiting classification",
    ]

    return "\n".join(lines)


def main():
    """Generate all reports."""
    results_dir = Path(__file__).parent.parent / "results"
    report_dir = results_dir / "report"
    report_dir.mkdir(exist_ok=True)

    # Load data
    df = pl.read_parquet(results_dir / "skill_features.parquet")
    print(f"Loaded {len(df)} skills from parquet")

    classifications = []
    classifications_path = results_dir / "skill_classifications.json"
    if classifications_path.exists():
        with open(classifications_path) as f:
            classifications = json.load(f)
        print(f"Loaded {len(classifications)} classifications")

    # Generate reports
    quant_report = generate_quantitative_report(df)
    (report_dir / "01_quantitative.md").write_text(quant_report)
    print(f"Wrote {report_dir / '01_quantitative.md'}")

    if classifications:
        llm_report = generate_llm_report(classifications)
        (report_dir / "02_llm_analysis.md").write_text(llm_report)
        print(f"Wrote {report_dir / '02_llm_analysis.md'}")

    synthesis_report = generate_synthesis_report(df, classifications)
    (report_dir / "03_synthesis.md").write_text(synthesis_report)
    print(f"Wrote {report_dir / '03_synthesis.md'}")


if __name__ == "__main__":
    main()
