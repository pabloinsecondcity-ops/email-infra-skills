---
name: set-inbox-signatures
description: >-
  Use when Smartlead inboxes (usually newly added ones) have no signature or
  need the standard signature: First Last / Job Title - Client / P.S. If this
  isn't relevant, just reply "No thanks".
---
# Set inbox signatures (Smartlead)

## Standard template (Pablo's format)
```
First Last            (bold)
Job Title - Client Name

P.S. If this isn't relevant, just reply "No thanks"   (italic)
```
Exact HTML to save in Smartlead's `signature` field:
```
<div><strong style="font-weight: 700">{First Last}<br></strong>{Job Title} - {Client Name}</div><div><br><em>P.S. If this isn't relevant, just reply "No thanks"</em></div>
```

## Known senders (verified from existing inboxes, Oct 2026)
| Sender (from_name) | Name in signature | Job Title - Client |
|---|---|---|
| Jed Mahrle | Jed Mahrle | Founder & CEO - Practical Prospecting |
| Wayne Selman | Wayne Selman | Director of Sales - SignWell |
| Mariana Sandi | Mariana Sandi | SDR - SignWell |
| Adi Hopwood | Adi Hopwood | Director of Business Development - CMAP |
| Daisy Greaves | Daisy Greaves | AE - CMAP |
| Ben Edwards | Ben Edwards | AE - CMAP |
| Adam Ilowite | Adam Ilowite | CEO/Founder - Axero Solutions |
| Alex Hoey | Alexandra Hoey | Director of Marketing - Axero Solutions |

For a sender not in this table: look up the most common signature on that sender's existing inboxes (same client_id + from_name) and use its name and title in the template. If none exist, ask the user for the job title. Never guess a title.

## Steps
1. Pull all accounts: `GET /email-accounts` (paginated, offset/limit 100). Select the target inboxes (e.g. created today, or empty `signature`). Save a before-snapshot with passwords redacted.
2. Map each inbox's `from_name` to its signature. List any inbox with no mapping and stop for those.
3. Show the user the counts per sender and the signatures before changing anything.
4. Canary: `POST /email-accounts/{id}` with body `{"signature": "..."}` on ONE inbox. Verify through the `GET /email-accounts` list (the single-account GET doesn't return tags) that the signature saved and client, tags, daily limit, tracking domain and warmup are unchanged.
5. Apply to the rest, only sending the `signature` field. Change nothing else.
6. Re-pull and verify every target has the exact signature and nothing else changed. Report counts, any failures, and plainly anything not done.

## Rules
- Only touch the signature. No tag, client, limit, campaign or warmup changes.
- Never delete or detach anything.
- Report only verified numbers.
