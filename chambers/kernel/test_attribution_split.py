"""charge-attribution/2 (ATTRIBUTION-SPEC Part II) as a standing lane —
split-bound escrows (S11/S12) and the V-court join.

The law: a pot bound to the split rule can only leave along the rule's
recomputed rows. The load-bearing story is the stiff: the issuer who
tries to pay the whole \$100M pot to bob is convicted from bytes, and
alice collects her \$12,500 row herself after expiry with no one's
permission (F4: the obligation arrives safety-shaped).

Families:
  1. HONEST FLOW — split escrow, both rows paid exactly, CLEAN across
     every family, conservation exact, alice's account holds \$12,500.
  2. CONVICTIONS — S11 (no beneficiary / phantom / wrong amount /
     unauditable game), S12 (row double-pay), S8 (premature default),
     S6 (malformed split, split+outcome, bad default direction).
  3. THE V-COURT — a lying report dirties the named source's keys:
     required_clean releases refuse live and convict after merge (S4).
  4. ANTI-HOLDUP — alice defaults her own row after expiry,
     permissionlessly; the fold credits her; the artifact verifies.
  5. SUBSTRATE — totality on junk, merge-shuffle invariance; honest
     issuer refusals mirror every audit arm.

Run: python3 chambers/kernel/test_attribution_split.py
"""
from __future__ import annotations

import io
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify as verify_mod  # noqa: E402
from accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from attribution import compile_report  # noqa: E402
from events import DerivationEvent, canonical_json, event_id  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402
from settlement import (  # noqa: E402
    DefaultResolutionEvent,
    SettlementIssuer,
    SettlementRefused,
    SplitCondition,
    audit_settlement_codes,
    settlement_fold,
)

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
FACT = "sha256:" + "d" * 64
FA = "sha256:" + "a" * 64
FB = "sha256:" + "b" * 64
K_ALICE = ("exp", "alice", "readerR")
K_BOB = ("exp", "bob", "readerR")

POT_100M = 100_000_000 * 1_000_000
ALICE_ROW = 12_500_000_000            # $12,500.000000 — 1/8000 of $100M
BOB_ROW = POT_100M - ALICE_ROW


def _est(total: int, channel: str) -> CapacityEstimate:
    return CapacityEstimate(total, 0, 0, 0, 0, channel)


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _economy(default_on_expiry: str = "refund_to_payer",
             required_clean: bool = True):
    """The alpha economy with a funded, split-bound pot: alice's idea
    (capacity 1) and bob's build (7999) feed FACT; requesterR escrows
    \$100M bound to the emission's split. Returns (ledger, bank, escrow,
    receipt charge ids)."""
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
    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    bank.deposit("requesterR", POT_100M, tick=3)
    escrow = bank.escrow(
        payer="requesterR", payee="orchestrator", amount_ucr=POT_100M,
        charge_keys=[K_ALICE, K_BOB], expires_tick=100, tick=4,
        required_clean=required_clean, default_on_expiry=default_on_expiry,
        split=SplitCondition(derived=FACT, node="n1", coupling_tick=2),
    )
    return ledger, bank, escrow, receipts


def _s(codes, prefix):
    return [c for c in codes if c.startswith(prefix)]


# ---- 1. honest flow ----

def test_honest_split_pays_both_rows_exactly_and_verifies() -> None:
    """The whole point, green: both rows released by the honest issuer,
    alice's account holds exactly \$12,500, every family CLEAN,
    conservation exact under the stranger's verifier."""
    ledger, bank, escrow, receipts = _economy()
    ra = bank.release_split(escrow, "alice", receipts, tick=5)
    rb = bank.release_split(escrow, "bob", receipts, tick=6)
    assert ra.amount_ucr == ALICE_ROW and rb.amount_ucr == BOB_ROW
    accounts, escrows = settlement_fold(ledger)
    assert accounts["alice"].released_in_ucr == ALICE_ROW
    assert accounts["bob"].released_in_ucr == BOB_ROW
    assert escrows[escrow.id].remaining_ucr == 0
    assert audit_settlement_codes(ledger) == []
    assert verify_mod.verify(ledger.to_jsonl(), out=io.StringIO()) == 0


def test_declared_report_and_split_flow_coexist_clean() -> None:
    """The report stays the legible claim beside the structural binding:
    an honest attribution_report in the same artifact adds no finding."""
    ledger, bank, escrow, receipts = _economy()
    ledger.add(compile_report(
        ledger, FACT, "n1", 2, POT_100M, issuer="chamberA", seq=9, tick=5))
    bank.release_split(escrow, "alice", receipts, tick=5)
    bank.release_split(escrow, "bob", receipts, tick=6)
    assert audit_settlement_codes(ledger) == []
    assert verify_mod.verify(ledger.to_jsonl(), out=io.StringIO()) == 0


# ---- 2. convictions ----

def _forged_release(escrow_id, amount, receipts, *, beneficiary=None, seq=7,
                    tick=5) -> dict:
    p = {
        "kind": "release", "escrow_id": escrow_id, "amount_ucr": amount,
        "charge_ids": list(receipts), "issuer": "houseEscrow",
        "seq": seq, "tick": tick,
    }
    if beneficiary is not None:
        p["beneficiary"] = beneficiary
    return p


def test_the_stiff_convicts_s11_and_s12() -> None:
    """The issuer pays the WHOLE pot to bob: S11 (amount is not bob's
    row) and S12 (cumulative credit to bob exceeds his row)."""
    ledger, bank, escrow, receipts = _economy()
    _forge(ledger, _forged_release(escrow.id, POT_100M, receipts,
                                   beneficiary="bob"))
    codes = audit_settlement_codes(ledger)
    assert _s(codes, "S11 ")
    assert any(c.startswith("S12 ") and '"bob"' in c for c in codes)


def test_no_beneficiary_and_phantom_convict_s11() -> None:
    ledger, bank, escrow, receipts = _economy()
    _forge(ledger, _forged_release(escrow.id, ALICE_ROW, receipts))
    _forge(ledger, _forged_release(escrow.id, ALICE_ROW, receipts,
                                   beneficiary="mallory", seq=8))
    codes = audit_settlement_codes(ledger)
    assert len(_s(codes, "S11 ")) >= 2


def test_row_double_pay_convicts_s12_independently() -> None:
    """Two exact-row releases to alice: each passes the per-event arm
    (right amount), the cumulative arm convicts — S12 is independent."""
    ledger, bank, escrow, receipts = _economy()
    bank.release_split(escrow, "alice", receipts, tick=5)
    _forge(ledger, _forged_release(escrow.id, ALICE_ROW, receipts,
                                   beneficiary="alice", seq=99))
    codes = audit_settlement_codes(ledger)
    assert any(c.startswith("S12 ") and '"alice"' in c for c in codes)
    assert not _s(codes, "S11 ")


def test_unauditable_game_fails_closed() -> None:
    """A split naming a coupling with no emissions: the honest issuer
    refuses live; a forged release convicts S11; refund stays open."""
    ledger, bank, escrow, receipts = _economy()
    bank.deposit("requesterR", 1_000, tick=5)
    ghost = bank.escrow(
        payer="requesterR", payee="orchestrator", amount_ucr=1_000,
        charge_keys=[K_ALICE], expires_tick=100, tick=5,
        split=SplitCondition(derived=FACT, node="ghost-node", coupling_tick=1),
    )
    try:
        bank.release_split(ghost, "alice", receipts, tick=6)
        assert False, "expected refusal"
    except SettlementRefused:
        pass
    bank.refund(ghost, 1_000, tick=7)  # returning value is always safe
    _forge(ledger, _forged_release(ghost.id, 1_000, receipts,
                                   beneficiary="alice", seq=50))
    codes = audit_settlement_codes(ledger)
    assert _s(codes, "S11 ")
    assert _s(codes, "S2 ")  # the forged flow also over-disburses now


def test_malformed_split_shapes_convict_s6() -> None:
    """Junk split block, split+outcome, release_by_report on a non-split
    escrow — each S6, none crashes anything."""
    ledger, bank, escrow, receipts = _economy()
    base = {
        "kind": "escrow", "payer": "requesterR", "payee": "o",
        "amount_ucr": 10, "charge_keys": [list(K_ALICE)],
        "required_clean": False, "expires_tick": 100,
        "default_on_expiry": "refund_to_payer", "issuer": "houseEscrow",
        "tick": 5,
    }
    _forge(ledger, {**base, "seq": 60, "split": "yes"})
    _forge(ledger, {**base, "seq": 61, "default_on_expiry": "release_by_report"})
    _forge(ledger, {
        **base, "seq": 62,
        "split": {"derived": FACT, "node": "n1", "coupling_tick": 2},
        "outcome": {"metric": "m", "lane": "attested", "quorum": 1,
                    "min_independence": "party", "min_bond_ucr": 0,
                    "contest_ticks": 0},
    })
    assert len(_s(audit_settlement_codes(ledger), "S6 ")) >= 3


# ---- 3. the V-court ----

def test_lying_report_dirties_the_sources_court() -> None:
    """A report that shaves alice's row: V1 findings touch alice's and
    bob's exposure keys, so the required_clean split escrow refuses
    live and a forged release convicts S4."""
    ledger, bank, escrow, receipts = _economy()
    honest = compile_report(
        ledger, FACT, "n1", 2, POT_100M, issuer="chamberA", seq=9, tick=5)
    p = honest.payload()
    p["shares"] = [dict(r) for r in p["shares"]]
    p["shares"][0]["payout_ucr"] -= 1
    p["shares"][1]["payout_ucr"] += 1
    _forge(ledger, p)
    try:
        bank.release_split(escrow, "alice", receipts, tick=6)
        assert False, "expected refusal against dirty V-court"
    except SettlementRefused as exc:
        assert "V1" in str(exc)
    _forge(ledger, _forged_release(escrow.id, ALICE_ROW, receipts,
                                   beneficiary="alice", seq=70))
    assert _s(audit_settlement_codes(ledger), "S4 ")


def test_v_court_does_not_block_unrelated_keys() -> None:
    """Precision, not blast radius: a lying report about a STRANGER's
    fact does not dirty alice/bob's escrow (V1 touches the named source
    only)."""
    ledger, bank, escrow, receipts = _economy()
    k_other = ("exp", "carol", "readerR")
    meter = KernelMeter(node="n2", issuer="chamberA", ledger=ledger)
    meter.register(k_other, subject_entropy_mbits=1_000, ceiling_mbits=5_000)
    other_fact = "sha256:" + "9" * 64
    reg = next(eid for eid, p in ledger._events.items()
               if p.get("kind") == "register" and p.get("key") == list(k_other))
    ledger.add(DerivationEvent(
        derived=other_fact, consumed=(reg,), hop_capacity_mbits=10,
        issuer="chamberA", seq=40, tick=1))
    meter.charge(k_other, _est(100, "derived:" + other_fact), TOR, tick=2)
    rep = compile_report(ledger, other_fact, "n2", 2, 1000,
                         issuer="chamberA", seq=41, tick=3).payload()
    rep["shares"] = [dict(r) for r in rep["shares"]]
    # the lie must be V3-shaped (phantom "dave", sums intact): a V2
    # finding's subject is the report id, which fails closed and would
    # rightly touch everything — precision is only claimed for V1/V3/V4.
    rep["shares"].append({"source": "dave", "share_bps": 0, "payout_ucr": 0})
    _forge(ledger, rep)
    # alice/bob's split escrow releases fine: carol's dirt is not theirs
    bank.release_split(escrow, "alice", receipts, tick=6)
    codes = audit_settlement_codes(ledger)
    assert not _s(codes, "S4 ")
    assert not _s(codes, "S11 ")


# ---- 4. anti-holdup ----

def test_alice_collects_her_own_row_after_expiry() -> None:
    """F4 satisfied: the issuer goes silent; after expiry alice submits
    the per-row default HERSELF; the fold credits her exactly her row;
    the artifact verifies CLEAN."""
    ledger, bank, escrow, receipts = _economy(
        default_on_expiry="release_by_report")
    ledger.add(DefaultResolutionEvent(
        escrow_id=escrow.id, amount_ucr=ALICE_ROW,
        charge_ids=tuple(receipts), submitter="alice", seq=1, tick=101,
        beneficiary="alice",
    ))
    accounts, escrows = settlement_fold(ledger)
    assert accounts["alice"].released_in_ucr == ALICE_ROW
    assert escrows[escrow.id].remaining_ucr == POT_100M - ALICE_ROW
    assert audit_settlement_codes(ledger) == []
    assert verify_mod.verify(ledger.to_jsonl(), out=io.StringIO()) == 0


def test_premature_or_offrow_default_convicts() -> None:
    """The same move before expiry is S8; a wrong-amount default is
    S11 — timing and row discipline hold on the permissionless path."""
    ledger, bank, escrow, receipts = _economy(
        default_on_expiry="release_by_report")
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
    codes = audit_settlement_codes(ledger)
    assert _s(codes, "S8 ")
    assert _s(codes, "S11 ")


# ---- 5. substrate ----

def test_issuer_refusals_mirror_the_audit() -> None:
    ledger, bank, escrow, receipts = _economy()
    for attempt in (
        lambda: bank.release(escrow, ALICE_ROW, receipts, tick=5),
        lambda: bank.release_split(escrow, "mallory", receipts, tick=5),
        lambda: bank.escrow(
            payer="requesterR", payee="o", amount_ucr=10,
            charge_keys=[K_ALICE], expires_tick=100, tick=5,
            default_on_expiry="release_by_report"),  # no split block
    ):
        try:
            attempt()
            assert False, "expected refusal"
        except SettlementRefused:
            pass
    bank.release_split(escrow, "alice", receipts, tick=5)
    try:
        bank.release_split(escrow, "alice", receipts, tick=6)
        assert False, "rows pay once"
    except SettlementRefused:
        pass


def test_total_on_junk_and_merge_invariant() -> None:
    ledger, bank, escrow, receipts = _economy()
    _forge(ledger, _forged_release(escrow.id, POT_100M, receipts,
                                   beneficiary="bob"))
    _forge(ledger, {"kind": "release", "escrow_id": escrow.id,
                    "amount_ucr": "lots", "charge_ids": None,
                    "issuer": [], "seq": {}, "tick": 5,
                    "beneficiary": 7})
    want = audit_settlement_codes(ledger)
    assert want
    lines = ledger.to_jsonl().splitlines()
    rng = random.Random(11)
    for _ in range(4):
        rng.shuffle(lines)
        got = audit_settlement_codes(Ledger.from_jsonl("\n".join(lines)))
        assert got == want


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"{len(fns)} passed")
