---
name: disconnect-by-domain
description: "Use when Pablo gives a list of domains and wants their inboxes detached from all Smartlead campaigns, without pausing, resuming, or reassigning; discovery first, detach only on his go-ahead."
---

Imported from a Claude memory note, not a Claude skill file.

**Pattern: "disconnect these N domains from all campaigns" -- detach-only, no pause/resume, no reassignment.**

**Why:** 2026-08-10, Pablo supplied a UI screenshot list of 10 domains (whiparounds.xyz, whiparound.xyz, hellowhiparound.xyz, signwell.xyz, trysignwell.xyz, trymortarlink.xyz, mortarlinkteam.xyz, mortarlinkhub.xyz, mortarlinkai.xyz, cmaphub.xyz) spanning 4 clients (Whip Around 53626, SignWell 206631, Mortarlink 131885, CMAP 142333, mapped by brand-name-in-domain) and asked to detach every inbox on those domains from any campaign, explicitly "don't pause campaigns if they're active, simply disconnect inboxes and do nothing else." This is the disconnect-only variant already noted in [[project_smartlead_automation]] (2026-08-04 Whip Around entry) generalized into a repeatable two-script pattern.

**How to apply:**
1. Map each domain to its client by brand-name matching (confirm against [[project_client_roster]] client_ids).
2. Discovery script (`domain_detach_discover_v1.py` in `/workspace/`): for each client, paginate `GET /email-accounts?client_id=X` (100/page), filter `from_email` domain against the target set, collect matched account ids. Then for each client, pull its full campaign list (`GET /campaigns?client_id=X`, fallback to unfiltered `GET /campaigns` + client-side filter if it times out -- see [[feedback_smartlead_api_lessons]]) and for every campaign call `GET /campaigns/{id}/email-accounts`, intersecting with the matched id set. This is the reliable way to find attachments -- do NOT trust the bulk list's `campaign_count` field. Write two tracking CSVs (matched inboxes; detach plan per campaign) to `/workspace/` before touching anything, per [[feedback_domain_tracking]].
3. Show Pablo the plan (counts per client, which campaigns are ACTIVE vs DRAFTED, note any inbox duplicated across multiple campaigns) and flag that detaching from an ACTIVE campaign drops the leads assigned to that inbox. Wait for explicit go-ahead per [[feedback_step_by_step]] and [[feedback_no_unrequested_actions]] -- do not assume permission just because a similar script exists.
4. Execute script (`domain_detach_execute_v1.py`): reads the plan CSV, calls `DELETE /campaigns/{id}/email-accounts` with body `{"email_account_ids": [...]}` per campaign (confirmed endpoint, [[feedback_smartlead_api_lessons]]). Response is `{"ok": true, "result": N}` where N is the count removed -- use as an inline correctness check. Never call `update_campaign_status` in this variant -- Pablo was explicit campaigns stay in whatever state they're in.
5. Verify by re-running the same `GET /campaigns/{id}/email-accounts` intersection check across every campaign in the plan -- expect 0 overlap. Write results CSV.

**2026-08-10 run result:** 71 inboxes matched, 122 total campaign attachments (multi-campaign duplication -- especially total on Mortarlink's two "Subcontractors V3/V4" campaigns, every inbox on both) across 14 campaigns, all cleanly detached, verification passed with 0 remaining. See `/workspace/domain_detach_{matched_inboxes,plan,results}_2026-08-10.csv`.

Scripts are versioned one-offs (`_v1`) per [[feedback_domain_tracking]]-style tracking, not yet folded into `check_multi_campaign.py`/`redistribute_inboxes.py` -- ask Pablo if this recurs whether to formalize as a reusable script with a `--domains` flag.

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
- MCP `get_email_accounts` = `GET /email-accounts?limit=100&offset=N` (add `client_id=X` to scope), paginate until an empty or short page. Pull unfiltered when you need to catch `client_id: null` orphans. Do not print full objects, they include passwords.
- `GET /campaigns/{id}/email-accounts` (verified 2026-10-22 with a read-only GET) is the live roster of what is attached right now. Response objects include SMTP/IMAP passwords, so keep only `id`, `from_email`, `type` and never print or save the rest.
- MCP `delete_email_accounts_from_campaign` = `DELETE /campaigns/{id}/email-accounts` with `{"email_account_ids": [...]}`, returns `{"ok": true, "result": N}` (documented). Write action: only on Pablo's explicit go-ahead.

- `domain_detach_discover_v1.py` and `domain_detach_execute_v1.py` are not on the box; reproduce discovery with the paginated `GET /email-accounts` plus per-campaign rosters.
- The Friday weekly sweep routine never detaches; other tasks may detach when the task calls for it (Pablo, chat 2026-10-22). The execute step runs on Pablo's go-ahead for the plan (step 3).
