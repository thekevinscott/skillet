# Use Case: Excel Formulas (xlsx)

Teaching Claude to create Excel spreadsheets with proper formulas instead of hardcoded values.

This walkthrough follows Anthropic's [five-step evaluation-driven development process](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration).

---

## Layout Notes

**Two-column Stripe-style layout:**
- Left: Scrollable prose (this content)
- Right: Sticky terminal running Claude Code with local LLM

Each `---` section has its own right-hand terminal state. As user scrolls, the right side shows the relevant demo for that section.

**Approach: Constrained prompts (video game design)**

The local LLM is live - real tokens, real execution - but we guide it with carefully crafted prompts that reliably produce the output we need. Like a video game with invisible walls: the user feels free, but we're steering them toward the destination.

**How it works:**

1. Each section has a "scene" with:
   - A prompt we send to the LLM (user doesn't see this scaffolding)
   - Expected behavior patterns (not exact text, but "should use hardcoded values")
   - Fallback handling if LLM goes off-script

2. The prompts are designed to constrain output:
   ```
   # Scene: The Problem (intentionally bad output)

   System: You are demonstrating common mistakes when creating Excel files.
   For this example, use hardcoded values instead of formulas.
   Write simple, readable code that a beginner would write.
   Do NOT use formulas like =SUM() or =A1*B1.

   User: Create an Excel file that calculates monthly revenue...
   ```

3. Variation is okay - even good! Each run is slightly different, which:
   - Proves it's live (not a recording)
   - Shows the LLM's actual behavior
   - Makes repeat visits interesting

4. We detect success/failure patterns, not exact strings:
   - Did the code contain `=` in cell assignments? → formulas used
   - Did it hardcode numbers? → the "bad" behavior we wanted
   - Either way, the narrative adapts

**The magic:** User watches a REAL LLM make REAL mistakes, then sees Skillet fix them. It's not a demo - it's proof.

---

## The Problem

Claude can generate Excel files using openpyxl:

```
┌─────────────────────────────────────────────────────────────┐
│ RIGHT SIDE: Live Claude Code terminal                       │
│                                                             │
│ TRIGGER: User scrolls to this section                       │
│ ACTION: Terminal shows prompt being entered:                │
│                                                             │
│   > Create an Excel file that calculates monthly revenue.   │
│     January: 100 units at $50. February: 120 at $52.        │
│     Include a total row.                                    │
│                                                             │
│ Then Claude (local LLM) responds, writes Python code,       │
│ creates the xlsx file.                                      │
│                                                             │
│ KEY: The LLM should produce BAD output here (hardcoded      │
│ values) to demonstrate the problem. This is the "before".   │
└─────────────────────────────────────────────────────────────┘
```

Without guidance, it often:
- Hardcodes calculated values instead of using formulas
- Creates spreadsheets that don't update when source data changes
- Misses financial modeling conventions (color coding, formatting)
- Produces formula errors (#REF!, #DIV/0!, etc.)

The terminal shows this happening live. The user watches the LLM write code like `sheet['C2'] = 5000` instead of `sheet['C2'] = '=A2*B2'`. They see the problem firsthand.

We can develop _evaluations_ that identify and codify these gaps in functionality, and write a skill that scores highly on those evaluations.

We'll follow Anthropic's process step by step.

---

## Step 1: Identify Gaps

```
┌─────────────────────────────────────────────────────────────┐
│ RIGHT SIDE: Terminal continues from above                   │
│                                                             │
│ TRIGGER: User scrolls to Step 1                             │
│ ACTION: Terminal scrolls to show the code Claude wrote:     │
│                                                             │
│   # Claude's code (highlighted as problematic)              │
│   sheet['C2'] = 5000    # ← RED HIGHLIGHT                   │
│   sheet['C3'] = 6240    # ← RED HIGHLIGHT                   │
│   sheet['C4'] = 11240   # ← RED HIGHLIGHT                   │
│                                                             │
│ Maybe: side-by-side with what it SHOULD be:                 │
│   sheet['C2'] = '=A2*B2'     # ← GREEN                      │
│   sheet['C3'] = '=A3*B3'     # ← GREEN                      │
│   sheet['C4'] = '=SUM(C2:C3)' # ← GREEN                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Ask Claude to create a spreadsheet without any skill:

```
"Create an Excel file that calculates monthly revenue.
January sales: 100 units at $50 each.
February sales: 120 units at $52 each.
Include a total row."
```

**Observed failures:**

```python
# What Claude often does (WRONG):
sheet['C2'] = 5000    # Hardcoded! Should be =A2*B2
sheet['C3'] = 6240    # Hardcoded! Should be =A3*B3
sheet['C4'] = 11240   # Hardcoded! Should be =SUM(C2:C3)
```

The spreadsheet looks correct, but:
- Change January units from 100 → 150, and revenue still shows $5,000
- The "total" doesn't actually sum anything
- It's not a spreadsheet, it's a picture of a spreadsheet

Other failures:
- No formula recalculation step (values show as 0 until opened in Excel)
- Formula errors like `#REF!` when referencing wrong cells
- Inconsistent formatting (some numbers with commas, some without)

---

## Step 2: Create Evaluations

```
┌─────────────────────────────────────────────────────────────┐
│ RIGHT SIDE: Terminal - capturing an eval                    │
│                                                             │
│ TRIGGER: User scrolls to Step 2                             │
│ ACTION: Show the /skillet:add workflow:                     │
│                                                             │
│   > /skillet:add                                            │
│                                                             │
│   What prompt triggered this behavior?                      │
│   > Create an Excel file that calculates monthly revenue... │
│                                                             │
│   What was wrong with Claude's response?                    │
│   > Used hardcoded values instead of formulas               │
│                                                             │
│   What should have happened?                                │
│   > Revenue cells should contain formulas like =A2*B2       │
│                                                             │
│   ✓ Created evals/xlsx-formulas/001-uses-formulas.yaml      │
│                                                             │
│ The user watches an eval get created in real-time.          │
│ This is the core "capture" workflow of Skillet.             │
└─────────────────────────────────────────────────────────────┘
```

Capture these failures as evals:

```yaml
# evals/xlsx-formulas/001-uses-formulas.yaml
prompt: |
  Create an Excel file with Q1 sales data:
  - January: 100 units at $50
  - February: 120 units at $55
  - March: 90 units at $48
  Include a Revenue column (units × price) and a Total row.
expected: |
  Uses Excel formulas for calculations, not hardcoded values.
  Revenue cells contain formulas like =A2*B2
  Total cell contains =SUM() formula
```

```yaml
# evals/xlsx-formulas/002-recalculates.yaml
prompt: |
  Create a budget spreadsheet with:
  - Income: $5000
  - Expenses: Rent $1500, Food $400, Transport $200
  - Calculate total expenses and remaining balance
expected: |
  Runs recalc.py or equivalent to ensure formulas are evaluated.
  Opening the file shows calculated values, not zeros.
```

```yaml
# evals/xlsx-formulas/003-no-errors.yaml
prompt: |
  Create a spreadsheet that calculates year-over-year growth:
  - 2023 Revenue: $1,000,000
  - 2024 Revenue: $1,250,000
  Include the growth percentage.
expected: |
  No formula errors (#REF!, #DIV/0!, #VALUE!, etc.)
  Growth formula correctly references cells: =(B2-B1)/B1
```

```yaml
# evals/xlsx-formulas/004-formatting.yaml
prompt: |
  Create a financial model with:
  - Revenue assumptions (editable inputs)
  - Calculated projections
  - 5-year forecast
expected: |
  Follows financial modeling conventions:
  - Input cells colored blue
  - Formula cells colored black
  - Currency formatting with proper symbols
  - Percentages formatted as 0.0%
```

---

## Step 3: Establish Baseline

```
┌─────────────────────────────────────────────────────────────┐
│ RIGHT SIDE: Terminal - running baseline eval                │
│                                                             │
│ TRIGGER: User scrolls to Step 3                             │
│ ACTION: Run skillet eval, show results streaming in:        │
│                                                             │
│   > skillet eval xlsx-formulas                              │
│                                                             │
│   Running 4 evaluations...                                  │
│                                                             │
│   001-uses-formulas     ❌ FAIL                             │
│     Expected: formulas like =A2*B2                          │
│     Got: hardcoded value 5000                               │
│                                                             │
│   002-recalculates      ✓ PASS                              │
│                                                             │
│   003-no-errors         ❌ FAIL                             │
│     Found: #REF! error in cell E2                           │
│                                                             │
│   004-formatting        ❌ FAIL                             │
│     Expected: blue input cells                              │
│     Got: no color coding                                    │
│                                                             │
│   Results: 1/4 passing (25%)                                │
│                                                             │
│ This is the BASELINE. Without a skill, Claude scores 25%.   │
│ Now we know exactly where the gaps are.                     │
└─────────────────────────────────────────────────────────────┘
```

```bash
skillet eval xlsx-formulas
```

Without a skill, expect maybe 1/4 passing. Claude knows formulas exist but defaults to the easier path of hardcoding values.

```
Results: 1/4 passing (25%)

❌ 001-uses-formulas: Used hardcoded values
✓ 002-recalculates: (lucky - simple case)
❌ 003-no-errors: #REF! error in growth formula
❌ 004-formatting: No color coding, inconsistent formats
```

---

## Step 4: Write Minimal Instructions

```
┌─────────────────────────────────────────────────────────────┐
│ RIGHT SIDE: Split view - editor + terminal                  │
│                                                             │
│ TRIGGER: User scrolls to Step 4                             │
│ ACTION: Show skill file being created/edited:               │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ skills/xlsx-formulas/SKILL.md                           │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ---                                                     │ │
│ │ name: xlsx-formulas                                     │ │
│ │ description: Create Excel spreadsheets with proper...   │ │
│ │ ---                                                     │ │
│ │                                                         │ │
│ │ # Excel with Formulas                                   │ │
│ │                                                         │ │
│ │ When creating Excel files, **always use formulas**...   │ │
│ │                                                         │ │
│ │ ❌ WRONG:  sheet['B10'] = 5000                          │ │
│ │ ✅ RIGHT:  sheet['B10'] = '=SUM(B2:B9)'                 │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Could show: Claude writing the skill via /skillet:tune,     │
│ or the user could watch a pre-written skill appear with     │
│ typewriter effect. The point is: this is MINIMAL - just     │
│ enough instruction to fix the failures we identified.       │
└─────────────────────────────────────────────────────────────┘
```

Create `skills/xlsx-formulas/SKILL.md`:

```markdown
---
name: xlsx-formulas
description: Create Excel spreadsheets with proper formulas. Triggers on: spreadsheet, Excel, xlsx, financial model, budget, calculations.
---

# Excel with Formulas

When creating Excel files, **always use formulas for calculated values**.

## Critical Rule

❌ WRONG - Hardcoding:
```python
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000
```

✅ CORRECT - Formula:
```python
sheet['B10'] = '=SUM(B2:B9)'
```

## Why This Matters

Spreadsheets must be dynamic. When inputs change, outputs should recalculate automatically. Hardcoded values break this.

## Workflow

1. Create spreadsheet with openpyxl
2. Use formulas for ALL calculations
3. Run `python recalc.py output.xlsx` to evaluate formulas
4. Verify no errors in output

## Common Formulas

```python
sheet['C2'] = '=A2*B2'           # Multiply
sheet['C10'] = '=SUM(C2:C9)'     # Sum range
sheet['D2'] = '=C2/C$10'         # Percentage (absolute ref)
sheet['E2'] = '=(B2-B1)/B1'      # Growth rate
sheet['F2'] = '=IF(A2>0,B2/A2,0)' # Avoid #DIV/0!
```

## Formatting Conventions

- **Blue text (RGB 0,0,255)**: Input values (editable assumptions)
- **Black text**: Formulas and calculations
- Currency: `$#,##0` with units in headers
- Percentages: `0.0%`
- Use parentheses for negatives: `(123)` not `-123`
```

---

## Step 5: Iterate

```
┌─────────────────────────────────────────────────────────────┐
│ RIGHT SIDE: Terminal - the payoff                           │
│                                                             │
│ TRIGGER: User scrolls to Step 5                             │
│ ACTION: Re-run evals, show improvement:                     │
│                                                             │
│   > skillet eval xlsx-formulas                              │
│                                                             │
│   Running 4 evaluations...                                  │
│                                                             │
│   001-uses-formulas     ✓ PASS  (was: ❌)                   │
│   002-recalculates      ✓ PASS                              │
│   003-no-errors         ✓ PASS  (was: ❌)                   │
│   004-formatting        ❌ FAIL                             │
│                                                             │
│   Results: 3/4 passing (75%)  ↑ from 25%                    │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ [After adding color coding guidance to skill]               │
│                                                             │
│   > skillet eval xlsx-formulas                              │
│                                                             │
│   001-uses-formulas     ✓ PASS                              │
│   002-recalculates      ✓ PASS                              │
│   003-no-errors         ✓ PASS                              │
│   004-formatting        ✓ PASS  (was: ❌)                   │
│                                                             │
│   Results: 4/4 passing (100%) 🎉                            │
│                                                             │
│ THIS IS THE MOMENT. The user sees measurable improvement.   │
│ 25% → 75% → 100%. The skill WORKS. Evals PROVE it.          │
└─────────────────────────────────────────────────────────────┘
```

```bash
skillet eval xlsx-formulas
```

First run with skill:

```
Results: 3/4 passing (75%)

✓ 001-uses-formulas: Formulas used correctly
✓ 002-recalculates: recalc.py called
✓ 003-no-errors: No formula errors
❌ 004-formatting: Missing color coding
```

The formatting test still fails. Add more specific guidance:

```markdown
## Color Coding (add to SKILL.md)

```python
from openpyxl.styles import Font

# Input cells - blue
sheet['B2'].font = Font(color='0000FF')

# Formula cells - black (default, but be explicit)
sheet['C2'].font = Font(color='000000')
```
```

Run again:

```bash
skillet eval xlsx-formulas
```

```
Results: 4/4 passing (100%)

✓ 001-uses-formulas
✓ 002-recalculates
✓ 003-no-errors
✓ 004-formatting
```

---

## The Contrast

```
┌─────────────────────────────────────────────────────────────┐
│ RIGHT SIDE: Side-by-side comparison                         │
│                                                             │
│ TRIGGER: User scrolls to "The Contrast"                     │
│ ACTION: Show before/after split screen:                     │
│                                                             │
│ ┌───────────────────────┬───────────────────────────────┐   │
│ │ WITHOUT SKILLET       │ WITH SKILLET                  │   │
│ ├───────────────────────┼───────────────────────────────┤   │
│ │                       │                               │   │
│ │ 1. Ask Claude         │ 1. Capture failure as eval    │   │
│ │ 2. Check output       │ 2. Run baseline (25%)         │   │
│ │ 3. "Please use        │ 3. Write minimal skill        │   │
│ │    formulas"          │ 4. Re-run (100%) ✓            │   │
│ │ 4. Check again...     │                               │   │
│ │ 5. "Still wrong"      │ DONE. Evals prove it works.   │   │
│ │ 6. Repeat forever     │ Re-run anytime to verify.     │   │
│ │                       │                               │   │
│ │ ❓ "Does it work now?" │ ✓ "Yes, 4/4 passing"         │   │
│ └───────────────────────┴───────────────────────────────┘   │
│                                                             │
│ Maybe animated: left side shows frustrating loop,           │
│ right side shows clean progression with checkmarks.         │
└─────────────────────────────────────────────────────────────┘
```

### Without Skillet

1. Ask Claude to make a spreadsheet
2. Get a file with hardcoded values
3. Manually check if formulas were used
4. Ask Claude to fix it
5. Check again... did it actually fix it?
6. Repeat until frustrated

No systematic way to know if Claude "gets it" now.

### With Skillet

1. Capture the failures as evals
2. See baseline: 25% passing
3. Write minimal skill
4. See improvement: 75% → 100%
5. **Know it works** because you can re-run evals anytime

The evals are your proof. When you update the skill later, you'll know immediately if you broke something.

---

## Real-World Value

This skill matters because:

- **Finance teams** need spreadsheets that actually work as spreadsheets
- **Reports** should update when source data changes
- **Auditors** expect to see formulas, not magic numbers
- **Collaboration** requires others to understand and modify the model

A spreadsheet with hardcoded values is just a fancy table. A spreadsheet with formulas is a living model.
