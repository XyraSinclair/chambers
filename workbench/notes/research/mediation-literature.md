# Mediation literature for the chamber calculus

Prior work most relevant to **chambers**: a confined judgment agent working over
mutually-distrusting parties' private corpora, releasing only finite-alphabet,
metered verdicts. Anchor use case: IP-overlap mediation between two labs.

Companion file: [`collaborative-confidential-inference-economy-arxiv.md`](./collaborative-confidential-inference-economy-arxiv.md)
(140KB) already covers the *substrate* — confidential-computing TEEs, private
inference, data-valuation/Shapley, verifiable inference markets, provenance and
attested receipts. This file deliberately does **not** re-cover that. It covers
the *calculus*: how to measure, bound, compose, and price the disclosure of a
verdict. Where a paper appears in both files it is flagged
`[already in substrate doc]` and only its steal-for-the-calculus angle is given.

Everything here is a preprint or published paper; nothing is peer-review-verified
by us. Canonical pre-arXiv results are cited by venue.

---

## Vein 1 — Quantitative information flow: g-leakage, capacity, composition

This is the spine of the chamber calculus. A chamber *is* an information channel
`C: Secret → Verdict` with a deliberately tiny output alphabet; QIF is exactly
the theory of how much such a channel leaks and how leakage accumulates.

- **Smith, "On the Foundations of Quantitative Information Flow"** (FoSSaCS 2009).
  Proves that Shannon entropy is the *wrong* measure for a one-guess adversary and
  founds **min-entropy leakage** `L = H_∞(prior) − H_∞(posterior)` as the operationally
  meaningful quantity. **Steal:** the metered-verdict budget must be stated in
  min-entropy (vulnerability under the *best single guess*), not Shannon bits — a
  verdict that halves the adversary's guessing work leaks 1 bit even if Shannon
  leakage looks small.
- **Alvim, Chatzikokolakis, McIver, Morgan, Palamidessi, Smith,
  *The Science of Quantitative Information Flow*** (Springer 2020) — the canonical
  book; **g-leakage** paper is Alvim et al., "Measuring Information Leakage using
  Generalized Gain Functions" (CSF 2012,
  [pdf](https://www.lix.polytechnique.fr/~catuscia/papers/QIF/gleakage.pdf)).
  Constructs the **gain-function** generalization `V_g`: an adversary scores partial
  wins (guess a property, guess within k tries, guess a close value), and proves
  min-capacity/g-capacity/Shannon-capacity ordering bounds. **Steal:** the chamber's
  threat model is a *choice of g*. "Did lab A's method overlap lab B's claim 7?" is a
  property-guess gain function; design the verdict alphabet to bound `V_g`-leakage for
  the specific g the parties fear, not generic bits. This is the single most important
  import: **the alphabet is chosen against a gain function.**
- **Kawamoto, Chatzikokolakis, Palamidessi, "On the Compositionality of
  Quantitative Information Flow"** ([arXiv:1611.00455](https://arxiv.org/abs/1611.00455),
  LMCS 2017). *The* composition result: bounds the multiplicative g-leakage of a
  whole system in terms of its components' g-leakages, with tight specializations for
  parallel channels and min-entropy. **Steal — the composition law:** a sequence of
  chamber verdicts is a channel composition; this gives the sub-additivity bound that
  lets a mediator sum per-verdict leakage into a session budget instead of
  re-analyzing the whole transcript. This is your leakage-accounting backbone.
- **Boreale, Pampaloni, "Quantitative Information Flow under Generic Leakage
  Functions and Adaptive Adversaries"**
  ([arXiv:1507.05766](https://arxiv.org/abs/1507.05766)). Handles the **adaptive**
  case — an adversary who chooses its next probe based on prior outputs — and relates
  adaptive to non-adaptive leakage under a generic uncertainty measure. **Steal —
  scoped by adversarial review:** this matters for TIGHT estimates of *actual* leakage
  against a specific adaptive strategy, never as a correction on the alphabet
  *ceiling* — L8 summation is already sound against adaptive requesters, because the
  whole transcript lives in the product of the declared alphabets
  (min-capacity ≤ Σ log2|alphabetᵢ| unconditionally, questions being gatePub-public).
- **McIver, Morgan, Rabehaja, "Compositional security and collateral leakage"**
  ([arXiv:1604.04983](https://arxiv.org/abs/1604.04983)). Shows that composing a
  secure component into a larger context can leak *collaterally* through correlations
  the component never saw. **Steal — the caveat:** a per-verdict-clean chamber can
  still leak about lab A's secret through its verdict about lab B if the corpora are
  correlated (both cite the same prior art). The calculus needs a collateral-leakage
  term whenever the two parties' private inputs are statistically dependent.
- **Américo, Malacaria, et al., "An Algebraic Approach for Reasoning About
  Information Flow"** ([arXiv:1801.08090](https://arxiv.org/abs/1801.08090)).
  Lattice/algebra of information (partitions ordered by refinement) as the structure
  underlying leakage. **Steal:** the verdict alphabet induces a partition of the secret
  space; the refinement lattice is the right domain for "verdict A reveals strictly
  more than verdict B," giving a partial order on chamber designs.

**Adjacent, weaker fit:** "Information Density Bounds for Privacy"
([arXiv:2407.01167](https://arxiv.org/abs/2407.01167)) — pointwise (per-outcome)
information-density tail bounds, a refinement over average leakage worth citing if the
chamber needs a *worst-case-outcome* guarantee rather than expected leakage.

---

## Vein 2 — IFC type systems and declassification

A chamber is a *declassifier*: it deliberately releases a function of secret inputs.
The whole 20-year declassification literature is about doing that safely, and its
vocabulary (what/who/where/when, robustness, delimited release) is exactly the spec
language a chamber's release policy needs.

- **Abadi, Banerjee, Heintze, Riecke, "A Core Calculus of Dependency"** (DCC, POPL
  1999). The foundational calculus giving a monadic `T_ℓ` protection modality and a
  single framework subsuming noninterference, binding-time, and slicing. **Steal — the
  definition:** the chamber's type discipline should be DCC-shaped — a graded modality
  indexed by *party* (A, B, mediator, public) with the verdict channel as the *only*
  well-typed elimination from the protected monad into the public level.
- **Sabelfeld, Sands, "Declassification: Dimensions and Principles"** (CSFW 2005 /
  JCS 2009,
  [pdf](https://www.cse.chalmers.se/~andrei/sabelfeld-sands-jcs07.pdf)). Classifies
  every declassification policy along **what / who / where / when** and states prudent
  principles (semantic consistency, non-occlusion, conservativity, monotonicity of
  release). **Steal — the spec grammar:** a chamber release policy is literally a point
  in this 4-cube — *what* = the gain-function property, *who* = owner-approved packet,
  *where* = the front door, *when* = per-metered-query. Adopt their four principles as
  the chamber's release-policy well-formedness checks.
- **Arden, Gollamudi, Cecchetti, Chong, Myers, "A Calculus for Flow-Limited
  Authorization" (FLAC)**
  ([arXiv:2104.10379](https://arxiv.org/abs/2104.10379); orig. CSF 2016). Extends DCC
  with dynamic authorization and proves **noninterference + robust declassification**
  for programs that themselves decide who may declassify. **Steal — the composition
  law + robustness:** FLAC's robust-declassification theorem (an attacker cannot
  *influence what gets released*) is the property the chamber front door must satisfy
  so that a malicious party cannot steer the verdict channel to exfiltrate the
  counterparty's corpus. This is the closest existing formal model to "confined agent
  whose release authority is itself typed."
- **Cruz, Tanter, et al., "Type Abstraction for Relaxed Noninterference" /
  "Type-based Declassification for Free"**
  ([arXiv:1905.00922](https://arxiv.org/abs/1905.00922)). Encodes *what*-declassification
  policies as security types via type abstraction, getting relaxed noninterference "for
  free" from parametricity. **Steal:** a lightweight route to specifying the verdict as
  a declassifying *type* (the alphabet is the observation type) rather than a separate
  policy language.
- **Hughes, Marshall, Orchard et al., "Graded Modal Types for Integrity and
  Confidentiality"** ([arXiv:2309.04324](https://arxiv.org/abs/2309.04324)) and
  "On Graded Coeffect Types for Information-Flow Control" (Granule project, 2025).
  Grades a comonadic modality by a security lattice and adds a dual integrity modality,
  with noninterference machine-checked. **Steal — the graded-monad structure:** this is
  the type-theoretic home for a *metered* verdict — grade the release modality by the
  **leakage budget** (a semiring element), so the type system statically accounts
  min-entropy spend the way Vein 1 accounts it semantically. Graded IFC + g-leakage is
  the natural fusion and nobody has closed it (see empty veins).
- **"Compositional security definitions for higher-order where-declassification"**
  ([arXiv:2604.18300](https://arxiv.org/abs/2604.18300)). Recent (2026) compositional
  semantics for *where* information may be released in higher-order programs.
  **Steal:** if chambers nest (a mediator chamber calling sub-chambers), this gives the
  higher-order compositional declassification semantics that Vein-1 channel composition
  doesn't cover.

---

## Vein 3 — Mediator / arbiter theory in economics

This vein tells you what a mediator *can achieve in principle* and how the message set
enters the optimization. Core results are pre-arXiv; the live arXiv work is on
persuasion under constraints.

- **Aumann, "Subjectivity and Correlation in Randomized Strategies"** (JME 1974) —
  correlated equilibrium; **Forges (1986)** and **Myerson, "Multistage Games with
  Communication"** (Econometrica 1986) — **communication equilibrium** and the
  **revelation principle for mediators**: any equilibrium of any mediated protocol is
  achievable by a *canonical* mediator that takes types in and returns action
  recommendations. **Steal — the definition + a reduction:** the revelation principle
  says you may WLOG restrict the chamber's verdict alphabet to *recommended actions /
  canonical outcomes* — you never need a richer alphabet than the decision the parties
  will actually take. This bounds alphabet size from the *decision* side, complementing
  the leakage bound from Vein 1.
- **Monderer, Tennenholtz, "Strong Mediated Equilibrium"** (AAAI 2006 /
  AIJ 2009) and **Ashlagi, Monderer, Tennenholtz, "Mediators in Position Auctions"**
  / **"the mediation value"** (GEB 2009). Define a mediator who can act *on behalf of*
  consenting parties and quantify the **mediation value** = ratio of best correlated to
  best Nash welfare. **Steal — the metric:** mediation value is the natural "is a
  chamber worth building here?" number — the welfare gap between mediated and
  unmediated outcomes upper-bounds what the two labs should jointly pay for the chamber.
- **Kamenica, Gentzkow, "Bayesian Persuasion"** (AER 2011). A sender commits to a
  signal (Blackwell experiment) to move a receiver's posterior; optimal signal =
  concavification of the sender's value over posteriors. **Steal — the frame:** the
  chamber *is* a committed signaling scheme; the verdict alphabet is the signal
  realization set, and the mediator's design problem is persuasion with **two receivers
  who are also the two sources** and an *added leakage constraint* — the exact object
  the pure-persuasion literature omits (see empty veins).
- **Aybas, Turkel, "Persuasion with Coarse Communication"** (2024) — optimal
  information design when the sender is **exogenously limited to k messages**, with a
  tight bound on the marginal value of message k+1. **Steal — the alphabet-sizing law:**
  this is the closest existing result to "how many verdict symbols do I need?" Their
  marginal-value-of-a-message bound is directly reusable to decide chamber alphabet
  cardinality — but it maximizes persuasion, not decision value under a privacy budget.
- **"Differentially Private Bayesian Persuasion"**
  ([arXiv:2402.15872](https://arxiv.org/abs/2402.15872)). Computes optimal signaling
  schemes under ε-DP, (ε,δ)-DP, and Rényi-DP constraints on the signal.
  **Steal — the constrained construction:** this is the *only* found paper that jointly
  optimizes a signal for persuasion value **and** a formal privacy bound. It is the
  nearest neighbor to the chamber's core optimization; steal its constrained-LP
  formulation, then swap DP-on-the-signal for **g-leakage-on-the-verdict** (DP bounds
  the wrong thing — it protects a row, not the min-entropy of a shared secret).
- **Geffner, Halpern, "Communication Games, Sequential Equilibrium, and Mediators"**
  ([arXiv:2309.14618](https://arxiv.org/abs/2309.14618)). Extends mediator
  implementability from Nash to **sequential** equilibrium (off-path credibility).
  **Steal:** if a chamber runs multiple rounds, this is the solution concept that keeps
  the mediator credible after an unexpected verdict.

---

## Vein 4 — Cryptographic mediation

This vein gives the *ideal object* a chamber approximates and the concrete two-party
primitives for the IP-overlap anchor. Substrate-level TEE/attestation crypto lives in
the companion doc; here it's the mediation-specific constructions.

- **Canetti, "Universally Composable Security"** (FOCS 2001; updated eprint
  [2000/067](https://eprint.iacr.org/2000/067)). The **ideal functionality + simulation**
  paradigm with a composition theorem: a protocol UC-realizing `F` is safe in any
  concurrent context. **Steal — the definition to write down:** specify the chamber as
  an ideal functionality `F_chamber` that takes both corpora, computes the verdict
  internally, and leaks *only* the metered alphabet symbol to each party. Everything
  else — TEE, MPC, or trusted mediator — is then judged as "does it UC-realize
  `F_chamber` up to the stated leakage." This is the cleanest formal contract for the
  whole project.
- **Ishai, Kushilevitz, Ostrovsky, Sahai, "Zero-Knowledge from Secure Multiparty
  Computation"** (MPC-in-the-Head, STOC 2007,
  [pdf](https://web.cs.ucla.edu/~rafail/PUBLIC/77.pdf)). Turns any MPC protocol into a
  ZK proof of an NP statement. **Steal — the construction:** a chamber verdict should
  ship with an MPC-in-the-Head proof that "verdict = f(committed corpus A, committed
  corpus B)" *without* revealing the corpora — verdict-faithfulness attestation without
  a TEE trust assumption. (Faithfulness of an *LLM* verdict is still open — empty vein.)
- **Distance-Aware PSI** ([arXiv:2112.14737](https://arxiv.org/abs/2112.14737)) and
  **Fuzzy PSI** — "from secret-shared OPRF"
  ([arXiv:2604.14909](https://arxiv.org/abs/2604.14909)), "from symmetric primitives
  with logarithmic dependence on the distance threshold"
  ([arXiv:2606.15093](https://arxiv.org/abs/2606.15093)), and Fuzzy-PSI-from-fuzzy-mapping
  (ASIACRYPT 2024). Return only the pairs of items within distance δ under an Lp metric,
  in linear communication. **Steal — the primitive for the anchor:** IP overlap between
  two labs *is* a fuzzy/distance-aware PSI over embedded document/code chunks. This gives
  a metered-leakage overlap count (or thresholded yes/no) as a cryptographic verdict,
  no LLM needed for the base signal — the chamber's LLM layer sits *above* a fuzzy-PSI
  substrate.
- **Scheffler et al., "Formalizing Human Ingenuity: A Quantitative Framework for
  Copyright Law's Substantial Similarity"**
  ([arXiv:2206.01230](https://arxiv.org/abs/2206.01230)). Formal information-theoretic
  model of "substantial similarity" / independent creation for copyright.
  **Steal — the domain semantics:** this is the closest thing to a *definition of the
  quantity a chamber measures* in the IP anchor — what "overlap" legally means. Use it
  to define the verdict's target predicate so the metered symbol maps to a legally
  meaningful threshold, not an ad hoc cosine score.
- **"Inference Control for Privacy-Preserving Genome Matching"**
  ([arXiv:1405.0205](https://arxiv.org/abs/1405.0205)). Secure two-party matching with
  an explicit **inference-control** layer limiting what repeated queries reveal.
  **Steal:** the query-budget/inference-control design here is a concrete precedent for
  metering a two-party comparison — the same problem the chamber faces, in genomics.

---

## Vein 5 — LLM agents + confidential computing + bounded-disclosure verdicts

Richest on 2025–2026 arXiv, but almost entirely on *substrate* (how to run an agent in a
TEE) rather than *calculus* (bounding what its verdict leaks). The substrate half is in
the companion doc; below is what's mediation-and-verdict specific.

- **"Simulating Dispute Mediation with LLM-Based Agents (AgentMediation)"**
  ([arXiv:2509.06586](https://arxiv.org/abs/2509.06586)). First LLM-agent framework for
  legal dispute mediation, motivated explicitly by *privacy constraints* limiting
  empirical mediation study. **Steal — the use-case validation + gap:** confirms the
  demand and that privacy is the binding constraint, but it *simulates* mediation with
  full information — it does **not** confine the agent or bound disclosure. It's the
  problem statement, not a solution; the chamber is what it's missing.
- **"Can LLMs Help Decentralized Dispute Arbitration? (UMA / Polymarket)"**
  ([arXiv:2604.15674](https://arxiv.org/abs/2604.15674)). Empirically studies LLMs as
  arbiters resolving disputed markets. **Steal:** evidence on LLM-as-arbiter reliability
  and failure modes — useful for the chamber's verdict-quality calibration, and a
  reminder that the *judgment* is fallible independently of the *confinement*.
- **"Proof-of-Guardrail in AI Agents and What (Not) to Trust from It"**
  ([arXiv:2603.05786](https://arxiv.org/abs/2603.05786)). Constructs a proof that an
  agent's output satisfied a guardrail, and analyzes its trust limits.
  **Steal — the nearest attestation primitive:** this is the closest existing work to
  "attest that the verdict respected the release policy," and its "what NOT to trust"
  analysis is a ready-made list of what a chamber's verdict attestation *cannot* promise.
- **"Evidence-Bound Gateway-Path Provenance for Third-Party LLM Inference"**
  ([arXiv:2606.22560](https://arxiv.org/abs/2606.22560)). Binds an inference's output to
  a provenance path through a gateway. **Steal:** mechanism for making a verdict's
  input-provenance checkable by both parties without exposing the inputs — the receipt
  half of the chamber.
- `[already in substrate doc]` **Confidential LLM Inference across CPU/GPU TEEs**
  ([arXiv:2509.18886](https://arxiv.org/abs/2509.18886)), **AgenTEE**
  ([arXiv:2604.18231](https://arxiv.org/abs/2604.18231)), **From Agent Traces to Trust /
  FIDES** ([arXiv:2606.04990](https://arxiv.org/abs/2606.04990)). These give the
  execution substrate and agent-level IFC labels. Calculus angle: FIDES's confidentiality/
  integrity taint labels are the *runtime* enforcement of the *static* DCC/graded types
  of Vein 2 — pair them.

---

## Named empty veins (field-building opportunities)

These are searched-for and **not found** — then adversarially re-searched, which
KILLED the broad forms of veins 1 and 5 (prior art below) and left narrower
survivors. Each surviving vein is a place the chamber calculus is genuinely new.

1. **Verdict-alphabet design under a leakage budget — NARROWED.** The broad claim
   ("nobody optimizes a finite alphabet for utility under a leakage constraint") is
   FALSE: the **privacy funnel** line is exactly utility-maximization under a leakage
   constraint with alphabet-cardinality results — Makhdoumi et al.
   ([arXiv:1402.1774](https://arxiv.org/abs/1402.1774)), constrained-release mechanisms
   ([arXiv:1710.09295](https://arxiv.org/abs/1710.09295)), and Liao–Kosut–Sankar–Calmon's
   tunable/maximal-α-leakage measures ([arXiv:1809.09231](https://arxiv.org/abs/1809.09231)),
   where maximal leakage IS sup-over-g multiplicative g-leakage. What survives is the
   **game-theoretic instance**: the objective as *mediation/equilibrium value between
   strategic parties who are also the sources* (not a statistical utility functional),
   with Aybas–Turkel and DP-Bayesian-Persuasion bracketing it. Still worth proving —
   as the strategic corner of a mapped field, not virgin territory.

2. **Adaptive-composition leakage accounting for a sequence of LLM verdicts.**
   QIF has the composition law (1611.00455) and the adaptive-adversary gap (1507.05766),
   but nobody has instantiated them for *metered natural-language verdicts from a
   confined agent over a private corpus*. The bounds exist; the application to a verdict
   channel — with the collateral-leakage correction (1604.04983) for correlated corpora —
   is unbuilt.

3. **Graded-type IFC where the grade IS the g-leakage budget.**
   Graded modal IFC (2309.04324, Granule) grades by a security *lattice*; QIF measures in
   *min-entropy*. No system grades the release modality by a **leakage semiring** so the
   type checker statically discharges the same budget the QIF semantics tracks. Fusing
   Vein 1 and Vein 2 is open and squarely in reach.

4. **Cryptographic proof that a *natural-language* verdict is faithful to confined
   inputs under a declassification policy.** MPC-in-the-Head proves faithfulness of a
   *circuit*; Proof-of-Guardrail (2603.05786) proves a guardrail *fired*. Neither proves
   "this LLM verdict is the policy-permitted declassification of exactly these committed
   inputs." Verdict-faithfulness attestation for LLM judgment is empty.

5. **Leakage-bounded *and* incentive-compatible mediation — NARROWED.** "The two
   literatures never touch" is FALSE: **privacy-aware mechanism design** is a named
   subfield combining incentives with quantified privacy — McSherry–Talwar (FOCS 2007),
   Nissim–Smorodinsky–Tennenholtz ([arXiv:1004.2888](https://arxiv.org/abs/1004.2888)),
   Nissim–Orlandi–Smorodinsky "Privacy-Aware Mechanism Design"
   ([arXiv:1111.3350](https://arxiv.org/abs/1111.3350)), and the Pai–Roth survey. What
   survives: that line uses **DP on mechanisms**; nobody has done **communication
   equilibria (Myerson mediators) under a g-leakage/min-entropy budget on the mediator's
   signal** — the recommendation-vs-secret-protection combination a chamber needs.
   Deepest surviving vein, one field over from occupied ground.
