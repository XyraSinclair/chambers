"""The attribution golden corpus as a standing lane (ATTRIBUTION-SPEC).

Mirror of test_settlement2_traces.py for charge-attribution/1+2: every
golden ledger must replay bit-for-bit from the artifact alone — parse
jsonl, recompute the canonical /2 settlement fold, the V-codes, S-codes
(now including S11/S12), P-codes, I-codes, X-codes, and the conservation
identity, compare to expected — and re-emission must be byte-identical.
A counterparty implementation built from ATTRIBUTION-SPEC.md alone
(exact-integer Shapley over the P.4 DPI game, largest-remainder
allocation, the split fold arm) is measured against exactly these bytes
— the alpha story's 12_500_000_000 ucr among them.

Run: python3 chambers/kernel/test_attribution_traces.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import emit_attribution_traces as eat  # noqa: E402
from attribution import attribution_codes  # noqa: E402
from events import canonical_json  # noqa: E402
from ledger import Ledger  # noqa: E402
from settlement import (  # noqa: E402
    audit_settlement_codes,
    conservation_identity,
    settlement_fold_canonical_v2,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "attribution_traces")


def _expected_of(ledger: Ledger, name: str) -> str:
    lhs, rhs = conservation_identity(ledger)
    return canonical_json({
        "spec": "charge-attribution/1+2",
        "name": name,
        "settlement": settlement_fold_canonical_v2(ledger),
        "v_codes": attribution_codes(ledger),
        "s_codes": audit_settlement_codes(ledger),
        "p_codes": ledger.provenance_codes(),
        "audit_codes": ledger.audit_codes(),
        "x_codes": ledger.substrate_codes(),
        "conservation": [lhs, rhs],
    })


def test_attribution_corpus_replays_bit_for_bit() -> None:
    """From the artifact bytes ALONE: recompute every surface and match
    the expected file exactly."""
    names = [n for n, _ in eat.SCENARIOS]
    assert len(names) >= 8, "corpus went missing?"
    for name in names:
        with open(os.path.join(OUT, f"{name}.ledger.jsonl"), encoding="ascii") as fh:
            ledger = Ledger.from_jsonl(fh.read())
        with open(os.path.join(OUT, f"{name}.expected.json"), encoding="ascii") as fh:
            want = fh.read().rstrip("\n")
        assert _expected_of(ledger, name) == want, name


def test_attribution_corpus_reemits_identical() -> None:
    """Determinism: rebuilding every scenario from the emitters yields
    byte-identical artifacts and expectations — no clock, no randomness,
    nothing ambient."""
    for name, build in eat.SCENARIOS:
        ledger = build()
        with open(os.path.join(OUT, f"{name}.ledger.jsonl"), encoding="ascii") as fh:
            assert fh.read() == ledger.to_jsonl(), name
        with open(os.path.join(OUT, f"{name}.expected.json"), encoding="ascii") as fh:
            assert fh.read().rstrip("\n") == _expected_of(ledger, name), name


def test_the_alpha_numbers_are_pinned() -> None:
    """The founding story's bytes cannot drift silently: alice's row is
    exactly $12,500.000000 of the $100M pot, conserved."""
    with open(os.path.join(OUT, "alpha-honest-split.expected.json"),
              encoding="ascii") as fh:
        d = json.load(fh)
    accs = {a["account"]: a["released_in_ucr"] for a in d["settlement"]["accounts"]}
    assert accs["alice"] == 12_500_000_000
    assert accs["bob"] == 99_987_500_000_000
    assert d["conservation"][0] == d["conservation"][1] == 100_000_000_000_000
    assert d["v_codes"] == d["s_codes"] == d["p_codes"] == d["audit_codes"] == []


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"{len(fns)} passed")
