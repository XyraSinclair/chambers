/-
ChargeKernel.Algebra — the indexed charge algebra and the fold homomorphism.

ASSURANCE.md L4 target 1. The algebra is the ordered commutative monoid of
charge vectors indexed by (source, reader) pairs — pointwise addition,
pointwise order, zero vector — with the coalition law as a distinguished
predicate: `SelfFree` (zero at self-leakage: telling a silo its own secret
is free). The theorems:

  * the monoid/order laws, stated pointwise (no funext, no extra axioms);
  * `SelfFree` holds at zero and is closed under addition and bounded
    below by order — the coalition zero-point is a sub-monoid, so
    composing self-free work stays self-free;
  * `fold_append` — THE homomorphism: the ledger fold maps the CRDT merge
    of disjoint fact sets (content-addressed union; distinct facts append)
    to algebra addition, exactly. "The implementation's fold is a
    homomorphism into the algebra" — merging ledgers and adding charges
    are the same operation seen twice;
  * `fold_sublist_le` — a sub-collection of facts never charges more
    (the algebra face of Monotone.lean's merge-only-escalates);
  * `fold_selfFree` — a ledger with no self-pair facts folds into the
    coalition zero-point.

Honest scope: SEQUENTIAL SUB-ADDITIVITY of real information (the claim
that a composed emission carries at most the sum of its parts' charges) is
a property of the ESTIMATOR, not of this algebra — the algebra adds what
the estimator attests, and whether the attestation upper-bounds reality is
L3's job (the estimator probe). Idempotent dedup of identical facts is the
content-addressing layer's job (same bytes ⟹ same sha256 id ⟹ one fact),
proven at L1 by the golden corpus, assumed here as disjointness.
-/

namespace ChargeKernel

/-- A charge vector: millibits charged per (source, reader) pair. -/
def ChargeVec (S : Type) := S × S → Nat

namespace ChargeVec

def zero : ChargeVec S := fun _ => 0

def add (u v : ChargeVec S) : ChargeVec S := fun k => u k + v k

/-- Pointwise order: `u ≤ v` iff u charges no pair more than v does. -/
def Le (u v : ChargeVec S) : Prop := ∀ k, u k ≤ v k

-- ---- ordered commutative monoid, pointwise ----

theorem add_assoc (u v w : ChargeVec S) (k : S × S) :
    add (add u v) w k = add u (add v w) k := Nat.add_assoc _ _ _

theorem add_comm (u v : ChargeVec S) (k : S × S) :
    add u v k = add v u k := Nat.add_comm _ _

theorem zero_add (v : ChargeVec S) (k : S × S) : add zero v k = v k :=
  Nat.zero_add _

theorem add_zero (v : ChargeVec S) (k : S × S) : add v zero k = v k :=
  Nat.add_zero _

theorem le_refl (v : ChargeVec S) : Le v v := fun _ => Nat.le_refl _

theorem le_trans {u v w : ChargeVec S} (h₁ : Le u v) (h₂ : Le v w) : Le u w :=
  fun k => Nat.le_trans (h₁ k) (h₂ k)

/-- Adding charges is monotone in both arguments: more observation never
    charges less. -/
theorem add_le_add {u₁ u₂ v₁ v₂ : ChargeVec S}
    (hu : Le u₁ u₂) (hv : Le v₁ v₂) : Le (add u₁ v₁) (add u₂ v₂) :=
  fun k => Nat.add_le_add (hu k) (hv k)

/-- Composition can only grow a charge: `u ≤ u + v`. -/
theorem le_add_right (u v : ChargeVec S) : Le u (add u v) :=
  fun _ => Nat.le_add_right _ _

-- ---- the coalition law: zero at self-leakage ----

/-- The coalition zero-point: a vector that charges nothing for any silo
    reading itself. I(Y; Sᵢ | Sᵢ) = 0 — self-leakage is free. -/
def SelfFree (v : ChargeVec S) : Prop := ∀ s : S, v (s, s) = 0

theorem selfFree_zero : SelfFree (zero : ChargeVec S) := fun _ => rfl

/-- The zero-point is closed under composition: self-free work composed
    with self-free work is self-free. The sub-monoid law. -/
theorem selfFree_add {u v : ChargeVec S}
    (hu : SelfFree u) (hv : SelfFree v) : SelfFree (add u v) := by
  intro s
  show u (s, s) + v (s, s) = 0
  rw [hu s, hv s]

/-- Anything below a self-free vector is self-free: the zero-point is
    downward closed. -/
theorem selfFree_of_le {u v : ChargeVec S}
    (hv : SelfFree v) (h : Le u v) : SelfFree u := by
  intro s
  have := h (s, s)
  rw [hv s] at this
  exact Nat.le_zero.mp this

end ChargeVec

-- ---- the ledger fold and its homomorphism ----

/-- A debit fact: (source, reader) key and attested millibits. Fact
    identity (sha256 content addressing) lives one layer down; by the time
    facts reach the fold, distinct facts are distinct list entries and the
    CRDT union of disjoint sets is append. -/
abbrev Fact (S : Type) := (S × S) × Nat

/-- The fold: total millibits charged per pair, over a fact collection. -/
def fold [DecidableEq S] : List (Fact S) → ChargeVec S
  | []          => ChargeVec.zero
  | (k, n) :: L => fun k' => (if k' = k then n else 0) + fold L k'

/-- **The homomorphism.** The fold maps ledger merge (append of disjoint
    fact sets) to algebra addition, exactly: fold (L₁ ∪ L₂) = fold L₁ +
    fold L₂, pointwise. Merging ledgers and adding charge vectors are the
    same operation. -/
theorem fold_append [DecidableEq S] (L₁ L₂ : List (Fact S)) (k : S × S) :
    fold (L₁ ++ L₂) k = ChargeVec.add (fold L₁) (fold L₂) k := by
  induction L₁ with
  | nil =>
    show fold L₂ k = ChargeVec.add ChargeVec.zero (fold L₂) k
    rw [ChargeVec.zero_add]
  | cons f L₁ ih =>
    obtain ⟨fk, fn⟩ := f
    show (if k = fk then fn else 0) + fold (L₁ ++ L₂) k
       = ((if k = fk then fn else 0) + fold L₁ k) + fold L₂ k
    rw [ih]
    exact (Nat.add_assoc _ _ _).symm

/-- A sub-collection of facts never charges more — the algebra face of
    merge-only-escalates. -/
theorem fold_sublist_le [DecidableEq S] {L₁ L₂ : List (Fact S)}
    (h : L₁.Sublist L₂) : ChargeVec.Le (fold L₁) (fold L₂) := by
  intro k
  induction h with
  | slnil => exact Nat.le_refl _
  | @cons L₁ L₂ f _ ih =>
    obtain ⟨fk, fn⟩ := f
    show fold L₁ k ≤ (if k = fk then fn else 0) + fold L₂ k
    exact Nat.le_trans ih (Nat.le_add_left _ _)
  | @cons₂ L₁ L₂ f _ ih =>
    obtain ⟨fk, fn⟩ := f
    show (if k = fk then fn else 0) + fold L₁ k
       ≤ (if k = fk then fn else 0) + fold L₂ k
    exact Nat.add_le_add_left ih _

/-- A ledger whose facts never charge a self-pair folds into the coalition
    zero-point. The meter preserves the zero: intra-silo work stays free. -/
theorem fold_selfFree [DecidableEq S] (L : List (Fact S))
    (h : ∀ f ∈ L, ∀ s : S, f.1 ≠ (s, s)) :
    ChargeVec.SelfFree (fold L) := by
  intro s
  induction L with
  | nil => rfl
  | cons f L ih =>
    obtain ⟨fk, fn⟩ := f
    show (if (s, s) = fk then fn else 0) + fold L (s, s) = 0
    have hne : (s, s) ≠ fk := fun heq => h (fk, fn) (List.mem_cons_self ..) s heq.symm
    rw [if_neg hne, ih (fun g hg => h g (List.mem_cons_of_mem _ hg))]

end ChargeKernel
