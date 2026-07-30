/-
ChargeKernel.ProvenanceCompleteness — conviction-completeness of the
P1 arm (charge-provenance/1, KERNEL-SPEC Part III) over adversarial
soups: the F3 campaign's second tranche, extending Completeness.lean
from the settlement laws to the provenance layer.

The law made theorem: **depth is not dilution, as a quantifier.** If an
adversarial soup contains ANY finite derivation chain from an emitted
fact down to an anchored source — three hops, thirty, through cycles,
past junk — and the emission coupling lacks a charge on that source,
the audit emits a P1 finding naming exactly that source. And ONLY real
ancestry convicts: every P1 finding carries a chain witness back.

What is claimed:

  * `p1_complete` — completeness at every fuel: a chain of length n to
    an anchor of source s, with s uncoupled, forces `P1 s` into the
    audit's findings at fuel n (hence, by `p1Audit_fuel_mono`, at every
    larger fuel).
  * `closure_saturates` / `p1_complete_saturated` — the capstone: fuel
    `soup.length` REACHES THE FIXPOINT. Any chain, of any length,
    prunes to one of length ≤ soup.length: every head a chain stands on
    is the derived fact of a soup event, so a chain longer than the
    soup revisits a head (pigeonhole) and the loop between the visits
    cuts out (`headsChain_cut`). Cycles are legal adversarial content
    and buy the adversary nothing: the audit at ONE fixed fuel convicts
    every crime the unbounded law names.
  * `p1_sound` — no false convictions: a P1 finding at any fuel yields
    a chain witness to a real anchor of the named source, uncoupled.
  * Executable micro-artifacts by `decide`: the three-hop laundering
    soup convicts; the honest coupling acquits; a derivation CYCLE
    neither diverges nor convicts falsely.

Model honesty (what is and is not captured):

  * The soup is a List of `PEvent`: `deriv id derived consumed` mirrors
    the `derivation` event's load-bearing fields; `anchor id s`
    collapses P.2's anchor test (a ledger event whose key is
    ["exp", s, ·]) to its content; `junk` is every event the closure
    walk ignores. Ids are opaque; nothing leans on dedup (all theorems
    over ALL lists).
  * One coupling, one reader: the theorems are per (emission, reader)
    instance — `coupled` is the list of sources the coupling already
    charges, and findings name sources. The (node, tick, channel)
    grouping and the reader index are canonicalization machinery owned
    by the Python audit and its test lane, not re-modeled here.
  * The Python walk is a visited-set BFS (the true fixpoint); the model
    walk is fueled expansion. `closure_saturates` is exactly the bridge:
    the fixpoint IS the fuel-soup.length set, so the fueled statements
    cover the real walk's verdicts.
  * NOT claimed: P2 (the DPI max-flow bound — integer max-flow is not
    re-modeled; its arithmetic is owned by `_dpi_maxflow` and its
    multi-hop/parallel-path tests), P3 (resolution), and the V-family
    (attribution recomputation). Open obligations, named here and in
    the L4 register.
-/
import ChargeKernel.Basic

namespace ChargeKernel

/-! ### The adversarial provenance soup -/

/-- The minimal event shape the P1 arm reads. -/
inductive PEvent where
  | anchor (id : String) (source : String)
  | deriv  (id : String) (derived : String) (consumed : List String)
  | junk   (id : String)
deriving Repr, DecidableEq

/-- A provenance finding: P1 names the dropped source. -/
structure PFinding where
  source : String
deriving Repr, DecidableEq

/-! ### The ancestry spec: chains, with lengths and walked heads -/

/-- `ChainN soup n f g`: a derivation chain of length `n` from fact `f`
    down to fact `g` — KERNEL-SPEC P.2's transitive ancestry with the
    path length explicit, so pruning can speak about it. -/
inductive ChainN (soup : List PEvent) : Nat → String → String → Prop where
  | refl (f : String) : ChainN soup 0 f f
  | step {n : Nat} {f mid g : String} {id : String} {cs : List String}
      (hmem : PEvent.deriv id f cs ∈ soup) (hc : mid ∈ cs)
      (htail : ChainN soup n mid g) : ChainN soup (n + 1) f g

/-- A chain with its walked heads reified: `hs` lists every fact the
    chain stands on before stepping (so `hs.length` is the chain
    length, and pigeonhole can argue about repeats). -/
inductive HeadsChain (soup : List PEvent) : List String → String → String → Prop where
  | refl (f : String) : HeadsChain soup [] f f
  | step {hs : List String} {f mid g : String} {id : String} {cs : List String}
      (hmem : PEvent.deriv id f cs ∈ soup) (hc : mid ∈ cs)
      (htail : HeadsChain soup hs mid g) : HeadsChain soup (f :: hs) f g

theorem chain_to_heads (soup : List PEvent) {n : Nat} {f g : String}
    (h : ChainN soup n f g) :
    ∃ hs : List String, hs.length = n ∧ HeadsChain soup hs f g := by
  induction h with
  | refl f => exact ⟨[], rfl, HeadsChain.refl f⟩
  | step hmem hc _ ih =>
    rcases ih with ⟨hs, hlen, hhc⟩
    exact ⟨_ :: hs, by simp [hlen], HeadsChain.step hmem hc hhc⟩

theorem heads_to_chain (soup : List PEvent) {hs : List String} {f g : String}
    (h : HeadsChain soup hs f g) : ChainN soup hs.length f g := by
  induction h with
  | refl f => exact ChainN.refl f
  | step hmem hc _ ih => exact ChainN.step hmem hc ih

/-- The derived facts the soup's derivations produce — the universe
    every chain head lives in. -/
def derivedList (soup : List PEvent) : List String :=
  soup.filterMap fun ev => match ev with
    | .deriv _ dv _ => some dv
    | _ => none

theorem heads_mem_derived (soup : List PEvent) {hs : List String}
    {f g : String} (h : HeadsChain soup hs f g) :
    ∀ x ∈ hs, x ∈ derivedList soup := by
  induction h with
  | refl f => intro x hx; simp at hx
  | @step hs f mid g id cs hmem _ _ ih =>
    intro x hx
    rcases List.mem_cons.mp hx with hx | hx
    · subst hx
      simp only [derivedList, List.mem_filterMap]
      exact ⟨_, hmem, rfl⟩
    · exact ih x hx

/-! ### The executable closure walk (fueled expansion) -/

/-- One expansion step: adjoin every consumed fact of every derivation
    whose derived fact is already reached. Membership-monotone by
    construction (the accumulator rides along). -/
def expand (soup : List PEvent) (acc : List String) : List String :=
  acc ++ soup.flatMap fun ev => match ev with
    | .deriv _ dv cs => if dv ∈ acc then cs else []
    | _ => []

/-- `n` expansion steps from a seed set. -/
def expandN (soup : List PEvent) : Nat → List String → List String
  | 0, acc => acc
  | n + 1, acc => expandN soup n (expand soup acc)

/-- The closure of fact `d` at fuel `n`. -/
def closureN (soup : List PEvent) (n : Nat) (d : String) : List String :=
  expandN soup n [d]

/-- The sources the audit anchors at fuel `n`: soup anchors whose fact
    id is in the closure (P.2's `sources(d)`). -/
def sourcesN (soup : List PEvent) (n : Nat) (d : String) : List String :=
  soup.filterMap fun ev => match ev with
    | .anchor fid s => if fid ∈ closureN soup n d then some s else none
    | _ => none

/-- The P1 arm at fuel `n`: every anchored source the coupling does not
    charge is a finding (KERNEL-SPEC P.5, the dropped-ancestor row). -/
def p1Audit (soup : List PEvent) (coupled : List String) (n : Nat)
    (d : String) : List PFinding :=
  (sourcesN soup n d).filterMap fun s =>
    if s ∈ coupled then none else some ⟨s⟩

/-! ### Walk lemmas: monotone, compositional, complete for chains -/

theorem subset_expand (soup : List PEvent) (acc : List String) :
    ∀ x ∈ acc, x ∈ expand soup acc := by
  intro x hx
  simp [expand, hx]

theorem expand_mono (soup : List PEvent) {a b : List String}
    (h : ∀ x ∈ a, x ∈ b) : ∀ x ∈ expand soup a, x ∈ expand soup b := by
  intro x hx
  simp only [expand, List.mem_append, List.mem_flatMap] at hx ⊢
  rcases hx with hx | ⟨ev, hev, hx⟩
  · exact Or.inl (h x hx)
  · refine Or.inr ⟨ev, hev, ?_⟩
    cases ev with
    | deriv id dv cs =>
      simp only at hx ⊢
      by_cases hdv : dv ∈ a
      · rw [if_pos hdv] at hx
        rw [if_pos (h dv hdv)]
        exact hx
      · rw [if_neg hdv] at hx
        simp at hx
    | anchor id s => simp at hx
    | junk id => simp at hx

theorem expandN_mono (soup : List PEvent) (n : Nat) :
    ∀ {a b : List String}, (∀ x ∈ a, x ∈ b) →
      ∀ x ∈ expandN soup n a, x ∈ expandN soup n b := by
  induction n with
  | zero => intro a b h; exact h
  | succ n ih => intro a b h; exact ih (expand_mono soup h)

theorem subset_expandN (soup : List PEvent) (n : Nat) :
    ∀ (acc : List String), ∀ x ∈ acc, x ∈ expandN soup n acc := by
  induction n with
  | zero => intro acc x hx; exact hx
  | succ n ih =>
    intro acc x hx
    exact ih (expand soup acc) x (subset_expand soup acc x hx)

theorem expandN_add (soup : List PEvent) (m n : Nat) :
    ∀ acc, expandN soup (m + n) acc = expandN soup n (expandN soup m acc) := by
  induction m with
  | zero => intro acc; simp [expandN]
  | succ m ih =>
    intro acc
    have h1 : m + 1 + n = (m + n) + 1 := by omega
    rw [h1]
    show expandN soup (m + n) (expand soup acc) = _
    exact ih (expand soup acc)

/-- Fuel is monotone for closure membership. -/
theorem closureN_fuel_mono (soup : List PEvent) {m n : Nat} (h : m ≤ n)
    (d : String) : ∀ x ∈ closureN soup m d, x ∈ closureN soup n d := by
  intro x hx
  have heq : n = m + (n - m) := by omega
  rw [heq]
  show x ∈ expandN soup (m + (n - m)) [d]
  rw [expandN_add]
  exact subset_expandN soup (n - m) _ x hx

/-- One chain step is one expansion step. -/
theorem step_expand (soup : List PEvent) {acc : List String} {f mid : String}
    {id : String} {cs : List String}
    (hmem : PEvent.deriv id f cs ∈ soup) (hf : f ∈ acc) (hc : mid ∈ cs) :
    mid ∈ expand soup acc := by
  simp only [expand, List.mem_append, List.mem_flatMap]
  refine Or.inr ⟨PEvent.deriv id f cs, hmem, ?_⟩
  simp [hf, hc]

/-- **Walk completeness for bounded chains**: a chain of length n lands
    in the closure at fuel n. -/
theorem mem_closureN_of_chain (soup : List PEvent) {n : Nat} {f g : String}
    (h : ChainN soup n f g) : g ∈ closureN soup n f := by
  induction h with
  | refl f => simp [closureN, expandN]
  | @step n f mid g id cs hmem hc htail ih =>
    have hmid : mid ∈ expand soup [f] :=
      step_expand soup hmem (by simp) hc
    have hemb : ∀ x ∈ expandN soup n [mid], x ∈ expandN soup n (expand soup [f]) := by
      refine expandN_mono soup n ?_
      intro x hx
      simp at hx
      subst hx
      exact hmid
    have hg : g ∈ expandN soup n (expand soup [f]) := hemb g ih
    show g ∈ expandN soup (n + 1) [f]
    have hcomm : n + 1 = 1 + n := by omega
    rw [hcomm, expandN_add]
    exact hg

/-- Soundness of the walk: everything in the expansion got there by a
    chain (of length at most the fuel) from something in the seed. -/
theorem chain_of_mem_expandN (soup : List PEvent) :
    ∀ (n : Nat) (acc : List String) (g : String), g ∈ expandN soup n acc →
      ∃ f, f ∈ acc ∧ ∃ m, m ≤ n ∧ ChainN soup m f g := by
  intro n
  induction n with
  | zero =>
    intro acc g hg
    exact ⟨g, hg, 0, Nat.le_refl 0, ChainN.refl g⟩
  | succ n ih =>
    intro acc g hg
    rcases ih (expand soup acc) g hg with ⟨f, hf, m, hm, hchain⟩
    simp only [expand, List.mem_append, List.mem_flatMap] at hf
    rcases hf with hf | ⟨ev, hev, hf⟩
    · exact ⟨f, hf, m, Nat.le_succ_of_le hm, hchain⟩
    · cases ev with
      | deriv id dv cs =>
        simp only at hf
        by_cases hdv : dv ∈ acc
        · rw [if_pos hdv] at hf
          exact ⟨dv, hdv, m + 1, by omega, ChainN.step hev hf hchain⟩
        · rw [if_neg hdv] at hf
          simp at hf
      | anchor id s => simp at hf
      | junk id => simp at hf

/-! ### Completeness and soundness of the P1 arm, fuel-indexed -/

/-- **P1 completeness**: any soup containing a chain from the emitted
    fact to an anchor of source `s`, with `s` uncoupled, convicts `s`
    at the chain's own fuel. -/
theorem p1_complete (soup : List PEvent) (coupled : List String)
    {n : Nat} {d g s : String}
    (hchain : ChainN soup n d g)
    (hanchor : PEvent.anchor g s ∈ soup)
    (hmiss : s ∉ coupled) :
    (⟨s⟩ : PFinding) ∈ p1Audit soup coupled n d := by
  have hg : g ∈ closureN soup n d := mem_closureN_of_chain soup hchain
  have hs : s ∈ sourcesN soup n d := by
    simp only [sourcesN, List.mem_filterMap]
    refine ⟨PEvent.anchor g s, hanchor, ?_⟩
    show (if g ∈ closureN soup n d then some s else none) = some s
    rw [if_pos hg]
  simp only [p1Audit, List.mem_filterMap]
  exact ⟨s, hs, by rw [if_neg hmiss]⟩

/-- Findings only grow with fuel. -/
theorem p1Audit_fuel_mono (soup : List PEvent) (coupled : List String)
    {m n : Nat} (h : m ≤ n) (d : String) :
    ∀ x ∈ p1Audit soup coupled m d, x ∈ p1Audit soup coupled n d := by
  intro x hx
  simp only [p1Audit, List.mem_filterMap] at hx ⊢
  rcases hx with ⟨s, hs, hif⟩
  refine ⟨s, ?_, hif⟩
  simp only [sourcesN, List.mem_filterMap] at hs ⊢
  rcases hs with ⟨ev, hev, hifa⟩
  refine ⟨ev, hev, ?_⟩
  cases ev with
  | anchor fid src =>
    simp only at hifa ⊢
    by_cases hin : fid ∈ closureN soup m d
    · rw [if_pos hin] at hifa
      rw [if_pos (closureN_fuel_mono soup h d fid hin)]
      exact hifa
    · rw [if_neg hin] at hifa
      simp at hifa
  | deriv id dv cs => simp at hifa
  | junk id => simp at hifa

/-- **P1 soundness**: every finding carries its crime — a chain to a
    real anchor of the named source, which the coupling misses. -/
theorem p1_sound (soup : List PEvent) (coupled : List String)
    {n : Nat} {d s : String}
    (h : (⟨s⟩ : PFinding) ∈ p1Audit soup coupled n d) :
    ∃ g, (∃ m, m ≤ n ∧ ChainN soup m d g) ∧
      PEvent.anchor g s ∈ soup ∧ s ∉ coupled := by
  simp only [p1Audit, List.mem_filterMap] at h
  rcases h with ⟨s', hs', hif⟩
  by_cases hc : s' ∈ coupled
  · rw [if_pos hc] at hif; simp at hif
  · rw [if_neg hc] at hif
    simp at hif
    subst hif
    simp only [sourcesN, List.mem_filterMap] at hs'
    rcases hs' with ⟨ev, hev, hifa⟩
    cases ev with
    | anchor fid src =>
      simp only at hifa
      by_cases hin : fid ∈ closureN soup n d
      · rw [if_pos hin] at hifa
        simp at hifa
        subst hifa
        rcases chain_of_mem_expandN soup n [d] fid hin with ⟨f, hf, m, hm, hchain⟩
        simp at hf
        subst hf
        exact ⟨fid, ⟨m, hm, hchain⟩, hev, hc⟩
      · rw [if_neg hin] at hifa
        simp at hifa
    | deriv id dv cs => simp at hifa
    | junk id => simp at hifa

/-! ### The capstone: saturation — fuel `soup.length` is the fixpoint -/

/-- First-occurrence removal, defined here so the pigeonhole below
    stays free of `Classical.choice` (the core `erase` lemmas carry
    it, and the axiom guards would stop the build). -/
def remove1 (a : String) : List String → List String
  | [] => []
  | b :: t => if b = a then t else b :: remove1 a t

theorem remove1_length {a : String} : ∀ {m : List String}, a ∈ m →
    (remove1 a m).length + 1 = m.length := by
  intro m
  induction m with
  | nil => intro h; simp at h
  | cons b t ih =>
    intro h
    by_cases hb : b = a
    · simp [remove1, hb]
    · have hat : a ∈ t := by
        rcases List.mem_cons.mp h with h' | h'
        · exact absurd h'.symm hb
        · exact h'
      have := ih hat
      simp only [remove1, if_neg hb, List.length_cons]
      omega

theorem mem_remove1_of_ne {x a : String} (hxa : x ≠ a) :
    ∀ {m : List String}, x ∈ m → x ∈ remove1 a m := by
  intro m
  induction m with
  | nil => intro h; simp at h
  | cons b t ih =>
    intro h
    by_cases hb : b = a
    · rcases List.mem_cons.mp h with h' | h'
      · exact absurd (h' ▸ hb) hxa
      · simpa [remove1, hb] using h'
    · rcases List.mem_cons.mp h with h' | h'
      · simp [remove1, hb, h']
      · simp only [remove1, if_neg hb]
        exact List.mem_cons_of_mem b (ih h')

/-- Nodup lists embed by length into anything they are a subset of —
    the pigeonhole's spine. -/
theorem nodup_subset_length : ∀ {l m : List String},
    l.Nodup → (∀ x ∈ l, x ∈ m) → l.length ≤ m.length := by
  intro l
  induction l with
  | nil => intro m _ _; simp
  | cons a t ih =>
    intro m hnd hsub
    have ha : a ∈ m := hsub a List.mem_cons_self
    have hat : a ∉ t := (List.nodup_cons.mp hnd).1
    have hndt : t.Nodup := (List.nodup_cons.mp hnd).2
    have hsub' : ∀ x ∈ t, x ∈ remove1 a m := by
      intro x hx
      have hxa : x ≠ a := fun he => hat (he ▸ hx)
      exact mem_remove1_of_ne hxa (hsub x (List.mem_cons_of_mem a hx))
    have hlen : t.length ≤ (remove1 a m).length := ih hndt hsub'
    have := remove1_length ha
    simp only [List.length_cons]
    omega

/-- A non-nodup list splits around its repeated element. -/
theorem exists_dup_split : ∀ {l : List String}, ¬l.Nodup →
    ∃ (l₁ : List String) (x : String) (l₂ l₃ : List String),
      l = l₁ ++ x :: l₂ ++ x :: l₃ := by
  intro l
  induction l with
  | nil => intro h; exact absurd List.nodup_nil h
  | cons a t ih =>
    intro h
    by_cases hat : a ∈ t
    · rcases List.append_of_mem hat with ⟨s, t', ht⟩
      exact ⟨[], a, s, t', by simp [ht]⟩
    · have hndt : ¬t.Nodup := by
        intro hnd
        exact h (List.nodup_cons.mpr ⟨hat, hnd⟩)
      rcases ih hndt with ⟨l₁, x, l₂, l₃, ht⟩
      exact ⟨a :: l₁, x, l₂, l₃, by simp [ht]⟩

/-- From any point a chain's heads pass through, a chain continues to
    the same end. -/
theorem headsChain_from (soup : List PEvent) :
    ∀ (l : List String) {x : String} {r : List String} {f g : String},
      HeadsChain soup (l ++ x :: r) f g → HeadsChain soup (x :: r) x g := by
  intro l
  induction l with
  | nil =>
    intro x r f g h
    cases h with
    | step hmem hc htail =>
      exact HeadsChain.step hmem hc htail
  | cons a l ih =>
    intro x r f g h
    cases h with
    | step hmem hc htail => exact ih htail

/-- **Loop cutting**: a chain whose heads repeat shortens — the walk
    between the two visits of the repeated head cuts out. -/
theorem headsChain_cut (soup : List PEvent) :
    ∀ (l₁ : List String) {x : String} {l₂ l₃ : List String} {f g : String},
      HeadsChain soup (l₁ ++ x :: l₂ ++ x :: l₃) f g →
      HeadsChain soup (l₁ ++ x :: l₃) f g := by
  intro l₁
  induction l₁ with
  | nil =>
    intro x l₂ l₃ f g h
    simp only [List.nil_append] at h ⊢
    -- the head of (x :: …) forces f = x; the tail walks through x again
    cases h with
    | step _ _ htail => exact headsChain_from soup l₂ htail
  | cons a l₁ ih =>
    intro x l₂ l₃ f g h
    cases h with
    | step hmem hc htail =>
      exact HeadsChain.step hmem hc (ih htail)

/-- **Chain pruning**, fuel-bounded induction: any chain shrinks to one
    no longer than the soup — cut a loop whenever the pigeonhole finds
    a repeated head; each cut strictly shortens, so a fuel of the
    original length suffices. -/
theorem chain_prune_aux (soup : List PEvent) :
    ∀ (k : Nat) {n : Nat} {f g : String}, n ≤ k → ChainN soup n f g →
      ∃ m, m ≤ soup.length ∧ ChainN soup m f g := by
  intro k
  induction k with
  | zero =>
    intro n f g hn h
    have : n = 0 := by omega
    subst this
    exact ⟨0, Nat.zero_le _, h⟩
  | succ k ih =>
    intro n f g hn h
    by_cases hle : n ≤ soup.length
    · exact ⟨n, hle, h⟩
    · rcases chain_to_heads soup h with ⟨hs, hlen, hhc⟩
      have hsub : ∀ x ∈ hs, x ∈ derivedList soup :=
        heads_mem_derived soup hhc
      have hdlen : (derivedList soup).length ≤ soup.length :=
        List.length_filterMap_le _ _
      have hnnd : ¬hs.Nodup := by
        intro hnd
        have := nodup_subset_length hnd hsub
        omega
      rcases exists_dup_split hnnd with ⟨l₁, x, l₂, l₃, hsplit⟩
      have hcut : HeadsChain soup (l₁ ++ x :: l₃) f g :=
        headsChain_cut soup l₁ (hsplit ▸ hhc)
      have hlens := hlen
      rw [hsplit] at hlens
      simp only [List.length_append, List.length_cons] at hlens
      have hshort : (l₁ ++ x :: l₃).length ≤ k := by
        simp only [List.length_append, List.length_cons]
        omega
      exact ih hshort (heads_to_chain soup hcut)

theorem chain_prune (soup : List PEvent) {n : Nat} {f g : String}
    (h : ChainN soup n f g) :
    ∃ m, m ≤ soup.length ∧ ChainN soup m f g :=
  chain_prune_aux soup n (Nat.le_refl n) h

/-- **Saturation**: the fixpoint is reached at fuel `soup.length` —
    membership at ANY fuel implies membership at the fixed fuel. -/
theorem closure_saturates (soup : List PEvent) {d g : String}
    (h : ∃ n, g ∈ closureN soup n d) :
    g ∈ closureN soup soup.length d := by
  rcases h with ⟨n, hn⟩
  rcases chain_of_mem_expandN soup n [d] g hn with ⟨f, hf, m, _, hchain⟩
  simp at hf
  rw [hf] at hchain
  rcases chain_prune soup hchain with ⟨m', hm', hchain'⟩
  exact closureN_fuel_mono soup hm' d g
    (mem_closureN_of_chain soup hchain')

/-- **The capstone**: the audit at the ONE fixed fuel `soup.length`
    convicts every dropped ancestor the unbounded law names — any
    chain, any depth, cycles included. -/
theorem p1_complete_saturated (soup : List PEvent) (coupled : List String)
    {n : Nat} {d g s : String}
    (hchain : ChainN soup n d g)
    (hanchor : PEvent.anchor g s ∈ soup)
    (hmiss : s ∉ coupled) :
    (⟨s⟩ : PFinding) ∈ p1Audit soup coupled soup.length d := by
  rcases chain_prune soup hchain with ⟨m, hm, hchain'⟩
  exact p1Audit_fuel_mono soup coupled hm d _
    (p1_complete soup coupled hchain' hanchor hmiss)

/-! ### Executable micro-artifacts (`decide`) -/

/-- The three-hop laundering soup: srcS anchors a register; three
    derivation hops later FACT emits, coupled only to the emitter.
    P1 names srcS — depth is not dilution, by kernel reduction. -/
def launderSoup : List PEvent :=
  [ .anchor "reg-src" "srcS",
    .deriv "d1" "hop1" ["reg-src"],
    .deriv "d2" "hop2" ["hop1"],
    .deriv "d3" "FACT" ["hop2"],
    .junk "noise" ]

example : (⟨"srcS"⟩ : PFinding) ∈
    p1Audit launderSoup ["chamberA"] launderSoup.length "FACT" := by decide

/-- The honest coupling (srcS charged) acquits. -/
example : p1Audit launderSoup ["chamberA", "srcS"] launderSoup.length "FACT"
    = [] := by decide

/-- A derivation CYCLE with an anchored source inside it: the walk
    terminates at the fixed fuel, the source convicts, and nothing
    else does. -/
def cycleSoup : List PEvent :=
  [ .anchor "reg-src" "srcS",
    .deriv "c1" "FACT" ["loop", "reg-src"],
    .deriv "c2" "loop" ["FACT"] ]

example : (⟨"srcS"⟩ : PFinding) ∈
    p1Audit cycleSoup [] cycleSoup.length "FACT" := by decide

example : p1Audit cycleSoup ["srcS"] cycleSoup.length "FACT" = [] := by
  decide

end ChargeKernel
