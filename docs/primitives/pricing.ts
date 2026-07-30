/**
 * Pricing primitives.
 *
 * Prices are emissions. A willingness-to-pay curve over private work is
 * itself private data: it leaks valuation, urgency, and sometimes the secret
 * being valued. So this layer trades in commitments, samples, and crossings —
 * enough to clear a trade, as little as possible about either party's curve.
 *
 * The protocol shape: each side commits to a distribution of prices it is
 * happy to pay (bid) or charge (ask). A mediated sampler draws once from
 * each. The trade clears iff bid-draw >= ask-draw and every reserve is met.
 * A failed cross tells each side one bit — the draws did not align — and
 * still debits a composition budget, because repeated probing reconstructs
 * the curve it was designed to hide.
 */

import type { Bucket, Hash, Id, Score01, TimeWindow, Timestamp, Visibility } from "./core";
import type { CreditMicros } from "./market";

export type PriceFamily =
  | "point"
  | "uniform_bucketed"
  | "lognormal_bucketed"
  | "piecewise_bucketed"
  | "opaque_committed";

/**
 * A committed distribution over prices. The parameterization never crosses a
 * boundary; only its hash, coarse family class, and bucketed support do.
 */
export interface PriceDistribution {
  readonly id: Id<"PriceDistribution">;
  readonly holderId: Id<"Principal">;
  readonly side: "bid" | "ask";
  readonly resource: PricedResource;
  readonly family: PriceFamily;
  /** Hash of the full parameterization plus salt. Auditable after the fact; unreadable before. */
  readonly commitmentHash: Hash;
  readonly supportBucket: { readonly floor: Bucket; readonly ceiling: Bucket };
  readonly valid: TimeWindow;
  readonly revokedAt?: Timestamp;
}

export type PricedResource =
  | "attention_interruption"
  | "detail_expansion"
  | "review_minutes"
  | "disclosure"
  | "escrow_stage"
  | "match_introduction"
  | "accepted_work";

/**
 * One ledgered draw from a committed distribution, performed by a sampler
 * both sides accept (a steward, or the protocol itself). The nonce makes the
 * draw verifiable against the commitment in a later audit without revealing
 * the distribution to the counterparty now.
 */
export interface PriceSample {
  readonly id: Id<"PriceSample">;
  readonly distributionId: Id<"PriceDistribution">;
  readonly samplerId: Id<"Principal">;
  /**
   * The draw seed is a JOINTLY-committed coin: both parties commit nonces
   * (simultaneous_commit_then_reveal) before the draw is computable, and the
   * seed is derived from both. A later audit therefore covers SELECTION
   * fairness — a corrupt sampler cannot grind a nonce to steer whether the
   * cross clears — not just membership. The sampler may not be a party.
   */
  readonly coinCommitmentIds: readonly [Id<"CoinCommitment">, Id<"CoinCommitment">, ...Id<"CoinCommitment">[]];
  readonly seedHash: Hash;
  readonly value: CreditMicros;
  /** The sample's value is visible to the sampler and settlement, never to the counterparty. */
  readonly visibility: Extract<Visibility, "system_secret" | "owner_private">;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/** A floor under someone's scarce resource. The holder need not disclose why anyone would pay it. */
export interface ReservePrice {
  readonly id: Id<"ReservePrice">;
  readonly holderId: Id<"Principal">;
  readonly resource: PricedResource;
  readonly minimum: CreditMicros;
  /** The owner can sell attention without buying an explanation. */
  readonly purposeDisclosure: "none_required" | "coarse_class_only" | "full";
  readonly valid: TimeWindow;
}

/** One party's committed contribution to the joint draw coin. */
export interface CoinCommitment {
  readonly id: Id<"CoinCommitment">;
  readonly partyId: Id<"Principal">;
  readonly commitmentHash: Hash;
  readonly revealedAt?: Timestamp;
}

export type ClearingRule = "midpoint" | "ask_price" | "bid_price" | "second_price";

/**
 * The match event. Cleared or not, it is ledgered, debited, and composed:
 * a failed cross is an `absence` emission worth exactly one bit.
 */
export interface PriceCross {
  readonly id: Id<"PriceCross">;
  readonly bidSampleId: Id<"PriceSample">;
  readonly askSampleId: Id<"PriceSample">;
  readonly reserveIds: readonly Id<"ReservePrice">[];
  readonly outcome: "cleared" | "no_cross";
  readonly clearingRule: ClearingRule;
  readonly clearedPrice?: CreditMicros;
  /** By construction. A cross that reveals more than this is a different, worse protocol. */
  readonly counterpartyLearns: "one_bit";
  readonly compositionKeyId: Id<"CompositionKey">;
  readonly egressDebitId: Id<"EgressDebit">;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * An agent pays to surface a recommendation. The card reaches the owner only
 * if the cross cleared the owner's reserve; the owner is paid for attention
 * spent, independent of the decision they then make.
 */
export interface SurfacingBid {
  readonly id: Id<"SurfacingBid">;
  readonly cardId: Id<"ReviewCard">;
  readonly bidderId: Id<"Principal">;
  readonly priceCrossId: Id<"PriceCross">;
  readonly paidToId: Id<"Principal">;
  readonly amount: CreditMicros;
  readonly purposeDisclosed: "none" | "coarse_class" | "full";
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * Score-to-price, published before work starts. For oracle-evaluated work
 * (e.g. pull requests scored against a pinned rubric), payment is a monotone
 * step function of the verdict — not a negotiation after the sponsor has
 * already read the work.
 */
export interface PriceSchedule {
  readonly id: Id<"PriceSchedule">;
  readonly sponsorId: Id<"Principal">;
  readonly poolId: Id<"CreditPool">;
  /** Binds the schedule to one rubric version; a rubric change is a new schedule. */
  readonly rubricHash: Hash;
  readonly points: readonly [SchedulePoint, ...SchedulePoint[]];
  readonly holdbackFraction: Score01;
  /** Clawback window: accepted work that regresses inside it is slashable. */
  readonly regressionWindow: TimeWindow;
  readonly visibility: Visibility;
}

export interface SchedulePoint {
  readonly minScore: Score01;
  readonly amount: CreditMicros;
}

export const PRICING_LAWS = {
  curvesNeverCrossBoundariesOnlyCommitmentsDo: true,
  samplesAreLedgeredAndAuditableAgainstCommitments: true,
  failedCrossesRevealOneBitAndStillDebitComposition: true,
  attentionClearsAboveReserveBeforeAnyCardSurfaces: true,
  ownersMaySellAttentionWithoutBuyingAnExplanation: true,
  schedulesBindBeforeWorkStartsNotAfter: true,
  probingReservesIsAReconstructionAttack: true,
  samplerCoinIsJointlyCommittedBeforeDraw: true,
  samplerMayNotBeAParty: true,
} as const;
