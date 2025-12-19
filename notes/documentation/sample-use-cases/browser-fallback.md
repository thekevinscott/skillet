# Use Case: Browser Fallback (Playwright)

Teaching Claude to use `npx playwright` when it needs to interact with web pages.

This walkthrough follows Anthropic's [five-step evaluation-driven development process](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration).

---

## Step 1: Identify Gaps

Run Claude on browser-related tasks without any skill:

```
"Go to example.com and tell me what the main heading says"
"Take a screenshot of the login page at myapp.com"
"Fill out the contact form at site.com/contact"
```

**Observed failures:**
- Claude attempts to use `curl` or `wget` which can't render JavaScript
- Claude says it can't interact with browsers
- Claude suggests the user do it manually

---

## Step 2: Create Evaluations

Use `skillet add` to capture these as eval files:

```yaml
# evals/browser-fallback/001-read-heading.yaml
prompt: "Go to example.com and tell me what the main heading says"
expected: "Uses npx playwright to navigate and extract heading text"
```

```yaml
# evals/browser-fallback/002-screenshot.yaml
prompt: "Take a screenshot of https://example.com"
expected: "Uses playwright screenshot command, saves file"
```

```yaml
# evals/browser-fallback/003-form-interaction.yaml
prompt: "Click the 'Learn More' button on example.com"
expected: "Uses playwright to locate and click the element"
```

---

## Step 3: Establish Baseline

```bash
skillet eval browser-fallback
```

Without a skill, expect 0/3 or 1/3 passing (Claude might luck into a solution occasionally).

---

## Step 4: Write Minimal Instructions

Create `skills/browser-fallback/SKILL.md`:

```markdown
---
name: browser-fallback
description: Use npx playwright for browser automation when curl/wget won't work. Triggers on: screenshots, form filling, JavaScript-rendered content, clicking elements.
---

# Browser Fallback

When you need to interact with a webpage (not just fetch HTML), use playwright:

## Common patterns

Screenshot:
```bash
npx playwright screenshot https://example.com output.png
```

Extract text from JS-rendered page:
```bash
npx playwright evaluate https://example.com "document.body.innerText"
```

Click and interact:
```bash
npx playwright open https://example.com
# Then use page.click(), page.fill(), etc.
```
```

---

## Step 5: Iterate

```bash
skillet eval browser-fallback
```

Check results. If 2/3 pass but form interaction fails, examine why and refine the skill. Maybe add an example of `page.fill()` usage.
