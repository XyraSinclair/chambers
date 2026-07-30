/**
 * Cross-chamber negotiation primitives.
 *
 * Two sovereign private worlds — major labs trading IP is the premier case —
 * negotiate by staged, reciprocal, escrowed disclosure. Neither side owns the
 * lane; each side's own review stack gates its own boundary. Claims are
 * committed before they are shown, verified before they are valued, and the
 * receipts each side keeps refuse to claim what was not verified.
 *
 * This generalizes matching's bilateral release: a consumer match is the
 * two-person special case of the same shape — commit, reciprocate, reveal in
 * stages, never retroactively.
 */

import type { Hash, Id, MinimizedText, ReceiptCaveat, Timestamp } from "./core";

export interface NegotiationLane {
  readonly id: Id<"NegotiationLane">;
  /** At least two sovereign chambers. The lane is between them, owned by none. */
  readonly partyChamberIds: readonly [Id<"Chamber">, Id<"Chamber">, ...Id<"Chamber">[]];
  readonly purpose: MinimizedText;
  readonly stageIds: readonly [Id<"RevealStage">, ...Id<"RevealStage">[]];
  /** Optional steward. Mediates sampling and escrow; is never a party. */
  readonly mediatorId?: Id<"Principal">;
  readonly symmetryRule: "strict_reciprocal" | "value_balanced" | "mediated";
  readonly state: "proposed" | "open" | "frozen" | "settled" | "abandoned";
  readonly frozenByChamberId?: Id<"Chamber">;
}

export type ClaimClass =
  | "capability"
  | "result"
  | "dataset_property"
  | "method"
  | "legal_right"
  | "valuation";

/**
 * A claim about private IP, committed by hash before anything is shown.
 * Verification runs inside a doubly-sealed environment: the verifier is
 * admitted by Grants from BOTH parties and its only sink is a verdict.
 */
export interface EscrowedClaim {
  readonly id: Id<"EscrowedClaim">;
  readonly laneId: Id<"NegotiationLane">;
  readonly claimantChamberId: Id<"Chamber">;
  readonly claimClass: ClaimClass;
  /** Hash of the claim artifact plus salt. The claim text stays home until its stage opens. */
  readonly commitmentHash: Hash;
  readonly verificationPlan: "none" | "mutual_verifier_run" | "third_party_audit" | "tee_replication";
  readonly verifierGrantIds: readonly Id<"Grant">[];
  readonly verdictArtifactId?: Id<"Artifact">;
  readonly state: "committed" | "under_verification" | "verified" | "failed" | "withdrawn";
}

/**
 * One rung of the ladder. A stage opens only when its required claims are
 * verified, its reciprocity condition holds, and — when disclosure itself is
 * priced — its price cross cleared. Each party spends its own egress budget;
 * there is no shared budget to hide behind.
 */
export interface RevealStage {
  readonly id: Id<"RevealStage">;
  readonly laneId: Id<"NegotiationLane">;
  readonly ordinal: number;
  readonly reciprocity: "simultaneous_commit_then_reveal" | "alternating" | "escrow_mediated";
  readonly requiredClaimIds: readonly Id<"EscrowedClaim">[];
  readonly perPartyEgressBudgetIds: readonly Id<"EgressBudget">[];
  readonly priceCrossId?: Id<"PriceCross">;
  readonly state: "locked" | "open" | "completed" | "skipped";
  readonly openedAt?: Timestamp;
}

/**
 * Each party keeps its own receipt for the same lane. Symmetric events,
 * asymmetric caveats: what you verified about them is not what they verified
 * about you.
 */
export interface CrossChamberReceipt {
  readonly id: Id<"CrossChamberReceipt">;
  readonly laneId: Id<"NegotiationLane">;
  readonly issuedToChamberId: Id<"Chamber">;
  readonly stageIds: readonly Id<"RevealStage">[];
  readonly verifiedClaimIds: readonly Id<"EscrowedClaim">[];
  readonly caveats: readonly ReceiptCaveat[];
  /** Freezing stops future stages. It cannot unsend the past. */
  readonly noRetroactiveUnreveal: true;
}

export const NEGOTIATION_LAWS = {
  neitherPartyOwnsTheLane: true,
  eachBoundaryIsGatedByItsOwnReviewStack: true,
  claimsCommitBeforeTheyReveal: true,
  verificationPrecedesValuation: true,
  stagesOpenOnReciprocityNotTrust: true,
  freezeStopsTheFutureNotThePast: true,
  walkAwayTimingIsItselfAnEmission: true,
} as const;
