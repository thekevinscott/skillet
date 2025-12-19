# Documentation Strategy

A conversation about how to document skillet. Formatted as a log to preserve the reasoning chain, not just conclusions.

----------

**Human:** Skillet doesn't fit the traditional "getting started" documentation model.

----------

**Claude:** Three reasons why:

1. **No standalone value** - You can't "get started" with skillet without already having a skill you want to improve
2. **Value is in the process** - The library teaches a methodology (eval-driven development), not just commands
3. **Best practices ARE the product** - Understanding when and why to use skillet is more important than knowing CLI syntax

----------

**Human:** The concept of "getting started" doesn't really apply here. A lot of the value comes from showing best practices, walking through an end-to-end example.

----------

**Claude:** Traditional tutorials say "follow these steps to build X". But with skillet:

- You need an existing skill to evaluate
- The "project" is improving Claude's behavior
- Success depends on your specific use case

If you tried a traditional tutorial:

> "Step 1: Create a skill"
>
> ...but what skill? The user's context matters enormously.

----------

**Human:** Examples are necessarily verbose; documentation should be simple and to the point. Importantly, it should clearly communicate *why it matters*.

----------

**Claude:** This is the key tension. We're proposing verbose examples as the primary learning path, but that creates friction. The bridge:

- **Documentation** (index, how-to) stays concise - tells you *what* skillet does and *why* you'd care
- **Examples** are verbose by design - shows you *how* through complete walkthroughs
- The documentation's job is to motivate diving into the examples

Users won't read a 200-line walkthrough unless they first understand why it's worth their time. So the landing page must nail the "why" in a few sentences, then point to examples for the "how".

----------

**Human:** It's the comparison that really delivers the message. Understanding how you'd do this *without* something like skillet proves the need for skillet.

----------

**Claude:** Yes - the "before" is as important as the "after". Without showing the pain of manual iteration:

1. Run Claude on a task
2. Notice it fails
3. Tweak the skill
4. Run Claude again
5. Did it improve? Hard to tell without tracking
6. Repeat until... when? How do you know you're done?

...users won't appreciate what skillet provides: captured evals, baseline scores, measurable improvement, reproducibility.

The examples should show this contrast explicitly. Not just "here's how to use skillet" but "here's the manual slog, and here's how skillet replaces it."

----------

**Human:** Given that we want users to onboard quickly and understand the value prop quickly - what are our options? DSPy may be a good template here.

----------

**Claude:** DSPy does this well:

1. **Landing page hero**: One sentence paradigm shift ("Programming—not prompting—language models")
2. **Minimal code comparison**: ~10 lines showing before/after
3. **Immediate "aha"**: You see the value before you install anything

For skillet, I lean toward a hybrid:
- Hero with one-liner value prop
- Side-by-side CLI comparison (5 lines each)
- "Pick an example" links for deep dives

----------

**Human:** Side-by-side comparisons for each use case sounds good - left shows no skillet, right shows skillet. But I'm still concerned about users who want to get started quickly.

----------

**Claude:** Maybe the answer is reframing what "quick" means:

**Traditional "Getting Started"**: Install → Hello World → You're ready!
**Skillet "Getting Started"**: Install → Pick a use case → See the workflow in action

The difference: we don't pretend there's a generic first step. "Quick" means 3 commands to see value - but those 3 commands need context.

----------

**Human:** The big problem is on a cold start, there are no existing evals.

----------

**Claude:** Right. The cold start problem is the real onboarding challenge:

1. User has a skill
2. Skill sometimes works, sometimes doesn't
3. User installs skillet
4. Runs `skillet eval` → "No evals found"
5. Now what?

The honest answer: the first eval comes from real usage, not upfront authoring. The real "getting started" is:

1. Use Claude with your skill
2. It fails
3. Capture the failure with `/skillet:add`
4. Now you have an eval

Skillet's job is to capture and systematize failures you're already experiencing.

----------

**Human:** That's necessarily an offline experience. How does a docs site integrate with that? Maybe an interactive playground? Run Claude Code on the web?

----------

**Claude:** The core tension: the best onboarding is *using the tool in your real environment*, but docs need to work before installation.

----------

**Human:** Why can't we build it? Claude Code has a JS SDK.

IN FACT: we could have the docs be live response. Terminal on the right, docs/conversation on the left. The docs are somewhat static, but as the user types, the docs live update - nudging the user to "capture that!" as an eval.

----------

**Claude:** This is a genuinely novel idea. Not just "interactive docs" but *reactive docs* - documentation that watches what you're doing and responds.

```
┌─────────────────────────────────┬─────────────────────────────────┐
│         LIVE DOCS               │          TERMINAL               │
│                                 │                                 │
│  Welcome to skillet!            │  $ claude                       │
│                                 │  > Help me write a commit msg   │
│  I see you're using Claude...   │                                 │
│                                 │  Claude: Here's a commit:       │
│  Claude gave a generic commit   │  "Updated files"                │
│  message. Let's capture this    │                                 │
│  as an eval.                    │                                 │
│                                 │                                 │
│  👉 [Show me]                   │                                 │
│                                 │                                 │
└─────────────────────────────────┴─────────────────────────────────┘
```

----------

**Human:** Maybe instead of asking - it's a [Show me] button that takes over typing for you.

----------

**Claude:** Even better. The user watches it happen:

```
┌─────────────────────────────────┬─────────────────────────────────┐
│         LIVE DOCS               │          TERMINAL               │
│                                 │                                 │
│  Watch: I'm running the         │  $ /skillet:add                 │
│  capture command...             │  > What was wrong?              │
│                                 │  │ (typing...) "Should use      │
│                                 │    conventional commits"        │
│                                 │                                 │
│  ✓ Eval saved to:               │  ✓ Created evals/commit/001.yaml│
│    evals/commit/001.yaml        │                                 │
│                                 │                                 │
│  Now you have your first eval.  │                                 │
│  Next: let's run it.            │                                 │
│                                 │                                 │
│  👉 [Show me]                   │                                 │
│                                 │                                 │
└─────────────────────────────────┴─────────────────────────────────┘
```

Each [Show me] advances the lesson:

1. [Show me] → captures the failure as an eval
2. [Show me] → runs `skillet eval`
3. [Show me] → runs `skillet tune`
4. [Show me] → runs eval again, shows improvement

The user learns by watching real commands execute in real-time. At any point they can take over and type themselves.

- **Passive learners**: Click through [Show me] buttons
- **Active learners**: Take over the terminal whenever they want
- **Everyone**: Sees real output, not canned examples

This could be a differentiator. No one else has "docs that pair program with you."

----------

**Human:** User would have to bring their own key. *Or* use a client-side LLM.

----------

**Claude:** Two paths:

**Option A: BYOK (Bring Your Own Key)**
- User enters their Anthropic API key
- Stored locally, never sent to our servers
- Full Claude experience
- Drawback: Friction at start

**Option B: Client-side LLM**
- Run Llama/Mistral in the browser (WebLLM, Transformers.js)
- Zero cost, zero API key needed
- Drawback: Won't behave exactly like Claude

**Option C: Hybrid**
- Start with client-side LLM for the tutorial
- Prompt: "Ready for real work? Enter your API key."
- Client-side gets them through onboarding, then they upgrade

The client-side model doesn't need to be good at following skills. It just needs to be *bad enough* to generate failures worth capturing. That's actually easy.

----------

## Summary

The documentation strategy:

1. **Landing page**: Hero + side-by-side comparison (with/without skillet)
2. **Primary learning path**: Reactive docs with live terminal
3. **[Show me] buttons**: Docs execute commands while user watches
4. **Cold start solved**: Client-side LLM generates failures to capture
5. **Upgrade path**: BYOK when ready for real Claude

The key insight: docs shouldn't just describe the workflow - they should *be* the workflow.
