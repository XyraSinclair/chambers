"""Emit the golden settlement corpus for charge-settlement/1 (SETTLEMENT-SPEC §2.1, §3).

Deterministic: no randomness, no clocks. Same discipline as
emit_ledger_traces.py, one layer up: each scenario builds a ledger —
honest ones through the real SettlementIssuer / resolve_default APIs,
adversarial ones by injecting forged payloads exactly the way a Byzantine
actor would — and writes:

    settlement_traces/<name>.ledger.jsonl    the artifact (id-sorted canonical lines)
    settlement_traces/<name>.expected.json   canonical settlement fold + S-codes
                                             + I-codes + conservation identity

The expected values are computed by the Python reference (settlement.py).
The point of the corpus is that a SECOND implementation, written from
SETTLEMENT-SPEC.md alone, reproduces every expected file bit-for-bit —
the same counterparty game the information layer already survived (and
which convicted the reference itself once; see ledger_traces).

Run: python3 chambers/kernel/emit_settlement_traces.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from chambers.kernel.events import canonical_json, event_id  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.meter import KernelMeter  # noqa: E402
from chambers.kernel.settlement import (  # noqa: E402
    SettlementIssuer,
    audit_settlement_codes,
    conservation_identity,
    resolve_default,
    settlement_fold_canonical,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "settlement_traces")

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
KEY = ("exp", "srcA", "readerR")


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _metered_base() -> "tuple[Ledger, str]":
    """An audit-clean information substrate: one account, one self-lease,
    one accepted 10,000-mbit charge. Returns (ledger, charge_event_id)."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="srcA_chamber", ledger=ledger)
    meter.register(KEY, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(KEY, CapacityEstimate(10_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    charge_id = next(
        eid for eid, p in getattr(ledger, "_events").items()
        if p.get("kind") == "charge" and p.get("accepted") is True
    )
    return ledger, charge_id


def _release_payload(escrow_id: str, amount: int, charge_ids: list, seq: int,
                     tick: int, issuer: str = "bank") -> dict:
    return {"kind": "release", "escrow_id": escrow_id, "amount_ucr": amount,
            "charge_ids": charge_ids, "issuer": issuer, "seq": seq, "tick": tick}


# ---- scenarios ----

def s_empty_value() -> Ledger:
    ledger, _ = _metered_base()
    return ledger


def s_honest_flow() -> Ledger:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 500_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=120_000,
                      charge_keys=[KEY], expires_tick=100, tick=2)
    bank.release(esc, 100_000, [charge_id], tick=3)
    bank.refund(esc, 20_000, tick=101)
    return ledger


def s_honest_default_refund() -> Ledger:
    ledger, _ = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 300_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=10, tick=2)
    resolve_default(ledger, esc, submitter="payerP", amount_ucr=50_000, tick=11)
    return ledger


def s_honest_default_release() -> Ledger:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 300_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=10, tick=2,
                      default_on_expiry="release_to_payee")
    resolve_default(ledger, esc, submitter="workerW", amount_ucr=50_000,
                    tick=11, charge_ids=[charge_id])
    return ledger


def s_s1_overdraft_escrow() -> Ledger:
    ledger, _ = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 1_000, tick=0)
    _forge(ledger, {"kind": "escrow", "payer": "payerP", "payee": "workerW",
                    "amount_ucr": 999_999, "charge_keys": [list(KEY)],
                    "required_clean": True, "expires_tick": 100,
                    "default_on_expiry": "refund_to_payer",
                    "issuer": "bank", "seq": 99, "tick": 1})
    return ledger


def s_s2_over_release_and_orphan() -> Ledger:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=10_000,
                      charge_keys=[KEY], expires_tick=100, tick=2)
    # over-release: 9k + 5k > 10k (second one forged; issuer would refuse)
    bank.release(esc, 9_000, [charge_id], tick=3)
    _forge(ledger, _release_payload(esc.id, 5_000, [charge_id], seq=98, tick=4))
    # orphan: release against an escrow id that is not in the ledger
    _forge(ledger, _release_payload("sha256:" + "0" * 64, 1_000, [charge_id],
                                    seq=99, tick=5))
    return ledger


def s_s3_bad_receipts() -> Ledger:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 400_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=100_000,
                      charge_keys=[KEY], expires_tick=100, tick=2)
    events = getattr(ledger, "_events")
    deposit_id = next(e for e, p in events.items() if p.get("kind") == "deposit")
    refused_id = None
    # add a REFUSED charge to reference (over-ceiling attempt)
    meter = KernelMeter(node="n1", issuer="srcA_chamber", ledger=ledger)
    # hydrate a second meter view over the same ledger/key
    meter.register(KEY, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(KEY, CapacityEstimate(999_999, 0, 0, 0, 0, "c"), TOR, tick=6)
    refused_id = next(e for e, p in getattr(ledger, "_events").items()
                      if p.get("kind") == "charge" and p.get("accepted") is False)
    # off-key charge: register+charge a DIFFERENT key through the same node
    other_key = ("exp", "srcB", "readerR")
    meter.register(other_key, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(other_key, CapacityEstimate(1_000, 0, 0, 0, 0, "c"), TOR, tick=7)
    offkey_id = next(e for e, p in getattr(ledger, "_events").items()
                     if p.get("kind") == "charge" and p.get("accepted") is True
                     and tuple(p.get("key", ())) == other_key)
    _forge(ledger, _release_payload(esc.id, 1_000, [], seq=90, tick=8))                     # empty receipt
    _forge(ledger, _release_payload(esc.id, 1_000, ["sha256:" + "1" * 64], seq=91, tick=9))  # absent id
    _forge(ledger, _release_payload(esc.id, 1_000, [deposit_id], seq=92, tick=10))          # not a charge
    _forge(ledger, _release_payload(esc.id, 1_000, [refused_id], seq=93, tick=11))          # refused charge
    _forge(ledger, _release_payload(esc.id, 1_000, [offkey_id], seq=94, tick=12))           # off-key
    return ledger


def s_s4_dirty_court_release() -> Ledger:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=100, tick=2)
    # dirty the court on the escrowed key: forged overspend charge (I3/I4/I6 family)
    events = getattr(ledger, "_events")
    lease_p = next(p for p in events.values() if p.get("kind") == "lease")
    _forge(ledger, {"kind": "charge", "key": list(KEY), "node": "n1",
                    "lease_id": event_id(lease_p), "charge_seq": 999, "tick": 50,
                    "channel": "c", "estimate_total_mbits": 999_999,
                    "estimator_id": "e", "estimator_independence": "adversarial_review",
                    "estimator_worst_case": True, "accepted": True,
                    "reason_class": "EMITTED", "reason_detail": "x",
                    "demand_mbits": 999_999, "debit_mbits": 999_999})
    # issuer would refuse a release on a dirty court; the Byzantine forges it
    _forge(ledger, _release_payload(esc.id, 10_000, [charge_id], seq=95, tick=51))
    return ledger


def s_s5_release_equivocation() -> Ledger:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=100, tick=2)
    _forge(ledger, _release_payload(esc.id, 1_000, [charge_id], seq=7, tick=3))
    _forge(ledger, _release_payload(esc.id, 2_000, [charge_id], seq=7, tick=3))
    return ledger


def s_s6_malformed_events() -> Ledger:
    ledger, _ = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    _forge(ledger, {"kind": "deposit", "account": "x", "amount_ucr": -5,
                    "issuer": "bank", "seq": 50, "tick": 1})
    _forge(ledger, {"kind": "deposit", "account": "x", "amount_ucr": 5,
                    "issuer": "bank", "seq": 0, "tick": 1})
    _forge(ledger, {"kind": "escrow", "payer": "p", "payee": "w",
                    "amount_ucr": 5, "charge_keys": [],
                    "required_clean": True, "expires_tick": 10,
                    "default_on_expiry": "refund_to_payer",
                    "issuer": "bank", "seq": 51, "tick": 1})
    _forge(ledger, {"kind": "escrow", "payer": "p", "payee": "w",
                    "amount_ucr": 5, "charge_keys": [list(KEY)],
                    "required_clean": True, "expires_tick": 10,
                    "default_on_expiry": "keep_forever",
                    "issuer": "bank", "seq": 52, "tick": 1})
    _forge(ledger, {"kind": "release", "escrow_id": 7, "amount_ucr": 5,
                    "charge_ids": ["sha256:" + "2" * 64],
                    "issuer": "bank", "seq": 53, "tick": 1})
    return ledger


def s_s7_expired_release() -> Ledger:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=10, tick=2)
    _forge(ledger, _release_payload(esc.id, 10_000, [charge_id], seq=96, tick=11))
    return ledger


def s_s8_premature_default() -> Ledger:
    ledger, _ = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=100, tick=2)
    _forge(ledger, {"kind": "default_resolution", "escrow_id": esc.id,
                    "amount_ucr": 50_000, "charge_ids": [],
                    "submitter": "workerW", "seq": 1, "tick": 50})
    return ledger


def s_s8_default_release_without_receipt() -> Ledger:
    ledger, _ = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=10, tick=2,
                      default_on_expiry="release_to_payee")
    _forge(ledger, {"kind": "default_resolution", "escrow_id": esc.id,
                    "amount_ucr": 50_000, "charge_ids": [],
                    "submitter": "workerW", "seq": 1, "tick": 11})
    return ledger


SCENARIOS = [
    ("empty-value", s_empty_value),
    ("honest-flow", s_honest_flow),
    ("honest-default-refund", s_honest_default_refund),
    ("honest-default-release", s_honest_default_release),
    ("s1-overdraft-escrow", s_s1_overdraft_escrow),
    ("s2-over-release-and-orphan", s_s2_over_release_and_orphan),
    ("s3-bad-receipts", s_s3_bad_receipts),
    ("s4-dirty-court-release", s_s4_dirty_court_release),
    ("s5-release-equivocation", s_s5_release_equivocation),
    ("s6-malformed-events", s_s6_malformed_events),
    ("s7-expired-release", s_s7_expired_release),
    ("s8-premature-default", s_s8_premature_default),
    ("s8-default-release-without-receipt", s_s8_default_release_without_receipt),
]


def emit() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, build in SCENARIOS:
        ledger = build()
        artifact = ledger.to_jsonl()
        lhs, rhs = conservation_identity(ledger)
        expected = canonical_json({
            "spec": "charge-settlement/1",
            "name": name,
            "settlement": settlement_fold_canonical(ledger),
            "s_codes": audit_settlement_codes(ledger),
            "audit_codes": ledger.audit_codes(),
            "conservation": [lhs, rhs],
        })
        with open(os.path.join(OUT, f"{name}.ledger.jsonl"), "w", encoding="ascii") as fh:
            fh.write(artifact)
        with open(os.path.join(OUT, f"{name}.expected.json"), "w", encoding="ascii") as fh:
            fh.write(expected + "\n")
        print(f"{name}: {ledger.event_count()} events, "
              f"{len(audit_settlement_codes(ledger))} s-codes, "
              f"{len(ledger.audit_codes())} i-codes")
    print(f"\n{len(SCENARIOS)} golden settlement ledgers in {OUT}")


if __name__ == "__main__":
    emit()
