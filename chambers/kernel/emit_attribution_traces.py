"""Emit the golden corpus for charge-attribution/1+2 (ATTRIBUTION-SPEC).

Deterministic: no randomness, no clocks. Same discipline as the
settlement emitters: honest scenarios go through the real compile_report /
SettlementIssuer.release_split APIs; adversarial ones inject forged
payloads exactly the way a Byzantine actor would. Each scenario writes:

    attribution_traces/<name>.ledger.jsonl   the artifact (id-sorted canonical lines)
    attribution_traces/<name>.expected.json  canonical /2 settlement fold + V-codes
                                             + S-codes + P-codes + I-codes + X-codes
                                             + conservation identity

Every other corpus is FROZEN and untouched. THIS family is the
attribution counterparty target — a second implementation written from
ATTRIBUTION-SPEC.md alone (exact-integer Shapley over the P.4 DPI game,
largest-remainder allocation, V1–V5, S11/S12, the split fold arm) must
reproduce every expected file bit-for-bit. The alpha story is pinned
here at microcredit resolution: 1/8000 of a $100M pot is exactly
12_500_000_000 ucr.

Run: python3 chambers/kernel/emit_attribution_traces.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from chambers.kernel.attribution import attribution_codes, compile_report  # noqa: E402
from chambers.kernel.events import DerivationEvent, canonical_json, event_id  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.meter import KernelMeter  # noqa: E402
from chambers.kernel.settlement import (  # noqa: E402
    DefaultResolutionEvent,
    SettlementIssuer,
    SplitCondition,
    audit_settlement_codes,
    conservation_identity,
    settlement_fold_canonical_v2,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attribution_traces")

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
FACT = "sha256:" + "d" * 64
FA = "sha256:" + "a" * 64
FB = "sha256:" + "b" * 64
K_ALICE = ("exp", "alice", "readerR")
K_BOB = ("exp", "bob", "readerR")
POT_100M = 100_000_000 * 1_000_000
ALICE_ROW = 12_500_000_000
BOB_ROW = POT_100M - ALICE_ROW


def _est(total: int, channel: str) -> CapacityEstimate:
    return CapacityEstimate(total, 0, 0, 0, 0, channel)


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _alpha_economy(*, funded: bool, default_on_expiry: str = "refund_to_payer"):
    """The alpha story's metered economy: alice's idea (capacity 1) and
    bob's build (7999) feed FACT; the coupled emission charges both.
    With `funded`, requesterR escrows the $100M pot split-bound to the
    emission. Returns (ledger, bank_or_None, escrow_or_None, receipts)."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="chamberA", ledger=ledger)
    for k in (K_ALICE, K_BOB):
        meter.register(k, subject_entropy_mbits=1_000_000, ceiling_mbits=50_000)
    reg = {
        k: next(eid for eid, p in ledger._events.items()
                if p.get("kind") == "register" and p.get("key") == list(k))
        for k in (K_ALICE, K_BOB)
    }
    ledger.add(DerivationEvent(
        derived=FA, consumed=(reg[K_ALICE],), hop_capacity_mbits=1,
        issuer="chamberA", seq=1, tick=1))
    ledger.add(DerivationEvent(
        derived=FB, consumed=(reg[K_BOB],), hop_capacity_mbits=7999,
        issuer="chamberA", seq=2, tick=1))
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(FA, FB), hop_capacity_mbits=50_000,
        issuer="chamberA", seq=3, tick=1))
    decisions = meter.charge_coupled(
        [K_ALICE, K_BOB], _est(8_000, "derived:" + FACT), TOR, tick=2)
    assert all(d.accepted for d in decisions.values())
    receipts = sorted(
        eid for eid, p in ledger._events.items()
        if p.get("kind") == "charge" and p.get("accepted") is True
    )
    if not funded:
        return ledger, None, None, receipts
    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    bank.deposit("requesterR", POT_100M, tick=3)
    escrow = bank.escrow(
        payer="requesterR", payee="orchestrator", amount_ucr=POT_100M,
        charge_keys=[K_ALICE, K_BOB], expires_tick=100, tick=4,
        required_clean=True, default_on_expiry=default_on_expiry,
        split=SplitCondition(derived=FACT, node="n1", coupling_tick=2),
    )
    return ledger, bank, escrow, receipts


def _honest_report_payload(ledger) -> dict:
    return compile_report(
        ledger, FACT, "n1", 2, POT_100M,
        issuer="chamberA", seq=9, tick=5).payload()


def _forged_release(escrow_id, amount, receipts, *, beneficiary=None,
                    seq=7, tick=5) -> dict:
    p = {
        "kind": "release", "escrow_id": escrow_id, "amount_ucr": amount,
        "charge_ids": list(receipts), "issuer": "houseEscrow",
        "seq": seq, "tick": tick,
    }
    if beneficiary is not None:
        p["beneficiary"] = beneficiary
    return p


# ---- scenarios ----

def s_alpha_honest_split() -> Ledger:
    """The founding story, green end to end: the declared report and the
    split-bound pot coexist; both rows pay exactly; every surface clean;
    alice's row is 12_500_000_000 ucr to the microcredit."""
    ledger, bank, escrow, receipts = _alpha_economy(funded=True)
    ledger.add(compile_report(
        ledger, FACT, "n1", 2, POT_100M, issuer="chamberA", seq=9, tick=5))
    ra = bank.release_split(escrow, "alice", receipts, tick=5)
    rb = bank.release_split(escrow, "bob", receipts, tick=6)
    assert (ra.amount_ucr, rb.amount_ucr) == (ALICE_ROW, BOB_ROW)
    return ledger


def s_report_lie_v1() -> Ledger:
    """A report shaving one microcredit from alice onto bob: V1 on both
    rows, sums intact so no V2 — the finding names the recomputed pair."""
    ledger, _bank, _escrow, _receipts = _alpha_economy(funded=False)
    p = _honest_report_payload(ledger)
    p["shares"] = [dict(r) for r in p["shares"]]
    p["shares"][0]["payout_ucr"] -= 1
    p["shares"][1]["payout_ucr"] += 1
    _forge(ledger, p)
    return ledger


def s_report_mints_v2() -> Ledger:
    """A report whose payouts leave 5 ucr of the pot unaccounted: V2,
    the conservation arm that never goes dark, plus the V1 on the row."""
    ledger, _bank, _escrow, _receipts = _alpha_economy(funded=False)
    p = _honest_report_payload(ledger)
    p["shares"] = [dict(r) for r in p["shares"]]
    p["shares"][1]["payout_ucr"] -= 5
    _forge(ledger, p)
    return ledger


def s_split_stiff() -> Ledger:
    """The stiff: the whole pot forged to bob. S11 (not his row's
    amount) + S12 (cumulative overdraw) + S4 (the V-dirty court? no —
    no report here: the split binding convicts without any report)."""
    ledger, _bank, escrow, receipts = _alpha_economy(funded=True)
    _forge(ledger, _forged_release(escrow.id, POT_100M, receipts,
                                   beneficiary="bob"))
    return ledger


def s_row_default_antiholdup() -> Ledger:
    """F4 exercised: the issuer goes silent; alice submits her own row's
    default after expiry; the fold credits her exactly; clean."""
    ledger, _bank, escrow, receipts = _alpha_economy(
        funded=True, default_on_expiry="release_by_report")
    ledger.add(DefaultResolutionEvent(
        escrow_id=escrow.id, amount_ucr=ALICE_ROW,
        charge_ids=tuple(receipts), submitter="alice", seq=1, tick=101,
        beneficiary="alice",
    ))
    return ledger


def s_premature_offrow_default() -> Ledger:
    """The same move before expiry (S8) and at the wrong amount (S11):
    timing and row discipline hold on the permissionless path."""
    ledger, _bank, escrow, receipts = _alpha_economy(
        funded=True, default_on_expiry="release_by_report")
    ledger.add(DefaultResolutionEvent(
        escrow_id=escrow.id, amount_ucr=ALICE_ROW,
        charge_ids=tuple(receipts), submitter="alice", seq=1, tick=50,
        beneficiary="alice",
    ))
    ledger.add(DefaultResolutionEvent(
        escrow_id=escrow.id, amount_ucr=ALICE_ROW + 5,
        charge_ids=tuple(receipts), submitter="alice", seq=2, tick=101,
        beneficiary="alice",
    ))
    return ledger


def s_arity_refusal_v5() -> Ledger:
    """Thirteen sources: the game is unauditable in bounded work and the
    report convicts V5 — the denial-of-audit refusal, fail closed."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="chamberA", ledger=ledger)
    keys = [("exp", f"s{i:02d}", "readerR") for i in range(13)]
    for k in keys:
        meter.register(k, subject_entropy_mbits=100_000, ceiling_mbits=5_000)
    consumed = []
    for i, k in enumerate(keys):
        reg = next(eid for eid, p in ledger._events.items()
                   if p.get("kind") == "register" and p.get("key") == list(k))
        f = "sha256:" + ("%02x" % i) * 32
        ledger.add(DerivationEvent(
            derived=f, consumed=(reg,), hop_capacity_mbits=10,
            issuer="chamberA", seq=1 + i, tick=1))
        consumed.append(f)
    ledger.add(DerivationEvent(
        derived=FACT, consumed=tuple(consumed),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=99, tick=1))
    decisions = meter.charge_coupled(
        keys, _est(1_000, "derived:" + FACT), TOR, tick=2)
    assert all(d.accepted for d in decisions.values())
    _forge(ledger, {
        "kind": "attribution_report", "derived": FACT,
        "coupling": {"node": "n1", "tick": 2}, "pot_ucr": 0,
        "method": "shapley_dpi/1", "shares": [],
        "issuer": "chamberA", "seq": 1, "tick": 3,
    })
    return ledger


def s_soup_junk_report_total() -> Ledger:
    """Totality: a report of pure junk beside an honest economy — V5s,
    no crash, every other surface unchanged."""
    ledger, _bank, _escrow, _receipts = _alpha_economy(funded=False)
    _forge(ledger, {"kind": "attribution_report", "derived": 7,
                    "coupling": None, "pot_ucr": -3, "method": 9,
                    "shares": "nope", "issuer": [], "seq": {}, "tick": 3})
    return ledger


SCENARIOS = [
    ("alpha-honest-split", s_alpha_honest_split),
    ("report-lie-v1", s_report_lie_v1),
    ("report-mints-v2", s_report_mints_v2),
    ("split-stiff", s_split_stiff),
    ("row-default-antiholdup", s_row_default_antiholdup),
    ("premature-offrow-default", s_premature_offrow_default),
    ("arity-refusal-v5", s_arity_refusal_v5),
    ("soup-junk-report-total", s_soup_junk_report_total),
]


def emit() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, build in SCENARIOS:
        ledger = build()
        artifact = ledger.to_jsonl()
        lhs, rhs = conservation_identity(ledger)
        expected = canonical_json({
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
        with open(os.path.join(OUT, f"{name}.ledger.jsonl"), "w", encoding="ascii") as fh:
            fh.write(artifact)
        with open(os.path.join(OUT, f"{name}.expected.json"), "w", encoding="ascii") as fh:
            fh.write(expected + "\n")
        print(f"{name}: {ledger.event_count()} events, "
              f"{len(attribution_codes(ledger))} v-codes, "
              f"{len(audit_settlement_codes(ledger))} s-codes")
    print(f"\n{len(SCENARIOS)} golden attribution ledgers in {OUT}")


if __name__ == "__main__":
    emit()
