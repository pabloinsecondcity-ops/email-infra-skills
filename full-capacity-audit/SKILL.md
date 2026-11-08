---
name: full-capacity-audit
description: "Use when Pablo asks to audit or fix a client's active campaigns and inboxes against the full capacity sending standard (campaign trigger interval, Gmail, Outlook and SMTP daily caps, inbox gap); inboxes not at exactly 25/6/35 (too high or too low) and gaps not at 20 are report-only; any fix only on his explicit go-ahead in that conversation."
---

# Full Capacity Audit

Trigger: "check [client]'s inboxes/campaigns against the full capacity standard" / "are [client]'s inboxes set up right" / "run the full capacity audit on [client]".

Built 2026-09-10 on Jason Lee (Brand XYZ, client_id 543007), see [[feedback_full_capacity_campaign_setup]] for the standard itself and why these specific numbers.

---

## The standard being checked

**Campaign level** (per active campaign):
- Trigger interval (`min_time_btwn_emails` / `min_time_btw_emails`) = **25 minutes**
- Sending window sized to produce **~26 triggers/day/sender** (reference window: 07:39–18:42; recompute if a client needs a different window, but keep interval=25)

**Inbox level** (per inbox, by provider `type`):
- Gmail: `message_per_day` **exactly 25**
- Outlook: `message_per_day` **exactly 6**
- SMTP: `message_per_day` **exactly 35** (Pablo, chat 2026-10-22)
- "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own." (Pablo, chat 2026-10-22, forever rule, approved wording)
- All types: `minTimeToWaitInMins` (gap) = **20** (Pablo, chat 2026-10-22, forever rule)

(Pablo, chat 2026-10-22. Replaces the Claude standard of Outlook exactly 5 and the Oct 16 keep-higher-caps exception.)

---

## Process

### Step 1. Resolve the client_id

Smartlead's client list (`GET /client/`) is often named by contact person, not company (e.g. Mason Interactive shows as "Ben Mitchell", client_id 529362). If the client is only known by a company/project nickname (like "Brand XYZ"), it may not string-match, ask Pablo to confirm which client_id it maps to rather than guessing. Check [[project_client_roster]] first, it may already be recorded.

### Step 2. Pull all campaigns, filter to the client

`GET /campaigns` **unfiltered**, then filter client-side by `client_id`, the filtered `/campaigns?client_id=` endpoint times out/500s for clients with 100+ campaigns (see [[feedback_smartlead_api_lessons]]). Identify the ACTIVE ones; ignore PAUSED/DRAFTED/COMPLETED for the compliance check itself (but confirm with Pablo before assuming they're out of scope for the fix).

### Step 3. Get each active campaign's schedule

`GET /campaigns/{id}` returns the schedule inline, `min_time_btwn_emails`, `scheduler_cron_value` (`tz`, `days`, `startHour`, `endHour`), `max_leads_per_day`. No separate schedule endpoint needed (a `/campaigns/{id}/schedule` GET returns 404, don't try it).

### Step 4. Pull the client's FULL inbox roster

`GET /email-accounts?client_id={id}&limit=100&offset=0`, looping `offset` in steps of 100 **until a page comes back empty** (or shorter than 100). Do not stop after the first page, a single-page pull silently truncates (confirmed 2026-09-10: Jason Lee had 570 inboxes total, not the 100 a single call returns). Capture `id`, `from_email`/`username`, `type`, `message_per_day`, `minTimeToWaitInMins` per inbox.

Skip the campaign-level `GET /campaigns/{id}/email-accounts` pull and any inbox-overlap cross-referencing unless specifically asked, not needed to answer "is this client compliant," and check_multi_campaign.py already exists as the purpose-built overlap detector if that question comes up separately (see [[redistribute-inboxes]]).

### Step 5. Compare against the standard, report

For each inbox: `cap_std = {"GMAIL": 25, "OUTLOOK": 6, "SMTP": 35}.get(type)`, `cap_ok = (message_per_day == cap_std)`; when `message_per_day != cap_std`, label it `too high` (above) or `too low` (below), `gap_ok = (minTimeToWaitInMins == 20)`. For each active campaign: `interval_ok = (min_time_btwn_emails == 25)`.

Don't print all rows to chat, write a CSV to `/workspace/` (or the session scratchpad) and report a compact summary: campaign compliance table, and inbox counts broken into fully-compliant / cap-only-wrong / gap-only-wrong / both-wrong (cap-wrong split into too high and too low), plus the underlying value distributions (e.g. "414 inboxes at gap=10, 150 at gap=120") so Pablo can see the shape of the problem, not just a pass/fail count.

### Step 6. Fix

**Inbox caps not at the exact standard: report-only (Pablo, chat 2026-10-22).** Never change caps on your own. List every Gmail inbox not at 25, Outlook inbox not at 6 and SMTP inbox not at 35 for Pablo, with too high and too low listed separately (counts per client and type, current values), and he decides. Only if Pablo explicitly asks for the cap fix in this conversation: set Gmail to 25, Outlook to 6, SMTP to 35 (whether too high or too low), canary one inbox, read it back, then batch, then re-pull and report exactly what changed (before and after values). No delete still applies. Gap is always 20 for every inbox type (chat 2026-10-22); gaps not at 20 min are monitored and reported to Pablo only, never fixed automatically (Pablo, chat 2026-10-22). Change a gap only when Pablo asks for that specific fix. Campaign schedule changes still need Pablo's explicit go-ahead.

**Campaigns**, use the MCP tool `update_campaign_schedule` (not a raw REST guess): requires `campaign_id`, `timezone`, `days_of_the_week`, `start_hour`, `end_hour`, `min_time_btw_emails`, `max_new_leads_per_day`. Carry forward the client's existing `timezone`/`days_of_the_week`/`max_new_leads_per_day` unchanged unless told otherwise, only touch `min_time_btw_emails` (and `start_hour`/`end_hour` if the window also needs to change to hit ~26 triggers). Confirmed working 2026-09-10 on 3 campaigns.

**Inboxes**, confirmed REST endpoint `POST /email-accounts/{id}?api_key=...` with body `{"max_email_per_day": 25|6|35}` (only when Pablo has asked for the cap fix, only for inboxes not at the exact standard). Send `time_to_wait_in_mins: 20` only when Pablo has asked for that specific gap fix (gaps are report-only, chat 2026-10-22). Canary one inbox and read it back first (see [[feedback_smartlead_api_lessons]]). At hundreds of inboxes, sequential calls are too slow and `xargs -P` with a multi-field line reliably breaks ("command line cannot be assembled, too long" / arg-splitting issues), use a Python `concurrent.futures.ThreadPoolExecutor` (10-15 workers) shelling out to `curl` per call instead. Confirmed: 569 inboxes updated this way in one batch, 569/569 succeeded.

### Step 7. Verify

Re-run Step 4 (full paginated re-pull) and Step 3 (re-fetch the fixed campaigns) after the fix, don't trust the `{"ok": true}` responses alone. Confirmed 2026-09-10: 570/570 inboxes and all 3 campaigns verified compliant after the fix.

---

## Rollout status

Piloted on Jason Lee (Brand XYZ, 543007) on 2026-09-10. The inbox standard (Gmail exactly 25/day, Outlook exactly 6/day, SMTP exactly 35/day, gap 20) applies to EVERY client, not just Jason Lee (Pablo, chat 2026-10-22). Caps not exactly 25/6/35 (too high or too low) and gaps not at 20 are report-only (change them only when Pablo asks, chat 2026-10-22); the campaign-level schedule change still needs a go-ahead per client.

---

## Related

- [[feedback_full_capacity_campaign_setup]], the standard itself, and the "why" (26 triggers vs 25/5 caps)
- [[feedback_use_purpose_built_diagnostics]], general reminder to check for audit/diagnostics endpoints before hand-reconstructing; this skill's Step 4/5 is the manual-reconstruction path because no single Smartlead endpoint answers "is this client's whole roster at cap X" directly, checked and confirmed no better option exists for this specific question.
- `redistribute-inboxes` skill / `check_multi_campaign.py`, for inbox-to-campaign overlap, a related but separate problem this skill deliberately does not check.

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
- MCP `get_campaign_by_id` = `GET /campaigns/{id}` (verified 2026-10-22 with a read-only GET; includes `status`, `client_id`, `scheduler_cron_value`, `min_time_btwn_emails`, `max_leads_per_day`). `GET /campaigns/{id}/schedule` returns 404 (re-confirmed).
- `GET /campaigns/{id}/email-accounts` (verified 2026-10-22 with a read-only GET) is the live roster of what is attached right now. Response objects include SMTP/IMAP passwords, so keep only `id`, `from_email`, `type` and never print or save the rest.
- MCP `get_email_accounts` = `GET /email-accounts?limit=100&offset=N` (add `client_id=X` to scope), paginate until an empty or short page. Pull unfiltered when you need to catch `client_id: null` orphans. Do not print full objects, they include passwords.
- MCP `update_campaign_schedule`: REST equivalent not yet verified. Smartlead's public docs list `POST /campaigns/{id}/schedule` with `timezone`, `days_of_the_week`, `start_hour`, `end_hour`, `min_time_btw_emails`, and a daily lead cap whose field name differs between doc pages (`max_leads_per_day` vs `max_new_leads_per_day`). It is a write, so it was not probed. Canary one campaign on Pablo's go-ahead and re-fetch `GET /campaigns/{id}` to confirm.
- MCP `update_email_account_details` = `POST /email-accounts/{id}` with any of `max_email_per_day`, `time_to_wait_in_mins`, `signature`, `from_name` (documented in feedback_smartlead_api_lessons). Wrong patterns: `PUT /email-accounts/{id}`, `POST /email-accounts/{id}/update`.

- Limits: resolved per Pablo's chat 2026-10-22 forever rule (now in the standard above): caps are exact, Gmail 25, Outlook 6, SMTP 35, and the inbox gap is ALWAYS 20 min for every inbox type. No open question here.
- Fix step: inbox caps via `POST /email-accounts/{id}` are documented (gaps: report only unless Pablo asks); the campaign schedule fix has no verified REST equivalent yet (see above). Canary first, then bulk, then re-pull to verify.
