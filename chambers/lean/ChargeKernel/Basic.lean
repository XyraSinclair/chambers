/-
ChargeKernel.Basic — the egress-accountant/1 decision core, as a Lean model.

This is the ~40 lines where wrongness is catastrophic (ASSURANCE.md L4):
the SPEC §2.2 step function A–E over one account, in exact Nat arithmetic.
Nat subtraction is truncated, which is exactly the SPEC's
`max 0 (ceiling - cumulative)` — the model matches the normative text by
construction, and the worked micro-example of SPEC §4 is replayed by `rfl`
at the bottom of ChargeKernel.lean (the executable binding to the document).

Theorems here (per account, any charge sequence):
  * `run_cumulative_le_ceiling` — the odometer never passes the ceiling.
  * `run_cumulative_eq_accepted` — cumulative is exactly the sum of
    accepted debits (the fold IS the meter).
  * monotonicity of both counters, and frame lemmas (entropy/ceiling fixed).
-/

namespace ChargeKernel

/-- SPEC §1.5 / §2.2 — the incident threshold, per-mille. -/
def unsafePermille : Nat := 800

/-- SPEC §1.4 CompositionState, key-elided (the key indexes a map above
    this model; every law here is per-account). -/
structure Account where
  entropy    : Nat
  ceiling    : Nat
  cumulative : Nat  := 0
  demanded   : Nat  := 0
  blocked    : Bool := false
  incident   : Bool := false
deriving Repr, DecidableEq

/-- One charge attempt: the estimator's admissibility verdict (SPEC §1.3,
    abstracted to its outcome) and the attested integer millibits. -/
structure Charge where
  admissible : Bool
  bits       : Nat
deriving Repr, DecidableEq

inductive Reason where
  | emitted | refusedEstimator | refusedBlocked | refusedCeiling
deriving Repr, DecidableEq

/-- SPEC §2.2, steps A–E in order. Steps C/D/E read only fields that
    step B does not touch, so B's demanded/incident update is inlined
    into each branch (definitionally the same account). -/
def step (a : Account) (c : Charge) : Account × Reason :=
  if c.admissible = false then
    (a, .refusedEstimator)                                          -- step A
  else if a.blocked then                                            -- step C
    ({ a with demanded := a.demanded + c.bits,
              incident := a.incident
                || decide ((a.demanded + c.bits) * 1000 ≥ unsafePermille * a.entropy) },
     .refusedBlocked)
  else if a.ceiling - a.cumulative < c.bits then                    -- step D
    ({ a with demanded := a.demanded + c.bits,
              incident := a.incident
                || decide ((a.demanded + c.bits) * 1000 ≥ unsafePermille * a.entropy),
              blocked := true },
     .refusedCeiling)
  else                                                              -- step E
    ({ a with demanded := a.demanded + c.bits,
              incident := a.incident
                || decide ((a.demanded + c.bits) * 1000 ≥ unsafePermille * a.entropy),
              cumulative := a.cumulative + c.bits,
              blocked := decide (a.cumulative + c.bits ≥ a.ceiling) },
     .emitted)

/-- Fold a charge sequence through one account. -/
def run (a : Account) : List Charge → Account
  | []      => a
  | c :: cs => run (step a c).1 cs

/-- The bits that actually crossed: sum of debits of accepted charges. -/
def acceptedBits (a : Account) : List Charge → Nat
  | []      => 0
  | c :: cs =>
    (if (step a c).2 = .emitted then c.bits else 0) + acceptedBits (step a c).1 cs

/-- The per-step verdict trace — the observable the golden replay pins. -/
def runReasons (a : Account) : List Charge → List Reason
  | []      => []
  | c :: cs => (step a c).2 :: runReasons (step a c).1 cs

-- ---- frame lemmas: step never moves entropy or ceiling ----

theorem step_ceiling (a : Account) (c : Charge) : (step a c).1.ceiling = a.ceiling := by
  unfold step
  split
  · rfl
  · split
    · rfl
    · split <;> rfl

theorem step_entropy (a : Account) (c : Charge) : (step a c).1.entropy = a.entropy := by
  unfold step
  split
  · rfl
  · split
    · rfl
    · split <;> rfl

theorem run_ceiling (a : Account) (cs : List Charge) : (run a cs).ceiling = a.ceiling := by
  induction cs generalizing a with
  | nil => rfl
  | cons c cs ih => rw [run, ih, step_ceiling]

-- ---- monotonicity: the two counters never decrease ----

theorem step_cumulative_mono (a : Account) (c : Charge) :
    a.cumulative ≤ (step a c).1.cumulative := by
  unfold step
  split
  · exact Nat.le_refl _
  · split
    · exact Nat.le_refl _
    · split
      · exact Nat.le_refl _
      · simp

theorem step_demanded_mono (a : Account) (c : Charge) :
    a.demanded ≤ (step a c).1.demanded := by
  unfold step
  split
  · exact Nat.le_refl _
  · split
    · simp
    · split
      · simp
      · simp

theorem run_cumulative_mono (a : Account) (cs : List Charge) :
    a.cumulative ≤ (run a cs).cumulative := by
  induction cs generalizing a with
  | nil => exact Nat.le_refl _
  | cons c cs ih => exact Nat.le_trans (step_cumulative_mono a c) (ih _)

theorem run_demanded_mono (a : Account) (cs : List Charge) :
    a.demanded ≤ (run a cs).demanded := by
  induction cs generalizing a with
  | nil => exact Nat.le_refl _
  | cons c cs ih => exact Nat.le_trans (step_demanded_mono a c) (ih _)

-- ---- the odometer law: cumulative never passes the ceiling ----

theorem step_cumulative_le_ceiling (a : Account) (c : Charge)
    (h : a.cumulative ≤ a.ceiling) : (step a c).1.cumulative ≤ a.ceiling := by
  unfold step
  split
  · simpa
  · split
    · simpa
    · split
      · simpa
      · rename_i _ _ hle
        simp only [Nat.not_lt] at hle
        simp
        omega

theorem run_cumulative_le_ceiling (a : Account) (cs : List Charge)
    (h : a.cumulative ≤ a.ceiling) : (run a cs).cumulative ≤ a.ceiling := by
  induction cs generalizing a with
  | nil => simpa [run]
  | cons c cs ih =>
    rw [run]
    have hc := step_cumulative_le_ceiling a c h
    have hrec := ih (step a c).1 (by rw [step_ceiling]; exact hc)
    rw [step_ceiling] at hrec
    exact hrec

-- ---- accounting exactness: cumulative = initial + accepted debits ----

theorem step_cumulative_eq (a : Account) (c : Charge) :
    (step a c).1.cumulative
      = a.cumulative + (if (step a c).2 = .emitted then c.bits else 0) := by
  unfold step
  split
  · simp
  · split
    · simp
    · split
      · simp
      · simp

theorem run_cumulative_eq_accepted (a : Account) (cs : List Charge) :
    (run a cs).cumulative = a.cumulative + acceptedBits a cs := by
  induction cs generalizing a with
  | nil => simp [run, acceptedBits]
  | cons c cs ih =>
    rw [run, acceptedBits, ih (step a c).1, step_cumulative_eq]
    omega

/-- The per-account cap on accepted debits — premise (2) of the global cap
    theorem, proven rather than assumed: from any within-ceiling start, the
    sum of accepted debits over ANY charge sequence fits in the remaining
    budget, hence is at most the ceiling. -/
theorem acceptedBits_le_ceiling (a : Account) (cs : List Charge)
    (hle : a.cumulative ≤ a.ceiling) :
    acceptedBits a cs ≤ a.ceiling := by
  have h1 := run_cumulative_le_ceiling a cs hle
  have h2 := run_cumulative_eq_accepted a cs
  omega

end ChargeKernel
