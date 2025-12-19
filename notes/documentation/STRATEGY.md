# Documentation Strategy

Skillet doesn't fit the traditional "getting started" documentation model.

1. **No standalone value** - You can't "get started" with skillet without already having a skill you want to improve
2. **Value is in the process** - The library teaches a methodology (eval-driven development), not just commands
3. **Best practices ARE the product** - Understanding when and why to use skillet is more important than knowing CLI syntax

## Diátaxis Framework

[Diátaxis](https://diataxis.fr/) proposes four documentation types:

| Type | Purpose | Skillet fit? |
|------|---------|--------------|
| **Tutorials** | Learning-oriented, hands-on | Problematic - need real project context |
| **How-to guides** | Task-oriented, solve specific problems | Good fit for specific scenarios |
| **Reference** | Information-oriented, dry facts | CLI commands, config options |
| **Explanation** | Understanding-oriented, concepts | Core methodology, philosophy |

## The Problem with Tutorials

Traditional tutorials say "follow these steps to build X". But with skillet:

- You need an existing skill to evaluate
- The "project" is improving Claude's behavior
- Success depends on your specific use case

**Attempting a traditional tutorial:**

> "Step 1: Create a skill"
>
> ...but what skill? The user's context matters enormously.

## Proposed Approach: Example-Driven Documentation

Instead of "getting started", lead with **complete end-to-end examples** that demonstrate the methodology.

### Structure

```
docs/
├── index.md              # Philosophy + pointer to examples
├── examples/
│   ├── browser-fallback/ # Complete walkthrough
│   ├── commit-messages/  # Complete walkthrough
│   └── pdf-extraction/   # Complete walkthrough
├── how-to/
│   ├── add-eval.md
│   ├── run-evals.md
│   └── tune-skill.md
└── reference/
    ├── cli.md
    ├── eval-format.md
    └── config.md
```

### The Examples ARE the Tutorial

Each example in `examples/` is a complete narrative:

1. Here's a real skill
2. Here's what Claude gets wrong
3. Here's how we captured that as evals
4. Here's the baseline score
5. Here's how we improved it
6. Here's the final result

The user learns the methodology by seeing it applied, not by following abstract steps.

### Entry Point: "Pick an Example"

Instead of "Getting Started", the homepage says:

> **Learn by example**
>
> Skillet teaches evaluation-driven skill development. Pick an example that matches your use case:
>
> - [Browser automation](examples/browser-fallback/) - Teaching Claude to use Playwright
> - [Commit messages](examples/commit-messages/) - Enforcing project conventions
> - [PDF extraction](examples/pdf-extraction/) - Complex document processing

## How This Maps to Diátaxis

| Diátaxis type | Skillet implementation |
|--------------|------------------------|
| Tutorials | → Examples (complete walkthroughs with real context) |
| How-to guides | → How-to (specific tasks, assumes you've read an example) |
| Reference | → Reference (CLI, config, formats) |
| Explanation | → Woven into examples + dedicated "Why eval-driven?" page |
