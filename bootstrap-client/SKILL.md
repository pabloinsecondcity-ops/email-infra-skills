---
name: bootstrap-client
description: >-
  Use when Pablo says bootstrap [client name] or set up client folder for
  [client name], to build or re-sync a client folder from their ICP and
  onboarding Google Docs.
---
# Skill: bootstrap-client

Bootstrap a client folder from their Google Docs. Run once when a new client is onboarded, or when ICP/onboarding docs need to be re-synced.

## Trigger

"Bootstrap [client name]" or "Set up client folder for [client name]"

## Steps

1. Look up the client in `clients/registry.md` to get their folder name, ICP Doc ID, and Onboarding Doc ID.
2. Read the ICP doc via Google Drive using the ICP Doc ID.
3. Read the onboarding form doc via Google Drive using the Onboarding Doc ID.
4. Write `clients/[folder]/icp.md` using this structure:
   - Titles / personas targeted
   - Company criteria (industry, size, geography, tech stack signals)
   - Exclusions
   - Key signals to look for when researching a prospect
   - Last updated date
5. Write `clients/[folder]/onboarding.md` using this structure:
   - Website
   - Ideal company profile
   - Problems solved
   - Dream outcome
   - Competitors
   - Competitive differences
   - How they get by without the client
   - Research signals
   - Outbound history
   - Why last customers bought
   - Qualified meeting definition
   - Goal
   - Sender names
6. Update `clients/registry.md` to mark the client's status as "complete" and record today's date.
7. Confirm: "Client folder for [name] is ready. ICP and onboarding files are at clients/[folder]/."

## Notes

- If a doc ID returns "not found", the doc isn't shared with the Drive API. Tell the AM: "The [ICP/onboarding] doc for [client] isn't accessible. Ask Jed or the GTME to set sharing to 'anyone with the link' and share the URL."
- Never overwrite an icp.md that has been manually edited since the last sync without confirming first.
- The onboarding form never changes, only write it once. Skip if the file already exists.
- icp.md gets re-synced when the AM says "refresh [client]'s ICP" or when a GTME updates the criteria.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22). The recipe above is Pablo's original text; this section only maps it to the tools available here.

- Files: write output to `/workspace/`.
- The client folders (`clients/[folder]/...`, `clients/registry.md`) are in Pablo's pp-gtm repo, not on the box. Without the repo, write the outputs to `/workspace/clients/[folder]/` and tell Pablo they are box copies.
- Google Drive: no Google Drive connector is connected (connected: Gmail, Google Sheets, Airtable, Zapmail). Connect Google Drive (see the `add-connector` skill) or ask Pablo to share the doc content before running.
- Standing rules: never invent facts or names, no em dashes.
