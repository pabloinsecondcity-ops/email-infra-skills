---
name: export-leads-by-status
description: "Use when Pablo asks to export every lead across a client's Smartlead campaigns filtered to one or more lead statuses (for example BLOCKED) and merge them into one CSV."
---

# Export Leads By Status

Trigger: "export all the leads for [client]", "give me a CSV of [status] leads across all campaigns", "pull every BLOCKED/COMPLETED/INPROGRESS lead for [client]".

Built and confirmed 2026-09-03 on Routeware (29 campaigns, 6,111 BLOCKED leads found).

---

## Step 1 -- Find the client and their campaigns

`mcp__smartlead__get_all_clients` to get the `client_id` (match by name).

`mcp__smartlead__get_campaigns(client_id=...)` to list every campaign (id + name). Note the total count -- you will process every one of them, including PAUSED/COMPLETED/DRAFTED, not just ACTIVE.

## Step 2 -- Export each campaign's leads, ONE AT A TIME

Call `mcp__smartlead__export_campaign_leads(campaign_id=...)` per campaign.

**Never call this in parallel across multiple campaigns.** Confirmed 2026-09-03: a batch of 10 parallel calls returned only 9 distinct results -- one campaign's export silently vanished with no error, which would have caused that campaign's leads to be dropped from the final file undetected. Sequential calls avoid this; each result is unambiguously tied to the campaign_id you just requested.

The result is usually too large for the tool response and gets saved to a local `.txt` file (the error message names the path). That file's content is:
```
Campaign leads export initiated:
"\"id\",\"campaign_lead_map_id\",\"status\",...\n\"1234\",...\n..."
```
Strip the `Campaign leads export initiated:\n` prefix, then `json.loads()` the remainder to unescape it into real CSV text:
```python
import json
content = open(path).read()
csv_text = json.loads(content[len("Campaign leads export initiated:\n"):])
```
A campaign with 0 leads returns inline (no file) as just the header row -- skip it, 0 rows to add.

CSV fieldnames (confirmed 2026-09-03, in this order): `id, campaign_lead_map_id, status, category, is_interested, created_at, first_name, last_name, email, phone_number, company_name, website, location, custom_fields, linkedin_profile, company_url, is_unsubscribed, unsubscribed_client_id_map, last_email_sequence_sent, open_count, click_count, reply_count`.

## Step 3 -- Filter and merge

Use `csv.DictReader` (via `io.StringIO(csv_text)`) to parse, filter rows where `status` matches the requested value(s), and `csv.writer` in append mode to add them to one master file with `campaign_id` and `campaign_name` prepended to the 22 fields above. Use Python's `csv` module for both read and write -- don't hand-roll parsing, `custom_fields` and other columns contain embedded commas/quotes.

Write the master CSV to `/workspace/` per [[feedback_domain_tracking]] and this repo's file-conventions rule -- **never into `clients/[name]/`**, that folder is context-only (icp.md, onboarding.md, context.md), no CSVs or raw data.

### Re-engagement pulls (Pablo, chats 2026-10-15 and 2026-10-22)

When the pull is for re-adding leads to a new campaign:
- Engagement means replies only; opens and clicks are not tracked.
- Remove real replies, unsubscribes and blocked leads.
- KEEP Out Of Office leads (chat 2026-10-22: "keep OOO in the list"), even though Smartlead logs OOO as a reply.
- Keep leads whose only issue is Sender Originated Bounce with no reply (the bounce was on our inbox side).
- Required custom fields (e.g. `{{Niche}}`) must come through the export; if one cannot be exported, do not upload (chat 2026-10-15). Leave out leads with that field empty, and show Pablo 5 sample rows first.
- The export itself never removes anything from any campaign (chat 2026-10-15: "don't remove anything from anywhere").

## Step 4 -- Delegate the bulk loop

For a client with 20+ campaigns, this is 20+ sequential large tool calls -- delegate to a background subagent with the full campaign_id/name list, the exact parsing recipe above, and the explicit "one at a time, no parallel calls" instruction, so it doesn't hit the same dropped-result issue. Have it report a per-campaign count table plus a grand total.

## Step 5 -- Independently verify before reporting to Pablo

Per [[feedback_verification_steps]], don't just trust the subagent's self-reported counts -- re-open the final master CSV yourself and confirm:
- every row's `status` actually matches what was requested (no leakage of other statuses)
- the row count matches the sum of per-campaign counts
- flag duplicate emails across campaigns if the client cares about that (a lead can be BLOCKED, or any other status, in more than one campaign)

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
- MCP `export_campaign_leads` = `GET /campaigns/{id}/leads-export` (verified 2026-10-22 with a read-only GET). It returns raw CSV text directly with the same 22-column header, so the `Campaign leads export initiated:` prefix strip and `json.loads` unescape step is not needed over REST. Still call it one campaign at a time.

- This is read-only. Output CSV goes to `/workspace/`, never into a client folder.
