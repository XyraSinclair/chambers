# Literature Provenance

> Generated from [`LITERATURE.json`](../LITERATURE.json) by
> `python3 -m chambers.literature format`. Edit the registry, not this file.

This map records which primary sources a Chambers surface is answerable to.
It is intentionally stricter than a bibliography: every entry states the
relationship, the exact import, the repository targets, and the boundary
of what the citation does **not** establish. Citation is not theorem
inheritance, implementation equivalence, or a novelty claim.

## Relationship vocabulary

- **foundation** — supplies a formal or conceptual basis used by the design.
- **adaptation** — a named mechanism or theorem pattern is translated into
  the Chambers setting.
- **implementation** — the repository directly implements or uses the cited
  standard or system.
- **comparison** — locates an adjacent mechanism without claiming adoption.
- **open-frontier** — names machinery being considered but not presently
  claimed by the implementation.

## Accountability

### Casper the Friendly Finality Gadget (2017)

Vitalik Buterin and Virgil Griffith. *Casper the Friendly Finality Gadget*. arXiv preprint arXiv:1710.09437. [1710.09437](https://arxiv.org/abs/1710.09437).

**Relationship:** `comparison`

**Applies to:** [`workbench/notes/FRAMEWORKS.md`](../workbench/notes/FRAMEWORKS.md)

**Import:** Slashing conditions are a salient example of designing violations to leave compact, transferable evidence against attributable actors.

**Boundary:** Chambers is not a consensus protocol or proof-of-stake system and inherits no finality, fault-threshold, or accountable-safety theorem from Casper.

### BFT Protocol Forensics (2020)

Peiyao Sheng, Gerui Wang, Kartik Nayak, Sreeram Kannan, and Pramod Viswanath. *BFT Protocol Forensics*. arXiv preprint arXiv:2010.06785. [2010.06785](https://arxiv.org/abs/2010.06785).

**Relationship:** `comparison`

**Applies to:** [`workbench/notes/FRAMEWORKS.md`](../workbench/notes/FRAMEWORKS.md)

**Import:** BFT forensics supplies the closest formal comparison for asking when a protocol violation necessarily leaves transferable evidence identifying culpable actors.

**Boundary:** Chambers is not BFT consensus. Detector completeness is claimed only for the exact laws formally proved or exhaustively characterized here, never by analogy to the cited protocols.

## Cryptographic Identity

### Edwards-Curve Digital Signature Algorithm (EdDSA) (2017)

Simon Josefsson and Ilari Liusvaara. *Edwards-Curve Digital Signature Algorithm (EdDSA)*. Internet Engineering Task Force, RFC 8032. [RFC8032](https://www.rfc-editor.org/rfc/rfc8032.html).

**Relationship:** `implementation`

**Applies to:** [`chambers/kernel/IDENTITY-SPEC.md`](../chambers/kernel/IDENTITY-SPEC.md)

**Import:** The identity layer implements Ed25519 verification and pins its implementation against the RFC's test vectors and strict encoding requirements.

**Boundary:** A valid signature attributes bytes to possession of a key. It does not establish a human identity, beneficial ownership, independence, or Sybil resistance.

## Differential Privacy

### Privacy Odometers and Filters: Pay-as-You-Go Composition (2016)

Ryan M. Rogers, Aaron Roth, Jonathan Ullman, and Salil Vadhan. *Privacy Odometers and Filters: Pay-as-You-Go Composition*. Advances in Neural Information Processing Systems 29:1921–1929. [Primary source](https://proceedings.neurips.cc/paper/2016/hash/58c54802a9fb9526cd0923353a34a7ae-Abstract.html).

**Relationship:** `comparison`

**Applies to:** [`workbench/notes/FRAMEWORKS.md`](../workbench/notes/FRAMEWORKS.md)

**Import:** Privacy odometers and filters provide a precise comparison for adaptive lifetime accounting and stopping rules under differential privacy.

**Boundary:** The Chambers lifetime exposure ledger is not a differential-privacy odometer: its charges are declared channel bounds, not realized DP privacy loss, and it inherits no ε,δ guarantee.

### Rényi Differential Privacy (2017)

Ilya Mironov. *Rényi Differential Privacy*. 30th IEEE Computer Security Foundations Symposium (CSF):263–275. [10.1109/CSF.2017.11](https://doi.org/10.1109/CSF.2017.11).

**Relationship:** `open-frontier`

**Applies to:** [`workbench/notes/FRAMEWORKS.md`](../workbench/notes/FRAMEWORKS.md)

**Import:** Rényi differential privacy is recorded as a candidate mechanism-derived estimator lane with tractable composition for genuinely randomized aggregate mechanisms.

**Boundary:** No current Chambers component claims differential privacy or converts an arbitrary judgement channel into an RDP mechanism.

## Distributed Systems

### Conflict-Free Replicated Data Types (2011)

Marc Shapiro, Nuno Preguiça, Carlos Baquero, and Marek Zawirski. *Conflict-Free Replicated Data Types*. Stabilization, Safety, and Security of Distributed Systems, LNCS 6976:386–400. [10.1007/978-3-642-24550-3_29](https://doi.org/10.1007/978-3-642-24550-3_29).

**Relationship:** `foundation`

**Applies to:** [`chambers/kernel/KERNEL-SPEC.md`](../chambers/kernel/KERNEL-SPEC.md)

**Import:** Convergent replicated data types supply the lineage for grow-only, order-insensitive merge under a deterministic fold.

**Boundary:** The Chambers ledger is a narrow content-addressed grow-only set. The citation does not establish availability, dissemination, network-fault tolerance, or correctness of every derived fold.

## Information Elicitation

### A Bayesian Truth Serum for Subjective Data (2004)

Dražen Prelec. *A Bayesian Truth Serum for Subjective Data*. Science 306(5695):462–466. [10.1126/science.1102081](https://doi.org/10.1126/science.1102081).

**Relationship:** `comparison`

**Applies to:** [`workbench/notes/FRAMEWORKS.md`](../workbench/notes/FRAMEWORKS.md)

**Import:** Bayesian Truth Serum is an adjacent no-ground-truth elicitation mechanism used to distinguish peer-prediction families and their information assumptions.

**Boundary:** It is not implemented by Chambers, and the citation imports neither its equilibrium assumptions nor a general certificate of truthful subjective judgement.

### Eliciting Informative Feedback: The Peer-Prediction Method (2005)

Nolan Miller, Paul Resnick, and Richard Zeckhauser. *Eliciting Informative Feedback: The Peer-Prediction Method*. Management Science 51(9):1359–1373. [10.1287/mnsc.1050.0379](https://doi.org/10.1287/mnsc.1050.0379).

**Relationship:** `foundation`

**Applies to:** [`workbench/notes/frontier/judgement-markets/peer-prediction.md`](../workbench/notes/frontier/judgement-markets/peer-prediction.md)

**Import:** Peer prediction supplies the foundational possibility of incentive-compatible elicitation without direct ground truth.

**Boundary:** The result depends on model assumptions and does not make correlation truth, prevent collusion, establish judge independence, or pay the leakage cost of redundant reports.

### Informed Truthfulness in Multi-Task Peer Prediction (2016)

Victor Shnayder, Arpit Agarwal, Rafael Frongillo, and David C. Parkes. *Informed Truthfulness in Multi-Task Peer Prediction*. 17th ACM Conference on Economics and Computation (EC '16):179–196. [10.1145/2940716.2940790](https://doi.org/10.1145/2940716.2940790).

**Relationship:** `adaptation`

**Applies to:** [`workbench/notes/frontier/judgement-markets/peer-prediction.md`](../workbench/notes/frontier/judgement-markets/peer-prediction.md), [`workbench/peer_sim/run_peer_prediction.py`](../workbench/peer_sim/run_peer_prediction.py)

**Import:** The Correlated Agreement mechanism is adapted as exact ledger arithmetic over repeated reports, with the mechanism's own redundant readership charged explicitly.

**Boundary:** Informed-truthfulness assumptions remain assumptions; correlation is not truth, collusion and permutation strategies remain live, and metered redundancy can make the mechanism infeasible.

## Monitorability

### Defining Liveness (1985)

Bowen Alpern and Fred B. Schneider. *Defining Liveness*. Information Processing Letters 21(4):181–185. [10.1016/0020-0190(85)90056-0](https://doi.org/10.1016/0020-0190(85)90056-0).

**Relationship:** `adaptation`

**Applies to:** [`chambers/kernel/PROTOCOL.md`](../chambers/kernel/PROTOCOL.md)

**Import:** The safety/liveness distinction disciplines protocol obligations: a finitely auditable court can convict safety violations, while progress obligations must be reduced to deadlines plus permissionless resolution.

**Boundary:** The citation supplies the monitorability doctrine, not a proof that every Chambers obligation has been reduced correctly or that the system guarantees liveness.

## Privacy Theory

### Privacy as Contextual Integrity (2004)

Helen Nissenbaum. *Privacy as Contextual Integrity*. Washington Law Review 79:119–158. [Primary source](https://digitalcommons.law.uw.edu/wlr/vol79/iss1/10/).

**Relationship:** `foundation`

**Applies to:** [`docs/primitives/contexts.ts`](primitives/contexts.ts)

**Import:** Context-relative transmission norms motivate representing disclosure as a typed relation among source, subject, recipient, purpose, and governing context rather than as a global private/public bit.

**Boundary:** The type system records and constrains declared context; it does not mechanically prove social appropriateness, consent, legitimacy, or justice.

## Proof Engineering

### The Lean Theorem Prover (System Description) (2015)

Leonardo de Moura, Soonho Kong, Jeremy Avigad, Floris van Doorn, and Jakob von Raumer. *The Lean Theorem Prover (System Description)*. CADE-25, Lecture Notes in Computer Science 9195:378–388. [10.1007/978-3-319-21401-6_26](https://doi.org/10.1007/978-3-319-21401-6_26).

**Relationship:** `implementation`

**Applies to:** [`chambers/lean/README.md`](../chambers/lean/README.md)

**Import:** Lean is the proof checker used for the repository's stated algebraic theorems and replayed golden facts.

**Boundary:** Lean verifies only the formal statements and assumptions encoded under chambers/lean; it does not certify the whole Python or Rust implementation, the runtime, or any deployment claim.

## Quantitative Information Flow

### The Science of Quantitative Information Flow (2020)

Mário S. Alvim, Konstantinos Chatzikokolakis, Annabelle McIver, Carroll Morgan, Catuscia Palamidessi, and Geoffrey Smith. *The Science of Quantitative Information Flow*. Springer. [10.1007/978-3-319-96131-6](https://doi.org/10.1007/978-3-319-96131-6).

**Relationship:** `foundation`

**Applies to:** [`chambers/conformance/SPEC.md`](../chambers/conformance/SPEC.md), [`docs/primitives/entropy.ts`](primitives/entropy.ts)

**Import:** Reader-relative leakage, adversarial gain, channel composition, and refinement supply the formal lineage for treating release as an information channel rather than as an informal privacy label.

**Boundary:** Chambers' integer millibit accountant is a deliberately narrower engineering contract. It meters declared channel capacity and does not inherit a theorem about downstream harm, attacker goals, or deployment coverage.

## Transparency

### Secure Untrusted Data Repository (SUNDR) (2004)

Jinyuan Li, Maxwell N. Krohn, David Mazières, and Dennis Shasha. *Secure Untrusted Data Repository (SUNDR)*. 6th USENIX Symposium on Operating Systems Design and Implementation (OSDI 04):121–136. [Primary source](https://www.usenix.org/conference/osdi-04/secure-untrusted-data-repository-sundr).

**Relationship:** `adaptation`

**Applies to:** [`chambers/kernel/SCOPE-SPEC.md`](../chambers/kernel/SCOPE-SPEC.md)

**Import:** Fork consistency motivates treating inconsistent reader histories as evidence that becomes detectable when views meet.

**Boundary:** Detection depends on cross-reader comparison or gossip. The adaptation does not promise a globally consistent view, availability, or protection against permanently isolated forks.

### CONIKS: Bringing Key Transparency to End Users (2015)

Marcela S. Melara, Aaron Blankstein, Joseph Bonneau, Edward W. Felten, and Michael J. Freedman. *CONIKS: Bringing Key Transparency to End Users*. 24th USENIX Security Symposium (USENIX Security 15):383–398. [Primary source](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/melara).

**Relationship:** `comparison`

**Applies to:** [`workbench/notes/FRAMEWORKS.md`](../workbench/notes/FRAMEWORKS.md)

**Import:** CONIKS is a comparison point for authenticated partial views and efficient user-verifiable consistency over a provider-maintained map.

**Boundary:** Chambers does not implement CONIKS, a hidden-user key directory, or its monitoring and privacy model; the citation narrows an adjacent design space.

### Certificate Transparency Version 2.0 (2021)

Ben Laurie, Erran Messeri, and Rob Stradling. *Certificate Transparency Version 2.0*. Internet Engineering Task Force, RFC 9162. [RFC9162](https://www.rfc-editor.org/rfc/rfc9162.html).

**Relationship:** `adaptation`

**Applies to:** [`chambers/kernel/SCOPE-SPEC.md`](../chambers/kernel/SCOPE-SPEC.md)

**Import:** Merkle membership and append-only consistency proofs are adapted to reader-scoped court views so served facts can be checked against a committed whole.

**Boundary:** Inclusion and consistency do not prove completeness, solvency, honest scoping, or signed-head authenticity beyond the exact guarantees stated by charge-scope/1.

## Value Attribution

### A Value for n-Person Games (1953)

Lloyd S. Shapley. *A Value for n-Person Games*. Contributions to the Theory of Games II:307–317. [10.1515/9781400881970-018](https://doi.org/10.1515/9781400881970-018).

**Relationship:** `adaptation`

**Applies to:** [`chambers/kernel/ATTRIBUTION-SPEC.md`](../chambers/kernel/ATTRIBUTION-SPEC.md)

**Import:** The Shapley value supplies the symmetric marginal-contribution allocation rule used over a declared, exactly recomputable cooperative game.

**Boundary:** The characteristic function is Chambers-specific capacity arithmetic. The resulting split is not a causal-value estimate, moral entitlement, or universal data-valuation theorem.

### Graphs and Cooperation in Games (1977)

Roger B. Myerson. *Graphs and Cooperation in Games*. Mathematics of Operations Research 2(3):225–229. [10.1287/moor.2.3.225](https://doi.org/10.1287/moor.2.3.225).

**Relationship:** `comparison`

**Applies to:** [`workbench/notes/FRAMEWORKS.md`](../workbench/notes/FRAMEWORKS.md)

**Import:** The Myerson value is the graph-aware cooperative-game comparison point for attribution over a provenance network.

**Boundary:** charge-attribution/1 implements a declared Shapley game over a Chambers-specific capacity function, not the Myerson value, unless a future spec says otherwise.
