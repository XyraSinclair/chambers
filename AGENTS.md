# Agent Operating Contract

Chambers is a court file, not a notebook. Changes must leave a stranger able
to locate the governing law, reproduce the decision, trace substantive imports
to primary sources, and distinguish what is proved from what is merely
demonstrated.

## First read

1. Run `python3 -m chambers.landscape show`.
2. Read the relevant entry in `docs/SPECS.md`.
3. Read the normative spec named there, then its committed corpus and tests.
4. Read the applicable refusals in `docs/BOOK.md`.
5. For cross-cutting work, read `docs/primitives/CANON.md` and
   `docs/ASSURANCE.md` before touching code.
6. When importing or invoking external machinery, read
   `docs/LITERATURE.md` and update `LITERATURE.json` rather than adding an
   unbounded name-drop to prose.

`LANDSCAPE.json` is the topology index. It is not a second normative spec.
`docs/SPECS.md` remains the registry of live identifiers; `docs/MACHINES.md`
remains the register of runnable claims. `LITERATURE.json` is the
primary-source provenance registry; it is not permission to inherit a cited
paper's theorem or assumptions.

## Authority order

When two surfaces appear to disagree, use this order:

1. A named release tag and its frozen golden bytes define a conformance claim.
2. The live identifier's normative spec defines the intended decision.
3. Golden traces, tests, and proof replay are executable evidence.
4. Reference implementations and demos are evidence, not permission to amend a
   spec silently.
5. Explanatory prose yields to the surfaces above.

The refusal register travels with every implementation. Passing a corpus never
licenses a stronger privacy, identity, coverage, confidentiality, or harm
claim than canon makes.

## Semantic changes

A change is semantic when a conforming counterparty could emit different bytes,
a different decision, a different finding code, a different balance, or a
different proof obligation for the same input.

For a semantic change:

- mint a new versioned identifier; never reuse a frozen identifier;
- update `docs/SPECS.md` and the normative spec;
- add or replace the relevant golden corpus;
- update every claimed independent implementation;
- update Lean when the changed law lies inside the proved algebra;
- preserve an explicit migration story for old artifacts;
- state newly introduced refusals or residues.

A refactor that claims to be non-semantic must leave committed corpora
byte-identical and the full verification matrix green.

## Protocol invariants

Preserve these unless a new spec version explicitly changes them:

- decision paths use exact integers; estimation may use floats only outside the
  counterparty-compilable boundary;
- event identity is content-addressed and folds are total;
- malformed or adversarial facts convict or refuse; they do not turn the
  verifier into an exception oracle;
- merge is grow-only union and verdicts escalate rather than retract;
- settlement reads charge facts; the charge layer never depends on value;
- leakage is reader-relative and cumulative;
- a ceiling bounds the ledgered channel, not downstream harm;
- no boolean may launder an unsolved privacy or identity problem into
  `private = true`;
- deterministic machines do not consult wall time, ambient randomness, or
  undeclared network state.

## Repository shape

Every top-level `chambers/` component, every `docs/` root entry, and every Rust
crate must appear in `LANDSCAPE.json`. Entry points name a real target; evidence
paths must exist. Every substantive literature import must appear in
`LITERATURE.json`, name real repository targets, and reproduce
`docs/LITERATURE.md` exactly. Run:

```text
python3 -m chambers.landscape check
python3 -m chambers.landscape hotspots
python3 -m chambers.literature check
python3 -m chambers.literature show
```

Production Python has a 50,000-byte default ceiling. Three inherited files are
grandfathered at their exact current sizes:

- `chambers/kernel/settlement.py`
- `chambers/intro_clearing/intro_clearing.py`
- `chambers/intro_clearing/run_clearing.py`

Those ceilings are ratchets, not allowances. Do not add a byte without first
extracting a coherent module. When a file shrinks, tighten or remove its
exception in the same change. Keep protocol extraction separate from semantic
change so byte parity can adjudicate the move.

Do not casually rewrite the kernel's flat import boundary or public exports.
Several executable artifacts intentionally import the kernel as a local,
stdlib-only protocol package. An import-architecture migration deserves its own
mechanical, corpus-preserving change.

## Verification matrix

Run the smallest relevant lane while editing, then the whole matrix before
claiming completion:

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

The two Rust crates prove different things. The conformance crate is the
independent `egress-accountant/1` implementation; `rust_ledger` verifies the
ledger and settlement surfaces. Neither substitutes for the other.

## Evidence hygiene

- Freeze generated corpora; do not edit expected outputs by hand.
- A generator change and its corpus delta belong in the same commit.
- Name the exact identifier and trace in failures and findings.
- Keep private working records out of the public tree. Refer to intentionally
  withheld artifacts with the existing `private:` convention.
- Do not turn a demo's god-view, fixture knowledge, or mocked oracle into a
  protocol assumption.
- Use a primary source when one exists. Record a stable DOI, RFC, arXiv
  identifier, or official archival URL; name the exact import and its
  non-transfer boundary.
- Do not use citation as theorem inheritance, implementation equivalence, or a
  novelty claim.
- Do not describe R1/R2 reproducibility as R3 confidentiality or TEE
  attestation.
- Do not describe declared identity as Sybil resistance.
- Do not describe channel accounting as a proof that no secret or harm escaped.

## Definition of done

A change is complete when its governing identifier is unambiguous, its
topology is indexed, its intellectual imports are bounded and traceable, its
decision evidence is reproducible, all claimed twins agree, proof obligations
are current, and the prose says no more than the evidence.
