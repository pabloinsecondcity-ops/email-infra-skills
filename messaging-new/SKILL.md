---
name: messaging-new
description: >-
  Use when someone says build messaging for new client or new client campaign:
  the full messaging build for a brand new client, ICP intelligence through
  Smartlead campaign creation, with explicit confirmation at every step.
---
# Skill: messaging-new

**Trigger:** "build messaging for new client" / "new client campaign"

**Who runs this:** AM during client onboarding (month 1). Full build from scratch.

**What it does:** Complete messaging build for a brand new client, ICP intelligence through Smartlead campaign creation. Every step needs explicit confirmation. Never skip. Never combine.

---

## Before you start

Read `clients/[folder]/onboarding.md` (ICP, offer, pain points, signals, list sources) and `clients/[folder]/icp.md`. If either is missing, stop and say so.

Ask the AM: "Do you have any winning emails from a similar past client to use as examples?" If yes, paste them in before Step 0A.

---

## STEP 0A. ICP intelligence

Output: their day-to-day and responsibilities; top 2-3 problems this client solves; what they've tried and why it failed; what they're skeptical of and what makes them delete cold emails; what would make them respond; the language they use for the problem (onboarding form, transcripts, G2, Reddit).

**Approval gate:** AM confirms the ICP profile.

---

## STEP 0B. Offer development

1. **Diagnostic question**: the one question that makes a qualified prospect think "actually... I'm not sure." Pointed and specific, not a generic pain question.
2. **Offer framing**, by tier: Tier 1 true industry data, video, audit with named deliverables, free trial/hands-on demo; Tier 2 binary CTAs (if no compelling offer); Tier 3 last resort.

**Approval gate:** AM confirms both.

---

## STEP 1. Segmentation

Minimum viable segments, target 2, max 3. Only segment when messaging must genuinely change. For each: who (title + company type), why messaging differs, hook framework (Observation / Social proof / Diagnostic question / Poke the bear), list source.

Same pain + same value prop + same hook = one segment; use `{{custom_fields}}` for variation.

**Approval gate:** AM confirms segments before any copy.

---

## STEP 2. Messaging

**Email 1, 4 variants:** A under 120 words full structure (hook + problem + value prop + CTA); B under 60, stripped down, lead with diagnostic question or offer; C under 120, different hook framework than A; D under 60, different angle than B (try fourth-wall or binary CTA).

**Email 2:** one sentence, colleague referral only: "Hey {{first_name}}, would it make more sense to reach out to {{colleague_name}} about this?"

**Email 3:** 1-2 sentences, specific offer or resource from the onboarding form. No compelling offer means flag to AM first. No placeholder.

**Subject lines:** 1-3 words, lowercase, no question marks or exclamation points.

Hard rules: no em dashes; no "Quick question."; no homepage copy; intentional imperfection is a feature.

**Approval gate:** AM reviews before self-QA.

---

## STEP 3. Self-QA

Per Email 1 variant, pass/fail:
- [ ] Could a competitor say the same value prop? If yes, rewrite.
- [ ] Hook applies to 5,000 people or feels specific?
- [ ] Problem sounds like the prospect describing it to a peer?
- [ ] CTA Tier 1 or 2? Flag Tier 3.
- [ ] Em dashes, "Quick question.", homepage copy?
- [ ] Word count within spec?
- [ ] Email 3 has a real offer?

Fix failures before the AM sees it.

---

## STEP 4. AM review

AM edits directly and pastes back the final approved version. No spintax until then.

---

## STEP 5. Spintax

Approved copy only. Format `{option A|option B|option C}`. Apply to greeting `{Hi|Hey|Hello} {{first_name}}`, hook opening (2-3 variations), one value prop phrase, CTA (2-3 variations). Not to `{{custom_fields}}`, `{{AI: ...}}` prompts, core problem statement, subject lines, Email 2 or Email 3.

**Approval gate:** AM confirms before Smartlead upload.

---

## STEP 6. Signal campaigns

Read `knowledge/campaign-archive.md`, cross-reference onboarding signals. For each signal (job postings, G2 intent, competitor users, new to role, website visitors): one-line idea with signal source, who to target, hook angle. AM picks now vs later. Flag any needing a different list build.

---

## STEP 7. LinkedIn messaging

After email is approved:
- **Connection request:** blank.
- **Message 1** (after accept): 1-2 sentences, open-ended question tied to the diagnostic angle, casual, lowercase.
- **Message 2** (3 hours later): a visual, PDF, Loom or link, one sentence of context max.
- **Message 3** (soft bump): casual check-in referencing something specific; offer a short video.

Write like texting a smart colleague; lowercase; never "Thanks for connecting!", "Came across your profile", or a calendar link first.

**Approval gate:** AM confirms before HeyReach upload.

---

## STEP 8. Create in Smartlead

**Not until the client approves the messaging.** `POST /campaigns/create` per segment.

| Setting | Value |
|---|---|
| Daily send limit | 1,000 |
| Sending schedule | 8am - 6pm EST, Mon - Fri |
| Timezone | America/New_York |
| Email sequence | 3 emails, 2 days between each |
| Tracking | Plain text, no open or click tracking |
| Follow-up / new lead split | 20% / 80% |
| Smart categorization | On |
| OOO re-categorization | On |

**Naming:** `[Client]: [Persona] | [Company] | [Differentiator] | [Type]`. Only slots that add information; never "All Personas" or "All Company Types."

**After creating:** confirm the returned campaign ID, report name and URL to the AM. Do not upload leads; that's the GTME's job.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key). Verified reads: `GET /campaigns/{id}`, `/analytics`, `/sequences`.
- Creating campaigns or saving sequences is a write and not verified here; only on Pablo's explicit approval. HeyReach is not connected.
- `clients/`, `knowledge/` and `context/` files are in the pp-gtm repo, not on the box; ask Pablo for the content first.
- Never invent facts or names. No em dashes.
