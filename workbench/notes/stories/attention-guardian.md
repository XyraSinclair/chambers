# The guardian at the bell

Full ledger depth for STORIES.md Story 7: the attention-protecting
agent. The party story priced a ring; this story asks who OWNS the bell,
who decides what deserves it, what "the wrong framing is disruptive"
costs in the meter, and how a third-party agent operating over someone's
most private data — their attention patterns — stays *their* agent in a
way a stranger can verify from the fold.

The design goal, in the operator's words: people should end up
**retroactively appreciating** what was called to their attention. That
sentence becomes a settlement condition below.

## Cast

Noor is a surgeon: deep-work blocks, on-call windows, a drowning inbox.
Her **guardian** is a third-party agent that is the ISSUER of every
attention account keyed to her — `("att", noor, <sender>, <epoch>)` —
running under her declared policy, leased deep read access to her
private context (calendar, current case load, what she ignores, what
she opens twice). Senders: colleagues, the story-1 matchmaker, a
journal-alert bot, a recruiter.

## The bell has three channels, and framing is capacity

The guardian sells three delivery channels at different unit prices:
`interrupt_now` (10,000 micro-interrupts), `daily_digest` (1,000),
`weekly_roundup` (100). But the deeper move is that **framing features
are metered capacity**: urgency markers, red banners, alarm verbs,
"URGENT:" prefixes are enum dimensions of the notification schema, and
they cost. A sender who wants adrenaline pays for adrenaline. The
disruption premium is not a vibe — it is the estimator charging for the
features that produce disruption.

The guardian then RE-frames: the admitted content is rewritten into
Noor's shape (the calm digest line, the two-sentence version, delivery
at her break). That rewrite is in-chamber cognitive work over her
private context — *what framing works for Noor is itself private data*
(`SelfFree`: the rewrite costs nothing because it never leaves her
world). Senders never learn which framing survived.

## Timing is a channel too

When Noor is interruptible is private. A sender observing instant-bounce
vs 4-hour-delay learns her state — so delivery receipts are batched to a
padded cadence (G15's topology discipline applied to attention), and a
refusal is byte-constant with a deferral. The bell does not echo.

## Retroactive appreciation as settlement

Every admitted ring carries an escrow: base attention price + the
framing premium. At epoch close, Noor one-taps each: **glad / neutral /
noise**. That tap is an `OutcomeAttestation` (G1) in its most honest
form — the attester is the receiver herself, the observable is her own
recorded judgement, and the counterfactual ("would she have found it
anyway") is refused as unoperationalizable, per doctrine.

The split teaches everyone:

- **glad** → most of the premium returns to the sender; the guardian
  takes its fee; the sender's future price to reach Noor drifts DOWN.
  Being right about her attention is cheap.
- **neutral** → base price stands, premium returns. No signal, no
  punishment.
- **noise** → the premium forfeits to NOOR (the disruption was hers) at
  a declared multiple, and the sender's future price rises. The
  guardian's admission policy just learned at the sender's expense.

The asymmetry is deliberate: the system chills toward quiet. Retroactive
appreciation is simultaneously the settlement condition, the sender's
price discovery, and the guardian's training signal — pay-after-value
for attention, with the value judged by the only party entitled to
judge it.

## Whose agent is it? — fiduciary duty as fold arithmetic

The adtech failure mode is structural: the gatekeeper quietly paid by
the senders. Here the constitution is checkable from the settlement
fold: **the guardian's income may flow only from Noor's side** — her
subscription, its fee share of glad-splits and forfeits. Every fee is a
ledgered flow; a guardian drawing sender-side revenue shows up in public
arithmetic, and "does this guardian's income correlate with admitted
volume?" is a QUERY over the fold, not an investigative journalism
project (G9, extended from fee legibility to *fiduciary legibility*).
Whose agent is it — asked of the ledger, answered by the ledger.

## The ideal reader is a black hole

The guardian reads enormously and emits almost nothing: a deep
observation budget on `("exp", noor, guardian_vendor)` — the lifetime
"how much of me can this vendor ever see" number — against a tiny,
priced emission aperture. Its model of Noor is a bounded latent
(LICENSING.md rights 1–2: execution + silo-local annotation, never
export); switching vendors is G7's export workflow — the accounts and
their cumulative history survive the divorce, the latent does not.

## Honest limits, loud

- **Appreciation is manipulable** — mood, hindsight, a manipulative
  sender crafting glad-bait. The tap is an attestation, not a truth;
  its power is that it prices future access, not that it is right.
- **Chilling is a chosen bias.** Noise-forfeit under-delivers borderline
  rings. A guardian policy can price "miss-critical" asymmetrically
  (on-call channels with inverted penalties), but the default leans
  quiet, on purpose.
- **The guardian sees everything.** Its exposure account makes the
  intimacy legible; nothing makes it small. This is the highest-trust
  vendor relationship in the stack, and the fold's fiduciary
  legibility is the reason it can exist at all.

## Gaps this story feeds

- G1: retroactive appreciation = receiver-attested outcome events; the
  cleanest OutcomeAttestation instance yet (single attester, owns the
  experience, not the payee).
- G6: attention accounts get their missing half — the guardian as
  ISSUER with policy, not just the receiver as beneficiary.
- G9 → **fiduciary legibility**: fee flows as the answer to "whose
  agent is it"; wants the ledgered `fee_schedule` primitive.
- G12: the guardian's model of Noor is preference formation running
  continuously; the doctrine (richness stays inside) is what keeps it
  survivable.
