# The Docs

Type substrates for confidential cognitive work: **private worlds become
partially computable without becoming public.** Owners admit bounded agents
into typed environments; agents produce owner-private structure; work is
reviewed, priced, paid, and released only as minimized projections; every
crossing, side channel, attention debit, and settlement is ledgered.

## If you read one thing

Read **[`primitives/CANON.md`](primitives/CANON.md)**. It is the map of the
whole type system in one screen: the modules, the laws each enforces, the
admission test for new primitives, and — at the bottom — the **open
frontier**, the problems deliberately *not* solved and never asserted away.

**"The whole system, minimally?"** → **[`BOOK.md`](BOOK.md)** — seven
objects, twelve axioms, two theorems, fourteen refusals; every canon law an
axiom, a one-line corollary, or a named refusal — with the full coverage
map as appendix.

## Reading order by intent

**"What is the type system?"**
→ [`primitives/CANON.md`](primitives/CANON.md), then the modules it maps:
`core.ts` (spine), `entropy.ts` (egress accounting), `runtime.ts`,
`environment.ts`, `attention.ts`, `market.ts`, `matching.ts`, `pricing.ts`,
`negotiation.ts`, `iptrade.ts`, `coalition.ts` (reader-relative leakage),
`mediation.ts` (tuple-scoped structure judgements), `calculus.ts` (the
composition laws), and `contexts.ts` (the disclosure grade).

**"How will we KNOW the stack is solved?"**
→ [`ASSURANCE.md`](ASSURANCE.md) — the six-rung assurance ladder (types →
conformance → running accountant → adversarial audit → Lean kernel →
priced social layer), the charge-algebra decision, and the build order.

**"What actually RUNS?"** → [`MACHINES.md`](MACHINES.md) — one command per
machine (node, economy demos, verifiers, proof kernel) and the endpoint gap
register for a real deployment.

**"How does it run over private data — VMs, encryption, stateful agents?"**
→ [`RUNTIME.md`](RUNTIME.md) — the execution ladder R1→R3
(operator-observed → reproducible → TEE-attested), and where plaintext
appears.

**"What operations can actually run, graded?"** → [`OPERATIONS.md`](OPERATIONS.md)
— ~80 operations located on six spine axes, comfort tiers derived from
coordinates rather than declared, and the 22-step IP-mediation protocol
walked tier by tier.

**"Where does the math touch people?"** → [`STORIES.md`](STORIES.md) (nine
grounded narratives + the gap register) and [`stories/`](stories/) (seven of
them at full ledger depth, a markets note, and two adversarial consult
reports).

**"What formal machinery exists that we are NOT using yet?"**
→ [`FRAMEWORKS.md`](FRAMEWORKS.md) — the import register: adjacent
literatures with real theorems, each priced against the law or gap of ours
it touches.

**"What does the substrate sell, economically?"**
→ [`LICENSING.md`](LICENSING.md) — licensed latent formation: the
six-right decomposition of "can this agent access my data?", with the
model-improvement right deliberately unbundled.

**"What is the deep frontier?"**
→ [`frontier/`](frontier/) — coalitional inference (reader-relative
leakage, the lifetime exposure ledger), IP trades (the feasibility floor at
model scale), generative private-data moats, g-leakage measurement, and
judgement markets.

## The research record

The record that produced this canon is in the book: the autoresearch runs
(a 207-agent stress test that retired three overclaims, the economy atlas
that killed 28 of 32 candidate domains) in [`autoresearch/`](autoresearch/),
the ideation series in [`ideation/`](ideation/), and the deep-read syntheses
in [`research/`](research/). The demo chamber and its runbook, the corpus
confinement demo, and the compliance kit live in `chambers/`.

A small residue still stays home: the operator's live chamber deployment
(its deploy machinery, egress harness, and dogfood log) and every run
artifact over the operator's own private corpus. Citations to that residue
are marked "private" where they occur; every protocol-grade finding it
produced has landed in the specs and tests that *are* here.

## Working rule

Boring primitives. Low residue. No success-shaped privacy claims — a type
may *name* an unsolved problem and record an honest "unprovable", never
assert it away with a boolean. New records pass the five-test admission
gate in [`primitives/CANON.md`](primitives/CANON.md) or they are a field, a
payload, or a future module — not a primitive.
