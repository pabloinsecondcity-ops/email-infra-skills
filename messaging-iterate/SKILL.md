---
name: messaging-iterate
description: >-
  Use when someone says iterate on [client] campaign, campaign isn't working, or
  review [client] performance: diagnose, walk the iteration checklist in
  priority order, write new variants, and push changes to Smartlead only after
  the AM approves each gate.
---
# Skill: messaging-iterate

**Trigger:** "iterate on [client] campaign" / "campaign isn't working" / "review [client] performance"

**Who runs this:** AM during the 2-day review cycle when a campaign is underperforming or flagged in the command center.

**What it does:** Diagnoses what's wrong, walks the iteration checklist in priority order, writes new variants or changes, and pushes updates to Smartlead. The AM makes the judgment call at each gate.

---

## Before you start

Read `clients/[folder]/context.md` and `clients/[folder]/onboarding.md`.

Ask the AM: 1. Which campaign(s)? 2. What signal triggered this (command center flag, gut feel, client feedback)? 3. Current stats (reply rate, positive reply rate, emails sent, leads remaining)? 4. What's already been tried?

If from the command center, identify the AMTDUTS flag:
- **Review**: new campaign, 2 days in, decide kill / iterate / scale
- **No positive replies**: 2+ days without a positive reply
- **No activity**: no new campaigns, variants, or list uploads
- **Variant winner**: one variant outperforming another

---

## STEP 1. Deliverability check (fix before messaging)

- [ ] 95%+ inbox health?
- [ ] 1,000+ emails/day sending? (Target 3,000/day)
- [ ] HeyReach accounts sending 30+ LinkedIn messages/day?
- [ ] Bounce rates below 5%?

**Any no:** stop and flag the deliverability issue. Do not iterate on messaging until infrastructure is healthy; that is the most common mistake. **All yes:** go to Step 2.

---

## STEP 2. Targeting check

Right job titles? Right company types? Any pattern in who replied positively vs not (title, size, vertical, geography)?

**Off:** recommend a list build change, flag to Pablo/Jaimin via #list-requests, note in `context.md`. **Right:** go to Step 3.

---

## STEP 3. Messaging diagnosis

Read the email as the prospect: what would confuse me, what sounds not believable, what sounds AI or templated? Work the tiers in order; Tier 1 is almost always the issue.

**Tier 1 (start here):**
- **Pain point:** prospect's language or marketing language? Pull from onboarding form, call transcripts, G2 reviews. If the pain framing is off, nothing else matters.
- **Value prop:** specific enough to be believable? Explains HOW? Could a competitor say the same sentence?
- **Offer/CTA:** real offer or generic? Generic PDFs and "learn more" are dead. No compelling offer means binary CTA.

**Tier 2:**
- **Hook:** specific to this person or applies to 5,000? Which framework, and has it been tested against others?
- **Social proof:** relevant to this ICP? "We work with companies like yours" is dead.
- **Objection handle:** most common objection in replies, addressed?

**Tier 3 (last lever):**
- **Personalization:** only once a generic template with strong pain/value/offer gets positive replies.
- **Length:** all short so far? Try longer, and vice versa.
- **Tone:** tech/below-the-line casual; IT/gov/healthcare more formal.

**Output:** written diagnosis: which tier, what's wrong, why.

**Approval gate:** AM confirms the diagnosis before new variants.

---

## STEP 4. Five phases check

1. **Negative replies, no context**: no signal yet.
2. **Negative replies with context** ("We already have X" / "Not the right person"): inform targeting and messaging. One reply like this means ~100 who thought it.
3. **Inconsistent positives**, under 10%: who responded? Tighten on the winners.
4. **Consistent positives**, 10%+: scale.
5. **Consistent meetings**: 25-50%+ of positives convert.

State the phase and the priority action to reach the next one. Don't skip ahead.

---

## STEP 5. Decision: kill / iterate / scale

**Scale when all true:** reply rate 2%+; positive reply rate 10%+; client converts 25-50%+ of positives to meetings; TAM large enough. Flag Pablo/Jaimin to push more leads and confirm infrastructure.

**Kill when:** under 10% positive after 20+ variants across angles; targeting confirmed correct; all tiers pulled; nothing works. Note in `context.md`; flag to Jed if the client nears the "nothing will work" threshold.

**Iterate when:** some signal but benchmarks not hit, and the diagnosis points to a fixable problem.

---

## STEP 6. Write new variants

Surgical changes only. Tier 1 issue: 2-4 new Email 1 variants with new framing. Tier 2: new openings or P.S. lines. Tier 3: adjust length or tone.

Iterate Email 2/3 only after Email 1 hits benchmarks; set Smartlead to "prioritize new leads 100%" so testing data concentrates on Email 1.

Hard rules: no em dashes; no "Quick question."; no homepage copy; word counts (A/C under 120, B/D under 60, Email 3 under 50). Self-QA: competitor could say it? hook specific? prospect's language? CTA Tier 1 or 2? hard rules clean?

**Approval gate:** AM approves before pushing to Smartlead.

---

## STEP 7. Variant winner action (if flagged)

1. Confirm the winner: which variant, positive reply rate difference, sends each.
2. Recommend pausing the loser, keeping the winner.
3. Recommend whether to build a new challenger from what the winner reveals.

**Approval gate:** AM confirms before pausing anything.

---

## STEP 8. Push to Smartlead

New variants or pausing a variant: `POST /campaigns/[campaign_id]/sequences`. Standard settings unchanged unless the AM changes them (1,000/day; 8am-6pm EST Mon-Fri; America/New_York; 3 emails 2 days apart; plain text, no open/click tracking; 20% follow-up / 80% new; smart categorization on; OOO re-categorization on).

**Output:** confirm what changed; note it in `context.md` under Campaign Status Notes.

---

## When nothing's working

Read `knowledge/campaign-archive.md`. If only Consistent performers were tested, propose the next Inconsistent option. If those are exhausted, last-ditch options: **feedback campaign** (low-threat emails asking for feedback on problem/solution), **lean into LinkedIn** (more accounts, more volume), **cold calling** (engaged leads list from activity data). Flag to Jed; the best clients see results within 2 weeks.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key). Verified reads: `GET /campaigns/{id}`, `/analytics`, `/sequences`.
- Saving sequences or pausing variants is a write and not verified here; only on Pablo's explicit approval. HeyReach is not connected.
- `clients/`, `knowledge/` and `context/` files are in the pp-gtm repo, not on the box; ask Pablo for the content first.
- Never invent facts or names. No em dashes.
