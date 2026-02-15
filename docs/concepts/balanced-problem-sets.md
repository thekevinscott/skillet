# Balanced Problem Sets

A good eval suite tests both what a skill *should* do and what it *should not* do.

## The overtriggering problem

Most people start by writing positive cases: prompts where the skill should activate and produce specific output. This makes sense — you're building the skill because you want it to do something, so you test that it does it.

But positive-only eval suites have a blind spot. A skill that applies conventional comments formatting to *every* code review comment — including casual questions, clarifications, and acknowledgments — would score 100% on positive cases. It would also be unusable.

Without negative cases, you can't detect overtriggering. You only see that the skill does what you want. You never check whether it also does what you *don't* want.

## Positive and negative cases

**Positive cases** are prompts where the skill should activate:

```yaml
name: conventional-comments
prompt: "Review this function for potential issues: def get_user(id): ..."
expected: |
  Should use conventional comments format with a label
  like **suggestion**, **issue**, or **nitpick**.
```

**Negative cases** are prompts where the skill should *not* activate:

```yaml
name: conventional-comments
prompt: "What does this function do? def get_user(id): ..."
expected: |
  Should answer the question directly without using
  conventional comments format. This is an explanation
  request, not a code review.
```

The `domain: triggering` field is designed for exactly this — evals that test whether the skill activates in the right contexts. Use it for both positive triggering ("should activate here") and negative triggering ("should stay silent here").

## Writing good negative cases

Negative cases should be *plausible confusions*, not strawmen. A conventional comments skill won't be confused by "what's the weather?" — that's too far from its domain to be a useful test. Good negative cases are prompts that are *close* to the skill's domain but shouldn't trigger it:

- A question about code (not a review)
- A review of documentation (not code)
- A request to explain an existing review comment (not write a new one)
- A casual "looks good to me" acknowledgment

The closer the negative case is to the boundary, the more useful it is. Boundary cases are where overtriggering actually happens in practice.

## How many negative cases?

A reasonable starting point is **1 negative case for every 2-3 positive cases**. For a suite of 6 positive evals, add 2-3 negative evals. This ratio gives enough coverage to catch overtriggering without making the suite lopsided.

If tuning keeps improving positive pass rate but degrading negative cases, that's a signal the skill is overfitting — it's learning to always trigger rather than learning to trigger *correctly*. Rebalance by adding more negative cases at the boundary.
