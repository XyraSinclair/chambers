/**
 * Environment primitives for work near private context.
 *
 * These types describe what a run was allowed to touch and how it was isolated.
 * They are not a generic container platform and they do not prove secrecy. A
 * stronger runtime can attach receipts later; the core invariant remains: no
 * Grant, no Run, no raw requester access.
 */

import type {
  Bytes,
  Hash,
  Id,
  MinimizedText,
  Seconds,
  Timestamp,
  Visibility,
} from "./core";

export type IsolationMode =
  | "local_read_only"
  | "docker_rootless"
  | "cloud_code_read_only"
  | "tee_attested";

export type ToolKind = "read" | "search" | "compute" | "browser_headless" | "warehouse_query" | "model_call";
export type NetworkMode = "none" | "allowlisted_egress" | "provider_only";

export interface AgentPackage {
  readonly id: Id<"AgentPackage">;
  readonly authorId: Id<"Principal">;
  readonly name: string;
  readonly version: string;
  readonly bundleHash: Hash;
  readonly manifestHash: Hash;
  readonly declaredPurpose: string;
  readonly declaredOutputSchemas: readonly string[];
  readonly noMutableRemoteCode: true;
}

export interface ResourceBudget {
  readonly maxWallSeconds: Seconds;
  readonly maxCpuSeconds: Seconds;
  readonly maxMemoryBytes: Bytes;
  readonly maxScratchBytes: Bytes;
  readonly maxReadBytes: Bytes;
  readonly maxOutputBytes: Bytes;
}

export interface MountSpec {
  readonly id: Id<"MountSpec">;
  readonly scopeId: Id<"Scope">;
  readonly mountLabel: string;
  readonly access: "metadata_only" | "read_only" | "synthetic_preview";
  readonly pathVirtualization: "opaque" | "stable_alias";
  readonly globHash?: Hash;
}

export interface ToolGrant {
  readonly id: Id<"ToolGrant">;
  readonly kind: ToolKind;
  readonly commandHash?: Hash;
  readonly purpose: string;
  readonly inputVisibility: Visibility;
  readonly outputVisibility: Visibility;
  readonly maxInvocations?: number;
}

export interface NetworkPolicy {
  readonly mode: NetworkMode;
  readonly allowlistHashes: readonly Hash[];
  readonly secretsMayTransit: false;
  readonly rawPrivateDataMayTransit: false;
}

export interface ModelAccessPolicy {
  readonly providerClass: "none" | "owner_local" | "operator_hosted" | "remote_api";
  readonly promptClass: "no_private_context" | "minimized_context" | "reviewed_private_excerpt";
  readonly trainingUseForbidden: true;
  readonly logRetentionClaim: "none" | "provider_policy" | "contractual" | "attested";
}

export interface SecretPolicy {
  readonly secretIds: readonly Id<"Secret">[];
  readonly exposedAs: "none" | "ephemeral_env" | "brokered_token";
  readonly neverVisibleToAgentAuthor: true;
}

export interface LogPolicy {
  readonly stdout: Visibility;
  readonly stderr: Visibility;
  readonly commandLines: Visibility;
  readonly paths: Visibility;
  readonly redactBeforePersist: true;
}

export interface EnvRecipe {
  readonly id: Id<"EnvRecipe">;
  readonly chamberId: Id<"Chamber">;
  readonly packageId: Id<"AgentPackage">;
  readonly isolation: IsolationMode;
  readonly baseImageHash?: Hash;
  readonly rootfsHash?: Hash;
  readonly mounts: readonly MountSpec[];
  readonly tools: readonly ToolGrant[];
  readonly resources: ResourceBudget;
  readonly network: NetworkPolicy;
  readonly modelAccess: ModelAccessPolicy;
  readonly secrets: SecretPolicy;
  readonly logs: LogPolicy;
  readonly createdById: Id<"Principal">;
  readonly createdAt: Timestamp;
}

export interface EnvironmentReceiptPayload {
  readonly envRecipeId: Id<"EnvRecipe">;
  readonly runId: Id<"Run">;
  readonly observedIsolation: IsolationMode;
  readonly observedMountHashes: readonly Hash[];
  readonly observedToolHashes: readonly Hash[];
  readonly observedNetworkMode: NetworkMode;
  readonly observedOutputHash: Hash;
  readonly claimClass: "operator_observed" | "reproducible_local" | "tee_quote";
  readonly caveats: readonly MinimizedText[];
}

export const ENVIRONMENT_LAWS = {
  noGrantNoEnvironment: true,
  noRawNetworkEgressByDefault: true,
  pathsAreVirtualizedBeforeWorkerAccess: true,
  logsAreOwnerPrivateUnlessReleased: true,
  receiptsDescribeObservedConfigurationNotPerfectIsolation: true,
} as const;
