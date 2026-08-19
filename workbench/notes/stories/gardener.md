# The gardener

Full ledger depth for STORIES.md Story 6: strangers improving each
other's codebases through a third-party agent, with the CI verdict as a
mechanical settlement oracle. The premier use case "paid oracle-approved
PRs" (README) finally storied — and it turns out to be the second wedge
where G1 (outcome attestation) never bites, for the same reason as the
frontier-labs story: **the oracle's verdict is itself a metered charge
event**, so value releases against receipts all the way down.

## Cast

Maya maintains a solo infrastructure product; her private repo holds a
battle-hardened backoff/retry module and, unknown to her, a latent
deadlock in her connection pool. Ravi's startup fixed that deadlock's
exact twin eight months ago (three days of pain, one subtle commit); his
repo carries a naive backoff that falls over under the load patterns
Maya solved in 2024. Neither would ever show the other their code.
A third-party **gardener** agent is leased into both chambers.

## The sweep (observation, priced)

The gardener reads both repos inside their chambers — metered against
`("exp", maya_repo, gardener_vendor)` and `("exp", ravi_repo,
gardener_vendor)`, the LIFETIME accounts answering "how much of my
codebase can this vendor's agent ever see, cumulatively, forever." Its
annotations (call graphs, defect hypotheses, style maps) stay
silo-local: in-chamber richness is free (`SelfFree` — the coalition
zero-point); only crossings cost.

Never-reveals hold structurally: Ravi's licensing-enforcement core is a
never-leased sub-source (G5). The gardener does not see it, cannot
charge for it, cannot leak it.

## The find (a coalitional derivative)

"Ravi's fix-pattern from commit-cluster X resolves the deadlock class in
Maya's pool module" is an artifact whose provenance names both silos —
a `CoalitionalDerivative`, born confined. Nobody has been told anything
yet.

## The offer (typed, cheap) vs the patch (raw, expensive)

The **price gradient is the product decision**, straight from the
estimator probe's proven ceilings:

- **The hint** — a typed offer card to Maya: defect class (CWE-style
  enum, 8 bits), affected-module bucket (4), fix-shape taxonomy entry
  (6), confidence (2) ≈ **20 bits**, charged to
  `("exp", ravi_repo, maya)` — the existence and shape of Ravi's fix IS
  information about Ravi's engineering. Maya's own agent then
  re-derives the concrete fix *inside her chamber* using the hint —
  in-chamber derivation is free. This is LICENSING.md right 3
  (coalition-bound derivative) doing product work: what Maya bought is
  licensed latent formation, not Ravi's diff.
- **The patch** — the literal unified diff, if she wants it: raw bytes
  at the 8-bits/byte ceiling, maybe 2,400 bytes ≈ 19,200 bits — a
  thousand times the hint's exposure, priced accordingly. Almost nobody
  buys the patch. That is the meter teaching the ecosystem to compress
  (the consult's codebook thesis, observed in the wild).

## The oracle (why G1 never bites)

Payment terms: escrow releases when the fix is **green in Maya's CI**.
No outcome attestation is needed, because the CI run happens *inside
Maya's chamber as metered work*: the test-suite execution's verdict is
emitted as a typed judgement — a ChargeEvent with `accepted: true` —
and the escrow's `charge_ids` reference exactly that event. Pay-on-green
is `release(escrow, receipt=[ci_verdict_charge])` under a clean court.
Mechanical, stranger-auditable, no oracle theater.

The honest limit stays loud: **tests green is not correctness** (G2's
engineering cousin). The escrow buys "her suite passed," never "the bug
is gone." A gardener that games weak test suites is convicted by nothing
in the fold — it is priced by track record (L5), like every judgement
vendor.

## The split (provenance closure, live)

The release disburses through a pool: gardener's fee, and a
**source-repo royalty to Ravi** — the derivative's provenance named his
silo, so the payment names his account. This is G14 (provenance closure)
as economics: the emission toward Maya was never separable from its
ancestry, and neither is the money. Symmetrically, the same sweep sells
Maya's backoff wisdom back to Ravi; a codebase in the gardener's garden
is simultaneously mine and customer. People improving each other's
codebases without ever seeing them.

## Gaps this story feeds

- G1: closed here by construction (CI verdict = charge event) — pattern
  confirmed twice now; wedges should be CHOSEN for mechanical oracles.
- G3: a Sybil gardener fragments its lifetime read-budget across
  shells — visible under declared ownership hypotheses, priced not
  prevented.
- G14: the royalty edge is computable today; the audit family that
  convicts a dropped source is still owed.
- New pressure, named: **test-suite quality is an unpriced input** to
  the oracle. A `fee_schedule`-style declared coverage statement
  (G9-shaped) would at least make the weakness legible at escrow time.
