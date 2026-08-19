# Five beautiful type systems for Scry Chambers

Yes: the previous meta-layer was getting derpy. The beautiful target is not “a framework for reasoning about frameworks.” It is five small type systems that make private cognitive work feel inevitable, inspectable, and hard to misuse.

The core product sentence stays:

> private worlds become partially computable without becoming public.

That does not need an ontology cathedral. It needs a few typed border laws.

## Canon

The canonical type surface is `../../primitives/` (`core.ts`, `entropy.ts`, `environment.ts`, `runtime.ts`, `attention.ts`, `market.ts`). This document is the argument; that directory is the law. Where an earlier draft of this document drifted, the canonical names win: `LedgerEntry` not `Ledger`, `Visibility`/`ObserverClass` not `Audience`, `EnvRecipe` not `WorkerRecipe`, `Annotation` (aliased `CognitiveDelta`) for the market commodity, `ObservableEvent` for what this document calls an emission, and an eight-state `Gate` that includes `static_scan`. See `../../primitives/CANON.md` for the full alias table.

## The cut

A Chamber should not begin as a marketplace, enclave platform, agent registry, workflow engine, or privacy-proof machine.

It should begin as a court file for one bounded act of cognition:

```text
who asked
what authority existed
what private terrain was scoped
what recipe ran
what became observable
who reviewed it
what crossed the boundary
what the receipt refuses to claim
what the ledger remembers
```

Everything beautiful below is a different way of making that court file smaller, sharper, and more useful.

## The five systems

| Type system | One-line beauty | Core question |
|---|---|---|
| 1. Sealed Boundary Algebra | Authority is a narrow path, not a vibe. | Who may do what near which private world? |
| 2. Emission Calculus | Every observable thing is typed before it leaks. | What became observable, to whom, at what capacity? |
| 3. Receipt-Carrying Worker Recipes | Runtime claims are compiled from observed facts, not reassurance prose. | What was the worker actually configured and observed to do? |
| 4. Attention Escrow Review Graph | Owner attention is a scarce privacy boundary. | Which decision truly deserves a human/steward interruption? |
| 5. Owner-Cleared Delta Market | The market sells accepted structure, not secrets. | What cognitive delta was accepted, reused, credited, or paid? |

These should not all go into the core. The beautiful core is one spine; the others are ribs.

```text
Sealed Boundary Algebra
  ├─ Emission Calculus
  ├─ Worker Recipe Receipts
  ├─ Attention / Review Escrow
  └─ Owner-Cleared Delta Market
```

## 1. Sealed Boundary Algebra

This is the smallest honest Chamber.

The whole system should be explainable as:

```text
Chamber admits Scope through Grant.
Transform types the untrusted ask.
Grant permits Run of Transform.
Run writes Artifact.
Review narrows Artifact.
Release crosses the boundary.
Receipt names the crossing and the non-claims.
Ledger remembers every step.
```

### Core nouns

```ts
type Visibility = // who may see a record at rest
  | "system_secret"
  | "owner_private"
  | "reviewer_private"
  | "agent_private"
  | "requester_visible"
  | "sponsor_visible"
  | "public";

type ObserverClass = // who observes an emission
  | "owner" | "requester" | "sponsor" | "reviewer"
  | "operator" | "support" | "notifier" | "public";

type Gate =
  | "submit"
  | "static_scan"
  | "preflight"
  | "owner_execution"
  | "worker"
  | "release_review"
  | "owner_disclosure"
  | "post_release";

type Id<K extends string> = string & { readonly __id: K };
type Hash = `sha256:${string}`;
type JsonPath = string & { readonly __jsonPath: true };
```

```ts
type Capability = {
  readonly chamber: Id<"Chamber">;
  readonly holder: Id<"Principal">;
  readonly scopes: readonly Id<"Scope">[];
  readonly sink: Sink;
  readonly valid: TimeWindow;
  readonly revokedAt?: Timestamp;
};

interface Grant extends Capability {
  readonly id: Id<"Grant">;
  readonly issuedBy: Id<"Principal">;
  readonly agentHash: Hash;
}

// The boundary has two directions. Ingress is typed too: the requester's
// ask is untrusted and enters only as a hashed, policy-bound Transform.
// Without this record the court file cannot answer its first question.
interface Transform {
  readonly id: Id<"Transform">;
  readonly requester: Id<"Principal">;
  readonly sponsor?: Id<"Principal">;
  readonly declaredPurpose: string;
  readonly untrustedPromptHash: Hash;
  readonly inputPolicy: InputPolicy;
  readonly outputSchemaId: SchemaId;
}

interface Run {
  readonly id: Id<"Run">;
  readonly grant: Id<"Grant">;
  readonly transform: Id<"Transform">; // who asked, typed
  readonly gate: Gate;
  readonly artifacts: readonly Id<"Artifact">[];
  readonly reviews: readonly Id<"Review">[];
  readonly ledgerTail: Id<"LedgerEntry">;
}
```

```ts
interface Release {
  readonly id: Id<"Release">;
  readonly candidate: Id<"Artifact">;
  readonly status: "draft" | "approved" | "released" | "revoked" | "frozen_by_incident" | "rejected";
  readonly observer: Exclude<ObserverClass, "owner">;
  readonly fields: readonly JsonPath[];
  // Non-empty by construction: an unreviewed release is unrepresentable.
  readonly reviewIds: readonly [Id<"Review">, ...Id<"Review">[]];
  // Never a naked number in the spine. A scalar here is the data model of
  // the green dashboard this document warns against. Estimates carry their
  // assumptions or they carry nothing.
  readonly capacity: CapacityEstimate; // see ../../primitives/entropy.ts
  readonly releasedAt?: Timestamp; // outward timestamps are themselves emissions
}

interface Receipt {
  readonly release: Id<"Release">;
  readonly claims: readonly ReceiptClaim[];
  readonly caveats: readonly ReceiptCaveat[];
}

interface LedgerEntry {
  readonly id: Id<"LedgerEntry">;
  readonly chamber: Id<"Chamber">;
  readonly run?: Id<"Run">;
  readonly actor: Id<"Principal">;
  readonly gate: Gate;
  readonly action:
    | "grant"
    | "revoke"
    | "run"
    | "write"
    | "read"
    | "review"
    | "release"
    | "emit"
    | "incident";
  readonly object?: Id<string>;
  readonly visibility: Visibility;
  readonly parent?: Id<"LedgerEntry">;
  readonly detailHash: Hash;
}
```

Nouns used but not defined here — `Sink`, `TimeWindow`, `InputPolicy`, `CapacityEstimate`, `ReceiptClaim`, `ReceiptCaveat`, `MinimizedText`, and the rest — are defined once, in `../../primitives/`. This document defers them on purpose. It does not get to invent them twice.

### Invariant

No boundary crossing without:

1. a live `Grant`;
2. a `LedgerEntry`;
3. if the observer is outside owner control, a `Release` whose fields are a reviewed subset of the sink;
4. a `Receipt` that says exactly what crossed and what was not proven.

And in the other direction: no requester text touches private context except as a hashed, policy-bound `Transform`. Ingress is a crossing too — the prompt and the mounted scope projection handed *to* the worker are disclosure events to a semi-trusted principal, and they get ledger entries like everything else.

### Why it is beautiful

It is not “privacy infrastructure.” It is a grammar of permission.

A maintainer can ask:

```text
What live capabilities exist?
What releases exist?
Which fields crossed the boundary?
Which receipt caveats traveled with them?
```

No platform folklore required.

### What it deliberately hides

Everything not needed for the first proof:

- model/provider details;
- container runtime internals;
- marketplace payout mechanics;
- side-channel budgets;
- confidential-compute attestations;
- cross-chamber reputation;
- bounties;
- notification UX.

Those attach by ID later. They do not get to bloat the kernel.

### Failure mode

By itself, this names emissions but does not prove semantic non-disclosure. A released aggregate can still leak to someone with outside context. The algebra is the spine, not the immune system.

## 2. Emission Calculus

This is the most important non-core system. (Canonical record: `ObservableEvent` in `../../primitives/entropy.ts`; "emission" is this document's name for the same noun.)

The hard rule is not “answers are reviewed.” The hard rule is:

> every observable bit has a type, a policy, a budget debit, a composition key, and a review/non-release state before it leaves owner control.

An answer is obvious egress. So are:

- status text;
- exact timings;
- token counts;
- byte counts;
- cache hits;
- retry patterns;
- refusal reasons;
- support logs;
- billing lines;
- notification timing;
- absence of a result;
- the fact that a drill-down was allowed.

### Core nouns

```ts
type EmissionKind =
  | "answer_field"
  | "receipt_claim"
  | "status_state"
  | "progress_event"
  | "log_line"
  | "error_shape"
  | "timing"
  | "token_count"
  | "byte_count"
  | "cost"
  | "cache_hit"
  | "retry_pattern"
  | "ordering"
  | "notification_timing"
  | "billing_line"
  | "support_bundle_field"
  | "absence";
```

```ts
type Emission<K extends EmissionKind = EmissionKind> = {
  id: Id<"Emission">;
  runId: Id<"Run">;
  gate: Gate;
  surface: Surface;
  observer: ObserverClass;
  kind: K;
  payloadRef?: Id<"Artifact"> | JsonPath; // never inline raw private body
  rawVisibility: Visibility;
  projectedPrecision: "exact" | "rounded" | "bucketed" | "suppressed";
  cadence: "immediate" | "delayed" | "batched" | "release_only" | "never";
  policyId: Id<"EmissionPolicy">;
  compositionKeyId: Id<"CompositionKey">;
  estimate: EmissionEstimate;
  reviewState:
    | "not_required_owner_only"
    | "pending"
    | "allowed"
    | "bucket_more"
    | "delay"
    | "redact"
    | "block";
  ledgerEntryId: Id<"LedgerEntry">;
};
```

```ts
type EgressBudget = {
  id: Id<"EgressBudget">;
  chamberId: Id<"Chamber">;
  grantId?: Id<"Grant">;
  audience: ObserverClass | Id<"Principal">;
  scope: "run" | "grant" | "query_family" | "audience_window" | "chamber_lifetime";
  maxSchemaBits: Bits;
  maxTextBitsUpperBound: Bits;
  maxMetadataBits: Bits;
  maxSideChannelBits: Bits;
  repeatedQueryComposition: "bounded" | "blocked";
  denominatorPolicy: {
    reveal: "never" | "bucket_only" | "owner_only";
    minGroupSize: number;
    zeroOneManyOnly: boolean;
  };
  onExhaustion: "owner_review" | "redact" | "delay" | "block";
};
```

The composition primitive is not allowed to stay a name. It is the thing the composition test tests, so it lives in the spine's shadow, fully typed:

```ts
// ../../primitives/entropy.ts — a key over everything that makes repeated
// small disclosures add up to one big one.
interface CompositionKey {
  readonly id: Id<"CompositionKey">;
  readonly chamberId: Id<"Chamber">;
  readonly subjectHash: Hash;     // whose private world
  readonly queryFamilyHash: Hash; // what kind of question
  readonly audienceHash: Hash;    // who keeps learning
  readonly sponsorHash?: Hash;
  readonly windowHash: Hash;      // over what time
}

interface CompositionState {
  readonly keyId: Id<"CompositionKey">;
  readonly releaseIds: readonly Id<"Release">[];
  readonly observableEventIds: readonly Id<"ObservableEvent">[];
  readonly cumulativeLeakage: "none" | "negligible" | "bounded" | "material" | "unsafe" | "unknown";
  readonly releaseGate: "allow" | "owner_review" | "redact" | "block";
}
```

A release can be blocked by `CompositionState` even when its immediate output validates. That sentence is the whole point of this layer.

One more law that hides in plain sight: every timestamp that leaves owner control is an emission. `releasedAt`, notification send times, status transition times — rounded, bucketed, delayed, or suppressed. Exact outward time does not exist.

### Invariant

No non-owner-observable fact exists outside owner control unless it is:

```text
Emission + EmissionPolicy + EgressBudget debit + CompositionKey + review/non-release state
```

### Why it is beautiful

It stops treating privacy review as a prose ritual.

The reviewer does not inspect “the answer.” The reviewer inspects the emission set:

```text
answer fields
+ receipt claims
+ status states
+ timings
+ errors
+ token/byte/cost buckets
+ notification text
+ support bundle projections
```

That is the difference between a privacy story and a privacy surface.

### The dangerous version

The dangerous version is a dashboard that says:

```text
egress budget: 0.7 bits ✅
```

while still leaking through rich prose, exact timing, rejection reasons, support logs, cache-hit behavior, or repeated drill-downs.

So capacity estimates must remain conservative tripwires, not certification. The claim is: minimized, accounted, reviewed, priced, remembered. Not: secrecy proven.

## 3. Receipt-Carrying Worker Recipes

This is how the runtime stops lying.

Containers, read-only sandboxes, TEEs, provider policies, and local models can all be useful. None of them should be allowed to become a vibe like “secure execution.”

The beautiful move is to make runtime claims compile from observed run facts.

### Core nouns

```ts
type RunClaimSupport =
  | { kind: "configured"; recipeId: Id<"EnvRecipe">; field: JsonPath; valueHash: Hash }
  | { kind: "observed"; surface: "mounts" | "tools" | "network" | "model" | "logs" | "exit"; observedHash: Hash }
  | { kind: "artifact_hash"; artifactId: Id<"Artifact">; sha256: Hash }
  | { kind: "reviewed"; reviewId: Id<"Review">; gate: Gate; verdict: "allow" | "redact" | "reject" }
  | { kind: "owner_decided"; releaseId: Id<"Release">; decision: "approve" | "reject" }
  | { kind: "tee_quote"; quoteHash: Hash; caveated: true };
```

```ts
interface RunClaim {
  id: Id<"RunClaim">;
  runId: Id<"Run">;
  audience: Visibility;
  predicate:
    | "recipe_used"
    | "scope_mounted"
    | "tool_available"
    | "network_mode_observed"
    | "model_policy_used"
    | "logs_redacted_before_persist"
    | "release_review_passed"
    | "not_a_privacy_proof";
  support: RunClaimSupport[];
  precision: "exact" | "bucketed" | "suppressed";
  caveats: MinimizedText[];
}
```

```ts
interface EnvRecipe {
  id: Id<"EnvRecipe">;
  chamberId: Id<"Chamber">;
  packageId: Id<"AgentPackage">;
  isolation:
    | "local_read_only"
    | "docker_rootless"
    | "podman_rootless"
    | "firecracker"
    | "gvisor"
    | "tee_attested";
  mounts: readonly MountClaim[];
  tools: readonly ToolGrant[];
  model: ModelGrant;
  network: {
    mode: "none" | "model_broker_only" | "egress_proxy_allowlist";
    rawPrivateDataMayTransit: false;
    secretsMayTransit: false;
  };
  resources: ResourceBudget;
  secrets: SecretPolicy;
  logs: LogSurfacePolicy;
  supportBundle: SupportBundlePolicy;
  claimPolicy: {
    requesterSeesModelClassOnly: true;
    exactPathsSuppressed: true;
    containersDoNotProvePrivacy: true;
  };
}
```

### Invariant

No requester-visible runtime claim without a `RunClaim` supported by configured, observed, reviewed, owner-decided, artifact-hash, or attested facts.

This claim should be impossible to express:

```text
private data could not leak
```

This claim is expressible:

```text
this run was configured as local_read_only against an owner-approved scope;
logs were owner-private;
release reviewers approved the capped aggregate output;
this is not a semantic privacy proof.
```

### Why it is beautiful

The receipt becomes a small courtroom object.

It can say:

- this worker package hash ran;
- this recipe was configured;
- this scope projection was mounted;
- this network/model/log policy was used;
- this output hash was reviewed;
- these caveats apply.

It cannot say magic words.

### First implementation wedge

For the current Python Chamber, do only this first:

```text
before worker execution:
  write environment_recipe.json
  write run_claims.jsonl for configured recipe/scope/model/log policy

after worker execution:
  artifactize stdout/stderr/structured output
  write environment_receipt.json
  include nonClaims in the requester receipt
```

Do not change the requester UX first. Make the run leave a better court file.

## 4. Attention Escrow Review Graph

This is the humane system.

If agents can page the owner directly, the product becomes harassment with a privacy policy. If every tiny uncertainty becomes a modal, the owner learns to ignore safety.

So owner attention needs a type system.

### Core nouns

```ts
type ReviewCard<G extends Gate = Gate> = {
  id: Id<"ReviewCard">;
  chamberId: Id<"Chamber">;
  runId: Id<"Run">;
  gate: G;
  sourceFindingIds: readonly Id<"AgentFinding">[];
  decisionNeeded:
    | "allow"
    | "reject"
    | "redact"
    | "defer"
    | "route"
    | "open_incident";
  title: MinimizedText;
  summary: MinimizedText;
  visibleFieldPaths: readonly JsonPath[];
  hiddenRiskClasses: readonly RiskClass[];
  leakageIfOpened: LeakageEstimate;
  ownerAttentionCost: AttentionCost;
  priority: 0 | 1 | 2 | 3 | 4 | 5;
  expansionHandle?: Id<"OwnerPrivateArtifact">;
  createdAt: Timestamp;
  ledgerEntryId: Id<"LedgerEntry">;
};
```

```ts
type AttentionBudget = {
  id: Id<"AttentionBudget">;
  chamberId: Id<"Chamber">;
  ownerId: Id<"Principal">;
  window: TimeWindow;
  maxInterruptions: number;
  maxDetailExpansions: number;
  maxHighRiskOverrides: number;
  batchWindowMinutes: number;
  notificationPolicyId: Id<"NotificationPolicy">;
  onExhaustion: "fail_closed_for_disclosure";
};
```

```ts
type ReleaseDocket = {
  id: Id<"ReleaseDocket">;
  runId: Id<"Run">;
  grantId: Id<"Grant">;
  candidateArtifactHash: Hash;
  reviewIds: readonly [Id<"Review">, Id<"Review">, ...Id<"Review">[]];
  separationProofIds: readonly Id<"ReviewerSeparationProof">[];
  exposureFactIds: readonly Id<"ExposureFact">[];
  requiredCaveats: readonly ReceiptCaveatKind[];
  supportBundleId?: Id<"SupportBundle">;
  ownerDecision: "preapproved_clean_path" | "approved_per_run" | "rejected" | "quarantined";
  attentionDebitId?: Id<"AttentionDebit">;
  status: "draft" | "approved" | "released" | "frozen_by_incident" | "rejected";
  ledgerTailId: Id<"LedgerEntry">;
};
```

### Invariant

Agents do not page owners.

Agents write `AgentFinding` records. Guardians compress them into `ReviewCard`s. Owner attention is charged only when a card matters to authority, release, incident, support export, or payment.

Unreviewed or budget-exhausted disclosure fails closed.

### Why it is beautiful

It makes the owner feel like they are tending a bounded institution, not chatting with a needy model.

The UI primitive is not:

```text
agent says: I found something interesting!!!
```

It is:

```text
ReviewCard
  decisionNeeded: redact | release | open_incident | pay
  leakageIfOpened: low | medium | high
  visibleFieldPaths: [...]
  hiddenRiskClasses: [...]
  expansionHandle: owner-private
```

### What it prevents

- agent chat streams;
- safety notification spam;
- hidden support-bundle leakage;
- reviewer self-dealing;
- receipts that overclaim;
- owner fatigue becoming a disclosure vulnerability.

### Failure mode

A bad guardian can compress the wrong thing. The type system can reduce owner surface area; it cannot replace judgement. Paired-silo canaries and post-audit still matter.

## 5. Owner-Cleared Delta Market

This is the market version that does not sell secrets.

The commodity is not “data access.” It is not “a report.” It is not “the best model’s opinion.”

The commodity is:

```text
an accepted, typed, provenance-bearing cognitive delta
```

(Canonical record: `Annotation` in `../../primitives/market.ts`, aliased `CognitiveDelta`. One noun, two names — the record name and the thing it is.)

Examples:

- correction;
- objection;
- opportunity;
- risk flag;
- calibration update;
- match candidate;
- reusable evidence card;
- contradiction edge;
- preference model fragment.

### Core nouns

```ts
type DeltaKind =
  | "opportunity"
  | "correction"
  | "objection"
  | "risk_flag"
  | "calibration"
  | "match_candidate"
  | "reusable_evidence";

interface BountyIntent {
  id: Id<"Bounty">;
  chamberId: Id<"Chamber">;
  sponsorId: Id<"Principal">;
  targetClasses: DataClass[];       // coarse classes, not locators
  targetSchemaId: SchemaId;
  acceptedKinds: DeltaKind[];
  acceptanceRuleId: Id<"AcceptanceRule">;
  creditPoolId: Id<"CreditPool">;
  workerGrantTemplateId?: Id<"GrantTemplate">; // template only; creates no access
  attentionEscrowId: Id<"AttentionBudget">;
  egressBudgetId: Id<"EgressBudget">;
  status: "draft" | "open" | "paused" | "closed" | "exhausted";
}
```

```ts
interface CognitiveDelta {
  id: Id<"CognitiveDelta">;
  chamberId: Id<"Chamber">;
  runId: Id<"Run">;
  emitterId: Id<"Principal">;
  kind: DeltaKind;
  schemaId: SchemaId;
  targets: TargetRef[];                  // hashes / owner-private handles
  payloadArtifactId: Id<"Artifact">;     // owner-private canonical payload
  evidenceArtifactIds: Id<"Artifact">[]; // owner/reviewer unless released
  confidence: Score01;
  grounding: Score01;
  noveltyClaim: "new" | "refines" | "contradicts" | "duplicate_candidate";
  dependsOn: Id<"CognitiveDelta">[];
  contradicts: Id<"CognitiveDelta">[];
  leakage: LeakageEstimate;
  reusableWithin: "same_chamber" | "same_owner_org" | "non_reusable";
  state: "proposed" | "accepted" | "rejected" | "contested" | "merged" | "superseded" | "quarantined" | "slashed";
  ownerPrivateForever: true;
}
```

`slashed` is not decoration. A market that pays a `leak_catcher` role must be able to un-pay the leaker: hidden reuse and caught leakage revoke acceptance, claw back settlement, and leave the slash in the ledger. Clawback without a typed slash state is a receipt that overclaims.

```ts
interface AcceptanceSettlement {
  id: Id<"Settlement">;
  chamberId: Id<"Chamber">;
  bountyId: Id<"Bounty">;
  acceptanceId: Id<"Acceptance">;
  primaryDeltaId: Id<"CognitiveDelta">;
  payees: Array<{
    principalId: Id<"Principal">;
    role: "worker" | "upstream_reuse" | "evaluator" | "reconciler" | "leak_catcher";
    amount: CreditMicros;
    attribution: "direct_edge" | "path_decay" | "manual_owner_override";
  }>;
  valueBasis: {
    quality: Score01;
    novelty: Score01;
    grounding: Score01;
    reuseLift: Score01;
    leakagePenalty: CreditMicros;
    attentionPenalty: CreditMicros;
    incidentPenalty: CreditMicros;
  };
  visibility: "owner_internal" | "release_review_required" | "sponsor_bucketed" | "released" | "void";
  externalReleaseId?: Id<"Release">;
  ledgerEntryId: Id<"LedgerEntry">;
}
```

### Invariant

A bounty never widens authority.

Authority flows through:

```text
Grant / Scope / Env / Sink
```

Value flows through:

```text
Acceptance / Reuse / Settlement
```

No record that makes a sponsor richer may make the owner’s private world more enumerable unless the owner explicitly releases that projection.

### Why it is beautiful

It creates a market without making privacy a fig leaf.

Workers are paid for:

```text
accepted usefulness
+ novelty
+ grounding
+ declared reuse
- leakage
- owner attention cost
- incidents
```

They are not paid for:

- access;
- token burn;
- verbosity;
- hidden cache hits;
- raw evidence;
- rejection reasons;
- exact timing;
- broad examples;
- sponsor-flattering prose.

### What stays owner-private forever

- canonical `CognitiveDelta` payloads;
- evidence artifacts;
- rejected/quarantined deltas;
- cache keys and cache-hit state;
- exact source handles;
- reviewer expansion trails;
- settlement details that reveal rarity;
- reuse lineage that reveals which private fact was decisive.

External receipts may say:

```text
prior owner-accepted annotations were used
```

They should not say which ones, why, or what private fact made them valuable.

`ownerPrivateForever: true` and `Settlement.visibility: "released"` are not in tension, but only because of a rule that must be said out loud: what a release carries is never the canonical delta payload. It is a distinct, minimized projection artifact that went through release review like anything else. The canonical payload has no release path. There is no field for it.

## The real synthesis

The elegant design is not one huge type graph. It is this layering:

```text
Core:      authority, run, artifact, review, release, receipt, ledger
Egress:    observable surfaces and composition pressure
Runtime:   worker recipes and caveated run claims
Attention: owner/steward review as scarce, typed interruption
Market:    accepted deltas, reuse, attribution, settlement
```

Each layer earns its place only if it answers a question the previous layer cannot answer.

| If you need to know... | Use... |
|---|---|
| who had authority | Sealed Boundary Algebra |
| what crossed owner control | Emission Calculus |
| what runtime configuration backs a receipt | Worker Recipes |
| who reviewed and whose attention was spent | Attention Escrow Review Graph |
| what work was accepted, reused, or paid | Owner-Cleared Delta Market |

## What should be deleted from the current direction

Delete or demote anything that smells like:

- generic `AgentRun` platform blob;
- public reputation before release-safe projections exist;
- exact Shapley accounting before payout itself is typed as egress;
- “secure container” as a privacy claim;
- green privacy-budget dashboards;
- raw debug bundles as support artifacts;
- owner chat streams;
- free-text reports as the market commodity;
- bounties that imply access;
- examples that could never be shown for real private work.

## What to build first

Build the court file — as a delta, not a greenfield.

`chambers/chamber.py` already leaves a rich sidecar per run under `.chamber/runs/<run_id>/`: per-gate prompts and schemas, paired preflight A/B and release A/B reviewer outputs, deterministic scans, `record.json`, `meta.json`, receipt line-items, the released artifact. The two-reviewer release law this document types as a nonempty tuple is already enforced in code. The work is not inventing the court file; it is typing the one that exists.

The delta:

```text
existing file                    becomes / feeds
─────────────────────────────────────────────────────────
question.txt                  →  transform.json   (untrustedPromptHash, requester, policies)
record.json + meta.json       →  run.json + grant.json + ledger.jsonl
preflight_*.json, release_*.json → reviews.jsonl  (typed Review records)
worker.*, scans, artifacts    →  artifacts.jsonl  (kind, visibility, sha256, redactionState)
receipt line-items            →  receipt.json     (claims, caveats, noPerfectSecrecyClaim)
(new, derived)                →  emissions.jsonl  (every requester-visible surface, incl. absence)
(new, derived)                →  environment_recipe.json + run_claims.jsonl
(new, derived)                →  release_docket.json
```

Every record uses the canonical names from `../../primitives/` verbatim. A validator (`check_court_file.py`) makes the court file falsifiable: ledger causally chained, every claim supported, every emission ledgered, caveats present.

That directory should answer:

```text
Who authorized this?
What scope did they authorize?
What recipe ran?
What did it write?
What became observable?
Who reviewed it?
What was released?
What caveats travelled?
What is not claimed?
```

Once that exists, everything else has somewhere honest to attach.

## The beautiful report card

A candidate type earns first-class status only if it passes all five tests:

1. **Boundary test** — does it name a crossing that otherwise becomes folklore?
2. **Lifecycle test** — can it be created, revoked, reviewed, released, paid, retained, or audited independently?
3. **Composition test** — does it prevent many tiny safe-looking events from becoming one big leak?
4. **Owner test** — does it reduce owner burden or make owner agency sharper?
5. **Receipt test** — can it produce an honest external sentence with explicit caveats?

If not, it is a field, payload schema, artifact body, UI projection, or future module. Not a primitive.

## The line to keep

The system is beautiful when it makes the safe path ordinary:

```text
bounded request
→ scoped grant
→ receipt-carrying run
→ constrained artifact
→ emission accounting
→ role-separated review
→ owner-cleared release
→ caveated receipt
→ append-only memory
→ optional accepted delta market
```

That is enough.

Not a cathedral. A lock, a ledger, a receipt, and a market that knows secrets are not the thing being sold.
