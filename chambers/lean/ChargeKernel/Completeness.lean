/-
ChargeKernel.Completeness — conviction-completeness of the audit over
adversarial event soups (FRAMEWORKS.md F3; the ASSURANCE.md L4 upgrade
from "the honest ops conserve" toward "the audit is COMPLETE for the
law set").

The lift this module makes, which the previous modules deliberately
avoided: the AUDIT is modelled over an ABSTRACT ADVERSARIAL SOUP — an
arbitrary finite multiset of events, not the states reachable by guarded
honest ops. Settlement.lean proves the honest issuer conserves; this file
proves the other half of the division of labor: WHATEVER a Byzantine
party emits, if a law is violated then the audit (a total, executable
Lean function mirroring settlement.py `audit_settlement_findings` and
ledger.py `substrate_findings`) emits a finding naming the violation's
subject — a finite witness a stranger can check against the soup itself.

Laws covered (SETTLEMENT-SPEC §3; KERNEL-SPEC Part II):

  S2  escrow over-disbursement — released(e) + refunded(e) > amount(e).
      `s2_complete` (any soup containing an over-disbursed escrow yields
      an S2 finding whose subject is that escrow), `s2_sound` (an S2
      finding implies the inequality or a dangling reference),
      `s2_dangling_complete` (the unknown-escrow arm), and
      `s2_convicts_issuer` — the F3 sentence itself: the finding names an
      event, present in the soup, that names its issuer.
  S1  account overdraft — available(a) < 0 in signed arithmetic.
      `s1_complete` and `s1_sound`. The audit only ranges over accounts
      that OCCUR in the soup, and occurrence is DERIVED from the crime:
      an overdraft forces a positive lock-out, which forces an escrow
      naming the account as payer — so completeness quantifies over ALL
      account strings, not just enumerated ones.
  X0  substrate equivocation — two events with different ids claiming the
      same (actor, kind, seq). `x0_complete` and `x0_sound`.

Model honesty (what is and is not captured):
  * The soup is a List; the real ledger is a content-addressed SET (a
    dict keyed by sha256 of canonical bytes). Every theorem is proven
    for ALL lists — a strict superset containing every Nodup soup —
    so nothing here leans on dedup.
  * Amounts are Nat because SETTLEMENT-SPEC §2 rules that non-uint
    amounts contribute NOTHING to any sum (they are S6's crime, not
    S1/S2's); a malformed event is `junk` for these folds, which is
    exactly the spec's rule, not a simplification of it.
  * A default_resolution is modelled as the release/refund its DECLARED
    direction makes it (§2: default resolutions count toward the
    escrow's declared direction; the submitter does not choose).
  * The audit returns raw findings; the Python conformance surface
    sorts and dedups into `"<code> <subject>"` strings. Membership is
    the law proven here; dedup does not change membership.
  * NOT claimed: completeness for S3/S4/S7/S8 (work-receipt, clean-court,
    expiry timing — their predicates drag in the whole I-code court) and
    S9/S10 (outcome attestations). Open obligations, named here and in
    the L4 register — no theorem below mentions them.
-/

namespace ChargeKernel

/-! ### The adversarial settlement soup -/

/-- The minimal event shape the S1/S2 arms of the settlement audit read.
    Ids are opaque strings (content addresses upstream). `junk` stands
    for every event the settlement fold ignores — foreign kinds AND
    malformed settlement events, whose amounts contribute to no sum
    (SETTLEMENT-SPEC §2; they are S6's subject, out of scope here). -/
inductive SoupEvent where
  | deposit (id : String) (issuer : String) (account : String) (amount : Nat)
  | escrow  (id : String) (issuer : String) (payer : String) (payee : String) (amount : Nat)
  | release (id : String) (issuer : String) (escrowId : String) (amount : Nat)
  | refund  (id : String) (issuer : String) (escrowId : String) (amount : Nat)
  | junk    (id : String)
deriving Repr, DecidableEq

inductive AuditCode where
  | S1 | S2
deriving Repr, DecidableEq

/-- A finding: the code and the canonical subject it convicts —
    SETTLEMENT-SPEC §3's `"<code> <subject>"` discipline. -/
structure Finding where
  code    : AuditCode
  subject : String
deriving Repr, DecidableEq

/-! ### The settlement fold (SETTLEMENT-SPEC §2), over ANY soup -/

/-- released(e): Σ amounts of releases naming escrow id `e`. -/
def releasedTo (soup : List SoupEvent) (e : String) : Nat :=
  (soup.filterMap fun ev => match ev with
    | .release _ _ eid amt => if eid = e then some amt else none
    | _ => none).sum

/-- refunded(e): Σ amounts of refunds naming escrow id `e`. -/
def refundedTo (soup : List SoupEvent) (e : String) : Nat :=
  (soup.filterMap fun ev => match ev with
    | .refund _ _ eid amt => if eid = e then some amt else none
    | _ => none).sum

/-- deposited(a): Σ amounts of deposits into account `a`. -/
def depositedTo (soup : List SoupEvent) (a : String) : Nat :=
  (soup.filterMap fun ev => match ev with
    | .deposit _ _ acct amt => if acct = a then some amt else none
    | _ => none).sum

/-- The lock an escrow charges against payer `a` (named, so its inversion
    is an equation lemma, not an anonymous-lambda excavation). -/
def lockAmtOf (a : String) : SoupEvent → Option Nat
  | .escrow _ _ payer _ amt => if payer = a then some amt else none
  | _ => none

/-- The escrow lock amounts charged against payer `a`, kept as a LIST
    (not just its sum) because `s1_complete` needs its inhabitant. -/
def lockedOutList (soup : List SoupEvent) (a : String) : List Nat :=
  soup.filterMap (lockAmtOf a)

/-- locked_out(a): Σ amount(e) over escrows with payer = a. -/
def lockedOut (soup : List SoupEvent) (a : String) : Nat :=
  (lockedOutList soup a).sum

/-- released_in(a): Σ released(e) over escrows with payee = a. -/
def releasedIn (soup : List SoupEvent) (a : String) : Nat :=
  (soup.filterMap fun ev => match ev with
    | .escrow id _ _ payee _ => if payee = a then some (releasedTo soup id) else none
    | _ => none).sum

/-- refunded_in(a): Σ refunded(e) over escrows with payer = a. -/
def refundedIn (soup : List SoupEvent) (a : String) : Nat :=
  (soup.filterMap fun ev => match ev with
    | .escrow id _ payer _ _ => if payer = a then some (refundedTo soup id) else none
    | _ => none).sum

/-- available(a), in SIGNED arithmetic (SETTLEMENT-SPEC §2): a negative
    value IS the S1 crime — the artifact records it rather than clamping
    it away. -/
def available (soup : List SoupEvent) (a : String) : Int :=
  (depositedTo soup a : Int) + releasedIn soup a + refundedIn soup a
    - lockedOut soup a

/-- Whether the soup contains an escrow event with id `e` (the S2
    unknown-escrow arm reads this). -/
def hasEscrow (soup : List SoupEvent) (e : String) : Bool :=
  soup.any fun ev => match ev with
    | .escrow id _ _ _ _ => id = e
    | _ => false

/-! ### The audit, as a total executable function -/

/-- SPEC §2: an account exists iff it appears as a deposit `account`,
    an escrow `payer`, or an escrow `payee`. -/
def accountsOf (soup : List SoupEvent) : List String :=
  soup.flatMap fun ev => match ev with
    | .deposit _ _ acct _ => [acct]
    | .escrow _ _ payer payee _ => [payer, payee]
    | _ => []

/-- The S2-family findings one event contributes: an escrow convicts
    itself when over-disbursed; a release/refund convicts itself when it
    references an escrow absent from the soup (SETTLEMENT-SPEC §3, S2
    both arms). -/
def s2FindingsOf (soup : List SoupEvent) : SoupEvent → List Finding
  | .escrow id _ _ _ amount =>
      if amount < releasedTo soup id + refundedTo soup id
      then [⟨.S2, id⟩] else []
  | .release id _ eid _ =>
      if hasEscrow soup eid then [] else [⟨.S2, id⟩]
  | .refund id _ eid _ =>
      if hasEscrow soup eid then [] else [⟨.S2, id⟩]
  | _ => []

def s2Audit (soup : List SoupEvent) : List Finding :=
  soup.flatMap (s2FindingsOf soup)

/-- The S1 verdict for one enumerated account. -/
def s1FindingOf (soup : List SoupEvent) (a : String) : Option Finding :=
  if available soup a < 0 then some ⟨.S1, a⟩ else none

def s1Audit (soup : List SoupEvent) : List Finding :=
  (accountsOf soup).filterMap (s1FindingOf soup)

/-- The (S1 ∪ S2) settlement audit over an arbitrary soup — the Lean
    mirror of the S1/S2 blocks of `audit_settlement_findings`. -/
def settleAudit (soup : List SoupEvent) : List Finding :=
  s1Audit soup ++ s2Audit soup

/-! ### Routing: each sub-audit only speaks its own code -/

theorem s1Audit_code (soup : List SoupEvent) (f : Finding)
    (h : f ∈ s1Audit soup) : f.code = .S1 := by
  obtain ⟨a, _, hsome⟩ := List.mem_filterMap.mp h
  simp only [s1FindingOf] at hsome
  split at hsome
  · cases hsome; rfl
  · cases hsome

theorem s2Audit_code (soup : List SoupEvent) (f : Finding)
    (h : f ∈ s2Audit soup) : f.code = .S2 := by
  obtain ⟨ev, _, hf⟩ := List.mem_flatMap.mp h
  cases ev with
  | escrow id issuer payer payee amount =>
    simp only [s2FindingsOf] at hf
    split at hf
    · have := List.mem_singleton.mp hf; subst this; rfl
    · cases hf
  | release id issuer eid amt =>
    simp only [s2FindingsOf] at hf
    split at hf
    · cases hf
    · have := List.mem_singleton.mp hf; subst this; rfl
  | refund id issuer eid amt =>
    simp only [s2FindingsOf] at hf
    split at hf
    · cases hf
    · have := List.mem_singleton.mp hf; subst this; rfl
  | deposit id issuer acct amt => simp [s2FindingsOf] at hf
  | junk id => simp [s2FindingsOf] at hf

/-! ### S2 — conviction-completeness and soundness -/

/-- **S2 completeness (the F3 target, smallest law first).** ANY event
    soup — adversarial, unordered, containing arbitrary junk — in which
    escrow `e` has released(e) + refunded(e) > amount(e) yields an S2
    finding whose subject is exactly that escrow's event id. The witness
    is finite and checkable: the escrow event plus the releases/refunds
    the fold summed. -/
theorem s2_complete (soup : List SoupEvent)
    (id issuer payer payee : String) (amount : Nat)
    (hmem : SoupEvent.escrow id issuer payer payee amount ∈ soup)
    (hover : amount < releasedTo soup id + refundedTo soup id) :
    (⟨.S2, id⟩ : Finding) ∈ settleAudit soup := by
  apply List.mem_append_right
  exact List.mem_flatMap.mpr ⟨_, hmem, by simp [s2FindingsOf, hover]⟩

/-- **S2 completeness, unknown-escrow arm**: a release or refund whose
    `escrow_id` matches no escrow in the soup is itself convicted, its
    own event id the subject (SETTLEMENT-SPEC §2/§3: it contributes to
    no sum and is convicted via S2's unknown/unresolvable arm). -/
theorem s2_dangling_complete (soup : List SoupEvent)
    (id issuer eid : String) (amount : Nat)
    (hmem : SoupEvent.release id issuer eid amount ∈ soup ∨
            SoupEvent.refund id issuer eid amount ∈ soup)
    (hghost : hasEscrow soup eid = false) :
    (⟨.S2, id⟩ : Finding) ∈ settleAudit soup := by
  apply List.mem_append_right
  cases hmem with
  | inl h => exact List.mem_flatMap.mpr ⟨_, h, by simp [s2FindingsOf, hghost]⟩
  | inr h => exact List.mem_flatMap.mpr ⟨_, h, by simp [s2FindingsOf, hghost]⟩

/-- **S2 soundness.** Every S2 finding convicts a real crime in the soup:
    its subject is an escrow that is over-disbursed, or a release/refund
    whose referenced escrow does not exist. No false convictions. -/
theorem s2_sound (soup : List SoupEvent) (subj : String)
    (h : (⟨.S2, subj⟩ : Finding) ∈ settleAudit soup) :
    (∃ issuer payer payee amount,
        SoupEvent.escrow subj issuer payer payee amount ∈ soup ∧
        amount < releasedTo soup subj + refundedTo soup subj)
    ∨ (∃ issuer eid amount,
        (SoupEvent.release subj issuer eid amount ∈ soup ∨
         SoupEvent.refund subj issuer eid amount ∈ soup) ∧
        hasEscrow soup eid = false) := by
  cases List.mem_append.mp h with
  | inl h1 => exact absurd (s1Audit_code soup _ h1) (by simp)
  | inr h2 =>
    obtain ⟨ev, hev, hf⟩ := List.mem_flatMap.mp h2
    cases ev with
    | escrow id issuer payer payee amount =>
      simp only [s2FindingsOf] at hf
      split at hf
      · rename_i hover
        have hsubj := List.mem_singleton.mp hf
        cases hsubj
        exact Or.inl ⟨issuer, payer, payee, amount, hev, hover⟩
      · cases hf
    | release id issuer eid amt =>
      simp only [s2FindingsOf] at hf
      split at hf
      · cases hf
      · rename_i hghost
        simp only [Bool.not_eq_true] at hghost
        have hsubj := List.mem_singleton.mp hf
        cases hsubj
        exact Or.inr ⟨issuer, eid, amt, Or.inl hev, hghost⟩
    | refund id issuer eid amt =>
      simp only [s2FindingsOf] at hf
      split at hf
      · cases hf
      · rename_i hghost
        simp only [Bool.not_eq_true] at hghost
        have hsubj := List.mem_singleton.mp hf
        cases hsubj
        exact Or.inr ⟨issuer, eid, amt, Or.inr hev, hghost⟩
    | deposit id issuer acct amt => simp [s2FindingsOf] at hf
    | junk id => simp [s2FindingsOf] at hf

/-- **The F3 sentence, verbatim, for S2**: any event set in which a law
    is violated contains a finite witness that convicts under the audit
    AND NAMES ITS ISSUER. The finding names the escrow event; the escrow
    event — present in the very soup being audited — names the issuer
    who authored it. Conviction is transferable: anyone holding the soup
    re-derives both. -/
theorem s2_convicts_issuer (soup : List SoupEvent)
    (id issuer payer payee : String) (amount : Nat)
    (hmem : SoupEvent.escrow id issuer payer payee amount ∈ soup)
    (hover : amount < releasedTo soup id + refundedTo soup id) :
    ∃ f ∈ settleAudit soup, f.code = .S2 ∧
      SoupEvent.escrow f.subject issuer payer payee amount ∈ soup :=
  ⟨⟨.S2, id⟩, s2_complete soup id issuer payer payee amount hmem hover,
    rfl, hmem⟩

/-! ### S1 — conviction-completeness and soundness -/

/-- Any positive Nat-sum has a member (self-contained, no mathlib). -/
theorem sum_pos_mem {l : List Nat} (h : 0 < l.sum) : ∃ x ∈ l, 0 < x := by
  induction l with
  | nil => simp at h
  | cons x xs ih =>
    cases Nat.eq_zero_or_pos x with
    | inr hx => exact ⟨x, List.Mem.head _, hx⟩
    | inl hx =>
      subst hx
      simp only [List.sum_cons, Nat.zero_add] at h
      obtain ⟨y, hy, hpos⟩ := ih h
      exact ⟨y, List.Mem.tail _ hy, hpos⟩

/-- An overdraft forces a positive lock-out: the deposit/release/refund
    terms of `available` are non-negative by construction, so only
    locked_out can drive it below zero. -/
theorem overdraft_forces_lock (soup : List SoupEvent) (a : String)
    (h : available soup a < 0) : 0 < lockedOut soup a := by
  unfold available at h
  omega

/-- A positive lock-out forces an escrow event in the soup naming `a`
    as payer — the crime carries its own occurrence witness. -/
theorem lock_forces_escrow (soup : List SoupEvent) (a : String)
    (h : 0 < lockedOut soup a) :
    ∃ id issuer payee amt,
      SoupEvent.escrow id issuer a payee amt ∈ soup := by
  obtain ⟨x, hx, _⟩ := sum_pos_mem h
  obtain ⟨ev, hev, hsome⟩ := List.mem_filterMap.mp hx
  cases ev with
  | escrow id issuer payer payee amt =>
    simp only [lockAmtOf] at hsome
    split at hsome
    · rename_i hpa
      subst hpa
      exact ⟨id, issuer, payee, amt, hev⟩
    · cases hsome
  | deposit id issuer acct amt => simp [lockAmtOf] at hsome
  | release id issuer eid amt => simp [lockAmtOf] at hsome
  | refund id issuer eid amt => simp [lockAmtOf] at hsome
  | junk id => simp [lockAmtOf] at hsome

/-- The payer of any escrow in the soup is an account the audit ranges
    over. -/
theorem payer_mem_accounts (soup : List SoupEvent)
    (id issuer a payee : String) (amt : Nat)
    (hmem : SoupEvent.escrow id issuer a payee amt ∈ soup) :
    a ∈ accountsOf soup :=
  List.mem_flatMap.mpr ⟨_, hmem, by simp⟩

/-- **S1 completeness.** For ANY account string whatsoever: if the soup
    drives available(a) below zero, the audit emits an S1 finding whose
    subject is `a`. The quantifier is honest — no "provided the account
    is enumerated" side condition, because enumeration is DERIVED: the
    overdraft forces a lock, the lock forces an escrow naming `a` as
    payer, and payers are enumerated. -/
theorem s1_complete (soup : List SoupEvent) (a : String)
    (hneg : available soup a < 0) :
    (⟨.S1, a⟩ : Finding) ∈ settleAudit soup := by
  obtain ⟨id, issuer, payee, amt, hmem⟩ :=
    lock_forces_escrow soup a (overdraft_forces_lock soup a hneg)
  apply List.mem_append_left
  exact List.mem_filterMap.mpr
    ⟨a, payer_mem_accounts soup id issuer a payee amt hmem,
     by simp [s1FindingOf, hneg]⟩

/-- **S1 soundness.** An S1 finding for `a` means available(a) really is
    negative — the audit never slanders an account. -/
theorem s1_sound (soup : List SoupEvent) (a : String)
    (h : (⟨.S1, a⟩ : Finding) ∈ settleAudit soup) :
    available soup a < 0 := by
  cases List.mem_append.mp h with
  | inr h2 => exact absurd (s2Audit_code soup _ h2) (by simp)
  | inl h1 =>
    obtain ⟨b, _, hsome⟩ := List.mem_filterMap.mp h1
    simp only [s1FindingOf] at hsome
    split at hsome
    · rename_i hneg
      cases hsome
      exact hneg
    · cases hsome

/-! ### X0 — substrate equivocation (KERNEL-SPEC Part II) -/

/-- The substrate identity of a fact: (actor, kind, seq). ledger.py's
    `substrate_findings` derives the actor as the first authoring field
    present and skips events lacking a uint seq / string kind / string
    actor; here an event either presents a well-formed identity or none
    — the field plumbing is Python's job, the law is this triple. -/
structure FactIdent where
  actor : String
  kind  : String
  seq   : Nat
deriving Repr, DecidableEq

/-- A substrate event: its content-address and its claimed identity.
    X0 ranges over ALL kinds, including kinds no auditor understands —
    that is the point of promoting fact identity to genesis. -/
structure XEvent where
  id    : String
  ident : Option FactIdent
deriving Repr, DecidableEq

/-- The head event's contribution to the X0 verdict: it convicts its
    identity when some OTHER event (different id — same bytes are the
    SAME fact under content addressing, replay is a no-op) claims the
    same (actor, kind, seq). -/
def x0Head (e : XEvent) (rest : List XEvent) : List FactIdent :=
  match e.ident with
  | some i =>
    if rest.any (fun e' => decide (e'.ident = some i ∧ e'.id ≠ e.id))
    then [i] else []
  | none => []

/-- The X0 audit over the whole soup. Emits the same subject SET as
    ledger.py's seen-dict walk; the conformance surface dedups. -/
def x0Audit : List XEvent → List FactIdent
  | [] => []
  | e :: rest => x0Head e rest ++ x0Audit rest

theorem x0Head_mem (e : XEvent) (rest : List XEvent) (i : FactIdent)
    (hf : e.ident = some i) (e' : XEvent) (he' : e' ∈ rest)
    (hi' : e'.ident = some i) (hne : e'.id ≠ e.id) :
    i ∈ x0Head e rest := by
  have hany : (rest.any fun x => decide (x.ident = some i ∧ x.id ≠ e.id)) = true := by
    apply List.any_eq_true.mpr
    refine ⟨e', he', ?_⟩
    simp only [decide_eq_true_eq]
    exact ⟨hi', hne⟩
  simp only [x0Head, hf, hany, if_true]
  exact List.Mem.head _

theorem x0Head_sound (e : XEvent) (rest : List XEvent) (i : FactIdent)
    (h : i ∈ x0Head e rest) :
    e.ident = some i ∧ ∃ e' ∈ rest, e'.ident = some i ∧ e'.id ≠ e.id := by
  cases hf : e.ident with
  | none => simp [x0Head, hf] at h
  | some j =>
    simp only [x0Head, hf] at h
    split at h
    · rename_i hany
      have hij := List.mem_singleton.mp h
      subst hij
      obtain ⟨e', he', hp⟩ := List.any_eq_true.mp hany
      simp only [decide_eq_true_eq] at hp
      -- `cases hf : e.ident` abstracted `e.ident` to `some i` in the goal,
      -- so the first conjunct is now definitional.
      exact ⟨rfl, e', he', hp.1, hp.2⟩
    · cases h


/-- **X0 completeness.** Any soup containing two events with different
    ids claiming the same (actor, kind, seq) yields an X0 finding whose
    subject is exactly that triple — the equivocation is named, whatever
    the events' kinds, whether or not any auditor understands them. -/
theorem x0_complete (soup : List XEvent) (e e' : XEvent) (i : FactIdent)
    (hi : e.ident = some i) (hi' : e'.ident = some i)
    (hne : e.id ≠ e'.id) :
    e ∈ soup → e' ∈ soup → i ∈ x0Audit soup := by
  induction soup with
  | nil => intro h _; cases h
  | cons f rest ih =>
    intro he he'
    rcases List.mem_cons.mp he with rfl | hetail
    · rcases List.mem_cons.mp he' with rfl | he'tail
      · exact absurd rfl hne
      · exact List.mem_append_left _
          (x0Head_mem e rest i hi e' he'tail hi' (fun h => hne h.symm))
    · rcases List.mem_cons.mp he' with rfl | he'tail
      · exact List.mem_append_left _
          (x0Head_mem e' rest i hi' e hetail hi hne)
      · exact List.mem_append_right _ (ih hetail he'tail)

/-- **X0 soundness.** Every X0 finding names a real equivocation: two
    events in the soup, distinct ids, both claiming the convicted
    triple. -/
theorem x0_sound (soup : List XEvent) (i : FactIdent) :
    i ∈ x0Audit soup →
    ∃ e ∈ soup, ∃ e' ∈ soup,
      e.ident = some i ∧ e'.ident = some i ∧ e.id ≠ e'.id := by
  induction soup with
  | nil => intro h; cases h
  | cons f rest ih =>
    intro h
    rcases List.mem_append.mp h with hl | hr
    · obtain ⟨hf, e', he', hi', hne⟩ := x0Head_sound f rest i hl
      exact ⟨f, List.Mem.head _, e', List.Mem.tail _ he',
             hf, hi', fun hid => hne hid.symm⟩
    · obtain ⟨e, he, e', he', h1, h2, h3⟩ := ih hr
      exact ⟨e, List.Mem.tail _ he, e', List.Mem.tail _ he', h1, h2, h3⟩

/-! ### Executable bindings — the audit convicts and acquits by `rfl` -/

/-- Honest micro-artifact: deposit, escrow, exact release. Clean. -/
example : settleAudit
    [ .deposit "d1" "carol" "alice" 100,
      .escrow  "e1" "carol" "alice" "bob" 60,
      .release "r1" "carol" "e1" 60 ] = [] := rfl

/-- One forged extra release microcredit and the SAME soup convicts:
    S2 naming the escrow. -/
example : settleAudit
    [ .deposit "d1" "carol" "alice" 100,
      .escrow  "e1" "carol" "alice" "bob" 60,
      .release "r1" "carol" "e1" 60,
      .release "r2" "mallory" "e1" 1 ] = [⟨.S2, "e1"⟩] := rfl

/-- An escrow against an account that never deposited convicts by
    itself: S1 naming the account (the issuer escrowed value the account
    never had). -/
example : settleAudit
    [ .escrow "e1" "mallory" "alice" "bob" 80 ] = [⟨.S1, "alice"⟩] := rfl

/-- A release against a ghost escrow convicts itself: S2's unknown arm,
    subject the release's own id. -/
example : settleAudit
    [ .release "r1" "mallory" "ghost" 5 ] = [⟨.S2, "r1"⟩] := rfl

/-- Two facts, different ids, same (actor, kind, seq): X0 names the
    triple. -/
example : x0Audit
    [ ⟨"id1", some ⟨"alice", "charge", 7⟩⟩,
      ⟨"id2", some ⟨"alice", "charge", 7⟩⟩ ]
    = [⟨"alice", "charge", 7⟩] := rfl

/-- Same bytes, same id: a replay is the SAME fact under content
    addressing, not an equivocation. Clean. -/
example : x0Audit
    [ ⟨"id1", some ⟨"alice", "charge", 7⟩⟩,
      ⟨"id1", some ⟨"alice", "charge", 7⟩⟩ ] = [] := rfl

end ChargeKernel
