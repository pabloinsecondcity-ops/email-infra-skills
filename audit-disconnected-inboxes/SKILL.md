---
name: audit-disconnected-inboxes
description: "Use when Pablo asks for the weekly disconnected inbox audit, to find Smartlead inboxes with failed SMTP/IMAP auth, confirm whether they still exist at the provider, confirm they are not sending, and list or tag them for Pablo; deletion only with his explicit OK for that specific list."
---

# Audit Disconnected Inboxes (Weekly)

Trigger: "give me all the disconnected inboxes" / "check for disconnected inboxes" / "clean up disconnected inboxes" / weekly recurring.

Built and confirmed 2026-08-04 across CMAP, BMO Media, Axero, SignWell, Practical Prospecting, Mortar Link (521 disconnected inboxes found that day).

---

## Step 1 -- Pull every Smartlead inbox, filter to disconnected

Page through `GET /email-accounts` (Smartlead REST, `?api_key=...`, `limit=100`, no client filter -- pulling all clients in one pass is faster than per-client calls). ~6,700 total inboxes takes ~70 pages.

An inbox is **disconnected** if `is_smtp_success` is `false` OR `is_imap_success` is `false` (confirmed field names, see [[feedback_smartlead_api_lessons]]). Capture per inbox: `id`, `email`/`username`, `client_id`, `type` (GMAIL/OUTLOOK/SMTP), `daily_sent_count`, `campaign_count`, `smtp_failure_error`, `imap_failure_error`.

Reference script: `/workspace/disconnected_inboxes_2026-08-04_v2.py` -- copy it forward with a new date suffix each week (matches this repo's dated-script convention, never overwrite the prior week's file).

**Do NOT use the MCP tool `get_email_accounts` for this** -- a single page of 100 accounts blows the tool-result token limit (157k+ chars). Call the raw REST endpoint from a Python script instead and only summarize counts back into the conversation.

Report back: total disconnected count, breakdown by `client_id`, breakdown by `type`. On 2026-08-04 all 521 disconnected inboxes were type SMTP -- 0 Gmail/Outlook -- worth checking each week since it changes the story (Gmail/Outlook disconnects usually mean a real reauth is needed, SMTP disconnects usually mean the mailbox is gone upstream).

---

## Step 2 -- Confirm each disconnected inbox still exists on Mission Inbox (the source)

**The domain existing in MI does NOT mean the specific inbox exists in MI.** Checking only `GET /api/domains` and matching by domain name is misleading -- MI often keeps the domain connected but has trimmed the mailbox list down to a smaller canonical set (e.g. 10 clean addresses like `first@`, `first.last@`) while Smartlead still has old inbox records for variants that no longer exist on MI (`edwardsb@`, `benedwards@`, `d.greaves@`, etc.). Confirmed 2026-08-04: 11 of 32 disconnected domains matched in MI at the domain level, but **0 of 521 disconnected inbox email addresses** matched an exact mailbox in MI once checked properly.

**Correct check -- exact email match against MI's mailbox list, not the domain list:**

1. `GET /api/domains` (Mission Inbox, header `X-Server-API-Key: ...`, paginate `limit=100&page=N`) -- only needed if you want domain-level DNS health context, not for the existence check itself.
2. `GET /api/mailboxes` (same auth), paginate `limit=100&page=N` across ALL pages (confirmed ~1,200 mailboxes total as of 2026-08-04, ~13 pages) -- build a set of every `email` field, lowercased.
3. Compare the disconnected Smartlead email list against that MI mailbox-email set. Anything not in the set no longer exists on MI -- MI has nothing to reconnect it to.

MI API base: `https://api.v4.missioninbox.com`. Key lives in [[project_mission_inbox_integration]].

---

### Step 2b -- Zapmail check (Pablo, chat 2026-10-13)

For Zapmail-provisioned inboxes, compare the disconnected Smartlead list with Zapmail (`user-Zapmail` read tools): does the mailbox still exist, is it scheduled for deletion, does it show errors. Pablo noted some mailboxes show "Active" in Zapmail but are not usable and are not billed, so report the Zapmail status as seen, do not assume it is healthy.

## Step 3 -- Confirm the inbox isn't sending anything today

Even though a disconnected inbox (`is_smtp_success: false`) mechanically cannot send (auth fails at the SMTP layer), confirm explicitly before deleting:

- `daily_sent_count` == 0 for today
- `campaign_count` == 0 (not attached to any campaign, so nothing is even queued to try)
- Before calling a batch disconnected, spot-check a sample (Pablo asked for 10 on 2026-10-19) for any emails sent today.

Confirmed 2026-08-04: all disconnected inboxes showed `daily_sent_count: 0` and `campaign_count: 0`. Note `campaign_count` on the bulk list endpoint has been unreliable/stale in other contexts (see [[feedback_smartlead_api_lessons]] -- Whip Around case), so if this number matters for a specific client's decision, spot-check a sample with `get_email_account_by_id(fetch_campaigns=true)` before trusting it at scale.

---

## Step 4 -- Delete, with explicit go-ahead

**Deletion gate (chat 2026-10-20: "don't ever delet things without my authorization").** Never delete anything (Smartlead, Zapmail, Mission Inbox, anywhere) without Pablo's explicit OK for that specific deletion. No Zapmail removal scheduling. Default instead: tag and list, Pablo deletes manually. Pattern Pablo used on 2026-10-19/20: give him the list, tag the confirmed ones `burned` in Smartlead when he asks, and he removes the ones that are tagged `burned` and disconnected himself.

Once an inbox is confirmed (a) disconnected, (b) not present in MI's mailbox list, and (c) not sending / not campaign-attached, it's safe to remove from Smartlead: `DELETE /email-accounts/{id}` (confirmed endpoint, returns `{"ok": true}`).

**Always get Pablo's explicit go-ahead before running the deletes** -- this is permanent and matches the standing rule to never delete without permission ([[feedback_smartlead_assignment]]). Report the final confirmed-safe count and per-client breakdown first, then wait for the word before calling delete.

---

## Weekly cadence

This is a recurring job -- run it every week (or when Pablo asks "give me the disconnected inboxes"), not just once. Each run should produce a freshly dated CSV (never overwrite the prior week's), and the disconnected count/composition can legitimately shift week to week as MI's canonical mailbox set changes or new domains rotate in.

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
- `GET /campaigns/{id}/email-accounts` (verified 2026-10-22 with a read-only GET) is the live roster of what is attached right now. Response objects include SMTP/IMAP passwords, so keep only `id`, `from_email`, `type` and never print or save the rest.
- `GET /campaigns/{id}/mailbox-statistics?limit=100&offset=0` (verified 2026-10-22 with a read-only GET; rows have `email_account_id`, `from_email`, `sent_count`, `reply_count`, `bounce_count`, `sender_bounce_count`).
- MCP `delete_email_accounts_from_campaign` = `DELETE /campaigns/{id}/email-accounts` with `{"email_account_ids": [...]}`, returns `{"ok": true, "result": N}` (documented). Write action: only on Pablo's explicit go-ahead.
- MCP `get_all_clients` = `GET /client/` (verified 2026-10-22 with a read-only GET; returns `id`, `name`, `email`, ...).

- Mission Inbox: valid provider again (Pablo, chat 2026-10-22, about 900 MI inboxes not yet on campaigns), so MI inboxes are in scope for this audit. API `https://api.v4.missioninbox.com` with header `X-Server-API-Key`. No Mission Inbox key is on the box, so the MI existence check is not runnable yet; report MI inboxes as unconfirmed at the provider until the key is added. REST equivalent not yet verified from here; ask Pablo to add the key as an env var (never paste it into a skill or chat).
- Zapmail: use the `user-Zapmail` MCP connector (read tools such as `list_workspaces`, `list_domains`, `list_mailboxes`, `get_mailbox_details`, `check_dns_records`, `get_export_status` are safe). Write tools (`provision_mailboxes`, `assign_mailboxes`, `export_mailboxes_to_third_party`, `schedule_mailbox_removal`) need Pablo's explicit go-ahead. Note: the connector's `schedule_mailbox_removal` describes removal of a specific set of mailboxes by ID, which contradicts the older Claude note that Zapmail deletion cannot target individual mailbox IDs. Not tested (it is a delete).
- The reference script `disconnected_inboxes_2026-08-04_v2.py` is not on the box. Earlier box runs of this audit wrote `/workspace/disconnected_inboxes_<date>.csv` and checked Zapmail-provisioned Gmail inboxes against the Zapmail connector instead of Mission Inbox.
- The clear-out step (detach or delete from Smartlead) is a write or delete. Report first and wait for Pablo's explicit go-ahead; deletion is never standing.
