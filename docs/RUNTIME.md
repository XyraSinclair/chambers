# Runtime — how the work actually runs over private data

ASSURANCE.md is the ladder for the ACCOUNTING (can a stranger check what
crossed?). This file is the ladder for the EXECUTION (can a stranger
trust *where and how* the work ran?). They are orthogonal and both
required: a perfectly-metered emission from a worker that secretly
phoned home is still a leak the meter never saw. The whole point of a
private cognitive work economy is that people get comfortable letting
background agents do L-cognitive work over each other's data — and
"comfortable" is not a feeling, it is a claim class on a receipt that a
counterparty can independently raise or lower.

The organizing question, per run: **what is the trusted computing base
(TCB), and what does the receipt let a skeptic verify about it?**

## The execution ladder (four rungs, we are on rung 1)

The canon declares the ladder: `EnvironmentReceiptPayload`
(environment.ts) carries a `claimClass`, and its enum IS the rungs.
Honest state: the running chamber (the private wedge) emits an
environment recipe with the R1 observation hashes (mount / network /
model / logs) but does NOT yet construct the receipt payload or stamp a
`claimClass` — the field is declared type surface, not an emitted
runtime fact. Each rung below is honest about its own TCB.

**R0 — Declared.** The recipe says read-only, network-off, no training
use. Nothing checks it. TCB = the operator's word. Useful only as a
statement of intent; a receipt at R0 is a promise, not evidence.

**R1 — Operator-observed (WHERE WE ARE).** `claimClass:
"operator_observed"`. The private chamber wedge runs the worker as a real `codex exec`
under a read-only sandbox, web disabled, ephemeral, and the run RECORDS
what it observed: mount hashes, tool hashes, the network mode, the
output hash, the model/service tier (`finalize_claims`, RunClaim). TCB =
the operator's honest kernel + the OS sandbox. A skeptic who trusts the
operator's host gets a real, hash-pinned account of the configuration;
one who doesn't gets nothing stronger than R0. This is enough to
dogfood over YOUR OWN data (private dogfood runs 1–3), which is exactly why
the wedge started there: the operator and the subject are the same
person, so the TCB question is vacuous.

**R2 — Reproducible-local.** `claimClass: "reproducible_local"`. The
agent package (`AgentPackage.bundleHash`, `noMutableRemoteCode: true`)
plus the recipe (`rootfsHash`, `baseImageHash`, mount glob hashes) pin
the run to a content-addressed, deterministic environment: a second
party re-runs the same bytes on the same inputs and gets the same output
hash. TCB shrinks to "the build is deterministic and the inputs were
what the receipt says." This is the first rung a STRANGER's data can
honestly ride, because reproduction is a check they can perform, not a
trust they must extend. **First artifact shipped 2026-07-06:
`runtime-r2/1`** (`chambers/runtime/RUNNER-SPEC.md`) — the
content-addressed bundle, the double-run issuance law (deterministic or
no receipt), and the stranger's one-command re-run verifier, with the
two consumer-story workloads as golden bundles (the match-card
projection, the ranking comparator). Two disciplines stated bluntly in
the spec: R2 claims reproducibility, not confidentiality; and NO LLM
call rides R2 — R2 workers are the deterministic shells around the
model, with recorded model outputs pinned as bundle inputs. Owed second
artifact: interpreter/rootfs pinning (`rootfsHash`, `baseImageHash` —
a Nix/OCI build); today the interpreter is declared, not pinned.

**R3 — Hardware-attested.** `claimClass: "tee_quote"`. The worker runs
in a TEE (SEV-SNP / TDX / a well-audited enclave); the receipt carries a
signed quote binding the code-measurement hash to the output. TCB
shrinks to the silicon vendor + the enclave's audited code. Now the
OPERATOR is removed from the TCB: the data owner's chamber can require a
valid quote before decrypting inputs to the enclave, so even a malicious
host cannot read the plaintext. This is frontier #6 (TCB minimization),
canon's standing non-claim, and the only rung that makes "agents doing
background work over each other's data" comfortable BETWEEN mutually
distrusting parties at scale.

The honest law, already in canon (`ENVIRONMENT_LAWS`):
`receiptsDescribeObservedConfigurationNotPerfectIsolation`. A receipt is
evidence at its claim class and NOTHING above it. Selling an R1 receipt
as an R3 guarantee is the exact dishonesty this ladder exists to make
impossible — the class is on the receipt, in the fold, checkable.

## Where encryption lives (and where plaintext appears)

The confidentiality boundary is the chamber, and the ladder above is
precisely the story of WHO can be inside it when plaintext exists:

- **At rest / in transit**: standard envelope encryption; uninteresting,
  assumed. Private worlds are ciphertext everywhere except during a run.
- **The decrypt moment is the whole game.** Data becomes plaintext only
  inside the execution environment, for the duration of one metered run,
  and the receipt's claim class says who could have observed it then:
  - R1: the operator's host could (you trust the operator).
  - R2: the operator's host could, but the computation was
    deterministic and re-checkable, so *what* it did with the plaintext
    is pinned even if *seeing* it wasn't prevented.
  - R3: nobody outside the enclave could — decryption is gated on a
    valid attestation quote, so the key release IS the access-control
    primitive. The data owner encrypts to the enclave's measurement,
    not to a host.
- **Egress re-encryption**: whatever crosses is the typed projection,
  re-encrypted to the reader's key. The meter charges the projection's
  capacity; the crypto ensures only the charged reader can open it. The
  bits the ledger counts and the bytes the cipher protects are the same
  emission, bound by the escrow's `charge_ids` (the settlement layer
  already keys releases to exact charge events — the crypto layer keys
  decryption to the same events).

Nothing here needs new math; it needs the R2/R3 runner and a key-release
service that gates on `claimClass`. The accounting is done; the
substrate is the build.

## Private data sync = the CRDT, already built

"Private data syncs" sounds like new infrastructure; it is
`chamber-node/1` (node.py) plus envelope encryption. The state is a
grow-only content-addressed set, so:

- **Replication is merge** — two nodes converge by exchanging events,
  proven byte-identical over real HTTP (test_node_federation.py), no
  consensus, order-free, idempotent. A "private data sync" is that
  exchange with each event encrypted to the recipient coalition.
- **Partial sync is honest** — a reader gets exactly the sub-court their
  keys open; the fold over their partial view is still total and still
  convicts (missing facts can only make a court cleaner-looking, never
  forge a cleaner verdict — merge_escalates, Monotone.lean). The frontier
  gap is READ SCOPING (MACHINES.md E2): today node.py serves the whole
  artifact; a real deployment serves reader-scoped, reader-encrypted
  views of the same underlying set.
- **No global ledger, ever.** The Ethereum test (STORIES doctrine)
  explicitly excludes global consensus — it would surveil the very
  worlds this protects. Sync is pairwise/coalitional, and the "chain" is
  whatever set of events a given coalition has merged. There is no
  everyone-sees-everything layer, by construction.

## Stateful judgment agents over private data

The hardest comfort question: an agent that runs continuously over my
data, keeps a MODEL of me, and acts on it (the guardian at the bell; the
gardener across sweeps). What keeps a persistent, learning, third-party
agent survivable?

1. **The model is a bounded latent, custody-escrowed.** The agent's
   accumulated model of you is a `CoalitionalDerivative` with
   `latentCustody: escrowed_full_latent` (coalition.ts): it exists, it
   is rich, and it never exports — LICENSING.md rights 1-2 (execution +
   silo-local annotation), never right 6 (model-improvement) without a
   priced, admission-tested grant. Continuous learning is fine *inside*;
   the confinement invariant (Widening.lean) says it cannot silently
   widen.
2. **State lives as ledgered events, not hidden RAM.** A stateful agent's
   memory is a stream of typed judgements in the chamber's court — every
   time it "updates its model," that is metered in-chamber work
   (`SelfFree`: intra-silo, free) whose OUTPUTS, if they cross, are
   ordinary charged emissions. The agent has no private side-state that
   escapes the fold; its whole biography is auditable.
3. **The cumulative exposure account is the intimacy meter.** A
   long-lived agent's `(source → vendor)` lifetime account is the running
   total of everything it has ever been permitted to see — the number
   that answers "how deep is this relationship." It only grows; it is
   the honest price of a persistent agent, and it is public arithmetic.
4. **Fiduciary structure is fold-legible.** The guardian story's move:
   an agent's INCOME may be constrained to flow only from the principal's
   side, and since every fee is a ledgered flow, "whose agent is it" is a
   query over the settlement fold (G9 → fiduciary legibility). A
   persistent agent over your data is trustworthy when its incentives are
   checkable, not when it promises alignment.
5. **Leaving is defined.** Vendor switch = G7 export: the accounts and
   their cumulative history survive the divorce; the escrowed latent is
   destroyed by custodian attestation (declared, R2/R3-checkable). You
   can end the relationship and the ledger proves the model died.

## What this buys, stated as the comfort ladder

| you are comfortable letting an agent work over... | when the run is at least... | because the TCB is... |
| --- | --- | --- |
| your own data | R1 (operator = you) | you |
| a trusted vendor's data, low stakes | R1 + fiduciary legibility | the vendor, checkably incentivized |
| a stranger's data, or high stakes | R2 | a re-runnable deterministic build |
| a mutually-distrusting counterparty's data | R3 | audited silicon, operator removed |

We are at R1 and honest about it. The accounting ladder (ASSURANCE.md) is
at L4 (Lean-proven core). The gap between "the math is done" and "people
get comfortable at scale" is precisely R1→R3: a deterministic runner and
an attestation-gated key-release service. Neither needs new theory; both
are named machines on the endpoint register (MACHINES.md). That is the
good news — the hard part (what may cross, priced and proven) is behind
us; the remaining part (where it runs, attested) is engineering with a
clear spec.
