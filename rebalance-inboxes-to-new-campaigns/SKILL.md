---
name: rebalance-inboxes-to-new-campaigns
description: "MOST COMMON CASE. Use when a client already has running campaigns and new campaigns were created: take inboxes from the active campaigns and add them to the new ones so every campaign has an even count, provider mix, 1 inbox per campaign, then report any inbox not at exactly Gmail 25/day, Outlook 6/day or SMTP 35/day (too high or too low) or with a gap not at 20 min (Pablo decides; never change caps or gaps on your own). Keep it simple. Once Pablo confirms the plan, inboxes may be taken off old campaigns to move them to the new ones."
---

# Rebalance inboxes onto new campaigns (simple)

Goal in one line: every target campaign ends with the SAME number of inboxes (N = eligible pool / number of campaigns), a Gmail/Outlook/SMTP mix in each, and no inbox on more than one of the target campaigns.

Keep it simple. Restate the goal in 2-3 lines, get one go, run it, report. Do not pile on extra questions or side flags.

## Inputs (from the user)
- Client
- Target campaign IDs (live ones + new/paused ones)

## Rules
- Never pause/resume or change any campaign's status. Live stay live, paused stay paused (user launches).
- Never delete inboxes. Only remove/add at campaign level.
- Don't touch campaigns outside the target list.
- Never mix clients.
- REST with `SMARTLEAD_API_KEY`, 10-15 parallel workers.

## Steps
1. **Fresh pull.** Rosters of every target campaign (`GET /campaigns/{id}/email-accounts`) and the client's inbox list (`GET /email-accounts?client_id=`; take TAGS and warmup from this bulk list, the single-inbox endpoint no longer returns tags). Save a backup snapshot JSON.
2. **Eligible pool.** Client's connected inboxes minus: Burned, `WARMING UP - DONT USE YET`, future `Dont use until MM/DD`, disconnected, other clients.
3. **Target N** = pool / number of campaigns (divmod; spread remainder). Per campaign aim for an even Gmail/Outlook/SMTP share, mixing vendors too (Zapmail, Mission Inbox), as much as possible by default (Pablo, chat 2026-10-22).
4. **Plan (minimize churn).** Keep inboxes where they already are when possible; on live campaigns keep highest warmup. Remove extras and any ineligible inboxes. Fill short campaigns from removed + unused inboxes. Each inbox to exactly one target campaign. Write plan CSV.
5. **Canary.** POST one add to one paused campaign, re-GET, confirm +1 only (roster can lag ~20s).
6. **Execute.** Removals `DELETE /campaigns/{id}/email-accounts` `{"email_account_ids":[...]}`; adds `POST` same path; batches <=100.
   Once Pablo confirms the plan, removals from old campaigns run as part of the move, per this skill's design (chat 2026-10-22). The Friday weekly sweep routine never detaches; other tasks may detach when the task calls for it (Pablo, chat 2026-10-22).
7. **Verify.** Re-GET every roster: each exactly N, all eligible, no inbox on 2 targets, mix per campaign. Fix shortfalls once.
7b. **Swap tags (forever step).** After the inboxes are added and verified on their campaigns, remove the tags 'WARMING UP - DONT USE YET' and any 'dont use until X' from those inboxes, and add the tag 'ACTIVE' instead. (Pablo, chat 2026-10-26, forever step, approved wording) Only for inboxes confirmed present on their target roster; read back tags after.
8. **Inbox settings on the pool.** "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own." (Pablo, chat 2026-10-22, forever rule, approved wording) Report any inbox not at exactly Gmail 25/day, Outlook 6/day or SMTP 35/day to Pablo, too high and too low separately; do not change caps on your own, only when he explicitly asks in this conversation. Gap between sends per inbox is always 20 min for every inbox type; gaps not at 20 min are monitored and reported to Pablo only, never fixed automatically (Pablo, chat 2026-10-22). The exact 25/6/35 standard applies to every client. If Pablo asks for the cap fix, set the exact value via `POST /email-accounts/{id}` and read back. Canary one inbox and verify it BEFORE the batch starts, not in parallel with it (lesson from 2026-10-16). (Current standard per Pablo 2026-10-22; overrides older 5/day Outlook notes and the Oct 16 keep-higher-caps exception.)
9. **Report.** Short table: campaign, status, count, G/O/S. Attach verify CSV.

## Related
- assign-inboxes (empty campaigns only)
- add-inboxes-to-campaigns (add-only, no removals)
- redistribute-inboxes is superseded by this skill (Pablo, chat 2026-10-22)
