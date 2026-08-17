# Contributing

Chambers accepts work that improves a specification, formal result,
conformance surface, executable implementation, or claim boundary.

Read [`AGENTS.md`](AGENTS.md) before changing protocol code.

## Change classes

**Documentary.** Clarifies a claim without changing observable protocol
behavior. New substantive literature imports update `LITERATURE.json`.

**Mechanical.** Reorganizes an implementation while preserving committed bytes,
decisions, findings, balances, and proof obligations.

**Semantic.** Changes observable behavior for an admitted input. It requires a
new versioned identifier, updated specification, new or migrated artifacts,
every claimed implementation, applicable Lean proofs, and a migration account.

Do not mix semantic work into a refactor.

## Formal contributions

A Lean contribution should state:

- the public claim it supports;
- the model boundary and assumptions;
- whether it reduces trusted code or establishes a new quantified property;
- the theorem's axiom dependencies;
- a checked counterexample or witness when a premise is load-bearing;
- the implementation-correspondence evidence, if any.

A theorem over a simplified model is welcome when the simplification is named.
It must not be presented as a proof of an implementation or deployment that has
not been related to the model.

## Literature contributions

Use primary sources whenever possible. Each `LITERATURE.json` entry records:

- a stable DOI, RFC, arXiv identifier, or official archival URL;
- the repository surfaces that use the source;
- one relationship: `foundation`, `adaptation`, `implementation`,
  `comparison`, or `open-frontier`;
- the mechanism actually imported;
- what the citation does not establish.

Then run:

```text
python3 -m chambers.literature format
python3 -m chambers.literature check
```

## Evidence in a pull request

Run every applicable lane:

```text
cd chambers/lean && lake build
cd ../conformance/rust && cargo test --locked
cd ../../kernel/rust_ledger && cargo test --locked
cd ../../..
python3 -m chambers.literature check
python3 -m pytest -q
```

For accountant conformance, also emit the Rust traces and check them through the
language-independent harness:

```text
cd chambers/conformance/rust
cargo run --locked -- --emit out
cd ../../..
python3 -m chambers.conformance.check_conformance \
  --actual chambers/conformance/rust/out
```

Never report a lane as green unless it ran against the proposed commit.

## Findings and security

Conformance divergences, corpus errors, and specification ambiguities should
name the exact identifier and trace. Security-sensitive reports follow
[`SECURITY.md`](SECURITY.md). Confirmed findings are credited unless the
reporter asks otherwise.
