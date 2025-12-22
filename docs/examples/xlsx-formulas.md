---
title: "Excel Formulas"
---

<script setup>
import { ref, onMounted } from 'vue'
</script>

# Excel Formulas

Teaching Claude to create dynamic spreadsheets instead of static tables.

::: tip Example Walkthrough
This page demonstrates [Anthropic's 5-step process for building effective skills](https://www.anthropic.com/engineering/claude-code-best-practices) using Excel formula generation as a concrete example. Follow along in the terminal on the right!
:::

<div class="tutorial-layout">
<div class="tutorial-content">

## The Problem

Claude can generate Excel files using `openpyxl`. But without guidance, it takes shortcuts:

- **Hardcodes values** instead of using formulas
- Creates spreadsheets that **don't update** when inputs change
- Misses financial modeling conventions (color coding, formatting)
- Produces formula errors (`#REF!`, `#DIV/0!`)

The spreadsheet *looks* right but doesn't *work* like one.

When you ask Claude to create a revenue spreadsheet, it writes:

```python
sheet['D2'] = 5000      # Hardcoded!
```

Instead of:

```python
sheet['D2'] = '=B2*C2'  # Formula!
```

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

Now we **capture** this failure as an evaluation using the Skillet workflow.

Try it yourself - run this in the terminal:

```bash
/skillet:add
```

Skillet asks three questions:

1. **What prompt** triggered this behavior?
2. **What went wrong** with the response?
3. **What should have happened** instead?

This creates an eval file like:

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

Create a skill file with **just enough** guidance to fix the failures.

The skill is minimal—we're not writing a textbook. Just the critical rules:

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

---

## Step 5: Iterate

Run the evaluations again—now *with* the skill:

```bash
skillet eval xlsx-formulas
```

**Result: 100% (4/4)**

The journey: **25% → 100%**

The evals are your proof. Re-run them anytime to verify the skill still works.

</div>
<div class="tutorial-terminal">

<skillet-terminal height="100%"></skillet-terminal>

</div>
</div>

<style>
.tutorial-layout {
  display: flex;
  gap: 2rem;
  margin-top: 1.5rem;
}

.tutorial-content {
  flex: 1;
  min-width: 0;
}

.tutorial-terminal {
  width: 45%;
  position: sticky;
  top: 80px;
  height: calc(100vh - 120px);
  max-height: 700px;
}

.tutorial-content hr {
  margin: 2.5rem 0;
  border: none;
  border-top: 1px solid var(--vp-c-divider);
}

.tutorial-content h2 {
  border-top: none;
  padding-top: 0;
  margin-top: 0;
}

@media (max-width: 960px) {
  .tutorial-layout {
    flex-direction: column;
  }
  .tutorial-terminal {
    width: 100%;
    position: static;
    height: 400px;
  }
}
</style>
