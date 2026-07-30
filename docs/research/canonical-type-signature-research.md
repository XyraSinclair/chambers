# Canonical Type-Signature Research: Scry Chambers

## Canon status

The canonical type surface is `../primitives/` (see `../primitives/CANON.md`). This memo is the research program behind it, not a competing definition. Where signatures in this memo drift from that directory, the directory wins. Known outcomes of the reconciliation:

- This memo's `CapacityEstimate`, `Transform`, `ExposureSummary`, and the Timestamp law (exact inside owner control, bucketed outward) **won** and live in canon.
- This memo's `MoneyMicros` **lost** to `CreditMicros`; `Annotation` remains the record name with `CognitiveDelta` as its prose alias; the 8-state `Gate` (with `static_scan`) is canonical.
- The beautiful-type-systems cut (`../autoresearch/2026-06-29-beautiful-type-systems/`) contributed `RunClaim`/`RunClaimSupport` (now `../primitives/runtime.ts`), bounty targets as coarse `DataClass`es rather than scope locators, the nonempty-reviewer tuple on `Release`, and `absence` as an observable kind.

This is the pointable research memo for the type-signature work. The target is not a pretty schema dump. The target is a language for private-data labor where every boundary crossing is named, budgeted, reviewed, paid or rejected, and remembered.

The current product shape is right: a Chamber is not a generic agent platform. It is a bounded institution around a private world. The owner admits scoped work, agents operate near private context, outputs land in constrained sinks, guardians review them, the owner controls disclosure, and receipts say only what the system actually did.

## Working thesis

The canonical type system should optimize for one sentence:

> Private worlds become partially computable without becoming public.

That requires a type surface that makes these questions answerable without folklore:

- Who asked?
- Who paid?
- Who was allowed near which private scope?
- What exact agent recipe ran?
- Which environment was it given?
- What did it read, write, emit, time out on, spend, log, or retry?
- Which outputs are owner-private annotations versus release candidates?
- Which human or guardian reviewed which field at which granularity?
- Which side channels were visible to which observer?
- Which annotations were later reused and credited?
- Which release crossed the boundary, to whom, with which caveats?

The beautiful version is small at the core and ruthless at the edges. A tiny core handles identity, grants, runs, artifacts, reviews, release, and ledger entries. Specialized layers attach for side channels, attention, bounties, matchmaking, execution environments, and reputation. Do not bake every future institution into the core.

## Source anchors

Local anchors:

- `chambers/CHAMBER.md` defines the current Chamber law: requester input is untrusted; four gates mediate preflight and release; automatic mode is allowed only on clean-path runs; deterministic scans are useful but not semantic privacy proofs.
- `docs/ideation/02-private-cognitive-labor-market.md` defines the economic object: accepted, typed, provenance-bearing cognitive deltas, not raw access or persuasive prose.
- `docs/ideation/03-egress-and-immune-system.md` defines the hard security stance: everything observable outside owner control is egress; logs, errors, timings, paths, examples, embeddings, and refusal reasons are not harmless.
- `docs/ideation/06-canonical-type-signatures.md` is the current type-signature lens and should remain the canonical ideation document.
- the archived first-stab kernel's canon (private archive) already states the kernel laws: no grant/no access, walled run, typed persistence, schema as privacy budget, free text gated, release screen boundary, annotations-only channel, additive dissent, provenance floor, and trust-domain separation.

External anchors:

- Dwork and Roth, *The Algorithmic Foundations of Differential Privacy*, frame privacy-preserving analysis as a query-release problem with composition limits, not a magic anonymization switch: <https://www.cis.upenn.edu/~aaroth/privacybook.html>.
- Jif’s decentralized label model gives a useful precedent for principals, acts-for authority, confidentiality policies, integrity policies, labels, and a lattice over allowed flows: <https://www.cs.cornell.edu/jif/doc/jif-3.3.0/dlm.html>.
- Ghorbani and Zou’s Data Shapley gives a reference point for paying contributors by marginal value while warning that exact contribution accounting can be expensive and privacy-sensitive: <https://arxiv.org/abs/1904.02868>.
- Forough, Kogias, and Haddadi survey confidential computing for agentic AI and name the agent-specific threat surface: planning, memory, tool use, delegation, credentials, prompt injection, context exfiltration, and multi-hop trust: <https://arxiv.org/abs/2605.03213>.
- Figuera’s Notarized Agents argues that logs produced by the acting agent are structurally compromised and motivates receiver-attested, owner-encrypted receipts and public witness logs: <https://arxiv.org/abs/2606.04193>.
- Seo, Catak, Rong, and Jang frame federated inference as protected collaborative computation with privacy, observability, incentive, and performance trade-offs: <https://arxiv.org/abs/2603.02214>.
- Wang et al.’s ZK-Value shows the shape of privacy-preserving data valuation with proofs, but also the cost pressure that makes simpler owner-private ledgers attractive first: <https://arxiv.org/abs/2605.03581>.

## Design taste: what counts as “beautiful” here

Beautiful type signatures for Scry Chambers should be:

1. **Low-capacity by default**: booleans, enums, buckets, sketches, hashes, owner-private pointers, and bounded tables before prose.
2. **Disclosure-aware**: every field has an audience, precision, cadence, and release path.
3. **Compositional**: a safe single run can still become unsafe when repeated across agents, audiences, and time.
4. **Institutional**: reviewers, stewards, auditors, treasurers, model brokers, and agent authors are principals, not comments.
5. **Economically legible**: pay for accepted, grounded, low-leakage structure; do not pay for broad access, token burn, verbosity, or unreviewed demos.
6. **Side-channel honest**: timing, cost, progress, logs, errors, filenames, retries, support bundles, notifications, and billing are first-class surfaces.
7. **Owner-centered**: owner attention is a scarce security resource; exhausted attention fails closed for disclosure.
8. **Expandable without migration theater**: the local JSONL demo, a rootless container runner, a hosted enclave, and a paid marketplace should speak the same core nouns.

The wrong aesthetic is an all-knowing `AgentRun` blob. The right aesthetic is a small algebra plus ledgers.

## Recommended core algebra

The core should stay near eleven records. These are the nouns every later feature needs.

```ts
type Brand<T, B extends string> = T & { readonly __brand: B };

type Id<B extends string> = Brand<string, B>;
type Hash = `sha256:${string}`;
type Timestamp = string; // RFC3339 inside owner control; rounded or bucketed outside.
type Bits = number;
type JsonPath = string;

type Visibility =
  | "system_secret"
  | "owner_private"
  | "reviewer_private"
  | "agent_private"
  | "requester_visible"
  | "sponsor_visible"
  | "public";

type Bucket = "zero" | "one" | "few" | "some" | "many" | "unknown";
type Precision = "exact" | "rounded" | "bucketed" | "suppressed";

type PrincipalRole =
  | "owner"
  | "requester"
  | "sponsor"
  | "agent_author"
  | "worker_agent"
  | "reviewer"
  | "steward"
  | "auditor"
  | "operator"
  | "model_broker"
  | "tool"
  | "system";

interface Principal {
  id: Id<"Principal">;
  role: PrincipalRole;
  display: "named" | "pseudonymous" | "opaque";
  trustDomain: "owner" | "admitted_guest" | "market" | "operator" | "public";
}

interface Chamber {
  id: Id<"Chamber">;
  owner: Id<"Principal">;
  purpose: string;
  retention: RetentionPolicy;
  defaultRelease: "owner_only" | "review_required";
}

interface Scope {
  id: Id<"Scope">;
  chamberId: Id<"Chamber">;
  ownerPrivateLabel: string;
  requesterVisibleClass: DataClass[];
  sensitivity: "low" | "medium" | "high" | "special";
  selectors: ScopeSelector[];
  ownerPrivateLocator?: string;
  exposedAs: "opaque_handle" | "schema_only" | "synthetic_preview" | "aggregate_only" | "owner_only";
  canary?: CanaryProfile;
}

interface Grant {
  id: Id<"Grant">;
  chamberId: Id<"Chamber">;
  grantor: Id<"Principal">;
  grantee: Id<"Principal">;
  agentHash: Hash;
  allowedScopes: Id<"Scope">[];
  envRecipeId: Id<"EnvRecipe">;
  allowedTransforms: Id<"Transform">[];
  sinkPolicy: SinkPolicy;
  observablePolicy: ObservablePolicy[];
  attentionBudgetId: Id<"AttentionBudget">;
  egressBudgetId: Id<"EgressBudget">;
  valid: TimeWindow;
  revokedAt?: Timestamp;
}

interface Transform {
  id: Id<"Transform">;
  chamberId: Id<"Chamber">;
  requester: Id<"Principal">;
  sponsor?: Id<"Principal">;
  declaredPurpose: string;
  untrustedPromptHash: Hash;
  inputPolicy: InputPolicy;
  outputSchemaId: string;
  outputPolicy: OutputPolicy;
  reviewPlan: ReviewPlan;
}

interface Run {
  id: Id<"Run">;
  chamberId: Id<"Chamber">;
  grantId: Id<"Grant">;
  transformId: Id<"Transform">;
  status: RunStatus;
  currentGate: Gate;
  parentRunId?: Id<"Run">;
  artifactIds: Id<"Artifact">[];
  reviewIds: Id<"Review">[];
  ledgerTail: Id<"LedgerEntry">;
}

interface Artifact {
  id: Id<"Artifact">;
  runId: Id<"Run">;
  kind:
    | "prompt"
    | "typed_output"
    | "annotation"
    | "stdout"
    | "stderr"
    | "scan"
    | "review"
    | "release_candidate"
    | "receipt"
    | "support_bundle";
  visibility: Visibility;
  sha256: Hash;
  redactionState: "raw" | "deterministic_redaction" | "review_redaction" | "public_minimized";
  provenance: ProvenanceEdge[];
  retainedUntil: Timestamp;
}

interface Review {
  id: Id<"Review">;
  runId: Id<"Run">;
  stage: "admission" | "preflight" | "release" | "appeal" | "posthoc_audit";
  reviewer: Id<"Principal">;
  saw: ExposureSummary;
  verdict: "allow" | "owner_review" | "redact" | "reject" | "quarantine";
  risk: RiskVector;
  unsafeFieldPaths: JsonPath[];
  rationaleOwnerVisible: MinimizedText;
}

interface Release {
  id: Id<"Release">;
  runId: Id<"Run">;
  candidateArtifactId: Id<"Artifact">;
  reviewerIds: Id<"Review">[];
  ownerDecision: "approve" | "reject" | "edit" | "delegate_clean_path";
  releasedFields: JsonPath[];
  redactedFields: JsonPath[];
  cumulativeCapacity: CapacityEstimate;
  releasedAt?: Timestamp;
}

interface Receipt {
  id: Id<"Receipt">;
  releaseId: Id<"Release">;
  publicArtifactHash: Hash;
  visibleClaims: ReceiptClaim[];
  caveats: ReceiptCaveat[];
  noPerfectSecrecyClaim: true;
}

interface LedgerEntry {
  id: Id<"LedgerEntry">;
  chamberId: Id<"Chamber">;
  runId?: Id<"Run">;
  at: Timestamp;
  actor: Id<"Principal">;
  gate: Gate;
  action: LedgerAction;
  artifactId?: Id<"Artifact">;
  sideChannel?: SideChannelObservation;
  visibility: Visibility;
  causalParentIds: Id<"LedgerEntry">[];
}
```

This core deliberately keeps `Annotation` out of the minimal boundary core even though annotations are the market commodity. In the local product wedge, annotations can be `Artifact.kind = "annotation"`. In the market layer, `Annotation` gets promoted to its own record with acceptance, reuse, and payout edges.

## Policy atoms the core depends on

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

type Gate =
  | "submit"
  | "static_scan"
  | "preflight"
  | "owner_execution"
  | "worker"
  | "release_review"
  | "owner_disclosure"
  | "post_release";

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

type LedgerAction =
  | "grant_created"
  | "grant_revoked"
  | "run_created"
  | "gate_changed"
  | "artifact_written"
  | "artifact_read"
  | "review_submitted"
  | "release_approved"
  | "release_rejected"
  | "attention_debited"
  | "credit_debited"
  | "side_channel_observed"
  | "incident_opened"
  | "incident_closed";

interface TimeWindow { startsAt: Timestamp; endsAt: Timestamp; }
interface RetentionPolicy { retainRawUntil?: Timestamp; retainMinimizedUntil: Timestamp; deleteScratchAfterSeconds: number; }
interface MinimizedText { text: string; maxWords: number; forbiddenClasses: RiskClass[]; }
interface ScopeSelector { kind: "table" | "row_filter" | "semantic_class" | "owner_label" | "opaque_mount"; valueHash: Hash; }
interface CanaryProfile { kind: "string" | "paired_silo" | "distribution_shift"; markerHash: Hash; }
interface ProvenanceEdge { from: Id<"Scope"> | Id<"Artifact">; to: Id<"Artifact">; granularity: ExposureSummary["granularity"]; transform: string; }
interface ExposureSummary { sawRawPrivateData: boolean; dataClasses: DataClass[]; granularity: "none" | "metadata" | "aggregate" | "snippet" | "full"; }
```
Additional policy records referenced by the signatures:

```ts
interface SinkPolicy {
  durableChannel: "typed_annotation" | "owner_internal_text" | "release_candidate";
  schemaId: string;
  ownerOnlyFields: JsonPath[];
  potentiallyReleasableFields: JsonPath[];
  scanProfiles: string[];
  maxCapacityBits: Bits;
}

interface InputPolicy {
  allowedScopes: Id<"Scope">[];
  prohibitedScopes: Id<"Scope">[];
  allowedGranularity: "metadata" | "aggregate" | "search_hit" | "snippet" | "full_read";
  requireMockFirst: boolean;
  canRevealSourceLocators: false;
}

interface OutputPolicy {
  schemaId: string;
  freeText: "forbidden" | "owner_internal_only" | "release_review_required";
  maxBytes: number;
  maxWords?: number;
  allowedFieldClasses: ("boolean" | "enum" | "bucket" | "sketch" | "aggregate_table" | "capped_text")[];
  forbiddenRiskClasses: RiskClass[];
  exactCountsAllowed: false;
  sourceListsAllowed: false;
}

interface ReviewPlan {
  preflight: number;
  release: number;
  independence: "same_pool_ok" | "separate_roles" | "separate_models";
}

interface ReceiptClaim {
  fieldPath: JsonPath;
  claimType: "aggregate" | "boolean" | "bucket" | "sketch" | "process";
}

interface ReceiptCaveat {
  code: "bounded_leakage" | "not_anonymity" | "not_semantic_proof" | "not_full_context" | "audience_limited";
  text: MinimizedText;
}

interface AcceptanceRule {
  quorum: number;
  minQuality: Score01;
  minNovelty: Score01;
  duplicatePolicy: "reject" | "merge_delta_only";
  requireProvenance: true;
  preserveDissent: true;
  allowFreeTextForPayout: false;
  releaseRequiredForCompletion: false;
}

interface TmpfsMount { target: string; sizeMiB: number; noexec: true; }
interface ResourceBudget { cpuMs: number; wallMs: number; memoryMiB: number; pids: number; }
interface EnvVarPolicy { allow: string[]; deny: string[]; redactValues: true; }
interface SecretPolicy { mode: "none" | "brokered" | "explicit_mount"; secretIds: string[]; }
interface LogPolicy { stdout: Visibility; stderr: Visibility; maxBytes: number; redactBeforePersist: boolean; }
interface AttestationPolicy { requireMeasurement: boolean; publicClaim: "none" | "environment_class" | "verified_measurement"; }
```

## Side-channel layer

The most important correction to naive type design is this: output schema is not the privacy schema. Output is one channel. Every observer-visible state is a channel.

```ts
type Surface =
  | "requester_result"
  | "requester_status"
  | "owner_console"
  | "review_card"
  | "agent_prompt"
  | "agent_stdout"
  | "agent_stderr"
  | "run_artifact"
  | "server_log"
  | "support_bundle"
  | "browser"
  | "network"
  | "notification"
  | "billing_statement"
  | "receipt";

type SideChannelKind =
  | "timing"
  | "token_count"
  | "cost"
  | "byte_count"
  | "word_count"
  | "exact_count"
  | "path"
  | "filename"
  | "log_line"
  | "error_shape"
  | "model_metadata"
  | "tool_metadata"
  | "screenshot"
  | "browser_history"
  | "network_endpoint"
  | "cache_key"
  | "ordering"
  | "progress_state"
  | "retry_pattern"
  | "followup_right"
  | "repeated_query"
  | "match_denominator"
  | "notification_timing";

type ObserverClass =
  | "owner"
  | "requester"
  | "sponsor"
  | "reviewer"
  | "operator"
  | "support"
  | "notifier"
  | "public";

interface ObservablePolicy {
  surface: Surface;
  observer: ObserverClass;
  fieldPaths: JsonPath[];
  precision: Precision;
  cadence: "immediate" | "delayed" | "batched" | "release_only" | "never";
  maxBits: Bits;
  secretDependentBranching: "forbidden" | "padded_only" | "owner_only";
}

interface SideChannelObservation {
  kind: SideChannelKind;
  surface: Surface;
  observer: ObserverClass;
  valueShape: "exact" | "range" | "bucket" | "presence_only" | "suppressed";
  precision: Precision;
  mitigation: "none" | "bucketed" | "delayed" | "padded" | "redacted" | "blocked";
  estimatedLeakage: LeakageEstimate;
  releaseBlocking: boolean;
}

interface EgressBudget {
  id: Id<"EgressBudget">;
  maxBitsPerRun: Bits;
  maxBitsPerGrant: Bits;
  maxBitsPerAudience: Record<ObserverClass, Bits>;
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

Laws for this layer:

- Every non-owner observable must have an `ObservablePolicy`.
- Requester-visible timing, token, retry, cache, model, and cost signals are suppressed, delayed, bucketed, or padded.
- Logs, errors, screenshots, support bundles, notifications, and receipts are artifacts, not exhaust.
- A release can be blocked by cumulative leakage even when its immediate output validates.
- Follow-up rights and denial reasons are emissions.

## Attention layer

Human attention is a leak boundary and a scarce compute resource. If review costs are untyped, the system will either spam the owner or silently govern them.

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
  id: Id<"AttentionBudget">;
  human: Id<"Principal">;
  window: TimeWindow;
  maxInterruptions: number;
  maxReviewCards: number;
  maxDetailExpansions: number;
  maxHighRiskOverrides: number;
  exhaustionPolicy: "fail_closed_disclosure" | "defer_low_risk" | "batch_notifications";
}

interface ReviewCard {
  id: Id<"Artifact">;
  runId: Id<"Run">;
  gate: Gate;
  decisionNeeded: "approve_execution" | "reject_execution" | "approve_release" | "redact" | "override";
  minimalFacts: MinimizedText[];
  quantityHint: Bucket;
  risk: RiskVector;
  proposedVisibleFields: JsonPath[];
  expansionArtifactId?: Id<"Artifact">;
}

interface AttentionDebit {
  budgetId: Id<"AttentionBudget">;
  runId: Id<"Run">;
  human: Id<"Principal">;
  reason: AttentionReason;
  interruptions: number;
  reviewCards: number;
  detailExpansions: number;
  minutesBucket: Bucket;
  cognitiveLoad: "low" | "medium" | "high";
}

interface NotificationPolicy {
  channel: "inbox" | "email_digest" | "push" | "sms" | "webhook";
  allowedFields: JsonPath[];
  lockscreenSafe: boolean;
  containsCounts: false;
  containsPaths: false;
  containsRawData: false;
  cadence: "fixed_digest" | "jittered_prompt" | "owner_pull_only";
}
```

Default UI rule: show the smallest safe card first. Expanding detail is an exposure event. Publishing cannot depend on a tired implicit approval.

## Market layer

The economy exists to buy accepted private cognitive labor, not to buy secrets. The market records should sit above the boundary core.

```ts
type MoneyMicros = Brand<bigint, "MoneyMicros">;
type Score01 = Brand<number, "Score01">;

type TargetRef =
  | { kind: "scope"; id: Id<"Scope"> }
  | { kind: "artifact"; id: Id<"Artifact"> }
  | { kind: "annotation"; id: Id<"Annotation"> }
  | { kind: "pair"; id: Id<"CandidateRelation"> };

interface Bounty {
  id: Id<"Bounty">;
  chamberId: Id<"Chamber">;
  sponsor: Id<"Principal">;
  scope: Id<"Scope">[];
  targetSchemaId: string;
  dependencySchemas: string[];
  sinkPolicy: SinkPolicy;
  egressBudgetId: Id<"EgressBudget">;
  attentionBudgetId: Id<"AttentionBudget">;
  workerGrantTemplate: Partial<Grant>;
  submissionBond?: MoneyMicros;
  maxOpenSubmissionsPerAgent: number;
  acceptanceRule: AcceptanceRule;
  payoutPoolId: Id<"CreditPool">;
  status: "draft" | "open" | "paused" | "closed" | "expired";
}

interface Annotation {
  id: Id<"Annotation">;
  chamberId: Id<"Chamber">;
  runId: Id<"Run">;
  emitter: Id<"Principal">;
  schemaId: string;
  targets: TargetRef[];
  payloadArtifactId: Id<"Artifact">;
  confidence: Score01;
  evidenceRefs: Id<"Artifact">[];
  dependsOn: Id<"Annotation">[];
  contradicts: Id<"Annotation">[];
  leakage: LeakageEstimate;
  visibility: "owner_private";
  reusableWithin: "same_chamber" | "same_owner_org" | "non_reusable";
  state: "proposed" | "accepted" | "rejected" | "contested" | "superseded" | "slashed";
}

interface Acceptance {
  id: Id<"Acceptance">;
  bountyId: Id<"Bounty">;
  annotationId: Id<"Annotation">;
  evaluator: Id<"Principal">;
  reviewIds: Id<"Review">[];
  decision: "accept" | "reject" | "refine" | "contest" | "merge";
  acceptedFor: "owner_internal_use" | "market_memory" | "release_input";
  quality: Score01;
  novelty: Score01;
  calibration: Score01;
  grounding: Score01;
  leakagePenalty: MoneyMicros;
  reasons: MinimizedText[];
  mergedInto?: Id<"Annotation">;
}

interface ReuseCredit {
  id: Id<"ReuseCredit">;
  sourceAnnotationId: Id<"Annotation">;
  consumerRunId: Id<"Run">;
  consumerBountyId: Id<"Bounty">;
  role: "evidence" | "feature" | "constraint" | "candidate_filter" | "reconciliation_input";
  necessity: "helpful" | "material" | "required";
  computedBy: Id<"Principal">;
  method: "direct_edge" | "path_decay" | "counterfactual_sample";
  marginalValue: Score01;
  shareBps: number;
}

interface Payout {
  id: Id<"Payout">;
  bountyId: Id<"Bounty">;
  acceptanceId: Id<"Acceptance">;
  payee: Id<"Principal">;
  role: "worker" | "upstream_reuse" | "evaluator" | "reconciler" | "caught_leak";
  amount: MoneyMicros;
  basis: LeakageAdjustedValue;
  status: "pending" | "heldback" | "released" | "slashed" | "void";
  clawbackWindow?: TimeWindow;
}

interface LeakageAdjustedValue {
  grossValue: MoneyMicros;
  qualityMultiplier: Score01;
  noveltyMultiplier: Score01;
  reuseMultiplier: Score01;
  leakageBits: Bits;
  prosePenalty: MoneyMicros;
  attentionPenalty: MoneyMicros;
  incidentPenalty: MoneyMicros;
  finalValue: MoneyMicros;
}
```

Market laws:

- Bounties buy accepted annotations, accepted review, reconciliation, and caught leaks; they do not buy raw access.
- Free text is non-paying by default.
- Worker, evaluator, reconciler, and release screener roles must be separated for a bounty.
- Dissent is additive. Reconciliation creates new records and credit edges; it does not overwrite history.
- Hidden reuse is non-payable and slashable.
- Public reputation is aggregate-only unless separately released.
- Payment can settle on owner-internal acceptance; external release is optional and separately gated.

## Matchmaking layer

Dating, hiring, collaboration, and advisory matching stress the privacy model because the valuable fact is often exactly the sensitive fact: this person is unusually good for that person or role.

```ts
interface MatchBounty {
  id: Id<"Bounty">;
  sponsor: Id<"Principal">;
  purpose: "dating" | "hiring" | "collaboration" | "advising" | "grantmaking";
  participantScopes: Id<"Scope">[];
  matchSchemaId: string;
  denominatorPolicy: DenominatorPolicy;
  consentPolicy: ConsentPolicy;
  bilateralReleasePolicy: BilateralReleasePolicy;
  maxCandidateRelationsPerWindow: Bucket;
}

interface CandidateRelation {
  id: Id<"CandidateRelation">;
  bountyId: Id<"Bounty">;
  members: Id<"Principal">[];
  memberScopeHashes: Hash[];
  relationKind: "pair" | "team" | "role_fit" | "mentor_match";
  scoreBucket: Bucket;
  rationaleArtifactId: Id<"Artifact">; // owner-private until release.
  denominator: DenominatorSummary;
  leakage: LeakageEstimate;
  state: "proposed" | "consent_pending" | "bilateral_release_ready" | "released" | "rejected";
}

interface DenominatorPolicy {
  minGroupSize: number;
  revealDenominator: "never" | "bucket_only" | "owner_only";
  zeroOneManyOnly: boolean;
  audienceOverlapLimit: Bucket;
  suppressWhenExternallyIdentifiable: true;
}

interface DenominatorSummary {
  poolHash: Hash;
  sizeBucket: Bucket;
  externalIdentifiabilityRisk: "low" | "medium" | "high" | "unknown";
}

interface ConsentPolicy {
  requiredFrom: "all_members" | "owner_then_counterparty" | "steward_mediated";
  consentArtifactSchemaId: string;
  denialVisibleToCounterparty: false;
  timeoutDecision: "silent_expire" | "owner_private_reject";
}

interface BilateralReleasePolicy {
  releaseMode: "symmetric" | "staged" | "mediated";
  firstMessageSchemaId: string;
  revealScore: "never" | "bucket_only";
  revealRationale: "none" | "owner_edited" | "steward_minimized";
  receiptToEachParty: true;
}
```

Default stance: no one receives a live list of who nearly matched them. The safe primitive is a mediated candidate relation with consent and denominator controls, not a public ranker over private people.

## Production environment layer

Containers and enclaves are implementation details, but the type system must know what the environment promised.

```ts
interface EnvRecipe {
  id: Id<"EnvRecipe">;
  isolation: "local_read_only" | "docker_rootless" | "podman_rootless" | "firecracker" | "gvisor" | "k8s_job" | "tee";
  imageDigest?: Hash;
  entrypoint: string[];
  user: { uid: number; gid: number; noNewPrivileges: true };
  rootfs: { readOnly: true; tmpfs: TmpfsMount[] };
  mounts: MountSpec[];
  network: NetworkPolicy;
  modelAccess: ModelAccessPolicy;
  resources: ResourceBudget;
  envVars: EnvVarPolicy;
  secrets: SecretPolicy;
  logs: LogPolicy;
  attestation?: AttestationPolicy;
}

interface MountSpec {
  sourceSnapshot: Hash | Id<"Scope">;
  target: string;
  mode: "ro" | "wo" | "tmpfs";
  exposeFilenames: boolean;
  allowGlobs?: string[];
  denyGlobs?: string[];
}

interface NetworkPolicy {
  mode: "none" | "model_broker_only" | "egress_proxy_allowlist";
  allowlist?: string[];
}

interface ModelAccessPolicy {
  mode: "none" | "owner_local" | "broker_no_raw_context" | "direct_provider_exception";
  exactModelOwnerPrivate: boolean;
  requesterSeesModelClassOnly: true;
}

interface SupportBundlePolicy {
  allowedArtifactKinds: Artifact["kind"][];
  requireReleaseReview: true;
  requesterVisible: false;
  maxBytesBucket: Bucket;
}
```

Production rule: never mount `$HOME`, browser profiles, SSH config, cloud credentials, package caches, git credentials, agent auth, or personal app state into guest runs. A curated owner-prepared scope is a product primitive, not a convenience flag.

## Risk classes

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
  | "cost_abuse"
  | "reviewer_exposure"
  | "match_denominator"
  | "synthetic_preview_laundering"
  | "repeated_query_reconstruction";

interface RiskScore { severity: 0 | 1 | 2 | 3 | 4 | 5; likelihood: 0 | 1 | 2 | 3 | 4 | 5; mitigated: boolean; }

interface RiskVector {
  overall: "low" | "medium" | "high" | "blocker";
  classes: Partial<Record<RiskClass, RiskScore>>;
  confidence: "low" | "medium" | "high";
  releaseBlockers: RiskClass[];
  rationale: MinimizedText[];
}
```

The risk taxonomy should be boring and enumerable. A blocker that cannot be typed cannot be reliably paid, routed, audited, or improved.

## Open research questions

### 1. How should leakage budgets compose?

Per-run budgets are not enough. The same one-bit answer repeated across many audiences can become a dossier. The right primitive is likely a composition key over subject, query family, audience, sponsor, agent, and time window. This is partly a privacy problem and partly an identity/Sybil problem.

Default stance: every release belongs to a `QueryCompositionPolicy`; cumulative leakage can block future releases.

### 2. How much constant-work padding is economically tolerable?

Timing, token, cost, retry, and status signals leak. Padding them makes the system safer and more expensive. Perfect padding is unrealistic; unpadded per-run status is unsafe.

Default stance: requester and sponsor see delayed/bucketed status, no per-run token spend, no exact model, no retry count, and no exact cost. Owner sees the raw operational ledger.

### 3. When may reviewers see raw data?

Reviewer minimization conflicts with review quality. Some hard cases need raw context. Unlogged raw review access turns guardians into an insider-risk surface.

Default stance: reviewers start at structured artifacts; every expansion requires an `ExpansionToken`, justification, exposure debit, and ledger entry.

### 4. How should synthetic previews be validated?

Synthetic rows, schema examples, and redacted samples can leak distributional shape, rare phrases, and nearest-neighbor facts. One distance metric will not solve this.

Default stance: synthetic previews are artifacts with leakage estimates, canaries, rare-token scans, and paired-silo tests. They are not automatically public examples.

### 5. How does credit assignment avoid becoming a monitoring surface?

Reuse credit and Shapley-like attribution are attractive but may require logging detailed dependency paths and counterfactuals. Those logs can reveal what mattered inside private context.

Default stance: start with direct reuse edges and path decay. Defer counterfactual/Shapley approximations until the privacy cost of the valuation process itself is typed.

### 6. What is the primitive for cross-silo matching?

A match may require two or more people’s private contexts. The result may be safe for neither party alone until consent, denominator, and symmetry rules hold.

Default stance: model `CandidateRelation` as owner-private until all required consent gates clear. The requester never receives denominator details beyond a bucketed receipt.

### 7. What reputation can leave the Chamber?

Agent reputation is needed for market liquidity. Exact examples can leak private work. Aggregate scores can still leak if the agent ran on a small set of unusual bounties.

Default stance: reputation is chamber-local first, owner-org local second, and exportable only as release-screened aggregate receipts.

### 8. What becomes notarized?

Agent-produced logs are not enough. Receiver-attested receipts are attractive for external services, but Scry’s first loop can get far with owner-local hash ledgers and later add witness logs.

Default stance: every artifact gets a hash and ledger entry now. External receiver receipts become an optional production layer for tools and broker calls.

### 9. Where does differential privacy actually fit?

Differential privacy is useful for aggregate query release and repeated analytics, not for arbitrary free-text private-life matching. It should not be used as a decorative privacy word.

Default stance: use DP only for explicitly aggregate mechanisms with stated parameters, composition, and utility loss. Use low-capacity schemas and review gates elsewhere.

### 10. What is the first product wedge?

The first wedge should not be a full marketplace or enclave platform. It should make the current Chamber loop ledgered and typed.

Default stance:

1. Give every prompt, stdout, stderr, worker output, scan, review, release candidate, receipt, and support bundle an `Artifact`.
2. Replace loose event text with `LedgerEntry` records.
3. Add `ExposureSummary`, `AttentionDebit`, and `SideChannelObservation`.
4. Generate two projections from the same ledger: owner-forensic and requester-minimized.
5. Keep annotations owner-private by default.
6. Add bounties only after typed annotations and reviews are stable.

## Research tracks to keep running

### Track A: type algebra

Goal: compress the signatures until they are small enough to remember but not so small that side channels, attention, and market incentives become prose.

Output: a stable core-schema module with about eleven core records and separate modules for side channels, attention, markets, matching, and environments.

### Track B: adversarial egress harness

Goal: run paired silos that differ by one secret and compare every observer-visible output: answer, status, latency bucket, token bucket, error shape, log line, review card, notification, billing, and receipt.

Output: a regression suite that turns “anything observable outside owner control is egress” into executable checks.

### Track C: annotation market simulation

Goal: simulate bounties, annotations, evaluation, reuse credit, spam, evaluator capture, and leakage-adjusted payout before real money is involved.

Output: a toy ledger with adversarial agents and clear metrics: accepted value per leaked bit, accepted value per steward minute, slashes per agent, and reuse credit concentration.

### Track D: matchmaking denominator model

Goal: model when a match result is unsafe because the candidate pool is small, externally enumerable, or audience-overlapping.

Output: `DenominatorPolicy` and `ConsentPolicy` examples for dating, hiring, advising, and collaboration.

### Track E: production isolation receipts

Goal: decide which environment receipts are worth building first: local read-only receipts, rootless container receipts, model-broker receipts, receiver-attested tool receipts, or TEE attestations.

Output: environment recipe matrix with claims, non-claims, costs, and failure modes.

## Recommended doc structure from here

The "keep two documents" rule did not survive contact with the work; there are now four-plus surfaces. The honest structure is one law and orbiting arguments:

1. `../primitives/` — the canonical, typechecked signatures plus `CANON.md`. When a signature stabilizes, it lands here and nowhere else.
2. `../ideation/06-canonical-type-signatures.md` — the inspiring lens; stays readable standalone.
3. This memo — the research program: open questions, external anchors, candidate signatures *before* they stabilize.
4. `../autoresearch/*` — dated cuts and arguments; each declares canon at the top and may drift only knowingly.

Do not turn the ideation doc into a migration manual, and do not let any prose document define a record that `../primitives/` already defines.

## Bottom line

The premier architecture is not “let third-party agents browse private data safely.” It is:

> Admit bounded agents into typed work environments; let them produce owner-private annotations; evaluate, reconcile, and pay for accepted low-leakage structure; route only reviewed minimized releases across the boundary; and ledger every explicit output, side channel, attention debit, credit movement, and receipt.

The first implementation move is the typed ledger. Once the ledger exists, containers, bounties, matchmaking, reputation, canaries, confidential compute, and external receipts have somewhere honest to attach.
