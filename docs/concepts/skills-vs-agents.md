# Skills vs Agents

Skillet evaluates **skills**, not agents.

A *skill* is a SKILL.md file that shapes how Claude Code behaves in a specific context — what format to use for code reviews, how to structure commit messages, which libraries to prefer. The skill provides instructions, constraints, and examples that steer behavior.

An *agent* is the underlying capability: Claude Code reading files, running commands, writing code, browsing the web. The agent is the engine. The skill is the steering.

## Why the distinction matters

When people say "I want to evaluate my coding agent," they usually mean one of two things:

1. **Can the agent do X at all?** — This is a capability question about the model and tooling. Skillet doesn't address this. If Claude Code can't run shell commands, no skill will fix that.

2. **Does the agent do X the way I want?** — This is a behavior question. The agent *can* write code reviews, but does it use conventional comments format? Does it flag security issues with the right severity? This is what skills control, and what Skillet evaluates.

Most practical frustrations fall into category 2. The model is capable enough; the problem is that it doesn't know your team's conventions, your preferred patterns, or your quality bar. Skills close that gap.

## Grading techniques transfer

Because Skillet evaluates behavior rather than capability, the same grading approaches work across different agent contexts:

- A **coding skill** (e.g., conventional comments) gets graded on whether the output matches format expectations.
- A **research skill** (e.g., summarize papers) gets graded on whether the output covers required sections.
- A **computer use skill** (e.g., navigate a UI) gets graded on whether it performs the right sequence of actions.

The eval structure is the same: a prompt, an expected behavior, and a judge that checks whether the output meets the expectation. What changes across agent types is the *content* of the evals — the prompts, the expectations, and what "good" looks like — not the evaluation machinery.

## Agent type is orthogonal

You don't need to declare what kind of agent your skill targets. Skillet doesn't have an "agent type" field, and intentionally so. A skill that targets Claude Code for coding tasks uses the same eval format, the same CLI commands, and the same tuning loop as a skill that targets Claude Code for research tasks.

If your skill works, the evals will show it. If it doesn't, the evals will show that too. The agent type is context for *writing* good evals, not a configuration parameter.
