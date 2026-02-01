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
    # LLM-Based Skill Classification Analysis

    This notebook analyzes the Claude-generated taxonomy classifications of SKILL.md files.
    """)
    return


@app.cell
def _():
    import json
    from pathlib import Path
    from collections import Counter

    results_dir = Path(__file__).parent.parent / "results"
    with open(results_dir / "skill_classifications.json") as f:
        classifications = json.load(f)

    print(f"Loaded {len(classifications)} classifications")
    return Counter, classifications


@app.cell
def _(mo):
    mo.md("""
    ## Primary Purpose Distribution
    """)
    return


@app.cell
def _(Counter, classifications, mo):
    purposes = Counter(c.get("primary_purpose", "unknown") for c in classifications)
    n = len(classifications)
    rows = [f"| {p} | {c} | {c/n*100:.1f}% |" for p, c in purposes.most_common()]

    mo.md(f"""
    | Purpose | Count | % |
    |---------|-------|---|
    {chr(10).join(rows)}
    """)
    return (purposes,)


@app.cell
def _(mo):
    mo.md("""
    ## Knowledge Domain Distribution
    """)
    return


@app.cell
def _(Counter, classifications, mo):
    domains = Counter(c.get("knowledge_domain", "unknown") for c in classifications)
    n2 = len(classifications)
    rows2 = [f"| {d} | {c} | {c/n2*100:.1f}% |" for d, c in domains.most_common()]

    mo.md(f"""
    | Domain | Count | % |
    |--------|-------|---|
    {chr(10).join(rows2)}
    """)
    return (domains,)


@app.cell
def _(mo):
    mo.md("""
    ## Domain Specifics (Frameworks/Tools)
    """)
    return


@app.cell
def _(Counter, classifications):
    all_specifics = [
        s.lower()
        for cl in classifications
        for s in (cl.get("domain_specifics") or [])
        if isinstance(cl.get("domain_specifics"), list)
    ]

    specific_counts = Counter(all_specifics)
    specific_counts.most_common(30)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Scope Distribution
    """)
    return


@app.cell
def _(Counter, classifications, mo):
    scopes = Counter(c.get("scope", "unknown") for c in classifications)
    n3 = len(classifications)
    rows3 = [f"| {s} | {c} | {c/n3*100:.1f}% |" for s, c in scopes.most_common()]

    mo.md(f"""
    | Scope | Count | % |
    |-------|-------|---|
    {chr(10).join(rows3)}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Trigger Mechanism
    """)
    return


@app.cell
def _(Counter, classifications, mo):
    triggers = Counter(c.get("trigger_mechanism", "unknown") for c in classifications)
    n4 = len(classifications)
    rows4 = [f"| {t} | {c} | {c/n4*100:.1f}% |" for t, c in triggers.most_common()]

    mo.md(f"""
    | Trigger | Count | % |
    |---------|-------|---|
    {chr(10).join(rows4)}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Claude's Role
    """)
    return


@app.cell
def _(Counter, classifications, mo):
    roles = Counter(c.get("claude_role", "unknown") for c in classifications)
    n5 = len(classifications)
    rows5 = [f"| {r} | {c} | {c/n5*100:.1f}% |" for r, c in roles.most_common()]

    mo.md(f"""
    | Role | Count | % |
    |------|-------|---|
    {chr(10).join(rows5)}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Sophistication Level
    """)
    return


@app.cell
def _(Counter, classifications, mo):
    sophistication = Counter(c.get("sophistication", "unknown") for c in classifications)
    n6 = len(classifications)
    levels = ["minimal", "standard", "comprehensive", "system-grade"]
    rows6 = [f"| {lv} | {sophistication.get(lv, 0)} | {sophistication.get(lv, 0)/n6*100:.1f}% |" for lv in levels]

    mo.md(f"""
    | Level | Count | % |
    |-------|-------|---|
    {chr(10).join(rows6)}
    """)
    return (sophistication,)


@app.cell
def _(mo):
    mo.md("""
    ## Quality Scores
    """)
    return


@app.cell
def _(Counter, classifications, mo):
    quality_scores = [c.get("quality_score", 0) for c in classifications if c.get("quality_score")]
    quality_dist = Counter(quality_scores)
    qlen = len(quality_scores)
    rows7 = [f"| {sc} | {quality_dist[sc]} | {quality_dist[sc]/qlen*100:.1f}% |" for sc in sorted(quality_dist.keys())]

    avg = sum(quality_scores) / qlen if qlen else 0
    high_quality = sum(1 for q in quality_scores if q >= 4)

    mo.md(f"""
    | Score | Count | % |
    |-------|-------|---|
    {chr(10).join(rows7)}

    **Mean quality score:** {avg:.2f}
    **High quality (4-5):** {high_quality} ({high_quality/qlen*100:.1f}%)
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Content Features
    """)
    return


@app.cell
def _(classifications, mo):
    features = {
        "has_examples": sum(1 for c in classifications if c.get("has_examples")),
        "has_explicit_rules": sum(1 for c in classifications if c.get("has_explicit_rules")),
        "has_external_refs": sum(1 for c in classifications if c.get("has_external_refs")),
    }
    n7 = len(classifications)
    rows8 = [f"| {f} | {ct} | {ct/n7*100:.1f}% |" for f, ct in sorted(features.items(), key=lambda x: x[1], reverse=True)]

    mo.md(f"""
    | Feature | Count | % |
    |---------|-------|---|
    {chr(10).join(rows8)}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Exemplary Skills by Purpose
    """)
    return


@app.cell
def _(classifications, mo):
    purpose_examples = {}
    for cl in classifications:
        purpose = cl.get("primary_purpose", "unknown")
        quality = cl.get("quality_score", 0)
        if quality >= 4:
            if purpose not in purpose_examples:
                purpose_examples[purpose] = []
            purpose_examples[purpose].append(cl)

    lines = []
    for key in sorted(purpose_examples.keys()):
        examples = purpose_examples[key][:3]
        lines.append(f"### {key.upper()} ({len(purpose_examples[key])} high-quality)")
        for example in examples:
            summary = example.get("summary", "")[:80]
            lines.append(f"- [{example.get('quality_score')}] {summary}...")
        lines.append("")

    mo.md("\n".join(lines))
    return


@app.cell
def _(classifications, domains, mo, purposes, sophistication):
    n8 = len(classifications)
    top_purpose = purposes.most_common(1)[0] if purposes else ("unknown", 0)
    top_domain = domains.most_common(1)[0] if domains else ("unknown", 0)

    mo.md(f"""
    ## Summary

    | Metric | Value |
    |--------|-------|
    | Total classified | {n8} |
    | Top purpose | {top_purpose[0]} ({top_purpose[1]/n8*100:.0f}%) |
    | Top domain | {top_domain[0]} ({top_domain[1]/n8*100:.0f}%) |
    | Minimal sophistication | {sophistication.get('minimal', 0)} ({sophistication.get('minimal', 0)/n8*100:.0f}%) |
    | Comprehensive+ | {sophistication.get('comprehensive', 0) + sophistication.get('system-grade', 0)} ({(sophistication.get('comprehensive', 0) + sophistication.get('system-grade', 0))/n8*100:.0f}%) |
    """)
    return


if __name__ == "__main__":
    app.run()
