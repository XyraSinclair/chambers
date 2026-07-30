# Consult report — moat type-theory lens (fable subagent, 2026-07-06)

*Primary source, preserved verbatim (two parts, joined). Adjudicated
synthesis lives in README.md. Charter: the type-level discipline for
generative private-data moats, against CANON.md's admission gate and the
2026-07-02 premier-type-surface verdict.*

---

# The type-level discipline for generative private-data moats — PART 1 (invariant set + discipline survey)

**The object, in this stack's nouns.** A moat is not a new thing; it is the *interior* the twelve modules already orbit: the owner-private, provenance-closed DAG of artifacts, annotations, and judgements that every `Run` extends, whose only exterior morphisms are charged emissions. The claim to make theorem-shaped is a conjunction of four checkable statements and one refusal:

> **The Moat Theorem (target shape).** For every chamber C, reader r, under any interleaving across any number of nodes, sessions, and coalitions: (i) the interior DAG only grows (inflation); (ii) the summed charged capacity of everything r has ever observed of C never exceeds ceiling(C, r) (cap — proven for the honest kernel); (iii) every emission's charge covers the provenance closure of its content (closure — the open one); (iv) any violation of (i)–(iii) leaves a finite witness in the court that a stranger can convict from bytes alone (conviction-completeness, F3's shape). Standing non-claims, printed on every receipt: charges are declared capacity, not harm (G2); readers are claimed entities (G3/frontier #1); entropy denominators depreciate (G13).

One decomposition before anything else, because it is where moat-talk usually lies: **"the moat compounds" splits into a structural half and an economic half.** The structural half — the interior grows monotonically, remembers its sources, and its exterior budget only ratchets down — is theorem-shaped and mostly already proven. The economic half — the interior is *worth* more — is an estimated-lane market fact the type system can only refuse to lie about, exactly as `OptionValueEstimate` refuses (`estimatorRole: "price_input"`, never a gate). Any design that types "moat value" as a load-bearing field has imported the ε-halo under a new name. Everything below is about the structural half.

---

## 1. The invariant set

### M1 — Accumulation is lattice inflation. **PARTIALLY CARRIED.**

*The invariant.* The interior is a join-semilattice of content-addressed facts; every operation is inflationary: M ⊑ M ⊔ op(M). Deletion is representable only as a *point in the lattice* — a tombstone that is itself a grown fact — never as a retraction. Merge of two views of the interior is join, so replication can only escalate, never lose.

*What carries it.* The court side is fully carried and is the stack's best property: the kernel ledger is a grow-only CRDT (union by sha256 id, byte-equality conflict = the only fatal error), the fold is monotone by construction ("merge escalates, never retracts"), X0 makes fact identity a substrate law so replays and equivocations convict rather than collapse. The artifact side is carried at the record level: `Artifact.redactionState: "erased_tombstone"` with the salted-commitment discipline (`sha256(salt‖payload)` at write time, so erasure destroys salt+bytes while every `causalParentIds` link still verifies), and `retentionOutlivesTheClaimsItBacks` prevents deleting scratch out from under a live claim.

*What is missing.* No law says the **value-bearing interior** is append-only. `CORE_LAWS` polices crossings; nothing forbids a chamber implementation from overwriting its annotation store in place, orphaning provenance edges, or garbage-collecting artifacts whose `retainedUntil` passed but which sit in the closure of a *later* derived fact. The retention invariant protects claims; it does not protect *ancestry*. The moat needs the dual of `retentionOutlivesTheClaimsItBacks`: **retention outlives the derivations it feeds** — an artifact reachable from any live artifact's provenance closure is tombstonable but not droppable. This is one law and one audit check (closure ⊆ retained-or-tombstoned), not a new record.

### M2 — Projection is the only exterior functor, and it is charged-coupled. **CARRIED AT THE KERNEL; PARTIAL AT CANON.**

*The invariant.* A fact with non-owner visibility is reachable *only* through a typed emission: schema-bound (typing is what caps channel capacity — `coalition.ts` says this exactly), capacity charged at the adversarial maximum *before* release, and coupled all-or-none across every account the emission draws on. Unrepresentable form: `visibility ≠ owner_private ⟹ ∃ EgressDebit ∧ LedgerEntry`, with the debit's coupling atomic in both directions — no partial emission, no phantom debit from a refused one.

*What carries it.* This is the stack's center of mass. `noCrossingWithoutALedgerEntry`, adversarial-maximum capacity, the numeric∧ordinal conjunction gate, and — decisively — `Accountant.charge_coupled` in charge-kernel/2, which fixed exactly the two failure modes a moat cares about (debits for emissions that never flowed; emissions that cleared some accounts and not others). The mediation session already charges *both* sides of the boundary: reading the interior is exposure of the interior (a read past the exposure lease means the agent simply cannot see that much), and emission debits the requester-as-reader against every tuple member atomically.

*What is missing.* The premier-type-surface cut's confirmed findings are precisely the moat's leak inventory and need no relitigating: matching bucket emissions, `CreditSettlement.amount`, and `NotificationAttempt` are not type-forced into debits; the `"one_bit"` cleared-branch overclaim; the conjunction gate as doc-comment. Tier 0 of that cut *is* M2's completion. One moat-specific addition: the interior's compounding makes the *read* channel grow in value — as the moat deepens, one read of a derived judgement is worth many reads of raw silo. The exposure charge for reading derived structure must therefore be keyed to the derived fact's *closure capacity*, not its byte size — which is M4's job. M2 and M4 meet at exactly this point.

### M3 — Residual monotonicity: what has crossed is permanently crossed, and the remainder is a computable sentence. **THEOREM CARRIED; THE SENTENCE MISSING.**

*The invariant.* Per (source chamber × reader entity), lifetime-scoped: `residual(s,r) := ceiling − cumulative` is monotone non-increasing under merge and any interleaving, never replenishes (lifetime keys, "information is never unlearned"), and is ≥ 0 for honest nodes — the global cap theorem, proven in Lean. Widening is a priced one-way event (`WideningEvent.oneWay: true`); the covenant's `residue` field names what stays exposed forever and refuses to pretend otherwise.

*What carries it.* Almost everything: the exposure-account key (`["exp", source, reader]`, pair-lifetime, the one key the cross-coalition accumulation attack cannot slip past), min-resolution of conflicting registrations, monotone escalation laws, lease partition. This is the moat's floor and it is the most-proven floor in the stack.

*What is missing.* The moat's *residue statement* as a compiled artifact. The premier cut already proposed `PlainAccount.whatDidNotCross` be **compiled from budget residuals** rather than asserted; the moat is the reason to ship it. A moat owner's one honest exterior sentence is: "reader r has consumed X of the Y millibits I ever ceded; the residual is Z; this is a budget fact, not a secrecy fact." That sentence is pure fold arithmetic today — recomputable by a stranger from the court — but no receipt schema carries it. Note also the moat's **decay term**: declared `subject_entropy` is a delta over public knowledge, which moves (G13). The residual honestly depreciates as the world learns; G13's owner-signed monotone-down re-declaration is the moat's depreciation schedule, and it moves in the direction the merge laws already prove safe. A moat statement that omits G13 overstates the moat.

### M4 — Provenance closure: derived structure remembers its sources, and projections charge the ancestry. **DATA CARRIED; LAW MISSING. This is the moat's load-bearing gap.**

*The invariant.* Every derived interior fact carries its transitive source closure; every emission of a derived fact debits, coupled and atomically, every source in that closure, with the data-processing inequality supplying the sound per-hop bound (charge toward source s via derivative d is capped by the min-cut of first-hop capacities on paths s→d — post-processing cannot manufacture information about s). Convictable violation: an emission whose consumed-judgement set dropped an ancestor. "Not separable from its ancestry."

*What carries it.* The records exist: `Artifact.provenance: ProvenanceEdge[]`, `CoalitionalDerivative.sourceChamberIds` (non-empty tuple, typed), leaf charges name their sources, mediation couples the emission charge across the *tuple*. G14's register row says it plainly: ledger-computable today.

*What is missing.* The coupling is over the **session tuple**, not the **transitive closure**. Chained judgements — a judgement consumed by a later run, whose output crosses to a terminal reader — charge the original sources only by orchestrator discipline, not law. This matters doubly for moats, because **the moat's compounding mechanism and the moat-laundering attack are the same operation**: derive, re-derive, project from the derivative. Without M4, depth is dilution — every internal hop washes a source out of the charge set, and the deeper (more valuable) the moat, the cheaper its leaks. With M4, depth is *safe* compounding: internal derivation stays free (self-leakage is free — the coalition module's zero-cost release principle), and only the boundary pays, but it pays for everything upstream. M4 is what makes "generative" and "never leaks past its budget" compatible rather than in tension. It is the single highest-value delta this lens finds, and it is an *audit family plus one event kind*, not a primitive (Part 2, §3).

### M5 — Exit caps authority, never rewrites history. **CARRIED; portability residue unexercised.**

*The invariant.* Wind-down decomposes exactly as charge-covenant/1 decomposes revocation: tenor (every lease expires), covenant (cease/cap on future issuance, with grandfathered authority named *by content id in the covenant's own bytes*), residue (the honest prose of what stays exposed — unenforceable by theorem, named on purpose). Value fails closed against any covenant breach, including C-codes the auditor cannot parse. Erasure destroys bytes, never proofs. The composite: **a moat is windable-down without being erasable** — the owner can refuse all future authority over the interior while the court that backs every receipt others hold stays intact and every subject tombstone stays exercisable.

*What carries it.* Essentially all of it, and recently: `charge-covenant/1` (the strictest covenant binds; un-covenanting is impossible by construction; `cap_mbits: 0` is "no new authority, ever"), S8 (no issuer strands funds; exit never strands money), the tombstone discipline, `retentionOutlivesTheClaimsItBacks`. The monitorability design law is satisfied: both covenant forms are safety properties.

*What is missing.* Two residues, both already named in the registers: (1) **portability** — export the interior, re-attach under a new house with cumulative exposure accounts intact — is "implied by the data model, never exercised" (G7). For a moat this is not a nicety; a moat that cannot move houses is a hostage, and hostage-shaped assets get discounted by exactly the parties the stack wants to attract. It needs a dogfooded run, not a type. (2) **Succession** is frontier #8's governance half: `Chamber.ownerId` is one `Principal`; a moat that outlives its owner (labs, estates) has no quorum story. Named, open, not moat-specific.

---

## 2. The discipline survey, ranked for this job

The 2026-07-02 cut settled the substrate question (branded-ADT canon + graded-semiring accountant + relational validator; sovereignty filters guarantees; only re-checkable artifacts cross). Nothing below reopens it. The question here is narrower: which disciplines add anything *for the moat invariants specifically*.

| # | Discipline | What it buys for moats | What it costs | Verdict |
|---|---|---|---|---|
| 1 | **Graded semirings / graded modal (QTT)** — the incumbent | M2 and M3 as algebra: the exterior functor is graded, grades add along the semiring, the cap is grade subsumption; the moat theorem's clause (ii) is a *corollary of the already-proven global cap theorem* once keys are `["exp", s, r]` — which shipped | Structured channels only; side-channel leaves stay attested axioms | **IMPORT** (already in; the moat asks for zero new algebra, one new corollary printed as a receipt) |
| 2 | **Refinement types over court files** — as the relational validator (§12 rename honored) | M1's closure-retention check, M3's residual arithmetic, M4's dropped-ancestor conviction, M5's grandfather-set subset checks are all hash-equality / set-subset / integer-monotonicity — exactly the validator's grain, and the only guarantee that crosses the sovereign boundary | Statement bugs (a certified-wrong closure check is worse than none); the fact-canonicalization pin | **IMPORT** (the moat's audit family is validator work, not proof-term work) |
| 3 | **Ownership & borrowing, Rust regions** | The sharpest *vocabulary* for the moat: chamber = region; admission = `&Chamber` (a shared borrow that cannot escape); projection = the only `move` out; the egress gate = escape analysis; membrane revocation = dropping the borrow. Explains in one sentence why interior copying is free and boundary crossing is not | No compile-time story survives sovereignty (the counterparty doesn't run your borrow checker); the stack *deliberately* audits-after-merge and convicts rather than prevents — a borrow checker prevents | **LENS-ONLY** (name the analogy in docs; import no mechanism — leases already are the affine tokens) |
| 4 | **Linear/affine types** | One real insight: the moat discipline is an **LNL-style adjoint decomposition** — a cartesian interior (facts copy free; self-leakage is free; the moat is deliberately *non*-linear) mated to a graded/affine boundary (lease amounts spend-once and drain by tenor). The type theory says the split itself is the design, and the graded modality is the mediating comonad — which is what the accountant already is | Full linearity misplaced on the interior would *destroy* the moat (a moat is precisely the thing you reuse without consuming); monitors remain the deployable form | **LENS-ONLY** (the adjunction names why M1 and M2 don't contradict; already the de facto architecture) |
| 5 | **Session types (MPST)** | M2's ordering half — charge-precedes-emission, accumulate\*/project alternation as a lane shape — and blame-at-message-k when a counterparty projects out of order | Everything the prior cut priced: lane-shape governance, rigidity vs. human moves; audit-after-merge admits ill-typed events on purpose (they convict, not crash) | **LENS-ONLY** (per prior verdict; the moat adds no new reason to promote it) |
| 6 | **IFC (DCC / FLAC label lattices)** | Almost nothing new: the moat's lattice is two-point (`owner_private` vs. crossed), already carried by `Visibility`; conjunctive ownership stays shelved pending a ≥3-party lane, per the prior cut | Qualitative where the moat is quantitative; the integer meter dominates every question a lattice could answer; declassify-to-compile laundering is the imported failure class | **DECLINE** (settled 2026-07-02; the moat question strengthens the verdict — a moat's boundary is a *meter*, not a label) |
| 7 | **Dependent types for receipt-indexed APIs** | The receipt-indexed shape ("this settlement is typed by the charge event it releases against") is real — and already achieved by content-addressed ids + relational validation + the S-code audit; the genuinely dependent statements (conservation, monotone escalation) live in Lean where they pay | A dependently-typed data plane is the proof-language rewrite Tier 3 shelved; maintenance cost on every schema change | **DECLINE** for the data plane; the Lean kernel *is* the dependent layer, correctly quarantined |

The ranking's shape is the finding: **the moat needs no new discipline.** The two imports are the two already made. What the moat adds is *demand* — one corollary (M3's residual sentence), one law pair (M1's ancestry retention), one audit family (M4's closure conviction) — all expressible in the machinery the prior cut chose. That is evidence the 2026-07-02 verdict was right, arriving from a direction it wasn't tested against.

---

# PART 2 (minimal primitive proposal + timelessness test)

## 3. The minimal primitive proposal

Run "moat" through the five-test gate:

1. **Boundary** — a moat names a *non*-crossing; the crossings it governs are already named (`EgressDebit`, `WideningEvent`, `ExposureDebit`). Fails as a record.
2. **Lifecycle** — a moat is not created/revoked/released independently; it is coextensive with the chamber's interior. Fails.
3. **Composition** — the composition threat (many safe hops → one leak) is real but is M4's audit, not a record.
4. **Owner** — a `MoatRecord` would add a field an owner must maintain that duplicates the fold. Fails.
5. **Receipt** — the honest external sentence exists, but it is *computed from the fold*, not stored.

**Verdict: "moat" is a PATTERN, not a primitive. Zero new canon records.** The pattern earns a named composition law in CANON.md prose:

> **The moat pattern.** Moat(C) := grow-only interior (M1) × charged-coupled boundary (M2) × lifetime (source × reader) residuals (M3) × provenance-closure charging (M4) × covenant-capped exit (M5). A chamber satisfying the conjunction compounds structurally and cannot leak past budget except through the named non-claims (G2, G3, G13, G15, frontier #5, #7).

Three concrete deltas ship the pattern, none of them a canon primitive:

**(1) One kernel event kind — `derivation` — plus the P-code audit family (G14 closed as law).** The kernel's charge event doesn't name consumed judgements; the closure audit needs the DAG at the ledger layer, not just in canon records. Per KERNEL-SPEC §5.5 discipline (new kinds add a row before first issuance) and X0 (equivocation coverage at genesis, free):

```jsonc
{ "kind": "derivation",
  "derived": "sha256:…",            // content id of the derived fact
  "consumed": ["sha256:…", "…"],    // direct ancestors, by content id
  "hop_capacity_mbits": 12000,      // declared first-hop capacity (DPI bound input)
  "issuer": "chamberA", "seq": 7, "tick": 40 }
```

P-codes, same discipline as I/S/C/X (sorted `"<code> <subject>"`, total over adversarial content, separate verdict surface):
- **P1 — dropped ancestor:** an `EMITTED` charge whose emission names derived fact d, where the derivation closure of d contains source s, with no coupled charge on `["exp", s, reader]` in the same coupling — convicts the coupled set. This is "not separable from its ancestry" made convictable, the exact sentence G14's register row asks for.
- **P2 — closure undercount:** the coupled charge toward s is below the DPI bound (min-cut of `hop_capacity_mbits` along s→d paths) implied by the emission's own declared capacity — the dishonest direction, convicted. Estimation itself stays attested and outside the kernel, as everywhere.
- **P3 — orphaned derivation:** a `derivation` whose `consumed` id resolves to no event and no tombstone — M1's ancestry-retention check at the substrate.

**(2) One canon law pair, no new records.** In `CORE_LAWS`: `retentionOutlivesTheDerivationsItFeeds` (an artifact in any live artifact's provenance closure may be tombstoned, never dropped) and `projectionsChargeTheProvenanceClosure` (the canon-side name of P1/P2, badged [L] until the audit ships, per the enforcement-tier discipline the premier cut mandated).

**(3) One receipt payload schema — not a primitive; a projection of the fold.** In branded-ADT style, for the compiled residue sentence:

```ts
/**
 * Computed from the ledger fold — NEVER stored as authority; a stranger
 * recomputes it. The residual is a budget fact about declared capacity,
 * not a secrecy fact: it inherits G2 (bits are not harm), G3 (reader is a
 * claimed entity), G13 (the entropy denominator depreciates), and
 * frontier #5 (no auxiliary-knowledge model) — the caveat codes are
 * mandatory, not decorative.
 */
export interface MoatResidualStatement {
  readonly sourceChamberId: Id<"Chamber">;
  readonly readerEntityId: Id<"BeneficialEntity">;
  readonly scope: "pair_lifetime";
  readonly ceilingMbits: Bits;
  readonly cumulativeChargedMbits: Bits;   // Σ debits, from the fold
  readonly residualMbits: Bits;            // ceiling − cumulative; ≥ 0 or convicted
  readonly foldHash: Hash;                 // the exact ledger fold this projects
  readonly entropyDeclarationTick: number; // G13: which denominator vintage
  readonly notASecrecyClaim: true;
  readonly caveatCodes: readonly ["bits_not_harm", "reader_identity_claimed",
                                  "denominator_depreciates", ...string[]];
}
```

**What must NOT become a primitive, and why:**

- **`MoatValue` / moat strength as a stored score.** Unauditable discretion wearing a type; the exact "market maker" failure the Ethereum test declined in LMSR. Economic value is estimated-lane, `price_input`, gameability-caveated — `OptionValueEstimate` is the ceiling of what's admissible, and it never gates.
- **A `hasMoat` / `moatIntact` boolean on `Chamber`.** A success-shaped privacy claim, the one thing the working rule bans by name. The moat is a conjunction of audits; booleans launder conjunctions (the stack already caught itself doing this once, with `EscrowedClaim.state: "verified"`).
- **An `Accumulation` operator.** Accumulation is already `Run` + `Artifact` + `LedgerEntry` + provenance; a new operator would rename the spine, and renames are what the alias table exists to bury.
- **Depreciation inside the kernel.** G13's answer is right: temporal physics lives in the key schema and the re-declaration event, floats live in estimators. A kernel that decays is a kernel that re-litigates, and decisions are final.

---

## 4. The timelessness test

Which invariants survive a total rewrite — new language, new hash, new wire format, no TypeScript, no Lean file carried over?

**Timeless (laws of the problem, not the implementation):**

1. **Conservation under partition.** Σ parts ≤ whole when the issuer never over-grants and each node respects its slice — arithmetic, not engineering. Any future moat kernel re-proves it in an afternoon or is wrong.
2. **One-way widening / monotone escalation.** Disclosure is entropy-irreversible; merge of evidence can only escalate. The interior-as-join-semilattice with inflationary ops (M1) is the order-theoretic core and survives any storage substrate.
3. **The coupled-charge law, both directions.** An emission is not separable from its inputs: no partial emission, no phantom debit. This is a statement about *information*, not about `charge_coupled`.
4. **Provenance closure under DPI (M4).** Post-processing cannot create information about a source; therefore charging the closure at first-hop capacity is sound forever, and any accounting that forgets ancestry under-charges *provably*, in every future implementation. The data-processing inequality is the moat's deepest ally: it is the reason internal compounding can be free while the boundary pays honestly.
5. **Charged-before-released, safety-shaped.** No crossing without a prior debit is a safety property over any finite event set; the F4 doctrine (every obligation arrives safety-shaped or carries its deadline reduction) is Alpern–Schneider, older than this stack and outliving it.
6. **Erasure-as-tombstone.** You can destroy bytes; you cannot destroy the fact that committed bytes existed without destroying other people's proofs. Salted-commitment erasure is commitment logic, not a product decision.
7. **Residual arithmetic per (source, reader), lifetime.** `residual = ceiling − crossed`, monotone down, keyed to the pair because information is never unlearned — a bookkeeping identity plus one epistemic fact.
8. **The estimator/kernel separation.** *That* judgment is quarantined at a named, attested boundary is timeless architecture; *what* the estimator contains is 2026.
9. **Two timeless negatives.** Economic compounding never becomes a theorem — the moat's worth is a market fact in every possible implementation. And bits-are-not-harm survives as a conjunction: F1's g-leakage may someday give the ordinal half a calculus, but the human conjunct it formalizes does not dissolve.

**2026 engineering (correct today, replaceable without touching the theorems):** integer millibits as the granularity; sha256 content addressing and the canonical-JSON/JSONL wire; lease `tick` clock domains and the specific I/S/C/X/P code alphabets; TypeScript brands as the enforcement of nominal typing; TEE custody of escrowed latents; the attested-estimator tables; Sybil softness of `BeneficialEntity` (contingent on identity technology, frontier #1); G13's depreciation schedules; the kLOC validator itself.

**The clean summary:** the moat is the pattern the stack was already building, minus one law. Four of the five invariants are carried or proven; the fifth — provenance-closure charging, G14 — is the one place where "generative" currently outruns "metered," because the compounding move and the laundering move are the same move until the closure audit exists. Ship the `derivation` event and the P-codes, add the two retention/closure laws, compile the residual sentence from the fold, and "the moat compounds and never leaks past its budget" stops being an aspiration and becomes what conservation and one-way widening already are: a property a stranger convicts from bytes.
