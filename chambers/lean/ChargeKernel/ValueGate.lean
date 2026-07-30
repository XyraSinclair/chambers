/-
ChargeKernel.ValueGate — the value-gate corollary: S4 inherits the
verdict partition.

THE COROLLARY: no adversary can talk value out of a dirty court by
adding events — a required_clean release convicted against a dirty
court clears ONLY when every finding touching its escrow's keys
retracts by supplying its named missing fact (honest completion), and
against a PERMANENT conviction touching its keys the release is
convicted forever.

This file adds the S4 arm to the adversarial-soup model and proves that
VerdictPartition.lean's partition passes through the gate unchanged:
the retractable side of S4 is exactly the retractable side of the court
it reads, filler for filler; the permanent side is permanent.

What is claimed:

  * `s4Audit` (+ `s4_sound` / `s4_complete`) — the S4 arm as a total
    executable function over the value soup, the F3 sentence shape:
    a conviction names a real dirty-court intersection (a release, a
    resolving required_clean escrow, and a court finding whose subject
    is among the escrow's keys — all present in the soup); every such
    intersection convicts.
  * `s4Audit_mem_swap` — S4 membership is merge-order-blind: the check
    is SET-SHAPED, mirroring settlement.py, where
    `i_findings = _court_findings(ledger)` is computed ONCE from the
    final ledger (a pure function of the event set) and every resolving
    release is checked against that final court — there is no
    tick-ordered arm to model, and this lemma pins the claim.
  * `s4_value_gate` — THE COROLLARY, positive direction: if release r
    is S4-convicted in E and not in E ++ A, then (the gate is named by
    `s4_sound`) for EVERY court finding f of E whose subject touches
    the gate escrow's keys: f is absent from the court of E ++ A, and
    its retraction was completion — S1 findings retracted only by a
    genuinely new credit to their account
    (`s1_retraction_is_completion`), S2 findings only by supplying the
    exact named missing escrow (`s2_retraction_is_completion`). The
    partition theorems are INVOKED, not re-proven.
  * `s4_permanent_against_permanent` — the sharp negative direction:
    an over-disbursed escrow in E whose event id is among the gate
    escrow's keys convicts the release in E ++ A for ALL A
    (`s2_overdisburse_permanent` carries the crime through every
    union). Value fails closed forever against permanent crimes.
  * Examples, both directions, machine-checked in-file (the
    f1_prefix_breaks discipline): `s4_convicts_example` (dirty court
    convicts the release), `s4_honest_completion_example` (the S2 gap
    finding retracts via its NAMED filler arriving in A and the release
    clears — while the court stays dirty ELSEWHERE, pinning the spec's
    touch precision: "a dirty account elsewhere in a shared ledger is
    not this escrow's crime"), `s4_never_clears_example` +
    `s4_never_clears_universal` (a permanent conviction touching the
    keys; one concrete attack soup — deposits plus a forged
    duplicate-id escrow — fails by `decide`, and the universally
    quantified theorem instantiates in-file for ALL extensions).

Modeling choices, each argued against settlement.py — the F1 fidelity
bar (model the implemented predicate, not the wished-for one):

  * SET-SHAPED, verified: `audit_settlement_findings` computes the
    dirty stream once over the whole ledger and checks each release
    against it; the fold and audit are functions of the event set
    (CRDT law). `dirtyOn` reads the audit of the whole soup; no order
    enters anywhere.
  * THE COURT IS THE MODEL'S HONEST SLICE. Real S4 ranges over the
    FULL dirty-court stream — `_court_findings` = the charge-ledger/1
    I-codes plus covenant C-codes, provenance P-codes, attribution
    V-codes. This model carries S1/S2 (Completeness.lean) and nothing
    of the I-court, so the S4 arm here reads `settleAudit` as its
    stand-in court: the GATE LAW (clean-on-touch, checked set-shaped,
    partition inherited) is what is proven; the full-court range is
    the Python audit's surface (NOT claimed). No I-codes are faked.
  * X0 IS EXCLUDED from the S4 range, on fidelity: equivocation
    findings are not in `_court_findings` at all (the dirty stream is
    I/C/P/V; S5 lives in the settlement audit, which S4 never
    consults), no `_touches` arm maps an (actor, kind, seq) triple to
    keys, and the Lean X0 model lives on a separate event type never
    glued to the settlement soup. Fidelity over reach: the permanent
    arm is S2 over-disbursement.
  * TOUCH IS SUBJECT-IN-KEYS — the `_KEY_SUBJECT_CODES` identity arm
    (I1/I2/I7/C2/P1/P2: the finding's subject IS the canonical JSON of
    a key), which is exactly the arm the corpus row
    settlement_traces/s4-dirty-court-release exercises (its S4 fires
    on an I2 finding whose subject is the escrow's key). The model's
    court subjects are already strings, so the identity arm is the
    faithful collapse; the lease-id/charge-id/I8/V subject resolution
    maps and the unknown-code fail-closed default are the Python
    surface (NOT claimed).
  * `VEvent` carries the escrow's `required_clean` + `charge_keys` —
    settlement.py's escrow payload shape — because Completeness.lean's
    SoupEvent deliberately dropped both (S1/S2 read neither) and
    extending it would churn two proven files. `VEvent.toSoup` forgets
    exactly the gate fields; the court is `settleAudit` OF THE
    PROJECTION of the same event list — one soup, one court, and the
    partition theorems apply verbatim through `project_append`.
  * ESCROW RESOLUTION IS PER-EVENT EXISTENTIAL: settlement.py resolves
    `escrow_id` through a dict keyed by content address (same id ⟹
    same bytes; duplicate-id-different-payload soups are
    unrepresentable in the real ledger). On the List superset the gate
    convicts when ANY matching escrow event is required_clean with a
    dirty touch — the same strict-superset discipline as
    `s2_per_event_duplicate_id`, and the reading under which the
    adversarial "add a second escrow with the same id and
    required_clean = false" move provably does nothing
    (`s4_never_clears_universal` covers it for free).
  * The `!keys.isEmpty` guard mirrors settlement.py's
    `if ep.get("required_clean") is True and key_set:` — logically
    redundant here (an empty key list can touch nothing) but kept so
    the gate is the implemented predicate line for line.

NOT claimed (named so the register stays honest):

  * The full dirty-court range (I/C/P/V codes) and the multi-arm
    subject→key resolution including the fail-closed unknown-code
    default — the Python audit's surface, above.
  * S8's default-resolution clean-court arm (the same check applied to
    release-direction defaults, reported under S8) — same shape,
    unproven here.
  * S3 work receipts, S7 expiry, S9–S12 — untouched.
  * A corpus-trace binding: the one S4 corpus row
    (s4-dirty-court-release) convicts through an I2 finding, an I-code
    this model does not carry; the in-file examples mirror its SHAPE
    (identity-arm touch on the gate escrow's key) against the model's
    own court instead of faking the I-court.
-/
import ChargeKernel.VerdictPartition

namespace ChargeKernel

/-! ### The value soup: Completeness's events plus the S4 gate fields -/

/-- The settlement soup with the escrow's gate fields restored
    (settlement.py escrow payload: `required_clean`, `charge_keys`).
    A key string stands for the canonical JSON of a charge-ledger key. -/
inductive VEvent where
  | deposit (id issuer account : String) (amount : Nat)
  | escrow  (id issuer payer payee : String) (amount : Nat)
            (requiredClean : Bool) (chargeKeys : List String)
  | release (id issuer escrowId : String) (amount : Nat)
  | refund  (id issuer escrowId : String) (amount : Nat)
  | junk    (id : String)
deriving Repr, DecidableEq

/-- Forget exactly the gate fields: the court reads Completeness.lean's
    model of the SAME event list. -/
def VEvent.toSoup : VEvent → SoupEvent
  | .deposit id i a n      => .deposit id i a n
  | .escrow id i p q n _ _ => .escrow id i p q n
  | .release id i e n      => .release id i e n
  | .refund id i e n       => .refund id i e n
  | .junk id               => .junk id

def project (soup : List VEvent) : List SoupEvent :=
  soup.map VEvent.toSoup

theorem project_append (E A : List VEvent) :
    project (E ++ A) = project E ++ project A := by
  unfold project
  exact List.map_append ..

/-! ### The S4 arm, as a total executable function -/

/-- The court is dirty ON `keys` — some finding's subject is among them
    (the identity touch arm; see header). Set-shaped: reads the audit
    of the WHOLE soup, like settlement.py's one-shot `i_findings`. -/
def dirtyOn (soup : List VEvent) (keys : List String) : Bool :=
  (settleAudit (project soup)).any fun f => keys.contains f.subject

/-- The gate for a release naming escrow id `eid`: some escrow event
    with that id is required_clean, has keys, and its keys are dirty. -/
def s4Gate (soup : List VEvent) (eid : String) : Bool :=
  soup.any fun ev => match ev with
    | .escrow id _ _ _ _ rc keys =>
        id = eid && rc && !keys.isEmpty && dirtyOn soup keys
    | _ => false

/-- One event's S4 contribution: a release convicts ITSELF (subject =
    the release event id, SETTLEMENT-SPEC §3) when its escrow's gate
    fires. Refunds never S4 (spec: "a refund needs no clean court"). -/
def s4FindingsOf (soup : List VEvent) : VEvent → List String
  | .release id _ eid _ => if s4Gate soup eid then [id] else []
  | _ => []

/-- The S4 audit: the convicted release event ids. -/
def s4Audit (soup : List VEvent) : List String :=
  soup.flatMap (s4FindingsOf soup)

/-! ### Soundness and completeness — the F3 sentence shape -/

/-- **S4 soundness.** A conviction names a real dirty-court
    intersection, every piece present in the soup: the convicted
    release, a required_clean escrow it resolves, and a court finding
    whose subject is among that escrow's keys. -/
theorem s4_sound (soup : List VEvent) (rid : String)
    (h : rid ∈ s4Audit soup) :
    ∃ ri eid amtR ei py pe amtE keys,
      VEvent.release rid ri eid amtR ∈ soup ∧
      VEvent.escrow eid ei py pe amtE true keys ∈ soup ∧
      ∃ f ∈ settleAudit (project soup), f.subject ∈ keys := by
  obtain ⟨ev, hev, hf⟩ := List.mem_flatMap.mp h
  cases ev with
  | release id issuer eid amt =>
    simp only [s4FindingsOf] at hf
    split at hf
    · rename_i hgate
      have hid := List.mem_singleton.mp hf
      subst hid
      obtain ⟨esc, hescmem, hcond⟩ := List.any_eq_true.mp hgate
      cases esc with
      | escrow id2 ei py pe amtE rc keys =>
        simp only [Bool.and_eq_true, decide_eq_true_eq] at hcond
        obtain ⟨⟨⟨hid2, hrc⟩, _⟩, hdirty⟩ := hcond
        subst hid2; subst hrc
        obtain ⟨f, hfmem, hfsub⟩ := List.any_eq_true.mp hdirty
        exact ⟨issuer, _, amt, ei, py, pe, amtE, keys, hev, hescmem,
          f, hfmem, by simpa using hfsub⟩
      | deposit id2 i a n => simp at hcond
      | release id2 i e n => simp at hcond
      | refund id2 i e n => simp at hcond
      | junk id2 => simp at hcond
    · cases hf
  | deposit id i a n => simp [s4FindingsOf] at hf
  | escrow id i p q n rc keys => simp [s4FindingsOf] at hf
  | refund id i e n => simp [s4FindingsOf] at hf
  | junk id => simp [s4FindingsOf] at hf

/-- **S4 completeness.** Every dirty-court intersection with a
    required_clean release convicts: release present, resolving escrow
    present and required_clean, any court finding touching its keys —
    the release id enters the audit. -/
theorem s4_complete (soup : List VEvent) (rid ri eid : String) (amtR : Nat)
    (ei py pe : String) (amtE : Nat) (keys : List String)
    (hrel : VEvent.release rid ri eid amtR ∈ soup)
    (hesc : VEvent.escrow eid ei py pe amtE true keys ∈ soup)
    (f : Finding) (hf : f ∈ settleAudit (project soup))
    (hsub : f.subject ∈ keys) :
    rid ∈ s4Audit soup := by
  have hgate : s4Gate soup eid = true := by
    apply List.any_eq_true.mpr
    refine ⟨_, hesc, ?_⟩
    have hdirty : dirtyOn soup keys = true := by
      apply List.any_eq_true.mpr
      exact ⟨f, hf, by simpa using hsub⟩
    have hne : keys.isEmpty = false := by
      cases keys with
      | nil => cases hsub
      | cons k ks => rfl
    simp [hdirty, hne]
  exact List.mem_flatMap.mpr ⟨_, hrel, by simp [s4FindingsOf, hgate]⟩

/-- **Merge-order insensitivity (S4).** The gate is set-shaped: a
    release is convicted in E ++ A iff in A ++ E — through the
    sound+complete characterization and the court's own swap law. -/
theorem s4Audit_mem_swap_aux (E A : List VEvent) (rid : String)
    (h : rid ∈ s4Audit (E ++ A)) : rid ∈ s4Audit (A ++ E) := by
  obtain ⟨ri, eid, amtR, ei, py, pe, amtE, keys, hrel, hesc, f, hf, hsub⟩ :=
    s4_sound (E ++ A) rid h
  have hf' : f ∈ settleAudit (project (A ++ E)) := by
    rw [project_append] at hf ⊢
    exact (settleAudit_mem_swap (project E) (project A) f).mp hf
  exact s4_complete (A ++ E) rid ri eid amtR ei py pe amtE keys
    (mem_append_swap hrel) (mem_append_swap hesc) f hf' hsub

theorem s4Audit_mem_swap (E A : List VEvent) (rid : String) :
    rid ∈ s4Audit (E ++ A) ↔ rid ∈ s4Audit (A ++ E) :=
  ⟨s4Audit_mem_swap_aux E A rid, s4Audit_mem_swap_aux A E rid⟩

/-! ### The named completions (VerdictPartition's conclusions, as
predicates, so the corollary can invoke them by name) -/

/-- The S1 retraction certificate: a genuinely new fund fact crediting
    `a` — verbatim the conclusion of `s1_retraction_is_completion`. -/
def S1Completion (E A : List SoupEvent) (a : String) : Prop :=
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
       SoupEvent.refund rid ri eid amtR ∈ A))

/-- The S2 retraction certificate: the exact named missing escrow,
    supplied — verbatim the conclusion of
    `s2_retraction_is_completion`. -/
def S2Completion (E A : List SoupEvent) (subj : String) : Prop :=
  ∃ eid, hasEscrow E eid = false ∧
    (∃ issuer amt, SoupEvent.release subj issuer eid amt ∈ E ∨
                   SoupEvent.refund subj issuer eid amt ∈ E) ∧
    ∃ issuer payer payee amt, SoupEvent.escrow eid issuer payer payee amt ∈ A

/-! ### The corollary, both directions -/

/-- **THE VALUE-GATE COROLLARY.** If release `rid` is S4-convicted in E
    and NOT convicted in E ++ A, then — with the gate named by
    soundness (its release, its required_clean escrow, and at least one
    touching court finding, all in E) — EVERY court finding of E whose
    subject touches the gate escrow's keys is GONE from the court of
    E ++ A, and each such retraction was honest completion: an S1
    finding died only by a genuinely new credit to its account, an S2
    finding only by the arrival of its exact named missing escrow. The
    partition theorems do the work; nothing is re-proven. -/
theorem s4_value_gate (E A : List VEvent) (rid : String)
    (hconvict : rid ∈ s4Audit E)
    (hclear : rid ∉ s4Audit (E ++ A)) :
    ∃ ri eid amtR ei py pe amtE keys,
      VEvent.release rid ri eid amtR ∈ E ∧
      VEvent.escrow eid ei py pe amtE true keys ∈ E ∧
      (∃ f ∈ settleAudit (project E), f.subject ∈ keys) ∧
      ∀ f ∈ settleAudit (project E), f.subject ∈ keys →
        f ∉ settleAudit (project (E ++ A)) ∧
        (f.code = .S1 → S1Completion (project E) (project A) f.subject) ∧
        (f.code = .S2 → S2Completion (project E) (project A) f.subject) := by
  obtain ⟨ri, eid, amtR, ei, py, pe, amtE, keys, hrel, hesc, hdirt⟩ :=
    s4_sound E rid hconvict
  refine ⟨ri, eid, amtR, ei, py, pe, amtE, keys, hrel, hesc, hdirt, ?_⟩
  intro f hfE hsub
  have hnot : f ∉ settleAudit (project (E ++ A)) := fun hfEA =>
    hclear (s4_complete (E ++ A) rid ri eid amtR ei py pe amtE keys
      (List.mem_append_left _ hrel) (List.mem_append_left _ hesc) f hfEA hsub)
  have hnot' : f ∉ settleAudit (project E ++ project A) := by
    rw [← project_append]; exact hnot
  obtain ⟨c, subj⟩ := f
  refine ⟨hnot, ?_, ?_⟩
  · intro hcode
    cases c with
    | S1 => exact s1_retraction_is_completion (project E) (project A) subj hfE hnot'
    | S2 => simp at hcode
  · intro hcode
    cases c with
    | S1 => simp at hcode
    | S2 => exact s2_retraction_is_completion (project E) (project A) subj hfE hnot'

/-- **Permanent conviction, permanent gate — the sharp negative
    direction.** If an escrow in E is over-disbursed (the PERMANENT
    S2 arm) and its event id is among the gate escrow's keys, then the
    release is S4-convicted in E ++ A for ALL extensions A: value fails
    closed forever against permanent crimes. Composition of
    `s2_overdisburse_permanent` with `s4_complete`. -/
theorem s4_permanent_against_permanent (E : List VEvent)
    (rid ri eid : String) (amtR : Nat)
    (ei py pe : String) (amtE : Nat) (keys : List String)
    (hrel : VEvent.release rid ri eid amtR ∈ E)
    (hesc : VEvent.escrow eid ei py pe amtE true keys ∈ E)
    (cid ci cp cq : String) (camt : Nat) (crc : Bool) (ckeys : List String)
    (hcrime : VEvent.escrow cid ci cp cq camt crc ckeys ∈ E)
    (hover : camt < releasedTo (project E) cid + refundedTo (project E) cid)
    (htouch : cid ∈ keys) :
    ∀ A : List VEvent, rid ∈ s4Audit (E ++ A) := by
  intro A
  have hcrime' : SoupEvent.escrow cid ci cp cq camt ∈ project E :=
    List.mem_map_of_mem hcrime
  have hs2 : (⟨.S2, cid⟩ : Finding) ∈ settleAudit (project (E ++ A)) := by
    rw [project_append]
    exact s2_overdisburse_permanent (project E) (project A) cid ci cp cq camt
      hcrime' hover
  exact s4_complete (E ++ A) rid ri eid amtR ei py pe amtE keys
    (List.mem_append_left _ hrel) (List.mem_append_left _ hesc)
    ⟨.S2, cid⟩ hs2 htouch

/-! ### The witnesses — both directions, machine-checked in-file -/

/-- The gate soup: a required_clean escrow whose keys name the court's
    S2 subject, its release, and the dangling disbursement that dirties
    the court. -/
def gateSoup : List VEvent :=
  [ .escrow "e1" "carol" "alice" "bob" 60 true ["r1"],
    .release "rel1" "carol" "e1" 60,
    .release "r1" "mallory" "ghost" 5 ]

/-- The honest completion: exactly the named missing escrow ("ghost"). -/
def gateFix : List VEvent :=
  [ .escrow "ghost" "dave" "px" "py" 10 false [] ]

/-- **S4 convicts — witnessed.** The court holds S2 "r1" (a dangling
    release), "r1" is among the gate escrow's keys, and the release is
    convicted. -/
theorem s4_convicts_example :
    (⟨.S2, "r1"⟩ : Finding) ∈ settleAudit (project gateSoup) ∧
    "rel1" ∈ s4Audit gateSoup := by
  decide

/-- **The honest direction is REAL — witnessed.** The extension
    supplies exactly the finding's named filler (escrow "ghost"), the
    S2 conviction retracts, and the release CLEARS — while the merged
    court is still dirty on "alice" (and on the fix's own payer):
    clean-ON-TOUCH is what gates value, the spec's own touch precision
    ("a dirty account elsewhere in a shared ledger is not this
    escrow's crime"). -/
theorem s4_honest_completion_example :
    "rel1" ∈ s4Audit gateSoup ∧
    (⟨.S2, "r1"⟩ : Finding) ∉ settleAudit (project (gateSoup ++ gateFix)) ∧
    "rel1" ∉ s4Audit (gateSoup ++ gateFix) ∧
    (⟨.S1, "alice"⟩ : Finding) ∈ settleAudit (project (gateSoup ++ gateFix)) := by
  decide

/-- The permanent-crime soup: the gate escrow's keys name an
    over-disbursed escrow ("bad": amount 10, released 50). -/
def permSoup : List VEvent :=
  [ .escrow "e1" "carol" "alice" "bob" 60 true ["bad"],
    .release "rel1" "carol" "e1" 10,
    .escrow "bad" "mallory" "ma" "mb" 10 false [],
    .release "rx" "eve" "bad" 50 ]

/-- One concrete attack: flood deposits AND forge a duplicate-id escrow
    with a huge amount (the `s2_per_event_duplicate_id` move). -/
def permAttack : List VEvent :=
  [ .deposit "d1" "phil" "alice" 1000000,
    .deposit "d2" "phil" "ma" 1000000,
    .escrow "bad" "forger" "ma" "mb" 1000000 false [] ]

/-- **The permanent direction, one concrete attack failing by
    `decide`.** The deposits clear what is clearable and the forged
    duplicate-id escrow moves nothing (per-event audit); the S2
    conviction stands and the release stays convicted. -/
theorem s4_never_clears_example :
    "rel1" ∈ s4Audit permSoup ∧
    (⟨.S2, "bad"⟩ : Finding) ∈ settleAudit (project (permSoup ++ permAttack)) ∧
    "rel1" ∈ s4Audit (permSoup ++ permAttack) := by
  decide

/-- **The permanent direction, ALL extensions** — the universally
    quantified theorem instantiated on the concrete soup: no A
    whatsoever clears "rel1". -/
theorem s4_never_clears_universal :
    ∀ A : List VEvent, "rel1" ∈ s4Audit (permSoup ++ A) :=
  s4_permanent_against_permanent permSoup
    "rel1" "carol" "e1" 10 "carol" "alice" "bob" 60 ["bad"]
    (by decide) (by decide)
    "bad" "mallory" "ma" "mb" 10 false []
    (by decide) (by decide) (by decide)

end ChargeKernel
