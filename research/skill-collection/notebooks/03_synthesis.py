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
    # Skill Collection Synthesis

    Combined quantitative and LLM analysis with visualizations.
    """)
    return


@app.cell
def _():
    import json
    import polars as pl
    import matplotlib.pyplot as plt
    from pathlib import Path
    from collections import Counter

    results_dir = Path(__file__).parent.parent / "results"
    df = pl.read_parquet(results_dir / "skill_features.parquet")
    with open(results_dir / "skill_classifications.json") as f:
        classifications = json.load(f)

    print(f"Quantitative: {len(df)} skills")
    print(f"LLM classified: {len(classifications)} skills")
    return Counter, classifications, df, pl, plt


@app.cell
def _(mo):
    mo.md("""
    ## Size Distribution
    """)
    return


@app.cell
def _(df, plt):
    fig1, axes = plt.subplots(1, 2, figsize=(12, 4))

    ax1 = axes[0]
    byte_sizes = df["byte_size"].to_list()
    ax1.hist(byte_sizes, bins=50, edgecolor='white', alpha=0.7, color='steelblue')
    ax1.axvline(df["byte_size"].median(), color='red', linestyle='--', label=f'Median: {df["byte_size"].median():.0f}')
    ax1.set_xlabel('File Size (bytes)')
    ax1.set_ylabel('Count')
    ax1.set_title('File Size Distribution')
    ax1.legend()
    ax1.set_xlim(0, 5000)

    ax2 = axes[1]
    line_counts = df["line_count"].to_list()
    ax2.hist(line_counts, bins=50, edgecolor='white', alpha=0.7, color='green')
    ax2.axvline(df["line_count"].median(), color='red', linestyle='--', label=f'Median: {df["line_count"].median():.0f}')
    ax2.set_xlabel('Line Count')
    ax2.set_ylabel('Count')
    ax2.set_title('Line Count Distribution')
    ax2.legend()
    ax2.set_xlim(0, 100)

    plt.tight_layout()
    fig1
    return


@app.cell
def _(mo):
    mo.md("""
    ## Primary Purpose
    """)
    return


@app.cell
def _(Counter, classifications, plt):
    purposes = Counter(c.get("primary_purpose", "unknown") for c in classifications)
    sorted_p = sorted(purposes.items(), key=lambda x: x[1], reverse=True)
    labels = [p[0] for p in sorted_p]
    counts = [p[1] for p in sorted_p]

    fig2, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Set2.colors[:len(labels)]
    bars = ax.barh(labels[::-1], counts[::-1], color=colors[::-1], edgecolor='white')
    ax.set_xlabel('Count')
    ax.set_title(f'Primary Purpose (n={len(classifications)})')

    for _i, (_label, _count) in enumerate(zip(labels[::-1], counts[::-1])):
        _pct = _count / len(classifications) * 100
        ax.text(_count + 0.5, _i, f'{_pct:.0f}%', va='center')

    plt.tight_layout()
    fig2
    return


@app.cell
def _(mo):
    mo.md("""
    ## Sophistication Distribution
    """)
    return


@app.cell
def _(Counter, classifications, plt):
    sophistication = Counter(c.get("sophistication", "unknown") for c in classifications)
    soph_order = ["minimal", "standard", "comprehensive", "system-grade"]
    soph_counts = [sophistication.get(s, 0) for s in soph_order]

    fig3, ax3 = plt.subplots(figsize=(8, 5))
    colors3 = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1']
    ax3.bar(soph_order, soph_counts, color=colors3, edgecolor='white')
    ax3.set_ylabel('Count')
    ax3.set_title(f'Sophistication Distribution (n={len(classifications)})')

    for _i, (_s, _c) in enumerate(zip(soph_order, soph_counts)):
        _pct = _c / len(classifications) * 100
        ax3.text(_i, _c + 1, f'{_pct:.0f}%', ha='center')

    plt.tight_layout()
    fig3
    return


@app.cell
def _(mo):
    mo.md("""
    ## Quality Score Distribution
    """)
    return


@app.cell
def _(Counter, classifications, plt):
    quality_scores = [c.get("quality_score", 0) for c in classifications if c.get("quality_score")]
    quality_dist = Counter(quality_scores)

    fig4, ax4 = plt.subplots(figsize=(8, 5))
    scores = sorted(quality_dist.keys())
    q_counts = [quality_dist[s] for s in scores]
    colors4 = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60']
    ax4.bar([str(s) for s in scores], q_counts, color=[colors4[s-1] if s <= 5 else '#999' for s in scores], edgecolor='white')
    ax4.set_xlabel('Quality Score')
    ax4.set_ylabel('Count')
    ax4.set_title(f'Quality Score Distribution (n={len(quality_scores)})')

    for _i, (_s, _c) in enumerate(zip(scores, q_counts)):
        ax4.text(_i, _c + 1, str(_c), ha='center')

    plt.tight_layout()
    fig4
    return


@app.cell
def _(mo):
    mo.md("""
    ## Top Repositories
    """)
    return


@app.cell
def _(df, plt):
    repos = df.group_by(["owner", "repo"]).len().sort("len", descending=True).head(15)
    repo_names = [f"{r['owner']}/{r['repo']}" for r in repos.to_dicts()]
    repo_counts = repos["len"].to_list()

    fig5, ax5 = plt.subplots(figsize=(12, 6))
    ax5.barh(repo_names[::-1], repo_counts[::-1], color='teal', edgecolor='white')
    ax5.set_xlabel('Number of Skills')
    ax5.set_title('Top 15 Repositories')

    for _i, _count in enumerate(repo_counts[::-1]):
        ax5.text(_count + 0.2, _i, str(_count), va='center')

    plt.tight_layout()
    fig5
    return


@app.cell
def _(Counter, classifications, df, mo, pl):
    # Executive Summary
    total = len(df)
    n_class = len(classifications)
    purposes2 = Counter(c.get("primary_purpose", "unknown") for c in classifications)
    sophistication2 = Counter(c.get("sophistication", "unknown") for c in classifications)
    quality_scores2 = [c.get("quality_score", 0) for c in classifications if c.get("quality_score")]

    top_purpose = purposes2.most_common(1)[0] if purposes2 else ("unknown", 0)
    avg_quality = sum(quality_scores2) / len(quality_scores2) if quality_scores2 else 0
    high_quality = sum(1 for q in quality_scores2 if q >= 4)

    mo.md(f"""
    ## Executive Summary

    | Metric | Value |
    |--------|-------|
    | Total skills analyzed | {total:,} |
    | Unique owners | {df['owner'].n_unique():,} |
    | Unique repos | {df.select([pl.concat_str(['owner', 'repo'], separator='/')]).n_unique():,} |
    | LLM classified | {n_class} |
    | Median file size | {df['byte_size'].median():.0f} bytes |
    | Frontmatter adoption | {df['has_frontmatter'].sum()/total*100:.1f}% |
    | Top purpose | {top_purpose[0]} ({top_purpose[1]/n_class*100:.0f}%) |
    | Minimal sophistication | {sophistication2.get('minimal', 0)/n_class*100:.0f}% |
    | Mean quality score | {avg_quality:.2f}/5 |
    | High quality (4-5) | {high_quality} ({high_quality/len(quality_scores2)*100:.1f}%) |
    """)
    return


if __name__ == "__main__":
    app.run()
