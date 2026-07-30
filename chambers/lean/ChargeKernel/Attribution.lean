/-
ChargeKernel.Attribution — charge-attribution/1's split rule as
machine-checked law (ATTRIBUTION-SPEC.md V.3; FRAMEWORKS F6; the G20 gap).

Two laws, one sharp negative:

  * `walk_efficiency` — the Shapley decomposition's efficiency arm: for
    ANY coalition-value function v and ANY ordering of the players, the
    sum of prefix marginals telescopes EXACTLY to v(order) - v(∅).
    Nothing is minted and nothing is burned by decomposing a pot's worth
    into per-player marginals — the identity the allocator's denominator
    (Σ numerators = n!·v(N)) leans on, proven for every ordering at once.
  * `alloc_conserves` (with `floors_le`, `shortfall_lt`,
    `shortfall_exact`) — the largest-remainder allocation of SPEC V.3
    conserves the pot exactly: floors fall short of P by a shortfall k
    that (a) satisfies D·k = Σ remainders — the multiplicative
    characterization, stated without division so no rounding hides in
    the statement — and (b) is strictly under n, so k bonus units of one
    microcredit each always fit; floors plus ANY k-unit bonus assignment
    sum to P. The tie-break rule (which k rows get the unit) is
    deliberately NOT modeled: conservation holds for every choice, which
    is exactly why determinism can be an implementation convention.
  * `floor_only_leaks` — the sharp negative: floors WITHOUT the
    remainder arm lose a unit on weights [1,1,1] at pot 10000, by
    kernel reduction. The remainder rule is load-bearing, not
    decorative — the attribution analog of `f1_prefix_breaks`.

Executable bindings: the alpha story's arithmetic (a source carrying
numerator 2 of denominator 16000 — Shapley over capacities 1 vs 7999 —
is paid exactly 12_500_000_000 microcredits of a 10^14 pot) reduces by
`rfl`; if the spec's worked example and this file ever disagree, the
build stops.

NOT claimed (named so the register stays honest):

  * The subset-weight formula of attribution.py equals the
    permutation-walk decomposition modeled here — the classical Shapley
    identity. It is property-tested exactly (brute force over all
    orderings for n ≤ 5, test_attribution.py) and not machine-proven.
  * Anything about max-flow: v enters as an arbitrary function. The DPI
    characteristic function's own arithmetic is owned by the Python/Rust
    P-audit and its 17-test lane.
-/
import ChargeKernel.Basic

namespace ChargeKernel

/-! ### Walk efficiency — marginals telescope, for every ordering -/

/-- Prefix marginals: walking the ordering `l` after having seated
`pre`, each player contributes `v (pre ++ [p]) - v pre`. Int-valued —
nothing here assumes monotone games. -/
def walkMarginals (v : List String → Int) : List String → List String → Int
  | _, [] => 0
  | pre, p :: rest => (v (pre ++ [p]) - v pre) + walkMarginals v (pre ++ [p]) rest

theorem walk_telescopes (v : List String → Int) (l pre : List String) :
    walkMarginals v pre l = v (pre ++ l) - v pre := by
  induction l generalizing pre with
  | nil => simp [walkMarginals]
  | cons p rest ih =>
    have h := ih (pre ++ [p])
    simp only [walkMarginals, h, List.append_assoc, List.singleton_append]
    omega

/-- Efficiency: the marginal decomposition of any ordering exhausts
exactly the grand coalition's worth over the empty coalition's. -/
theorem walk_efficiency (v : List String → Int) (o : List String) :
    walkMarginals v [] o = v o - v [] := by
  simpa using walk_telescopes v o []

/-! ### Largest-remainder allocation conserves the pot (SPEC V.3) -/

/-- Sum of floor shares of pot `P` over weights `l` at denominator `D`. -/
def floorsSum (P D : Nat) (l : List Nat) : Nat :=
  (l.map fun x => P * x / D).sum

/-- Sum of the corresponding remainders. -/
def remsSum (P D : Nat) (l : List Nat) : Nat :=
  (l.map fun x => P * x % D).sum

/-- The division decomposition, summed: P·Σl = D·floors + rems, for any
list and any D (including 0 — Nat division is total, as is the fold). -/
theorem sum_decomp (P D : Nat) (l : List Nat) :
    P * l.sum = D * floorsSum P D l + remsSum P D l := by
  induction l with
  | nil => simp [floorsSum, remsSum]
  | cons x xs ih =>
    have hdm := Nat.div_add_mod (P * x) D
    simp only [floorsSum, remsSum, List.map_cons, List.sum_cons,
      Nat.mul_add] at *
    omega

/-- Each remainder is under D, so the remainder pile is under n·D
(stated additively: rems + n ≤ n·D — subtraction-free). -/
theorem rems_bounded (P D : Nat) (hD : 0 < D) (l : List Nat) :
    remsSum P D l + l.length ≤ l.length * D := by
  induction l with
  | nil => simp [remsSum]
  | cons x xs ih =>
    have hlt : P * x % D < D := Nat.mod_lt _ hD
    have hsm : (xs.length + 1) * D = xs.length * D + D := Nat.succ_mul _ _
    simp only [remsSum, List.map_cons, List.sum_cons, List.length_cons] at *
    omega

/-- Floors never overshoot the pot. -/
theorem floors_le (P D : Nat) (nums : List Nat) (hD : 0 < D)
    (hsum : nums.sum = D) : floorsSum P D nums ≤ P := by
  have h := sum_decomp P D nums
  rw [hsum] at h
  have hle : D * floorsSum P D nums ≤ D * P := by
    have : P * D = D * P := Nat.mul_comm _ _
    omega
  exact Nat.le_of_mul_le_mul_left hle hD

/-- The shortfall is EXACTLY the remainder pile, multiplicatively:
D·(P − floors) = Σ remainders. No division appears in the statement, so
no rounding can hide in it. -/
theorem shortfall_exact (P D : Nat) (nums : List Nat) (hD : 0 < D)
    (hsum : nums.sum = D) :
    D * (P - floorsSum P D nums) = remsSum P D nums := by
  have h := sum_decomp P D nums
  rw [hsum] at h
  have hF : floorsSum P D nums ≤ P := floors_le P D nums hD hsum
  -- write P = F + k and distribute: D·P = D·F + D·k
  have hmul := Nat.mul_add D (floorsSum P D nums) (P - floorsSum P D nums)
  have hPk : floorsSum P D nums + (P - floorsSum P D nums) = P := by omega
  rw [hPk] at hmul
  have hcomm : P * D = D * P := Nat.mul_comm _ _
  omega

/-- Left-factor cancellation for `<`, derived locally without
`Classical.choice` (the core lemma of this name carries it, and the
axiom guards in ChargeKernel.lean would stop the build). -/
private theorem lt_of_mul_lt_mul {a b c : Nat} (h : a * b < a * c) : b < c := by
  rcases Nat.lt_or_ge b c with hbc | hbc
  · exact hbc
  · exact absurd h (Nat.not_lt.mpr (Nat.mul_le_mul_left a hbc))

/-- The shortfall fits: strictly fewer bonus units than players (so a
0/1-per-row bonus assignment distributing it always exists). -/
theorem shortfall_lt (P D : Nat) (nums : List Nat) (hD : 0 < D)
    (hsum : nums.sum = D) : P - floorsSum P D nums < nums.length := by
  have hne : 0 < nums.length := by
    cases nums with
    | nil => rw [List.sum_nil] at hsum; omega
    | cons _ xs => exact Nat.succ_pos xs.length
  have hex := shortfall_exact P D nums hD hsum
  have hbd := rems_bounded P D hD nums
  -- D·k = rems < n·D  ⇒  k < n
  have hlt : D * (P - floorsSum P D nums) < D * nums.length := by
    have h1 : nums.length * D = D * nums.length := Nat.mul_comm _ _
    omega
  exact lt_of_mul_lt_mul hlt

/-- **The conservation law.** Floors plus ANY bonus assignment that
distributes the shortfall sum to the pot exactly — one microcredit in,
one microcredit out, for every tie-break rule an implementation could
choose. -/
theorem alloc_conserves (P D : Nat) (nums bonus : List Nat) (hD : 0 < D)
    (hsum : nums.sum = D)
    (hb : bonus.sum = P - floorsSum P D nums) :
    floorsSum P D nums + bonus.sum = P := by
  have hF : floorsSum P D nums ≤ P := floors_le P D nums hD hsum
  omega

/-! ### The sharp negative, and the alpha story by kernel reduction -/

/-- Floors WITHOUT the remainder arm leak: weights [1,1,1], pot 10000 —
a microcredit vanishes. The remainder rule is load-bearing. -/
theorem floor_only_leaks : floorsSum 10000 3 [1, 1, 1] = 9999 := by decide

/-- ...and the shortfall theorems say exactly one bonus unit repairs it:
3·(10000 − 9999) = Σ remainders = 3. -/
example : 3 * (10000 - floorsSum 10000 3 [1, 1, 1])
    = remsSum 10000 3 [1, 1, 1] := by decide

/-- The alpha story's arithmetic (ATTRIBUTION-SPEC V.0/V.3;
test_attribution.py): Shapley numerators over declared capacities 1 vs
7999 are (2, 15998) with denominator 16000, and the $100M pot pays the
1/8000 contributor exactly $12,500.000000 — floors exhaust the pot
(shortfall 0), by kernel reduction. -/
example : floorsSum 100000000000000 16000 [2, 15998] = 100000000000000 := by
  decide

/-- The same, share by share: the two floor payouts. -/
example : 100000000000000 * 2 / 16000 = 12500000000 := rfl
example : 100000000000000 * 15998 / 16000 = 99987500000000 := rfl

end ChargeKernel
