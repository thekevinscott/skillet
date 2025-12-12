# Capture a Gap

The user has just noticed that your previous response wasn't what they wanted. Help them capture this as a "gap" for skill development.

## Your Task

1. **Ask what they expected** — Ask the user what behavior or format they expected instead of what you produced.

2. **Check existing gaps** — List directories in `~/.skillet/gaps/` to see what gap categories already exist.

3. **Suggest gap name options** — Use `AskUserQuestion` to present exactly 3 options:
   - If an existing gap seems related to this issue, suggest it first with "(existing, N gaps)"
   - Include 1-2 new name suggestions based on the user's description
   - The user can always type a custom name via "Other"

4. **Save the gap** — Write a YAML file to `~/.skillet/gaps/<name>/<number>.yaml` containing:
   - `timestamp`: Current ISO timestamp
   - `prompt`: The user's original prompt (from conversation context)
   - `actual`: Your response (summarized if long)
   - `expected`: What the user said they wanted
   - `name`: The gap name

5. **Confirm** — Tell the user the gap was saved and how many gaps exist for this name.

## Example Interaction

User runs `/gap`

You: "What behavior or format did you expect?"

User: "Should have automatically used Playwright when WebFetch failed"

You: *checks ~/.skillet/gaps/ and finds browser-fallback/ with 2 gaps*
*uses AskUserQuestion with options:*
- "browser-fallback (existing, 2 gaps)" — Add to existing gap category
- "webfetch-retry" — New category for fetch retry behavior
- "auto-playwright" — New category for automatic Playwright usage

User selects: "browser-fallback (existing, 2 gaps)"

You: *saves to ~/.skillet/gaps/browser-fallback/003.yaml*
"Gap saved to ~/.skillet/gaps/browser-fallback/003.yaml

  ├─ Prompt: "Read https://reddit.com/..."
  ├─ Actual: Asked user what to do
  ├─ Expected: Automatically use Playwright

You now have 3 examples of this gap."

## Important

- Look at the conversation history to find the prompt and your response
- Always check existing gaps first — grouping related gaps is valuable
- Keep the YAML simple and human-readable
- Create the ~/.skillet/gaps directory if it doesn't exist
