/**
 * Market primitives for bounded cognitive work.
 *
 * The market does not sell access to private data. It pays for accepted,
 * schema-valid cognitive deltas that were produced under a Grant, stored as
 * constrained annotations, reviewed, and recorded in the ledger. Attribution is
 * computed from recorded reuse evidence; the attribution method is not itself a
 * durable primitive.
 */

import type {
  DataClass,
  Hash,
  Id,
  JsonPath,
  MinimizedText,
  SchemaId,
  Score01,
  TimeWindow,
  Timestamp,
  Visibility,
} from "./core";
import type { LeakageEstimate } from "./entropy";

export type CreditMicros = number & { readonly __brand: "CreditMicros" };
export type BasisPoints = number & { readonly __brand: "BasisPoints" };

export type AnnotationState =
  | "draft"
  | "submitted"
  | "accepted"
  | "rejected"
  | "contested"
  | "superseded"
  | "quarantined"
  | "slashed";

export type AnnotationRole =
  | "match_candidate"
  | "risk_flag"
  | "opportunity"
  | "correction"
  | "objection"
  | "summary"
  | "calibration"
  /** A concrete proposed change to an owner artifact — e.g. a pull request. */
  | "patch";

export interface TargetRef {
  readonly scopeId: Id<"Scope">;
  readonly selectorHash: Hash;
  readonly ownerPrivateLocatorHash?: Hash;
}

export interface Annotation {
  readonly id: Id<"Annotation">;
  readonly chamberId: Id<"Chamber">;
  readonly runId: Id<"Run">;
  readonly authorId: Id<"Principal">;
  readonly schemaId: SchemaId;
  readonly role: AnnotationRole;
  readonly targets: readonly TargetRef[];
  readonly payloadArtifactId: Id<"Artifact">;
  readonly confidence: Score01;
  readonly evidenceArtifactIds: readonly Id<"Artifact">[];
  readonly dependsOn: readonly Id<"Annotation">[];
  readonly contradicts: readonly Id<"Annotation">[];
  readonly leakage: LeakageEstimate;
  readonly state: AnnotationState;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * Prose name for the market commodity: an accepted, typed, provenance-bearing
 * cognitive delta. The record is an Annotation; the two names are one noun.
 */
export type CognitiveDelta = Annotation;

/**
 * A named, pinned evaluator — e.g. a specific model checkpoint plus rubric —
 * whose verdict is reproducible enough to price against. "Fable approved it"
 * is only a payable event when Fable is a hash, a rubric, and an appeal path,
 * not a vibe.
 */
export interface EvaluatorOracle {
  readonly id: Id<"EvaluatorOracle">;
  readonly principalId: Id<"Principal">;
  /** Pinned checkpoint/config. A model upgrade is a new oracle. */
  readonly modelClassHash: Hash;
  readonly rubricArtifactId: Id<"Artifact">;
  readonly rubricHash: Hash;
  readonly determinism: "deterministic" | "sampled_majority" | "best_of_n";
  /**
   * Oracle capture is the failure mode: the oracle's author must not be a paid
   * worker under it. This is enforced by a ConflictOfInterestCheck over
   * beneficial entities, not by a boolean — a boolean the identity model
   * cannot back is an overclaim. The check may honestly return "unprovable".
   */
  readonly conflictCheckId: Id<"ConflictOfInterestCheck">;
  readonly appealPath: "none" | "human_steward" | "second_oracle";
}

export type AcceptanceDecision = "accept" | "reject" | "needs_redaction" | "quarantine";
export type AcceptedFor = "owner_memory" | "bounty" | "downstream_reuse" | "release_candidate";

export interface AcceptanceRule {
  readonly schemaId: SchemaId;
  readonly requiredFields: readonly JsonPath[];
  readonly forbiddenFields: readonly JsonPath[];
  readonly minQuality: Score01;
  readonly minGrounding: Score01;
  readonly maxLeakage: LeakageEstimate["class"];
  readonly evaluatorRoleSeparated: true;
}

export interface CreditPool {
  readonly id: Id<"CreditPool">;
  readonly chamberId: Id<"Chamber">;
  readonly sponsorId: Id<"Principal">;
  readonly label: string;
  readonly balance: CreditMicros;
  readonly visibility: Visibility;
  readonly externalPaymentReleaseRequired: true;
}

export interface Bounty {
  readonly id: Id<"Bounty">;
  readonly chamberId: Id<"Chamber">;
  readonly sponsorId: Id<"Principal">;
  readonly targetSchemaId: SchemaId;
  /**
   * Coarse data classes, never scope locators. A bounty describes what kind
   * of work is wanted; it creates no access. Authority flows only through
   * Grants the owner issues separately.
   */
  readonly targetClasses: readonly DataClass[];
  readonly acceptanceRule: AcceptanceRule;
  /** When evaluation is delegated to a pinned oracle rather than ad-hoc reviewers. */
  readonly evaluatorOracleId?: Id<"EvaluatorOracle">;
  /** When payment is a published function of the oracle score. See pricing.ts. */
  readonly priceScheduleId?: Id<"PriceSchedule">;
  readonly creditPoolId: Id<"CreditPool">;
  readonly window?: TimeWindowLike;
  readonly resetWindow?: "none" | "daily" | "weekly" | "monthly";
  readonly status: "draft" | "open" | "paused" | "closed" | "exhausted";
}

export interface Acceptance {
  readonly id: Id<"Acceptance">;
  readonly chamberId: Id<"Chamber">;
  readonly bountyId?: Id<"Bounty">;
  readonly annotationId: Id<"Annotation">;
  readonly evaluatorId: Id<"Principal">;
  readonly oracleId?: Id<"EvaluatorOracle">;
  readonly oracleScore?: Score01;
  readonly decision: AcceptanceDecision;
  readonly acceptedFor: readonly AcceptedFor[];
  readonly quality: Score01;
  readonly novelty: Score01;
  readonly grounding: Score01;
  readonly leakage: LeakageEstimate;
  readonly rationaleArtifactId: Id<"Artifact">;
  readonly decidedAt: Timestamp;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export type ReuseRole = "input_feature" | "evidence" | "objection" | "calibration" | "routing_signal";
export type ReuseNecessity = "incidental" | "helpful" | "necessary" | "decisive";

export interface ReuseEdge {
  readonly id: Id<"ReuseEdge">;
  readonly chamberId: Id<"Chamber">;
  readonly sourceAnnotationId: Id<"Annotation">;
  readonly consumerRunId: Id<"Run">;
  readonly role: ReuseRole;
  readonly necessity: ReuseNecessity;
  readonly declaredById: Id<"Principal">;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * The method is declared above the protocol, like pricing. The kernel's
 * shipped, audited instance of `shapley_proxy` is `shapley_dpi/1`
 * (chambers/kernel/ATTRIBUTION-SPEC.md): exact-integer Shapley over
 * the DPI carrying capacity of the provenance closure — recomputable
 * from the artifact, conviction on misdeclaration (V-codes), share
 * conservation machine-checked. "Proxy" is honest: it prices declared
 * carrying capacity, never quality or counterfactual causation.
 */
export type AttributionMethod =
  | "direct_reuse"
  | "path_decay"
  | "counterfactual_sample"
  | "shapley_proxy";

export interface AttributionShare {
  readonly annotationId: Id<"Annotation">;
  readonly acceptanceIds: readonly Id<"Acceptance">[];
  readonly shareBps: BasisPoints;
  readonly explanation: MinimizedText;
}

export interface AttributionReportPayload {
  readonly method: AttributionMethod;
  readonly inputReuseEdgeIds: readonly Id<"ReuseEdge">[];
  readonly inputAcceptanceIds: readonly Id<"Acceptance">[];
  readonly shares: readonly AttributionShare[];
  readonly caveats: readonly MinimizedText[];
}

export type SettlementRole =
  | "worker"
  | "upstream_reuse"
  | "evaluator"
  | "reconciler"
  | "leak_catcher";

export interface CreditSettlement {
  readonly id: Id<"CreditSettlement">;
  readonly chamberId: Id<"Chamber">;
  readonly poolId: Id<"CreditPool">;
  readonly recipientId: Id<"Principal">;
  readonly recipientRole: SettlementRole;
  readonly acceptanceIds: readonly Id<"Acceptance">[];
  readonly attributionReportArtifactId?: Id<"Artifact">;
  readonly amount: CreditMicros;
  readonly status:
    | "owner_internal"
    | "release_review_required"
    | "heldback"
    | "released"
    | "slashed"
    | "void";
  readonly clawbackWindow?: TimeWindowLike;
  readonly externalReleaseId?: Id<"Release">;
  /** Present iff this payout settled zero-touch under a standing authorization. */
  readonly payoutAuthorizationId?: Id<"SettlementPayoutAuthorization">;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * Standing authorization for recurring PAYOUTS only — never content releases.
 * Bound once by a human before work starts, to a specific oracle + price
 * schedule + match predicate. Lets use case (c) — pay for oracle-approved PRs —
 * settle zero-touch while every payout stays attributable, revocable, and
 * inside the regression window. Content disclosure keeps its per-release human
 * gate (ownerDecision); money and disclosure are deliberately split.
 */
export interface SettlementPayoutAuthorization {
  readonly id: Id<"SettlementPayoutAuthorization">;
  readonly chamberId: Id<"Chamber">;
  /** The one human act. A system/operator principal may not author this. */
  readonly authorizedById: Id<"Principal">;
  readonly poolId: Id<"CreditPool">;
  readonly oracleId: Id<"EvaluatorOracle">;
  readonly priceScheduleId: Id<"PriceSchedule">;
  /** Matches acceptances eligible for zero-touch payout; anything outside falls back to human. */
  readonly matchPredicateHash: Hash;
  readonly perPayoutCeiling: CreditMicros;
  readonly windowCeiling: CreditMicros;
  readonly validWithin: TimeWindow;
  readonly revokedAt?: Timestamp;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface FeedProjectionPolicy {
  readonly schemaId: SchemaId;
  readonly allowedFields: readonly JsonPath[];
  readonly redactedFields: readonly JsonPath[];
  readonly maxLeakage: LeakageEstimate["class"];
  readonly noRawPrivatePayloads: true;
}

export interface AnnotationFeed {
  readonly id: Id<"AnnotationFeed">;
  readonly chamberId: Id<"Chamber">;
  readonly ownerVisibleName: string;
  readonly producerAgentId?: Id<"Principal">;
  readonly schemaId: SchemaId;
  readonly projection: FeedProjectionPolicy;
  readonly status: "draft" | "active" | "paused" | "closed";
}

export interface FeedSubscription {
  readonly id: Id<"FeedSubscription">;
  readonly chamberId: Id<"Chamber">;
  readonly feedId: Id<"AnnotationFeed">;
  readonly subscriberId: Id<"Principal">;
  readonly bountyId?: Id<"Bounty">;
  readonly grantId: Id<"Grant">;
  readonly visibility: Visibility;
  readonly reviewBeforeNotify: true;
  readonly active: boolean;
}

export interface TimeWindowLike {
  readonly startsAt: Timestamp;
  readonly endsAt: Timestamp;
}

export const MARKET_LAWS = {
  bountiesBuyAcceptedAnnotationsNotAccess: true,
  externalPaymentIsARelease: true,
  freeTextDoesNotEarnByDefault: true,
  evaluatorMustBeRoleSeparated: true,
  reuseCreditUsesDeclaredEdgesNotRawReplays: true,
  subscriptionsExposeProjectedAnnotationsOnly: true,
  bountiesNeverWidenAuthority: true,
  hiddenReuseIsSlashable: true,
  paymentSettlesOnOwnerInternalAcceptance: true,
  oracleVerdictsPriceOnlyAgainstPinnedRubrics: true,
  anOracleUpgradeIsANewOracle: true,
  roleSeparationIsCheckedOverBeneficialEntitiesNotIds: true,
  standingAuthorizationsMovePayoutsNeverContent: true,
  attributionSharesConserveThePot: true,
} as const;
