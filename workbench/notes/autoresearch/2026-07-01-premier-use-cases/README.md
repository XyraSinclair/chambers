# Three premier use cases, carried natively

Canon: `../../primitives/` decides; this document demonstrates. The test here
is not "could the system be extended to support this" — it is that each case
walks through existing records with at most a thin new rib, and every hard
moment lands on a law that already exists.

The three cases stress three different seams:

| Case | Seam stressed | Rib that carries it |
|---|---|---|
| Labs trading IP | Two sovereigns, neither is "the owner" | `negotiation.ts` |
| Purpose-blind priced matchmaking | The owner sells attention without buying an explanation | `pricing.ts` + `matching.ts` |
| Paid PRs, oracle-approved | Payment against a machine verdict without oracle capture | `pricing.ts` + `market.ts` |

## 1. Major AI labs negotiating an IP trade

Two labs. Each has a Chamber wrapping its private world: model recipes, eval
results, dataset properties, legal posture. Each wants to learn enough about
the other's asset to price a trade, and to reveal only what the deal stage
has earned.

The cast, in canonical records:

```text
Lab A Chamber, Lab B Chamber      two sovereign boundary algebras
NegotiationLane                   the pipe between them; owned by neither
EscrowedClaim                     "our method achieves X on Y" — as a hash, first
RevealStage ladder                stage k opens only on reciprocity at stage k-1
Verifier (Principal)              admitted by Grants from BOTH chambers
CrossChamberReceipt × 2           one per side; symmetric events, asymmetric caveats
```

The sequence:

1. Each lab commits `EscrowedClaim`s — `commitmentHash` only. Nothing about
   the method crosses. (`claimsCommitBeforeTheyReveal`)
2. A verification run is a normal `Run` in a doubly-sealed environment: the
   verifier holds a `Grant` from each chamber, its `EnvRecipe` has no egress,
   and its only sink is a verdict artifact. Both chambers' review stacks gate
   what the verdict may say. The verifier learns the most of anyone in the
   protocol and can emit the least: verdict enums, not excerpts.
   (`verificationPrecedesValuation`)
3. Stages open per the ladder. Each stage carries per-party `EgressBudget`s —
   there is no shared budget to hide behind — and, when disclosure itself is
   priced, a `PriceCross` that must clear first.
4. Either side freezes at will. `freezeStopsTheFutureNotThePast`: crossed
   projections stay crossed, ledgered, receipted; nothing retroactive.
   And `walkAwayTimingIsItselfAnEmission` — a lab that always freezes right
   after seeing benchmark claims is leaking its interest profile, so freeze
   timing draws from the same emission calculus as everything else.

What the spine already gave us for free: the untrusted-ingress law (each
lab's asks are `Transform`s against the other's chamber), the composition key
(a lab probing many small claims across weeks is one adversary, not many
requests), and the receipt's refusal grammar ("verified: capability class;
not verified: training data provenance").

Open question worth its own memo: valuation claims (`claimClass:
"valuation"`) are second-order private data — what A thinks B's asset is
worth reveals A's roadmap. They likely need the same committed-distribution
treatment as prices, not plain escrow.

## 2. Purpose-blind matchmaking with priced attention

The owner admits third-party agents to annotate their private world under
ordinary Grants. Bounties name coarse `DataClass`es — the owner's world stays
unenumerable. Crucially: **the owner never needs to learn why.** They set a
reserve; anything worth interrupting them for must pay it.

```text
Annotation (role: match_candidate)   agents build owner-private structure
CandidateRelation                    the possible match; owner-private, consent-gated
ReservePrice                         owner's floor; purposeDisclosure: "none_required"
PriceDistribution (bid)              agent commits what it would pay to surface
PriceDistribution (ask)              owner commits what they charge for a look
PriceSample × 2                      mediated draws; nonce-auditable, never shown across
PriceCross                           cleared ⇒ SurfacingBid ⇒ ReviewCard reaches the owner
```

The protocol answer to "match only if sampled distributions align": both
sides commit curves (`commitmentHash`), a mediator samples one draw each,
and the introduction happens iff bid-draw ≥ ask-draw ≥ reserve. Neither side
ever sees the other's curve. A failed cross tells each side exactly one bit —
and still debits the `CompositionKey`, because fifty failed probes against
one person's reserve is a reconstruction attack, not fifty coincidences.
(`failedCrossesRevealOneBitAndStillDebitComposition`)

Why sampling rather than revealing the curves to a trusted mediator and
computing the overlap exactly? Because sampling makes the mediator cheap to
distrust: it holds one draw, not the curve; a corrupt mediator leaks bits,
not valuations. And the randomness is load-bearing for the *parties* too — a
deterministic threshold would let an agent binary-search an owner's exact
reserve; a sampled one only yields a noisy estimate at composition-budget
prices.

The humane part is inherited, not added: the recommendation arrives as a
`ReviewCard` with `leakageIfOpened` and a coarse purpose class, the owner is
paid the cleared price for the look regardless of their decision, denials
are invisible (`denialsAreInvisibleToCounterparties`), and exhausted
attention fails closed. The owner's felt experience: my agents mind my world;
occasionally something pays my price to be seen; I look or I don't; either
way the meter ran.

## 3. Third-party agents improving a repo; paying for oracle-approved PRs

The repo plus the owner's standards form the chamber's scoped world. Worker
agents produce patches; the commodity is the accepted delta, exactly as the
market layer already says.

```text
Annotation (role: "patch")        the PR: payload = patch artifact, evidence = CI runs
EvaluatorOracle                   "Fable approves" as a hash: pinned modelClassHash,
                                  rubricHash, determinism mode, appeal path
PriceSchedule                     score → credits, published BEFORE work starts;
                                  monotone step points, holdback, regressionWindow
Acceptance                        oracleId + oracleScore; decision from the rubric
CreditSettlement                  recipientRole: worker | upstream_reuse | leak_catcher;
                                  heldback → released, or slashed on regression
ReuseEdge                         stacked PRs credit the PR they build on
```

What makes the pricing smart rather than a tip jar:

- **Schedules bind before work starts.** The sponsor cannot read the patch
  and then discover their budget shrank. (`schedulesBindBeforeWorkStartsNotAfter`)
- **The oracle is pinned.** `anOracleUpgradeIsANewOracle` — old schedule
  prices are never silently re-scored by a new model. A rubric change is a
  new `rubricHash` is a new schedule.
- **Capture is typed away.** `oracleAuthorMayNotBeWorker: true` on the record
  itself; appeal goes to a human steward or a second oracle, and appeals are
  attention debits like anything else.
- **Regression is priced in.** Holdback fraction plus `regressionWindow`:
  an accepted patch that breaks main inside the window is `slashed`, and the
  agent that caught it settles as `leak_catcher`'s sibling — the caught-
  regression role rides the same rails.
- **Worker asks can be distributions too.** A worker agent that would take
  the task at a range of prices commits an ask curve; the sponsor's schedule
  is effectively a public bid curve; the same `PriceCross` machinery decides
  whether the work starts at all. One pricing rib, all three markets.

And the part that stays quietly radical: even when the repo is public, the
*ledger* of who tried what, which patches were rejected, and what the oracle
scores were is owner-private. Rejected work is not a public reputation stain;
it is a private market memory. (`rejectedWorkStaysPrivate` is just
`Visibility` doing its ordinary job.)

## The synthesis

One new question per rib, as the report card demands:

- `pricing.ts` — *at what price does a crossing clear, revealing how little?*
- `negotiation.ts` — *how do two sovereigns disclose in stages?*

Everything else — ingress, egress, attention, review, receipts, ledger,
composition — was already load-bearing and did not move. That is the check
that the spine was cut right: three very different economies (IP trading,
matchmaking, code work) run on the same eleven-ish core records, and the new
ribs never touch the boundary algebra itself.

## Open questions

1. **Sybil pressure on price crosses.** One agent, many identities, many
   one-bit probes. Composition keys must key on something Sybil-resistant
   (stake, sponsor, verified authorship) — this is the identity problem
   wearing a pricing mask.
2. **Distribution commitment families.** `PriceFamily` is coarse on purpose,
   but sampled-only-once semantics need a verifiable-random draw the mediator
   cannot grind. Commit-reveal with both-party nonces is probably enough;
   worth a short spec.
3. **Valuation claims in negotiation** (see case 1): prices about secrets are
   secrets. Likely resolution: `EscrowedClaim(claimClass: "valuation")` must
   reference a `PriceDistribution` commitment rather than a point value.
4. **Oracle score channels.** An `oracleScore` is a high-precision emission
   about a possibly-private patch. Schedules should quantize scores to the
   step points — pay bands, not floats — so the score channel carries no more
   than the price does.
