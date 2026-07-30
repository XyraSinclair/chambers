# Paper atlas: coalitional inference against the literature

Mined 2026-07-04 via Scry full-text search over arxiv paper bodies plus
OpenAlex title search. Method and receipts at the bottom. Verdict shorthand:
**anchor** (canonical prior work a claim stands on), **extends** (we add
something it lacks), **competes** (overlapping design, differentiate or
absorb), **adopt-term** (the literature already named our concept).

## The five discoveries that matter most

1. **"Collateral leakage" is our affected≠contributing, already named.**
   Bordenabe–McIver et al., *Compositional security and collateral leakage*
   (1604.04983): leakage about correlated third parties whose data was never
   an input, treated compositionally in the QIF framework. **Adopt the term**:
   `InferentialTargetScreen` screens *collateral leakage*; cite this lineage.

2. **The per-source lifetime ledger has exact math waiting: privacy odometers
   and individual filters.** Rogers–Roth–Ullman–Vadhan (1605.08294) define
   pay-as-you-go composition (odometers/filters); Feldman–Zrnic (2008.11193)
   make accounting *individual* — per data-subject, adaptive, Rényi;
   Whitehouse et al. (2203.05481) give fully adaptive composition;
   Lécuyer et al.'s deployment cousin **Cohere** (2301.08517) manages DP
   budgets in a real large-scale system. All of this is keyed **per source**.
   None is keyed **per (source, reader)** — the audience side is ours. The
   `ExposureAccount` should be built as an individual Rényi filter with the
   key widened to the pair.

3. **The reader-relative leakage estimator family exists: pointwise maximal
   leakage and maximal (α,β)-leakage.** Issa–Wagner–Kamath (1807.07878,
   operational maximal leakage), Saeidian et al. (2303.07782, pointwise —
   per-realization, exactly what a per-derivative debit needs), Gilani et al.
   (2211.15453, 2304.07456 — a tunable family unifying MI, maximal leakage,
   local DP). `ReaderRelativeLeakage.estimator.method` should be able to name
   these: they are the candidate estimators with adversarial (guessing)
   semantics, not just Shannon MI. Alvim et al. (1103.5188) is the bridge
   from DP to QIF leakage.

4. **OCELOT (2606.12341, 2026) is the closest engineering competitor.**
   "Inference-leakage budgets for privacy-preserving LLM agents… privacy is a
   property of an entire trajectory… leakage is cumulative, as individually
   innocuous releases compose." That is the trench's composition thesis,
   shipped as an agent-runtime budget. Differentiators we keep: (a) budgets
   keyed (source, reader) across *coalitions and time*, not per
   trajectory/session; (b) coalition provenance and mutual-exposure consent;
   (c) widening as a priced, unanimous, screened economic event; (d) credit
   attribution on the same measure. Companion: Metere (2605.20734), a
   covert-channel reference monitor for LLM agent egress — the
   adversarial-maximum capacity charge (`entropy.ts`) as a running system.
   **Read both in full before building the checker.**

5. **The duality's credit half has a literature: replication-robust data
   valuation.** Ohrimenko et al. (1911.09052) construct payment rules where
   replicated data earns nothing — the exact property we derived for
   conditional-information credit; Agarwal–Dahleh–Sarkar (1805.08125) hit the
   same replication problem in a data marketplace; Ghorbani–Zou (1904.02868,
   Data Shapley) is the baseline being repaired; Yona et al. (1910.04214)
   separates algorithm vs data contribution. Nobody connects the payment
   measure to the *exposure* measure — `creditAndExposureShareOneMeasure`
   remains our conjecture, now with both halves independently grounded.

## Claim-by-claim mapping

### Claim 1 — leakage is reader-relative (declared priors)

| Paper | Verdict | Note |
|---|---|---|
| Kifer–Machanavajjhala lineage: *Blowfish* (1312.3913) | anchor | Privacy defined **relative to a policy** of secrets + adversarial knowledge — the direct precedent for `ReaderModel` as a declared object |
| *Pufferfish Mechanisms for Correlated Data* (1603.03977) | anchor | Mechanisms under declared correlation classes; Wasserstein mechanism |
| *Multi-user Pufferfish* (2512.18632, 2026) | extends-us | Per-user secret classes — closest to per-reader conditioning; check their composition section |
| Ghosh–Kleinberg, *Inferential Privacy* (1603.01508) | anchor | Network-correlated inference guarantees: the max over correlation structures |
| Song et al., *Composition of Inferential Privacy* (1707.02702) | anchor | Composition under correlation — the hard case our ledger must survive |
| *Attribute Privacy* (2009.04013) | anchor | Dataset-level (not row-level) secrets — silo-level properties are what coalition members actually fear leaking |
| Wu et al., *Dalenius' Goal with Practical Assumptions* (1703.07474) | anchor | The honest boundary: Dalenius is unachievable absolutely, achievable under assumptions — which is why `ReaderModel` must be declared |
| *Prior Knowledge and Data Correlation on Privacy Leakage* (1906.02606) | anchor | Unified analysis of adversary priors — the `unconditionalCeilingBits` vs `conditionalBits` split |
| *Inferentially-Private Private Information* (2410.17095) | adjacent | Disclosure correlated with undisclosed secrets (earnings ↔ strategy) — the release-screen problem in economic form |

### Claims 1/4 — the QIF calculus (estimators for the ledger)

Issa–Wagner–Kamath 1807.07878 (maximal leakage, operational); Saeidian
2303.07782 (pointwise ML); Gilani 2211.15453 + 2304.07456 ((α,β) family);
Alvim 1103.5188 (DP↔QIF bridge); Biswas 2406.13569 (Bayes' capacity as
reconstruction-attack measure — an estimator for gradient-channel debits);
Bordenabe 1604.04983 (compositional + collateral).

### Claim 2 — coalition as zero point; the output itself leaks

| Paper | Verdict | Note |
|---|---|---|
| Zinkus et al., *McFIL: Functionality-Inherent Leakage* (2306.05633) | anchor | Even ideal MPC leaks through the agreed output; automated quantification via model counting. The complement of our zero-point claim: confinement's residue is *within-coalition* leakage, and this measures it |
| *SMCQL* (1606.06808) | anchor | Federated private querying — the running-system shape of a coalition computation |
| Williams–Beer (1004.2515), Timme (1111.6857), Chicharro (1711.11408) | anchor | Partial information decomposition: synergy/redundancy formalized — the `SynergyEstimate` estimator family. Known caveat: PID has no agreed unique decomposition; treat as estimated lane, never a cap |
| Christensen et al., *Semi-Private Data Similarity for Valuation* (2206.06650) | adjacent | Observe-to-value under partial privacy — the ip-trades leakage-metered appraisal, independently invented |
| Kong et al., *Securely Trading Unverifiable Information* (1903.07379) | adjacent | Information loses value on revelation; peer-prediction style trade — economic cousin of widening |

### Claim 3 — composition, reconstruction, the lifetime ledger

Odometers/filters (1605.08294, 2008.11193, 2203.05481, 2103.01379,
2209.15596); *Actual Knowledge Gain as Privacy Loss* (2307.08159 — retrospective
actual-leakage accounting vs worst-case: the `conditionalBits` vs `chargedBits`
distinction, independently derived); Kasiviswanathan et al., *Power of Linear
Reconstruction Attacks* (1210.2381); *Averaging Attacks on Bounded Noise*
(1902.06414 — why bounded-noise confinement fails under repetition); Cohere
(2301.08517 — deployed budget management); Riess et al. (2402.12861 — formal
DP bounds against real reconstruction).

### Claim 4 — typed capacity, declassification, IFC

Wutschitz et al., *ML Pipelines from an IFC Perspective* (2311.15792 — Microsoft's
metadata-flow framing; the chamber as IFC system); relaxed noninterference /
typed declassification (1911.04560, 1906.04830, 2604.18300) — the PL-theory
ancestry of `DeclassificationWitness`; *Language-Based Security for Low-Level
MPC* (2407.16504); the 2026 LLM-agent pair: OCELOT (2606.12341) and the
covert-channel egress monitor (2605.20734).

### Duality / economics

Data Shapley (1904.02868); replication-robust payments (1911.09052);
marketplace design (1805.08125); *A Survey on Data Markets* (2411.07267 — the
map); data pricing surveys (2009.04462, 2303.04810); Cummings et al., *Optimal
Data Acquisition with Privacy-Aware Agents* (2209.06340 — buying data from
people who care about leakage: the ExposureConsent pricing problem); Li,
*Selling Data to an Agent with Endogenous Information* (2103.05788);
Gu, *Data Trade and Consumer Privacy* (2406.12457); Abowd–Schmutte
(1808.06303 — privacy vs accuracy as a *social choice* with prices: the
statistical-agency version of widening economics); Vincent–Prewitt–Li,
*Collective Bargaining in the Information Economy* (2506.10272 — the
coalition as bargaining unit, policy side). Non-arxiv (OpenAlex):
Bergemann–Bonatti, *Markets for Information: An Introduction* (W3125511080);
Acquisti et al., *Economics of Privacy*; *Should We Treat Data as Labor?*
(W2783314343); *A Survey on Interdependent Privacy* (W2973890672); *Group
Privacy* (W2561974640); data cooperatives (W4319316196).

### Affected ≠ contributing (collateral leakage)

*Privacy in the Genomic Era* (1405.1891 — the kin-leakage canon); *Privacy
with Good Taste: Genetic Scores* (2208.12497 — quantifying inference on
relatives); SNP hiding (2106.05211); *Interdependent Privacy in Smart Homes:
Bystanders* (2510.26523); collateral leakage (1604.04983).

### Gradients are egress

Shokri et al. (1610.05820, membership inference); Carlini et al. (2012.07805,
training-data extraction); Morris et al. (2505.24832 — **≈3.6
bits-per-parameter memorization capacity**: a literal capacity estimate for
the weight channel; feeds `modelImprovementChannel` accounting); *When Machine
Unlearning Jeopardizes Privacy* (2005.02205 — the *difference* between model
versions is itself a release: version-delta is an emission); gradient
inversion (2204.13784 as representative).

### Singularity condition (cheap inference)

*Automated Profile Inference with LM Agents* (2505.12402); *Beyond Data
Privacy: New Privacy Risks for LLMs* (2509.14278); VLM/audio attribute
profiling (2505.19139, 2507.10016). The Staab et al. "LLMs violate privacy by
inference" line is here as running code: inversion is already cheap.

## What the literature does NOT have (our differentiated ground, confirmed)

1. **The (source × reader) lifetime key.** Individual accounting is
   per-source; OCELOT is per-trajectory; QIF is per-channel. Nobody ledgers
   the pair across coalitions and time.
2. **Coalition as the zero point + mutual-exposure consent.** Correlated-data
   DP treats correlation as a threat to defend against; nobody treats the
   generating coalition as the zero-cost audience with priced cross-exposure.
3. **Widening as a priced, unanimous, screened one-way event** with
   destroyed-option-value floors. Abowd–Schmutte price accuracy socially;
   information economics prices signals; neither prices *audience expansion
   of a joint derivative* per member.
4. **Credit = exposure duality.** Replication-robust valuation and leakage
   accounting exist separately; the identification is unclaimed. Still our
   conjecture, now better grounded on both sides.
5. **Synergy as the exposure price of jointness.** PID is used in
   neuroscience/complex systems, not in disclosure economics.

## Revisions this forces on the trench

- Rename in prose (not yet in types): inferential-target screening *is*
  **collateral leakage** screening; cite 1604.04983.
- `ReaderRelativeLeakage.estimator.method` should admit named estimators:
  `pointwise_maximal_leakage`, `maximal_alpha_beta_leakage`, `bayes_capacity`,
  `shannon_mi_bound` — future canon change, listed here, not drifted.
- `ExposureAccount` implementation target: an individual Rényi filter
  (2008.11193) with the key widened to (source, reader).
- The weight channel now has a number: ~3.6 bits/param (2505.24832) — the
  `dp_budgeted` lane can be a real budget, not a gesture.
- Read fully before building: OCELOT (2606.12341), egress monitor
  (2605.20734), McFIL (2306.05633), pointwise ML (2303.07782),
  Feldman–Zrnic (2008.11193), collateral leakage (1604.04983),
  multi-user Pufferfish (2512.18632), knowledge-gain accounting (2307.08159).

## Method and receipts (Scry)

- **Search lane**: full-text lexical search over arXiv bodies (up to 50k
  chars; body-only phrases like "privacy odometer" recall correctly), with
  per-query exposure caps passed explicitly. No semantic lane was available
  for this pass; recall was compensated with probe diversity, not semantics.
- **Probes**: 37 full-text lexical probes across 13 tag families (two
  rounds; round 2 sharpened noisy families), 8 hits each → 289 rows, 278
  unique papers, 0 errors after the exposure fix. Plus 12 OpenAlex
  title-level probes for non-arxiv economics/governance literature.
- **Selection**: 56 papers hydrated (year, authors, first 650 chars of body);
  atlas curated by hand from those plus per-tag top lists.
- **Known coverage gaps**: OpenAlex search is title-level (weak recall for
  body concepts, e.g. Bergemann–Bonatti found only by exact title); no
  citation-graph expansion ran yet (next action: expand from the 8
  read-fully seeds via `openalex_work_references`); non-English and
  paywalled venues unprobed.
