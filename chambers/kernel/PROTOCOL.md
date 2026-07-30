# charge-kernel/2 — the shared distributive protocol

**Status:** normative for the kernel; extends `../conformance/SPEC.md`
(`egress-accountant/1`), which remains the authority for the decision core.

One protocol for **incremental, third-party-designed cognitive work over
private data**, with information-leakage tracking that (a) is exact integer
arithmetic, (b) composes across repeated work, and (c) enforces a global
ceiling across many nodes without coordination at charge time. It is the L2
"running accountant" of `ASSURANCE.md`, built to be the single kernel under
`chamber.py` (private), `ip_trade_sim`, `d1_bounty`, and `intro_clearing`.

## The layers

```
  accountant.py   the decision core (SPEC §1-2), key-generic, + coupled charge
  events.py       content-addressed, grow-only ledger events (sha256 ids)
  ledger.py       CRDT merge (union by id) + total fold + audit I1–I8 + jsonl wire
  leases.py       ceiling partition — how a global cap holds across nodes
  session.py      MediationSession — hydrated, node-bound, atomic emission
  meter.py        KernelMeter — the single-node front-end (register → self-
                  lease → seq'd charge events); what the sims run on, so a
                  sim run and a distributed deployment produce the same
                  auditable artifact. There is one accounting path, not a
                  "lite" one for simulations.
```

Dependency direction is one-way and shallow: `{session, meter} → {leases,
ledger} → events → accountant`. `accountant.py` imports nothing from the
kernel.

Sibling documents: `KERNEL-SPEC.md` is the **normative, language-independent
spec of the distributive layer** (`charge-ledger/1`: canonical JSON, event
identity, jsonl wire format, fold, audit codes) with a golden corpus in
`ledger_traces/` and an independent from-spec Rust implementation in
`rust_ledger/`; `SETTLEMENT-SPEC.md` is the **value layer**
(`charge-settlement/1`: escrowed microcredits that release only against
work receipts — charge events by id — under a clean court; Part II,
`charge-settlement/2`: contingent OUTCOMES — bonded, independence-classed,
contestable `outcome_attestation` events gate release by hardened quorum,
bonds join the conservation identity, strictly better evidence slashes;
`settlement.py` implements both, `demo_work_economy.py` runs the
paid-judgement economy end to end, golden corpora live in
`settlement_traces/` (/1, frozen) and `settlement2_traces/` (/2), and
`verify.py` / `rust_ledger`'s `charge-verify` are the stranger's
one-command receipt verifiers); `SCOPE-SPEC.md` is the **scoped-serving
layer** (`charge-scope/1`: reader-scoped views with Merkle membership
proofs against a whole-court head, an append-only ingestion log with
consistency proofs — fork-consistent serving, unsigned heads named L5;
`scope.py` implements it, `node.py --scoped-only` serves it);
`COVENANT-SPEC.md` is the **exit layer** (`charge-covenant/1`: issuer
self-restrictions with content-addressed grandfathering; C-codes fail
closed for value; revocation = tenor + covenant + residue);
`../lean/` holds the L4 formal kernel
(the global cap theorem under any interleaving, the monotone-escalation
laws, and settlement conservation — available + escrowed + bonded —
proven).

## Delta from charge-kernel/1 (why /2 exists)

/1 had the right shape and six real holes, several in the **dishonest
direction** (leakage under-reported). /2 closes all six; each has a
regression test.

1. **Fact identity.** /1 event ids were pure content hashes, so two *real*
   charges with identical fields (a session restart replaying the same
   estimate at the same local tick) collided to one id and union-by-id
   silently dropped one — an undercount. /2 adds `charge_seq`, node-local and
   strictly monotone per lease: distinct facts get distinct ids by
   construction, and two events claiming one `(node, lease_id, charge_seq)`
   are an **equivocation** the audit flags (I8). `tick` is thereby freed to
   be a pure declared clock label in the issuer's domain.
2. **Honest resumption.** /1 gave a restarted node no way to recover its
   lease state, so the API itself walked an *honest* node into overspending
   its lease (and audit I3 then convicted the innocent). /2 sessions hydrate
   from the ledger (`Ledger.lease_usage`): cumulative, demand, the blocked
   latch, the incident latch, and the next `charge_seq`. Honest nodes cannot
   violate I3 across any number of restarts.
3. **Atomic emission.** /1 charged the k members of an emission one at a
   time, so a refusal at member j left members 1..j-1 debited for an emission
   that never happened — the court file stated leakage that never flowed, and
   repeated failed emissions griefed the requester's accounts. /2 adds
   `Accountant.charge_coupled`: SPEC step B (demand + incident latch) on
   every account — the attempt was real — then steps C/D as predicates over
   all accounts, then step E **all-or-none**. Guilty members keep their true
   SPEC reason (a ceiling refusal latches, per step D); solvent members
   refused only by the coupling report `REFUSED_COUPLED`, unchanged beyond
   demand. "The emission is not separable from its inputs" now holds in both
   directions: no partial emission, and no phantom debits from a refused one.
4. **Total fold.** In /1, one conflicting RegisterEvent made every auditor's
   `fold()` raise forever — a one-event denial-of-audit any node could mount.
   /2's fold is total: conflicting registrations resolve to the
   **conservative minimum** (entropy and ceiling), the account is marked
   `conflicted`, and audit reports I7. Both minima move severity
   monotonically under union — smaller entropy escalates class and incident,
   smaller ceiling creates findings — so quarantine preserves the honest
   direction: merge escalates, never retracts.
5. **Boundary validation.** SPEC §1.2 declares estimate components
   `int >= 0` and §5 assigns validation to the boundary; in the live kernel
   the kernel IS the boundary. /1 validated nothing: a negative component
   *credited* the meter (demand shrank, budget un-spent). /2 refuses negative
   (and bool) components at `CapacityEstimate` construction, and the fold
   ignores non-uint contributions from forged events (audited as I6).
6. **Authority edges.** /1 never checked that a charge's node is the leased
   node, that a charge's tick respects the lease's expiry, that a lease's
   issuer registered the key, or that an event's demand/debit are consistent
   with its reason class. /2 enforces node binding and expiry live in the
   session (honest refusal) and audits all four after merge (I4, I5, I6).

Event payloads changed (`charge_seq`); /1 and /2 ledgers do not gossip.
Nothing outside this directory ever emitted a /1 event.

## Why these five and not fewer

### The accountant is the SPEC, generalized in exactly one axis

`accountant.py` is `egress-accountant/1` with the account key widened from the
fixed `(subject, query_family, audience)` CompositionKey to **any string
tuple**. Two adapters:

- `composition_key(subject, query_family, audience)` — the original egress key.
- `exposure_key(source_chamber, reader_entity)` — the `coalition.ts`
  ExposureAccount key: **(source × reader), lifetime scope** — the one key the
  cross-coalition accumulation attack cannot slip past (see the trench).

Everything else is byte-identical semantics: admissibility, the A–E charge
steps, integer millibits, leakage classes, incident-on-uncapped-demand. This
is proven, not asserted: `test_kernel.py` replays all 31 golden traces and
matches `expected` field-for-field. Generalizing the key did not move a bit,
and neither did the /2 hardening.

`charge_coupled` is a **kernel-level extension**, not part of
egress-accountant/1: single-key `charge` remains the exact SPEC and never
produces `REFUSED_COUPLED`. The coupled operation composes SPEC transitions;
it does not alter them.

### The ledger is a CRDT so the system is distributive by construction

Every fact is an immutable event with a canonical-JSON sha256 id. **Merge is
set union by id** with a byte-equality conflict check — idempotent,
commutative, associative — so any gossip/replication order converges
(`test_merge_is_crdt`, `test_jsonl_roundtrip_and_gossip_convergence`). The
global account view is a deterministic **fold**: plain integer sums of
per-event monotone contributions (`demand_mbits`, `debit_mbits`). Merging can
only *escalate* leakage class, incident, and conflict status (all monotone),
never retract — the honest direction. The fold never re-decides; ChargeEvents
are final local decisions, and the fold is bookkeeping over facts.

The wire format is the ledger: `to_jsonl()` emits one canonical payload per
line sorted by event id — a byte-deterministic artifact — and `from_jsonl`
recomputes ids from content (derived, never trusted). Equal ledgers give
equal bytes; a tampered line becomes a different event and fails the audit's
referential checks.

### Leases make the ceiling hold across nodes — the load-bearing idea

Eventual consistency alone cannot bound a ceiling: two nodes spending the same
budget concurrently overspend it, and merge only reports the corpse. The
kernel answers with **partition, not consensus**. The key's owner — the source
chamber, *the party whose secret the ceiling protects*, so no external
coordinator is trusted — issues **leases** whose amounts never sum past the
ceiling (`leases.py` refuses to over-grant). A node accepts charges only
against a live lease **granted to it**, running an unmodified accountant whose
**local ceiling is the lease amount**.

**Global cap theorem** (the L4 Lean target, stated here for the reference):

```
  (1) Σ_leases amount ≤ ceiling                  [issuer refuses past it]
  (2) ∀ node: Σ accepted debits ≤ its lease      [accountant step D/E + hydration]
  ⟹  Σ_all accepted debits ≤ ceiling             under ANY interleaving,
                                                  zero coordination at charge time
```

Premise (2) is now true for honest nodes **across session restarts**, not
just within one process lifetime — that is what hydration buys, and it is
what makes the theorem's premise something an honest implementation actually
satisfies rather than something it merely intends.

`test_global_cap_holds_under_partition`: two nodes, 30 000 mbit lease each,
each *attempts* 40 000 — global accepted is 60 000 = ceiling, not 80 000.
`ledger.audit()` independently re-verifies I1–I8 over the merged event set and
catches: forged over-spends (I2/I3), spends against foreign leases (I4),
post-expiry charges (I4), leases from non-issuers (I5), malformed or
inconsistent facts (I6), registration poison (I7), and equivocation (I8).
Byzantine nodes are *detected after the fact*, not prevented — an honest,
named limit.

### The session charges both sides of the mediation boundary

`MediationSession` is where the kernel meets `mediation.ts`. A guest agent is
admitted to an exact tuple of chambers to produce a StructureJudgement, and
two facts of the theory become two charge sites:

- **Observation.** Reading a member's silo is exposure of that member to the
  agent-as-reader: each read debits `exposure_key(member, agent)`. A read
  past the member's exposure lease is refused — the agent simply cannot see
  that much.
- **Emission.** The judgement toward the requester debits the
  **requester-as-reader** (the requester is not a privileged sink) against
  **every** member of the tuple — atomically. A single judgment carries
  information about all of them, so it must clear all of their accounts;
  demand accrues on all either way, but debits land all-or-none
  (`test_mediation_session_charges_both_sides`,
  `test_atomic_emission_no_partial_debit`).

The session's `court_file()` is just the fold restricted to the keys it
touched — a receipt a stranger recomputes after merging the ledger.

**Clock domain.** `tick` is a declared integer label in the lease issuer's
clock domain — the same domain as `expires_tick`, which is what makes the
expiry comparison meaningful. An honest session refuses to charge an expired
lease; a node that lies about ticks is exactly what audit I4 catches.

## What this protocol deliberately does NOT claim

- **Estimation stays out.** The float that turns `log2`/byte-ceilings into
  millibits lives in an attested estimator (SPEC §0, §3), never in the kernel.
  The kernel's agreement claim is about accounting, not estimation.
- **Byzantine prevention.** Leases + audit *detect* a lying node; they do not
  *prevent* one. Prevention needs signed leases + verified execution (TEE/MPC)
  — the TCB-minimization frontier (#6), unbuilt. In particular events are
  unsigned: `issuer`/`node` are claims the audit cross-checks for
  consistency, not identities it can authenticate.
- **Identity.** `exposure_key`'s reader is a beneficial entity; a Sybil reader
  fragments its account (frontier #1). The kernel makes the undercount
  *auditable* (one account per claimed identity), not impossible.
- **Lease liveness / utilization.** Unspent lease remainder is stranded until
  expiry — a safety-over-utilization tradeoff. Reclaim-before-expiry would
  need the issuer to prove the node's non-spend, which is consensus by
  another name; the kernel declines.
- **Wall-clock time.** `tick` is an integer label; ordering within a key is by
  `charge_seq`, not by real time.

## Design law: every obligation arrives safety-shaped

Adopted 2026-07-06 (FRAMEWORKS.md F4; Alpern–Schneider). Only SAFETY
properties are convictable from a finite event set; liveness ("the
issuer eventually releases") is not monitorable by ANY audit, ever. The
silent-holdup hole in charge-settlement/1 was a liveness law, and its
fix — declared expiry + permissionless `default_resolution` (S8) — is
the standard reduction of liveness to safety by deadline reification,
rediscovered by consult. Do not rediscover it again: **every future
protocol obligation must either be a safety property over the event set,
or carry its declared-deadline + permissionless-resolution reduction at
design time.** Checklist question for every new law: "if the obligated
party goes silent forever, which event convicts, and who may emit it?"

## Wiring plan (the extraction this replaces)

`ip_trade_sim/leakage.py` and `d1_bounty/egress.py` currently charge in float
and are annotated not-yet-compilable (ASSURANCE L1). The migration: replace
their bespoke meters with `kernel.Accountant` on `composition_key`, keep their
float `log2` in a local estimator that rounds to attested millibits, and emit
`ChargeEvent`s into a shared `Ledger`. `intro_clearing` gains a
`MediationSession` per candidate pair. When all four import the kernel, the
"one shared accountant" box of ASSURANCE L2 is checked, and the Lean rung (L4)
has exactly one algebra to prove.

## Tests

`python3 chambers/kernel/test_kernel.py` — 21 tests in three families:
31-trace conformance; distributive properties (CRDT merge, order-independent
fold, global cap under partition, jsonl round-trip + 3-shard gossip
convergence, the golden ledger corpus replaying bit-for-bit); and one
adversarial regression per hole closed in /2 (fact identity, honest
resumption, atomic emission, registration poison, node binding, lease
expiry, equivocation, negative-millibit injection at both the boundary and
the forged-event path), plus the meter's full-path/restart property and the
canonical audit-code surface.

`python3 chambers/kernel/test_fuzz_audit.py` — the L3 detector-
completeness lane: seeded random honest multi-node deployments must audit
clean (soundness, no false positives), and fourteen Byzantine mutation
classes must each be convicted with the expected I-code across seeds
(completeness), with every verdict invariant under shuffle-merge.

All green. No floating point in any decision path.
