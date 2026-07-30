"""peer-sim as a standing lane — F5's worked machinery
(frontier/judgement-markets/peer-prediction.md).

Families:
  1. THE IDENTITY — the constant-report strategy scores EXACTLY zero
     under exact-integer correlated agreement, swept over random report
     vectors (an identity, not an expectation).
  2. THE SCENES — the full sim: v0 low-sensitivity coupling settles
     receipt-bound with the redundancy printed; the kill regime's audit
     reader is REFUSED_CEILING inside the owner's declared budget; both
     artifacts verify CLEAN.

Run: python3 chambers/peer_sim/test_peer_sim.py
"""
from __future__ import annotations

import io
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_peer_prediction as sim  # noqa: E402


def test_constant_strategy_scores_exactly_zero_always() -> None:
    """Memo §2.1 swept: for ANY report vector and ANY constant, the CA
    score is exactly 0 — the arithmetic identity that makes blind
    agreement worthless."""
    rng = random.Random(97)
    for _ in range(200):
        n = rng.randint(2, 20)
        r1 = [rng.randint(0, 3) for _ in range(n)]
        for c in range(4):
            assert sim.ca_score(r1, [c] * n) == 0
            assert sim.ca_score([c] * n, r1) == 0


def test_informative_correlation_scores_positive() -> None:
    """Perfect agreement on a non-constant vector scores positive; the
    anti-correlated binary pair scores negative."""
    rng = random.Random(98)
    for _ in range(50):
        n = rng.randint(4, 16)
        r = [rng.randint(0, 1) for _ in range(n)]
        if len(set(r)) < 2:
            r[0] = 1 - r[0]
        assert sim.ca_score(r, list(r)) > 0
        assert sim.ca_score(r, [1 - x for x in r]) < 0


def test_the_scenes_run_clean() -> None:
    """The whole sim: every self-check passes and both scene artifacts
    verify CLEAN under the stranger's verifier."""
    sim.CHECKS.clear()
    out = io.StringIO()
    assert sim.main(out) == 0
    text = out.getvalue()
    assert "redundancy_mbits" in text
    assert "REFUSED_CEILING" in text
    assert "court CLEAN" in text


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"{len(fns)} passed")
