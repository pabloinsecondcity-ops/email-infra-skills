---
name: onboarding-icp
description: >-
  Use when someone says new client onboarding or parse onboarding form for
  [client]: read the onboarding form, build the ICP doc and TAM Breakdown Report
  HTML, save to the client folder, and flag for review before it goes to the
  client.
---
# Skill: onboarding-icp

**Trigger:** "new client onboarding" / "parse onboarding form for [client]"

**Who runs this:** Jed or Eric when a new client signs. Runs before anything else. TAM build does not start until the ICP doc is client-approved.

**What it does:** Reads the onboarding form, builds the ICP doc, generates the TAM Breakdown Report HTML, saves everything to the client folder, and flags for review before it goes to the client.

---

## Before you start

Check `clients/registry.md`. If a folder already exists for this client, read `clients/[folder]/onboarding.md` first, the form answers are already parsed there. If no folder exists yet, run `bootstrap-client` first.

---

## STEP 1. Parse the onboarding form

Read `clients/[folder]/onboarding.md`. Extract and clearly summarize:

**Company Criteria:** industry / company type; company size (headcount and/or revenue); geography; must-have attributes (tech stack, certifications, business model, specific qualifiers); explicit disqualifiers.

**Persona Criteria:** target job titles and functions; seniority level; persona-specific attributes.

**Segmentation:** the AM will have already defined segments in the messaging doc. Confirm what's been approved. If not defined yet, propose a minimum viable split (target 2, max 3). Only segment when messaging must change.

**Signals:** note any signals (hiring, funding, new location, tech stack, intent data). These are not qualifiers, they're used for signal campaigns later.

Flag gaps before proceeding: no employee size range; geography not specified; industry too broad with no qualifier; vague job title criteria (e.g. "marketing people"); no clarity on must-have vs. nice-to-have. Output these as **"Questions to Confirm Before Sending to Client"**.

**Approval gate:** Wait for confirmation that the parsed summary looks right before proceeding.

---

## STEP 2. Determine list source

Recommend the right data source with one-sentence reasoning:
- **Clay / LinkedIn (default):** B2B, SaaS, agencies, professional services, tech, finance, healthcare, enterprise, mid-market.
- **ZoomInfo:** strong technographic component (must use Salesforce, HubSpot, etc.) or firmographic filters needing more granularity than Clay.
- **Store Leads / BuiltWith:** selling to e-commerce businesses. Store Leads finds Shopify stores; BuiltWith identifies tech stack.
- **Google Maps / Outscraper:** blue-collar or local SMBs (HVAC, plumbers, roofers, landscapers, restaurants, auto shops, home services).
- **Association / directory scrape:** a specific niche with a known member directory (non-profits, licensed contractors, state boards).

---

## STEP 3. LinkedIn industries (if Clay path)

Output the specific LinkedIn industries for the "Find Companies" search. Philosophy: **always go broader.** Filter bad fits with the ICP qualifier later. Output as a clean bullet list the GTME can paste into Clay. Full list in `knowledge/tam-build.md`.

---

## STEP 4. Build ICP qualifier prompt

Generate the GPT-4o Mini prompt run on each company's website. Every qualifier prompt must return:
```
ICP_FIT: YES or NO
REASONING: [1-2 sentences explaining why]
```

How to build it:
1. Identify must-have attributes that need the company website to determine
2. Instruct the model to review the website and make a YES/NO determination
3. Use proxy signals for unreliable data: revenue for SMBs ("does this look like an established operating business with real customers, not a solo freelancer or brand new startup?"); headcount for small companies (website, job postings, team page); funding stage (press page, about page, site language)

When substituting a proxy, flag it: "I replaced [criteria] with [proxy] because [reason]."

After generating: "Run this on the first 10 companies and spot-check the results before running on the full list. If anything is wrong, paste the misclassified companies + their reasoning back and I'll update the prompt." Save the approved prompt to `clients/[folder]/icp.md` under ICP Qualifier Prompt.

---

## STEP 5. Build job title keyword lists

**A) Seniority Filter:** recommend LinkedIn seniority levels (Director, VP, C-Suite, Owner, Partner, etc.).

**B) Include Keywords, comma-separated:** function/role keywords only, no seniority prefixes ("Sales" not "Director of Sales"). Be expansive: every variant, abbreviation, adjacent term. Example for sales leaders: Sales, Revenue, GTM, Growth, Business Development, BD, Account Executive, AE, Commercial.

**C) Exclude Keywords, comma-separated:** every title the include keywords might accidentally pull. Be thorough.

Format as three labeled sections for copy-paste.

---

## STEP 6. Contact-first vs company-first check

"We're planning company-first (find companies, then contacts). This works for most TAMs. However, if the target persona is very niche (Salesforce Admins, RevOps Managers, a highly specialized role), contact-first may be more effective: search LinkedIn for anyone with that title, then qualify the company via prompt. Based on this ICP, [recommendation]."

---

## STEP 7. Write icp.md

Write `clients/[folder]/icp.md` with this structure:

```
# [Client Name] -- ICP & Campaign Strategy
Last updated: [today's date]

## Company Criteria
| Attribute | Value |
| Industries | ... | Company Size | ... | Geography | ... | Must-Have Attributes | ... | Disqualifiers | ... |

## Persona Criteria
| Titles (Include) | Title Keywords (Include) | Title Keywords (Exclude) | Seniority |

## Segments
| Segment | Description | List Source |

## Signals (for future campaigns)
[signals with one-line note on how to use each]

## TAM Build Config
| List Source | LinkedIn Industries | Contact Approach | Seniority Filter |

## ICP Qualifier Prompt
[full prompt text]

## Active Campaign Custom Fields
[populated after campaigns are live; GTME updates when new campaigns launch]
| Campaign | Custom Fields Required |

## Change Log
| Date | What Changed | Who |
```

---

## STEP 8. Generate TAM Breakdown Report

An HTML artifact for the client confirming your understanding of their market before the TAM build. Three sections:

1. **Cover:** client name + "ICP Market Sizing & TAM Analysis"; one-line descriptor; three stat boxes: ~[X] ICP-qualified accounts, ~[Y] contactable decision-makers (qualified accounts x 2.5 default), [N] target verticals analyzed.
2. **Executive Summary:** 2-3 sentences on what the client does and what this covers; ICP Qualification Criteria table (Geography, Company Type, Size, Must-Have Attributes).
3. **Market Sizing by Vertical:** horizontal bar chart, one row per segment, estimated company count with proportional bar, priority tag HIGH / MEDIUM / LOW, sorted largest to smallest.

Design rules: client brand colors if available, default dark professional theme; premium Google Font (Sora, DM Sans, Plus Jakarta Sans, never Inter or Arial); prefix all estimates with ~; no internal notes or process language.

After generating: "Review this before sending to the client. Once you're happy with it, send it along with the ICP guide and ask for their approval. Do not start the TAM build until they confirm."

---

## STEP 9. ICP Guide for client

Plain-text client-facing doc:

```
ICP GUIDE -- [Client Name]
Prepared by Practical Prospecting

COMPANY CRITERIA
Industry / Company Type: ...
Company Size: ...
Geography: ...
Must-Have Attributes: ...
Disqualifiers: ...

PERSONA CRITERIA
Target Functions: ...
Seniority: ...
Include Keywords: ...
Exclude Keywords: ...

SEGMENTATION
Segment 1 -- [Name]: ...
Segment 2 -- [Name]: ...

SIGNALS (for future targeting)
[signals, not qualifiers]
```

**Approval gate:** Do not start `tam-build` until the client confirms the ICP guide is accurate. Flag this clearly to Eric.

---

## STEP 10. Confirm and hand off

Tell the team: ICP doc saved to `clients/[folder]/icp.md`; TAM Breakdown Report ready to send; ICP Guide ready to send; waiting on client approval; once approved, GTME runs `tam-build`.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Client folders, `knowledge/` and `context/` files are in Pablo's pp-gtm repo, not on the box. Write outputs to `/workspace/clients/[folder]/` as box copies unless the repo is available.
- The onboarding form lives in Google Docs; no Google Drive connector is connected. Clay is not connected.
- Standing rules: never invent facts or names, no em dashes, nothing goes to the client without review.
