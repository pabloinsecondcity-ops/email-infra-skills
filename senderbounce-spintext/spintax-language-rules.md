# Spintax language rules

The whole skill lives or dies here. Spintax multiplies whatever you write by every
combination, so a single sloppy option poisons a fraction of every send. Read this
in full before writing a single brace.

Two brace systems, never confuse them:
- **Spin group:** single braces, `{option one|option two|option three}`. Smartlead
  picks one at send time.
- **Merge field:** double braces, `{{first_name}}`, `{{City_WI}}`, `{{company_name}}`.
  Real data gets injected. **Never** put a spin group inside a merge field, and never
  spin a merge field's contents. Keep spin groups flat: no nesting, Smartlead handles
  nested braces inconsistently.

Preserve all HTML (`<div>`, `<br>`) and all merge fields exactly. Spin the text
between them, not the markup.

## Subjects: 20 whole-unit variations

The subject is spun as **one flat group of up to 20 complete subjects**, never
word by word. Combinatorial spinning of a 2-word subject produces junk, so
`{quick|fast} {note|question}` is banned. Write each of the 20 as a finished subject.

Every option must independently pass the PP subject rules:
- 1 to 3 words, lowercase, no punctuation.
- Reads like something a colleague typed in four seconds, not a campaign.
- Same angle as the email. All 20 orbit the same topic. If the email is about fleet
  inspections, every subject points at inspections / vehicles / damage / drivers.
  A prospect who opens "damage reports" and reads about scheduling software feels baited.

Draw from four buckets to reach variety without repeating yourself:
1. The topic noun, plain: `inspections`, `vehicle checks`, `walkarounds`
2. The pain in their words: `unreported dents`, `missed damage`, `stained seats`
3. The context or relationship: `from linkedin`, `your fleet`, `other limo companies`
4. The offer: `free trial`, `quick idea`, `possible fit`

Banned in every subject option: "quick question" (banned everywhere), any punctuation,
any capital letter, anything over 3 words, buzzwords, anything that reads like an ad.

**20 is a target, not a guillotine.** Fourteen great subjects beat twenty padded with
six that smell automated. If an option would look like a campaign wrote it, cut it.

## Body: 3 to 4 options per clause

"Every five words" is a density guide, not a mechanical rule. Taken literally it
shreds the voice. Translate it as **roughly one spin group per clause or sentence,
3 to 4 options each.** In a 100-word email that lands around 15 to 20 groups, dense
without spinning mid-fragment.

### Where to spin
- **Greeting:** `{Hi|Hey|Hello} {{first_name}}` — always.
- **Connective tissue:** transitions and verbs where wording varies but meaning does
  not: `wanted to {reach out|connect|send a note|drop you a line}`.
- **Framing verbs, not the observation:** `{We've been working with|We work with|We've
  helped} a few {{niche}} teams` — the fact stays fixed, the framing verb spins.
- **Truly neutral synonyms:** one or two, only where the swap changes nothing:
  `{log|capture|record} it all from their phone`.
- **CTA, within one tier:** `{Lmk if you want more details.|Happy to send more details
  if useful.|Want me to send more details?}` — do not mix a yes/no ask with an
  open-ended one in the same group; they are different asks with different friction.
- **Sign-off:** `{Thanks,|thanks|Cheers,|Best,}` — the lowercase option is intentional,
  it reads human.

### Where NEVER to spin (hard exclusion list)
- **Merge fields and `{{AI:}}` prompts.** Spinning inside them breaks the injection.
- **Numbers and proof points.** `3-5 days`, `15,000 communities`, named customers.
  `{3-5|4-6|about 5}` days is fabrication, not variation. These are the email's credibility.
- **The core problem statement.** Lines like `unreported dents, stained seats, or messy
  interiors` are winning language pulled from the ICP's world. Synonym-spinning it
  ("blemishes, soiled upholstery") launders out exactly what made it land.
- **Signature and fourth-wall lines.** `It worked until it didn't.` and `Appreciate you
  probably get a lot of emails like this` are load-bearing. If you spin a fourth-wall
  line at all, every option must be equally honest and specific, never one specific
  option against a generic "I know you're busy".
- **P.S. lines.** Spin lightly or not at all. The P.S. is the most human moment; three
  interchangeable versions usually means two are filler.
- **Email 2 and Email 3.** Out of scope for this skill entirely.

## The grammar-integrity rule (this is the one that catches everyone)

Every option in a group must be a drop-in replacement: same part of speech, same
tense, agreeing with the words before and after the braces.

Bad: `we {work with|helped|are working} a few teams` renders "we helped a few teams
near {{city}} and wanted to reach out" (tense clash with the next clause).

Enforce it: read the sentence out loud once with each option substituted in. If any
render is even slightly off, fix the option or move the brace boundary. Put boundaries
at natural phrase edges, never mid-idiom: spin `{drop you a line|send a note}`, never
`drop you a {line|note}`.

## The voice-consistency rule

Every option in a group carries the same register. `{Lmk|Let me know|Please advise}`
fails because "Please advise" is a different human. Casual email, every option casual.
If an option would fail the founder-note test on its own, it fails inside the braces too.

## QA workflow (before showing or pushing anything)

1. Render 3 to 5 random full combinations and read each as the prospect. Every render
   must independently pass the founder-note test (does it sound like one real person
   wrote it to one real person).
2. Run `scripts/validate_spintax.py` on the spun email. It catches em dashes, "quick
   question", broken or nested braces, spin groups inside merge fields, subject-rule
   breaks, and the word ceiling. Fix every FAIL and re-run until clean.
3. Word count: check the longest render, not the shortest. Options of different lengths
   can push a 118-word email over the ceiling in some combinations (the validator's
   word check already uses the longest render).
