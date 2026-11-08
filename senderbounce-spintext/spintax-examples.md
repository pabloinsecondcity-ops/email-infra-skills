# Spintax examples

A real PP Email 1 spun the right way, and one over-spun failure annotated. The
examples teach density and boundaries faster than the rules alone. Study both.

## Good: Whip Around limo campaign, Email 1

This is a real winning email (variant A of an active limo/chauffeur campaign). The
spin varies the connective tissue and framing while leaving the winning problem
statement, the merge fields, and the proof detail untouched.

### Before

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

### After (spun)

Subject (one flat group of 20 whole-unit options):

```
{inspections|vehicle checks|walkarounds|unreported dents|stained seats|damage logs|between jobs|your fleet|limo interiors|from linkedin|other limo companies|driver checkins|catch it early|photo logs|the next guest|messy interiors|free trial|quick idea|possible fit|vehicle damage}
```

Body (HTML preserved, merge fields and the problem statement untouched):

```html
<div>{Hi|Hey|Hello} {{first_name}}, {we work with|we've been working with|we've helped} a few other limo/chauffeur companies in {{City_WI}}, so I {wanted to connect|figured I'd reach out|thought I'd drop you a note}. Most {relied on texts|used texts|tracked things by text} to catch issues between jobs and stuff {got missed|slipped through|fell off}: unreported dents, stained seats, or messy interiors.<br><br></div><div>Whip Around {helps|lets} drivers {log|capture|record} it all from their phone with time-stamped photos, so you {know|can see} exactly when something happened and who caught it. {No more surprises|Nothing slips} when the next guest gets in.<br><br></div><div>{Would it be a bad idea to try it out for free?|Any interest in trying it out for free?|Open to trying it out for free?}</div><br><div>{Thanks,|thanks|Cheers,|Best,}</div><br>
```

Why this works:
- The subject group is 20 finished subjects, all orbiting the same email (inspections,
  damage, limo interiors, the offer). Each is 1 to 3 words, lowercase, no punctuation.
- The problem statement `unreported dents, stained seats, or messy interiors` is left
  completely alone. That is the winning ICP language; spinning it would launder out
  what made it land.
- `{{first_name}}` and `{{City_WI}}` are untouched. `time-stamped photos` (a proof
  detail) is untouched.
- Every CTA option is the same soft-ask tier. No yes/no ask mixed with an open-ended one.
- Each body group is a clean drop-in: read the sentence with any option and it still
  parses. Boundaries sit at phrase edges, never mid-idiom.

## Bad: the same email over-spun

Every group below breaks a rule. This is what to never do.

```html
Subject: {Inspections!|quick question|boost your fleet uptime}

<div>{Hi|Hey|yo} {{first|name}}, we {work with|helped|are working} a few limo teams — so I wanted to connect. Most had issues with {unreported dents|small dents|minor blemishes}, {stained seats|dirty seats|soiled upholstery}, or messy interiors.<br></div><div>Drivers {log|capture} it in {3-5|about 4} seconds. {Want to try it free?|Happy to hop on a call and walk you through the whole platform whenever suits you.}</div>
```

What is wrong, group by group:
- **Subject** `{Inspections!|quick question|boost your fleet uptime}`: capital letter and
  punctuation ("Inspections!"), the banned phrase "quick question", and an ad-like
  option over 3 words. All three fail the subject rules.
- **`{Hi|Hey|yo}`**: "yo" is a different register from "Hi/Hey". Voice-consistency fail.
- **`{{first|name}}`**: a spin group jammed inside a merge field. This breaks the merge
  entirely; the field will not resolve.
- **`we {work with|helped|are working} ... so I wanted to connect`**: tense clash.
  "we are working a few limo teams so I wanted to connect" does not parse.
- **em dash** after "teams": banned everywhere.
- **`{unreported dents|small dents|minor blemishes}, {stained seats|dirty seats|soiled
  upholstery}`**: spinning the core problem statement. "minor blemishes" and "soiled
  upholstery" are nobody's real words; the winning language is gone.
- **`{3-5|about 4} seconds`**: spinning a number. That is fabrication, not variation.
- **CTA** `{Want to try it free?|Happy to hop on a call and walk you through the whole
  platform whenever suits you.}`: two different asks in one group. A one-tap yes/no next
  to a book-a-call. Different friction, different asks; never in the same group.
