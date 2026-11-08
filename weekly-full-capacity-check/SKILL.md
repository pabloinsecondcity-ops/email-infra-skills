---
name: weekly-full-capacity-check
description: "Use for the recurring full capacity compliance sweep across every active Smartlead client, including the sending.ac Outlook reset pattern (cap=4, gap=120); report-only: caps not at exactly 25/6/35 (too high or too low), gaps and everything else are reported to Pablo, never fixed here."
---

# Weekly Full-Capacity Check (all clients)

Trigger: "check all clients for full capacity compliance" / "run the weekly compliance check" / "is anyone drifted out of the full-capacity standard" / weekly recurring once scheduled.

Built 2026-09-15, directly after fixing Jason Lee, Whip Around, Mortar Link, and CMAP and discovering that Jason Lee had already drifted (500/570 inboxes reverted) days after being fixed, see [[project_sending_ac_vendor_lock]]. This skill exists so drift gets caught on a cadence instead of by accident.

---

## Scope

Every active Smartlead client (`GET /client/`, cross-referenced against the canceled-client list in [[project_client_roster]], Smartlead's own client list is source of truth, names are often personal contact names not company names, e.g. Ben Mitchell = Mason Interactive). Exclude clients confirmed canceled.

## Process (report only; nothing gets fixed here)

Reuse `full-capacity-audit` skill Steps 2-5 exactly, per client, in one batched pass:

1. Pull `GET /campaigns` unfiltered once, filter client-side per client_id (avoids the 100+-campaign timeout on the filtered endpoint). The bulk response already includes `min_time_btwn_emails` and `scheduler_cron_value` inline, no per-campaign GET needed.
2. Pull each client's full inbox roster via `GET /email-accounts?client_id=X&limit=100&offset=0`, paginating to an empty page, never trust a single page.
3. For each active campaign: compliant if `min_time_btwn_emails == 25`.
4. For each Gmail/Outlook/SMTP inbox: compliant if `message_per_day` equals its type's exact number (Gmail 25, Outlook 6, SMTP 35; flag `!=` as too high or too low, chat 2026-10-22) AND `minTimeToWaitInMins == 20` (all types, chat 2026-10-22).
5. **Sending.ac drift flag:** any Outlook inbox found at `message_per_day=4` AND `minTimeToWaitInMins=120` gets called out specifically as "likely sending.ac reset" rather than lumped in as generic non-compliance, this is the vendor's known force-default, not a one-off misconfiguration (see [[project_sending_ac_vendor_lock]]). Gmail at 40 or 50/day is non-compliant (too high) and gets reported (caps are exact, chat 2026-10-22).

Can run all clients in parallel with a `ThreadPoolExecutor` for the inbox pagination (proven pattern from the CMAP/Whip Around/Mortar Link runs, 10-15 workers).

## Output

One consolidated table, one row per client: client name/id, active campaign count and how many are interval-compliant, total inboxes with type breakdown, compliant/non-compliant inbox counts, and a called-out count of "sending.ac-pattern" non-compliant Outlook inboxes specifically. Do not dump full per-inbox CSVs into chat, write them to `/workspace/` or the session scratchpad and only summarize.

**Report inboxes not at the exact cap, do not change them (Pablo, chat 2026-10-22, forever rule, approved wording).** "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own." List every Gmail inbox not at 25/day, every Outlook inbox not at 6/day and every SMTP inbox not at 35/day for Pablo, too high and too low separately (per client, per type, current values); he decides. Never raise or lower caps in this sweep. The exact 25/6/35 standard applies to every client. This includes sending.ac-pattern Outlook inboxes (cap 4); report them separately since they may get reset again (see [[project_sending_ac_vendor_lock]]). No delete. Gaps not at 20 min are monitored and reported to Pablo only, never fixed automatically (Pablo, chat 2026-10-22). Campaign intervals are reported only too; ask Pablo before any campaign fix from `full-capacity-audit`.

---

## Routine status (deferred)

Pablo wants this as an automatic weekly cloud routine eventually, but as of 2026-09-15 this is **not yet scheduled**, deferred because setting it up requires first authorizing the "Smartlead" connector at claude.ai/customize/connectors (cloud routines can't use the local Keychain API key or the local Smartlead MCP server the way an interactive session can). Until that connector is authorized and a routine is created via the `/schedule` skill (`RemoteTrigger` tool), run this skill manually when Pablo asks for a compliance check.

**When ready to actually schedule it:** use the `schedule` skill. It will need: the Smartlead connector authorized, a day/time (Pablo hasn't picked one yet), and a delivery preference (Pablo said "just leave it in the run log" for now, no proactive Slack ping needed). The routine's prompt should point at this skill file's process, not re-derive it from scratch.

## Related

- `full-capacity-audit` skill, the single-client audit+fix process this skill is built from
- [[feedback_full_capacity_campaign_setup]], the standard itself
- [[project_sending_ac_vendor_lock]], why Outlook inboxes specifically keep drifting, and current status of the vendor fix
- [[project_client_roster]], active vs canceled client_ids

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

- Scheduling: on Grok Bot this would be a routine (see the `routines` skill) using `SMARTLEAD_API_KEY` from the box env; the claude.ai connector blocker does not apply. Create it only if Pablo asks.
- Limits: resolved (Pablo, chat 2026-10-22, forever rule, approved wording): "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own."
