# Operations, graded — what can actually run, at what comfort

> Source-column citations marked "(private)" refer to the operator's
> withheld artifacts — see the Private artifacts note in `../README.md`
> and `IP-MANIFEST.md` at the repo root.

## 1. Purpose

The corpus has two layers and a hole between them. Below: the calculus
(`primitives/CALCULUS.md`) — four crossing combinators, eight composition
laws, the cut bound. Above: the stories (`stories/`, `STORIES.md`) — nine
narratives that show the algebra touching people. What is missing is the
middle layer this document supplies: a graded classification of the
**operations** — the ~80 distinct things an AI can do inside a
privacy-bounded chamber, each located on a small set of axes, each with a
comfort tier that is *derived* from those coordinates rather than asserted.
The grounding case throughout is frontier-lab IP mediation
(`stories/frontier-lab-ip-mediation.md`, `frontier/ip-trades/README.md`).

Reading discipline: `primitives/STRUCTURE.md` governs. The primary grade of
any operation is its disclosure context — audience × purpose × alphabet —
and the alphabet is the object; the bit number is its logarithm. Nothing
below is a leakage claim in bits; every row is a claim about *structure*:
what kind of sentence the operation can ever say, to whom, backed by what,
closing how, running where, repeatable at what accounted cost. Status tags
follow the corpus inventory: **IMPL** = running code under `chambers/`,
**SPEC** = normative spec or canon record, **NAMED** = ideated or
gap-registered only. Where an operation is IMPL in simulation but SPEC for
real deployment, the row says so and the tier reflects the real-deployment
reading.

## 2. The six spine axes

The corpus already classifies along ~27 dimensions. Six of them carry the
grading; the rest are demoted to refinements (table below). The spine:

1. **Alphabet class** — `closed` (small closed alphabet; capacity =
   log₂|alphabet|, derived, failure codes enumerated — theorem-grade),
   `schema` (typed fields and enums; capacity derived from the schema
   product), `declared` (open content under a declared estimate — probes,
   capped prose, reveals; the meter bounds the *ledger*, not the adversary),
   `unbounded` (no ceiling stated; not admissible as a charged channel).
   This is charge legibility. `primitives/CALCULUS.md` §2;
   `primitives/STRUCTURE.md` §4.
2. **Silo structure** — `self` (single silo; owner's own world),
   `2T` (exact 2-tuple, joint silo), `kT` (k-coalition),
   `3C` (third-chamber-escrowed: work carried into an enclave neither party
   reads), `3R` (third reader with its own exposure accounts, e.g. a
   regulator). Tuple identity is judgement identity. `primitives/mediation.ts`.
3. **Epistemic lane** — `prov` / `trust` / `est` / `unprov`: what backs the
   operation's claim — established by crypto/attestation/proof, resting on a
   named root that degrades loudly, a declared estimate that prices but
   never gates, or honestly unprovable. `primitives/iptrade.ts`;
   `frontier/ip-trades/valuation-and-research.md`. *Drift, reported not
   resolved:* `primitives/CANON.md` IPTRADE_LAWS still reads as the
   three-partition without `estimated`, and the derived/declared distinction
   (CALCULUS_LAWS) is a separate grading of charge channels that nothing yet
   maps onto the verdict lanes. This document adopts the four-lane form; the
   reconciliation is owed in §6.
4. **Contingency closure** — `in-ch` (the contingent outcome IS an
   in-chamber ChargeEvent; escrow releases against its exact ids, no
   oracle), `ext` (bonded, independence-classed outcome attestation —
   charge-settlement/2, S9/S10), `refused` (counterfactual metrics — no lane
   can express one), `—` (no contingent leg). `stories/gardener.md`;
   `ASSURANCE.md` L2.
5. **Runtime rung required** — R1 / R2 / R3 (`RUNTIME.md`): the lowest
   execution rung at which the row's claim is honest for its listed silo
   structure. Ledger arithmetic that a stranger re-audits from the court
   file is rung-indifferent (`any`).
6. **Extraction posture** — `1shot` (a single crossing; repetition has no
   meaning), `meter` (repeatable by design; lifetime (source × reader)
   accounted, refusals accrue demand), `campgn` (the operation *is* a
   distillation channel; only the lifetime account and the incident latch
   stand between use and extraction). `primitives/coalition.ts`;
   `stories/frontier-lab-ip-mediation.md`, the meter under adversarial
   pressure.

The disclosure context itself is not demoted — it governs. Axis 1 is its
alphabet leg, axis 2 its audience leg; the purpose leg lives in the signed
program-level consent and scopes every row.

Every other axis in the corpus refines one of the six:

| Corpus axis | Refines |
|---|---|
| BCR seven-tuple (`primitives/STRUCTURE.md` §2) | the traded object the coordinates describe; its review/recourse legs refine lane and closure |
| derived vs declared capacity (CALCULUS_LAWS) | alphabet class (closed/schema vs declared) |
| trust root class (`frontier/ip-trades/README.md` §3.1) | epistemic lane (what `trust` names) |
| assurance ladder L0–L5 (`ASSURANCE.md`) | epistemic lane (what `prov` is backed by) |
| counterparty structure (`primitives/mediation.ts`) | silo structure (same axis, canonical form) |
| rights stack rows 1–6 (`LICENSING.md`) | extraction posture (which crossings may repeat, under what grant) |
| pitch posture: codebook vs odometer (`primitives/STRUCTURE.md` §6) | alphabet class, restated as register |
| value-density regime (`frontier/private-data-moats/lens-economics.md` §1.3) | extraction posture (whether the meter's bound is honest) |
| attack verdict PREVENTED/PRICED/RECORDED/UNPRICEABLE | closure + extraction (what the substrate does under abuse) |
| moat invariants M1–M5 (`frontier/private-data-moats/lens-types.md`) | extraction posture (the lifetime-accounting laws behind `meter`) |
| account key families (kernel PROTOCOL) | extraction posture (the ledger keys implementing it) |
| declassification 4-cube (`research/mediation-literature.md` Vein 2) | alphabet (what), silo (who), alphabet's schedule proviso (when), rung (where) |
| reversibility / one-way widening | silo structure (audience transitions never narrow) |
| valuation type (priceless/barter/monetary/attribution) | contingency closure (what the settlement leg may reference) |
| carrier class (`pure_recipe` pins reuse to `unprov`) | epistemic lane |
| atomicity regime (operator/TEE/hashlock/optimistic) | contingency closure (how the swap closes) |
| estimate provenance (corpus_relative vs buyer_conditioned) | extraction posture (whose budget debits) |
| independence class (attester/estimator) | contingency closure (who may attest the external outcome) |
| oracle mechanicalness (in-chamber vs attested vs refused) | this IS axis 4's source (`stories/gardener.md`) |
| ObservableClass × precision × cadence atlas (`private: autoresearch/2026-06-29-orthogonal-type-systems/01-orthogonal-type-atlas.md` §6) | alphabet class — the concrete enumeration checklist the calculus proviso needs; currently ignored by CALCULUS/STRUCTURE (§6) |
| gain-function class (`FRAMEWORKS.md` F1) | alphabet class (design-time input: the alphabet is designed against a declared gain function) |
| schedule discipline (fixed/bucketed/padded) | alphabet class (timing is a channel the ceiling never sees) |
| deal-intimacy ladder (`stories/frontier-lab-ip-mediation.md`) | not an axis: a path through the spine, alphabet widening and silo deepening per step |
| sensitivity / data class | deliberately refines nothing — the spine grades channels, not harm (`primitives/STRUCTURE.md` §1, harm-blindness); sensitivity is an admission-review input |
| market buildability (typed channel × cheap gate × locked-out demand) | not an axis: a derived composite over tier + demand |

## 3. Comfort tiers — derived, not declared

The derivation rule: **a tier is read off an operation's spine coordinates
plus its build status; it is never assigned by hand.**

**Tier A — comfortable now.** Coordinates: alphabet `closed`, lane
`prov`/`trust`, closure `in-ch` or none, rung ≤ R2, extraction `meter` or
`1shot`. Status IMPL — everything in A is running code whose court file a
stranger can re-audit today. A SPEC/NAMED row whose coordinates are A-grade
is not A; it is **B(build)** — A-shaped, waiting only on the build.

**Tier B — buildable, with priced caveats.** Coordinates miss A on an axis
whose price is named: a `schema` or `declared` alphabet (the meter bounds
the ledger, not the adversary — say so out loud, MARKETS.md L1); an `est`
lane (price input, never a payoff cliff); an `ext` closure (bonded social
roots, priced not proven); or gated on exactly one named unbuilt piece —
the **R3 runner** (attestation-gated key release, `RUNTIME.md`), **G15
entropy-pool batching**, the **TEE first-wedge**
(`frontier/ip-trades/README.md` §5), the **two-silo chamber run mode**
(`primitives/CALCULUS.md` §8 item 3), or the **cross-question adaptive
budget** for the live chamber. SPEC-heavy by nature. The tier tag names its
reason: B(schema), B(declared), B(est), B(ext), B(R3), B(G15), B(TEE),
B(2-silo), B(build).

**Tier C — honestly gated or refused.** The operation's claim is one no
lane can carry at model scale 2026: method/causality/transfer verification,
novelty as a *gate* rather than a price haircut, counterfactual outcome
metrics, unbounded prose emission as a charged channel, topology channels
nobody has priced (direction-of-dependence without G15), and G13
re-declaration until its event kind exists. **The Tier-C rows are
load-bearing refusals** — the register of what the substrate declines to
claim is itself the product; a substrate that asserted these away would be
selling success-shaped privacy claims.

The one-line law: **an operation's tier can be read off its spine
coordinates; a tier claim without coordinates is marketing.**

## 4. The operations table

Column legend — alph: closed/schema/declared/`—` (never crosses) · silo:
self/2T/kT/3C/3R/any · lane: prov/trust/est/unprov · closure:
in-ch/ext/refused/`—` · rung: R1/R2/R3/any · extr: 1shot/meter/campgn/`—`.

### A. Confined computation (the calculus's crossing primitives)

| Operation | alph | silo | lane | closure | rung | extr | status | tier | source |
|---|---|---|---|---|---|---|---|---|---|
| `work` (pure confined worker) | — | self/2T | trust | — | R1 | meter | IMPL | A | `primitives/CALCULUS.md` §3(i); the chamber wedge and corpus-demo harness (both private) |
| `judge` (evidence → closed verdict) | closed | self/2T | trust | — | R1 | meter | IMPL | A | `primitives/CALCULUS.md` §3(ii); `chambers/ip_trade_sim/test_calculus_bound.py` |
| `release` (consent-gated crossing) | closed | any | prov | — | R1 | meter | IMPL | A | `primitives/CALCULUS.md` §3(iii); `primitives/CANON.md` CORE_LAWS |
| `gatePub` (public-inputs envelope) | closed | — | prov (L5) | — | any | 1shot | IMPL | A | `primitives/CALCULUS.md` §3(iv); `stories/MARKETS.md` §6; the chamber wedge (private) |
| `gatePriv` (= release at Bool) | closed | 2T | trust | — | R1 | meter | SPEC | B(build) | `primitives/CALCULUS.md` §3(iv) |
| `ablate` / `influence` (counterfactual review) | closed | 2T | trust | — | R1 | meter | IMPL | A | `primitives/CALCULUS.md` §4; `primitives/STRUCTURE.md` §5; the corpus demo and egress harness (both private) |
| Guest transform (third-party-authored, contract-only) | closed | 2T | trust | — | R1 | meter | IMPL | A | the corpus demo's guest contract (private) |
| In-chamber derivation / annotation | — | self | prov (zero-charge, `chambers/lean/ChargeKernel/Algebra.lean`) | — | any | — | SPEC | B(build) | `LICENSING.md` rights 1–2; `stories/gardener.md` |
| Elicitation (typed questions to an owner) | schema | 2T | trust | — | R1 | meter | NAMED | B(schema) | `stories/party-matchmaker.md` Act 1; G12 |
| In-chamber reframing (never crosses) | — | self | trust | — | any | — | NAMED | B(build) | `stories/attention-guardian.md` |

### B. Verdict and judgement operations

| Operation | alph | silo | lane | closure | rung | extr | status | tier | source |
|---|---|---|---|---|---|---|---|---|---|
| Overlap detection (trit / IPVerdict ≈ 9.72 bits) | closed | 2T | trust | — | R2 | meter | SPEC; verdict channel IMPL in sim | B(2-silo) | `primitives/CALCULUS.md` §7; `stories/frontier-lab-ip-mediation.md` Deal 1; `stories/MARKETS.md` §5 |
| Result verification (score ≥X in sealed verifier) | closed | 3C | prov (TEE) / trust (sim) | in-ch | R3 | meter | IMPL sim / SPEC real | B(TEE) | `frontier/ip-trades/README.md` §2 §5; `chambers/ip_trade_sim/SIM.md` |
| Method verification (causality/novelty/transfer) | — | — | unprov | refused | — | — | NAMED-as-refusal | **C** | `frontier/ip-trades/README.md` §2 §6.1; `primitives/CANON.md` IPTRADE_LAWS |
| Verified partition (proven[]/trusted[]/unprovable[]) | closed | any | (the lane machinery itself) | — | any | — | SPEC | B(build) | `primitives/iptrade.ts` via `frontier/ip-trades/README.md` §2 |
| Novelty / OOD estimation (price haircut, never a gate) | declared | self | est | — | R1 | meter | IMPL | B(est) | `frontier/ip-trades/valuation-and-research.md`; `chambers/ip_trade_sim/novelty.py` |
| Ranking (full order charges log₂ n!) | closed | self | trust | — | R2 | meter | IMPL | A | `frontier/private-data-moats/lens-economics.md` §1.2; `chambers/cardinal_wedge/run_sort_metered.py` |
| Selection / shortlist (pick-k, fixed reason codes) | closed | self | trust | — | R1 | meter | IMPL | A | the corpus demo's guest contract and sink schema (private) |
| Redact-summarize (word-capped diligence prose) | declared | self | trust | — | R1 | meter | IMPL | B(declared) | the chamber runbook's output law (private); `stories/MARKETS.md` §1 |
| Drill-down facet (fixed 5-element menu, 3.00 bits) | closed | self | trust | — | R1 | meter | IMPL | A | the chamber runbook (private); `primitives/CALCULUS.md` §7 |
| Reference check (~60-bit schema + subject consent) | schema | 2T+subject | trust | — | R1 | meter | SPEC | B(schema) | `stories/reference-check.md`; `stories/MARKETS.md` §2; G4 |
| Match card projection (13-bit card, no identity) | closed | 2T | trust | — | R2 | meter | IMPL | A | `stories/party-matchmaker.md` Act 3; `chambers/kernel/demo_attention_notify.py`; runtime `match_card` golden bundle |
| Fit / complement / risk / non-relation judgements | closed | kT | trust | — | R1 | meter | SPEC; intro path IMPL | B(build) | `primitives/CANON.md` MEDIATION_LAWS; `stories/consult-storyweaver.md`; `chambers/intro_clearing/` |
| Defect hint (~20-bit card) vs raw patch (8 bits/byte) | schema vs declared | 2T | trust | — | R1 | meter | NAMED | B(schema) | `stories/gardener.md` |
| Negative-knowledge advisory (searched-and-empty) | schema | self | est | ext (bonded coverage) | R1 | meter | NAMED | B(est) | `frontier/private-data-moats/lens-economics.md` C6, M3; `stories/frontier-lab-ip-mediation.md` |
| Technique sketch (class/applicability/effect-size enums) | schema | 2T | trust | — | R1 | meter | NAMED | B(schema) | `stories/frontier-lab-ip-mediation.md` Deal 2 stage 1 |
| Mediated reproduction verdict (third attested enclave) | closed | 3C | trust | in-ch | R3 | meter | NAMED | B(R3) | `stories/frontier-lab-ip-mediation.md` Deal 2 stage 2 |
| Eval-conformance buckets to regulator | closed | 3R | trust | — | R1 | meter | NAMED; accounting shape exercised (`chambers/d1_bounty/`) | B(build) | `stories/frontier-lab-ip-mediation.md` Deal 3 |
| Synthesis over leaf judgements (closure-charged) | closed | kT | trust | — | R1 | meter | NAMED | B(build) | `stories/coagent-economy.md`; P-codes |
| Committed alpha attestation (hash now, score later) | closed | self | est | ext (neutral harness vs public prices) | R2 | meter | NAMED | B(est) | `stories/MARKETS.md` §3 |
| Cohort aggregate (N-party, real DP ε) | declared | kT | est | — | R1 | meter | NAMED | B(est) | `stories/MARKETS.md` §7 |
| Expert confidential consult (typed severity verdict) | schema | 2T | trust | ext (audited samples) | R1 | meter | NAMED | B(schema) | `stories/MARKETS.md` §4 |
| Oracle-approved patch acceptance (quantized bands) | closed | 2T | trust | in-ch | R2 | meter | SPEC | B(build) | `private: autoresearch/2026-07-01-premier-use-cases/README.md` §3; `primitives/market.ts`, `primitives/pricing.ts` |
| CI-verdict-as-oracle (pay-on-green) | closed | 2T | trust | in-ch | R2 | meter | SPEC; kernel binding IMPL | B(build) | `stories/gardener.md`; kernel charge_ids law |

### C. Verification, attestation, audit

| Operation | alph | silo | lane | closure | rung | extr | status | tier | source |
|---|---|---|---|---|---|---|---|---|---|
| Outcome attestation (bonded, quorum'd, slashable) | closed | ext parties | trust | ext (it IS the ext-closure machinery) | R1 | meter | IMPL | B(ext) | charge-settlement/2, `ASSURANCE.md` L2; `stories/party-matchmaker.md` Act 4 |
| Retroactive appreciation tap (glad/neutral/noise) | closed | 2T | trust | ext | R1 | meter | NAMED | B(ext) | `stories/attention-guardian.md` |
| R2 deterministic run + stranger re-run | — | self | prov | — | R2 | — | IMPL | A | `chambers/runtime/RUNNER-SPEC.md` |
| Environment observation (R1 hashes) | — | self | trust | — | R1 | — | IMPL (claimClass stamping open) | A | `RUNTIME.md`; ENVIRONMENT_LAWS; the chamber wedge's `finalize_claims` (private) |
| TEE attestation-gated key release | — | self | prov | — | R3 | — | NAMED | B(R3) | `RUNTIME.md` R3 |
| Denial canaries (demonstrated OS denial) | closed | self | trust | — | R1 | — | IMPL | A | the corpus demo's confinement canaries (private) |
| Estimator adversarial probe (sound + tight over 1472 emissions) | — | self | trust (L3 empirical) | — | R1 | — | IMPL | A | `ASSURANCE.md` L3; `chambers/d1_bounty/estimator_probe.py` |
| Conformance replay (two shared-nothing impls, bit-for-bit) | — | any | prov | — | any | — | IMPL | A | `ASSURANCE.md` L1; `chambers/conformance/`, `chambers/kernel/rust_ledger/` |
| Peer-prediction quality scoring | closed | kT | trust | — | R1 | meter | IMPL sim | B(build) | `FRAMEWORKS.md` F5; `chambers/peer_sim/` |
| Reviewer-coherence battery (order-swap/paraphrase probes) | schema | self | est | — | R1 | meter | SPEC | B(est) | `chambers/review_audit/PROBE-SPEC.md` |
| Reuse attestation (licensee-signed build provenance) | declared | self | trust | ext | R1 | 1shot | SPEC | B(ext) | `frontier/ip-trades/README.md` §3.2 |
| Reuse evidence (contestable exhibit, never a boolean) | schema | 2T | est | ext | R1 | 1shot | SPEC | B(est) | `frontier/ip-trades/README.md` §3.2 |
| Fuzzy/distance-aware PSI (crypto overlap count) | closed | 2T | prov | — | R1 | 1shot | NAMED | B(build) | `research/mediation-literature.md` Vein 4 |

### D. Matching, introduction, attention

| Operation | alph | silo | lane | closure | rung | extr | status | tier | source |
|---|---|---|---|---|---|---|---|---|---|
| Priced introduction clearing | closed | 2T | trust | in-ch | R1 | meter | IMPL (contingent-fee leg = named residue, `PARTY_LANE_GAPS`) | A | `private: autoresearch/2026-07-01-premier-use-cases/README.md` §2; PRICING_LAWS; `chambers/intro_clearing/` |
| Attention notification (credits AND bits, atomic) | closed | 2T+3rd | trust | in-ch | R1 | meter | IMPL | A | `chambers/kernel/attention_node.py`, `chambers/kernel/demo_attention_notify.py`; `stories/party-matchmaker.md` Act 3 |
| Denominator control (bucketed pool sizes) | closed | kT | trust | — | R1 | meter | SPEC | B(build) | MATCHING_LAWS; `private: autoresearch/2026-06-29-orthogonal-type-systems/01-orthogonal-type-atlas.md` §11 |
| Bilateral reveal / identity widening | closed | 2T | prov (`chambers/lean/ChargeKernel/Widening.lean`) | — | R1 | 1shot (one-way) | SPEC; algebra IMPL | B(build) | `stories/consult-storyweaver.md` runs 2/6; COALITION_LAWS |

### E. Trade and negotiation lifecycle

| Operation | alph | silo | lane | closure | rung | extr | status | tier | source |
|---|---|---|---|---|---|---|---|---|---|
| Claim commitment (hash first, salted) | closed | self | prov | — | R1 | 1shot | IMPL sim / SPEC | B(build) | `private: autoresearch/2026-07-01-premier-use-cases/README.md` §1; `chambers/ip_trade_sim/SIM.md`; `primitives/negotiation.ts` |
| Staged reveal ladder (reciprocity-gated) | schema | 2T | trust | — | R1 | campgn (walk-away timing is an emission) | SPEC | B(schema) | NEGOTIATION_LAWS; `private: autoresearch/2026-07-01-premier-use-cases/README.md` §1 |
| Black-box probe (the distillation channel) | declared | 2T | est | — | R1 | campgn | IMPL sim | B(declared) | `chambers/ip_trade_sim/SIM.md` |
| Appraisal / valuation (benchmark-normalized marginal) | declared | self | est | — | R1 | meter | IMPL sim | B(est) | `chambers/ip_trade_sim/economics.py` |
| Price negotiation (metered rounds, commitments persist) | declared | 2T | est | — | R1 | meter | IMPL sim | B(declared) | `chambers/ip_trade_sim/price_debate.py`, `chambers/ip_trade_sim/SIM.md` |
| Atomic settlement / key-for-payment swap | closed | 2T + consortium | trust (regime-typed) | in-ch | R1–R3 by regime | 1shot | SPEC | B(build) | `frontier/ip-trades/README.md` §3.3 §5 |
| Paid method reveal (fills a fresh consented ceiling) | declared | 2T | trust | — | R1 | 1shot | IMPL sim | B(declared) | `stories/frontier-lab-ip-mediation.md` Deal 2.4; `chambers/ip_trade_sim/SIM.md` |
| Royalty licensing (consent-first LicenseGrant spine) | schema | 2T | trust | ext | R1 | meter | SPEC | B(ext) | `frontier/ip-trades/README.md` §3.2 |
| Refusal with evidence (typed refusal record + priorityCommit) | closed | self | trust | — | R1 | 1shot | SPEC | B(build) | `frontier/ip-trades/valuation-and-research.md` Truth 1 |
| Barter fairness oracle (dual metered OOD estimates) | declared | 2T | est | — | R1 | meter | NAMED | B(est) | `frontier/ip-trades/valuation-and-research.md` first wedge |

### F. Accounting, lifecycle, ledger (substrate verbs)

These rows emit court-file arithmetic, not disclosure channels: the
"alphabet" is the ledger itself, public and stranger-checkable, so
disclosure axes are marked `—` and rung is `any` (the accounting ladder,
`ASSURANCE.md`, carries the assurance instead of the runtime ladder).

| Operation | lane | closure | extr | status | tier | source |
|---|---|---|---|---|---|---|
| Coupled atomic charging (all accounts or none) | prov | — | — | IMPL | A | `ASSURANCE.md` L2 MediationSession; `LICENSING.md` |
| Lifetime (source × reader) exposure accounting + incident latch | prov | — | — | IMPL | A | COALITION_LAWS; `chambers/kernel/`; `stories/frontier-lab-ip-mediation.md` |
| Lease issuance / partition ceiling | prov (Lean) | — | — | IMPL | A | `ASSURANCE.md` L2/L4 |
| Block-before-ceiling refusal (fail closed pre-crossing) | prov (Lean odometer) | — | — | IMPL | A | CALCULUS_LAWS L8 |
| Derivation declaration + provenance-closure charging | prov | — | — | IMPL | A | `frontier/private-data-moats/lens-types.md` §3; G14; `chambers/lean/ChargeKernel/ProvenanceCompleteness.lean` |
| Attribution split (exact integer Shapley) | prov (`chambers/lean/ChargeKernel/Attribution.lean`) | — | — | IMPL | A | `stories/alpha-sharing.md`; `chambers/kernel/attribution.py` |
| Settlement (conservation by theorem; fails closed on dirty courts) | prov | in-ch | — | IMPL | A | `chambers/kernel/settlement.py`, `chambers/kernel/SETTLEMENT-SPEC.md` |
| Entropy-pool payment batching (anonymity set stated, k honest) | trust | — | meter | SPEC | B(G15) | `primitives/mediation.ts` laws; `stories/frontier-lab-ip-mediation.md` Deal 2 |
| Widening (priced, unanimous, one-way) | prov (algebra) | — | 1shot | IMPL algebra; routing all paths through it = L1–L3's open job | A | `primitives/coalition.ts`; `chambers/lean/ChargeKernel/Widening.lean` |
| Covenant / revocation / exit (cap future, grandfather past) | prov | — | — | IMPL | A | `chambers/kernel/covenant.py`, `chambers/kernel/COVENANT-SPEC.md` |
| Erasure tombstone (destroys bytes, never others' proofs) | trust | — | 1shot | SPEC | B(build) | CORE_LAWS; `frontier/private-data-moats/lens-types.md` M1 |
| Export / portability (exposure history survives the divorce) | trust | — | 1shot | NAMED (G7, unexercised) | B(build) | `frontier/private-data-moats/lens-types.md` M5 |
| Scoped court views (Merkle-scoped, fork detection) | prov | — | — | IMPL | A | `chambers/kernel/scope.py`, `chambers/kernel/SCOPE-SPEC.md` |
| Key-author identity (signature or conviction) | prov | — | — | IMPL | A | `chambers/kernel/identity.py`, `chambers/kernel/IDENTITY-SPEC.md` |
| Audit conviction (total fold over adversarial soups) | prov (`chambers/lean/ChargeKernel/VerdictPartition.lean`, `ValueGate.lean`) | — | — | IMPL | A | `chambers/kernel/ledger.py`, `chambers/kernel/node.py` |
| Fiduciary legibility query (whose agent is it) | prov (fold arithmetic) | — | — | NAMED | B(build) | `stories/attention-guardian.md` |
| Moat residual statement (per-pair residual sentence) | trust | — | — | SPEC | B(schema) | `frontier/private-data-moats/lens-types.md` §3(3) |
| Entropy re-declaration (owner-signed, monotone-down) | — | — | — | NAMED (missing event kind) | **C** until the G13 event kind exists | `stories/frontier-lab-ip-mediation.md` |

### G. Review and admission

| Operation | alph | silo | lane | closure | rung | extr | status | tier | source |
|---|---|---|---|---|---|---|---|---|---|
| Preflight review ×2 (adversarial-safety + proportionality) | — | self | trust | — | R1 | — | IMPL | A | the chamber runbook's four gates (private) |
| Release review ×2 (privacy + injection/truthfulness) | — | self | trust | — | R1 | — | IMPL | A | the chamber runbook (private) |
| Deterministic scans (secrets, paths, timestamps, blobs) | — | self | prov (deterministic) | — | R1 | — | IMPL | A | the chamber runbook (private) |
| Canonicality / admission review (requested vs justified capacity) | — | any | trust | — | R1 | — | SPEC | B(build) | `primitives/CANON.md` MEDIATION_LAWS; `stories/consult-storyweaver.md` runs 1/2/7 |
| Inferential-target (collateral leakage) screen | — | kT | est (`unenumeratedTargetsRemain: true` standing) | — | R1 | — | SPEC | B(est) | `primitives/coalition.ts` frontier #16 |
| Subject consent gate + response right | schema | 2T+subject | trust | — | R1 | meter | NAMED (G4) | B(build) | `stories/reference-check.md` |
| Owner release decision (human gate on content) | — | self | trust | — | R1 | — | IMPL | A | CORE_LAWS; the chamber wedge (private) |

## 5. The premier case, walked

The 22-step IP-mediation protocol (`primitives/CALCULUS.md` §7,
`stories/frontier-lab-ip-mediation.md`, `frontier/ip-trades/`,
`chambers/ip_trade_sim/SIM.md`), each step read off the table above.

**Tier A today** (running code, stranger-auditable court files):

- Step 1, registration — kernel IMPL; the ledger act is A. The declared
  entropy figure it records is an `est`-lane input (B-grade; see step 11).
- Step 3, gatePub envelope check — free by simulatability (L5).
- Step 14, influence pass — the paired-ablation harness runs
  (the corpus demo and egress harness (both private)); its
  *protocol position* as a pre-release consent-time pass is still SPEC.
- Step 15, release + one drill-down facet under the printed cut bound.
- Step 16 (core), settlement — escrow bound to exact charge ids,
  required_clean, conservation by theorem.
- Step 19, lifetime composition accounting + incident latch — the
  verification-as-extraction defense, IMPL.
- Step 20, the structural evidence artifact (PlainAccount) in
  `primitives/STRUCTURE.md` §5 order.

**Tier B**, each gated on a named piece — the whole build-out is five
pieces, not a research program:

- *Two-silo chamber run mode* (`primitives/CALCULUS.md` §8 item 3) gates
  step 2 (program-level consent ceremony), step 5 (dual confined work over
  the exact 2-tuple), and step 6 (the atomic overlap verdict — whose
  verdict machinery is already IMPL in sim).
- *The TEE first-wedge* (`frontier/ip-trades/README.md` §5) gates step 9,
  result verification for real counterparties (IMPL in sim today).
- *The R3 runner + attestation-gated key release* (`RUNTIME.md`) gates
  step 10, mediated reproduction in a third enclave — per the story, the
  only new infrastructure Deal 2 stage 2 needs.
- *G15 entropy-pool batching* gates step 16's payment leg: an exact-amount
  timestamped license payment leaks which lab needed whose technique, and
  direction-of-dependence between frontier labs is market-moving.
- *The cross-question adaptive budget* gates running steps 8 and 13
  (black-box probe, price negotiation) on the live chamber rather than the
  sim — the sim has it, the chamber demo does not.
- Alphabet- and lane-priced B steps, buildable without new infrastructure:
  step 4 (canonicality review, SPEC), step 7 (technique sketch — schema),
  steps 11–12 (novelty estimate and valuation — `est` lane, price inputs
  never cliffs; the buyer-conditioned leakage wiring is the barter-oracle
  wedge), step 17 (paid method reveal — declared, fills a fresh consented
  ceiling), step 18 (royalty spine — `ext` closure on bonded roots),
  step 21 (third-reader regulator emission — its accounting shape already
  exercised by `chambers/d1_bounty/`).

**Tier C**, refused or waiting on an event kind:

- Step 22, G13 re-declaration when the public baseline catches up —
  C until the owner-signed monotone-down event kind exists; today a
  downward re-declaration hits the I7 quarantine.
- Standing over the whole protocol: the buyer question "does this
  *technique* work / did it cause the lift / is it novel" is method
  verification — `unprov`, refused, never on the step list. The protocol
  sells overlap verdicts, result verifications, and reproduction verdicts
  precisely because those are the claims a lane can carry.

Why this case is premier (`stories/frontier-lab-ip-mediation.md`, closing
argument): its high-value deals sit almost entirely in A–B — seven steps
run today (three carrying a named qualification in-row) and the rest gate
on five named builds; its contingent outcomes
(repro, eval conformance) are **in-chamber metered work**, so escrow
releases against ChargeEvent ids and the deepest missing rung (G1, outcome
oracles) never bites; and its counterparties are structurally
Sybil-resistant — single-digit named entities, public beneficial ownership,
already running the clean-team institutions the chamber mechanizes, already
denominating value in compute. The (source × reader) key is at its
strongest exactly where each reader is few, named, and heavily capitalized.

## 6. What the taxonomy exposes

Register entries, not solved problems. Operations a working IP mediation
needs that the corpus does not yet name or build:

- **Freshness/staleness attestation** — attesting a claim's vintage against
  a pinned public-corpus snapshot at deal time; NoveltyRoot's VRF pin is
  the closest machinery, scoped to novelty only
  (`stories/frontier-lab-ip-mediation.md` G13;
  `frontier/ip-trades/valuation-and-research.md`).
- **The arXiv-reading estimator institution** — declaring
  delta-over-public-knowledge IS a literature review with a signature;
  adversarial_review independence becomes mandatory; no spec beyond
  `chambers/ip_trade_sim/novelty.py`.
- **Worker-side fair exchange** — commit-before-read / escrowed reveal;
  `primitives/CANON.md` frontier #2, named unsolved; needed the moment the
  seller is the weak party.
- **Verification-cost pricing** — frontier #14; nobody pays for enclave
  runs or research-substrate tokens; cost incidence is unfunded.
- **Multilateral forms** — barter rings, combinatorial bundles, competing
  bidders; everything is still bilateral
  (`frontier/ip-trades/valuation-and-research.md`).

Axis reconciliations owed:

- **Two lane systems, never unified**: derived/declared (charge channels,
  CALCULUS_LAWS) vs proven/trusted/estimated/unprovable (verdicts,
  `primitives/iptrade.ts`) — and within the second, `estimated`'s
  membership drifts: `iptrade.ts` shipped three lanes,
  `frontier/ip-trades/valuation-and-research.md` added the fourth,
  `primitives/mediation.ts` uses it, `primitives/CANON.md` IPTRADE_LAWS
  still reads as the three-partition.
- **Codebook / schema / alphabet** — three names, one object;
  `primitives/STRUCTURE.md` fixes "alphabet"; not yet in CANON.md's alias
  table.
- **Independence classes in three lexicons** — estimator attestation,
  outcome attestation, reviewer role separation; one concept, no shared
  enum.
- **`entropy_bits` vs `subject_entropy_mbits`** — unit and name drift
  across the sim/kernel boundary (`chambers/ip_trade_sim/types.py` vs
  kernel/stories).
- **The atlas ObservableClass × precision × cadence taxonomy**
  (`private: autoresearch/2026-06-29-orthogonal-type-systems/01-orthogonal-type-atlas.md`
  §6) is the richest emission-surface axis in the corpus and is ignored by
  CALCULUS/STRUCTURE — it is the concrete checklist the calculus's
  every-observable-enumerated proviso needs.

## 7. Vocabulary

This document says **alphabet** for the object a channel can express —
never codebook or schema as the object's name (that three-way drift is a §6
register entry; "schema" here names only the alphabet *class* whose
capacity derives from typed fields). The outward artifact is the
**evidence artifact** — `PlainAccount`, the court file. One deliberate
substitution, marked once: canon's historical name for that artifact, and
one canonical sentence quoted below, use a word this taxonomy replaces
everywhere with "evidence artifact" / "legible evidence"; every quotation
in this file carries the substitution.

The load-bearing phrases this document preserves:

- "the alphabet is the object; the bit number is its logarithm"
- "a derivative is confined to its generating context unless a release
  transaction widens the context"
- "bits are the anti-laundering clause, not the guarantee"
- "sell verdicts, not prose"
- "no boolean `verified`" — every verification resolves to
  proven[]/trusted[]/unprovable[]
- "value moves iff metered work moved"
- "nobody buys bits; people buy scoped rights and legible evidence"
  (substituted form)
