---
name: audit-inbox-signatures
description: >-
  Use when Pablo says find inboxes without a signature, audit signatures, or
  check missing signatures: find every Smartlead inbox missing a signature,
  match each to a confirmed name and title, write via REST on his go-ahead, and
  verify.
---
# Audit Inbox Signatures

Built and confirmed 2026-09-14/15: found and fixed 1,718 inboxes missing a signature across all active Smartlead clients.

---

## Step 1 -- Pull every inbox UNFILTERED, not per-client

Page through `GET /email-accounts` (Smartlead REST, `?api_key=...`, `limit=100&offset=N`, **no `client_id` filter**) until an empty page comes back.

**Do not sum per-client-filtered pulls (`?client_id=X`) and assume that's the full picture.** `GET /email-accounts?client_id=X` can silently omit inboxes that actually belong to that client -- they come back showing `client_id: null` in the API response despite visibly belonging to a real client in the Smartlead UI. Confirmed 2026-09-14: summing all 15 per-client pulls gave 1,403 missing signatures; the true unfiltered total was 1,718 (315 more, all with `client_id: null`). See [[feedback_smartlead_api_lessons]] for the full writeup of this bug.

An inbox is missing a signature if `signature` is `null` or empty string.

For any `client_id: null` row, identify the real client by:
1. Sending domain (e.g. `heycampdigital.com` -> Camp Digital) -- fastest, usually unambiguous
2. `from_name` matched against the confirmed name list in [[signature_job_titles_by_client]]

Never assume a `client_id: null` inbox is actually unowned/orphaned without checking domain + name first.

Report back grouped by client, with a total. If Pablo gives you a number he's seeing in the Smartlead UI and your first-pass count is lower, that's the signal to check for the `client_id: null` gap above before assuming his number is wrong.

---

## Step 2 -- Get the name -> job title map before writing anything

**Never invent a job title.** For every client with missing signatures, check [[signature_job_titles_by_client]] first -- it has the confirmed template and every name/title Pablo has given so far. If a `from_name` isn't on that list (new person, new client, or a mangled name like "Mclaughlin Patrick" for Patrick McLaughlin), stop and ask Pablo rather than guessing. Confirm identity explicitly for any mangled/reordered name before matching it.

If Pablo says not to worry about exact titles for a specific batch (happened for Rocket Shipping/Maven Analytics), use the title-less variant: `{First} {Last}<br>{Client Display Name}` instead of `{First} {Last}<br>{Job Title} - {Client Display Name}`.

---

## Step 3 -- Signature variation SOP (current standard, added 2026-09-28)

**Supersedes the old single bold/italic HTML template below for all NEW signature-writing work.** Leave every signature already written with the old template as-is -- do not retroactively migrate already-fixed inboxes to the new format. This new format only applies going forward.

**Why:** If every inbox for the same sender (e.g. 200 inboxes all sending as "Wayne Selman") uses the exact same signature HTML, that's a pattern spam filters can key on. The fix isn't a live spintax tag in the signature field -- it's generating a pool of real, pre-rendered signature variants and spreading them across the inbox batch so no two inboxes look identical.

**Important technical note:** Smartlead's `{option1|option2}` spintax syntax only gets parsed in the campaign body/subject editor. It does NOT get parsed in the account-level signature field (that field is injected via `%signature%` after spintax processing runs). If you paste `{Contracts|Signatures|Signing}` directly into the signature field, prospects will literally see the curly braces and pipes in their inbox. Never do this. Always generate the full set of literal, already-picked variants and assign one per inbox.

**As with the old template: if a person's name/title isn't in the confirmed map in [[signature_job_titles_by_client]], stop and ask Pablo every time -- never guess or invent a title.**

### Every signature needs exactly 4 elements

1. Full name
2. Job title
3. Company name (never varied -- always the real company, spelled consistently)
4. Opt-out line

No bold, no italics, no HTML styling. Plain text only, using `<br>` for line breaks. Format shell (use this exact structure for everyone):

```
{Name}<br>{Title} - {Company}<br><br>{Opt-out line}
```

### 3a. Build the name variant pool (2-3 options per person)

- Short/common form + last name (e.g. Ben Edwards)
- Full/formal form + last name, if a real expansion exists (e.g. Benjamin Edwards) -- always prefer including the longer form when one naturally exists (Joe -> Joseph, Sam -> Samuel, Mike -> Michael, Nick -> Nicholas, Dan -> Daniel, Pat -> Patrick, Gabe -> Gabriel, etc.)
- Short or full first name + last initial (e.g. Ben E.)

Don't invent a nickname that doesn't actually fit the person. If there's no natural short/long pair, just use the two forms: full name, and first name + last initial.

### 3b. Build the title variant pool

- If the person is a Founder or CEO: title is LOCKED. Do not vary it. Use their exact real title every time (e.g. always "Founder & CEO", never swapped for a different title). Changing a founder's title is a factual misrepresentation, not just a phrasing tweak.
- Everyone else: vary phrasing within the same seniority band only. An AE can rotate between "AE" / "Account Executive" / "Sales". An SDR can rotate between "SDR" / "Sales Development Rep" / "Business Development". Never promote someone's title to a higher level (don't turn an SDR into a "Director") -- that's a factual claim, not a phrasing choice.

### 3c. Opt-out line pool (5 options, verbatim -- use exactly as written)

1. If this isn't relevant, just reply "No thanks."
2. If this isn't relevant, reply "Stop"
3. If you don't want to hear from me, just reply "Stop"
4. If you don't want to hear from me, just reply "No thanks"
5. Feel free to reply "No thanks" if this isn't a fit.

### 3d. Casing rule (applies to every rendered variant)

Sentence case only: capitalize the first letter of the first word, lowercase everything else -- EXCEPT real abbreviations (API, SDK, HR, AI, DOT, PPC, CRO, SMS, BFCM, FAQs) and proper nouns (company names, brand names), which keep their normal capitalization.

- Right: `Ben E.<br>Account executive - Acme<br><br>If this isn't relevant, just reply "No thanks."`
- Wrong: `Ben E.<br>Account Executive - Acme<br><br>...` (don't title-case "Executive")

### 3e. Render the full variant set

Cross the name pool x title pool x opt-out pool into a list of literal, fully-written-out signatures (not spintax syntax -- actual finished strings). Example, for a non-founder AE named Ben Edwards at Acme:

```
Ben Edwards<br>AE - Acme<br><br>If this isn't relevant, just reply "No thanks."
Ben Edwards<br>AE - Acme<br><br>If this isn't relevant, reply "Stop"
Ben Edwards<br>Account executive - Acme<br><br>If you don't want to hear from me, just reply "Stop"
Benjamin Edwards<br>AE - Acme<br><br>Feel free to reply "No thanks" if this isn't a fit.
Ben E.<br>Account executive - Acme<br><br>If you don't want to hear from me, just reply "No thanks"
...
```

Aim for a pool of at least ~15-20 rendered variants per person if the name/title/opt-out combinations allow it. It's fine to end up with fewer for someone with very few natural name or title variants -- don't force artificial duplicates.

### 3f. Assign variants to inboxes

Sort that person's inbox account IDs, then assign in batches of 5 inboxes per variant, cycling through the pool. Example: variant 1 -> the first 5 inboxes, variant 2 -> the next 5, and so on. Once you reach the end of the pool, wrap back to variant 1 for the remaining inboxes.

### 3g. Apply it

Use the Smartlead API to set the signature field on each account: `update_email_account_details(account_id=<id>, signature="<rendered variant>")`. If you're also fixing a bad `from_name` on the account (typo, wrong person), pass `from_name` in the same call.

### Data hygiene -- check these before generating variants

- **One person, one identity.** If someone sends for two different companies or roles (e.g. moonlighting for a second client), keep those as two completely separate variant pools -- never mix company names for the same person's inboxes.
- Check for `from_name` typos or duplicates before pooling by name (e.g. "Ben Ben", reversed names, retyped variants of the same person). Fix these to the correct canonical name as part of the same update, so they don't end up as a fake extra identity with no real signature of their own.
- Skip inboxes with no title/company on file rather than guessing -- flag those back for a real answer instead of inventing a title.

### Quick checklist before you push live

- [ ] Every rendered signature has name + title + company + opt-out, nothing else
- [ ] No bold/italic/HTML styling -- plain text with `<br>` only
- [ ] Sentence case applied (only abbreviations/proper nouns capitalized)
- [ ] No `{a|b|c}` spintax syntax anywhere in the signature field -- every variant is a finished literal string
- [ ] Founder/CEO titles are identical across all their variants
- [ ] Company name is spelled identically across every variant for that person
- [ ] Inboxes assigned in batches of 5 per variant, cycling through the pool

---

## Step 3 (legacy) -- The old confirmed signature template

**No longer used for new work as of 2026-09-28 (see Step 3 above) -- kept here only because existing inboxes already carry this format and are being left as-is, not migrated.**

```html
<div><strong style="font-weight: 700">{First} {Last}<br></strong>{Job Title} - {Client Display Name}</div><div><br><em>P.S. If this isn't relevant, just reply "No thanks"</em></div>
```

Renders as: bold name on its own line, plain "Title - Client" on the next line, blank line, then italic P.S.

Write it with `POST /email-accounts/{id}`, body `{"signature": "..."}` **only** -- never include other fields, never touch `client_id`.

---

## Step 4 -- Scope every write to the EXACT accounts you mean to touch

**Match and fix by specific account ID, never by a broad filter like `from_name` across a whole client.** Confirmed 2026-09-15 mistake: after fixing 49 specific inboxes (missing signature) for two people, Pablo asked to "add the role AE to them." A script that matched by `from_name` across the whole client caught 112 inboxes instead of the intended 49 -- 63 of them already had unrelated signature content that got silently overwritten with no way to recover the original text (Smartlead's API has no signature history). See [[feedback_scope_bulk_fixes_tightly]].

**How to apply:** When fixing/updating a named batch of inboxes, keep the exact list of account IDs from the audit step and write to only those IDs on every follow-up action, even if a later request seems to describe the same group by name. If a request could plausibly mean "everyone with this name" instead of "the specific inboxes we just discussed," ask before writing.

---

## Step 5 -- Verify

Re-pull unfiltered `GET /email-accounts`, recount missing signatures. Confirm the number dropped by exactly what you expected to fix -- not more, not less. If it changed by more than expected, something touched accounts outside the intended scope.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22). The recipe above is Pablo's original text; this section only maps it to the tools available here.

- Smartlead: REST only (Pablo's 2026-09-28 rule: always REST for Smartlead, never MCP). Base `https://server.smartlead.ai/api/v1`, auth `?api_key=$SMARTLEAD_API_KEY` (already set in the box env; never print, log or save it). There is no Smartlead MCP and no macOS Keychain on this box. Run calls from Shell with Python shelling out to `curl`.
- Files: write CSVs and scratch output to `/workspace/` (replaces `temp/` and `pp-gtm/temp/`).
- Scripts under `integrations/` (and other `pp-gtm` or `~/Desktop/Automations` scripts) live in Pablo's pp-gtm repo, not on the box. Reproduce their logic with the REST calls described here; do not assume the script exists.
- `[[...]]` links point to Claude memory notes that were not imported as skills, except `fix-sender-bounce-emails`, `clean-up-inboxes-smartlead` and `disconnect-by-domain`, which are skills now.
- Standing rules still apply: never delete without Pablo's explicit authorization, the Friday weekly sweep routine never detaches (other tasks may detach when the task calls for it, chat 2026-10-22), canary first before any bulk write, verify every number by re-pulling, no em dashes.

REST equivalents for the calls used above:
- MCP `get_email_accounts` = `GET /email-accounts?limit=100&offset=N` (add `client_id=X` to scope), paginate until an empty or short page. Pull unfiltered when you need to catch `client_id: null` orphans. Do not print full objects, they include passwords.
- MCP `update_email_account_details` = `POST /email-accounts/{id}` with any of `max_email_per_day`, `time_to_wait_in_mins`, `signature`, `from_name` (documented in feedback_smartlead_api_lessons). Wrong patterns: `PUT /email-accounts/{id}`, `POST /email-accounts/{id}/update`.
- MCP `get_all_clients` = `GET /client/` (verified 2026-10-22 with a read-only GET; returns `id`, `name`, `email`, ...).

- Overlap with the saved `set-inbox-signatures` skill: this Claude version has a 2026-09-28 variation SOP (plain text signatures, name/title pools, 5 opt-out lines, about 15-20 variants, batches of 5), while the saved skill uses the older bold/italic template that Pablo confirmed for the 220 inboxes. Ask Pablo which template applies before writing anything.
- Writing signatures is a Smartlead write: canary one inbox first, then batches, and re-pull to verify.
