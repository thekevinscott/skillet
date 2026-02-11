import { query } from "@anthropic-ai/claude-agent-sdk";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";

const CACHE_DIR = join(homedir(), ".cache", "skill-labeler");
mkdirSync(CACHE_DIR, { recursive: true });

/**
 * Generic cached LLM call with structured output via claude-agent-sdk.
 * Cache key = SHA-256 of { systemPrompt, userPrompt }.
 */
export async function cachedQuery(systemPrompt, userPrompt, schema) {
  const key = createHash("sha256")
    .update(JSON.stringify({ systemPrompt, userPrompt }))
    .digest("hex");
  const cachePath = join(CACHE_DIR, `${key}.json`);

  if (existsSync(cachePath)) {
    return JSON.parse(readFileSync(cachePath, "utf-8"));
  }

  let result = null;
  for await (const message of query({
    prompt: userPrompt,
    options: {
      systemPrompt,
      model: "haiku",
      maxTurns: 3,
      permissionMode: "bypassPermissions",
      allowDangerouslySkipPermissions: true,
      outputFormat: { type: "json_schema", schema },
    },
  })) {
    if (message.type === "result" && message.structured_output) {
      result = message.structured_output;
    }
  }

  if (!result) throw new Error("No structured output from LLM");

  writeFileSync(cachePath, JSON.stringify(result, null, 2));
  return result;
}

const SYSTEM_PROMPT = `You are a precise document-section classifier for AI agent skill definition files (SKILL.md). Given a complete SKILL.md file, identify distinct sections and categorize each one.

Each section should be tagged with exactly one of these 14 anatomy categories:
- background: Contextual or prerequisite knowledge needed to understand the skill; historical context, domain background, or foundational concepts.
- best-practices: Recommended approaches, tips, guidelines, or advice for effectively applying the skill; often phrased as "do this" or "prefer X over Y."
- checklist: Step-by-step verification lists, often using checkbox characters or numbered/bulleted action items to confirm completion of a process.
- description: High-level overview or introductory explanation of what the skill is about; typically appears near the top of the file summarizing the skill's purpose.
- examples: Concrete demonstrations, sample inputs/outputs, code snippets illustrating usage, or worked-through scenarios showing the skill in action.
- output-format: Specifications for how results should be structured or formatted; describes expected output shape, schema, templates, or formatting conventions.
- persona: Defines the role, identity, or character the agent should adopt when using this skill; often begins with "You are..." or "Act as..."
- resources: Links, references, external documentation pointers, file paths to related materials, or sections containing URLs or resource listings.
- verification: Criteria, tests, or validation steps to confirm the skill was applied correctly; may include acceptance criteria, test commands, or quality checks.
- version-history: Changelog entries, version numbers with dates, or records of updates and modifications to the skill file over time.
- what-not-to-do: Explicit anti-patterns, prohibitions, or negative instructions warning against specific mistakes; phrased as "Do NOT," "Avoid," or "Never."
- what-to-do: Explicit positive instructions or directives specifying required actions or behaviors; phrased as imperatives like "Always," "Make sure to," or "You must."
- when-not-to-use: Conditions, scenarios, or contexts where the skill should NOT be applied; describes exclusions or situations outside the skill's scope.
- when-to-use: Conditions, triggers, or scenarios that indicate this skill should be activated; often phrased as "Use this skill when..."

Classification guidelines:
1. Focus on the purpose and function of each section, not just surface keywords.
2. Distinguish semantically close categories: "what-not-to-do" (prohibited actions) vs. "when-not-to-use" (inapplicable scenarios); "best-practices" (recommendations) vs. "what-to-do" (mandatory directives); "description" (overview) vs. "background" (prerequisite context).
3. Use structural cues like headings as signals, but verify by examining actual content.
4. Every part of the file should be covered — assign exactly one tag per section.

Use line numbers (1-indexed) and character offsets within those lines.
Be precise about where each section starts and ends.`;

const SCHEMA = {
  type: "object",
  properties: {
    sections: {
      type: "array",
      items: {
        type: "object",
        properties: {
          line_start: { type: "integer", description: "1-indexed start line" },
          char_start: {
            type: "integer",
            description: "0-indexed char offset within start line",
          },
          line_end: { type: "integer", description: "1-indexed end line" },
          char_end: {
            type: "integer",
            description: "0-indexed char offset within end line (exclusive)",
          },
          tag: { type: "string", enum: ["background", "best-practices", "checklist", "description", "examples", "output-format", "persona", "resources", "verification", "version-history", "what-not-to-do", "what-to-do", "when-not-to-use", "when-to-use"], description: "Anatomy category" },
          reason: {
            type: "string",
            description: "Brief explanation for this categorization",
          },
        },
        required: [
          "line_start",
          "char_start",
          "line_end",
          "char_end",
          "tag",
          "reason",
        ],
      },
    },
  },
  required: ["sections"],
};

/**
 * Categorize a skill file into anatomy sections.
 * Returns { sections: [...] }.
 */
export async function categorizeSkill(text) {
  return await cachedQuery(SYSTEM_PROMPT, text, SCHEMA);
}
