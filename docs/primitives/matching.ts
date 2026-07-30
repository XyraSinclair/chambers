/**
 * Matchmaking primitives.
 *
 * Matching stresses the whole model because the valuable fact is often exactly
 * the sensitive fact: this person is unusually good for that person or role.
 * The result may be safe for neither party alone until consent, denominator,
 * and symmetry rules hold. No one receives a live list of who nearly matched
 * them. The safe primitive is a mediated candidate relation, not a public
 * ranker over private people.
 */

import type { Bucket, Hash, Id, MinimizedText, SchemaId, Timestamp } from "./core";
import type { LeakageEstimate } from "./entropy";

export type MatchPurpose = "dating" | "hiring" | "collaboration" | "advising" | "grantmaking";
export type RelationKind = "pair" | "team" | "role_fit" | "mentor_match";

/**
 * When is a match result unsafe because the pool is small, externally
 * enumerable, or audience-overlapping? Enforced via the entropy layer's
 * DenominatorGuard; this is the policy the guard instantiates.
 */
export interface DenominatorPolicy {
  readonly minGroupSize: number;
  readonly revealDenominator: "never" | "bucket_only" | "owner_only";
  readonly zeroOneManyOnly: boolean;
  readonly audienceOverlapLimit: Bucket;
  readonly suppressWhenExternallyIdentifiable: true;
}

export interface DenominatorSummary {
  readonly poolHash: Hash;
  readonly sizeBucket: Bucket;
  readonly externalIdentifiabilityRisk: "low" | "medium" | "high" | "unknown";
}

export interface ConsentPolicy {
  readonly requiredFrom: "all_members" | "owner_then_counterparty" | "steward_mediated";
  readonly consentSchemaId: SchemaId;
  /** A denial is private. The counterparty learns nothing, including timing. */
  readonly denialVisibleToCounterparty: false;
  readonly timeoutDecision: "silent_expire" | "owner_private_reject";
}

/** Consent is itself a ledgered, revocable record — never an implicit state. */
export interface ConsentRecord {
  readonly id: Id<"ConsentRecord">;
  readonly relationId: Id<"CandidateRelation">;
  readonly memberId: Id<"Principal">;
  readonly decision: "granted" | "declined" | "expired" | "revoked";
  readonly decidedAt?: Timestamp;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface BilateralReleasePolicy {
  readonly releaseMode: "symmetric" | "staged" | "mediated";
  readonly firstMessageSchemaId: SchemaId;
  readonly revealScore: "never" | "bucket_only";
  readonly revealRationale: "none" | "owner_edited" | "steward_minimized";
  readonly receiptToEachParty: true;
}

export interface MatchBounty {
  readonly id: Id<"Bounty">;
  readonly sponsorId: Id<"Principal">;
  readonly purpose: MatchPurpose;
  readonly matchSchemaId: SchemaId;
  readonly denominatorPolicy: DenominatorPolicy;
  readonly consentPolicy: ConsentPolicy;
  readonly bilateralReleasePolicy: BilateralReleasePolicy;
  readonly maxCandidateRelationsPerWindow: Bucket;
}

export interface CandidateRelation {
  readonly id: Id<"CandidateRelation">;
  readonly bountyId: Id<"Bounty">;
  readonly memberIds: readonly [Id<"Principal">, ...Id<"Principal">[]];
  readonly memberScopeHashes: readonly Hash[];
  readonly relationKind: RelationKind;
  readonly scoreBucket: Bucket;
  /** Owner-private until every consent gate clears. */
  readonly rationaleArtifactId: Id<"Artifact">;
  readonly denominator: DenominatorSummary;
  readonly denominatorGuardId: Id<"DenominatorGuard">;
  /**
   * When introductions are priced, the relation may surface only after a
   * cleared cross of the parties' committed price distributions (pricing.ts).
   * The owners need not learn the purpose to be paid for the look.
   */
  readonly priceCrossId?: Id<"PriceCross">;
  readonly leakage: LeakageEstimate;
  readonly state:
    | "proposed"
    | "consent_pending"
    | "bilateral_release_ready"
    | "released"
    | "rejected"
    | "expired";
  readonly caveats: readonly MinimizedText[];
}

export const MATCHING_LAWS = {
  noLiveNearMissLists: true,
  pricedIntroductionsClearBeforeTheySurface: true,
  denialsAreInvisibleToCounterparties: true,
  relationsStayOwnerPrivateUntilAllConsentClears: true,
  denominatorLeakageBlocksMatchRelease: true,
  scoresAndRationalesReleaseOnlyAsBucketsOrMediatedText: true,
} as const;
