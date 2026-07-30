# Orthogonal type atlas

This atlas names the type families that should survive contact with real Scry Chambers work. It is intentionally parsimonious. The product does not need a grand taxonomy of agents, datasets, models, and marketplaces. It needs a few orthogonal records that make private cognitive labor legible without turning private worlds public.

Core claim: **Scry Chambers should be a bounded institution around a private world, not a generic agent platform.** Its primitives should answer who had authority, what boundary was granted, what ran, what was emitted, who reviewed, what was released, what caveats travel with it, and what the ledger remembers.

## 0. Boundary test

A type is first-class only if it has independent lifecycle pressure:

- It needs its own ID.
- It can be created, revoked, reviewed, released, paid, retained, or audited independently.
- It participates in more than one product flow.
- It prevents a real failure mode that a payload field would hide.
- Its absence would make a consequential boundary crossing unanswerable.

Everything else should be a field, payload schema, UI projection, support file, or future extension.

## 1. The eleven-record spine

| Record | Owns | Does not own | Why it earns first-class status |
|---|---|---|---|
| `Principal` | Actors and trust domains | Permissions, jobs, payouts, identity-provider internals | Every authority, review, disclosure, and settlement needs an accountable actor or office. |
| `Chamber` | The private-world boundary and owner control plane | Raw data, arbitrary app logic, generic tenant management | The boundary is the product unit. Everything else attaches to it. |
| `Scope` | Owner-approved private terrain selectors and canaries | Worker-readable raw locators, release decisions | Lets the owner expose handles without exposing paths, table names, notebooks, people, or projects. |
| `Grant` | Capability to run a transform over scopes under policies | Worker code body, final answer, payment | Converts "agent can work here" into a revocable, auditable, time-bounded fact. |
| `Transform` | The declared bounded work: purpose, expected inputs, output schema, review plan | Runtime container, data access, reviewer decision | Makes work a product object instead of a prompt blob. |
| `Run` | One execution attempt and state machine | Artifact bodies, review decisions, release payload | Joins grant, transform, artifacts, reviews, current gate, parent run, and ledger tail. |
| `Artifact` | Durable bodies and payloads with kind, hash, visibility, provenance, retention | Semantics of approval, payment, or final truth | Everything durable is an artifact: prompts, stdout, stderr, output cards, scans, release candidates, receipts, support bundles. |
| `Review` | Gate-specific judgement over artifacts | Owner final release, worker output schema, market payout | Separates preflight, output review, entropy review, appeal, post-audit, and incident review. |
| `Release` | Owner/delegate decision over which fields cross owner control | Worker output generation, reviewer confidence, private source labels | Disclosure is a distinct act, not a side effect of a passing review. |
| `ReceiptPayload` | Outwardly safe claims and caveats | Proof of secrecy, raw evidence, complete audit log | The receipt is how the system talks without laundering risk. |
| `LedgerEntry` | Append-only transitions and emitted facts | Rich object body, mutable lifecycle state | The ledger is the accountable spine: every access, emission, review, attention debit, credit debit, release, and incident becomes reconstructable. |

This is enough to run the current local Chamber and enough to generalize later. It is not enough for bounties, side-channel accounting, or full environment receipts; those are modules that attach by IDs.

## 2. Orthogonality matrix

| Family | First-class records | Owns | Must not own | Common failure if overgrown |
|---|---|---|---|---|
| Core | `Principal`, `Chamber`, `Scope`, `Grant`, `Transform`, `Run`, `Artifact`, `Review`, `Release`, `ReceiptPayload`, `LedgerEntry` | Authority, boundary, work, artifacts, review, release, receipts, ledger | Entropy math, container details, payout mechanics, notification UX | Becomes a generic agent platform or marketplace schema. |
| Environment | `AgentPackage`, `EnvRecipe`, `MountSpec`, `ToolGrant`, `ResourceBudget`, `NetworkPolicy`, `ModelAccessPolicy`, `LogPolicy`, `EnvironmentReceiptPayload` | What the worker could touch and do | Final answer, review decision, agent reputation | Pretends runtime isolation alone is privacy. |
| Entropy / egress | `Surface`, `ObservableClass`, `ObservableEvent`, `EgressBudget`, `CapacityEstimate`, `CompositionState`, `DenominatorGuard` | Observable channels and composition pressure | Final release approval, cryptographic privacy proof | False precision; bit budgets become privacy theater. |
| Attention | `AgentFinding`, `ReviewCard`, `AttentionQueue`, `AttentionDebit`, `NotificationPolicy`, `NotificationAttempt` | Human interruption as scarce boundary resource | Product truth, owner sovereignty, worker output schema | Owner gets pelted with agent chat and learns to ignore safety prompts. |
| Market | `CognitiveDelta`, `Bounty`, `Acceptance`, `ReuseCredit`, `AttributionReportPayload`, `CreditSettlement`, `FeedSubscription` | Paying for accepted low-leakage structure | Direct access, private-data sale, public reputation by default | Marketplace rewards leakage, token burn, speed theater, or cache-hit side channels. |
| Governance / liability | `ExposureSummary`, `ReviewerSeparationProof`, `IncidentRecord`, `Appeal`, `SupportBundlePolicy` | Projections that answer authority/exposure/decision/economic/receipt questions | Parallel shadow source of truth | Bureaucracy duplicates core records and creates conflicting truth. |
| Cache / provenance | `Annotation`, `ReuseEdge`, `InvalidationRecord`, `ProvenanceEdge`, `CachePolicy` | Owner-private accepted memory and reuse lineage | Raw context replay, external cache disclosure | Model memory quietly becomes data leakage. |
| Matchmaking / consent | `TargetRelation`, `ConsentPolicy`, `DenominatorPolicy`, `BilateralRelease`, `MatchCandidate` | Multi-party disclosure choreography | Unilateral public ranking, exact rarity, hidden denominator leakage | The system reveals exactly the unusualness it was supposed to protect. |

## 3. Core algebra sketch

The implemented primitives in `primitives/core.ts` already follow this shape. The important cut is not field-perfect TypeScript; it is the record boundary.

```ts
type Principal = {
  id: Id<"Principal">;
  kind: "owner" | "requester" | "sponsor" | "worker" | "reviewer" | "auditor" | "tool" | "model" | "system";
  trustDomain: "owner" | "admitted" | "market" | "auditor" | "public";
  display: "named" | "pseudonym" | "opaque";
};

type Chamber = {
  id: Id<"Chamber">;
  owner: Id<"Principal">;
  purpose: string;
  retention: RetentionPolicy;
  defaultRelease: "owner_only" | "review_required" | "public_allowed";
};

type Scope = {
  id: Id<"Scope">;
  chamberId: Id<"Chamber">;
  ownerPrivateLocator: string;       // never requester-visible
  requesterVisibleClass: DataClass;  // e.g. calendar, repo, notes, CRM, logs
  sensitivity: "low" | "medium" | "high" | "special";
  selectorHash: Hash;
  canary?: CanaryProfile;
};

type Grant = {
  id: Id<"Grant">;
  chamberId: Id<"Chamber">;
  grantor: Id<"Principal">;
  grantee: Id<"Principal">;
  transformId: Id<"Transform">;
  allowedScopes: Id<"Scope">[];
  envRecipeId: Id<"EnvRecipe">;
  sinkPolicy: SinkPolicy;
  egressBudgetId?: Id<"EgressBudget">;
  attentionBudgetId?: Id<"AttentionBudget">;
  creditPoolId?: Id<"CreditPool">;
  valid: TimeWindow;
  revokedAt?: Timestamp;
};

type Transform = {
  id: Id<"Transform">;
  chamberId: Id<"Chamber">;
  requester: Id<"Principal">;
  purpose: string;
  expectedInputShape: InputPolicy;
  outputPolicy: OutputPolicy;
  sinkPolicy: SinkPolicy;
  reviewPlan: ReviewPlan;
};

type Run = {
  id: Id<"Run">;
  chamberId: Id<"Chamber">;
  grantId: Id<"Grant">;
  transformId: Id<"Transform">;
  status: "queued" | "preflight" | "running" | "review" | "release_pending" | "released" | "rejected" | "incident" | "expired";
  currentGate: Gate;
  parentRunId?: Id<"Run">;
  artifactIds: Id<"Artifact">[];
  reviewIds: Id<"Review">[];
  ledgerTail: Id<"LedgerEntry">;
};
```

## 4. Supporting atoms worth keeping boring

These are boring on purpose. They prevent semantic leakage by making composition possible without making every module invent its own IDs and buckets.

| Atom | Use |
|---|---|
| `Id<K>` | Branded references across records. |
| `Hash` | Content, policy, package, selector, artifact, and receipt hashes. |
| `Timestamp`, `TimeWindow`, `Seconds` | Validity, retention, timing buckets, timeouts. |
| `Bits`, `Bytes`, `Words`, `Score01` | Coarse capacity and size accounting. |
| `Bucket` | Low-cardinality reporting instead of exact values. |
| `Visibility` | `system_secret`, `owner_private`, `reviewer_private`, `agent_private`, `requester_visible`, `public`. |
| `DataClass` | Coarse requester-visible domain class, not private locator. |
| `RiskClass`, `RiskScore`, `RiskVector` | Review and release risk vocabulary. |
| `ReceiptClaim`, `ReceiptCaveat` | Outward language with explicit non-claims. |
| `Precision`, `Cadence`, `Surface` | Emission shape and temporal observability. |

Avoid clever types for things that do not matter yet. Over-typed fields are just another way to create premature platform gravity.

## 5. Environment module

The environment module answers: **what could the admitted worker touch and do?**

It should not promise confidentiality by itself. It should emit receipts, not slogans.

Minimum records:

```ts
type AgentPackage = {
  id: Id<"AgentPackage">;
  source: "repo+commit" | "upload_bundle" | "prompt_template" | "WASM_module" | "provider_agent";
  manifestHash: Hash;
  declaredPurpose: string;
  requestedNetwork: NetworkMode;
  requestedTools: string[];
  requestedModelAccess: string[];
};

type EnvRecipe = {
  id: Id<"EnvRecipe">;
  isolation: "local_read_only" | "docker_rootless" | "firecracker" | "gvisor" | "k8s_job" | "managed_connector" | "tee_claimed";
  imageDigest?: Hash;
  mounts: MountSpec[];
  network: NetworkPolicy;
  tools: ToolGrant[];
  resourceBudget: ResourceBudget;
  logPolicy: LogPolicy;
  modelAccess: ModelAccessPolicy;
  secrets: SecretPolicy;
  claims: string[];
};

type EnvironmentReceiptPayload = {
  envRecipeId: Id<"EnvRecipe">;
  runId: Id<"Run">;
  observedMounts: ExposureSummary[];
  observedNetwork: "none" | "blocked" | "allowlisted" | "unknown";
  observedToolCalls: ExposureSummary[];
  caveats: ReceiptCaveat[];
};
```

Useful PySyft inspiration: datasite/owner runtime, service registry, worker pools, request service, code execution service, blob/object stores, and output service. Useful Scry correction: approved execution is not equivalent to disclosure, and an object store is not a warehouse.

## 6. Entropy and observable egress module

The entropy module answers: **what could be inferred from everything that became observable?**

The important abstraction is not Shannon math. It is the discipline that every observer-visible surface is a channel.

Minimum records:

```ts
type ObservableClass =
  | "answer_field"
  | "receipt_claim"
  | "requester_status"
  | "owner_status"
  | "review_card"
  | "agent_prompt"
  | "agent_stdout"
  | "agent_stderr"
  | "notification"
  | "queue_position"
  | "score"
  | "timing"
  | "token_count"
  | "byte_count"
  | "exact_count"
  | "path"
  | "filename"
  | "cache_hit"
  | "payment"
  | "leaderboard"
  | "support_bundle";

type ObservableEvent = {
  id: Id<"ObservableEvent">;
  runId: Id<"Run">;
  observer: Id<"Principal">;
  surface: Surface;
  class: ObservableClass;
  precision: "exact" | "rounded" | "bucketed" | "suppressed";
  cadence: "immediate" | "delayed" | "batched" | "release_only" | "never";
  compositionKey: Id<"CompositionKey">;
  mitigation: "blocked" | "bucketed" | "padded" | "delayed" | "reviewed" | "released" | "logged";
};

type EgressBudget = {
  id: Id<"EgressBudget">;
  maxBitsPerRun?: Bits;
  maxBytesPerGrant?: Bytes;
  maxTextFields?: number;
  repeatedQueryComposition: "none" | "bounded" | "blocked";
  denominatorLeakageBlocksRelease: boolean;
};
```

Rules:

- Status pages leak. Do not give exact stage, rank, retry count, worker identity, or rejection reason to requesters by default.
- Timing leaks. Bucket or delay if the answer depends on rare private material.
- Payment leaks. A payout can reveal that a high-value private fact exists.
- Cache hits leak. External cache reuse must be explicit or hidden behind safe batching.
- Leaderboards leak. Public reputation should not expose private-work volume, domain, rarity, or specific acceptance paths.
- Token and byte counts leak. They can imply corpus size, document class, or complexity.

## 7. Attention module

The attention module answers: **which owner or steward attention act is justified?**

Do not make the owner feel like they are chatting with every worker. Make them feel like they are tending a bounded institution.

Minimum records:

```ts
type AgentFinding = {
  id: Id<"AgentFinding">;
  agentId: Id<"Principal">;
  runId: Id<"Run">;
  category: "match" | "risk" | "opportunity" | "anomaly" | "correction" | "objection";
  confidence: Score01;
  novelty: Score01;
  leakage: RiskScore;
  sinkRef: Id<"Artifact">;
  ownerVisibleByDefault: false;
};

type ReviewCard = {
  id: Id<"ReviewCard">;
  artifactId: Id<"Artifact">;
  runId: Id<"Run">;
  gate: Gate;
  decisionNeeded: "approve_execution" | "reject_execution" | "approve_release" | "redact" | "accept_finding" | "open_incident" | "payment_decision";
  minimalFacts: MinimizedText[];
  proposedVisibleFields: JsonPath[];
  expansionArtifactId?: Id<"Artifact">;
};

type AttentionDebit = {
  id: Id<"AttentionDebit">;
  actor: Id<"Principal">;
  reason: "grant_escalation" | "release_decision" | "high_value_finding" | "high_risk_finding" | "budget_exhaustion" | "incident_response" | "payment_decision";
  runId?: Id<"Run">;
  reviewCardId?: Id<"ReviewCard">;
  cost: { interruptions: number; reviewCards: number; minutesBucket: Bucket };
};
```

Four scarce owner acts:

1. Authority change.
2. Disclosure change.
3. Economic change.
4. Incident/liability change.

Everything else becomes batched memory, evaluator work, cache maintenance, or no-op.

## 8. Market module

The market module answers: **what useful structure was produced, accepted, reused, and paid for without selling access?**

The market should not appear until the core ledger can prove every run and release. It should pay for accepted deltas, not for raw access, broad effort, or token spend.

Minimum records:

```ts
type CognitiveDelta = {
  id: Id<"CognitiveDelta">;
  chamberId: Id<"Chamber">;
  runId: Id<"Run">;
  artifactId: Id<"Artifact">;
  kind: "annotation" | "objection" | "candidate_relation" | "risk_flag" | "preference_signal" | "calibration" | "quote_backed_summary" | "reconciled_timeline";
  visibility: Visibility;
  leakage: RiskScore;
  grounding: "source_handle" | "owner_verified" | "reviewer_verified" | "external_public" | "synthetic_preview";
  state: "submitted" | "accepted" | "rejected" | "quarantined" | "released" | "superseded";
};

type Bounty = {
  id: Id<"Bounty">;
  chamberId: Id<"Chamber">;
  sponsor: Id<"Principal">;
  target: TargetRef;
  acceptedKinds: CognitiveDelta["kind"][];
  acceptanceRule: Id<"AcceptanceRule">;
  payoutRule: Id<"PayoutRule">;
  maxOpenSubmissions: number;
  status: "draft" | "open" | "paused" | "closed" | "expired";
};

type Acceptance = {
  id: Id<"Acceptance">;
  deltaId: Id<"CognitiveDelta">;
  acceptedBy: Id<"Principal">;
  reviewId: Id<"Review">;
  acceptanceReason: "helpful" | "necessary" | "incisive" | "grounded" | "calibrated" | "non_leaky";
  ownerEditedBeforeReuse: boolean;
};

type ReuseCredit = {
  id: Id<"ReuseCredit">;
  sourceDeltaId: Id<"CognitiveDelta">;
  consumerRunId: Id<"Run">;
  role: "constraint" | "evidence" | "candidate" | "counterfactual" | "calibration";
  declared: true;
};
```

Market laws:

- No direct access market.
- No automatic external payout before acceptance and release/payment review.
- No hidden reuse payout.
- No public leaderboard by default.
- No exact match denominator disclosure.
- No reward for token burn alone.
- No reputation export unless release-screened and caveated.

## 9. Governance and liability projections

Most governance should be a projection over existing records, not a separate source of truth.

Five graphs should be reconstructable from IDs:

1. **Authority graph**: `Principal -> Grant -> Transform -> Run -> Gate -> Release`.
2. **Exposure graph**: `Artifact -> Visibility -> Review.saw -> ObservableEvent -> ExposureSummary`.
3. **Decision graph**: `Review -> Release -> Acceptance -> AttentionDebit -> IncidentRecord`.
4. **Economic graph**: `CreditPool -> Bounty -> Acceptance -> CreditSettlement`.
5. **Receipt graph**: `ReceiptPayload.visibleClaims -> caveats -> nonClaims -> releasedArtifactHash`.

Create dedicated governance records only when a projection needs durable lifecycle: incident, appeal, support bundle, reviewer separation proof, or regulated attestation.

## 10. Cache and provenance

Owner-private memory should be typed, accepted, and invalidatable. It should not be a model-memory fog.

Minimum records:

```ts
type Annotation = CognitiveDelta & {
  kind: "annotation" | "objection" | "risk_flag" | "preference_signal" | "calibration";
};

type ReuseEdge = {
  id: Id<"ReuseEdge">;
  from: Id<"CognitiveDelta">;
  to: Id<"Run"> | Id<"Artifact"> | Id<"Release">;
  purpose: "constraint" | "evidence" | "candidate" | "counterfactual" | "calibration";
  declaredAt: Timestamp;
  reviewerVisible: boolean;
};

type InvalidationRecord = {
  id: Id<"InvalidationRecord">;
  target: Id<"CognitiveDelta">;
  reason: "owner_edit" | "source_changed" | "policy_changed" | "incident" | "superseded" | "stale";
  ledgerEntryId: Id<"LedgerEntry">;
};
```

The cache is market memory, not model memory. It remembers accepted typed deltas, review exposure, reuse edges, staleness, and caveats. It should forget or quarantine raw context aggressively.

## 11. Matchmaking and denominator control

Matchmaking is the use case that most wants to reveal exactly what privacy wants to hide: unusual fit.

Minimum concepts:

```ts
type TargetRelation = {
  id: Id<"TargetRelation">;
  chamberA: Id<"Chamber">;
  chamberB?: Id<"Chamber">;
  targetClass: "dating" | "collaboration" | "hiring" | "grant" | "investment" | "care" | "trade";
  releaseMode: "none" | "unilateral_private" | "bilateral_reveal" | "mediated_intro" | "public_call";
};

type DenominatorPolicy = {
  id: Id<"DenominatorPolicy">;
  minimumPoolBucket: Bucket;
  hideExactRank: true;
  hideExactPoolSize: true;
  repeatedQueryLimit: number;
  allowReasonCategoriesOnly: boolean;
};

type BilateralRelease = {
  id: Id<"BilateralRelease">;
  relationId: Id<"TargetRelation">;
  partyAReleaseId: Id<"Release">;
  partyBReleaseId: Id<"Release">;
  mediatedBy: Id<"Principal">;
  receiptId: Id<"ReceiptPayload">;
};
```

Default law: no exact rank, no exact denominator, no unilateral rare-trait reveal, no repeated-query reconstruction, no match bounty payout that reveals a private preference before release.

## 12. Deletion list

Cut or demote these until repeated pressure proves otherwise.

| Candidate | Decision | Reason |
|---|---|---|
| Generic `User` | Delete | `Principal` + `TrustDomain` is more honest and less app-shaped. |
| Generic `Agent` | Field/projection | Agent is a `Principal` plus `AgentPackage`, `Grant`, and reputation projections. |
| Generic `Dataset` | Avoid | Scry has private scopes and context sources, not warehouse ownership by default. |
| Generic `Task` | Avoid | `Transform` + `Run` is more precise. |
| Generic `Message` | Avoid | Free-form messages become prompt artifacts, review cards, or notifications. |
| `PrivacyScore` | Avoid | Too easy to launder caveats into a number. Use risk vectors and receipt caveats. |
| `SafeBoolean` / `approved: true` | Avoid | Approval is scoped to gate, role, artifacts, fields, caveats, and time. |
| Public `ReputationProfile` | Defer | Reputation can leak domain, volume, rarity, or acceptance history. Start owner-local. |
| Generic `Subscription` | Defer | Feeds and bounties need emission and attention rules first. |
| `Leaderboard` | Defer | Public ranking turns private work into side-channel advertising. |
| `TEEProof` | Defer | Runtime attestation is useful only after semantic output accounting exists. |
| `DPGuarantee` | Defer | DP applies to narrow mechanisms, not arbitrary agent cognition by slogan. |

## 13. Keep / kill summary

Keep:

- Small core boundary algebra.
- Environment receipts.
- Observable surface accounting.
- Attention debits and review cards.
- Market records only for accepted deltas.
- Explicit reuse edges.
- Caveated receipts.
- Incident and appeal records as lifecycle projections.

Kill or delay:

- Generic agent marketplace platform.
- Broad app identity and tenant model.
- Warehouse-style data objects.
- Raw transcript default review.
- Public reputation defaults.
- Real-time requester telemetry.
- Exact counts, exact ranks, exact denominators.
- Hidden cache reuse.
- Automatic payout before review.

## 14. The aesthetic standard

The primitive set should feel like common law for private computation:

- terse enough to implement as append-only JSONL around `chamber.py`;
- expressive enough to support bounties, matchmaking, and institutions later;
- honest enough to say what it cannot prove;
- strict enough that every useful or harmful behavior leaves a typed trace;
- sparse enough that a maintainer can hold the whole algebra in their head.

That is the beauty standard: not maximal abstraction, but minimum durable law.
