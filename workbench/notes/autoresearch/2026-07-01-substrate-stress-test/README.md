# Substrate stress test: what 207 agents found, what we change, what we still don't satisfy

This is the synthesis of an exhaustive, adversarial pass over the canonical
type substrate (`../../primitives/`). Method, so the conclusions are auditable:

- **8 orthogonal disciplinary lenses** (DP/composition, information-flow
  control, mechanism design, HCI/friction, interpretability, red-team
  adversary, systems/implementation, consent/rights) independently enumerated
  the properties a *premier* confidential-cognitive-work economy must satisfy.
- Deduped into a **12-cluster property catalog** (74 properties).
- Each cluster **audited against the actual canon**, then every non-satisfied
  finding faced **two adversarial skeptics** (a canon-defender and a
  pragmatist trying to show the fix backfires). Only findings that survived
  refutation carried forward: **51 gaps** (1 high, 4 medium, 46 low).
- The **5 sharpest genuine tensions** were argued both sides, cross-examined
  (each side forced to concede), and ruled by an independent adjudicator. All
  five reached **synthesis at high confidence** — none was a clean win for
  either pole.
- **5 hard-committed redesigns** (enforced IFC lattice, object-capabilities,
  accounting-first, friction-first, market-native) were each scored by **4
  independent judges** on privacy rigor / friction / interpretability /
  expressiveness, equally weighted.
- A **completeness critic** then attacked the whole analysis for shared blind
  spots.

207 agents, 0 errors, ~11M tokens. Raw result archived as
`the run's full result artifact (private)`; per-agent transcripts in the run's `journal.jsonl`.

The headline: **the substrate is sound in shape but overclaims in three
places, and it is CIA-minus-A — it models confidentiality and integrity
pervasively and availability not at all.** The five debates give us concrete,
non-overclaiming type changes. The blind spots give us an honest map of what
types alone will not fix.

---

## 1. The five tensions, resolved

Every one resolved to *synthesis* — which is itself a finding: the poles were
false dichotomies, and the sharp answer sits between them.

### 1.1 Capacity: qualitative buckets vs. a numeric bit-accountant

**Ruling.** Keep the qualitative `LeakageClass`, and *add* an authoritative
monotone `cumulativeBits: Bits` to `CompositionState` — a true Σ over
`EgressDebit.estimate` per `CompositionKey`. `releaseGate` becomes a
**conjunction**: `allow` requires both that the numeric accountant has not
tripped *and* that the ordinal/`EntropyReview` gate permits. Neither certifies
`allow` alone. `EgressBudget.onExhaustion` finally gets its numeric trigger,
making `repeatedQueryComposition: "blocked"` enforceable rather than aspirational.

**Why it matters.** The reserve-probing defense in the matchmaking case (b)
rests entirely on repeated one-bit crosses composing into a block. Today that
composition is qualitative and non-binding — an adversary can probe an owner's
reserve indefinitely. The numeric accountant is what makes
`failedCrossesRevealOneBitAndStillDebitComposition` true instead of decorative.

**Residual risk (honest).** Σ is the *wrong operator for correlated free-text*.
Summing `textBitsUpperBound` per field either saturates (every free-text field
≈ maxBytes·8, pinning the sum and firing spurious fail-closed STOPs on safe
work) or, tuned down, silently under-counts. **So the numeric accountant binds
structured/enumerable channels (schema fields, orderings, buckets, price
crosses, denominators); free text stays on qualitative + human review.** We do
not pretend to bit-count prose.

### 1.2 Information flow: descriptive labels vs. an enforced lattice

**Ruling.** Add an **integrity dual** without the pervasive relabel.
Introduce `Integrity` and `Label = {conf: Visibility, integ: Integrity}`; a
checked `WellLabeled` constructor that succeeds only if a derived label
dominates its sources (`conf ≥ join(sources)`, `integ ≤ meet(sources)`);
`Release` references a `WellLabeled` candidate and carries a
`DeclassificationWitness`. **Do not** relabel every `visibility` field into the
lattice (that is the "pervasive blob" both sides rejected).

**Why it matters.** Today `oracleAuthorMayNotBeWorker` and "release is a
reviewed subset" are asserted; a laundering path (mix a high-integrity
selector with untrusted content, declassify the blend) is expressible.
Robust declassification requires the field-selector itself be high-integrity.

**Residual risk (honest).** The constructor guarantees label *consistency over
declared provenance* — never that opaque LLM prose respects its label. Omit a
`ProvenanceEdge` or mislabel a source and the join is computed over a lie. This
is a consistency check, not noninterference. The receipts must say so.

### 1.3 Price discovery: sampled crossing vs. exact secure overlap (2PC)

**Ruling.** Keep the mediated sampled cross; **do not** add two-party
computation. But **kill sampler-grinding**: replace `PriceSample.nonceHash`
with a *jointly-committed coin* pinned before the draw is computable (bind it
to `RevealStage`'s `simultaneous_commit_then_reveal`), so a later audit covers
*selection fairness*, not just membership. Add `samplerMayNotBeAParty` (the
analogue of `evaluatorMustBeRoleSeparated`).

**Why it matters.** Today a corrupt sampler can grind nonces to steer whether a
match clears — the privacy of the sampled protocol is only as good as the
draw's unpredictability. A joint coin makes the sampler unable to choose the
outcome without collusion, at the cost of one extra commit-reveal round.

**Residual risk.** A stalled reveal is itself an emission
(`walkAwayTimingIsItselfAnEmission`); the joint coin adds mild interactivity.

### 1.4 Owner attention: mandatory per-release gate vs. standing delegation

**Ruling.** **Split content from money.** Keep `Release.ownerDecision` a
required *human* act and `owner_decided` support human-only — reject a general
`StandingReleaseDelegation` that auto-emits content releases (it fails the
CANON owner-agency and receipt-honesty tests). *Admit* a narrow rib,
`SettlementPayoutAuthorization`, that authorizes recurring **payouts** (not
disclosures) zero-touch, bound once to an oracle + schedule + match predicate,
revocable, within the regression window.

**Why it matters.** This is exactly use case (c): pay for oracle-approved PRs
without a human clicking approve on every settlement — *while* never letting a
standing authorization move private *content* across the boundary. The thing
that recurs is money; the thing that always needs a human is disclosure.

**Residual risk.** Even a content-free payout is an emission (`billing_line`,
`notification_timing`); repeated payouts to one worker across chambers compose
(open question #1). The authorization debits the accountant like anything else.

### 1.5 The tail: append-only ledger vs. provable erasure

**Ruling.** Backbone stays append-only-with-external-witness; subject erasure
is a **salted-commitment tombstone** as the *default* for subject payloads:
commit as `C = sha256(salt ‖ payload)` with a high-entropy salt held in the
payload store, never the ledger. Erasure destroys salt + bytes; `C` and every
`causalParentIds` link still verify. Add `redactionState: "erased_tombstone"`,
`Artifact.erasedAt`, an `ErasureRequest` record, and `LedgerAction:
"artifact_erased"`.

**Why it matters.** Right-to-deletion vs. an append-only integrity chain looks
irreconcilable; salted commitments dissolve it. The chain proves *what
happened* without retaining *what was said*.

**Residual risk / hard precondition.** The salt must be applied **at write
time**. Any subject payload committed as raw `sha256(payload)` — legacy data,
or any path that skips salting — cannot be retroactively erased. This is a
construction-time obligation, not a feature flag.

---

## 2. The overclaims (this is where the ethos bites)

The substrate's own non-negotiable is *no success-shaped privacy claims*. The
audit found three places where the types themselves overclaim:

1. **`oracleAuthorMayNotBeWorker: true`** (and every "separate role" predicate)
   is a hardcoded boolean the identity model cannot back. One controlling
   entity registers distinct `Principal`s as worker, reviewer, evaluator, and
   oracle-author; all ids differ; every `separate` check passes; the entity
   colludes with itself. **The boolean is a lie the type system tells.**

2. **The accounting stack is only as sound as whoever computes it.**
   `CapacityEstimate`, `LeakageEstimate`, `EgressDebit.estimate` name no
   estimator and bound no adversarial understatement. An agent/operator that
   lowballs `sideChannelBits` breaks every budget silently, and nothing records
   who did the estimating.

3. **`schemaBits` is a number an implementation can underfill.** Nothing types
   it as the *adversarial maximum* = log2(count of all schema-valid outputs,
   including every legal enum value, field presence, and ordering permutation).
   A malicious agent steganographically encodes secrets in legal field/ordering
   choices at the adversarial rate while the budget is charged honest-case.

All three are fixable by turning an assertion into a *checked, attributed
record* — which is the canon's own aesthetic.

---

## 3. What we adopt now (passes the 5-test admission gate)

Applied to `../../primitives/` in this pass. Each removes an overclaim or
makes an aspirational law enforceable; none bloats the spine.

| Change | Module | What it buys | Debate/gap |
|---|---|---|---|
| `BeneficialEntity` + `Principal.beneficialEntityId` + `ConflictOfInterestCheck`; `oracleAuthorMayNotBeWorker` → disjointness verdict | market, core | Collusion becomes checkable set-disjointness, not a boolean lie | HIGH gap; 3/5 designs |
| `EstimatorAttestation` on capacity/leakage; `estimatorId` | entropy | Names who computed a budget; understatement becomes attributable | blind spot |
| `CompositionState.cumulativeBits` Σ + conjunctive `releaseGate` + numeric `onExhaustion` trigger (structured channels only) | entropy | Repeated-probe reconstruction actually blocks | Debate 1.1 |
| Split `CapacityEstimate` into `enumValueBits`/`orderingBits`/`fieldPresenceBits`; `capacityIsChargedAtAdversarialMaximum` law | entropy | Steganographic egress charged at the real rate | 1.2 gap |
| `Integrity`, `Label`, `DeclassificationWitness` on the release path (not pervasive) | core | Robust declassification; laundering-via-declassifier blocked | Debate 1.2 |
| `redactionState: "erased_tombstone"`, `Artifact.erasedAt`, `ErasureRequest`, `artifact_erased` action; salted-commitment note | core | Right-to-deletion over an append-only chain | Debate 1.5 |
| `SettlementPayoutAuthorization` rib | market | Zero-touch recurring payout without standing content release | Debate 1.4; use case (c) |
| `PriceSample` joint-committed coin; `samplerMayNotBeAParty` | pricing | Sampler cannot grind the match outcome | Debate 1.3 |
| `RetentionPolicy.disputeHorizon` + retention-outlives-claims law | core | Receipts remain auditable through their dispute window | medium gap |
| `PlainAccount` interpretability output (`whatCrossed`/`whatDidNotCross`/`whatItCannotPromise`) | core | A person can read what the system did and did *not* promise | friction_first top graft; your interpretability requirement |

The friction-first design scored highest (29.8/40) and — importantly — did *not*
buy low friction by sacrificing privacy (friction 9.0, privacy 7.8, tied top).
That is a real answer to "are low-friction and safe compatible here": **yes, if
safety comes from derivation and defaults, not from asking the owner to
understand.** `PlainAccount` is the graft that carries that philosophy into the
canon without adopting its riskier moves (see §4).

---

## 4. What we deliberately do NOT adopt

- **Deleting `Release.ownerDecision` for a pure derivation** (friction_first's
  core move). Judged fatal: it replaces N heterogeneous human judgments with
  one shared pure function — a correlated blast radius, and it cannot produce
  an honest `owner_decided` receipt. Disclosure keeps its human.
- **A pervasive information-flow relabel / full lattice** (minimal_lattice).
  "Provable" overclaims: noninterference does not hold over opaque prose, and
  timing/cost/cache channels escape a provenance lattice by construction — the
  classic IFC blind spot, and precisely our most product-relevant leaks.
- **`Cap<F>` as the universal authority primitive** (capability_ocap). Category
  error at the center: object-capabilities confine *overt* authority; side
  channels flow *without invoking any door*. And `Cap` as a branded string is
  forgeable without an unspecified reference monitor — and two sovereign
  chambers share no monitor (breaks use case (a)).
- **2PC / garbled-circuit price overlap.** Rejected in 1.3: interactivity and
  liveness cost outweigh the benefit over a joint-coin sampled cross.

Each of these had genuinely good *grafts* (adversarial-max capacity;
label-derived composition keys; authority-monotonicity as `meet()`;
declassify-as-single-boundary-event) — those are folded into §3 or §5. The
*organizing philosophies* are not adopted wholesale.

---

## 5. What types alone will not fix — the honest open frontier

The completeness critic's deepest finding: **all five designs and all eight
lenses shared an owner-centric, confidentiality-integrity, identity-solved,
harm-linear-in-bits, all-channels-substrate-mediated worldview.** The following
are not gaps in the current types — they are places where a type is the *wrong
tool* and we must say so rather than paper over it. These become the next
research tracks; none is closed by this pass.

1. **Identity is given.** Every Sybil/collusion/composition defense
   presupposes principal-uniqueness. `Principal` is an id with a `display`
   mode. `BeneficialEntity` (§3) relocates the problem to "are two entities
   secretly one" = identity governance — it does not solve it. **Proof-of-
   uniqueness is a substrate dependency, not a field.** For use case (a),
   sovereign labs, there is no shared identity root at all.

2. **Worker-side fair exchange.** The substrate protects the owner
   comprehensively and the worker barely. An owner can read an `AgentFinding`
   / `Annotation` payload and then `reject` — obtaining the cognitive product
   without paying. Needs commit-before-read or escrowed reveal, symmetric to
   what negotiation already does for claims. **Currently the market is not
   incentive-compatible for the worker.**

3. **CIA-minus-A: availability is unmodeled.** Every property is
   confidentiality/integrity/accounting; liveness is absent, so `fail-closed`
   was treated as unambiguously safe rather than as a griefing amplifier.
   Flood `AttentionQueue` with cheap `ReviewCard`s → exhaust `AttentionBudget`
   → `attentionExhaustionFailsClosedForDisclosure` → **denial of release and
   denial of payment as an attack.** Needs an anti-grief / cost-to-interrupt
   model beyond the reserve.

4. **Harm is not linear in bits.** The entire entropy apparatus measures
   leakage in bits, decoupled from `Scope.sensitivity`/`DataClass`. One
   catastrophic attribute ("has condition X") is one bit and a life; a
   sensitivity-weighted or lexicographic budget is needed so the accountant
   cannot trade a catastrophic bit for many trivial ones.

5. **No auxiliary-knowledge model.** Budgets are absolute intrinsic bits, not
   bits *relative to what the observer already knows*. `uniquenessRisk` gestures
   at it; there is no model of the observer's prior. This is the real Dwork/Roth
   lesson and we cite it without honoring it.

6. **Trust is routed through mediators, not minimized.** operator / steward /
   `samplerId` / negotiation `verifierGrantIds` are trusted third parties whose
   misbehavior is only ledgered *post hoc*. The "doubly-sealed verifier" that
   sees both sovereign chambers' secrets is a TTP, not MPC. TCB minimization
   (threshold, MPC, client-side encryption) is a whole research track we have
   only gestured at.

7. **The human-head channel.** What a reviewer/steward/owner learns via an
   `ExpansionToken` lives in their memory and mouth; `reviewer_exposure` names
   the risk but no type governs it. Minimize exposure; do not pretend to
   contain it.

8. **Multi-owner authority.** `Chamber.ownerId` is one `Principal`. Labs,
   companies, couples, and multi-maintainer repos are not individuals — who may
   issue a `Grant`, approve a `Release`, set a `ReservePrice`? A quorum/role
   model inside the owner boundary is unbuilt.

9. **Purpose is an unenforced free string.** `declaredPurpose` drives admission
   yet sits next to the bit-rigorous entropy layer as prose. Purpose-limitation
   and behavior-drift detection are unmodeled.

10. **Breach response, jurisdiction, liability routing.** After an erroneous
    `Release` there is no containment primitive, no affected-party/regulator
    notification record, no data-residency or cross-border transfer typing, no
    liability attribution across owner-who-approved / reviewer-who-allowed /
    operator-who-ran. Use case (a) implicates all of this.

---

## 6. What adopting this actually feels like — three walkthroughs revisited

**(a) Labs trading IP.** The joint-coin sampler (1.3) and integrity dual (1.2)
harden the negotiation lane, but §5.1 (no shared identity root) and §5.6 (the
verifier is a TTP, not MPC) mean the premier version of this case is *gated on
MPC we have not built*. Honest status: the type shape is right; the trust model
is a stub. We should say "verified by a mutually-admitted verifier under these
caveats," never "neither side learned anything."

**(b) Purpose-blind matchmaking.** The numeric accountant (1.1) is what makes
"the owner never notices a probe" true: repeated reserve-probes now compose to a
block instead of leaking freely. The joint coin (1.3) stops a corrupt sampler
steering matches. But §5.3 (grief) means a flood of sub-reserve surfacing
attempts can still exhaust attention, and §5.1 means the whole thing rests on
the prober not being cheaply Sybil. Adoption makes the *good* path safe and
interpretable; the adversarial path needs identity + anti-grief.

**(c) Paid oracle-approved PRs.** This is the case that comes out best.
`SettlementPayoutAuthorization` (1.4) delivers zero-touch recurring payment
without standing content release; `BeneficialEntity` (§3) turns
"Fable-author isn't secretly the worker" from a boolean lie into a checkable
disjointness verdict; the dispute-horizon retention (§3) keeps the oracle's
verdict auditable. Residual: §5.2 — the worker can still be read-then-rejected
until fair-exchange lands.

---

## 7. Bottom line

The shape survived. The substrate is a sound *grammar of permission,
accounting, and receipt* — the debates refined it, they did not overturn it.
Three overclaims are being retired this pass (self-collusion boolean,
unattributed estimates, honest-case capacity). Five tensions resolved to
concrete, non-overclaiming type changes. And the real discipline is §5: the
system's most important next moves — identity, worker-side fairness,
availability, TCB minimization — are **not type-system problems**, and the
canon's honesty requires we stop the types from pretending otherwise.

Anti-isotropy held: the poles were false, the syntheses are sharp, and the
blind spots are now named instead of averaged away.
