---
name: review-session
description: >-
  Use when someone says review this session, what broke today, or improve the
  skills: read the session transcript, find where things went wrong, map
  failures to skills or rules, and propose prioritized fixes.
---
# Skill: review-session

**Trigger:** "review this session" / "what broke today" / "improve the skills"

**Who runs this:** Jed or any team member at the end of a working session.

**What it does:** Reads the session transcript, finds every place something went wrong or needed correction, maps failures to specific skills or rules, and outputs a prioritized list of proposed improvements ready to apply.

---

## Before you start

Identify the session to review. If the user says "review this session," use the current one. If they name a session or date, find the matching one by timestamp.

---

## STEP 1. Read the session transcript

Read the full conversation: what the user said, what the assistant did, tool calls and their results. Build a picture of what was attempted, what succeeded, what didn't.

---

## STEP 2. Find every failure signal

**Explicit corrections:** user said "no," "wrong," "that's not right," "wait," "stop," "actually"; rephrased the same request more than once; had to clarify something obvious from context.

**Tool failures:** a call errored and needed a retry or workaround; an approach failed and was switched; a script ran but produced wrong output.

**Workarounds:** something done manually that should have been automated; a step skipped or combined when the skill said not to; asking for info that should have been in a context file.

**Quality misses:** em dashes; summarizing instead of acting; asking instead of acting when direction was clear; output not matching the skill's format.

**Approval gate misses:** proceeding past a gate without explicit confirmation; pushing to Smartlead or HeyReach before approval.

For each instance note what happened, where in the session (early, mid, late), and how the user had to correct it.

---

## STEP 3. Map each failure to its source

- **Missing from a skill:** scenario or edge case not covered
- **Wrong in a skill:** the skill said X and X was incorrect
- **Missing from global rules:** a behavioral rule that should apply everywhere (on Grok Bot, the bot's memory/profile)
- **Missing from a context file:** info that should have been in `clients/[folder]/icp.md` or `context.md`
- **One-off:** user error or genuinely unpredictable, no change needed

Group by source. The file with the most failures needs the most work.

---

## STEP 4. Output the review

```
Session Review -- [date]
What we built: [1-2 sentences]
Failures found: [N]

[skill name] -- 2 issues
Issue 1: [what happened, one sentence]
Root cause: [why, e.g. Step 4 doesn't say what to do when the client has no case studies]
Proposed fix: [exact text to add or change]

[global rules] -- 1 issue
Issue 1: asked for the client folder instead of checking clients/registry.md first
Root cause: no rule requires the registry lookup
Proposed fix: add "Always check clients/registry.md before asking which client folder to use"

[One-off -- no fix needed] -- 1 instance
[why no change is needed]

Recommended priority:
1. [highest impact, apply now]
2. [second]
3. [can wait]
```

---

## STEP 5. Apply fixes (with confirmation)

Ask: "Want me to apply any of these now? Tell me which numbers and I'll update the files directly."

If confirmed: make exactly the specified changes to exactly those skills or files, surgically, then report "Done. [N] fixes applied to [list]." If not confirmed, stop.

---

## HARD RULES

1. Never invent failures not in the transcript
2. Proposed fixes must be specific and immediately applicable
3. One sentence per issue
4. Never update more than what was identified, no bonus cleanup
5. Ambiguous failures (skill or user?) get "unclear -- needs judgment" and no proposed fix
6. No em dashes anywhere; use -- instead

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- The original read Claude Code `~/.claude/projects/...jsonl` transcripts, which don't exist on the box. Here, review the current conversation (and earlier ones via ReadTranscript if available) plus the saved skills.
- Skill edits go through UpdateSkill, memory edits through UpdateMemory, and only after Pablo approves the numbered fixes.
