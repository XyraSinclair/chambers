"""The metered-sort wedge as a standing lane (cardinal-harness adoption #2).

Pins the claim from the mapping report — the kernel prices cardinal's
ranking output as a coupled ordering emission — and the coupling law: a
ranking that would bust ANY one source's ceiling emits against NONE.
"""
from __future__ import annotations

import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kernel"))

import run_sort_metered as wedge  # noqa: E402


def test_end_to_end() -> None:
    with tempfile.TemporaryDirectory(prefix="cardinal_sort_") as out:
        assert wedge.main(["--out", out, "--n", "6"]) == 0
        assert os.path.exists(os.path.join(out, "sort_metered.jsonl"))


def test_ordering_mbits_is_log2_factorial() -> None:
    """Against the EXACT integer derivation, not the implementation's own
    lgamma expression (the first cut re-computed the identical formula on
    both sides — it pinned determinism, not correctness; fable review
    finding, 2026-07-06). math.log2 on the exact factorial integer is
    correctly rounded, so agreement at millibit resolution is a real
    cross-check of the lgamma path."""
    for n in [*range(2, 1201), 5000, 12345, 20000]:
        want = round(math.log2(math.factorial(n)) * 1000.0)
        assert wedge.ordering_mbits(n) == want, n
    assert wedge.ordering_mbits(1) == 0  # a 1-item ranking carries nothing
    assert wedge.ordering_mbits(0) == 0


def test_small_and_large_n_build_or_refuse_honestly() -> None:
    """--n 0/--n 50 both CRASHED the first cut (empty-charge-key escrow;
    hardcoded 200k ceiling < log2(50!) ≈ 214,208 mbits). Now: n < 2 is
    refused with a real error, and the ceiling is a declared bound that
    scales, so every legal n builds and conserves."""
    import pytest
    for bad in (0, 1):
        with pytest.raises(ValueError):
            wedge.build(bad)
    for n in (2, 50, 80):
        ledger = wedge.build(n)
        from settlement import conservation_identity
        lhs, rhs = conservation_identity(ledger)
        assert lhs == rhs == 1_000_000, n
    # the declared read bound is sound: no source exceeded its ceiling
    folded = wedge.build(50).fold()
    for acct in folded.values():
        assert acct.cumulative_mbits <= wedge._ceiling_mbits(50)


def test_ranking_emission_is_atomic_across_sources() -> None:
    ledger = wedge.build(n=6)
    folded = ledger.fold()
    ranking_accounts = [a for k, a in folded.items() if k[2] == wedge.RANKER]
    assert len(ranking_accounts) == 6
    # every source carries the SAME ordering share (one coupled emission),
    # so all cumulative totals moved together — none was left behind.
    ordering_share = wedge.ordering_mbits(6)
    for a in ranking_accounts:
        # cumulative = its pairwise reads + its share of the one ranking
        assert a.cumulative_mbits >= ordering_share
    print("ranking emission landed atomically on all 6 sources")


def test_tight_ceiling_refuses_whole_ranking() -> None:
    # If one source's ceiling cannot absorb the ordering emission, the
    # coupled charge must refuse for ALL sources — no partial ranking.
    from accountant import CapacityEstimate, EstimatorAttestation, exposure_key
    from ledger import Ledger
    from meter import KernelMeter

    ledger = Ledger()
    meter = KernelMeter(node="n", issuer=wedge.RANKER, ledger=ledger)
    keys = [exposure_key(f"o{i}", wedge.RANKER) for i in range(3)]
    for i, k in enumerate(keys):
        # source 2 has a ceiling far below the ordering emission
        ceiling = 100 if i == 2 else 100_000
        meter.register(k, subject_entropy_mbits=400_000, ceiling_mbits=ceiling)
    est = CapacityEstimate(0, wedge.ordering_mbits(3), 0, 0, 0, "ranking")
    decisions = meter.charge_coupled(keys, est, wedge.RANK_ESTIMATOR, tick=1)
    assert not any(d.accepted for d in decisions.values()), "no source may emit"
    # the innocent sources are REFUSED_COUPLED, not silently debited
    folded = ledger.fold()
    for k in keys:
        assert folded[k].cumulative_mbits == 0
    print("a bustable source refused the whole coupled ranking")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
    print("cardinal metered-sort lane green")
