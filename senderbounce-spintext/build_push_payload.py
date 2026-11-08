#!/usr/bin/env python3
"""
Build a safe `save_campaign_sequences` payload that changes ONLY Email 1's copy.

The GET shape from `get_campaign_sequences` differs from what
`save_campaign_sequences` expects, and that mismatch is exactly where a careless
push clobbers a live campaign. This script does the mapping deterministically:

    GET field            -> POST field
    sequence_variants    -> seq_variants
    delayInDays          -> seq_delay_details.delay_in_days
    (ids preserved so Smartlead UPDATES rows instead of creating new ones)

Everything except Email 1's targeted variant subject/body is copied through
untouched. Email 2 and Email 3 are never modified.

Usage:
    python build_push_payload.py original_sequences.json "spun subject" spun_body.txt
    python build_push_payload.py original.json "sub" body.txt --variant-label A
    python build_push_payload.py original.json "sub" body.txt --variant-id 7063640
    python build_push_payload.py --selftest

Output (stdout): {"campaign_id": <id>, "sequences": [...]} ready for save_campaign_sequences.
"""
import argparse
import json
import sys


def _delay(seq):
    d = seq.get("seq_delay_details") or {}
    val = d.get("delay_in_days", d.get("delayInDays"))
    return {"delay_in_days": int(val) if val is not None else 1}


def _map_variant(v, spun_subject=None, spun_body=None):
    out = {
        "id": v["id"],
        "subject": spun_subject if spun_subject is not None else v.get("subject", ""),
        "email_body": spun_body if spun_body is not None else v.get("email_body", ""),
        "variant_label": v.get("variant_label"),
        "is_deleted": bool(v.get("is_deleted", False)),
    }
    if v.get("variant_distribution_percentage") is not None:
        out["variant_distribution_percentage"] = v["variant_distribution_percentage"]
    return out


def build(sequences, spun_subject, spun_body, variant_label=None, variant_id=None):
    campaign_id = None
    out_seqs = []
    email1_touched = 0

    for seq in sequences:
        campaign_id = campaign_id or seq.get("email_campaign_id")
        row = {"seq_number": seq["seq_number"], "seq_delay_details": _delay(seq)}
        if seq.get("id") is not None:
            row["id"] = seq["id"]

        variants = seq.get("sequence_variants")
        if variants:  # variant-based step (Email 1 is one of these)
            is_email1 = seq.get("seq_number") == 1
            mapped = []
            # Which variant gets the spun copy: explicit target, else the only one.
            target_id = None
            if is_email1:
                live = [v for v in variants if not v.get("is_deleted")]
                if variant_id is not None:
                    target_id = variant_id
                elif variant_label is not None:
                    match = [v for v in live if v.get("variant_label") == variant_label]
                    if not match:
                        raise SystemExit(f"No live Email 1 variant with label {variant_label!r}")
                    target_id = match[0]["id"]
                elif len(live) == 1:
                    target_id = live[0]["id"]
                else:
                    labels = [v.get("variant_label") for v in live]
                    raise SystemExit(
                        f"Email 1 has {len(live)} live variants {labels}; "
                        f"pass --variant-label or --variant-id to choose one."
                    )
            for v in variants:
                if is_email1 and v["id"] == target_id:
                    mapped.append(_map_variant(v, spun_subject, spun_body))
                    email1_touched += 1
                else:
                    mapped.append(_map_variant(v))  # untouched
            row["seq_variants"] = mapped
        else:  # top-level content step (Email 2, Email 3): copy verbatim
            row["subject"] = seq.get("subject", "")
            row["email_body"] = seq.get("email_body", "")

        out_seqs.append(row)

    if email1_touched != 1:
        raise SystemExit(f"Expected to modify exactly 1 Email 1 variant, modified {email1_touched}.")
    return {"campaign_id": campaign_id, "sequences": out_seqs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("subject")
    ap.add_argument("body_file")
    ap.add_argument("--variant-label")
    ap.add_argument("--variant-id", type=int)
    args = ap.parse_args()

    sequences = json.loads(open(args.original, encoding="utf-8").read())
    spun_body = open(args.body_file, encoding="utf-8").read().strip()
    payload = build(sequences, args.subject, spun_body, args.variant_label, args.variant_id)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _selftest():
    seqs = [
        {"id": 1, "email_campaign_id": 999, "seq_number": 1,
         "seq_delay_details": {"delayInDays": 1, "delay_in_days": 1},
         "subject": "", "email_body": "",
         "sequence_variants": [
             {"id": 11, "is_deleted": False, "subject": "inspections",
              "email_body": "<div>old body</div>", "variant_label": "A",
              "variant_distribution_percentage": None}]},
        {"id": 2, "email_campaign_id": 999, "seq_number": 2,
         "seq_delay_details": {"delayInDays": 3, "delay_in_days": 3},
         "subject": "", "email_body": "<div>follow up two</div>", "sequence_variants": None},
    ]
    out = build(seqs, "{a|b|c}", "<div>NEW spun</div>")
    assert out["campaign_id"] == 999
    e1 = out["sequences"][0]
    assert e1["seq_variants"][0]["subject"] == "{a|b|c}"
    assert e1["seq_variants"][0]["email_body"] == "<div>NEW spun</div>"
    assert e1["seq_variants"][0]["id"] == 11  # id preserved
    assert e1["seq_delay_details"] == {"delay_in_days": 1}
    e2 = out["sequences"][1]
    assert e2["email_body"] == "<div>follow up two</div>"  # Email 2 untouched
    assert "seq_variants" not in e2
    # multi-variant Email 1 without a target should refuse
    seqs2 = json.loads(json.dumps(seqs))
    seqs2[0]["sequence_variants"].append(
        {"id": 12, "is_deleted": False, "subject": "x", "email_body": "y", "variant_label": "B"})
    try:
        build(seqs2, "s", "b")
        assert False, "should have refused ambiguous Email 1"
    except SystemExit:
        pass
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    else:
        main()
