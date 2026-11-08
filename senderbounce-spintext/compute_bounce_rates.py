#!/usr/bin/env python3
"""
Compute campaign-level SENDER bounce rate the exact way the Command Center
deliverability dashboard does, then rank the culprits.

Verified against the live dashboard 2026-08-26 (Whip Around - FMCSA: 675 sender
bounces / 90,443 sent = 0.7%).

Formula (do not change without re-verifying against the dashboard):
    sender_bounce_rate = round(sender_bounces / sent_count * 1000) / 10   # percent, 1 decimal

Culprit = sender_bounce_rate > 5.0 AND sent_count >= 500.

Input: a JSON file (or stdin) that is a list of rows:
    [{"campaign_id": 3496770, "name": "Whip Around - FMCSA", "client": "Whip Around",
      "sent_count": 90443, "bounce_count": 2500, "sender_bounces": 675}]

`sender_bounces` may be null/missing for a campaign whose sender data could not be
fetched. Those are reported separately as "unavailable", never as 0%.

Usage:
    python compute_bounce_rates.py rows.json
    python compute_bounce_rates.py rows.json --threshold 5 --floor 500 --json
"""
import argparse
import json
import sys


def sender_rate(sender_bounces, sent_count):
    """The dashboard's rounding: 1 decimal place, via *1000/10."""
    if not sent_count:
        return 0.0
    return round(sender_bounces / sent_count * 1000) / 10


def classify(rows, threshold, floor):
    culprits, clean, unavailable = [], [], []
    for r in rows:
        sent = int(r.get("sent_count") or 0)
        sb = r.get("sender_bounces", None)
        if sb is None:
            unavailable.append(r)
            continue
        rate = sender_rate(int(sb), sent)
        r = {**r, "sender_bounce_rate": rate}
        if sent < floor:
            clean.append(r)  # below the volume floor, never a culprit
        elif rate > threshold:
            culprits.append(r)
        else:
            clean.append(r)
    culprits.sort(key=lambda x: x["sender_bounce_rate"], reverse=True)
    return culprits, clean, unavailable


def fmt_table(culprits):
    if not culprits:
        return "No campaigns over the sender-bounce line."
    w_client = max(6, max(len(str(c.get("client", ""))) for c in culprits))
    w_name = max(8, max(len(str(c.get("name", ""))) for c in culprits))
    head = f"{'CLIENT':<{w_client}}  {'CAMPAIGN':<{w_name}}  {'SENT':>8}  {'SENDER':>7}  {'RATE':>6}"
    lines = [head, "-" * len(head)]
    for c in culprits:
        lines.append(
            f"{str(c.get('client','')):<{w_client}}  {str(c.get('name','')):<{w_name}}  "
            f"{int(c.get('sent_count') or 0):>8}  {int(c.get('sender_bounces') or 0):>7}  "
            f"{c['sender_bounce_rate']:>5}%"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rows", nargs="?", help="JSON file of rows; omit to read stdin")
    ap.add_argument("--threshold", type=float, default=5.0, help="sender bounce %% cutoff (default 5.0)")
    ap.add_argument("--floor", type=int, default=500, help="minimum lifetime sends to qualify (default 500)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    raw = open(args.rows, encoding="utf-8").read() if args.rows else sys.stdin.read()
    rows = json.loads(raw)
    if not isinstance(rows, list):
        print("Input must be a JSON list of rows.", file=sys.stderr)
        sys.exit(2)

    culprits, clean, unavailable = classify(rows, args.threshold, args.floor)

    if args.json:
        print(json.dumps({"culprits": culprits, "clean_count": len(clean),
                          "unavailable": unavailable}, indent=2))
        return

    print(f"Scanned {len(rows)} campaigns. "
          f"{len(culprits)} over {args.threshold}% sender bounce (>= {args.floor} sends).\n")
    print(fmt_table(culprits))
    if unavailable:
        print(f"\nSender data unavailable for {len(unavailable)} campaign(s) "
              f"(MCP returned nothing after retry): "
              + ", ".join(str(u.get("name") or u.get("campaign_id")) for u in unavailable))


def _selftest():
    # Whip Around - FMCSA, the dashboard-verified case.
    assert sender_rate(675, 90443) == 0.7, sender_rate(675, 90443)
    assert sender_rate(0, 1000) == 0.0
    rows = [
        {"campaign_id": 1, "name": "hot", "client": "A", "sent_count": 1000, "sender_bounces": 80},   # 8.0%
        {"campaign_id": 2, "name": "fine", "client": "A", "sent_count": 90443, "sender_bounces": 675}, # 0.7%
        {"campaign_id": 3, "name": "tiny", "client": "B", "sent_count": 100, "sender_bounces": 20},    # 20% but under floor
        {"campaign_id": 4, "name": "nodata", "client": "B", "sent_count": 5000, "sender_bounces": None},
    ]
    culprits, clean, unavailable = classify(rows, 5.0, 500)
    assert [c["campaign_id"] for c in culprits] == [1], culprits
    assert len(unavailable) == 1 and unavailable[0]["campaign_id"] == 4
    assert any(c["campaign_id"] == 3 for c in clean)  # tiny excluded by floor, not a culprit
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    else:
        main()
