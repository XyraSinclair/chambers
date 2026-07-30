# Liability and review model

Scry Chambers should not promise that private work is magically safe. The safer posture is more concrete: bounded work under explicit authority, observable egress accounting, role-separated review, release/payment gates, incident records, and receipts that preserve caveats instead of laundering risk.

This document is a governance model, not legal advice. Its job is to keep the primitives honest enough that counsel, operators, reviewers, sponsors, owners, and future agents can answer the same questions from the same records.

## 1. The five questions

Every meaningful liability question should reduce to five graphs:

1. **Authority graph:** who was allowed to do what, over which private boundary, under which grant, when?
2. **Exposure graph:** who or what observed which class of material, at what granularity, through which surface?
3. **Decision graph:** who reviewed, approved, rejected, escalated, released, paid, appealed, or closed an incident?
4. **Economic graph:** who funded, who earned, what was accepted, what was settled, and did payment itself cross a boundary?
5. **Receipt graph:** what did the system say outward, what did it caveat, and what did it explicitly refuse to claim?

If those cannot be reconstructed from `runId`, `grantId`, `envRecipeId`, `releaseId`, and `ledgerTailId`, the product is not legible enough.

## 2. Authority graph

Authority is not identity. A user, agent, model, sponsor, reviewer, or tool can all be a `Principal`; authority comes from `Grant`, `Transform`, `Scope`, `EnvRecipe`, and gate decisions.

### Required records

```ts
type AuthorityFact = {
  principalId: Id<"Principal">;
  chamberId: Id<"Chamber">;
  roleAtTime: "owner" | "requester" | "sponsor" | "worker" | "reviewer" | "auditor" | "tool" | "model" | "system";
  grantId?: Id<"Grant">;
  transformId?: Id<"Transform">;
  scopeIds?: Id<"Scope">[];
  envRecipeId?: Id<"EnvRecipe">;
  gate?: Gate;
  valid: TimeWindow;
  revokedAt?: Timestamp;
  ledgerEntryId: Id<"LedgerEntry">;
};
```

### Authority rules

- No run without a grant.
- No grant without scope, transform, sink policy, environment recipe, validity, and revocation path.
- No worker package authority by reputation alone.
- No bounty authority. A bounty can fund work; it cannot confer access.
- No automatic escalation from output approval to release approval.
- No reviewer authority over their own payout or conflicted sponsor release.
- No owner-independent disclosure for sensitive private-world outputs.

### Authority failure modes

| Failure | Example | Required mitigation |
|---|---|---|
| Ambient machine authority | Worker can read `$HOME` because process can. | `Scope` + `MountSpec` + scanner + owner-visible scope class. |
| Prompt-granted authority | Requester says "ignore policy". | Transform input scanner; grant is not prompt text. |
| Bounty-granted authority | Sponsor pays and therefore sees output. | Access through `Grant`; visibility through `Release`. |
| Reviewer overreach | Reviewer approves disclosure outside gate. | `Review.gate`, `Release.ownerDecision`, role separation. |
| Revocation ambiguity | Old passcode or grant still works. | `revokedAt`, TTL, use limits, ledgered revocation. |

## 3. Exposure graph

Exposure is not only raw data access. Exposure includes reviewer views, model prompts, stdout, status pages, receipt text, support bundles, payout, queue movement, timing, token count, cache hits, and public reputation.

### Required records

```ts
type ExposureFact = {
  id: Id<"ExposureFact">;
  runId: Id<"Run">;
  artifactId?: Id<"Artifact">;
  principalId: Id<"Principal">;
  surface: Surface;
  class: ObservableClass;
  dataClasses: DataClass[];
  granularity: "none" | "metadata" | "aggregate" | "snippet" | "full";
  precision: "exact" | "rounded" | "bucketed" | "suppressed";
  cadence: "immediate" | "delayed" | "batched" | "release_only" | "never";
  legalBasis: "owner_authorized" | "review_required" | "incident" | "system_operation" | "public_source" | "unknown";
  caveats: ReceiptCaveat[];
  ledgerEntryId: Id<"LedgerEntry">;
};
```

### Exposure rules

- Reviewer exposure is real exposure, even if reviewer is trusted.
- Model prompt exposure is real exposure, even if the model is internal.
- Logs are not harmless.
- Errors are not harmless.
- Embeddings are not harmless.
- Timing is not harmless.
- Payment is not harmless.
- "No raw text" is not equivalent to "no leakage".
- Exact counts, exact ranks, exact denominators, exact paths, exact filenames, exact timestamps, exact token counts, and exact byte counts are high-risk by default.

### Exposure classes

| Class | Risk | Default |
|---|---|---|
| Raw private text | Direct disclosure | Owner/reviewer only; release forbidden unless explicit. |
| Source handle | Reconstructable context | Reviewer only; owner-private by default. |
| Snippet | Semantic leakage | Release only after review and redaction. |
| Aggregate answer | Composition leakage | Capped, caveated, denominator-guarded. |
| Status | Timing/severity leakage | Coarse and delayed for requesters. |
| Timing | Corpus/rarity leakage | Bucketed or owner-only. |
| Counts | Corpus/match leakage | Rounded, bucketed, or blocked. |
| Payout | Value/existence leakage | Owner-only or delayed aggregate unless released. |
| Cache hit | Existence leakage | Never externally visible by default. |
| Support bundle | Raw/log leakage | Owner/auditor only with explicit retention. |

## 4. Decision graph

A review decision is scoped. There is no generic `approved: true`.

### Gate types

| Gate | Decision | Reviewer sees | Owner attention? |
|---|---|---|---|
| `request_preflight` | Is the requester ask allowed? | Question, policy flags, public context | Usually no; yes if escalated. |
| `grant_preflight` | Is the capability safe to issue? | Scope classes, transform, env recipe, sink | Yes for new authority. |
| `execution_monitor` | Did runtime violate recipe? | Logs, tool calls, blocked network, canaries | Only if incident/escalation. |
| `output_review` | Is worker output schema-valid, grounded, non-obviously leaky? | Output artifact, source handles if authorized | Maybe batch. |
| `entropy_review` | Does composition/side-channel risk block release? | Observable events, capacity estimates, denominator state | Yes if release-affecting. |
| `release_review` | Which fields can leave owner control? | Release candidate, caveats, redaction plan | Yes. |
| `payment_review` | Can value or payment be released? | Acceptance, leakage risk, payout rule | Yes for external payout. |
| `appeal` | Was a rejection or incident misclassified? | Prior decision file and safe evidence | Yes if materially changes authority/disclosure/payment. |
| `post_audit` | Did a past run violate claims or policy? | Ledger, artifacts, support bundle | Yes if incident/liability. |

### Review record

```ts
type ReviewDecision = "allow" | "owner_review" | "redact" | "reject" | "quarantine" | "incident" | "defer";

type ReviewFile = {
  id: Id<"Review">;
  runId: Id<"Run">;
  gate: Gate;
  reviewerId: Id<"Principal">;
  saw: ExposureSummary[];
  decision: ReviewDecision;
  reasons: RiskVector[];
  proposedRedactions: JsonPath[];
  requiredCaveats: ReceiptCaveat[];
  conflictOfInterest?: ConflictCheck;
  createdAt: Timestamp;
  ledgerEntryId: Id<"LedgerEntry">;
};
```

### Decision rules

- Two low-quality reviews do not equal one good review. Review plans must specify independence and role separation, not just count.
- A reviewer can reject for policy, leakage, grounding, or fraud without exposing raw evidence to the requester.
- A release reviewer should not need raw transcripts by default; they need minimized cards and expansion handles.
- Dissent is additive. A dissenting review should be preserved, not overwritten by consensus prose.
- Reviewer uncertainty is a first-class reason, not a failure to be hidden.

## 5. Economic graph

Money is an egress channel. It reveals value, existence, scarcity, and acceptance.

### Required records

```ts
type EconomicFact = {
  id: Id<"EconomicFact">;
  chamberId: Id<"Chamber">;
  runId?: Id<"Run">;
  bountyId?: Id<"Bounty">;
  deltaId?: Id<"CognitiveDelta">;
  acceptanceId?: Id<"Acceptance">;
  settlementId?: Id<"CreditSettlement">;
  payer: Id<"Principal">;
  payee?: Id<"Principal">;
  amountBucket: Bucket;
  visibility: Visibility;
  releaseRequired: boolean;
  leakageRisk: RiskScore;
  ledgerEntryId: Id<"LedgerEntry">;
};
```

### Economic rules

- A sponsor pays for accepted structure, not access.
- A worker earns only after acceptance rules are satisfied.
- External payout must pass payment review if it reveals anything about private content.
- Reuse credit must be declared, not inferred from hidden cache hits.
- Public reputation is a release surface.
- Leaderboards are off by default.
- Refunds, slashings, and clawbacks are observable too.

### Market abuse patterns

| Abuse | Mechanism | Type-level mitigation |
|---|---|---|
| Bounty probing | Sponsor posts many narrow bounties to infer private facts. | `DenominatorGuard`, repeated-query composition, coarse target classes. |
| Payout leakage | Large payout reveals rare sensitive match. | Settlement visibility, delayed aggregates, release gate. |
| Token-burn farming | Worker spends compute to signal effort. | Pay only accepted deltas, not runtime cost. |
| Hidden reuse | Worker reuses private annotation externally. | `ReuseEdge`, provenance, invalidation, slashable undeclared reuse. |
| Reputation laundering | Public profile implies private-domain success. | Reputation owner-local by default; export as release-reviewed aggregate only. |
| Evaluator capture | Reviewer profits from accepting own work. | Conflict check and reviewer separation proof. |

## 6. Receipt graph

Receipts are product language under constraint. They should be useful but legally and epistemically humble.

### Receipt payload

```ts
type ReceiptClaimKind =
  | "scope_reviewed"
  | "grant_authorized"
  | "environment_configured"
  | "worker_ran"
  | "output_schema_checked"
  | "release_reviewed"
  | "owner_approved"
  | "answer_capped"
  | "aggregate_only"
  | "no_raw_quotes_released"
  | "network_blocked"
  | "payment_reviewed";

type ReceiptCaveatKind =
  | "not_anonymity_proof"
  | "not_semantic_non_leakage_proof"
  | "not_full_context"
  | "review_can_fail"
  | "residual_inference_risk"
  | "environment_not_enclave"
  | "source_list_not_released"
  | "counts_bucketed";

type ReceiptPayload = {
  id: Id<"ReceiptPayload">;
  releaseId: Id<"Release">;
  visibleClaims: ReceiptClaimKind[];
  caveats: ReceiptCaveatKind[];
  noPerfectSecrecyClaim: true;
  releasedArtifactHash: Hash;
  policyHash: Hash;
};
```

### Receipt laws

A receipt may say:

- the request was reviewed;
- execution was owner-authorized;
- the worker ran in a configured environment;
- arbitrary online code execution or raw dumps were disallowed if that is true;
- output was schema-checked;
- release was reviewed;
- owner approved disclosure;
- answer was capped, aggregate, or minimized;
- specific classes of raw material were not released.

A receipt must not say:

- no data leaked;
- anonymity is guaranteed;
- inference is impossible;
- reviewers prove semantic safety;
- a TEE/container/sandbox makes output safe;
- aggregate means harmless;
- no raw text means no private information crossed.

## 7. Incident model

Incidents are not only data breaches. In Scry Chambers, an incident can be a suspected side-channel leak, reviewer conflict, payout leak, canary hit, prompt injection, prohibited output, policy mismatch, stale annotation reuse, or receipt overclaim.

### Incident record

```ts
type IncidentRecord = {
  id: Id<"Incident">;
  chamberId: Id<"Chamber">;
  runId?: Id<"Run">;
  openedBy: Id<"Principal">;
  class:
    | "prompt_injection"
    | "raw_disclosure"
    | "side_channel_leak"
    | "canary_hit"
    | "reviewer_conflict"
    | "payout_leak"
    | "receipt_overclaim"
    | "policy_mismatch"
    | "stale_reuse"
    | "external_complaint";
  severity: 1 | 2 | 3 | 4 | 5;
  affectedArtifacts: Id<"Artifact">[];
  affectedReleases: Id<"Release">[];
  immediateActions: LedgerAction[];
  closeCriteria: string[];
  status: "open" | "mitigating" | "closed" | "appealed";
  ledgerEntryId: Id<"LedgerEntry">;
};
```

### Incident defaults

- Freeze release if incident affects disclosure.
- Freeze settlement if incident affects payout or acceptance.
- Quarantine affected annotations and reuse edges.
- Preserve support bundle under owner/auditor visibility.
- Notify only roles whose authority, disclosure, payment, or liability changes.
- Do not notify requester with precise incident class unless release-reviewed.

## 8. Reviewer separation

Role separation is a product invariant, not paperwork.

### Reviewer separation proof

```ts
type ReviewerSeparationProof = {
  id: Id<"ReviewerSeparationProof">;
  runId: Id<"Run">;
  gate: Gate;
  requesterId?: Id<"Principal">;
  workerId?: Id<"Principal">;
  reviewerIds: Id<"Principal">[];
  sponsorId?: Id<"Principal">;
  payeeIds?: Id<"Principal">[];
  policy: "two_person" | "n_of_m" | "owner_delegate" | "auditor_required";
  conflictsChecked: true;
  unresolvedConflicts: ConflictCheck[];
  ledgerEntryId: Id<"LedgerEntry">;
};
```

### Separation rules

- Requester should not approve release of raw private content.
- Worker should not be sole reviewer of own output.
- Sponsor should not decide acceptance alone when payout reveals private value.
- Owner can override, but override is a ledgered decision with caveats.
- Automated scanners are tools, not independent reviewers.
- Model-based review is reviewer assistance, not proof.

## 9. Support bundles

Support bundles are dangerous because they collect exactly the material that normal receipts omit: logs, prompts, error traces, paths, and review notes.

### Support bundle policy

```ts
type SupportBundlePolicy = {
  id: Id<"SupportBundlePolicy">;
  allowedArtifacts: Id<"Artifact">[];
  defaultVisibility: "owner_private" | "auditor_private";
  requesterVisibleByDefault: false;
  includeRawLogs: boolean;
  redactPaths: boolean;
  redactSecrets: boolean;
  redactNames: boolean;
  retention: RetentionPolicy;
  exportRequiresReview: true;
};
```

### Rules

- No support bundle export without review.
- No default requester-visible support bundle.
- No raw path export by default.
- No full prompt transcript export by default.
- No private source list export by default.
- Every support bundle should have a policy hash and ledger entry.

## 10. Liability posture by deployment level

| Level | Example | Minimum posture |
|---|---|---|
| Local demo | One owner, one requester, one machine | Owner token, passcode, read-only worker, review gates, scans, capped receipt, local ledger. |
| Owner lab | Repeated private runs for one owner | Typed artifacts, accepted annotations, reuse edges, incident records, retention policy. |
| Partner silo | Organization admits third-party transforms | Environment receipts, role separation, support bundle policy, auditor visibility, revocation. |
| Market beta | Bounties and sponsor-funded deltas | Acceptance rules, settlement visibility, payout review, anti-probing budgets, reputation local by default. |
| Multi-party match | Bilateral/collaboration/dating/hiring | Consent policy, denominator guards, bilateral release, asymmetric-disclosure review. |
| Regulated deployment | Health/legal/finance/public sector | Counsel-reviewed policies, audit export, explicit data classes, human approvals, jurisdiction-specific retention and notices. |

## 11. Open legal/product questions

These should be preserved as open questions until answered by counsel, product pressure, or real incidents:

1. When does an accepted annotation become a record the owner must be able to export or delete?
2. When does a sponsor-funded bounty create contractual duties to disclose rejection reasons?
3. How should co-owned private context be represented when one owner wants to release and another does not?
4. What kinds of review delegation can satisfy owner-in-the-loop without exhausting the owner?
5. When does worker reputation become personal data or sensitive commercial information?
6. What audit trail can be shared with a requester without leaking the very thing it is meant to prove?
7. How should deleted private sources affect cached annotations and downstream payouts?
8. What is the minimum incident notice that is honest but not over-disclosing?
9. Can a no-network agent still leak through model-provider calls if model access is allowed?
10. Which receipt claims require deterministic verification rather than reviewer assertion?

## 12. Recommended first implementation posture

For the next product wedge, implement governance as sidecar records around the current Chamber flow:

1. `AuthorityFact` from passcode/request/grant/run setup.
2. `ExposureFact` for requester status, owner console, worker prompt, worker stdout/stderr, review card, release answer, receipt, and support bundle.
3. `ReviewFile` for preflight and release gates.
4. `ReceiptPayload` with explicit caveats.
5. `IncidentRecord` for scanner hits, prompt injection, raw disclosure, canary hit, or receipt overclaim.
6. `LedgerEntry` for all state transitions.

Do not start with notarization, enclaves, cryptographic receipts, public leaderboards, or a bounty marketplace. Those features amplify any ambiguity in the records. First make one run reconstructable and caveated.

## 13. The liability sentence

The product should be able to say, truthfully:

> This was bounded work under explicit owner authority. The worker received only approved scope handles and wrote to constrained sinks. Reviewers inspected minimized artifacts and release candidates. The owner or delegate approved what left owner control. The receipt states what happened and preserves caveats. The system does not claim perfect secrecy, anonymity, or impossible non-inference.

If the records cannot substantiate that sentence, the implementation is ahead of the governance model.
