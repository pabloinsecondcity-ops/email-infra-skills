---
name: Smartlead per-inbox reply counts (fast + accurate)
description: >-
  Use whenever you need campaign reply counts per Smartlead inbox. Fast one-call
  analytics for quick checks; accurate message-history method when decisions
  depend on it (the weekly burned sweep).
---
# Per-inbox reply counts in Smartlead

## Option A: fast (default for quick checks, ~10 seconds)
1. `GET https://server.smartlead.ai/api/v1/analytics/mailbox/name-wise-health-metrics?api_key=$SMARTLEAD_API_KEY&start_date=2023-01-01&end_date=<today>` (ranges over 30 days work).
2. `data.email_health_metrics[]` has `from_email`, `sent`, `opened`, `clicked`, `replied`, `unsubscribed`, `bounced` per mailbox.
3. Join to `/email-accounts/` on lowercased `from_email`. Missing inboxes have never sent: 0 replies.
4. Caveat: on 2026-10-13 it disagreed with the accurate method on 39 of 126 low-rep inboxes (often 0 for re-created inboxes with real replies). Say so when reporting, and don't use it alone for burned or delete decisions.

## Option B: accurate (about an hour, used by the weekly burned sweep)
1. Pull email accounts and narrow to the inboxes needed, for example warmup rep >0 and <90.
2. Pull replied leads from every non-draft campaign, including archived ones.
3. Keep replies in the inbox's own client campaigns that came after the inbox was created in Smartlead.
4. Read each lead's message history to find the actual sending address. Credit the reply to every inbox that sent in that thread.
5. Auto-replies and out-of-office replies count as replies. OOO and other auto-replies (for example no longer with the company, ticket acknowledgments) count as replies for burned and healthy, but not as human/positive replies in reply-rate scoring (Pablo, chat 2026-10-22).
6. Rate limit is about 800 requests per minute. Cache counts between runs where you can.

## Middle option
`GET /campaigns/{id}/mailbox-statistics?limit=20&offset=N` (no dates means the whole campaign). Sum `reply_count` by `email_account_id`. Takes about 5 to 10 minutes.
