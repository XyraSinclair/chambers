# Judgement program for Scry Chambers type signatures

Scry Chambers needs beautiful primitives, but "beautiful" is not an aesthetic-only property. The useful judgement is whether a primitive set makes bounded cognitive work over private worlds easier to run, safer to review, cheaper to explain, and harder to abuse. This document turns that vague target into a judgement program: a set of concrete questions, scoring rubrics, evidence cells, and decision records that can be farmed out to agents without turning the research process into folklore.

The target product shape is already narrow:

- A Chamber is a typed border around a private world.
- Agents work near private context without carrying it away.
- Every boundary crossing is named, budgeted, reviewed, paid or rejected, and remembered.
- Raw private data is not the commodity. Accepted, typed, provenance-bearing cognitive deltas are.
- No receipt may imply perfect secrecy, perfect anonymization, or impossible non-inference.

Sources used in this workspace:

- Current Chamber law and demo behavior: `chambers/CHAMBER.md` and `chambers/chamber.py`.
- Canonical type-signature lens: `workbench/notes/ideation/06-canonical-type-signatures.md`.
- Current primitive modules: `docs/primitives/{core,entropy,environment,attention,market,index}.ts`.
- Market and egress lenses: `workbench/notes/ideation/02-private-cognitive-labor-market.md`, `workbench/notes/ideation/03-egress-and-immune-system.md`.
- Prior kernel canon: the archived first-stab kernel's canon (private archive).
- Research memo and external anchors: `workbench/notes/research/canonical-type-signature-research.md` and `external-anchors/*.json` in this autoresearch folder.

## 1. The core judgement

A candidate primitive earns its place only if it answers at least one of these questions better than a payload field would:

1. **Authority**: Who had authority over what private boundary, under which grant, for which transform, at what time?
2. **Execution**: What exact agent recipe ran, with which mounts, tools, network, model access, environment claims, and runtime constraints?
3. **Output**: What did the worker emit, at what granularity, into which constrained sink, under which schema and output policy?
4. **Review**: Who saw which artifact class, which gate did they review, what decision did they make, and what risk rationale did they record?
5. **Disclosure**: Which fields crossed owner control, which fields were redacted, what caveats traveled with the release, and what non-claims were preserved?
6. **Observability**: What non-answer signals were observable: status, timing, token spend, byte count, exact count, path, filename, retry pattern, cache hit, payout, notification, leaderboard movement?
7. **Attention**: Which human attention act was consumed, why did it deserve interruption, and which lower-value cards were batched or suppressed?
8. **Economics**: Who paid, what was purchased, what was accepted, what was rejected, and did payment itself disclose anything?
9. **Reuse**: Did an accepted finding become owner-private memory, downstream input, payout evidence, or public receipt material? Under what explicit reuse edge?
10. **Liability**: Can the system reconstruct who authorized, who saw, what crossed, what was promised, and what was explicitly not promised?

If a proposed type does not sharpen one of these questions, it is probably a schema field, a UI projection, or a later market feature.

## 2. Judgement records

Use a small research algebra so future agents can contribute without inventing incompatible language.

```ts
type JudgementId = string & { readonly __brand: "JudgementId" };
type EvidenceId = string & { readonly __brand: "EvidenceId" };
type CandidateTypeId = string & { readonly __brand: "CandidateTypeId" };
type SourceRef = string; // path, URL, agent:// id, artifact:// id, or paper id.

type JudgementAxis =
  | "authority"
  | "execution"
  | "output"
  | "review"
  | "disclosure"
  | "observability"
  | "attention"
  | "economics"
  | "reuse"
  | "liability"
  | "ergonomics"
  | "implementation";

type JudgementQuestion = {
  id: JudgementId;
  axis: JudgementAxis;
  question: string;
  whyPivotal: string;
  falsifier: string;
  minimumEvidence: SourceRef[];
};

type EvidenceCell = {
  id: EvidenceId;
  source: SourceRef;
  quoteOrSummary: string;
  observedFact: string;
  supports: JudgementId[];
  contradicts: JudgementId[];
  confidence: "low" | "medium" | "high";
};

type CandidateType = {
  id: CandidateTypeId;
  name: string;
  owns: JudgementAxis[];
  mustNotOwn: JudgementAxis[];
  minimumFields: string[];
  deletionCase: string;
  abuseIfMissing: string;
};

type TypeDecision = {
  candidate: CandidateTypeId;
  decision: "core" | "module" | "field" | "projection" | "defer" | "delete";
  rationale: string;
  evidence: EvidenceId[];
  unresolved: JudgementQuestion[];
};
```

The record itself is not product API. It is a way to keep research composable: agents can submit evidence cells and candidate decisions without smuggling in unreviewed prose as authority.

## 3. Scoring rubric

Score candidate primitives on seven axes. The goal is not a weighted average; a type with a fatal 1 should be cut even if it is elegant elsewhere.

| Axis | 1 | 3 | 5 |
|---|---|---|---|
| Boundary clarity | Blurs authority, output, review, and market roles | Separates most stages but leaks responsibility into fields | One primitive owns one boundary and composes by IDs |
| Egress accounting | Treats only final answer as output | Tracks answer and some logs | Treats every observer-visible signal as an emission |
| Review ergonomics | Creates more owner prompts | Batches some review decisions | Routes only authority, disclosure, payment, and incident changes to humans |
| Market safety | Pays for access, effort, or token burn | Pays for accepted outputs but weakly controls reuse | Pays only for accepted, low-leakage, provenance-bearing deltas under explicit release/reuse rules |
| Abuse resistance | Adaptive probing, retry games, cache hits, payouts, and leaderboards leak freely | Some leakage classes are named | Every market mechanic is itself typed as an egress surface |
| Implementation fit | Requires enclaves, container fleet, or warehouse-scale migration before value | Can sidecar current demo but needs many new moving pieces | Works as append-only records around the current local Chamber loop |
| Language fit | Sounds like generic platform plumbing | Mostly preserves Chamber framing | Preserves bounded cognitive work, privacy as selective agency, and no success-shaped secrecy claims |

## 4. Pivotal judgements to run repeatedly

### J1. What is truly core?

**Question:** What records are needed in every future Chamber, including a one-off local demo, a partner silo, a bounty marketplace, and a high-assurance institutional deployment?

**Current answer:** `Principal`, `Chamber`, `Scope`, `Grant`, `Transform`, `Run`, `Artifact`, `Review`, `Release`, `ReceiptPayload`, and `LedgerEntry` are the durable spine. `CognitiveDelta` and `Settlement` are the first market extension, not the spine.

**Falsifier:** A future scenario cannot answer who authorized a run, what it touched, what emitted, who reviewed, what released, or what the receipt claims without adding another always-present record.

### J2. What is an artifact?

**Question:** Should prompts, stdout, stderr, worker outputs, release candidates, receipt payloads, scans, support bundles, attention cards, attribution reports, and market settlements all be artifacts?

**Current answer:** Yes, if they need provenance, review, retention, or release classification. The rule "everything durable is an artifact; every state transition is a ledger entry" prevents special stores that evade review.

**Falsifier:** A durable object needs lifecycle, visibility, provenance, or retention but cannot be modeled as an artifact without corrupting its meaning.

### J3. Is output schema the privacy schema?

**Question:** Can a schema-valid `CognitiveDelta` or `AgentFinding` be treated as safe to disclose?

**Current answer:** No. Output schema says what the worker was allowed to write. Privacy schema is `SinkPolicy + Review + Release + ReceiptCaveat + EgressBudget + LedgerEntry`. A well-shaped card can still leak through exact count, unique phrasing, timing, score distribution, or payout movement.

**Falsifier:** A worker output class can be released automatically across all chambers with no human/guardian review and no composition budget. This conflicts with current Chamber law.

### J4. Where does entropy belong?

**Question:** Should entropy / leakage / capacity estimates be first-class core records?

**Current answer:** Keep the core aware of observable events and visibility. Put quantitative capacity estimates in the entropy module. The product must account for side channels, but it should not pretend a rough bit budget is a proof of privacy.

**Falsifier:** Governance, attention, or market settlement cannot safely function without a first-class `EgressBudget` pointer on core `Grant`/`Run`/`Release` records.

### J5. What does the market sell?

**Question:** Does the market sell agent time, access to private context, accepted annotations, downstream utility, or reputation?

**Current answer:** The first market sells accepted, low-leakage, provenance-bearing cognitive deltas. Agents may be rewarded for useful structure that survives review. They are not paid for access, effort, broad token burn, or hidden cache reuse.

**Falsifier:** A real buyer cannot express a valuable demand without paying for private access rather than accepted output. That would mean the product promise is not yet sharp enough.

### J6. What makes owner attention scarce?

**Question:** Which events deserve owner interruption?

**Current answer:** Four events: authority changes, disclosure changes, economic changes, and incident/liability changes. Findings, quality improvements, routine low-risk rejections, and cache maintenance should become owner-visible structure, not chatty prompts.

**Falsifier:** A recurring event outside those four classes must interrupt immediately or the system becomes materially less safe.

### J7. Can PySyft be stolen conceptually without importing its storage model?

**Question:** Which PySyft ideas adapt cleanly to Scry Chambers now that the 100 TB warehouse question is out of scope?

**Current answer:** Adopt the control plane vocabulary: datasite-like owner runtime, service registry, request/approval workflow, policy-gated code, mock/private split, execution outputs, job history, blob/object provenance, and worker pools. Do not copy the object-store-as-warehouse model or assume approved Python object execution is the primary product act.

**Falsifier:** The first valuable Chamber use case requires PySyft-style Python object pointers and remote execution semantics rather than typed annotation/review/release semantics.

## 5. Atomic judgement jobs

These jobs are small enough to run repeatedly across Claude, Codex, Kimi, Gemini, or future local evaluators. Each should return evidence cells, not essays.

| Job | Prompt shape | Output | Good answer |
|---|---|---|---|
| Core deletion test | "Delete one core primitive. Which scenario breaks first?" | `TypeDecision[]` | Names a concrete broken reconstruction question |
| Side-channel inventory | "List observer-visible signals in scenario X." | `ObservableClass[]` | Includes status, timing, retry, token, byte, cache, payout, leaderboard, notification |
| Market abuse test | "How can a sponsor buy leakage without seeing raw data?" | `RiskVector[]` | Treats bounty, payout, score, queue priority, and cache reuse as emissions |
| Attention cost test | "Which cards should interrupt the owner?" | `AttentionDebit[]` | Routes only authority/disclosure/economic/incident decisions to humans |
| Review separation test | "Can the same actor request, run, review, and profit?" | `ReviewerSeparationProof[]` | Names role separation and conflict records |
| Receipt truth test | "What can the product truthfully say outward?" | `ReceiptClaim[]` + caveats | Preserves no-perfect-secrecy and no-semantic-proof caveats |
| Implementation wedge test | "What can be sidecarred onto current `chamber.py` first?" | `LedgerEntry[]` skeleton | Starts with local append-only JSONL and typed artifacts |
| Matchmaking denominator test | "Does a match reveal rarity?" | `DenominatorGuard[]` | Blocks exact denominator, rank, unique episode, and repeated-query reconstruction |

## 6. Research operating rules

1. **No general platform drift.** If a proposed primitive exists only to support arbitrary agents, arbitrary apps, arbitrary data sources, or arbitrary payments, defer it.
2. **No schema-as-safety mistake.** A schema can minimize shape; it cannot prove semantic non-leakage.
3. **No untyped observability.** Any status, cache hit, timing bucket, payout, score, queue priority, or support bundle that leaves owner control is an emission.
4. **No invisible incentives.** If an agent can profit from a behavior, that behavior must be legible to the ledger and slashable or rejectable.
5. **No owner chat treadmill.** Human attention is a boundary resource. The design should make fewer, sharper asks.
6. **No heroic reviewer fantasy.** Reviewers need small cards, risk vectors, source handles, caveats, and separation proofs. Do not make them read raw transcripts by default.
7. **No premature DP/enclave branding.** Differential privacy, TEEs, notarized receipts, and cryptographic attestations are useful only when the surrounding ledger, review, and release semantics are already honest.
8. **No access market.** The system should pay for accepted structure, not for letting agents browse private lives.

## 7. Suggested judgement queue

Run these in order when continuing the research:

1. **Deletion pressure:** for each primitive in `core.ts`, write the smallest scenario that fails if it is demoted to a field.
2. **Emission pressure:** for each scenario in the practice playbook, list every observer-visible emission and whether it is blocked, bucketed, delayed, hidden, or release-reviewed.
3. **Market pressure:** for each market primitive, name the concrete abuse if it is absent and the concrete overreach if it is core.
4. **Attention pressure:** for each owner notification, classify it as authority, disclosure, economic, incident, or batchable memory.
5. **Implementation pressure:** for each primitive, decide whether the current Python Chamber can emit it as a JSONL sidecar without changing requester UX.
6. **External anchor pressure:** for each outside paper or system, record one thing it clarifies and one reason it should not dictate the product language.

## 8. Stop rule

Stop adding primitives when these eleven records can reconstruct the product story for a run:

`Principal -> Chamber -> Scope -> Grant -> Transform -> Run -> Artifact -> Review -> Release -> ReceiptPayload -> LedgerEntry`.

Then add modules only when a scenario creates a repeated, independently governed pressure:

- `environment` for runtime recipes and resource claims.
- `entropy` for observable surfaces and capacity budgets.
- `attention` for review-card queues and interruption budgets.
- `market` for accepted deltas, bounties, reuse credit, and settlement.
- `governance/liability` only as projections over authority, exposure, decision, economic, and receipt graphs unless regulation forces dedicated records.

The beautiful system is not the one with the richest ontology. It is the one where the next agent, reviewer, sponsor, or owner cannot perform a consequential act without leaving the right small fact behind.
