---
name: tam-build
description: >-
  Use when someone says build the TAM for [client] or start TAM build after the
  client approved the ICP guide: build the full Total Addressable Market from
  ICP-qualified companies through enriched contacts ready for Smartlead or
  HeyReach.
---
# Skill: tam-build

**Trigger:** "build the TAM for [client]" / "start TAM build"

**Who runs this:** GTME (Pablo or Jaimin) after the client approved the ICP guide from `onboarding-icp`.

**What it does:** Builds the full Total Addressable Market for a new client, from ICP-qualified company list through enriched contacts uploaded to Smartlead/HeyReach. One-time build per client; all future list requests pull from this TAM.

**Prerequisites:** `clients/[folder]/icp.md` exists with client approval; `clients/[folder]/onboarding.md` exists; ICP qualifier prompt saved in icp.md.

---

## Before you start

Read `icp.md` (criteria, segments, TAM config, qualifier prompt, keyword lists) and `onboarding.md`. Confirm with the GTME: "Which segments are we building first? All in one pass or prioritizing one?"

---

## STEP 1. Confirm ICP and segments

Summarize: client and target segments; list source; expected TAM size (estimate); contact approach (company-first or contact-first). Ask: "Does this match your understanding? Any changes before we start?" **Approval gate.**

## STEP 2. Check for overlapping TAM

Ask whether another client has an overlapping TAM to repurpose or cross-reference. Also sample the warehouse (`GET https://command-center-one-drab.vercel.app/api/warehouse/lookup?linkedin_url=[sample_url]`, header `X-API-Key: $WAREHOUSE_API_KEY`). If the hit rate is meaningful, flag it; part of the list may skip enrichment.

## STEP 3. Scrape companies

- **Clay / LinkedIn:** "Find Companies" with industries (full list, go broad), size range, geography. Up to 50k rows at a time; for bigger TAMs run batches excluding prior pulls. **Validation check:** upload the client's existing customer list to Clay, enrich, and confirm they appear in your scraped list. If not, investigate the filters first.
- **Google Maps / Outscraper:** scrape by category and geography; then STEP 9 for contacts.
- **ZoomInfo:** Instant Data Scraper extension, then upload the CSV into Clay.
- **Store Leads / BuiltWith:** export filtered to criteria, import into Clay.

## STEP 4. Run ICP qualifier

Parallel batches of 50; each visits the website and returns `ICP_FIT: YES or NO` + `REASONING`. Keep YES only. Clay alternative: OpenAI column with GPT-4o Mini using the icp.md prompt exactly. **Spot-check** 10-20 results first; refine if misclassified. If still wrong after 3-4 iterations: run on 100, export with reasoning, send to AM/Jed for manual annotation, fix with that feedback.

## STEP 5. TAM size validation

- In range: confirm and move on.
- Significantly lower: flag (missing industries, wrong source, overly strict qualifier).
- Significantly higher: flag (qualifier too permissive), spot-check YES results.

If qualified company count is under 1,000, flag to Jed; the client needs to know.

## STEP 6. Segment companies

Apply segmentation from `icp.md`, using OpenAI prompts (cheaper than Clay enrichments). Also normalize company names for `{{company_name}}`.

## STEP 7. Find contacts (LinkedIn path)

In Clay, "Find People at These Companies" with: company size (again), geography (if wanted), seniority from icp.md, include keywords ("Contains", NOT "Similar to" or "Exactly"), exclude keywords. Then normalize first + last name, normalize company name (from the company list, not the contact record), apply segment labels.

**Contact ratio check:** fewer contacts than companies means missing titles, investigate; 3x+ more means keywords too broad, tighten excludes.

## STEP 8. Find emails (waterfall)

Order, lowest cost first: 1. Warehouse (free, always first) 2. Prospeo (150k/mo) 3. LeadMagic (250k/mo) 4. IcyPeas 5. TryKitt. Report total processed, found and hit rate %, by provider, no-email count. Keep no-email contacts but flag them; don't discard.

## STEP 9. Non-LinkedIn contact finding (Google Maps path only)

- **A. Website research (GPT-4o Mini):** find owner or primary decision-maker's name, title, contact info; return `first_name, last_name, title, email (if found), confidence (High/Medium/Low)`.
- **B. LinkedIn people search** on each company name; merge with website results; dedupe by company.

## STEP 10. Enrich custom fields

**Do not run until** messaging is client-approved AND campaigns are live. Niche/vertical via GPT-4o Mini on the website; personalized line from company context + ICP; anything else, confirm approach with the AM. **Spot-check** 5 examples in the template as the prospect.

## STEP 11. Dedup against existing campaign

Report total, already in campaign (removed), net new. If net new is under 500, flag to AM.

## STEP 12. Upload to campaigns

**Get AM sign-off first.**
- Smartlead: first upload 5,000 contacts max per campaign; QA custom field mapping before notifying AM; confirm campaign ID and URL.
- HeyReach: 500 contacts max per campaign; warmest leads only (Segment 1 or signal-based, confirm with Jed); QA mapping.

## STEP 13. Update icp.md

Add final qualified company count and contact count to TAM Build Config, update Active Campaign Custom Fields, add a change log entry.

## Completion report

Client and segments built; qualified companies; total contacts; emails found (hit rate); uploaded to Smartlead (campaign name + URL); HeyReach if applicable; custom fields mapped; gaps or issues flagged.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key). Campaign creation and uploads are writes, only on Pablo's explicit go-ahead; canary first.
- Supabase/warehouse keys are not in the box env. Clay, HeyReach, Prospeo and the pp-gtm enrichment scripts are not on the box.
- Client folders are in the pp-gtm repo; use `/workspace/` copies otherwise. No em dashes.
