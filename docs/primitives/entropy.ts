/**
 * Entropy and obfuscation primitives.
 *
 * This layer does not claim formal secrecy. It names observer-visible surfaces,
 * budgets them crudely, and records how the system bucketed, delayed, padded,
 * suppressed, or blocked emissions. It attaches to core LedgerEntry records.
 */

import type {
  Bits,
  Bucket,
  Gate,
  Hash,
  Id,
  JsonPath,
  MinimizedText,
  Precision,
  RiskClass,
  Score01,
  Seconds,
  Timestamp,
  Visibility,
} from "./core";

export type Surface =
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

export type ObserverClass =
  | "owner"
  | "requester"
  | "sponsor"
  | "reviewer"
  | "operator"
  | "support"
  | "notifier"
  | "public";

export type ObservableKind =
  | "answer_field"
  | "status_state"
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
  | "notification_timing"
  | "receipt_claim"
  | "cache_hit"
  | "billing_line"
  | "support_bundle_field"
  /** A missing result is an observation. Silence has a type. */
  | "absence";

export type LeakageClass = "none" | "negligible" | "bounded" | "material" | "unsafe" | "unknown";
export type ObfuscationAction = "pass" | "bucket" | "round" | "delay" | "jitter" | "pad" | "suppress" | "block";

export interface ObservablePolicy {
  readonly id: Id<"ObservablePolicy">;
  readonly surface: Surface;
  readonly observer: ObserverClass;
  readonly fieldPaths: readonly JsonPath[];
  readonly allowedKinds: readonly ObservableKind[];
  readonly precision: Precision;
  readonly cadence: "immediate" | "delayed" | "batched" | "release_only" | "never";
  readonly maxBits: Bits;
  readonly secretDependentBranching: "forbidden" | "padded_only" | "owner_only";
}

export interface ObfuscationPlan {
  readonly id: Id<"ObfuscationPlan">;
  readonly policyId: Id<"ObservablePolicy">;
  readonly actions: readonly ObfuscationStep[];
  readonly publicClaim: "no_claim" | "bucketed" | "delayed" | "padded" | "suppressed";
}

export interface ObfuscationStep {
  readonly kind: ObfuscationAction;
  readonly appliesTo: readonly ObservableKind[];
  readonly bucket?: Bucket;
  readonly delayFloor?: Seconds;
  readonly delayCeiling?: Seconds;
  readonly padToBucket?: Bucket;
  readonly reason: MinimizedText;
}

export interface ObservableEvent {
  readonly id: Id<"ObservableEvent">;
  readonly runId: Id<"Run">;
  readonly gate: Gate;
  readonly surface: Surface;
  readonly observer: ObserverClass;
  readonly kind: ObservableKind;
  readonly occurredAt: Timestamp;
  readonly rawVisibility: Visibility;
  readonly projectedPrecision: Precision;
  readonly obfuscationPlanId?: Id<"ObfuscationPlan">;
  readonly leakage: LeakageEstimate;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * Who computed an estimate, and how much to trust it. Every budget is only as
 * sound as its estimator; an unattributed estimate is an unbounded silent hole.
 * A self-interested estimator (the paid agent itself) understating side-channel
 * bits breaks every budget invisibly — so the estimator is named and its
 * independence recorded.
 */
export interface EstimatorAttestation {
  readonly estimatorId: Id<"Principal">;
  readonly independence: "self_interested" | "operator" | "role_separated" | "adversarial_review";
  readonly method: "static_schema_bound" | "sampled" | "adversarial_probe" | "declared";
  /** True iff the estimate is a worst-case bound over all schema-consistent secrets. */
  readonly worstCaseOverSecrets: boolean;
}

export interface LeakageEstimate {
  readonly class: LeakageClass;
  readonly bitsBucket: Bucket;
  readonly uniquenessRisk: "common_pattern" | "small_group" | "unique_episode" | "unknown";
  readonly compositionRisk: "single" | "accumulates_with_prior_receipts" | "repeated_query_attack" | "unknown";
  readonly riskClasses: readonly RiskClass[];
  readonly assumptions: readonly MinimizedText[];
  readonly estimator: EstimatorAttestation;
}

export interface CompositionKey {
  readonly id: Id<"CompositionKey">;
  readonly chamberId: Id<"Chamber">;
  readonly subjectHash: Hash;
  readonly queryFamilyHash: Hash;
  readonly audienceHash: Hash;
  readonly sponsorHash?: Hash;
  readonly windowHash: Hash;
}

export interface CompositionState {
  readonly keyId: Id<"CompositionKey">;
  readonly releaseIds: readonly Id<"Release">[];
  readonly observableEventIds: readonly Id<"ObservableEvent">[];
  readonly cumulativeLeakage: LeakageClass;
  /**
   * Authoritative monotone-non-decreasing Σ of EgressDebit.estimate over this
   * key. Binds STRUCTURED channels only (schema fields, orderings, buckets,
   * price crosses, denominators) — summing free-text upper bounds either
   * saturates or under-counts, so prose stays on cumulativeLeakage + review.
   * This is what makes repeated-probe reconstruction actually block.
   */
  readonly cumulativeStructuredBits: Bits;
  readonly structuredBitsCeiling: Bits;
  /**
   * Conjunction: "allow" requires BOTH cumulativeStructuredBits < ceiling AND
   * the ordinal/EntropyReview gate permitting. Either alone forces non-allow;
   * neither alone certifies allow.
   */
  readonly releaseGate: "allow" | "owner_review" | "redact" | "block";
  readonly numericAccountantTripped: boolean;
  readonly reviewerConfidence: "low" | "medium" | "high";
}

export interface CapacityEstimate {
  /**
   * schemaBits is charged at the ADVERSARIAL MAXIMUM, not honest-case usage: a
   * malicious agent steganographically encodes secrets in legal enum values,
   * field presence, and ordering permutations. Split so each is log2 of its
   * legal choice space and the sum is auditable.
   */
  readonly schemaBits: Bits;
  readonly enumValueBits: Bits;
  readonly orderingBits: Bits;
  readonly fieldPresenceBits: Bits;
  readonly textBitsUpperBound: Bits;
  readonly metadataBits: Bits;
  readonly sideChannelBits: Bits;
  readonly cumulativeBits: Bits;
  readonly qualitative: LeakageClass;
  readonly assumptions: readonly MinimizedText[];
  readonly estimator: EstimatorAttestation;
}

export interface DenominatorGuard {
  readonly id: Id<"DenominatorGuard">;
  readonly compositionKeyId: Id<"CompositionKey">;
  readonly minGroupSize: number;
  readonly revealDenominator: "never" | "bucket_only" | "owner_only";
  readonly zeroOneManyOnly: boolean;
  readonly suppressWhenExternallyIdentifiable: true;
  readonly currentSizeBucket: Bucket;
  readonly risk: "low" | "medium" | "high" | "unknown";
}

/**
 * A budget over what one observer class may learn, per composition scope.
 * Estimates are conservative tripwires, not certificates: exhausting a budget
 * forces a decision; staying under one proves nothing.
 */
export interface EgressBudget {
  readonly id: Id<"EgressBudget">;
  readonly chamberId: Id<"Chamber">;
  readonly grantId?: Id<"Grant">;
  readonly observer: ObserverClass;
  readonly scope: "run" | "grant" | "query_family" | "audience_window" | "chamber_lifetime";
  readonly compositionKeyId: Id<"CompositionKey">;
  readonly maxSchemaBits: Bits;
  readonly maxTextBitsUpperBound: Bits;
  readonly maxMetadataBits: Bits;
  readonly maxSideChannelBits: Bits;
  readonly repeatedQueryComposition: "bounded" | "blocked";
  readonly onExhaustion: "owner_review" | "redact" | "delay" | "block";
}

/** Every debit is a ledgered event tied to what was actually observed or released. */
export interface EgressDebit {
  readonly id: Id<"EgressDebit">;
  readonly budgetId: Id<"EgressBudget">;
  readonly observableEventId?: Id<"ObservableEvent">;
  readonly releaseId?: Id<"Release">;
  readonly estimate: CapacityEstimate;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface EntropyReview {
  readonly id: Id<"EntropyReview">;
  readonly runId: Id<"Run">;
  readonly compositionKeyId: Id<"CompositionKey">;
  readonly observableEventIds: readonly Id<"ObservableEvent">[];
  readonly decision: "allow" | "bucket_more" | "delay" | "owner_only" | "block";
  readonly rationale: MinimizedText;
  readonly confidence: Score01;
}

export const ENTROPY_LAWS = {
  everyNonOwnerObservableHasPolicy: true,
  exactOperationalSignalsOwnerPrivate: true,
  repeatedQueriesCompose: true,
  denominatorLeakageBlocksRelease: true,
  noPerfectPrivacyClaim: true,
  budgetsAreTripwiresNotCertificates: true,
  absenceIsAnEmission: true,
  capacityIsChargedAtAdversarialMaximum: true,
  releaseGateIsConjunctionOfNumericAndOrdinal: true,
  everyEstimateNamesItsEstimator: true,
  numericAccountantBindsStructuredChannelsNotProse: true,
} as const;
