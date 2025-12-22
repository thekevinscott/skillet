---
title: "Excel Formulas"
---

# Excel Formulas

Teaching Claude to create dynamic spreadsheets instead of static tables.

::: tip Example Walkthrough
This page demonstrates [Anthropic's 5-step process for building effective skills](https://www.anthropic.com/engineering/claude-code-best-practices) using Excel formula generation as a concrete example.
:::

<Columns>
<template #left>

## The Problem

Claude can generate Excel files using `openpyxl`. But without guidance, it takes shortcuts:

- **Hardcodes values** instead of using formulas
- Creates spreadsheets that **don't update** when inputs change
- Misses financial modeling conventions (color coding, formatting)
- Produces formula errors (`#REF!`, `#DIV/0!`)

The spreadsheet *looks* right but doesn't *work* like one.

</template>
<template #right>

```python
# What Claude writes:
sheet['D2'] = 5000      # Hardcoded!

# What it should write:
sheet['D2'] = '=B2*C2'  # Formula!
```

</template>
</Columns>

<Columns>
<template #left>

## Step 1: Identify Gaps

First, we ask Claude to create a spreadsheet and observe what goes wrong:

> "Create an Excel file that calculates monthly revenue.
> January: 100 units at $50 each.
> February: 120 units at $52 each.
> Include a total row."

Claude's response hardcodes the calculated values where formulas should be. This is the **gap** we want to fix.

</template>
<template #right>

```python
# Claude's output:
sheet['A1'] = 'Month'
sheet['B1'] = 'Units'
sheet['C1'] = 'Price'
sheet['D1'] = 'Revenue'
sheet['A2'] = 'January'
sheet['B2'] = 100
sheet['C2'] = 50
sheet['D2'] = 5000      # ⚠️ Hardcoded!
sheet['A3'] = 'February'
sheet['B3'] = 120
sheet['C3'] = 52
sheet['D3'] = 6240      # ⚠️ Hardcoded!
sheet['D4'] = 11240     # ⚠️ Hardcoded!
```

</template>
</Columns>

<Columns>
<template #left>

## Step 2: Create Evaluations

Now we **capture** this failure as an evaluation using the Skillet workflow:

```
/skillet:add
```

Skillet asks three questions:

1. **What prompt** triggered this behavior?
2. **What went wrong** with the response?
3. **What should have happened** instead?

</template>
<template #right>

```yaml
# evals/xlsx-formulas/001-uses-formulas.yaml
prompt: |
  Create an Excel file with Q1 sales data.
  Calculate revenue from units and prices.

expected: |
  Uses Excel formulas for calculations.
  Revenue cells contain =A2*B2 style formulas.
  Total cell contains =SUM() formula.
```

</template>
</Columns>

<Columns>
<template #left>

## Step 3: Establish Baseline

Run the evaluations *without* a skill to see how Claude performs by default:

```bash
skillet eval xlsx-formulas
```

**Result: 25% (1/4)**

This is our baseline. Claude knows formulas exist but doesn't use them consistently.

</template>
<template #right>

```
$ skillet eval xlsx-formulas

Running 4 evaluations...

✗ 001-uses-formulas
✗ 002-sum-formula
✗ 003-percentage-formula
✓ 004-basic-structure

Results: 1/4 (25%)
```

</template>
</Columns>

<Columns>
<template #left>

## Step 4: Write Minimal Instructions

Create a skill file with **just enough** guidance to fix the failures:

The skill is minimal—we're not writing a textbook. Just the critical rules.

</template>
<template #right>

```markdown
# skills/xlsx-formulas/SKILL.md

**Always use formulas for calculations.**

## Critical Rule

❌ WRONG: sheet['B10'] = 5000
✅ RIGHT: sheet['B10'] = '=SUM(B2:B9)'

## Common Formulas

- '=A2*B2'        # Multiply
- '=SUM(C2:C9)'   # Sum range
- '=(B2-B1)/B1'   # Growth rate
```

</template>
</Columns>

<Columns>
<template #left>

## Step 5: Iterate

Run the evaluations again—now *with* the skill:

```bash
skillet eval xlsx-formulas
```

**Result: 100% (4/4)**

The journey: **25% → 100%**

The evals are your proof. Re-run them anytime to verify the skill still works.

</template>
<template #right>

```
$ skillet eval xlsx-formulas

Running 4 evaluations...

✓ 001-uses-formulas
✓ 002-sum-formula
✓ 003-percentage-formula
✓ 004-basic-structure

Results: 4/4 (100%)
```

</template>
</Columns>
