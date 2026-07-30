/**
 * Coalitional inference primitives.
 *
 * A coalitional derivative is an artifact computed jointly over ≥2 private
 * silos whose information content is RELATIVE TO THE READER: the same bytes
 * can be zero bits to an outsider and total disclosure to a co-member.
 * Witness: Y = S_A xor S_B over independent uniform bits — I(Y; S_A) = 0 to
 * the public, H(S_B | Y, S_A) = 0 to Alice. Leakage is therefore never a
 * scalar property of an output; the only well-formed quantity is
 * I(Y; S_i | K_r) — leakage of source i to reader r given r's holdings.
 *
 * This module exists to close (partially, honestly) CANON open-frontier #5:
 * budgets in entropy.ts are absolute bits per ObserverClass; here leakage is
 * charged per (source chamber, reader beneficial entity), conditioned on a
 * DECLARED reader model, and accumulated for the lifetime of the pair —
 * across coalitions, across query families, across time. Confinement to the
 * generating coalition is the ZERO POINT of this metric (self-leakage is
 * free), not a fortress: cross-member exposure is maximal exactly when the
 * joint computation was worth doing (synergy IS cross-exposure).
 *
 * Standing non-claims: exact mutual information is uncomputable here — every
 * figure is an estimator-attested surrogate; reader models are declared, not
 * observed; the set of inferential targets of a derivative is unenumerable;
 * per-reader accounting inherits the identity problem (open frontier #1) and
 * undercounts against Sybil readers.
 */

import type {
  Bits,
  Bucket,
  Hash,
  Id,
  MinimizedText,
  SchemaId,
  Score01,
  Timestamp,
  Visibility,
} from "./core";
import type {
  CapacityEstimate,
  EstimatorAttestation,
  LeakageClass,
  ObserverClass,
} from "./entropy";
import type { CreditMicros } from "./market";

// ---- Reader models: the auxiliary-knowledge object ----

/** What a reader is assumed to already hold. The Dwork/Roth lesson, typed. */
export type ReaderKnowledgeBasis =
  | "own_silo"
  | "public_context"
  | "prior_releases_ledgered"
  | "declared_auxiliary"
  | "unknown_auxiliary";

/**
 * A declared model of one reader's prior holdings. DECLARED, not observed:
 * nothing here certifies what a reader actually knows. Low confidence does
 * not soften anything — it forces the unconditional ceiling to be charged
 * (see ReaderRelativeLeakage.chargedBits).
 */
export interface ReaderModel {
  readonly id: Id<"ReaderModel">;
  readonly readerEntityId: Id<"BeneficialEntity">;
  readonly bases: readonly ReaderKnowledgeBasis[];
  /** Ledgered releases assumed held: auditable part of the prior. */
  readonly priorReleaseIds: readonly Id<"Release">[];
  readonly declaredAuxiliary: readonly MinimizedText[];
  /** The honest boundary of the whole construct. */
  readonly auxiliaryIsDeclaredNotObserved: true;
  readonly confidence: "low" | "medium" | "high";
}

/**
 * Reader-relative leakage of one source silo through one observable/artifact.
 * Two figures, one charge: conditionalBits assumes the reader model holds;
 * unconditionalCeilingBits assumes nothing. chargedBits — the number that
 * debits the ExposureAccount — equals conditionalBits only when the reader
 * model is medium/high confidence; otherwise the ceiling is charged. Both are
 * adversarial-maximum bounds in the sense of entropy.ts CapacityEstimate.
 */
export interface ReaderRelativeLeakage {
  readonly id: Id<"ReaderRelativeLeakage">;
  readonly sourceChamberId: Id<"Chamber">;
  readonly readerModelId: Id<"ReaderModel">;
  readonly conditionalBits: Bits;
  readonly unconditionalCeilingBits: Bits;
  readonly chargedBits: Bits;
  readonly class: LeakageClass;
  readonly assumptions: readonly MinimizedText[];
  readonly estimator: EstimatorAttestation;
}

// ---- Coalitions: mutual-exposure consent, not a safe interior ----

/**
 * The set of chambers whose silos jointly feed derivatives. Formation is
 * mutual-exposure consent: each member accepts being read-about by the
 * others, charged at the adversarial maximum. No grant, no membership.
 */
export interface Coalition {
  readonly id: Id<"Coalition">;
  /** ≥2 by construction. */
  readonly memberChamberIds: readonly [Id<"Chamber">, Id<"Chamber">, ...Id<"Chamber">[]];
  /** One grant per member; membership without authority is unrepresentable. */
  readonly grantIds: readonly Id<"Grant">[];
  readonly exposureConsentIds: readonly Id<"ExposureConsent">[];
  readonly formedAt: Timestamp;
  readonly dissolvedAt?: Timestamp;
  /**
   * Gradients are egress: training on coalition outputs is a widening to the
   * model-user audience with unbounded retention. "forbidden_declared" is a
   * policy statement, not an enforcement claim.
   */
  readonly modelImprovementChannel: "forbidden_declared" | "dp_budgeted" | "unbounded_declared";
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * One member's acknowledgement, at formation, of what co-members may come to
 * know about their silo. The consent names a cap, not a promise: crossing the
 * cap forces a decision (like EgressBudget.onExhaustion), staying under it
 * proves nothing.
 */
export interface ExposureConsent {
  readonly id: Id<"ExposureConsent">;
  readonly coalitionId: Id<"Coalition">;
  readonly memberChamberId: Id<"Chamber">;
  /** Per co-member reader entity: the accepted lifetime cross-exposure cap. */
  readonly perCounterpartCapBits: Bits;
  readonly acknowledgesSynergyIsCrossExposure: true;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * Interaction-information estimate for a derivative: how much of its content
 * exists only jointly. Positive synergy is the value signal AND the
 * cross-exposure signal — the same quantity read from two sides. The estimate
 * INFORMS pricing and review; the exposure charge stays at the adversarial
 * maximum regardless (a low synergy estimate never discounts a debit).
 */
export interface SynergyEstimate {
  readonly id: Id<"SynergyEstimate">;
  readonly derivativeId: Id<"CoalitionalDerivative">;
  readonly jointOnlyFraction: Score01;
  readonly confidenceInterval: readonly [Score01, Score01];
  readonly gameabilityCaveat: MinimizedText;
  readonly estimator: EstimatorAttestation;
}

// ---- The derivative and its custody ----

/**
 * An artifact whose provenance names ≥2 source silos. Its default audience is
 * the generating coalition — the zero-cost release, because self-leakage is
 * free — and any wider audience is a WideningEvent. Typed (schema-bound)
 * because typing is what caps channel capacity and makes the ledger
 * arithmetic decidable; prose derivatives stay owner/escrow-private.
 */
export interface CoalitionalDerivative {
  readonly id: Id<"CoalitionalDerivative">;
  readonly coalitionId: Id<"Coalition">;
  readonly runId: Id<"Run">;
  readonly artifactId: Id<"Artifact">;
  readonly sourceChamberIds: readonly [Id<"Chamber">, Id<"Chamber">, ...Id<"Chamber">[]];
  readonly schemaId: SchemaId;
  readonly capacity: CapacityEstimate;
  /**
   * Where the full latent lives. Synergistic reasoning traces are the
   * high-capacity channel, so the default is escrow: members see typed
   * projections, not the trace.
   */
  readonly latentCustody: "escrowed_full_latent" | "member_visible";
  readonly audience: "generating_coalition";
  readonly projectionIds: readonly Id<"IntraCoalitionProjection">[];
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

/**
 * What one member actually sees of the derivative — with the cross-leakage
 * that seeing it costs every OTHER member, each debited to the corresponding
 * ExposureAccount.
 */
export interface IntraCoalitionProjection {
  readonly id: Id<"IntraCoalitionProjection">;
  readonly derivativeId: Id<"CoalitionalDerivative">;
  readonly viewerChamberId: Id<"Chamber">;
  readonly projectionArtifactId: Id<"Artifact">;
  readonly capacity: CapacityEstimate;
  /** One entry per non-viewer source silo. */
  readonly crossLeakageIds: readonly Id<"ReaderRelativeLeakage">[];
}

// ---- The ledger: (source × reader), lifetime, cross-coalition ----

/**
 * THE object of the module. Keyed by (source chamber, reader beneficial
 * entity) — not by coalition, not by query family, not by window — because
 * the cross-coalition accumulation attack (join many small coalitions that
 * each include the target; compose the individually-safe slices) is invisible
 * to any narrower key. Monotone, lifetime-scoped, audience-independent.
 *
 * Keyed over BeneficialEntity per CORE_LAWS role-separation discipline; this
 * MITIGATES but does not solve Sybil readers — an entity that fragments
 * identities fragments its account. The weakest linkage confidence is
 * recorded so undercounting is at least visible.
 */
export interface ExposureAccount {
  readonly id: Id<"ExposureAccount">;
  readonly sourceChamberId: Id<"Chamber">;
  readonly readerEntityId: Id<"BeneficialEntity">;
  readonly scope: "pair_lifetime";
  /** Monotone non-decreasing Σ of ExposureDebit.leakage.chargedBits. */
  readonly cumulativeChargedBits: Bits;
  readonly ceilingBits: Bits;
  readonly debitIds: readonly Id<"ExposureDebit">[];
  readonly readerLinkageConfidence: "low" | "medium" | "high";
  readonly sybilUndercountRisk: "low" | "medium" | "high" | "unknown";
  readonly onExhaustion: "owner_review" | "redact" | "delay" | "block";
}

/** Every debit ties an account movement to the event that caused it. */
export interface ExposureDebit {
  readonly id: Id<"ExposureDebit">;
  readonly accountId: Id<"ExposureAccount">;
  readonly leakageId: Id<"ReaderRelativeLeakage">;
  readonly derivativeId?: Id<"CoalitionalDerivative">;
  readonly wideningEventId?: Id<"WideningEvent">;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

// ---- Widening: the priced one-way door ----

/**
 * Destroyed-option-value estimate for one member if the audience widens.
 * ESTIMATED lane: evidence-backed, calibrated, gameable — a price input,
 * never a payoff cliff. It sets the floor of a widening price; it never
 * auto-approves or auto-blocks anything.
 */
export interface OptionValueEstimate {
  readonly id: Id<"OptionValueEstimate">;
  readonly wideningEventId: Id<"WideningEvent">;
  readonly memberChamberId: Id<"Chamber">;
  readonly destroyedValueMicros: CreditMicros;
  readonly confidenceInterval: readonly [Score01, Score01];
  readonly gameabilityCaveat: MinimizedText;
  readonly estimatorRole: "price_input";
  readonly estimator: EstimatorAttestation;
}

/**
 * Third parties a derivative is informative ABOUT despite contributing
 * nothing: affected strictly exceeds contributing (the sibling's genome, the
 * colleague's calendar, the market's structure). Named targets are screened;
 * the unenumerable remainder is a standing non-claim, typed as a flag no
 * receipt may drop.
 */
export interface InferentialTargetScreen {
  readonly id: Id<"InferentialTargetScreen">;
  readonly derivativeId: Id<"CoalitionalDerivative">;
  readonly namedTargets: readonly InferentialTarget[];
  readonly unenumeratedTargetsRemain: true;
  readonly reviewId: Id<"Review">;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface InferentialTarget {
  /** Salted reference — the screen must not itself become a disclosure. */
  readonly subjectRef: Hash;
  readonly basis: "correlated_data" | "relational" | "group_membership" | "market_structure";
  readonly verdict: "negligible" | "material" | "blocked" | "unprovable";
  readonly rationale: MinimizedText;
}

/**
 * Audience expansion beyond the generating coalition. A new ledgered event,
 * never a side effect; one-way, because disclosure is entropy-irreversible —
 * the resource being spent is optionality. Requires unanimous member consent,
 * an inferential-target screen, and a core Release (which carries the human
 * owner-decision law). The price floor is the sum of destroyed option value —
 * as a price input.
 */
export interface WideningEvent {
  readonly id: Id<"WideningEvent">;
  readonly derivativeId: Id<"CoalitionalDerivative">;
  readonly toAudience: ObserverClass | { readonly coalitionId: Id<"Coalition"> };
  /** Unanimous by construction: one Release per member, each owner-decided. */
  readonly memberReleaseIds: readonly [Id<"Release">, ...Id<"Release">[]];
  readonly screenId: Id<"InferentialTargetScreen">;
  readonly optionValueEstimateIds: readonly Id<"OptionValueEstimate">[];
  readonly clearedPriceMicros: CreditMicros;
  readonly oneWay: true;
  readonly occurredAt: Timestamp;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

// ---- Metadata: silence is a channel ----

/**
 * Coalition existence, membership, cadence, and silence are observables. "You
 * were not matched" and "no computation ran this month" carry bits. Cover
 * traffic and padded cadence are mitigations with a named public claim —
 * never a certificate.
 */
export interface ActivityCoverPolicy {
  readonly id: Id<"ActivityCoverPolicy">;
  readonly coalitionId: Id<"Coalition">;
  readonly formationVisibility: Visibility;
  readonly dummyRunRate: Bucket;
  readonly cadence: "padded" | "batched" | "natural";
  readonly nonMembershipObservableRisk: "low" | "medium" | "high" | "unknown";
  readonly publicClaim: "no_claim" | "padded" | "covered";
}

// ---- The duality conjecture, held loosely ----

/**
 * Credit basis for one member's contribution to a derivative: conditional
 * information given the other silos — the same measure the exposure ledger
 * tracks, read with the opposite sign. Replication-resistant by construction
 * (copies contribute zero conditional information). CONJECTURE-lane: bits are
 * the accounting basis, not the value — one decisive bit can outprice a
 * megabyte of texture, so this is a price input, never a payoff cliff.
 */
export interface ContributionCredit {
  readonly id: Id<"ContributionCredit">;
  readonly derivativeId: Id<"CoalitionalDerivative">;
  readonly memberChamberId: Id<"Chamber">;
  readonly conditionalBitsBasis: Bits;
  readonly creditMicros: CreditMicros;
  readonly dualityCaveat: MinimizedText;
  readonly estimatorRole: "price_input";
  readonly estimator: EstimatorAttestation;
}

export const COALITION_LAWS = {
  /** No scalar leakage: every estimate names its reader model. */
  leakageIsReaderRelative: true,
  /** Auxiliary knowledge is declared, not observed; low confidence charges the unconditional ceiling. */
  readerModelsAreDeclaredNotObserved: true,
  /** Confinement neutralizes self-leakage only; the coalition is the metric's zero, not a wall. */
  coalitionIsTheZeroPointNotAFortress: true,
  /** Cross-member exposure is charged at the adversarial maximum and consented at formation. */
  synergyIsCrossExposure: true,
  /** The ledger key is (source chamber, reader entity), lifetime, across all coalitions. */
  exposureAccountsAreSourceByReader: true,
  /** Named dependency on open frontier #1: Sybil readers undercount; linkage confidence is recorded. */
  perReaderAccountingPresupposesIdentity: true,
  /** Audience expansion is a new ledgered event, never a side effect; it is one-way. */
  wideningIsAPricedOneWayEvent: true,
  /** Destroyed option value prices the door; it never gates it. */
  optionValueIsAPriceInputNeverACliff: true,
  /** Inferential targets exceed contributors; every widening screens named targets and admits the remainder. */
  affectedExceedsContributing: true,
  /** Training on coalition outputs is a widening to the model-user audience. */
  gradientsAreEgress: true,
  /** Formation, membership, cadence, and silence are emissions with policies. */
  coalitionMetadataIsAnEmission: true,
  /**
   * CONJECTURE, deliberately not asserted: payment and exposure may be one
   * measure with two signs (conditional information). Recorded as an
   * accounting basis with a caveat, not as a law.
   */
  creditAndExposureShareOneMeasure: false,
} as const;
