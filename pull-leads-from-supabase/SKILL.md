---
name: pull-leads-from-supabase
description: >-
  Use when Pablo says get me all of [client]'s leads from Supabase or pull
  [client]'s lead history: export every warehouse lead for one client with
  last-sent, replied and bounced flags and category into a CSV.
---
# Pull Leads Out Of Supabase (By Client)

Trigger: "get all of [client]'s leads from Supabase" / "pull [client]'s leads out of the warehouse" / "give me [client]'s lead history."

Built and confirmed 2026-08-11 for Arovy (client_id 321558): 17 campaigns, 104,732 raw campaign-lead rows, 66,069 unique leads, 65,632 matched a contact record.

Schema and event-flow background: [supabase-warehouse.md](../knowledge/supabase-warehouse/supabase-warehouse.md). Query patterns this skill is based on: [lead-recycling-last-email-sent.md](../knowledge/supabase-warehouse/lead-recycling-last-email-sent.md).

---

## Before you start

Credentials: `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` live in `pp-gtm/.env` (gitignored). See [[reference_supabase_warehouse_creds]].

**Load them correctly -- two gotchas that will silently break this:**

1. Shell state does not persist between separate tool calls in this environment. Everything below has to run in one shell invocation per step -- don't `source .env` in one command and expect a later command to still have it.
2. The `.env` file's lines are plain `KEY=value`, not `export KEY=value`. `source .env` alone only sets shell variables, which bash itself can still expand inside a `curl` command line -- but a Python subprocess spawned after won't see them. Use `set -a && source .env && set +a` before invoking Python so the vars actually export into the process environment.

**Also:** on this machine, Python's stdlib `urllib` fails Supabase's TLS handshake (`CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`) -- the Python.org build's cert bundle doesn't have the right root. `curl` uses the system trust store and works fine. Any Python enrichment step should shell out to `curl` via `subprocess`, not use `urllib.request` directly.

Get the client's Smartlead client_id first (not a Supabase-internal id -- `wh_campaigns.client_id` is the same numeric Smartlead client_id). Check [[project_client_roster]] or `clients.yaml`, and confirm active status before pulling.

---

## Step 1 -- Get the client's campaign IDs

```bash
cd pp-gtm
set -a && source .env && set +a
curl -s "${SUPABASE_URL}/rest/v1/wh_campaigns?client_id=eq.<CLIENT_ID>&select=smartlead_campaign_id,name,status,client_id" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -o /workspace/<client>_campaigns.json
```

Sanity-check the returned campaign names actually look like the client's before continuing.

## Step 2 -- Pull campaign-lead rows, paginated

PostgREST caps at 1000 rows per request regardless of `limit`. Loop on `offset` in steps of 1000 until a page comes back with fewer than 1000 rows. Filter with `smartlead_campaign_id=in.(<id1>,<id2>,...)` using the IDs from Step 1. Needed fields: `lead_email,last_sent_at,replied,is_bounced,lead_category,smartlead_campaign_id`.

Write each page's rows to a `.jsonl` file as you go rather than holding one giant array -- Arovy alone was 105 pages / 104,732 rows.

## Step 3 -- Aggregate to one row per lead

The same email can appear once per campaign. Group by lowercased `lead_email` and take:
- `last_sent_at` = max across all campaigns for this client
- `replied` = true if true in any campaign row
- `is_bounced` = true if true in any campaign row
- `lead_category` = category from whichever row had the max `last_sent_at`
- `campaign_count_seen` = count of rows for that email

## Step 4 -- Enrich with contact detail

`wh_contacts` is a global table (no client scoping), so batch the aggregated email list -- 250 emails per request is a safe URL length -- and query `email=in.(...)` with `select=email,first_name,last_name,company_name,company_domain,linkedin_url`. Run batches concurrently (a `ThreadPoolExecutor`, 5-6 workers, via `curl` subprocess per the SSL note above) -- sequential requests for tens of thousands of leads would take too long.

Not every lead will match a contact row -- that's expected (e.g. old rows, or a lead only ever touched at the campaign-lead level). Report the match rate.

## Step 5 -- Write the CSV

Columns: `email, first_name, last_name, company_name, company_domain, linkedin_url, last_email_sent_at, has_replied, has_bounced, lead_category, campaign_count_seen`. Sort by `last_email_sent_at` descending (most recently emailed first). Write to `/workspace/<client>-leads-full-<date>.csv` -- `/workspace/` is a staging spot per workspace rules, not a permanent home, so confirm with Pablo where the file should actually end up (Sheet, back into Smartlead, etc.) once it's built.

Report back: total unique leads, replied count, bounced count, top lead_category breakdown -- this is what lets Pablo sanity-check the pull before using it for anything.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22). The recipe above is Pablo's original text; this section only maps it to the tools available here.

- Files: write CSVs and scratch output to `/workspace/` (replaces `temp/`).
- Scripts under `integrations/` live in Pablo's pp-gtm repo, not on the box. The client folders (`clients/[folder]/...`, `clients/registry.md`), `knowledge/` and `context/` files are also in that repo and not on the box; ask Pablo for the content or a copy before running this.
- Smartlead, where used: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key).
- Standing rules still apply: never invent facts or names, no writes to Smartlead/HeyReach/Slack without Pablo's explicit go-ahead, no em dashes.

- Supabase: `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are not in the box env, so the warehouse steps are not runnable yet. Ask Pablo to add them as env vars (never paste them into a skill or chat). Not verified from the box.
- The macOS TLS gotcha in this recipe may not apply on the Linux box; untested.
- Read-only. Output to `/workspace/`.
