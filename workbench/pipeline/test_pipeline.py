"""The pipeline as a standing lane — the composition holds, not just
the layers. The demo IS the assertion suite (31 inline self-checks:
seats, moats, schema refusals, budget refusals, exact balances,
conservation, secret-absence, verifier verdicts, and — identity /2 —
every authored fact key-signed with both tamper directions convicting),
so the lane replays it end to end and re-derives the headline claims
from the ARTIFACT BYTES alone — what a stranger would do.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "chambers", "kernel"))


def test_pipeline_end_to_end_and_stranger_rederives() -> None:
    import run_pipeline as P
    from ledger import Ledger
    import verify as verify_mod
    import identity as ID

    with tempfile.TemporaryDirectory(prefix="pipeline_") as out:
        P.build(out)
        artifact = open(os.path.join(out, "pipeline.jsonl"), encoding="ascii").read()

    # the stranger's re-derivation, from bytes alone
    led = Ledger.from_jsonl(artifact)
    assert led.to_jsonl() == artifact                      # canonical bytes
    buf = io.StringIO()
    assert verify_mod.verify(artifact, out=buf) == 0       # CLEAN, all surfaces
    assert "sk-live-" not in artifact                      # the secret never crossed
    assert ID.identity_codes(led) == []                    # every sig verifies
    # identity /2: the whole court is attributable — every event whose
    # kind names an author is key-authored AND signed (the stranger can
    # slash/bind a KEY for any fact here, not argue with a string)
    for p in led.events():
        if p.get("kind") in ID.AUTHOR_FIELD:
            assert (ID.author_of(p) or "").startswith(ID.KEY_PREFIX), p["kind"]
            assert isinstance(p.get("sig"), str) and len(p["sig"]) == 128, p["kind"]

    folded = led.fold()
    x_bob = ("exp", "bobs_service", "alice_agent")
    assert folded[x_bob].cumulative_mbits <= folded[x_bob].ceiling_mbits
    assert folded[x_bob].demanded_mbits > folded[x_bob].cumulative_mbits, \
        "the refused bulk-exfil demand must be visible pressure"

    # the seat fact is present and cites a coherence receipt
    seats = [p for p in led.events() if p.get("kind") == "reviewer_seat"]
    assert len(seats) == 1 and seats[0]["coherence_receipt_id"].startswith("sha256:")
    print("pipeline lane: composition green; stranger re-derives every headline")


def test_pipeline_is_deterministic() -> None:
    """Same fixtures, same battery, same court bytes — the whole composed
    system is a pure function of the repo fixtures (R2 discipline at the
    system level; ticks are internal counters, no clock anywhere)."""
    import run_pipeline as P

    arts = []
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix="pipeline_det_") as out:
            P.build(out)
            arts.append(open(os.path.join(out, "pipeline.jsonl"),
                             encoding="ascii").read())
    assert arts[0] == arts[1], "the pipeline must be byte-deterministic"
    print("pipeline determinism: two runs, identical court bytes")


if __name__ == "__main__":
    import contextlib

    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            with contextlib.redirect_stdout(io.StringIO()):
                fn()
            print(f"{name}: ok")
    print("pipeline lane green")
