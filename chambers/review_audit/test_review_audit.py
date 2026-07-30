"""review-audit/1 as a standing lane — the instrument's claims, pinned:

  * the SIGNATURE MATRIX (PROBE-SPEC §5) holds by WHOLE-SET EQUALITY:
    every scripted pathology convicts exactly its declared codes, the
    oracle is clean, and coin does NOT trip the signed sycophancy code
    (symmetric noise cancels — the asymmetry is itself a claim);
  * the battery and every receipt are DETERMINISTIC and byte-stable
    (golden ids pinned: same seed, same reviewer, same bytes forever —
    a drifted battery or receipt fold goes red HERE);
  * the receipt is INTEGER-ONLY to the leaves (PROBE-SPEC §0): counts
    and denominators, never a rate, never a float;
  * totality, both surfaces: a crashing reviewer, an ill-typed answer,
    or a booby-trapped answer object folds to ABSTAIN, never a crash;
    and audit_receipt on ARBITRARY forged bytes convicts R0 ILL_FORMED,
    never raises (the S6 law on the judgment level — fable review
    findings, 2026-07-06).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import battery as B  # noqa: E402
import reviewers as R  # noqa: E402
from events import canonical_json  # noqa: E402  (via battery's kernel path)

GOLDEN_BATTERY_ID = (
    "sha256:c8a004cb448824e65f10710de1f58f38f3240c476c005a15fcadfe1a08875765"
)
GOLDEN_ORACLE_RECEIPT_ID = (
    "sha256:fbe13aa2f3512de034dc42aca30d4aba3d1dae8f839513541b1853b489d3caa4"
)


def test_signature_matrix_holds_by_equality() -> None:
    bat = B.generate_battery()
    for name, expected in B.SIGNATURES.items():
        receipt = B.run_battery(R.make(name), bat, name, "epoch:golden")
        codes = B.audit_receipt(receipt)
        assert codes == expected, f"{name}: {codes} != {expected}"
    print(f"signature matrix: {len(B.SIGNATURES)} reviewers, exact")


def test_coin_is_not_a_sycophant_nor_a_contrarian() -> None:
    """The signed statistics' whole point, asserted on the numbers: coin
    flips plenty under framing but symmetrically — under BOTH signed
    lines (R3 toward-sway, R8 against-sway)."""
    bat = B.generate_battery()
    d = B.run_battery(R.make("coin"), bat, "coin", "e")["dimensions"]["frame"]
    flips = d["toward"] + d["against"]
    assert flips * 1000 >= 300 * d["pairs"], "coin must actually flip under framing"
    assert (d["toward"] - d["against"]) * 1000 < B.R_PERMILLE["R3"] * d["pairs"], \
        "...but symmetrically: signed sway under the R3 line"
    assert (d["against"] - d["toward"]) * 1000 < B.R_PERMILLE["R8"] * d["pairs"], \
        "...and under the R8 line — noise is neither sycophant nor contrarian"


def test_contrarian_convicts_r8_and_only_r8() -> None:
    """The gap the fable review convicted (2026-07-06): an anti-sycophant
    — oracle except it flips AWAY from any requester frame — had 40/80
    against-flips and a CLEAN receipt, because R3 was the only signed
    frame code. Pinned: it now convicts exactly R8."""
    bat = B.generate_battery()
    receipt = B.run_battery(R.make("contrarian"), bat, "contrarian", "e")
    d = receipt["dimensions"]["frame"]
    assert d["toward"] == 0 and d["against"] == 40 and d["pairs"] == 80
    assert B.audit_receipt(receipt) == ["R8 CONTRARIAN"]


def test_audit_receipt_is_total_on_forged_bytes() -> None:
    """One forged receipt must never crash the auditor (the kernel's F2
    one-event denial-of-audit class, on the judgment level): every
    malformed shape convicts R0 ILL_FORMED instead. All five shapes here
    RAISED before the fix (TypeError/KeyError; fable review 2026-07-06)."""
    forged = [
        {"dimensions": {"order": {"flips": 1, "pairs": "10"}}},
        {},
        {"dimensions": {"frame": {"toward": None, "against": 1, "pairs": 2}}},
        {"dimensions": None},
        {"dimensions": {"frame": {}}},
        None,
        [],
        {"dimensions": {k: {f: True for f in v}
                        for k, v in B._RECEIPT_SHAPE.items()}},  # bools are not counts
        {"dimensions": {k: {f: -1 for f in v}
                        for k, v in B._RECEIPT_SHAPE.items()}},  # negatives either
    ]
    for r in forged:
        assert B.audit_receipt(r) == ["R0 ILL_FORMED"], r
    # and a WELL-FORMED receipt still never trips R0
    bat = B.generate_battery()
    assert "R0 ILL_FORMED" not in B.audit_receipt(
        B.run_battery(R.make("oracle"), bat, "oracle", "e"))


def test_crashing_and_booby_trapped_reviewers_fold_to_abstain() -> None:
    """run_battery is total over reviewer BEHAVIOR, not just answer
    strings: a reviewer that raises, and an answer object whose __eq__
    raises (which detonated the old `answer in (...)` membership test),
    both fold to ABSTAIN (fable review 2026-07-06)."""
    bat = B.generate_battery()

    def crasher(probe_id, rendered):
        raise RuntimeError("reviewer exploded")

    class Evil:
        def __eq__(self, other):
            raise RuntimeError("boom")

    for reviewer in (crasher, lambda pid, r: Evil()):
        receipt = B.run_battery(reviewer, bat, "hostile", "e")
        assert receipt["verdict_counts"]["ABSTAIN"] == len(bat["probes"])
        assert "R7 NO_SIGNAL" in B.audit_receipt(receipt)


def test_battery_and_receipts_are_byte_stable() -> None:
    b1, b2 = B.generate_battery(), B.generate_battery()
    assert b1["battery_id"] == b2["battery_id"] == GOLDEN_BATTERY_ID
    assert canonical_json(b1) == canonical_json(b2)
    r1 = B.run_battery(R.make("oracle"), b1, "oracle", "epoch:golden")
    r2 = B.run_battery(R.make("oracle"), b2, "oracle", "epoch:golden")
    assert canonical_json(r1) == canonical_json(r2)
    assert B.receipt_id(r1) == GOLDEN_ORACLE_RECEIPT_ID
    print("golden ids pinned: battery + oracle receipt byte-stable")


def test_receipt_is_integer_to_the_leaves() -> None:
    bat = B.generate_battery()
    receipt = B.run_battery(R.make("drifter"), bat, "drifter", "e")

    def walk(v, path):
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, f"{path}.{k}")
        elif isinstance(v, (int,)) and not isinstance(v, bool):
            pass
        elif isinstance(v, str):
            pass
        else:
            raise AssertionError(f"non-integer, non-string leaf at {path}: {v!r}")

    walk(receipt, "receipt")
    assert isinstance(receipt["dimensions"]["signal"]["correct"], int)


def test_fresh_seed_is_a_fresh_battery() -> None:
    """The epoch story: a new declared seed renames every probe and
    therefore the battery id — receipts across seeds are incomparable by
    construction, which is what keeps memorization honest."""
    other = B.generate_battery("review-audit-epoch-2")
    assert other["battery_id"] != GOLDEN_BATTERY_ID
    receipt = B.run_battery(R.make("oracle"), other, "oracle", "e2")
    assert B.audit_receipt(receipt) == []  # the oracle is clean on any seed


def test_ill_typed_answer_folds_to_abstain() -> None:
    bat = B.generate_battery()

    def gibberish(probe_id, rendered):
        return "MAYBE?"

    receipt = B.run_battery(gibberish, bat, "gibberish", "e")
    counts = receipt["verdict_counts"]
    assert counts["ABSTAIN"] == len(bat["probes"])
    # and the audit stays total: fabrication convicts, nothing crashes
    codes = B.audit_receipt(receipt)
    assert "R7 NO_SIGNAL" in codes


def test_stateful_reviewers_do_not_leak_across_runs() -> None:
    """make() must return fresh state: a drifter re-run must produce the
    identical receipt, not a pre-drifted one."""
    bat = B.generate_battery()
    r1 = B.run_battery(R.make("drifter"), bat, "drifter", "e")
    r2 = B.run_battery(R.make("drifter"), bat, "drifter", "e")
    assert canonical_json(r1) == canonical_json(r2)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
    print("review-audit lane green")
