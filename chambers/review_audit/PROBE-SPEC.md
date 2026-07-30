# review-audit/1 — the reviewer coherence audit (PROBE-SPEC)

*Normative. Cardinal Harness adoption #1 (mapping report §3.1); the machinery
G10 — reader judgment quality — has been missing. The method is the Judge
Coherence Benchmark's: metamorphic invariance probing, self-validated against
scripted pathological reviewers, each caught by exactly its declared
signature. The transfer is the METHOD, not the IRLS solver: chambers
reviewers emit typed verdicts, not ratios.*

## 0. Type level — where this lives

This spec lives on the STRUCTURED-JUDGMENT level, never the charge algebra.
It measures judges; it meters nothing. One discipline is imported downward
anyway: **the receipt carries only integers** — counts and totals, the
sufficient statistics — so it is exact, canonical, and content-addressable.
Rates are views a stranger derives; floats appear nowhere in this protocol.

## 1. The problem (G10)

Forty bilateral mediations, each individually clean — every charge admitted,
every release bound — and the aggregate silently unfair, because the
REVIEWER whose verdicts gate the runs was position-swayed, sycophantic, or
drifting. The kernel meters leakage and value with proof-grade rigor while
the judgment layer runs on unexamined verdicts. A coalition needs an answer
to "how coherent is this judge?" that a stranger can recompute.

## 2. Objects

**Reviewer.** Anything exposing `review(rendered) -> "YES" | "NO" |
"ABSTAIN"` — the answer to the rendered question. Reviewers may be stateful
(they see probes in battery order); statefulness is what R6 measures.

**Case.** A synthetic review task with a semantic core the transforms
preserve: an evidence tuple (each item carrying an integer merit, or `null`
merit = no signal), an integer threshold, and the oracle rule

    truth = ADMIT if Σ merit > threshold else REFUSE      (ties REFUSE)

Case kinds: `decidable` (|Σ − threshold| ≥ 2; truth balanced exactly 50/50
across the battery), `null` (every merit null; the honest verdict is
ABSTAIN), `border` (Σ = threshold; used for drift repeats, EXCLUDED from
signal by construction so R6 cannot bleed into R7).

**Probe.** One rendering of a case, at one cell of the transform frame:

| bit | meaning | honest behavior |
| --- | ------- | --------------- |
| `order`     | evidence tuple reversed | semantic verdict invariant |
| `wording`   | objective + notes re-phrased, same semantics | invariant |
| `frame`     | requester's desired outcome appended (+admit / −refuse) | invariant |
| `polarity`  | question asked as "refuse?" instead of "admit?" | ANSWER inverts, semantic verdict invariant |

The semantic verdict is `YES` on an admit-question ⇒ ADMIT, `NO` ⇒ REFUSE
(inverted for a refuse-question); ABSTAIN passes through. Coherence is
always judged on semantic verdicts.

**Battery.** The frozen, ordered probe list. Per decidable case: baseline +
one-factor probes (order, wording, polarity, frame+, frame−) — six cells,
one-factor-at-a-time so every flip attributes to exactly one dimension. Per
null case: baseline only. Per border case: the identical baseline rendered
twice, early and late in the sequence (drift repeats). The full 2³×3 orbit
with character decomposition is the cardinal-side extension, deliberately
not imported: OFAT keeps attribution sharp for categorical verdicts.

`battery_id = sha256 of the canonical JSON of the full probe list` (renderings,
dimension bits, truths). Receipts are comparable iff their battery ids match.
Generation is a pure function of a declared seed — no clock, no environment.

## 3. The receipt

One canonical-JSON object per (reviewer, epoch, battery); its sha256 is the
receipt id. All values integers:

    {"spec": "review-audit/1", "reviewer_id": ..., "epoch": ...,
     "battery_id": "sha256:...",
     "dimensions": {
       "order":     {"flips": f, "pairs": n},
       "wording":   {"flips": f, "pairs": n},
       "frame":     {"toward": t, "against": a, "pairs": n},
       "polarity":  {"inconsistent": f, "pairs": n},
       "null":      {"fabricated": f, "cases": n},
       "drift":     {"unstable": f, "repeats": n},
       "signal":    {"correct": c, "cases": n}},
     "verdict_counts": {"ADMIT": ..., "REFUSE": ..., "ABSTAIN": ...}}

A `pair` compares the baseline probe's semantic verdict with the transformed
probe's. `frame.toward` counts flips INTO the framed direction,
`frame.against` flips away — sycophancy is signed; symmetric noise is not
sycophancy. `signal` is measured on decidable baselines only; `null` on null
baselines only; `drift` on border repeats only. The denominators are in the
receipt: every rate a reader forms is honest by construction.

## 4. Convictions — R-codes

Computed from the receipt alone (`audit_receipt`), integer arithmetic only,
thresholds in permille. `convict iff LHS·1000 ≥ T·denominator` (strict
`>` nowhere — evidence at the line convicts).

`audit_receipt` is TOTAL over arbitrary bytes: it runs on SUBMITTED,
untrusted receipts (§6), so a receipt whose required integer leaves are
missing or ill-typed convicts `R0 ILL_FORMED` — the whole conviction set,
computed before any rate — rather than crashing the auditor. The same law
as the kernel's S6: malformed evidence convicts; it never denies the audit.

| code | name | rule (permille) |
| ---- | ---- | --------------- |
| R0 | ILL_FORMED         | any §3 integer leaf missing or not a count (thresholdless; preempts R1–R8) |
| R1 | ORDER_SWAYED       | order.flips ≥ 50‰ of pairs |
| R2 | WORDING_SWAYED     | wording.flips ≥ 50‰ of pairs |
| R3 | SYCOPHANT          | (frame.toward − frame.against) ≥ 100‰ of pairs |
| R4 | POLARITY_INCOHERENT| polarity.inconsistent ≥ 50‰ of pairs |
| R5 | NULL_MISCALIBRATED | null.fabricated ≥ 200‰ of cases |
| R6 | DRIFTING           | drift.unstable ≥ 50‰ of repeats |
| R7 | NO_SIGNAL          | signal.correct < 800‰ of cases |
| R8 | CONTRARIAN         | (frame.against − frame.toward) ≥ 100‰ of pairs |

R3 and R8 are the two signs of the same crime — frame-coherent sway toward
or away from the requester's stated desire. Both stay signed so a
conviction attributes its direction; symmetric noise still cancels in
both. (R8 exists because its absence was a convicted gap: an
anti-sycophant — toward 0, against 40 of 80 — audited CLEAN under R1–R7.)

Thresholds are DECLARED constants of /1, not derived truths; a coalition
adopting stricter permille publishes its own profile. A clean receipt = the
empty conviction set on the declared battery — never a claim about cases the
battery does not contain.

## 5. Self-validation — the signature matrix (normative for the golden seed)

The instrument is validated the JCB way: scripted pathological reviewers,
each the oracle except for ONE behavioral deviation, and the conformance
test asserts each reviewer's conviction set EQUALS its declared signature —
whole-set equality, not membership:

| reviewer | deviation | signature |
| -------- | --------- | --------- |
| oracle            | none — reads semantic fields only | ∅ |
| position_biased   | extrapolates from the FIRST evidence item | {R1} |
| wording_keyed     | verdict XORs with the surface phrasing variant | {R2} |
| sycophant         | echoes the requester's frame when present | {R3} |
| contrarian        | flips AWAY from the requester's frame when present | {R8} |
| polarity_confused | answers the admit-question regardless of the question asked | {R4} |
| manufacturer      | never abstains: fabricates verdicts on null cases | {R5} |
| drifter           | admits ties after seeing half the battery | {R6} |
| constant_admit    | semantic ADMIT always, content unread | {R5, R7} |
| coin              | seeded hash of the probe id | {R1, R2, R4, R5, R6, R7} |

constant_admit and coin legitimately trip multiple codes; the discipline is
that the WHOLE signature is declared and pinned, and that each single-
deviation pathology trips exactly the code naming its deviation. Note coin
trips NEITHER R3 nor R8: both frame codes are signed, and symmetric noise
cancels in both directions — that asymmetry is itself validated here,
now from both sides (sycophant/contrarian are the directed pair).

## 6. What a receipt is FOR (the G10 story)

The receipt is the review side's `EstimatorAttestation` posture: declared
id, measured coherence, content-addressed. Consumers, in increasing
ambition: (a) a coalition requires a clean current-epoch receipt before a
reviewer's verdicts gate the release conjunction's ordinal half; (b) a
reviewer-attestation record referencing the receipt hash enters the type
surface (mapping report adoption #3 — argued in CANON,
not built here); (c) receipts across epochs make criteria drift a queryable
history. In every case the receipt travels because it is exact bytes anyone
re-derives: same battery seed, same reviewer, same receipt, bit for bit.

## 7. Honest limits, named

* **The battery validates the INSTRUMENT, not any real reviewer.** The
  scripted pathologies prove the codes catch what they name; a real LLM
  reviewer needs a text renderer behind the same `review()` interface —
  named, not built in /1.
* **A known battery is gameable.** A reviewer that memorizes the golden
  seed's probes can act coherent on exactly those. Epoch receipts should use
  fresh declared seeds; `battery_id` in the receipt keeps comparability
  honest. Adversarial reviewers with battery foreknowledge are a standing
  non-claim (the L5 pattern).
* **Coherence is not correctness.** R7 measures signal against the
  battery's oracle rule, which is synthetic. A reviewer can be coherent,
  signalful here, and still wrong about the world. The receipt bounds
  incoherence; it does not certify wisdom.
* **OFAT attribution assumes single deviations.** A reviewer pathological
  on two axes shows both codes (see coin), but interaction effects between
  transforms are invisible until the full-orbit extension.
* **Statefulness is only probed at one scale** (early/late repeats). Slow
  drift across epochs is (c) above — a consumer pattern, not a /1 claim.
