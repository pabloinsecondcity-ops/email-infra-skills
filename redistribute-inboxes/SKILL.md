---
name: redistribute-inboxes
description: "SUPERSEDED by rebalance-inboxes-to-new-campaigns (Pablo prefers that one). Reference only: the old Claude full redistribution (pause, detach the pool, reassign, resume). Do not run; use rebalance-inboxes-to-new-campaigns."
---

# Redistribute Inboxes (Full Client Rebalance)

> **SUPERSEDED (Pablo, chat 2026-10-22).** Pablo prefers the skill we built together, `rebalance-inboxes-to-new-campaigns`, over this Claude-era full redistribution. Use that skill instead. This recipe is kept unchanged for reference only.

Trigger: "assign inboxes to campaigns" / "redistribute inboxes" / "I'm launching new campaigns, rebalance across all of them" for a client whose campaigns are not empty.

Script: `integrations/redistribute_inboxes.py`

---

## Detecting the problem first: check_multi_campaign.py

Before assuming a client needs this treatment, run `integrations/check_multi_campaign.py --client-id <id>` (report-only, never makes changes). It fetches every campaign under the client (any status) and every inbox currently attached to each, then reports any inbox attached to more than one campaign at once -- the exact failure mode this skill exists to fix. Confirmed on 2026-07-30 across 8 clients: SignWell (31 duplicated), BMO (394 duplicated across a 5-7 campaign cluster), RevPilots (637 duplicated across literally every non-draft campaign -- the known assign-endpoint bug), Whip Around, cmap.io, Mortar Link, Arovy, and Practical Prospecting (all 85-100% overlap once you include their large backlogs of legacy/one-off campaigns). Routeware and Axero (the clients this skill was built for) checked clean.

**How to apply:** Run this check on any client before touching inboxes, even ones you think are fine -- the overlap can be total (100% of attached inboxes duplicated) and invisible from the Smartlead UI unless you're looking at inbox-level campaign attachments specifically.

---

## When to use this vs assign-inboxes skill

- **assign-inboxes skill** (`assign_inboxes.py`): campaigns are EMPTY (new client setup, or Day 14 rotation assignment). Blocks if any target campaign already has inboxes.
- **redistribute-inboxes skill** (this skill, `redistribute_inboxes.py`): campaigns ALREADY have inboxes and the whole roster needs rebalancing. Disconnects the client's entire inbox pool from every campaign under that client (any status -- active, paused, completed, drafted, archived, stopped) first, then reassigns per plan.

---

## Inputs to gather up front -- ask ONCE, as a single batch, before starting

1. Client name.
2. Full campaign list for the client (active, paused, drafted -- pull all of it). Confirm with the client which campaigns are actually in scope for this round. Don't assume "active" = "in scope," and don't assume drafted campaigns are out of scope -- they're often deliberately included (e.g. a new launch).
3. Any fixed-count exceptions (e.g. "auto-refresh / re-engage campaigns only need 5 inboxes, not an even share").
4. Any type-based priority (e.g. "give the best inboxes to campaign X"). Before agreeing to implement this, see the Gotcha below -- check the actual inbox-type breakdown first, don't assume.
5. Today's date, for tag-hold evaluation.

Getting all 5 up front avoids the multi-round back-and-forth that happened the first time this was built (Axero, then Routeware, 2026-07-29) -- most of the friction was avoidable if the campaign list, exceptions, and priority rules were nailed down before any pausing/disconnecting started.

---

## The "Dont use until <date>" rule

Inboxes may carry a tag like `Dont use until 08/11`. If that date is AFTER today, exclude the inbox -- it's still inside its warmup hold. If the date has already PASSED, the inbox is eligible regardless of current send activity (a nonzero `daily_sent_count` does NOT disqualify it -- that tripped up the first pass on Axero). Tag date format is `MM/DD`; assume the current year.

---

## Gotcha: check inbox type distribution before any type-based priority request

A client's inbox pool is NOT reliably majority-SMTP or majority-Gmail/Outlook -- check every single time before implementing a "give the best inboxes to X" request. Confirmed cases (2026-07-29):

- **Axero**: 204 SMTP vs. 135 Gmail/Outlook -- Gmail/Outlook was the minority, so giving 3 drafted campaigns the entire Gmail/Outlook pool (45 each) worked cleanly without starving the other 8 campaigns.
- **Routeware**: 27 SMTP vs. 565 Gmail/Outlook -- Gmail/Outlook was the overwhelming majority. Applying the same "priority campaign gets the whole best-type pool" logic would have given one draft campaign 565 inboxes and left only 3-4 each for the other 8 active campaigns. Caught via dry-run before running live; the fix was to drop type-based priority entirely and do a plain even split.

Always run the type breakdown (`GMAIL` / `OUTLOOK` / `SMTP` counts on the eligible pool) and sanity-check the resulting per-campaign counts in the dry-run BEFORE going live. If a type-priority request would produce a lopsided result, flag it and confirm the actual intended behavior rather than guessing.

---

## Gotcha: pause/resume verification is unreliable via the obvious endpoint

`update_campaign_status` (PAUSED or START) returns `{"ok": true}` even when the status change hasn't propagated to read endpoints yet. `get_campaign_by_id` and `get_campaigns` can show STALE status (e.g. still "ACTIVE") for a while after the mutation succeeded. Use `get_campaign_status_stats` (aggregate status counts, filtered by `client_ids`) to verify instead -- it reliably reflects the true current state. Always verify pause before disconnecting anything, and verify resume before reporting the task done.

---

## Process

0. **Save a tracking CSV FIRST**, before touching anything -- `/workspace/{client}_campaigns_{date}.csv` listing every target campaign (id, name, current status). Do this before pausing, not after (learned the hard way on the first Axero pass).
1. Pause every currently-ACTIVE campaign in scope (`update_campaign_status` -> PAUSED). Drafted campaigns don't need pausing (they aren't sending). Verify via `get_campaign_status_stats`.
2. **Always dry-run first**: `redistribute_inboxes.py --dry-run`. Sanity-check pool size, tag exclusions, and per-campaign counts before running live -- this is what caught the Routeware type-distribution problem before it caused damage.
3. Run live (drop `--dry-run`). The script disconnects the client's entire inbox pool from every campaign under that client (any status), builds the eligible pool (excluding future-held tags), assigns per plan, and verifies counts automatically.
4. Resume every campaign paused in step 1 (`update_campaign_status` -> START). Verify via `get_campaign_status_stats`.
5. Update the tracking CSV with final per-campaign counts and status.
6. Report a compact summary table: campaign name -> final inbox count, plus how many inboxes were excluded for a future tag hold.

---

## Script usage

```bash
cd /workspace/pp-gtm

# Plain even split across N campaigns, no exceptions (e.g. Routeware)
python3 integrations/redistribute_inboxes.py \
  --client-id 350583 \
  --split 3365376 3725662 3725619 3725287 3684962 3684961 3684960 3448904 3241461 \
  --today 2026-07-29 \
  --dry-run

# With fixed-count exceptions (e.g. Axero -- auto-refresh/re-engage campaigns get exactly 5)
python3 integrations/redistribute_inboxes.py \
  --client-id 178500 \
  --fixed 3158562:5 2949399:5 3700016:5 \
  --split 3739076 3699802 3644576 3644541 3019682 \
  --today 2026-07-29

# With type-based priority (e.g. give drafted campaigns the best/Gmail+Outlook inboxes --
# ONLY after confirming the type breakdown supports it, see Gotcha above)
python3 integrations/redistribute_inboxes.py \
  --client-id 178500 \
  --fixed 3158562:5 2949399:5 \
  --priority 3572370 3572369 3307546 \
  --best-types GMAIL,OUTLOOK \
  --split 3739076 3700016 3699802 3644576 3644541 3019682 \
  --today 2026-07-29
```

Drop `--dry-run` to execute live.

---

## Resuming after the fix: default to yes, unless told otherwise

After the reassignment, resume (START) every campaign that was ACTIVE before you touched it -- that's the default across every client done this way (Axero, Routeware, RevPilots, Whip Around, cmap.io, Mortar Link, Arovy, Practical Prospecting). The one exception was BMO (2026-07-30), where Pablo explicitly said "allocate inboxes but don't launch at the end" because the client had paused everything and a relaunch date was still pending. Drafted campaigns always stay drafted regardless -- never START a campaign that was DRAFTED going in.

**How to apply:** Ask once per client whether this round is a "resume as normal" or a "load but hold" situation if it's not obvious from context (e.g. client explicitly paused things, or a specific relaunch date was mentioned) -- otherwise resume everything that was active without asking again.

---

## Campaign names are not reliable signals for exceptions

`[Auto-Refresh]` in a campaign name has consistently meant "give this one a small fixed count (5), not an even share" across every client (Axero, Whip Around, Mortar Link, Arovy). But `[One-Off]` does NOT mean the same thing -- confirmed on Whip Around's "Wallet Campaign [One-Off]" and Arovy's "Salesforce Ben Followers [One-Off]", both of which Pablo explicitly said to treat as a normal even-split campaign, calling the "[One-Off]" tag "just a name convention." Likewise, follow-up sequence campaigns (BMO's "Interested Follow Up 1", Practical Prospecting's "Interested - Follow Up") are NOT automatically a fixed-count exception -- BMO got a small fixed count for them, but Practical Prospecting's got a full even share, both by explicit instruction, not by name pattern.

**How to apply:** Never infer an exception from a campaign name alone. `[Auto-Refresh]` is the one pattern confirmed to always mean "fixed 5" -- for everything else (`[One-Off]`, "Follow Up", "Re-Engage", etc.) ask what treatment it should get.

---

## Never

- Never delete inboxes -- only detach/reattach at the campaign level.
- Never skip the dry-run, even on a client you've already done this for once.
- Never assume a "Dont use until" tag means the inbox is unavailable without checking whether the date has actually passed.
- Never apply `--priority`/`--best-types` without checking the real type breakdown of the eligible pool first.
- Never resume campaigns without verifying via `get_campaign_status_stats` (not `get_campaign_by_id`).

---

## Related

- `assign-inboxes` skill -- fresh assignment to empty campaigns (Day 14 rotation, new client setup)
- `integrations/redistribute_inboxes.py` -- the script
- `integrations/check_multi_campaign.py` -- report-only overlap detector, run this first
- `integrations/assign_inboxes.py` -- the empty-campaign-only sibling script

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22). The recipe above is Pablo's original text; this section only maps it to the tools available here.

- Smartlead: REST only (Pablo's 2026-09-28 rule: always REST for Smartlead, never MCP). Base `https://server.smartlead.ai/api/v1`, auth `?api_key=$SMARTLEAD_API_KEY` (already set in the box env; never print, log or save it). There is no Smartlead MCP and no macOS Keychain on this box. Run calls from Shell with Python shelling out to `curl`.
- Files: write CSVs and scratch output to `/workspace/` (replaces `temp/` and `pp-gtm/temp/`).
- Scripts under `integrations/` (and other `pp-gtm` or `~/Desktop/Automations` scripts) live in Pablo's pp-gtm repo, not on the box. Reproduce their logic with the REST calls described here; do not assume the script exists.
- `[[...]]` links point to Claude memory notes that were not imported as skills, except `fix-sender-bounce-emails`, `clean-up-inboxes-smartlead` and `disconnect-by-domain`, which are skills now.
- Standing rules still apply: never delete without Pablo's explicit authorization, the Friday weekly sweep routine never detaches (other tasks may detach when the task calls for it, chat 2026-10-22), canary first before any bulk write, verify every number by re-pulling, no em dashes.

REST equivalents for the calls used above:
- MCP `get_all_clients` = `GET /client/` (verified 2026-10-22 with a read-only GET; returns `id`, `name`, `email`, ...).
- MCP `get_campaigns` = `GET /campaigns` unfiltered, then filter client-side by `client_id` (documented in feedback_smartlead_api_lessons; the `?client_id=` filter times out for 100+ campaign clients).
- MCP `get_campaign_status_stats` = `GET /analytics/campaign/status-stats?client_ids=<id>` (verified 2026-10-22 with a read-only GET; returns `data.campaign_status_stats` as a list of `{status, total_count}` for Active/Paused/Drafted/Completed/Stopped; the `client_ids` filter does narrow the counts).
- MCP `update_campaign_status` (PAUSED / START): REST equivalent not yet verified. Smartlead's public docs list `POST /campaigns/{id}/status` with `{"status": "PAUSED"|"START"|"STOPPED"}`, but one doc page says PATCH. It is a write, so it was not probed. Test on one campaign with Pablo's go-ahead before relying on it, and verify with the status-stats GET above.
- `GET /campaigns/{id}/email-accounts` (verified 2026-10-22 with a read-only GET) is the live roster of what is attached right now. Response objects include SMTP/IMAP passwords, so keep only `id`, `from_email`, `type` and never print or save the rest.
- MCP `delete_email_accounts_from_campaign` = `DELETE /campaigns/{id}/email-accounts` with `{"email_account_ids": [...]}`, returns `{"ok": true, "result": N}` (documented). Write action: only on Pablo's explicit go-ahead.
- MCP `get_email_accounts` = `GET /email-accounts?limit=100&offset=N` (add `client_id=X` to scope), paginate until an empty or short page. Pull unfiltered when you need to catch `client_id: null` orphans. Do not print full objects, they include passwords.
- `GET /email-accounts/tags` (verified 2026-10-22 with a read-only GET). The live objects have keys `id`, `name`, `color`.

- `integrations/redistribute_inboxes.py`, `assign_inboxes.py` and `check_multi_campaign.py` are not on the box.
- Overlap with saved skills: `add-inboxes-to-campaigns` and `rebalance-inboxes-to-new-campaigns` (2026-10-16) cover add-only and rebalance flows. This full detach-and-reassign flow is superseded; do not run it without Pablo's explicit go-ahead.
- Attaching: `POST /campaigns/{id}/email-accounts` (documented, write).
- Limits: current inbox standard (Pablo, chat 2026-10-22, forever rule, approved wording): "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own." Caps and gaps are report-only; change them only when Pablo asks. See `full-capacity-audit`.
