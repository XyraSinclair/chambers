"""charge-verify (Python) — the stranger's one-command receipt verifier.

    python3 -m chambers.kernel.verify <receipt.jsonl>

Reads a charge-kernel ledger artifact, recomputes everything a counterparty
is owed — the information fold (charge-ledger/1), the value fold
(charge-settlement/2: accounts, escrows, attestation bonds), every audit
verdict (the I, S, X, C, P, A, and V families; each family's codes are
defined in its spec, never re-enumerated here), and the conservation
identity — and exits:

    0   clean (no I/S/X/C/P/A/V codes, conservation exact)
    1   findings (the verdicts are printed; the receipt convicts itself)
    2   unreadable artifact

This is the trust equation's evidence made operational: no access to the
producer's code, state, or goodwill is needed. The Rust twin
(`rust_ledger/`'s `charge-verify`) re-verifies the I, S, A, and V
families from an implementation sharing only the specs with this one;
X0, C, and P are Python-only today (the parity residue is recorded in
docs/SPECS.md).
"""
from __future__ import annotations

import sys

from . import findings as findings_registry  # noqa: E402
from .events import canonical_json  # noqa: E402
from .ledger import Ledger  # noqa: E402
from .settlement import (  # noqa: E402
    conservation_identity,
    settlement_fold_canonical_v2,
)


def verify(text: str, out=sys.stdout) -> int:
    try:
        ledger = Ledger.from_jsonl(text)
    except Exception as exc:  # same-id-different-bytes, malformed JSON line
        print(f"UNREADABLE: {exc}", file=out)
        return 2

    w = lambda s="": print(s, file=out)  # noqa: E731
    w(f"events: {ledger.event_count()}")

    # information layer
    accounts = ledger.fold()
    w("\n== charge-ledger/1 (information) ==")
    for key in sorted(accounts, key=lambda k: canonical_json(list(k))):
        a = accounts[key]
        flags = "".join(
            f" [{name}]"
            for name, on in (("INCIDENT", a.incident), ("CONFLICTED", a.conflicted))
            if on
        )
        w(
            f"  {canonical_json(list(key))}: {a.cumulative_mbits}/{a.ceiling_mbits} mbits "
            f"({a.leakage_class}), demanded {a.demanded_mbits}, "
            f"leased {a.granted_lease_mbits}{flags}"
        )
    # value layer
    s_fold = settlement_fold_canonical_v2(ledger)
    lhs, rhs = conservation_identity(ledger)
    if s_fold["accounts"] or s_fold["escrows"] or s_fold["bonds"]:
        w("\n== charge-settlement/2 (value) ==")
        for a in s_fold["accounts"]:
            bonded = (
                f", bonded {a['bonded_out_ucr']}" if a["bonded_out_ucr"] else ""
            )
            slashed = (
                f", slashed-in {a['slashed_in_ucr']}" if a["slashed_in_ucr"] else ""
            )
            w(
                f"  {a['account']}: available {a['available_ucr']} ucr "
                f"(deposited {a['deposited_ucr']}, locked {a['locked_out_ucr']}, "
                f"earned {a['released_in_ucr']}, refunded {a['refunded_in_ucr']}"
                f"{bonded}{slashed})"
            )
        for e in s_fold["escrows"]:
            w(
                f"  escrow {e['escrow_id'][:23]}…: remaining {e['remaining_ucr']}/"
                f"{e['amount_ucr']} ucr (released {e['released_ucr']}, "
                f"refunded {e['refunded_ucr']})"
            )
        for b in s_fold["bonds"]:
            w(
                f"  bond {b['attestation_id'][:23]}…: remaining {b['remaining_ucr']}/"
                f"{b['amount_ucr']} ucr (returned {b['returned_ucr']}, "
                f"slashed {b['slashed_ucr']})"
            )
        w(f"  conservation: {lhs} == {rhs} {'OK' if lhs == rhs else 'BROKEN'}")

    w("\n== verdict ==")
    # every family's codes, in registry order (the one roster is
    # findings.FAMILIES; nothing is re-enumerated here)
    findings = [
        code
        for _prefix, codes in findings_registry.verdict_codes(ledger)
        for code in codes
    ]
    conserved = lhs == rhs
    if not findings and conserved:
        w("CLEAN: no findings; conservation exact")
        return 0
    for c in findings:
        w(f"  {c}")
    if not conserved:
        w("  CONSERVATION BROKEN (unreachable for well-formed artifacts)")
    w(f"CONVICTED: {len(findings)} finding(s)")
    return 1


def main(argv: list) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    try:
        with open(argv[1], "r", encoding="ascii") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"UNREADABLE: {exc}")
        return 2
    return verify(text)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
