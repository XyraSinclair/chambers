# Machines — what runs today

The operational register: one entry per machine that exists, the command a
stranger can type, what a green run proves, and the named gap between it and a
real deployment. Companion to [`ASSURANCE.md`](ASSURANCE.md) (what is
*known*) — this file is what is *runnable*. Nothing enters without a command a
stranger can type. Design sources marked *private* are the operator's records;
nothing normative rests on them.

## Running today

### chamber-node/1 — the protocol endpoint

```text
python3 -m chambers.kernel.node
```

Open-write ledger node: POST events, GET fold/audit/settlement/verify. The
security model is the theorem list (content-addressed identity, total folds,
escalation-only verdicts, fail-closed value), not auth.

### Federation

Two nodes + `GET /v1/ledger → POST /v1/events` each way. Replication is merge:
byte-identical convergence, no consensus, Byzantine facts propagate as
convictions (`test_node_federation.py`).

### The paid-judgement economy

```text
python3 -m chambers.kernel.demo_work_economy
```

Value moves iff metered work moved: deposit → escrow → atomic emission →
release against the receipt → refund, one artifact, tamper-convicting.

### The 50¢ notification

```text
python3 -m chambers.kernel.demo_attention_notify
```

Attention is the second key family: rings paid to the bell's owner, refusal
*before* third-party leakage, epochs regenerate.

### attention-node/1 — the notify economy served

```text
python3 -m chambers.kernel.attention_node
python3 chambers/kernel/test_attention_node.py   # lane
```

chamber-node/1 plus one verb: `POST /v1/notify` = funds check → attention
charge first (a refused ring leaks zero third-party exposure) → exposure
charge → escrow+release bound to the exact ring, payee = the bell's owner
(G6); `GET /v1/attention` is the court's per-account view. Provisioning *is*
the open-write endpoint — parties post register/lease/deposit facts and the
node adopts leases addressed to it from the ledger, so provisioning, restart
hydration, and federation are one code path; the whole economy merges into a
plain chamber-node/1 and verifies CLEAN.

### Scoped courts — charge-scope/1

```text
python3 -m chambers.kernel.node --scoped-only
python3 chambers/kernel/test_scope.py            # lane
```

Reader-scoped views with theorems: every served event carries a Merkle
membership proof against a head committing to the whole court; the node's
serving history is an append-only log a rewrite cannot fake (RFC 6962/9162,
brute-force cross-checked; SUNDR fork consistency); withholding leaves
charge_seq gaps the scoped verifier reports. Refusals named: inclusion not
completeness, unsigned heads, scope ≠ solvency.

### The $5-if-they-talk tier — outcome settlement (charge-settlement/2)

```text
python3 chambers/kernel/test_settlement2.py
python3 -m chambers.kernel.verify chambers/kernel/settlement2_traces/platform-override-slash.ledger.jsonl
```

Release gated on a bonded, independence-classed, contest-hardened attestation
quorum (S9); bonds conserve (Lean-proven) and slash only under strictly better
evidence (S10) — the verifier output shows a platform log convicting a bonded
ruling, the slash flowing to the harmed payer, and the leaning release
convicted. Counterfactuals refused; anti-holdup both directions; served by the
node (`test_node.py::test_outcome_economy_served_end_to_end`).

### The metered sort — cardinal's output priced

```text
python3 -m workbench.cardinal_wedge.run_sort_metered
```

A ranking of n private items is a coupled emission of log₂(n!) ordering-mbits
against all n sources; pairwise reads metered as observation; fee released
against the ranking receipt. The kernel prices cardinal-harness's output
(adoption #2 from a *private* mapping report; ranking oracle mocked hermetic,
kernel side identical to production).

### review-audit/1 — the reviewer coherence audit

```text
python3 -m chambers.review_audit.battery
python3 chambers/review_audit/test_review_audit.py   # lane
```

The judgment layer gets receipts: a frozen content-addressed battery
(270 probes: order swap / re-wording / requester framing / polarity, null
calibration, drift repeats) audits any `review()` judge; the receipt is
integer-only counts (exact bytes a stranger re-derives, golden ids pinned);
R1–R7 convictions in permille arithmetic from the receipt alone.
Self-validated against scripted judge pathologies, sharpened to
whole-signature equality over nine scripted pathologies — including the
negative claim that symmetric noise does not trip the SIGNED sycophancy code.
Structured-judgment level only: it measures judges, meters nothing
(PROBE-SPEC §0). Adoption #1 from a *private* mapping report (G10).

### Closure charging — charge-provenance/1 (G16, the moat law)

```text
python3 chambers/kernel/test_provenance_p.py
```

Depth is not dilution: a derived fact's emission must charge its transitive
ancestry at the integer max-flow DPI bound or convict (P1 dropped ancestor,
P2 undercount, P3 orphan); multi-hop laundering convicts; value fails closed
against P-dirty courts; separate `p_codes` surface, frozen corpora untouched.
Named residue: undeclared emissions are invisible (G8's trust class).

### The judgement market — peer prediction under metered leakage (F5, G10)

```text
python3 -m workbench.peer_sim.run_peer_prediction
python3 workbench/peer_sim/test_peer_sim.py      # lane
```

Honesty priced without ground truth, with the mechanism's own redundancy
metered openly: exact-integer correlated agreement over two judges' reports
(the constant-report strategy scores exactly zero, an identity); the v0
low-sensitivity coupling settles fees + CA bonus receipt-bound with
`redundancy_mbits` printed, court CLEAN; the kill regime is live — the owner's
ceilings REFUSED_CEILING the audit reader, the bonus refunds untouched, and
honesty above the moat line stays priced by process receipts. Named gaps:
reports ride sim-local books (score-bound escrows await a report event kind,
/3); correlation is not truth.

### The split rule — charge-attribution/1+2 (F6, the G20 gap)

```text
python3 chambers/kernel/test_attribution.py
python3 chambers/kernel/test_attribution_split.py    # enforcement lane
python3 chambers/kernel/test_attribution_traces.py   # frozen corpus: 8 golden ledgers, the counterparty target
```

Attribution is a recomputable fact, not a percentage: a pot divides across a
derived fact's sources by exact-integer Shapley over the DPI capacity the
P-codes already charge; a misdeclared split convicts from bytes (V1–V5) *and*
the money obeys — split-bound escrows disburse only along the recomputed rows
(S11/S12), V findings dirty the named contributor's court, and the stiffed
contributor collects her own row after expiry with nobody's permission (F4).
Conservation is a Lean theorem for every tie-break; the alpha story (1/8000 of
$100M → exactly $12,500.000000, releasable by alice herself) is a passing
test. Residues: Rust-twin parity for V/S11/S12; outcome-conditioned split pots
refused (/3).

### Derived views — charge-views/1

```text
python3 -m pytest chambers/kernel/test_views.py -q
python3 chambers/kernel/emit_views_traces.py     # corpus
```

Interpretation is policy, not fold: `view(fold, policy)` labels accounts under
a content-addressed policy (strictly-increasing boundaries make
escalate-never-retract structural for *every* admissible policy); fold/1's
embedded `leakage_class`/`incident` are provably the legacy-default view,
bit-for-bit over all 16 frozen ledger corpora (the parity law — meaning moved,
zero bytes moved); out-of-domain keys read `"void"`, never a lying class;
W1/W2 refuse all-or-nothing. Residues: entropy provenance + policy
registration are E4's; presentation layers must not render labels as
calibrated until registers carry provenance.

### The party lane — both consumer fee legs, end to end

```text
python3 -m workbench.intro_clearing.run_clearing
python3 workbench/intro_clearing/test_party_outcome.py   # lane
```

The party scenario as ledger arithmetic on the real kernel: 50¢-to-raise
(attention charge before exposure, released against the exact ring receipt) +
$5-on-outcome (charge-settlement/2 outcome escrow, platform-log lane,
first-contact attribution as the release's ledger fact). Three acts — talk
pays, silence refunds mechanically, the lie is refused live then slashed by
strict override — 62/62 self-checks, conservation exact. Named gap: the
house's internal fees still ride sim-local books (`PARTY_LANE_GAPS`).

### Attributable authority — charge-identity/1

```text
python3 chambers/kernel/test_identity.py
```

Identity *is* the key: an author id may be `ed25519:<pubkey>`
(self-certifying, no registry, no merge-order dependence) and every event it
authors must carry an RFC 8032 signature over its canonical bytes or convict
(A1/A2, separate surface). Pure-stdlib Ed25519 pinned to RFC §7.1 vectors,
strict (s < L, canonical encodings, total). The lane's teeth: a forged
10⁹-ucr mint in a key's name convicts under the stranger's verifier; 45
golden ledgers move by zero bytes. Bonds now slash a key, covenants bind a
key, attestors answer with a key. Residues: Sybil stays L5/G3, rotation is
/2, Rust port owed.

### The pipeline — the composed system

```text
python3 -m workbench.pipeline.run_pipeline
python3 workbench/pipeline/test_pipeline.py      # lane
```

Nine machines as one system over real files on disk: Alice's agent emits
schema-bound finding-cards over bounded repos; lifetime moats cap what it can
ever learn (bulk-exfil hits REFUSED_CEILING with the demand recorded); a
reviewer seated only on a clean coherence receipt (seat key-signed,
charge-identity/1) reproduces findings against the bytes — the smuggler's
excerpt card is refused and the secret appears nowhere in the artifact; paid
rings on the owners' bells, budget-bounded; every fee released against the
exact receipt. Byte-deterministic, 28 self-checks, CLEAN across I/S/X/C/P/A,
conservation exact. Zero new mechanism needed — the composition parsimony
test, passed.

### The stranger's verifier (Python)

```text
python3 -m chambers.kernel.verify ARTIFACT
```

Both layers + conservation from bytes alone.

### The counterparty verifier (Rust)

```text
cargo test    # in chambers/kernel/rust_ledger; binary: charge-verify
```

Independent re-implementation from the specs alone, both layers (settlement
port landed 2026-07-06): information 16/16, settlement 26/26 (13 `/1` + 13
`/2`) bit-for-bit; verdicts information fold + S1–S10 + conservation from
bytes alone; cross-checked CLEAN/CONVICTED against a live attention-node
artifact outside any corpus. The differentiated haul: 8 recorded spec
ambiguities in the crate README where the golden bytes force what the spec
underdetermines — standing spec-tightening candidates.

### The proof kernel

```text
cd chambers/lean && lake build
```

20+ machine-checked theorems, axiom-guarded; golden traces from the Python
reference replay by `rfl`.

### Private machine, not in this release

The L5 chamber wedge — the operator's live diligence deployment (`chamber.py`
+ its dogfood log) runs against the operator's own private context and stays
home. Its kernel accounting is the same `KernelMeter` path every machine above
exercises; nothing it proves depends on code absent here except the wedge's
own private data.

## The endpoint gap register — what a real deployment still needs

Closed rows, kept for the record — each shipped surface now lives in the
running register above:

- **E1** (shipped 2026-07-06) — outcome attestation + quorum release
  (charge-settlement/2); intro_clearing's contingent leg wired the same day
  (the party lane). Design source: SETTLEMENT-SPEC Part II.
- **E2** (shipped 2026-07-06) — charge-scope/1 (`scope.py`, `SCOPE-SPEC.md`):
  reader-scoped views with Merkle membership proofs + append-only consistency
  proofs; `--scoped-only` makes keys bearer capabilities; residues named:
  inclusion not completeness, unsigned heads (L5), scope ≠ solvency. Design
  source: FRAMEWORKS F2 (CT logs + SUNDR fork consistency).
- **E3** (shipped 2026-07-06) — attention-node/1, the served notify economy;
  residues: price discovery is the payer's declaration (receiver tariffs are
  an E4 schema question), identity stays declared (L5), read privacy stays
  E2's. Design sources: `demo_attention_notify.py`; STORIES G6.
- **E5** (shipped 2026-07-06) — charge-covenant/1 (`covenant.py`,
  `COVENANT-SPEC.md`): cease/cap covenants with content-addressed
  grandfathering ("these named grants survive; nothing else, ever"), C1–C3 on
  a separate surface, LeaseIssuer refuses its own covenant-breaking grants,
  value fails closed on covenant-broken authority (C-codes join the
  dirty-court stream), X0 covers equivocation for free; lane
  `test_covenant.py` (the Bob-leaves exit story end to end). Why it mattered:
  revocation = tenor + covenant + residue statement — the exit story that
  makes upload sellable. Design source: design consult (2026-07-05,
  *private*) §4.
- **E6** (shipped 2026-07-06) — charge-substrate/1 (KERNEL-SPEC Part II): X0
  convicts (actor, kind, seq) equivocation for all kinds including future
  ones; separate `x_codes` surface so nothing frozen moved; I8/S5 now
  instances; lane `test_substrate_x0.py` (the load-bearing test equivocates a
  kind the auditor has never seen). Why it mattered: the lesson stops being
  relearned — E4/E5 kinds arrive covered. Design source: design consult
  (2026-07-05, *private*) §5.
- **E7** (shipped 2026-07-08) — charge-views/1; each conviction answered:
  labels bound to policy hash + the exact integers they were computed from,
  thresholds versioned out of the fold (fold/1's embedded fields redefined as
  the legacy-default view, provable bit-for-bit — the §V.5 parity law over
  frozen bytes), `"void"` reserved where the denominator has no meaning (the
  attention lie unrepresentable). Residues (entropy provenance, policy
  registration) moved to E4. Argued independently three times (dogfood
  finding 2, consult, the attention demo's void labels).

Open rows, ordered by ripeness:

- **E4 — schema catalog.** Content-addressed schema registration events;
  probes run against catalog entries. Binding amendment (moats frontier): the
  catalog and attestor sets ship permissionless and forkable at genesis —
  standardized receipts are fungible receipts, and whoever controls catalog
  admission captures the ecosystem; codebook capture is unpriceable unless
  forkable. Why: the price-gradient answer to generality — "the meter is the
  training loss of the ecosystem's codebook," but the codebook is the
  ecosystem's moat, not any owner's. E4 also holds two of E7's named
  residues: entropy provenance and policy registration. Design sources:
  design consult (2026-07-05, *private*) §3; private-data-moats frontier.
- **E8 — transport hardening.** TLS, size/rate policy, persistence
  compaction. The minimum for the reality-contact tranche is planned
  (*private* runbook): Caddy TLS termination in front, protocol untouched,
  non-hardened scope named and priced. Deployment table stakes; deliberately
  not protocol.

Standing argument (2026-07-08): before E4, a reality-contact tranche is
owed — private dogfood run 4 with an external requester over TLS (minimum
E8), the deploy gate exercised. The denominator that matters is the dogfood
log's: 3 real runs against ~20 shipped surfaces, and the two protocol-grade
findings reality has filed were invisible to every sim and every proof. Let
reality file the next ones; let entropy provenance arrive as E4's forcing
function rather than another interior row.

## The runtime ladder — orthogonal to the endpoint register

The endpoint register above is the *accounting* machines. These are the
*execution* machines — the TCB-shrinking ladder described in
[`RUNTIME.md`](RUNTIME.md). We are on R1.

- **R1 — operator-observed** (running). claimClass `operator_observed`; TCB =
  operator host + OS sandbox. Done: the private chamber wedge records
  mount/tool/network/output hashes per run.
- **R2 — reproducible-local** (first artifact running). claimClass
  `reproducible_local`; TCB = deterministic build + pinned inputs. Shipped
  2026-07-06 as `runtime-r2/1`:
  `python3 -m chambers.runtime.runner run chambers/runtime/bundles/match_card`;
  lane `python3 chambers/runtime/test_runner.py`. Content-addressed bundle,
  double-run issuance (deterministic or no receipt), stranger's one-command
  re-run verifier; golden bundles = the card projection + the ranking
  comparator; nondeterminism refused with certain witnesses; claim-class
  promotion is malformed. Owed second artifact: rootfs/interpreter pinning
  (Nix/OCI) — today the interpreter is declared, not pinned. No LLM call
  rides R2 (RUNNER-SPEC §0).
- **R3 — hardware-attested** (open). claimClass `tee_quote`; TCB = silicon
  vendor + audited enclave. To build: TEE runner + attestation-gated key
  release; decryption gated on a valid quote removes the operator from the
  TCB (frontier #6).

R2 is the first rung a stranger's data can honestly ride; R3 is the first
that works between mutually-distrusting parties. Neither needs new theory —
the accounting is proven; this is where-it-runs engineering.
