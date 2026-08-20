"""The settlement golden corpus as a standing lane (SETTLEMENT-SPEC §2.1/§3).

Mirror of the information layer's corpus test: every golden settlement
ledger must replay bit-for-bit from the artifact alone — parse jsonl,
recompute the canonical settlement fold, S-codes, I-codes, and the
conservation identity, compare to expected — and re-emission must be
byte-identical (Python-reference drift goes red HERE; a counterparty
implementation built from SETTLEMENT-SPEC.md alone is measured against
exactly these bytes).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel import emit_settlement_traces as est  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.settlement import (  # noqa: E402
    audit_settlement_codes,
    conservation_identity,
    settlement_fold_canonical,
)

TRACES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settlement_traces")


def test_settlement_corpus_replays_bit_for_bit() -> None:
    names = sorted(
        f[: -len(".ledger.jsonl")]
        for f in os.listdir(TRACES)
        if f.endswith(".ledger.jsonl")
    )
    assert len(names) >= 13, names
    for name in names:
        artifact = open(os.path.join(TRACES, f"{name}.ledger.jsonl"), encoding="ascii").read()
        expected = json.load(open(os.path.join(TRACES, f"{name}.expected.json"), encoding="ascii"))
        ledger = Ledger.from_jsonl(artifact)
        assert ledger.to_jsonl() == artifact, f"{name}: reserialization not byte-identical"
        assert settlement_fold_canonical(ledger) == expected["settlement"], f"{name}: fold diverges"
        assert audit_settlement_codes(ledger) == expected["s_codes"], f"{name}: s-codes diverge"
        assert ledger.audit_codes() == expected["audit_codes"], f"{name}: i-codes diverge"
        assert list(conservation_identity(ledger)) == expected["conservation"], \
            f"{name}: conservation diverges"
    print(f"settlement corpus: {len(names)} golden ledgers replay bit-for-bit")


def test_settlement_corpus_reemits_identical() -> None:
    committed = {}
    for f in os.listdir(TRACES):
        with open(os.path.join(TRACES, f), "rb") as fh:
            committed[f] = fh.read()
    est.emit()
    for f, before in committed.items():
        with open(os.path.join(TRACES, f), "rb") as fh:
            assert fh.read() == before, f"{f}: re-emission not byte-identical"
    print("settlement corpus re-emits byte-identical")


if __name__ == "__main__":
    test_settlement_corpus_replays_bit_for_bit()
    test_settlement_corpus_reemits_identical()
    print("settlement corpus lane green")
