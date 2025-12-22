---
title: "Excel Formulas"
---

# Excel Formulas

Teaching Claude to create dynamic spreadsheets instead of static tables.

::: tip Example Walkthrough
This page demonstrates [Anthropic's 5-step process for building effective skills](https://www.anthropic.com/engineering/claude-code-best-practices) using Excel formula generation as a concrete example.
:::

## The Problem

<div class="columns">
<div class="left">

Claude can generate Excel files using `openpyxl`. But without guidance, it takes shortcuts:

- **Hardcodes values** instead of using formulas
- Creates spreadsheets that **don't update** when inputs change
- Misses financial modeling conventions (color coding, formatting)
- Produces formula errors (`#REF!`, `#DIV/0!`)

The spreadsheet *looks* right but doesn't *work* like one.

</div>
<div class="right">

<skillet-terminal height="200px"></skillet-terminal>

</div>
</div>

## Step 1: Identify Gaps

<div class="columns">
<div class="left">

First, we ask Claude to create a spreadsheet and observe what goes wrong:

> "Create an Excel file that calculates monthly revenue.
> January: 100 units at $50 each.
> February: 120 units at $52 each.
> Include a total row."

Claude's response hardcodes the calculated values where formulas should be. This is the **gap** we want to fix.

</div>
<div class="right">

<skillet-terminal height="300px"></skillet-terminal>

</div>
</div>

## Step 2: Create Evaluations

<div class="columns">
<div class="left">

Now we **capture** this failure as an evaluation using the Skillet workflow:

```
/skillet:add
```

Skillet asks three questions:

1. **What prompt** triggered this behavior?
2. **What went wrong** with the response?
3. **What should have happened** instead?

</div>
<div class="right">

<skillet-terminal height="280px"></skillet-terminal>

</div>
</div>

## Step 3: Establish Baseline

<div class="columns">
<div class="left">

Run the evaluations *without* a skill to see how Claude performs by default:

```bash
skillet eval xlsx-formulas
```

**Result: 25% (1/4)**

This is our baseline. Claude knows formulas exist but doesn't use them consistently.

</div>
<div class="right">

<skillet-terminal height="280px"></skillet-terminal>

</div>
</div>

## Step 4: Write Minimal Instructions

<div class="columns">
<div class="left">

Create a skill file with **just enough** guidance to fix the failures:

The skill is minimal—we're not writing a textbook. Just the critical rules.

</div>
<div class="right">

<skillet-terminal height="300px"></skillet-terminal>

</div>
</div>

## Step 5: Iterate

<div class="columns">
<div class="left">

Run the evaluations again—now *with* the skill:

```bash
skillet eval xlsx-formulas
```

**Result: 100% (4/4)**

The journey: **25% → 100%**

The evals are your proof. Re-run them anytime to verify the skill still works.

</div>
<div class="right">

<skillet-terminal height="280px"></skillet-terminal>

</div>
</div>
