# SPECS — the registry of record

Every normative surface in this repository carries a versioned
identifier (`charge-kernel/2`, `egress-accountant/1`). This file is the
registry: which identifiers are live, where each is defined, and what a
claim of conformance against one means.

## Live identifiers

| Identifier | Defined in |
|---|---|
| `charge-kernel/2` | [`chambers/kernel/KERNEL-SPEC.md`](../chambers/kernel/KERNEL-SPEC.md) Part I (the delta from `/1` is documented in [`chambers/kernel/PROTOCOL.md`](../chambers/kernel/PROTOCOL.md)) |
| `charge-substrate/1` | [`chambers/kernel/KERNEL-SPEC.md`](../chambers/kernel/KERNEL-SPEC.md) Part II — the X0 law |
| `charge-provenance/1` | [`chambers/kernel/KERNEL-SPEC.md`](../chambers/kernel/KERNEL-SPEC.md) Part III — closure charging |
| `charge-ledger/1` | [`chambers/kernel/KERNEL-SPEC.md`](../chambers/kernel/KERNEL-SPEC.md) — the grow-only ledger layer |
| `charge-views/1` | [`chambers/kernel/VIEWS-SPEC.md`](../chambers/kernel/VIEWS-SPEC.md) |
| `charge-settlement/1`, `charge-settlement/2` | [`chambers/kernel/SETTLEMENT-SPEC.md`](../chambers/kernel/SETTLEMENT-SPEC.md) |
| `charge-scope/1` | [`chambers/kernel/SCOPE-SPEC.md`](../chambers/kernel/SCOPE-SPEC.md) |
| `charge-covenant/1` | [`chambers/kernel/COVENANT-SPEC.md`](../chambers/kernel/COVENANT-SPEC.md) |
| `charge-identity/1`, `charge-identity/2` | [`chambers/kernel/IDENTITY-SPEC.md`](../chambers/kernel/IDENTITY-SPEC.md) (`/2` is §7, the authoring front-ends) |
| `charge-attribution/1`, `charge-attribution/2` | [`chambers/kernel/ATTRIBUTION-SPEC.md`](../chambers/kernel/ATTRIBUTION-SPEC.md) Parts I and II |
| `egress-accountant/1` | [`chambers/conformance/SPEC.md`](../chambers/conformance/SPEC.md) |
| `chamber-node/1` | [`chambers/kernel/node.py`](../chambers/kernel/node.py) module header; endpoint entry in [`MACHINES.md`](MACHINES.md) |
| `attention-node/1` | [`chambers/kernel/attention_node.py`](../chambers/kernel/attention_node.py) module header |
| `review-audit/1` | [`chambers/review_audit/PROBE-SPEC.md`](../chambers/review_audit/PROBE-SPEC.md) |
| `runtime-r2/1` | [`chambers/runtime/RUNNER-SPEC.md`](../chambers/runtime/RUNNER-SPEC.md) |

Named but not live: `charge-kernel/1` (the superseded predecessor),
`charge-ledger/2+`, `charge-settlement/3`, `charge-views/2`, and
`egress-accountant/2` — version bumps reserved in prose where a future
obligation is queued. No document defines them; nothing may claim
conformance to them.

## The freeze rule

The corpus of record is the content of this repository at a release
tag. The tag `v0.1.0` freezes every live identifier above at the spec
text and golden trace corpora present in that tag. A spec that changes
gets a new version suffix and new corpora; identifiers are never reused
and never silently edited under a frozen tag.

## What a conformance claim means

An implementation may claim conformance to an identifier only if it
reproduces that identifier's golden corpora bit-for-bit at a named
release tag. Two limits are part of the claim's meaning:

- **Trace-passing verifies meter arithmetic, never deployment
  coverage.** A conformant meter says nothing about whether a
  deployment routes every crossing through it. "Runs a conformant
  meter" and "meters everything" are different claims; only the first
  is testable here.
- **The refusal register travels with the spec.** A conformant
  implementation reproduces the refusals in [`BOOK.md`](BOOK.md) as
  stated. An implementation that asserts what canon refuses to assert
  is nonconformant regardless of its trace results.

## Coverage and the court, stated exactly

Two facts a reader should not have to assemble from fragments:

**Per-family implementation coverage.** The verdict families and where
each executes today: I, S1–S10, A, and W in both Python and the Rust
twin; S11/S12, X0, C, P, and V in Python only. The Rust `charge-verify`
re-verifies I, S1–S10, A, and the conservation identity. A cross-language
conformance claim extends exactly this far and no further.

**The court is defined differently by surface.** The full verifier
(`chambers/kernel/verify.py`) verdicts on all seven information/value
families. `chamber-node/1`'s `/v1/audit` joins I/X/C/P. The S4 value
gate (`settlement.py`'s `_court_findings`) joins I/C/P/V. The Rust
twin's S4 gate joins I only. The Python and Rust S4 courts therefore
diverge on any ledger holding covenant, derivation, or attribution
facts near a `required_clean` escrow — latent today only because the
frozen corpora carry none of those kinds. Under this file's own rule
that Python/Rust divergence is release-critical, this is the named
open debt. The Python-side roster now lives in one place —
`chambers/kernel/findings.py`, a registry (per family: code prefix,
defining identifier, coverage, court and audit membership, and the
recorded reason for every exclusion) that the verifier, the node's
`/v1/audit`, and the S4 gate all consume — so the divergence is data,
not scattered code. Reconciling the memberships themselves (and the
Rust twin's court) remains the queued versioned spec change with
migrated corpora. Until it lands, do not rely on S4 gating of
covenant/provenance/attribution dirt agreeing across implementations.

## Findings

Divergences between conformant implementations, ambiguities two careful
readers resolved differently, and corpus errors: open an issue on this
repository naming the identifier and the trace. Divergence between this
repository's own Python and Rust implementations is a release-critical
bug.
