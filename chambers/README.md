# chambers — the maintained system

Everything in this tree is maintained and claim-bearing: specifications,
proofs, frozen corpora, verifiers, and the demos named in the root README.
Exploratory material lives in [`../workbench/`](../workbench/) and never
crosses back — nothing here imports it.

| surface | contents |
|---|---|
| [`kernel/`](kernel/) | The executable protocol: ledger, audit, settlement, attribution, identity, scope, node — with normative specs and frozen trace corpora. |
| [`conformance/`](conformance/) | `egress-accountant/1`: language-independent spec, golden traces, and the from-spec Rust twin. |
| [`lean/`](lean/) | The formal model and theorem inventory; the intended semantic center. |
| [`runtime/`](runtime/) | `runtime-r2/1`: reproducible-local execution with content-addressed bundles. |
| [`review_audit/`](review_audit/) | `review-audit/1`: the frozen probe battery that audits judges. |
| [`chamber.py`](chamber.py), [`CHAMBER.md`](CHAMBER.md) | The single-file working chamber and its runbook — deliberately one file, distributed as a two-file zip. |
| [`check_court_file.py`](check_court_file.py), [`check_requester_bundle.py`](check_requester_bundle.py) | Offline verifiers, deliberately duplicated rather than shared: a verifier must not depend on the machinery it checks. |
| [`corpus_demo/`](corpus_demo/) | Guest confinement against a contract and sink schema. |
| [`compliance_kit/`](compliance_kit/) | The normative specs packaged with a hash manifest and checker. |
| [`literature.py`](literature.py) | Generator and checker for the research-lineage map (`LITERATURE.json`). |

The registry of identifiers is [`../docs/SPECS.md`](../docs/SPECS.md); the
reading order is [`../AGENTS.md`](../AGENTS.md).
