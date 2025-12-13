# Add an Eval

The user has just noticed that your previous response wasn't what they wanted. Help them add this as an eval for skill development.

## Your Task

1. **Ask what they expected** — Ask the user what behavior or format they expected instead of what you produced.

2. **Check existing evals** — List directories in `{{SKILLET_DIR}}/evals/` to see what eval categories already exist.

3. **Suggest eval name options** — Use `AskUserQuestion` to present exactly 3 options:
   - If an existing eval seems related to this issue, suggest it first with "(existing, N evals)"
   - Include 1-2 new name suggestions based on the user's description
   - The user can always type a custom name via "Other"

4. **Save the eval** — Write a YAML file to `{{SKILLET_DIR}}/evals/<name>/<number>.yaml` containing:
   - `timestamp`: Current ISO timestamp
   - `prompt`: The user's original prompt (from conversation context)
   - `actual`: Your response (summarized if long)
   - `expected`: What the user said they wanted
   - `name`: The eval name

5. **Confirm** — Tell the user the eval was saved and how many evals exist for this name.

## Example Interaction

User runs `/add`

You: "What behavior or format did you expect?"

User: "Should have automatically used Playwright when WebFetch failed"

You: *checks {{SKILLET_DIR}}/evals/ and finds browser-fallback/ with 2 evals*
*uses AskUserQuestion with options:*
- "browser-fallback (existing, 2 evals)" — Add to existing eval category
- "webfetch-retry" — New category for fetch retry behavior
- "auto-playwright" — New category for automatic Playwright usage

User selects: "browser-fallback (existing, 2 evals)"

You: *saves to {{SKILLET_DIR}}/evals/browser-fallback/003.yaml*
"Eval saved to {{SKILLET_DIR}}/evals/browser-fallback/003.yaml

  ├─ Prompt: "Read https://reddit.com/..."
  ├─ Actual: Asked user what to do
  ├─ Expected: Automatically use Playwright

You now have 3 evals for this skill."

## Important

- Look at the conversation history to find the prompt and your response
- Always check existing evals first — grouping related evals is valuable
- Keep the YAML simple and human-readable
- Create the {{SKILLET_DIR}}/evals directory if it doesn't exist
