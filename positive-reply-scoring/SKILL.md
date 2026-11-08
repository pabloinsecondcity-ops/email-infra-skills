---
name: positive-reply-scoring
description: >-
  Use when someone says score campaigns, check reply rates, how are campaigns
  performing, or what's our positive reply rate: compute leads per positive
  reply and positive reply rate per active campaign and flag underperformers.
---
# Skill: positive-reply-scoring

**Trigger:** "score campaigns" / "check reply rates" / "how are campaigns performing" / "what's our positive reply rate"

**Who runs this:** Jed (weekly pulse) or Eric (before/after iterating a campaign). Part of the Monday Karpathy loop.

**What it does:** Pulls reply data from Smartlead across all active campaigns, classifies every reply, computes leads-per-positive-reply and positive reply rate per campaign, flags underperformers, and saves scores.

**North-star metric:** Leads per positive reply. Lower is better. A campaign sending to 500 leads that generates 5 positive replies scores 100. Target: under 300. Flag: over 600.

---

## Before you start

Read `clients/registry.md` to confirm which clients are active and which folders they map to. Confirm `$SMARTLEAD_API_KEY` is set.

## Step 1. Score

The pp-gtm script `integrations/scoring/score-campaigns.py` (options `--client whip-around`, `--campaign-id 3378252`):
- Pulls all campaigns from Smartlead
- Fetches replies for each campaign with 500+ sends
- Classifies each reply (positive_interested, positive_soft, positive_referral, negative, ooo, bounce)
- Computes leads-per-positive-reply and positive reply rate
- Saves scores to `clients/[folder]/experiments/scores/YYYY-MM-DD-[campaign_id].json`
- Prints a ranked report, best to worst by leads-per-positive-reply

## Step 2. Read the report

Status thresholds:
- Under 500 leads/positive reply: healthy
- 500-1000: watch it, consider iteration
- Over 1000 or zero positives: needs attention now

## Step 3. Flag underperformers

For each flagged campaign, read `clients/[folder]/context.md` to see what's been tried. Then determine the likely issue tier:
- **Tier 1 (deliverability):** If open rate is under 30%, deliverability is the problem, not messaging.
- **Tier 2 (targeting):** If opens are fine but positive replies are zero, the list or persona is off.
- **Tier 3 (messaging):** If some positives but weak rate, hook or angle needs iteration.

Post findings to the internal PP working channel with a one-line summary per flagged campaign: "Campaign score update, [campaign name]: [N] leads/positive reply ([X]% pos reply rate). [Tier diagnosis]. Flagging for [Eric/GTME] to review."

## Step 4. Update context files

Append to `clients/[folder]/context.md` under "Campaign Scores (last updated: YYYY-MM-DD)" a table: Campaign | Sent | Pos Reply Rate | Leads/Pos Reply | Status.

## Step 5. Feed the Karpathy loop

- Flagged red with 500+ sends: challenger variants generated
- Watch status: watched one more week before challengers
- Healthy: no action; new challenger when current winner has run 1000+ sends

---

## HARD RULES

1. Never flag a campaign with under 500 sends
2. Leads-per-positive-reply is the primary metric, do not optimize for raw reply rate alone
3. OOO and bounce replies do not count as positive or negative, they are excluded from the rate
4. Never post campaign performance data publicly, internal PP channel only, never the client-shared channel
5. No em dashes

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key).
- The scoring script is not on the box. Campaign totals come from the verified `GET /campaigns/{id}/analytics`; per-inbox replies from the verified `GET /campaigns/{id}/mailbox-statistics`. Reply classification has no verified REST source mapped yet; also see the saved `smartlead-per-inbox-reply-counts-fast` skill. Pablo says opens and clicks aren't tracked, so the open-rate tier check may have no data.
- Client folders are in the pp-gtm repo; use `/workspace/` otherwise. No Slack connector on the box; any post needs Pablo's approval of the exact text.
