# Skill Labeler

Annotation tool for labeling SKILL.md files with anatomy tags.

## Architecture

- **Frontend**: Vite + TypeScript + Tiptap v3 (vanilla JS, no React)
- **API server**: Express on port 2721 (proxied through Vite on `/api`)
- **Data**: SQLite — reads from `../data/analyzed/content.db`, labels stored in `../data/analyzed/labels.db`

## Dev Setup

```bash
cd research/skill-collection/labeler
pnpm install
node server.js &          # API on port 2721
pnpm dev                  # Vite dev server on port 2720 with HMR
```

Accessible via Tailscale: `http://tower.tail790bbc.ts.net:2720`

## Key Files

- `index.html` — Vite entry point
- `src/main.ts` — Tiptap editor, API calls, navigation
- `src/style.css` — Styles
- `server.js` — Express API server (reads content.db, serves skills)
- `vite.config.js` — Vite config with `/api` proxy to port 2721

## Tiptap Details

- **SkillBlock**: Custom Node — `content: "text*"`, `marks: "_"`, `whitespace: "pre"`, `code: true`. Renders as `<pre>`, preserves whitespace, allows marks.
- **PM_OFFSET = 1**: ProseMirror position = raw text offset + 1 (cost of entering the skillBlock node)
- **BubbleMenu**: Tiptap extension for selection-based UI. Appears on text selection, hides when selection collapses.
- **Read-only**: `editable: true` but all input events blocked via `editorProps` (handleKeyDown, handleTextInput, handleDrop, handlePaste). Allows selection tracking without content editing.

## Testing Interactions

Use Playwright scripts in `/tmp` to test interactive behavior:

```bash
node /tmp/test-labeler.mjs
```

Scripts should use `page.evaluate()` to inspect DOM state and `page.mouse.click()` with `clickCount: 3` for line selection. Static screenshots can't capture selection-dependent UI.

## Running Processes

- Don't kill servers running in `--watch` mode; file changes trigger automatic restarts
- Vite dev server handles HMR — no need to rebuild for frontend changes
- API server on 2721, Vite on 2720
