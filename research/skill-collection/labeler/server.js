import express from "express";
import Database from "better-sqlite3";
import { inflateSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { categorizeSkill } from "./llm.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "..", "data", "analyzed", "content.db");
const URLS_PATH = join(__dirname, "..", "data", "analyzed", "english_deduped_urls.txt");

const LABELS_PATH = join(__dirname, "..", "data", "analyzed", "labels.db");

const db = new Database(DB_PATH, { readonly: true });
const labelsDb = new Database(LABELS_PATH);
labelsDb.pragma("journal_mode = WAL");
labelsDb.exec(`
  CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_url TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    selected_text TEXT NOT NULL,
    tag TEXT NOT NULL,
    color TEXT NOT NULL DEFAULT '#bfdbfe',
    created_at TEXT DEFAULT (datetime('now'))
  )
`);

// Migrate: add color column if missing
try {
  labelsDb.exec("ALTER TABLE labels ADD COLUMN color TEXT NOT NULL DEFAULT '#bfdbfe'");
} catch { /* column already exists */ }

// Tags table: unique tag name → color
labelsDb.exec(`
  CREATE TABLE IF NOT EXISTS tags (
    name TEXT PRIMARY KEY,
    color TEXT NOT NULL
  )
`);

// 100 maximally-spaced pastel colors (golden angle in HSL, varied saturation/lightness)
const LABEL_COLORS = [
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

function getOrCreateTagColor(tagName) {
  const existing = labelsDb.prepare("SELECT color FROM tags WHERE name = ?").get(tagName);
  if (existing) return existing.color;
  const tagCount = labelsDb.prepare("SELECT COUNT(*) as c FROM tags").get().c;
  const color = LABEL_COLORS[tagCount % LABEL_COLORS.length];
  labelsDb.prepare("INSERT INTO tags (name, color) VALUES (?, ?)").run(tagName, color);
  return color;
}

const insertLabel = labelsDb.prepare(
  "INSERT INTO labels (skill_url, start_offset, end_offset, selected_text, tag, color) VALUES (?, ?, ?, ?, ?, ?)"
);
const labelsByUrl = labelsDb.prepare(
  "SELECT id, start_offset, end_offset, selected_text, tag, color, created_at FROM labels WHERE skill_url = ? ORDER BY start_offset"
);

const app = express();
app.use(express.json());

// Load URLs and shuffle deterministically
const allUrls = readFileSync(URLS_PATH, "utf-8").trim().split("\n");
function mulberry32(seed) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rng = mulberry32(42);
for (let i = allUrls.length - 1; i > 0; i--) {
  const j = Math.floor(rng() * (i + 1));
  [allUrls[i], allUrls[j]] = [allUrls[j], allUrls[i]];
}

const total = allUrls.length;
const stmtByUrl = db.prepare("SELECT url, raw FROM content WHERE url = ?");

function decompress(raw) {
  try {
    return inflateSync(raw).toString("utf-8");
  } catch {
    return raw.toString("utf-8");
  }
}

function shortUrl(url) {
  const m = url.match(/github\.com\/([^/]+\/[^/]+)\/blob\/[^/]+\/(.+)/);
  return m ? `${m[1]}/${m[2]}` : url;
}

function getSkill(url) {
  const row = stmtByUrl.get(url);
  if (!row) return null;
  return { url: row.url, short: shortUrl(row.url), text: decompress(row.raw) };
}

// --- Routes ---

app.get("/api/skill/:index", (req, res) => {
  const idx = parseInt(req.params.index, 10);
  if (isNaN(idx) || idx < 0 || idx >= total)
    return res.status(404).json({ error: "index out of range" });
  const skill = getSkill(allUrls[idx]);
  if (!skill) return res.status(404).json({ error: "not found in db" });
  res.json({ ...skill, index: idx, total });
});

app.get("/api/skill", (req, res) => {
  const { url } = req.query;
  if (!url) return res.status(400).json({ error: "url required" });
  const skill = getSkill(url);
  if (!skill) return res.status(404).json({ error: "not found" });
  res.json({ ...skill, index: allUrls.indexOf(url), total });
});

app.post("/api/label", (req, res) => {
  const { skill_url, start_offset, end_offset, selected_text, tag } = req.body;
  if (!skill_url || start_offset == null || end_offset == null || !selected_text || !tag)
    return res.status(400).json({ error: "missing fields" });
  const color = getOrCreateTagColor(tag);
  const result = insertLabel.run(skill_url, start_offset, end_offset, selected_text, tag, color);
  res.json({ id: result.lastInsertRowid, color });
});

app.get("/api/labels", (req, res) => {
  const { url } = req.query;
  if (!url) return res.status(400).json({ error: "url required" });
  res.json(labelsByUrl.all(url));
});

app.get("/api/tags", (_req, res) => {
  const tags = labelsDb.prepare("SELECT name, color FROM tags ORDER BY name").all();
  res.json(tags);
});

app.delete("/api/label/:id", (req, res) => {
  const id = parseInt(req.params.id, 10);
  labelsDb.prepare("DELETE FROM labels WHERE id = ?").run(id);
  res.json({ ok: true });
});

app.get("/api/auto-categorize/:index", async (req, res) => {
  const idx = parseInt(req.params.index, 10);
  if (isNaN(idx) || idx < 0 || idx >= total)
    return res.status(404).json({ error: "index out of range" });
  const skill = getSkill(allUrls[idx]);
  if (!skill) return res.status(404).json({ error: "not found in db" });
  try {
    const result = await categorizeSkill(skill.text);
    res.json(result);
  } catch (err) {
    console.error("auto-categorize error:", err);
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 2721;
app.listen(PORT, "0.0.0.0", () => {
  console.log(`API server → http://localhost:${PORT}  (${total} skills)`);
});
