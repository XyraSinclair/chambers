# Formalization program

More Lean is useful when it changes the trusted boundary, proves a property
that testing cannot quantify over, or turns a result into a compact certificate.
Translating implementation code line by line is not the objective.

The current formal kernel is already substantial. The next work should be
selected by the claim it unlocks.

## 1. Make Lean the accountant oracle

**Present gap.** `GoldenTraces.lean` replays a finite scenario battery emitted
by the Python accountant. This is useful correspondence evidence, but it leaves
the implementation upstream of the formal artifact.

**Target.** Define the canonical scenario and serialization layer in Lean and
emit the accountant conformance corpus from a Lean executable. Rust and Python
then consume the same Lean-produced decisions.

**Completion criterion.**

- the Lean oracle is deterministic and byte-stable;
- every committed accountant trace is emitted by it;
- Rust and Python agree with the emitted corpus;
- the existing step and run theorems apply directly to the oracle semantics;
- no Python output is needed to state or regenerate the formal decision law.

This is the highest-leverage near-term change because it changes the direction
of authority without requiring the entire system to be reimplemented in Lean.

## 2. Return proof-carrying verdicts

Audits currently return finding codes and referents. The stronger interface is a
finding plus a minimal witness that a small checker can validate.

For each audit family, define:

```text
evidence -> verdict × certificate
certificate -> checkable proposition
```

The producer may remain an optimized Rust or Python program. Trust moves to the
certificate checker and its soundness theorem.

Start with findings that already have Lean soundness/completeness results:
equivocation, over-disbursement, malformed settlement parties, dangling
references, and provenance-chain violations. A useful certificate should name
only the events required for the conviction, not replay the entire court.

This follows the proof-carrying-code and certifying-algorithm pattern: expensive
search may be untrusted when the result carries a cheap, independently
checkable witness.

## 3. Verify the byte boundary

The most consequential unformalized transition is not another arithmetic
identity. It is:

```text
bytes -> parsed event -> canonical bytes -> content identifier
```

A narrow verified codec should establish:

- decoding is total and malformed inputs produce named refusals;
- encoding followed by decoding is identity on valid events;
- decoding followed by encoding produces the unique canonical form;
- content identifiers are computed over domain-separated canonical bytes;
- two accepted byte strings cannot denote the same event with different
  protocol meaning.

Do this for the smallest protocol-critical event subset first. The result can be
used by the Rust verifier without formalizing the surrounding HTTP or storage
stack.

## 4. Prove implementation refinement

Golden corpora detect disagreement on chosen inputs. Refinement proves agreement
for all inputs admitted by the model.

The first tractable target is the egress accountant:

```text
Rust state + input
    refines
Lean Account + Charge
```

A hand-written forward simulation is acceptable if the state relation is small
and explicit. Functional translation of the Rust core is another route, with
Aeneas as the most relevant current experiment. The proof should cover refusal
reasons and post-state, not only cumulative totals.

Do not begin with the full node or settlement stack. The accountant has exact
integers, a small state, and a closed decision alphabet; it is the right
correspondence wedge.

## 5. Add a hyperproperty layer

Most existing theorems concern one trace or one merged event set. Privacy and
noninterference are relational: they compare executions that differ in secret
inputs.

For finite, closed-output mechanisms, formalize:

- observational equivalence for a declared reader;
- transcript cardinality and an induced capacity bound;
- sequential and parallel composition of those bounds;
- refinement: replacing a mechanism with a less informative one cannot increase
  charge;
- a countermodel showing why unmodeled channels receive no guarantee.

This is where the quantitative-information-flow lineage should become theorem
statements rather than motivation. The first target should be deterministic
finite mechanisms; randomized mechanisms and Rényi accounting belong in a
larger theory layer.

## 6. Complete the audit matrix

Every audit code should eventually have four entries:

| Obligation | Question |
|---|---|
| Soundness | Does every emitted finding name a real violation? |
| Completeness | Does every modeled violation produce a finding? |
| Merge behavior | Is the finding permanent, or exactly what fact can clear it? |
| Sharpness | Which removed gate yields a checked counterexample? |

The current Lean modules establish this pattern for selected settlement,
equivocation, provenance, and value-gate findings. Extend it systematically to
the remaining S-, P-, and V-family obligations rather than accumulating isolated
lemmas.

A generated matrix should link each code to its spec clause, Lean theorem,
counterexample, corpus scenario, and open residue.

## 7. Prove composition and version refinement

Chambers is intended to compose across readers, sources, nodes, and protocol
versions. Formal work should cover:

- overlapping lease partitions rather than only disjoint grants;
- composition of chamber computations with shared readers;
- preservation of caps under federation and partial replication;
- refinement between protocol versions;
- migration functions that preserve old artifact meaning;
- conditions under which two independently clean courts compose to a clean
  joint court.

This is where local laws become a substrate rather than a collection of
machines.

## 8. Split kernel from theory

Keep `ChargeKernel` small, fast, and conservative: exact decision semantics,
finite witnesses, conservation, monotonicity, and correspondence.

Create a separate `ChargeTheory` package when the work genuinely needs mathlib:
entropy, submodularity, stochastic mechanisms, cooperative-game identities,
mechanism design, or asymptotic bounds. The kernel should not acquire a larger
trusted and dependency surface merely to make exploratory mathematics
convenient.

## Evidence discipline

Every formal tranche should ship with:

- a theorem whose quantifiers match the public claim;
- an executable witness or negative model showing why a load-bearing premise is
  necessary;
- an axiom report;
- an explicit model-to-code correspondence statement;
- a claim boundary;
- a `LITERATURE.json` entry for each substantive imported mechanism;
- a frozen artifact that a second implementation can consume where applicable.

## Literature additions for these tranches

The corresponding work should add the following primary sources to the
literature registry when it begins:

- George C. Necula, *Proof-Carrying Code*, DOI
  `10.1145/263699.263712`;
- Kurt Mehlhorn et al., *Certifying Algorithms*, DOI
  `10.1016/j.cosrev.2010.09.009`;
- Michael R. Clarkson and Fred B. Schneider, *Hyperproperties*, DOI
  `10.3233/JCS-2009-0393`;
- Xavier Leroy, *Formal Verification of a Realistic Compiler*, DOI
  `10.1145/1538788.1538814`;
- Son Ho and Jonathan Protzenko, *Aeneas: Rust Verification by Functional
  Translation*, DOI `10.1145/3547647`;
- the IronFleet and Verdi primary papers for end-to-end refinement of
  distributed systems.

These references supply methods and comparison points. They do not establish
that Chambers has completed the corresponding proof.
