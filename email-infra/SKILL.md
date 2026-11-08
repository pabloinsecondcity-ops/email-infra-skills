---
name: email-infra
description: "Use at the start of any session involving domain or inbox work for Practical Prospecting: the knowledge base for Dynadot domains, Mission Inbox and Zapmail provisioning and warmup, and Smartlead inbox config, campaign assignment, and rotation detection."
---

# Email Infrastructure. Practical Prospecting

This is the single reference for everything infrastructure-related. It covers how the four systems connect, the full lifecycle for new clients, the inbox rotation workflow, and all the API traps learned the hard way.

---

## How the four systems connect

```
Dynadot (buy domains) -> Mission Inbox / Zapmail (create inboxes, warmup) -> Smartlead (campaigns, sending)
Rotation detection happens in Smartlead and flows back to remove/replace inboxes
```

New client flow: Dynadot -> MI or Zapmail -> Smartlead
Rotation flow: Smartlead detects -> remove from campaign -> quarantine in MI/Zapmail -> delete -> reprovision via Dynadot + MI/Zapmail -> back into Smartlead

Friday weekly sweep routine (chat 2026-10-13 and 2026-10-20): burned inboxes are only tagged `burned` in Smartlead and their domains tagged `burned` in Zapmail, with the campaigns they are on listed. The sweep does not detach, does not delete, and does not schedule Zapmail removal; Pablo reviews and deletes manually. The Friday weekly sweep routine never detaches; other tasks may detach when the task calls for it (Pablo, chat 2026-10-22). Deleting anything, anywhere, still needs Pablo's explicit OK for that specific deletion, and no Zapmail removal scheduling.

---

## Config files (always read these first)

- `/workspace/clients.yaml`, master client config (all IDs, job titles, rotation rules)
- `/workspace/.env`, all API keys (never hardcode)

```python
# Standard setup block for every script
import os, yaml
from dotenv import load_dotenv
load_dotenv()
with open("clients.yaml") as f:
    config = yaml.safe_load(f)
clients = config["clients"]
defaults = config["onboarding_defaults"]
rotation = config["rotation"]
```

---

## SYSTEM 1. DYNADOT (domain purchase)

### API basics
- Base URL: `https://api.dynadot.com/api3.json`
- Auth: `?key={DYNADOT_API_KEY}` as query param on every request
- Every endpoint is a GET
- Env var: `DYNADOT_API_KEY`
- Account: pablogallego9 / Practical Prospecting
- Pricing tier: Super Bulk Account
- **Actual .com price: ~$10.88/year** (confirmed 2026-07-06: 65 domains cost $707.20 = $10.88/domain)
- Budget formula: `ceil(domains * 10.88) + $5 buffer`

### Critical traps

1. **HTTP 200 means nothing.** Dynadot returns 200 for failures too. Always inspect the response body. Check `ResponseCode == 0` for success (loose equality, it can be string "0" or number 0). Exception: `set_ns` returns `SetNsResponse.Status === "success"` instead of a ResponseCode.
2. **`set_ns` comma encoding bug.** Multiple domains in one call use `domain=a.com,b.com`. URLSearchParams encodes the comma and breaks the call. Build that URL by hand.
3. **Search: max 100 domains per call.** Params are `domain0`, `domain1`, etc. Add ~1s delay between batches.
4. **Register: one domain per call.** Loop with ~500ms delay. Track partial failures, don't treat the batch as all-or-nothing.
5. **Nameservers are fixed per provider:**
   - Mission Inbox: use MI's nameservers (returned by MI domain create)
   - Zapmail: CloudNS nameservers (pns61-64.cloudns.*)
   - Hypertide (legacy): DNSimple nameservers (ns1-4.dnsimple*)
6. **To tell where a domain points:** check nameservers from `domain_info`. Contains `cloudns` = Zapmail. Contains `dnsimple` = Hypertide.

### Domain naming methodology
Never use the client's real primary domain, always brand-adjacent throwaway domains. Take the brand name, add safe prefixes/suffixes, use `.com` only. Keep it short and natural-sounding.

Safe suffixes/prefixes: leads, reach, growth, deals, system, solutions, strategy, digital, tools, services, build, lab, biz, online, global, outreach, base, data, hire, fleet, inc.

Avoid: `crm`, `hq`, `ai`, `pro`, `app`, `tech` (heavily squatted, rarely available).

Generate 1.5x the needed count as candidates, roughly half of common suffixes will be squatted. Check availability in batches of 90 via Dynadot search API.

Always confirm domain names with Pablo before purchasing. Purchases are irreversible.

### Lifecycle
1. Generate candidate names from client brand
2. Check availability: `command=search&domain0=...&domain1=...`
3. Register: `command=register&domain=example.com&duration=1`
4. Point nameservers: `command=set_ns&domain=example.com,example2.com&ns0=...`
5. Verify: `command=domain_info&domain=example.com`

---

## SYSTEM 2. MISSION INBOX (primary inbox provider)

### API basics
- Base URL: `https://api.v4.missioninbox.com`
- Auth header: `X-Server-API-Key: {MISSION_INBOX_API_KEY}` on every request
- All requests/responses: JSON with `Content-Type: application/json`
- SMTP host: `main.outboxment.com` port 465 (SSL)
- IMAP host: `main.outboxment.com` port 993 (SSL)
- Env var: `MISSION_INBOX_API_KEY`

### Standard Python client

```python
import os, time, requests
MI_KEY = os.getenv("MISSION_INBOX_API_KEY")
MI_BASE = "https://api.v4.missioninbox.com"
MI_HEADERS = {"X-Server-API-Key": MI_KEY, "Content-Type": "application/json"}

def mi_get(path, params=None, retries=3):
    for attempt in range(retries):
        r = requests.get(f"{MI_BASE}{path}", headers=MI_HEADERS, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 10))); continue
        r.raise_for_status(); return r.json()

def mi_post(path, body, retries=3):
    for attempt in range(retries):
        r = requests.post(f"{MI_BASE}{path}", headers=MI_HEADERS, json=body, timeout=30)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 10))); continue
        r.raise_for_status(); return r.json()

def mi_delete(path, retries=3):
    for attempt in range(retries):
        r = requests.delete(f"{MI_BASE}{path}", headers=MI_HEADERS, timeout=30)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 10))); continue
        r.raise_for_status(); return r.json() if r.content else {}
```

### Rate limits
- Default: 600 req/min
- Bulk endpoints: 30 req/min
- Always check `Retry-After` on 429s

### Provisioning pipeline

**Step 1, Create project** (one per client): `POST /api/projects` body `{ "name": "Client Name" }`, returns `{ "id": "uuid" }`. Store the project ID in clients.yaml under `mi_project_id`.

**Step 2, Create domains (bulk)**: `POST /api/domains/bulk-create` body `{ "domains": [{ "domainName": "domain1.com", "projectId": "uuid" }] }`, returns `{ "taskId": "uuid" }`. Poll until COMPLETED. Max 500 per call.

**Step 3, Push DNS (bulk)**: `POST /api/domains/bulk-push-dns` body `{ "domainNames": ["domain1.com"] }`. Pushes SPF, DKIM, DMARC, MX, Return-Path automatically if Cloudflare integration is configured. Otherwise returns values to add manually.

**Step 4, Verify domains (bulk)**: `POST /api/domains/bulk-verify` body `{ "domainNames": ["domain1.com"] }`. All four records (SPF, DKIM, MX, DMARC) must pass before mailboxes can be created. Safe to poll repeatedly.

**Step 5, Create mailboxes (bulk)**: `POST /api/mailboxes/bulk-create` body `{ "mailboxes": [{ "email": "john@domain1.com", "fullName": "John Smith", "password": "..." }] }`. Standard: 5 mailboxes per domain. Use contact names from clients.yaml. Username patterns: `firstname@`, `firstname.lastname@`, `f.lastname@`. Generate passwords with `secrets.token_urlsafe(16)`. Store in output CSV. Password always retrievable via `GET /api/mailboxes/{email}`.

**Step 6, SKIP: Do NOT enable warmup in MI.** Warmup runs inside Smartlead (already paid for). Enabling warmup in MI costs 7 credits per mailbox and is redundant. Never call the MI warmup endpoint.

**Step 7, Monitor warmup**: `GET /api/warmup/mailboxes/{email}` returns `{ "mailbox": { "warmedDays": 8, "isWarmupActive": true }, "warmyMailbox": { "syncStatus": "SYNCED" } }`. Wait for `syncStatus == SYNCED` before trusting `warmedDays`. Ready for Smartlead when `warmedDays >= 14` AND health score >= 8.5.

**Step 8, Health check before going live**: `POST /api/health-check/mailboxes` body `{ "emails": [...], "subject": "Following up on our conversation", "textContent": "Hi, I wanted to follow up on what we discussed. Let me know if you have questions." }`. Poll task, then `GET /api/health-check/mailboxes/{email}` for score (0-10). Only add to Smartlead if score >= 8.5.

### Bulk task polling pattern

```python
def poll_task(task_id, interval=3, timeout=300):
    import time
    start = time.time()
    while True:
        task = mi_get(f"/api/tasks/{task_id}")
        status = task["status"]
        if status == "COMPLETED":
            if task.get("result", {}).get("failed", 0) > 0:
                print(f"Partial failures: {task['errors']}")
            return task
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Task {task_id} {status}: {task.get('errors')}")
        if time.time() - start > timeout:
            raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
        time.sleep(interval)
```

### All bulk endpoints
| Endpoint | Body | Task type |
|---|---|---|
| POST /api/domains/bulk-create | domains[] | BULK_DOMAIN_CREATE |
| POST /api/domains/bulk-verify | domainNames[] | BULK_DOMAIN_VERIFY |
| POST /api/domains/bulk-push-dns | domainNames[] | BULK_DNS_PUSH |
| POST /api/domains/bulk-delete | domainNames[] | BULK_DOMAIN_DELETE |
| POST /api/mailboxes/bulk-create | mailboxes[] | BULK_MAILBOX_CREATE |
| POST /api/mailboxes/bulk-delete | emails[] | BULK_MAILBOX_DELETE |
| POST /api/warmup/mailboxes/bulk | emails[], enabled | BULK_WARMUP_TOGGLE |
| POST /api/warmup/domains/bulk | domainNames[], enabled | BULK_DOMAIN_WARMUP_TOGGLE |
| POST /api/health-check/mailboxes | emails[], subject, textContent | MAILBOX_HEALTH_CHECK |

### Error traps
- **409 Conflict**: domain or mailbox already exists, skip and log, don't fail
- **404 Not Found**: domain not verified yet, or email doesn't exist
- **403 Forbidden**: subscription inactive OR feature requires Pro plan (domain warmup is Pro-only; mailbox warmup available on Starter)
- **Bulk partial failures**: COMPLETED status does NOT mean all items succeeded, always check `result.failed > 0` and log `errors[]`
- **PENDING warmup sync**: after enabling warmup, wait for `syncStatus == SYNCED` before trusting warmedDays

---

## SYSTEM 3. ZAPMAIL (secondary inbox provider)

### API basics
- Base URL: `https://api.zapmail.ai/api`
- Auth headers: `api-key: {ZAPMAIL_API_KEY}` on every request
- Optional workspace header: `x-workspace-key: {workspace_id}`
- Optional provider header: `x-service-provider: GOOGLE` (or MICROSOFT)

### Rate limits
- General: 5 req/sec, 20 req/min
- Domain search: 10 req per 30 min
- Re-export mailbox: 3 per mailbox per week

### Key operations
- List workspaces, show domains in a workspace, check domain availability, create 5 mailboxes per domain where there are zero, export mailboxes to Smartlead, link Smartlead account.
- API: `GET /mailboxes`, `POST /mailboxes` (assign new mailboxes to domains), `PUT /mailboxes` (update), `PUT /mailboxes/remove` (remove on next renewal), `POST /mailboxes/export` (export to Smartlead/Instantly/CSV), `GET /mailboxes/export/status`, `GET /domains`, `POST /domains/connect`, `POST /domains/dns/check`, `POST /domains/nameservers`.

### Smartlead export via Zapmail
Zapmail has a native Smartlead export, use this instead of building a CSV manually. API: `POST /mailboxes/export` with `{ "platform": "smartlead" }`.

---

## SYSTEM 4. SMARTLEAD (campaigns and sending)

### Inbox configuration standards (from clients.yaml defaults)
- Inbox standard (Pablo, chat 2026-10-22, forever rule, approved wording): "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own."
- Daily send limit: Gmail exactly 25/day, Outlook exactly 6/day, SMTP exactly 35/day. An existing inbox above or below its number is reported to Pablo, never changed on my own. (The Oct 16 note to keep higher caps was a one-time exception, chat 2026-10-22.)
- Min time between emails: 20 min for every inbox type (Pablo, chat 2026-10-22, forever rule)
- Schedule: Mon-Fri, 8am-5pm Eastern
- Warmup in Smartlead: OFF on CSV import, then enabled separately in Smartlead after import

### Smartlead import CSV format
```
From Email, From Name, SMTP Host, SMTP Port, SMTP Username, SMTP Password,
IMAP Host, IMAP Port, IMAP Username, IMAP Password, Max Email Per Day,
Daily Ramp, Warmup Enabled
```
- SMTP/IMAP Host (MI): `main.outboxment.com`; SMTP Port 465, IMAP Port 993
- Username = the mailbox email; Password = mailbox password (retrievable from MI/Zapmail API)
- Max Email Per Day: exactly 25 for Gmail, 6 for Outlook, 35 for SMTP (chat 2026-10-22); Warmup Enabled: false

### Signature format

Signature templates are under review with Pablo (2026-10-22). Use the `set-inbox-signatures` skill for any signature write, not the templates in this file.

```
{full_name}
{job_title} - {client_display_name}

If this isn't relevant, just reply "No thanks"
```
Job titles come from `clients.yaml` per client. Apply name-matching rules where defined (e.g. Axero: "adam" in email = "Founder & CEO", else "Marketing").

### Inbox configuration API (confirmed endpoints)

```
# Update account details at setup (exact cap per the standard above, 20 min gap, signature).
# On existing inboxes, gaps not at 20 are report-only (chat 2026-10-22): omit time_to_wait_in_mins.
POST /email-accounts/{id}
Body: {"max_email_per_day": 25 (Gmail) | 6 (Outlook) | 35 (SMTP), "time_to_wait_in_mins": 20, "signature": "..."}
# On existing inboxes, caps above or below 25/6/35 are report-only (chat 2026-10-22): omit max_email_per_day.

# Enable warmup
POST /email-accounts/{id}/warmup
Body: {"warmup_enabled": true}

# List all tags (to find tag ID by name)
GET /email-accounts/tags

# Assign tag to inboxes (max 25 IDs per call)
POST /email-accounts/tag-mapping
Body: {"email_account_ids": [101, 102], "tag_ids": [465050]}
```

Confirmed: July 2026 batch of 575 new inboxes across 5 clients.

### Known Smartlead API quirks
- **Bulk assign bug**: assigning many inboxes to a campaign in one call can silently fail for some. Always verify assignment completed.
- **Warmup reputation field**: the `reputation_score` field documented in Smartlead's API does NOT exist in actual API responses. Use bounce rate and spam rate from campaign stats instead for rotation detection.
- **Pagination**: email accounts use `?offset=0&limit=100` with incrementing offset.

---

## FULL NEW CLIENT ONBOARDING WORKFLOW

Trigger: "New client: [Name], website: [url], contacts: [names]"

1. DYNADOT: generate 10 brand-adjacent domain candidates from the website URL; confirm names with Pablo before purchasing; check availability; register approved domains (1 year); point nameservers at MI (or Zapmail if specified).
2. MISSION INBOX (or ZAPMAIL): create project for the client; bulk create domains + push DNS + bulk verify; bulk create mailboxes (3 per domain, using contact names); wait 14 days (warmedDays >= 14 + health score >= 8.5).
3. SMARTLEAD: generate import CSV with SMTP/IMAP credentials; import inboxes; set daily limits, schedule, signatures per clients.yaml; assign to client; assign to campaigns when ready.
4. clients.yaml: add new client entry with all IDs populated; set inbox_providers, job_title rules, campaign filters.

Always confirm domain names and contact details before any purchases.

---

## INBOX ROTATION WORKFLOW (older version, see inbox-rotation-v2)

**Superseded.** Step 1 thresholds are replaced by Pablo's burned definition (chat 2026-10-13: warmup reputation under 90%, 0% excluded, AND 0 lifetime replies; skip `WARMING UP - DONT USE YET`, chat 2026-10-15). Step 2 (remove from campaigns) may run when the task calls for it and Pablo confirms; the Friday weekly sweep routine never detaches (chat 2026-10-22). Steps 3 and 4 need his explicit OK for each specific deletion (chat 2026-10-20). Kept for reference only.

### Step 1. Detect burned inboxes (Smartlead)
Flag if EITHER: Smartlead bounce rate > 20%, or Smartlead warmup reputation < 95%. Use bounce rate as primary signal. Cross-reference with MI health check score.

### Step 2. Remove from Smartlead campaigns
Remove inbox from all active campaigns. Do NOT delete from Smartlead yet, keep for reply capture.

### Step 3. Disable warmup in MI/Zapmail
Disable warmup but do NOT delete the mailbox yet. Log to `quarantine_log.csv`: `email, domain, client_id, removed_at, delete_after (removed_at + 14 days)`.

### Step 4. After 14 days: delete everywhere
When `delete_after <= today`: delete from Mission Inbox (`POST /api/mailboxes/bulk-delete`), from Zapmail (`PUT /mailboxes/remove`), and from Smartlead email accounts.

### Step 5. Replacement decision tree
- IF any single domain has ALL inboxes burned: DOMAIN BURNED. Buy replacement domains in Dynadot, full provisioning in MI/Zapmail, add to Smartlead after warmup.
- ELIF burned_count >= 10 (scattered): MANY INBOXES BURNED. Create new inboxes on existing domains, add to Smartlead after warmup. No Dynadot action.
- ELIF burned_count < 10: FEW INBOXES BURNED. Remove + quarantine + delete only. No replacement.

---

## ADD INBOXES TO EXISTING CLIENT WORKFLOW

Trigger: "Add [N] inboxes to [client name]"

1. Check if existing domains have capacity (< 5 inboxes per domain). If yes, create new mailboxes on existing domains. If no, buy new domains via Dynadot first, then provision.
2. Create mailboxes (bulk)
3. Wait 14 days
4. Import to Smartlead + assign to campaigns

---

## ENV VARS REQUIRED

`SMARTLEAD_API_KEY`, `MISSION_INBOX_API_KEY`, `ZAPMAIL_API_KEY`, `DYNADOT_API_KEY`, `HYPERTIDE_API_KEY` (legacy). Never hardcode values.

---

## SMARTLEAD CLIENT REFERENCE

`clients.yaml` is the source of truth for client IDs and job titles. Point-in-time reference (July 2026): Axero 178500, Mortarlink 131885, Arovy 321558. All others: look up live.

### Signature framework

Template (HTML): `{from_name}<br>{title} - {display_name}<br><br>If this isn't relevant, just reply "No thanks"`

- `from_name`: the inbox's `from_name` field from Smartlead
- `title`: the sender's job title for this client
- `display_name`: the client's brand name as used in outreach

Some clients have name-based title logic (e.g. Axero). This is always specified in `clients.yaml` or told explicitly by Pablo. Never invent title logic, ask if it's not documented.

---

## INBOX AUDIT & FIX WORKFLOW

"Audit inboxes for [client]" means: find every inbox that is misconfigured, fix signature and warmup, report caps and gaps to Pablo, and verify.

**Correctly configured = all three:**
- `minTimeToWaitInMins == 20` (always 20 for every inbox type, Pablo, chat 2026-10-22)
- `max_email_per_day` exactly: Gmail 25, Outlook 6, SMTP 35 (above or below is off-standard)
- `signature` is non-empty
- `warmup_details.status == "ACTIVE"`

**Caps (Pablo, chat 2026-10-22, forever rule, approved wording):** "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own." Report-only: list every inbox too high and every inbox too low separately for Pablo (per client and type, current values) and he decides. Change caps only when Pablo explicitly asks for that fix in this conversation; then set the exact value (25/6/35), canary one inbox first, then batch, then re-pull and report what changed. No delete still applies. The exact 25/6/35 standard applies to every client.

**Gap rule:** the gap between sends from one inbox is ALWAYS 20 min for every inbox type (Pablo, chat 2026-10-22, forever rule). There is no client-specific gap exception; flag any inbox not at 20 (e.g. 10, 13, 25, 60, 120) as non-compliant. Gaps not at 20 min are monitored and reported to Pablo only, never fixed automatically (Pablo, chat 2026-10-22).

**New-batch domains:** inboxes provisioned in the same session are already configured. Skip them during the fix (filter by domain against the new-batch tracking CSV, typically `/workspace/new_domains_YYYY-MM-DD.csv`). Ask Pablo if a new-batch CSV exists before assuming everything is old.

### Sequence (one client at a time)
1. Audit: pull all inboxes for client, flag failures, show grouped by domain
2. Confirm with Pablo (or proceed if direction is already clear)
3. Fix old inboxes: signature where missing, warmup where not ACTIVE (canary first). Caps not exactly 25/6/35 (too high or too low) and gaps not at 20 go in the report only; do not change them unless Pablo explicitly asks for that fix in this conversation (chat 2026-10-22)
4. Verify: re-pull all inboxes, confirm 0 signature and warmup failures remain; cap and gap issues stay listed in the report for Pablo
5. Move to next client only after verify passes

### Canonical audit + fix + verify script

```python
import requests, os, time
API_KEY = os.getenv("SMARTLEAD_API_KEY")
BASE = "https://server.smartlead.ai/api/v1"

def get_all_accounts(client_id):
    accounts, offset = [], 0
    while True:
        r = requests.get(f"{BASE}/email-accounts",
            params={"api_key": API_KEY, "client_id": client_id, "limit": 100, "offset": offset}, timeout=30)
        r.raise_for_status()
        page = r.json()
        if not page: break
        accounts.extend(page)
        if len(page) < 100: break
        offset += 100
        time.sleep(0.3)
    return accounts

def issues_for(a):
    issues = []
    if not a.get("signature"): issues.append("no signature")
    if (a.get("minTimeToWaitInMins") or 0) != 20: issues.append(f"gap={a.get('minTimeToWaitInMins')}")
    std = {"GMAIL": 25, "OUTLOOK": 6, "SMTP": 35}.get(a.get("type"))  # exact, not a minimum (chat 2026-10-22)
    cap = a.get("message_per_day") or 0
    if std and cap != std: issues.append(f"cap={cap} too {'high' if cap > std else 'low'} (want {std})")
    if (a.get("warmup_details") or {}).get("status") != "ACTIVE": issues.append("warmup not ACTIVE")
    return issues

# AUDIT
accounts = get_all_accounts(CLIENT_ID)
bad = []
for a in accounts:
    if a["from_email"].split("@")[1] in NEW_BATCH_DOMAINS: continue
    iss = issues_for(a)
    if iss: bad.append((a["from_email"], a["from_name"], a["id"], iss))

# FIX. Canary one inbox first and read it back. Caps are report-only (Pablo, chat 2026-10-22): leave PABLO_ASKED_CAP_FIX False unless Pablo explicitly asked for the cap fix in this conversation. If he asks, caps go to the exact standard (25/6/35), whether too high or too low.
PABLO_ASKED_CAP_FIX = False
for email, from_name, account_id, iss in bad:
    # Gap issues ("gap=") are report-only (Pablo, chat 2026-10-22): never send time_to_wait_in_mins here.
    if any("no signature" in i for i in iss):
        requests.post(f"{BASE}/email-accounts/{account_id}", params={"api_key": API_KEY},
            json={"signature": build_signature(from_name)}, timeout=30).raise_for_status()
    if PABLO_ASKED_CAP_FIX and any(i.startswith("cap=") for i in iss):
        std = int(next(i for i in iss if i.startswith("cap=")).split("want ")[1].rstrip(")"))
        requests.post(f"{BASE}/email-accounts/{account_id}", params={"api_key": API_KEY},
            json={"max_email_per_day": std}, timeout=30).raise_for_status()
    if any("warmup" in i for i in iss):
        requests.post(f"{BASE}/email-accounts/{account_id}/warmup", params={"api_key": API_KEY},
            json={"warmup_enabled": True}, timeout=30).raise_for_status()
    time.sleep(0.15)

# VERIFY
bad_after = [(a["from_email"], issues_for(a)) for a in get_all_accounts(CLIENT_ID) if issues_for(a)]
```

Run with `python3 -u` when running in background to avoid stdout buffering.

### Key account object field names

| What you want | Field name |
|---|---|
| Daily send limit | `message_per_day` |
| Gap between emails | `minTimeToWaitInMins` |
| SMTP connected | `is_smtp_success` (bool) |
| IMAP connected | `is_imap_success` (bool) |
| Warmup status | `warmup_details.status` ("ACTIVE" / "INACTIVE") |
| Warmup reputation | `warmup_details.warmup_reputation` (string: "100%") |

**Usable inbox** = `is_smtp_success AND is_imap_success AND float(warmup_reputation.strip('%')) > 90`

Daily send volume = sum of `message_per_day` over usable inboxes.

### Tag operations (tag name and ID vary per batch, always look up by name)

```python
r = requests.get(f"{BASE}/email-accounts/tags", params={"api_key": API_KEY}, timeout=30)
tag_id = next(t["id"] for t in r.json() if t["name"] == TAG_NAME)  # live field is name, TAG_NAME told by Pablo

def assign_tag_batch(account_ids, tag_id):
    for i in range(0, len(account_ids), 25):
        requests.post(f"{BASE}/email-accounts/tag-mapping", params={"api_key": API_KEY},
            json={"email_account_ids": account_ids[i:i+25], "tag_ids": [tag_id]}, timeout=30).raise_for_status()
        time.sleep(0.2)
```

Tags mark inbox groups (e.g. "Dont use until [date]" for new warmup batches). Never hardcode a tag ID.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22). The recipe above is Pablo's original text; this section only maps it to the tools available here.

- Smartlead: REST only (Pablo's 2026-09-28 rule). Base `https://server.smartlead.ai/api/v1`, auth `?api_key=$SMARTLEAD_API_KEY` (already in the box env; never print, log or save it). No Smartlead MCP on this box.
- Files: write CSVs and scratch output to `/workspace/`.
- Standing rules: never delete without Pablo's explicit authorization, the Friday weekly sweep routine never detaches (other tasks may detach when the task calls for it, chat 2026-10-22), canary first before any bulk write, verify every number by re-pulling, keep every counted client at 250 Gmail inboxes (Rocket and Maven excluded, Mortar Link undecided), no em dashes.

REST equivalents:
- `GET /client/` (verified 2026-10-22) for clients.
- `GET /email-accounts?limit=100&offset=N` (add `client_id=X`), paginate. Pull unfiltered to catch `client_id: null` orphans. Objects include passwords, never print them.
- `POST /email-accounts/{id}` with `max_email_per_day`, `time_to_wait_in_mins`, `signature`, `from_name`. Wrong patterns: `PUT /email-accounts/{id}`, `POST /email-accounts/{id}/update`.
- `GET /campaigns/{id}/email-accounts` (verified) is the live attached roster.
- `DELETE /campaigns/{id}/email-accounts` with `{"email_account_ids": [...]}`: write, only on Pablo's explicit go-ahead.
- `GET /email-accounts/tags` (verified): keys `id`, `name`, `color`. The original Claude snippet used `t["title"]`, which is wrong; it is `name`.
- `GET /campaigns/{id}/mailbox-statistics?limit=100&offset=0` (verified): `email_account_id`, `from_email`, `sent_count`, `reply_count`, `bounce_count`, `sender_bounce_count`.

Other notes:
- Zapmail: use the `user-Zapmail` connector. Read tools (`list_workspaces`, `list_domains`, `list_mailboxes`, `get_mailbox_details`, `check_dns_records`, `get_export_status`) are safe. Write tools (`provision_mailboxes`, `assign_mailboxes`, `export_mailboxes_to_third_party`, `schedule_mailbox_removal`) need Pablo's explicit go-ahead. Never schedule removals (weekly sweep rule). `schedule_mailbox_removal` by ID is untested.
- Mission Inbox is a valid, active provider again (Pablo, chat 2026-10-22): it went away and came back, and there are about 900 MI inboxes that are not assigned to campaigns yet. Include MI inboxes in pools, sweeps and audits like any other provider. MI API steps still need a `MISSION_INBOX_API_KEY` env var on the box (ask Pablo; never paste a key into chat or a skill).
- Mission Inbox and Dynadot API steps: no keys on the box, so those steps are not runnable yet. Ask Pablo to add keys as env vars (never pasted into chat or a skill).
- `clients.yaml`, `.env`, `quarantine_log.csv` and Jaimin's `dynadot-SKILL.md` were not in the export. Check live `GET /client/` for current IDs.
- Rotation thresholds: resolved. Pablo's burned definition (chat 2026-10-13) wins over the older rule here (bounce >20% / reputation <95%) and over v2 Rule 1: warmup reputation under 90% (0% means warmup off, excluded) AND 0 lifetime replies. Auto-replies and OOO count as replies (chat 2026-10-13). Low-rep inboxes with any reply stay. OOO and other auto-replies (for example no longer with the company, ticket acknowledgments) count as replies for burned and healthy, but not as human/positive replies in reply-rate scoring (Pablo, chat 2026-10-22). Skip inboxes tagged `WARMING UP - DONT USE YET` (chat 2026-10-15).
- Limits: resolved (Pablo, chat 2026-10-22, forever rule, approved wording): "Every Gmail inbox sends exactly 25 cold emails a day. Every Outlook sends exactly 6, and every SMTP inbox sends exactly 35. All of them have a 20-minute gap between sends. Any inbox set above or below its number gets reported to Pablo for review. Never change it on my own." Gmail exactly 25/day, Outlook exactly 6/day, SMTP exactly 35/day; above or below is reported, never changed on my own. The Oct 16 keep-higher-caps note was a one-time exception. Older Claude numbers (Outlook 5) are replaced above.
- 250 Gmail inboxes per client is the top goal (chat 2026-10-20). Rocket (Rocket Shipping) and Maven (Maven Analytics) are permanently excluded from the 250 count (Pablo, chat 2026-10-22). Mortar Link is undecided: do not count it either way on your own, ask Pablo each time it matters. Never take an action that drops a client below 250 Gmail inboxes without flagging it and getting Pablo's OK.
- Files to share with Pablo: CSV files, not images of tables (chat 2026-09-29).
