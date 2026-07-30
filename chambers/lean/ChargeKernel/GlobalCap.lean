/-
ChargeKernel.GlobalCap — the lease-partition theorem, at trace level.

PROTOCOL.md states it in two lines of algebra; the real content is the
quantifier: **under ANY interleaving** of node steps, with zero coordination
at charge time. So the model is honest about that: a system is a list of
independent accountants (one per lease — the node's local accountant whose
ceiling IS the lease amount), a schedule is an arbitrary list of
(node index, charge) pairs in arbitrary order, and the theorem quantifies
over every schedule.

  global_cap:  if every account starts within its ceiling and the ceilings
               sum to at most C, then after ANY schedule the cumulative
               debits sum to at most C.

  global_cap_fresh: the deployment form — fresh accountants whose ceilings
               are the granted lease amounts (premise (1), the issuer's
               refusal to over-grant, arrives as `(leases).sum ≤ C`).

Out-of-range node indices are no-ops (a charge against a lease you don't
hold is not a step of any honest accountant; the Byzantine version of that
move lives in the audit, not in this theorem — see PROTOCOL.md non-claims).
-/
import ChargeKernel.Basic

namespace ChargeKernel

/-- One distributed step: node `i` charges its own accountant. -/
def stepAt (sys : List Account) (i : Nat) (c : Charge) : List Account :=
  if h : i < sys.length then sys.set i (step sys[i] c).1 else sys

/-- An arbitrary interleaving of node steps. -/
def runSys (sys : List Account) : List (Nat × Charge) → List Account
  | []             => sys
  | (i, c) :: rest => runSys (stepAt sys i c) rest

def totalCumulative (sys : List Account) : Nat := (sys.map Account.cumulative).sum
def totalCeiling    (sys : List Account) : Nat := (sys.map Account.ceiling).sum

-- ---- helper lemmas ----

theorem sum_map_le_sum_map {α : Type} (f g : α → Nat) (l : List α)
    (h : ∀ a ∈ l, f a ≤ g a) : (l.map f).sum ≤ (l.map g).sum := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons]
    have hx := h x (List.mem_cons_self ..)
    have hxs := ih (fun a ha => h a (List.mem_cons_of_mem _ ha))
    omega

theorem map_set_eq {α β : Type} (f : α → β) (l : List α) (i : Nat) (b : α)
    (hf : ∀ hi : i < l.length, f b = f l[i]) :
    (l.set i b).map f = l.map f := by
  induction l generalizing i with
  | nil => simp
  | cons x xs ih =>
    cases i with
    | zero => simp only [List.set_cons_zero, List.map_cons]
              rw [hf (by simp)]
              rfl
    | succ n =>
      simp only [List.set_cons_succ, List.map_cons]
      rw [ih n (fun hi => hf (by simpa using Nat.succ_lt_succ hi))]

/-- The per-account invariant survives any single distributed step. -/
theorem inv_stepAt (sys : List Account) (i : Nat) (c : Charge)
    (hinv : ∀ a ∈ sys, a.cumulative ≤ a.ceiling) :
    ∀ a ∈ stepAt sys i c, a.cumulative ≤ a.ceiling := by
  unfold stepAt
  split
  · rename_i hi
    intro a ha
    rcases List.mem_or_eq_of_mem_set ha with hmem | heq
    · exact hinv a hmem
    · subst heq
      have hbase := hinv sys[i] (List.getElem_mem hi)
      have h1 := step_cumulative_le_ceiling sys[i] c hbase
      have h2 := step_ceiling sys[i] c
      omega
  · exact fun a ha => hinv a ha

/-- Ceilings are conserved by any distributed step. -/
theorem totalCeiling_stepAt (sys : List Account) (i : Nat) (c : Charge) :
    totalCeiling (stepAt sys i c) = totalCeiling sys := by
  unfold stepAt totalCeiling
  split
  · rw [map_set_eq Account.ceiling sys i _ (fun _ => step_ceiling sys[i] c)]
  · rfl

-- ---- the theorem ----

/-- Global cap under ANY interleaving: every account within its ceiling and
    ceilings summing to ≤ C at the start ⟹ cumulative debits sum to ≤ C
    after every schedule. Zero coordination between accounts is used —
    each step touches exactly one. -/
theorem global_cap (sys : List Account) (sched : List (Nat × Charge)) (C : Nat)
    (hinv : ∀ a ∈ sys, a.cumulative ≤ a.ceiling)
    (hC : totalCeiling sys ≤ C) :
    totalCumulative (runSys sys sched) ≤ C := by
  induction sched generalizing sys with
  | nil =>
    have hsum := sum_map_le_sum_map Account.cumulative Account.ceiling sys hinv
    simp only [runSys, totalCumulative]
    unfold totalCeiling at hC
    omega
  | cons ic rest ih =>
    obtain ⟨i, c⟩ := ic
    exact ih (stepAt sys i c) (inv_stepAt sys i c hinv)
      (by rw [totalCeiling_stepAt]; exact hC)

/-- The deployment form. `leases` are the granted (entropy, amount) pairs;
    premise (1) — Σ amounts ≤ ceiling — is the lease issuer's refusal to
    over-grant; premise (2) is `run_cumulative_le_ceiling`, used through
    `global_cap`'s invariant. -/
def freshAccount (p : Nat × Nat) : Account := { entropy := p.1, ceiling := p.2 }

theorem global_cap_fresh (leases : List (Nat × Nat)) (sched : List (Nat × Charge)) (C : Nat)
    (hC : (leases.map Prod.snd).sum ≤ C) :
    totalCumulative (runSys (leases.map freshAccount) sched) ≤ C := by
  apply global_cap
  · intro a ha
    rcases List.mem_map.1 ha with ⟨p, _, rfl⟩
    simp [freshAccount]
  · unfold totalCeiling
    rw [List.map_map]
    exact hC

end ChargeKernel
