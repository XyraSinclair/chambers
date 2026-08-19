# Coalitional inference: reader-relative leakage and the (source × reader) ledger

Trench opened 2026-07-04 from a live design conversation on "singularity data
licensing." The question it answers: **when a bounded agent computes over
several private silos at once, what is the honest algebra of who may see the
result — and what makes exclusive derivatives economically real?**

Shipped design: `../../primitives/coalition.ts`. This document is the argument;
the module decides.

Literature grounding: **`paper-atlas.md`** — a full-text Scry mining pass over
arxiv bodies + OpenAlex (37 probes, 278 candidates, 56 hydrated). Headlines:
the QIF literature already names affected≠contributing (**collateral
leakage**, 1604.04983); the ledger's math exists as privacy odometers /
individual Rényi filters (1605.08294, 2008.11193) keyed per-source — the
(source × reader) pair key is ours; pointwise maximal leakage (2303.07782) is
the natural `ReaderRelativeLeakage` estimator; **OCELOT** (2606.12341, 2026)
is the closest competitor (per-trajectory inference-leakage budgets for LLM
agents) — differentiate on pair-lifetime keying, coalition provenance, priced
widening, credit attribution; and the weight channel has a measured capacity
(~3.6 bits/param, 2505.24832).

Second pass: **`paper-atlas-2-mediation.md`** (25 more fulltext probes, 193
candidates) grounds `mediation.ts`. Headlines: judgement release is
*joint-posterior implementation* (constrained mediation, 2510.20986) and the
chamber has a game-theoretic charter (crypto replaces the mediator,
1001.0054); peer prediction is the payment mechanism for unverifiable
judgements — Kong–Schoenebeck's MI-maximizing payments pay by the measure the
exposure ledger charges by; a 2026 cluster (PrivScope, DAVE, RedacBench,
CalBench, OCELOT) is converging on task-scoped disclosure without our ledger —
the window is open but not idle; pool anonymity fragility is empirical fact
(Tornado Cash clustering, PCN timing attacks); Shrinkwrap/KloakDB are the
running-system ancestors of tuple computation; and "stronger entropy
tracking" means auditing the accountant (tight DP auditing, empirical ε).

## The five claims worth understanding

Each claim carries its epistemic status. Nothing here is vibes; nothing here is
overclaimed either.

### 1. Information content is reader-relative — leakage is not a scalar (theorem)

Witness: independent uniform bits, derivative `Y = S_A ⊕ S_B`.

- To an outsider: `I(Y; S_A) = I(Y; S_B) = 0`. Zero leakage.
- To Alice, holding `S_A`: `H(S_B | Y, S_A) = 0`. Total disclosure of Bob.

So "how much does this output leak" is ill-posed. The only well-formed
quantity is

```
leak(Y → r, about i) = I(Y; S_i | K_r)
```

— leakage of source `i` to reader `r`, conditioned on what `r` already holds.
One artifact, a *function* from reader-state to bits, not a number.

This is the real content of CANON open-frontier #5 ("budgets are absolute
bits, not bits relative to the observer's prior — the Dwork/Roth lesson").
`coalition.ts` types the reader's prior as `ReaderModel` and the conditional
charge as `ReaderRelativeLeakage`. The honest residue: reader models are
**declared, not observed** — a low-confidence model charges the unconditional
ceiling instead of the conditional figure. The frontier item is narrowed, not
closed.

### 2. The coalition is the zero point of the metric, not a fortress (corollary)

Confining a derivative to its generating coalition neutralizes *self*-leakage
(`I(Y; S_A | S_A) = 0` — telling Alice about her own silo is free). That is why
the coalition is the natural default audience: it is the audience for which
release costs nothing *with respect to each member's own silo*.

But the XOR witness shows the same confinement **maximizes cross-leakage**:
synergistic outputs reveal the most to co-members, and synergy is exactly what
made the joint computation worth running. Value-of-jointness and
cross-exposure are the same quantity read from two sides.

Consequences, all typed:

- Joining a coalition is **mutual-exposure consent** (`ExposureConsent`), not
  entry into a safe interior.
- Synergistic reasoning traces are the high-capacity channel, so the full
  latent defaults to **escrow**; members see typed projections
  (`IntraCoalitionProjection`), each projection debiting every *other*
  member's exposure account.
- Confinement is neither necessary (a sufficiently noised output can go wider
  at bounded cost) nor sufficient (members leak each other; sequences
  compose). Correct statement: **coalition confinement is the zero-cost
  release; every wider audience is a priced release.**

### 3. Composition crosses coalition boundaries — the ledger key is (source, reader), lifetime (design theorem)

The attack that kills per-coalition accounting: to reconstruct Bob's silo,
join twelve small coalitions that each include Bob. Each derivative is
properly confined; the attacker is a legitimate member of each; each grants a
conditionally-safe slice. The slices compose. Per-coalition, per-query-family,
and per-window accounting never fire — DP composition (ε's add) says the
reconstruction lives exactly in the gaps between narrower keys.

So the authoritative account (`ExposureAccount`) is keyed by
**(source chamber, reader beneficial entity)**, monotone, scoped
`pair_lifetime`, audience-independent, fed by every projection and widening
the reader ever sees. This extends `entropy.ts`'s `CompositionKey` (which
hashes audience + window) to the one key the accumulation attack cannot slip
past.

Named dependency, not hidden: per-reader accounting **presupposes identity**
(CANON open frontier #1). A Sybil reader fragments its account. Keying over
`BeneficialEntity` mitigates; `sybilUndercountRisk` makes the undercount
visible; nothing here solves it.

### 4. Typed outputs are what make the calculus decidable (already canon — restated as the reason)

An arbitrary-prose output is an unboundable covert channel: `I(Y; S_i)` for
free text has no free upper bound, so ledger arithmetic over prose is
undefined. A schema-bound output with `k` bits of legal choice space leaks at
most `k` bits per event, **unconditionally, by channel capacity** — no
semantic analysis needed.

`entropy.ts` already enforces this (adversarial-maximum `CapacityEstimate`;
"the numeric accountant binds structured channels, not prose"). What this
trench adds is the *why* at system level: **the type system is the enforcement
mechanism.** Typing outputs = capping channel capacity = turning disclosure
review from judgment into arithmetic. Prose derivatives are not "messy," they
are unaccountable — so they stay owner/escrow-private.

### 5. At singularity conditions, only information-theoretic bounds and custody survive (argument)

As inference cost → 0, simultaneously:

1. **Inversion gets cheap.** Every protection of the form "practically hard to
   reconstruct" evaporates — the attacker has the same cheap cognition.
   Survivors: capacity caps and DP-style bounds (information-theoretic), and
   physical custody (the bits never left). Everything else was a compute-cost
   assumption in disguise.
2. **Event volume explodes.** Millions of coalition computations per day means
   human review cannot be the routine enforcement layer. Only
   machine-checkable invariants scale — which forces exactly this design:
   typed outputs, additive budgets, ledger events, review reserved for
   widenings.

The intuition "confined for math reasons" is right in this strong sense: at
singularity conditions, **math reasons are the only reasons left standing.**

## Two holes no confinement closes

**Affected ≠ contributing.** `f(S_A, S_B)` can be informative about Carol, who
consented to nothing — her genome via her sibling's, her org via a colleague's
calendar, her position via market structure. Coalition provenance records
*causal inputs*; harm accrues to *inferential targets*, a strictly larger set.
Typed as `InferentialTargetScreen` at every widening: named targets get
verdicts (including honest `unprovable`); the field
`unenumeratedTargetsRemain: true` is a standing non-claim no receipt may drop.
Consent-of-inputs does not imply harmlessness-of-outputs.

**Silence leaks.** If the matching service is known to exist, "you were not
matched" and "no coalition formed around you this quarter" carry bits —
`absenceIsAnEmission` (entropy law) lifted to coalition metadata: formation,
membership, cadence, and silence are all observables. `ActivityCoverPolicy`
names the mitigation (dummy runs, padded cadence) and its public claim —
mitigation, never certificate.

## Gradients are egress

The largest exfiltration channel is not any output — it is the model.
Fine-tuning on coalition outputs launders everything through weights, to an
audience ("future model users") with unbounded retention. Typed as
`Coalition.modelImprovementChannel` with only honest values
(`forbidden_declared` / `dp_budgeted` / `unbounded_declared`) and the law
`gradientsAreEgress`. The model-improvement license is not one item in a
stack; it is the channel that dwarfs the others.

## The duality conjecture (held loosely, typed as a non-law)

Attribution and leakage may be one ledger with two signs. Data-Shapley-style
credit is gameable by replication (split a silo into ten shells, harvest ten
shares) — *unless* contribution is valued as **conditional information given
the other silos**, under which copies contribute exactly zero. But that is the
same quantity the exposure ledger already tracks:

> You are paid in proportion to the conditional information you contributed;
> you are exposed in proportion to the conditional information others
> extracted about you.

Why it stays conjecture: bits are not value — one decisive bit can outprice a
megabyte of texture. So `ContributionCredit` uses conditional bits as the
*accounting basis* with a mandatory `dualityCaveat`, `estimatorRole:
"price_input"`, and the corresponding law is deliberately recorded `false`
(`creditAndExposureShareOneMeasure`) — an aspiration named, not asserted. This
is the estimated-lane discipline from `iptrade.ts`: a gameable signal may
inform a continuous decision, never gate a discontinuous one. Same rule for
widening prices: `OptionValueEstimate` sets floors, never gates.

## The economics restated

The sellable object is not private data and not access. It is **licensed
bounded latent formation**: agents may create specified typed derivative
states, under coalition provenance, with per-(source, reader) exposure
accounting, where

- the generating coalition is the zero-cost audience,
- every widening is a priced, one-way, unanimous, screened ledger event
  (`WideningEvent` — disclosure is entropy-irreversible; the resource spent is
  optionality),
- the floor price of a widening is the members' destroyed option value (as a
  price input),
- and upstream contributions earn on the same measure that exposes them.

The platform this implies is a **custodian of conditional epistemic
positions** — a ledger of who can infer what, given what they already hold —
and a toll booth on doors that only open one way.

## Structure judgements and the mediated economy (2026-07-04 extension)

`primitives/mediation.ts` refines the derivative into the working primitive of
the economy: the **structure judgement** — a typed, capacity-bounded claim
(overlap / duplicate / contradiction / complement / fit / gap /
shared-frontier / risk / opportunity / **non-relation**) scoped to an EXACT
k-tuple of repositories. The tuple is the judgement's identity: the same
relation over a different tuple is a different judgement, and visibility to
any subset or superset is a WideningEvent, never an implementation detail.
Three supporting moves:

- **Reading is an exposure event.** A member who reads a synergistic
  judgement debits the *other* members' exposure accounts; the index shows
  the price (`readCostBitsToOthers`) before the read. Nobody browses for free.
- **The requester is a reader, not a privileged sink.** "Don't reveal too
  much to the user" falls out of the ledger: what returns to the requesting
  user is screened like any other disclosure, and **canonicality review**
  (a review agent, because owners won't read much) compares requested vs
  justified capacity and prefers the least-capable agent that meets the
  objective. Excess capacity is denied by default.
- **Payments are emissions.** Payout timing/amount/counterparty identify
  which computation paid — so settlement flows through **entropy pools**
  (batched, delayed, value-bucketed disbursements) whose unlinkability claim
  states the anonymity set *achieved*, never the mechanism hoped. A pool
  with two participants hides nothing, and a Sybil payee fragments the set
  (frontier #1, again, loudly).

### Narrow wedges worth optimizing (not generic)

1. **Cross-vendor vulnerability dedup** (extends the D1 build-first wedge):
   "is your embargoed bug the same as mine" is a `duplicate` judgement over
   an exact 2-tuple of PSIRT repos — enormously valuable, catastrophic to
   leak wider, naturally non-relation-heavy.
2. **Two-lab freedom-to-operate / IP-overlap adjudication** (ip-trades
   composition): `overlap`/`gap` judgements over 2-tuples of research repos,
   priced reads, escrowed latents.
3. **Pairwise collaboration-fit introductions** (matching.ts composition):
   `fit` judgements over 2-tuples of personal chambers; the intro price
   clears through a pool so neither side learns which probe matched.

## Relation to canon (explicit, not drifted)

| Canon object | This trench |
|---|---|
| Open frontier #5 (no auxiliary-knowledge model) | Narrowed: `ReaderModel` + conditional charging; residue = models are declared, not observed |
| `CompositionKey` (audience+window hashed scope) | Extended: `ExposureAccount` keyed (source, reader entity), `pair_lifetime` — the key the cross-coalition attack cannot slip past |
| `EgressBudget` per `ObserverClass` | Refined to per-reader-entity where coalitions exist; class budgets remain for role surfaces |
| Open frontier #1 (identity) | Inherited, named: `perReaderAccountingPresupposesIdentity`, `sybilUndercountRisk` |
| `matching.ts` relations | A match over ≥2 silos is a `CoalitionalDerivative`; near-miss/denial invisibility is the `ActivityCoverPolicy` case |
| Estimated lane (`iptrade.ts`) | Reused verbatim: `SynergyEstimate`, `OptionValueEstimate`, `ContributionCredit` are price inputs, never cliffs |

## What this trench refuses to claim

- Exact mutual information is uncomputable here; every figure is an
  estimator-attested surrogate (worst-case-over-secrets where possible).
- Reader models are declared, not observed. Low confidence charges the
  unconditional ceiling; it certifies nothing.
- The inferential-target set is unenumerable; screens cover named subjects
  only.
- Per-reader accounting undercounts against Sybil identities.
- Cover traffic bounds nothing; it raises the attacker's cost and is labeled
  as exactly that.
- The human-head channel (what a co-member *remembers*) has no type. Escrowed
  latents and typed projections minimize it; nothing contains it.
