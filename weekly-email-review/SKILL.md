---
name: weekly-email-review
description: "Use for the consolidated weekly Smartlead health check across all active clients: full capacity, disconnected inboxes, multi-campaign overlap, sender bounce rate, and missing signatures in one report; never fixes anything itself."
---

# Weekly Email Review

Trigger: "run the weekly email review" / "email review" / "how's our email health looking" / weekly recurring once scheduled.

Built 2026-09-15 by consolidating five checks that were previously run ad hoc into one sequence, so email infra health gets looked at on a cadence instead of only when something breaks.

---

## What this is (and isn't)

This is a **checklist that calls five existing skills in order**, not a new detection process. Don't reimplement their logic here -- follow each skill's own file for the actual mechanics. This skill's only job is: run all five, on every active client, and hand back one report Pablo can act on.

**Nothing gets fixed automatically.** Each of the five checks below ends in a report; fixing anything requires going into that specific skill's process and getting Pablo's go-ahead, the same as if he'd asked for that check on its own. This includes signature writes (check 5) -- even though `audit-inbox-signatures` skill is capable of writing directly, treat the write step here as gated on Pablo's go-ahead like every other fix in this review, not auto-applied.

## Scope

Every active Smartlead client. Pull the live client list (`GET /client/`) and cross-check against [[project_client_roster]]'s canceled-ID list -- Smartlead is the source of truth, not clients.yaml.

---

## The five checks, in order

### 1. Full-capacity compliance
Run `weekly-full-capacity-check` skill's process: campaign trigger interval (want 25 min), inbox cap (Gmail exactly 25/day, Outlook exactly 6/day, SMTP exactly 35/day; inboxes too high or too low are reported to Pablo, never changed here (Pablo, chat 2026-10-22)), inbox gap (always 20 min, every inbox type). Inbox numbers per Pablo, chat 2026-10-22. Flags the sending.ac cap=4/gap=120 reset pattern separately from generic drift -- see [[project_sending_ac_vendor_lock]] for current status (fix rollout paused as of 2026-09-15, this check still runs to track drift). Gaps not at 20 min are monitored and reported to Pablo only, never fixed automatically (Pablo, chat 2026-10-22).

### 2. Disconnected inboxes
Run `audit-disconnected-inboxes` skill's process: find inboxes with `is_smtp_success`/`is_imap_success` false, confirm each no longer exists at its provider (Mission Inbox mailbox list, exact email match not domain match; Zapmail for Zapmail inboxes). Mission Inbox is an active provider again (chat 2026-10-22), confirm `daily_sent_count`/`campaign_count` are 0. Report the confirmed count and list. Never delete; Pablo deletes manually unless he gives an explicit OK for that specific deletion (chat 2026-10-20).

### 3. Multi-campaign inbox overlap
Run `integrations/check_multi_campaign.py --client-id <id>` (report-only, from [[project_smartlead_automation]] / `redistribute-inboxes` skill) per client -- finds any inbox attached to more than one campaign at once. This has historically been found at very high rates on some clients (e.g. BMO had 394 duplicated inboxes, Practical Prospecting 85-100% overlap including legacy campaigns) so don't assume a client is clean without checking.

### 4. Sender bounce rate
Per active campaign, per client: flag anything over 5% bounce rate (any campaign status, per the precedent in [[fix-sender-bounce-emails]] (skill) -- 1,531 inboxes were flagged this way on 2026-07-30). `get_campaign_diagnostics` (MCP tool) surfaces this directly per campaign (`hasHighBounceRate` + `stats.rates.bounceRate`) without needing to hand-reconstruct it -- see [[feedback_use_purpose_built_diagnostics]].

### 5. Missing signatures
Run `audit-inbox-signatures` skill's process: pull every inbox **unfiltered** (`GET /email-accounts`, no `client_id` filter, paginate to empty) -- a per-client-filtered pull can silently miss inboxes that show `client_id: null` despite belonging to a real client (confirmed 315-inbox gap on 2026-09-14, see [[feedback_smartlead_api_lessons]]). An inbox is missing a signature if `signature` is null/empty. Match each to a confirmed name/job title via the client's signature template before writing anything -- never invent a title, stop and ask if a name isn't on file. **Scope every write to the exact account IDs identified in the audit, never a broad filter like `from_name`** -- a name-based batch write previously overwrote 63 inboxes that already had unrelated signature content, with no way to recover it (Smartlead has no signature history). Verify by re-pulling unfiltered and confirming the missing-signature count dropped by exactly the expected amount.

---

## Output

One consolidated report, one row per client, five columns (one per check above) summarizing pass/flag counts -- not five separate walls of text. Where a check has findings, name the specific problem (e.g. "12 inboxes disconnected + confirmed gone from MI", "394 inboxes duplicated across 5 campaigns", "3 campaigns over 5% bounce", "212 inboxes missing a signature") so Pablo can decide what to act on without re-running the check himself. Save any per-inbox/per-campaign detail (CSVs) to `/workspace/`, don't dump it into chat.

---

## Explicitly NOT part of this review

`assign-inboxes` skill and `inbox-rotation-v2` skill are event-triggered (new client onboarding, Day-14 lead rotation) rather than periodic health checks -- they don't belong in a recurring review because there's nothing to "check," they're actions taken in response to a specific business event. Leave them out unless Pablo asks to fold them in later.

---

## Routine status (deferred)

Same blocker as [[weekly-full-capacity-check]]: this needs the Smartlead claude.ai connector authorized before it can run as an unattended cloud routine (cloud routines can't use the local Keychain API key). Run manually until that's set up and Pablo has time to wire up `/schedule`.

## Related

- `weekly-full-capacity-check` skill, `audit-disconnected-inboxes` skill, `redistribute-inboxes` skill (`check_multi_campaign.py`), `audit-inbox-signatures` skill -- the five checks this orchestrates
- [[project_sending_ac_vendor_lock]], [[fix-sender-bounce-emails]] (skill), [[feedback_use_purpose_built_diagnostics]] -- context behind checks 1 and 4
- [[project_client_roster]] -- active vs canceled client_ids

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
- MCP `get_campaign_by_id` = `GET /campaigns/{id}` (verified 2026-10-22 with a read-only GET; includes `status`, `client_id`, `scheduler_cron_value`, `min_time_btwn_emails`, `max_leads_per_day`). `GET /campaigns/{id}/schedule` returns 404 (re-confirmed).
- `GET /campaigns/{id}/email-accounts` (verified 2026-10-22 with a read-only GET) is the live roster of what is attached right now. Response objects include SMTP/IMAP passwords, so keep only `id`, `from_email`, `type` and never print or save the rest.
- MCP `get_email_accounts` = `GET /email-accounts?limit=100&offset=N` (add `client_id=X` to scope), paginate until an empty or short page. Pull unfiltered when you need to catch `client_id: null` orphans. Do not print full objects, they include passwords.
- `GET /campaigns/{id}/mailbox-statistics?limit=100&offset=0` (verified 2026-10-22 with a read-only GET; rows have `email_account_id`, `from_email`, `sent_count`, `reply_count`, `bounce_count`, `sender_bounce_count`).
- MCP `get_campaign_analytics` = `GET /campaigns/{id}/analytics` (verified 2026-10-22 with a read-only GET; has `sent_count`, `bounce_count`, `reply_count`, `unique_sent_count`, `client_id`, `client_name`).

- Multi-campaign overlap: `check_multi_campaign.py` is not on the box; reproduce it by pulling `GET /campaigns/{id}/email-accounts` for every active campaign and counting inbox ids that appear in more than one.
- Sender bounce: `get_campaign_diagnostics` has no verified REST equivalent; use `mailbox-statistics` `sender_bounce_count / sent_count` per inbox per campaign (the method in `fix-sender-bounce-emails`).
- Scheduling: the Claude cloud routine blocker does not apply here; on Grok Bot this would be a routine (see the `routines` skill), created only if Pablo asks.
- Limits: resolved (Pablo, chat 2026-10-22, forever rule, approved wording): "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own."
- Signatures (check 5): templates are under review with Pablo; report missing signatures only.
