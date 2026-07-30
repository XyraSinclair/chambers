/-
ChargeKernel.Widening — audience provenance and the one-way door.

ASSURANCE.md L4 targets 3 and 4, in one model:

  3. Widening one-way-ness: no sequence of ledger operations returns a
     derivative to a narrower audience; confinement is not re-establishable.
  4. Tuple-scope soundness: judgement visibility never exceeds the
     generating tuple without a WideningEvent in the trace.

The model mirrors coalition.ts: a CoalitionalDerivative is born with
`audience = generating coalition` (the zero-cost release, because
self-leakage is free), and the op algebra over a derivative's visibility
has exactly ONE audience-touching constructor — `widen`, the WideningEvent
(`oneWay: true` in the record; HERE that field is a theorem, not a flag).
Charges and intra-coalition projections move the exposure ledger, never
the audience.

The headline theorem is `audience_provenance`, an exact EQUALITY:

    (applyTrace d ops).audience = d.audience ++ widenedReaders ops

Every reader who can see the derivative is either in the birth audience or
admitted by a named widening in the trace — no other door exists in the
algebra. One-way-ness (`audience_never_narrower`), unrevokability
(`confinement_not_reestablishable`), and tuple-scope soundness
(`tuple_scope_sound`, `escape_names_widening`) are corollaries.

Honest limit (same as the rest of this kernel): this proves the ALGEBRA has
one door. That the deployed system's every disclosure path actually routes
through the algebra is L1–L3's job (conformance, fuzz-audit, estimator
probes), and Byzantine nodes are the audit's job, not the model's.
-/

namespace ChargeKernel

/-- The visibility-relevant op algebra over one derivative. `widen` is the
    WideningEvent; `charge` (an ExposureDebit) and `project` (an
    IntraCoalitionProjection to a member already in the audience) are the
    audience-neutral ledger movements. -/
inductive VisOp (R : Type) where
  | widen   (readers : List R)
  | charge  (bits : Nat)
  | project (viewer : R)
deriving Repr, DecidableEq

/-- A derivative's visibility state: the generating tuple it was born to,
    and who can currently see it. Born with `audience = tuple`
    (coalition.ts: `audience: "generating_coalition"`). -/
structure Deriv (R : Type) where
  tuple    : List R
  audience : List R
deriving Repr, DecidableEq

/-- Birth state: visibility IS the generating coalition. -/
def Deriv.birth (tuple : List R) : Deriv R := ⟨tuple, tuple⟩

def applyOp (d : Deriv R) : VisOp R → Deriv R
  | .widen rs  => { d with audience := d.audience ++ rs }
  | .charge _  => d
  | .project _ => d

def applyTrace (d : Deriv R) : List (VisOp R) → Deriv R
  | []        => d
  | op :: ops => applyTrace (applyOp d op) ops

/-- The readers admitted by the widenings of a trace, in order. -/
def widenedReaders : List (VisOp R) → List R
  | []                 => []
  | .widen rs :: ops   => rs ++ widenedReaders ops
  | .charge _ :: ops   => widenedReaders ops
  | .project _ :: ops  => widenedReaders ops

-- ---- frame: the generating tuple never moves ----

theorem applyOp_tuple (d : Deriv R) (op : VisOp R) :
    (applyOp d op).tuple = d.tuple := by
  cases op <;> rfl

theorem applyTrace_tuple (d : Deriv R) (ops : List (VisOp R)) :
    (applyTrace d ops).tuple = d.tuple := by
  induction ops generalizing d with
  | nil => rfl
  | cons op ops ih => rw [applyTrace, ih, applyOp_tuple]

-- ---- the headline: exact audience provenance ----

/-- **Audience provenance.** The final audience is exactly the birth
    audience plus the readers admitted by the trace's widenings. There is no
    other door: nothing else in the algebra adds a reader, and NOTHING
    removes one. -/
theorem audience_provenance (d : Deriv R) (ops : List (VisOp R)) :
    (applyTrace d ops).audience = d.audience ++ widenedReaders ops := by
  induction ops generalizing d with
  | nil => simp [applyTrace, widenedReaders]
  | cons op ops ih =>
    cases op with
    | widen rs =>
      rw [applyTrace, ih, widenedReaders]
      simp [applyOp, List.append_assoc]
    | charge b =>
      rw [applyTrace, ih, widenedReaders]
      rfl
    | project v =>
      rw [applyTrace, ih, widenedReaders]
      rfl

-- ---- corollary: one-way-ness ----

theorem applyTrace_append (d : Deriv R) (pre suf : List (VisOp R)) :
    applyTrace d (pre ++ suf) = applyTrace (applyTrace d pre) suf := by
  induction pre generalizing d with
  | nil => rfl
  | cons op ops ih => rw [List.cons_append, applyTrace, applyTrace, ih]

/-- **Widening one-way-ness.** Extending a trace never narrows the
    audience: every reader visible after any prefix is visible after any
    extension of it. No sequence of ledger operations returns a derivative
    to a narrower audience. -/
theorem audience_never_narrower (d : Deriv R) (pre suf : List (VisOp R))
    (r : R) (h : r ∈ (applyTrace d pre).audience) :
    r ∈ (applyTrace d (pre ++ suf)).audience := by
  rw [applyTrace_append, audience_provenance]
  exact List.mem_append_left _ h

/-- **Confinement is not re-establishable.** A reader once admitted — at
    birth or by any widening — is in the audience of EVERY subsequent
    state. There is no operation sequence after which they are gone. -/
theorem confinement_not_reestablishable (d : Deriv R) (ops : List (VisOp R))
    (r : R) (h : r ∈ d.audience) :
    r ∈ (applyTrace d ops).audience := by
  rw [audience_provenance]
  exact List.mem_append_left _ h

-- ---- corollary: tuple-scope soundness ----

/-- A trace with no widening events. -/
def wideningFree : List (VisOp R) → Prop
  | []                => True
  | .widen _ :: _     => False
  | .charge _ :: ops  => wideningFree ops
  | .project _ :: ops => wideningFree ops

theorem wideningFree_no_readers (ops : List (VisOp R))
    (h : wideningFree ops) : widenedReaders ops = ([] : List R) := by
  induction ops with
  | nil => rfl
  | cons op ops ih =>
    cases op with
    | widen rs => exact absurd h (by simp [wideningFree])
    | charge b => exact ih h
    | project v => exact ih h

/-- **Tuple-scope soundness.** Over any widening-free trace, visibility
    stays EXACTLY the generating tuple — not merely bounded by it. -/
theorem tuple_scope_sound (tuple : List R) (ops : List (VisOp R))
    (h : wideningFree ops) :
    (applyTrace (Deriv.birth tuple) ops).audience = tuple := by
  rw [audience_provenance, wideningFree_no_readers ops h]
  exact List.append_nil _

/-- The contrapositive, constructively: a reader outside the generating
    tuple who can nevertheless see the derivative was admitted by a
    widening — the trace NAMES the event that let them in. -/
theorem escape_names_widening (tuple : List R) (ops : List (VisOp R))
    (r : R) (hsee : r ∈ (applyTrace (Deriv.birth tuple) ops).audience)
    (hout : r ∉ tuple) :
    r ∈ widenedReaders ops := by
  rw [audience_provenance] at hsee
  cases List.mem_append.mp hsee with
  | inl hbirth => exact absurd hbirth hout
  | inr hwiden => exact hwiden

end ChargeKernel
