---
name: sync-context
description: >-
  Use when someone says sync context for [client] or update context for
  [client]: pull the latest Slack activity and TLDV meeting transcripts for the
  client and write a fresh context.md.
---
# Skill: sync-context

**Trigger:** "sync context for [client]" / "update context for [client]"

**Who runs this:** AMs before any client work, GTM Engineers before a list build, Jed before a business pulse check.

**What it does:** Pulls the latest Slack activity and TLDV meeting transcripts for a client and writes a fresh `context.md` so the team has current context.

---

## Step 1. Look up the client in the registry

Read `clients/registry.md`, find the client's row, note the folder name and Slack channel IDs. If the client isn't there, stop and say so.

## Step 2. Read the client's Slack channels

Last 30 messages (or 30 days, whichever is less) from:
1. **Main PP working channel** (campaigns and strategy)
2. **Positive replies channel**

Do NOT read `#replies-[client]`; it's raw notification noise.

Summarize into: team discussion highlights (decisions, open questions, things flagged by Eric/Pablo/Jaimin/Jed) and notable positive replies (prospect name, company, what they said, follow-up notes).

## Step 3. Pull TLDV meeting transcripts

`python integrations/tldv.py --client "[client name]" --days 60` (uses `$TLDV_API_KEY`). Per meeting: date and title, summary or key highlights, action items. If none, note that and continue.

## Step 4. Write the updated context.md

Write to `clients/[folder]/context.md` with this structure:

```
# [Client Name]. Context

Last synced: [today's date]

## Recent Meetings

### [YYYY-MM-DD]. [Meeting Title]
**Summary:** [2-4 sentences]
**Key decisions:** [bullets or "None noted"]
**Action items:** [bullets or "None noted"]

---

## Slack Highlights (last 30 days)

### Team channel (#[channel-name])
[2-5 bullets: decisions, flagged issues, open questions]

### Positive replies (#[channel-name])
[prospect name, company, gist, follow-up context]

---

## Campaign Status Notes

[Anything inferable about campaign health, active segments, messaging experiments. Otherwise a one-line placeholder.]
```

Do not invent information. Empty sections say "Nothing in the last 30 days."

## Step 5. Confirm

Tell the user: which client, how many TLDV meetings, how many Slack messages read, the file path.

**Approval gate:** none, read-only sync. Flag anything wrong (no TLDV results, API error, client not found) clearly.

---

## Channel map

| Client | PP Working Channel | Positive Replies Channel |
|---|---|---|
| Whip Around | #whiparound | #hot-leads-whiparound |
| Mortarlink | #mortar-link | (none found) |
| CMAP | #cmap | #cmap-positive-replies |
| Mixmax | #pp-mixmax | #mixmax-positive-replies |
| Axero Solutions | #axerosolutions | (none found; check #axero-non-ooo-replies) |
| SignWell | #signwell | #signwell-positive-replies |
| Arovy | #arovy-pp | (none found) |
| KickCharge | #kickcharge-pp | #kickcharge-positive-replies |
| LogixBoard | #logixboard-pp | #logixboard-positive-replies |
| Routeware | #routeware-pp | #positive-replies-routeware |
| BMO Media | #connect-write-pp | #connect-write-positive-replies |
| RevPilots | #revpilots-pp | #positive-replies-revpilots-2 |
| D8 Group | #d8-pp | #d8group-positive-replies |

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- No Slack connector and no TLDV key on the box, and `integrations/tldv.py` is not on the box. Not runnable until Slack is connected and a TLDV key is added as an env var.
- `clients/` files are in the pp-gtm repo, not on the box. Never invent facts or names. No em dashes.
