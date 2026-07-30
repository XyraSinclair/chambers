# Generative private-data moats — the frontier

*Lead synthesis, 2026-07-06. Three fable-subagent lenses ran in
parallel against the whole stack — economics (`lens-economics.md`),
type-theory (`lens-types.md`), adversary (`lens-adversary.md`),
preserved verbatim beside this file. This document adjudicates them: what
they independently converged on (the signal), where they disagree (the
tension worth holding), and the buildable deltas, as a register in the
house style — every row a passing test, a proof, or a named gap.*

## The question, sharpened

In a future where software capability is commodity (AI writes all code),
the durable competitive substrate is **private data that compounds**:
owner-private structure that grows in value with every unit of paid work
performed against it, while everything that crosses out is typed,
metered, and bounded. Call it a **generative private-data moat**. Does
this stack support them, which shapes survive contact, and what does the
protocol still owe?

## The convergence (three independent lenses, one conclusion)

All three lenses, from unrelated starting points, landed on the same
five findings. Convergence under decorrelated generators is the strongest
evidence this project produces, so these are stated as the load-bearing
results:

1. **The exposure ledger is a distillation budget, not a moat.** The
   `(source × reader)` lifetime ceiling is an information-theoretic cap
   on what one reader can clone (adversary's DPI framing; economics'
   `P·h ≥ V` inequality; types' "cap is grade subsumption, a corollary
   of the global cap theorem"). It bounds cloning **per identity** — and
   is therefore *exactly as strong as identity*, which is unsolved (L5).

2. **Moats must be flow-shaped, never stock-shaped.** A static corpus is
   UNPRICEABLE against substitution (adversary (b)) and has a negative
   real interest rate as public knowledge catches up (economics'
   G13-applies-to-moats; "a melting ice cube with a meter on the door").
   Only a live flow of *outcome-labeled reality* or *structurally
   unpublishable* results has a positive real rate.

3. **Provenance is the only substitution-proof asset — and closure-
   charging is the one missing law.** A competitor's synthetic
   equivalent cannot forge the bonded `outcome_attestation` history
   (adversary (b); economics C2/C3 defensibility). But the type lens
   found the sharp edge: **the moat's compounding mechanism and the
   moat-laundering attack are the same operation** — derive, re-derive,
   project from the derivative. Until the provenance closure is *charged*
   (G14 as law, not orchestrator discipline), depth is dilution: every
   internal hop washes a source out of the charge set, so the deeper and
   more valuable the moat, the cheaper its leaks. This is the single
   highest-value protocol delta the exercise found, and all three lenses
   point at it.

4. **The seductive codebook moat is the ecosystem's, not the owner's.**
   "The meter is the training loss of the ecosystem's codebook" is the
   repo's most moat-shaped sentence; economics *kills it* (schemas that
   clear cheap are visible by construction — the compression discoveries
   are commons by design) and the adversary shows the E4 catalog *cuts
   against* moats (standardized receipts are fungible receipts;
   whoever controls catalog admission captures the ecosystem). **Design
   consequence, now binding on E4: the schema catalog and attestor sets
   must be permissionless and forkable at genesis**, or the moat you
   build accrues to the platform.

5. **"Moat" is a pattern, not a primitive.** The type lens ran it
   through CANON.md's five-test gate and it fails every test as a
   record: it names a *non*-crossing, is coextensive with the chamber
   interior, and its one honest external number is *computed from the
   fold*, not stored. It earns a named composition law and refuses a
   `MoatValue` field, a `hasMoat` boolean, and an `Accumulation`
   operator — each of which would launder a conjunction or a market
   estimate into a success-shaped type.

## The moat pattern (adopted)

> **Moat(C)** := grow-only interior (M1) × charged-coupled boundary (M2)
> × lifetime (source × reader) residuals (M3) × provenance-closure
> charging (M4) × covenant-capped exit (M5). A chamber satisfying the
> conjunction compounds structurally and cannot leak past budget except
> through the named non-claims.

Structural status: **M1, M2, M3, M5 are carried or proven; M4 is the
open law.** Four-fifths of the moat is what the stack already built for
other reasons — the pattern arrived from a direction the design was
never tested against and held, which is itself evidence the primitives
are right.

**Split the two halves and never confuse them** (the type lens's cut):
"the moat compounds" = a *structural* half (the interior grows, remembers
its sources, ratchets its budget down — theorem-shaped, mostly proven)
and an *economic* half (the interior is worth more — an estimated-lane
market fact the type system may only refuse to lie about). Any design
that types moat *value* as load-bearing has re-imported the ε-halo the
whole stack exists to refuse.

## The moat register — M-invariants (structural)

| # | invariant | status | the gap |
|---|-----------|--------|---------|
| M1 | Accumulation is lattice inflation (interior grows; deletion = tombstone, never retraction) | CARRIED (court: grow-only CRDT + X0; artifact: salted-commitment tombstones) | `retentionOutlivesTheDerivationsItFeeds` — one law + one check (closure ⊆ retained-or-tombstoned); today retention protects *claims*, not *ancestry* |
| M2 | Projection is the only exterior functor, charged-coupled all-or-none | CARRIED at kernel (`charge_coupled`); PARTIAL at canon (premier-cut Tier 0 leaks) | read-charge for *derived* structure must key to closure capacity, not byte size — meets M4 |
| M3 | Residual monotonicity, lifetime (source × reader); the remainder is a computable sentence | THEOREM PROVEN (Lean global cap); SENTENCE missing | compile `MoatResidualStatement` from the fold — pure arithmetic today, no receipt schema carries it; must carry the G13 depreciation vintage |
| M4 | Provenance closure: derived facts remember sources; emissions charge the transitive ancestry at the DPI bound | **LAW SHIPPED 2026-07-06** (`charge-provenance/1`, KERNEL-SPEC Part III: derivation events + P1/P2/P3, integer max-flow DPI bound, value fails closed) | residue: undeclared emissions invisible to P1/P2 (declared-channel convention; G8's trust class); tombstone hook awaits G18 |
| M5 | Exit caps authority, never rewrites history — windable-down without being erasable | CARRIED (`charge-covenant/1` + S8 + tombstones) | portability (export → re-attach, cumulative intact) is G7's unexercised residue; a moat that can't move houses is a hostage and gets discounted |

## The anti-moat attack table (which shapes die)

Verdicts in the §11.1 discipline: PREVENTED / PRICED / RECORDED /
UNPRICEABLE. Full reasoning in `lens-adversary.md`.

| attack | verdict | the honest mechanism-or-gap |
|--------|---------|------------------------------|
| Distillation, high-D moat | PRICED | ceiling caps cloneable bits; the lifetime account renders a campaign as one monotone number (d1_bounty's VEX shape) |
| Distillation, **low-D decision boundary** | **UNPRICEABLE** | `C < D/ε` fails; the moat sells its own extraction, one receipt at a time. G2 cuts toward the attacker. **Do not build a moat whose value is "the label."** |
| Sybil / coalition pooling | PRICED (weak) → UNPRICEABLE undeclared | ceiling resets per identity; **only the per-mbit price survives Sybil, not the ceiling.** Budget against the *pooled* adversary until proof-of-uniqueness (frontier #3) exists |
| Substitution (synthesize an equivalent, touch nothing) | UNPRICEABLE for static corpora; PREVENTED-adjacent for attested-outcome flows | the stack has no verb for a zero-query attacker; only unfakeable provenance defeats it |
| Insider / operator plaintext | UNPRICEABLE at R1, integrity-only at R2, PREVENTED only at R3 (unbuilt) | the runtime ladder *labels the rung each moat needs*; a stranger-data moat at R1 is mislabeled, not defended |
| Estimator undercount (G8) | PRICED weakly → UNPRICEABLE if subtle | the meter's soundness IS the moat's soundness, and it trusts a declared estimator; F7/F8 are the unbuilt escapes |
| Topology / metadata (G15) | RECORDED | existence, size, cadence leak through head cardinality and session shape; a moat must price its own metadata or leak its thesis free |
| Staleness / decay (G13) | PRICED, never PREVENTED | the meter charges marginal-over-public entropy, so decay is *visible*; the discipline tells you the moat is rotting, it does not stop the rot |
| Subject ≠ owner (G4) | UNPRICEABLE — and a **liability**, not a gap | third-party facts have no account and no erasure verb; a reputational moat is a compliance bomb with no landing pad |
| Forced disclosure | UNPRICEABLE by construction | no metering survives a subpoena; the stack's own transparency can aid discovery |
| Codebook / attestor-root capture (E4, L5) | UNPRICEABLE unless forkable | "no unauditable discretion" is owed, not shipped; permissionless+forkable catalog is the only defense |

## The portfolio — build these three (economics lens, adjudicated)

Ranked compounding × defensibility × time-to-value; every one satisfies
the master requirement (flow-shaped, outcome-anchored):

1. **Match-outcome graph** — highest time-to-value: every mechanism
   shipped this week (attention-node/1 + charge-settlement/2); the only
   residue is a sim wiring (E1). Edges are outcome-labeled reality; AI
   matchmaking is commodity, *ground truth about which private pairings
   worked* is purchasable only here. Demands: E1-residue wiring, the
   operator-is-a-subject gap (G4 applies to the moat-holder), G15.
2. **Judge calibration archive** — highest compounding rate: value grows
   in two denominators (judges × schemas) and the stack is *uniquely*
   able to bind judgement receipts to later outcome attestations under a
   machine-checked court. Demands: E4 (the key axis), cardinal adoption
   #1 (G10 coherence receipts), a calibration-ledger record kind.
3. **Negative-knowledge archive** = the already-decided D1 PSIRT wedge:
   structurally unpublishable, expensive to regenerate, outcome-labeled
   by pay-on-repro (the reproduction verdict IS a ChargeEvent — a
   mechanical oracle). Concentrated-value regime, so it leans on G5
   partitioning + ordinal review, not the meter alone. Demands: G13
   closure (honest depreciation), the searched-and-empty typed crossing
   with a bonded coverage claim, R2.

Relationship capital (C1) is the *substrate* all three ride on — it
accrues automatically. Underwriting folds (C8) have the best 10-year and
worst 1-year shape (blocked behind F14/G11); they become buildable
*because* the first three generate the folds. All three share one
exhaust pipe — topology — so **G15 is the single common infrastructure
investment**, and one common clock — **G13 must ship before any moat is
marketed as durable.**

## New gaps this exercise adds to the register

Proposed for STORIES.md's G-register and MACHINES.md's E-register on the
next kernel-lane pass (L1 owns the specs):

- **G16 — provenance-closure charging (M4).** The `derivation` event
  kind + P1/P2/P3 audit family; charges the transitive ancestry at the
  DPI bound; makes "not separable from its ancestry" convictable from
  bytes. Supersedes G14's "ledger-computable but not law" status. **The
  headline buildable — depth becomes safe compounding instead of a
  laundering channel.** X0 covers its fact identity for free.
- **G17 — the moat residual statement (M3).** Compile
  `MoatResidualStatement` from the fold (a stranger recomputes it);
  mandatory caveat codes (bits-not-harm, reader-identity-claimed,
  denominator-depreciates); carries the G13 vintage. Not a primitive — a
  projection of the fold.
- **G18 — ancestry retention (M1).** `retentionOutlivesTheDerivationsItFeeds`:
  an artifact in any live provenance closure is tombstonable but not
  droppable. One law, one check.
- **E4 amendment (binding).** The schema catalog and attestor sets ship
  **permissionless and forkable** — the codebook-capture defense (finding
  4) is a genesis requirement, not a retrofit.
- **G4 escalation.** Subject-vs-owner is re-classed from "unmodeled gap"
  to "compliance liability" for any moat over third-party facts: subject-
  indexed shadow accounts or consent-at-ingest, do not improvise.

## The one-sentence verdict

The stack defends a moat that is **a flow of attested outcomes over a
high-complexity function, run at R3, padded against metadata, on a real-
identity substrate, over consenting subjects, against a forkable
codebook.** It cannot defend a static corpus, a low-D decision function,
a stock of third-party facts, or anything whose value lives outside the
metered channel. Four-fifths of the machinery exists; the missing fifth
is provenance-closure charging (G16), without which the compounding move
and the laundering move are the same move. Build the flow, charge the
ancestry, sell the receipts, and price the identity gap you cannot close.
