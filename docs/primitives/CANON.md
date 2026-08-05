# Canon

This directory is the single canonical type surface for Scry Chambers. When any
prose document — the research memo, the ideation series, an autoresearch cut —
disagrees with these modules, these modules win. Prose documents argue; this
directory decides.

## Module map

Each module earns its place by answering a question the previous layer cannot.

| Module | Question it answers | Spine or rib |
|---|---|---|
| `core.ts` | Who had authority, what ran, what was reviewed, released, remembered? | Spine |
| `entropy.ts` | What became observable, to whom, at what capacity, composing how? | Rib |
| `environment.ts` | What was the worker allowed to touch and how was it isolated? | Rib |
| `runtime.ts` | What may the runtime *claim*, compiled from which recorded facts? | Rib |
| `attention.ts` | Whose attention was spent, on what, against which budget? | Rib |
| `market.ts` | What work was accepted, reused, credited, settled? | Rib |
| `matching.ts` | When may a relation between private worlds exist, and for whom? | Rib |
| `pricing.ts` | At what price does a crossing clear, revealing how little? | Rib |
| `negotiation.ts` | How do two sovereign chambers disclose to each other in stages? | Rib |
| `iptrade.ts` | How do labs/researchers trade IP: verify results, exchange atomically, license royalties — honestly? | Rib |
| `coalition.ts` | For whom does a joint derivative carry information, and how much has each reader accumulated about each source — across everything? | Rib |
| `mediation.ts` | How does a typed judgement live on an exact k-tuple of silos; who checked the agent was minimal; how does money settle without becoming the leak? | Rib |
| `calculus.ts` | Under what composition laws does all of the above stay leakage-bounded — and which charges are theorems (derived) vs estimates (declared)? | Spine |
| `contexts.ts` | What is the disclosure state of a derivative — audience × purpose × alphabet — and when, at what price, does it widen? | Spine |

Dependency direction is one-way: ribs import from `core.ts` (and `entropy.ts`
for leakage estimates). `core.ts` imports nothing.

## Alias table

Renames that appeared in prose documents. Left column is canon.

| Canon (here) | Seen elsewhere | Where |
|---|---|---|
| `LedgerEntry` | `Ledger` | beautiful-type-systems README §1 |
| `Visibility` (data at rest) + `ObserverClass` (emission observers) | `Audience` | beautiful-type-systems README |
| `Annotation` (alias `CognitiveDelta`) | `CognitiveDelta` | beautiful-type-systems README §5 |
| `EnvRecipe` | `WorkerRecipe` | beautiful-type-systems README §3 |
| `CreditMicros` | `MoneyMicros` | research memo |
| `ObservableEvent` / `ObservableKind` | `Emission` / `EmissionKind` | beautiful-type-systems README §2 |
| `Transform` | `Request` (dropped entirely in one cut) | beautiful-type-systems README §1 |
| `Gate` (8 states, incl. `static_scan`) | 7-state variant | beautiful-type-systems README |
| `CapacityEstimate` | bare `capacityBits: number` | beautiful-type-systems README §1 |
| `EnvironmentReceiptPayload` + `RunClaim` | `environment_receipt.json` prose | wedge sketches |

## Laws index

Every module exports a `*_LAWS` const. These are the invariants an
implementation must enforce and a reviewer may cite by key.

- `CORE_LAWS` — no grant no run; requester input untrusted; ingress typed via
  `Transform`; no crossing without a `LedgerEntry`; release fields are a
  reviewed subset of the sink; outward timestamps are emissions; receipts name
  non-claims; **content disclosure requires a human owner decision** (payouts
  are separate); **role separation is checked over `BeneficialEntity`, not ids**;
  **declassification selectors must be high-integrity**; **subject erasure is a
  salted tombstone, not a chain break**; **retention outlives the claims it backs**.
- `ENTROPY_LAWS` — every non-owner observable has a policy; exact operational
  signals are owner-private; repeated queries compose; denominator leakage
  blocks release; no perfect-privacy claim; budgets are tripwires, not
  certificates; absence is an emission; **capacity is charged at the adversarial
  maximum** (enum × ordering × presence, not honest-case); **the release gate is
  the conjunction of a numeric accountant and the ordinal gate**; **every
  estimate names its estimator**; **the numeric accountant binds structured
  channels, not prose**.
- `ENVIRONMENT_LAWS` — no grant no environment; no raw egress by default;
  paths virtualized; logs owner-private unless released; receipts describe
  observed configuration, not perfect isolation.
- `RUNTIME_LAWS` — claims compile from recorded facts only; unsupported claims
  are unrepresentable; containers do not prove privacy; TEE quotes are always
  caveated; requester sees model class only.
- `ATTENTION_LAWS` — agents write findings, not pages; owners see review
  cards, not raw payloads; every interruption debits the ledger; exhaustion
  fails closed for disclosure; notification text is itself egress.
- `MARKET_LAWS` — bounties buy accepted annotations, not access, and never
  widen authority; external payment is a release; free text does not earn;
  evaluators are role-separated; reuse credit uses declared edges; hidden
  reuse is slashable; payment settles on owner-internal acceptance; **role
  separation is checked over beneficial entities, not ids**; **standing
  authorizations move payouts, never content**.
- `MATCHING_LAWS` — no live near-miss lists; priced introductions clear
  before they surface; denials are invisible to counterparties; relations
  stay owner-private until all consent clears; denominator leakage blocks
  match release; scores and rationales release only as buckets or mediated
  text.
- `PRICING_LAWS` — curves never cross boundaries, only commitments do;
  samples are ledgered and auditable against commitments; failed crosses
  reveal one bit and still debit composition; attention clears above reserve
  before any card surfaces; owners may sell attention without buying an
  explanation; schedules bind before work starts; probing reserves is a
  reconstruction attack; **the sampler coin is jointly committed before the
  draw**; **the sampler may not be a party**.
- `NEGOTIATION_LAWS` — neither party owns the lane; each boundary is gated
  by its own review stack; claims commit before they reveal; verification
  precedes valuation; stages open on reciprocity, not trust; freeze stops
  the future, not the past; walk-away timing is itself an emission.
- `COALITION_LAWS` — **leakage is reader-relative** (no scalar; every estimate
  names its reader model); reader models are declared, not observed — low
  confidence charges the unconditional ceiling; **the coalition is the zero
  point of the leakage metric, not a fortress**; synergy IS cross-exposure,
  charged at the adversarial maximum and consented at formation; **exposure
  accounts are keyed (source chamber × reader entity), lifetime, across all
  coalitions** — the one key the cross-coalition accumulation attack cannot
  slip past; per-reader accounting presupposes identity (frontier #1, named);
  widening is a priced one-way event; option value is a price input, never a
  cliff; affected exceeds contributing (inferential-target screens, honest
  `unprovable`); **gradients are egress**; coalition metadata (formation,
  membership, silence) is an emission. Deliberate non-law, recorded `false`:
  `creditAndExposureShareOneMeasure` (the payment/exposure duality is a
  conjecture with a mandatory caveat, not an invariant).
- `MEDIATION_LAWS` — **structure judgements are tuple-scoped** (the exact
  k-tuple is the judgement's identity; sub/superset visibility is a
  WideningEvent); judgements are CoalitionalDerivatives first (capacity caps
  and exposure debits inherit); **non-relation is a judgement** (absence gets
  the same confinement); **reading is an exposure event** (debits the other
  members; owners see the price first); admission review compares requested
  to justified capacity — excess denied by default; canonicality is
  least-authority; **the requester is a reader, not a privileged sink**;
  estimated objectives size payments, never gate disclosures; **payments are
  emissions** — entropy pools are the obfuscation plan for money, claims
  state the anonymity set achieved (never the mechanism hoped), pools move
  payments on standing authorization and never content or authority.
- `IPTRADE_LAWS` — **no boolean `verified`, only a proven/trusted/unprovable
  partition**; method claims are unprovable at model scale in 2026 (only
  results verify); trust roots are named and degrade loudly; research-horizon
  plans (ZK/MPC/FHE) may not gate a live settlement; delivered binding must
  equal verified binding; on-chain atomicity is for small artifacts only;
  pure-recipe reuse pins to unprovable; reuse is a contestable exhibit, not a
  boolean; royalty is consent-first, not surveillance; slashability requires a
  stated consequence root. Standing non-claims: the verification channel may
  leak via model extraction; the doubly-sealed verifier sees both secrets;
  cryptographic receipts are not self-enforcing contracts; `reputational_only`
  is wrong for one-shot crown-jewel trades.
- `CALCULUS_LAWS` — **provenance joins, never shrinks**; leakage charges
  compose additively against a hard pre-charge cap (**block before the
  ceiling**); **charges on codebook channels are derived** (log2 of a closed
  alphabet), never declared, and derived/declared pools stay separate in any
  cut-bound report; **every observable outcome is a codebook member**
  (rejections and errors included — an un-enumerated outcome is a defect);
  post-processing is free (DPI); **gates are public-only or charged** —
  a decision that consults silo content is a release at Bool; refusals may
  cross uncharged only while blockage is computable from the public charge
  transcript; **consent covers the full provenance grade**; **aborts and
  reviews are releases** (data-dependent withholds are `Withheld` symbols;
  influence views are charged against the other parties' exposure; consent
  is program-level, signed once before data enters); total leakage to
  any observer coalition is a cut bound — with event count, ordering, and
  timing named as surfaces that are free only where fixed or public-computable.
  Status: these laws are a SPEC enforced by kernel + review; the types-to-QIF
  soundness theorem is the named open goal (mediation-literature.md, vein 3).
  Runnable shadow: `chambers/ip_trade_sim/test_calculus_bound.py`.

## Admission test for new primitives

A candidate record enters this directory only if it passes all five:

1. **Boundary** — names a crossing that otherwise becomes folklore.
2. **Lifecycle** — can be created, revoked, reviewed, released, paid,
   retained, or audited independently.
3. **Composition** — prevents many tiny safe-looking events from becoming one
   big leak.
4. **Owner** — reduces owner burden or sharpens owner agency.
5. **Receipt** — can produce an honest external sentence with explicit caveats.

Fails one? It is a field, payload schema, artifact body, UI projection, or
future module. Not a primitive.

## Open frontier — what types do NOT solve

An exhaustive adversarial pass (207 agents; see
`private: autoresearch/2026-07-01-substrate-stress-test/`) established that the
following are load-bearing dependencies the type system must not pretend to
have solved. New records here may *name* these problems and record verdicts
honestly (e.g. `ConflictVerdict = "unprovable"`), but must never assert them
away with a boolean.

1. **Identity / proof-of-uniqueness.** Every Sybil, collusion, and composition
   defense presupposes principal uniqueness. `BeneficialEntity` relocates the
   problem ("are two entities secretly one?") to identity governance; it does
   not decide it. Sovereign parties (labs) share no identity root at all.
2. **Worker-side fair exchange.** An owner can read an annotation payload then
   `reject` — the market is not yet incentive-compatible for the worker. Needs
   commit-before-read / escrowed reveal.
3. **Availability.** The substrate is CIA-minus-A. `fail-closed` is a griefing
   amplifier (flood attention → deny release and payment). No anti-grief model.
4. **Harm is not linear in bits.** The bit accountant is decoupled from
   `Scope.sensitivity`; one catastrophic attribute is one bit and a life.
5. **No auxiliary-knowledge model.** Budgets are absolute bits, not bits
   relative to the observer's prior — the real Dwork/Roth lesson, uncredited.
   *Narrowed, not closed, by `coalition.ts`* (`ReaderModel` +
   `ReaderRelativeLeakage` charge conditionally on a declared prior); the
   honest residue stands: reader models are declared, not observed — a
   low-confidence model charges the unconditional ceiling.
6. **TCB is trusted, not minimized.** operator / steward / sampler / the
   negotiation verifier are trusted third parties, ledgered post-hoc, not MPC.
7. **The human-head channel.** What a reviewer/owner learns lives in memory;
   `reviewer_exposure` names it, no type contains it. Minimize, don't pretend.
8. **Multi-owner authority.** `Chamber.ownerId` is one `Principal`; labs,
   orgs, couples, and repos need a quorum/role model inside the boundary.
9. **Purpose enforcement.** `declaredPurpose` is an unenforced free string.
10. **Breach response, jurisdiction, liability routing** — unmodeled.

### IP-trade frontier (see `../frontier/ip-trades/`)

11. **Method verification** — verifying a technique *works* (causality, novelty,
    transfer) without revealing it is impossible at model scale in 2026; only
    *results* verify. `iptrade.ts` refuses to claim otherwise.
12. **Verification-as-extraction** — the query/run access that proves a
    capability is the channel that distills the model or reconstructs the eval.
13. **The doubly-sealed verifier sees both secrets** — a single entity that can
    leak A's method to B; the pricing joint-coin hardens the sampler, not this.
14. **Verification-cost economics** — honest verification at frontier scale can
    approach the trade's own value; uncosted.
15. **Enforcement is extra-substrate** — cryptographic receipts are not
    contracts; cross-sovereign/jurisdiction enforcement, export-control/KYC,
    and trade-secret forfeiture all live outside the types.

### Coalitional-inference frontier (see `../frontier/coalitional-inference/`)

16. **Inferential targets are unenumerable** — a joint derivative is
    informative about parties who contributed nothing (affected ⊋
    contributing); `InferentialTargetScreen` covers *named* subjects and
    carries `unenumeratedTargetsRemain: true` as a standing non-claim.
17. **Per-reader exposure accounting is Sybil-soft** — `ExposureAccount` is
    keyed over `BeneficialEntity` and inherits frontier #1 wholesale; a reader
    who fragments identities fragments the account (`sybilUndercountRisk`
    makes the undercount visible, nothing prevents it).
18. **Reader models are declared, not observed** — the conditional-leakage
    machinery is only as honest as the declared prior; the unconditional
    ceiling is the backstop, not a fix.
19. **Pool unlinkability is an empirical set size, not a mechanism property**
    — an entropy pool with a thin epoch hides nothing; `publicClaim` states
    the bucket achieved, and a Sybil payee (frontier #1) fragments the set
    invisibly. Canonicality review (frontier: the review agent itself is a
    trusted judge — TCB, frontier #6) is judgment with an `unprovable` lane,
    never proof of minimality.

## Serialization

The chamber wedge's run sidecar (private) (`.chamber/runs/<run_id>/`) is the
first implementation surface. JSON records there use these type names and
field names verbatim (camelCase), one JSONL line per record for append-only
files. The sidecar is a court file: it must answer who asked, what authority
existed, what recipe ran, what became observable, who reviewed it, what
crossed, what the receipt refuses to claim, and what the ledger remembers.
