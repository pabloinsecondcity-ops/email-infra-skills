---
name: messaging-campaign
description: >-
  Use when an AM says new campaign for [client] or build a campaign for [client]
  for an existing client: segmentation through Smartlead campaign creation,
  confirming each step before moving on.
---
# Skill: messaging-campaign

**Trigger:** "new campaign for [client]" / "build a campaign for [client]"

**Who runs this:** AM when an existing client needs a new campaign. Context already exists, so skip the ICP/offer build.

**What it does:** Builds a new campaign for an existing client, segmentation through Smartlead creation. Faster than `messaging-new` because onboarding context is already in the client folder. All steps still require confirmation before moving forward.

---

## Before you start

Read `clients/[folder]/onboarding.md`, `clients/[folder]/icp.md`, and `clients/[folder]/context.md` (current campaign status, what's been tried, what's working).

Ask the AM for the campaign brief:
1. **Target segment**: titles, company type, size, vertical
2. **What's different**: why a new campaign vs an iteration (new persona, signal, angle, list source?)
3. **Signal or list source**: where the leads come from
4. **Constraints**: anything to avoid based on what's been tried

Do not proceed until all four are answered.

---

## STEP 1. Segmentation

Read `knowledge/campaign-archive.md`. Check which campaign types have run for this client (from `context.md`). Start with Consistent performers not yet tried.

Propose segments, target 2, max 3. For each: who it targets (title + company type), why messaging differs, best hook framework given what's been tried, list source (per campaign-archive.md).

Don't repeat a losing angle; flag it if the AM steers toward one.

**Approval gate:** AM confirms segments before writing.

---

## STEP 2. Messaging

For each approved segment:

**Email 1, 4 variants:**
- A: under 120 words, full structure (hook + problem + value prop + CTA)
- B: under 60 words, lead with diagnostic question or offer
- C: under 120 words, different hook than A
- D: under 60 words, different angle than B

**Email 2:** one sentence, colleague referral only.

**Email 3:** 1-2 sentences, specific offer or resource from the onboarding form. If no compelling offer exists, flag to AM. No placeholder.

**Subject lines:** 1-3 words, lowercase, no punctuation.

Hard rules: no em dashes; no "Quick question."; no homepage copy; word counts (A/C under 120, B/D under 60, Email 3 under 50); intentional imperfection is a feature.

**Approval gate:** AM review before self-QA.

---

## STEP 3. Self-QA

For each Email 1 variant:
- [ ] Value prop: could a competitor say the same thing?
- [ ] Hook: specific to this person, or generic?
- [ ] Problem: prospect's language, not marketing language?
- [ ] CTA tier: Tier 1 or 2? Flag Tier 3.
- [ ] Hard rules clean?
- [ ] Word count within spec?
- [ ] Email 3 has a real offer?

Fix failures before showing the AM.

**Approval gate:** AM reviews, edits, pastes back the approved version.

---

## STEP 4. Spintax

AM-approved copy only. Apply to: greeting `{Hi|Hey|Hello} {{first_name}}`; hook opening (2-3 natural variations); one value prop phrase; CTA (2-3 variations).

Do NOT apply to `{{custom_fields}}` or `{{AI: ...}}` prompts, the core problem statement, subject lines, Email 2 or Email 3.

**Approval gate:** AM confirms before Smartlead upload.

---

## STEP 5. Create in Smartlead

**Do not run until the client has approved the messaging.** Create each campaign via `POST /campaigns/create`.

| Setting | Value |
|---|---|
| Daily send limit | 1,000 |
| Sending schedule | 8am - 6pm EST, Mon - Fri |
| Timezone | America/New_York |
| Email sequence | 3 emails, 2 days between each |
| Tracking | Plain text, no open or click tracking |
| Follow-up / new lead split | 20% follow-up, 80% new |
| Smart categorization | On |
| OOO re-categorization | On |

**Naming:** `[Client]: [Persona] | [Company] | [Differentiator] | [Type]`. Check existing names; a second version of a segment gets V2 (V3, etc.). A re-engagement of a full TAM uses the Re-Engage tag.

**After creating:** report campaign name and Smartlead URL to the AM. Do not upload leads; that is the GTME's job.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key). Verified reads: `GET /campaigns/{id}`, `/analytics`, `/sequences`.
- Creating campaigns or saving sequences is a write and not verified here; only on Pablo's explicit approval. HeyReach is not connected.
- `clients/`, `knowledge/` and `context/` files are in the pp-gtm repo, not on the box; ask Pablo for the content first.
- Scratch output goes to `/workspace/`. Never invent facts or names. No em dashes.
