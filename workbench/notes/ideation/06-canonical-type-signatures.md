# Canonical Type Signatures

The private-data work environment needs a small number of canonical type signatures before it needs a large platform. The purpose of the types is not bureaucratic neatness. The purpose is to make every boundary crossing nameable: who asked, what was granted, what ran, what it touched, what it emitted, who reviewed it, whose attention it consumed, which credits paid for it, which side channels existed, and what was finally allowed to leave.

A Chamber is a typed border around a private world. The type system should make the safe path ordinary: agents receive scoped capabilities, run inside explicit environments, write to constrained sinks, accumulate ledgers, and reach outsiders only through reviewed disclosures.

## Hard rule

Anything observable outside owner control is an emission.

That includes answers, receipts, logs, errors, timing, token counts, byte counts, filenames, paths, screenshots, progress states, retry patterns, model metadata, credit usage, refusal reasons, and the fact that a follow-up was allowed. Each emission is either blocked, bucketed, charged, reviewed, retained owner-only, or named as a non-claim.

The canonical signatures should therefore optimize for three things:

1. **low-capacity default output**: booleans, enums, buckets, sketches, hashes, and owner-internal pointers before prose;
2. **auditable computation**: every grant, run, artifact, review, release, and override has stable identity and provenance;
3. **attention preservation**: owner and steward attention is a scarce security boundary, not an infinite UI resource.

## Type ladder

These are layers of abstraction, not implementation phases.

### Level 0: atoms

Opaque identifiers, hashes, timestamps, buckets, and visibility labels. Nothing human-meaningful leaks through an id unless deliberately dereferenced inside the owner boundary.

```ts
type Brand<T, B extends string> = T & { readonly __brand: B };

type ChamberId = Brand<string, "ChamberId">;
type OwnerId = Brand<string, "OwnerId">;
type PrincipalId = Brand<string, "PrincipalId">;
type AgentId = Brand<string, "AgentId">;
type RunId = Brand<string, "RunId">;
type GrantId = Brand<string, "GrantId">;
type ArtifactId = Brand<string, "ArtifactId">;
type ReviewId = Brand<string, "ReviewId">;
type ReleaseId = Brand<string, "ReleaseId">;
type BudgetId = Brand<string, "BudgetId">;
type EventId = Brand<string, "EventId">;
type DataSourceId = Brand<string, "DataSourceId">;

type Hash = `sha256:${string}`;
type Timestamp = string; // RFC3339 internally; rounded or bucketed outside owner control.
type Bits = number;

type Visibility =
  | "system_secret"
  | "owner_private"
  | "reviewer_private"
  | "agent_private"
  | "requester_visible"
  | "public";

type Bucket =
  | "none"
  | "one"
  | "few"
  | "some"
  | "many"
  | "large"
  | "unknown";

type MinimizedText = Brand<string, "MinimizedText">;
type RedactedShape = Brand<string, "RedactedShape">;
type JsonPath = string;

interface TimeWindow { startsAt: Timestamp; endsAt: Timestamp; }
interface RetentionPolicy { retainRawUntil?: Timestamp; retainMinimizedUntil: Timestamp; deleteScratchAfterSeconds: number; }
interface CanaryProfile { kind: "none" | "string" | "paired_silo" | "distribution_shift"; markerHash?: Hash; }
interface ScopeSelector { kind: "path_glob" | "table" | "row_filter" | "semantic_class" | "owner_label"; valueHash: Hash; }
interface ToolGrant { tool: string; verbs: string[]; maxCalls?: number; networkAllowed: boolean; }
interface NetworkPolicy { mode: "none" | "model_broker_only" | "egress_proxy_allowlist"; allowlist?: string[]; }
interface TmpfsMount { target: string; sizeMiB: number; noexec: true; }
interface ResourceBudget { cpuMs: number; wallMs: number; memoryMiB: number; pids: number; }
interface EnvVarPolicy { allow: string[]; deny: string[]; redactValues: true; }
interface SecretPolicy { mode: "none" | "brokered" | "explicit_mount"; secretIds: string[]; }
interface LogPolicy { stdout: Visibility; stderr: Visibility; maxBytes: number; redactBeforePersist: boolean; }
interface ExecutionPolicy { envRecipeId: string; resourceBudget: ResourceBudget; toolBudget: ToolGrant[]; }
interface ReviewPlan { preflight: number; release: number; independence: "same_pool_ok" | "separate_roles" | "separate_models"; }
interface RiskScore { severity: 0 | 1 | 2 | 3 | 4 | 5; likelihood: 0 | 1 | 2 | 3 | 4 | 5; mitigated: boolean; }
interface ExposureSummary { sawRawPrivateData: boolean; dataClasses: DataClass[]; granularity: "none" | "metadata" | "aggregate" | "snippet" | "full"; }
interface ProvenanceEdge { from: DataSourceId | ArtifactId; to: ArtifactId; granularity: ExposureSummary["granularity"]; transform: string; }
interface ProvenanceSummary { sourceClasses: DataClass[]; highestGranularity: ExposureSummary["granularity"]; uniqueEpisodeRisk: boolean; }
interface ModelRef { provider: string; modelClass: string; exactModelOwnerPrivate?: string; }
type PublicFieldClass = "boolean" | "enum" | "bucket" | "sketch" | "aggregate_table" | "capped_text";
interface PublicField { path: JsonPath; fieldClass: PublicFieldClass; valueShape: RedactedShape; capacity: Bits; }
```

### Level 1: actors and authority

Principals are not just users. They include owners, requesters, sponsors, workers, reviewers, auditors, tools, model brokers, and offices. Authority flows through grants, not vibes.

```ts
type ActorKind =
  | "owner"
  | "requester"
  | "sponsor"
  | "worker_agent"
  | "reviewer_agent"
  | "human_reviewer"
  | "auditor"
  | "tool"
  | "model_broker"
  | "system";

interface ActorRef {
  id: PrincipalId;
  kind: ActorKind;
  displayClass: "named_owner" | "pseudonymous" | "opaque";
  trustTier: "owner_internal" | "admitted_guest" | "market_guest" | "red_team" | "system";
}

interface OfficeAppointment {
  office:
    | "retriever"
    | "decomposer"
    | "worker"
    | "privacy_steward"
    | "truth_reviewer"
    | "release_screener"
    | "treasurer"
    | "auditor"
    | "red_team";
  holder: ActorRef;
  agentHash?: Hash;
  scope: ScopeRef[];
  canSubdelegate: boolean;
  expiresAt: Timestamp;
  revokedAt?: Timestamp;
}
```

The institution can become complex, but revocation must stay legible. If an owner cannot answer “who currently has authority to do what near my private context?”, the type system failed.

### Level 2: private context and scopes

A dataset is not raw data access. It is a catalog of sources, mock views, synthetic previews, sensitivity labels, owner-private locators, and allowed use.

```ts
type DataClass =
  | "private_text"
  | "private_metadata"
  | "contact"
  | "credential"
  | "local_path"
  | "behavioral_history"
  | "financial"
  | "medical"
  | "work_product"
  | "public_reference"
  | "synthetic";

interface ScopeRef {
  id: string;
  chamberId: ChamberId;
  label: string;                 // owner-visible; requester gets a coarse class only.
  sensitivity: "low" | "medium" | "high" | "special";
  sourceClasses: DataClass[];
  selectors: ScopeSelector[];
  prohibitedSelectors: ScopeSelector[];
  ownerPrivateLocator?: string;  // never requester-visible.
  opaqueMountName?: string;      // e.g. /chamber/input/source/00017.
}

interface PrivateContextSource {
  id: DataSourceId;
  chamberId: ChamberId;
  sourceClass: DataClass;
  ownerPrivateLocator: string;
  exposedAs: "opaque_id" | "synthetic_preview" | "aggregate_only" | "owner_only";
  sensitivity: ScopeRef["sensitivity"];
  canaryProfile?: CanaryProfile;
  retention: RetentionPolicy;
}

interface MockView {
  sourceId: DataSourceId;
  viewKind: "schema_only" | "synthetic_rows" | "summary_stats" | "redacted_sample";
  artifactId: ArtifactId;
  leakageEstimate: LeakageEstimate;
}
```

The product should make mock views first-class. Guests can inspect schemas, synthetic examples, sensitivity labels, and allowed outputs without receiving raw private context.

### Level 3: grants and environment recipes

The environment is a durable object. It is not a shell command with good intentions.

```ts
interface ChamberGrant {
  id: GrantId;
  chamberId: ChamberId;
  ownerId: OwnerId;
  grantee: ActorRef;
  agentHash: Hash;
  allowedImageDigests: Hash[];
  allowedScopes: ScopeRef[];
  allowedSchemas: string[];
  allowedTools: ToolGrant[];
  envPolicy: EnvPolicy;
  sinkPolicy: SinkPolicy;
  egressBudget: EgressBudget;
  attentionBudget: BudgetId;
  creditPool: BudgetId;
  validFrom: Timestamp;
  expiresAt: Timestamp;
  revokedAt?: Timestamp;
}

interface EnvRecipe {
  id: string;
  isolation: "local_read_only" | "docker_rootless" | "podman_rootless" | "firecracker" | "gvisor" | "k8s_job";
  imageDigest?: Hash;
  entrypoint: string[];
  user: { uid: number; gid: number; noNewPrivileges: true };
  rootfs: { readOnly: true; tmpfs: TmpfsMount[] };
  mounts: MountSpec[];
  network: NetworkPolicy;
  resources: ResourceBudget;
  envVars: EnvVarPolicy;
  secrets: SecretPolicy;
  logs: LogPolicy;
}

interface EnvPolicy {
  allowedIsolation: EnvRecipe["isolation"][];
  requirePinnedImage: boolean;
  requireOpaquePaths: boolean;
  allowHostHomeMount: false;
  allowPackageInstallDuringRun: false;
  allowNetworkByDefault: false;
  modelAccess: "none" | "broker_only" | "direct_provider_allowed_by_exception";
}

interface MountSpec {
  sourceSnapshot: Hash | DataSourceId;
  target: string;
  mode: "ro" | "wo" | "tmpfs";
  exposeFilenames: boolean;
  allowGlobs?: string[];
  denyGlobs?: string[];
}
```

Production should never mount `$HOME`, browser profiles, SSH directories, cloud config, package caches, git credentials, or agent auth into guest workers. If a local demo temporarily uses a read-only workspace, that is a product sketch, not the safety primitive.

### Level 4: transforms and sinks

A transform is a contract: input policy, execution policy, output schema, sink, and review route. The worker does not “answer a prompt.” The worker writes a typed candidate into a constrained sink.

```ts
interface AgentRecipe {
  hash: Hash;
  sourceRef: string; // repo+commit, uploaded bundle, prompt template, WASM module.
  manifest: AgentManifest;
  admissionReviewIds: ReviewId[];
}

interface AgentManifest {
  name: string;
  version: string;
  declaredPurpose: string;
  entrypoint: string[];
  outputSchemaId: string;
  requestedTools: ToolGrant[];
  requestedNetwork: NetworkPolicy;
  maxRuntimeSeconds: number;
  maxMemoryMiB: number;
  claims: string[];
}

interface TransformSpec {
  id: string;
  chamberId: ChamberId;
  requester: ActorRef;
  trustedWrapper: string;
  untrustedRequesterText: string;
  purpose: string;
  inputPolicy: InputPolicy;
  executionPolicy: ExecutionPolicy;
  outputPolicy: OutputPolicy;
  sinkPolicy: SinkPolicy;
  reviewPlan: ReviewPlan;
}

interface InputPolicy {
  allowedScopes: ScopeRef[];
  prohibitedScopes: ScopeRef[];
  allowedGranularity: "metadata" | "aggregate" | "search_hit" | "snippet" | "full_read";
  requireMockFirst: boolean;
  canRevealSourceLocators: false;
}

interface OutputPolicy {
  schemaId: string;
  freeText: "forbidden" | "owner_internal_only" | "release_review_required";
  maxBytes: number;
  maxWords?: number;
  allowedFieldClasses: PublicFieldClass[];
  forbiddenFieldClasses: RiskClass[];
  exactCountsAllowed: false;
  sourceListsAllowed: false;
}

interface SinkPolicy {
  durableChannel: "typed_annotation" | "owner_internal_text" | "release_candidate";
  schemaId: string;
  ownerOnlyFields: string[];
  potentiallyReleasableFields: string[];
  scanProfiles: string[];
  maxCapacityBits: Bits;
}
```

The design bias is owner-visible structure first, external prose last. A useful worker should be able to produce valuable claims, objections, comparisons, risk flags, evidence cards, sketches, and calibrated uncertainty without receiving permission to narrate private life outward.

### Level 5: runs, artifacts, and event ledgers

The run ledger is the institutional memory. It must be append-only in spirit even if the first implementation is JSONL on disk.

```ts
type RunStatus =
  | "created"
  | "preflight"
  | "awaiting_owner_execution"
  | "scheduled"
  | "running"
  | "worker_done"
  | "release_review"
  | "awaiting_owner_release"
  | "released"
  | "owner_visible_only"
  | "rejected"
  | "revoked"
  | "error";

type Gate =
  | "submit"
  | "static_scan"
  | "preflight"
  | "owner_execution"
  | "worker"
  | "release_review"
  | "owner_disclosure"
  | "post_release";

interface RunRecord {
  id: RunId;
  chamberId: ChamberId;
  grantId: GrantId;
  transformSpecId: string;
  envRecipeId: string;
  status: RunStatus;
  currentGate: Gate;
  requester: ActorRef;
  owner: ActorRef;
  parentRunId?: RunId;
  followupRunIds: RunId[];
  eventIds: EventId[];
  artifactIds: ArtifactId[];
  reviewIds: ReviewId[];
  releaseId?: ReleaseId;
}

interface ArtifactRef {
  id: ArtifactId;
  runId: RunId;
  kind:
    | "prompt"
    | "stdout"
    | "stderr"
    | "typed_output"
    | "release_candidate"
    | "review"
    | "scan"
    | "receipt"
    | "debug";
  visibility: Visibility;
  sha256: Hash;
  storageUri: string;
  provenance: ProvenanceEdge[];
  redactionState: "raw" | "deterministically_redacted" | "review_redacted" | "public_minimized";
  retention: RetentionPolicy;
}

interface ChamberEvent<K extends string = string> {
  id: EventId;
  kind: K;
  runId: RunId;
  chamberId: ChamberId;
  at: Timestamp;
  actor: ActorRef;
  gate: Gate;
  surface: Surface;
  visibility: Visibility;
  causalParentIds: EventId[];
  summary: MinimizedText;
}
```

A raw event log is not automatically shareable. There should be at least three projections: owner-forensic bundle, reviewer bundle, and requester receipt bundle.

## Attention as a typed security resource

Human attention is part of the boundary. A system that interrupts the owner too often will train rubber-stamping. A system that hides too much will silently govern. The type signatures should make attention spend visible and make exhausted attention fail closed for disclosure.

```ts
type AttentionReason =
  | "owner_execution_escalation"
  | "release_decision"
  | "high_risk_override"
  | "budget_threshold"
  | "incident"
  | "appeal"
  | "routine_receipt";

interface AttentionBudget {
  id: BudgetId;
  human: ActorRef;
  window: TimeWindow;
  maxInterruptions: number;
  maxReviewCards: number;
  maxDetailExpansions: number;
  maxHighRiskOverrides: number;
  exhaustionPolicy: "fail_closed_disclosure" | "defer_low_risk" | "batch_notifications";
}

interface ReviewCard {
  id: ArtifactId;
  runId: RunId;
  gate: Gate;
  decisionNeeded: "approve_execution" | "reject_execution" | "approve_release" | "redact" | "override";
  minimalFacts: MinimizedText[];
  risk: RiskVector;
  proposedVisibleFields: string[];
  expansionArtifactId?: ArtifactId;
}

interface AttentionDebit {
  budgetId: BudgetId;
  runId: RunId;
  human: ActorRef;
  reason: AttentionReason;
  interruptions: number;
  reviewCards: number;
  detailExpansions: number;
  minutesBucket: Bucket;
  cognitiveLoad: "low" | "medium" | "high";
}
```

The UI implication is sharp: show the smallest safe review card first. Expanding raw details is itself an exposure event. Publishing cannot depend on a tired implicit approval.

## Side-channel ledger

Side channels are not comments in a threat model. They are typed observations.

```ts
type Surface =
  | "requester_result"
  | "requester_status"
  | "owner_console"
  | "agent_prompt"
  | "agent_stdout"
  | "agent_stderr"
  | "run_artifact"
  | "server_log"
  | "browser"
  | "network"
  | "notification";

type SideChannelKind =
  | "timing"
  | "token_count"
  | "byte_count"
  | "word_count"
  | "exact_count"
  | "path"
  | "filename"
  | "log_line"
  | "model_metadata"
  | "tool_metadata"
  | "screenshot"
  | "browser_history"
  | "network_endpoint"
  | "cache_key"
  | "ordering"
  | "retry_pattern"
  | "repeated_query"
  | "error_shape";

interface SideChannelObservation {
  kind: SideChannelKind;
  runId: RunId;
  surface: Surface;
  actor: ActorRef;
  valueShape: RedactedShape;
  precision: "exact" | "rounded" | "bucketed" | "suppressed";
  audience: ActorRef[];
  linkableTo?: ArtifactId | RunId | ReleaseId;
  mitigation: "none" | "bucketed" | "delayed" | "redacted" | "padded" | "blocked";
  estimatedLeakage: LeakageEstimate;
  releaseBlocking: boolean;
}
```

Default treatments:

- requester status is coarse and optionally delayed;
- exact timestamps, runtimes, token counts, retry counts, and cache hits stay owner-private;
- paths and filenames are virtualized before worker access;
- stdout, stderr, stack traces, and dependency errors are owner-private artifacts;
- screenshots and browser/network traces are disallowed unless explicitly granted as high-risk data sources;
- repeated follow-ups are scored against prior receipts and visible artifacts.

## Entropy and capacity

The system should not overclaim mathematical privacy. Still, every output shape should carry a crude capacity estimate. The estimate is a policy instrument and market signal, not a proof of secrecy.

```ts
interface EgressBudget {
  id: BudgetId;
  maxBitsPerRun: Bits;
  maxBitsPerGrant: Bits;
  maxBitsPerAudience: Record<string, Bits>;
  repeatedQueryCompositionWindowDays: number;
  freeTextAllowed: boolean;
}

interface CapacityEstimate {
  schemaBits: Bits;
  textBitsUpperBound: Bits;
  metadataBits: Bits;
  sideChannelBits: Bits;
  cumulativeBits: Bits;
  qualitative: "none" | "negligible" | "bounded" | "material" | "unsafe" | "unknown";
  assumptions: MinimizedText[];
}

interface LeakageEstimate {
  qualitative: CapacityEstimate["qualitative"];
  bitsBucket?: Bucket;
  uniquenessRisk: "common_pattern" | "small_group" | "unique_episode" | "unknown";
  compositionRisk: "single" | "accumulates_with_prior_receipts" | "repeated_query_attack" | "unknown";
  sideChannelClasses: SideChannelKind[];
}
```

One bit a thousand times is not “only one bit.” Capacity composes across schemas, targets, agents, requesters, audiences, and time. The ledger should reward agents that produce more accepted value per leaked bit.

## Token and credit pools

Credits are not just billing. They are control pressure. Separate pools prevent “we ran out of money” from becoming “skip the release review.”

```ts
interface CreditPool {
  id: BudgetId;
  chamberId: ChamberId;
  owner: ActorRef;
  sponsor?: ActorRef;
  purpose: "preflight" | "worker" | "release_review" | "audit" | "human_review" | "payout";
  hardLimitBucket?: Bucket;
  resetWindow?: TimeWindow;
  exhaustionPolicy: "stop" | "degrade_model" | "ask_owner" | "batch" | "fail_closed";
}

interface TokenSpend {
  id: EventId;
  runId: RunId;
  poolId: BudgetId;
  model: ModelRef;
  gate: Gate;
  inputTokensBucket: Bucket;
  outputTokensBucket: Bucket;
  reasoningTokensBucket?: Bucket;
  cachedTokensBucket?: Bucket;
  costBucket?: Bucket;
  billableTo: "owner" | "requester" | "sponsor" | "system";
}

interface PayoutRule {
  paysFor: "accepted_annotation" | "accepted_release" | "accepted_review" | "caught_leak";
  metric: "owner_value" | "reviewer_acceptance" | "leakage_adjusted_value";
  slashOn: RiskClass[];
}
```

A market only works if payment attaches to accepted, bounded work rather than access, verbosity, or persuasion. Token spend belongs in the owner ledger; requester receipts should receive only coarse process claims.

## Reviews, release, and receipts

Release is declassification. It is not the last line of a worker response.

```ts
type RiskClass =
  | "secret"
  | "identifier"
  | "source_locator"
  | "exact_count"
  | "timeline"
  | "behavioral_dossier"
  | "prompt_injection"
  | "covert_channel"
  | "overclaim"
  | "side_channel"
  | "attention_fatigue"
  | "cost_abuse";

interface RiskVector {
  overall: "low" | "medium" | "high" | "blocker";
  classes: Record<RiskClass, RiskScore>;
  confidence: "low" | "medium" | "high";
  releaseBlockers: RiskClass[];
  rationale: MinimizedText[];
}

interface ReviewDecision {
  id: ReviewId;
  runId: RunId;
  stage: "admission" | "preflight" | "release" | "appeal" | "posthoc_audit";
  reviewer: ActorRef;
  verdict: "allow" | "owner_review" | "redact" | "reject";
  risk: RiskVector;
  unsafeFieldPaths: string[];
  saw: ExposureSummary;
  rationaleOwnerVisible: MinimizedText;
}

interface ReleaseCandidate {
  id: ArtifactId;
  runId: RunId;
  intendedAudience: "requester" | "sponsor" | "public" | "auditor";
  fields: PublicField[];
  provenanceSummary: ProvenanceSummary;
  leakageEstimate: LeakageEstimate;
  reviewStatus: "unreviewed" | "reviewed_clean" | "needs_redaction" | "rejected";
}

interface ReleaseDecision {
  id: ReleaseId;
  runId: RunId;
  candidateId: ArtifactId;
  reviewerIds: ReviewId[];
  ownerDecision: "approve" | "reject" | "edit" | "delegate_clean_path";
  releasedFields: string[];
  redactedFields: string[];
  cumulativeCapacity: CapacityEstimate;
  releasedAt?: Timestamp;
}

interface DisclosureReceipt {
  id: string;
  releaseId: ReleaseId;
  publicArtifactHash: Hash;
  visibleClaims: ReceiptClaim[];
  caveats: ReceiptCaveat[];
  noPerfectSecrecyClaim: true;
}
```

Receipt claims should say what happened: scoped request, preflight review, owner or clean-path execution gate, bounded worker, deterministic scans, release review, capped aggregate answer. They should not say scans prove safety, no data left, anonymity is guaranteed, or inference is impossible.

## PySyft-inspired mapping

PySyft is useful here as a mature taxonomy for governed remote computation, not as a drop-in substrate.

- PySyft **Datasite / Server** maps to Chamber runtime and service registry.
- PySyft **Dataset / Asset** maps to `PrivateContextSource`, `ScopeRef`, `MockView`, and sensitivity labels.
- PySyft **UserCode** maps to `AgentRecipe` plus `TransformSpec`.
- PySyft **Request / Change** maps to `ChamberGrant`, owner approval, and revocation.
- PySyft **WorkerPool / Job** maps to `EnvRecipe`, scheduler, and run ledger.
- PySyft **OutputService / ExecutionOutput** maps to owner-private artifacts and release candidates.
- PySyft **API service registry** maps to a Chamber control plane: typed capabilities, not arbitrary method reachability.

The key divergence: Scry should not copy a “grant read permission to output object” model as the disclosure primitive. Outputs should land in constrained sinks, then pass guardian review and owner release. Object permissions are useful internally; disclosure is a separate ceremony.

## Minimal product wedge

The smallest durable move is not a full container platform. It is a typed ledger behind the current Chamber loop.

1. Replace loose run events with `ChamberEvent` records.
2. Give every prompt, stdout, stderr, worker output, scan, review, release candidate, and receipt an `ArtifactRef` with visibility, hash, redaction state, and retention.
3. Add `ExposureRecord`: who or what saw which artifact or field, at what granularity.
4. Add `AttentionDebit`: why the owner or steward was interrupted, what they saw, and what default would have happened without intervention.
5. Add `SideChannelObservation`: timing, counts, paths, token spend, errors, and repeated-query risk.
6. Generate two bundles from the same ledger: owner-forensic and requester-minimized.

This preserves the current product shape while making future containers, worker pools, credit markets, and canary harnesses attach cleanly.

## Failure modes the types should catch

- **Review card leakage**: the owner notification itself includes a path, name, exact count, or source list.
- **Attention fatigue**: too many escalations train approval without comprehension.
- **Cost-driven safety skip**: credit exhaustion silently omits release review.
- **Receipt theater**: process language implies perfect secrecy or scan certainty.
- **Repeated-query reconstruction**: many safe-looking releases triangulate a unique episode.
- **Reviewer exposure creep**: reviewers see full transcripts when structured artifacts would suffice.
- **Debug artifact sprawl**: raw logs become support bundles or examples.
- **Model metadata leakage**: exact model/tool choices reveal hidden routing, cost, or capability information.
- **Synthetic preview laundering**: mock data is close enough to reveal real data distribution or rare cases.

A type signature cannot stop all of these. It can force each one to have a name, event, budget, reviewer, and receipt caveat.

## Product surface

The interface should make the institution visible:

- active grants and their revocation buttons;
- environment recipes and what they can touch;
- pending review cards sorted by risk and attention cost;
- cumulative egress, attention, and credit ledgers;
- side-channel observations waiting for mitigation;
- accepted annotations per leaked bit;
- release candidates and receipts by audience;
- agent offices, reputation, and incident history;
- owner-private forensic trail versus requester-visible receipt.

The user should not feel like they are chatting with a model over their private world. They should feel they are tending a bounded institution that can recruit agents, spend attention, pay for work, preserve privacy pressure, and release only what was deliberately declassified.
