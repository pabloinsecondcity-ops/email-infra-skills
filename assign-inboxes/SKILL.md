---
name: assign-inboxes
description: "Use ONLY for a NEW client: assign Smartlead inboxes evenly onto empty campaigns (1 inbox : 1 campaign, Gmail+Outlook mix, Dont-use-until tags respected). For existing clients with running campaigns plus new ones, use rebalance-inboxes-to-new-campaigns."
---

# Assign Inboxes to Campaigns (v2)

Trigger: "Assign inboxes to campaigns" or "Distribute inboxes" or "Day 14 assignment"

Script (Pablo's Mac): `integrations/assign_inboxes.py`. On the box, do the same via REST with exact inbox IDs.

---

## What the script does

1. Looks up the client and fetches all inboxes belonging to it (filtered strictly by client_id, no cross-client leakage)
2. Blocks if any target campaign already has inboxes
3. Splits the inboxes evenly across the specified campaigns
4. Assigns each chunk to its campaign via the Smartlead API
5. Verifies what is actually in each campaign after assignment and flags discrepancies
6. Never deletes anything. Removal is left to the operator.

## What the script does NOT do (manual checks required)

The script only takes `--client`, `--campaigns`, and `--dry-run`. It pulls the client's ENTIRE inbox pool. It does not:

- Exclude inboxes tagged "Dont use until <date>"
- Exclude inboxes already connected to another campaign
- Balance provider types (Gmail / Outlook / SMTP) within each campaign
- Handle fixed-count campaigns (e.g. "[Auto-Refresh]" = 5)

Do every check in the Pre-flight section below before running live. If any of them would change the plan, stop and confirm with Pablo instead of running the script as is.

---

## Pre-flight checklist (do every time)

1. **Confirm scope.** Assign only what was literally asked. If the request is "assign this week's tagged inboxes," do NOT run anything that touches the rest of the client's pool. Never disconnect or reassign inboxes outside the request (disconnecting loses their lead assignments).
2. **"Dont use until <MM/DD>" tags.** Parse the date (current year) and compare to today.
   - Future date: exclude the inbox.
   - Today or past date: eligible, regardless of send activity or warmup status.
   - `WARMING UP - DONT USE YET`: exclude (Pablo, chat 2026-09-30: those inboxes wait 2 weeks and must not be on campaigns). Also exclude inboxes tagged `burned`.
3. **1 inbox : 1 campaign.** Check that no eligible inbox is already connected to another campaign. If one is, flag it. Overlap is human/process error on our side, not a Smartlead bug. Use `check_multi_campaign.py` (or parallel `GET /email-accounts/{id}?fetch_campaigns=true`) to detect it.
4. **Provider type breakdown.** Count GMAIL / OUTLOOK / SMTP in the eligible pool. Never assume which type dominates. If a "best inboxes to campaign X" priority is requested, sanity-check the per-campaign counts in a dry run. If the split looks lopsided, flag it and confirm.
5. **Provider mix per campaign.** Mix as much as possible by default (Pablo, chat 2026-10-22). Every campaign must get a mix of Gmail + Outlook (and any other types and vendors in play, e.g. Zapmail, Mission Inbox, SMTP). Never route all of one provider to one campaign and all of another to a different campaign.
6. **Fixed-count campaigns.** "[Auto-Refresh]" in the name always means fixed 5 inboxes. Every other name pattern ("[One-Off]", "Follow Up", "Re-Engage", etc.) is a normal even split unless Pablo says otherwise. Ask, don't infer.
7. **Campaigns empty.** Target campaigns must have zero inboxes before assigning. The script blocks otherwise.

---

## How to run

```bash
cd ~/Desktop/Automations/pp-gtm

# Dry run
python3 integrations/assign_inboxes.py \
  --client "Routeware" \
  --campaigns "Routeware - Municipal V2" "Routeware - Private Haulers V3" \
  --dry-run

# Live run
python3 integrations/assign_inboxes.py \
  --client "Routeware" \
  --campaigns "Routeware - Municipal V2" "Routeware - Private Haulers V3"
```

Always run `--dry-run` first and show the plan (per-campaign count AND per-campaign provider mix) before executing.

If the pre-flight checks exclude any inboxes, the script cannot be used as is, because it would assign the full pool. Do the assignment with exact inbox IDs via REST instead (`POST /campaigns/{id}/email-accounts` with `{"email_account_ids": [...]}`), after Pablo confirms the plan.

---

## Rules

- Inboxes are split evenly. 20 inboxes and 4 campaigns = 5 per campaign.
- Never all inboxes to all campaigns.
- No inbox appears in more than one campaign, ever.
- Every campaign gets a Gmail + Outlook mix. Never single-provider.
- Never mix clients. Filter strictly by client_id.
- Never delete anything without explicit instruction from Pablo. Report extras, let him decide.
- Always verify counts after assigning. The bulk assign can silently skip some inboxes.
- Use REST (`SMARTLEAD_API_KEY`) for bulk work. MCP only for quick single lookups.

---

## Post-assignment checks

1. Verify the exact inbox count per campaign matches the plan.
2. Verify the provider mix per campaign (no single-provider campaign).
3. Verify no inbox is in more than one campaign.
4. **Swap tags (forever step).** After the inboxes are added and verified on their campaigns, remove the tags 'WARMING UP - DONT USE YET' and any 'dont use until X' from those inboxes, and add the tag 'ACTIVE' instead. (Pablo, chat 2026-10-26, forever step, approved wording) Only for inboxes confirmed present on their target roster; read back tags after.
4. Confirm inbox settings match the full-capacity standard. Report any inbox not at exactly 25/6/35 (Gmail/Outlook/SMTP), too high or too low, or with a gap not at 20 to Pablo; do not change caps or gaps yourself unless he explicitly asks for that fix in this conversation (Pablo, chat 2026-10-22):
   - Gmail: exactly 25/day, 20 min gap (Pablo, chat 2026-10-22)
   - Outlook: exactly 6/day, 20 min gap (Pablo, chat 2026-10-22)
   - SMTP: exactly 35/day, 20 min gap (Pablo, chat 2026-10-22)
   - "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own." (Pablo, chat 2026-10-22, forever rule, approved wording)
   - Campaign: 25 min interval, window sized for 26 triggers/day
   - Inbox gap is ALWAYS 20 min for every inbox type (Pablo, chat 2026-10-22, forever rule); the old 4-min buffer rule is retired.
5. Campaign status: resume campaigns that were ACTIVE going in, unless told to "load but hold." Never resume a DRAFTED campaign.

---

## When to use

**New clients only (Pablo, chat 2026-10-16).** For an existing client (including Day 14 replacements), use `add-inboxes-to-campaigns` (add-only onto populated campaigns) or `rebalance-inboxes-to-new-campaigns` (most common case: new campaigns created for a client with running ones).

**New client setup:** after importing inboxes into Smartlead and warmup is complete, distribute across all active campaigns.

---

## Related

- `integrations/rotate_inboxes_v5.py`: latest rotation script
- `integrations/check_multi_campaign.py`: detects inboxes connected to more than one campaign
- rebalance-inboxes-to-new-campaigns: most common case for existing clients (chat 2026-10-16).
- redistribute-inboxes: superseded by rebalance-inboxes-to-new-campaigns (Pablo, chat 2026-10-22).
- add-inboxes-to-campaigns: add-only onto already-populated campaigns.
- inbox-rotation-v2, email-infra, full-capacity-audit (Claude export skills)
