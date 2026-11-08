#!/usr/bin/env python3
"""
Validate a spintax email before it is shown or pushed.

Spintax multiplies every mistake by the number of combinations, so the cheap
deterministic checks belong in a script, not in a human's eyes. This does NOT
judge whether the spin reads well (that is the human's job on a few renders); it
catches the mechanical failures that would otherwise ship silently.

Spin syntax:   {option one|option two|option three}    (single braces)
Merge fields:  {{first_name}}, {{City_WI}}             (double braces, never spun)

Input: a text file. If a line starts with "Subject:" it is checked under the
subject rules. Everything else is treated as the body (HTML is fine).

Hard failures (exit 1):
  - em dash anywhere
  - banned phrase "quick question"
  - unbalanced or nested single braces
  - a spin group sitting inside a {{merge field}}

Warnings (exit 0, but reported):
  - a subject option that bends the subject guidelines (over 3 words, capitals,
    punctuation) — these are guidelines with room for exceptions, not hard laws
  - marketing buzzwords (imagine, unlock, transform, no strings attached)
  - longest possible render over the word ceiling (default 120)

Usage:
    python validate_spintax.py email.txt
    python validate_spintax.py email.txt --max-words 120
    python validate_spintax.py --selftest
"""
import argparse
import re
import sys

BANNED = ["quick question"]
BUZZWORDS = ["imagine", "unlock", "transform", "no strings attached"]
MERGE_RE = re.compile(r"\{\{.*?\}\}", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def protect_merge(text):
    """Replace {{...}} with a brace-free sentinel so single-brace parsing is clean."""
    fields = []

    def repl(m):
        fields.append(m.group(0))
        return f"\x00{len(fields)-1}\x00"

    return MERGE_RE.sub(repl, text), fields


def brace_errors(protected):
    """Return a list of structural brace errors on merge-protected text."""
    errs = []
    depth = 0
    for i, ch in enumerate(protected):
        if ch == "{":
            depth += 1
            if depth > 1:
                errs.append(f"nested '{{' at position {i}")
        elif ch == "}":
            depth -= 1
            if depth < 0:
                errs.append(f"unmatched '}}' at position {i}")
                depth = 0
    if depth > 0:
        errs.append(f"{depth} unclosed '{{'")
    return errs


def find_groups(protected):
    """All spin groups {a|b|c} on merge-protected text (assumes braces already validated)."""
    return re.findall(r"\{([^{}]*)\}", protected)


def spin_in_merge(text):
    """True if any {{ }} field contains a '|' (a spin group leaked inside a merge field)."""
    return any("|" in m for m in MERGE_RE.findall(text))


def max_render(protected, fields):
    """Render choosing the LONGEST option in every group — an upper bound for word count."""
    def repl(m):
        opts = m.group(1).split("|")
        return max(opts, key=len)

    out = re.sub(r"\{([^{}]*)\}", repl, protected)
    for i, f in enumerate(fields):
        out = out.replace(f"\x00{i}\x00", f)
    return out


def visible_words(text):
    text = TAG_RE.sub(" ", text)
    text = MERGE_RE.sub("name", text)  # a merge field renders to ~one word
    text = re.sub(r"&[a-z]+;", " ", text)
    return [w for w in re.split(r"\s+", text) if w.strip()]


SUBJECT_PUNCT = re.compile(r"[.!?,;:\"'()\[\]/\\—–-]")


def check_subject(group_body):
    """group_body is the inside of the subject spin group: 'a|b|c'. Returns list of errors."""
    errs = []
    for opt in group_body.split("|"):
        o = opt.strip()
        if not o:
            errs.append("empty subject option")
            continue
        if o != o.lower():
            errs.append(f"subject not lowercase: '{o}'")
        if SUBJECT_PUNCT.search(o):
            errs.append(f"subject has punctuation: '{o}'")
        if len(o.split()) > 3:
            errs.append(f"subject over 3 words: '{o}'")
    return errs


def validate(text, max_words=120):
    hard, warn = [], []

    if "—" in text:  # em dash
        hard.append("em dash present")
    low = text.lower()
    for b in BANNED:
        if b in low:
            hard.append(f"banned phrase: '{b}'")
    for b in BUZZWORDS:
        if re.search(rf"\b{re.escape(b)}\b", low):
            warn.append(f"buzzword: '{b}'")

    if spin_in_merge(text):
        hard.append("a spin group is inside a {{merge field}}")

    protected, fields = protect_merge(text)
    berrs = brace_errors(protected)
    hard.extend(berrs)

    # Subject line rules
    for line in text.splitlines():
        if line.strip().lower().startswith("subject:"):
            sp, _ = protect_merge(line.split(":", 1)[1])
            groups = find_groups(sp) if not berrs else []
            if groups:
                for g in groups:
                    warn.extend(check_subject(g))  # subject style = guideline, not a blocker
            else:
                # a plain (unspun) subject is allowed; only flag if it breaks basic rules
                pass

    # Word ceiling on the longest possible render
    if not berrs:
        longest = max_render(protected, fields)
        wc = len(visible_words(longest))
        if wc > max_words:
            warn.append(f"longest render is {wc} words (ceiling {max_words})")

    return hard, warn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--max-words", type=int, default=120)
    args = ap.parse_args()
    text = open(args.file, encoding="utf-8").read()
    hard, warn = validate(text, args.max_words)

    for w in warn:
        print(f"WARN  {w}")
    for h in hard:
        print(f"FAIL  {h}")
    if not hard and not warn:
        print("OK  no issues")
    elif not hard:
        print("OK  (warnings only)")
    sys.exit(1 if hard else 0)


def _selftest():
    good = (
        "Subject: {inspections|vehicle checks|walkarounds}\n"
        "<div>{Hi|Hey|Hello} {{first_name}}, we {work with|help} a few {{City_WI}} teams.</div>"
    )
    hard, warn = validate(good)
    assert not hard, hard

    assert validate("<div>a — b</div>")[0], "em dash not caught"
    assert validate("Subject: quick question")[0], "banned phrase not caught"
    assert validate("<div>{a|{b|c}}</div>")[0], "nested brace not caught"
    assert validate("<div>{a|b</div>")[0], "unbalanced brace not caught"
    assert validate("<div>{{first|name}}</div>")[0], "spin-in-merge not caught"
    assert validate("Subject: {Big News!|quick note}")[1], "subject punctuation/case not warned"
    long_body = "<div>" + ("{word one|word two|word three} " * 70) + "</div>"
    assert any("longest render" in w for w in validate(long_body)[1]), "word ceiling not warned"
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    else:
        main()
