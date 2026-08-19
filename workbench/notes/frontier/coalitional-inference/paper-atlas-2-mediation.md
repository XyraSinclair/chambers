# Paper atlas 2: mediation, cognitive-work economies, tuples, pools, judgement

Mined 2026-07-04, second pass — same Scry full-text pipeline as `paper-atlas.md`
(25 body-text probes + 15 OpenAlex title probes; 193 unique arxiv candidates,
43 hydrated; raw ledgers in the private mining logs). This pass grounds `mediation.ts`:
structure judgements over exact k-tuples, canonicality review, autonomy
envelopes, entropy pools.

## The eight discoveries

### 1. Mediation economics gives the chamber its theory slot

- *Cryptographic Implications for Artificially Mediated Games* (1001.0054):
  cryptography **replaces the trusted mediator** of correlated equilibrium —
  the chamber-as-mediator has a 15-year-old game-theoretic charter.
- *Constrained Mediation: Bayesian Implementability of Joint Posteriors*
  (2510.20986): a mediator's design problem is *which joint posteriors over
  the participants are implementable*. That is exactly what releasing a
  `StructureJudgement` to its tuple does — it implements a target joint
  posterior across the members. **Adopt as theory anchor**: judgement release
  = joint-posterior implementation; the exposure ledger prices the posterior
  movement.
- *Money Burning Improves Mediated Communication* (2411.19431): costly,
  wasteful commitment makes mediated messages credible under intermediate
  commitment. Widening prices and pool fees are not only compensation — they
  are **credibility devices**; pricing.ts should eventually know the
  difference.
- *The Power of Mediators: PoA/PoS in Bayesian games* (2506.02655);
  Bayesian-persuasion commitment lineage (2511.18662, 2506.05876,
  2305.00777) — what commitment power the platform must actually hold.

### 2. Peer prediction is the payment mechanism for unverifiable judgements

The economy pays agents for `StructureJudgement`s nobody can ground-truth.
That is *information elicitation without verification*, a solved-shape
problem:

- Kong–Schoenebeck, *Water from Two Rocks: Maximizing the Mutual Information*
  (1802.08887) — payments that maximize MI between reports; **pays by the
  same measure our exposure ledger charges by**. The duality conjecture in
  mechanism form, from the credit side.
- *Dominantly Truthful Multi-task Peer Prediction* (1911.00272) — truthful
  with a constant number of tasks; the practical batch shape for judgement
  markets.
- *Peer Truth Serum* (1704.05269), *Surrogate Scoring Rules* (1802.09158),
  *Mechanisms for belief elicitation without ground truth* (2409.07277,
  BTS lineage).

Future canon change (listed, not drifted): `ContributionCredit` estimator
methods should admit `peer_prediction_mi` and `multi_task_peer_prediction`.

### 3. A 2026 cluster is converging on task-scoped disclosure — move fast

- **PrivScope: Task-scoped Disclosure Control for Hybrid Agentic Systems**
  (2605.16630) — minimizing what an agent's cloud-bound payload exposes
  relative to task need: the `CanonicalityReview` justified-capacity check,
  shipped as engineering.
- **DAVE: A Policy-Enforcing LLM Spokesperson for Secure Multi-Document Data
  Sharing** (2602.17413) — Fraunhofer, inter-organizational data spaces: the
  chamber spokesperson pattern.
- **RedacBench: Can AI Erase Your Secrets?** (2603.20208) — redaction
  benchmarks; **CalBench: Coordination-Privacy Trade-offs in Multi-Agent
  LLMs** (2605.09823, Stanford) — the intra-coalition exposure question,
  benchmarked. With OCELOT (atlas 1), that is four 2026 systems circling the
  trench. None has tuple-scoped judgement stores, exposure accounts, or
  priced widening. **The differentiation window is open but not idle.**

### 4. LLM-as-judge reliability is the canonicality-review evidence base — and it cautions

*Reliability without Validity* (2606.19544): exact-match agreement
systematically overstates judge ability once chance-corrected — across 21
judges. Position bias is systematic (2406.07791); survey 2411.15594. Scalable
oversight (2211.03540; weak-judging-strong 2407.04622) is the regime where
review agents must outlast worker capability. Consequences for
`CanonicalityReview`: verdicts keep the `unprovable` lane; production reviews
want judge panels with chance-corrected agreement and perturbation-coherence
checks (the Scry rerank `perturbation_report` pattern) — future field, listed
not drifted.

### 5. Pool anonymity fragility is empirical fact

- *Clustering Tornado Cash Activity* (2510.09433): behavioral linkage
  collapses nominal anonymity sets — `poolClaimsAreAchievedNotHoped`,
  demonstrated on the largest deployed mixer.
- *Timing Attacks on Payment Channel Networks* (2006.12143): payment timing
  deanonymizes — `paymentsAreEmissions`, demonstrated.
- *Loopix* (1703.00536): the delay/cover-traffic design space done right;
  *SoK: Mixing Techniques* (2504.20296); *Hitchhiker's Guide to
  Privacy-Preserving Digital Payments* (2505.21008).
- **AMR: Autonomous Coin Mixer with Privacy-Preserving Reward Distribution**
  (2010.01056) — the closest single design to `EntropyPool` +
  `PoolDisbursement` (mixing plus reward payout unlinkability). Ours differs:
  pool disbursements settle *cognitive work* under standing authorizations,
  inside the money/content separation laws.

### 6. Tuple computation has a running-system lineage to inherit

The Northwestern/VLDB private-data-federation line is the direct engineering
ancestor of pairwise chamber computation: SMCQL (1606.06808, atlas 1) →
**Shrinkwrap** (1810.01816, DP-bounded intermediate result sizes — leakage
metered *inside* the computation) → **KloakDB** (1904.00411, k-anonymous
query processing as the honest middle ground); plus DP-Sync (2103.15942 —
*when you update* leaks), Adore (2212.05176), IncShrink (2203.05084).
On the protocol side: **AnonPSI** (2311.18118) quantifies what PSI *outputs*
leak — the attack surface of `overlap`/`duplicate` judgements; *Private
Collection Matching* (2206.07009) is the matching-without-learning-why
primitive; multi-party PPRL via Bloom filters (1612.08835, 2212.05682) is the
record-linkage workhorse (with known Bloom-filter re-identification caveats).

### 7. Autonomy envelopes have parallel prior art in agent governance

*Agent Contracts* (2601.08815 — resource-bounded formal contracts for
autonomous AI; the `AutonomyEnvelope` shape, independently derived from
Contract-Net lineage); *Governing AI Agents* (2501.07913 — agency law:
loyalty, care, delegation doctrine); principal-agent liability for agentic
systems (2504.03255); *Insurance of Agentic AI* (2606.05449 — the risk-transfer
layer envelopes will eventually need); agent-economy infrastructure
(Magentic Marketplace 2510.25779, Agent Exchange 2507.03904, AgenticPay
2602.06008, SoK agentic commerce 2604.15367, Coral 2505.00749). The economy
we are typing is being built around us without disclosure discipline.

### 8. "Stronger entropy tracking" = audit the accountant

Worst-case budgets need empirical counterparts: *Tight Auditing of DP ML*
(2302.07956), *One-shot Empirical Privacy Estimation for FL* (2302.03098),
grey-box auditing of DP libraries (2602.17454), auditing frameworks
(2210.08643). Deployed budget managers: Cohere (2301.08517, atlas 1) and
**Big Bird** (2506.05290 — W3C-scale budget management across *untrusted*
domains). The checker should ship with an audit lane: estimated-epsilon
probes against our own release gates, `estimated` lane, never a certificate.

## Non-arxiv anchors (OpenAlex, title-level)

Balkin, *Information Fiduciaries and the First Amendment* (W2203925131, 194
cites) + *A Skeptical View of Information Fiduciaries* (W2917451424) — the
legal frame for the platform's duty position; Akerlof lemons lineage;
*Peer Prediction for Peer Review: Designing a Marketplace for Ideas*
(W4361807212); *Diversity and the Division of Cognitive Labor* (W1489910468,
Weisberg–Muldoon) — the epistemics of allocating cognitive work;
communication-equilibrium payoffs (W2143653381); ODR literature; *Neither
Consent nor Property: A Policy Lab for Data Law* (2510.26727) — the legal
third way our licensing regime needs.

## Still unclaimed (differentiated ground after two passes)

1. Tuple-scoped judgement stores as first-class market objects (kind-typed,
   decaying, non-relation included), with reading priced as exposure.
2. Peer-prediction payments *composed with* exposure ledgers — pay by MI
   while charging by MI, one measure two signs, mechanism + accounting in one
   system.
3. Entropy pools for cognitive-work settlement under money/content
   separation (AMR mixes coins; nobody settles judgement markets unlinkably).
4. Canonicality review as admission gate (PrivScope scopes payloads
   post-hoc; nobody reviews *agent minimality* pre-admission with
   chance-corrected judge panels).
5. The mediator charter: judgement release as constrained joint-posterior
   implementation, priced by destroyed option value. Nobody has connected
   mediation economics to leakage accounting.

## Receipts

Probe ledgers: private run artifacts (query lists + hydration logs)
(tagged hits). Round 3: 25 fulltext probes, 193 unique papers, 0 errors,
~40–90s/probe under `X-Scry-Max-Exposure: 100000000`. OpenAlex lane remains
title-only (weak body recall); the arxiv semantic lane remains down (bug
`dd383300`). Citation-graph expansion from the read-fully seeds is still the
next recall move.
