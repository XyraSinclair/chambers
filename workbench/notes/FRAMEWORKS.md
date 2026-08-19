# Frameworks — the import register

**What this is.** ASSURANCE.md says what is *known*; MACHINES.md what is
*runnable*; STORIES.md where it *touches people*. This file is the fourth
question: **what formal machinery exists elsewhere that we are not using
yet.** Each row is a candidate import. Admission discipline, same culture
as everywhere else: a framework enters only with its **core theorem
named**, the **law or gap of ours it touches**, the **delta to the build
queue**, and the **honest price**. Status of every row is NOT IMPORTED
unless marked. Nothing here is a claim of possession — this register
exists precisely so we don't gesture at literatures we haven't done the
work to hold.

(The type layer already ran this move once: the 2026-07-02 premier-type-
surface pass judged seven type systems against one crossing and chose the
branded-ADT canon + graded-semiring accountant. This register is the same
move for the ECONOMIC and AUDIT layers.)

---

## Tier 1 — would change what we build next

### F1. Quantitative information flow: g-leakage
**Framework.** QIF (Alvim–Chatzikokolakis–McIver–Morgan–Palamidessi–
Smith, *The Science of Quantitative Information Flow*). Leakage as
**g-vulnerability**: parameterized by an attacker **gain function** g —
what the adversary can *do* with the information, not how many bits it
is. Core results: channel composition bounds; the **refinement order**
(Coriaceous theorem: channel A refines B iff NO gain function prefers A —
robust dominance, not per-metric argument).
**Touches.** G2 — "bits are not harm" — is the register's oldest named
limit, held today as a permanent conjunction with an unformalized
"ordinal review." Gain functions ARE the missing calculus for that other
half: one bit of "which house" vs one megabyte of trivia is a *g*
difference, not a mbits difference.
**Delta.** Leakage classes become g-indexed families; an estimator
attestation may declare the gain-function class its worst-case was taken
over; the refinement order gives the principled statement of "this
emission is safe against EVERY attacker goal in class G," which is what
`worst_case_over_secrets` gestures at today.
**Price.** Real modeling work at the estimator boundary (the meter stays
integer — g-computations live where log₂ lives today). Danger of
false precision: gain functions must be declared, coarse, and few, or
they become unauditable discretion.
**DESIGN LANDED 2026-07-06** (`frontier/measurement/g-leakage.md`, L5
lane): verdict SPLIT — v0 import-now (declared `gain_class` +
`predicate_family` as non-load-bearing attestation metadata; every
existing attestation defaults to `full_secret`, a confession not a
change; `goal_coverage` receipt caveat), v1 wait behind three named
preconditions (owner-signed predicate registry with G13 depreciation;
per-key-estimates `charge_coupled` generalization = an
egress-accountant/2 conformance bump; the one-import-in-flight queue —
F3 is ahead). Central reduction: a declared attacker goal is a DERIVED
SECRET with its own account and entropy denominator — the concentrated-
regime failure is a denominator error, not an arithmetic error. Worked
example replayed bit-for-bit through accountant.py: same emission,
`bounded` against the file and `REFUSED_CEILING` against the goal.
Refusals: closed 3-class enum (free gain functions = unauditable
discretion with a bibliography); G5 keeps the only all-g quantifier;
"regret is not a gain function" — the G2 conjunction stands.

### F2. Transparency logs + fork consistency
**Framework.** Merkle/Certificate-Transparency verifiable logs; SUNDR
**fork consistency**; CONIKS/key-transparency verifiable maps. Core
theorems: O(log n) membership and append-only consistency proofs; a
forking server is detected on the first cross-gossip between two clients
it showed different worlds.
**Touches.** **E2 (reader scoping)** — currently marked "the first
genuinely new design work." It is not new: it is exactly the
authenticated-partial-view problem.
**Delta.** E2 becomes an adaptation, not an invention: a deterministic
Merkle tree over the id-sorted event set; a scoped view = subset +
membership proofs + a signed tree head; federation gossip doubles as
fork-consistency checking. "Point it at courts, not secrets" becomes a
mechanism with a theorem.
**Price.** Signatures enter the stack for the first time (tree heads
need node keys) — authentication is L5, deliberately unsolved; the
import must keep the unsigned-claims core intact and price STH keys as
the lease-issuer trust is priced today. Spec churn: canonical
Merkleization of the jsonl artifact.
**IMPORTED 2026-07-06** as `charge-scope/1` (SCOPE-SPEC.md, scope.py,
node endpoints /v1/{head,scope,consistency}, --scoped-only) — WITHOUT
signatures: unsigned heads still give two-reader fork detection; the
signature layer stays priced at L5/E8 as this row demanded. Refusals
carried into the spec: inclusion not completeness (seq-density gaps as
omission evidence), scope ≠ solvency, topology channel stands (G15).

### F3. Accountable safety — conviction completeness as a theorem
**Framework.** BFT forensics / accountable-safety literature (Casper
slashing conditions, Tendermint forensics): protocols engineered so any
safety violation yields a **transferable proof identifying culpable
parties**, with completeness results.
**Touches.** The entire I/S-code culture is an instance of this design
pattern, built independently. Our L3 detector-completeness fuzzer is the
empirical shadow of a provable claim.
**Delta.** State and prove, law by law, in Lean over the abstract soup
model: *"any event set in which escrow e is over-disbursed contains a
finite witness that convicts under S2 and names its issuer."* Upgrades
ASSURANCE L4 from "the honest ops conserve" to "the audit is COMPLETE
for the law set" — the strongest single claim the stack could add.
**Price.** Lean must model the AUDIT over adversarial soups, not just
honest ops — the lift we have so far avoided. Bounded if done one law at
a time; the fuzzer tells us which laws are cheap to start with.
**TRANCHE 1 LANDED** (`Completeness.lean`): S1/S2/X0 complete and sound
over arbitrary soups, each finding naming its subject and issuer.
**TRANCHE 2 LANDED 2026-07-09** (`ProvenanceCompleteness.lean`): the P1
arm — any derivation chain to an uncoupled anchored source convicts at a
FIXED fuel (closure saturation by pigeonhole loop-cutting; cycles and
depth buy the adversary nothing), and only real ancestry convicts.
Open, named: S3/S4/S7/S8 (drag in the I-code court), S9/S10, P2
(max-flow), the V-family.

### F4. Monitorability doctrine — safety vs liveness (import = doctrine, ~free)
**Framework.** Runtime verification; Alpern–Schneider safety/liveness
decomposition. Core fact: only **safety** properties are convictable
from a finite event set; liveness ("the issuer eventually releases") is
not monitorable — ever.
**Touches.** This retroactively *explains* S8: silent holdup was a
liveness law; the shipped fix (declared expiry + permissionless
resolution) is exactly the standard reduction of liveness to safety via
deadline reification. We derived it by consult and correction; the
literature says it was forced.
**Delta.** Promote to design law: **every protocol obligation must
arrive safety-shaped, or carry its deadline + permissionless-resolution
reduction at design time.** Apply as a checklist to every future law
(E5 covenants, E6 substrate equivocation, attention windows). Prevents
relearning S8 per layer the way fact-identity was relearned per layer
(the pattern that forced E6).
**Price.** None. **IMPORTED 2026-07-06** — adopted as design law in
`chambers/kernel/PROTOCOL.md` ("every obligation arrives
safety-shaped"), with the checklist question every new law must answer.

---

## Tier 2 — named literatures for open gaps (design-queue entries)

### F5. Peer prediction — pricing the unprovable lane
**Framework.** Proper scoring rules; peer-prediction mechanisms
(Miller–Resnick–Zeckhauser; Dasgupta–Ghosh; correlated agreement;
Bayesian Truth Serum). Core theorem: truthful reporting as a strict
equilibrium **without ground truth**.
**Touches.** charge-settlement/2 refuses unprovable-lane outcome
conditions (flat-fee only) and G10 (judgement quality) has "no
vocabulary." Peer prediction is the only known machinery that prices
honesty where no platform log can exist.
**Delta.** A /3 candidate: unprovable-lane quality bonuses scored by
correlated agreement among independent judges, with the IC theorem and
its known collusion limits stated in the spec's non-claims.
**The novel constraint — ours, not the literature's.** Every additional
judge is a READER: the mechanism's own redundancy is metered leakage.
Peer prediction assumes reports are free; here each report costs
exposure mbits. Whether the IC bonus survives the leakage price of the
redundancy that generates it is a genuine open research question this
stack is uniquely positioned to pose. It may kill the import — that
verdict would itself be publishable.
**DESIGN LANDED 2026-07-09** (`frontier/judgement-markets/
peer-prediction.md`, runnable companion `workbench/peer_sim/`):
verdict SPLIT plus a KILL, and the question's presupposition rejected —
IC neither survives nor dies globally, because the redundancy price is
LOCAL AND INTEGER (`redundancy_mbits = Σ audit-reader charges`, already
on the artifact); the protocol's one obligation is printing it. Central
findings: the CA score is pure ledger arithmetic over reports (the
constant-report strategy scores EXACTLY zero, an identity the sim
self-checks — so peer prediction is the conversion of an unprovable
world-fact into the recomputable fact the settlement doctrine demands;
the /3 becomes a score-bound escrow, attribution/2's pattern, third
instance); spot-check subsetting and PROJECTION JUDGING (novel: the
audit reader reads a cheaper schema-bound projection iff Δ-dominance
survives coarsening — leakage-aware mechanism design) are the two
knobs on L. The KILL, made arithmetic and demonstrated live: on
high-sensitivity sources the owner's registration ceilings refuse the
audit reader (REFUSED_CEILING inside a token redundancy budget — the
sim shows it), so the mechanism cannot buy honesty with the owner's
secrets exactly where honesty matters most; that regime keeps process
receipts (review-audit/1, zero owner leakage). v1 preconditions: a
report event kind (stranger-recomputable score); judge independence
beyond declaration (G8's cell); estimator-lane evidence for projection
dominance. Residues: correlation ≠ truth; permutation collusion (L5).

### F6. Cooperative attribution — Shapley/Myerson on the provenance DAG
**Framework.** Cooperative game theory: Shapley value (unique axiomatic
surplus split), Myerson value (respects graph structure).
**Touches.** G14 (provenance closure) + multi-payee escrows: when a
placement fee lands, which of the five consumed upstream judgements gets
what share? Today: ad hoc percentages. First-contact attribution (shipped
as the G1 proxy) is the degenerate last-touch case.
**Delta.** Attribution becomes a **declared split rule recomputable from
the artifact** — the ledger already stores the DAG (leaf charges name
their sources). Pairs with G14's audit family.
**Price.** Exact Shapley is exponential — irrelevant at our n; the real
price is agreeing on the characteristic function (declared, like
pricing, above the protocol).
**IMPORTED 2026-07-08** as `charge-attribution/1` (ATTRIBUTION-SPEC.md,
`attribution.py`, V1–V5 on a separate `v_codes` surface; frozen corpora
untouched). The characteristic function question answered the register's
own way: v(S) = min(E, maxflow(coalition anchors → d)) — the SAME
quantity the P-codes charge, priced from the pot's direction, so the
"agreement" is a ledger fact a stranger recomputes, and counterfactuals
stay inexpressible. Exact integer Shapley (subset weights, NMAX=12 — a
denial-of-audit refusal, not a scaling apology), largest-remainder
allocation conserved-by-theorem (`Attribution.lean`: `alloc_conserves`,
`walk_efficiency`, floor-only rule proven leaky axiom-free); the alpha
story — 1/8000 of an emission's capacity is paid exactly $12,500 of a
$100M pot — is a passing test and an `rfl`. Refusals carried into the
spec: capacity is the proxy (Goodhart priced openly, quality is the
oracle layer's job); declared reuse only (P.7's trust class, priced
once); one method (/1 convicts unknown method strings rather than
gesture at plurality).
**Part II landed same day** (ATTRIBUTION-SPEC Part II, S11/S12): the
conviction became enforcement — split-bound escrows disburse only along
the recomputed rows (exact amount, once, no report consulted on the
value path), V findings joined the dirty court with source-precise
touch, and the stiffed contributor collects her own row after expiry
permissionlessly (F4's checklist answered at design time). Remaining
residues: Rust-twin parity for V/S11/S12 — whose landing pad is now
FROZEN (2026-07-09, `attribution_traces/`: 8 golden ledgers, the alpha
story's 12_500_000_000 ucr pinned to the byte, honest CLEAN + stiff
CONVICTED under the one-command verifier; the counterparty implements
from ATTRIBUTION-SPEC alone and lands on these bytes); and
outcome-conditioned split pots refused, not designed (/3).

### F7. Differential privacy — a second estimator lane
**Framework.** DP: mechanism-derived ε with composition theorems (Rényi
accountants), parallel composition ≈ partitioning.
**Touches.** Every estimate today is *attested* worst-case. A noised-
aggregate emission can carry a *mechanism-derived* bound — machine-
checkable, no attestor to capture (shrinks G8 wherever it applies).
**Delta.** The evidence-lane idea just shipped for outcomes, applied to
the estimator itself: `attested` vs `mechanism_derived` estimate lanes,
higher lane = smaller trust surface. Pleasing symmetry: lanes become a
kernel-wide idiom.
**Price.** Applies only to aggregate/noised emissions (most judgements
are not). ε→mbits conversion must be a declared conservative table
(max-divergence bounds MI); getting that table wrong in the generous
direction is the dishonest direction — spec care.

### F8. Inspection games — random audit lotteries for estimator capture
**Framework.** Optimal-auditing literature (Mookherjee–Png):
randomized inspection + penalties achieve deterrence at sublinear audit
cost; equilibrium audit rates are computable.
**Touches.** G8 — a captured estimator under-counts and the audit "has
no independent ground truth." Deterministic re-checking of everything
would cost more than the work.
**Delta.** A declared audit lottery: random sample of accepted charges
re-estimated by an `adversarial_review` estimator; divergence slashes a
posted estimator bond — the S9/S10 machinery just built, pointed at the
estimator layer.
**Price.** Randomness in a CRDT needs a declared beacon (VRF-ish or
block-hash-style, itself an L5 trust object — name it); re-estimation
must be cheaper than the original work or the lottery is theater.

### F9. The decentralized-oracle attack register
**Framework.** Schelling-point oracle attacks: **p+ε bribery**
(Buterin), lazy-equilibrium critiques, escalation-game designs
(Kleros/UMA/Augur).
**Touches.** charge-settlement/2's attestation game IS a bonded oracle;
these are its known predators.
**Delta.** Cheap: import as an adversarial test checklist (a p+ε bribe
against a quorum; lazy attestors copying each other; bond-vs-bribe
bounds) + a SPEC non-claims table stating which attacks are priced-not-
prevented (bribery is L5, like every collusion).
**Price.** Days, not weeks. Highest defensive value per token on the
register. **IMPORTED 2026-07-06** — `test_settlement2_attacks.py` (8
attacks, each verdicted PREVENTED / PRICED / RECORDED) + SETTLEMENT-SPEC
§11.1 attack table with the bond-sizing rule (`min_bond_ucr ≥ amount /
quorum` for bribery indemnity) and the payment-finality non-claim. The
lane earned its keep on arrival: it caught a real S9 subject-escrow bug
(leaked loop variable — any multi-escrow artifact misjudged) that 23
unit tests and 12 golden scenarios had missed; fixed + regression
scenario `two-escrows-cross-reference` added to the corpus.

---

## Tier 3 — horizon; named so we stop half-remembering them

- **F10. ZK / succinct selective disclosure.** Prove fold/audit facts
  without serving the court — E2's endgame and the only full answer to
  G15. Against culture until forced: recompute-from-bytes beats
  trust-the-circuit for a stranger. Import when reader-scoping's Merkle
  form (F2) hits its ceiling, not before.
- **F11. Linear-logic / graded-semiring presentation of the kernel.**
  Microcredits and mbits are linear resources; conservation-by-typing.
  Partially imported on the type-surface side already (the graded
  semiring accountant, 2026-07-02). Elegance dividend for the kernel
  spec; no new theorem for the artifact. Note: session types are a
  *specification* lens only — audit-after-merge deliberately admits
  ill-typed events (they convict, not crash).
- **F12. Reputation as capital** (repeated games, Fudenberg–Levine).
  The formal home of the registration-bond idea already in the consult
  record; prices G3's whitewashing (re-registration = burned stake).
- **F13. Edge-DP / anonymity-set bounds for the topology channel.** G15's
  formal home: k-anonymity of the convened set as a declared, checkable
  receipt statement; edge-DP on the session graph.
- **F14. Bond insurance / pooling.** Under-capitalized honest attestors
  buy bonds from a pool; actuarial pricing. Blocked behind multi-issuer
  netting (G11's declared non-claim) — keep out until netting exists.

## Considered and declined

- **Petri nets / vector-addition systems** — conservation as P-invariant:
  true, and already carried by the Lean model; no marginal theorem.
- **Prediction markets (LMSR) for outcome aggregation** — a market maker
  is an issuer with unauditable discretion over prices; violates the
  Ethereum-test doctrine until someone prices that discretion. Peer
  prediction (F5) covers the honest need.
- **Full ocap/capability formalization** — leases already are
  capabilities; confinement theorems add naming, not mechanism.

## Import discipline

One import in flight at a time; an import lands the way E1 landed — spec
delta, implementation, corpus/tests, Lean where it touches conservation
or completeness, docs — or it stays a row here. Rows are cheap; halfway
imports are the sludge this register exists to prevent.

**Recommended order (2026-07-06):** F4 today (doctrine, free) → F9
alongside any /2 hardening (defensive, days) → F2 as the E2 design source
→ F3 as the next Lean campaign → F1 as the G2 research track. F5's
leakage-cost-of-redundancy question is the register's best *original*
research prompt.
