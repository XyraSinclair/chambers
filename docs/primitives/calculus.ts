/**
 * The chamber calculus, as canon: composition laws over the other modules.
 *
 * CALCULUS.md is the narrative; this module is the citable law surface. It
 * adds no new data shapes — it names the algebra that core.ts (authority,
 * release), entropy.ts (capacity, surfaces), coalition.ts (audience,
 * widening), and mediation.ts (tuple-scoped judgements) must jointly
 * satisfy, so a reviewer can cite CALCULUS_LAWS.<key> against a diff the
 * same way they cite MEDIATION_LAWS today.
 *
 * Semantic model: quantitative information flow. Every observer-visible
 * surface is a channel; log2 n ceilings the min-capacity of any channel
 * with a closed n-symbol alphabet, which upper-bounds MULTIPLICATIVE
 * g-leakage for every NON-NEGATIVE gain function g (Miracle theorem; an
 * odds-ratio guarantee — additive/absolute-damage threat models need
 * per-protocol analysis). Derived charges (log2 of an enumerated alphabet)
 * are exact ceilings by construction; declared charges (probes, free text)
 * are honest estimates and must be pooled separately wherever both are
 * reported.
 *
 * Status honesty: the soundness theorem "well-typed protocol ⇒ leakage ≤
 * Σ charges" (a leakage-semiring graded type system) is the named OPEN
 * goal, and TypeScript cannot enforce the no-eliminator property. These
 * laws are the specification that the kernel meter, runtime checks, and
 * review enforce — cite them by key; do not present them as proved.
 *
 * Runnable shadow: chambers/ip_trade_sim/{codebook,leakage}.py and
 * test_calculus_bound.py exercise derivedNotDeclared, closedAlphabet,
 * blockBeforeCeiling, and refusalsSimulatable against a malicious judge.
 */

import type { Bits } from "./core";

/**
 * A closed release alphabet. Capacity is DERIVED from the symbol list —
 * there is no field an operator can set, so the charge cannot drift from
 * the surface. Mirrors ip_trade_sim/codebook.py; the TS shape exists so
 * codebooks can appear in consent objects and court files.
 */
export interface Codebook {
  readonly name: string;
  /** Every symbol an observer can EVER see on this channel: verdicts,
   * rejections, errors, and the accountant-emitted `blocked`. */
  readonly symbols: readonly string[];
  /** log2(symbols.length) — recompute on read; never trust a stored copy. */
  readonly capacityBits: Bits;
}

export const CALCULUS_LAWS = {
  /** Provenance grades join on composition; a derivative's silo set never
   *  shrinks. (The graded-monad bind; coalition.ts audience is its dual.) */
  provenanceJoins: true,
  /** Leakage charges compose additively in the odometer and the budget is a
   *  hard pre-charge cap: refusal happens BEFORE the crossing, never after. */
  blockBeforeCeiling: true,
  /** Charges on codebook channels are derived (log2 of the enumerated
   *  alphabet), never declared; declared estimates are permitted only on
   *  channels with no closed alphabet and must be pooled separately in any
   *  cut-bound report. */
  derivedNotDeclared: true,
  /** Every observable outcome of a release channel is a codebook member —
   *  rejections and errors included. An un-enumerated outcome is a defect
   *  (an unmetered side channel), not a policy choice. */
  closedAlphabet: true,
  /** Post-processing a released value never increases its charge (data-
   *  processing inequality); no combinator re-charges a public value. */
  postProcessingFree: true,
  /** A gate that leaks nothing is one whose decision is a function of
   *  public data only; any gate consulting silo content is itself a release
   *  at Bool and is charged and consented as one. */
  gatesArePublicOrCharged: true,
  /** Accountant refusals (`blocked`) may cross uncharged ONLY while
   *  blockage is computable from the public charge transcript alone; if a
   *  refusal ever depends on silo content, it becomes a charged release. */
  refusalsSimulatable: true,
  /** A release typechecks only with consent covering the FULL provenance
   *  grade: no joint derivative crosses on one party's signature. */
  consentCoversProvenance: true,
  /** Data-dependent aborts and review affordances are releases: whether a
   *  release happens at all is a `Withheld` symbol in the outcome alphabet,
   *  and an influence/counterfactual view shown to one party is a charged
   *  release against the other parties' exposure — consent is signed once,
   *  program-level, BEFORE data enters (codebook + program + influence-view
   *  codebook); nothing is conditioned on silo content for free. */
  abortsAndReviewsAreReleases: true,
  /** The protocol cut bound: total leakage to an observer coalition is at
   *  most the sum of charges on crossings it can see, under ANY behavior of
   *  confined agents — a malicious judge's only freedom is symbol choice,
   *  which is already paid for. Event count, ordering, and timing are
   *  themselves surfaces: they are free only where fixed or public-
   *  computable, else they must be charged (entropy.ts orderingBits /
   *  side-channel budgets). */
  leakageIsACutBound: true,
} as const;
