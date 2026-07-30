# Assurance: how we will KNOW the stack is solved

"Solved" is not a feeling and not a proof of everything. It is a **layered
assurance case** where every layer is machine-checked at its own level, the
unprovable layers are named and priced, and the whole ladder is inspectable by
a stranger. This file is the ladder. When all six rungs hold for a wedge, that
wedge is *known-solved*; the stack is solved when the rungs hold for every
shipped wedge and the kernel.

## The ladder

**L0 — Types.** Illegal states unrepresentable. Fourteen modules, laws as
exported consts, admission-gated. Status: HOLDS (`deno check
--sloppy-imports` green; survived
one 207-agent adversarial pass).

**L1 — Conformance.** A reference implementation plus a trace checker: every
implementation must emit court files that replay against `SPEC.md`. Status:
HOLDS for the egress-accountant sub-engine (`chambers/conformance/`) —
`SPEC.md` is normative and language-independent, and **two implementations
sharing no code (Python reference + a std-only Rust crate written from the spec
alone) agree bit-for-bit on 31 golden traces / 195 decisions**, cross-checked in
both harness directions and shown to fail on a single flipped bit. That build
forced the L2/L4 prerequisite into the open: the counterparty-compilable
boundary is the estimation/accounting boundary — the accountant charges in exact
integer millibits (`log2`/byte-ceilings live in the attested estimator), which
is what makes "the implementation's fold is a homomorphism" (L4) even statable.
A SECOND normative spec now covers the distributive layer:
`chambers/kernel/KERNEL-SPEC.md` (`charge-ledger/1` — canonical JSON, event
identity, jsonl wire, fold, audit codes) with a 16-scenario golden ledger
corpus (`ledger_traces/`, honest + Byzantine, including coupled mediation
charges) that replays bit-for-bit and regenerates deterministically — and the
counterparty build EXISTS: `chambers/kernel/rust_ledger/`, a std-only Rust
crate (hand-rolled canonical JSON + in-crate FIPS 180-4 SHA-256) written from
KERNEL-SPEC.md alone, never consulting the Python reference, **agreeing
bit-for-bit on all 16 golden ledgers** — fold, audit verdict, and byte-identical
reserialization — with a mutation test proving the harness is not vacuously
green. The exercise did its job twice over: the independent implementer
surfaced two spec ambiguities (issuer well-formedness in §3.1; the I3×I4
interaction), resolved as normative clarifications in KERNEL-SPEC.md and then
PINNED as corpus scenarios (`spec-ambiguity-issuer`, `spec-ambiguity-i3-i4`)
so every future implementation is forced to agree on exactly the cases that
tripped the first counterparty — and emitting those scenarios convicted the
Python REFERENCE itself of a real soundness bug: a forged lease echoing a
non-string register issuer was audit-clean (I5 evasion), and two mixed-type
deviant registers crashed the auditor outright. Fixed in ledger.py with the
pre-fix failure demonstrated against HEAD and a standing regression test
(`test_nonstring_issuer_cannot_authorize_leases`). Honest gaps: SPEC.md
still does not cover coalition records (exposure accounts, structure
judgements, widenings, pools); and every conformant implementation to date
shared an author — a genuinely separate implementer is the stronger form,
still owed.

**L2 — The running accountant.** The premier-type-surface verdict, now the
build order: a session monitor + **graded charge algebra** (below) +
refinement checks over the court file. Every release gate is the conjunction
of the numeric accountant and the ordinal review — enforced at runtime, not
asserted in comments. Status: **BORN as `chambers/kernel/`
(`charge-kernel/2`)** — one key-generic integer-millibit accountant (the SPEC
decision core, replays all 31 golden traces bit-for-bit), a content-addressed
grow-only event ledger with **CRDT merge** (union by sha256 id; idempotent,
commutative, associative fold; jsonl wire format), a **lease layer** that
enforces the global ceiling across nodes *by partition, not consensus*
(issuer refuses to grant past the ceiling ⟹ Σ accepted debits ≤ ceiling under
any interleaving, zero charge-time coordination), an `audit()` with eight
invariant families (forged over-spend, foreign-lease spend, post-expiry
charges, registration poison, equivocation, malformed facts), and a
`MediationSession` that charges **observation** (agent-as-reader across the
tuple) and **emission** (requester-as-reader against every member,
ATOMICALLY — all accounts accept or none is debited; the emission is not
separable from its inputs, in both directions). /2 hardened /1's six holes:
fact identity (`charge_seq` — no dedup undercount), honest lease resumption
across restarts, atomic emission, total fold under poison registrations,
negative-millibit boundary validation, and node/expiry/issuer authority
edges. No float in any decision path. See `chambers/kernel/PROTOCOL.md`.
The kernel is now METERING REAL WEDGES: `meter.py` (KernelMeter) is the
single-node front-end running the full distributive path — register →
self-lease → seq'd charge events — so a sim run and a distributed deployment
produce the same auditable jsonl artifact; there is one accounting path, not
a "lite" one for sims. `d1_bounty/egress.py`, `intro_clearing`,
`ip_trade_sim/leakage.py`, and the chamber wedge (private) all charge through it (floats
confined to the attested-estimator boundary with a documented rounding rule;
every run emits a mergeable ledger a stranger re-audits), exercised
end-to-end by their run scripts/tests. The kernel is now the only meter:
four of four sims, no remaining float-charging surface.
And the ledger now carries the ECONOMY, not just the meter:
`charge-settlement/1` (`kernel/SETTLEMENT-SPEC.md`, `settlement.py`) puts
value in the same artifact under the same discipline — integer
microcredits, no minting (deposits are declared boundary facts; pricing is
the value-side analog of estimation), a partition-authority
`SettlementIssuer` that refuses live what S1–S7 convict after merge, and
the binding law that is the whole point: **a release references the exact
charge events it pays for and is convicted if they are absent, refused,
off-key, or if the court touching the escrow's metered accounts is dirty**
(unknown future audit codes fail closed — value never outruns the audit's
vocabulary; dirt on unrelated keys does not block). Conservation
(Σ available + Σ escrow remainders = Σ deposits) is arithmetic for any
event set, proven in Lean for honest interleavings (`Settlement.lean`,
with an executable counterexample showing the guards are load-bearing),
asserted on forged soups in the tests, and — since the 2026-07-06 fable
review convicted BOTH implementations of folding escrow amounts on uint
alone (a forged null-payer escrow minted value with a clean audit) —
pinned as adversarial corpus scenarios that the reference and the Rust
port reproduce bit-for-bit (the `soup-*` family: paired quantities move
all-or-nothing, every total surface returns, every crime named) — and,
as of 2026-07-08, PROVEN OVER RAW SOUPS (`RawConservation.lean`): the
event model carries Option-typed adversarial fields (`none` IS the
forged field), the §2 all-or-nothing fold conserves for any raw soup
hypothesis-free (`raw_conservation_canonical`), the PRE-FIX fold is
proven broken on the F1 soup by `decide` (`f1_prefix_breaks`: 1999 ≠
1000 — the gate is necessary, not decorative), and S6's payer/payee arm
is complete and sound over the same model (`s6_gate_complete`: the
gating never silently launders value). Had this file existed on
2026-07-05, F1 could not have shipped — the model can no longer assume
the bug away.
`charge-settlement/2` (SPEC Part II, shipped 2026-07-06) extends the law
to CONTINGENT OUTCOMES — the $5-if-they-talk tier (G1/E1): an escrow may
declare a bonded, independence-classed outcome condition; release then
also requires a quorum of hardened, uncontested `outcome_attestation`
events referenced by id like work receipts (S9); attestor bonds are
locked by the fold itself, join the conservation identity (+ Σ bond
remainders; Lean extended, same axiom guard), return after an
uncontested window, and are slashed to the harmed party only under
STRICTLY better evidence (platform log over bonded ruling, S10) —
equal-lane contest blocks payment but slashes nobody: contested is not
convicted. Counterfactual metrics are REFUSED (no lane can express one);
outcome conditions size payments and never gate disclosure; anti-holdup
survives in both directions (unattested expiry refunds the payer; a
quorum-holding payee defaults to release against a silent issuer).
Golden corpus: `settlement2_traces/`, 17 scenarios (13 honest/Byzantine
+ 3 adversarial soups + the G19 named-override-referent court) — the /2
counterparty target; the /1 corpus stays frozen. The end-to-end wedge exists:
`kernel/demo_work_economy.py` — deposit → escrow → metered mediation →
atomic emission → release against the work receipt → refund — one
16-event jsonl artifact that the Python verifier
(`python3 -m chambers.kernel.verify`: both layers + conservation) and
the independent Rust verifier (`rust_ledger`'s `charge-verify`: both
layers — the settlement port landed 2026-07-06, 30/30 corpus cases
bit-for-bit) both pass CLEAN, and that
convicts itself when one payment byte is tampered. Value moves iff
metered work moved. And the protocol now has its MINIMUM REAL ENDPOINT:
`chamber-node/1` (`kernel/node.py`, stdlib only) — POST /v1/events plus
ledger/fold/audit/settlement/verify views — whose write endpoint is OPEN
because the security model is the theorem list, not an auth layer:
content-addressed identity makes facts unforgeable-without-bytes and
replay a no-op; total folds make hostile facts convict instead of
corrupt; verdicts only escalate; value fails closed. Replication is
`Ledger.merge` of state files — no consensus, the state is a grow-only
set. Exercised over real HTTP (honest artifact clean end-to-end;
Byzantine fact admitted AND convicted with the node healthy; garbage
refused stateless; restart + concurrent-writer merge-on-persist; 12
racing POSTs land as the exact union). Named non-protections: spam/disk,
read privacy (point it at courts, not secrets), availability.

**L3 — Adversarial/empirical.** Audit the accountant: estimated-ε probes
against our own gates (tight-auditing lineage, atlas 2 §8), the paired-silo
egress harness, red-team games against pools and judgement stores. An
estimate that cannot be attacked is not an estimate. Status: PARTIAL
(a private egress harness exists; `kernel/test_fuzz_audit.py` is a standing
detector-completeness lane — seeded honest multi-node deployments must audit
clean and fourteen Byzantine mutation classes must each be convicted with
the expected I-code, shuffle-merge invariant. A SECOND lane now attacks the
estimator itself — `d1_bounty/estimator_probe.py` builds a steganographic
encoder/decoder that smuggles a known secret through each metered channel
(enum, ordering via Lehmer code, raw-byte repro, plus an amortized
arithmetic-coding adversary) at the channel's physical maximum and measures
achieved vs charged bits: over 1472 emissions the meter is sound
(achieved ≤ charged) and tight (worst-case ratio 1.0), and the probe is
verified LIVE — a deliberately halved estimator is convicted. It also makes
the honest limit executable: an UNMODELED channel carries recoverable bits
at ZERO charge (uncharged capacity, named not fixed). Still open: an
estimated-ε probe lane against ε/Rényi mechanisms, and red-team games
against pools and judgement stores).

**L4 — Formal kernel (Lean).** Not the stack — the ~300 lines where wrongness
is catastrophic and proof is tractable:

1. The **charge algebra**: an indexed ordered semiring of leakage charges.
   Laws to prove: monotonicity (more observation never charges less),
   sequential sub-additivity (the surrogate upper-bounds composition),
   parallel join, **zero at self-leakage** (the coalition zero-point),
   and that the implementation's fold is a homomorphism into it.
2. The **odometer lemma** re-keyed: the pay-as-you-go filter argument
   (Rogers et al. / Feldman–Zrnic) restated over (source, reader) accounts —
   cumulative charged bits are monotone and cap-respecting under adaptive
   composition across coalitions.
3. **Widening one-way-ness**: no sequence of ledger operations returns a
   derivative to a narrower audience; confinement is not re-establishable.
4. **Tuple-scope soundness**: judgement visibility never exceeds the
   generating tuple without a WideningEvent in the trace.

Method: lean-formal-feedback-loop — Lean theorems paired with the
Python/TS reference; any divergence is a bug in one of them, found before a
user finds it. Status: **SEED BORN as `chambers/lean/`** — Lean 4, no
mathlib (trusted base = the Lean kernel itself), axiom-purity ENFORCED by
build-time guards (`propext`/`Quot.sound` only, guard shown to go red on a
flipped expectation). Proven: the per-account odometer laws (cumulative ≤
ceiling over any charge sequence; cumulative = Σ accepted debits exactly),
the **global cap under ANY interleaving** at trace level (the lease-partition
theorem — the /2 claim with its real quantifier), and the monotone-escalation
laws that license the CRDT merge story (class only escalates under more
leakage / lower entropy; merge never lowers class; incident never un-fires),
and now **widening one-way-ness and tuple-scope soundness** (targets 3 and 4)
via `Widening.lean`'s audience-provenance theorem — an exact equality: final
audience = birth audience ++ readers admitted by named widenings, over ANY
operation trace. One-way-ness, unrevokable confinement, and
visibility-stays-the-tuple are corollaries; `coalition.ts`'s `oneWay: true`
field is a theorem there, not a flag. Target 1's fold-homomorphism half is
now proven in `Algebra.lean` — the indexed charge algebra (pointwise ordered
commutative monoid over (source, reader) keys) with the coalition zero-point
(`SelfFree`: zero at self-leakage, closed under addition, downward closed),
and `fold_append`: the ledger fold maps CRDT merge of disjoint fact sets to
algebra addition EXACTLY — merging ledgers and adding charges are the same
operation. The module is AXIOM-FREE (guards pin "does not depend on any
axioms"). SPEC §4's worked example, a widening trace, and a fold-merge
example replay by `rfl`, binding model to normative text.
Model-code correspondence is now MECHANICAL at the trace level:
`kernel/emit_lean_traces.py` runs a 14-scenario battery (every SPEC §2.2
branch and boundary) through the real accountant.py and transcribes the
observed per-step verdicts and final states into `GoldenTraces.lean`,
replayed by `rfl` — Python drift goes red in pytest (byte-identical
re-emission pinned), model drift goes red in `lake build` (shown live on a
corrupted golden value). Honest limits (see `lean/README.md`): the binding
covers the golden battery, not all inputs (the full-function correspondence
proof is the stronger still-owed form); Byzantine nodes are deliberately
out of model (the audit's job);
Widening.lean proves the algebra has one door, not that every deployed
disclosure path routes through the algebra (L1–L3's job); Algebra.lean's
sub-additivity non-claim is deliberate (whether an attested estimate
upper-bounds real composed information is the ESTIMATOR's property — L3's
probe — not an algebra theorem); the remaining targets (the ordered-semiring
multiplicative structure if one is ever needed, and the adaptive-composition
odometer) are not yet formalized.
FRAMEWORKS F3 now has its first tranche: `Completeness.lean` models the
AUDIT over abstract ADVERSARIAL event soups — arbitrary event sets, not
honest-op reachable states, the lift the seed had avoided — and proves
CONVICTION-COMPLETENESS law by law, each with its soundness converse (no
false convictions) under the same propext/Quot.sound guard: any soup in
which an escrow is over-disbursed yields an S2 finding naming exactly that
escrow, and via the escrow event its issuer (`s2_complete`, `s2_sound`,
`s2_dangling_complete` for the unknown-escrow arm, `s2_convicts_issuer` —
the F3 sentence verbatim); any soup driving an account's signed available
below zero yields an S1 naming the account, quantified over ALL account
strings because occurrence in the audit's range is DERIVED from the crime
(overdraft ⟹ positive lock-out ⟹ an escrow naming the payer)
(`s1_complete`, `s1_sound`); and any two events with distinct ids claiming
one (actor, kind, seq) yield an X0 naming the triple, whatever their kinds
(`x0_complete`, `x0_sound`). Honest micro-artifacts acquit and forged ones
convict by `rfl`. Open, stated not claimed: completeness for S3/S4/S7/S8
(their predicates drag in the full I-code court) and S9/S10 (outcome
attestations).
The F3 campaign's SECOND tranche (2026-07-09,
`ProvenanceCompleteness.lean`): the P1 arm is conviction-complete and
sound over adversarial soups — any derivation chain from an emitted fact
to an anchored, uncoupled source forces a P1 naming that source
(`p1_complete`), every P1 carries a chain witness back (`p1_sound`), and
the capstone `closure_saturates` proves the fueled walk reaches its
fixpoint at fuel soup.length via pigeonhole loop-cutting
(`chain_prune`, `headsChain_cut` — the latter axiom-FREE): cycles and
depth buy the adversary nothing. "Depth is not dilution" is now a
quantifier, not a test. Named open: P2 (the max-flow bound), P3, the
V-family, and the (node, tick, channel) grouping, all owned by the
Python audit and its lanes.
And the SPLIT RULE now conserves by theorem (`Attribution.lean`,
charge-attribution/1 / FRAMEWORKS F6, shipped 2026-07-08): the
largest-remainder allocation that divides a pot across a derived fact's
sources neither mints nor burns a microcredit, for EVERY tie-break rule an
implementation could choose (`alloc_conserves`); the shortfall equals the
remainder pile stated multiplicatively — no division in the statement, so
no rounding can hide in it (`shortfall_exact`, `shortfall_lt`); prefix
marginals telescope to exactly the grand coalition's worth for any
coalition-value function and any ordering (`walk_efficiency`); and the
floor-only rule is proven leaky by `decide`, axiom-free
(`floor_only_leaks` — the remainder arm is load-bearing, the negative in
the `f1_prefix_breaks` tradition). Named, not papered over: the
subset-weight ↔ permutation-walk Shapley identity is property-tested
exactly for n ≤ 5 (`test_attribution.py`), not machine-proven; max-flow
arithmetic stays the P-audit's. This is the answer to "do we work in
THE VERDICT PARTITION THEOREM (`VerdictPartition.lean`, 2026-07-09) —
the master law of Byzantine merge at the VERDICT level, the altitude the
registers had only claimed informally. The naive law "verdicts only grow
under union" is FALSE and the file proves it (`s1_retracts_example`);
the true law is a partition plus a characterization: **adding evidence
never erases a crime whose evidence is already present; it can only
complete a gap — and each retractable code retracts only by supplying
its named missing fact.** Permanence for the evidence-backed codes
(`x0_permanent`, `s2_overdisburse_permanent` — UNCONDITIONAL, the
duplicate-id trap dissolved because the audit is per-event, exhibit
pinned — and `s6_permanent` via audit-of-union = union-of-audits).
Characterized retraction for the gap codes: `s1_retraction_is_completion`
(S1 clears only when A supplies a positive fund fact crediting the exact
convicted account — deposit, inbound-release pair, or inbound-refund
pair; the deposit-only reading is machine-checked FALSE,
`s1_retracts_without_deposit` — the proof WIDENED the law honestly);
`s2_retraction_is_completion` (the dangling arm dies only via the exact
named escrow id). Audit membership is merge-order-insensitive; the
escalation laws (class never drops, incident never un-latches) are now
stated AT THE SOUP LEVEL, composed with Monotone.lean; min-resolution is
antitone as a relation. 63 theorems/examples, all guard-listed (64
guards total), zero sorries. Named open: partition classes for
S3/S7/S8/S9/S10 (conjectured retractable-by-completion) and the raw
Option-typed restatement of S1. What this buys operationally: no
adversary can compose a court into un-convicting itself except by
honestly completing it — the CRDT story's safety claim is now a
quantified sentence, not an analogy.
THE VALUE-GATE COROLLARY (`ValueGate.lean`, 2026-07-09, same day) —
the theorem the partition campaign aimed at, CLOSED: **no adversary can
talk value out of a dirty court by adding events.** A required_clean
release convicted against a dirty court clears ONLY when every finding
touching its escrow's keys retracts by supplying its named missing fact
(`s4_value_gate` — the partition lemmas invoked as terms, re-proving
nothing), and against a PERMANENT conviction touching its keys the
release is convicted FOREVER (`s4_permanent_against_permanent`).
S4 modeled with implementation fidelity, and the fidelity work WAS the
finding: settlement.py's dirty stream is `_court_findings` (I/C/P/V
codes — the settlement S-codes are not in it), the clean-court check is
SET-SHAPED (computed once over the final ledger; `s4Audit_mem_swap`
pins merge-order-blindness as a theorem), the modeled touch arm is the
key-subject identity arm (I1/I2/I7/C2/P1/P2's shape — exactly what the
S4 corpus row exercises), and X0 is OUT of S4's range on three
implementation grounds, each named. `s4_sound`/`s4_complete` in the F3
sentence shape; examples both directions by decide — including the
honest-completion witness where the named ghost escrow arrives, the
release clears, and the court STAYS dirty on an untouched key (touch
precision pinned). 73 guards total now, propext/Quot.sound only, zero
sorries, 363 green. Named open: the lease-id/charge-id/I8/V touch arms
and the unknown-code fail-closed default (Python's surface), S4 over
the raw Option-typed model, the corpus binding (the row convicts
through an I-code the model does not carry). The three-theorem arc of
the calculus program now reads: monotonicity PROVEN → partition PROVEN
→ value-gate PROVEN; the remaining pole is the g-leakage soundness
bridge (L5's research program, F1/G2).
Lean": yes, scoped exactly here, never as a substitute for L1–L3.

**L5 — The social layer, priced not proven.** Identity/Sybil (frontier #1),
the human-head channel (#7), reader models declared-not-observed (#18), pool
sets empirical-not-mechanical (#19), TCB trust (#6). These CANNOT enter the
proof; the assurance case states them as standing non-claims with
mitigations and prices. Solved-ness includes *saying so* — that discipline is
itself the product. CONTACT HAS BEGUN: the operator's private dogfood log is the L5
evidence file — evidence from real runs only. The chamber wedge has served a real released
answer end-to-end (real Codex worker over the real repo, dual review,
kernel-metered: one diligence answer = 11.74M mbits = half a passcode
holder's lifetime exposure budget), and a real timed-out run that
FAILED CLOSED with an auditable court file and a 2-bit requester cost.
Reality filed protocol-grade bugs no sim or proof caught (run-scoped
accumulation hole; last-writer-wins persist) — both fixed same-day with
the kernel's own primitives (pair-lifetime account; CRDT merge-on-persist).

## The calculus decision (yes, and it already has a shape)

We do need a special calculus for information leakage, and it is small: one
**indexed charge algebra**, three instantiations.

- Carrier: charges `c` in an ordered commutative monoid with a cap order;
  indexed by (source silo, reader entity, reader-model confidence).
- Operations: `⊕` sequential composition (adds, or Rényi-composes),
  `⊔` parallel join, `0` = self-leakage, `⊤` = block.
- Instantiations: (1) capacity bits (schema/enum/ordering — decidable,
  adversarial-max), (2) ε/Rényi (mechanism noise — composable), (3) QIF
  g-leakage / pointwise maximal leakage (adversarial gain — operational).
- The ledger is the free module over this algebra; the court file is its
  trace; L2 implements it once (~200 lines), L4 proves its laws.

Do NOT invent a grand unified leakage theory. The Book version is the small
algebra with three honest instantiations and named estimators. Everything
fancier is a paper, not a kernel.

## The trust equation (how users say "yep, upload")

Users do not upload because of proofs. They upload because of:

1. **Small first asks** — one repo, one purpose, one wedge (intro clearing,
   bounty triage), revocable.
2. **Receipts** — after every run, a court file a stranger can check:
   what ran, what left, in whose direction, at what charge. No incumbent
   shows this. This is the visible artifact of L1–L2.
3. **The exposure surface** — "who can infer what about me, cumulatively, in
   bits" as a user-facing page. The (source × reader) ledger IS the moat:
   accounting compounds, and honesty cannot be retrofitted by platforms
   whose business is the leak.
4. **Cards, not corpora** — canonicality-reviewed agents, attention laws,
   autonomy envelopes. The user reads four lines and a price.

## Build order (fast, without lying)

1. Extend `conformance/SPEC.md` to coalition + mediation records; court
   files gain ExposureAccount / StructureJudgement / WideningEvent /
   PoolDisbursement lines. (L1 — KERNEL-SPEC.md now covers coupled
   mediation charges at the ledger layer; coalition records still open)
2. Extract the charge algebra into one shared kernel used by the chamber wedge (private),
   ip_trade_sim, d1_bounty, intro_clearing. (L2 — DONE for all four via
   KernelMeter; the chamber wedge was the last migration)
3. Lean kernel: algebra laws + odometer lemma + one-way widening. (L4 —
   odometer + global cap + monotone laws + widening one-way-ness +
   tuple-scope soundness + the fold homomorphism with the coalition
   zero-point all proven; the adaptive-composition form still open)
4. Audit lane: estimated-ε probes as a standing CI job against the gates.
   (L3 — the Byzantine fuzz-audit lane and the adversarial estimator-
   soundness probe both stand; estimated-ε probes still open)
5. Wedges to design partners: D1 bounty (committed decision) and intro
   clearing v2 with pool-cleared pricing + tuple judgement store. (L5 contact
   with reality)

Fleet discipline: canon and review stay with the lead; sims and conformance
extensions parallelize across workers on disjoint files; archive freely — a wedge
that doesn't survive contact goes to `archive/` with its lessons, not into
the spine.
