# Contributing

Chambers is specification-first software. A useful contribution makes the
governing law easier to locate, the decision easier to reproduce, or the
boundary of a claim harder to misunderstand.

Read [`AGENTS.md`](AGENTS.md) before changing code. It is the complete operating
contract; this file is the public entry point.

## Choose the change class

### Documentary

A documentary change clarifies a claim without changing protocol behavior.
It must preserve the distinction among normative specifications, executable
evidence, demonstrations, and private working records. New literature claims
also update `LITERATURE.json`.

### Mechanical

A mechanical change reorganizes an implementation without changing the bytes,
decisions, findings, balances, or proof obligations a conforming counterparty
observes. Committed corpora remain byte-identical, and every claimed
implementation stays green.

### Semantic

A semantic change can alter observable protocol behavior for the same input.
It requires a new versioned identifier, an updated normative specification,
new golden evidence, all claimed independent implementations, applicable Lean
proofs, a migration story, and explicit new refusals or residue.

Do not mix semantic work into a refactor.

## Literature standard

Use primary sources whenever a primary source exists. Every substantive import
must enter [`LITERATURE.json`](LITERATURE.json) with:

- a stable DOI, RFC, arXiv identifier, or official archival URL;
- the exact repository surfaces that rely on it;
- one declared relationship: `foundation`, `adaptation`, `implementation`,
  `comparison`, or `open-frontier`;
- a concrete statement of what Chambers imports; and
- a boundary stating what the citation does not prove.

Then run:

```text
python3 -m chambers.literature format
python3 -m chambers.literature check
```

A citation is not theorem inheritance, implementation equivalence, or a
novelty claim.

## Evidence expected in a pull request

Run the smallest relevant lane while editing. Before completion, run:

```text
python3 -m chambers.landscape check
python3 -m chambers.literature check
python3 -m pytest -q

cd chambers/conformance/rust
cargo test --locked
cargo run --locked -- --emit out
cd ../../..
python3 -m chambers.conformance.check_conformance \
  --actual chambers/conformance/rust/out

cd chambers/kernel/rust_ledger
cargo test --locked
cd ../../..

cd chambers/lean
lake build
```

A focused documentary contribution may mark an inapplicable Rust or Lean lane
as such, with a reason. Never report a lane as green unless it ran against the
proposed commit.

## Findings and security

Conformance divergences, corpus errors, and specification ambiguities should
name the exact identifier and trace. Security-sensitive reports follow
[`SECURITY.md`](SECURITY.md).

Confirmed findings are credited unless the reporter asks otherwise.
