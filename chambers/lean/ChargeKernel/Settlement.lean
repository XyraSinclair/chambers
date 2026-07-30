/-
ChargeKernel.Settlement — conservation for charge-settlement/2.

The value layer's analog of the global cap theorem. Model: account
balances as a list of Nats, escrow remainders as a grow-only list of
Nats, attestation-bond remainders as a grow-only list of Nats, a running
total of declared deposits, and the guarded honest ops (SETTLEMENT-SPEC
§4 and Part II §8). The /2 extension adds bond lock/return/slash. The
theorem:

  conservation: under ANY interleaving of guarded ops,
      Σ available + Σ escrow remainders + Σ bond remainders = Σ deposits.

Every declared microcredit is available, escrowed, or bonded, always. The
guards are load-bearing and Lean shows it sharply: in Nat, truncated
subtraction means an UNGUARDED escrow or bond lock (locking more than the
actor has) silently DESTROYS the shortfall and the identity breaks —
exhibited below as executable counterexamples (`decide`), not comments.
The honest issuer's refusals are exactly what the arithmetic demands.

Non-negativity is definitional here (Nat); its ledger-side content — a
lying issuer drives a SIGNED balance negative and is convicted (S1/S2) —
lives in settlement.py's audit, which this model deliberately excludes:
Byzantine issuers are the audit's problem, honest conservation is this
theorem's, the same division of labor as GlobalCap vs the I-codes.
-/
import ChargeKernel.Basic

namespace ChargeKernel

structure SettleState where
  avail     : List Nat  -- account balances, by index
  esc       : List Nat  -- escrow remainders, by index (grow-only)
  bonds     : List Nat  -- attestation-bond remainders, by index (grow-only)
  deposited : Nat       -- Σ declared deposits
deriving Repr, DecidableEq

inductive SettleOp where
  | deposit (a : Nat) (amt : Nat)                    -- declared inflow to account a
  | escrowNew (payer : Nat) (amt : Nat)              -- lock payer value into a new escrow
  | release (e : Nat) (payee : Nat) (amt : Nat)      -- disburse from escrow e to payee
  | refund  (e : Nat) (payer : Nat) (amt : Nat)      -- return from escrow e to payer
  | attestBond (attestor : Nat) (amt : Nat)          -- lock attestor value into a new bond
  | bondReturn (b : Nat) (attestor : Nat) (amt : Nat) -- return from bond b to attestor
  | bondSlash (b : Nat) (beneficiary : Nat) (amt : Nat) -- slash from bond b to beneficiary
deriving Repr, DecidableEq

/-- One guarded honest-issuer step. A failed guard is a REFUSAL: the state
    does not move (SETTLEMENT-SPEC §4 — the issuer refuses live). Balances
    are read with `getD` (default 0), guards with plain decidable ifs. -/
def settleStep (s : SettleState) (op : SettleOp) : SettleState :=
  match op with
  | .deposit a amt =>
    if a < s.avail.length then
      { s with avail := s.avail.set a (s.avail.getD a 0 + amt),
               deposited := s.deposited + amt }
    else s
  | .escrowNew payer amt =>
    if payer < s.avail.length ∧ amt ≤ s.avail.getD payer 0 then
      { s with avail := s.avail.set payer (s.avail.getD payer 0 - amt),
               esc := s.esc ++ [amt] }
    else s
  | .release e payee amt =>
    if e < s.esc.length ∧ payee < s.avail.length ∧ amt ≤ s.esc.getD e 0 then
      { s with esc := s.esc.set e (s.esc.getD e 0 - amt),
               avail := s.avail.set payee (s.avail.getD payee 0 + amt) }
    else s
  | .refund e payer amt =>
    if e < s.esc.length ∧ payer < s.avail.length ∧ amt ≤ s.esc.getD e 0 then
      { s with esc := s.esc.set e (s.esc.getD e 0 - amt),
               avail := s.avail.set payer (s.avail.getD payer 0 + amt) }
    else s
  | .attestBond attestor amt =>
    if attestor < s.avail.length ∧ amt ≤ s.avail.getD attestor 0 then
      { s with avail := s.avail.set attestor (s.avail.getD attestor 0 - amt),
               bonds := s.bonds ++ [amt] }
    else s
  | .bondReturn b attestor amt =>
    if b < s.bonds.length ∧ attestor < s.avail.length ∧ amt ≤ s.bonds.getD b 0 then
      { s with bonds := s.bonds.set b (s.bonds.getD b 0 - amt),
               avail := s.avail.set attestor (s.avail.getD attestor 0 + amt) }
    else s
  | .bondSlash b beneficiary amt =>
    if b < s.bonds.length ∧ beneficiary < s.avail.length ∧ amt ≤ s.bonds.getD b 0 then
      { s with bonds := s.bonds.set b (s.bonds.getD b 0 - amt),
               avail := s.avail.set beneficiary (s.avail.getD beneficiary 0 + amt) }
    else s

def runSettle (s : SettleState) : List SettleOp → SettleState
  | []        => s
  | op :: ops => runSettle (settleStep s op) ops

/-- The conservation quantity: where every microcredit currently sits. -/
abbrev holdings (s : SettleState) : Nat := s.avail.sum + s.esc.sum + s.bonds.sum

abbrev conserved (s : SettleState) : Prop := holdings s = s.deposited

-- ---- sum-over-set lemmas (self-contained, no mathlib) ----

theorem sum_append_singleton (l : List Nat) (a : Nat) :
    (l ++ [a]).sum = l.sum + a := by
  induction l with
  | nil => simp
  | cons x xs ih => simp [ih]; omega

theorem sum_set_add (l : List Nat) (i v : Nat) (h : i < l.length) :
    (l.set i (l.getD i 0 + v)).sum = l.sum + v := by
  induction l generalizing i with
  | nil => simp at h
  | cons x xs ih =>
    cases i with
    | zero => simp [List.set_cons_zero]; omega
    | succ n =>
      have hn : n < xs.length := by simpa using Nat.lt_of_succ_lt_succ h
      simp only [List.set_cons_succ, List.sum_cons, List.getD_cons_succ]
      rw [ih n hn]
      omega

theorem sum_set_sub (l : List Nat) (i v : Nat) (h : i < l.length)
    (hv : v ≤ l.getD i 0) : (l.set i (l.getD i 0 - v)).sum + v = l.sum := by
  induction l generalizing i with
  | nil => simp at h
  | cons x xs ih =>
    cases i with
    | zero =>
      simp only [List.getD_cons_zero] at hv
      simp [List.set_cons_zero]
      omega
    | succ n =>
      have hn : n < xs.length := by simpa using Nat.lt_of_succ_lt_succ h
      have hv' : v ≤ xs.getD n 0 := by simpa using hv
      simp only [List.set_cons_succ, List.sum_cons, List.getD_cons_succ]
      have := ih n hn hv'
      omega

-- ---- conservation ----

theorem settleStep_conserves (s : SettleState) (op : SettleOp)
    (h : conserved s) : conserved (settleStep s op) := by
  have h0 : s.avail.sum + s.esc.sum + s.bonds.sum = s.deposited := h
  cases op with
  | deposit a amt =>
    simp only [settleStep]
    split
    · rename_i ha
      have h1 := sum_set_add s.avail a amt ha
      try dsimp only [conserved, holdings]
      omega
    · exact h
  | escrowNew payer amt =>
    simp only [settleStep]
    split
    · rename_i hg
      have h1 := sum_set_sub s.avail payer amt hg.1 hg.2
      have h2 := sum_append_singleton s.esc amt
      try dsimp only [conserved, holdings]
      omega
    · exact h
  | release e payee amt =>
    simp only [settleStep]
    split
    · rename_i hg
      have h1 := sum_set_add s.avail payee amt hg.2.1
      have h2 := sum_set_sub s.esc e amt hg.1 hg.2.2
      try dsimp only [conserved, holdings]
      omega
    · exact h
  | refund e payer amt =>
    simp only [settleStep]
    split
    · rename_i hg
      have h1 := sum_set_add s.avail payer amt hg.2.1
      have h2 := sum_set_sub s.esc e amt hg.1 hg.2.2
      try dsimp only [conserved, holdings]
      omega
    · exact h
  | attestBond attestor amt =>
    simp only [settleStep]
    split
    · rename_i hg
      have h1 := sum_set_sub s.avail attestor amt hg.1 hg.2
      have h2 := sum_append_singleton s.bonds amt
      try dsimp only [conserved, holdings]
      omega
    · exact h
  | bondReturn b attestor amt =>
    simp only [settleStep]
    split
    · rename_i hg
      have h1 := sum_set_add s.avail attestor amt hg.2.1
      have h2 := sum_set_sub s.bonds b amt hg.1 hg.2.2
      try dsimp only [conserved, holdings]
      omega
    · exact h
  | bondSlash b beneficiary amt =>
    simp only [settleStep]
    split
    · rename_i hg
      have h1 := sum_set_add s.avail beneficiary amt hg.2.1
      have h2 := sum_set_sub s.bonds b amt hg.1 hg.2.2
      try dsimp only [conserved, holdings]
      omega
    · exact h

/-- **Conservation under ANY interleaving of guarded ops**: from any
    conserved state (e.g. the empty bank), every schedule of honest
    deposits, escrows, releases, refunds, and bond operations leaves
    every declared microcredit in exactly one place. -/
theorem runSettle_conserves (s : SettleState) (ops : List SettleOp)
    (h : conserved s) : conserved (runSettle s ops) := by
  induction ops generalizing s with
  | nil => simpa [runSettle]
  | cons op ops ih => exact ih _ (settleStep_conserves s op h)

/-- The empty bank is conserved; hence so is everything reachable. -/
theorem conservation_from_genesis (nAccounts : Nat) (ops : List SettleOp) :
    conserved (runSettle ⟨List.replicate nAccounts 0, [], [], 0⟩ ops) := by
  apply runSettle_conserves
  show (List.replicate nAccounts 0).sum + ([] : List Nat).sum + ([] : List Nat).sum = 0
  simp

/-- The guard is LOAD-BEARING, shown executably: an unguarded escrow of 7
    against a balance of 5 truncates the payer to 0 but locks 7 —
    manufacturing 2 microcredits from nothing. The identity breaks. -/
example :
    ¬ conserved { avail := [5].set 0 (5 - 7), esc := [] ++ [7], bonds := [],
                  deposited := 5 : SettleState } := by
  decide

/-- Whereas the GUARDED step refuses it and conservation holds. -/
example :
    conserved (settleStep { avail := [5], esc := [], bonds := [], deposited := 5 }
                          (.escrowNew 0 7)) := by
  decide

/-- The same load-bearing guard for /2 bonds: an unguarded bond lock of 7
    against a balance of 5 truncates the attestor to 0 but records a bond
    of 7, manufacturing 2 microcredits. -/
example :
    ¬ conserved { avail := [5].set 0 (5 - 7), esc := [], bonds := [] ++ [7],
                  deposited := 5 : SettleState } := by
  decide

/-- Whereas the GUARDED bond step refuses it and conservation holds. -/
example :
    conserved (settleStep { avail := [5], esc := [], bonds := [], deposited := 5 }
                          (.attestBond 0 7)) := by
  decide

end ChargeKernel
