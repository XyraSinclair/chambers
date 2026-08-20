# charge_ledger

Independent second implementation of `charge-ledger/1`,
`charge-settlement/1`, `charge-settlement/2` (including the S11/S12
split extension), `charge-attribution/1+2`, and `charge-views/1`
in Rust.

This crate implements the ledger artifact parser, canonical JSON
serialization, event id recomputation, set-union merge, fold, audit verdict,
and canonical jsonl reserialization described by
`../KERNEL-SPEC.md`. Leakage class thresholds are from
`../../conformance/SPEC.md` section 1.5. The settlement value fold,
S-code audit, and conservation identity are implemented from
`../SETTLEMENT-SPEC.md`. The derived-views layer (`charge-views/1`:
policy admissibility, the view computation, W1/W2 all-or-nothing
refusals, canonical report bytes) is implemented from `../VIEWS-SPEC.md`
— `views_traces/` replays bit-for-bit, and the §V.5 parity law
(legacy-default view ≡ the fold's embedded `leakage_class`/`incident`)
is asserted against every frozen ledger fold from this side too.
The attribution layer (`charge-attribution/1+2`: exact-integer Shapley
over DPI max-flow, V1–V5, split-bound disbursement S11/S12) is
implemented from `../ATTRIBUTION-SPEC.md` — `attribution_traces/`
replays bit-for-bit.

## Independence discipline

This was implemented from the normative specs and the golden ledger artifacts.
The Python reference files were not opened or consulted during the port.
For the settlement port, this explicitly includes not opening or consulting
`settlement.py`, `verify.py`, `emit_settlement_traces.py`,
`emit_settlement2_traces.py`, `test_settlement*.py`, `node.py`, or any
other Python in `chambers/`. The golden corpora were used only as the
byte-for-byte conformance oracle.

Same-author honesty caveat: this implementation was written in the same
repository as the reference and therefore cannot prove social independence by
itself. It does provide a separately compiled, std-only implementation whose
behavior is forced by the public spec and golden artifacts.

## Ambiguities recorded

1. `KERNEL-SPEC.md` section 3.1 defines well-formed register using only
   `subject_entropy_mbits` and `ceiling_mbits`, then defines `issuers(key)` as
   issuer strings of well-formed registers. This implementation treats a
   non-string `issuer` on an otherwise well-formed register as absent from
   `issuers(key)`, not as making the register malformed.
2. `KERNEL-SPEC.md` section 4, I3 says charges whose `lease_id` resolves feed
   the overspend sum, while unresolved leases are skipped. This implementation
   skips I3 debit contribution only when `lease_id` matches no lease. Charges
   with key mismatch, node mismatch, or expiry I4 findings still count toward
   I3 sums when their lease resolves.
3. `SETTLEMENT-SPEC.md` marks malformed escrows S6 but does not explicitly
   say whether those escrows still enter the fold. The golden bytes force
   escrows with readable `amount_ucr`, `payer`, and `payee` to lock value and
   appear in `escrows` even when `charge_keys` is empty or
   `default_on_expiry` is invalid.
4. `SETTLEMENT-SPEC.md` says release/refund/default events with non-string
   `escrow_id` are S6, and S2 covers absent escrows. The golden bytes force a
   non-string `escrow_id` to be treated as unresolvable for S2, while still
   independently auditing the event's `charge_ids` for S3.
5. For outcome escrows, `SETTLEMENT-SPEC.md` makes
   `default_on_expiry != "refund_to_payer"` malformed. The golden bytes force
   such an escrow to remain fold-visible, and an explicit release against it
   still disburses value while receiving S9 because the outcome condition is
   unreadable.
6. `SETTLEMENT-SPEC.md` says every `outcome_attestation` has a bond state, but
   its S6 text could be read as excluding malformed attestations from value
   accounting. The golden bytes force an attestation with an invalid `claim`
   to still bond value when `bond_ucr` is uint and `attestor` is a string.
7. `SETTLEMENT-SPEC.md` section 7.4 chooses release-direction default
   resolution when the payload carries a non-empty `attestation_ids` list. The
   golden bytes force that direction decision to be syntactic: a non-empty list
   selects release even when the referenced proof is absent or invalid, and S8
   carries the proof failure.
8. `SETTLEMENT-SPEC.md` defines S10 for bond-resolution crimes, while S6 owns
   malformed `bond_resolution` shape. The golden bytes force an invalid
   `direction` to emit S6 only: it contributes to no bond sum and does not also
   emit S10.

## Suspected reference findings

None. The local checkout contains 26 settlement scenarios
(13 `settlement_traces/` and 13 `settlement2_traces/`), one more `/2`
scenario than the port brief described. The Rust test covers every
`*.ledger.jsonl` present in both corpora.

## Running

```sh
cargo test
```
