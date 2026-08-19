# Documentation

The documentation has three roles: define the protocol, state what is proved,
and identify what remains open. Start with the shortest document that answers
your question.

## Core reading

| Document | Purpose |
|---|---|
| [`BOOK.md`](BOOK.md) | Compact account of the system's objects, axioms, theorems, and explicit refusals. |
| [`primitives/CANON.md`](primitives/CANON.md) | Typed vocabulary and admission rule for new primitives. |
| [`SPECS.md`](SPECS.md) | Registry of versioned protocol identifiers and their defining files. |
| [`FORMALIZATION.md`](FORMALIZATION.md) | Prioritized program for moving semantic authority and verification into Lean. |
| [`ASSURANCE.md`](ASSURANCE.md) | Evidence ladder from types and conformance through proof and deployment. |
| [`LITERATURE.md`](LITERATURE.md) | Generated map from primary sources to exact repository claims and boundaries. |

The machine-readable source for the literature map is
[`../LITERATURE.json`](../LITERATURE.json).

## Execution and operations

- [`MACHINES.md`](MACHINES.md) lists runnable machines and one command for each.
- [`RUNTIME.md`](RUNTIME.md) describes the execution ladder and where plaintext
  appears.
- [`OPERATIONS.md`](OPERATIONS.md) grades candidate operations against the
  system's exposure and assurance dimensions.
- [`LICENSING.md`](LICENSING.md) separates the rights involved in access,
  computation, derivative use, and model improvement.

## Human and economic cases

- [`STORIES.md`](STORIES.md) and [`stories/`](stories/) contain grounded
  scenarios and adversarial reviews.
- [`frontier/`](frontier/) contains open work on coalitional inference, IP
  trades, private-data moats, leakage measurement, and judgement markets.
- [`FRAMEWORKS.md`](FRAMEWORKS.md) surveys adjacent formal machinery that may be
  useful but is not necessarily implemented.

## The research record

The record that produced this canon is in the repository: the autoresearch
runs in [`autoresearch/`](autoresearch/), the ideation series in
[`ideation/`](ideation/), and the deep-read syntheses in
[`research/`](research/).

A small residue stays with the operator: the live chamber deployment (deploy
machinery, egress harness, dogfood log) and runs over the operator's own
private corpus. Citations to that residue are marked as private. Protocol laws
and public findings must be represented in the specifications, proofs, tests,
or frozen artifacts included in this repository; a private record is never the
sole support for a public conformance claim.

## Working rule

A new abstraction should either remove an illegal state, support a stated
theorem, or close an identified implementation gap. Unsolved privacy, identity,
and social-assurance problems remain explicit rather than being compressed into
a boolean or an optimistic label.
