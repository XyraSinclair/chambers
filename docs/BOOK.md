# The Book — Scry Chambers, the minimal statement

A chamber economy is the theory of one doubly-graded computation: graded once by whose private worlds it has touched, and once by what has been made expressible to whom. Around that computation runs a market whose only tradable good is a bounded computation right, whose only deliverable is one symbol from a closed alphabet, whose price system is a lifetime exposure ledger, and whose settlement instrument is a court file. Nobody buys bits; people buy scoped rights and legible evidence. Every law in canon is an axiom of this algebra, a one-line corollary of the axioms, or a refusal the algebra records rather than resolves.

Standing rule: `primitives/` decides; this document argues. Where they disagree, canon wins on fields and this Book owes an erratum. Nothing here is a success-shaped privacy claim; the refusal register is load-bearing.

## Objects

- **O1 Party** — a beneficial entity; identifiers are aliases, never the unit of governance; a silo is a finite set of parties.
- **O2 Chamber** — the computation confined to the joint silo of every private world it has touched; the provenance-graded monad with no eliminator; no exit but release.
- **O3 Alphabet** — the closed finite set of everything a counterparty can ever distinguish from a crossing, failure modes included; capacity is log2 of its size — derived, never declared. (Canonical name: alphabet; codebook and schema are aliases for the same object.)
- **O4 Context** — audience × purpose × alphabet under componentwise widening; the disclosure state of every derivative. The alphabet is the object; the bit number is its logarithm.
- **O5 Right** — the traded good: one grant of (algorithm, scope, purpose, alphabet, audience, review, recourse), priced, revoked, and audited as a unit.
- **O6 Account** — the lifetime (source × reader) cell of the (Bits, +, 0) writer with a hard ceiling; attention budgets are accounts of the same shape, debited in interruptions rather than bits; bits are the anti-laundering clause, not the guarantee.
- **O7 Court file** — the append-only evidence of grants, crossings, charges, refusals, and settlements, from which every outward claim compiles.

## Axioms

- **A1 GRANT** — Authority moves only by an explicit ledgered grant of the least capacity its signed purpose justifies; content, requests, and payments never carry it.
- **A2 JOIN** — Provenance only joins: composition unions silo grades, and nothing shrinks one.
- **A3 ALPHABET** — Everything a non-owner can distinguish — verdict, rejection, error, withhold, absence, timing, payment, silence — is a member of an alphabet closed before the run, or the protocol is defective.
- **A4 PUBLICITY** — An operation is free exactly when it is computable from public values alone.
- **A5 CHARGE** — A crossing is charged the capacity of its full outcome alphabet at the adversarial maximum: derived where the alphabet closes, a labeled estimate where it does not.
- **A6 METER** — Every observer is a reader; every reading debits its lifetime (source × reader) account; a crossing that would pass the ceiling is blocked before it happens.
- **A7 CONSENT** — A release exists only under unforgeable signatures from every party in its provenance grade, over the exact alphabet and program, given before data enters.
- **A8 WIDENING** — A context only widens, only through a consented priced release, and never narrows back: revocation caps the future, and no disclosure rewinds.
- **A9 LANES** — Every claim carries its lane — proven, trusted on a named root that degrades loudly, estimated, or unprovable — and estimates price, never gate.
- **A10 EVIDENCE** — Every outward claim compiles from the court file and names its non-claims; what cannot compile cannot be said.
- **A11 ROLES** — No beneficial entity adjudicates a crossing it stands to gain from; roles separate over beneficial owners, never identifiers.
- **A12 OWNER** — Content crosses only on an affirmative human owner decision; owners see priced cards rather than payloads; exhaustion fails closed for disclosure.

Settlement is not a thirteenth axiom: an outward payment is a symbol crossing (A3) that widens context (A8); authority never rides it (A1); and value moves exactly when metered work moved, because settlement releases against charge events in the court file (A10+A6). Pool separation — derived and declared charges never mix in one number — is A5+A9: pooling an estimate with a theorem launders the label.

## Theorems

- **T1 CLEARING (cut bound)** — from A2+A3+A4+A5+A6: leakage to any observer coalition is at most the sum of charges on the crossings that reach it, under any behavior inside the chamber — provided every observable is enumerated and every schedule is fixed or public-computable. Status: a specification enforced by kernel and review; its soundness proof is R14.
- **T2 FREE POST-PROCESSING** — from A4: released symbols are public values, so any function of them is computable from public values alone and charges nothing.

## Attack verdicts

| Attack class | Verdict |
|---|---|
| Laundering — many small releases pooling into one leak | PRICED by A6; plumbing variants PREVENTED by A2 |
| Accumulation / distillation campaigns | PRICED by A6 (lifetime accounts); residue NAMED R1 |
| Side channels — errors, aborts, absence, gradients, notifications | PREVENTED by A3+A5: enumerated and charged, or made unobservable |
| Sybil fragmentation | NAMED R1; made visible, not stopped, by A11+A6 |
| Verification-as-extraction | PRICED by A6; NAMED R10 |
| Timing / topology | PREVENTED-or-priced by A3+A4: schedules fixed or public-computable; metadata residue NAMED R12 |
| Success-shaped claims | PREVENTED by A9+A10: unsupported claims cannot compile; no boolean verified where a partition belongs |
| Consent laundering — release on partial signatures | PREVENTED by A7 |
| Authority injection — prompt, bounty, payment | PREVENTED by A1 |
| Role collusion / self-dealing | PREVENTED by A11, degrading to R1 where identity fails |
| Insider / operator plaintext | NAMED R4; who-saw is always stated, by A10 |
| Reconstruction probing — reserves, estimation channel | PRICED by A5+A6 |

## Refusal register

- **R1 IDENTITY** — uniqueness is unsolved; every per-entity key is Sybil-soft, the undercount visible, not prevented; thin pools inherit this.
- **R2 PRIORS** — reader models are declared, never observed; the unconditional ceiling is the backstop, not knowledge of the adversary's head.
- **R3 HARM** — the meter prices channel width, never damage; one bit can be a life.
- **R4 TRUSTED CORE** — operator, steward, sampler, verifiers, reviewers, hardware roots: trusted and ledgered, not eliminated; the doubly-sealed verifier sees both secrets, and the substrate sees everything it mediates.
- **R5 THE HUMAN HEAD** — what a reviewer learns lives in memory no type contains; minimized, never closed.
- **R6 WORKER EXCHANGE** — an owner can read delivered work and then reject it; the market is not yet incentive-compatible for the worker.
- **R7 AVAILABILITY** — fail-closed is a griefing amplifier; there is no anti-denial model.
- **R8 THE INTERIOR** — one owner principal per chamber and an unenforced purpose string; quorums and purpose enforcement are unbuilt.
- **R9 ENFORCEMENT** — court files are evidence, not contracts; breach, jurisdiction, liability, and forfeiture live outside the types.
- **R10 METHODS** — only results verify at model scale (2026); the channel that verifies also extracts; honest verification cost can approach the trade's own value, unfunded; estimator calibration does not reach the crown-jewel regime.
- **R11 INFERENTIAL TARGETS** — a joint derivative informs on parties who contributed nothing; screens cover named subjects only, and unenumerated targets remain.
- **R12 METADATA** — existence, cardinality, cadence, and direction-of-dependence leak through shape; batching defenses are unbuilt; a thin anonymity set hides nothing.
- **R13 DECLARED CHANNELS** — where no alphabet closes, the meter bounds the ledger, not the adversary; the seatbelt, not the car.
- **R14 SOUNDNESS** — the types-to-QIF theorem is a named open goal; the credit/exposure duality is a recorded conjecture (`false` in canon), never assumed.

Register note, stated once: canon spells three law keys, one admission-gate test name, and one preserved phrase with a word this document does not use; "evidence" and "court file" stand in for it throughout, quoted keys included.

---

## Appendix — coverage map

Every law key in canon, mapped. Verdicts: `AXIOM An` (instance of axiom n), `COR n(+m)` (corollary, with its derivation), `NAMED Rk` (the law records a refusal). Denominator, verified by direct extraction from `primitives/*.ts` on 2026-07-23: **146 keys across 14 `*_LAWS` consts** (the earlier 147 figure was an overcount — `IPTRADE_LAWS` has 31 keys, not 32). Plus CALCULUS.md L1–L8 (L-numbers inline; L4 has no key and gets its own row) and CANON.md's five-test admission gate. Zero drops; zero exclusions.

**CORE_LAWS (core.ts, 12)**

- no grant, no run → AXIOM A1
- requester input is untrusted → COR A1 — content never carries authority; only ledgered grants do
- ingress is typed via Transform → COR A1+A3 — entry is itself a granted crossing with a declared, enumerated shape
- no boundary crossing without a ledger entry → COR A6+A10 — every crossing debits an account, and an unrecorded crossing could back no claim
- release fields are a reviewed subset of the sink → COR A7+A3 — consent binds an exact alphabet; nothing outside it can cross
- outward timestamps are emissions → AXIOM A3 — timing is an enumerated member
- evidence artifacts name non-claims → AXIOM A10
- content disclosure requires a human owner decision → AXIOM A12
- role separation is checked over beneficial entities → AXIOM A11
- declassification selectors must be high-integrity → COR A1+A7 — a low-integrity selector lets content re-scope a signed release: authority arriving as data under a stale signature
- subject erasure is a salted tombstone, not a chain break → COR A10 — claims compile from an append-only record; erasure is a new record, and the evidence chain survives
- retention outlives the claims it backs → COR A10 — a claim whose backing facts expired becomes uncompilable, hence unsayable

**ENTROPY_LAWS (entropy.ts, 11)**

- every non-owner observable has a policy → AXIOM A3 — an unpoliced observable is outside every closed alphabet: a defect
- exact operational signals are owner-private → COR A3 — exact values are data-dependent surfaces; only bucketed alphabet members cross
- repeated queries compose → AXIOM A6 — debits add for life
- denominator leakage blocks release → COR A3+A5 — candidate-set size is an outcome symbol; un-enumerated, the release blocks
- no perfect-privacy claim → COR A9+A10 — perfection sits in no lane and cannot compile
- budgets are tripwires, not certificates → COR A10 + NAMED R3, R13 — the meter binds the ledger, never harm, and on declared channels never the adversary
- absence is an emission → AXIOM A3
- capacity is charged at the adversarial maximum → AXIOM A5
- release gate is the conjunction of numeric accountant and ordinal gate → COR A6+A12 — the meter blocks and the owner review blocks; two independently necessary doors
- every estimate names its estimator → COR A9+A10 — a lane-carrying claim without a named source is an unnamed trust root and cannot compile
- numeric accountant binds structured channels, not prose → COR A5+A9 + NAMED R13 — where no alphabet closes, the charge is a labeled estimate binding the ledger only

**ENVIRONMENT_LAWS (environment.ts, 5)**

- no grant, no environment → AXIOM A1
- no raw network egress by default → COR A8 — the chamber's only exit is release; an ungranted channel does not exist
- paths are virtualized before worker access → COR A3 — real paths are un-enumerated operational surfaces; virtualization replaces them with enumerated ones
- logs are owner-private unless released → COR A8 — logs are born in the silo's context and confined until a release widens it
- evidence artifacts describe observed configuration, not perfect isolation → COR A9+A10 — isolation is a trusted-lane claim on a named root, never proven by assertion

**RUNTIME_LAWS (runtime.ts, 5)**

- claims compile from recorded facts only → AXIOM A10
- unsupported claims are unrepresentable → COR A10 — the compile is total from evidence; no slot exists for the unbacked
- containers do not prove privacy → COR A9 + NAMED R4 — container isolation is trusted on a named root inside the trusted core
- TEE quotes are always caveated → COR A9+A10 — attestation is the trusted lane: a named root that degrades loudly
- requester sees model class only → COR A3 — exact model identity is outside the requester's alphabet; the class is the enumerated member

**ATTENTION_LAWS (attention.ts, 6)**

- agents write findings, not pages → COR A3 + NAMED R5 — unbounded prose at the owner is an unmetered channel into the reviewer's head
- attention may carry a reserve, and cards clear it before surfacing → COR A6 — block before the crossing, in attention as in bits
- owners see review cards, not raw payloads, by default → AXIOM A12
- every interruption debits the ledger → COR A6 — the owner is a reader; attention is a reader account
- attention exhaustion fails closed for disclosure → AXIOM A12
- notification text is itself egress → AXIOM A3

**MARKET_LAWS (market.ts, 14)**

- bounties buy accepted annotations, not access → COR A1 — payment buys a deliverable, never a grant
- external payment is a release → COR A3+A8 — an outward payment is a symbol crossing that widens context: charged and consented like any release
- free text does not earn by default → COR A5+A10 — an open alphabet has no derivable charge, so settlement has nothing typed to release against
- evaluator must be role-separated → AXIOM A11
- reuse credit uses declared edges, not raw replays → COR A10+A2 — credit compiles from recorded provenance edges; replay surveillance is an unconsented channel
- subscriptions expose projected annotations only → COR A3+A8 — a subscription is a standing audience; only closed-alphabet projections cross to it, and the standing grant widens nothing further
- bounties never widen authority → AXIOM A1
- hidden reuse is slashable → COR A10+A9 — an undeclared edge later evidenced contradicts the file, and the consequence lands on a stated root
- payment settles on owner-internal acceptance → COR A12+A10 + NAMED R6 — settlement is the owner's decision compiled from the file, not itself a disclosure; the worker-side residue is a refusal
- oracle verdicts price only against pinned rubrics → COR A3+A7 — the rubric is the alphabet consent covered; a drifting rubric is an unconsented channel
- an oracle upgrade is a new oracle → COR A3 — a new alphabet is a new channel: new consent, new account
- role separation is checked over beneficial entities, not ids → AXIOM A11
- standing authorizations move payouts, never content → AXIOM A1
- attribution shares conserve the pot → COR A10 — splits compile from recorded acceptance facts and a minted share has no backing fact; exact conservation is a kernel theorem (Lean), consistent with A10, not generated by it

**MATCHING_LAWS (matching.ts, 6)**

- no live near-miss lists → COR A2+A7 — a near-miss is a joint derivative whose grade includes both parties; surfacing it without both signatures is release without consent
- priced introductions clear before they surface → COR A6 — debit before the crossing
- denials are invisible to counterparties → COR A3 — a distinguishable denial would be an alphabet member and charged; the design removes it from the counterparty's distinguishable set instead
- relations stay owner-private until all consent clears → AXIOM A7 — the relation's grade is the pair's join; release needs every signature
- denominator leakage blocks match release → COR A3+A5 — same derivation as the entropy denominator law
- scores and rationales release only as buckets or mediated text → COR A3+A5 — only closed-alphabet projections carry a derivable charge; the rest is a labeled declared channel

**PRICING_LAWS (pricing.ts, 9)**

- curves never cross boundaries, only commitments do → COR A3+A2 — a full curve is silo content; only committed points are alphabet members
- samples are ledgered and auditable against commitments → COR A10
- failed crosses reveal one bit and still debit composition → COR A3+A6 — failure is an enumerated outcome symbol; its charge composes for life
- attention clears above reserve before any card surfaces → COR A6 — the debit lands before the interruption happens
- owners may sell attention without buying an explanation → COR A1+A12 — attending grants nothing beyond the least capacity granted; explanations are separate goods behind their own grant
- schedules bind before work starts, not after → COR A7+A3 — everything the protocol can pay or say is signed before data enters; a post-hoc schedule is an un-enumerated timing surface
- probing reserves is a reconstruction attack → COR A6 — repeated one-bit probes compose on the lifetime account
- sampler coin is jointly committed before the draw → COR A4+A11 — joint commitment makes the draw public-computable, leaving no party discretion over an outcome it could gain from
- sampler may not be a party → AXIOM A11

**NEGOTIATION_LAWS (negotiation.ts, 7)**

- neither party owns the lane → COR A2+A11 — the lane's grade is the join; sole authority over a joint object is adjudicating one's own gain
- each boundary is gated by its own review stack → COR A7+A12 — one sovereign, one consent, one owner review per boundary; neither delegates
- claims commit before they reveal → COR A5+A7 — the commitment fixes the alphabet the later reveal is charged against, under the pre-data signature
- verification precedes valuation → COR A9 — price only after the lane is known; estimates price, never gate
- stages open on reciprocity, not trust → COR A8+A6 — each stage is a separately priced widening with symmetric debits
- freeze stops the future, not the past → AXIOM A8 — revocation caps the future; no disclosure rewinds
- walk-away timing is itself an emission → AXIOM A3

**COALITION_LAWS (coalition.ts, 12)**

- leakage is reader-relative, never a scalar → COR A6 + NAMED R2 — accounts key by reader, so no readerless number exists; priors are declared
- reader models are declared, not observed → NAMED R2 — backstopped by COR A5: low confidence charges the unconditional ceiling
- the coalition is the zero point, not a fortress → COR A2+A6 — formation joins grades and members are readers of each other; charging begins at the silo boundary
- synergy is cross-exposure → COR A2+A5+A7 — a joint derivative is mutual exposure, charged at the adversarial maximum and consented at formation
- exposure accounts are keyed (source × reader), lifetime → AXIOM A6
- per-reader accounting presupposes identity → NAMED R1
- widening is a priced one-way event → AXIOM A8
- option value is a price input, never a cliff → COR A9 — estimates price, never gate
- affected exceeds contributing → NAMED R11 — screens carry an honest unprovable lane via A9
- gradients are egress → COR A3+A8 — a trained model is an emission surface to its whole audience; training on silo content is a widening
- coalition metadata is an emission → AXIOM A3
- credit and exposure share one measure (recorded `false`) → NAMED R14 — a recorded conjecture A10 forbids asserting

**MEDIATION_LAWS (mediation.ts, 12)**

- structure judgements are tuple-scoped → COR A2 — the provenance grade is the judgement's identity
- tuple-scope changes are widenings → AXIOM A8
- judgements are derivatives first → COR A2+A6 — capacity caps and exposure debits inherit from the grade
- non-relation is a judgement → COR A3 — absence is a symbol with the same confinement as presence
- reading is an exposure event → AXIOM A6 — reading debits the other members' accounts, and owners see the price first
- review compares requested to justified capacity → AXIOM A1 — least capacity the signed purpose justifies; excess denied by default
- canonicality is least authority → COR A1 + NAMED R4 — the narrowest right that serves the purpose, judged by a reviewer who is trusted core
- the requester is a reader, not a privileged sink → AXIOM A6
- estimated objectives never gate disclosure → AXIOM A9
- payments are emissions → AXIOM A3
- pool claims state the set achieved, never hoped → COR A10 + NAMED R1 — the achieved set is a recorded fact, the hoped mechanism is not, and a thin set inherits the identity refusal
- pools never move content or authority → COR A1 — pools move payouts on standing authorization only

**IPTRADE_LAWS (iptrade.ts, 31)**

- no boolean verified, only a partition → AXIOM A9
- method claims are unprovable at model scale in 2026 → NAMED R10 — A9 gives the refusal its lane
- trust roots are named and degrade loudly → AXIOM A9 — the trusted lane's definition
- research-horizon plans may not gate live settlement → COR A9 — hopes are estimates, and estimates never gate
- verification precedes valuation → COR A9 — price only after the lane is known
- delivered binding must equal verified binding → COR A10 — the settlement claim compiles from the same ledgered commitment the verification did; substitution breaks the compile
- on-chain atomicity is for small artifacts only → COR A10+A9 — an atomicity claim beyond what the root honestly binds is unsayable
- settlement consortium members are disjoint beneficial entities → AXIOM A11
- pure-recipe reuse pins to unprovable → COR A9 + NAMED R10
- reuse is a contestable exhibit, not a boolean → COR A9+A10 — reuse evidence is graded, and only its proven or trusted parts bear weight
- royalty is consent-first, not surveillance → COR A7+A1 — payout rides a pre-signed standing authorization; enforcement may not widen observation
- slashability requires a stated consequence root → COR A9+A10 — a consequence without a named root is an unbacked claim
- valuation is a tagged union, not a scalar → COR A9 — the lane structure extends to value
- priceless is excluded from monetary clearing → COR A9 — no forced conversion between tags
- infinite weight is recorded, never the default → COR A9+A3 — an infinite valuation is a claim needing a lane, and declaring it is itself a position-revealing symbol
- valuation tag is cheap talk until backed by a bond or barter → COR A9+A10 — unbacked claims are named as unbacked
- refusal is a first-class output and itself a signal → AXIOM A3 — the withhold is an enumerated member
- estimated is a fourth lane that never promotes → AXIOM A9
- estimates are price inputs, never payoff cliffs → AXIOM A9
- corpus snapshot is VRF-pinned before negotiation → COR A4+A11 — pinning makes the estimation base public-computable; snapshot shopping is discretion over one's own gain
- estimation channel is metered (closest prior art is a scoop map) → AXIOM A6 — the estimator is a reader, and its readings debit
- sparse prior art means unknown, not novel → COR A10+A9 — absence of evidence compiles to nothing; novelty is a claim needing backing
- calibration does not cover the crown-jewel regime → COR A9+A10 + NAMED R10 — an estimate outside its calibration support must compile with that non-claim; the regime gap itself is method-verification residue
- verification channel may leak via model extraction → NAMED R10 — priced by A6
- the doubly-sealed verifier sees both secrets → NAMED R4
- cryptographic evidence artifacts are not self-enforcing contracts → NAMED R9
- reputational root is wrong for one-shot crown-jewel trades → COR A9 — the named root must bear the claim's weight, and reputation cannot for one-shot stakes
- everything here is bilateral; barter rings unbuilt → COR A10 — a scope non-claim the file must name
- attribution is not yet an escrowable currency → COR A10 — same
- the research substrate is not neutral; it sees everything → NAMED R4
- cost incidence of verification and estimation is unfunded → NAMED R10

**CALCULUS_LAWS (calculus.ts, 10 keys; CALCULUS.md L1–L8 inline)**

- provenance joins (L1) → AXIOM A2
- block before ceiling (L2, L8) → AXIOM A6
- derived, not declared → AXIOM A5 — pool separation of derived and declared charges is COR A5+A9: pooling an estimate with a theorem launders the label
- closed alphabet (L6) → AXIOM A3
- post-processing free (L3) → THEOREM T2, from A4
- gates are public-only or charged (L5) → COR A4+A5 — free exactly when public-computable; a gate that reads silo content is a release at Bool and pays its outcome alphabet
- refusals simulatable or charged → COR A4+A3 — uncharged only while the blockage is computable from the public transcript; otherwise the withhold is a symbol and pays
- consent covers provenance (L7) → AXIOM A7
- aborts and reviews are releases → COR A3+A6 — data-dependent withholds are symbols, and influence views are readings that debit the other parties
- leakage is a cut bound → THEOREM T1, from A2+A3+A4+A5+A6; soundness NAMED R14
- CALCULUS.md L4, monotone widening (no `*_LAWS` key) → AXIOM A8

**STRUCTURE_LAWS (contexts.ts, 6)**

- context is the primary grade → OBJECT O4 — definitional
- confined unless widened → AXIOM A8
- incomparable is widening → COR A8 — a cumulative order has no lateral moves; any transition that is not a narrowing is a widening and pays
- no purpose lattice yet → COR A8 + NAMED R8 — purposes compare by signed-hash equality only, so any purpose change is a widening; the missing refinement lattice is interior residue
- bits are the homomorphic shadow → COR of O3+O6 — capacity is the monotone additive image of the alphabet leg, kept as the composition budget and nothing more
- harm is not denominated in bits → NAMED R3

**Admission gate (CANON.md, 5 tests)**

- Boundary: names a crossing → COR A3 — an unnamed crossing is an unmetered channel; primitives exist to enumerate
- Lifecycle: independently creatable, revocable, auditable → COR A1+A10 — whatever is granted must be revocable and re-auditable from the court file on its own
- Composition: small events cannot pool into one leak → COR A6 — a primitive must not launder past the lifetime account
- Owner: reduces burden or sharpens agency → COR A12 — the owner is the disclosure gate and must not be worn down into one
- Evidence: an honest external sentence with explicit caveats → AXIOM A10

**Frontier map (CANON.md's 19 open-frontier items → the register)**: 1, 17, 19 → R1; 5, 18 → R2; 4 → R3; 6, 13 → R4; 7 → R5; 2 → R6; 3 → R7; 8, 9 → R8; 10, 15 → R9; 11, 12, 14 → R10; 16 → R11; metadata/topology non-claims (G15) → R12; the calculus and structure declared-channel non-claims → R13; the open soundness theorem and the recorded duality conjecture → R14.

Accounting: 146 law keys + the keyless L4 row + 5 gate tests = 152 rows, all mapped; 0 excluded, 0 dropped. Primary verdicts: 46 AXIOM, 92 COR, 2 THEOREM, 11 NAMED, 1 OBJECT (definitional); 23 rows in total carry a NAMED Rk, since several carry both a derivation and a refusal.

## Derivation notes

- Merged the candidates' separate Emission axiom into ALPHABET (A3) and replaced its "unless public" escape clause with the Publicity biconditional (A4), so free-vs-charged is one iff rather than an exception.
- Split the candidates' Money/Settlement axiom into derived instances — payment-as-symbol (A3+A8), authority-never-rides-payment (A1), value-moves-iff-metered-work-moved (A10+A6) — and re-derived every money law with nothing lost; 13 → 12 axioms held.
- Kept the four-lane partition where the algebraic candidate's three lanes silently dropped `estimated`; split trusted-core (R4) from the human head (R5) because institutional trust and irreducible memory fail differently; corrected the coverage denominator from 147 to 146 by direct extraction.
