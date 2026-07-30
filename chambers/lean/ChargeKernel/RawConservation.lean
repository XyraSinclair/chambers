/-
ChargeKernel.RawConservation — the 2026-07-06 F1 fix as a machine-checked
law (ASSURANCE L4): SETTLEMENT-SPEC §2's "paired quantities move
all-or-nothing" gating, proven to make the conservation identity
arithmetic on ANY raw soup — including soups containing FORGED events
with non-string parties and non-uint amounts.

Why this file exists. On 2026-07-06 an adversarial review (F1) found
that a forged escrow with a NON-STRING payer minted its amount into the
conservation LHS with a clean audit (1999 ≠ 1000) — in the Python
reference AND the clean-room Rust port, because the spec carried the bug
and the existing Lean conservation proofs modeled only WELL-TYPED events
(Settlement.lean's honest ops; Completeness.lean collapses malformedness
into `junk` by assumption — the spec's rule, but exactly the assumption
under which F1 hides). This file removes that assumption: the event
model carries Option-typed adversarial fields, `none` IS the forged
field, and the identity is proven over every raw soup.

What is claimed:

  * `raw_conservation` / `raw_conservation_canonical` — the SPEC §2
    conservation identity Σ_a available(a) + Σ_e remaining(e) = Σ deposits
    holds for ANY raw soup whatsoever, PROVIDED the fold implements the
    §2 all-or-nothing gates: an escrow's amount enters (remainder AND
    payer's locked_out) only when `amount_ucr` is uint AND `payer` is a
    string; a disbursement counts toward released(e)/refunded(e) only
    when the credited party (payee for the release direction, payer for
    the refund direction) is a string; a deposit counts only when both
    `account` is a string and `amount_ucr` is uint.
  * `f1_prefix_breaks` — the sharp NEGATIVE that proves the gate is
    necessary, not decorative: the PRE-FIX fold (escrow amount gated on
    uint alone, as the spec read before 2026-07-06) evaluated on the F1
    counterexample soup (deposit 1000 + escrow amount=999, payer=none)
    yields 1999 ≠ 1000, by `decide`. The fixed fold on the same soup
    yields 1000 = 1000. This is the theorem that would have caught F1.
  * `s6_complete` / `s6_gate_complete` / `s6_sound` — the S6 audit arm
    that owns the crime: an escrow with a non-string payer or payee is
    convicted (named by event id); any escrow whose positive uint amount
    the fixed fold's gate zeroed IS such a convict; and S6 convicts only
    actually-malformed escrows. SCOPE: this models ONLY the
    payer/payee arm of the SPEC §3 S6 row — the other arms (non-uint
    `amount_ucr`, missing/invalid `seq`, `charge_keys` shape,
    `default_on_expiry` literals, non-string `escrow_id`) are owned by
    the Python/Rust audits and the conformance battery, not here.

Modeling choices, each the spec's rule and not a simplification:

  * `Option Nat` models "uint or not-a-uint"; `Option String` models
    "string or junk". This is the actual adversarial surface F1 used:
    `none` is the forged field. Event ids stay plain `String` because
    ids are content addresses — the ledger's KEY, computed by the
    substrate, not attacker-supplied content; an event without an id is
    not in the soup at all.
  * The soup is a List; the real ledger is a content-addressed set.
    Every theorem is proven for ALL lists — a strict superset containing
    every Nodup soup — so nothing leans on dedup.
  * Sums are Int-valued: SPEC §2 computes `available`/`remaining` in
    signed arithmetic (a negative value is the S1/S2 crime, recorded,
    not clamped).
  * A default_resolution is the release/refund its DECLARED direction
    makes it (§2), the same choice as Completeness.lean; the direction
    machinery itself is not re-modeled here.
  * Σ_a ranges over any duplicate-free enumeration covering the
    accounts that occur (`raw_conservation` takes the enumeration as a
    hypothesis — the identity does not depend on which one), and
    `raw_conservation_canonical` instantiates the canonical one.

NOT claimed (each named so the register stays honest):

  * S3/S4 completeness — release work-receipt and clean-court coupling
    drag in the whole I-code court; owned by the Python audit + battery.
  * S8 completeness — default_resolution timing and the declared-
    direction machinery are not re-modeled here.
  * S9/S10 completeness — the outcome-attestation game (bonds, §8) has
    its own conservation arm in Settlement.lean's honest ops; its audit
    completeness is open.
  * This file proves the LAW over the model. The bridge to the shipped
    implementations is the corpus of `rfl`/golden-trace bindings
    (GoldenTraces.lean, kernel/test_review_regressions.py), not this
    file alone.
-/
import ChargeKernel.Basic

namespace ChargeKernel

/-! ### The raw adversarial event model -/

/-- A RAW settlement event: no well-typedness assumed. `none` in an
    `Option` field IS the forged field (non-string party / non-uint
    amount). `junk` stands for foreign kinds the settlement fold
    ignores wholesale. -/
inductive RawEvent where
  | deposit (id : String) (account : Option String) (amount : Option Nat)
  | escrow  (id : String) (payer payee : Option String) (amount : Option Nat)
  | release (id : String) (escrowId : Option String) (amount : Option Nat)
  | refund  (id : String) (escrowId : Option String) (amount : Option Nat)
  | junk    (id : String)
deriving Repr, DecidableEq

/-- The content address of a raw event (substrate-computed, always
    present). -/
def RawEvent.eventId : RawEvent → String
  | .deposit i _ _ => i
  | .escrow i _ _ _ => i
  | .release i _ _ => i
  | .refund i _ _ => i
  | .junk i => i

/-! ### The raw settlement fold (SPEC §2, all-or-nothing gates)

Per-account quantities are sums of per-event cells keyed by an
`Option String` field: `headCell key val ev a` is event `ev`'s
contribution to account `a`'s sum for that quantity. A `none` key
contributes to NO account — that is half of every gate; the other half
(the amount being uint) lives in the `val` functions. -/

/-- Event `ev`'s contribution to the `key/val` quantity of account `a`. -/
def headCell (key : RawEvent → Option String) (val : RawEvent → Int)
    (ev : RawEvent) (a : String) : Int :=
  if key ev = some a then val ev else 0

/-- Account `a`'s total for the `key/val` quantity over the soup. -/
def cellSum (key : RawEvent → Option String) (val : RawEvent → Int)
    (soup : List RawEvent) (a : String) : Int :=
  (soup.map fun ev => headCell key val ev a).sum

/-- The deposit's account field. -/
def depKey : RawEvent → Option String
  | .deposit _ acct _ => acct
  | _ => none

/-- The escrow's payer field (keys both `locked_out` and `refunded_in`). -/
def payerKey : RawEvent → Option String
  | .escrow _ payer _ _ => payer
  | _ => none

/-- The escrow's payee field (keys `released_in`). -/
def payeeKey : RawEvent → Option String
  | .escrow _ _ payee _ => payee
  | _ => none

/-- A deposit's amount when uint, else 0 (S6's crime contributes
    nothing). -/
def depVal : RawEvent → Int
  | .deposit _ _ (some amt) => (amt : Int)
  | _ => 0

/-- An escrow's amount when uint, else 0. Paired with `payerKey`, the
    cell is exactly the §2 gate: the amount debits the payer iff amount
    is uint AND payer is a string. -/
def lockVal : RawEvent → Int
  | .escrow _ _ _ (some amt) => (amt : Int)
  | _ => 0

/-- released-to-id: Σ uint amounts of releases naming escrow id `e`.
    A release with a non-string `escrow_id` or non-uint amount matches
    nothing and contributes nothing (S6). -/
def rawReleasedTo (soup : List RawEvent) (e : String) : Int :=
  (soup.map fun ev => match ev with
    | .release _ (some eid) (some amt) => if eid = e then (amt : Int) else 0
    | _ => 0).sum

/-- refunded-to-id: Σ uint amounts of refunds naming escrow id `e`. -/
def rawRefundedTo (soup : List RawEvent) (e : String) : Int :=
  (soup.map fun ev => match ev with
    | .refund _ (some eid) (some amt) => if eid = e then (amt : Int) else 0
    | _ => 0).sum

/-- The releases the soup aims at this escrow's id (credited to the
    payee via `payeeKey` — the release-direction gate). -/
def relVal (soup : List RawEvent) : RawEvent → Int
  | .escrow id _ _ _ => rawReleasedTo soup id
  | _ => 0

/-- The refunds the soup aims at this escrow's id (credited to the
    payer via `payerKey` — the refund-direction gate). -/
def refVal (soup : List RawEvent) : RawEvent → Int
  | .escrow id _ _ _ => rawRefundedTo soup id
  | _ => 0

/-- deposited(a): a deposit counts iff `account` is a string AND
    `amount_ucr` is uint (SPEC §2). -/
def rawDeposited (soup : List RawEvent) (a : String) : Int :=
  cellSum depKey depVal soup a

/-- locked_out(a): Σ amount(e) over escrows with payer = a — under the
    §2 all-or-nothing gate (amount uint AND payer a string). -/
def rawLockedOut (soup : List RawEvent) (a : String) : Int :=
  cellSum payerKey lockVal soup a

/-- released_in(a): Σ released(e) over escrows with payee = a. A
    non-string payee credits no account (§2: the disbursement counts
    only when the credited party is a string). -/
def rawReleasedIn (soup : List RawEvent) (a : String) : Int :=
  cellSum payeeKey (relVal soup) soup a

/-- refunded_in(a): Σ refunded(e) over escrows with payer = a. -/
def rawRefundedIn (soup : List RawEvent) (a : String) : Int :=
  cellSum payerKey (refVal soup) soup a

/-- available(a), in SIGNED arithmetic (SPEC §2). -/
def rawAvailable (soup : List RawEvent) (a : String) : Int :=
  rawDeposited soup a + rawReleasedIn soup a + rawRefundedIn soup a
    - rawLockedOut soup a

/-- amount(e) under THE gate (the F1 fix): an escrow's amount enters the
    fold — remainder and locked_out both — only when `amount_ucr` is
    uint AND `payer` is a string. Everything else contributes nothing
    anywhere and is S6's subject. -/
def escrowAmt : RawEvent → Int
  | .escrow _ (some _) _ (some amt) => (amt : Int)
  | _ => 0

/-- released(e): counted only when the credited payee is a string —
    otherwise the disbursement would burn remainder with no offsetting
    account gain (§2). -/
def escrowReleased (soup : List RawEvent) : RawEvent → Int
  | .escrow id _ (some _) _ => rawReleasedTo soup id
  | _ => 0

/-- refunded(e): counted only when the credited payer is a string. -/
def escrowRefunded (soup : List RawEvent) : RawEvent → Int
  | .escrow id (some _) _ _ => rawRefundedTo soup id
  | _ => 0

/-- remaining(e) = amount(e) − released(e) − refunded(e), signed
    (negative only if lied — the S2 crime, recorded not clamped). -/
def escrowRemaining (soup : List RawEvent) (ev : RawEvent) : Int :=
  escrowAmt ev - escrowReleased soup ev - escrowRefunded soup ev

/-- Σ_e remaining(e) over the soup (non-escrows contribute 0). -/
def rawRemainders (soup : List RawEvent) : Int :=
  (soup.map fun ev => escrowRemaining soup ev).sum

/-- One deposit's contribution to Σ deposits — same gate as
    `rawDeposited` (account a string AND amount uint). -/
def depContrib : RawEvent → Int
  | .deposit _ (some _) (some amt) => (amt : Int)
  | _ => 0

/-- Σ deposits: the RHS of the conservation identity. -/
def rawDeposits (soup : List RawEvent) : Int :=
  (soup.map depContrib).sum

/-! ### Account enumeration (SPEC §2: an account exists iff it appears
as a deposit `account`, an escrow `payer`, or an escrow `payee`) -/

/-- The singleton-or-empty list of a maybe-string field. -/
def optList : Option String → List String
  | some a => [a]
  | none   => []

/-- Every account string occurring in the soup (with duplicates). -/
def rawAccountsOf (soup : List RawEvent) : List String :=
  soup.flatMap fun ev => match ev with
    | .deposit _ acct _ => optList acct
    | .escrow _ payer payee _ => optList payer ++ optList payee
    | _ => []

/-- Duplicate-free canonicalization (keeps last occurrences; only
    membership and Nodup matter). Self-contained — no mathlib. -/
def dedupStr : List String → List String
  | [] => []
  | a :: rest => if a ∈ rest then dedupStr rest else a :: dedupStr rest

theorem mem_dedupStr {a : String} : ∀ {l : List String}, a ∈ dedupStr l ↔ a ∈ l := by
  intro l
  induction l with
  | nil => simp [dedupStr]
  | cons b rest ih =>
    by_cases hb : b ∈ rest
    · simp only [dedupStr, if_pos hb, List.mem_cons, ih]
      constructor
      · exact Or.inr
      · rintro (rfl | h)
        · exact hb
        · exact h
    · simp only [dedupStr, if_neg hb, List.mem_cons, ih]

theorem nodup_dedupStr : ∀ l : List String, (dedupStr l).Nodup := by
  intro l
  induction l with
  | nil => simp [dedupStr]
  | cons b rest ih =>
    by_cases hb : b ∈ rest
    · simpa [dedupStr, if_pos hb] using ih
    · simp only [dedupStr, if_neg hb]
      exact List.nodup_cons.mpr ⟨fun h => hb (mem_dedupStr.mp h), ih⟩

/-! ### Sum plumbing (self-contained, Int-valued) -/

theorem intSum_map_congr {α : Type} (l : List α) (f g : α → Int)
    (h : ∀ x ∈ l, f x = g x) : (l.map f).sum = (l.map g).sum := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons]
    rw [h x (List.mem_cons_self ..), ih (fun y hy => h y (List.mem_cons_of_mem _ hy))]

theorem intSum_map_add3_sub {α : Type} (l : List α) (f1 f2 f3 f4 : α → Int) :
    (l.map fun x => f1 x + f2 x + f3 x - f4 x).sum
      = (l.map f1).sum + (l.map f2).sum + (l.map f3).sum - (l.map f4).sum := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons, ih]
    omega

theorem intSum_map_sub2 {α : Type} (l : List α) (f g h : α → Int) :
    (l.map fun x => f x - g x - h x).sum
      = (l.map f).sum - (l.map g).sum - (l.map h).sum := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons, ih]
    omega

/-- A `none`-keyed event contributes to no account. -/
theorem headSum_none (key : RawEvent → Option String) (val : RawEvent → Int)
    (ev : RawEvent) (hk : key ev = none) :
    ∀ accts : List String, (accts.map (headCell key val ev)).sum = 0 := by
  intro accts
  induction accts with
  | nil => rfl
  | cons a as ih =>
    simp only [List.map_cons, List.sum_cons, ih]
    simp [headCell, hk]

/-- A keyed event contributes nothing to enumerations missing its key. -/
theorem headSum_notMem (key : RawEvent → Option String) (val : RawEvent → Int)
    (ev : RawEvent) (k : String) (hk : key ev = some k) :
    ∀ accts : List String, k ∉ accts →
      (accts.map (headCell key val ev)).sum = 0 := by
  intro accts
  induction accts with
  | nil => intro _; rfl
  | cons a as ih =>
    intro hnot
    simp only [List.mem_cons, not_or] at hnot
    simp only [List.map_cons, List.sum_cons, ih hnot.2]
    simp [headCell, hk, hnot.1]

/-- A keyed event contributes its value EXACTLY ONCE to any Nodup
    enumeration containing its key — the heart of Σ_a well-definedness. -/
theorem headSum_single (key : RawEvent → Option String) (val : RawEvent → Int)
    (ev : RawEvent) (k : String) (hk : key ev = some k) :
    ∀ accts : List String, accts.Nodup → k ∈ accts →
      (accts.map (headCell key val ev)).sum = val ev := by
  intro accts
  induction accts with
  | nil => intro _ hmem; cases hmem
  | cons a as ih =>
    intro hnd hmem
    rw [List.nodup_cons] at hnd
    simp only [List.map_cons, List.sum_cons]
    by_cases hka : k = a
    · subst hka
      rw [headSum_notMem key val ev k hk as hnd.1]
      simp [headCell, hk]
    · have hmem' : k ∈ as := by
        cases List.mem_cons.mp hmem with
        | inl h => exact absurd h hka
        | inr h => exact h
      rw [ih hnd.2 hmem']
      simp [headCell, hk, hka]

/-- Σ over a Nodup covering enumeration of per-account `key/val` sums. -/
def bySum (key : RawEvent → Option String) (val : RawEvent → Int)
    (soup : List RawEvent) (accts : List String) : Int :=
  (accts.map (cellSum key val soup)).sum

theorem bySum_nil (key : RawEvent → Option String) (val : RawEvent → Int)
    (accts : List String) : bySum key val [] accts = 0 := by
  induction accts with
  | nil => rfl
  | cons a as ih =>
    simp only [bySum, List.map_cons, List.sum_cons] at ih ⊢
    rw [ih]
    simp [cellSum]

theorem cellSum_cons (key : RawEvent → Option String) (val : RawEvent → Int)
    (ev : RawEvent) (rest : List RawEvent) (a : String) :
    cellSum key val (ev :: rest) a
      = headCell key val ev a + cellSum key val rest a := by
  simp [cellSum]

theorem bySum_cons (key : RawEvent → Option String) (val : RawEvent → Int)
    (ev : RawEvent) (rest : List RawEvent) (accts : List String) :
    bySum key val (ev :: rest) accts
      = (accts.map (headCell key val ev)).sum + bySum key val rest accts := by
  induction accts with
  | nil => rfl
  | cons a as ih =>
    simp only [bySum, List.map_cons, List.sum_cons] at ih ⊢
    rw [cellSum_cons, ih]
    omega

/-- **Fubini for the fold**: summing a `key/val` quantity account-by-
    account over a Nodup enumeration covering every occurring key equals
    summing it event-by-event with the key-presence gate. This is why
    the conservation identity is independent of the enumeration. -/
theorem intSum_group (key : RawEvent → Option String) (val : RawEvent → Int)
    (soup : List RawEvent) (accts : List String) (hnd : accts.Nodup)
    (hcov : ∀ ev ∈ soup, ∀ a, key ev = some a → a ∈ accts) :
    bySum key val soup accts
      = (soup.map fun ev => if (key ev).isSome then val ev else 0).sum := by
  induction soup with
  | nil => simpa using bySum_nil key val accts
  | cons ev rest ih =>
    have hcov' : ∀ e ∈ rest, ∀ a, key e = some a → a ∈ accts :=
      fun e he a hk => hcov e (List.mem_cons_of_mem _ he) a hk
    rw [bySum_cons, ih hcov']
    simp only [List.map_cons, List.sum_cons]
    cases hk : key ev with
    | none => rw [headSum_none key val ev hk accts]; simp
    | some k =>
      rw [headSum_single key val ev k hk accts hnd
            (hcov ev (List.mem_cons_self ..) k hk)]
      simp

/-! ### Coverage: every key the fold reads occurs in `rawAccountsOf` -/

theorem depKey_covered (soup : List RawEvent) :
    ∀ ev ∈ soup, ∀ a, depKey ev = some a → a ∈ rawAccountsOf soup := by
  intro ev hmem a hk
  refine List.mem_flatMap.mpr ⟨ev, hmem, ?_⟩
  cases ev <;> simp [depKey] at hk
  subst hk; simp [optList]

theorem payerKey_covered (soup : List RawEvent) :
    ∀ ev ∈ soup, ∀ a, payerKey ev = some a → a ∈ rawAccountsOf soup := by
  intro ev hmem a hk
  refine List.mem_flatMap.mpr ⟨ev, hmem, ?_⟩
  cases ev <;> simp [payerKey] at hk
  subst hk; simp [optList]

theorem payeeKey_covered (soup : List RawEvent) :
    ∀ ev ∈ soup, ∀ a, payeeKey ev = some a → a ∈ rawAccountsOf soup := by
  intro ev hmem a hk
  refine List.mem_flatMap.mpr ⟨ev, hmem, ?_⟩
  cases ev <;> simp [payeeKey] at hk
  subst hk; simp [optList]

/-! ### Pointwise bridges: the per-escrow quantities ARE the keyed cells,
gate for gate -/

theorem escrowAmt_keyed (ev : RawEvent) :
    escrowAmt ev = if (payerKey ev).isSome then lockVal ev else 0 := by
  cases ev with
  | escrow id payer payee amount =>
    cases payer <;> cases amount <;> simp [escrowAmt, payerKey, lockVal]
  | deposit id acct amt => rfl
  | release id eid amt => rfl
  | refund id eid amt => rfl
  | junk id => rfl

theorem escrowReleased_keyed (soup : List RawEvent) (ev : RawEvent) :
    escrowReleased soup ev
      = if (payeeKey ev).isSome then relVal soup ev else 0 := by
  cases ev with
  | escrow id payer payee amount =>
    cases payee <;> simp [escrowReleased, payeeKey, relVal]
  | deposit id acct amt => rfl
  | release id eid amt => rfl
  | refund id eid amt => rfl
  | junk id => rfl

theorem escrowRefunded_keyed (soup : List RawEvent) (ev : RawEvent) :
    escrowRefunded soup ev
      = if (payerKey ev).isSome then refVal soup ev else 0 := by
  cases ev with
  | escrow id payer payee amount =>
    cases payer <;> simp [escrowRefunded, payerKey, refVal]
  | deposit id acct amt => rfl
  | release id eid amt => rfl
  | refund id eid amt => rfl
  | junk id => rfl

theorem depContrib_keyed (ev : RawEvent) :
    depContrib ev = if (depKey ev).isSome then depVal ev else 0 := by
  cases ev with
  | deposit id acct amt =>
    cases acct <;> cases amt <;> simp [depContrib, depKey, depVal]
  | escrow id payer payee amount => rfl
  | release id eid amt => rfl
  | refund id eid amt => rfl
  | junk id => rfl

/-! ### THE THEOREM -/

/-- **Raw conservation (the F1 law).** For ANY raw soup whatsoever —
    adversarial, unordered, containing forged non-string parties and
    non-uint amounts — and any duplicate-free account enumeration
    covering the accounts that occur:

        Σ_a available(a) + Σ_e remaining(e) = Σ deposits.

    The §2 all-or-nothing gates are exactly what makes this arithmetic:
    every quantity that credits an account is paired with the debit of
    the same gated amount, so each event's net contribution telescopes
    to zero except deposits. No honesty assumed anywhere. -/
theorem raw_conservation (soup : List RawEvent) (accts : List String)
    (hnd : accts.Nodup) (hcov : ∀ a ∈ rawAccountsOf soup, a ∈ accts) :
    (accts.map fun a => rawAvailable soup a).sum + rawRemainders soup
      = rawDeposits soup := by
  -- split Σ_a available into the four keyed double sums
  have havail : (accts.map fun a => rawAvailable soup a).sum
      = bySum depKey depVal soup accts
        + bySum payeeKey (relVal soup) soup accts
        + bySum payerKey (refVal soup) soup accts
        - bySum payerKey lockVal soup accts := by
    simp only [rawAvailable, rawDeposited, rawReleasedIn, rawRefundedIn,
               rawLockedOut, bySum]
    exact intSum_map_add3_sub accts _ _ _ _
  -- regroup each double sum event-by-event (Fubini + Nodup coverage)
  have hdep := intSum_group depKey depVal soup accts hnd
    (fun ev hm a hk => hcov a (depKey_covered soup ev hm a hk))
  have hrel := intSum_group payeeKey (relVal soup) soup accts hnd
    (fun ev hm a hk => hcov a (payeeKey_covered soup ev hm a hk))
  have href := intSum_group payerKey (refVal soup) soup accts hnd
    (fun ev hm a hk => hcov a (payerKey_covered soup ev hm a hk))
  have hlock := intSum_group payerKey lockVal soup accts hnd
    (fun ev hm a hk => hcov a (payerKey_covered soup ev hm a hk))
  -- split Σ_e remaining into its three event-by-event sums
  have hrem : rawRemainders soup
      = (soup.map fun ev => escrowAmt ev).sum
        - (soup.map fun ev => escrowReleased soup ev).sum
        - (soup.map fun ev => escrowRefunded soup ev).sum := by
    simp only [rawRemainders, escrowRemaining]
    exact intSum_map_sub2 soup _ _ _
  -- the per-escrow quantities are the keyed cells, gate for gate
  have hb1 : (soup.map fun ev => escrowAmt ev).sum
      = (soup.map fun ev => if (payerKey ev).isSome then lockVal ev else 0).sum :=
    intSum_map_congr soup _ _ (fun ev _ => escrowAmt_keyed ev)
  have hb2 : (soup.map fun ev => escrowReleased soup ev).sum
      = (soup.map fun ev => if (payeeKey ev).isSome then relVal soup ev else 0).sum :=
    intSum_map_congr soup _ _ (fun ev _ => escrowReleased_keyed soup ev)
  have hb3 : (soup.map fun ev => escrowRefunded soup ev).sum
      = (soup.map fun ev => if (payerKey ev).isSome then refVal soup ev else 0).sum :=
    intSum_map_congr soup _ _ (fun ev _ => escrowRefunded_keyed soup ev)
  have hb4 : rawDeposits soup
      = (soup.map fun ev => if (depKey ev).isSome then depVal ev else 0).sum := by
    simp only [rawDeposits]
    exact intSum_map_congr soup _ _ (fun ev _ => depContrib_keyed ev)
  omega

/-- The canonical conservation LHS, executable (canonical enumeration =
    deduplicated occurring accounts). -/
def conservationLHS (soup : List RawEvent) : Int :=
  ((dedupStr (rawAccountsOf soup)).map fun a => rawAvailable soup a).sum
    + rawRemainders soup

/-- **Raw conservation, canonical form**: the identity with the
    enumeration discharged — TRUE OF EVERY RAW SOUP, no hypotheses. -/
theorem raw_conservation_canonical (soup : List RawEvent) :
    conservationLHS soup = rawDeposits soup :=
  raw_conservation soup (dedupStr (rawAccountsOf soup))
    (nodup_dedupStr _) (fun _ ha => mem_dedupStr.mpr ha)

/-! ### The PRE-FIX fold and the F1 counterexample

The pre-2026-07-06 spec gated an escrow's remainder contribution on the
amount being uint ALONE. `locked_out` is keyed by payer, so a
`payer = none` escrow debits nobody — but its amount still entered the
remainder. The counterexample below is the exact F1 forgery. -/

/-- amount(e) as the spec read BEFORE the F1 fix: uint gate only, no
    payer gate. THE BUG. -/
def preFixEscrowAmt : RawEvent → Int
  | .escrow _ _ _ (some amt) => (amt : Int)
  | _ => 0

def preFixRemaining (soup : List RawEvent) (ev : RawEvent) : Int :=
  preFixEscrowAmt ev - escrowReleased soup ev - escrowRefunded soup ev

def preFixRemainders (soup : List RawEvent) : Int :=
  (soup.map fun ev => preFixRemaining soup ev).sum

/-- The pre-fix conservation LHS. -/
def preFixLHS (soup : List RawEvent) : Int :=
  ((dedupStr (rawAccountsOf soup)).map fun a => rawAvailable soup a).sum
    + preFixRemainders soup

/-- The F1 forgery, verbatim: an honest 1000-deposit plus an escrow
    whose payer is NOT A STRING and whose amount is 999. -/
def f1Soup : List RawEvent :=
  [ .deposit "d1" (some "alice") (some 1000),
    .escrow "e1" none (some "bob") (some 999) ]

/-- **The sharp negative (gate necessity).** Under the PRE-FIX fold the
    F1 soup breaks conservation — the forged escrow MINTS 999 into the
    LHS with no offsetting debit. This is the executable content of the
    2026-07-06 review finding; the fixed fold on the same soup satisfies
    `raw_conservation_canonical` above. -/
theorem f1_prefix_breaks : preFixLHS f1Soup ≠ rawDeposits f1Soup := by decide

/-- The broken numbers, pinned: 1999 on the left … -/
example : preFixLHS f1Soup = 1999 := by decide

/-- … against 1000 declared deposits. -/
example : rawDeposits f1Soup = 1000 := by decide

/-! ### S6 over the raw model — the payer/payee arm

SCOPE: ONLY the non-string-payer / non-string-payee arm of the SPEC §3
S6 row is modeled here (the arm that owns F1's crime). The row's other
arms — non-uint `amount_ucr`, `seq`, `charge_keys`, `default_on_expiry`,
non-string `escrow_id` — are owned by the Python/Rust audits and the
conformance battery. -/

/-- S6 (payer/payee arm): an escrow with a non-string payer or payee is
    malformed. -/
def s6 : RawEvent → Bool
  | .escrow _ payer payee _ => payer.isNone || payee.isNone
  | _ => false

/-- The S6 audit: the event ids of convicted escrows (§3's
    `"<code> <subject>"` discipline, subject = event id). -/
def s6Audit (soup : List RawEvent) : List String :=
  soup.filterMap fun ev => if s6 ev then some ev.eventId else none

/-- **S6 completeness (direct arm).** Any soup containing an escrow with
    a non-string payer or payee yields an S6 conviction naming exactly
    that escrow's event id. -/
theorem s6_complete (soup : List RawEvent)
    (id : String) (payer payee : Option String) (amount : Option Nat)
    (hmem : RawEvent.escrow id payer payee amount ∈ soup)
    (hmal : payer = none ∨ payee = none) : id ∈ s6Audit soup := by
  refine List.mem_filterMap.mpr ⟨_, hmem, ?_⟩
  cases hmal with
  | inl h => subst h; simp [s6, RawEvent.eventId]
  | inr h => subst h; simp [s6, RawEvent.eventId]

/-- **S6 gate-completeness (the fix is audited, not silent).** If the
    fixed fold's gate ZEROED an escrow's positive uint amount, the soup
    contains an escrow event the S6 audit names: gating never launders
    value away without a conviction. -/
theorem s6_gate_complete (soup : List RawEvent)
    (id : String) (payer payee : Option String) (n : Nat)
    (hmem : RawEvent.escrow id payer payee (some n) ∈ soup)
    (hzero : escrowAmt (.escrow id payer payee (some n)) = 0)
    (hpos : 0 < n) : id ∈ s6Audit soup := by
  cases payer with
  | some p =>
    simp only [escrowAmt] at hzero
    omega
  | none => exact s6_complete soup id none payee (some n) hmem (Or.inl rfl)

/-- **S6 soundness.** Every S6 conviction names a real crime: an escrow
    event in the soup with a non-string payer or payee. No slander. -/
theorem s6_sound (soup : List RawEvent) (subj : String)
    (h : subj ∈ s6Audit soup) :
    ∃ payer payee amount,
      RawEvent.escrow subj payer payee amount ∈ soup ∧
        (payer = none ∨ payee = none) := by
  obtain ⟨ev, hmem, hsome⟩ := List.mem_filterMap.mp h
  by_cases hs : s6 ev = true
  · cases ev with
    | escrow id payer payee amount =>
      simp only [s6, Bool.or_eq_true, Option.isNone_iff_eq_none] at hs
      simp only [s6, RawEvent.eventId] at hsome
      · rw [if_pos] at hsome
        · cases hsome
          exact ⟨payer, payee, amount, hmem, hs⟩
        · simp [hs]
    | deposit id acct amt => simp [s6] at hs
    | release id eid amt => simp [s6] at hs
    | refund id eid amt => simp [s6] at hs
    | junk id => simp [s6] at hs
  · rw [if_neg hs] at hsome
    cases hsome

/-! ### Executable golden bindings (decide/rfl) -/

/-- **F1 golden**: under the FIXED fold the forged soup conserves
    (1000 = 1000 — the forged 999 enters nothing) … -/
example : conservationLHS f1Soup = rawDeposits f1Soup := by decide

/-- … AND the forged escrow is convicted by name. Zeroed and named:
    the gate and the audit close together. -/
example : s6Audit f1Soup = ["e1"] := by decide

/-- The release-mirror of F1: escrow with a string payer but a
    NON-STRING payee, plus a release aimed at it. The release credits
    nobody and burns nothing (§2: the disbursement counts only when the
    credited party is a string) — the identity holds. -/
def mirrorSoup : List RawEvent :=
  [ .deposit "d1" (some "alice") (some 1000),
    .escrow "e1" (some "alice") none (some 500),
    .release "r1" (some "e1") (some 100) ]

example : conservationLHS mirrorSoup = rawDeposits mirrorSoup := by decide

/-- The mirror's escrow is likewise convicted (payee arm). -/
example : s6Audit mirrorSoup = ["e1"] := by decide

/-- An honest soup: deposit, well-formed escrow, partial release.
    No convictions, identity holds, every microcredit in one place
    (400 available to alice, 400 to bob, 200 parked in the escrow). -/
def honestSoup : List RawEvent :=
  [ .deposit "d1" (some "alice") (some 1000),
    .escrow "e1" (some "alice") (some "bob") (some 600),
    .release "r1" (some "e1") (some 400) ]

example : s6Audit honestSoup = [] := by decide
example : conservationLHS honestSoup = rawDeposits honestSoup := by decide
example : rawAvailable honestSoup "alice" = 400 := by decide
example : rawAvailable honestSoup "bob" = 400 := by decide
example : rawRemainders honestSoup = 200 := by decide

/-! ### Axiom guards (the root file's discipline, enforced here because
this module owns its theorems: propext / Quot.sound only, no
Classical.choice, no sorryAx) -/

/-- info: 'ChargeKernel.raw_conservation' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms raw_conservation

/-- info: 'ChargeKernel.raw_conservation_canonical' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms raw_conservation_canonical

/-- info: 'ChargeKernel.intSum_group' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms intSum_group

/-- info: 'ChargeKernel.f1_prefix_breaks' depends on axioms: [propext] -/
#guard_msgs in #print axioms f1_prefix_breaks

/-- info: 'ChargeKernel.s6_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s6_complete

/-- info: 'ChargeKernel.s6_gate_complete' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s6_gate_complete

/-- info: 'ChargeKernel.s6_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in #print axioms s6_sound

end ChargeKernel
