# The party matchmaker

The deep-dive companion to `../STORIES.md` Story 1 ("The party"): the same
scenario worked to full ledger depth — every beat binds to a real object,
every number is a ledger line, and everything the protocol cannot do is
said out loud. This file stresses the two mechanisms the other wedges
don't: **attention pricing** (gap register G6) and **outcome-contingent
settlement** (G1).

## Cast

Alice runs a matchmaking agent at a party. Bob and Charlie are guests who
each, at some point, uploaded a lot of themselves into a personal chamber —
work history, enthusiasms, half-formed beliefs, things they'd say at 2am.
Bob marked some facts **never-reveal**. Neither has written down most of
their preferences, because nobody has; personalities are high-dimensional
and beliefs are circumstantial. Nobody hands Alice their data. That is the
point.

## Act 1 — What Alice's agent is actually allowed to do

Alice's agent never receives Bob's data. It receives **execution rights**
(LICENSING.md right 1): a lease to run bounded cognitive work *inside*
Bob's chamber, with annotations staying silo-local (right 2). Concretely:

- Bob's chamber registers exposure keys with declared entropy and
  ceilings. His never-reveal facts live under keys with **ceiling 0** —
  the accountant's step D refuses any charge against them, mechanically,
  before any review gets a vote. A never-reveal fact is not a policy; it
  is an account with no budget.
- "General-purpose over a multidimensional personality" is exactly the
  typed-channel tension: the kernel can only meter **typed** emissions
  (schema-bound capacity), and a personality is unbounded prose. The
  stack's answer: the full latent stays **escrowed**
  (`latentCustody: "escrowed_full_latent"`, coalition.ts) and only typed
  projections cross. Alice's agent thinks in prose *inside* the chamber;
  what leaves is a match card.
- Unknown preferences are elicited, not assumed: the agent asks Bob typed
  questions over time ("would you rather argue about type systems or
  urbanism?"). Every ANSWER is an emission charged to (Bob → mediator);
  every REFUSAL to answer is also an emission (absence is a channel,
  1 bit, metered — chamber.py (private) already does this for status). Circumstantial
  beliefs stay **tuple-scoped judgements**: valid in the context that
  generated them, any wider use is a WideningEvent.

## Act 2 — The match is a coalitional derivative

The agent, holding leases into both chambers, forms the hypothesis:
*Bob × Charlie, about speculative fiction as urban-planning critique,
strength: strong.* This artifact's provenance names two silos, so it is a
`CoalitionalDerivative` — **born confined to the generating coalition**
{Bob's chamber, Charlie's chamber, Alice's mediator}, audience =
generating coalition, by construction (proven one-way: `Widening.lean`,
`audience_provenance`). Neither Bob nor Charlie has seen it yet. It is a
fact about both of them that currently belongs to no one's attention.

## Act 3 — 50 cents to raise it to Bob's attention

Here the economics invert. The kernel meters information **out of**
silos; a notification prices information **into** attention. Both happen
in the same act:

- The match card shown to Bob is an `IntraCoalitionProjection` — and its
  `crossLeakageIds` are the story's spine: showing Bob *"someone here
  matches you on X"* leaks bits **about Charlie** to Bob. The card is
  schema-bound — topic facet (one of 64: 6 bits), strength bucket
  (2 bits), a fixed-taxonomy why-safe line (5 bits), no name, no face —
  call it **13 bits**, charged as 13,000 mbits against the
  (Charlie → Bob) exposure account. Charlie's ceiling for
  strangers-at-this-party might be 100 bits lifetime. The meter, not
  Alice's taste, decides how many cards Bob may ever see about Charlie.
- The **50¢** is settlement, not information: Alice (fronting for
  Charlie's side of the match) deposits 50¢, escrowed against exactly the
  charge events of that card emission (charge-settlement/1: the release
  references the charge event ids; if the emission was refused or the
  court is dirty, the payment cannot release — S-code conviction). Bob's
  attention has a price floor he sets himself: 50¢ is what it costs to
  ring his bell, and the payment *provably paid for that ring and nothing
  else*. Value moved iff metered work moved.
- Bob ignoring the card is also information (Charlie's side learns
  nothing — the card's non-answer stays inside Bob's chamber; only a
  padded-cadence "no action" crosses, per `ActivityCoverPolicy`:
  non-matching must not be cheaply observable).

## Act 4 — $5 if it actually worked

The proposition Bob and Charlie each accepted at upload: *pay after
value.* If they end up talking more than 15 minutes about the matched
facet, each owes $5 — to Alice's agent and, through the disbursement
pool, back to the data that made the match possible.

The honest mechanics, and exactly where honesty runs out:

- At card-accept time, each party's $5 goes into **escrow** with a
  timeout refund. No outcome, full refund, automatically.
- The **counterfactual clause is REFUSED, not priced.** "Talked *because
  of* the card" is unoperationalizable; a protocol that accepts it is
  selling oracle theater. The contract prices the OBSERVABLE: "talked
  ≥15 min about the matched facet." (Gap register G1's posture; this file
  originally proposed pricing the counterfactual and lost the argument.)
- The observable releases via an **OutcomeAttestation** (G1): an attested
  outcome event mirroring estimator attestation — declared attester set,
  independence class, timeout default. HERE the natural attester set is
  the two people the outcome happened to, co-signing: independence class
  `jointly_self_interested`, the weakest class that is still honest,
  declared as such on the receipt. Equivocation (signing conflicting
  outcomes) is convicted like any equivocating fact.
- Collusion-to-deny (talk 3 hours, sign nothing, keep $10) is theft of
  realized value that no cryptography here prevents — an L5 standing
  non-claim, mitigated by the same forces that make people tip. The $5 is
  calibrated as a small fraction of realized surplus so the lie stays
  cheaper than the reputation.
- What the settlement layer DOES prove: the $5 releases only against the
  court file of the match that caused it (S-code audit: absent, refused,
  or off-key charge events convict the release), conservation holds
  (`Settlement.lean` — every microcredit in exactly one place), and a
  stranger can re-audit the whole causal chain from deposit to
  disbursement.

## Act 5 — The part the protocol refuses to touch

The moment Bob walks over to Charlie, the widening has happened — two
human heads are now an unmetered channel, forever (the human-head channel,
ASSURANCE L5). The protocol's whole job was BEFORE that moment: making
sure the walk-over was worth 13 bits of Charlie, 50 cents of Alice, and
nothing else. Confinement is one-way (`confinement_not_reestablishable`);
"Bob changes his mind" going forward means his ceilings drop to 0 for new
work — it cannot mean un-telling Charlie. The protocol is honest about
being a door, not an eraser.

## The invariant this story adds to the canon

> **Attention is priced in credits; exposure is priced in bits; a
> notification spends both at once, and the settlement must reference the
> exact charge events of the emission it paid for.**

The 50¢ and the 13 bits are not two systems glued together — the escrow
release is *keyed to the charge event ids*, which the settlement layer
already supports. The matchmaker is charge-settlement/1's first
consumer-shaped story, and it needs exactly one primitive the stack does
not yet have: **OutcomeAttestation** (gap register G1) — an attested
outcome event with a declared attester set (here: the parties themselves,
co-signing), independence class, and timeout default, usable as a release
condition alongside work receipts. Everything else in this story already
exists. Attention accounts (G6) upgrade the 50¢ from "a price Alice pays"
to "an account Bob owns" — recipient-as-fee-beneficiary — and are the
second-ripest build.

## Ledger sketch (one match, end to end)

| # | event | layer | account / amount |
| - | ----- | ----- | ---------------- |
| 1 | register Bob's keys (never-reveal: ceiling 0) | charge | (Bob → \*) |
| 2 | lease to Alice's agent, TTL = party + 1h | charge | issuer: Bob's chamber |
| 3 | elicitation answers, typed | charge | (Bob → mediator), ~2–20 bits each |
| 4 | derivative formed, audience = coalition | — | zero-cost (self-leakage is free) |
| 5 | deposit 50¢ | settlement | Alice available → escrow |
| 6 | match card → Bob | charge | (Charlie → Bob), 13,000 mbits |
| 7 | release 50¢ against event #6's id | settlement | escrow → Bob's attention account |
| 8 | $5 + $5 escrow at card-accept | settlement | timeout-refunded |
| 9 | OutcomeAttestation, co-signed | settlement | **the missing primitive (G1)** |
| 10 | release + pool disbursement | settlement | conservation checked |

A stranger re-audits rows 1–10 from one jsonl artifact. Rows 4 and 9 are
where the deep math lives: row 4 is the coalition zero-point
(`SelfFree`, Algebra.lean), row 9 is the next thing to build.

**Rows 5–7 are now EXECUTABLE**: `chambers/kernel/demo_attention_notify.py`
runs Act 3 for real — attention as the kernel's second key family
(`("att", receiver, sender, epoch)`, temporal physics in the key, zero
kernel changes), 5 rings paid to the bell's owner at 50¢ each with each
release bound to that ring's charge event id, the 6th ring refused
*before anything about Charlie leaked* (the receiver's spam ceiling
protects the third party), a fresh epoch regenerating the budget, and
the artifact conserved, stranger-verifiable, and tamper-convicting.
Standing tests: `kernel/test_attention_notify.py`.
