"""The attention key family as a standing lane (stories/party-matchmaker.md
Act 3; design consult (2026-07-05, private) move 1). Pins:

  * the demo replays end-to-end (5 paid rings, 6th refused, epoch
    regenerates, conservation, tamper conviction) — the whole file IS the
    assertion suite, so one call suffices;
  * the ordering law specifically: a refused ring leaks ZERO exposure —
    the receiver's spam ceiling protects the THIRD PARTY's privacy.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_attention_demo_end_to_end() -> None:
    import demo_attention_notify as demo

    with tempfile.TemporaryDirectory(prefix="attention_demo_") as out:
        assert demo.main(["--out", out]) == 0
        assert os.path.exists(os.path.join(out, "attention_notify.jsonl"))


def test_refused_ring_leaks_nothing() -> None:
    import demo_attention_notify as demo

    ledger = demo.build()
    folded = ledger.fold()
    a_key = demo.att_key("bob", "alice_mediator", "epoch:2026-07-05")
    x_key = ("exp", "charlie_chamber", "bob")
    # six attempts, five admitted: demand shows the pressure, cumulative
    # shows the truth, and exposure moved ONLY for admitted rings.
    assert folded[a_key].demanded_mbits == 6 * demo.INTERRUPT_UNITS
    assert folded[a_key].cumulative_mbits == 5 * demo.INTERRUPT_UNITS
    assert folded[x_key].cumulative_mbits == 5 * demo.CARD_MBITS
    assert folded[x_key].demanded_mbits == 5 * demo.CARD_MBITS
    print("refused ring: attention demand recorded, zero third-party exposure")


if __name__ == "__main__":
    test_attention_demo_end_to_end()
    test_refused_ring_leaks_nothing()
    print("attention lane green")
