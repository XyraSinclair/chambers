/-
ChargeKernel.VerdictPartition — the verdict partition theorem: the master
law of Byzantine merge, stated at the VERDICT level.

The naive law "verdicts only grow under union" is FALSE — an S1 overdraft
conviction retracts when the missing deposit arrives, and the spec RULES
it so (SETTLEMENT-SPEC: findings are functions of the set, and the set
growing toward completeness is the honest direction). The true law is a
PARTITION of the codes plus a CHARACTERIZATION of the retractable side:

    Adding evidence never erases a crime whose evidence is already
    present; it can only complete a gap — and each retractable code
    retracts only by supplying its named missing fact.

Everything below is over the adversarial soup (all Lists, no Nodup, no
honesty anywhere), reusing Completeness.lean's model and audit functions
verbatim, RawConservation.lean's raw model for the S6 arm, and gluing to
Monotone.lean's arithmetic laws — nothing is re-modeled.

What is claimed:

  Permanence (the crimes whose evidence is a POSITIVE fact in the set):
  * `x0_permanent` (+ `_prepend`) — an equivocation in E convicts in
    E ++ A for every raw extension A: the evidence is a pair of events
    and both persist.
  * `s2_overdisburse_permanent` (+ `_prepend`) — an over-disbursed escrow
    in E convicts in E ++ A, UNCONDITIONALLY: the audit is per-EVENT
    (each escrow checked against its own declared amount), so there is no
    cross-event amount resolution a forged duplicate-id escrow could
    move; disbursement sums only grow. `s2_per_event_duplicate_id` pins
    the exhibit. (In the real ledger same id ⟹ same bytes under content
    addressing, so duplicate-id-different-amount soups are
    unrepresentable there; the List model is the strict superset and the
    law holds even on it.)
  * `s6_permanent` (+ `_prepend`) — intrinsic per-event malformedness
    (RawConservation's raw Option-typed model, payer/payee arm) cannot be
    un-malformed by additions: `s6Audit_append` shows the audit of a
    union is the union of the audits.

  Characterized retraction (the gap class — the codes that convict an
  ABSENCE, and die only when the absent fact arrives):
  * `s1_retraction_is_completion` — THE SHARP LEMMA. If S1 convicts
    account a in E and not in E ++ A, then A supplied a fund fact
    crediting a: a positive deposit into a, or an inbound-release pair
    (escrow naming a as payee + positive release against it), or an
    inbound-refund pair (escrow naming a as payer + positive refund),
    with at least one member of the pair in A. Lock-outs only grow under
    append, so the only direction out of negative is money in
    (`available_append`, `s1_clear_forces_credit`). NOTE the honest
    width: SPEC §2's available(a) carries released_in and refunded_in,
    so the missing fund fact is any CREDIT, not only a deposit —
    `s1_retracts_without_deposit` machine-checks that the deposit-only
    reading is false.
  * `s2_retraction_is_completion` — if S2 convicts subj in E and not in
    E ++ A, the E-conviction was the dangling-reference arm and A
    contains an escrow event with EXACTLY the dangled id. The only way
    out is supplying the named missing escrow.
  * `s1_retracts_example`, `s2_dangling_retracts_example` — the honest-
    direction witnesses, machine-checked in-file forever (the
    f1_prefix_breaks discipline): the partition is non-vacuous in BOTH
    directions.

  Order-insensitivity (stated as lemmas, since the audits proved to be
  order-INsensitive at the membership level):
  * `settleAudit_mem_swap`, `x0Audit_mem_swap` — a finding is in the
    audit of E ++ A iff it is in the audit of A ++ E, proven through the
    sound+complete characterizations. The audit LISTS are order-sensitive
    as lists; membership is the conformance relation (§3 sorts + dedups).

  The fold glue (escalation stated AT THE SOUP LEVEL, KERNEL-SPEC §3):
  * `soup_sums_mono` — per-key cumulative/demanded uint-gated sums only
    grow under append.
  * `resolution_antitone` (+ `resolution_exists`, `resolvesTo_pos`) —
    §3.1 minimum-resolution of declared entropies only drops under
    union, exists when any well-formed register does, and stays positive.
  * `class_escalates_over_soups`, `incident_escalates_over_soups`,
    `merge_never_lowers_class` — composing the above with Monotone.lean's
    rank_mono_cumulative / rank_antitone_entropy / incident_mono:
    E ++ A never lowers any key's class rank and never un-latches
    incident. `class_escalation_example` witnesses 0 → 3 end to end.

Modeling choices, each the spec's rule and not a simplification:

  * The settlement/X0 arms reuse Completeness.lean's SoupEvent model and
    audit functions UNCHANGED — same junk-collapse rule (malformedness is
    S6's crime, folded to zero contribution, SPEC §2), same List-not-set
    superset discipline. The S6 arm is proven against RawConservation's
    raw Option-typed model, where malformedness is representable; the two
    models are not glued (importing both is composition, not unification).
  * `KeyEvent` is the minimal charge-ledger soup the fold glue needs:
    registers declare entropy per key (well-formed = positive, §3.1;
    `none`/0 contributes no candidate — I7's crime), charges carry
    uint-gated debit/demand (`none` contributes to no sum — I6's crime,
    §3.2). A key string stands for the canonical JSON of the key list.
  * Resolution is a RELATION (`ResolvesTo`: a declared candidate that is
    ≤ all candidates), not an Option-valued min — so the antitone law is
    membership arithmetic and non-vacuity is a separate theorem.

NOT claimed (each named so the register stays honest):

  * S3/S4/S7/S8 arms (work receipts, clean court, expiry timing) and
    S9/S10 (outcome attestations): their partition classes are unproven
    here — S3/S4 are expected RETRACTABLE-by-completion (a missing charge
    or work receipt can arrive) but that is a conjecture, not a theorem.
  * The S6 arms beyond payer/payee (non-uint amount, seq, charge_keys,
    default_on_expiry, escrow_id) — RawConservation's scope, inherited.
  * S1 retraction in the RAW Option-typed model (Completeness's model
    carries well-typedness by the §2 junk rule; the raw restatement is
    open).
  * The value-gate corollary (releases against convicted courts) is
    proven downstream in ValueGate.lean, which invokes the retraction
    characterizations above; the S4 arm itself is modeled there.
  * Register conflict flags and issuer sets at soup level (only the
    entropy minimum is modeled — the piece rank/incident read).
  * Full permutation invariance of the audits (only the binary merge swap
    E ++ A vs A ++ E is proven; it is what the CRDT merge needs).
-/
import ChargeKernel.Completeness
import ChargeKernel.RawConservation
import ChargeKernel.Monotone

namespace ChargeKernel

/-! ### Nat sum plumbing (self-contained, no mathlib) -/

theorem natSum_map_congr {α : Type} (l : List α) (f g : α → Nat)
    (h : ∀ x ∈ l, f x = g x) : (l.map f).sum = (l.map g).sum := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons]
    rw [h x (List.mem_cons_self ..), ih (fun y hy => h y (List.mem_cons_of_mem _ hy))]

theorem natSum_map_add {α : Type} (l : List α) (f g : α → Nat) :
    (l.map fun x => f x + g x).sum = (l.map f).sum + (l.map g).sum := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons, ih]
    omega

theorem natSum_append (l₁ l₂ : List Nat) :
    (l₁ ++ l₂).sum = l₁.sum + l₂.sum := by
  induction l₁ with
  | nil => simp
  | cons x xs ih =>
    simp only [List.cons_append, List.sum_cons, ih]
    omega

/-- A positive mapped Nat-sum has a positively-valued member. -/
theorem map_sum_pos_mem {α : Type} (l : List α) (f : α → Nat)
    (h : 0 < (l.map f).sum) : ∃ x ∈ l, 0 < f x := by
  obtain ⟨y, hy, hpos⟩ := sum_pos_mem h
  obtain ⟨x, hx, rfl⟩ := List.mem_map.mp hy
  exact ⟨x, hx, hpos⟩

/-- filterMap-sums are map-sums with default 0 — the bridge that turns
    every fold below into a pointwise-additive quantity. -/
theorem sum_filterMap_eq_map {α : Type} (l : List α) (f : α → Option Nat) :
    (l.filterMap f).sum = (l.map fun x => (f x).getD 0).sum := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    cases hf : f x with
    | none => simp [hf, ih]
    | some v => simp [hf, ih]

/-- Append-membership commutes (the merge form E ++ A vs A ++ E). -/
theorem mem_append_swap {α : Type} {x : α} {E A : List α}
    (h : x ∈ E ++ A) : x ∈ A ++ E := by
  rcases List.mem_append.mp h with h | h
  · exact List.mem_append_right _ h
  · exact List.mem_append_left _ h

/-! ### Append decomposition of the settlement sums

Every fold quantity of Completeness.lean is a filterMap-sum, so it is
ADDITIVE under append — the arithmetic skeleton of both halves of the
partition (growth for permanence, exact bookkeeping for retraction). -/

theorem releasedTo_append (E A : List SoupEvent) (e : String) :
    releasedTo (E ++ A) e = releasedTo E e + releasedTo A e := by
  unfold releasedTo
  rw [List.filterMap_append, natSum_append]

theorem refundedTo_append (E A : List SoupEvent) (e : String) :
    refundedTo (E ++ A) e = refundedTo E e + refundedTo A e := by
  unfold refundedTo
  rw [List.filterMap_append, natSum_append]

theorem depositedTo_append (E A : List SoupEvent) (a : String) :
    depositedTo (E ++ A) a = depositedTo E a + depositedTo A a := by
  unfold depositedTo
  rw [List.filterMap_append, natSum_append]

theorem lockedOut_append (E A : List SoupEvent) (a : String) :
    lockedOut (E ++ A) a = lockedOut E a + lockedOut A a := by
  unfold lockedOut lockedOutList
  rw [List.filterMap_append, natSum_append]

theorem hasEscrow_append (E A : List SoupEvent) (e : String) :
    hasEscrow (E ++ A) e = (hasEscrow E e || hasEscrow A e) := by
  unfold hasEscrow
  rw [List.any_append]

/-- An escrow event with id `e` in the soup makes `hasEscrow` true. -/
theorem hasEscrow_of_mem (soup : List SoupEvent)
    (e issuer payer payee : String) (amt : Nat)
    (hmem : SoupEvent.escrow e issuer payer payee amt ∈ soup) :
    hasEscrow soup e = true := by
  apply List.any_eq_true.mpr
  exact ⟨_, hmem, by simp⟩

/-! ### The inbound-credit cells (releasedIn / refundedIn, made additive)

`releasedIn`/`refundedIn` are DOUBLE sums (per matching escrow, a sum of
disbursements over the whole soup), so they are not plain filterMap-sums
in the soup. The cells below expose them as map-sums whose per-event
value is itself additive in the soup argument — that is what makes the
exact append decomposition (and hence the retraction characterization)
arithmetic. -/

/-- Event `ev`'s inbound release credit to account `a`, disbursements
    read from `soup`. -/
def relCell (soup : List SoupEvent) (a : String) : SoupEvent → Nat
  | .escrow id _ _ payee _ => if payee = a then releasedTo soup id else 0
  | _ => 0

/-- Event `ev`'s inbound refund credit to account `a` (escrows name their
    PAYER as the refund creditee), disbursements read from `soup`. -/
def refCell (soup : List SoupEvent) (a : String) : SoupEvent → Nat
  | .escrow id _ payer _ _ => if payer = a then refundedTo soup id else 0
  | _ => 0

theorem releasedIn_eq_map (soup : List SoupEvent) (a : String) :
    releasedIn soup a = (soup.map (relCell soup a)).sum := by
  unfold releasedIn
  rw [sum_filterMap_eq_map]
  refine natSum_map_congr _ _ _ (fun ev _ => ?_)
  cases ev with
  | escrow id issuer payer payee amt =>
    by_cases hp : payee = a <;> simp [relCell, hp]
  | deposit id issuer acct amt => simp [relCell]
  | release id issuer eid amt => simp [relCell]
  | refund id issuer eid amt => simp [relCell]
  | junk id => simp [relCell]

theorem refundedIn_eq_map (soup : List SoupEvent) (a : String) :
    refundedIn soup a = (soup.map (refCell soup a)).sum := by
  unfold refundedIn
  rw [sum_filterMap_eq_map]
  refine natSum_map_congr _ _ _ (fun ev _ => ?_)
  cases ev with
  | escrow id issuer payer payee amt =>
    by_cases hp : payer = a <;> simp [refCell, hp]
  | deposit id issuer acct amt => simp [refCell]
  | release id issuer eid amt => simp [refCell]
  | refund id issuer eid amt => simp [refCell]
  | junk id => simp [refCell]

/-- The cell is additive in its SOUP argument (disbursement sums split). -/
theorem relCell_append (E A : List SoupEvent) (a : String) (ev : SoupEvent) :
    relCell (E ++ A) a ev = relCell E a ev + relCell A a ev := by
  cases ev with
  | escrow id issuer payer payee amt =>
    by_cases hp : payee = a <;> simp [relCell, hp, releasedTo_append]
  | deposit id issuer acct amt => simp [relCell]
  | release id issuer eid amt => simp [relCell]
  | refund id issuer eid amt => simp [relCell]
  | junk id => simp [relCell]

theorem refCell_append (E A : List SoupEvent) (a : String) (ev : SoupEvent) :
    refCell (E ++ A) a ev = refCell E a ev + refCell A a ev := by
  cases ev with
  | escrow id issuer payer payee amt =>
    by_cases hp : payer = a <;> simp [refCell, hp, refundedTo_append]
  | deposit id issuer acct amt => simp [refCell]
  | release id issuer eid amt => simp [refCell]
  | refund id issuer eid amt => simp [refCell]
  | junk id => simp [refCell]

/-- The EXACT append decomposition of releasedIn: the old value plus the
    two genuinely new routes (new disbursements against old escrows; new
    escrows with whatever disbursements the merged soup aims at them). -/
theorem releasedIn_append (E A : List SoupEvent) (a : String) :
    releasedIn (E ++ A) a
      = releasedIn E a
        + ((E.map (relCell A a)).sum + (A.map (relCell (E ++ A) a)).sum) := by
  rw [releasedIn_eq_map (E ++ A) a, releasedIn_eq_map E a,
      List.map_append, natSum_append]
  have hsplit : (E.map (relCell (E ++ A) a)).sum
      = (E.map (relCell E a)).sum + (E.map (relCell A a)).sum :=
    calc (E.map (relCell (E ++ A) a)).sum
        = (E.map fun ev => relCell E a ev + relCell A a ev).sum :=
          natSum_map_congr _ _ _ fun ev _ => relCell_append E A a ev
      _ = (E.map (relCell E a)).sum + (E.map (relCell A a)).sum :=
          natSum_map_add _ _ _
  omega

theorem refundedIn_append (E A : List SoupEvent) (a : String) :
    refundedIn (E ++ A) a
      = refundedIn E a
        + ((E.map (refCell A a)).sum + (A.map (refCell (E ++ A) a)).sum) := by
  rw [refundedIn_eq_map (E ++ A) a, refundedIn_eq_map E a,
      List.map_append, natSum_append]
  have hsplit : (E.map (refCell (E ++ A) a)).sum
      = (E.map (refCell E a)).sum + (E.map (refCell A a)).sum :=
    calc (E.map (refCell (E ++ A) a)).sum
        = (E.map fun ev => refCell E a ev + refCell A a ev).sum :=
          natSum_map_congr _ _ _ fun ev _ => refCell_append E A a ev
      _ = (E.map (refCell E a)).sum + (E.map (refCell A a)).sum :=
          natSum_map_add _ _ _
  omega

/-! ### Order-insensitivity: audit MEMBERSHIP does not see merge order

The audit functions return Lists (order- and duplication-sensitive as
lists), but the conformance surface is sorted-deduplicated membership
(SETTLEMENT-SPEC §3). At the membership level the whole settlement audit
and X0 are invariant under swapping the two sides of a merge — proven
through the sound+complete characterizations, so no new structural
excavation of the folds is needed. -/

theorem relCell_swap (E A : List SoupEvent) (a : String) (ev : SoupEvent) :
    relCell (E ++ A) a ev = relCell (A ++ E) a ev := by
  rw [relCell_append, relCell_append]
  omega

theorem refCell_swap (E A : List SoupEvent) (a : String) (ev : SoupEvent) :
    refCell (E ++ A) a ev = refCell (A ++ E) a ev := by
  rw [refCell_append, refCell_append]
  omega

theorem releasedIn_swap (E A : List SoupEvent) (a : String) :
    releasedIn (E ++ A) a = releasedIn (A ++ E) a := by
  rw [releasedIn_eq_map (E ++ A) a, releasedIn_eq_map (A ++ E) a,
      List.map_append, List.map_append, natSum_append, natSum_append]
  have hE : (E.map (relCell (E ++ A) a)).sum = (E.map (relCell (A ++ E) a)).sum :=
    natSum_map_congr _ _ _ fun ev _ => relCell_swap E A a ev
  have hA : (A.map (relCell (E ++ A) a)).sum = (A.map (relCell (A ++ E) a)).sum :=
    natSum_map_congr _ _ _ fun ev _ => relCell_swap E A a ev
  omega

theorem refundedIn_swap (E A : List SoupEvent) (a : String) :
    refundedIn (E ++ A) a = refundedIn (A ++ E) a := by
  rw [refundedIn_eq_map (E ++ A) a, refundedIn_eq_map (A ++ E) a,
      List.map_append, List.map_append, natSum_append, natSum_append]
  have hE : (E.map (refCell (E ++ A) a)).sum = (E.map (refCell (A ++ E) a)).sum :=
    natSum_map_congr _ _ _ fun ev _ => refCell_swap E A a ev
  have hA : (A.map (refCell (E ++ A) a)).sum = (A.map (refCell (A ++ E) a)).sum :=
    natSum_map_congr _ _ _ fun ev _ => refCell_swap E A a ev
  omega

theorem releasedTo_swap (E A : List SoupEvent) (e : String) :
    releasedTo (E ++ A) e = releasedTo (A ++ E) e := by
  rw [releasedTo_append, releasedTo_append]
  omega

theorem refundedTo_swap (E A : List SoupEvent) (e : String) :
    refundedTo (E ++ A) e = refundedTo (A ++ E) e := by
  rw [refundedTo_append, refundedTo_append]
  omega

theorem hasEscrow_swap (E A : List SoupEvent) (e : String) :
    hasEscrow (E ++ A) e = hasEscrow (A ++ E) e := by
  rw [hasEscrow_append, hasEscrow_append]
  cases hasEscrow E e <;> cases hasEscrow A e <;> rfl

/-- available(a) is merge-order-blind. -/
theorem available_swap (E A : List SoupEvent) (a : String) :
    available (E ++ A) a = available (A ++ E) a := by
  unfold available
  rw [depositedTo_append E A, depositedTo_append A E,
      lockedOut_append E A, lockedOut_append A E,
      releasedIn_swap, refundedIn_swap]
  omega

/-- One direction of the swap, routed by finding code through the
    sound+complete pairs. -/
theorem settleAudit_mem_swap_aux (E A : List SoupEvent) (f : Finding)
    (hf : f ∈ settleAudit (E ++ A)) : f ∈ settleAudit (A ++ E) := by
  obtain ⟨c, subj⟩ := f
  cases c with
  | S1 =>
    have hneg := s1_sound (E ++ A) subj hf
    rw [available_swap] at hneg
    exact s1_complete (A ++ E) subj hneg
  | S2 =>
    rcases s2_sound (E ++ A) subj hf with
      ⟨issuer, payer, payee, amount, hmem, hover⟩ | ⟨issuer, eid, amount, hmem, hghost⟩
    · apply s2_complete (A ++ E) subj issuer payer payee amount (mem_append_swap hmem)
      rw [releasedTo_swap A E, refundedTo_swap A E]
      exact hover
    · apply s2_dangling_complete (A ++ E) subj issuer eid amount
      · rcases hmem with h | h
        · exact Or.inl (mem_append_swap h)
        · exact Or.inr (mem_append_swap h)
      · rw [← hasEscrow_swap]
        exact hghost

/-- **Merge-order insensitivity (settlement).** A finding is in the audit
    of E ++ A iff it is in the audit of A ++ E: the verdict is a function
    of the SET, exactly the CRDT claim. -/
theorem settleAudit_mem_swap (E A : List SoupEvent) (f : Finding) :
    f ∈ settleAudit (E ++ A) ↔ f ∈ settleAudit (A ++ E) :=
  ⟨settleAudit_mem_swap_aux E A f, settleAudit_mem_swap_aux A E f⟩

theorem x0Audit_mem_swap_aux (E A : List XEvent) (i : FactIdent)
    (h : i ∈ x0Audit (E ++ A)) : i ∈ x0Audit (A ++ E) := by
  obtain ⟨e, he, e', he', h1, h2, h3⟩ := x0_sound (E ++ A) i h
  exact x0_complete (A ++ E) e e' i h1 h2 h3 (mem_append_swap he) (mem_append_swap he')

/-- **Merge-order insensitivity (X0).** -/
theorem x0Audit_mem_swap (E A : List XEvent) (i : FactIdent) :
    i ∈ x0Audit (E ++ A) ↔ i ∈ x0Audit (A ++ E) :=
  ⟨x0Audit_mem_swap_aux E A i, x0Audit_mem_swap_aux A E i⟩

/-! ### Part 1 — conviction permanence (the permanent class) -/

/-- **X0 permanence.** An equivocation present in E is present in E ++ A,
    for EVERY raw extension A: the evidence is a pair of events, and both
    persist under union. Composition of x0_sound with x0_complete. -/
theorem x0_permanent (E A : List XEvent) (i : FactIdent)
    (h : i ∈ x0Audit E) : i ∈ x0Audit (E ++ A) := by
  obtain ⟨e, he, e', he', h1, h2, h3⟩ := x0_sound E i h
  exact x0_complete (E ++ A) e e' i h1 h2 h3
    (List.mem_append_left _ he) (List.mem_append_left _ he')

/-- The prepended-merge form, via order-insensitivity. -/
theorem x0_permanent_prepend (E A : List XEvent) (i : FactIdent)
    (h : i ∈ x0Audit E) : i ∈ x0Audit (A ++ E) :=
  (x0Audit_mem_swap E A i).mp (x0_permanent E A i h)

/-- **S2 over-disbursement permanence.** UNCONDITIONAL: the audit is
    per-EVENT — each escrow event is checked against ITS OWN declared
    amount (`s2FindingsOf`), so there is no cross-event amount resolution
    a forged duplicate-id escrow could move. The convicting escrow event
    persists, and disbursement sums only grow under append. (In the real
    ledger same id ⟹ same bytes — content addressing — so duplicate-id-
    different-amount soups are unrepresentable there; the List model is a
    strict superset and the law holds even on it. See
    `s2_per_event_duplicate_id` below for the pinned exhibit.) -/
theorem s2_overdisburse_permanent (E A : List SoupEvent)
    (id issuer payer payee : String) (amount : Nat)
    (hmem : SoupEvent.escrow id issuer payer payee amount ∈ E)
    (hover : amount < releasedTo E id + refundedTo E id) :
    (⟨.S2, id⟩ : Finding) ∈ settleAudit (E ++ A) := by
  apply s2_complete (E ++ A) id issuer payer payee amount (List.mem_append_left _ hmem)
  rw [releasedTo_append, refundedTo_append]
  omega

/-- The prepended-merge form. -/
theorem s2_overdisburse_permanent_prepend (E A : List SoupEvent)
    (id issuer payer payee : String) (amount : Nat)
    (hmem : SoupEvent.escrow id issuer payer payee amount ∈ E)
    (hover : amount < releasedTo E id + refundedTo E id) :
    (⟨.S2, id⟩ : Finding) ∈ settleAudit (A ++ E) :=
  (settleAudit_mem_swap E A _).mp
    (s2_overdisburse_permanent E A id issuer payer payee amount hmem hover)

/-- s6Audit distributes over append — malformedness is intrinsic to the
    event, so the audit of a union is the union of the audits. -/
theorem s6Audit_append (E A : List RawEvent) :
    s6Audit (E ++ A) = s6Audit E ++ s6Audit A := by
  unfold s6Audit
  rw [List.filterMap_append]

/-- **S6 permanence** (RawConservation's raw Option-typed model, payer/
    payee arm): an intrinsically malformed event cannot be un-malformed
    by additions. -/
theorem s6_permanent (E A : List RawEvent) (subj : String)
    (h : subj ∈ s6Audit E) : subj ∈ s6Audit (E ++ A) := by
  rw [s6Audit_append]
  exact List.mem_append_left _ h

/-- The prepended-merge form. -/
theorem s6_permanent_prepend (E A : List RawEvent) (subj : String)
    (h : subj ∈ s6Audit E) : subj ∈ s6Audit (A ++ E) := by
  rw [s6Audit_append]
  exact List.mem_append_right _ h

/-! ### Part 2 — characterized retraction (the gap class) -/

/-- The new credit an extension A brings to account `a`: new deposits,
    new disbursements against old escrows, and disbursements (from the
    whole merged soup) against new escrows naming `a`. -/
def s1CreditGrowth (E A : List SoupEvent) (a : String) : Nat :=
  depositedTo A a
    + ((E.map (relCell A a)).sum + (A.map (relCell (E ++ A) a)).sum)
    + ((E.map (refCell A a)).sum + (A.map (refCell (E ++ A) a)).sum)

/-- The EXACT bookkeeping of available(a) under append: old value, plus
    the new credit, minus the new lock-outs. Everything the retraction
    characterization needs is this one identity. -/
theorem available_append (E A : List SoupEvent) (a : String) :
    available (E ++ A) a
      = available E a + (s1CreditGrowth E A a : Int) - (lockedOut A a : Int) := by
  unfold available s1CreditGrowth
  rw [depositedTo_append, lockedOut_append, releasedIn_append, refundedIn_append]
  omega

/-- An overdraft cannot clear without STRICTLY new credit: lock-outs only
    grow under append, so the only direction out of negative is money in. -/
theorem s1_clear_forces_credit (E A : List SoupEvent) (a : String)
    (hneg : available E a < 0) (hok : 0 ≤ available (E ++ A) a) :
    0 < s1CreditGrowth E A a := by
  have h := available_append E A a
  omega

/-- A positive deposit sum names its deposit event. -/
theorem depositedTo_pos (soup : List SoupEvent) (a : String)
    (h : 0 < depositedTo soup a) :
    ∃ id issuer amt, SoupEvent.deposit id issuer a amt ∈ soup ∧ 0 < amt := by
  unfold depositedTo at h
  rw [sum_filterMap_eq_map] at h
  obtain ⟨ev, hev, hpos⟩ := map_sum_pos_mem _ _ h
  cases ev with
  | deposit id issuer acct amt =>
    by_cases hacct : acct = a
    · subst hacct
      exact ⟨id, issuer, amt, hev, by simpa using hpos⟩
    · simp [hacct] at hpos
  | escrow id issuer payer payee amt => simp at hpos
  | release id issuer eid amt => simp at hpos
  | refund id issuer eid amt => simp at hpos
  | junk id => simp at hpos

/-- A positive release sum names its release event. -/
theorem releasedTo_pos (soup : List SoupEvent) (e : String)
    (h : 0 < releasedTo soup e) :
    ∃ id issuer amt, SoupEvent.release id issuer e amt ∈ soup ∧ 0 < amt := by
  unfold releasedTo at h
  rw [sum_filterMap_eq_map] at h
  obtain ⟨ev, hev, hpos⟩ := map_sum_pos_mem _ _ h
  cases ev with
  | release id issuer eid amt =>
    by_cases heid : eid = e
    · subst heid
      exact ⟨id, issuer, amt, hev, by simpa using hpos⟩
    · simp [heid] at hpos
  | deposit id issuer acct amt => simp at hpos
  | escrow id issuer payer payee amt => simp at hpos
  | refund id issuer eid amt => simp at hpos
  | junk id => simp at hpos

/-- A positive refund sum names its refund event. -/
theorem refundedTo_pos (soup : List SoupEvent) (e : String)
    (h : 0 < refundedTo soup e) :
    ∃ id issuer amt, SoupEvent.refund id issuer e amt ∈ soup ∧ 0 < amt := by
  unfold refundedTo at h
  rw [sum_filterMap_eq_map] at h
  obtain ⟨ev, hev, hpos⟩ := map_sum_pos_mem _ _ h
  cases ev with
  | refund id issuer eid amt =>
    by_cases heid : eid = e
    · subst heid
      exact ⟨id, issuer, amt, hev, by simpa using hpos⟩
    · simp [heid] at hpos
  | deposit id issuer acct amt => simp at hpos
  | escrow id issuer payer payee amt => simp at hpos
  | release id issuer eid amt => simp at hpos
  | junk id => simp at hpos

/-- A positive release cell names its escrow (payee = a) and forces a
    positive release sum against it. -/
theorem relCell_pos (soup : List SoupEvent) (a : String) (ev : SoupEvent)
    (h : 0 < relCell soup a ev) :
    ∃ id issuer payer amt, ev = SoupEvent.escrow id issuer payer a amt ∧
      0 < releasedTo soup id := by
  cases ev with
  | escrow id issuer payer payee amt =>
    by_cases hp : payee = a
    · subst hp
      exact ⟨id, issuer, payer, amt, rfl, by simpa [relCell] using h⟩
    · simp [relCell, hp] at h
  | deposit id issuer acct amt => simp [relCell] at h
  | release id issuer eid amt => simp [relCell] at h
  | refund id issuer eid amt => simp [relCell] at h
  | junk id => simp [relCell] at h

/-- A positive refund cell names its escrow (payer = a) and forces a
    positive refund sum against it. -/
theorem refCell_pos (soup : List SoupEvent) (a : String) (ev : SoupEvent)
    (h : 0 < refCell soup a ev) :
    ∃ id issuer payee amt, ev = SoupEvent.escrow id issuer a payee amt ∧
      0 < refundedTo soup id := by
  cases ev with
  | escrow id issuer payer payee amt =>
    by_cases hp : payer = a
    · subst hp
      exact ⟨id, issuer, payee, amt, rfl, by simpa [refCell] using h⟩
    · simp [refCell, hp] at h
  | deposit id issuer acct amt => simp [refCell] at h
  | release id issuer eid amt => simp [refCell] at h
  | refund id issuer eid amt => simp [refCell] at h
  | junk id => simp [refCell] at h

/-- **S1 retraction is completion — THE SHARP LEMMA.** If S1 convicts
    account `a` in E and does not convict in E ++ A, then A supplied a
    genuinely new FUND FACT crediting `a` — one of exactly three routes,
    each named by its events:

      (i)   a positive deposit into `a`, in A;
      (ii)  an inbound-release pair — an escrow naming `a` as payee and a
            positive release against it — with at least one member in A;
      (iii) an inbound-refund pair — an escrow naming `a` as payer and a
            positive refund against it — with at least one member in A.

    NOTE the honest width: SETTLEMENT-SPEC §2's available(a) carries
    released_in and refunded_in, so "the missing fund fact" is any credit
    to the account, NOT only a deposit — `s1_retracts_without_deposit`
    below machine-checks that the deposit-only reading is false. What IS
    proven impossible: clearing an overdraft by adding lock-outs, junk,
    unrelated events, or any soup that credits `a` nothing. -/
theorem s1_retraction_is_completion (E A : List SoupEvent) (a : String)
    (hconvict : (⟨.S1, a⟩ : Finding) ∈ settleAudit E)
    (hclear : (⟨.S1, a⟩ : Finding) ∉ settleAudit (E ++ A)) :
    (∃ id issuer amt, SoupEvent.deposit id issuer a amt ∈ A ∧ 0 < amt)
    ∨ (∃ eid ei ep amtE rid ri amtR,
        SoupEvent.escrow eid ei ep a amtE ∈ E ++ A ∧
        SoupEvent.release rid ri eid amtR ∈ E ++ A ∧ 0 < amtR ∧
        (SoupEvent.escrow eid ei ep a amtE ∈ A ∨
         SoupEvent.release rid ri eid amtR ∈ A))
    ∨ (∃ eid ei pe amtE rid ri amtR,
        SoupEvent.escrow eid ei a pe amtE ∈ E ++ A ∧
        SoupEvent.refund rid ri eid amtR ∈ E ++ A ∧ 0 < amtR ∧
        (SoupEvent.escrow eid ei a pe amtE ∈ A ∨
         SoupEvent.refund rid ri eid amtR ∈ A)) := by
  have hneg : available E a < 0 := s1_sound E a hconvict
  have hok : 0 ≤ available (E ++ A) a := by
    by_cases hlt : available (E ++ A) a < 0
    · exact absurd (s1_complete (E ++ A) a hlt) hclear
    · omega
  have hg : 0 < s1CreditGrowth E A a := s1_clear_forces_credit E A a hneg hok
  unfold s1CreditGrowth at hg
  have hcases : 0 < depositedTo A a
      ∨ 0 < (E.map (relCell A a)).sum
      ∨ 0 < (A.map (relCell (E ++ A) a)).sum
      ∨ 0 < (E.map (refCell A a)).sum
      ∨ 0 < (A.map (refCell (E ++ A) a)).sum := by omega
  rcases hcases with h | h | h | h | h
  · exact Or.inl (depositedTo_pos A a h)
  · -- new release in A against an old escrow (payee = a) in E
    obtain ⟨ev, hevE, hcell⟩ := map_sum_pos_mem _ _ h
    obtain ⟨eid, ei, ep, amtE, rfl, hrt⟩ := relCell_pos A a ev hcell
    obtain ⟨rid, ri, amtR, hrel, hamt⟩ := releasedTo_pos A eid hrt
    exact Or.inr (Or.inl ⟨eid, ei, ep, amtE, rid, ri, amtR,
      List.mem_append_left _ hevE, List.mem_append_right _ hrel, hamt,
      Or.inr hrel⟩)
  · -- new escrow in A (payee = a), disbursed from anywhere in the merge
    obtain ⟨ev, hevA, hcell⟩ := map_sum_pos_mem _ _ h
    obtain ⟨eid, ei, ep, amtE, rfl, hrt⟩ := relCell_pos (E ++ A) a ev hcell
    obtain ⟨rid, ri, amtR, hrel, hamt⟩ := releasedTo_pos (E ++ A) eid hrt
    exact Or.inr (Or.inl ⟨eid, ei, ep, amtE, rid, ri, amtR,
      List.mem_append_right _ hevA, hrel, hamt, Or.inl hevA⟩)
  · -- new refund in A against an old escrow (payer = a) in E
    obtain ⟨ev, hevE, hcell⟩ := map_sum_pos_mem _ _ h
    obtain ⟨eid, ei, pe, amtE, rfl, hrt⟩ := refCell_pos A a ev hcell
    obtain ⟨rid, ri, amtR, href, hamt⟩ := refundedTo_pos A eid hrt
    exact Or.inr (Or.inr ⟨eid, ei, pe, amtE, rid, ri, amtR,
      List.mem_append_left _ hevE, List.mem_append_right _ href, hamt,
      Or.inr href⟩)
  · -- new escrow in A (payer = a), refunded from anywhere in the merge
    obtain ⟨ev, hevA, hcell⟩ := map_sum_pos_mem _ _ h
    obtain ⟨eid, ei, pe, amtE, rfl, hrt⟩ := refCell_pos (E ++ A) a ev hcell
    obtain ⟨rid, ri, amtR, href, hamt⟩ := refundedTo_pos (E ++ A) eid hrt
    exact Or.inr (Or.inr ⟨eid, ei, pe, amtE, rid, ri, amtR,
      List.mem_append_right _ hevA, href, hamt, Or.inl hevA⟩)

/-- **S2 retraction is completion (dangling arm).** If S2 convicts `subj`
    in E and does not convict in E ++ A, then the E-conviction was the
    dangling-reference arm — a release/refund naming an escrow id absent
    from E — and A contains AN ESCROW EVENT WITH EXACTLY THAT ID. The
    over-disbursement arm cannot retract (`s2_overdisburse_permanent`);
    the only way out of the dangling arm is supplying the named missing
    escrow. -/
theorem s2_retraction_is_completion (E A : List SoupEvent) (subj : String)
    (hconvict : (⟨.S2, subj⟩ : Finding) ∈ settleAudit E)
    (hclear : (⟨.S2, subj⟩ : Finding) ∉ settleAudit (E ++ A)) :
    ∃ eid, hasEscrow E eid = false ∧
      (∃ issuer amt, SoupEvent.release subj issuer eid amt ∈ E ∨
                     SoupEvent.refund subj issuer eid amt ∈ E) ∧
      ∃ issuer payer payee amt, SoupEvent.escrow eid issuer payer payee amt ∈ A := by
  rcases s2_sound E subj hconvict with
    ⟨issuer, payer, payee, amount, hmem, hover⟩ | ⟨issuer, eid, amount, hmem, hghost⟩
  · exact absurd (s2_overdisburse_permanent E A subj issuer payer payee amount hmem hover)
      hclear
  · refine ⟨eid, hghost, ⟨issuer, amount, hmem⟩, ?_⟩
    have hmem' : SoupEvent.release subj issuer eid amount ∈ E ++ A ∨
                 SoupEvent.refund subj issuer eid amount ∈ E ++ A := by
      rcases hmem with h | h
      · exact Or.inl (List.mem_append_left _ h)
      · exact Or.inr (List.mem_append_left _ h)
    cases htrue : hasEscrow (E ++ A) eid with
    | false =>
      exact absurd (s2_dangling_complete (E ++ A) subj issuer eid amount hmem' htrue)
        hclear
    | true =>
      obtain ⟨ev, hev, hid⟩ := List.any_eq_true.mp htrue
      cases ev with
      | escrow id2 iss2 payer2 payee2 amt2 =>
        have hid' : id2 = eid := by simpa using hid
        subst hid'
        rcases List.mem_append.mp hev with hE | hA
        · rw [hasEscrow_of_mem E id2 iss2 payer2 payee2 amt2 hE] at hghost
          cases hghost
        · exact ⟨iss2, payer2, payee2, amt2, hA⟩
      | deposit id2 issuer2 acct amt => simp at hid
      | release id2 issuer2 eid2 amt => simp at hid
      | refund id2 issuer2 eid2 amt => simp at hid
      | junk id2 => simp at hid

/-! ### The retraction witnesses — the honest direction, pinned in-file
(the f1_prefix_breaks discipline: the partition is non-vacuous in BOTH
directions, machine-checked forever) -/

/-- An overdraft conviction: mallory escrowed value alice never had. -/
def s1GapSoup : List SoupEvent :=
  [ .escrow "e1" "mallory" "alice" "bob" 80 ]

/-- The genuinely missing fund fact. -/
def s1GapFix : List SoupEvent :=
  [ .deposit "d1" "carol" "alice" 100 ]

/-- **S1 retracts — the honest direction, witnessed.** The overdraft
    conviction stands on the gap soup and is GONE once the missing
    deposit arrives: verdicts are not monotone, and that is the spec's
    own ruling ("findings are functions of the set, and the set growing
    toward completeness is the honest direction"). -/
theorem s1_retracts_example :
    (⟨.S1, "alice"⟩ : Finding) ∈ settleAudit s1GapSoup ∧
    (⟨.S1, "alice"⟩ : Finding) ∉ settleAudit (s1GapSoup ++ s1GapFix) := by
  decide

/-- Overdraft cleared by an inbound RELEASE, no deposit anywhere in A. -/
def s1RelGapSoup : List SoupEvent :=
  [ .escrow "e1" "carol" "bob" "alice" 50,
    .escrow "e2" "mallory" "alice" "cara" 30 ]

def s1RelGapFix : List SoupEvent :=
  [ .release "r1" "carol" "e1" 40 ]

/-- **The deposit-only reading of S1 retraction is FALSE.** Here the
    clearing fund fact is an inbound release (alice is payee of e1);
    depositedTo of the extension is 0. This pins why
    `s1_retraction_is_completion` must name all three credit routes —
    proving the naive "only a deposit can clear an overdraft" would have
    been a lie about SPEC §2's available(a). -/
theorem s1_retracts_without_deposit :
    (⟨.S1, "alice"⟩ : Finding) ∈ settleAudit s1RelGapSoup ∧
    (⟨.S1, "alice"⟩ : Finding) ∉ settleAudit (s1RelGapSoup ++ s1RelGapFix) ∧
    depositedTo s1RelGapFix "alice" = 0 := by
  decide

/-- A dangling release: convicted S2 until its escrow shows up. -/
def s2GapSoup : List SoupEvent :=
  [ .release "r1" "mallory" "ghost" 5 ]

def s2GapFix : List SoupEvent :=
  [ .escrow "ghost" "carol" "payer" "payee" 10 ]

/-- **S2 (dangling arm) retracts — witnessed.** The unknown-escrow
    conviction dies exactly when the named escrow arrives. (The merged
    soup convicts S1 "payer" instead — the completion moved the crime to
    its true subject; nothing was laundered.) -/
theorem s2_dangling_retracts_example :
    (⟨.S2, "r1"⟩ : Finding) ∈ settleAudit s2GapSoup ∧
    (⟨.S2, "r1"⟩ : Finding) ∉ settleAudit (s2GapSoup ++ s2GapFix) := by
  decide

/-- **The duplicate-id exhibit.** The audit is per-EVENT: a forged second
    escrow claiming the same id with a huge amount does NOT retract the
    over-disbursement conviction of the small one — there is no
    cross-event amount resolution to poison. (Real ledgers cannot even
    represent this soup: same id ⟹ same bytes under content addressing,
    and same-actor-different-bytes is X0's crime. The List model is the
    strict superset; permanence holds even on it, unconditionally.) -/
theorem s2_per_event_duplicate_id :
    (⟨.S2, "e1"⟩ : Finding) ∈ settleAudit
      [ .escrow "e1" "mallory" "a" "b" 10, .release "r1" "c" "e1" 50 ] ∧
    (⟨.S2, "e1"⟩ : Finding) ∈ settleAudit
      [ .escrow "e1" "mallory" "a" "b" 10, .release "r1" "c" "e1" 50,
        .escrow "e1" "forger" "a" "b" 1000 ] := by
  decide

/-! ### Part 3 — the fold glue: escalation stated AT THE SOUP LEVEL

Monotone.lean proves the arithmetic laws (rank_mono_cumulative,
rank_antitone_entropy, incident_mono) over bare numbers. Neither
Completeness.lean (settlement events) nor RawConservation.lean (raw
settlement events) carries per-key information sums, so the minimal
charge-ledger soup is built here (KERNEL-SPEC §3): registers declare
entropy for a key, charges debit/demand against it, uint-gated. The glue
theorems compose the soup-level sums with Monotone.lean's laws — the
statement the registers have been making informally: E ++ A never lowers
any key's class rank and never un-latches incident. -/

/-- The minimal charge-ledger soup the fold glue reads. `none` is the
    non-uint field (I6/I7's crime — contributes to no sum, KERNEL-SPEC
    §3.2); a key string stands for the canonical JSON of the key list. -/
inductive KeyEvent where
  | register (id : String) (key : String) (entropy : Option Nat)
  | charge   (id : String) (key : String) (debit demand : Option Nat)
  | junk     (id : String)
deriving Repr, DecidableEq

/-- cumulative_mbits(k): Σ uint debits of charges naming key `k`. -/
def cumulativeOf (soup : List KeyEvent) (k : String) : Nat :=
  (soup.filterMap fun ev => match ev with
    | .charge _ key (some d) _ => if key = k then some d else none
    | _ => none).sum

/-- demanded_mbits(k): Σ uint demands of charges naming key `k`. -/
def demandedOf (soup : List KeyEvent) (k : String) : Nat :=
  (soup.filterMap fun ev => match ev with
    | .charge _ key _ (some d) => if key = k then some d else none
    | _ => none).sum

/-- The well-formed declared entropies for key `k` (KERNEL-SPEC §3.1:
    an int > 0; `none`/0 is the malformed register, I7's subject —
    it contributes no candidate). -/
def entropiesOf (soup : List KeyEvent) (k : String) : List Nat :=
  soup.filterMap fun ev => match ev with
    | .register _ key (some n) => if key = k ∧ 0 < n then some n else none
    | _ => none

/-- §3.1 minimum-resolution, as a relation: `s` is a declared well-formed
    entropy for `k` and no declared one is smaller. -/
def ResolvesTo (soup : List KeyEvent) (k : String) (s : Nat) : Prop :=
  s ∈ entropiesOf soup k ∧ ∀ t ∈ entropiesOf soup k, s ≤ t

instance (soup : List KeyEvent) (k : String) (s : Nat) :
    Decidable (ResolvesTo soup k s) :=
  inferInstanceAs (Decidable (s ∈ entropiesOf soup k ∧ ∀ t ∈ entropiesOf soup k, s ≤ t))

theorem cumulativeOf_append (E A : List KeyEvent) (k : String) :
    cumulativeOf (E ++ A) k = cumulativeOf E k + cumulativeOf A k := by
  unfold cumulativeOf
  rw [List.filterMap_append, natSum_append]

theorem demandedOf_append (E A : List KeyEvent) (k : String) :
    demandedOf (E ++ A) k = demandedOf E k + demandedOf A k := by
  unfold demandedOf
  rw [List.filterMap_append, natSum_append]

theorem entropiesOf_append (E A : List KeyEvent) (k : String) :
    entropiesOf (E ++ A) k = entropiesOf E k ++ entropiesOf A k := by
  unfold entropiesOf
  rw [List.filterMap_append]

/-- **Soup sums are monotone under append** — the per-key cumulative and
    demanded folds only grow as facts are added. -/
theorem soup_sums_mono (E A : List KeyEvent) (k : String) :
    cumulativeOf E k ≤ cumulativeOf (E ++ A) k ∧
    demandedOf E k ≤ demandedOf (E ++ A) k :=
  ⟨by rw [cumulativeOf_append]; omega, by rw [demandedOf_append]; omega⟩

/-- A resolved entropy is positive (the well-formedness gate carries
    through resolution — Monotone.lean's `0 < s₂` hypothesis is real). -/
theorem resolvesTo_pos (soup : List KeyEvent) (k : String) (s : Nat)
    (h : ResolvesTo soup k s) : 0 < s := by
  obtain ⟨ev, hev, hsome⟩ := List.mem_filterMap.mp h.1
  cases ev with
  | register id key n =>
    cases n with
    | none => simp at hsome
    | some m =>
      by_cases hc : key = k ∧ 0 < m
      · obtain ⟨hk, hm⟩ := hc
        simp [hk, hm] at hsome
        omega
      · simp [hc] at hsome
  | charge id key debit demand => simp at hsome
  | junk id => simp at hsome

/-- **Resolution is antitone under union** (KERNEL-SPEC §3.1's deliberate
    minimum): whatever the merged soup resolves to is ≤ whatever any side
    resolved to, because the side's declared minimum is still a candidate. -/
theorem resolution_antitone (E A : List KeyEvent) (k : String) (s₁ s₂ : Nat)
    (h₁ : ResolvesTo E k s₁) (h₂ : ResolvesTo (E ++ A) k s₂) : s₂ ≤ s₁ := by
  apply h₂.2
  rw [entropiesOf_append]
  exact List.mem_append_left _ h₁.1

/-- Minimum-resolution exists for any nonempty candidate list (the
    relation above is non-vacuous). Self-contained Nat minimum. -/
theorem nat_min_exists (x : Nat) (l : List Nat) :
    ∃ s ∈ x :: l, ∀ t ∈ x :: l, s ≤ t := by
  induction l generalizing x with
  | nil =>
    refine ⟨x, List.mem_cons_self .., ?_⟩
    intro t ht
    rcases List.mem_cons.mp ht with rfl | h
    · omega
    · cases h
  | cons y ys ih =>
    obtain ⟨s, hs, hmin⟩ := ih y
    by_cases hxs : x ≤ s
    · refine ⟨x, List.mem_cons_self .., ?_⟩
      intro t ht
      rcases List.mem_cons.mp ht with rfl | h
      · omega
      · exact Nat.le_trans hxs (hmin t h)
    · refine ⟨s, List.mem_cons_of_mem _ hs, ?_⟩
      intro t ht
      rcases List.mem_cons.mp ht with rfl | h
      · omega
      · exact hmin t h

/-- Any key with at least one well-formed register resolves. -/
theorem resolution_exists (soup : List KeyEvent) (k : String)
    (h : entropiesOf soup k ≠ []) : ∃ s, ResolvesTo soup k s := by
  cases hl : entropiesOf soup k with
  | nil => exact absurd hl h
  | cons x xs =>
    obtain ⟨s, hs, hmin⟩ := nat_min_exists x xs
    exact ⟨s, by rw [ResolvesTo, hl]; exact ⟨hs, hmin⟩⟩

/-- Merge moves BOTH coordinates the bad way — more cumulative AND a
    lower (min-resolved) entropy — and the class still never drops. Pure
    arithmetic composition of Monotone.lean's two laws. -/
theorem merge_never_lowers_class (c₁ c₂ s₁ s₂ : Nat)
    (hc : c₁ ≤ c₂) (hpos : 0 < s₂) (hs : s₂ ≤ s₁) :
    rank c₁ s₁ ≤ rank c₂ s₂ :=
  Nat.le_trans (rank_mono_cumulative c₁ c₂ s₁ hc)
    (rank_antitone_entropy c₂ s₁ s₂ hpos hs)

/-- **Class escalation, AT THE SOUP LEVEL.** For any raw extension A:
    the merged soup's resolved account never carries a lower leakage
    class than any side's. Cumulative only grows (`soup_sums_mono`),
    resolution only drops (`resolution_antitone`), and Monotone.lean's
    rank laws compose (`merge_never_lowers_class`). This is the CRDT
    sentence the registers have been claiming informally, finally stated
    over the event soup itself. -/
theorem class_escalates_over_soups (E A : List KeyEvent) (k : String)
    (s₁ s₂ : Nat) (h₁ : ResolvesTo E k s₁) (h₂ : ResolvesTo (E ++ A) k s₂) :
    rank (cumulativeOf E k) s₁ ≤ rank (cumulativeOf (E ++ A) k) s₂ :=
  merge_never_lowers_class _ _ _ _
    (soup_sums_mono E A k).1
    (resolvesTo_pos (E ++ A) k s₂ h₂)
    (resolution_antitone E A k s₁ s₂ h₁ h₂)

/-- **Incident latch, AT THE SOUP LEVEL.** Once a key's merged demand
    crosses the unsafe line, no extension un-crosses it: demand only
    grows, resolution only drops, and `incident_mono` carries the latch. -/
theorem incident_escalates_over_soups (E A : List KeyEvent) (k : String)
    (s₁ s₂ : Nat) (h₁ : ResolvesTo E k s₁) (h₂ : ResolvesTo (E ++ A) k s₂)
    (hfire : demandedOf E k * 1000 ≥ unsafePermille * s₁) :
    demandedOf (E ++ A) k * 1000 ≥ unsafePermille * s₂ := by
  have hd : demandedOf E k ≤ demandedOf (E ++ A) k := (soup_sums_mono E A k).2
  have hs : s₂ ≤ s₁ := resolution_antitone E A k s₁ s₂ h₁ h₂
  have h1 := incident_mono (demandedOf E k) (demandedOf (E ++ A) k) s₁ hd hfire
  unfold unsafePermille at h1 ⊢
  omega

/-- The soup-level escalation, witnessed end to end: the extension both
    RAISES cumulative (10 → 70) and LOWERS the resolved entropy
    (1000 → 100), and the class jumps 0 → 3. Never the other way. -/
def keySoupE : List KeyEvent :=
  [ .register "g1" "k" (some 1000),
    .charge "c1" "k" (some 10) (some 10) ]

def keySoupA : List KeyEvent :=
  [ .register "g2" "k" (some 100),
    .charge "c2" "k" (some 60) (some 60) ]

theorem class_escalation_example :
    ResolvesTo keySoupE "k" 1000 ∧
    ResolvesTo (keySoupE ++ keySoupA) "k" 100 ∧
    rank (cumulativeOf keySoupE "k") 1000 = 0 ∧
    rank (cumulativeOf (keySoupE ++ keySoupA) "k") 100 = 3 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> decide

end ChargeKernel
