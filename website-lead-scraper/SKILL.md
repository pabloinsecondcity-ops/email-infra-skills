---
name: website-lead-scraper
description: >-
  Use when asked to scrape a website for leads, find leads or companies from a
  website, pull a company list from a site, or build a TAM from websites (member
  directories, permit or license registries, business listings, sponsor pages).
---
# Website Lead Scraper

A reusable method for extracting company/lead lists from websites that don't show up in a normal search: trade association directories, government permit/license registries, business listings, sponsor pages, or any site with a list of companies. Developed building a waste/recycling hauler TAM (233+ companies from associations, 87K from FMCSA, 8.6K from state/county gov registries); it generalizes to any site or industry.

**If asked to "find leads from a website," "scrape this site for companies," or similar, check this skill first, whatever the site.**

## Core tool: Playwright, not a flat fetch

A flat HTML-to-markdown fetch can't run JavaScript, click buttons, submit search forms, or get past bot detection. Most real directories are JS-rendered widgets (Wild Apricot, MembershipWorks, GrowthZone) or use basic bot-fingerprint blocking. Use Python + Playwright (chromium) from the shell.

**Default headless Chromium gets 403s on many sites.** Fix:

```python
browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
context = await browser.new_context(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
```

Use `wait_until="domcontentloaded"` + `page.wait_for_timeout(2000-3000)`, not `"networkidle"` (background analytics make networkidle time out).

## Escalation pattern (association / directory sites)

1. Check homepage nav for "Members," "Directory," "Roster," "Find a Member," "Locations."
2. Full public roster: scrape it directly.
3. Login-gated (SAML SSO, member portals): don't bypass. Pull what IS public: sponsor/partner pages, board of directors with company affiliations, member spotlights.
4. Organizations rebrand or merge; search the current name (e.g. "CRRC" became "Resource Recovery Coalition of California").
5. Some domains are dead; confirm via `dig`/`curl` before calling it a scrape failure, and don't retry a dead domain.

## Escalation pattern (government registries)

1. Check the relevant state agency first for the specific permit/license/registration type. Facility permits and business/operator permits are usually separate; don't conflate them.
2. No state list (often regulated locally): fall back to one or two representative counties/cities. Say explicitly which level you're reporting; never blur state and county data.
3. Watch for **segment mismatches**: a "Special Waste Hauler" or "Hazardous Waste Transporter" registry is NOT a general municipal solid waste hauler registry. Flag it.
4. Formats, easiest first: (a) live database with CSV/Excel export, always look for this first; (b) static PDF/CSV, extract with pdfplumber/PyMuPDF and verify the text is clean (PDFs can be image-based); (c) HTML table/page, scrape directly.

## Open-data APIs (Socrata / SODA)

Sites like `data.transportation.gov`, `data.cityofnewyork.us`, `data.cityofchicago.org`: hit the API, not the HTML frontend.

- `https://{domain}/resource/{dataset-id}.json?{field}={value}&$limit=100000` for server-side filtering (test scale with `$select=count(*)` first).
- `.csv` on the same URL gives a direct CSV.
- Check field names with `?$limit=1` (lowercased CSV headers). Checkbox values are often `"X"`, not `"Y"` or `true`; verify with a `$group` query before trusting a filter.

## Verification discipline (don't report a wrong number)

- **Pair logos to links via the DOM** (`img.closest('a')`), not two separate lists; that mismatched twice on sponsor logo walls.
- **Carousel duplication:** Owl Carousel / Swiper clone slides can double or triple count. Check `owl-dots` or dedupe by unique `href`/`src`.
- A suspiciously round or low first-pass count gets re-verified before it's reported as final.

## Output schema

One CSV schema across sources: `Company Name, Website, Source Page, Member/Registration Type, Email, Phone, Address, Note`

- **Never silently exclude entries** (government, universities, individuals, nonprofits, large national competitors); include and flag in `Note` (e.g. "NOT A PROSPECT - municipal government").
- `Note` carries every caveat: gated vs public, segment mismatches, stale sites, low-confidence matches from garbled logo filenames.
- **Keep wildly different-scale sources in separate files**, named by source and date.

## Scaling

Once validated on one example, fan out in parallel, one worker per site, each given the anti-bot fix, the escalation pattern and verify-before-reporting. Batches of 4-9 with interim check-ins; not 13+ at once.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Playwright may need installing on the box (`pip install playwright && playwright install chromium`); not verified here.
- Output CSVs go to `/workspace/`. Never invent facts or names. No em dashes.
