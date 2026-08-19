# Implementation roadmap: from beautiful primitives to running Chambers

This roadmap turns the research into a build sequence. The main constraint: **do not build a generic agent platform first**. Build the smallest durable Chamber loop that produces typed records, can be reviewed, can be released with caveats, can remember accepted work, and can later support bounties without selling access.

The current repo already has the right product seed:

- Current `chambers/chamber.py` runs a local owner-controlled demo.
- Current `chambers/CHAMBER.md` defines requester/owner split, output law, reviewer gates, residual risk, and receipt language.
- Current `docs/primitives/*.ts` now sketches core, entropy, environment, attention, and market primitives.
- The research memo `workbench/notes/research/canonical-type-signature-research.md` explains why the primitive set should be small and orthogonal.

The next implementation should be a sidecar, not a rewrite.

## 1. Product wedge

Build a **typed run ledger + environment receipt sidecar** for the current local Chamber.

Success means a normal Chamber run can produce append-only records sufficient to reconstruct:

1. who requested;
2. who owned;
3. what private classes were in scope;
4. what transform was authorized;
5. which worker package/env recipe ran;
6. which artifacts were produced;
7. which reviews happened;
8. what was released;
9. what receipt claims and caveats were shown;
10. which observable surfaces emitted;
11. which accepted annotations can be reused later.

Do this without changing the requester experience first. The owner console can show extra debug/report files, but the first value is provenance and reviewability, not UI.

## 2. Non-goals for the first wedge

Do not build these yet:

- public marketplace;
- arbitrary agent package registry;
- multi-tenant SaaS control plane;
- container fleet;
- TEE or DP claims;
- public reputation;
- public leaderboard;
- external payout rails;
- open-ended data connectors;
- warehouse-scale query engine;
- social matching network;
- generic chat app.

These all become safer after the ledger, environment receipt, and release semantics exist.

## 3. Minimum file layout

Add a small implementation package beside the current Python demo or as a `chambers/typed_records/` module.

Recommended initial layout:

```text
chambers/
  chamber.py
  CHAMBER.md
  typed_records/
    __init__.py
    ids.py
    schema.py
    ledger.py
    artifacts.py
    policies.py
    receipts.py
    scans.py
    sidecar.py
    tests/
      test_ledger_roundtrip.py
      test_receipt_caveats.py
      test_observable_surfaces.py
      test_release_redaction.py
```

If the repo pivots to TypeScript first, mirror the same concepts under `docs/primitives/` and a later runtime package. The Python sidecar is faster because `chamber.py` is already the running loop.

## 4. Data model for v0 sidecar

Use append-only JSONL plus content-addressed artifact files. SQLite can come later if queries matter.

```text
.chamber/runs/<run_id>/
  ledger.jsonl
  artifacts/
    <artifact_id>.json
    <artifact_id>.txt
  receipts/
    requester_receipt.json
    owner_receipt.json
  reviews/
    preflight_a.json
    preflight_b.json
    release_a.json
    release_b.json
  sidecar.json
```

### Why JSONL first

- Works with the current local demo.
- Easy to inspect and zip for owner-private support.
- Avoids migration work while primitives are still settling.
- Keeps append-only discipline visible.
- Makes tests simple: parse every line, validate transitions, verify hashes.

### Record envelope

```python
@dataclass(frozen=True)
class RecordEnvelope:
    id: str
    kind: str
    version: int
    run_id: str | None
    chamber_id: str
    created_at: str
    visibility: str
    body_hash: str
    body: dict[str, Any]
```

### Ledger event envelope

```python
@dataclass(frozen=True)
class LedgerEvent:
    id: str
    run_id: str
    action: str
    actor_id: str
    subject_id: str
    artifact_id: str | None
    previous_hash: str | None
    body_hash: str
    created_at: str
    visibility: str
    caveats: list[str]
```

Use stable JSON serialization for hashes. Do not catch broad exceptions and pretend success; fail closed and surface the error in owner-visible state.

## 5. Core sidecar records

### Principal

Represent current roles:

- owner;
- requester;
- worker;
- preflight reviewer A/B;
- release reviewer A/B;
- deterministic scanner;
- system.

The current demo can assign opaque IDs. Real auth can come later.

### Chamber

One local chamber per demo run or persistent owner workspace. Fields:

- owner principal;
- purpose;
- retention policy;
- default release policy;
- version;
- policy hash.

### Scope

For the current demo, `Scope` can be coarse:

- `local_work_history`;
- `home_directory_default` only as owner-private locator;
- `requesterVisibleClass = "work_history"`;
- selector hash;
- canary policy;
- disallowed classes.

The requester never sees raw path.

### Transform

Build from the approved menu question and output law:

- purpose;
- expected input policy;
- disallowed prompt classes;
- output shape: evidence cards + capped answer + receipt;
- review plan;
- sink policy.

### Grant

Build after preflight and owner approval:

- allowed scope IDs;
- transform ID;
- env recipe ID;
- validity window;
- max words;
- output policy;
- network policy;
- revocation state.

### Run

The current `RunRecord` in `chamber.py` can map to:

- queued;
- preflight;
- waiting_owner_execution;
- running_worker;
- release_review;
- waiting_owner_release;
- released;
- rejected;
- incident.

Keep current UX status coarse for requesters.

### Artifact

Make every durable body an artifact:

- requester prompt;
- preflight prompts/responses;
- worker prompt;
- worker stdout/stderr;
- structured worker artifact;
- deterministic scan;
- release reviewer prompts/responses;
- release candidate;
- approved answer;
- receipt;
- support bundle manifest;
- accepted annotation.

This is the single most important implementation move.

### Review

Create typed review files for:

- preflight A;
- preflight B;
- release A;
- release B;
- deterministic scanner as tool result, not independent reviewer.

### Release and receipt

Store released fields and redacted fields separately. The receipt should be an artifact linked to the release.

### LedgerEntry

Write ledger entries for every state change, artifact creation, review decision, owner decision, release, receipt, attention debit, incident open/close, and annotation acceptance.

## 6. Observable surfaces to instrument first

Start with the surfaces the current demo already has:

| Surface | Current source | V0 record |
|---|---|---|
| Requester status | requester page state | `ObservableEvent(class="requester_status")` |
| Owner console status | owner page | `ObservableEvent(class="owner_console")` |
| Worker prompt | `worker_prompt.md` | `Artifact(kind="prompt")` + `ObservableEvent(class="agent_prompt")` |
| Worker stdout/stderr | Codex result | `Artifact(kind="stdout")`, `Artifact(kind="stderr")` |
| Reviewer prompts/output | preflight/release prompts | `Artifact(kind="review_prompt")`, `Review` |
| Release answer | approved answer | `Release` + `Artifact(kind="release_answer")` |
| Receipt | receipt text | `ReceiptPayload` + artifact |
| Deterministic scan | scan function | `Artifact(kind="scan")` + `Review`/risk vector |
| Error state | exception/status path | `ObservableEvent(class="error")` owner-only by default |
| Timing buckets | run timestamps | owner-private; requester coarse only |

Do not expose exact token counts, byte counts, timing, file counts, or source paths to requesters.

## 7. Implementation phases

### Phase 1: schema-only sidecar

Deliverables:

- `schema.py` dataclasses or pydantic models for core records.
- Stable JSON canonicalization and hash helper.
- Append-only `ledger.jsonl` writer with hash chain.
- Unit tests for round-trip, hash stability, and broken-chain detection.

Acceptance:

- Can create a synthetic run with principal/chamber/scope/transform/grant/run/artifact/review/release/receipt/ledger records.
- Ledger rejects malformed records and hash-chain mismatches.
- No broad catch or silent success fallback.

### Phase 2: artifactization of current Chamber run

Deliverables:

- Wrap current prompt, worker output, reviewer output, scan result, release candidate, and receipt in artifacts.
- Store artifact hashes and visibility.
- Keep current requester UI unchanged.

Acceptance:

- A real local run produces artifact files and ledger entries.
- Owner can inspect artifact manifest.
- Requester still sees only current coarse status and released answer/receipt.

### Phase 3: typed reviews and release fields

Deliverables:

- Preflight and release reviews become `Review` records.
- Release stores approved fields, redacted fields, caveats, and owner decision.
- Receipt generated from release + review facts, not ad hoc prose.

Acceptance:

- A release reviewer rejection prevents release.
- A deterministic scan hit becomes a review risk and blocks or escalates.
- Receipt includes non-claims by construction.

### Phase 4: environment receipt

Deliverables:

- `EnvRecipe` for current worker mode: local read-only, no network or explicit model access policy, resource budget, logging policy.
- `EnvironmentReceiptPayload` records observed/configured runtime claims.
- Owner-visible caveat: local sandbox is not perfect secrecy.

Acceptance:

- Every grant points to an env recipe.
- Every run has an environment receipt artifact.
- Receipt does not overclaim isolation.

### Phase 5: accepted annotation cache

Deliverables:

- Owner can accept a reviewed evidence card as `CognitiveDelta` / `Annotation`.
- Later run can declare `ReuseEdge`.
- Invalidation record can quarantine stale annotations.

Acceptance:

- Accepted annotation is owner-private by default.
- Reuse is visible to reviewer.
- Release does not reveal raw source unless explicitly approved.

### Phase 6: attention cards

Deliverables:

- `ReviewCard` model for owner decisions.
- `AttentionDebit` records for authority/disclosure/economic/incident prompts.
- Batchable findings do not interrupt.

Acceptance:

- Owner console groups routine findings.
- Release and grant decisions still interrupt.
- Attention exhaustion blocks or defers non-critical disclosure.

### Phase 7: toy bounty simulation

Deliverables:

- In-process fake `Bounty`, `Acceptance`, `CreditSettlement` records without real money.
- Sponsor-visible output must pass release.
- Payout visibility is owner-only or bucketed.

Acceptance:

- Bounty cannot confer access.
- Unaccepted submissions are not sponsor-visible.
- Settlement is ledgered and caveated.

## 8. Testing strategy

Write tests around invariants, not implementation plumbing.

### Must-have tests

| Test | Failure it catches |
|---|---|
| Ledger hash chain rejects mutation | Hidden edit to audit trail. |
| Artifact hash changes on body change | Receipt points to wrong content. |
| Requester projection excludes owner-private fields | Accidental raw disclosure. |
| Release cannot happen without review | Approval shortcut. |
| Review approval is gate-scoped | `approved: true` reused at wrong stage. |
| Receipt always includes non-claims | Success-shaped privacy language. |
| Support bundle export requires review | Debug artifact leak. |
| Observable event emitted for requester status | Untyped side channel. |
| Exact count blocked in requester-visible answer | Corpus/match leakage. |
| Bounty cannot create grant | Payment-as-access bug. |
| Reuse edge required for downstream annotation use | Hidden cache leakage. |
| Incident freezes release/settlement | Continuing after known risk. |

### Avoid weak tests

- Do not snapshot exact wording unless wording is the product contract.
- Do not test default constants unless they encode a safety invariant.
- Do not mock away the artifact/ledger writer in invariant tests.
- Do not only test happy path.
- Do not assert that a scanner proves semantic privacy.

## 9. Developer ergonomics

The v0 API should be boring:

```python
sidecar = ChamberSidecar.open(run_dir)

owner = sidecar.principal(kind="owner", display="opaque")
requester = sidecar.principal(kind="requester", display="opaque")

chamber = sidecar.chamber(owner=owner, purpose="local bounded diligence")
scope = sidecar.scope(chamber=chamber, data_class="work_history", owner_locator=read_root)
transform = sidecar.transform(chamber=chamber, requester=requester, purpose=question, output_policy=policy)
env = sidecar.env_recipe(isolation="local_read_only", network="none", tools=["codex_worker"])
grant = sidecar.grant(chamber=chamber, transform=transform, scopes=[scope], env_recipe=env)
run = sidecar.run(grant=grant)

worker_prompt = sidecar.artifact(run, kind="prompt", body=prompt, visibility="owner_private")
worker_output = sidecar.artifact(run, kind="worker_output", body=output, visibility="owner_private")
review = sidecar.review(run, gate="release_review", artifacts=[worker_output], decision="allow")
release = sidecar.release(run, review=review, approved_fields=["answer", "receipt"])
receipt = sidecar.receipt(release, claims=[...], caveats=[...])
```

Each call writes a ledger entry. If a call cannot validate or persist, it raises and leaves an owner-visible error. No success-shaped fallbacks.

## 10. Migration path from current `chamber.py`

### Low-risk insertion points

1. After run record creation: create `Principal`, `Chamber`, `Scope`, `Transform`, initial `Run`.
2. After preflight prompts are saved: create prompt artifacts.
3. After preflight outputs: create review artifacts and `Review` records.
4. Before worker execution: create `Grant` and `EnvRecipe`.
5. After worker result: create stdout/stderr/output artifacts.
6. After deterministic scan: create scan artifact and risk review.
7. Before owner release decision: create `ReviewCard` and `AttentionDebit`.
8. After release: create `Release`, `ReceiptPayload`, and final ledger entry.

### Risky insertion points

- Changing requester status strings: can create observable behavior changes.
- Changing worker prompt law: can change output quality and leakage profile.
- Changing passcode/TTL handling: can break demo access semantics.
- Changing cleanup of raw artifacts: can either lose forensic data or leak it.
- Changing release scan regexes: can cause false confidence or false blocks.

Start by sidecar-writing records without changing decisions.

## 11. TypeScript primitives status

Current primitive docs are useful as design pressure and future implementation reference:

- `primitives/core.ts`: boundary algebra and core records.
- `primitives/entropy.ts`: observable egress accounting.
- `primitives/environment.ts`: runtime envelopes and receipts.
- `primitives/attention.ts`: review cards, queues, attention debits, notification policy.
- `primitives/market.ts`: cognitive deltas, bounties, acceptances, reuse credit, attribution, settlement, feeds.
- `primitives/index.ts`: export surface.

These should not become app code until the Python sidecar proves which records are needed in real runs. Keep the TypeScript as a crisp reference, not a second source of operational truth.

## 12. PySyft inspiration to keep

PySyft is useful as inspiration for control plane shape, not as a direct architecture import for this wedge.

Adopt:

- owner runtime / datasite concept;
- service registry shape;
- request and approval workflow;
- policy-gated code execution;
- mock/private split as review metaphor;
- worker pools and job state;
- output service;
- blob/object provenance;
- client/server API dispatch discipline.

Do not steal yet:

- object store as private-data warehouse;
- Python object pointer as core product primitive;
- approved code execution as default value proposition;
- heavy server/service stack before local ledger works;
- warehouse-scale storage abstraction.

Scry's stronger primitive is not remote object permission. It is reviewed, constrained, caveated cognitive output from private context.

## 13. External research anchors to preserve

The external anchor files in `external-anchors/` are not product dependencies. They are prompts for future judgement work:

- information flow control for LLM agents: reinforces observable-surface accounting and prompt/output taint thinking;
- Shapley/data valuation papers: useful for thinking about dynamic contribution and reuse credit, not direct payout truth;
- human attention / notification fatigue: reinforces attention as a scarce boundary;
- confidential computing receipts: useful for environment receipt caveats, not proof of semantic privacy;
- DP composition queries: useful as warning that privacy math applies only to narrow mechanisms.

Do not cite these as settled authority without reading the full paper. Use them as a research queue.

## 14. First implementation issue set

If converting this roadmap into issues, use this order:

1. Add sidecar schema package.
2. Add stable JSON hashing and artifact writer.
3. Add append-only ledger with hash chain.
4. Add projection helper for requester-visible run state.
5. Wrap current prompts and outputs as artifacts.
6. Emit preflight and release reviews as typed records.
7. Generate receipt from typed release facts.
8. Emit observable events for requester status and release answer.
9. Add support bundle policy and owner-only export manifest.
10. Add accepted annotation record.
11. Add declared reuse edge in a synthetic second run.
12. Add toy bounty/acceptance/settlement simulation with no real payout.

## 15. Verification gate for the wedge

The wedge is done only when a real local run can answer these questions from records alone:

- Who asked?
- Who owned?
- Which scope class was authorized?
- Which worker recipe ran?
- Which artifacts were produced?
- Which review gates passed or failed?
- Which fields were released?
- Which caveats were shown?
- Which surfaces were observable to requester, owner, worker, reviewer, and system?
- Did any incident open?
- Which accepted annotations can be reused?
- Can the ledger detect tampering?

If any answer requires reading an ad hoc transcript or trusting a mutable Python object, the sidecar is not finished.

## 16. Product roadmap after the wedge

### Next: owner-private research institution

Add accepted annotation cache, review files, invalidation, and reuse edges. This makes the Chamber compound.

### Then: safe sponsor-funded work

Add toy bounties and credit settlement. Keep all payouts fake/internal until payment itself has release semantics.

### Then: mediated matching

Add bilateral release and denominator guards. Do this before any public matching surface.

### Then: partner environments

Add richer env recipes, package admission, tool grants, and support bundle policies. Only then consider containers, k8s, or TEEs.

### Then: public receipts and reputation

Expose only caveated, release-reviewed aggregates. Never let reputation reveal private-domain volume by default.

## 17. The build mantra

One local Chamber run should leave a small court file:

```text
who asked
who owned
what scope was granted
what recipe ran
what artifacts were created
who reviewed
what was redacted
what was released
what caveats traveled
what got accepted for reuse
what the ledger can prove
what the receipt explicitly does not claim
```

Build that first. Everything else is leverage on top of it.
