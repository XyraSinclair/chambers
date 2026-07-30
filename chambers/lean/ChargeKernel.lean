/-
ChargeKernel — the L4 formal kernel of charge-kernel/2 (ASSURANCE.md).

Not the stack: the ~300 lines where wrongness is catastrophic and proof is
tractable. Three files:

  Basic.lean     the SPEC §2.2 step function and per-account odometer laws
  GlobalCap.lean the lease-partition theorem under ANY interleaving
  Monotone.lean  leakage-class monotonicity and merge-only-escalates

The executable binding to the normative documents: SPEC §4's worked
micro-example replays below by `rfl` — if the model and the document ever
disagree, this file stops compiling.
-/
import ChargeKernel.Basic
import ChargeKernel.GlobalCap
import ChargeKernel.Monotone
import ChargeKernel.Settlement
import ChargeKernel.Widening
import ChargeKernel.GoldenTraces
import ChargeKernel.Algebra
import ChargeKernel.Completeness
import ChargeKernel.RawConservation
import ChargeKernel.Attribution
import ChargeKernel.ProvenanceCompleteness
import ChargeKernel.VerdictPartition
import ChargeKernel.ValueGate

namespace ChargeKernel

/-- SPEC §4 worked micro-example, charge 1: entropy 100000, ceiling
1000000, one admissible 80000-mbit charge. Expected: emitted, cumulative
80000, demanded 80000, incident latched (uncapped demand, ≥), not blocked. -/
example :
    step { entropy := 100000, ceiling := 1000000 } { admissible := true, bits := 80000 }
      = ({ entropy := 100000, ceiling := 1000000, cumulative := 80000,
           demanded := 80000, blocked := false, incident := true }, .emitted) := rfl

/-- SPEC §4, charge 2: incident already latched, cumulative 160000. -/
example :
    run { entropy := 100000, ceiling := 1000000 }
        [ { admissible := true, bits := 80000 }, { admissible := true, bits := 80000 } ]
      = { entropy := 100000, ceiling := 1000000, cumulative := 160000,
          demanded := 160000, blocked := false, incident := true } := rfl

/-- An exact-remaining emission is admitted and then blocks (SPEC step D
strictness + step E latch). -/
example :
    step { entropy := 100, ceiling := 50, cumulative := 20 } { admissible := true, bits := 30 }
      = ({ entropy := 100, ceiling := 50, cumulative := 50,
           demanded := 30, blocked := true, incident := false }, .emitted) := rfl

/-- An inadmissible estimator accrues nothing (step A). -/
example :
    step { entropy := 100, ceiling := 50 } { admissible := false, bits := 999 }
      = ({ entropy := 100, ceiling := 50 }, .refusedEstimator) := rfl

/-- Widening model, executable: a derivative born to coalition {A,B},
charged, widened to {C}, projected, charged again — the audience is exactly
birth ++ widened, the tuple never moves, and no op removed anyone. -/
example :
    applyTrace (Deriv.birth ["A", "B"])
        [ .charge 10, .widen ["C"], .project "A", .charge 5 ]
      = { tuple := ["A", "B"], audience := ["A", "B", "C"] } := rfl

/-
Axiom discipline, ENFORCED at build time (not asserted in a README): every
headline theorem depends only on `propext` and `Quot.sound` — no
`Classical.choice`, no `sorryAx`, no custom axioms. If a proof ever picks up
another axiom, these guards stop the build.
-/

/-- info: 'ChargeKernel.run_cumulative_le_ceiling' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms run_cumulative_le_ceiling

/-- info: 'ChargeKernel.run_cumulative_eq_accepted' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms run_cumulative_eq_accepted

/-- info: 'ChargeKernel.acceptedBits_le_ceiling' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms acceptedBits_le_ceiling

/-- info: 'ChargeKernel.global_cap' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms global_cap

/-- info: 'ChargeKernel.global_cap_fresh' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms global_cap_fresh

/-- info: 'ChargeKernel.rank_eq_spec' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms rank_eq_spec

/-- info: 'ChargeKernel.rank_mono_cumulative' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms rank_mono_cumulative

/-- info: 'ChargeKernel.rank_antitone_entropy' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms rank_antitone_entropy

/-- info: 'ChargeKernel.merge_escalates' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms merge_escalates

/-- info: 'ChargeKernel.incident_mono' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms incident_mono

/-- info: 'ChargeKernel.audience_provenance' depends on axioms: [propext] -/
#guard_msgs in #print axioms audience_provenance

/-- info: 'ChargeKernel.audience_never_narrower' depends on axioms: [propext] -/
#guard_msgs in #print axioms audience_never_narrower

/-- info: 'ChargeKernel.confinement_not_reestablishable' depends on axioms: [propext] -/
#guard_msgs in #print axioms confinement_not_reestablishable

/-- info: 'ChargeKernel.tuple_scope_sound' depends on axioms: [propext] -/
#guard_msgs in #print axioms tuple_scope_sound

/-- info: 'ChargeKernel.escape_names_widening' depends on axioms: [propext] -/
#guard_msgs in #print axioms escape_names_widening

/-- info: 'ChargeKernel.fold_append' does not depend on any axioms -/
#guard_msgs in #print axioms fold_append

/-- info: 'ChargeKernel.fold_sublist_le' does not depend on any axioms -/
#guard_msgs in #print axioms fold_sublist_le

/-- info: 'ChargeKernel.fold_selfFree' does not depend on any axioms -/
#guard_msgs in #print axioms fold_selfFree

/-- info: 'ChargeKernel.ChargeVec.selfFree_add' does not depend on any axioms -/
#guard_msgs in #print axioms ChargeVec.selfFree_add

/-- info: 'ChargeKernel.ChargeVec.selfFree_of_le' does not depend on any axioms -/
#guard_msgs in #print axioms ChargeVec.selfFree_of_le

/-- The fold homomorphism, executable: two disjoint ledgers (silo A charged
to reader R twice, silo B once) merge and fold to the pointwise sum. -/
example :
    fold ((([(("A", "R"), 30), (("A", "R"), 12)] : List (Fact String))
            ++ [(("B", "R"), 5)])) ("A", "R")
      = ChargeVec.add (fold [(("A", "R"), 30), (("A", "R"), 12)])
                      (fold [(("B", "R"), 5)]) ("A", "R") := rfl


/-- info: 'ChargeKernel.runSettle_conserves' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms runSettle_conserves

/-- info: 'ChargeKernel.conservation_from_genesis' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms conservation_from_genesis

/-
Completeness.lean (FRAMEWORKS F3): conviction-completeness of the audit
over ADVERSARIAL soups — any event set violating S2 / S1 / X0 contains a
finite witness the audit names — plus the soundness directions (no false
convictions). See that file's header for the laws still open (S3/S4/
S7/S8, S9/S10).
-/

/-- info: 'ChargeKernel.s2_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s2_complete

/-- info: 'ChargeKernel.s2_dangling_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s2_dangling_complete

/-- info: 'ChargeKernel.s2_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s2_sound

/-- info: 'ChargeKernel.s2_convicts_issuer' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s2_convicts_issuer

/-- info: 'ChargeKernel.s1_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s1_complete

/-- info: 'ChargeKernel.s1_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s1_sound

/-- info: 'ChargeKernel.x0_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms x0_complete

/-- info: 'ChargeKernel.x0_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms x0_sound

/-
Attribution.lean (FRAMEWORKS F6, charge-attribution/1): the split rule's
conservation — largest-remainder allocation conserves the pot for EVERY
tie-break, the shortfall is the remainder pile stated multiplicatively,
and walk-marginals telescope to exactly the grand coalition's worth. The
floor-only rule provably leaks (the sharp negative).
-/

/-- info: 'ChargeKernel.walk_efficiency' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms walk_efficiency

/-- info: 'ChargeKernel.alloc_conserves' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms alloc_conserves

/-- info: 'ChargeKernel.shortfall_exact' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms shortfall_exact

/-- info: 'ChargeKernel.shortfall_lt' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms shortfall_lt

/-- info: 'ChargeKernel.floor_only_leaks' does not depend on any axioms -/
#guard_msgs in #print axioms floor_only_leaks

/-
ProvenanceCompleteness.lean (FRAMEWORKS F3, tranche 2): conviction-
completeness of the P1 arm over adversarial soups — depth is not
dilution AS A QUANTIFIER. Any derivation chain to an uncoupled anchored
source convicts (p1_complete); the fixed fuel soup.length reaches the
closure fixpoint via pigeonhole loop-cutting, so cycles and depth buy
the adversary nothing (closure_saturates, p1_complete_saturated); and
only real ancestry convicts (p1_sound).
-/

/-- info: 'ChargeKernel.p1_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms p1_complete

/-- info: 'ChargeKernel.p1_complete_saturated' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms p1_complete_saturated

/-- info: 'ChargeKernel.p1_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms p1_sound

/-- info: 'ChargeKernel.closure_saturates' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms closure_saturates

/-- info: 'ChargeKernel.chain_prune' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms chain_prune

/-- info: 'ChargeKernel.headsChain_cut' does not depend on any axioms -/
#guard_msgs in #print axioms headsChain_cut

/-
VerdictPartition.lean: the verdict partition theorem — permanence for the
evidence-backed codes (X0 / S2 over-disbursement / S6), characterized
retraction for the gap codes (S1 clears only via a fund fact crediting
the account; S2's dangling arm clears only via the named missing escrow),
merge-order insensitivity of audit membership, and the soup-level
escalation glue onto Monotone.lean (class never drops, incident never
un-latches, under E ++ A). The retraction witnesses are machine-checked
in-file (non-vacuity in both directions).
-/

/-- info: 'ChargeKernel.x0_permanent' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms x0_permanent

/-- info: 'ChargeKernel.x0_permanent_prepend' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms x0_permanent_prepend

/-- info: 'ChargeKernel.s2_overdisburse_permanent' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s2_overdisburse_permanent

/-- info: 'ChargeKernel.s2_overdisburse_permanent_prepend' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s2_overdisburse_permanent_prepend

/-- info: 'ChargeKernel.s6_permanent' depends on axioms: [propext] -/
#guard_msgs in #print axioms s6_permanent

/-- info: 'ChargeKernel.s6_permanent_prepend' depends on axioms: [propext] -/
#guard_msgs in #print axioms s6_permanent_prepend

/-- info: 'ChargeKernel.s1_retraction_is_completion' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s1_retraction_is_completion

/-- info: 'ChargeKernel.s2_retraction_is_completion' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s2_retraction_is_completion

/-- info: 'ChargeKernel.available_append' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms available_append

/-- info: 'ChargeKernel.s1_clear_forces_credit' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s1_clear_forces_credit

/-- info: 'ChargeKernel.settleAudit_mem_swap' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms settleAudit_mem_swap

/-- info: 'ChargeKernel.x0Audit_mem_swap' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms x0Audit_mem_swap

/-- info: 'ChargeKernel.s1_retracts_example' depends on axioms: [propext] -/
#guard_msgs in #print axioms s1_retracts_example

/-- info: 'ChargeKernel.s1_retracts_without_deposit' depends on axioms: [propext] -/
#guard_msgs in #print axioms s1_retracts_without_deposit

/-- info: 'ChargeKernel.s2_dangling_retracts_example' depends on axioms: [propext] -/
#guard_msgs in #print axioms s2_dangling_retracts_example

/-- info: 'ChargeKernel.s2_per_event_duplicate_id' depends on axioms: [propext] -/
#guard_msgs in #print axioms s2_per_event_duplicate_id

/-- info: 'ChargeKernel.soup_sums_mono' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms soup_sums_mono

/-- info: 'ChargeKernel.resolution_antitone' depends on axioms: [propext] -/
#guard_msgs in #print axioms resolution_antitone

/-- info: 'ChargeKernel.resolution_exists' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms resolution_exists

/-- info: 'ChargeKernel.merge_never_lowers_class' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms merge_never_lowers_class

/-- info: 'ChargeKernel.class_escalates_over_soups' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms class_escalates_over_soups

/-- info: 'ChargeKernel.incident_escalates_over_soups' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms incident_escalates_over_soups

/-- info: 'ChargeKernel.class_escalation_example' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms class_escalation_example

/-- info: 'ChargeKernel.s4_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s4_sound

/-- info: 'ChargeKernel.s4_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s4_complete

/-- info: 'ChargeKernel.s4Audit_mem_swap' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s4Audit_mem_swap

/-- info: 'ChargeKernel.s4_value_gate' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s4_value_gate

/-- info: 'ChargeKernel.s4_permanent_against_permanent' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s4_permanent_against_permanent

/-- info: 'ChargeKernel.s4_convicts_example' depends on axioms: [propext] -/
#guard_msgs in #print axioms s4_convicts_example

/-- info: 'ChargeKernel.s4_honest_completion_example' depends on axioms: [propext] -/
#guard_msgs in #print axioms s4_honest_completion_example

/-- info: 'ChargeKernel.s4_never_clears_example' depends on axioms: [propext] -/
#guard_msgs in #print axioms s4_never_clears_example

/-- info: 'ChargeKernel.s4_never_clears_universal' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s4_never_clears_universal

end ChargeKernel
