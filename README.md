# Email Infra Skills

Custom operational skills for Practical Prospecting email infrastructure and GTM workflows. This repo is the source of truth for inbox operations, campaign assignment, deliverability, list building, messaging, and weekly reviews.

Each skill lives in its own folder as `SKILL.md`. A few skills also include helper scripts or reference docs in the same folder.

API keys are not stored here. Skills refer to environment variable names such as `$SMARTLEAD_API_KEY`.

## List building

Yes. This repo includes end-to-end list building plus supporting scrapers and lead exports:

| Skill | What it does |
| --- | --- |
| [list-build](list-build/SKILL.md) | End-to-end list build from ICP criteria through contacts uploaded to Smartlead and written to the warehouse |
| [list-request](list-request/SKILL.md) | Handle an incoming list request: check what already exists, build the gap, enrich, dedupe, and prepare for upload |
| [tam-build](tam-build/SKILL.md) | Build the Total Addressable Market after ICP approval, from qualified companies through enriched contacts |
| [google-maps-list-builder](google-maps-list-builder/SKILL.md) | Scrape Google Maps for local businesses by category and location into a CSV ready for enrichment |
| [website-lead-scraper](website-lead-scraper/SKILL.md) | Pull companies or leads from websites such as member directories, registries, listings, and sponsor pages |
| [smartscout-scraping](smartscout-scraping/SKILL.md) | Capture SmartScout brand or company tables when export is locked |
| [pull-leads-from-supabase](pull-leads-from-supabase/SKILL.md) | Export a client's warehouse lead history to CSV |
| [export-leads-by-status](export-leads-by-status/SKILL.md) | Export every lead across a client's Smartlead campaigns filtered by status |

## Inbox and domain operations

| Skill | What it does |
| --- | --- |
| [email-infra](email-infra/SKILL.md) | Knowledge base for domains, inbox provisioning and warmup, Smartlead config, assignment, and rotation |
| [assign-inboxes](assign-inboxes/SKILL.md) | Assign inboxes evenly onto empty campaigns for a new client |
| [add-inboxes-to-campaigns](add-inboxes-to-campaigns/SKILL.md) | Add a named batch of unused inboxes onto campaigns that already have inboxes (add-only) |
| [rebalance-inboxes-to-new-campaigns](rebalance-inboxes-to-new-campaigns/SKILL.md) | Spread inboxes from running campaigns onto newly created ones so counts stay even |
| [redistribute-inboxes](redistribute-inboxes/SKILL.md) | Older full-client redistribution. Superseded by `rebalance-inboxes-to-new-campaigns` |
| [inbox-rotation-v2](inbox-rotation-v2/SKILL.md) | Detect burned inboxes, then remove, replace, and reassign them |
| [disconnect-by-domain](disconnect-by-domain/SKILL.md) | Detach every inbox on a given list of domains from all campaigns |
| [clean-up-inboxes-smartlead](clean-up-inboxes-smartlead/SKILL.md) | Flag inboxes with high sender bounce and no replies, then disconnect them on approval |
| [set-inbox-signatures](set-inbox-signatures/SKILL.md) | Apply the standard signature to Smartlead inboxes |
| [audit-inbox-signatures](audit-inbox-signatures/SKILL.md) | Find inboxes missing a signature and write the correct one on approval |
| [audit-disconnected-inboxes](audit-disconnected-inboxes/SKILL.md) | Find inboxes with failed SMTP/IMAP auth and confirm whether they still exist |
| [full-capacity-audit](full-capacity-audit/SKILL.md) | Check a client's active campaigns against daily caps and send gaps |

## Deliverability and copy

| Skill | What it does |
| --- | --- |
| [senderbounce-spintext](senderbounce-spintext/SKILL.md) | Find high sender-bounce campaigns and generate Email 1 spintax. Includes helper scripts and spintax reference docs |
| [fix-sender-bounce-emails](fix-sender-bounce-emails/SKILL.md) | Cross-client sender bounce inbox audit |
| [smartlead-per-inbox-reply-counts-fast](smartlead-per-inbox-reply-counts-fast/SKILL.md) | Per-inbox reply counts, fast analytics or the slower accurate method |

The `senderbounce-spintext` folder also has `spintax-examples.md`, `spintax-language-rules.md`, `build_push_payload.py`, `compute_bounce_rates.py`, and `validate_spintax.py`.

## Weekly reviews

| Skill | What it does |
| --- | --- |
| [weekly-email-review](weekly-email-review/SKILL.md) | Combined weekly health check: capacity, disconnected inboxes, overlap, sender bounce, and missing signatures |
| [weekly-full-capacity-check](weekly-full-capacity-check/SKILL.md) | Recurring full-capacity sweep across every active client (report-only) |
| [weekly-scorecard](weekly-scorecard/SKILL.md) | Fill the weekly inbox-health Scorecard |

## Messaging and client setup

| Skill | What it does |
| --- | --- |
| [onboarding-icp](onboarding-icp/SKILL.md) | Parse a new-client onboarding form and build the ICP doc and TAM breakdown |
| [bootstrap-client](bootstrap-client/SKILL.md) | Build or re-sync a client folder from ICP and onboarding docs |
| [sync-context](sync-context/SKILL.md) | Refresh a client's context file from recent Slack and meeting transcripts |
| [messaging-new](messaging-new/SKILL.md) | Full messaging build for a brand-new client through campaign creation |
| [messaging-campaign](messaging-campaign/SKILL.md) | Build a new campaign for an existing client |
| [messaging-iterate](messaging-iterate/SKILL.md) | Diagnose an underperforming campaign and write new variants |
| [karpathy-loop](karpathy-loop/SKILL.md) | Score active campaigns, flag underperformers, and draft challenger variants |
| [positive-reply-scoring](positive-reply-scoring/SKILL.md) | Compute leads per positive reply and positive reply rate per campaign |

## Other

| Skill | What it does |
| --- | --- |
| [review-session](review-session/SKILL.md) | Review a session transcript, map failures to skills or rules, and propose fixes |
| [typesafe-ai](typesafe-ai/SKILL.md) | Build with TypeSafe: structured judgments, routing, ranking, extraction, and verification |
