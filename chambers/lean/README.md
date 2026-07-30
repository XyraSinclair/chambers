# ChargeKernel — the L4 formal kernel (Lean 4)

The ~300 lines of `charge-kernel/2` where wrongness is catastrophic and
proof is tractable (ASSURANCE.md L4), machine-checked. Lean 4.26, **no
mathlib** — core tactics only (`omega`, `simp`, structural induction), so
the build is seconds and the trusted base is the Lean kernel itself.

```
lake build          # from this directory (elan picks the pinned toolchain)
```

## What is proven

**Basic.lean** — the SPEC §2.2 step function (A–E), modeled with Nat
arithmetic (truncated subtraction = the SPEC's `max 0 (…)`).

- `run_cumulative_le_ceiling` — the odometer law: over ANY charge sequence,
  accepted leakage never passes the ceiling.
- `run_cumulative_eq_accepted` — exactness: cumulative is precisely the sum
  of accepted debits (the fold IS the meter; no bit appears or vanishes).
- `acceptedBits_le_ceiling` — premise (2) of the global cap theorem, proven.
- Frame + monotonicity lemmas (entropy/ceiling never move; counters never
  decrease).

**GlobalCap.lean** — the lease-partition theorem at trace level, which is
where the actual claim lives ("under ANY interleaving, zero coordination"):

- `global_cap` — a system of independent per-lease accountants, an
  arbitrary schedule of (node, charge) steps in arbitrary order: if
  ceilings sum ≤ C at the start, cumulative debits sum ≤ C after every
  schedule.
- `global_cap_fresh` — the deployment form: fresh accountants over granted
  lease amounts; the issuer's refusal to over-grant arrives as
  `Σ amounts ≤ C`.

**Monotone.lean** — the laws the CRDT merge story rests on:

- `rank_eq_spec` — the counting form of the leakage class equals SPEC §1.5's
  ordered-branch form (the theorems bind to the normative definition).
- `rank_mono_cumulative`, `rank_antitone_entropy` — class only escalates
  with more leakage or lower declared entropy. The antitone law is what
  licenses `ledger.py`'s minimum-resolution quarantine of conflicting
  registrations: resolving DOWN can only escalate.
- `merge_escalates`, `incident_mono` — a superset of debit facts never
  lowers the class; the incident latch cannot un-fire under merge.

**Widening.lean** — audience provenance and the one-way door (ASSURANCE L4
targets 3 and 4), mirroring `coalition.ts`: a derivative is born with
`audience = generating coalition`, and `widen` (the WideningEvent) is the
only audience-touching constructor in the visibility op algebra — its
`oneWay: true` field is here a theorem, not a flag.

- `audience_provenance` — the headline, an exact EQUALITY: final audience =
  birth audience ++ readers admitted by the trace's widenings. No other
  door exists in the algebra; nothing removes a reader.
- `audience_never_narrower` — widening one-way-ness: no sequence of ledger
  operations returns a derivative to a narrower audience.
- `confinement_not_reestablishable` — a reader once admitted is in every
  subsequent audience.
- `tuple_scope_sound` — over any widening-free trace, visibility stays
  exactly the generating tuple.
- `escape_names_widening` — constructive contrapositive: a reader outside
  the tuple who can see the derivative was admitted by a widening the
  trace names.

**Algebra.lean** — the indexed charge algebra and the fold homomorphism
(ASSURANCE L4 target 1, the fold-homomorphism half). `ChargeVec` = charge
vectors indexed by (source, reader), pointwise ordered commutative monoid;
`SelfFree` = the coalition zero-point (zero at self-leakage), proven closed
under addition and downward closed. The headline is `fold_append`: the
ledger fold maps CRDT merge of disjoint fact sets to algebra addition,
EXACTLY — merging ledgers and adding charges are the same operation seen
twice. `fold_sublist_le` is merge-only-escalates in algebra form;
`fold_selfFree` shows a ledger with no self-pair facts folds into the
zero-point. The whole module is AXIOM-FREE (guards pin "does not depend on
any axioms"). Honest scope in the module header: sequential sub-additivity
of real information is an estimator property (L3's probe), not an algebra
theorem; idempotent dedup is the content-addressing layer's job (L1).

**Settlement.lean** — conservation for `charge-settlement/1+2`
(SETTLEMENT-SPEC §4, Part II §8): under ANY interleaving of guarded honest
ops (deposit, escrow, release, refund, bond lock/return/slash),
Σ available + Σ escrow remainders + Σ bond remainders = Σ deposits
(`runSettle_conserves`, `conservation_from_genesis`), with executable
`decide` counterexamples showing the guards are load-bearing (an unguarded
lock manufactures microcredits from Nat truncation).

**Completeness.lean** — conviction-completeness of the AUDIT over abstract
ADVERSARIAL event soups (FRAMEWORKS F3): the lift the seed deliberately
avoided — theorems over arbitrary event sets, not honest-op reachable
states. The audit is a total executable Lean function mirroring
`settlement.py audit_settlement_findings` (S1/S2 arms) and `ledger.py
substrate_findings` (X0), and:

- `s2_complete` / `s2_sound` — ANY soup in which an escrow has
  released + refunded > amount yields an S2 finding naming exactly that
  escrow; every S2 finding convicts a real crime. `s2_dangling_complete`
  covers the unknown-escrow arm; `s2_convicts_issuer` is the F3 sentence
  verbatim (the named escrow event, in the soup, names its issuer).
- `s1_complete` / `s1_sound` — available(a) < 0 (signed) yields an S1
  naming the account, quantified over ALL account strings: the audit only
  enumerates occurring accounts, and occurrence is DERIVED from the crime
  (overdraft ⟹ positive lock-out ⟹ an escrow naming `a` as payer).
- `x0_complete` / `x0_sound` — two events with distinct ids claiming one
  (actor, kind, seq) yield an X0 naming the triple, whatever their kinds.
- Executable micro-artifacts replay by `rfl`: honest soup acquitted, one
  forged release byte convicted, ghost-escrow release self-convicted,
  same-id replay NOT an equivocation.

Open (stated, not claimed): completeness for S3/S4/S7/S8 (work receipts,
clean court, expiry — their predicates drag in the full I-code court) and
S9/S10 (outcome attestations).

**RawConservation.lean** — the 2026-07-06 F1 fix as law: SETTLEMENT-SPEC
§2's "paired quantities move all-or-nothing" gating over a RAW event model
that assumes NO well-typedness (`Option`-typed parties and amounts — `none`
IS the forged field, the exact adversarial surface F1 used).

- `raw_conservation` / `raw_conservation_canonical` — the conservation
  identity Σ available + Σ remaining = Σ deposits holds for ANY raw soup
  whatsoever, given the §2 gates (escrow amount enters remainder AND
  locked_out only when amount is uint AND payer is a string; a
  disbursement counts only when the credited party is a string).
- `f1_prefix_breaks` — the sharp negative that proves the gate necessary:
  the PRE-FIX fold (uint gate alone) on the F1 forgery soup (deposit 1000
  + escrow amount=999, payer=none) yields 1999 ≠ 1000 by `decide`, while
  the fixed fold on the same soup conserves.
- `s6_complete` / `s6_gate_complete` / `s6_sound` — the S6 payer/payee arm:
  non-string-party escrows are convicted by name, anything the gate zeroes
  is convicted (value is never laundered away silently), and only
  actually-malformed escrows convict. Scope: just that arm — the other S6
  arms are the Python/Rust audits' and the battery's.
- Golden bindings by `decide`: the F1 soup (conserves AND convicts), its
  release-mirror (non-string payee + release: the release credits nobody,
  burns nothing), and an honest soup (no convictions, 400/400/200).
- Axiom guards live in the module itself (same `#guard_msgs` discipline as
  the root file).

**ProvenanceCompleteness.lean** — conviction-completeness of the P1 arm
(charge-provenance/1) over adversarial soups: FRAMEWORKS F3, tranche 2.
"Depth is not dilution" as a quantifier, not a test.

- `p1_complete` / `p1_sound` — any soup containing a derivation chain
  from the emitted fact to an anchor of an uncoupled source yields a P1
  naming that source, at the chain's own fuel; every P1 carries a chain
  witness back to a real anchor. Chains are an inductive spec
  (`ChainN`); the walk is fueled expansion, proven monotone,
  compositional (`expandN_add`), and complete/sound for chains.
- `closure_saturates` / `p1_complete_saturated` — the capstone: fuel
  `soup.length` reaches the closure FIXPOINT. Any chain prunes to one
  no longer than the soup (`chain_prune`): every walked head is the
  derived fact of a soup event, so a longer chain revisits a head
  (pigeonhole, `nodup_subset_length` — with a local choice-free
  `remove1` because core's `erase` lemmas carry `Classical.choice`)
  and the loop cuts out (`headsChain_cut`, axiom-FREE). Cycles are
  legal adversarial content and buy the adversary nothing.
- Executable micro-artifacts by `decide`: the three-hop laundering soup
  convicts, the honest coupling acquits, a derivation cycle terminates
  and convicts exactly its real source.
- Scope: one (emission, reader) instance per theorem — the
  (node, tick, channel) grouping is the Python audit's; P2 (max-flow),
  P3, and the V-family are named open obligations.

**Attribution.lean** — charge-attribution/1's split rule (ATTRIBUTION-SPEC
V.3; FRAMEWORKS F6): the value analog of raw conservation — a pot divided
among a derived fact's sources neither mints nor burns a microcredit.

- `alloc_conserves` (with `floors_le`, `shortfall_exact`, `shortfall_lt`)
  — largest-remainder allocation conserves the pot exactly, for EVERY
  bonus tie-break rule an implementation could choose; the shortfall
  equals the remainder pile stated multiplicatively (D·k = Σ rems — no
  division in the statement, so no rounding hides in it) and is strictly
  under n, so the bonus always fits.
- `walk_efficiency` / `walk_telescopes` — the Shapley decomposition's
  efficiency arm: prefix marginals telescope to exactly v(order) − v(∅)
  for ANY coalition-value function and ANY ordering.
- `floor_only_leaks` — the sharp negative (axiom-FREE, by `decide`):
  floors without the remainder arm lose a microcredit on [1,1,1] at pot
  10000. The remainder rule is load-bearing.
- Executable bindings by `rfl`/`decide`: the alpha story's arithmetic
  (numerators (2, 15998)/16000 on a 10^14 pot pay exactly
  12_500_000_000 — the 1/8000 contributor's $12,500).
- Scope: v enters as an arbitrary function (max-flow arithmetic is the
  Python/Rust P-audit's); the subset-weight ↔ permutation-walk identity
  is property-tested in `test_attribution.py`, not proven here.

**VerdictPartition.lean** — the master law of Byzantine merge at the
VERDICT level, over Completeness.lean's adversarial soups: adding evidence
never erases a crime whose evidence is present, and each retractable code
retracts ONLY by supplying its named missing fact. Permanence:
`x0_permanent`, `s2_overdisburse_permanent` (per-event, so duplicate-id
forgeries move nothing), `s6_permanent`. Characterized retraction:
`s1_retraction_is_completion` (an overdraft clears only by a genuinely new
credit — deposit, inbound release, or inbound refund, each named),
`s2_retraction_is_completion` (a dangling reference clears only by the
exact named escrow arriving). Plus `settleAudit_mem_swap`/`x0Audit_mem_swap`
(merge-order-blind membership) and the soup-level fold glue
(`class_escalates_over_soups`, `incident_escalates_over_soups`). Honest
witnesses for BOTH directions replay by `decide`.

**ValueGate.lean** — the value-gate corollary: S4 inherits the partition.
The S4 arm (release against a `required_clean` escrow whose keys touch a
dirty court) is modeled SET-SHAPED, mirroring `settlement.py`'s one-shot
`_court_findings` check, over the model's own court (S1/S2 — the honest
slice; the real I/C/P/V dirty stream is the Python audit's surface, named
NOT-claimed). `s4_sound`/`s4_complete`/`s4Audit_mem_swap`, then the
headline pair: `s4_value_gate` — a convicted release clears ONLY when
every touching finding retracts via its named filler (the partition
theorems invoked, not re-proven) — and `s4_permanent_against_permanent` —
against an over-disbursed escrow among its keys, the release is convicted
in E ++ A for ALL A. Both directions witnessed by `decide`, including the
universal no-extension-clears instantiation.

**GoldenTraces.lean** — GENERATED by `kernel/emit_lean_traces.py`: the
observed behavior of the Python reference on a 14-scenario battery
(per-step verdicts via `runReasons` + final accounts), replayed by `rfl`.
The mechanical model↔code binding; see Honest limits.

**ChargeKernel.lean** (root) — the executable binding to the documents:
SPEC §4's worked micro-example and three edge cases replay by `rfl`, plus a
widening trace (charge → widen → project → charge) whose audience is
exactly birth ++ widened. If the model and the normative text ever diverge,
this file stops compiling.

## Axioms

Every headline theorem depends only on `propext` and `Quot.sound` (the
Widening module needs only `propext`, the Algebra module no axioms at
all): no `Classical.choice`, no `sorryAx`. This is ENFORCED at build time
— `ChargeKernel.lean` ends with `#guard_msgs in #print axioms` guards for
every headline theorem, so an axiom creeping into any proof stops the
build (verified to go red on a deliberately flipped expectation).

## Honest limits

- **Model-code correspondence is now MECHANICAL at the trace level.**
  `kernel/emit_lean_traces.py` runs a deterministic scenario battery
  (every SPEC §2.2 branch and boundary: exact-remaining latch, incident at
  the exact threshold, zero ceilings, interleaved inadmissibles) through
  the REAL `accountant.py` and transcribes the observed per-step verdicts
  and final states into `GoldenTraces.lean`, where all 14 traces replay by
  `rfl`. Python drift goes red in pytest (byte-identical re-emission
  pinned); model drift goes red in `lake build` (shown live on a corrupted
  golden value). Remaining gap: the binding covers the golden battery, not
  all inputs — the full-function correspondence proof (a verified
  extraction or a bisimulation argument) is the stronger form, still owed.
- **Byzantine nodes are out of the HONEST-OP models** — deliberately.
  `stepAt` and `settleStep` only model honest accountants/issuers; a node
  that fabricates events is the audit's problem (KERNEL-SPEC.md I1–I8,
  SETTLEMENT-SPEC S1–S10). `Completeness.lean` now takes the audit's side
  of that division for S1/S2/X0: the audit is proven conviction-complete
  and sound over ARBITRARY adversarial soups; `VerdictPartition.lean` adds
  the merge law for those codes and `ValueGate.lean` the S4 gate law over
  the model's court. Completeness for the remaining arms (S3, S4's full
  I/C/P/V court range, S7/S8/S9–S12) is open and named in each module.
- **Widening.lean proves the ALGEBRA has one door**, not that the deployed
  system's every disclosure path routes through the algebra — that is
  L1–L3's job (conformance, fuzz-audit, estimator probes). A model with a
  hidden second door would be a modeling bug, which is why the op algebra
  is three constructors you can audit by eye against `coalition.ts`.
- The remaining L4 targets (charge-algebra homomorphism, odometer lemma
  over adaptive composition) are not yet formalized; this directory is the
  seed, scoped to the global cap + monotone-escalation + widening core.
