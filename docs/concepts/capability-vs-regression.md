# Capability vs Regression Evals

Skillet uses the same eval format and API for two distinct purposes. The difference is in how you interpret results and when you run them.

## Capability evals

A capability eval asks: **can the skill handle this scenario at all?**

You write these during development, when you're exploring what the skill can do. The metric that matters is **pass@k** — did *any* of the k samples pass? If the skill passes 1 out of 3 samples, it demonstrates the behavior is reachable. Tuning can improve consistency.

Capability evals are exploratory. You expect some failures. A 60% pass rate on a new skill isn't a crisis — it's a baseline to improve from.

```bash
# Exploring: does the skill handle multi-file reviews?
skillet eval conventional-comments ~/.claude/skills/conventional-comments
```

## Regression evals

A regression eval asks: **does the skill still work?**

You run these after the skill is stable, typically in CI. The metric that matters is **pass^k** — did *all* k samples pass? A single failure in 3 samples means the skill is flaky on that scenario. For regression, flaky is broken.

Regression evals are conservative. You expect consistent success. A drop from 100% to 93% is a signal that something changed and needs attention.

```bash
# CI gate: fail the build if the skill regresses
skillet eval conventional-comments ~/.claude/skills/conventional-comments --samples 3
# Check exit code: 0 = all passed, 1 = failures
```

## Same evals, different lens

The YAML files are identical. The prompts, expected behaviors, and grading criteria don't change. What changes is:

| | Capability | Regression |
|---|---|---|
| **When** | During development | In CI / after changes |
| **Question** | Can it do this? | Does it still do this? |
| **Success metric** | pass@k (any sample) | pass^k (all samples) |
| **Failure response** | Tune the skill | Investigate the regression |
| **Tolerance** | Partial success is useful | Flakiness is a bug |

## The lifecycle

Evals naturally transition from capability to regression as a skill matures:

1. **Capture** a failure scenario with `/skillet:add`. It's a capability eval — you're defining what "good" looks like.
2. **Tune** until the skill handles it consistently. The eval is proving the skill *can* do it.
3. **Promote** the eval to your CI suite. Now it's a regression eval — it guards against future breakage.

You don't need to mark evals as one type or the other. The distinction is in how you use them, not how you store them. An eval that you run during `skillet tune` is a capability eval. The same eval, run in a CI pipeline with a nonzero exit code check, is a regression eval.
