---
name: clean-up-inboxes-smartlead
description: "Use when Pablo says clean up our inboxes from Smartlead (or similar): per client, active campaigns only, flag inboxes with sender bounce >5% and 0 replies in that campaign, write a CSV, and disconnect them from those campaigns only on his go-ahead."
---

Imported from a Claude memory note (resume anchor), not a Claude skill file.

**Trigger phrase:** When Pablo says "clean up our inboxes from Smartlead" (or close to it), run this locked methodology -- don't re-derive it from scratch, don't ask him to re-explain the rule.

## Locked methodology

An inbox qualifies for disconnect if, within a single **ACTIVE** campaign (active only -- not paused/completed/stopped/drafted, which is what distinguishes this from the older [[fix-sender-bounce-emails]] (skill) initiative):
- sender bounce rate (`sender_bounce_count / sent_count`) **> 5%**
- **AND** `reply_count == 0` within that same campaign

Both conditions required together. Sender bounce alone is not enough -- confirmed via a same-day comparison: SignWell's flagged inboxes were all very-low-volume (1-90 sends) and 0-for-7 on replies, but Whip Around's flagged inboxes ran much higher volume and 42 of 108 (39%) had at least one reply despite exceeding 5% bounce. The 0-reply condition is what correctly filters out inboxes that are still functioning from ones that are actually burned.

## Action

The Friday weekly sweep routine never detaches; other tasks may detach when the task calls for it (Pablo, chat 2026-10-22).

**Disconnect only** (`DELETE /campaigns/{id}/email-accounts` or MCP `delete_email_accounts_from_campaign`) -- detach flagged inboxes from the campaigns they were flagged in. Do **not** delete from Smartlead as part of this standing methodology.

**Verification pattern:** always re-check via a live `GET /campaigns/{id}/email-accounts` roster fetch after disconnecting, and confirm the target IDs are actually absent. Do NOT trust `mailbox-statistics` for this -- that endpoint is historical/aggregate and keeps showing inboxes as present even after they've been disconnected (discovered during the SignWell run, 2026-08-04).

## Process per client

1. Pull all campaigns for the client, filter to `status == ACTIVE`.
2. Pull `mailbox-statistics` per active campaign (need `sent_count`, `sender_bounce_count`, `reply_count`, `email_account_id`, `from_email`).
3. Flag rows where `sent_count > 0`, sender bounce rate `> 5%`, `reply_count == 0`.
4. Save flagged list to a per-client CSV (pattern used: `/workspace/burned_{client}_{date}.csv`).
5. Group flagged rows by campaign, disconnect each group via the campaign's email-accounts endpoint.
6. Verify every disconnect via the live campaign roster (not mailbox-statistics).
7. Produce one combined report CSV with a `disconnect_status` column (`CONFIRMED_REMOVED` / still-present) so Pablo has a record of exactly what was touched.

## Clients already run through this methodology (2026-08-04/05 pass)

Whip Around (53626), Routeware (350583), Arovy (321558), Axero (178500), SignWell (206631), Practical Prospecting (53675), BMO Media (411869), cmap.io (142333), Mortar Link (131885) -- 391 flagged rows / 360 unique inboxes disconnected across all 9, 0 failures on verification. Client IDs also cross-referenced in [[project_smartlead_automation]].

If Pablo names a client NOT in this list, run the same process fresh for it -- the methodology isn't client-specific, just the initial run was scoped to these 9.

## Relationship to the older sender-bounce project

[[fix-sender-bounce-emails]] (skill) used a broader, unconfirmed rule (sender bounce >5% across ALL campaign statuses, no reply filter) and never got past identification for most clients. This "clean up inboxes" methodology is the refined, action-ready successor -- active campaigns only, reply-confirmed, disconnect immediately per client. Treat "clean up our inboxes from Smartlead" as the trigger for THIS methodology specifically, distinct from "let's fix the sender bounce emails."

## Deletion is NOT part of this standing rule

On 2026-08-05, Pablo had 391 of these disconnected inboxes permanently deleted from Smartlead in the same session, but explicitly called it a one-time exception and asked that the deletion step itself not be saved to memory -- only the identify-and-disconnect methodology above. **Do not delete from Smartlead by default when this trigger phrase is used again** -- disconnect only, and if Pablo asks for deletion on top of it, treat that as a fresh explicit ask each time (confirm scope/pacing per [[feedback_step_by_step]], not a standing permission).

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
- `GET /campaigns/{id}/mailbox-statistics?limit=100&offset=0` (verified 2026-10-22 with a read-only GET; rows have `email_account_id`, `from_email`, `sent_count`, `reply_count`, `bounce_count`, `sender_bounce_count`).
- `GET /campaigns/{id}/email-accounts` (verified 2026-10-22 with a read-only GET) is the live roster of what is attached right now. Response objects include SMTP/IMAP passwords, so keep only `id`, `from_email`, `type` and never print or save the rest.
- MCP `delete_email_accounts_from_campaign` = `DELETE /campaigns/{id}/email-accounts` with `{"email_account_ids": [...]}`, returns `{"ok": true, "result": N}` (documented). Write action: only on Pablo's explicit go-ahead.

- The old "don't even detach from campaigns" rule applies only to the Friday weekly sweep routine, not to this skill (Pablo, chat 2026-10-22). Disconnect on his go-ahead as described above; deleting still needs his explicit OK.
