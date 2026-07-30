# The reference check

A story for gap register **G4 — subject ≠ owner** (`../STORIES.md`), the
one structural hole every other story can politely walk around: most of
the sensitive information in the world is *about* someone who does not
hold it. The gap register says "needs design; do not improvise." A story
is how you feel out the design without improvising code — this file
proposes the shape and names what it costs.

## Cast

Dana is hiring for a role where a bad hire is expensive. Miguel is the
candidate. Priya managed Miguel for three years; everything she knows
about him — the brilliance, the two shipped disasters, the way he behaves
in week nine of a slog — lives in **Priya's** chamber. It is Priya's
memory and Priya's data. It is *about* Miguel.

Today's world offers two bad options: the backchannel call (Miguel never
knows, never consents, cannot correct the record, and Priya says more
than she should because nothing is metered) or the sanitized written
reference (worthless by construction). The protocol should be able to do
better than both — and the current stack honestly cannot, because Miguel
has no account anywhere in the flow. That is G4.

## The flow that should exist

1. **Dana's ask is typed.** Not "tell me about Miguel" but a schema:
   collaboration pattern (fixed taxonomy), delivery reliability bucket,
   one strongest counter-signal, confidence. Capacity-capped like any
   emission — say 60 bits total.
2. **Priya's chamber treats Miguel-facts as a tagged sub-source.** Her
   world is hers, but facts whose subject is another named person carry a
   `subjectEntityId`. This is the new object: today's exposure account is
   keyed (source chamber, reader entity); a subject-tagged fact demands a
   THIRD index — information about Miguel, held by Priya, read by Dana.
3. **The subject gets a gate, not a veto-in-the-dark.** Before the
   emission, Miguel's chamber receives a consent request naming the
   *schema* and the *reader* — never the content (Priya's actual
   judgement stays hers; Miguel consenting to "a 60-bit reliability
   reference to Dana" must not itself leak Priya's opinion). Miguel can:
   consent; refuse; or attach a **response right** — his own 60-bit card
   released alongside, the protocol's answer to "the record should be
   correctable."
4. **The emission charges BOTH ledgers.** Dana reading the reference
   debits (Priya → Dana) — it is still Priya's world leaking — AND a
   **subject-indexed shadow account** (subject: Miguel → Dana). Miguel's
   shadow ceiling is how much of *himself-as-seen-by-others* he tolerates
   any one reader accumulating; it composes across referees. Ten
   backchannel references about Miguel from ten managers is exactly the
   accumulation attack the pair-lifetime account kills for sources —
   G4 is the same theorem with the subject as the conserved quantity.
5. **Settlement follows the story's economics.** Dana pays per reference
   (the work is Priya's; disbursement includes her). Miguel's consent is
   NOT purchasable by Dana through the protocol — a subject gate with a
   price tag is a coercion market. (Priya paying Miguel for release
   rights is a different, legitimate transaction — rights stack row 4.)

## What this demands of the kernel — and what it does not

The honest surprise: the kernel needs **no new arithmetic**. Charges,
ceilings, leases, audit codes, folds all work unchanged over a key that
happens to contain a subject id — the charge algebra is indexed by
arbitrary keys (Algebra.lean is generic in `S`). What G4 actually
demands:

- **A registration convention**, not a new event kind: subject-tagged
  keys `(subject:miguel, holder:priya_chamber, reader:dana)` registered
  with Miguel's declared ceilings. KERNEL-SPEC already folds any key.
- **The consent-request flow** — a new *protocol conversation* (like the
  release-screen), with the hard invariant: the consent request's own
  channel is metered (asking "may I send a reference about you to Dana"
  leaks that Dana is asking about Miguel — ~5 bits Miguel is happy to
  have, but they are charged, to (Dana → Miguel) of all accounts: the
  asker's identity is the asker's leak).
- **The response right** — mechanically just a second emission with the
  same schema and coupled release (both cards or neither; the
  MediationSession's atomic emission already knows how).

## The honest limits, said loudly

- Priya can still make the phone call. The protocol cannot stop
  out-of-band speech; it can only make the metered path *better for
  Priya* — indemnified, typed, paid — so the backchannel becomes the
  expensive, legally naked option. Adoption is the enforcement.
- Subject tagging is declared by the HOLDER. Priya deciding "this fact
  is about Miguel" is an owner judgement; an dishonest holder just
  doesn't tag. Audit can catch *inconsistent* tagging (the same fact
  tagged in one emission and not another — equivocation-shaped), never
  missing tags. L5, priced.
- Identity: "Miguel" across chambers is the same Sybil/linkage problem
  as readers (G3); the shadow account inherits its confidence class.

## Why this story matters for the timeless core

G4 is the first pressure that distinguishes "chamber = person" from
"chamber = *someone's window on* persons." The second is true. The
protocol's atoms were already (source, reader) *pairs* — this story says
the timeless key is a **triple** with an optional subject, and the pair
was the special case `subject = source`. If that's right, it should be
in KERNEL-SPEC as key discipline (a convention over the existing list
key — zero wire change) long before anyone builds consent flows: keys
are cheap now and migrations are not.
