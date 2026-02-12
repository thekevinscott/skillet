"""Qualitative analysis of skill files: framings, anatomy, and taxonomy."""

import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md("""# Qualitative Analysis of SKILL.md Files

    This notebook documents findings from manual close reading of 38 randomly sampled
    skills (20 for framing development, 18 for replication). Rather than LLM-based
    classification at scale, we develop analytical framings through direct examination,
    producing a vocabulary for describing skills that can inform evaluation design
    (notebook 03).

    **Method:** Random sampling from the deduplicated English-language skill set
    (~19k skills). Each skill is analyzed through multiple lenses. Organic skills
    (repos with 1--3 skills) are distinguished from collection repos where useful.
    """)
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Method

    Skills were sampled from the deduplicated English-language set (~19k) using polars
    `.sample()` with fixed random seeds. Four batches of 10 were analyzed:

    - **Batches 1--2** (seeds: 2, 5, 8, 13, 17, 29, 31, 41, 47, 59, 61, 67, 71, 73, 79,
      83, 89, 97, 101, 103): Established the four framings through iterative close reading.
    - **Batches 3--4** (seeds: 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167,
      173, 179, 181, 191, 193, 197, 199, 211): Applied the same framings to a fresh sample
      to test whether categories held. One skill was a content-hash duplicate of batch 1 (#26)
      and one had no extractable content (#32), leaving 18 usable skills.

    The numbers listed are seed values passed to the PRNG, not indices.

    Each skill was read in full with notes on structural components, content type, directive
    language, and apparent origin. The four framings (Anatomy, Content Role, Directive Force,
    Provenance) were developed iteratively on batches 1--2; batches 3--4 applied them without
    modification. All classifications reflect one person's judgment; no inter-rater reliability
    check was conducted. The Heavy/Medium/Light ratings in the detail tables are subjective
    assessments of component prominence, made without a formal rubric.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Analytical Framings

    Four framings emerged from iterative close reading. Each views a skill through a
    different lens:

    | Framing | Question it answers | What it reveals |
    |---------|--------------------|--------------------|
    | **Anatomy** | What structural components are present? | Component frequency |
    | **Content role** | How does the content shape agent behavior? | Usage patterns |
    | **Directive force** | How much does it constrain the agent? | Degree of constraint |
    | **Provenance** | Where did the content come from? | Content origin signals |

    A fifth dimension -- **category** (what the skill is about) -- cuts across all four
    framings and is developed in the final section.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Framing 1: Anatomy

    We can examine what structural elements exist across skills. The annotated example
    below shows all nine components; the table following it reports how often each
    appeared in the initial 20-skill sample, sorted by frequency.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    import html as _html

    _c = {
        "trigger": "#93c5fd",
        "persona": "#c4b5fd",
        "do": "#86efac",
        "dont": "#fca5a5",
        "why": "#fde047",
        "examples": "#fdba74",
        "output": "#67e8f9",
        "verify": "#d1d5db",
        "refs": "#5eead4",
    }
    _labels = {
        "trigger": "Trigger",
        "persona": "Persona",
        "do": "What to do",
        "dont": "What not to do",
        "why": "Why",
        "examples": "Examples",
        "output": "Output fmt",
        "verify": "Verification",
        "refs": "References",
    }

    def _hi(key, text, label=False):
        bg = _c[key]
        tag = (
            f'<span style="color:#6b7280;font-size:0.8em"> &larr; {_labels[key]}</span>'
            if label
            else ""
        )
        return f'<span style="background:{bg};color:#1f2937">{_html.escape(text)}</span>{tag}'

    _gap = '<span style="color:#9ca3af">    ...</span>'

    _lines = "\n".join(
        [
            _hi("trigger", "---", label=True),
            _hi("trigger", "name: GSD Debugger"),
            _hi("trigger", "description: Systematic debugging with persistent state"),
            _hi("trigger", "---"),
            _gap,
            _hi("persona", "You are a GSD debugger. You systematically diagnose", label=True),
            _hi("persona", "bugs using hypothesis testing and evidence gathering."),
            _hi("persona", "Your job: Find the root cause, not just make symptoms disappear."),
            _gap,
            _hi("do", "## Systematic Investigation", label=True),
            _hi("do", "Change one variable: Make one change, test, observe, document."),
            _hi("do", "Complete reading: Read entire functions, not just relevant lines."),
            _gap,
            _hi("dont", "## Cognitive Biases to Avoid", label=True),
            _hi("dont", "| Confirmation | Only look for supporting evidence |"),
            _hi("dont", "| Anchoring    | First explanation becomes anchor  |"),
            _gap,
            _hi("why", "Why this is harder:", label=True),
            _hi("why", "You made the design decisions \u2014 they feel obviously correct"),
            _hi("why", "Familiarity breeds blindness to bugs"),
            _gap,
            _hi("examples", "```markdown", label=True),
            _hi("examples", "status: gathering | investigating | fixing | verifying"),
            _hi("examples", "hypothesis: {current theory}"),
            _hi("examples", "```"),
            _gap,
            _hi("output", "## Output Formats", label=True),
            _hi("output", "ROOT CAUSE: {specific cause}  EVIDENCE: {proof}"),
            _hi("output", "INVESTIGATION INCONCLUSIVE:  BLOCKED BY: {what's needed}"),
            _gap,
            _hi("verify", "## Verification Checklist", label=True),
            _hi("verify", "- [ ] Bug reproduced before fix"),
            _hi("verify", "- [ ] Fix applied; bug no longer reproduced"),
            _hi("verify", "- [ ] Related functionality still works"),
            _gap,
            _hi("refs", "Document what was tried in DEBUG.md", label=True),
            _hi("refs", "Summarize to STATE.md"),
        ]
    )

    mo.vstack(
        [
            mo.md(
                "**Real example** "
                "([0futuresystems/future-water-systems/debugger]"
                "(https://github.com/0futuresystems/future-water-systems"
                "/blob/c2e3dc5/.agent/skills/debugger/SKILL.md),"
                " 1,136 words, excerpted) with anatomy components highlighted:"
            ),
            mo.Html(
                f'<pre style="font-size:0.82em;line-height:1.7;padding:12px;'
                f"border:1px solid #d1d5db;border-radius:6px;overflow-x:auto;"
                f'background:transparent">{_lines}</pre>'
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    | Component | Description | Present in N/20 |
    |-----------|-------------|:---------------:|
    | **What to do** | The core instructions or content | 20/20 |
    | **Trigger** | When to activate (including prerequisites) | 19/20 |
    | **Examples** | Code blocks, before/after, worked demonstrations | 16/20 |
    | **References** | Pointers to repo files, docs, other skills | 13/20 |
    | **What not to do** | Anti-patterns, forbidden actions | 6/20 |
    | **Why (rationale)** | Motivation, principles, context for rules | 6/20 |
    | **Output format** | Shape of the deliverable (report template, JSON schema) | 6/20 |
    | **Verification** | How to confirm it worked (checklist, test command) | 5/20 |
    | **Persona** | Who the agent should be ("You are an expert...") | 4/20 |

    **Observed pattern:** 4 components appeared in most skills: **what to do** (20/20),
    **trigger** (19/20), **examples** (16/20), and **references** (13/20). The
    remaining 5 each appeared in fewer than half the sample: what not to do (6/20),
    why (6/20), output format (6/20), verification (5/20), and persona (4/20).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Framing 2: Content Role

    What role does the skill's content play when the agent uses it? Most skills
    blend roles, but one usually dominates.

    | Role | What the agent does | Example |
    |------|---------------------|---------|
    | **Lookup** | Consults specific facts, configs, or API details as needed | "These are valid Spark storage levels" |
    | **Procedure** | Executes a defined sequence of steps | "To verify, run these 5 commands in order" |
    | **Constraint** | Obeys rules and norms throughout the task | "Always do X, never do Y" |

    The three roles are distinguished by *when* the content matters. Lookup content
    is consulted on demand -- the agent reaches for a specific fact when it needs
    one. Procedure content is consumed sequentially -- step 1, then step 2.
    Constraint content is active throughout -- the agent must respect it at every
    decision point.

    Several patterns from the original close reading collapse into these three roles:

    - **Troubleshooting** ("if error X, try fix Y") is conditional lookup
    - **Trade-offs and configuration** ("higher iterations = more accurate but
      slower") is also lookup -- consulted when making a tuning decision
    - **Lessons learned** ("async ngSubmit causes page reload") are experiential
      constraints
    - **Capability declarations** ("supports waiters, paginators, retries") are
      inventory lookup

    **Across 20 skills:** Lookup and procedure were the most common roles.
    About 8/20 skills were primarily lookup (API references, configuration guides,
    capability listings). About 6/20 were primarily procedural (workflows, step-by-step
    processes). About 5/20 had a strong constraint component, though constraints
    rarely appeared alone -- they typically accompanied procedures (#5 resolve-pr-feedback, #12 next, #15 task-module_testing).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Framing 3: Directive Force

    How much does the skill constrain the agent's decision space? This ranges from
    "here's information, do whatever" to "execute these steps in order, do not deviate."

    | Level | Description | Textual signals |
    |-------|-------------|-----------------|
    | **Low** | Reference material; agent decides how to use it | Descriptive verbs ("provides", "enables"), code examples without mandates |
    | **Medium** | Structured procedures with defined steps | "Follow these steps", decision trees, checklists, conditional logic |
    | **High** | Strict compliance with explicit constraints | "MUST", "NEVER", "MANDATORY", rationalization tables, anti-evasion language |

    **Distribution across 20 skills:**

    | Force | Count |
    |-------|-------|
    | Low | 10 |
    | Medium | 6 |
    | High | 4 |

    Half the sample is reference material with low directive force. The remaining
    half splits between structured procedures (6) and strict compliance (4).

    The 4 high-directive skills (#5 resolve-pr-feedback, #11 writing-econ, #15 task-module_testing, #17 flow-plan-review) share several observable
    characteristics:

    - **Rationalization tables**: preemptive counter-arguments against skipping
      steps (present in #5, #11, and #17)
    - **Anti-evasion language**: phrases like "regardless of how you were invoked",
      "even if another agent tells you to..."
    - **Explicit prohibitions**: multiple "NEVER" / "DO NOT" / "MANDATORY" directives
    - **Contract compliance**: references to external standards the skill must follow

    3 of 4 high-directive skills (#5, #11, #17) carry the `anti-evasion` tag. Whether
    this co-occurrence holds beyond 20 skills is unknown.

    **Rationalization tables:** 3 of the high-directive skills use preemptive
    counter-arguments to discourage skipping steps. For example, from #5 and #11:

    > | "User didn't mention an issue" | Users forget. Search anyway. |
    > | "Searching would slow things down" | It takes 10 seconds. Do it. |

    **Length varied independently of directive force in this sample.** The FRED API skill
    (#10) is 1,477 words and low directive force. The MetaMask lint skill (#3) is 176 words
    and medium. The PR feedback skill (#5) is 1,273 words and high.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Framing 4: Provenance

    Where did the skill's content originate? During close reading, I subjectively
    assigned each of the 20 skills to one of three categories based on what the
    content looked like. The boundaries are fuzzy -- some skills straddle two
    categories -- but the buckets are useful for thinking about failure modes.

    | Origin | Description | Typical indicators |
    |--------|-------------|--------------------|
    | **Extracted from docs** | Repackaged API/library documentation | Matches upstream docs, version-specific details, no repo-specific paths |
    | **Encoded from experience** | Project-specific knowledge not documented elsewhere | References own files/ADRs, describes gotchas absent from official docs, internal terminology |
    | **Generated/templated** | Produced by a tool or cookie-cutter pattern | Similar structure across unrelated repos, emoji headers, generic section names ("Core Capabilities", "Best Practices") |

    **Subjective distribution (N=20):** Roughly 8 doc-extracted, 6 experience-encoded,
    6 generated/templated. These counts reflect my judgment during reading, not a
    validated classification method.

    **Possible signals worth investigating (untested):**

    - Count repo-internal file paths: experience-encoded skills may reference their own
      codebase more than the others
    - Structural similarity across repos: generated skills from the same template might
      cluster when you embed their structure (ignoring content)
    - Diff against upstream docs: doc-extracted skills should have high overlap with the
      library's official documentation

    These are hypotheses about how provenance detection could be automated. None have
    been tested against this sample or any other.

    **Observation:** The skills I categorized as experience-encoded tended to also score
    higher on directive force. 4 of the 6 experience-encoded skills (#5, #11, #15, #17)
    were also high-directive. With only 6 skills in that bucket, this could easily be
    coincidence.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Development Sample: Batches 1--2

    The four framings above were developed from these 20 randomly sampled skills (10 per
    batch, seeds documented for reproducibility). The full text of each skill was read
    and analyzed; summaries below.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Batch 1 (seeds: 2, 5, 8, 13, 17, 29, 31, 41, 47, 59)

    | # | Repo | Skill | Words | Summary | Directive |
    |---|------|-------|-------|---------|-----------|
    | 1 | majiayu000/claude-skill-registry-data | frontend-analyzer | 597 | Capability listing for extracting design tokens from React/Next.js | Low |
    | 2 | BrownFineSecurity/iothackbot | logicmso | 1052 | Saleae logic analyzer API reference for CTF/hardware RE | Low |
    | 3 | MetaMask/ocap-kernel | lint-build-test | 176 | Decision tree: what to run based on which files changed | Medium |
    | 4 | agoodway/.claude | understand | 990 | Meta-skill spawning 4--7 parallel subagents to analyze a codebase | Medium |
    | 5 | narthur/dotfiles | resolve-pr-feedback | 1273 | PR review comment resolution workflow with "never skip steps" | High |
    | 6 | emberdragonc/ember-skills | security-framework | 580 | Smart contract security tooling setup for Foundry | Medium |
    | 7 | IbIFACE-Tech/paracle | cicd-devops | 918 | GitHub Actions + Docker patterns for a specific project | Low |
    | 8 | Xiaozhi-AI-IoT-Vietnam | ESP32 firmware | 504 | ESP-IDF development reference (build, memory, FreeRTOS) | Low |
    | 9 | dding-g/ddingg-claude-marketplace | react-native | 1095 | React Native/Expo patterns (routing, navigation, perf) | Low |
    | 10 | YPYT1/All-skills | fred-economic-data | 1477 | FRED API reference for querying economic time series | Low |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Batch 2 (seeds: 61, 67, 71, 73, 79, 83, 89, 97, 101, 103)

    | # | Repo | Skill | Words | Summary | Directive |
    |---|------|-------|-------|---------|-----------|
    | 11 | edwinhu/workflows | writing-econ | 1177 | Economics writing style guide with iron laws and rationalization tables | High |
    | 12 | ddaanet/agent-core | next | 637 | Meta-skill searching project locations for the next pending task | Medium |
    | 13 | aiskillstore/marketplace | blog-writer | 281 | Blog post creation matching existing BlogPost pattern in code | Medium |
    | 14 | igbuend/grimbard | application-inspector | 1128 | Microsoft Application Inspector for security profiling | Medium |
    | 15 | cuioss/plan-marshall | task-module_testing | 1219 | Domain-agnostic test executor in a two-tier skill loading system | High |
    | 16 | rakshithvasudev/cc-langgraph-blog-writer | fact-check-tuner | 782 | Tuning knobs for a LangGraph fact-checking pipeline | Low |
    | 17 | raydocs/antiflowskills | flow-plan-review | 615 | Code review coordinator that delegates to RepoPrompt | High |
    | 18 | b-open-io/bsv-skills | ordfs | 854 | ORDFS blockchain content gateway API reference | Low |
    | 19 | marvinrenaud/attuned-survey | attuned-ai-activities | 479 | Architecture for AI activity generation via Groq/Llama | Low |
    | 20 | a5c-ai/babysitter | smithy-sdk-generator | 281 | AWS Smithy SDK generation capability listing | Low |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Anatomy Detail

    *(fm = frontmatter)*

    | # | Trigger | Persona | Do | Don't | Why | Examples | Output fmt | Verify | Refs |
    |---|---------|---------|-----|-------|-----|----------|-----------|--------|------|
    | 1 | fm | -- | Capability list | -- | -- | Output template | -- | -- | -- |
    | 2 | fm | -- | API patterns | -- | -- | Code | -- | -- | Library |
    | 3 | Heading | -- | Decision tree | -- | -- | yarn cmds | -- | "Report errors" | -- |
    | 4 | Slash cmd | -- | Spawn subagents | -- | -- | Prompts | Synthesis report | Phase 2 | -- |
    | 5 | fm | "Expert resolver" | Multi-step workflow | "NEVER skip" | Thread IDs | -- | Summary | -- | -- |
    | 6 | fm | -- | 3-step setup | -- | Problem stmt | Code | -- | CI | ConsenSys |
    | 7 | fm | -- | CI/CD patterns | -- | -- | YAML/Docker | -- | -- | -- |
    | 8 | fm triggers | -- | Dev patterns | -- | -- | Code | -- | -- | -- |
    | 9 | fm | -- | App patterns | -- | -- | TypeScript | -- | -- | -- |
    | 10 | fm | -- | API reference | -- | -- | Python | -- | -- | FRED |
    | 11 | fm + section | Writer | Style rules | Iron laws | McCloskey | Before/after | -- | -- | Book, siblings |
    | 12 | "what's next?" | -- | Search hierarchy | "Do NOT if..." | Scope explain | -- | Report fmt | -- | File paths |
    | 13 | fm | -- | 4-step workflow | -- | -- | -- | Checklist | Sanity check | blog-patterns.md |
    | 14 | fm | -- | Analyze workflow | "When NOT to" | Complements | CLI cmds | SARIF | -- | Other tools |
    | 15 | Loaded by parent | "Task executor" | 4-phase workflow | "MANDATORY" | -- | -- | Output schema | Tests | Contracts |
    | 16 | fm | -- | Tuning params | -- | Trade-offs | Configs | -- | -- | File+line |
    | 17 | -- | "Coordinator" | Backend+review | "DO NOT" x4 | "Drift" | bash | Gate result | -- | flowctl |
    | 18 | fm phrases | -- | API endpoints | -- | -- | URLs | -- | -- | GitHub repo |
    | 19 | fm | -- | Architecture | -- | -- | Code, flow | JSON schema | -- | File paths |
    | 20 | fm | -- | Capability list | -- | -- | YAML | Artifacts list | -- | Smithy tools |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Content Role Detail

    | # | Lookup | Procedure | Constraint | Notes |
    |---|--------|-----------|------------|-------|
    | 1 | Heavy | Light | -- | Capability inventory |
    | 2 | Heavy | Medium | -- | |
    | 3 | -- | Heavy | Medium | Decision-tree procedure |
    | 4 | -- | Heavy | Light | |
    | 5 | -- | Medium | Heavy | Experiential constraints |
    | 6 | Medium | Heavy | -- | |
    | 7 | Medium | Medium | -- | |
    | 8 | Heavy | Medium | -- | |
    | 9 | Medium | Medium | Light | |
    | 10 | Heavy | Medium | -- | |
    | 11 | -- | Light | Heavy | Style norms |
    | 12 | -- | Heavy | Heavy | |
    | 13 | Light | Heavy | Light | |
    | 14 | Medium | Heavy | Medium | |
    | 15 | -- | Heavy | Heavy | Compliance contracts |
    | 16 | Heavy | Medium | -- | Incl. trade-off/tuning context |
    | 17 | Light | Medium | Heavy | |
    | 18 | Heavy | Light | -- | |
    | 19 | Heavy | Medium | -- | Incl. troubleshooting context |
    | 20 | Medium | -- | -- | Capability inventory |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Replication: Batches 3--4

    To test whether the four framings developed on batches 1--2 hold on unseen data, we
    applied them to 20 additional randomly sampled skills. Two were excluded: #26 (duplicate
    content hash of #5) and #32 (no extractable content in database), leaving N=18.

    Notable features of this batch: three non-English skills (#21 Chinese, #27 Japanese, #31 French) that passed the language filter, a marketing skill (#28) with no technical
    content, and a cross-LLM audit skill (#38) that invokes Gemini to review Claude's work.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Batch 3 (seeds: 107, 109, 113, 127, 131, 137, 139, 149, 151, 157)

    | # | Repo | Skill | Words | Summary | Directive |
    |---|------|-------|-------|---------|-----------|
    | 21 | majiayu000/claude-skill-registry-data | openspec-proposal-clarifier | 567 | Chinese-language requirements clarifier with persona for OpenSpec proposals | Medium |
    | 22 | shinyorg/maui | shiny-maui-shell | 1168 | .NET MAUI Shell API reference with setup, navigation, lifecycle hooks | Low |
    | 23 | igbuend/grimbard | trivy | 1947 | Trivy security scanner reference: container/filesystem/IaC scanning | Low |
    | 24 | different-ai/openwork-enterprise | release-openwork | 306 | Patch release procedure with worktree-based workflow | Medium |
    | 25 | hotriluan/alkana-dashboard | research | 924 | 4-phase research methodology meta-skill with Gemini integration | Medium |
    | 26 | fx/cc | resolve-pr-feedback | 512 | *(Duplicate of #5 -- same normalized content hash, different repo)* | -- |
    | 27 | taku-o/go-webdb-template | test-auth-env | 94 | Japanese-language Go test auth troubleshooting (APP_ENV=test) | Medium |
    | 28 | Salesably/salesably-marketplace | positioning-angles | 943 | Marketing positioning: 8 frameworks for brand differentiation | Low |
    | 29 | majiayu000/claude-skill-registry-data | software-architecture-design | 1046 | Architecture patterns reference with decision trees and templates | Low |
    | 30 | Walshington/tripnest | clerk-auth | 2881 | Clerk auth breaking changes guide (API keys, Next.js 16, CVEs) | Low |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Batch 4 (seeds: 163, 167, 173, 179, 181, 191, 193, 197, 199, 211)

    | # | Repo | Skill | Words | Summary | Directive |
    |---|------|-------|-------|---------|-----------|
    | 31 | atournayre/claude-marketplace | init-marketplace | 914 | French-language marketplace initialization with dependency checks | Medium |
    | 32 | lubancafe/agent-skills | pptx | 4360 | *(No content in database -- likely binary or encoding issue)* | -- |
    | 33 | a5c-ai/babysitter | metrics-schema-generator | 312 | Prometheus/OpenTelemetry metrics schema generation capability listing | Low |
    | 34 | Dev-Int/tests | add-bc-contract | 445 | PHP bounded context contract pattern using Provider/Deptrac | High |
    | 35 | manusco/margin | margin-librarian | 174 | Document archiving agent ("The Archivist") for version control | Medium |
    | 36 | ayia/NutriProfile | i18n-manager | 1042 | i18n management across 7 languages including RTL Arabic | Low |
    | 37 | KyteApp/growth-agents-and-skills | compliance-check | 501 | OpenAI SDK compliance auditing with 11 named rules (A1--A11) | High |
    | 38 | cdrguru/portable-agent-kit | gemini-audit | 252 | Cross-LLM audit: validate task/plan alignment via Gemini CLI | Medium |
    | 39 | adriandarian/3Lens | testing-operations | 635 | Contract/regression/snapshot testing patterns for 3Lens platform | Medium |
    | 40 | mrpitch/ms-kanzlei | modern-best-practice-react-components | 423 | React 19+ best practices constraints (avoid useEffect, prefer derivation) | Medium |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Anatomy Detail (Batches 3--4)

    | # | Trigger | Persona | Do | Don't | Why | Examples | Output fmt | Verify | Refs |
    |---|---------|---------|-----|-------|-----|----------|-----------|--------|------|
    | 21 | fm | "Expert RA" | Analysis process | -- | Better proposals | Usage examples | Response template | -- | OpenSpec |
    | 22 | fm + triggers | "Expert" | API patterns | -- | -- | C# code | -- | -- | Docs, NuGet |
    | 23 | fm + tools | -- | Scan workflows | "When NOT" | Complements | bash cmds | -- | -- | Other tools |
    | 24 | fm | -- | Release steps | -- | -- | bash cmds | -- | -- | -- |
    | 25 | fm | -- | 4-phase research | -- | YAGNI/KISS | Report template | Report template | Quality stds | Gemini, config |
    | 27 | fm | -- | Check APP_ENV | -- | Auth skips | bash cmds | -- | -- | tech.md |
    | 28 | fm | -- | 8 frameworks | -- | -- | Templates | Defined format | Validation | Cross-refs |
    | 29 | fm | -- | Decision trees | "When NOT" | Decision factors | Trees, tables | Deliverables | -- | Extensive |
    | 30 | fm | -- | Auth patterns | -- | CVE context | TypeScript | -- | -- | Clerk docs |
    | 31 | fm | -- | 4-step init | -- | -- | bash cmds | Report | Dep checks | marketplace.json |
    | 33 | fm + tools | -- | Capabilities | -- | -- | JSON | Output schema | -- | -- |
    | 34 | fm | -- | 5-step process | -- | -- | PHP code | File structure | QA commands | Glossary, arch |
    | 35 | fm | "Archivist" | Archive workflow | -- | Philosophy | -- | Changelog | -- | margin-core |
    | 36 | fm | "i18n expert" | Translation mgmt | -- | -- | JSON, paths | -- | -- | File paths |
    | 37 | fm | -- | 5-step audit | Anti-patterns | -- | -- | Report schema | Severity stops | Checklist, rules |
    | 38 | fm | -- | Audit procedure | -- | -- | bash cmds | APPROVE/REJECT | Decision | File paths |
    | 39 | fm | -- | Test patterns | -- | -- | TypeScript | -- | MUST reqs | Playbook, rules |
    | 40 | fm | -- | Best practices | "AVOID" x6 | Principles | TSX code | -- | -- | useEffect guide |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Content Role Detail (Batches 3--4)

    | # | Lookup | Procedure | Constraint | Notes |
    |---|--------|-----------|------------|-------|
    | 21 | Light | Heavy | Medium | Chinese-language, persona-driven |
    | 22 | Heavy | Medium | -- | API reference with setup |
    | 23 | Heavy | Medium | Light | "When NOT to use" guardrails |
    | 24 | Medium | Heavy | -- | |
    | 25 | -- | Heavy | Medium | 5-research cap |
    | 27 | Medium | Light | Medium | Troubleshooting |
    | 28 | Heavy | Medium | Light | 8 framework descriptions |
    | 29 | Heavy | Medium | Light | |
    | 30 | Heavy | Medium | Light | Version-specific |
    | 31 | Medium | Heavy | Light | |
    | 33 | Heavy | Light | -- | Capability inventory |
    | 34 | Medium | Heavy | Heavy | Compliance contracts |
    | 35 | -- | Heavy | Light | |
    | 36 | Heavy | Medium | Light | |
    | 37 | Medium | Heavy | Heavy | 11 named rules |
    | 38 | Light | Heavy | Light | |
    | 39 | Heavy | Medium | Medium | Incl. MUST requirements |
    | 40 | Medium | -- | Heavy | Constraint-first |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Replication Results

    How the framings held up across both batches:

    #### Anatomy

    | Component | Batch 1--2 (N=20) | Batch 3--4 (N=18) | Combined |
    |-----------|:-----------------:|:-----------------:|:--------:|
    | Trigger | 19/20 | 18/18 | 37/38 |
    | Persona | 4/20 | 4/18 | 8/38 |
    | What to do | 20/20 | 18/18 | 38/38 |
    | What not to do | 6/20 | 5/18 | 11/38 |
    | Why | 6/20 | 7/18 | 13/38 |
    | Examples | 16/20 | 16/18 | 32/38 |
    | Output format | 6/20 | 10/18 | 16/38 |
    | Verification | 5/20 | 7/18 | 12/38 |
    | References | 13/20 | 16/18 | 29/38 |

    The "core four" from batch 1--2 (trigger, what-to-do, examples, references) remain
    the most common components. Output format and verification appeared more often in
    batch 3--4 (56% and 39%) than batch 1--2 (30% and 25%). With N=18, this could be
    sampling variance rather than a real difference. Persona remained rare in both
    samples (~20%).

    #### Content Role

    | Primary role | Batch 1--2 | Batch 3--4 |
    |-------------|:----------:|:----------:|
    | Lookup | 8/20 | 8/18 |
    | Procedure | 6/20 | 7/18 |
    | Constraint | 1/20 | 1/18 |
    | Mixed | 5/20 | 2/18 |

    The lookup-procedure-constraint trichotomy applied without difficulty to all 18 new
    skills. The distribution is stable: lookup and procedure are the two dominant roles,
    pure constraint skills are rare, and many skills blend roles.

    #### Directive Force

    | Level | Batch 1--2 | Batch 3--4 |
    |-------|:----------:|:----------:|
    | Low | 10/20 | 7/18 |
    | Medium | 6/20 | 9/18 |
    | High | 4/20 | 2/18 |

    The three levels were easy to assign. The new batch has more medium-force skills and
    fewer at the extremes. No anti-evasion language or rationalization tables appeared in
    batch 3--4's high-directive skills (#34, #37), suggesting that the co-occurrence of
    anti-evasion + high-directive observed in batch 1--2 may be specific to certain authors
    or communities rather than a general pattern.

    #### Provenance

    | Origin | Batch 1--2 | Batch 3--4 |
    |--------|:----------:|:----------:|
    | Doc-extracted | ~8/20 | 3/18 |
    | Experience-encoded | ~6/20 | 10/18 |
    | Generated/templated | ~6/20 | 5/18 |

    The three categories remained assignable but the distribution shifted. Batch 3--4
    has proportionally more experience-encoded skills. The correlation between
    experience-encoded provenance and high directive force, observed in batch 1--2
    (4 of 6 experience-encoded were high-directive), did **not** replicate: only 2 of 10
    experience-encoded skills in batch 3--4 were high-directive. This suggests the earlier
    observation was coincidental.

    #### New observations from batch 3--4

    - **Non-English content passes the English filter.** Three skills (#21 Chinese,
      #27 Japanese, #31 French) had substantial non-English text. The frontmatter was
      English-tagged but the body content was not. The language detection in notebook 01
      may undercount non-English skills.
    - **Non-technical domains.** Skill #28 (positioning-angles) is a marketing framework
      with no code, no technical stack, and no developer audience. The framings applied
      without modification -- it has lookup content role, low directive force, and
      generated provenance.
    - **Cross-LLM patterns.** Skill #38 (gemini-audit) uses Gemini to audit work done
      by Claude. This "second opinion" pattern has no analog in batch 1--2.
    - **Duplicate detection.** #26 was a content-hash duplicate of #5 from a different repo,
      confirming that the deduplication in notebook 01 correctly collapses these.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Category: Tags

    The framings above describe *how* a skill is structured and *how* it communicates.
    But they don't capture *what the skill is about*. A strict taxonomy
    (automation / guidance / meta / enforcement) was the original plan, but close
    reading showed that skills routinely span categories. A **flat tag set** is more
    honest.

    Tags are drawn from three pools. A skill can have any combination:

    **Activity tags** -- what the agent does:

    | Tag | Description |
    |-----|-------------|
    | `reference` | Passive information the agent draws on |
    | `process` | Defined workflow or procedure to execute |
    | `setup` | One-time scaffolding or project initialization |
    | `configuration` | Adjusting knobs, tuning parameters |
    | `orchestration` | Coordinating multiple agents or tasks |
    | `rules` | Normative constraints on behavior |

    **Domain tags** -- subject area:

    | Tag | Description |
    |-----|-------------|
    | `dev-workflow` | Git, PRs, CI, linting, testing |
    | `frontend` | Web UI, React, design systems |
    | `mobile` | React Native, Expo, iOS/Android |
    | `embedded` / `hardware` | Firmware, logic analyzers, IoT |
    | `security` | Audits, vulnerability scanning, access control |
    | `writing` | Prose, style guides, content creation |
    | `data-api` | External data sources, REST APIs |
    | `ai-pipeline` | LLM chains, fact-checking, embeddings |
    | `agent-meta` | Skills about agent behavior itself |
    | `blockchain` | On-chain content, smart contracts |

    **Stack tags** -- specific technology (open-ended):

    `react`, `nextjs`, `expo`, `typescript`, `python`, `esp-idf`, `freertos`,
    `foundry`, `solidity`, `github-actions`, `docker`, `langgraph`, `groq`,
    `yarn`, `dotnet`, `aws`, `bsv`, ...

    **Modifier tags** -- cross-cutting properties:

    | Tag | Description |
    |-----|-------------|
    | `anti-evasion` | Contains rationalization tables or counter-arguments |
    | `generated` | Appears templated or auto-generated |
    | `multi-agent` | Spawns or coordinates sub-agents |
    | `decision-tree` | Branch logic based on conditions |
    | `delegation` | Hands off to another tool or agent |

    ### Tags for All 20 Skills

    | # | Skill | Tags |
    |---|-------|------|
    | 1 | frontend-analyzer | `reference`, `frontend`, `react`, `nextjs`, `design-tokens`, `generated` |
    | 2 | logicmso | `reference`, `hardware`, `protocol-decoding`, `ctf`, `python` |
    | 3 | lint-build-test | `process`, `dev-workflow`, `monorepo`, `yarn`, `decision-tree` |
    | 4 | understand | `orchestration`, `agent-meta`, `code-analysis`, `multi-agent` |
    | 5 | resolve-pr-feedback | `process`, `dev-workflow`, `git`, `pr-review`, `anti-evasion` |
    | 6 | security-framework | `setup`, `security`, `smart-contracts`, `solidity`, `foundry` |
    | 7 | cicd-devops | `reference`, `dev-workflow`, `github-actions`, `docker`, `ci-cd` |
    | 8 | ESP32 firmware | `reference`, `embedded`, `hardware`, `esp-idf`, `freertos`, `cpp` |
    | 9 | react-native | `reference`, `mobile`, `react-native`, `expo`, `typescript` |
    | 10 | fred-economic-data | `reference`, `data-api`, `economics`, `python` |
    | 11 | writing-econ | `rules`, `writing`, `economics`, `style-guide`, `anti-evasion` |
    | 12 | next | `process`, `agent-meta`, `task-management` |
    | 13 | blog-writer | `process`, `writing`, `content-creation`, `nextjs`, `seo` |
    | 14 | application-inspector | `process`, `security`, `code-analysis`, `dotnet` |
    | 15 | task-module_testing | `process`, `testing`, `agent-meta`, `workflow-system` |
    | 16 | fact-check-tuner | `configuration`, `ai-pipeline`, `langgraph`, `tuning` |
    | 17 | flow-plan-review | `process`, `dev-workflow`, `code-review`, `delegation`, `anti-evasion` |
    | 18 | ordfs | `reference`, `blockchain`, `api`, `bsv` |
    | 19 | attuned-ai-activities | `reference`, `ai-pipeline`, `groq`, `llama`, `architecture` |
    | 20 | smithy-sdk-generator | `reference`, `code-generation`, `aws`, `sdk`, `generated` |

    ### Tag Frequency (activity + domain only)

    | Tag | Count | Skills |
    |-----|-------|--------|
    | `reference` | 9 | #1, 2, 7, 8, 9, 10, 18, 19, 20 |
    | `process` | 7 | #3, 5, 12, 13, 14, 15, 17 |
    | `dev-workflow` | 4 | #3, 5, 7, 17 |
    | `security` | 2 | #6, 14 |
    | `agent-meta` | 3 | #4, 12, 15 |
    | `writing` | 2 | #11, 13 |
    | `hardware` | 2 | #2, 8 |
    | `ai-pipeline` | 2 | #16, 19 |
    | `anti-evasion` | 3 | #5, 11, 17 |
    | `generated` | 2 | #1, 20 |

    In this sample, `reference` (9/20) and `process` (7/20) were the most common
    activity tags. Domain tags were more evenly distributed, with `dev-workflow` (4/20) most
    frequent.

    Tags are more useful than a strict taxonomy because a skill like #17
    (flow-plan-review) is simultaneously `process` + `dev-workflow` + `code-review` +
    `delegation` + `anti-evasion`. Forcing it into a single category loses information.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Observation: Inter-Skill Dependencies

    Some skills are not self-contained units -- they participate in dependency relationships
    with other skills or tools. Four of the 20 sampled skills exhibited this, each with a
    different structural relationship:

    | Relationship | Direction | Observed in | Mechanism |
    |-------------|-----------|-------------|-----------|
    | **includes** | Skill loads sibling skill | #11 writing-econ | `includes:` frontmatter loads writing-general |
    | **loaded-by** | Skill is loaded by parent | #15 task-module_testing | Parent skill invokes this as a module |
    | **delegates-to** | Skill hands off to external tool | #17 flow-plan-review | Delegates review execution to RepoPrompt |
    | **spawns** | Skill creates sub-agents | #4 understand | Spawns 4--7 parallel analysis agents |

    These relationships mean the individual skill file is not always the right unit
    of analysis. Skills #11 (writing-econ) and #15 (task-module_testing) are nodes in
    an explicit dependency graph. Skill #17 (flow-plan-review) depends on an external
    tool. Skill #4 (understand) is a coordinator whose output depends on sub-agent
    behavior.

    **Prevalence is unknown.** 4/20 showed inter-skill relationships, but the
    sample is too small to generalize. The `includes:` frontmatter field and references to
    other skill files could be detected programmatically across the full dataset -- this is
    a candidate for the quantitative notebook.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Limitations

    Combined sample is N=38 (20 development + 18 replication). Even with replication,
    differences of a few skills between categories are not meaningful; the value is in
    developing and stress-testing framings, not estimating population distributions.
    All analysis is one coder's judgment with no inter-rater check. Simultaneous coding
    across dimensions risks unconscious coherence -- a single researcher developing and
    applying framings may create narratives that appear to hold together without actually
    doing so. The batch 1--2 provenance/directive-force correlation (4/6 experience-encoded
    were high-directive) did not replicate in batch 3--4 (2/10), illustrating how small
    samples produce spurious patterns. Three non-English skills passed the English
    language filter, suggesting the deduplicated English set is not strictly English.
    Public repos discoverable via GitHub search represent a specific subset, not all skills
    in the wild.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Open Questions

    Grouped by what's needed to address them.

    ### Testable with current dataset

    1. **How common are multi-skill systems?** 4 of 20 sampled skills had inter-skill
       relationships (includes, loaded-by, delegates-to, spawns). The `includes:`
       frontmatter field and cross-skill references could be detected programmatically.
    2. **Can provenance be detected automatically?** Repo file paths, structural similarity,
       and upstream doc overlap are candidate heuristics but none have been validated.
    3. **Is the (activity, domain, stack) tuple the right category decomposition?** Or
       should it be a flat tagging system?

    ### Require evaluation data (notebook 03)

    4. **Does anatomy completeness correlate with agent performance?** The 4 common
       components (trigger, what-to-do, examples, references) vs. the 5 rarer ones
       could be compared.
    5. **Does directive force affect step-completion rates?** High-directive skills
       (#5, #11, #15, #17) vs. low-directive ones.
    6. **Does provenance correlate with accuracy?** Doc-extracted, experience-encoded,
       and generated skills may differ in how well agents follow them.
    7. **Does content role correlate with failure mode?** Lookup-heavy vs. constraint-heavy
       vs. procedure-heavy skills may produce different kinds of agent errors.
    8. **Do activity and domain tags interact with other framings?** E.g., do `process`
       skills differ from `reference` skills in which anatomy components are present?

    ### Require expanded sample

    9. **What's the distribution of directive force across the full dataset?** Batch 1--2
       showed 10/6/4 (low/medium/high); batch 3--4 showed 7/9/2. The combined 17/15/6
       is suggestive but too small to generalize.
    10. **Are there framings we're still missing?** N=38 surfaced non-technical skills
        (#28 marketing) and cross-LLM patterns (#38) absent from batch 1--2, suggesting
        more categories may emerge with larger samples.
    """)
    return


if __name__ == "__main__":
    app.run()
