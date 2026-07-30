# Chambers

**Private worlds become partially computable without becoming public.**

Most of what matters is trapped behind privacy boundaries: who should meet,
who should hire whom, which two labs hold techniques the other would pay
for, what a decade of someone's notes actually says about them. None of it
can be safely broadcast, so almost none of it is computed on. The default
answer — upload everything and trust the platform — launders a lifetime of
context into someone else's model.

A chamber is the other answer: a computation confined to the private worlds
it has touched. Around it runs a market whose only tradable good is a
bounded computation right, whose only deliverable is one symbol from a
closed alphabet, whose price system is a lifetime exposure ledger, and
whose settlement instrument is a court file. Nobody buys bits; people buy
scoped rights and legible evidence.

This repository is that sentence made to run. (The specs' long name for
the system is *Scry Chambers*; Chambers is short.)

## What is here

- **The Book** — [`docs/BOOK.md`](docs/BOOK.md): the whole system as seven
  objects, twelve axioms, two theorems, and fourteen refusals, with a
  verified coverage map over every law in canon.
- **The type canon** — [`docs/primitives/`](docs/primitives/): fourteen
  TypeScript modules that decide what the prose merely argues. Leakage is
  reader-relative. Charges are integers. No boolean ever says "private".
- **The kernel** — [`chambers/kernel/`](chambers/kernel/): a running
  economy over the canon. Egress accounting in millibits, a content-addressed
  grow-only ledger that convicts rather than crashes, escrowed settlement
  released only against ledgered work, bonded contestable outcome
  attestations, exact-integer Shapley attribution. Every spec written so a
  counterparty can implement from the file alone.
- **The conformance surface** — [`chambers/conformance/`](chambers/conformance/):
  the language-independent decision core, plus golden traces. The Python
  reference and a Rust twin written from the spec alone
  ([`chambers/kernel/rust_ledger/`](chambers/kernel/rust_ledger/)) agree
  bit-for-bit — 195/195 decisions — because every float was exiled from the
  decision path. One author wrote both, with the reference sealed shut
  during the port; the first truly foreign twin is the standing invitation.
- **The proofs** — [`chambers/lean/`](chambers/lean/): machine-checked
  theorems over the charge algebra (ceiling law, global cap under lease
  partition, settlement conservation, widening one-way-ness), with golden
  traces from the reference's accountant core replayed inside Lean. The
  proofs cover the charge algebra, not the whole kernel.
- **The economies** — [`chambers/ip_trade_sim/`](chambers/ip_trade_sim/),
  [`chambers/intro_clearing/`](chambers/intro_clearing/),
  [`chambers/d1_bounty/`](chambers/d1_bounty/),
  [`chambers/peer_sim/`](chambers/peer_sim/),
  [`chambers/pipeline/`](chambers/pipeline/): two labs trading IP under a
  leakage meter, priced introductions, metered third-party security
  research, peer prediction with its redundancy metered openly, and nine
  machines composed into one system — all on the same accounting path,
  stdlib-only, deterministic.
- **The maps** — [`docs/OPERATIONS.md`](docs/OPERATIONS.md) (~80 operations
  graded on six axes), [`docs/ASSURANCE.md`](docs/ASSURANCE.md) (the six-rung
  ladder from types to priced social layer),
  [`docs/MACHINES.md`](docs/MACHINES.md) (one command per machine that
  runs), [`docs/SPECS.md`](docs/SPECS.md) (the registry of record: every
  spec identifier, its defining file, and what a conformance claim means),
  and the frontier papers under [`docs/frontier/`](docs/frontier/).

## Run something

```
python3 -m pytest -q                                  # the whole floor, ~365 tests
python3 -m chambers.kernel.demo_work_economy          # value moves iff metered work moved
python3 -m chambers.pipeline.run_pipeline             # nine machines as one system
python3 -m chambers.intro_clearing.run_clearing       # priced introductions, end to end
cd chambers/kernel/rust_ledger && cargo test          # the counterparty's verifier
cd chambers/lean && lake build                        # the proof kernel
```

Python ≥ 3.9 with `pytest` runs everything Python — the code itself is
stdlib-only. The Rust twin wants `cargo`; the proofs want `elan`, which
reads the pinned toolchain from `chambers/lean/lean-toolchain`.

## What this does not claim

No success-shaped privacy claims. The refusal register in
[`docs/BOOK.md`](docs/BOOK.md) is load-bearing: identity is Sybil-soft, the
meter prices channel width and never harm, the trusted core is ledgered
rather than eliminated, and where no alphabet closes the meter bounds the
ledger, not the adversary. A type may name an unsolved problem and record
an honest "unprovable"; it may never assert the problem away with a
boolean. Anything this substrate cannot compile from its court files, it
does not say.

## Status

The accounting layer runs and is cross-verified (two implementations, one
proof kernel, frozen golden corpora). The execution ladder is at R1–R2:
operator-observed and reproducible-local rungs are real; TEE attestation is
named, not built. What you are reading is a substrate and its evidence, not
a hosted product. The operator's own live deployment and its dogfood record
stay private; [`IP-MANIFEST.md`](IP-MANIFEST.md) states exactly what this
release gives and withholds.

## License

[The Harvest License](LICENSE.md). Use it, fork it, sell it. At most once a
year the steward may ask you one question — *what has this been worth to
you?* — and you answer honestly: money, work, releasing your own work this
way, or an honest zero. Every answer satisfies the license in full. Only
silence is a breach. The question arrives, if ever, through the channel
this repository names; no ask means nothing owed. Pass the work on and
the same single question is all that travels with it.

## Findings

Conformance divergences, spec ambiguities, and corpus errors: open an
issue naming the spec identifier ([`docs/SPECS.md`](docs/SPECS.md) is the
registry). Security reports: [`SECURITY.md`](SECURITY.md).

## Prior art, gratefully

Quantitative information flow and g-leakage (Alvim, Chatzikokolakis,
McIver, Morgan, Palamidessi, Smith); differential privacy and the
odometer/filter line; contextual integrity (Nissenbaum); Certificate
Transparency (RFC 6962/9162) and SUNDR fork consistency; peer prediction
and correlated agreement; Shapley data valuation; Ed25519 (RFC 8032);
Lean 4. The frontier papers in `docs/frontier/` cite the specific
literatures each law leans on.
