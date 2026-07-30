/**
 * Scry Chambers core primitives.
 *
 * The core is the boundary algebra: who may do bounded cognitive work near a
 * private world, what ran, what it emitted, who reviewed it, what was released,
 * and what the ledger remembers. Market, entropy, matching, and production
 * isolation layers attach to these records; they do not replace them.
 */

export type Brand<T, B extends string> = T & { readonly __brand: B };
export type Id<K extends string> = Brand<string, `${K}Id`>;
export type Hash = Brand<`sha256:${string}`, "Hash">;
/**
 * RFC3339 inside owner control. Any timestamp that crosses to a non-owner
 * observer is itself an emission: rounded, bucketed, delayed, or suppressed
 * per the entropy layer. Exact outward timestamps do not exist.
 */
export type Timestamp = Brand<string, "Timestamp">;
export type JsonPath = Brand<string, "JsonPath">;
export type SchemaId = Brand<string, "SchemaId">;
export type Words = Brand<number, "Words">;
export type Bytes = Brand<number, "Bytes">;
export type Seconds = Brand<number, "Seconds">;
export type Bits = Brand<number, "Bits">;
export type Score01 = Brand<number, "Score01">;

export type Bucket = "zero" | "one" | "few" | "some" | "many" | "unknown";
export type Precision = "exact" | "rounded" | "bucketed" | "suppressed";

export type Visibility =
  | "system_secret"
  | "owner_private"
  | "reviewer_private"
  | "agent_private"
  | "requester_visible"
  | "sponsor_visible"
  | "public";

export type PrincipalRole =
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

export interface Principal {
  readonly id: Id<"Principal">;
  readonly role: PrincipalRole;
  readonly display: "named" | "pseudonymous" | "opaque";
  readonly trustDomain: "owner" | "admitted_guest" | "market" | "operator" | "public";
  /**
   * The real economic actor behind this (possibly pseudonymous) principal.
   * Role-separation predicates (evaluator ≠ worker, oracle-author ≠ worker)
   * are checkable set-disjointness over beneficial entities, never over ids —
   * distinct ids controlled by one entity are one colluding party.
   *
   * NOT SOLVED BY THIS FIELD: whether two BeneficialEntity records are secretly
   * one entity is an identity-governance problem the type system cannot decide.
   * `linkageBasis` records how confidently they were bound; treat low-confidence
   * separation as unproven, not as a guarantee.
   */
  readonly beneficialEntityId?: Id<"BeneficialEntity">;
}

/**
 * The controlling economic actor. Introduced to retire the overclaim that
 * distinct principal ids imply distinct parties. Uniqueness is asserted, not
 * proven — a proof-of-uniqueness substrate is an open dependency.
 */
export interface BeneficialEntity {
  readonly id: Id<"BeneficialEntity">;
  readonly controllerAttestation: Hash;
  readonly linkageBasis: "self_declared" | "kyc_verified" | "stake_bonded" | "proof_of_uniqueness";
  /** How much a same-entity / distinct-entity verdict about this actor can be trusted. */
  readonly confidence: "low" | "medium" | "high";
}

export type ConflictVerdict = "distinct" | "overlap_flagged" | "overlap_blocked" | "unprovable";

/**
 * Enumerates the beneficial entities behind every role in a bounty/acceptance
 * and yields a verdict. Replaces hardcoded "roleAMayNotBeRoleB: true" booleans
 * with an attributed, auditable check that can honestly say "unprovable".
 */
export interface ConflictOfInterestCheck {
  readonly id: Id<"ConflictOfInterestCheck">;
  readonly chamberId: Id<"Chamber">;
  readonly roleEntities: Readonly<Record<string, Id<"BeneficialEntity">>>;
  readonly verdict: ConflictVerdict;
  readonly weakestLinkageConfidence: "low" | "medium" | "high";
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface Chamber {
  readonly id: Id<"Chamber">;
  readonly ownerId: Id<"Principal">;
  readonly purpose: string;
  readonly defaultRelease: "owner_only" | "review_required";
  readonly retention: RetentionPolicy;
}

export type DataClass =
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

export interface Scope {
  readonly id: Id<"Scope">;
  readonly chamberId: Id<"Chamber">;
  readonly ownerPrivateLabel: string;
  readonly requesterVisibleClasses: readonly DataClass[];
  readonly sensitivity: "low" | "medium" | "high" | "special";
  readonly selectorHash: Hash;
  readonly presentation: "opaque_handle" | "schema_only" | "synthetic_preview" | "aggregate_only" | "owner_only";
  readonly canaryHash?: Hash;
}

export interface Grant {
  readonly id: Id<"Grant">;
  readonly chamberId: Id<"Chamber">;
  readonly grantorId: Id<"Principal">;
  readonly granteeId: Id<"Principal">;
  readonly agentHash: Hash;
  readonly allowedScopeIds: readonly Id<"Scope">[];
  readonly envRecipeId: Id<"EnvRecipe">;
  readonly sink: SinkPolicy;
  readonly valid: TimeWindow;
  readonly revokedAt?: Timestamp;
}

export interface Transform {
  readonly id: Id<"Transform">;
  readonly chamberId: Id<"Chamber">;
  readonly requesterId: Id<"Principal">;
  readonly sponsorId?: Id<"Principal">;
  readonly declaredPurpose: string;
  readonly untrustedPromptHash: Hash;
  readonly input: InputPolicy;
  readonly output: OutputPolicy;
  readonly review: ReviewPlan;
}

export type Gate =
  | "submit"
  | "static_scan"
  | "preflight"
  | "owner_execution"
  | "worker"
  | "release_review"
  | "owner_disclosure"
  | "post_release";

export type RunStatus =
  | "created"
  | "preflight"
  | "awaiting_owner_execution"
  | "running"
  | "worker_done"
  | "release_review"
  | "awaiting_owner_release"
  | "released"
  | "owner_visible_only"
  | "rejected"
  | "revoked"
  | "error";

export interface Run {
  readonly id: Id<"Run">;
  readonly chamberId: Id<"Chamber">;
  readonly grantId: Id<"Grant">;
  readonly transformId: Id<"Transform">;
  readonly status: RunStatus;
  readonly currentGate: Gate;
  readonly parentRunId?: Id<"Run">;
  readonly artifactIds: readonly Id<"Artifact">[];
  readonly reviewIds: readonly Id<"Review">[];
  readonly ledgerTailId?: Id<"LedgerEntry">;
}

export type ArtifactKind =
  | "prompt"
  | "typed_output"
  | "annotation"
  | "stdout"
  | "stderr"
  | "scan"
  | "review"
  | "release_candidate"
  | "receipt"
  | "environment_receipt"
  | "attribution_report"
  | "attention_card"
  | "market_settlement"
  | "support_bundle";

/**
 * Confidentiality is the `Visibility` lattice; integrity is its dual — how much
 * a value can be trusted, from untrusted requester text to system-trusted.
 * Robust declassification requires that the thing SELECTING what to release be
 * high-integrity, so a laundering path (mix a trusted selector with untrusted
 * content, declassify the blend) is not expressible.
 */
export type Integrity =
  | "untrusted"
  | "endorsed_agent"
  | "reviewed"
  | "owner_trusted"
  | "system_trusted";

export interface Label {
  readonly conf: Visibility;
  readonly integ: Integrity;
}

/**
 * Attached to a Release: names who declassified, under what authority, and via
 * which selector — and the selector must itself be high-integrity. Guarantees
 * label CONSISTENCY over DECLARED provenance only. It does NOT prove opaque
 * prose respects its label; a mislabeled source makes the join a lie. Receipts
 * must carry that caveat.
 */
export interface DeclassificationWitness {
  readonly declassifierId: Id<"Principal">;
  readonly selectorIntegrity: Integrity;
  readonly fromLabel: Label;
  readonly toLabel: Label;
  readonly consistencyOverDeclaredProvenanceOnly: true;
}

export interface Artifact {
  readonly id: Id<"Artifact">;
  readonly chamberId: Id<"Chamber">;
  readonly runId: Id<"Run">;
  readonly kind: ArtifactKind;
  readonly visibility: Visibility;
  /** Integrity dual of visibility; together they form the flow Label. */
  readonly integrity: Integrity;
  readonly sha256: Hash;
  /**
   * "erased_tombstone": body and salt destroyed, sha256 retained as a shredded
   * commitment. Requires the artifact was committed as sha256(salt‖payload) at
   * write time — a raw sha256(payload) cannot be provably erased later.
   */
  readonly redactionState:
    | "raw"
    | "deterministic_redaction"
    | "review_redaction"
    | "public_minimized"
    | "erased_tombstone";
  readonly provenance: readonly ProvenanceEdge[];
  readonly retainedUntil: Timestamp;
  readonly erasedAt?: Timestamp;
  readonly erasureRequestId?: Id<"ErasureRequest">;
}

/**
 * A subject exercising deletion over an append-only chain. Erasure destroys
 * salt + bytes; the salted commitment and every causalParentIds link still
 * verify. The ledger keeps proving WHAT HAPPENED without retaining WHAT WAS SAID.
 */
export interface ErasureRequest {
  readonly id: Id<"ErasureRequest">;
  readonly chamberId: Id<"Chamber">;
  readonly subjectHash: Hash;
  readonly artifactIds: readonly Id<"Artifact">[];
  readonly state: "requested" | "completed" | "refused_no_salt" | "refused_legal_hold";
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface Review {
  readonly id: Id<"Review">;
  readonly runId: Id<"Run">;
  readonly stage: "admission" | "preflight" | "release" | "appeal" | "posthoc_audit";
  readonly reviewerId: Id<"Principal">;
  readonly saw: ExposureSummary;
  readonly verdict: "allow" | "owner_review" | "redact" | "reject" | "quarantine";
  readonly risk: RiskVector;
  readonly unsafeFieldPaths: readonly JsonPath[];
  readonly rationaleOwnerVisible: MinimizedText;
}

export type ReleaseStatus =
  | "draft"
  | "approved"
  | "released"
  | "revoked"
  | "frozen_by_incident"
  | "rejected";

export interface Release {
  readonly id: Id<"Release">;
  readonly runId: Id<"Run">;
  readonly status: ReleaseStatus;
  readonly candidateArtifactId: Id<"Artifact">;
  /** Non-empty by construction: an unreviewed release is unrepresentable. */
  readonly reviewerIds: readonly [Id<"Review">, ...Id<"Review">[]];
  /**
   * A required HUMAN act for content disclosure — no system/operator principal
   * may author it, and no standing delegation auto-approves content. (Recurring
   * PAYOUTS are a separate rib; money and disclosure are split.)
   */
  readonly ownerDecision: "approve" | "reject" | "edit" | "delegate_clean_path";
  readonly declassification?: DeclassificationWitness;
  readonly releasedFields: readonly JsonPath[];
  readonly redactedFields: readonly JsonPath[];
  readonly receiptArtifactId?: Id<"Artifact">;
  readonly releasedAt?: Timestamp;
}

export interface ReceiptPayload {
  readonly releaseId: Id<"Release">;
  readonly visibleClaims: readonly ReceiptClaim[];
  readonly caveats: readonly ReceiptCaveat[];
  readonly noPerfectSecrecyClaim: true;
}

export type LedgerAction =
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
  | "observable_recorded"
  | "incident_opened"
  | "incident_closed"
  | "artifact_erased";

export interface LedgerEntry {
  readonly id: Id<"LedgerEntry">;
  readonly chamberId: Id<"Chamber">;
  readonly runId?: Id<"Run">;
  readonly at: Timestamp;
  readonly actorId: Id<"Principal">;
  readonly gate: Gate;
  readonly action: LedgerAction;
  readonly artifactId?: Id<"Artifact">;
  readonly visibility: Visibility;
  readonly causalParentIds: readonly Id<"LedgerEntry">[];
  readonly detailHash: Hash;
}

export interface TimeWindow {
  readonly startsAt: Timestamp;
  readonly endsAt: Timestamp;
}

export interface RetentionPolicy {
  readonly retainRawUntil?: Timestamp;
  readonly retainMinimizedUntil: Timestamp;
  readonly deleteScratchAfterSeconds: Seconds;
  /**
   * The dispute window a receipt/claim must remain auditable through.
   * Invariant (retentionOutlivesTheClaimsItBacks): retainMinimizedUntil and any
   * support artifact's retainedUntil must be ≥ the disputeHorizon end of every
   * live RunClaim or Release resting on it — scratch cannot be deleted out from
   * under a claim that still needs to be defensible.
   */
  readonly disputeHorizon: TimeWindow;
}

export type MinimizedText = Brand<string, "MinimizedText">;

export interface SinkPolicy {
  readonly durableChannel: "typed_annotation" | "owner_internal_text" | "release_candidate";
  readonly schemaId: SchemaId;
  readonly ownerOnlyFields: readonly JsonPath[];
  readonly potentiallyReleasableFields: readonly JsonPath[];
  readonly scanProfiles: readonly string[];
  readonly maxCapacityBits: Bits;
}

export interface InputPolicy {
  readonly allowedScopeIds: readonly Id<"Scope">[];
  readonly prohibitedScopeIds: readonly Id<"Scope">[];
  readonly allowedGranularity: "metadata" | "aggregate" | "search_hit" | "snippet" | "full_read";
  readonly requireMockFirst: boolean;
  readonly canRevealSourceLocators: false;
}

export interface OutputPolicy {
  readonly schemaId: SchemaId;
  readonly freeText: "forbidden" | "owner_internal_only" | "release_review_required";
  readonly maxBytes: Bytes;
  readonly maxWords?: Words;
  readonly allowedFieldClasses: readonly PublicFieldClass[];
  readonly exactCountsAllowed: false;
  readonly sourceListsAllowed: false;
}

export type PublicFieldClass = "boolean" | "enum" | "bucket" | "sketch" | "aggregate_table" | "capped_text";

export interface ReviewPlan {
  readonly preflight: number;
  readonly release: number;
  readonly independence: "same_pool_ok" | "separate_roles" | "separate_models";
}

export interface ProvenanceEdge {
  readonly from: Id<"Scope"> | Id<"Artifact">;
  readonly to: Id<"Artifact">;
  readonly granularity: ExposureSummary["granularity"];
  readonly transform: string;
}

export interface ExposureSummary {
  readonly sawRawPrivateData: boolean;
  readonly dataClasses: readonly DataClass[];
  readonly granularity: "none" | "metadata" | "aggregate" | "snippet" | "full";
}

export type RiskClass =
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

export interface RiskScore {
  readonly severity: 0 | 1 | 2 | 3 | 4 | 5;
  readonly likelihood: 0 | 1 | 2 | 3 | 4 | 5;
  readonly mitigated: boolean;
}

export interface RiskVector {
  readonly overall: "low" | "medium" | "high" | "blocker";
  readonly classes: Partial<Record<RiskClass, RiskScore>>;
  readonly confidence: "low" | "medium" | "high";
  readonly releaseBlockers: readonly RiskClass[];
  readonly rationale: readonly MinimizedText[];
}

export interface ReceiptClaim {
  readonly fieldPath: JsonPath;
  readonly claimType: "aggregate" | "boolean" | "bucket" | "sketch" | "process";
}

export type ReceiptCaveatCode =
  | "bounded_leakage"
  | "not_anonymity"
  | "not_semantic_proof"
  | "not_full_context"
  | "audience_limited";

export interface ReceiptCaveat {
  readonly code: ReceiptCaveatCode;
  readonly text: MinimizedText;
}

/**
 * The interpretability surface: a plain-language account compiled from a ledger
 * height-range, for an owner who will never read a type. Safety comes from
 * defaults and derivation, not from the owner understanding this — but they can
 * read it. Its power is the honest negative space: what did NOT cross, and what
 * the system explicitly cannot promise, are first-class, not omitted.
 */
export interface PlainAccount {
  readonly chamberId: Id<"Chamber">;
  readonly ledgerFromId: Id<"LedgerEntry">;
  readonly ledgerToId: Id<"LedgerEntry">;
  readonly whatCrossed: readonly MinimizedText[];
  readonly whatDidNotCross: readonly MinimizedText[];
  readonly whoWasPaid: readonly MinimizedText[];
  readonly whatItCannotPromise: readonly MinimizedText[];
  /** Compiled under closed-support discipline: every line traces to ledger entries. */
  readonly supportLedgerIds: readonly Id<"LedgerEntry">[];
}

/**
 * The boundary has two directions. Egress is governed by the entropy layer;
 * ingress is governed here: requester input is untrusted and enters only as
 * a hashed, policy-bound Transform. These laws are the spine.
 */
export const CORE_LAWS = {
  noGrantNoRun: true,
  requesterInputIsUntrusted: true,
  ingressIsTypedViaTransform: true,
  noBoundaryCrossingWithoutLedgerEntry: true,
  releaseFieldsAreAReviewedSubsetOfTheSink: true,
  outwardTimestampsAreEmissions: true,
  receiptsNameNonClaims: true,
  contentDisclosureRequiresAHumanOwnerDecision: true,
  roleSeparationIsCheckedOverBeneficialEntities: true,
  declassificationSelectorMustBeHighIntegrity: true,
  subjectErasureIsASaltedTombstoneNotAChainBreak: true,
  retentionOutlivesTheClaimsItBacks: true,
} as const;
