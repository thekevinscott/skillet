---
title: "Excel Formulas"
---

# Excel Formulas

Teaching Claude to create dynamic spreadsheets instead of static tables.

::: tip Example Walkthrough
This page demonstrates [Anthropic's 5-step process for building effective skills](https://www.anthropic.com/engineering/claude-code-best-practices) using Excel formula generation as a concrete example.
:::

## The Problem

Claude can generate Excel files using `openpyxl`. But without guidance, it takes shortcuts:

- **Hardcodes values** instead of using formulas
- Creates spreadsheets that **don't update** when inputs change
- Misses financial modeling conventions (color coding, formatting)
- Produces formula errors (`#REF!`, `#DIV/0!`)

When you ask Claude to create a revenue spreadsheet, it writes:

```python
sheet['D2'] = 5000      # Hardcoded!
```

Instead of:

```python
sheet['D2'] = '=B2*C2'  # Formula!
```

The spreadsheet *looks* right but doesn't *work* like one.

---

## Step 1: Identify Gaps

First, we ask Claude to create a spreadsheet and observe what goes wrong:

> "Create an Excel file that calculates monthly revenue.
> January: 100 units at $50 each.
> February: 120 units at $52 each.
> Include a total row."

Claude's response hardcodes the calculated values where formulas should be. This is the **gap** we want to fix.

---

## Step 2: Create Evaluations

Now we **capture** this failure as an evaluation using the Skillet workflow:

```
/skillet:add
```

Skillet asks three questions:

1. **What prompt** triggered this behavior?
2. **What went wrong** with the response?
3. **What should have happened** instead?

The result is a YAML file that codifies our expectations:

```yaml
prompt: |
  Create an Excel file with Q1 sales data.
  Calculate revenue from units and prices.
expected: |
  Uses Excel formulas for calculations.
  Revenue cells contain =A2*B2 style formulas.
  Total cell contains =SUM() formula.
```

---

## Step 3: Establish Baseline

Run the evaluations *without* a skill to see how Claude performs by default:

```bash
skillet eval xlsx-formulas
```

**Result: 25% (1/4)**

This is our baseline. Claude knows formulas exist but doesn't use them consistently.

---

## Step 4: Write Minimal Instructions

Create a skill file with **just enough** guidance to fix the failures:

```markdown
# skills/xlsx-formulas/SKILL.md

**Always use formulas for calculations.**

## Critical Rule

❌ WRONG:
  sheet['B10'] = 5000

✅ CORRECT:
  sheet['B10'] = '=SUM(B2:B9)'

## Common Formulas

  '=A2*B2'        # Multiply
  '=SUM(C2:C9)'   # Sum range
  '=(B2-B1)/B1'   # Growth rate

## Formatting

• Blue text: Input values
• Black text: Formulas
```

---

## Step 5: Iterate

Run the evaluations again—now *with* the skill:

```bash
skillet eval xlsx-formulas
```

**Result: 100% (4/4)**

The journey: **25% → 100%**

The evals are your proof. Re-run them anytime to verify the skill still works. When you update the skill later, you'll know immediately if you broke something.
