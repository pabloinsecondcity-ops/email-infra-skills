---
name: list-request
description: "Use when a list request comes in (build a list for [client] campaign, list request for [client]): check what we already have, build the gap, enrich, dedupe against the campaign, and prepare for upload pending GTME approval."
---

# Skill: list-request

**Trigger:** "build a list for [client] campaign" / "list request for [client]"

**Who runs this:** GTME when a list request comes in via #list-requests Slack channel.

**What it does:** Fulfills a list request end-to-end: checks what we already have, builds the gap, enriches emails, dedupes against the campaign, and prepares for upload. GTME approves before anything is pushed to Smartlead/HeyReach.

---

## Before you start

Get the list request and extract: **Client**; **Campaign** (name or Smartlead URL); **Due date**; **Volume**; **Special instructions** (new segment, signal, different persona).

Drop a waiting emoji in the Slack thread to confirm receipt.

Then read `clients/[folder]/icp.md` (ICP criteria, qualifier prompt, keyword lists, custom fields, TAM type) and `clients/[folder]/context.md` (campaigns running, what's been tried).

---

## STEP 1. Check what we already have

**A) Warehouse lookup:** `GET https://command-center-one-drab.vercel.app/api/warehouse/lookup?linkedin_url=[url]` with header `X-API-Key: $WAREHOUSE_API_KEY`. Bulk: `node integrations/scripts/lookup-emails-by-linkedin.mjs /workspace/[client]-candidates.csv`. Report the hit rate; if 30%+ is already in the warehouse, note the enrichment cost saved.

**B) Existing Clay TAM:** ask the GTME whether a Clay table exists from the original TAM build with qualified contacts not yet pushed to this campaign. If yes, pull those first. Always repurpose before rebuilding.

**C) What's already in the campaign:** dedupe against existing campaign leads (`integrations/smartlead-dedup.ts` with `CAMPAIGN_ID`, `WF_INPUT`, `WF_OUTPUT`).

---

## STEP 2. Assess the gap

Report: contacts available from warehouse / existing Clay TAM; already in campaign (deduped); net new available without new build; additional leads needed. If net new meets the volume, skip to STEP 6. Otherwise STEP 3.

---

## STEP 3. Build the gap

Only build what's needed. Do not over-build.

**Check the TAM ceiling first.** If at the ceiling, flag to AM: "Hey, we've hit the TAM limit for this segment. Do you want to re-engage the previous list, or are you fine moving forward with what's left?" If they want re-engagement, follow the re-engagement path below.

**If TAM remains:** use `clients/[folder]/icp.md` for list source, LinkedIn industries, keyword lists, and qualifier prompt. Follow `tam-build` STEP 3-7 but only for the volume needed.

Data providers, most credits first: SmartProspect 370k/mo; LeadMagic 250k/mo; Prospeo 150k/mo; ZoomInfo free via Instant Data Scraper.

**Always maximize TAM:** if the list comes back under 5,000 leads total, look for more TAM first (expand filters, adjacent segments, related titles) before declaring a ceiling.

---

## STEP 4. Run ICP qualifier (if new companies pulled)

Run the qualifier from `icp.md`. Parallel batches of 50; each visits the website and returns `ICP_FIT: YES or NO` + `REASONING`. Spot-check 10-20 results before the full batch.

---

## STEP 5. Find emails (waterfall)

`integrations/email-waterfall.ts` (`WF_INPUT`, `WF_OUTPUT`). Order: 1. Warehouse (free, always first) 2. Prospeo 3. LeadMagic 4. IcyPeas 5. TryKitt. Report total contacts, emails found, hit rate %, breakdown by provider.

---

## STEP 6. Enrich custom fields

Read the Active Campaign Custom Fields from `icp.md` and enrich every required field. Spot-check: paste 5 enriched contacts into the template and read as the prospect. Every custom field must flow grammatically. Fix before proceeding.

---

## STEP 7. Final dedup against campaign

Run a final dedup against the Smartlead campaign to confirm net new count.

---

## STEP 8. GTME approval gate

Post a summary before uploading:

```
List request ready for your review -- [Client], [Campaign name]
Total built: [count]
Already in campaign (removed): [count]
Net new ready to upload: [count]
Email hit rate: [%]
Custom fields mapped: [list]
File: /workspace/[client]-contacts-final.csv
Ready to push to Smartlead. Reply with approve to upload, or flag anything to fix first.
```

**Do not upload until the GTME or AM explicitly approves.**

---

## STEP 9. Upload to campaign

After approval: Smartlead upload (or via the Smartlead integration in Clay). QA custom field mapping before notifying AM. HeyReach: 500 contacts max, warmest leads only, QA before notifying AM.

---

## STEP 10. Complete the request

Drop a check emoji in the Slack thread and tag the AM; update `clients/[folder]/context.md` Campaign Status Notes with what was pushed and when; update the campaign tracker if applicable.

---

## Re-engagement path

If the AM chooses re-engagement when TAM is tapped:

**AM's responsibility:** copy the existing campaign in Smartlead; rename with a "Re-Engage" tag; update messaging (cannot use the same copy); ping the GTME once set up.

**GTME's responsibility (this skill):**
- Pull all leads from the original campaign who did NOT reply, did NOT unsubscribe and are NOT blocked (Pablo, chat 2026-10-22)
- Push those leads into the new re-engagement campaign
- Do not include anyone who replied (positive or negative), unsubscribed or was blocked
- KEEP Out Of Office leads; OOO is not engagement (chat 2026-10-22). Keep Sender Originated Bounce leads with no reply.
- Do not pre-skip leads that already exist in the target or other campaigns; upload them all and let Smartlead reject true duplicates (chat 2026-10-22)
- Map fields one to one: first name to first name, company name to company name, and so on (chat 2026-10-22)

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key).
  - Pull leads: `GET /campaigns/{id}/leads-export` returns raw CSV (columns include status, category, email, first_name, last_name, company_name, custom_fields, is_unsubscribed, reply_count). One campaign at a time, never in parallel.
  - Re-engagement filter (Pablo, 2026-10-22): remove replied (reply_count > 0 or replied status/category), unsubscribed, and blocked. Engagement means replies only; opens and clicks aren't tracked. Keep Out Of Office (category Out Of Office) leads. See `export-leads-by-status`.
  - Upload: `POST /campaigns/{id}/leads` with `lead_list` (max 100 per call) and settings `ignore_global_block_list: false`, `ignore_unsubscribe_list: false`, `ignore_duplicate_leads_in_other_campaign: true` for re-engagement. Map fields one to one, custom_fields as a dict. Canary 5 leads and read them back before the rest. Write: only on Pablo's explicit go-ahead.
- Pp-gtm scripts (`smartlead.py`, `smartlead-dedup.ts`, `email-waterfall.ts`, lookup script) are not on the box. Warehouse/Supabase keys are not in the box env.
- No Slack connector for #list-requests; Clay, HeyReach and Prospeo are not connected.
