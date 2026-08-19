# Maintainer contract

Chambers is specification-first research software. A change should make a
protocol law more precise, an implementation easier to check, or a claim
boundary harder to misunderstand.

## Read in this order

1. Find the identifier in `docs/SPECS.md`.
2. Read its normative specification.
3. Read the relevant Lean module when the surface is formalized.
4. Inspect the frozen corpus and every claimed implementation.
5. Read the applicable limits in `docs/BOOK.md` and `docs/ASSURANCE.md`.
6. Check `LITERATURE.json` before importing an external mechanism.

`LITERATURE.json` records intellectual provenance. It does not transfer a
paper's theorem, assumptions, novelty, or implementation assurance to this
repository.

## Sources of authority

The surfaces have different jobs:

1. A versioned normative specification states the intended protocol.
2. A released tag and its frozen artifacts fix a historical conformance claim.
3. Lean definitions and theorems establish only the formal claims encoded in
   `chambers/lean`.
4. Conformance corpora bind implementations to concrete decisions and bytes.
5. Implementations and demos provide executable evidence; they do not silently
   amend a specification.
6. Explanatory prose yields to all of the above.

A disagreement among these surfaces is a defect to resolve explicitly. Do not
choose the convenient answer and preserve the old identifier.

## Semantic changes

A change is semantic when the same admitted input can produce different bytes,
a different decision, a different finding, a different balance, or a different
proof obligation.

A semantic change requires:

- a new versioned identifier;
- an updated normative specification;
- new or intentionally migrated golden artifacts;
- updates to every claimed implementation;
- updated Lean definitions and proofs when the law is formalized;
- a migration account for old artifacts;
- explicit new limits or refusals.

A mechanical refactor must preserve committed artifacts byte-for-byte. Keep
mechanical extraction separate from semantic work.

## Formal direction

Lean should own core laws whenever the state and decision surface are tractable.
Do not add Python-specific conventions to a protocol surface merely because the
prototype is convenient.

The current `GoldenTraces.lean` battery is finite model-code correspondence
evidence generated from the Python accountant. It is not an all-input
refinement proof and must not be described as one. The intended next direction
is a Lean-generated accountant oracle consumed by executable implementations.

A new theorem is useful when it reduces trusted code, proves a genuinely
quantified property, or supports a compact certificate. Translating broad
integration code into Lean without changing the assurance boundary is not a
goal.

## Protocol invariants

Preserve these unless a new specification version changes them:

- decision paths use exact integers;
- estimation floats remain outside the counterparty-compilable decision core;
- event identity is content-addressed and folds are total;
- malformed facts refuse or produce named findings rather than crashing a
  verifier;
- merge is grow-only union;
- settlement reads charge evidence, while the charge layer does not depend on
  value;
- leakage is indexed by source and reader;
- a ceiling bounds a modeled channel, not downstream harm;
- signatures establish possession of a key, not unique human identity;
- deterministic machines do not consult undeclared time, randomness, or network
  state.

## Literature standard

Use a primary source when one exists. A substantive import adds a
`LITERATURE.json` record with a stable locator, exact repository targets,
declared relationship, concrete imported mechanism, and a boundary stating what
the citation does not establish.

Run:

```text
python3 -m chambers.literature format
python3 -m chambers.literature check
```

## Verification

Run the smallest relevant lane while editing, then every applicable lane before
claiming completion:

```text
cd chambers/lean
lake build
cd ../..

cd chambers/conformance/rust
cargo test --locked
cargo run --locked -- --emit out
cd ../../..
python3 -m chambers.conformance.check_conformance \
  --actual chambers/conformance/rust/out

cd chambers/kernel/rust_ledger
cargo test --locked
cd ../../..

python3 -m chambers.literature check
python3 -m pytest -q
```

The two Rust crates cover different surfaces and were written by the same
author. They provide source isolation and cross-language agreement, not social
independence.

## Evidence hygiene

- Generate frozen artifacts through their declared generator.
- Put a generator change and its artifact delta in the same commit.
- Name the exact identifier and trace in a finding.
- Keep the operator's private records (live deployment, dogfood log,
  personal-corpus runs) outside the public tree; the research record under
  `docs/autoresearch/`, `docs/ideation/`, and `docs/research/` is public by
  operator decision.
- Do not turn fixture knowledge or a demo's global view into a protocol
  assumption.
- Do not describe reproducibility as confidentiality or attestation.
- Do not describe channel accounting as proof that no secret or harm escaped.
- Record a sharp counterexample when a theorem relies on a non-obvious gate.

## Completion

A change is complete when its governing identifier is unambiguous, its formal
and executable evidence agree at the claimed boundary, relevant literature is
traceable, applicable verification lanes are green, and the prose makes no
stronger claim than the evidence.
