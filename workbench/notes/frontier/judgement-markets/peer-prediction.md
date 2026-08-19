# Peer prediction under metered leakage — the F5 design memo

*L5 lane, 2026-07-09. Status: DESIGN + WORKED MACHINERY. F5 remains NOT
IMPORTED in FRAMEWORKS.md; this memo is the artifact its row asked for —
the answer to "does the IC bonus survive the leakage price of the
redundancy that generates it," which the row correctly flagged as a
question only this stack can pose. The verdict is split and stated in
§6: a v0 that can run today on existing machinery, a v1 protocol import
held behind three named preconditions, and a genuine KILL on the
high-sensitivity regime — the publishable negative the row predicted,
made arithmetic. A runnable companion (`workbench/peer_sim/`) puts
exact integers through the real meter and settlement.*

**Sources this memo is answerable to:** FRAMEWORKS.md F5; STORIES.md
G10 (judgement quality — "no vocabulary") and G8 (estimator economic
capture); SETTLEMENT-SPEC §5/§11 (the unprovable-lane refusal: outcome
conditions must be attestable or platform-logged; counterfactuals have
no lane); `chambers/review_audit/PROBE-SPEC.md` (coherence receipts
— what the battery certifies and deliberately does not);
ATTRIBUTION-SPEC Part II (the recomputed-fact escrow pattern this memo
inherits); the peer-prediction literature (Miller–Resnick–Zeckhauser
2005; Dasgupta–Ghosh 2013; Shnayder–Agarwal–Frongillo–Parkes 2016,
correlated agreement), imported here for its theorem shape, not its
assumptions.

## 0. The question, and why the literature cannot ask it

Peer prediction prices honesty **without ground truth**: score a
judge's reports by their correlation with a peer's reports on the same
items, minus the correlation with the peer's reports on *different*
items (the penalty pairing that zeroes blind agreement). Under signal
correlation (the Δ-matrix diagonally dominant), truthful reporting is a
strict equilibrium. This is the only known machinery for the lane
charge-settlement/2 refuses: judgment quality that no platform log can
ever attest.

Every treatment in the literature assumes reports are free. Here a
report is preceded by a READ, and a read is an emission: judge j
reading item t charges `m_t` millibits against `["exp", source(t), j]`
— a permanent debit to the owner's lifetime moat toward that reader.
The mechanism's redundancy — the second judge who exists ONLY to price
the first judge's honesty — is not overhead in dollars. It is overhead
in the owner's secrets. The requester wanted one judgment; the
mechanism demands the item be shown twice.

So the F5 question. And the first finding of this memo is that the
question, as posed, has a false presupposition: it asks for a global
verdict ("does IC survive?") about a quantity that this stack makes
**local and integer**. The honest answer has three parts.

## 1. The reframe: IC has a price in mbits, and the protocol's job is to print it

Fix a coupling: owner O, items t₁…t_n with declared emission estimates
m₁…m_n, primary judge J₁ (fee f₁), audit judge J₂ scoring a subset
S ⊆ {t₁…t_n} (fee f₂), CA bonus budget B for J₁.

The **redundancy price** of the mechanism is

> `L = Σ_{t ∈ S} m_t`  millibits, debited to `["exp", O, J₂]`

— an exact integer the artifact already carries (it is the sum of J₂'s
coupled charges; nothing new is metered). The mechanism is worth
running on this coupling iff

> `value_O(J₁ honest) ≥ f₂ + B + price_O(L)`

where `price_O` — what the owner charges for L millibits of additional
lifetime exposure to J₂ — is pricing, and pricing stays above the
protocol, exactly as everywhere else in this stack. **IC neither
survives nor dies globally. It survives on the couplings where the
honesty premium clears the redundancy price, and the protocol's one
obligation is to make that price a visible receipt line
(`redundancy_mbits`) instead of an invisible ops externality.** The
literature could not ask this because it has no meter; we could not
NOT ask it.

Two knobs move L, both stack-native:

- **Spot-check amortization** (standard, sharpened by the meter): J₂
  reads a uniformly hidden subset S, and J₁'s bonus scales by n/|S|.
  Risk-neutral IC is preserved; L scales by |S|/n. The meter turns the
  textbook variance-vs-cost tradeoff into an explicit
  mbits-vs-bonus-variance schedule a coupling can declare.
- **Projection judging** (novel — ours, not the literature's): J₂ need
  not read the item J₁ read. A schema-bound projection π(t) with
  declared capacity m_π < m_t still supports CA **iff the projected
  signal stays correlated with J₁'s** (Δ-dominance surviving the
  coarsening). Leakage-aware mechanism design: choose the cheapest
  projection whose score gap stays strictly positive. Whether a given
  projection preserves dominance is an estimator-lane empirical fact —
  declared, tested, never assumed (§6 precondition 3).

## 2. The structural theorem-shape: the CA score is a ledger fact

The deepest finding, and the one that changes F5's delta. The
settlement doctrine refuses unprovable-lane outcome conditions because
release must gate on facts a stranger can recompute from the artifact.
A judgment's QUALITY is exactly such an unprovable world-fact. But the
CA score is not a world-fact at all: it is **pure integer arithmetic
over reports**, and reports can be ledger events. Score, exact form:

> `score(J₁,J₂) = (n−1) · Σ_t match(t) − Σ_{t ≠ t'} match(t, t')`

— match counts on the diagonal, minus off-diagonal match counts, kept
as multiplied-out integers (the Shapley-numerator discipline; no
expectation operator, no float, ever). Two consequences:

1. **The constant-report strategy scores EXACTLY zero** — not
   approximately, not in expectation: if J₂ reports the constant c,
   both sums equal (n−1)·|{t : x₁(t) = c}| and cancel identically, for
   every soup of reports. Blind agreement earns nothing as an
   arithmetic identity (the sim self-checks it; it is `decide`-grade).
2. **A bonus escrow can bind to the score** the way attribution/2's
   split escrows bind to recomputed rows: release gated on the declared
   score recomputed from named report events, fail closed, court
   pattern unchanged. Peer prediction does not VIOLATE the
   unprovable-lane refusal — it is the mechanism that converts the
   unprovable fact (quality) into a recomputable one (correlation),
   which is precisely the conversion the doctrine demands. F5's "/3
   candidate" is therefore not a new trust class; it is a third
   instance of the recomputed-fact escrow (rows: attribution/2;
   quorums: settlement/2; scores: this).

What the score does NOT certify (audit-the-oracle honesty): CA prices
*informativeness relative to the peer*, not truth. Two correlated
sycophants beat one honest outlier. The residues in §5 own this.

## 3. What the existing machinery already closes (composition, again)

Peer prediction's classic holes meet a stack that has been convicting
adjacent crimes for weeks:

- **Out-of-band item sharing** (J₂ "judges" by reading J₁'s copy):
  undeclared reuse — slashable above protocol
  (`MARKET_LAWS.hiddenReuseIsSlashable`); if laundered through declared
  derivations, P1/P2 convict, now with conviction-completeness theorems
  (`ProvenanceCompleteness.lean`): no laundering topology hides the
  ancestry.
- **Report coordination without reading** (the sycophant): zeroed by
  the penalty pairing (§2.1) AND visible to review-audit/1's coherence
  battery — the R-code signatures (order-swap, framing, polarity) that
  seat judges in the first place. The two instruments are
  complementary: the battery certifies the judge's PROCESS on synthetic
  probes at zero owner leakage; CA prices the judge's OUTPUT on real
  items at metered leakage. Seat with the battery, bonus with CA.
- **Sybil judges** (J₂ is J₁ behind a shell): the mechanism's value
  collapses (self-agreement is maximal) while the owner still pays L —
  the worst cell in the table. Mitigation is the vocabulary that
  already exists: judges declare independence classes
  (`INDEPENDENCE_CLASSES`, settlement/2), and the coupling refuses CA
  bonuses below `role_separated`. Economic capture beneath the declared
  class is G8's standing residue, not a new one.
- **Permutation collusion** (both judges relabel by an agreed
  bijection): the literature's open hole, and ours. Named at L5;
  partially bounded by the battery's polarity probes; not solved.

## 4. The kill regime — the moat's arithmetic refuses the mechanism

Take the items where judgment honesty matters most: high-sensitivity
sources — near-passcode entropy, G5 never-lease partitions, sources
whose owner cedes at most one read of themselves, ever. A precision the
runnable companion forced (the first draft of this section was wrong
and the sim refused to confirm it): the moat is PER READER — a second
judge arrives with a fresh lifetime account, so nothing collides
automatically. The kill is the **owner's registration arithmetic**: for
a high-sensitivity source the owner ceilings the primary judge at
exactly the coupling's needs and grants any audit reader only a token
redundancy budget — or no registration at all ("refusing to register IS
the zero ceiling," the meter's own doctrine, G5's priced sibling).
There:

> the audit reader's coupled charge hits `REFUSED_CEILING` inside the
> owner's declared budget — L is unpayable at any fee.

The mechanism is not expensive on this regime. It is **refused by the
owner's own declarations, live and convictably** — the redundancy IS
disclosure, and the moat exists to bound disclosure. This is F5's predicted kill, made arithmetic rather than
rhetorical, and it is the correct outcome, not a defect: **a mechanism
that buys honesty by spending the owner's secrets must go exactly as
far as the owner's exposure budget and no further.** On the refused
regime, the unprovable lane keeps what it has: flat fees, coherence
receipts, seat-gating — honesty priced by process evidence that costs
zero owner leakage, because the battery's probes are synthetic.

One sentence for the paper this row said would exist: *peer prediction
survives metered leakage only below the moat line, and the moat line is
where it was needed most; above the line, the honest substitute is
process receipts, not output correlation.*

## 5. Residues, named

1. **CA prices correlation, not truth** — a correlated-wrong pair
   outscores an honest outlier. Mitigated (not removed) by seating via
   the battery and independence classes. Permanent.
2. **Permutation collusion** stands (L5), as in all peer prediction.
3. **Projection-judging dominance** is an empirical property per
   (schema, projection) pair — declared and tested, never assumed.
4. **Report events do not exist yet**: today reports ride sim-local
   books (the intro_clearing precedent). The score-bound escrow needs
   them in the artifact (v1 precondition 1).
5. **G8 beneath independence declarations**: an audit judge paid by the
   primary judge's principal passes the declared class and breaks the
   game. Same trust cell as estimator capture; priced once, there.
6. **Risk-neutrality**: spot-check bonus scaling assumes it; a
   risk-averse judge needs a larger B for the same IC pressure — a
   pricing fact, above protocol.

## 6. Verdict — SPLIT, plus a kill

**v0 — run it now, zero protocol change** (the sim is this, live):
CA quality bonuses on LOW-sensitivity couplings only; judges under
declared independence ≥ `role_separated`; every read metered as today;
the receipt carries `redundancy_mbits = L` and the spot-check fraction
openly; the bonus settles as an ordinary escrow whose release the
issuer computes from the (sim-local) reports; constant-strategy zero
self-checked. Nothing here touches a frozen surface.

**v1 — the /3 protocol import, held behind three preconditions:**
1. a report/annotation EVENT KIND, so the CA score is
   stranger-recomputable from the artifact and the bonus escrow becomes
   score-bound (attribution/2's pattern, third instance);
2. an independence story for judges beyond declaration (shared with
   G8's resolution, whatever it turns out to be);
3. estimator-lane evidence that the chosen projections preserve
   Δ-dominance (else projection judging stays a named idea, not a
   shipped knob).

**KILLED — and stated as a law-shaped sentence, not an apology:** peer
prediction on the high-sensitivity regime. The ceiling refuses the
redundancy; the mechanism cannot buy honesty with the owner's secrets;
process receipts own that regime. The import's boundary IS the moat
line, and both sides of the line now know their instrument.
