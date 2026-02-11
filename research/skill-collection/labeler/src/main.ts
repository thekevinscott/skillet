import { Editor, Node, Extension, mergeAttributes } from "@tiptap/core";
import StarterKit from "@tiptap/starter-kit";
import { TextSelection, Plugin, PluginKey } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";
import "./style.css";

// Plugin: renders the current selection as inline decorations so the highlight
// persists even when browser focus moves to the tag input.
const selHighlightKey = new PluginKey("selHighlight");
const selHighlightPlugin = new Plugin({
  key: selHighlightKey,
  state: {
    init() {
      return DecorationSet.empty;
    },
    apply(tr, _old, _oldState, newState) {
      const { from, to } = newState.selection;
      if (from === to) return DecorationSet.empty;
      return DecorationSet.create(newState.doc, [
        Decoration.inline(from, to, { class: "sel-highlight" }),
      ]);
    },
  },
  props: {
    decorations(state) {
      return selHighlightPlugin.getState(state);
    },
  },
});

// Plugin: renders saved labels as persistent inline decorations.
const labelDecoKey = new PluginKey("labelDecos");
const labelDecoPlugin = new Plugin({
  key: labelDecoKey,
  state: {
    init() {
      return DecorationSet.empty;
    },
    apply(tr, old) {
      const meta = tr.getMeta(labelDecoKey);
      if (meta !== undefined) return meta;
      if (tr.docChanged) return DecorationSet.empty;
      return old;
    },
  },
  props: {
    decorations(state) {
      return labelDecoPlugin.getState(state);
    },
  },
});

// Custom node: preserves whitespace like <pre>, allows marks for highlighting
const SkillBlock = Node.create({
  name: "skillBlock",
  group: "block",
  content: "text*",
  marks: "_",
  whitespace: "pre",
  code: true,
  parseHTML() {
    return [{ tag: "pre" }];
  },
  renderHTML({ HTMLAttributes }) {
    return ["pre", mergeAttributes(HTMLAttributes), 0];
  },
});

// State
let editor: Editor;
let currentIndex = 0;
let totalSkills = 0;
let currentUrl = "";
let currentText = "";

// Selection drag tracking — prevents bubble menu from appearing mid-drag
let isDragging = false;

const PM_OFFSET = 1; // entering skillBlock costs 1 position

// Helpers
function shortUrl(url: string): string {
  const m = url.match(/github\.com\/([^/]+\/[^/]+)\/blob\/[^/]+\/(.+)/);
  return m ? `${m[1]}/${m[2]}` : url;
}

// API
async function fetchSkill(index: number) {
  const res = await fetch(`/api/skill/${index}`);
  if (!res.ok) throw new Error("Failed to load skill");
  return res.json();
}

// Load + render a skill
async function loadSkill(index: number) {
  const skill = await fetchSkill(index);
  currentIndex = skill.index;
  totalSkills = skill.total;
  currentUrl = skill.url;
  currentText = skill.text;

  editor.commands.setContent({
    type: "doc",
    content: [
      {
        type: "skillBlock",
        content: [{ type: "text", text: currentText }],
      },
    ],
  });

  updateNav();
  history.replaceState(null, "", `#${currentIndex + 1}`);
  window.scrollTo(0, 0);
}

function updateNav() {
  const meta = document.getElementById("meta")!;
  const counter = document.getElementById("counter")!;
  const prev = document.getElementById("prev") as HTMLButtonElement;
  const next = document.getElementById("next") as HTMLButtonElement;

  meta.innerHTML = `<a href="${currentUrl}" target="_blank">${shortUrl(currentUrl)}</a>`;
  counter.textContent = `${(currentIndex + 1).toLocaleString()} / ${totalSkills.toLocaleString()}`;
  prev.disabled = currentIndex <= 0;
  next.disabled = currentIndex >= totalSkills - 1;
}

// Init editor
editor = new Editor({
  element: document.getElementById("editor")!,
  editable: true,
  extensions: [
    StarterKit.configure({
      document: true,
      text: true,
      paragraph: false,
      heading: false,
      bulletList: false,
      orderedList: false,
      listItem: false,
      codeBlock: false,
      blockquote: false,
      horizontalRule: false,
      hardBreak: false,
      bold: false,
      italic: false,
      strike: false,
      code: false,
      dropcursor: false,
      gapcursor: false,
      history: false,
    }),
    SkillBlock,
    Extension.create({
      name: "selHighlight",
      addProseMirrorPlugins() {
        return [selHighlightPlugin, labelDecoPlugin];
      },
    }),
  ],
  content: {
    type: "doc",
    content: [
      { type: "skillBlock", content: [{ type: "text", text: "Loading..." }] },
    ],
  },
  // Read-only: allow selection but block edits
  editorProps: {
    handleDOMEvents: {
      mousedown: () => {
        isDragging = true;
        return false; // don't prevent default
      },
    },
    handleDoubleClick: (view, pos) => {
      // Select the full line instead of a word (or entire <pre> on triple-click)
      const resolved = view.state.doc.resolve(pos);
      const parent = resolved.parent;
      const offsetInNode = resolved.parentOffset;
      const text = parent.textContent;
      // Find line boundaries
      let lineStart = text.lastIndexOf("\n", offsetInNode - 1) + 1;
      let lineEnd = text.indexOf("\n", offsetInNode);
      if (lineEnd === -1) lineEnd = text.length;
      // Convert to absolute PM positions
      const base = resolved.start();
      const { tr } = view.state;
      tr.setSelection(TextSelection.create(tr.doc, base + lineStart, base + lineEnd));
      view.dispatch(tr);
      // Double-click is instant — clear drag flag so menu shows immediately
      isDragging = false;
      return true;
    },
    handleKeyDown: (_view, event) => {
      const allowed =
        event.key.startsWith("Arrow") ||
        event.key === "Home" ||
        event.key === "End" ||
        event.key === "PageUp" ||
        event.key === "PageDown" ||
        (event.key === "a" && (event.ctrlKey || event.metaKey)) ||
        (event.key === "c" && (event.ctrlKey || event.metaKey));
      return !allowed;
    },
    handleTextInput: () => true,
    handleDrop: () => true,
    handlePaste: () => true,
  },
});

function positionBubbleMenu() {
  const menuEl = document.getElementById("bubble-menu");
  if (!menuEl) return;
  const { from, to } = editor.state.selection;
  if (from === to) return;
  const wasHidden = menuEl.style.display === "none";
  menuEl.style.display = "flex";
  const start = editor.view.coordsAtPos(from);
  const end = editor.view.coordsAtPos(to, -1);
  const refLeft = Math.min(start.left, end.left);
  const refRight = Math.max(start.right, end.right);
  const refBottom = Math.max(start.bottom, end.bottom);
  const menuWidth = menuEl.offsetWidth;
  const x = refLeft + (refRight - refLeft - menuWidth) / 2;
  const y = refBottom + 8;
  menuEl.style.left = `${Math.max(4, x)}px`;
  menuEl.style.top = `${y}px`;
  // Only auto-focus when menu first appears, not on every reposition
  if (wasHidden) {
    const input = document.getElementById("tag-input") as HTMLInputElement;
    if (input) setTimeout(() => input.focus(), 0);
  }
}

function hideBubbleMenu() {
  const menuEl = document.getElementById("bubble-menu");
  if (menuEl) menuEl.style.display = "none";
}

function updateBubbleMenu() {
  const { from, to } = editor.state.selection;
  if (isDragging || from === to) {
    hideBubbleMenu();
  } else {
    positionBubbleMenu();
  }
}

// Show/hide bubble menu on every selection change
editor.on("selectionUpdate", () => updateBubbleMenu());

// Edge-scroll during drag selection
let scrollRafId = 0;
let scrollSpeed = 0;

function autoScroll() {
  if (scrollSpeed !== 0) {
    window.scrollBy(0, scrollSpeed);
    scrollRafId = requestAnimationFrame(autoScroll);
  } else {
    scrollRafId = 0;
  }
}

document.addEventListener("mousemove", (e) => {
  if (!isDragging) return;
  const threshold = 60;
  if (e.clientY > window.innerHeight - threshold) {
    scrollSpeed = Math.ceil((e.clientY - (window.innerHeight - threshold)) / 3);
  } else if (e.clientY < threshold) {
    scrollSpeed = -Math.ceil((threshold - e.clientY) / 3);
  } else {
    scrollSpeed = 0;
  }
  if (scrollSpeed !== 0 && !scrollRafId) {
    scrollRafId = requestAnimationFrame(autoScroll);
  }
});

// After drag ends, show the menu if there's a selection
document.addEventListener("mouseup", () => {
  if (!isDragging) return;
  isDragging = false;
  scrollSpeed = 0;
  requestAnimationFrame(() => updateBubbleMenu());
});

// Collapse selection when editor loses focus (unless focus went to tag input).
// Uses setTimeout because relatedTarget is null when focus moves via setTimeout.
editor.on("blur", () => {
  setTimeout(() => {
    const menuEl = document.getElementById("bubble-menu");
    const active = document.activeElement;
    if (active && menuEl?.contains(active)) return;
    const editorEl = document.getElementById("editor");
    if (active && editorEl?.contains(active)) return;
    const { from, to } = editor.state.selection;
    if (from !== to) {
      editor.commands.setTextSelection(to);
    }
  }, 0);
});

// Collapse selection on clicks outside editor + bubble menu
document.addEventListener("mousedown", (e) => {
  const target = e.target as Node;
  const editorEl = document.getElementById("editor");
  const menuEl = document.getElementById("bubble-menu");
  if (editorEl?.contains(target) || menuEl?.contains(target)) return;
  const { from, to } = editor.state.selection;
  if (from !== to) {
    editor.commands.setTextSelection(to);
  }
});

// Navigation
document.getElementById("next")!.addEventListener("click", () => {
  if (currentIndex < totalSkills - 1) loadSkillWithLabels(currentIndex + 1);
});
document.getElementById("prev")!.addEventListener("click", () => {
  if (currentIndex > 0) loadSkillWithLabels(currentIndex - 1);
});
document.addEventListener("keydown", (e) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
  if (e.key === "ArrowRight" || e.key === "l")
    document.getElementById("next")!.click();
  if (e.key === "ArrowLeft" || e.key === "h")
    document.getElementById("prev")!.click();
});

// --- Labels ---

interface Label {
  id: number;
  start_offset: number;
  end_offset: number;
  selected_text: string;
  tag: string;
  color: string;
}

let labels: Label[] = [];
const labelList = document.getElementById("label-list")!;
const tagInput = document.getElementById("tag-input") as HTMLInputElement;

async function fetchLabels() {
  const res = await fetch(`/api/labels?url=${encodeURIComponent(currentUrl)}`);
  if (!res.ok) return;
  labels = await res.json();
  renderLabelDecorations();
  // Wait for the editor to lay out before computing label positions
  requestAnimationFrame(() => renderLabels());
}

function renderLabelDecorations() {
  const decos = labels.map((label) =>
    Decoration.inline(
      label.start_offset + PM_OFFSET,
      label.end_offset + PM_OFFSET,
      { style: `background: ${label.color}` },
    ),
  );
  const decoSet = decos.length
    ? DecorationSet.create(editor.state.doc, decos)
    : DecorationSet.empty;
  editor.view.dispatch(
    editor.state.tr.setMeta(labelDecoKey, decoSet),
  );
}

function renderLabels() {
  labelList.innerHTML = "";
  // Use the editor's viewport top as reference — coordsAtPos returns viewport coords
  const editorTop = document.getElementById("editor")!.getBoundingClientRect().top;

  // Track occupied Y ranges per indent level for staggering
  const levels: Array<{ bottom: number }[]> = [[]];

  for (const label of labels) {
    const el = document.createElement("div");
    el.className = "label-item";
    el.innerHTML = `<span class="label-tag">${label.tag}</span>
      <button class="label-delete" data-id="${label.id}">&times;</button>`;

    const pmFrom = label.start_offset + PM_OFFSET;
    const pmTo = label.end_offset + PM_OFFSET;
    try {
      const startCoords = editor.view.coordsAtPos(pmFrom);
      const endCoords = editor.view.coordsAtPos(pmTo, -1);
      const top = startCoords.top - editorTop;
      const bottom = endCoords.bottom - editorTop;
      const height = Math.max(bottom - top, 20);

      // Find first indent level where this label doesn't overlap
      let level = 0;
      while (level < levels.length) {
        const occupied = levels[level];
        const overlaps = occupied.some((r) => top < r.bottom + 4);
        if (!overlaps) break;
        level++;
      }
      if (level >= levels.length) levels.push([]);
      levels[level].push({ bottom: top + height });

      el.style.top = `${top}px`;
      el.style.left = `${level * 80}px`;
      el.style.setProperty("--bar-height", `${height}px`);
      el.style.setProperty("--bar-color", label.color);
    } catch {
      // fallback: no positioning
    }

    labelList.appendChild(el);
  }

  // Re-render suggestions after user labels (they use the same stagger tracking)
  renderSuggestions(editorTop, levels);
}

// Delete label
labelList.addEventListener("click", async (e) => {
  const btn = (e.target as HTMLElement).closest(".label-delete") as HTMLElement;
  if (!btn) return;
  const id = btn.dataset.id;
  await fetch(`/api/label/${id}`, { method: "DELETE" });
  await fetchLabels();
});

// --- Tag autocomplete ---

interface TagInfo { name: string; color: string; }
let knownTags: TagInfo[] = [];
const tagSuggestions = document.getElementById("tag-suggestions")!;
let activeIdx = -1;

async function refreshKnownTags() {
  try {
    const res = await fetch("/api/tags");
    if (res.ok) knownTags = await res.json();
  } catch { /* ignore */ }
}
refreshKnownTags();

function showTagSuggestions(query: string) {
  const q = query.toLowerCase();
  const matches = q
    ? knownTags.filter((t) => t.name.toLowerCase().includes(q))
    : knownTags;
  if (matches.length === 0) {
    tagSuggestions.style.display = "none";
    tagSuggestions.innerHTML = "";
    activeIdx = -1;
    return;
  }
  tagSuggestions.innerHTML = matches
    .map(
      (t, i) =>
        `<div class="tag-option${i === activeIdx ? " active" : ""}" data-tag="${t.name}">` +
        `<span class="tag-color-dot" style="background:${t.color}"></span>${t.name}</div>`,
    )
    .join("");
  tagSuggestions.style.display = "block";
}

function hideTagSuggestions() {
  tagSuggestions.style.display = "none";
  activeIdx = -1;
}

function selectTag(tag: string) {
  tagInput.value = tag;
  hideTagSuggestions();
}

tagSuggestions.addEventListener("mousedown", (e) => {
  // Use mousedown instead of click so it fires before blur
  const option = (e.target as HTMLElement).closest(".tag-option") as HTMLElement;
  if (option) {
    e.preventDefault(); // prevent input blur
    selectTag(option.dataset.tag!);
  }
});

tagInput.addEventListener("input", () => {
  activeIdx = -1;
  showTagSuggestions(tagInput.value);
});

tagInput.addEventListener("focus", () => {
  showTagSuggestions(tagInput.value);
});

async function submitTag() {
  const tag = tagInput.value.trim();
  if (!tag) return;

  const { from, to } = editor.state.selection;
  if (from === to) return;

  const startOffset = from - PM_OFFSET;
  const endOffset = to - PM_OFFSET;
  const selectedText = currentText.slice(startOffset, endOffset);

  await fetch("/api/label", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      skill_url: currentUrl,
      start_offset: startOffset,
      end_offset: endOffset,
      selected_text: selectedText,
      tag,
    }),
  });

  tagInput.value = "";
  hideTagSuggestions();
  editor.commands.setTextSelection(to);
  await fetchLabels();
  refreshKnownTags();
}

// Keyboard navigation for tag input
tagInput.addEventListener("keydown", async (e) => {
  if (e.key === "Escape") {
    tagInput.value = "";
    hideTagSuggestions();
    const { to } = editor.state.selection;
    editor.commands.setTextSelection(to);
    editor.commands.focus();
    return;
  }

  const options = tagSuggestions.querySelectorAll(".tag-option");
  const count = options.length;

  if (e.key === "ArrowDown" && count > 0) {
    e.preventDefault();
    activeIdx = (activeIdx + 1) % count;
    options.forEach((el, i) => el.classList.toggle("active", i === activeIdx));
    options[activeIdx]?.scrollIntoView({ block: "nearest" });
    return;
  }

  if (e.key === "ArrowUp" && count > 0) {
    e.preventDefault();
    activeIdx = activeIdx <= 0 ? count - 1 : activeIdx - 1;
    options.forEach((el, i) => el.classList.toggle("active", i === activeIdx));
    options[activeIdx]?.scrollIntoView({ block: "nearest" });
    return;
  }

  if (e.key === "Tab" && activeIdx >= 0 && count > 0) {
    e.preventDefault();
    const selected = options[activeIdx] as HTMLElement;
    selectTag(selected.dataset.tag!);
    return;
  }

  if (e.key === "Enter") {
    if (activeIdx >= 0 && count > 0) {
      const selected = options[activeIdx] as HTMLElement;
      tagInput.value = selected.dataset.tag!;
      hideTagSuggestions();
    }
    await submitTag();
    return;
  }
});

// --- Auto-categorize (LLM suggestions) ---

interface Suggestion {
  line_start: number;
  char_start: number;
  line_end: number;
  char_end: number;
  tag: string;
  reason: string;
  // Computed character offsets into the full text
  start_offset?: number;
  end_offset?: number;
}

let suggestions: Suggestion[] = [];

/** Convert line:char positions to absolute character offsets. */
function resolveOffsets(text: string, sections: Suggestion[]): Suggestion[] {
  const lines = text.split("\n");
  // Build cumulative offsets: lineOffsets[i] = char index of line i start (1-indexed)
  const lineOffsets: number[] = [0]; // placeholder for index 0
  let cum = 0;
  for (let i = 0; i < lines.length; i++) {
    lineOffsets.push(cum); // lineOffsets[i+1] = start of line i+1 (1-indexed)
    cum += lines[i].length + 1; // +1 for the \n
  }

  return sections.map((s) => {
    const startLine = Math.max(1, Math.min(s.line_start, lines.length));
    const endLine = Math.max(1, Math.min(s.line_end, lines.length));
    const startOffset = lineOffsets[startLine] + Math.min(s.char_start, (lines[startLine - 1] || "").length);
    const endOffset = lineOffsets[endLine] + Math.min(s.char_end, (lines[endLine - 1] || "").length);
    return { ...s, start_offset: startOffset, end_offset: endOffset };
  });
}

const aiLoading = document.getElementById("ai-loading")!;

// Abort controller for auto-categorize requests — cancelled on navigation
let categorizeController: AbortController | null = null;

async function fetchAutoCategories(index: number) {
  // Abort any in-flight requests from previous navigation
  categorizeController?.abort();
  categorizeController = new AbortController();
  const { signal } = categorizeController;

  suggestions = [];
  aiLoading.hidden = false;
  try {
    const res = await fetch(`/api/auto-categorize/${index}`, { signal });
    if (!res.ok) return;
    const data = await res.json();
    if (data.sections && Array.isArray(data.sections)) {
      suggestions = resolveOffsets(currentText, data.sections);
      requestAnimationFrame(() => renderLabels());
    }
  } catch (e) {
    if ((e as Error).name === "AbortError") return;
  } finally {
    aiLoading.hidden = true;
  }
}

// Same 100 colors as server.js — golden angle spacing for maximum visual separation
const SUGGESTION_PALETTE = [
  "#eec4c4", "#b3efc5", "#e3d1f0", "#f0e7a8", "#c6eaf1",
  "#eec4da", "#c2efb3", "#d2d1f0", "#f0c0a8", "#c6f1e1",
  "#eac4ee", "#e2efb3", "#d1e0f0", "#f0a8b7", "#c6f1ca",
  "#d4c4ee", "#efdbb3", "#d1f0ee", "#f0a8de", "#d9f1c6",
  "#c4cbee", "#efbbb3", "#d1f0de", "#dba8f0", "#f1f1c6",
  "#c4e1ee", "#efb3cc", "#d5f0d1", "#b4a8f0", "#f1dac6",
  "#c4eee3", "#efb3ec", "#e5f0d1", "#a8c3f0", "#f1c6c9",
  "#c4eecd", "#d1b3ef", "#f0e9d1", "#a8e9f0", "#f1c6e0",
  "#d2eec4", "#b3b5ef", "#f0d9d1", "#a8f0cf", "#eac6f1",
  "#e8eec4", "#b3d6ef", "#f0d1da", "#a8f0a9", "#d3c6f1",
  "#eeddc4", "#b3efe8", "#f0d1ea", "#cef0a8", "#c6d0f1",
  "#eec6c4", "#b3efc8", "#e4d1f0", "#f0eaa8", "#c6e7f1",
  "#eec4d8", "#bfefb3", "#d4d1f0", "#f0c4a8", "#c6f1e3",
  "#ecc4ee", "#dfefb3", "#d1dff0", "#f0a8b4", "#c6f1cc",
  "#d6c4ee", "#efdeb3", "#d1eff0", "#f0a8da", "#d7f1c6",
  "#c4c9ee", "#efbeb3", "#d1f0df", "#dfa8f0", "#eef1c6",
  "#c4dfee", "#efb3c9", "#d3f0d1", "#b8a8f0", "#f1dcc6",
  "#c4eee5", "#efb3e9", "#e4f0d1", "#a8bff0", "#f1c6c7",
  "#c4eecf", "#d4b3ef", "#f0ebd1", "#a8e6f0", "#f1c6de",
  "#cfeec4", "#b4b3ef", "#f0dad1", "#a8f0d3", "#ecc6f1",
];

const suggestionColorMap = new Map<string, string>();

function suggestionColor(tag: string): string {
  let color = suggestionColorMap.get(tag);
  if (!color) {
    color = SUGGESTION_PALETTE[suggestionColorMap.size % SUGGESTION_PALETTE.length];
    suggestionColorMap.set(tag, color);
  }
  return color;
}

function renderSuggestions(editorTop: number, levels: Array<{ bottom: number }[]>) {
  labelList.querySelectorAll(".label-suggestion").forEach((el) => el.remove());

  for (let i = 0; i < suggestions.length; i++) {
    const s = suggestions[i];
    if (s.start_offset == null || s.end_offset == null) continue;

    const color = suggestionColor(s.tag);
    const el = document.createElement("div");
    el.className = "label-item label-suggestion";
    el.title = s.reason;
    el.innerHTML = `<span class="label-tag" style="color: ${color}">${s.tag}</span>
      <button class="suggestion-accept" data-idx="${i}" title="Accept">&#x2713;</button>
      <button class="suggestion-dismiss" data-idx="${i}" title="Dismiss">&times;</button>`;

    const pmFrom = s.start_offset + PM_OFFSET;
    const pmTo = s.end_offset + PM_OFFSET;
    try {
      const startCoords = editor.view.coordsAtPos(pmFrom);
      const endCoords = editor.view.coordsAtPos(pmTo, -1);
      const top = startCoords.top - editorTop;
      const bottom = endCoords.bottom - editorTop;
      const height = Math.max(bottom - top, 20);

      let level = 0;
      while (level < levels.length) {
        const occupied = levels[level];
        const overlaps = occupied.some((r) => top < r.bottom + 4);
        if (!overlaps) break;
        level++;
      }
      if (level >= levels.length) levels.push([]);
      levels[level].push({ bottom: top + height });

      el.style.top = `${top}px`;
      el.style.left = `${level * 80}px`;
      el.style.setProperty("--bar-height", `${height}px`);
      el.style.setProperty("--bar-color", color);
    } catch {
      // fallback: no positioning
    }

    labelList.appendChild(el);
  }
}

// Accept / dismiss suggestion clicks
labelList.addEventListener("click", async (e) => {
  const accept = (e.target as HTMLElement).closest(".suggestion-accept") as HTMLElement;
  if (accept) {
    const idx = parseInt(accept.dataset.idx!, 10);
    const s = suggestions[idx];
    if (!s || s.start_offset == null || s.end_offset == null) return;

    const selectedText = currentText.slice(s.start_offset, s.end_offset);
    await fetch("/api/label", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        skill_url: currentUrl,
        start_offset: s.start_offset,
        end_offset: s.end_offset,
        selected_text: selectedText,
        tag: s.tag,
      }),
    });
    suggestions.splice(idx, 1);
    await fetchLabels();
    return;
  }

  const dismiss = (e.target as HTMLElement).closest(".suggestion-dismiss") as HTMLElement;
  if (dismiss) {
    const idx = parseInt(dismiss.dataset.idx!, 10);
    suggestions.splice(idx, 1);
    renderLabels();
    return;
  }
});

async function loadSkillWithLabels(index: number) {
  await loadSkill(index);
  await fetchLabels();
  // Fire auto-categorize in background (non-blocking)
  fetchAutoCategories(index);
  // Pre-warm cache for next 5 skills
  prefetchAutoCategories(index);
}

let prefetchController: AbortController | null = null;

function prefetchAutoCategories(current: number) {
  prefetchController?.abort();
  prefetchController = new AbortController();
  const { signal } = prefetchController;
  for (let i = 1; i <= 5; i++) {
    const idx = current + i;
    if (idx < totalSkills) {
      fetch(`/api/auto-categorize/${idx}`, { signal }).catch(() => {});
    }
  }
}

// Reposition labels on resize
window.addEventListener("resize", () => {
  if (labels.length || suggestions.length) renderLabels();
});

// Expose for Playwright testing
(window as any).__editor = editor;

// Boot
const hashNum = parseInt(location.hash.replace("#", ""), 10) || 1;
const startIndex = Math.max(0, hashNum - 1);
loadSkillWithLabels(startIndex);
