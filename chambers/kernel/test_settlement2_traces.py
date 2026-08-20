"""The settlement/2 golden corpus as a standing lane (SETTLEMENT-SPEC Part II).

Mirror of test_settlement_traces.py, one spec version up: every golden
/2 ledger must replay bit-for-bit from the artifact alone — parse jsonl,
recompute the canonical /2 settlement fold, S-codes (S1–S10), I-codes,
and the /2 conservation identity, compare to expected — and re-emission
must be byte-identical. A counterparty implementation built from
SETTLEMENT-SPEC.md Part II alone is measured against exactly these bytes.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel import emit_settlement2_traces as est2  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.settlement import (  # noqa: E402
    audit_settlement_codes,
    conservation_identity,
    settlement_fold_canonical_v2,
)

TRACES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settlement2_traces")


def test_settlement2_corpus_replays_bit_for_bit() -> None:
    names = sorted(
        f[: -len(".ledger.jsonl")]
        for f in os.listdir(TRACES)
        if f.endswith(".ledger.jsonl")
    )
    assert len(names) >= 12, names
    for name in names:
        artifact = open(os.path.join(TRACES, f"{name}.ledger.jsonl"), encoding="ascii").read()
        expected = json.load(open(os.path.join(TRACES, f"{name}.expected.json"), encoding="ascii"))
        assert expected["spec"] == "charge-settlement/2", name
        ledger = Ledger.from_jsonl(artifact)
        assert ledger.to_jsonl() == artifact, f"{name}: reserialization not byte-identical"
        assert settlement_fold_canonical_v2(ledger) == expected["settlement"], f"{name}: fold diverges"
        assert audit_settlement_codes(ledger) == expected["s_codes"], f"{name}: s-codes diverge"
        assert ledger.audit_codes() == expected["audit_codes"], f"{name}: i-codes diverge"
        assert ledger.substrate_codes() == expected["x_codes"], f"{name}: x-codes diverge"
        assert list(conservation_identity(ledger)) == expected["conservation"], \
            f"{name}: conservation diverges"
        assert expected["conservation"][0] == expected["conservation"][1], \
            f"{name}: conservation identity BROKEN (impossible for the total fold)"
    print(f"settlement/2 corpus: {len(names)} golden ledgers replay bit-for-bit")


def test_settlement2_corpus_reemits_identical() -> None:
    committed = {}
    for f in os.listdir(TRACES):
        with open(os.path.join(TRACES, f), "rb") as fh:
            committed[f] = fh.read()
    est2.emit()
    for f, before in committed.items():
        with open(os.path.join(TRACES, f), "rb") as fh:
            assert fh.read() == before, f"{f}: re-emission not byte-identical"
    print("settlement/2 corpus re-emits byte-identical")


if __name__ == "__main__":
    test_settlement2_corpus_replays_bit_for_bit()
    test_settlement2_corpus_reemits_identical()
    print("settlement/2 corpus lane green")
