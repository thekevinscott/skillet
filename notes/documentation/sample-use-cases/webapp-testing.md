# Use Case: Web App Testing (Playwright)

Teaching Claude to test web applications using Playwright instead of giving up or using inadequate tools.

This walkthrough follows Anthropic's [five-step evaluation-driven development process](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration).

---

## The Problem

When asked to interact with or test a web application, Claude often:
- Says it can't interact with browsers
- Attempts to use `curl` which can't handle JavaScript
- Suggests the user do it manually
- Doesn't know about `npx playwright` CLI commands

This is a missed opportunity because Playwright is available and powerful.

---

## Step 1: Identify Gaps

Ask Claude to test a web app without any skill:

```
"Go to my local dev server at localhost:3000 and verify the login form works"
"Take a screenshot of the homepage at example.com"
"Click the submit button on the contact form and tell me what happens"
```

**Observed failures:**

- "I cannot interact with web browsers directly..."
- Uses `curl http://localhost:3000` which returns raw HTML, missing JS-rendered content
- Suggests: "You'll need to open the browser yourself and..."

---

## Step 2: Create Evaluations

```yaml
# evals/webapp-testing/001-takes-screenshot.yaml
prompt: "Take a screenshot of https://example.com and save it as screenshot.png"
expected: |
  Uses playwright to take screenshot.
  Command like: npx playwright screenshot https://example.com screenshot.png
  Or writes a Python script using playwright.
```

```yaml
# evals/webapp-testing/002-extracts-text.yaml
prompt: "Go to https://example.com and tell me what the main heading says"
expected: |
  Uses playwright to navigate and extract text.
  Does NOT use curl or wget.
  Returns the actual heading text from the page.
```

```yaml
# evals/webapp-testing/003-handles-dynamic-content.yaml
prompt: |
  My React app is running at localhost:3000.
  Wait for it to fully load, then tell me how many items are in the list.
expected: |
  Uses playwright with proper wait conditions.
  Waits for networkidle or specific selectors.
  Does not assume content is immediately available.
```

```yaml
# evals/webapp-testing/004-interacts-with-forms.yaml
prompt: |
  Go to localhost:3000/login
  Fill in username "testuser" and password "testpass"
  Click the login button
  Tell me if login succeeded or failed
expected: |
  Uses playwright to fill form fields.
  Uses page.fill() or similar.
  Clicks the button and checks the result.
```

---

## Step 3: Establish Baseline

```bash
skillet eval webapp-testing
```

Expected baseline: 0-1/4 passing. Claude might occasionally use playwright if it's mentioned in context, but usually defaults to "I can't do that."

---

## Step 4: Write Minimal Instructions

Create `skills/webapp-testing/SKILL.md`:

```markdown
---
name: webapp-testing
description: Test web applications using Playwright. Triggers on: screenshot, browser, webpage, click, form, login, test site, localhost.
---

# Web App Testing with Playwright

When you need to interact with a webpage (not just fetch HTML), use Playwright.

## Quick Commands

Screenshot:
```bash
npx playwright screenshot https://example.com output.png
```

Extract text from JS-rendered page:
```bash
npx playwright evaluate https://example.com "document.querySelector('h1').textContent"
```

Open interactive browser:
```bash
npx playwright open https://example.com
```

## Python Script Pattern

For complex interactions, write a script:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000')
    page.wait_for_load_state('networkidle')  # Wait for JS!

    # Interact
    page.fill('#username', 'testuser')
    page.fill('#password', 'testpass')
    page.click('button[type="submit"]')

    # Verify
    page.wait_for_selector('.dashboard')
    print("Login succeeded!")

    browser.close()
```

## Critical: Wait for JavaScript

Dynamic apps need time to render. Always wait:

```python
page.wait_for_load_state('networkidle')  # Wait for network
page.wait_for_selector('.my-element')     # Wait for element
```

Never inspect the DOM immediately after goto() on dynamic apps.
```

---

## Step 5: Iterate

Run evals, refine skill based on failures, repeat until all pass.

---

## Why This Matters

- **E2E testing** is essential for modern web apps
- **Visual regression** testing catches UI bugs
- **Automation** saves hours of manual clicking
- **CI/CD integration** requires scriptable browser tests

Claude with this skill becomes a useful testing assistant instead of saying "I can't."
