---
name: karpathy-loop
description: >-
  Use when someone says run the loop, karpathy loop, or score and generate
  challengers: score active campaigns, flag underperformers by leads per
  positive reply, draft 2 challenger variants each, and post for approval before
  anything touches Smartlead.
---
# Skill: karpathy-loop

**Trigger:** "run the loop" / "karpathy loop" / "score and generate challengers"

**Who runs this:** Ran every Monday morning as a scheduled task in Claude. Can also be triggered manually by Jed.

**What it does:** Scores all active campaigns, finds underperformers (1000+ leads/positive reply), generates 2 challenger email variants per flagged campaign, and posts to Eric in #pp-internal for approval before anything touches Smartlead.

**North-star metric:** Leads per positive reply (lower is better).
- Under 500: healthy
- 500-999: watch it
- 1000+ or zero positives: generate challengers

---

## What the loop tests

Only these elements are fair game for challengers:
- Hook / opening frame
- Subject line
- Opening line
- Body framing (problem-led vs. outcome-led vs. social proof-led)
- Email length

**Locked, never change these:**
- CTA (the ask at the end)
- List or segment
- Sending schedule

---

## Full flow

Monday morning:
1. Score all campaigns (see `positive-reply-scoring`)
2. Find flagged campaigns with 500+ leads and no active experiment
3. Pull current step 1 copy from Smartlead
4. Read client ICP + context
5. Generate 2 challengers per campaign
6. Post to #pp-internal for Eric's approval
7. Save pending experiment records

Eric replies "approve A / approve B / approve both / skip":
- Create the approved variant in Smartlead
- Move experiment file from pending/ to active/

Following Monday:
- Scoring runs again
- Active experiments get compared: control vs. challenger
- Winner promoted, loser killed

---

## Experiment file locations

- Pending (waiting on Eric): `clients/[folder]/experiments/pending/[campaign_id]-experiment.json`
- Active (approved, live in Smartlead): `clients/[folder]/experiments/active/[campaign_id]-experiment.json`
- Completed (winner declared): `clients/[folder]/experiments/completed/[campaign_id]-experiment.json`

---

## Step by step (manual run)

1. Run scoring (`integrations/scoring/score-campaigns.py --quiet` in pp-gtm).
2. Find flagged campaigns: read today's score files, filter to lppr >= 1000 or null, total_leads >= 500, no existing experiment.
3. For each flagged campaign, fetch step 1 copy from the Smartlead sequences endpoint.
4. Read `clients/[folder]/icp.md` and `clients/[folder]/context.md`.
5. Generate 2 challengers. Variant A tests a different hook. Variant B tests a different subject line angle + opener.
6. Post to #pp-internal (channel ID: C08SSGSHWCD) with full copy and approval instructions for Eric.
7. Save experiment record to `clients/[folder]/experiments/pending/`.
8. Post summary to #pp-internal.

---

## Approval flow

When Eric replies in Slack with approval:
1. Read the approval message from #pp-internal
2. Find the matching pending experiment file
3. Create the approved variant as a new sequence variant in Smartlead via `POST /api/v1/campaigns/{campaign_id}/sequences/{seq_id}/variants`
4. Move the experiment file from `pending/` to `active/` with the Smartlead variant ID recorded
5. Confirm back in the Slack thread

---

## HARD RULES

1. Never create or modify Smartlead campaigns without Eric's explicit Slack approval
2. Only post to #pp-internal, never client-shared channels
3. Never test CTA, list, or segment, only hook, subject, opener, body framing, length
4. Never re-run challengers for a campaign already in pending/ or active/
5. Minimum 500 leads before flagging
6. No em dashes in any generated copy or messages

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key). Verified GETs: `GET /campaigns/{id}/analytics`, `GET /campaigns/{id}/sequences`.
- `integrations/scoring/score-campaigns.py` and the client folders are in the pp-gtm repo, not on the box. Use `/workspace/` for experiment records otherwise.
- The Monday schedule would be a Grok Bot routine (see the `routines` skill), only if Pablo asks.
- No Slack connector is connected, and any Slack post needs Pablo's explicit approval of the exact text. No Smartlead writes without explicit approval.
