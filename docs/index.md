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

Then capture a gap, run an eval, and improve your skill:

```bash
# Capture a failure scenario
skillet gap add

# Run evaluations
skillet eval run

# Improve your skill based on results
skillet tune
```

## Get started

<div class="card-grid">
  <a href="/getting-started" class="card">
    <h3>Getting Started</h3>
    <p>Learn about skills, how they work, and why they matter.</p>
  </a>
  <a href="/interactive-tutorial" class="card">
    <h3>Interactive Tutorial</h3>
    <p>Try Skillet in your browser with our interactive tutorial.</p>
  </a>
  <a href="https://github.com/thekevinscott/skillet" class="card">
    <h3>View on GitHub</h3>
    <p>Browse the source code, report issues, and contribute.</p>
  </a>
</div>
