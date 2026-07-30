/**
 * Mediation primitives: tuple-scoped structure judgements, canonicality
 * review of guest agents, autonomy envelopes, and entropy pools for
 * unlinkable settlement.
 *
 * The scenario this module types: an agent is admitted to view an EXACT
 * k-tuple of sovereign repositories (k = 2, 3, 4…), forms a typed judgement
 * about the structure that exists only across them — overlap, duplication,
 * contradiction, complementarity, fit, a shared frontier — and stores that
 * judgement scoped to precisely that tuple. The judgement is readable inside
 * the tuple and nowhere else; any wider audience is a WideningEvent
 * (coalition.ts). Owners do not read much: review agents judge whether the
 * worker agent is canonical (as simple as its objective permits) and whether
 * what it returns to the REQUESTER over-reveals; settlement flows through
 * pools so that payment timing and amount do not become the leak.
 *
 * Standing non-claims: canonicality review is judgment, not proof — the
 * verdict lane admits "unprovable"; pool unlinkability presupposes identity
 * (frontier #1) and an anonymity set that actually exists; the requester's
 * memory of what they read is the human-head channel, unmodeled.
 */

import type {
  Bits,
  Bucket,
  Hash,
  Id,
  MinimizedText,
  SchemaId,
  Score01,
  Seconds,
  Timestamp,
} from "./core";
import type { CapacityEstimate, EstimatorAttestation } from "./entropy";
import type { CreditMicros } from "./market";

// ---- Structure judgements: typed relations over exact k-tuples ----

/**
 * What kind of cross-silo structure a judgement asserts. Closed enum on
 * purpose: each kind is a typed, capacity-bounded claim, not prose.
 */
export type StructureKind =
  | "overlap"
  | "duplicate"
  | "contradiction"
  | "complement"
  | "fit"
  | "gap"
  | "shared_frontier"
  | "risk"
  | "opportunity"
  | "non_relation";

/**
 * A typed judgement over an EXACT tuple of chambers. It refines
 * CoalitionalDerivative (coalition.ts): the derivative machinery carries
 * capacity caps, per-member projections, and exposure debits; this record
 * adds the judgement semantics and the exact-tuple scope discipline.
 *
 * tupleKey = hash of the canonically sorted member chamber ids. The scope is
 * the IDENTITY of the judgement: the same relation observed over a different
 * tuple is a different judgement. Visibility to any subset or superset of
 * the tuple is not an implementation detail — it is a WideningEvent.
 *
 * "non_relation" is first-class: the agent looked and found nothing. Recorded
 * with the same confinement, because absence is an emission (ENTROPY_LAWS)
 * and "these two repos have no overlap" is itself tradable structure.
 */
export interface StructureJudgement {
  readonly id: Id<"StructureJudgement">;
  readonly derivativeId: Id<"CoalitionalDerivative">;
  readonly tupleKey: Hash;
  readonly memberChamberIds: readonly [Id<"Chamber">, Id<"Chamber">, ...Id<"Chamber">[]];
  readonly kind: StructureKind;
  /** Typed stance payload, schema-bound; never free prose by default. */
  readonly schemaId: SchemaId;
  readonly stanceArtifactId: Id<"Artifact">;
  readonly confidence: Score01;
  /** Four-lane discipline (iptrade.ts): estimates never promote themselves. */
  readonly evidenceLane: "proven" | "trusted" | "estimated" | "unprovable";
  readonly estimator: EstimatorAttestation;
  /** Judgements decay: stale structure misleads. Re-derivation is a new run. */
  readonly validUntil?: Timestamp;
  readonly supersedesId?: Id<"StructureJudgement">;
  readonly revokedAt?: Timestamp;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * The queryable index entry for judgements a chamber participates in — the
 * owner-facing view. Owners see that a judgement exists, its kind, and its
 * capacity charge before deciding to read it: reading a synergistic
 * judgement is itself an exposure event for the OTHER members.
 */
export interface JudgementIndexEntry {
  readonly judgementId: Id<"StructureJudgement">;
  readonly viewerChamberId: Id<"Chamber">;
  readonly kind: StructureKind;
  readonly tupleSizeBucket: Bucket;
  readonly readCostBitsToOthers: Bits;
  readonly state: "unread" | "read" | "revoked" | "expired";
}

// ---- Canonicality review: is the agent as simple as the objective permits? ----

/**
 * Pre-admission (and pre-release) review of a guest agent by a REVIEW AGENT,
 * because owners will not read much: the review must compress to a card.
 *
 * Two comparisons anchor the verdict:
 * 1. requested vs justified CAPACITY — the least-authority check, in bits.
 *    Excess capacity is denied by default, not negotiated afterwards.
 * 2. returned vs needed DISCLOSURE — what flows back to the requester is
 *    screened as a reading event like any other: the requester is a reader
 *    in the exposure ledger, not a privileged sink.
 */
export interface CanonicalityReview {
  readonly id: Id<"CanonicalityReview">;
  readonly reviewerId: Id<"Principal">;
  readonly reviewerEntityId: Id<"BeneficialEntity">;
  readonly agentPackageHash: Hash;
  readonly declaredObjective: MinimizedText;
  readonly requestedCapacity: CapacityEstimate;
  /** Reviewer's bound on what the declared objective actually needs. */
  readonly justifiedCapacity: CapacityEstimate;
  /** Could a strictly simpler agent (fewer tools, narrower schema) meet the objective? */
  readonly simplerAgentSuffices: "no" | "yes" | "unprovable";
  readonly requesterOverexposure: "none_found" | "flagged" | "blocking" | "unprovable";
  readonly verdict: "admit" | "narrow" | "reject" | "unprovable";
  readonly narrowingHints: readonly MinimizedText[];
  readonly reviewCardId?: Id<"ReviewCard">;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

// ---- Autonomy envelopes: objectives achieved without owner reading ----

/**
 * The contract under which an agent works autonomously. Owners see cards and
 * gates, not corpora; the envelope is what makes that safe to say. Success
 * criteria carry the four-lane discipline — an "estimated" objective may
 * inform payment size (continuous) but never auto-release a disclosure
 * (discontinuous).
 */
export interface AutonomyEnvelope {
  readonly id: Id<"AutonomyEnvelope">;
  readonly grantId: Id<"Grant">;
  readonly objectiveSchemaId: SchemaId;
  readonly objectiveArtifactId: Id<"Artifact">;
  readonly successLane: "proven" | "trusted" | "estimated" | "unprovable";
  readonly maxAttentionDebits: number;
  /** Per counterpart chamber: exposure this envelope may spend (coalition.ts accounts). */
  readonly maxExposureBitsPerCounterpart: Bits;
  readonly maxSpendMicros: CreditMicros;
  readonly escalation: "owner_card" | "pause" | "abort";
  readonly expiresAt: Timestamp;
}

// ---- Entropy pools: settlement without a timing/amount side channel ----

/**
 * A payout is an emission: its timing, amount, and counterparty identify
 * which computation paid, which judgement matched, which silo was consulted.
 * An entropy pool is the ObfuscationPlan for money — contributions flow in,
 * disbursements leave batched, delayed, and value-bucketed, so a payee
 * cannot be linked to a specific run by an observer of the payment surface
 * (including the payee themselves: "you were paid from the pool this epoch"
 * rather than "this intro paid you").
 *
 * Claims are honest and default to nothing: unlinkability is stated as the
 * anonymity-set bucket actually achieved at disbursement time, never as a
 * property of the mechanism. A pool with two participants hides nothing.
 */
export interface EntropyPool {
  readonly id: Id<"EntropyPool">;
  readonly chamberScope: "single_chamber" | "coalition" | "market_wide";
  readonly batchCadence: "epoch" | "threshold" | "randomized";
  readonly delayFloor: Seconds;
  readonly delayCeiling: Seconds;
  /** Disbursement amounts round to buckets; exact values never leave. */
  readonly valueBucketing: "none" | "round_amounts" | "fixed_denominations";
  readonly minAnonymitySetSize: number;
  readonly publicClaim: "no_claim" | "batched" | "delayed" | "bucketed" | "k_anonymous_bucket";
  /** Frontier #1 again: a Sybil payee fragments the set; recorded, not solved. */
  readonly anonymitySetPresupposesIdentity: true;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * One disbursement from a pool. References the market rib's payout
 * authorization so money/content separation laws carry: pools move PAYMENTS
 * on standing authorization; they never move content, and they never widen
 * authority.
 */
export interface PoolDisbursement {
  readonly id: Id<"PoolDisbursement">;
  readonly poolId: Id<"EntropyPool">;
  readonly payoutAuthorizationId: Id<"SettlementPayoutAuthorization">;
  readonly beneficiaryEntityId: Id<"BeneficialEntity">;
  readonly amountBucket: Bucket;
  readonly exactAmountVisibility: "owner_private" | "beneficiary_private";
  readonly anonymitySetSizeAtDisbursement: Bucket;
  readonly disbursedAt: Timestamp;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export const MEDIATION_LAWS = {
  /** A judgement's scope IS its identity: exact tuple, canonically keyed. */
  structureJudgementsAreTupleScoped: true,
  /** Sub/superset visibility is a WideningEvent, never an implementation detail. */
  tupleScopeChangesAreWidenings: true,
  /** Every judgement is a CoalitionalDerivative first — capacity caps and exposure debits inherit. */
  judgementsAreDerivativesFirst: true,
  /** "We found no relation" is a judgement with the same confinement: absence is an emission. */
  nonRelationIsAJudgement: true,
  /** Reading a judgement debits the OTHER members' exposure accounts; owners see the price first. */
  readingIsAnExposureEvent: true,
  /** Admission compares requested to justified capacity; excess is denied by default. */
  reviewComparesRequestedToJustifiedCapacity: true,
  /** The reviewer prefers the least-capable agent that meets the objective. */
  canonicalityIsLeastAuthority: true,
  /** The requester is a reader in the exposure ledger, not a privileged sink. */
  requesterIsAReader: true,
  /** Estimated success criteria size payments; they never auto-release disclosures. */
  estimatedObjectivesNeverGateDisclosure: true,
  /** Payout timing, amount, and counterparty are emissions with policies. */
  paymentsAreEmissions: true,
  /** Pools are obfuscation plans for money; claims state the set achieved, not the mechanism hoped. */
  poolClaimsAreAchievedNotHoped: true,
  /** Pools move payments on standing authorization; never content, never authority. */
  poolsNeverMoveContent: true,
} as const;
