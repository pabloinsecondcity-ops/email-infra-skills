---
name: add-inboxes-to-campaigns
description: "Use when adding a named batch of unused Smartlead inboxes onto campaigns that already have inboxes \u2014 add-only (no pause/disconnect/redistribute). Always skip Auto-Refresh, always canary, always parallel membership checks, dry-run then go. Not for empty-campaign Day 14 assign or full-client rebalance."
---

# Add Inboxes to Campaigns (Add-Only)

Trigger phrases: "add these inboxes to campaigns", "put unused inboxes on active campaigns", "add-only assign", "don't redistribute, just add", "connect unused inboxes without redistributing".

## Which skill to use

| Skill | When | Touches existing memberships? |
|---|---|---|
| **assign-inboxes** | Target campaigns are **empty** (Day 14 / from scratch) | No (start empty) |
| **rebalance-inboxes-to-new-campaigns** | Client has running campaigns plus new ones; even counts across all (most common case, chat 2026-10-16) | Yes, removals from live campaigns once Pablo confirms the plan |
| **redistribute-inboxes** | Superseded by rebalance (Pablo, chat 2026-10-22) | Do not use |
| **This skill** | Named unused batch onto **already populated** campaigns | **No** - `POST` adds only |

If the user says add-only / campaigns already have inboxes / do not redistribute: **this skill**. Never run redistribute for that ask. Never require empty campaigns.

---

## Hard defaults (do not ask unless user overrides)

1. **Always skip Auto-Refresh campaigns** - exclude any campaign whose name contains `[Auto-Refresh]`, `Auto-Refresh`, or `Auto Refresh` (case-insensitive). Do not add to them. Do not ask each time; only include them if the user explicitly says to.
2. **Always canary** - before any bulk POST, add **one** planned inbox to the smallest eligible campaign chunk, re-fetch the roster, confirm delta `+1` and only that account id appeared. If extras appear: stop and report to Pablo with the exact unexpected ids. Do not continue bulk.
3. **Always parallel discovery** - when checking many inboxes for campaign membership or fetching many campaign rosters, use concurrent workers (about 10–15). Never serialize thousands of `GET /email-accounts/{id}` calls one-by-one.
4. **Follow-Up / Interested campaigns** - include in the **even split** by default (same share as other eligible ACTIVE campaigns). Only use a fixed small add if the user asks.
5. **Provider mix (Gmail / Outlook / SMTP, and vendors such as Zapmail and Mission Inbox)**: mix as much as possible by default (Pablo, chat 2026-10-22; replaces the old "ignore the split" default). Spread each provider type evenly across the target campaigns. If the pool is lopsided (for example Outlook-heavy), still spread what there is evenly and say so in the dry run; do not block on it.
6. **No pause, no disconnect, no remove** - never pause/resume campaigns; never `DELETE` campaign email-accounts except emergency canary rollback of unexpected extras; never delete Smartlead inboxes.
7. **Prefer REST** with `SMARTLEAD_API_KEY` over MCP for Smartlead.
8. **Step-by-step with the user** - dry-run plan CSV → wait for explicit go → canary → bulk → verify CSVs. Do not go beyond the literal ask.
9. **CSV as file downloads** when sharing plans/logs with the user - not screenshots/images of spreadsheets.

---

## Inputs to gather once (single batch) before writes

1. **Inbox pool** - explicit IDs, CSV, or verified filter (e.g. NOT_IN_USE after a tag change). Do **not** default to the client's full roster.
2. **Client mapping** - every inbox’s `client_id`; never mix clients when assigning.
3. **Campaign scope** - default: that client’s **ACTIVE** campaigns minus Auto-Refresh. Confirm only if the user named a subset or exceptions beyond Auto-Refresh.
4. Hold-tag date rules only if the pool still carries future `dont use until` / `warmup until` tags. Always exclude `WARMING UP - DONT USE YET` and `burned` inboxes (chat 2026-09-30).

---

## Ground-truth rules (lessons)

- Bulk `GET /email-accounts` fields `campaign_count` and sometimes `client_id` are **unreliable**. Never decide “unused” from `campaign_count`.
- Per-inbox truth: `GET /email-accounts/{id}?fetch_campaigns=true` → `campaign_ids` (parallelize).
- Per-campaign truth after assign: `GET /campaigns/{id}/email-accounts` roster. Do **not** use mailbox-statistics for live membership.
- Client campaigns: `GET /campaigns?client_id=X` when it works; if it times out, fetch unfiltered `GET /campaigns` and filter client-side.
- Never invent inbox personas. Never mix clients in one assign batch.

---

## Process

0. **Tracking / plan CSV first** (before any mutation):  
   `id, from_email, client_id, client_name, target_campaign_id, target_campaign_name, campaign_current_count, planned_action`
1. Build unused pool with parallel `fetch_campaigns=true` (or a verified CSV from that method). Status NOT_IN_USE = empty campaign_ids.
2. Per client: list ACTIVE campaigns; **drop Auto-Refresh**; sort remaining by campaign id ascending.
3. Even-split: `base, rem = divmod(n, k)`; first `rem` campaigns get `base+1`, rest `base`. Mix providers: group the inboxes by type (and vendor), then deal them round-robin across the campaigns so each one gets an even share of every type (chat 2026-10-22). Do not assign consecutive chunks sorted by account id, that clumps one provider onto one campaign. Each new inbox → exactly one campaign in this plan.
4. Write dry-run summary JSON + plan CSV. Show per-client table (unused count, eligible campaigns, split, skipped Auto-Refresh names). **Wait for go.**
5. **Canary** (mandatory): smallest chunk → POST one id → verify delta +1.
6. **Live**: group remaining plan rows by `target_campaign_id`. Per campaign: snapshot roster count → `POST /campaigns/{id}/email-accounts` with `{"email_account_ids":[...]}` (planned ids only; batches ≤100 if needed) → re-GET roster.
7. **Verify**: `after == before + planned_add`; every planned id present; no unexplained extras. Continue other campaigns if one fails only when safe; never retry with a larger unscoped id set.
7b. **Swap tags (forever step).** After the inboxes are added and verified on their campaigns, remove the tags 'WARMING UP - DONT USE YET' and any 'dont use until X' from those inboxes, and add the tag 'ACTIVE' instead. (Pablo, chat 2026-10-26, forever step, approved wording) Only for inboxes confirmed present on their target roster; read back tags after.
8. Artifacts:
   - `*_dry_run_plan.csv`
   - `*_execution_log.csv` (per inbox: OK / SKIPPED_CANARY / FAILED / MISSING_AFTER)
   - `*_campaign_verify.csv` (`before_count, planned_add, after_count, delta, missing_ids, ok`)
   - `*_execution_summary.json` (totals + per client)

---

## API

- Base: `https://server.smartlead.ai/api/v1`
- Add: `POST /campaigns/{campaign_id}/email-accounts?api_key=...`  
  Body: `{"email_account_ids": [..]}`  
  Success shape (observed): `{"ok": true, "result": [...], "added_count": N, "already_associated_count": M}` - still verify with roster GET; do not trust POST alone.
- Roster: `GET /campaigns/{id}/email-accounts`
- Account + campaigns: `GET /email-accounts/{id}?fetch_campaigns=true`
- Emergency canary rollback only: `DELETE /campaigns/{id}/email-accounts` + `{"email_account_ids":[...]}` for unexpected extras only

**Historical bug:** older sessions saw POST ignore `email_account_ids` and attach the whole client pool. Mandatory canary + roster delta check catch that before bulk damage. Selective add was confirmed working 2026-09-29 (`added_count: 1`, delta +1).

---

## What this skill must never do

- Pause / resume campaigns
- Disconnect-all or redistribute
- Remove existing campaign members (except canary rollback of unexpected new ids)
- Add to Auto-Refresh unless user explicitly overrides
- Assign the same inbox to multiple campaigns in one add-only plan
- Cross-client assignment
- Skip dry-run approval or skip canary
