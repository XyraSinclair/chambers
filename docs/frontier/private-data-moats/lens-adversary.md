# Consult report — anti-moat adversarial lens (fable subagent, 2026-07-06)

*Primary source, preserved verbatim. Adjudicated synthesis lives in
README.md. Charter: enumerate every way a generative private-data moat
dies, with PREVENTED / PRICED / RECORDED / UNPRICEABLE verdicts matched
to SETTLEMENT-SPEC §11.1's discipline.*

---

# The Anti-Moat Attack Census — how a generative private-data moat dies

Verdict key, matched to SETTLEMENT-SPEC §11.1: **PREVENTED** (mechanism convicts or forbids it), **PRICED** (not stopped, but metered and made visible — attacker pays, defender sees), **RECORDED** (happens, unstoppable and unpriceable, but leaves an attributable artifact fact), **UNPRICEABLE** (the stack has no handle; the moat dies and no accounting saves it — *do not build this shape*).

The thesis to hold throughout: **the (source × reader) lifetime exposure ledger is not a moat — it is a distillation budget.** It bounds cloneable information *per reader identity*. Every attack below is an attack on one of three things: the identity assumption under it (L5), the assumption that value scales with metered bits (G2), or the assumption that the moat's value lives *inside* the metered channel at all (substitution). The stack is strong exactly where value = crossed bits and identity is real, and theater everywhere else.

---

## (a) DISTILLATION — buy metered queries, clone the function

**The math first.** A moat implements `f: X → Y`. The stack meters, per reader, the exact integer bits crossing. So the lifetime ceiling `C` is an information-theoretic cap on what one reader can reconstruct: a clone `f̂` cannot carry more mutual information about `f` than the bits it received. This is the *one place the stack is genuinely, provably a moat* — and it is worth stating loudly because it is rare.

But the model-extraction literature sets the exchange rate, and it is brutal for low-complexity functions. Tramèr et al. (2016): a `d`-dimensional linear/logistic model extracts **exactly** in `d+1` queries. Milli/Jagielski/Carlini (2020) cryptanalytic extraction: a two-layer ReLU net with `h` units recovers functionally-equivalent weights in `O(h)` queries per neuron via critical-point search. PAC framing: a concept class of VC-dimension `D` clones to accuracy `1−ε` in `≈ D/ε` queries. **The load-bearing number is `D`, the effective complexity of the decision function — not the size of the private corpus that produced it.** Most business-valuable functions (approve/deny, toxic/safe, hire/pass, priced/mispriced) are *low-D*: a few hundred effective parameters. A few thousand metered queries clone them to 95%.

So the ceiling is a real defense **iff `C < D/ε_threshold`** — iff the moat's high-value region is high-complexity relative to the budget you're willing to sell. **Verdict: PRICED when the moat is genuinely high-D (generative structure, large latent, relationship graph); UNPRICEABLE when it is a crisp low-D decision boundary.** G2 is the whole fight and it cuts *toward the attacker* here: one decision-boundary bit can be the entire moat, and the meter charges that bit the same integer millibits as one bit of trivia. A moat whose value is "the label" sells its own extraction, receipt by receipt.

**Multi-reader / Sybil amortization (G3).** The ceiling is keyed `(source, reader)`. Split `D/ε` queries across `k` shell identities and the extractable total is `k·C`. The ceiling resets every time the reader does, and readers are declared strings on an L5 identity substrate with no proof-of-uniqueness (frontier #3). **Verdict: PRICED, not PREVENTED — and the pricing is weak.** The stack makes each shell post its bond and ledgers every crossing (the coalition audit surfaces it *under declared collusion hypotheses*), so the price is *visible*; it cannot be *stopped*. Against an adversary willing to stand up `k` shells, the per-reader ceiling is theater. This is the single most important honest admission: **distillation resistance is exactly as strong as identity, and identity is unsolved.**

**Coalition pooling of scoped views.** `k` readers each buy a *different* typed projection, pool offline. Reader-relative leakage `I(Y; S_i | K_r)` is computed per-reader-in-isolation; pooling makes the effective conditioning set the union `⋃K_r`. `coalition.ts` anticipates this — the coalition is the metric's *zero-point*, and the `(source×reader)` lifetime ledger is designed to catch cross-coalition accumulation. **Verdict: PRICED under *declared* coalition hypotheses; UNPRICEABLE under undeclared sovereign-shell pooling** (collapses to G3). The audit can convict a coalition it is told to look for; it cannot discover one hand behind two strings.

**Slow distillation (the time version).** Spread extraction across epochs to duck per-epoch budgets. Here the stack is *strong*: the exposure account is **lifetime, not per-epoch** (this is exactly the run-scoped-accumulation hole the private dogfood log caught and fixed with a pair-lifetime account). Monotone, cap-respecting under adaptive composition — the Lean odometer lemma is the real quantifier. **Verdict: PREVENTED against a fixed identity; PRICED→UNPRICEABLE the instant the attacker resets identity** (Sybil again). Note the cruel interaction with (e): slow extraction races against G13 entropy decay, so for a *depreciating* moat, time-distillation may lose to staleness on its own — the decay defends better than the ceiling does.

---

## (b) SIMULATION / SUBSTITUTION — never touch the moat at all

The deadliest family, because **the stack has no verb for it.** Every mechanism here — metering, ceilings, receipts, bonds — presupposes the adversary *queries the moat*. A competitor who synthesizes an equivalent structure from simulators, public-data catch-up, or improving foundation-model priors crosses **zero bits**, posts zero bonds, appears in no ledger. The court file is silent because nothing crossed.

- **Any static corpus: UNPRICEABLE. Do not build it.** A snapshot of facts is on a countdown — public data catches up, foundation models memorize the neighborhood, and the marginal entropy over public knowledge (the *only* thing the meter can honestly charge, per G13) trends to zero. The meter will eventually, correctly, charge ~0 mbits for projections of a corpus the world has independently reconstructed. The stack *tells you this is happening* (declared entropy is a delta over public knowledge) but cannot stop it.
- **Realized-outcome records with attestation receipts: substitution-RESISTANT.** This is the shape to build. A record that *X actually happened and here is the bonded S9 attestation* cannot be synthesized by a simulator, because the substitute cannot forge the receipts — the provenance is the moat, not the content. A competitor's synthetic "equivalent" data has no `outcome_attestation` history, no conserved bond trail, no court file. **Verdict: PRICED/PREVENTED-adjacent — substitution is defeated not by secrecy but by *unfakeable provenance*.**
- **Relationship capital: substitution-RESISTANT** for the same reason — a live, updating tie between sovereign parties (the attention accounts, the fiduciary-legible income constraint) is a *flow* another party cannot instantiate cold. But note this is resistant because it's *outside* the data, not because the stack protects it.

The design consequence writes itself and it is the most important one in this document: **moats must be flow-shaped and receipt-anchored, never stock-shaped.** The stack can only defend a moat whose value is inseparable from an attested history it uniquely holds.

---

## (c) INSIDER / OPERATOR — the plaintext problem

The runtime ladder R1→R3 is the honest core here, and RUNTIME.md does not oversell it.

- **R1 (operator-observed, WHERE THEY ARE): UNPRICEABLE against the operator.** Plaintext appears inside the run; `chamber.py` (private) records mount/tool/network/output hashes — enough to detect *tampering with the record*, nothing against an operator who reads the plaintext and walks. R1 is honest only for *your own data*. Any moat run at R1 for a *stranger's* data has an unpriced exfiltration channel = the operator. Do not sell R1 to mutually-distrusting parties.
- **R2 (reproducible-local): PRICED for integrity, UNPRICEABLE for confidentiality.** A stranger can re-run and check the output hash — this defends *correctness of the projection*, not *secrecy of the input*. It buys "the operator didn't lie about what ran," not "the operator didn't read it."
- **R3 (TEE-attested): the only rung that PREVENTS the operator-insider** — the enclave quote removes the operator from the TCB. But TCB minimization is open frontier #6, TEEs have a side-channel history, and the attestation root is itself an L5 trust object. **Verdict: R1→R3 buys a real ladder against insiders, but only R3 prevents, and R3 is not yet built.** The ladder's value is that it *names the rung each moat requires* — a moat for distrusting parties that ships at R1 is mislabeled, not defended.

**Estimator undercount (G8).** A captured estimator systematically under-charges, so the moat leaks more than the receipt says — silent moat-death by a slow leak the ledger *certifies as small*. The audit has no independent ground truth against a lying estimator. **Verdict: PRICED weakly** (`estimator_payer` declared, inadmissible when payer == paying requester; L3's steganographic probe convicts a *halved* estimator live) **→ UNPRICEABLE against a subtly-biased one.** FRAMEWORKS F7 (mechanism-derived ε) and F8 (random-audit lottery) are the priced escapes, both unbuilt. This is a genuine hole: the meter's soundness is the whole moat's soundness, and the meter trusts a declared estimator.

---

## (d) TOPOLOGY / METADATA — the moat leaks through its shape (G15)

The moat's *existence, size, and query traffic* leak even when every projection is minimized. SCOPE-SPEC §5 states it without flinching: **the scope head commits to the whole court, so proof shapes and tree size leak court cardinality to every scoped reader**, and the settlement closure leaks how many events touch a key. Session graphs broadcast who convened whom.

**Verdict: RECORDED, honestly — assume it leaks.** The stack has no cover here today; G15 is unpriced metadata by declaration. A competitor learns your moat is valuable (traffic), large (head cardinality), and heating up (session cadence) without buying a single projection. For a moat whose *interest signal itself is sensitive* (an M&A target, a candidate under diligence), the topology channel can be the whole compromise. The named-but-unbuilt defense is the EntropyPool trick (batch to cadence, pad the convened set, state the achieved anonymity set on the receipt) + FRAMEWORKS F13 (edge-DP / k-anonymity on the session graph). **Design consequence: a moat must price its own metadata, or it leaks its thesis for free.**

---

## (e) STALENESS / DECAY — negative real interest rate (G13)

"Generative moat that compounds with use" is a claim about a **positive real interest rate**: value accrues faster than entropy depreciates. G13 is the honest counter: declared entropy is a delta over *public knowledge, which moves*, and re-declaring downward hits I7 quarantine (owner-signed monotone-down re-declaration is the named-but-unbuilt fix).

**Which moats have a positive real rate?**
- **Realized-outcome + attestation history: POSITIVE.** Each new bonded outcome *adds* an unfakeable record; the public world cannot catch up to what only just happened. Compounds. **Build these.**
- **Relationship / attention capital: POSITIVE.** Cumulative-exposure-as-intimacy-meter literally compounds by construction (RUNTIME's persistent-agent design).
- **Static factual corpus: NEGATIVE.** Decays to zero marginal entropy. **Verdict: UNPRICEABLE decay — do not build.**
- **Derived-analysis corpus (models, scores): NEGATIVE and worse** — it decays *and* it distills (family a). Double-exposed.

**Verdict: the stack PRICES decay honestly (the meter charges marginal-over-public entropy, so a decaying moat visibly earns less) but PREVENTS nothing.** The discipline is the product: it will tell you your moat is rotting. It will not stop the rot.

---

## (f) LEGAL / SOCIAL — forced disclosure, subjects, defection

- **Subject ≠ owner (G4): UNMODELED → UNPRICEABLE, and it is a *liability*, not just a gap.** The moat contains facts *about* third parties who hold no account, gave no consent, and have data-subject rights (GDPR erasure, CCPA). A generative reputational/diligence moat is *built out of other people's data*. The ledger meters the owner's exposure and the reader's exposure; **the subject has no account and no erasure verb.** A right-to-be-forgotten request has nowhere to land. **Design consequence: any moat over third-party facts needs subject-indexed shadow accounts or consent-at-ingest gates — do not improvise this, and treat it as a compliance bomb, not a feature gap.**
- **Forced disclosure / regulatory open-data mandates: UNPRICEABLE by construction.** A court order or an open-data mandate compels the plaintext; no metering survives a subpoena. The stack's *own transparency* (recompute-from-bytes, the scope head) can even *aid* discovery — the receipts are evidence. RECORDED at best (you get an attributable artifact of what was disclosed).
- **Human defection (the people who generate the moat leave): PARTIALLY PRICED.** G7 is closed both halves — S8 (no issuer strands funds) and `charge-covenant/1` (exit covenants, value fails closed on broken authority). One-way widening (Lean) means what a defector already saw stays seen. But the *generative* engine walking out is UNPRICEABLE if the moat's compounding depends on their continued contribution — you keep the receipts, you lose the flow. **This is why flow-shaped moats need the flow contractually and fiduciarily bound (the guardian-at-the-bell income constraint), not just the stock ledgered.**

---

## (g) ECONOMIC — commoditization and platform capture

- **Receipt commoditization (E4 cuts both ways).** The schema catalog is designed so "the meter is the training loss of the ecosystem's codebook." That standardization is a double-edged sword the operators must see: **once every moat emits the same typed projection against the same catalog schema, the outputs become interchangeable and the moat's pricing power collapses to the marginal producer.** The receipt that proves your work is honest *also* proves it is fungible with a competitor's identically-typed receipt. **Verdict: PRICED as a market fact, but the pricing works *against* the moat** — standardization commoditizes. The escape is content that is *typed-standard in form but provenance-unique in substance* (again: attested outcomes, not generic scores).
- **Winner-take-all codebook capture: UNPRICEABLE, and structural.** Whoever controls the canonical E4 schema catalog and the L5 identity/attestor roots captures the ecosystem — the platform whose business becomes "the codebook everyone types against" is a new intermediary with soft, unpriced power (schema-admission discretion, attestor-set curation). The Ethereum-test doctrine (no unauditable discretion, legible rules) is the *stated* defense; it is a **non-claim today** — "no unauditable discretion" is owed, not shipped. **Design consequence: the schema catalog and attestor sets must be permissionless and forkable at design time, or the moat you build accrues to the platform, not to you.**

---

## THE DESIGN CONSEQUENCES — what the attack table forces, ranked by how much dies without them

1. **Moats must be flow-shaped, not stock-shaped.** *Everything in (b) and (e) dies without this.* A static corpus is UNPRICEABLE against substitution and has a negative real interest rate. Only a live, updating flow has a defensible rate. This is the master requirement; the rest are how you make a flow defensible.

2. **Moats must anchor value in attested-outcome provenance the substitute cannot forge.** *Kills the (b) substitution attack and rescues (g) from commoditization.* The moat's worth must live in bonded S9 receipts and conserved bond trails — an unfakeable history — not in content a simulator can synthesize or a competitor can emit against the same schema. Provenance is the only substitution-proof asset the stack can hold.

3. **Moats must be high-D where they are valuable, or priced as extractable.** *Kills the (a) low-D distillation death.* If the high-value region is a crisp decision boundary, the ceiling is theater (`C < D/ε`) and you are selling your own extraction. Either the moat's value is genuinely high-complexity relative to the query budget, or you must price every query as a partial sale of the function and set the ceiling below the PAC clone threshold.

4. **Moats must not depend on identity for their defense — or must ship on a proof-of-uniqueness substrate.** *Without this, (a)-Sybil, (a)-coalition, and (c)-shells all collapse the ceiling to theater.* The `(source×reader)` ledger only bounds distillation if the reader is real. Until frontier #3 exists, assume `k` shells and set budgets against the *pooled* adversary, not the per-reader one. This is the gap that silently voids the stack's single strongest guarantee.

5. **Moats must price their own metadata.** *Without this, (d) leaks the thesis for free.* Existence, size, and cadence must be padded to a declared anonymity set (EntropyPool / F13) or the topology channel gives the moat away before a single projection is bought. For interest-sensitive moats this is not optional.

6. **Moats over third-party facts need subject accounts and consent-at-ingest — or must not be built.** *Without this, (f)-G4 is an unpriced legal liability, not a gap.* A generative reputational moat built from people who hold no account and have erasure rights is a compliance bomb with no landing pad in the ledger.

7. **Moats for mutually-distrusting parties must run at R3, and be labeled by rung.** *Without this, (c) insider exfiltration is unpriced.* R1/R2 defend integrity, not confidentiality; only the TEE rung removes the operator from the TCB, and it is unbuilt. A moat mislabeled as protecting strangers at R1 has a wide-open operator channel.

8. **The schema catalog and attestor sets must be permissionless and forkable.** *Without this, (g) hands the moat to the platform.* The E4 codebook and L5 attestor roots are where winner-take-all capture happens; "no unauditable discretion" must be shipped, not promised, or the ecosystem's value accrues to whoever owns the codebook.

---

**The one-line synthesis for the operators:** the stack defends a moat that is a *flow of attested outcomes over a high-complexity function, run at R3, padded against metadata, on a real-identity substrate, over consenting subjects, against a forkable codebook.* It cannot defend a static corpus, a low-D decision function, a stock of third-party facts, or anything whose value lives outside the metered channel. Build the first. The honest verdict on the naive "generative private-data moat" — a compounding corpus you monetize by selling queries — is **UNPRICEABLE on at least three independent axes (substitution, low-D distillation, Sybil), and you should not build that shape.** Build the flow, sell the receipts, and price the identity gap you cannot close.
