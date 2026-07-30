/**
 * Attention primitives.
 *
 * Human attention is a privacy boundary and a scarce system resource. Agents do
 * not get to page owners with raw discoveries. They write bounded findings;
 * guardians turn the few worth seeing into review cards; every interruption is
 * charged to the ledger.
 */

import type {
  Hash,
  Id,
  JsonPath,
  MinimizedText,
  RiskClass,
  Score01,
  TimeWindow,
  Timestamp,
  Visibility,
} from "./core";
import type { LeakageEstimate } from "./entropy";

export type FindingCategory = "match" | "risk" | "opportunity" | "anomaly" | "correction";
export type AttentionReason =
  | "release_decision"
  | "grant_escalation"
  | "high_value_finding"
  | "high_risk_finding"
  | "budget_exhaustion"
  | "incident_response"
  | "payment_decision";

export interface AgentFinding {
  readonly id: Id<"AgentFinding">;
  readonly chamberId: Id<"Chamber">;
  readonly runId: Id<"Run">;
  readonly agentId: Id<"Principal">;
  readonly category: FindingCategory;
  readonly summaryHash: Hash;
  readonly rawPayloadArtifactId: Id<"Artifact">;
  readonly targetAnnotationIds: readonly Id<"Annotation">[];
  readonly confidence: Score01;
  readonly novelty: Score01;
  readonly leakage: LeakageEstimate;
  readonly ownerVisibleByDefault: false;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface ReviewCard {
  readonly id: Id<"ReviewCard">;
  readonly chamberId: Id<"Chamber">;
  readonly findingIds: readonly Id<"AgentFinding">[];
  readonly gate: "preflight" | "release" | "bounty_acceptance" | "incident" | "appeal";
  readonly title: MinimizedText;
  readonly summary: MinimizedText;
  readonly decisionNeeded: "approve" | "reject" | "redact" | "defer" | "route";
  readonly visibleFieldPaths: readonly JsonPath[];
  readonly hiddenRiskClasses: readonly RiskClass[];
  readonly leakageIfOpened: LeakageEstimate;
  readonly priority: 0 | 1 | 2 | 3 | 4 | 5;
  readonly createdAt: Timestamp;
}

export interface AttentionQueue {
  readonly id: Id<"AttentionQueue">;
  readonly chamberId: Id<"Chamber">;
  readonly ownerId: Id<"Principal">;
  readonly cardIds: readonly Id<"ReviewCard">[];
  readonly ordering: "risk_then_value" | "deadline_then_risk" | "manual";
  readonly failClosedWhenUnreviewed: true;
}

/**
 * The thing debits exhaust. Without a budget record, "fail closed on
 * exhaustion" has no trigger and owner fatigue becomes an untyped
 * disclosure vulnerability.
 */
export interface AttentionBudget {
  readonly id: Id<"AttentionBudget">;
  readonly chamberId: Id<"Chamber">;
  readonly ownerId: Id<"Principal">;
  readonly window: TimeWindow;
  readonly maxInterruptions: number;
  readonly maxDetailExpansions: number;
  readonly maxHighRiskOverrides: number;
  readonly batchWindowMinutes: number;
  readonly onExhaustion: "fail_closed_for_disclosure";
}

export interface AttentionDebit {
  readonly id: Id<"AttentionDebit">;
  readonly budgetId: Id<"AttentionBudget">;
  readonly chamberId: Id<"Chamber">;
  readonly ownerId: Id<"Principal">;
  readonly cardId?: Id<"ReviewCard">;
  readonly runId?: Id<"Run">;
  readonly reason: AttentionReason;
  readonly interruptionCount: number;
  readonly detailExpansionCount: number;
  readonly highRiskOverrideCount: number;
  readonly ledgerEntryId: Id<"LedgerEntry">;
}

export interface NotificationPolicy {
  readonly id: Id<"NotificationPolicy">;
  readonly chamberId: Id<"Chamber">;
  readonly minimumPriority: ReviewCard["priority"];
  readonly allowedReasons: readonly AttentionReason[];
  readonly allowedVisibility: Visibility;
  readonly batchWindowMinutes: number;
  readonly quietHoursLocal?: string;
}

export interface NotificationAttempt {
  readonly id: Id<"NotificationAttempt">;
  readonly policyId: Id<"NotificationPolicy">;
  readonly cardIds: readonly Id<"ReviewCard">[];
  readonly channel: "owner_console" | "email" | "desktop" | "none";
  readonly sentAt?: Timestamp;
  readonly suppressedReason?: "low_priority" | "quiet_hours" | "budget_exhausted" | "owner_disabled";
  readonly visibleTextHash: Hash;
  readonly leakage: LeakageEstimate;
}

export const ATTENTION_LAWS = {
  agentsWriteFindingsNotPages: true,
  attentionMayCarryAReserveAndCardsClearItBeforeSurfacing: true,
  ownersSeeReviewCardsNotRawPayloadsByDefault: true,
  everyInterruptionDebitsTheLedger: true,
  attentionExhaustionFailsClosedForDisclosure: true,
  notificationTextIsItselfEgress: true,
} as const;
