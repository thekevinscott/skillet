# Capture a Gap

The user has just noticed that your previous response wasn't what they wanted. Help them capture this as a "gap" for skill development.

## Your Task

1. **Ask what they expected** — Ask the user what behavior or format they expected instead of what you produced.

2. **Infer a gap name** — Based on their description and the conversation context, suggest a short kebab-case name for this gap (e.g., `conventional-comments`, `browser-fallback`, `json-output`).

3. **Let them confirm or change** — Present the suggested name in brackets and ask them to confirm (enter) or type a different name.

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

User: "Should have started with **issue** (blocking):"

You: "Gap name: [code-review-format] (enter to confirm, or type a different name)"

User: "conventional-comments"

You: *saves to ~/.skillet/gaps/conventional-comments/001.yaml*
"Gap saved to ~/.skillet/gaps/conventional-comments/001.yaml

  ├─ Prompt: "Write a code review comment..."
  ├─ Actual: "This code has a vulnerability..."
  ├─ Expected: Starts with **issue** (blocking):

Use `/gaps` to view all gaps."

## Important

- Look at the conversation history to find the prompt and your response
- If this looks similar to an existing gap category, suggest that name
- Keep the YAML simple and human-readable
- Create the ~/.skillet/gaps directory if it doesn't exist
