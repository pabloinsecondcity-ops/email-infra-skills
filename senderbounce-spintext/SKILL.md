---
name: senderbounce-spintext
description: >-
  Use when Pablo wants to check sender bounce rates, find campaigns that are
  bouncing, reduce bounce rate, spin or spintax or spintext a campaign, or add
  spintax to approved cold email copy; read-only, it scans, shows culprits, and
  generates Email 1 spintax to paste by hand.
---
# Sender Bounce Spintext

Find the campaigns with high **sender** bounce, then spin their Email 1 copy so
identical repeated content stops getting fingerprinted and filtered by Gmail and
Outlook. This version **never writes to Smartlead**, it produces spintax for a
human to copy and paste in. Pushing directly to Smartlead is a future phase (see
"Deferred" at the bottom).

Requires the **Smartlead MCP** server (the same one every PP teammate has). No
Command Center, Supabase, or dashboard access needed. The bounce numbers this skill
computes match the Command Center deliverability dashboard, because they use the
same verified formula (below).

## Hard rules

- Runs only when Pablo asks. Never run the sender bounce >5% flag or the spin daily, on a schedule, or automatically (Pablo, chat 2026-10-22).

- **Read-only. This skill never writes to Smartlead.** No `save_campaign_sequences`,
  no edits. It only reads, computes, and prints spintax for a human to paste.
- **Email 1 only.** Spin Email 1 variants. Never Email 2 or Email 3; short follow-ups
  gain nothing from spinning and multiply risk.
- **Two approval gates.** After the scan, stop and let the user pick which campaigns
  to spin. Do not spin everything automatically.
- **No em dashes anywhere.** Not in copy, not in output. Use commas or periods.

## The verified sender-bounce metric

Confirmed against the live dashboard on 2026-08-26:

```
sender_bounce_rate = round( sender_bounces / sent_count * 1000 ) / 10   (percent, 1 decimal)
```

- `sent_count` comes from `get_campaign_analytics` (lifetime).
- `sender_bounces` comes from `check_campaign_bounce_or_lead_quality`, at
  `data.detailedFindings.leadIntegrity.bounceAnalysis.sender_bounces`. This tool is
  **lifetime** and ignores date ranges.
- **Sender bounce is its own number.** It is a separate metric from total/regular
  bounce, exactly like the dashboard shows them in separate columns. Do NOT infer
  sender bounce from total bounce, do NOT use total bounce to decide whether to check
  a campaign, do NOT compare the two. The only two numbers that matter are
  `sender_bounces` and `sent_count`.
- A campaign is a **culprit** when `sender_bounce_rate > 5.0` AND `sent_count >= 500`
  (the floor keeps a 40-send campaign with 3 bounces off the list).

Do the arithmetic with `scripts/compute_bounce_rates.py` so every run uses the same
rounding the dashboard uses. Do not eyeball it.

---

## Phase 1. Scan (read-only)

Goal: a ranked list of campaigns over the 5% sender-bounce line.

**Scope is deliberately ACTIVE campaigns only.** Spintax helps a campaign that is
still sending, so paused, completed, and archived campaigns are out of scope by
design (this was a considered decision, not an oversight). The dashboard shows all
statuses; this skill intentionally does not.

1. **Pick the scope.** Default is every ACTIVE campaign across all clients. If the
   user named a client, scope to that client's `client_id` (from `get_all_clients`).
2. **Enumerate campaigns.** For each client, call `get_campaigns` with that
   `client_id`. These payloads are large and get saved to a file; do not read the
   whole thing into context. Extract only ACTIVE campaigns (id + name) with a quick
   parse.
3. **Get sent_count.** Call `get_campaign_analytics` per active campaign and keep
   `sent_count`. Drop any campaign with `sent_count < 500` (the volume floor). That
   is the ONLY filter before the sender check. Do not look at total bounce.
4. **Get sender bounces for EVERY remaining campaign.** Call
   `check_campaign_bounce_or_lead_quality` for each campaign that cleared the 500-send
   floor and read `sender_bounces`. There is no shortcut here: sender bounce is a
   separate number from total bounce, so you cannot skip a campaign based on its total
   bounce. Check them all. If a call returns nothing or an unexpected shape, wait ~2s
   and retry once with a fresh call before giving up. If it still fails, mark that
   campaign "sender data unavailable" and show it separately, never as 0%. For a
   full-account scan this is many heavy calls; keep them throttled and sequential to
   respect Smartlead's shared account-wide rate limit.
5. **Compute and rank.** Write the collected rows to a JSON file and apply the formula,
   the 5% threshold, and the 500-send floor, then print the ranked culprit table.
6. **Present the culprits** as a table: client, campaign, sent, sender bounces, sender
   bounce rate. Then **stop and ask which campaigns to spin. Do not proceed on your own.**

Row JSON shape:
```json
[{"campaign_id": 3423395, "name": "Arovy: Salesforce Personas V4", "client": "Arovy",
  "sent_count": 24293, "sender_bounces": 2059}]
```

---

## Phase 2. Generate spintax and show it (read-only, the end of this skill)

For each campaign the user selected:

1. **Fetch the sequence.** `get_campaign_sequences <campaign_id>`. Email 1 is the step
   with `seq_number == 1`. Its live copy is inside `sequence_variants[]` (the top-level
   `subject`/`email_body` are usually empty for step 1). Spin **every live variant**
   (`is_deleted == false`); skip deleted ones. If the user asked for one specific
   variant, do just that one.
2. **Read the language rules.** Read the "Spintax language rules" section below in full
   before writing any braces, and the "Spintax examples" section for a real before/after
   and one annotated failure. The rules are the whole game; do not spin from memory.
3. **Spin the copy** per the rules:
   - **Subject:** one flat spin group of up to 20 whole-unit options. Aim for 1 to 3
     words, lowercase, no punctuation, internal-note feel. Guidelines with room for
     exceptions, not hard laws. 20 is a target, not a quota.
   - **Body:** roughly one group per clause, 3 to 4 options each, around 15 to 20 groups
     in a 100-word email. Spin connective tissue, framing verbs, neutral synonyms, CTA
     tier, and sign-off. Never spin the exclusion list in the rules (merge fields,
     numbers, proof points, the core problem statement, signature and fourth-wall lines).
   - Preserve all HTML tags and merge fields exactly. Spin text, never markup, never
     anything inside `{{ }}`.
4. **Validate.** Render random combinations and check for em dashes, banned phrases,
   broken or nested braces, and spin groups colliding with merge fields (hard failures),
   plus subject style and a word-count ceiling (warnings). Fix every hard FAIL and re-check.
5. **Show the before/after** in chat: original subject/body next to the spun version for
   each variant, ready for the user to copy and paste into Smartlead. **Then stop. This
   skill ends here.** Do not push, do not offer to push.

## Deferred (future phase, not built into this version)

Pushing the spun copy straight to Smartlead is intentionally out of scope for now. The
team copies and pastes the spintax by hand. Do NOT write to Smartlead until Jaimin
explicitly turns that phase on.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22). The recipe above is Pablo's original text; this section only maps it to the tools available here.

- Smartlead: REST only (Pablo's 2026-09-28 rule). Base `https://server.smartlead.ai/api/v1`, auth `?api_key=$SMARTLEAD_API_KEY` (already in the box env; never print, log or save it). There is no Smartlead MCP on this box. Run calls from Shell with Python shelling out to `curl`.
- Files: write scratch output to `/workspace/`.
- Standing rules: never delete without Pablo's explicit authorization, the Friday weekly sweep routine never detaches (other tasks may detach when the task calls for it, chat 2026-10-22), verify every number by re-pulling, no em dashes.

REST equivalents:
- MCP `get_all_clients` = `GET /client/` (verified 2026-10-22).
- MCP `get_campaigns` = `GET /campaigns` unfiltered, then filter client-side by `client_id` (the `?client_id=` filter times out for 100+ campaign clients).
- MCP `get_campaign_analytics` = `GET /campaigns/{id}/analytics` (verified 2026-10-22; has `sent_count`, `bounce_count`, `reply_count`).
- MCP `get_campaign_sequences` = `GET /campaigns/{id}/sequences` (verified 2026-10-22; steps with `seq_number`, `subject`, `email_body`, `sequence_variants`).
- `GET /campaigns/{id}/mailbox-statistics?limit=100&offset=0` (verified 2026-10-22; rows have `email_account_id`, `from_email`, `sent_count`, `reply_count`, `bounce_count`, `sender_bounce_count`).
- `check_campaign_bounce_or_lead_quality` (source of `sender_bounces`): REST equivalent not yet verified. Candidate: sum `sender_bounce_count` over every page of `mailbox-statistics`, not yet checked against the Command Center dashboard, so label any number from it as unverified.
- `scripts/compute_bounce_rates.py`, `scripts/validate_spintax.py` and `scripts/build_push_payload.py` were not in the export. Apply the formula directly (`round(sender_bounces / sent_count * 1000) / 10`, culprit when >5.0 and sent_count >= 500) and run the QA checks below by hand or with a quick Python script.
- Never push to Smartlead; this skill ends at showing the spintax.

---

## Spintax examples

A real PP Email 1 spun the right way, and one over-spun failure annotated. Study both.

### Good: Whip Around limo campaign, Email 1

Before:

```
Subject: inspections

Hey {{first_name}}, we work with a few other limo/chauffeur companies in {{City_WI}},
so I wanted to connect. Most used texts to catch issues between jobs and things got
missed: unreported dents, stained seats, or messy interiors.

Whip Around helps drivers log it all from their phone with time-stamped photos, so you
know exactly when something happened and who caught it. No more surprises when the next
guest gets in.

Would it be a bad idea to try it out for free?

Thanks,
```

After, subject (one flat group of 20 whole-unit options):

```
{inspections|vehicle checks|walkarounds|unreported dents|stained seats|damage logs|between jobs|your fleet|limo interiors|from linkedin|other limo companies|driver checkins|catch it early|photo logs|the next guest|messy interiors|free trial|quick idea|possible fit|vehicle damage}
```

After, body (HTML preserved, merge fields and the problem statement untouched):

```html
<div>{Hi|Hey|Hello} {{first_name}}, {we work with|we've been working with|we've helped} a few other limo/chauffeur companies in {{City_WI}}, so I {wanted to connect|figured I'd reach out|thought I'd drop you a note}. Most {relied on texts|used texts|tracked things by text} to catch issues between jobs and stuff {got missed|slipped through|fell off}: unreported dents, stained seats, or messy interiors.<br><br></div><div>Whip Around {helps|lets} drivers {log|capture|record} it all from their phone with time-stamped photos, so you {know|can see} exactly when something happened and who caught it. {No more surprises|Nothing slips} when the next guest gets in.<br><br></div><div>{Would it be a bad idea to try it out for free?|Any interest in trying it out for free?|Open to trying it out for free?}</div><br><div>{Thanks,|thanks|Cheers,|Best,}</div><br>
```

Why this works:
- The subject group is 20 finished subjects, all orbiting the same email. Each is 1 to 3 words, lowercase, no punctuation.
- The problem statement `unreported dents, stained seats, or messy interiors` is left completely alone. That is the winning ICP language.
- `{{first_name}}` and `{{City_WI}}` are untouched. `time-stamped photos` (a proof detail) is untouched.
- Every CTA option is the same soft-ask tier.
- Each body group is a clean drop-in. Boundaries sit at phrase edges, never mid-idiom.

### Bad: the same email over-spun

```html
Subject: {Inspections!|quick question|boost your fleet uptime}

<div>{Hi|Hey|yo} {{first|name}}, we {work with|helped|are working} a few limo teams, so I wanted to connect. Most had issues with {unreported dents|small dents|minor blemishes}, {stained seats|dirty seats|soiled upholstery}, or messy interiors.<br></div><div>Drivers {log|capture} it in {3-5|about 4} seconds. {Want to try it free?|Happy to hop on a call and walk you through the whole platform whenever suits you.}</div>
```

What is wrong:
- Subject: capital letter and punctuation, the banned phrase "quick question", and an ad-like option over 3 words.
- `{Hi|Hey|yo}`: "yo" is a different register. Voice-consistency fail.
- `{{first|name}}`: a spin group jammed inside a merge field. Breaks the merge.
- `we {work with|helped|are working}`: tense clash, "we are working a few limo teams" does not parse.
- An em dash after "teams" (in the original failure): banned everywhere.
- Spinning the core problem statement: "minor blemishes" and "soiled upholstery" are nobody's real words.
- `{3-5|about 4} seconds`: spinning a number is fabrication.
- CTA mixes a one-tap yes/no with a book-a-call. Different asks; never in the same group.

---

## Spintax language rules

Spintax multiplies whatever you write by every combination, so a single sloppy option poisons a fraction of every send. Read this in full before writing a single brace.

Two brace systems, never confuse them:
- **Spin group:** single braces, `{option one|option two|option three}`. Smartlead picks one at send time.
- **Merge field:** double braces, `{{first_name}}`, `{{City_WI}}`, `{{company_name}}`. **Never** put a spin group inside a merge field, and never spin a merge field's contents. Keep spin groups flat: no nesting.

Preserve all HTML (`<div>`, `<br>`) and all merge fields exactly. Spin the text between them, not the markup.

### Subjects: 20 whole-unit variations

The subject is spun as **one flat group of up to 20 complete subjects**, never word by word. `{quick|fast} {note|question}` is banned. Write each of the 20 as a finished subject.

Every option must independently pass the PP subject rules:
- 1 to 3 words, lowercase, no punctuation.
- Reads like something a colleague typed in four seconds, not a campaign.
- Same angle as the email. All 20 orbit the same topic.

Draw from four buckets:
1. The topic noun, plain: `inspections`, `vehicle checks`, `walkarounds`
2. The pain in their words: `unreported dents`, `missed damage`, `stained seats`
3. The context or relationship: `from linkedin`, `your fleet`, `other limo companies`
4. The offer: `free trial`, `quick idea`, `possible fit`

Banned in every subject option: "quick question" (banned everywhere), any punctuation, any capital letter, anything over 3 words, buzzwords, anything that reads like an ad.

**20 is a target, not a guillotine.** Fourteen great subjects beat twenty padded with six that smell automated.

### Body: 3 to 4 options per clause

Roughly one spin group per clause or sentence, 3 to 4 options each. In a 100-word email that lands around 15 to 20 groups.

Where to spin:
- **Greeting:** `{Hi|Hey|Hello} {{first_name}}`, always.
- **Connective tissue:** `wanted to {reach out|connect|send a note|drop you a line}`.
- **Framing verbs, not the observation:** `{We've been working with|We work with|We've helped} a few {{niche}} teams`.
- **Truly neutral synonyms:** one or two, only where the swap changes nothing.
- **CTA, within one tier:** `{Lmk if you want more details.|Happy to send more details if useful.|Want me to send more details?}`. Do not mix a yes/no ask with an open-ended one.
- **Sign-off:** `{Thanks,|thanks|Cheers,|Best,}`, the lowercase option is intentional.

Where NEVER to spin (hard exclusion list):
- **Merge fields and `{{AI:}}` prompts.**
- **Numbers and proof points.** `3-5 days`, `15,000 communities`, named customers.
- **The core problem statement.** Winning language pulled from the ICP's world.
- **Signature and fourth-wall lines.** If you spin a fourth-wall line at all, every option must be equally honest and specific.
- **P.S. lines.** Spin lightly or not at all.
- **Email 2 and Email 3.** Out of scope entirely.

### The grammar-integrity rule

Every option in a group must be a drop-in replacement: same part of speech, same tense, agreeing with the words before and after the braces. Read the sentence out loud once with each option substituted in. Put boundaries at natural phrase edges, never mid-idiom: spin `{drop you a line|send a note}`, never `drop you a {line|note}`.

### The voice-consistency rule

Every option in a group carries the same register. `{Lmk|Let me know|Please advise}` fails. Casual email, every option casual.

### QA workflow (before showing anything)

1. Render 3 to 5 random full combinations and read each as the prospect. Every render must pass the founder-note test.
2. Check for em dashes, "quick question", broken or nested braces, spin groups inside merge fields, subject-rule breaks, and the word ceiling. Fix every FAIL and re-check.
3. Word count: check the longest render, not the shortest.
