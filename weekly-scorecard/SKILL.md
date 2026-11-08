---
name: weekly-scorecard
description: >-
  Use when Pablo asks to fill, update, check or pull the weekly Scorecard (inbox
  health per client in the Scorecard Google Sheet), on demand or from the Friday
  routine.
---
# Weekly Scorecard

Fills THIS week's rows in Pablo's Scorecard sheet: one row per client with inbox inventory, health, volume, burned and cost. Report-only for Smartlead: change nothing in Smartlead or Zapmail while doing this.

## Sources
- Smartlead REST: https://server.smartlead.ai/api/v1/...?api_key=$SMARTLEAD_API_KEY (never print the key).
- Sheet: 1vJtD4FvPX63t8vFQ02OPvuPIN01emkxn_y5bgS0BIlY, tab "Scorecard" (Google Sheets connector).

## Week definition (one for everything)
Sunday through Saturday, the week in progress on the day it runs (weekends included). Example: a run on Fri Oct 16 uses Sun Oct 11 to Sat Oct 17. Never mix last week's sends or burned into this week's row. If Pablo asks for a specific past week, use that Sun-Sat window instead.

## Client mapping (Smartlead client to Scorecard name)
cmap.io=CMAP, Wayne Selman=SignWell, Jason Lee=BrandXYZ, Mike Flournoy=Whip Around, Adam Ilowite=Axero Solutions, Camp Digital=CAMP Digital, Clay Christenson=Maven Analytics, Jed Mahrle=Practical Prospecting (internal), Patrick McLaughlin=Mortar Link, Gabe P=Rocket Shipping.
Ignore: Pablo, Aragorn, Sell Better, Data Image. INCLUDE sending.ac inboxes in every count until Pablo says to stop.
If a client appears that isn't mapped, report it and ask Pablo; don't invent a row name.

## Rules
- Burned (Pablo, confirmed 2026-10-22): warmup reputation below 90% AND zero replies of any kind (OOO and other auto-replies count as replies). 90%+ or at least one reply of any kind means not burned. Skip inboxes tagged WARMING UP - DONT USE YET.
- Healthy (FOREVER, Pablo 2026-11-04): EVERY inbox is healthy UNLESS it is burned. Burned = warmup under 90% AND 0 replies. Warming-up, disconnected, warmup-off and low-rep inboxes with any reply all count as healthy. Total = all of the client's inboxes (warming included). Healthy = Total minus burned.
- Use the accurate slow reply method (message history) for burned and healthy decisions, per smartlead-per-inbox-reply-counts-fast. Reuse a recent reply cache when it's from the same day.

## Columns
- Total / Healthy / ops columns: snapshot at run time.
- Avg Daily Volume: actual sends ONLY inside this week's Sun-Sat window up to the run day, divided by days elapsed in the window (by 7 once the week is over). Never use the prior week.
- Burned This Week: inboxes that became burned in this week's sweep (from the weekly burned sweep CSV if it ran this week, otherwise compute it with the rule above and say so).
- New Inboxes Created This Week: created_at inside the Sun-Sat window.
- Weekly cost: ($3 x Total Inboxes) / 4.
- Healthy Daily Capacity: sum of message_per_day across healthy inboxes (all non-burned inboxes).
- Never type into grey % (formula) columns.
- Mission Inbox: pending until Pablo says how to count it.

## Steps
1. Pull /client/ and all /email-accounts/ (paginate). Drop ignored clients (keep sending.ac).
2. Map inboxes to clients and compute every column per the rules above.
3. Read the Scorecard tab. Find this week's Week Of rows. Add them if missing, or update them in place if they exist. Never edit other weeks' rows.
4. Write only the value columns, then read the sheet back and confirm every written cell matches.
5. Report to Pablo: one line per client (total, healthy, burned this week, avg daily volume, healthy capacity), plus anything unverified or unmapped. Plain text, no em dashes, only verified numbers. Don't create a Daily logs tab unless he asks.
