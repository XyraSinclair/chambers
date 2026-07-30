/**
 * Confidential IP-trade primitives.
 *
 * Lets sovereign labs — and independent researchers — trade IP (checkpoints,
 * adapters, curated datasets, techniques) with verification-before-valuation,
 * atomic exchange, and honest partitioning of what was proven, what is merely
 * trusted, and what nobody can establish.
 *
 * Grounded in what is actually feasible in 2026 (a 105-agent, crypto-reality-
 * checked pass — see ../frontier/ip-trades/): TEE remote attestation,
 * commitments, optimistic/escrow fair exchange, watermarking, and audit-rights
 * licensing SHIP NOW. MPC/FHE carry only small computations. ZK at model scale
 * is research-horizon; ZK-proving a training run is geologic-scale absurd. So
 * this module leans on NAMED trust roots (hardware vendor, TTP, reputation),
 * never on trustlessness it does not have — and it says so in every receipt.
 *
 * The cardinal rule, enforced by types: there is NO boolean `verified`. Every
 * verification resolves to a proven[] / trusted[] / unprovable[] partition.
 */

import type { Hash, Id, MinimizedText, Score01, TimeWindow, Timestamp } from "./core";
import type { CreditMicros } from "./market";

// ---- Trust roots: named, non-launderable, degrade explicitly ----

/**
 * What roots a verification or settlement. Ordered from strongest to weakest;
 * `reputational_only` is honest for a repeated-play indie community (S2) and
 * precisely WRONG for one-shot crown-jewel lab trades (S1) — the type records
 * the class so a receipt can never launder a weak root into a strong promise.
 */
export type VerificationTrustClass =
  | "trustless"
  | "threshold_ttp"
  | "single_ttp"
  | "tee_vendor_root"
  | "reputational_only";

export interface TrustRoot {
  readonly id: Id<"TrustRoot">;
  readonly kind: VerificationTrustClass;
  readonly feasibility: "practical_now" | "practical_small" | "research_horizon";
  /** On failure the root degrades LOUDLY — never silent impersonation. */
  readonly degradesTo: "explicit_unprovable" | "named_lower_trust" | "block";
  /** The blast radius if this root is compromised (leaked signing key, side channel, colluding TTP). */
  readonly compromiseLeaks: MinimizedText;
}

// ---- Verification: the forced three-way partition ----

/**
 * Now-feasible plans first; research-horizon plans exist as typed UPGRADE
 * SLOTS but a law forbids them from gating a live settlement (crypto-theater
 * inoculation — an aspirational proof system may not block or bless real money).
 */
export type VerificationPlan =
  | "none"
  | "third_party_audit"
  | "tee_replication"
  | "mutual_verifier_run"
  // upgrade slots — not for live settlement:
  | "mpc_2pc"
  | "zk_committed_eval"
  | "fhe_eval";

/**
 * The heart of the module. No boolean success — the ONLY success state is
 * `verified_partitioned`, and it carries three disjoint lists. A capability
 * RESULT ("this checkpoint scores ≥X on your private eval") can be proven under
 * a TEE root; a METHOD claim ("technique T causes the lift, transfers to other
 * bases, is novel") is unprovable in every 2026-shippable plan and must land in
 * `unprovable`, not be quietly asserted.
 */
export interface VerificationVerdict {
  readonly id: Id<"VerificationVerdict">;
  readonly claimId: Id<"EscrowedClaim">;
  readonly plan: VerificationPlan;
  readonly trustRootId: Id<"TrustRoot">;
  readonly proven: readonly MinimizedText[];
  readonly trusted: readonly MinimizedText[];
  /**
   * The fourth lane. Novelty / out-of-distribution / transfer claims that
   * cryptography cannot prove but a research substrate can ESTIMATE with
   * evidence and calibrated confidence. It NEVER promotes to proven/trusted
   * (law estimatedNeverPromotes), and it may only be consumed as a price
   * INPUT — a continuous haircut informing a human price — never as a
   * discontinuous gate on payoff (law estimatesArePriceInputsNeverPayoffCliffs).
   */
  readonly estimated: readonly Id<"OodEstimate">[];
  readonly unprovable: readonly MinimizedText[];
  readonly state: "verified_partitioned";
}

// ---- The ESTIMATED lane: research-substrate novelty/OOD as a contestable exhibit ----

/**
 * A named, pre-registered estimation root: which embedder ensemble and which
 * VRF-selected corpus snapshot, committed BEFORE negotiation opens. This kills
 * snapshot-shopping (picking a corpus that makes you look novel), embedder-
 * shopping (picking a metric that flatters), and post-hoc prior-art flooding.
 */
export interface NoveltyRoot {
  readonly id: Id<"NoveltyRoot">;
  readonly corpusSnapshotHash: Hash;
  readonly vrfSeed: Hash;                 // corpus snapshot selected by a jointly-verifiable coin
  readonly embedderEnsemble: readonly string[];   // median over the ensemble, not one metric
  readonly committedAt: Timestamp;
}

/**
 * Provenance discriminates a SHARED corpus-relative estimate (one-time, no
 * per-buyer redistribution leakage) from a BUYER-CONDITIONED deep read (which
 * debits the buyer's leakage + cost budget — because the closest-prior-art
 * citation IS a scoop map).
 */
export type EstimateProvenance =
  | { readonly kind: "corpus_relative"; readonly observer: "shared_substrate"; readonly marginalRedistributionLeakageBits: 0 }
  | { readonly kind: "buyer_conditioned"; readonly observerId: Id<"Principal">; readonly leakageBitsSpent: number; readonly costSpent: CreditMicros };

export interface OodEstimate {
  readonly id: Id<"OodEstimate">;
  readonly assetId: Id<"TradedAsset">;
  readonly noveltyRootId: Id<"NoveltyRoot">;
  readonly method: "embedding_distance" | "prior_art_density" | "citation_position" | "reproduction";
  /** Retrieval prior (cheap, informs search) vs valuation gating (feeds price) — the load-bearing role split. */
  readonly estimatorRole: "retrieval_prior" | "valuation_gating";
  readonly oodScoreVsCorpus: Score01;
  /** A calibrated INTERVAL, never a point — and see the calibration paradox non-claim below. */
  readonly confidenceInterval: readonly [Score01, Score01];
  readonly provenance: EstimateProvenance;
  readonly evidenceCitations: readonly MinimizedText[];
  readonly gameabilityCaveat: MinimizedText;
  /**
   * THE paradox, typed as a non-claim: the calibration set is by definition
   * known-novel / known-derivative pairs — NOT the frontier technique. And for
   * a true crown jewel the nearest PUBLIC prior art is far precisely because the
   * real prior art is secret. So sparse prior art means UNKNOWN, not novel; high
   * OOD over crown jewels is not trustworthy. This flag forces that honesty.
   */
  readonly calibrationCoversThisRegime: boolean;
}

/**
 * Dual commitment: exact bytes AND a behavioral/eval-response fingerprint.
 * Closes the attest-good / ship-requantized-bad gap a single byteHash leaves
 * open — the delivered binding must equal the verified binding (law).
 */
export interface BindingCommitment {
  readonly id: Id<"BindingCommitment">;
  readonly byteHash: Hash;
  readonly capabilityHash: Hash;
  readonly quantizationClass: string;
}

// ---- Carrier router: what physical form the IP takes gates what may be promised ----

export type CarrierClass =
  | "static_checkpoint"
  | "lora_adapter"
  | "curated_dataset"
  | "teacher_outputs"
  | "hosted_service"
  | "pure_recipe";

/**
 * A traded asset. `pure_recipe` (a technique described, not embodied in a file)
 * has no binding to commit and no carrier to watermark — so a law pins any
 * reuse verdict about it to "unprovable". The substrate DECLINES to sell a
 * propagation royalty it cannot back rather than pretend it can.
 */
export interface TradedAsset {
  readonly id: Id<"TradedAsset">;
  readonly carrier: CarrierClass;
  readonly binding?: BindingCommitment;
  readonly valuation: Valuation;
}

// ---- Heterogeneous valuation: value is not a scalar ----

/**
 * A tagged union, NOT a lexicographic scalar and NOT price=+∞. Some techniques
 * are priceless because exclusivity itself is the moat — the owner will not
 * sell at any monetary price, yet might barter for one specific complement.
 * Modeling "priceless" as a huge number invites a mechanism to "meet the price"
 * the owner would never accept, AND a finite ∞-proxy leaks the owner's position.
 * So priceless is a distinct branch that is categorically EXCLUDED from monetary
 * clearing (law pricelessIsExcludedFromMonetaryClearing).
 *
 * Honest residual (typed as RefusalReceipt, not asserted away): the tag is
 * uncertifiable cheap talk — a seller can tag priceless to force a counterparty
 * to disclose a complement in barter, or privately hold a finite reserve. The
 * substrate records the declaration and its non-verifiability; it does not
 * pretend to know the owner's true type.
 */
export type Valuation =
  | { readonly kind: "monetary"; readonly reservePriceId: Id<"ReservePrice"> }
  | { readonly kind: "barter_only"; readonly acceptableClasses: readonly CarrierClass[] }
  | { readonly kind: "attribution"; readonly terms: MinimizedText; readonly priorityCommitHash: Hash }
  | { readonly kind: "excluded_from_monetary_clearing"; readonly exclusivityRationale: MinimizedText };

/**
 * A first-class OUTPUT when the deciding term is not a substrate-enforceable
 * object: competitor-status → BLOCK, crown jewel → RefuseToList. Note the
 * honest sting: a refusal receipt is itself discoverable evidence that contact
 * (and interest) occurred — so refusing is not free of signal.
 */
export interface RefusalReceipt {
  readonly id: Id<"RefusalReceipt">;
  readonly assetId: Id<"TradedAsset">;
  readonly reason: "priceless_excluded" | "competitor_eligibility_block" | "barter_class_mismatch" | "tag_unverifiable";
  readonly discoverableContactSignal: true;
  readonly note: MinimizedText;
}

// ---- Atomic settlement: explicit regimes, honest ceilings ----

export type AtomicityRegime =
  | { readonly kind: "operator_adjudicated"; readonly operatorId: Id<"Principal"> }
  | { readonly kind: "tee_coresident_escrow"; readonly trustRootId: Id<"TrustRoot"> }
  /** Chain hash-lock / ZK contingent payment: key-for-payment, SMALL artifacts only. */
  | { readonly kind: "onchain_hashlock"; readonly artifactSizeCeilingBytes: number }
  | { readonly kind: "optimistic_with_dispute"; readonly disputeWindow: TimeWindow; readonly bondId: Id<"SlashableBond"> };

export interface SettlementConsortium {
  readonly memberIds: readonly [Id<"Principal">, Id<"Principal">, ...Id<"Principal">[]];
  readonly threshold: number;
}

export interface Settlement {
  readonly id: Id<"Settlement">;
  readonly laneId: Id<"NegotiationLane">;
  /** Non-empty: valuation and exchange are strictly downstream of a verdict. */
  readonly verdictIds: readonly [Id<"VerificationVerdict">, ...Id<"VerificationVerdict">[]];
  readonly priceCrossId?: Id<"PriceCross">;
  readonly regime: AtomicityRegime;
  /** Replaces negotiation.ts's singleton mediator when trust must be spread. */
  readonly consortium?: SettlementConsortium;
  readonly verifiedBinding: BindingCommitment;
  readonly deliveredBinding?: BindingCommitment;
  readonly state: "awaiting_verdict" | "priced" | "delivering" | "settled" | "disputed" | "aborted";
}

// ---- S2: royalty spine — ex-ante, consent-first, evidence as deterrent ----

/** Bound BEFORE work: what is licensed, at what schedule, with what audit rights. */
export interface LicenseGrant {
  readonly id: Id<"LicenseGrant">;
  readonly assetId: Id<"TradedAsset">;
  readonly licenseeId: Id<"Principal">;
  readonly priceScheduleId: Id<"PriceSchedule">;
  readonly payoutAuthorizationId: Id<"SettlementPayoutAuthorization">;
  readonly bondId?: Id<"SlashableBond">;
  readonly auditRights: "none" | "attestation_only" | "scoped_audit";
}

/**
 * Licensee-SIGNED, self-issued build provenance (in-toto/DSSE + Sigstore/Rekor
 * style). Makes MARKET_LAWS' "declared reuse edge" a first-class record that no
 * third party had to observe — the consent-first spine of royalty.
 */
export interface ReuseAttestation {
  readonly id: Id<"ReuseAttestation">;
  readonly licenseId: Id<"LicenseGrant">;
  readonly downstreamModelHash: Hash;
  readonly signedByLicensee: true;
  readonly provenanceRecordHash: Hash;
}

/**
 * A CONTESTABLE exhibit, never a boolean "reused". Watermarks are NOT robust to
 * an adversarial licensee's distillation or fine-tuning, so evidence carries its
 * own statistical honesty: false-positive bound, how many laundering hops it
 * survived, and an independent-discovery rebuttal state.
 */
export interface ReuseEvidence {
  readonly id: Id<"ReuseEvidence">;
  readonly licenseId: Id<"LicenseGrant">;
  readonly method: "keyed_radioactive_data" | "blackbox_trigger_set" | "output_watermark" | "statistical_similarity";
  readonly pValue: Score01;
  readonly falsePositiveBound: Score01;
  readonly hopDepthCovered: number;
  readonly launderingBudgetSurvived: MinimizedText;
  readonly state: "asserted" | "contested" | "upheld" | "rebutted_independent_discovery";
}

/**
 * Slashing presupposes posted stake AND a consequence root. Sovereign labs will
 * not bond meaningful collateral to a third-party substrate — so the type
 * records `consequenceRoot: "none"` honestly rather than pretend "hidden reuse
 * is slashable" universally.
 */
export interface SlashableBond {
  readonly id: Id<"SlashableBond">;
  readonly posterId: Id<"Principal">;
  readonly amount: CreditMicros;
  readonly consequenceRoot: "jurisdictional_arbitration" | "onchain_stake" | "reputational_only" | "none";
  readonly state: "posted" | "at_risk" | "slashed" | "released";
}

export const IPTRADE_LAWS = {
  // anti-overclaim spine
  noBooleanVerifiedOnlyAPartition: true,
  methodClaimsAreUnprovableAtModelScaleIn2026: true,
  trustRootsAreNamedAndDegradeLoudly: true,
  researchHorizonPlansMayNotGateLiveSettlement: true,
  // exchange integrity
  verificationPrecedesValuation: true,
  deliveredBindingMustEqualVerifiedBinding: true,
  onchainAtomicityIsForSmallArtifactsOnly: true,
  settlementConsortiumMembersAreDisjointBeneficialEntities: true,
  // royalty honesty
  pureRecipeReusePinsToUnprovable: true,
  reuseIsAContestableExhibitNotABoolean: true,
  royaltyIsConsentFirstNotSurveillance: true,
  slashabilityRequiresAStatedConsequenceRoot: true,
  // heterogeneous valuation (priceless-as-type debate, synthesis)
  valuationIsATaggedUnionNotAScalar: true,
  pricelessIsExcludedFromMonetaryClearing: true,
  infiniteWeightIsRecordedNeverTheDefault: true,   // ∞ is a lie that also leaks position
  valuationTagIsCheapTalkUntilBackedByABondOrBarter: true,
  refusalIsAFirstClassOutputAndItselfASignal: true,
  // the ESTIMATED lane (OOD debates, synthesis)
  estimatedIsAFourthLaneThatNeverPromotes: true,
  estimatesArePriceInputsNeverPayoffCliffs: true,   // continuous haircut into a human price, never a gate
  corpusSnapshotIsVrfPinnedBeforeNegotiation: true, // no snapshot/embedder shopping
  estimationChannelIsMeteredBecauseClosestPriorArtIsAScoopMap: true,
  sparsePriorArtMeansUnknownNotNovel: true,         // absence of evidence != evidence of novelty
  calibrationDoesNotCoverCrownJewelRegime: true,    // the calibration-OOD paradox, as a non-claim
  // the standing honest non-claims (limits types cannot fix — see CANON open frontier)
  verificationChannelMayLeakViaModelExtraction: true,
  theDoublySealedVerifierSeesBothSecrets: true,
  cryptographicReceiptsAreNotSelfEnforcingContracts: true,
  reputationalRootIsWrongForOneShotCrownJewelTrades: true,
  // frontier the substrate names but does not solve (completeness critic)
  everythingHereIsBilateralMultilateralBarterRingsUnbuilt: true,
  attributionIsNotYetAnEscrowableCurrency: true,
  theResearchSubstrateIsNotNeutralItSeesEverything: true,
  costIncidenceOfVerificationAndEstimationIsUnfunded: true,
} as const;
