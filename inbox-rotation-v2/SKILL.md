---
name: inbox-rotation-v2
description: "Use for the inbox rotation workflow (detect burned inboxes, remove, replace, and reassign across Day 0 and Day 14), or when Pablo asks for a rotation check; the Friday weekly sweep tags only and never detaches, other steps run only on his confirmation, and nothing is deleted without his explicit OK."
---

# Inbox Rotation Workflow (v2)

Trigger: "Run rotation check", "Check inbox health", "Run rotate_inboxes", "Rotate inboxes"

Script: `integrations/rotate_inboxes_v5.py`

---

## Overview. 5 steps across Day 0 and Day 14

| Step | Day | What happens | Auto? |
|---|---|---|---|
| 1 | 0 | Detect bad inboxes (Rule 1 + Rule 2) | Report only |
| 2 | 0 | Remove from campaigns in Smartlead | Asks confirmation |
| 3 | 0 | Create replacement inboxes | Asks confirmation |
| 4 | 14 | Delete bad inboxes from Smartlead, MI, Zapmail | Asks confirmation |
| 5 | 14 | Assign new inboxes to campaigns | Asks confirmation |

Nothing executes without explicit "yes" from Pablo.

**Current rules from Pablo's chats (override the Claude recipe below where they conflict):**
- Burned (chat 2026-10-13) = warmup reputation under 90% (0% means warmup off, excluded) AND 0 lifetime replies. Auto-replies and OOO count as replies (chat 2026-10-13), so low-rep inboxes with any reply stay.
- OOO and other auto-replies (for example no longer with the company, ticket acknowledgments) count as replies for burned and healthy, but not as human/positive replies in reply-rate scoring (Pablo, chat 2026-10-22).
- Skip any inbox tagged `WARMING UP - DONT USE YET`; it is not burned, it just has not sent yet (chat 2026-10-15).
- Friday weekly sweep routine action (chat 2026-10-13, tightened 2026-10-20): tag burned inboxes `burned` in Smartlead and their domains `burned` in Zapmail, and list the campaigns they are on. The sweep does not detach, does not delete, and does not schedule Zapmail removal. Pablo reviews and deletes manually. The Friday weekly sweep routine never detaches; other tasks may detach when the task calls for it (Pablo, chat 2026-10-22).
- Reply counts for the routine use the slow, accurate method; the fast endpoint stays in `smartlead-per-inbox-reply-counts-fast` for quick checks only (chat 2026-10-13).
- Email report format (chats 2026-09-30 and 2026-10-07): headcounts per client so Pablo knows how many to replace; Gmail section first (single inboxes are fine), Outlook second grouped by domain only, domains in plain text (no URLs), totals at the bottom.
- 250 Gmail inboxes per client is the top goal (chat 2026-10-20). Rocket (Rocket Shipping) and Maven (Maven Analytics) are permanently excluded from the 250 count (Pablo, chat 2026-10-22). Mortar Link is undecided: do not count it either way on your own, ask Pablo each time it matters. Flag any counted client that would drop below it.
- Mission Inbox is a valid, active provider again (Pablo, chat 2026-10-22): it went away and came back, and there are about 900 MI inboxes that are not assigned to campaigns yet. Include MI inboxes in pools, sweeps and audits like any other provider. MI API steps still need a `MISSION_INBOX_API_KEY` env var on the box (ask Pablo; never paste a key into chat or a skill).

---

## Step 1. Detect (Day 0)

### Rule 1. On-request check
Runs only when Pablo asks. Never run it daily, on a schedule, or automatically (Pablo, chat 2026-10-22). For the weekly burned sweep, use Pablo's burned definition above (chat 2026-10-13), not this rule.

Flags an inbox as BAD if ALL THREE are true:
- Warmup reputation between 1% and 94% (0% = warmup off, excluded)
- Bounce rate > 5%
- Reply rate = 0%

### Rule 2. On-request campaign bounce check
Runs only when Pablo asks (rare). Never run it weekly, on a schedule, or automatically (Pablo, chat 2026-10-22).

Flags a campaign if sender bounce rate > 5%, then lists which inboxes caused it.
Source: `sender_bounce_count` from `GET /campaigns/{id}/mailbox-statistics`

### How to run

```bash
cd /workspace/pp-gtm

# Both rules, all clients (only when Pablo asks)
python3 integrations/rotate_inboxes_v5.py

# Rule 1 only (only when Pablo asks)
python3 integrations/rotate_inboxes_v5.py --rule 1

# Rule 2 only (only when Pablo asks)
python3 integrations/rotate_inboxes_v5.py --rule 2

# Single client
python3 integrations/rotate_inboxes_v5.py --client "Routeware"

# Custom CSV path
python3 integrations/rotate_inboxes_v5.py --csv /path/to/output.csv
```

CSV saved to `/workspace/rule1_YYYY-MM-DD.csv` by default.

---

## Step 2. Remove from campaigns (Day 0)

The Friday weekly sweep routine never detaches; other tasks may detach when the task calls for it (Pablo, chat 2026-10-22). This step never runs inside the Friday sweep; outside it, run it only after Pablo says yes to the list.

After the report, the script asks:

```
Remove these inboxes from campaigns? (yes/no):
```

Type `yes` to proceed. Type anything else to stop, no changes are made.

What it does: calls `DELETE /campaigns/{id}/email-accounts` for each flagged inbox across every campaign it appears in. The inbox is disconnected from campaigns but still exists in Smartlead.

What it does NOT do: delete the inbox from Smartlead. That is Step 4.

---

## Step 3. Create replacement inboxes (Day 0)

Same count as removed. Follow the full provisioning pipeline from `email-infra` skill:

1. Generate brand-adjacent domain candidates, confirm with Pablo before purchasing
2. Buy domains on Dynadot (.com only)
3. Create inboxes in Mission Inbox or Zapmail
4. Push DNS, verify domains, create mailboxes
5. Import into Smartlead, start warmup
6. Log to `quarantine_log.csv`: email, domain, client_id, removed_at, delete_after (Day 14)

Wait 14 days before assigning to campaigns.

---

## Step 4. Delete bad inboxes (Day 14)

**Deletion gate (chat 2026-10-20: "don't ever delet things without my authorization").** Never delete anything (Smartlead, Zapmail, Mission Inbox, anywhere) without Pablo's explicit OK for that specific deletion. No Zapmail removal scheduling. Default instead: tag and list, Pablo deletes manually.

After the Step 2 confirmation, the script asks a second time:

```
Delete these inboxes from Smartlead and export provider CSV? (yes/no):
```

**What it does automatically:**
- Deletes each inbox from Smartlead via `DELETE /email-accounts/{id}` (confirmed working)
- Exports `/workspace/deletion_YYYY-MM-DD.csv` with columns: client, email, provider, smartlead_id, deleted_from_smartlead

**What requires manual action:**
- Zapmail: Zapmail's deletion API does not support individual mailbox IDs (only full domains). Log into the Zapmail UI, find the inbox by domain, and schedule removal from there.
- Mission Inbox: `POST /api/mailboxes/bulk-delete` is documented but not yet tested. Treat as manual until confirmed.

**How to use the CSV:**
Open `/workspace/deletion_YYYY-MM-DD.csv`. The `provider` column (Zapmail, Mission Inbox, Google Workspace) tells you exactly where to go to finish the deletion manually for each inbox.

**Provider detection:** inferred from `smtp_host` in Smartlead's `/email-accounts` response.

---

## Step 5. Assign new inboxes to campaigns (Day 14)

New inboxes are warmed and ready. Use `assign_inboxes.py`:

```bash
python3 integrations/assign_inboxes.py \
  --client "GSD Associates" \
  --campaigns "GSD - Founders" "GSD - Charlotte" \
  --dry-run   # preview first

python3 integrations/assign_inboxes.py \
  --client "GSD Associates" \
  --campaigns "GSD - Founders" "GSD - Charlotte"
```

Always dry-run first. Campaigns must be empty before assigning.
See `assign-inboxes` skill for full usage.

Per Pablo (chat 2026-10-16): `assign-inboxes` is for NEW clients only. For an existing client, add replacement inboxes with `add-inboxes-to-campaigns` (add-only) or `rebalance-inboxes-to-new-campaigns` (the most common case when new campaigns were created).

---

## Technical notes

- 15 parallel workers (ThreadPoolExecutor), required for large clients, avoids timeout
- Per-inbox stats aggregated from `GET /campaigns/{id}/mailbox-statistics` across all campaigns
- Warmup reputation from `warmup_details.warmup_reputation` in `/email-accounts`
- Provider detected from `smtp_host` field in `/email-accounts` response
- `email_account_id` always fetched via `.get()` with None guard, ID is never assumed present
- `global_email_map` is populated from `/email-accounts` (primary source) not from stats rows
- Inbox IDs flow as integers throughout, never derived from email address
- Smartlead deletion: `DELETE /email-accounts/{id}` returns `{"ok": true}` on success
- Zapmail MCP (`zapmail-mcp` via npx): read-only endpoints work, write/delete endpoints return 404, use Zapmail UI for manual deletion

---

## Related files

- `integrations/rotate_inboxes_v5.py`, the script (Steps 1, 2, 4)
- `integrations/assign_inboxes.py`, Step 5 assignment
- `assign-inboxes` skill, assignment skill doc
- `email-infra` skill, full provisioning pipeline for Step 3
- `knowledge/deliverability_v2.md`, rotation rules reference

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
- `GET /campaigns/{id}/mailbox-statistics?limit=100&offset=0` (verified 2026-10-22 with a read-only GET; rows have `email_account_id`, `from_email`, `sent_count`, `reply_count`, `bounce_count`, `sender_bounce_count`).
- `GET /campaigns/{id}/email-accounts` (verified 2026-10-22 with a read-only GET) is the live roster of what is attached right now. Response objects include SMTP/IMAP passwords, so keep only `id`, `from_email`, `type` and never print or save the rest.
- MCP `delete_email_accounts_from_campaign` = `DELETE /campaigns/{id}/email-accounts` with `{"email_account_ids": [...]}`, returns `{"ok": true, "result": N}` (documented). Write action: only on Pablo's explicit go-ahead.
- MCP `get_campaign_by_id` = `GET /campaigns/{id}` (verified 2026-10-22 with a read-only GET; includes `status`, `client_id`, `scheduler_cron_value`, `min_time_btwn_emails`, `max_leads_per_day`). `GET /campaigns/{id}/schedule` returns 404 (re-confirmed).

- `rotate_inboxes_v5.py` (and the v1 `rotate_inboxes_v2.py`) are not on the box. Rule 1 inputs (warmup reputation, bounce, reply) come from `GET /email-accounts` warmup fields; Rule 2 (campaign sender bounce >5%) comes from `mailbox-statistics` `sender_bounce_count / sent_count`.
- Steps 2 and 4 include detach and delete actions. Deletion needs Pablo's explicit authorization every time. Detaching (Step 2) runs on his yes; the Friday weekly sweep routine never detaches.
- Zapmail: use the `user-Zapmail` MCP connector (read tools such as `list_workspaces`, `list_domains`, `list_mailboxes`, `get_mailbox_details`, `check_dns_records`, `get_export_status` are safe). Write tools (`provision_mailboxes`, `assign_mailboxes`, `export_mailboxes_to_third_party`, `schedule_mailbox_removal`) need Pablo's explicit go-ahead. Note: the connector's `schedule_mailbox_removal` describes removal of a specific set of mailboxes by ID, which contradicts the older Claude note that Zapmail deletion cannot target individual mailbox IDs. Not tested (it is a delete).
- Mission Inbox: valid provider again (chat 2026-10-22, about 900 unassigned MI inboxes). API `https://api.v4.missioninbox.com` with header `X-Server-API-Key`. No Mission Inbox key is on the box, so MI API steps are not runnable yet; Smartlead-side checks on MI inboxes still run. REST equivalent not yet verified from here; ask Pablo to add the key as an env var (never paste it into a skill or chat).
- Pablo's burned definition (chat 2026-10-13) wins over Rule 1 here for the weekly sweep: warmup reputation under 90% (excluding 0%) AND 0 lifetime replies, OOO and auto-replies counting as replies. See the rules block at the top.

---

## Reference: legacy inbox-rotation (v1, superseded by v2 above)

Imported from Claude Code `skills/inbox-rotation.md` for reference only. The script `rotate_inboxes_v2.py` is not on the box.

Trigger: "Run rotation check" or "Check inbox health" or "Run rotate_inboxes". Mode: Report only. No actions taken automatically.

Rule 1 (was daily; now only when Pablo asks, chat 2026-10-22): BAD if warmup reputation between 1% and 94% (0% means warmup is off, excluded), bounce rate > 5%, and reply rate = 0%. Rule 2 (was weekly; now only when Pablo asks, chat 2026-10-22): flags a campaign if sender bounce rate > 5%, then lists which specific inboxes caused those sender bounces. Source field: `sender_bounce_count` from `GET /campaigns/{id}/mailbox-statistics`.

Rule 1 output CSV columns: `client`, `email`, `warmup_reputation`, `bounce_rate`, `reply_rate`, `sent_count`, `status` (`good` or `BAD`). Rule 2 output: campaign name and status, sender bounce count / total sent = sender bounce rate, list of inboxes with sender_bounce_count > 0.

What to do with flagged inboxes (after review): 1. Remove flagged inboxes from campaigns in Smartlead. 2. Create replacement inboxes in Mission Inbox or Zapmail. 3. Start warmup for new inboxes in Smartlead. 4. Log to quarantine_log.csv: email, domain, client_id, removed_at, delete_after (Day 14). 5. On Day 14: connect new inboxes, delete bad ones from Smartlead + MI + Zapmail.

Technical notes: 15 parallel workers (ThreadPoolExecutor) to fetch campaign stats, required for large clients, otherwise times out. Per-inbox stats are aggregated from `GET /campaigns/{id}/mailbox-statistics` across all campaigns. Warmup reputation comes from `warmup_details.warmup_reputation` in `/email-accounts`. sender_bounce_count is NOT available on a per-inbox basis outside of campaign context.
