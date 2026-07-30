/**
 * Runtime claim primitives.
 *
 * This is how the runtime stops lying. Containers, sandboxes, TEEs, provider
 * policies, and local models are all useful; none may become a vibe like
 * "secure execution". Every requester-visible runtime claim is compiled from
 * recorded facts: configured recipe fields, observed run surfaces, artifact
 * hashes, reviews, owner decisions, or caveated attestation quotes.
 *
 * The sentence "private data could not leak" is unrepresentable here.
 * The predicate "not_a_privacy_proof" is first-class.
 */

import type { Gate, Hash, Id, JsonPath, MinimizedText, Visibility } from "./core";

/** Run surfaces the operator can actually observe and hash. */
export type ObservedRunSurface = "mounts" | "tools" | "network" | "model" | "logs" | "exit";

/**
 * Evidence a claim may cite. Nothing else counts as support.
 * Prose reassurance is not a member of this union on purpose.
 */
export type RunClaimSupport =
  | { readonly kind: "configured"; readonly envRecipeId: Id<"EnvRecipe">; readonly field: JsonPath; readonly valueHash: Hash }
  | { readonly kind: "observed"; readonly surface: ObservedRunSurface; readonly observedHash: Hash }
  | { readonly kind: "artifact_hash"; readonly artifactId: Id<"Artifact">; readonly sha256: Hash }
  | { readonly kind: "reviewed"; readonly reviewId: Id<"Review">; readonly gate: Gate; readonly verdict: "allow" | "redact" | "reject" }
  | { readonly kind: "owner_decided"; readonly releaseId: Id<"Release">; readonly decision: "approve" | "reject" }
  | { readonly kind: "tee_quote"; readonly quoteHash: Hash; readonly caveated: true };

/**
 * The closed set of things a runtime may claim. Adding a predicate is a
 * deliberate act with a review; free-form claim strings do not exist.
 */
export type RunClaimPredicate =
  | "recipe_used"
  | "scope_mounted"
  | "tool_available"
  | "network_mode_observed"
  | "model_policy_used"
  | "logs_redacted_before_persist"
  | "release_review_passed"
  | "not_a_privacy_proof";

export interface RunClaim {
  readonly id: Id<"RunClaim">;
  readonly runId: Id<"Run">;
  readonly audience: Visibility;
  readonly predicate: RunClaimPredicate;
  /** Non-empty by construction: an unsupported claim is unrepresentable. */
  readonly support: readonly [RunClaimSupport, ...RunClaimSupport[]];
  readonly precision: "exact" | "bucketed" | "suppressed";
  readonly caveats: readonly MinimizedText[];
}

export const RUNTIME_LAWS = {
  claimsCompileFromRecordedFactsOnly: true,
  unsupportedClaimsAreUnrepresentable: true,
  containersDoNotProvePrivacy: true,
  teeQuotesAreAlwaysCaveated: true,
  requesterSeesModelClassOnly: true,
} as const;
