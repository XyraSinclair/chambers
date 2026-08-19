# IP Manifest

What this release gives, what it withholds, and why the give is safe.
Written before the release was polished; kept honest after.

## What this gives

Capabilities, not files:

- **A complete accounting substrate for confidential cognitive work.** The
  integer-only charge algebra (estimation outside the protocol, accounting
  in exact millibits), the grow-only convicting ledger, escrowed settlement
  bound to ledgered work, bonded contestable outcome attestations, and
  exact-integer Shapley attribution — with normative specs written for
  independent reimplementation.
- **The conformance method.** Golden-trace corpora plus a from-spec Rust
  twin agreeing bit-for-bit with the Python reference, and Lean-checked
  theorems over the algebra. This is the credibility device itself: anyone
  can now verify a meter instead of trusting one.
- **The theory.** Reader-relative leakage with the coalition as the zero
  point of the metric, the lifetime (source × reader) exposure ledger as a
  distillation budget, disclosure structure as audience × purpose ×
  alphabet under one-way widening, and the refusal register that keeps all
  of it honest. Plus the graded operations taxonomy and the feasibility
  floor for IP trades at model scale.
- **Working economies.** Deterministic, stdlib-only demonstrations — IP
  trading under a leakage meter, priced introductions, metered security
  research, peer prediction with metered redundancy — all running on the
  same kernel path a deployment would use.
- **The working chamber and its record.** The single-file demo chamber and
  its runbook (`chambers/chamber.py`, `chambers/CHAMBER.md`), the court-file
  and requester-bundle verifiers, the corpus confinement demo, the
  compliance kit, and the research record that produced the canon
  (`workbench/notes/`).

## What this withholds, and where the seam is

- **The business layer**: revenue mechanics, pricing, go-to-market, and the
  gap-audit roadmap. The seam is clean: nothing in this repo depends on
  them.
- **The live deployment**: the operator's running chamber — its deploy
  machinery, egress harness, and dogfood log. Cited here as "private" where
  canon leans on them; the findings they produced have landed in the specs.
- **The personal substrate**: runs against the operator's own private
  corpus, and every artifact derived from them.
- **The operating position**: calibration history, counterparty
  relationships, and the evidence trail of real trades. These accrue only
  by running trades and cannot be exported at all.

## Why the give is safe

The business thesis is "copyable code, uncopyable position": the value of a
neutral clearinghouse is being the party both rivals accept, the liquidity
map of who will trade what, and the calibration a meter earns by metering.
None of that is in a repository. Publishing the substrate strengthens the
position — "counterparty-compilable" is only true if counterparties can
compile it — at the cost of the one revenue rail that was always weakest
(selling the software itself).

## What a sharp competitor could build from this

A rival clearinghouse with a conformant meter, starting today. They would
begin at zero calibration, zero evidence history, and zero neutrality — and
their meter would be verifiable against the same public corpus ours is,
which is the ecosystem working as intended. The honest risk is framing
capture: a well-funded actor could adopt the vocabulary and ship
privacy-theater under it. The refusal register is the defense we chose —
[`docs/SPECS.md`](docs/SPECS.md) makes reproducing the register a condition
of conformance, so theater must either drop the conformance claim or
contradict the register in writing.
