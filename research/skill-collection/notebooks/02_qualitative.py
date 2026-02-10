"""LLM-based qualitative analysis of skill content (stub)."""

import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md("""# Qualitative Analysis (Stub)

    LLM-based analysis that requires judgment calls. This notebook is a placeholder
    for future work -- each section describes the analysis to be done and the expected
    data pipeline.
    """)
    return (mo,)


@app.cell
def _(mo):
    mo.md("""## Purpose Taxonomy

    Classify each skill into a primary purpose category:

    | Category | Description | Example |
    |----------|-------------|---------|
    | **Automation** | Automate a repeatable task | CI/CD, linting, deployment |
    | **Guidance** | Teach the agent how to do something | Coding style, commit messages |
    | **Meta** | Configure the agent itself | Model selection, tool permissions |
    | **Enforcement** | Constrain agent behavior | Security rules, review gates |

    **Pipeline:** Sample N skills, send each to Claude with a classification prompt,
    store results in `data/skill_classifications.parquet`.
    """)
    return


@app.cell
def _(mo):
    mo.md("""## Quality / Sophistication Scoring

    Score each skill on a 1-5 sophistication scale:

    1. **Minimal** -- A few lines, no structure
    2. **Basic** -- Has sections but thin content
    3. **Adequate** -- Covers the topic with some depth
    4. **Good** -- Well-structured with examples and edge cases
    5. **System-grade** -- Comprehensive, handles failure modes, has tests/verification

    **Pipeline:** Same LLM classification pass, store alongside purpose taxonomy.
    """)
    return


@app.cell
def _(mo):
    mo.md("""## Content Pattern Detection

    Boolean feature extraction via LLM:

    - `has_examples` -- Contains worked examples or sample code
    - `has_when_to_use` -- Explicitly describes when to apply the skill
    - `has_anti_patterns` -- Describes what NOT to do
    - `has_references` -- Links to external docs or resources
    - `has_verification` -- Describes how to verify the skill worked

    **Pipeline:** Can be batched with the classification pass above.
    """)
    return


@app.cell
def _(mo):
    mo.md("""## Archetype Discovery

    Use embeddings + clustering to find natural groupings:

    1. Embed each skill content with a sentence-transformer model
    2. Reduce dimensionality (UMAP or t-SNE)
    3. Cluster with OPTICS or HDBSCAN
    4. Label clusters by examining representative skills
    5. Visualize as 2D scatter plot colored by cluster

    **Data:**
    - `data/embeddings.npy` -- Dense vectors
    - `data/cluster_info.json` -- Cluster assignments and labels

    **Pipeline:** Compute embeddings in batch, cache to disk. Clustering runs
    on the cached embeddings.
    """)
    return


@app.cell
def _(mo):
    mo.md("""## Next Steps

    1. Build the classification pipeline script (`analyze_skills/classify.py`)
    2. Run on a representative sample (~1000 skills)
    3. Validate taxonomy coverage -- are there skills that don't fit?
    4. Scale to full dataset once prompt is stable
    5. Replace this stub with actual visualizations
    """)
    return


if __name__ == "__main__":
    app.run()
