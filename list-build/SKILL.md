---
name: list-build
description: >-
  Use when someone says build a list, build leads for [client], or list request:
  end-to-end list build from ICP criteria to contacts uploaded in Smartlead and
  written to the Supabase warehouse.
---
# Skill: list-build

**Trigger:** "build a list" / "build leads for [client]" / "list request"

**Who runs this:** GTME (Pablo or Jaimin). Can also be triggered by an AM passing a list request.

**What it does:** End-to-end list build from ICP criteria to contacts uploaded in Smartlead and written to the Supabase warehouse.

---

## Before you start

Read `clients/[folder]/icp.md` (ICP criteria, segments, qualifier prompt, custom fields, list source) and `clients/[folder]/context.md` (active campaigns, segments built, what's been tried).

Confirm: TAM build (new client) or gap fill (existing client)? Specific campaign to upload into, or new? Any segment or persona constraints beyond ICP defaults?

---

## STEP 1. Intake questions (ask all in ONE message)

1. **Client**: which client is this for?
2. **Extra criteria**: any targeting beyond the ICP doc (geography, seniority, signals, titles to add or exclude)? If none, "ICP defaults."
3. **Qualification prompt**: use the qualifier from the ICP doc, any adjustments?
4. **Custom fields**: any fields to enrich for personalization (e.g. `{{niche}}`, `{{icebreaker}}`)? If none, "none."
5. **Campaign**: which Smartlead campaign? Paste the ID or URL.
6. **Volume**: a number, "pull the full TAM", or "tell me the pool size first" (check Prospeo and report back).
7. **Normalization**: first names, company names and domains normalized by default (strips LLC/Inc, title cases names, cleans URLs). Anything to adjust?
8. **Anything else**: any context before running?

Then run end to end and notify when ready for final approval before uploading.

**Approval gate:** Do not proceed until all 8 are answered.

---

## STEP 2. Recommend the source

| ICP type | Source |
|---|---|
| Local / SMB businesses (restaurants, clinics, gyms, contractors) | Google Maps scraper (see `google-maps-list-builder`) |
| Healthcare providers, clinics, hospitals | NPI Registry (`integrations/npi-taxonomy-pull.py`) |
| Home health, nursing homes | CMS database (`integrations/cms-homecare-pull.py`) |
| Nonprofits, human services orgs | IRS NTEE file (`integrations/irs-ntee-pull.py`) |
| Commercial trucking fleets | FMCSA database |
| LinkedIn-indexed B2B companies (default) | Prospeo (`integrations/prospeo-search.py`) |
| E-commerce brands | Store Leads export + Prospeo people search |

If Prospeo, confirm the `## Prospeo Filters` block exists in `icp.md`; if not, build filters from the ICP and ask for confirmation. State the recommendation and get confirmation before pulling.

---

## STEP 3. Pull accounts

- **Prospeo path (most common):** `prospeo-search.py --client [folder] --segment "[segment]" --output /workspace/[client]-contacts-raw.csv --limit [target volume x 3]` (pull 3x for qualification falloff). Filters from `icp.md` or `--filters '{...}'`. Over 25k crawls state by state automatically.
- **Google Maps path:** scrape by category + location to `/workspace/[client]-accounts-raw.csv`. Company-level only; skip to STEP 5.
- **Specialty source path:** run the NPI / CMS / IRS script; output lands in `lists/[tam-type]/companies-raw.csv`, move to `/workspace/[client]-accounts-raw.csv`.

---

## STEP 4. Qualify accounts

Run the ICP qualifier from `icp.md` on each account in parallel batches of 50. Each visits the website, evaluates against the prompt, and returns `ICP_FIT: YES or NO` + `REASONING`. Keep YES only.

**Spot-check:** run on 10 rows first and fix the prompt if anything is wrong.

**Report** qualified out of total. If under 20% qualify, flag: source is wrong or qualifier too strict.

Prompt template:
```
You are qualifying companies for [client name]'s ICP.
ICP qualifier criteria:
[qualifier prompt from icp.md]
Company to evaluate:
Name: [company_name]
Website: [company_domain]
Industry: [company_industry]
Size: [company_size]
Visit the website and respond with:
ICP_FIT: YES or NO
REASONING: [1-2 sentences explaining why]
```

---

## STEP 5. Find contacts

Prospeo returns people already; skip to STEP 6.

For Google Maps or specialty sources: **website owner research is the only method for local SMBs.** Prospeo people search does NOT work for local SMBs (not LinkedIn-indexed; returns 400 on `company_name` and `company_website` filters). For each qualified company, visit the website and find the owner or primary decision-maker: `first_name, last_name, title, email, confidence`. Batches of 25 companies. Expect names at ~25-40% of SMBs. Keep only contacts with first + last name. Then run the waterfall; Prospeo's `enrich-person` by name + domain is the Prospeo step inside the waterfall.

---

## STEP 6. Email waterfall

Order: warehouse (validated) then Prospeo then LeadMagic then TryKitt (`email-waterfall.ts` with `WF_INPUT`, `WF_OUTPUT`, `WF_NO_EMAIL`; `trigger-enrich.ts` for 5k+). Report total, found, hit rate %, by provider. **If hit rate is under 30%,** flag and spot-check 10 rows (wrong LinkedIn URLs, fake domains, or wrong source).

---

## STEP 7. Enrich custom fields

From `## Active Campaign Custom Fields` in `icp.md`. Common: **niche** (classify from website + industry), **icebreaker** (personalized opener), **case_study** (match most relevant), **signal fields** (recent hire, funding). **Spot-check:** paste 5 rows into the template and read as the prospect; every field must flow grammatically.

---

## STEP 8. Normalize all fields

- `first_name`: title case, no middle initials, no numbers or symbols
- `last_name`: title case
- `company_name`: strip LLC/Inc/Corp/Ltd, title case
- `company_domain`: strip https://, www., trailing slashes
- `email`: lowercase
- `linkedin_url`: normalized to linkedin.com/in/[slug]

Review and fix before continuing.

---

## STEP 9. Dedup against existing campaign

Remove contacts already in the target campaign. Report total in, already in campaign (removed), net new. If net new is under 500, flag to AM before uploading.

---

## STEP 10. GTME approval gate

```
List ready for approval -- [Client], [Campaign name]
Source: [Prospeo / Google Maps / NPI / etc.]
Qualified accounts: [count]
Total contacts: [count]
Emails found: [count] ([%] hit rate)
Already in campaign (removed): [count]
Net new ready to upload: [count]
Custom fields enriched: [list]
File: /workspace/[client]-contacts-final.csv
Reply with approve to upload, or flag anything to fix first.
```

**Do not upload until explicitly approved.**

---

## STEP 11. Upload to Smartlead + Supabase

After approval, upload to Smartlead and write to the warehouse in one pass (`upload-leads.py`, with `--dry-run` first). Confirm the upload count matches expectation.

---

## STEP 12. Update context

1. Check-mark the Slack thread and tag the AM
2. Add to `clients/[folder]/context.md` under Campaign Status: `[Date]: Uploaded [N] contacts to [campaign name]. Email hit rate: [%]. Segment: [segment].`
3. Note gaps (no-email contacts, qualification falloff)

---

## HARD RULES

1. Always recommend the source before pulling, never just start scraping
2. Always run the qualifier before finding contacts
3. Never upload without GTME or AM approval
4. Spot-check custom fields in the actual email template before uploading
5. Minimum 500 net new contacts before upload is worth it, flag if under
6. Never put CSVs in client folders, all list data goes to /workspace/ then Supabase
7. No em dashes in any output

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Smartlead: REST only, `https://server.smartlead.ai/api/v1?api_key=$SMARTLEAD_API_KEY` (never print the key). Dedup with `GET /campaigns/{id}/leads-export` (raw CSV). Upload with `POST /campaigns/{id}/leads` (`lead_list`, max 100 per call), fields mapped one to one, canary 5 leads and read back first. Write: only on Pablo's explicit go-ahead.
- Supabase keys are not in the box env, so warehouse steps are not runnable yet.
- Prospeo, the waterfall, trigger-enrich, smartlead-dedup, normalize and gov-data scripts are in the pp-gtm repo with keys not on the box. Normalization and dedup can be reproduced in Python here.
