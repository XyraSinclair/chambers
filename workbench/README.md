# Workbench

The single non-normative region. Everything here is research material:
useful for integration evidence, counterexamples, and design pressure, and
authoritative for nothing. No file in this tree defines or amends a protocol
law; where workbench prose disagrees with a specification, a Lean theorem, or
a frozen corpus, the workbench is wrong.

## Scenario economies

Deterministic, stdlib-only economies that run on the maintained kernel — the
same `chambers.kernel` path a deployment would use. Each is a complete story
turned into ledger arithmetic, with its own tests.

| economy | run | scenario |
|---|---|---|
| [`intro_clearing/`](intro_clearing/) | `python3 -m workbench.intro_clearing.run_clearing` | Priced introductions: both consumer fee legs, attention before exposure, outcome escrow. |
| [`ip_trade_sim/`](ip_trade_sim/) | `python3 -m workbench.ip_trade_sim.run` | IP trading under a leakage meter: staged reveal, overlap verdicts, barter. |
| [`d1_bounty/`](d1_bounty/) | `python3 -m workbench.d1_bounty.run` | Metered security research: bounty lanes with an egress meter and an estimator probe. |
| [`peer_sim/`](peer_sim/) | `python3 -m workbench.peer_sim.run_peer_prediction` | Peer prediction with the mechanism's own redundancy metered openly. |
| [`cardinal_wedge/`](cardinal_wedge/) | `python3 -m workbench.cardinal_wedge.run_sort_metered` | A ranking of n private items priced as log₂(n!) ordering-mbits. |
| [`pipeline/`](pipeline/) | `python3 -m workbench.pipeline.run_pipeline` | The composed system: nine machines as one, over real files on disk. |

## Notes

[`notes/`](notes/) holds the written record: grounded scenario stories
([`notes/STORIES.md`](notes/STORIES.md), [`notes/stories/`](notes/stories/)),
open research under [`notes/frontier/`](notes/frontier/), the
adjacent-frameworks survey ([`notes/FRAMEWORKS.md`](notes/FRAMEWORKS.md)), and
the working record that produced the canon: dated autoresearch runs in
[`notes/autoresearch/`](notes/autoresearch/), the ideation series in
[`notes/ideation/`](notes/ideation/), and deep-read syntheses in
[`notes/research/`](notes/research/). The record is kept as it was written;
it is evidence of how the canon was reached, not a statement of what it is.

## Boundary

Workbench code may import `chambers.*`. Maintained code never imports
`workbench.*`. The direction is the point: deleting this entire tree must
leave every specification, proof, frozen corpus, and maintained test intact.

## Promotion

Work leaves the workbench the way anything enters canon: a versioned
identifier in [`docs/SPECS.md`](../docs/SPECS.md), a normative specification,
golden artifacts, and implementations bound to them. Until that happens, a
workbench result is an argument, not a claim.
