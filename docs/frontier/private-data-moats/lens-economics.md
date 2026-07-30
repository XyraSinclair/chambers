# Consult report — moat economics lens (fable subagent, 2026-07-06)

*Primary source, preserved verbatim. Adjudicated synthesis lives in
README.md of this directory. Charter: the mechanism-design economics of
generative private-data moats, mapped onto the chamber stack.*

---

# Generative Private-Data Moats on the Chamber Stack

## 1. Formal definition

### 1.1 The object

A **moat** is a stateful object `M` held inside a private world (a chamber), with an operation

```
op(M, work) → (M′, receipt)
```

subject to three conditions, all of which this stack already types:

- **Owner-private accretion.** `M′ = M ∪ σ(work, M)` where `σ` is structure produced *in-chamber* and never itself an emission. The stack's doctrine makes this free by construction: "in-chamber richness is free" — the gardener's call graphs and defect hypotheses "stay silo-local" (STORIES.md Story 6); the guardian's model of Noor never crosses (Story 7). Accretion is unmetered because it never crosses a boundary.
- **Metered egress.** The receipt is the only thing that leaves, and it is capacity-bounded: `I(receipt; M) ≤ b_op`, an exact integer-millibit coupled charge (`accountant.py` `charge_coupled`, PROTOCOL.md §"Atomic emission"), debited against the lifetime `exposure_key(source, reader)` account (PROTOCOL.md: "the one key the cross-coalition accumulation attack cannot slip past"). Cumulatively, for any reader r: `Σ_ops b ≤ C_r`, the lifetime ceiling, enforced across nodes without consensus by the lease partition (the Lean-proven global cap theorem, `chambers/lean/`).
- **Value monotonicity.** `V(M′) > V(M)` where `V(M)` is the NPV of rents: `V(M) = Σ_t δ^t Σ_r p_t(r)`, prices sustained by the gap between a reader's value for a judgement from `M` and their next-best alternative.

**Generative** requires more than monotone V. Two conditions:

1. **Compounding:** `dV/dop` is increasing in `|M|`. The marginal op is worth more when the moat is bigger — the calibration archive prices judges better, the match graph predicts edges better, the kill-list prunes more search. This is what distinguishes a moat from inventory.
2. **Distillation-resistance:** for any reader coalition R with pooled budget `C_R = Σ_{r∈R} C_r`, the best substitute `M̂` constructible from R's receipts satisfies `V(M̂) ≤ ε(C_R) · V(M)` with `ε(C_R) ≪ 1` at economically feasible budgets. Total extractable value is bounded by the cumulative metered ceiling — otherwise the moat is being sold off in installments, not rented.

The critical structural fact: **the customers fund `op`.** Every unit of work performed against `M` is paid work that leaves owner-private structure behind. "Every codebase in the garden is simultaneously mine and customer" (Story 6). A generative moat is a flywheel where the extraction channel and the accretion channel are the same transaction, with the meter guaranteeing the accretion side is unboundedly rich and the extraction side is integer-bounded.

A second structural fact unique to this stack: **the moat has a purchase ledger.** The operator accumulating cross-world structure is itself a reader — Aster "reads only typed, metered judgements, charged against its own accounts like any reader" (Story 9). So the moat's book value is a fold: cumulative exposure debits paid. And E5 (`charge-covenant/1`) plus G7 make future accumulation *refusable by the sources* — "no new authority, ever" is `cap_mbits: 0` with grandfathering by content id (COVENANT-SPEC.md §1). Moats here are purchased and covenant-bounded, not surveilled. That is the regulatory-economics differentiation of the whole stack: it converts moat-building from an adversarial fact into a priced, exit-compatible contract.

### 1.2 The meter as distillation-rate limiter — quantitative

Model extraction and knowledge distillation are, information-theoretically, channel problems: a clone of an `h`-bit structure cannot be built from receipts carrying `c < h` bits (data-processing inequality — the same DPI the repo already uses to license G14's per-hop charging as "a sound upper bound," Story 9). The stack turns the abstract channel into an exact priced one:

- A pairwise `overlap` judgement is 1,585 mbits = log₂3 bits — a trit (Story 8, deal 1).
- A full ranking of n private items is a coupled emission of log₂(n!) ordering-mbits (`cardinal_wedge/run_sort_metered.py`). Ranking 100 items ≈ 525 bits.
- Free prose is legal at the byte ceiling, 8,000 mbits/byte — "legal and maximally expensive" (design consult (2026-07-05, private) §3).

So an extraction campaign is arithmetic. Suppose the moat's decision-relevant sufficient statistic has declared entropy `h` bits — and note the stack already has this number: `subject_entropy_mbits` is the declared delta over public knowledge (G13), which is exactly the extractor-relevant `h`, since the extractor's public prior is free. Then:

- **Volume bound:** cloning needs `≥ h` bits through receipts. At 525 bits per fully-purchased ranking, cloning a 10⁶-parameter private ranking model (say 1 bit/parameter effective) needs ~1,900 complete rankings — a campaign the lifetime `(source × reader)` account renders visible as a single monotone number. "Verification-as-extraction (monthly sketch-probes as a distillation campaign) is exactly what the lifetime composition account meters" (Story 8) — d1_bounty's VEX shape.
- **Price bound (the defensibility inequality):** the moat is safe against distillation iff `P · h ≥ V(M̂)`, where `P` is the tariff per mbit. Equivalently `P ≥ V/h`: price per bit must exceed the moat's average value per bit of declared entropy. When this holds, selling receipts is selling amortized rents; when it fails, every sale is a partial liquidation.
- **The Sybil split.** G3 (reader identity fragments under shells, "L5 forever") breaks the *ceiling* `C_r` — a Sybil resets the account — but does **not** break the *price*: every shell still pays `P` per mbit. Hence a sharp mechanism-design theorem-shape (CONJECTURE, but forced by the register's own rows): **ceilings defend against harm concentration and relationship abuse; only prices defend against distillation, because only prices survive Sybil.** This is why G3's row already says "make the price visible on every receipt." Any moat whose defense story leans on ceilings alone is Sybil-soluble.

### 1.3 Where the bound is honest vs where G2 breaks it

The bit bound `V(M̂) ≤ ε(C_R)·V` is honest exactly when value density over bits is flat. Three regimes:

- **Flat regime** (calibration tables, match priors, actuarial folds): value ≈ linear in bits, `ε(c) ≈ c/h`. The meter's bound is tight and honest. These are the structures the stack protects *well*.
- **Concentrated regime** (the "which house" bit; a single go/no-go on a drug target): an adaptive extractor chooses queries so each purchased bit is the *most valuable remaining* bit. `ε(c)` can approach 1 at c = a handful of bits. This is precisely G2 — "one bit can be catastrophic; N bits can be trivia; regret is not a predicate" — held as "a permanent conjunction with ordinal review" (SPEC §7 via the register). The economics: for concentrated moats the meter is necessary but nowhere near sufficient; defense requires G5 never-leased partitioning (zero ceiling by non-registration) and, when imported, F1 g-leakage — gain-function-indexed ceilings, "safe against EVERY attacker goal in class G" (FRAMEWORKS.md F1). Until F1 lands, concentrated-value moats are defended by partitioning discipline plus human review, and the stack says so.
- **Model regime** (the moat is a model answering a query distribution): extraction = distillation through soft labels. Empirical literature (flagged: outside-repo, citation-shaped — Tramèr et al. 2016; Orekondy et al. 2019; Carlini–Jagielski–Mironov 2020) puts query-access extraction within 1–2 orders of magnitude of original training cost for undefended APIs. The meter changes the game not by making extraction impossible but by making its *cost function* exact and its *progress* ledgered — the L3 estimator probe and F8 inspection lotteries police the one remaining hole, an estimator that undercounts (G8).

Residual leak channels the definition must carry honestly: the topology channel (G15 — "who convened whom" is unpriced metadata; "assume it leaks"), the human-head channel (L5), refusal-shape leakage (partially engineered away: attention-node charges attention *first* so "a refused ring leaks zero third-party exposure"), and estimator capture (G8). None of these break the accounting; they bound what the accounting covers.

## 2. Candidate census

Twelve candidates. Format: accumulation loop → why it compounds → what crosses → carrying primitive → what's missing.

**C1. Lifetime relationship capital — the (source × reader) accounts themselves.**
Loop: every mediated session debits `exposure_key(source, reader)`; the *history* of granted context is unreplayable. Compounds: a reader with accumulated context needs fewer marginal bits per additional unit of service (the intimacy meter — RUNTIME.md's "cumulative-exposure-as-intimacy-meter"); serving cost falls while switching cost to a fresh vendor stays at full price. Crosses: ordinary judgements; the account state itself crosses to nobody. Carried: `accountant.py` `exposure_key`, `coalition.ts` `ExposureAccount`/`ExposureDebit`, and — remarkably — `OptionValueEstimate` (coalition.ts:241) already names the unspent-ceiling-as-asset idea. Missing: the export→re-attach portability workflow (G7 residue, "implied by the data model, never exercised") and any settlement surface for pricing *remaining* budget.

**C2. Judge calibration archives priced by realized outcomes.**
Loop: every `outcome_attestation` (S9) resolving against an earlier judgement adds a (judgement, outcome) pair keyed by (judge × schema). Compounds twice: per-judge calibration improves ~1/√n (flat), but *selection* — knowing which judge to trust on which schema — compounds with catalog breadth, and the archive's pricing power grows with the ecosystem's judge population. Crosses: nothing but better-priced future judgements. Carried: `charge-settlement/2` S9/S10, bonds, Cardinal Harness's Judge Coherence Benchmark ("the exact missing machinery" for G10), `review_audit/PROBE-SPEC.md` (filed, unbuilt). Missing: E4 (schemas to key by), the G10 coherence-receipt-per-reviewer-per-epoch, and a calibration-ledger schema binding judgement id → attestation id.

**C3. Match-outcome graphs.**
Loop: every cleared intro adds an edge; every $5-if-they-talk resolution adds an outcome label (the shipped `charge-settlement/2` tier). Compounds: link prediction improves with graph density superlinearly in the relevant regime (network effect; exact exponent CONJECTURE), and denominators — "of 400 screened, 3 cleared" — are themselves proprietary priors (`matching.ts` `DenominatorPolicy`/`DenominatorSummary`). Crosses: introductions and outcome-sized payments; the graph stays home. Carried: `intro_clearing`, `matching.ts` (`MatchBounty`, `CandidateRelation`), attention-node/1, first-contact attribution. Missing: intro_clearing's contingent leg wiring (named E1 residue), receiver tariffs (E4), and G15 discipline — the operator's topology moat is simultaneously everyone else's topology *leak*.

**C4. Elicited-preference stores.**
Loop: G12's answer — "in-chamber elicitation transforms whose OUTPUTS are ordinary metered judgements" — every interaction elicits preferences the subject never articulated publicly. Compounds per-subject only until saturation; the compounding part is the cross-subject elicitation *policy* prior. Crosses: match judgements. Carried: doctrine (richness stays inside), guardian story. Missing: nothing protocol-side; the moat is operator-side model craft.

**C5. Ecosystem codebook positions — the schema catalog.**
Loop: every agent that proposes a cheaper schema that still satisfies readers registers "a discovered sufficient statistic of personality for that use"; "the meter is the training loss of the ecosystem's codebook" (design consult (2026-07-05, private) §3). Compounds: compression discoveries are cumulative and reusable across all pairs. Crosses: the schema itself — content-addressed, registered, *visible*. Carried: E4 (unbuilt), `mediation.ts` `SchemaId`, `CanonicalityReview`. Missing: E4; but see the kill-list.

**C6. Negative-knowledge archives — kill-lists, searched-and-empty maps.**
Loop: every failed in-chamber experiment, dead-end audit path, or non-reproducing technique adds a negative result. Halcyon's "negative results worth their weight in compute" (Story 8). Compounds: pruning value grows with the size of the search space competitors still face, and negative results are structurally unpublished — public data *never* catches up, by publication bias. Crosses: overlap trits (log₂3 bits: same/distinct/adjacent), "don't bother" advisories. Carried: G5 never-leased sub-sources, the Story 8 duplication check, `iptrade.ts` `NoveltyRoot`. Missing: a typed negative-result crossing whose honesty is bonded (a coverage claim is G9-shaped — the gardener's "declared coverage statements at escrow time").

**C7. Provenance royalty positions.**
Loop: every downstream derivative consuming your silo's judgements adds a royalty edge — Ravi's source royalty (Story 6), "G14 as economics." Compounds: like an early patent position in a growing citation DAG — ecosystem growth multiplies terminal readers per upstream source. Crosses: the royalty flows themselves. Carried: the ledger already stores the DAG ("leaf charges name their sources"), F6 Shapley/Myerson as the declared split rule. Missing: G14's audit family (convict a coupled set that dropped a source) — without it royalty positions are "orchestrator discipline, not law," i.e., unenforceable.

**C8. Court files as underwriting data.**
Loop: every settled escrow the operator hosts adds an (escrow shape, dispute pattern, default/slash outcome) record; the settlement2 attack lane (F9 import) even generates labeled adversarial cases. Compounds: classical actuarial — loss-history advantage grows with book size, and bond pricing (`min_bond_ucr ≥ amount/quorum`, SETTLEMENT-SPEC §11.1) demands exactly this data. Crosses: quotes and bonds. Carried: settlement/1+/2 folds, S-codes, `iptrade.ts` `SlashableBond`, F14 (bond insurance — "blocked behind multi-issuer netting," G11). Missing: F14 and netting; also note charge-scope/1 cuts *against* this moat deliberately — scoped courts mean the host no longer sees everything by default.

**C9. Attention-response models — the guardian's model of the principal.**
Loop: every ring plus glad/neutral/noise tap trains the admission policy "at the sender's expense." Compounds: weakly per-principal (bounded human state, drift); the cross-principal admission prior compounds. Crosses: deliveries and forfeited premiums. Carried: attention-node/1 (shipped), the attention key family, Story 7. Missing: nothing — and that's the problem; see kill-list.

**C10. Reputation stakes and issuer refusal histories.**
Loop: every clean epoch, every ledgered refusal, every unslashed bond extends the track record ("the reputation surface the Ethereum test demands," Story 9; F12). Compounds: slowly, as repeated-game capital. Crosses: it *is* the crossing — that's the kill.

**C11. Entropy-pool liquidity — anonymity-set capital.**
Loop: every session routed through the operator's `EntropyPool` (`mediation.ts:174`) enlarges the achievable anonymity set for all; frontier-lab settlement "clears through an EntropyPool because the direction of dependence is itself market-moving" (Story 8). Compounds: pure network effect on *flow*. Missing: the G15 batching/padding machinery itself.

**C12. Estimator red-team archives.**
Loop: every successful achieved>charged demonstration (the L3 standing bounty, Story 9's meta-economy; `test_settlement2_attacks.py` caught a real S9 bug on arrival) adds an attack pattern. Compounds like security knowledge. Carried: the private egress harness, F8/F9 lanes.

## 3. The kill-list

Gauntlet: a candidate dies if (a) public data catches up, (b) it's simulable at lower cost — especially under the question's own premise that AI capability is commodity, or (c) it doesn't compound as *stock*.

**KILLED — C5, the codebook, as a private moat.** The schema catalog is content-addressed and registered; a schema that clears cheap is *visible by construction* — that's its point ("publish the gradient and let agents compress"). The compression discoveries are commons, deliberately. What remains private is which schemas clear at what prices for whom — but that's C8's fold data, not a codebook position. The codebook is infrastructure the venue operator benefits from as *flow* (C11-shaped), not ownable stock. Killing this one matters because "the meter is the training loss of the ecosystem's codebook" is the repo's most seductive moat-shaped sentence, and the moat it names belongs to the ecosystem, not to any owner.

**KILLED — C9, attention-response models.** The protocol is *engineered to weaken this moat*: fiduciary legibility makes the guardian's income auditable, covenant/exit (E5, G7) makes leaving mechanical, per-principal state is small and drifting, and "leaving the vendor is G7's export" is named in the story. A moat the protocol's own exit story dismantles is a service business, not a moat. Correct to build as revenue; dishonest to underwrite as defensibility.

**KILLED — C10, reputation stakes.** Fails the *private-data* test totally: the court file is the reputation, and it is public/scoped-shareable by design. It's a commitment asset (F12), real but replicable by any entrant willing to post bonds and wait. Commodity-trust-with-extra-steps.

**KILLED — C12, red-team archives.** Dies on the question's own premise: when AI writes all code, adversarial probe generation is commodity compute. The archive's half-life is one frontier-model generation. (The *bounty flow* is a fine business; the stockpile isn't a moat.)

**KILLED as stock, kept as complement — C11, entropy-pool liquidity.** It never accumulates structure; stop the flow and the anonymity set evaporates same-day. This is exchange-liquidity economics: winner-take-most, real, but a *flow* moat that belongs in the venue business case, not the data-moat portfolio. It is, however, the load-bearing complement: without G15 padding, every stock moat above leaks through topology.

**DEMOTED — C4, elicited preferences.** Per-subject it saturates and is exit-portable by G7's own direction; public revealed-preference data is enormous and AI inference over it is commodity. The surviving kernel — the cross-subject prior — is only defensible where it's outcome-labeled, which makes it a sub-case of C3. Merged.

**DEMOTED — C7, provenance royalties.** Until G14's audit family exists, royalty positions are unenforceable etiquette; and even after, the position is a *rights* portfolio whose value depends on holding a generative silo upstream — i.e., C6 or C2 wearing a financial hat. Kept as the monetization layer of survivors, not a standalone moat.

**SURVIVED:** C1 (relationship capital), C2 (judge calibration), C3 (match-outcome graphs + denominators), C6 (negative knowledge — with one sharpening: it survives only where the underlying experiment is expensive relative to commodity compute: wet lab, training runs, human trials, live-system security findings; negative knowledge about cheap experiments depreciates to the cost of re-running them), C8 (underwriting folds — the slowest but the classic).

One cross-cutting depreciation law binds all survivors: **G13 applies to moats, not just declared entropy.** `subject_entropy_mbits` is a delta over public knowledge and "efficiency-technique half-lives [are] under a year" (Story 8). Every `h` in the defensibility inequality `P·h ≥ V` is shrinking; a generative moat must satisfy `d|M|/dt · value-per-bit > depreciation` or it's a melting ice cube with a meter on the door. The moats that survive the gauntlet are exactly those whose accumulation is *outcome-labeled reality* (C2, C3, C8) or *structurally unpublishable* (C6) — categories where public catch-up is slow by construction, not by hope.

## 4. The portfolio: build these three first

Ranking function: compounding rate × defensibility × time-to-value, each argued with denominators.

### First: C3 — the match-outcome graph, on the machines that shipped this week

**Time-to-value: highest on the board.** Every required mechanism is green as of 2026-07-06: attention-node/1 serves the notify economy (`POST /v1/notify`, payee = bell's owner), charge-settlement/2 prices the outcome leg ($5-if-they-talk, 12-scenario corpus, Lean bond conservation). The named residue is a sim change, not a protocol gap: "wire intro_clearing's contingent fee leg onto the shipped mechanism" (since landed: the party lane). **Compounding:** each cleared intro adds an outcome-labeled edge; edges are the scarce complement to the commodity (AI matchmaking inference is free; *ground truth about which private-world pairings worked* is purchasable only here). **Defensibility:** the labels are generated by the operator's own settlement flow — a competitor must replicate the flow, not scrape the data; flat-regime value density means the millibit bound is honest; the outputs sold (introductions) carry ~log-bits each while the graph grows by full edges.
**Protocol demands (register-style):**
- **E1-residue** (named): intro_clearing contingent-leg wiring.
- **M1 — the operator is a subject** (new gap, G4-adjacent): the match graph is information *about* participants held *by* the operator; G4 ("subject ≠ owner... do not improvise") applies to the moat-holder itself. Needs: the operator's own aggregate-prior formation declared as in-chamber work under G12 doctrine, with subjects' covenant rights (E5) reaching it.
- **G15 build-out**: without batch/pad cadence, selling the graph's outputs leaks the graph's shape; the moat's exhaust is the attack surface.

### Second: C2 — the judge calibration archive

**Compounding rate: highest of the survivors.** Selection value compounds in *two* denominators simultaneously — judges × schemas — and the ecosystem's growth (more judges, more schemas via E4) raises the value of every existing calibration point (`dV/dop` increasing in |M|, the definition's clean case). It is also the moat the stack is *uniquely* positioned to hold: calibration requires binding judgement receipts to later outcome attestations under a court whose integrity is machine-checked — nobody outside this artifact discipline can produce trustworthy (judgement, outcome) pairs at scale. **Defensibility:** outcome labels are settlement facts; public benchmarks measure public tasks and do not transfer to private schemas. F5's own novel constraint is the moat's tailwind: "every additional judge is a READER: the mechanism's own redundancy is metered leakage" — redundant judging is *expensive for everyone*, so the archive that lets you buy *fewer, better* judgements has priced scarcity built into the substrate.
**Protocol demands:**
- **E4** (exists in register, leads the queue): schemas are the key axis; no catalog, no keying.
- **Cardinal adoption #1** (filed): the G10 coherence receipt per reviewer per epoch — `review_audit/PROBE-SPEC.md` is the first artifact.
- **M2 — calibration ledger** (new row, E4/G10 junction): a content-addressed record kind binding judgement id → outcome-attestation id per (judge × schema), with the F5 question stated as its non-claim: whether IC bonuses survive the leakage cost of judging redundancy — "the register's best original research prompt."

### Third: C6 — the negative-knowledge archive, instantiated as the D1 security-research wedge

**Alignment:** the repo's own build-first decision (cooperative-economy-atlas: "D1, third-party security research, wedged into one CRA-regulated PSIRT design partner") is *exactly* a negative-knowledge moat: which attack surfaces were swept and found empty, which vuln reports are duplicates, which mitigations failed — outcome-labeled by pay-on-repro, which "needs no outcome attestation: the reproduction verdict IS a ChargeEvent" (Story 8's mechanical-oracle closure; "wedges should be chosen for mechanical oracles," Story 6). **Defensibility:** structurally unpublishable (nobody publishes clean-sweep results), expensive to regenerate (live-system findings, not cheap sims — passing the sharpened gauntlet), and the duplication check (the overlap trit) sells the moat's *existence* at log₂3 bits per query. **Compounding:** every engagement prunes the next one's search space; dedup value grows with the report population — a PSIRT clearinghouse's value is superadditive in members. **Concentration warning, stated honestly:** security findings are the *concentrated* value regime — one bit ("this CVE reproduces") can be the whole value — so this moat leans on G5 partitioning and ordinal review, not the meter alone; the meter prices the distillation campaign, the partition guards the crown jewels.
**Protocol demands:**
- **G13 closure** (named, direction stated): the owner-signed monotone-down re-declaration event — negative knowledge depreciates as public disclosure catches up, and the archive must re-price honestly without I7 quarantine.
- **M3 — the searched-and-empty crossing** (new row, G2/G9 junction): a typed negative-result judgement whose honesty requires a bonded *coverage* claim (what was searched, how hard) — S9/S10 machinery pointed at absence claims; without it, "we checked, nothing there" is unpriceable.
- **R2** (named, tranche item 8): the deterministic pinned runner — "the first rung a stranger's data can honestly ride" — because a PSIRT partner's artifacts are exactly a stranger's data.

### Why this portfolio and not others

C1 (relationship capital) is real but is the *substrate* all three ride on — it accrues automatically to whoever executes; it needs no separate build beyond eventually pricing `OptionValueEstimate` into settlement. C8 (underwriting) has the best 10-year shape and the worst 1-year shape: it is blocked behind F14 and G11's multi-issuer netting non-claim, and its accumulation rate is bounded by total settlement flow — it becomes buildable *because* the first three generate the folds. Sequence: C3 generates flow now on shipped machines; C2 compounds fastest once E4 exists; C6 is where the repo already decided the wedge lives. The three share one exhaust pipe — topology — so G15's padding machinery is the single common infrastructure investment, and one common depreciation clock, G13, which should ship before any moat is marketed as durable.
