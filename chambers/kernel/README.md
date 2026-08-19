# kernel — the executable protocol

The Python reference implementation of the charge protocol, its normative
specifications, and the frozen trace corpora that bind them. The registry of
identifiers is [`../../docs/SPECS.md`](../../docs/SPECS.md); the runnable
machines built from these modules are listed in
[`../../docs/MACHINES.md`](../../docs/MACHINES.md).

## Specifications

[`KERNEL-SPEC.md`](KERNEL-SPEC.md) (charge-kernel/2, charge-substrate/1,
charge-provenance/1, charge-ledger/1) · [`SETTLEMENT-SPEC.md`](SETTLEMENT-SPEC.md)
(charge-settlement/1, /2) · [`VIEWS-SPEC.md`](VIEWS-SPEC.md) (charge-views/1) ·
[`SCOPE-SPEC.md`](SCOPE-SPEC.md) (charge-scope/1) ·
[`COVENANT-SPEC.md`](COVENANT-SPEC.md) (charge-covenant/1) ·
[`IDENTITY-SPEC.md`](IDENTITY-SPEC.md) (charge-identity/1, /2) ·
[`ATTRIBUTION-SPEC.md`](ATTRIBUTION-SPEC.md) (charge-attribution/1, /2) ·
[`PROTOCOL.md`](PROTOCOL.md) (the delta history from charge-kernel/1).

## Modules

- [`ledger.py`](ledger.py), [`events.py`](events.py), [`leases.py`](leases.py) —
  the grow-only convicting ledger: canonical bytes, content-addressed event
  identity, total folds.
- [`settlement.py`](settlement.py) — escrowed value bound to ledgered work;
  [`attribution.py`](attribution.py) — exact-integer Shapley splits;
  [`covenant.py`](covenant.py) — cease/cap covenants;
  [`identity.py`](identity.py) — Ed25519 key-bound authorship;
  [`scope.py`](scope.py) — reader-scoped views with Merkle proofs;
  [`views.py`](views.py) — policy-indexed interpretation.
- [`meter.py`](meter.py), [`accountant.py`](accountant.py),
  [`session.py`](session.py) — the charge path implementations share.
- [`node.py`](node.py), [`attention_node.py`](attention_node.py) — the served
  endpoints (chamber-node/1, attention-node/1).
- [`verify.py`](verify.py) — the stranger's verifier: both layers plus
  conservation, from bytes alone.
- `demo_*.py` — the runnable economies MACHINES.md indexes; `emit_*.py` — the
  declared generators for every frozen corpus.

## Frozen corpora

`ledger_traces/`, `settlement_traces/`, `settlement2_traces/`,
`attribution_traces/`, `views_traces/`, `lean_traces/` — golden artifacts,
regenerated only through their `emit_*` generator, moved only with a new
versioned identifier.

## The counterparty twin

[`rust_ledger/`](rust_ledger/) — a std-only Rust crate written from the specs
alone, agreeing bit-for-bit with this reference on every golden corpus it
claims. Same author, separate source: source isolation, not social
independence.
