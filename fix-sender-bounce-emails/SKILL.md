---
name: fix-sender-bounce-emails
description: "Use when Pablo says let's fix the sender bounce emails: the cross-client Smartlead sender bounce inbox audit (>5% per campaign, all statuses) that was paused 2026-07-30; resume from the recorded state."
---

Imported from a Claude memory note (resume anchor), not a Claude skill file.

**Trigger phrase:** When Pablo says "Let's fix the sender bounce emails" (or close to it), he means resume exactly this initiative -- pick up from here, don't re-derive the methodology from scratch.

**When it runs:** only when Pablo asks. The sender bounce >5% flag is never run daily, on a schedule, or automatically (Pablo, chat 2026-10-22).

**What this is:** Auditing every Smartlead inbox across every client for high SENDER bounce rate (not regular bounce rate), then fixing client by client -- deciding removal from campaigns and/or deletion, one client at a time, only on Pablo's explicit go-ahead.

**Status as of 2026-07-30:** Identification phase done for the whole account. Nothing has been removed or deleted yet except the RevPilots 150 (see below, Pablo did that himself before this session). We paused right after producing the final flat cross-client list -- next step is to start actually fixing clients one at a time, starting wherever Pablo wants when he resumes.

---

## Locked-in methodology (do not change without Pablo explicitly asking)

An inbox is "bad" if its own **sender bounce rate** (`sender_bounce_count / sent_count`) **within a single campaign** exceeds **5%**.

- Checked across ALL campaigns regardless of status (ACTIVE/PAUSED/COMPLETED/ARCHIVED/DRAFTED) -- not just active ones.
- Uses the `sender_bounce_count` field specifically from `GET /campaigns/{id}/mailbox-statistics`, NOT the generic `bounce_count` field (that includes recipient-side bad addresses, a lead-quality issue, not a sender-infra issue).
- Output format: flat CSV, **one row per (client, campaign, email)** -- plain columns only. Never combine campaign+rate into one text cell, never aggregate multiple campaigns into a single blended row unless explicitly asked. Columns used: `client, campaign, campaign_status, email, sent_count, sender_bounce_count, sender_bounce_rate_pct`.
- One client at a time. Do not suggest moving to the next client -- Pablo says explicitly when to proceed. Don't take any removal/deletion action without his go-ahead per client.

**Why this rule exists:** Earlier in this session I kept shifting the threshold and definition between messages (5% -> 3% -> a 1%+5% combo) and produced a CSV with a "detail" column crammed with text, which Pablo found unreadable and frustrating ("we are not even making any progress"). Also, Smartlead's bulk `/email-accounts` list endpoint returns `campaign_count: 0` for essentially everyone -- that field is unreliable/broken for checking current campaign connection; use `/campaigns/{id}/email-accounts` per-campaign instead to check what's actually connected right now.

---

## Files (in `pp-gtm` repo)

- **Script:** `integrations/find_high_sender_bounce_inboxes.py` -- run with `--threshold 5` (or any threshold) to regenerate the flat cross-client CSV. Pulls all clients -> all campaigns (any status) -> mailbox-statistics -> filters per-inbox sender bounce rate.
- **Cross-reference script:** `integrations/cross_reference_burned_inboxes.py` -- cross-references a flagged-inbox CSV against warmup reputation + all-time reply/bounce stats for one client. Less central now that the sender-bounce-rate-per-campaign rule above is the locked definition, but still useful for a deeper per-client look.
- **Latest full-account CSV (2026-07-30):** `/workspace/all_clients_sender_bounce_gt5pct_2026-07-30.csv` -- 3,088 rows, 1,531 unique inboxes, across 15 of 17 clients.

### Per-client breakdown (rows / unique inboxes), 2026-07-30 pull:

| Client | Rows | Unique inboxes |
|---|---|---|
| RevPilots | 1,412 | 511 |
| Wayne Selman (Signwell) | 419 | 173 |
| Arovy | 284 | 227 |
| Mike Flournoy | 244 | 126 |
| Adam Ilowite (Axero) | 190 | 68 |
| Routeware | 188 | 171 |
| Patrick McLaughlin | 90 | 45 |
| BMO Media | 86 | 86 |
| Jed Mahrle | 64 | 59 |
| cmap.io | 44 | 30 |
| Clay Christenson (Maven) | 21 | 3 |
| Brian (Spotlight Monitor) | 20 | 16 |
| GSD Associates | 17 | 9 |
| Gabe P | 8 | 6 |
| Reeba Magulick | 1 | 1 |

---

## Client-specific notes so far

**RevPilots** (deepest analysis done):
- 150 inboxes (`revpilotsservices.com` + `revpilotssolutions.com`, 75 each) confirmed dead by every real signal (92-94% bounce, ~1 reply combined across 3,236 sends). **Already removed from all campaigns by Pablo** before this session -- confirmed via direct campaign-level check (0 of 150 still connected).
- Under the locked 5%-per-campaign rule (all statuses), RevPilots has 511 unique bad inboxes, 1,412 flagged rows -- far more than the 150, because it includes inboxes on other lookalike domains (`revpilotstools.com`, `revpilotsstrategy.com`, `tryrevpilotsnow.com`, `revpilotshire.com`, `revpilotsales.com`, etc.) that are still currently connected to ACTIVE campaigns as of 2026-07-30.
- All 8 of RevPilots' ACTIVE campaigns individually stay under 5% sender bounce at the campaign-aggregate level (highest was 4.5%) -- the problem is diluted at the campaign level but real at the individual-inbox level.

**BMO Media:**
- 3 of 10 campaigns exceed 1% campaign-level sender bounce (Klaviyo TAM Over 25k: 5.16%, Klaviyo TAM Under 25k: 2.68%, TAM V2: 2.1%) -- all three PAUSED, not active.
- Only 1 campaign is ACTIVE (`BMO: Wrong Person [Auto-Refresh]`) and it's healthy (0.23%).
- 86 unique inboxes exceed 5% sender bounce rate within at least one campaign (see CSV, filter `client == "BMO Media"`).

**Other clients (Wayne Selman/Signwell, Arovy, Mike Flournoy, Adam Ilowite/Axero, Routeware, etc.):** identification done as part of the full-account pull, but no per-client deep dive (active-vs-paused breakdown, current campaign connection check) yet -- that's the work still ahead when Pablo resumes each one.

---

## Next step when resumed

Ask Pablo which client to start fixing first (don't assume, don't suggest RevPilots/BMO/next-alphabetical -- he decides). For whichever client he names:
1. Show the campaign-level sender bounce breakdown for that client (all statuses).
2. Show the flat list of inboxes exceeding 5% within flagged campaigns, filtered from the CSV above (or re-run fresh if data may have changed).
3. Wait for explicit go-ahead before removing from campaigns or deleting anything. Any deletion needs his explicit OK for that specific deletion (chat 2026-10-20). The Friday weekly sweep routine never detaches; other tasks may detach when the task calls for it (Pablo, chat 2026-10-22).

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

- The 2026-07-30 CSV lived in the pp-gtm repo `temp/` folder and is not on the box; re-run the audit to rebuild it.
