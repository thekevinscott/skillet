# Overview

A simple, open format for evaluation-driven Claude Code skill development.

Skillet helps you capture failures, run systematic evaluations, and iterate on your skills with data—not hunches.

## Why Skillet?

Claude Code skills are powerful, but often don't have the context they need to do real work reliably. Skillet solves this by giving you tools to:

**For skill authors:** Build capabilities once and test them systematically across multiple scenarios.

**For teams:** Capture organizational knowledge in portable, version-controlled evaluation suites.

**For production:** Know your skills work before deploying them, with quantitative feedback on improvements.

## What can Skillet enable?

- **Capture gaps**: Record when Claude Code fails or produces suboptimal results. Turn frustrations into test cases.
- **Run evaluations**: Systematically test your skills against captured scenarios. Get quantitative feedback on improvements.
- **Iterate with data**: Make targeted improvements based on actual failure modes.
- **Ship with confidence**: Know your skills work before deploying them to production.

## Quick Start

Install Skillet:

```bash
pip install pyskillet
```

Then capture evals, create a skill, and tune it:

```bash
# In Claude Code, capture a failure with /skillet:add
# Then run baseline eval
skillet eval my-skill

# Create a skill from captured evals
skillet create my-skill

# Eval with the skill
skillet eval my-skill ~/.claude/skills/my-skill

# Iteratively improve
skillet tune my-skill ~/.claude/skills/my-skill
```

## Get started

<div class="card-grid">
  <a href="/getting-started" class="card">
    <h3>Getting Started</h3>
    <p>Step-by-step guide to your first evaluation-driven skill.</p>
  </a>
  <a href="/reference/cli" class="card">
    <h3>CLI Reference</h3>
    <p>Complete documentation for all Skillet commands.</p>
  </a>
  <a href="https://github.com/thekevinscott/skillet" class="card">
    <h3>View on GitHub</h3>
    <p>Browse the source code, report issues, and contribute.</p>
  </a>
</div>
