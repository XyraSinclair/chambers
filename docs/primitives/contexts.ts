/**
 * Disclosure contexts: the structural grade, as canon.
 *
 * STRUCTURE.md is the narrative; this module is the citable surface. The
 * primary state of any derivative is its disclosure context —
 * (audience, purpose, alphabet) — and the priced event is strict
 * widening of that context. coalition.ts already mechanizes the audience
 * leg (CoalitionalDerivative.audience, WideningEvent, one-way by the
 * Lean widening proof); calculus.ts mechanizes the alphabet leg
 * (Codebook, capacity derived not declared); consent signatures bind the
 * purpose leg (ProgramHash signed before data enters). This module names
 * their conjunction so grants, receipts, and court files can carry ONE
 * context object and reviewers can cite STRUCTURE_LAWS.<key>.
 *
 * Bits appear here exactly once: `capacityBitsOf` is the homomorphism
 * from the alphabet leg into the composition budget. It is the
 * anti-laundering clause, not the guarantee (STRUCTURE.md §4). No other
 * function in this module returns a number.
 *
 * Honesty notes, load-bearing:
 * - There is NO purpose lattice yet. Purposes compare only by equality
 *   of the signed hash; "purpose A refines purpose B" is undeclarable
 *   today, so any purpose change is a widening for safety. A refinement
 *   relation would be a new admission-tested primitive, not a flag.
 * - Context comparison is a PARTIAL order; most pairs are incomparable
 *   and that is the point — an incomparable transition is not "sideways,"
 *   it is a widening on at least one leg and must be priced as one.
 */

import type { Hash, Id } from "./core";
import type { Bits } from "./core";
import type { ObserverClass } from "./entropy";
import type { Codebook } from "./calculus";

// ---- The three legs ----

/**
 * Who can observe. Either the generating coalition (the zero point of
 * the leakage metric — COALITION_LAWS.coalitionIsTheZeroPointNotAFortress)
 * or an enumerated set of observer classes. Cross-kind comparisons are
 * incomparable by construction: leaving the coalition is ALWAYS a
 * WideningEvent, never an ordering accident.
 */
export type Audience =
  | { readonly kind: "generating_coalition"; readonly coalitionId: Id<"Coalition"> }
  | { readonly kind: "observer_classes"; readonly classes: readonly ObserverClass[] };

/**
 * The purpose leg is what the consent signature covers: codebook hash +
 * worker program hash, signed once, before data enters (CALCULUS.md §4).
 * A purpose is not prose; it is the hash of what will actually run.
 */
export interface Purpose {
  readonly programHash: Hash;
  readonly codebookHash: Hash;
}

/**
 * The structural state of a derivative. Everything a counterparty can
 * ever learn is bounded by: who may look (audience), what was consented
 * to run (purpose), and what is expressible at all (alphabet). The
 * receipt leads with these three; the bit line is a footnote
 * (STRUCTURE.md §5).
 */
export interface DisclosureContext {
  readonly audience: Audience;
  readonly purpose: Purpose;
  readonly alphabet: Codebook;
}

// ---- The widening order ----

/**
 * The cumulative reading, load-bearing for "narrowing is impossible": a
 * context records what has ALREADY been made expressible to whom.
 * Revoking a BCR narrows future grants; it never narrows the past
 * context — disclosure is entropy-irreversible, so the enacted context
 * only ever widens (audience_never_narrower, generalized). STRUCTURE.md
 * §3 states the same reading.
 */
export type ContextRelation =
  | "equal"
  | "widening"      // strictly wider on ≥1 leg, no leg narrower
  | "narrowing"     // impossible to enact (one-way door); named for audits
  | "incomparable"; // treat as widening when pricing; never as free

const classSubset = (
  a: readonly ObserverClass[],
  b: readonly ObserverClass[],
): boolean => a.every((c) => b.includes(c));

const audienceRelation = (from: Audience, to: Audience): ContextRelation => {
  if (from.kind === "generating_coalition" && to.kind === "generating_coalition") {
    return from.coalitionId === to.coalitionId ? "equal" : "incomparable";
  }
  if (from.kind === "observer_classes" && to.kind === "observer_classes") {
    const fw = classSubset(from.classes, to.classes);
    const bw = classSubset(to.classes, from.classes);
    if (fw && bw) return "equal";
    if (fw) return "widening";
    if (bw) return "narrowing";
    return "incomparable";
  }
  // Coalition ↔ observer-classes: crossing the coalition boundary is a
  // WideningEvent by law, whatever the class list looks like.
  return "incomparable";
};

const symbolSubset = (a: Codebook, b: Codebook): boolean =>
  a.symbols.every((s) => b.symbols.includes(s));

const alphabetRelation = (from: Codebook, to: Codebook): ContextRelation => {
  const fw = symbolSubset(from, to);
  const bw = symbolSubset(to, from);
  if (fw && bw) return "equal";
  if (fw) return "widening";
  if (bw) return "narrowing";
  return "incomparable";
};

const purposeRelation = (from: Purpose, to: Purpose): ContextRelation =>
  from.programHash === to.programHash && from.codebookHash === to.codebookHash
    ? "equal"
    : "incomparable"; // no purpose lattice yet — see module header

/**
 * The partial order. A transition is free only when "equal"; everything
 * else is priced: "widening" through the WideningEvent machinery,
 * "incomparable" treated AS widening (safety direction), "narrowing"
 * refused (disclosure is entropy-irreversible; audience_never_narrower).
 */
export const compareContexts = (
  from: DisclosureContext,
  to: DisclosureContext,
): ContextRelation => {
  const legs = [
    audienceRelation(from.audience, to.audience),
    purposeRelation(from.purpose, to.purpose),
    alphabetRelation(from.alphabet, to.alphabet),
  ];
  if (legs.includes("incomparable")) return "incomparable";
  if (legs.includes("widening") && legs.includes("narrowing")) return "incomparable";
  if (legs.includes("narrowing")) return "narrowing";
  if (legs.includes("widening")) return "widening";
  return "equal";
};

// ---- The one homomorphism into arithmetic ----

/**
 * The only number this module emits: log2 of the enumerated alphabet.
 * Recomputed from the DEDUPLICATED symbol list on every call — never
 * trust a stored copy (CALCULUS_LAWS.derivedNotDeclared), and dedupe so
 * the map is well-defined on the order's equivalence classes: {a,b} and
 * {a,b,b} compare "equal" under the subset order and must charge alike.
 * An empty alphabet is a defect (log2 0 = -∞), not a zero-leak channel.
 * This is the map the odometer charges through; it is monotone along
 * "widening" on the alphabet leg, which is exactly why the budget
 * composes while the rest of the context does not need to.
 */
export const capacityBitsOf = (alphabet: Codebook): Bits => {
  const n = new Set(alphabet.symbols).size;
  if (n === 0) {
    throw new Error(
      `codebook ${alphabet.name} has an empty alphabet — a defect, not a channel`,
    );
  }
  return Math.log2(n) as Bits;
};

// ---- Laws ----

export const STRUCTURE_LAWS = {
  /** The disclosure context (audience × purpose × alphabet) is the primary
   *  grade; every boundary crossing is a context transition. */
  contextIsThePrimaryGrade: true,
  /** A derivative is confined to its generating context unless a release
   *  transaction widens the context; widening is priced, consented,
   *  ledgered, and one-way. Generalizes COALITION_LAWS.wideningIsAPriced-
   *  OneWayEvent from the audience leg to all three. */
  confinedUnlessWidened: true,
  /** Incomparable transitions are priced as widenings, never waved
   *  through: "sideways" is not a category the one-way door recognizes. */
  incomparableIsWidening: true,
  /** Purposes compare by signed-hash equality only; there is no purpose
   *  refinement lattice, so ANY purpose change is a widening. Declaring a
   *  refinement relation would be a new admission-tested primitive. */
  noPurposeLatticeYet: true,
  /** Bits enter through exactly one map — capacityBitsOf, derived from
   *  the alphabet — and serve exactly one job: the additively-composing
   *  anti-laundering budget (runMetered's hard cap). A receipt that
   *  leads with a bit number instead of the context is mis-registered
   *  (STRUCTURE.md §5). */
  bitsAreTheHomomorphicShadow: true,
  /** Harm claims are never denominated in bits: harm lives in WHICH
   *  proposition crossed (the counterfactual influence view), not in how
   *  many. Learned-bits estimates are internal-adversarial only. */
  harmIsNotDenominatedInBits: true,
} as const;
