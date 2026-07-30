/-
ChargeKernel.Monotone — the laws the CRDT story rests on.

The ledger's merge is set union and its fold is a sum, so the safety of
"merge freely, in any order" reduces to: the derived verdicts can only
ESCALATE as facts are added. Three laws:

  rank_mono_cumulative   more accepted leakage never lowers the class
  rank_antitone_entropy  a lower (more conservative) declared entropy never
                         lowers the class — why registration-poison
                         quarantine resolves to the MINIMUM (ledger.py)
  merge_escalates        a superset of debit facts never lowers the class
  incident_mono          the incident latch is monotone in demand

`rank` is stated in counting form (how many thresholds are crossed) and
proven equal to SPEC §1.5's ordered-branch form (`rank_eq_spec`), so the
monotonicity theorems apply to the normative definition, not a convenient
variant.
-/
import ChargeKernel.Basic

namespace ChargeKernel

/-- Leakage class as a rank 0..4 (negligible, bounded, material, unsafe,
    reconstructed), counting crossed thresholds. -/
def rank (cumulative entropy : Nat) : Nat :=
  (if 50 * entropy < min cumulative entropy * 1000 then 1 else 0)
  + (if 250 * entropy < min cumulative entropy * 1000 then 1 else 0)
  + (if 500 * entropy < min cumulative entropy * 1000 then 1 else 0)
  + (if 800 * entropy < min cumulative entropy * 1000 then 1 else 0)

/-- The counting form IS the SPEC §1.5 ordered-branch form. -/
theorem rank_eq_spec (c s : Nat) :
    rank c s =
      (if (min c s) * 1000 ≤ 50 * s then 0
       else if (min c s) * 1000 ≤ 250 * s then 1
       else if (min c s) * 1000 ≤ 500 * s then 2
       else if (min c s) * 1000 ≤ 800 * s then 3
       else 4) := by
  unfold rank
  repeat' split
  all_goals omega

/-- More accepted leakage never lowers the class. -/
theorem rank_mono_cumulative (c₁ c₂ s : Nat) (h : c₁ ≤ c₂) :
    rank c₁ s ≤ rank c₂ s := by
  unfold rank
  repeat' split
  all_goals omega

/-- A lower declared entropy never lowers the class (s₂ > 0: a zero-entropy
    declaration is malformed and quarantined upstream, ledger.py I7). This
    is the law that licenses minimum-resolution of conflicting
    registrations: resolving DOWN can only escalate. -/
theorem rank_antitone_entropy (c s₁ s₂ : Nat) (h2 : 0 < s₂) (h : s₂ ≤ s₁) :
    rank c s₁ ≤ rank c s₂ := by
  unfold rank
  repeat' split
  all_goals omega

/-- Sums only grow under superset (here: sublist) of debit facts. -/
theorem sublist_sum_le (l₁ l₂ : List Nat) (h : l₁.Sublist l₂) :
    l₁.sum ≤ l₂.sum := by
  induction h with
  | slnil => simp
  | cons a _ ih => simp; omega
  | cons₂ a _ ih => simp; omega

/-- Merge only escalates: if one auditor saw a sub-collection of the debit
    facts another saw, its leakage class is at most the other's. -/
theorem merge_escalates (debits₁ debits₂ : List Nat) (s : Nat)
    (h : debits₁.Sublist debits₂) :
    rank debits₁.sum s ≤ rank debits₂.sum s :=
  rank_mono_cumulative _ _ s (sublist_sum_le _ _ h)

/-- The incident latch is monotone in demand: once the merged demand crosses
    the unsafe line, more facts cannot un-cross it. -/
theorem incident_mono (d₁ d₂ s : Nat) (h : d₁ ≤ d₂)
    (hfire : d₁ * 1000 ≥ unsafePermille * s) :
    d₂ * 1000 ≥ unsafePermille * s := by
  unfold unsafePermille at *
  omega

end ChargeKernel
