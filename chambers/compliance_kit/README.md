# Scry Chambers Compliance Kit

Contract, verbatim:

> your implementation is conforming iff these bytes replay

Conformance means both:

1. The normative spec and corpus bytes match `MANIFEST.json` exactly.
2. Every corpus scenario replays to the expected verdict, and independent
   implementations have verdict parity on the same receipt bytes.

## Layout

In the repo, `chambers/compliance_kit/` contains only this README,
`MANIFEST.json`, and tooling. It does not duplicate frozen spec or corpus
bytes. Run `make_kit.py --dist <dir>` to assemble a distributable copy that
contains:

- `specs/`: normative specs copied from canonical in-repo sources.
- `corpora/`: frozen golden corpora copied from canonical in-repo sources.
- `verifier/python/`: the Python `charge-verify` implementation and its
  stdlib-only support modules.
- `verifier/rust_ledger/`: the Rust `charge-verify` crate sources.
- `check.py`: manifest and corpus replay runner.
- `MANIFEST.json`: sha256 and byte size for every normative spec, corpus file,
  and reference verifier source included in the distribution.

Fix canonical sources, not distribution copies. Distribution copies are
recreated and hash-checked by the assembler.

## Spec Versions

- `charge-ledger/1`: `KERNEL-SPEC.md`
- `charge-settlement/1` and `charge-settlement/2`: `SETTLEMENT-SPEC.md`
- `charge-scope/1`: `SCOPE-SPEC.md`
- `charge-covenant/1`: `COVENANT-SPEC.md`
- `charge-identity/1` and `charge-identity/2`: `IDENTITY-SPEC.md`
- `charge-attribution/1` and `charge-attribution/2`: `ATTRIBUTION-SPEC.md`
- `charge-views/1`: `VIEWS-SPEC.md`
- `charge-substrate/1`: `KERNEL-SPEC.md` Part II

Also packaged: `charge-provenance/1`, `charge-kernel/2`,
`egress-accountant/1`, and `review-audit/1`, because the verifier and corpus
contract depend on those normative surfaces.

## Verification Commands

From a distributable kit directory:

```sh
python3 check.py
python3 check.py --rust
PYTHONPATH=verifier/python python3 -m chambers.kernel.verify corpora/settlement2_traces/honest-outcome-flow.ledger.jsonl
cargo run --quiet --manifest-path verifier/rust_ledger/Cargo.toml --bin charge-verify -- corpora/ledger_traces/honest-single-node.ledger.jsonl
```

From this repository:

```sh
python3 chambers/compliance_kit/make_kit.py
python3 chambers/compliance_kit/check.py
python3 chambers/compliance_kit/make_kit.py --dist /tmp/scry-compliance-kit
```

`check.py --rust` is optional. If the Rust toolchain or crate cannot build in
the current sandbox, the Rust lane prints a skip reason and the default
Python compliance path remains authoritative.

## Expectation Discovery

`check.py` does not assume all corpora are clean.

- `ledger_traces`, `settlement_traces`, and `settlement2_traces` pair each
  `*.ledger.jsonl` artifact with a sibling `*.expected.json`. Expected verdict
  codes are read from `audit_codes`, `s_codes`, `x_codes`, `c_codes`,
  `p_codes`, `a_codes`, and `v_codes` when present. Empty code arrays plus an
  exact conservation pair expect verifier exit `0`; any expected code or
  broken conservation expects exit `1`.
- `views_traces` pair each `*.input.json` with a sibling `*.expected.json`.
  The expected bytes are the canonical `charge-views/1` report or refusal.
- `lean_traces/accountant_traces.json` embeds per-step `reasons` and final
  integer account state for each egress-accountant scenario.

## Change Process

The process that produced `/1`, `/2`, and `Part II` spec surfaces is the
Charge Improvement Process (CIP): an EIP-shaped discipline of versioned
normative specs, frozen golden corpora, reference and clean-room verifier
parity, and adversarial corpus additions before semantic changes are accepted.
