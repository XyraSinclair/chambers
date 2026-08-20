"""Tests for charge-settlement/1 (SETTLEMENT-SPEC.md).

Families:
  1. HONEST ECONOMY — deposit → escrow → metered mediation work → release
     against the work receipt → refund of the remainder: S-codes and
     I-codes empty, conservation identity exact, verdict shuffle-merge
     invariant.
  2. CONVICTIONS — one test per S-code, each injected the way a lying
     issuer would, plus the negative case (dirt on an UNRELATED key must
     not block a release).
  3. ISSUER — the honest authority refuses live everything the audit would
     convict after merge.
  4. CONSERVATION — the identity holds even on forged soups (it is
     arithmetic, not an honesty assumption).

Run: python3 chambers/kernel/test_settlement.py
"""
from __future__ import annotations

import os
import random
import sys
from typing import Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import CapacityEstimate, EstimatorAttestation, exposure_key  # noqa: E402
from chambers.kernel.events import ChargeEvent, event_id  # noqa: E402
from chambers.kernel.leases import LeaseIssuer  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.session import MediationSession  # noqa: E402
from chambers.kernel.settlement import (  # noqa: E402
    DepositEvent,
    EscrowEvent,
    RefundEvent,
    ReleaseEvent,
    SettlementIssuer,
    SettlementRefused,
    audit_settlement_codes,
    conservation_identity,
    settlement_fold,
)

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)


def _est(total: int, channel: str = "c") -> CapacityEstimate:
    return CapacityEstimate(total, 0, 0, 0, 0, channel)


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    before = ledger.event_count()
    ledger._add_payload(eid, payload)
    assert ledger.event_count() == before + 1, "forgery did not inject"
    return eid


def _paid_judgement() -> Tuple[Ledger, SettlementIssuer, EscrowEvent, list]:
    """The canonical honest economy: requesterR pays for a judgement over
    two private chambers; the meter runs; the receipt is the payment's
    justification. Returns (ledger, issuer, escrow, accepted_charge_ids)."""
    ledger = Ledger()
    lessor = LeaseIssuer(issuer="issuerOfRecord", ledger=ledger)
    members = ["chamberA", "chamberB"]
    leases: Dict = {}
    for m in members:
        k = exposure_key(m, "guestAgent")
        lessor.register(k, 100000, 50000)
        leases[k] = lessor.grant(k, "node1", 50000, 100)
    req_keys = []
    for m in members:
        k = exposure_key(m, "requesterR")
        lessor.register(k, 100000, 8000)
        leases[k] = lessor.grant(k, "node1", 8000, 100)
        req_keys.append(k)

    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    bank.deposit("requesterR", 500_000, tick=0)
    escrow = bank.escrow(
        payer="requesterR", payee="agentOperator", amount_ucr=120_000,
        charge_keys=req_keys, expires_tick=100, tick=1,
    )

    sess = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    sess.observe("chamberA", _est(20000, "read"), TOR, tick=2)
    sess.observe("chamberB", _est(20000, "read"), TOR, tick=3)
    emit = sess.emit(_est(4500, "judgement"), TOR, tick=4)
    assert emit.accepted
    receipt = [r.event_id for r in emit.results]

    return ledger, bank, escrow, receipt


def test_honest_paid_judgement_settles_clean() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    bank.release(escrow, 100_000, receipt, tick=5)
    bank.refund(escrow, 20_000, tick=101)

    assert ledger.audit_codes() == []
    assert audit_settlement_codes(ledger) == []
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs == 500_000

    accounts, escrows = settlement_fold(ledger)
    assert accounts["agentOperator"].available_ucr == 100_000
    assert accounts["requesterR"].available_ucr == 400_000
    assert escrows[escrow.id].remaining_ucr == 0

    # verdict is a function of the set: 3-shard shuffle-merge reproduces it
    rng = random.Random(11)
    lines = ledger.to_jsonl().strip().splitlines()
    rng.shuffle(lines)
    shards = [Ledger.from_jsonl("\n".join(lines[i::3])) for i in range(3)]
    merged = shards[0].copy().merge(shards[1]).merge(shards[2])
    assert audit_settlement_codes(merged) == []
    assert merged.to_jsonl() == ledger.to_jsonl()
    print("honest paid judgement: value moved, meter clean, conservation exact")


def test_s1_overdraft_convicted() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    # a lying issuer locks more than requesterR ever had
    _forge(ledger, EscrowEvent(
        payer="requesterR", payee="mallory", amount_ucr=10_000_000,
        charge_keys=(exposure_key("chamberA", "requesterR"),),
        required_clean=False, expires_tick=100,
        default_on_expiry="refund_to_payer", issuer="houseEscrow",
        seq=99, tick=9,
    ).payload())
    codes = audit_settlement_codes(ledger)
    assert any(c.startswith("S1 requesterR") for c in codes), codes
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs  # the identity survives the crime; the balance went negative
    print("S1: overdraft escrow convicted, conservation identity intact")


def test_s2_overdisbursed_and_unknown_escrow() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    _forge(ledger, ReleaseEvent(
        escrow_id=escrow.id, amount_ucr=999_999, charge_ids=tuple(receipt),
        issuer="houseEscrow", seq=77, tick=6,
    ).payload())
    codes = audit_settlement_codes(ledger)
    assert any(c == f"S2 {escrow.id}" for c in codes), codes

    _forge(ledger, RefundEvent(
        escrow_id="sha256:" + "0" * 64, amount_ucr=5, issuer="houseEscrow",
        seq=78, tick=6,
    ).payload())
    codes = audit_settlement_codes(ledger)
    assert sum(1 for c in codes if c.startswith("S2 ")) >= 2, codes
    print("S2: over-disbursement and unknown-escrow disbursement convicted")


def test_s3_release_without_work() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    # empty receipt
    r1 = _forge(ledger, ReleaseEvent(escrow.id, 1000, (), "houseEscrow", 71, 6).payload())
    # missing charge
    r2 = _forge(ledger, ReleaseEvent(
        escrow.id, 1000, ("sha256:" + "f" * 64,), "houseEscrow", 72, 6).payload())
    # refused work: find a refused charge by forging one refusal on a req key
    key = exposure_key("chamberA", "requesterR")
    lease_p = next(p for p in ledger.events()
                   if p.get("kind") == "lease" and tuple(p["key"]) == key)
    refused = ChargeEvent(
        key=key, node="node1", lease_id=event_id(lease_p), charge_seq=50, tick=6,
        channel="j", estimate_total_mbits=9000, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=False, reason_class="REFUSED_CEILING",
        reason_detail="would_exceed_ceiling", demand_mbits=9000, debit_mbits=0,
    )
    ledger.add(refused)
    r3 = _forge(ledger, ReleaseEvent(
        escrow.id, 1000, (refused.id,), "houseEscrow", 73, 6).payload())
    # off-key work: pay for the AGENT's observation charge (not a requester key)
    agent_charge = next(
        e for e, p in getattr(ledger, "_events").items()
        if p.get("kind") == "charge" and p.get("accepted") is True
        and tuple(p["key"]) == exposure_key("chamberA", "guestAgent")
    )
    r4 = _forge(ledger, ReleaseEvent(
        escrow.id, 1000, (agent_charge,), "houseEscrow", 74, 6).payload())

    codes = audit_settlement_codes(ledger)
    for rid in (r1, r2, r3, r4):
        assert any(c == f"S3 {rid}" for c in codes), (rid, codes)
    print("S3: empty, missing, refused, and off-key work receipts all convicted")


def test_s4_dirty_court_blocks_and_unrelated_dirt_does_not() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    # dirt on an UNRELATED key: forge an overspend on the agent's account
    other = exposure_key("chamberB", "guestAgent")
    lease_p = next(p for p in ledger.events()
                   if p.get("kind") == "lease" and tuple(p["key"]) == other)
    _forge(ledger, ChargeEvent(
        key=other, node="node1", lease_id=event_id(lease_p), charge_seq=60, tick=6,
        channel="c", estimate_total_mbits=999999, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=999999, debit_mbits=999999,
    ).payload())
    assert ledger.audit_codes() != []  # the ledger IS dirty...
    release = ReleaseEvent(escrow.id, 1000, tuple(receipt), "houseEscrow", 75, 6)
    ledger.add(release)
    codes = audit_settlement_codes(ledger)
    assert not any(c.startswith("S4 ") for c in codes), codes  # ...but not OUR keys

    # now dirt ON an escrowed key: forge an overspend on a requester account
    key = exposure_key("chamberA", "requesterR")
    lease_q = next(p for p in ledger.events()
                   if p.get("kind") == "lease" and tuple(p["key"]) == key)
    _forge(ledger, ChargeEvent(
        key=key, node="node1", lease_id=event_id(lease_q), charge_seq=61, tick=6,
        channel="c", estimate_total_mbits=999999, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=999999, debit_mbits=999999,
    ).payload())
    codes = audit_settlement_codes(ledger)
    assert any(c == f"S4 {release.id}" for c in codes), codes
    print("S4: dirty court on escrowed keys blocks; unrelated dirt does not")


def test_s5_equivocating_deposits() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    _forge(ledger, DepositEvent("mallory", 111, "houseEscrow", 1, 0).payload())
    # seq 1 already used by the honest deposit -> equivocation
    codes = audit_settlement_codes(ledger)
    assert any(c.startswith("S5 ") for c in codes), codes
    print("S5: two settlement facts claiming one (issuer, kind, seq) convicted")


def test_s6_malformed_settlement_events() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    e1 = _forge(ledger, {"kind": "deposit", "account": "x",
                         "amount_ucr": -5, "issuer": "houseEscrow", "seq": 9, "tick": 0})
    e2 = _forge(ledger, {"kind": "escrow", "payer": "x", "payee": "y",
                         "amount_ucr": 5, "charge_keys": [], "required_clean": True,
                         "expires_tick": 9, "issuer": "houseEscrow", "seq": 10, "tick": 0})
    codes = audit_settlement_codes(ledger)
    for eid in (e1, e2):
        assert any(c == f"S6 {eid}" for c in codes), (eid, codes)
    # negative amount must not move the fold
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs == 500_000
    print("S6: malformed settlement facts convicted; fold unmoved")


def test_s7_release_after_expiry() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    rid = _forge(ledger, ReleaseEvent(
        escrow.id, 1000, tuple(receipt), "houseEscrow", 76, 500).payload())
    codes = audit_settlement_codes(ledger)
    assert any(c == f"S7 {rid}" for c in codes), codes
    print("S7: value disbursed against an expired lock convicted")


def test_issuer_refuses_live() -> None:
    ledger, bank, escrow, receipt = _paid_judgement()
    for fn, msg in [
        (lambda: bank.escrow("requesterR", "x", 10_000_000,
                             [exposure_key("chamberA", "requesterR")], 100, 5),
         "overdraft"),
        (lambda: bank.release(escrow, 999_999, receipt, tick=5), "over-release"),
        (lambda: bank.release(escrow, 1000, receipt, tick=500), "expired"),
        (lambda: bank.release(escrow, 1000, [], tick=5), "empty receipt"),
        (lambda: bank.refund(escrow, 999_999, tick=5), "over-refund"),
    ]:
        try:
            fn()
            assert False, f"expected refusal: {msg}"
        except SettlementRefused:
            pass
    # dirty court on escrowed keys -> live refusal too
    key = exposure_key("chamberA", "requesterR")
    lease_p = next(p for p in ledger.events()
                   if p.get("kind") == "lease" and tuple(p["key"]) == key)
    _forge(ledger, ChargeEvent(
        key=key, node="node1", lease_id=event_id(lease_p), charge_seq=62, tick=6,
        channel="c", estimate_total_mbits=999999, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=999999, debit_mbits=999999,
    ).payload())
    try:
        bank.release(escrow, 1000, receipt, tick=5)
        assert False, "expected dirty-court refusal"
    except SettlementRefused:
        pass
    print("issuer: overdraft/over-release/expiry/empty-receipt/over-refund/dirty-court all refused live")


def test_conservation_is_arithmetic_not_honesty() -> None:
    # the identity must hold on every forged soup in this file's tests;
    # here: pile several crimes into one ledger and check it once more.
    ledger, bank, escrow, receipt = _paid_judgement()
    _forge(ledger, ReleaseEvent(escrow.id, 999_999, tuple(receipt),
                                "houseEscrow", 90, 6).payload())
    _forge(ledger, EscrowEvent(
        payer="requesterR", payee="mallory", amount_ucr=10_000_000,
        charge_keys=(exposure_key("chamberA", "requesterR"),),
        required_clean=False, expires_tick=100,
        default_on_expiry="refund_to_payer", issuer="houseEscrow",
        seq=91, tick=9,
    ).payload())
    _forge(ledger, {"kind": "refund", "escrow_id": escrow.id, "amount_ucr": -3,
                    "issuer": "houseEscrow", "seq": 92, "tick": 9})
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs == 500_000
    assert audit_settlement_codes(ledger) != []
    print("conservation: identity exact on a forged soup; the crimes are convictions, not leaks")


def test_silent_holdup_defeated_by_default_resolution() -> None:
    # The sharpest attack on /1-as-drafted: the issuer simply never acts on
    # a clean, fully-metered escrow. Now the PAYEE self-serves after expiry
    # — permissionless, and the audit stays clean because the claim is true.
    from chambers.kernel.settlement import resolve_default

    ledger = Ledger()
    lessor = LeaseIssuer(issuer="issuerOfRecord", ledger=ledger)
    members = ["chamberA", "chamberB"]
    leases: Dict = {}
    for m in members:
        k = exposure_key(m, "guestAgent")
        lessor.register(k, 100000, 50000)
        leases[k] = lessor.grant(k, "node1", 50000, 200)
    req_keys = []
    for m in members:
        k = exposure_key(m, "requesterR")
        lessor.register(k, 100000, 8000)
        leases[k] = lessor.grant(k, "node1", 8000, 200)
        req_keys.append(k)
    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    bank.deposit("requesterR", 500_000, tick=0)
    escrow = bank.escrow(
        payer="requesterR", payee="agentOperator", amount_ucr=120_000,
        charge_keys=req_keys, expires_tick=100, tick=1,
        default_on_expiry="release_to_payee",
    )
    sess = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    emit = sess.emit(_est(4500, "judgement"), TOR, tick=4)
    assert emit.accepted
    receipt = [r.event_id for r in emit.results]

    # the issuer goes silent forever; the payee waits out the expiry...
    try:
        resolve_default(ledger, escrow, "agentOperator", 120_000, tick=50,
                        charge_ids=receipt)
        assert False, "premature default must be refused live"
    except SettlementRefused:
        pass
    # ...and then self-serves the declared default
    resolve_default(ledger, escrow, "agentOperator", 120_000, tick=101,
                    charge_ids=receipt)

    accounts, escrows = settlement_fold(ledger)
    assert accounts["agentOperator"].available_ucr == 120_000
    assert escrows[escrow.id].remaining_ucr == 0
    assert audit_settlement_codes(ledger) == []
    assert ledger.audit_codes() == []
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs == 500_000
    print("silent holdup defeated: payee self-served the declared default, audit clean")


def test_s8_premature_and_receiptless_defaults_convicted() -> None:
    from chambers.kernel.settlement import DefaultResolutionEvent

    ledger, bank, escrow, receipt = _paid_judgement()  # default: refund_to_payer
    # premature refund-direction default (escrow expires at 100)
    d1 = _forge(ledger, DefaultResolutionEvent(
        escrow_id=escrow.id, amount_ucr=1000, charge_ids=(),
        submitter="requesterR", seq=1, tick=50,
    ).payload())
    codes = audit_settlement_codes(ledger)
    assert any(c == f"S8 {d1}" for c in codes), codes

    # release-direction escrow: a receiptless late default must convict too
    bank2_escrow = bank.escrow(
        payer="requesterR", payee="agentOperator", amount_ucr=10_000,
        charge_keys=[exposure_key("chamberA", "requesterR")],
        expires_tick=100, tick=6, default_on_expiry="release_to_payee",
    )
    d2 = _forge(ledger, DefaultResolutionEvent(
        escrow_id=bank2_escrow.id, amount_ucr=10_000, charge_ids=(),
        submitter="agentOperator", seq=1, tick=101,
    ).payload())
    codes = audit_settlement_codes(ledger)
    assert any(c == f"S8 {d2}" for c in codes), codes
    # refund-direction default after expiry with true remainder: legitimate,
    # and the fold routes it to the PAYER regardless of who submitted
    from chambers.kernel.settlement import resolve_default
    resolve_default(ledger, escrow, "anyone", 20_000, tick=102)
    accounts, _ = settlement_fold(ledger)
    # 20_000 legitimate + 1_000 from the CONVICTED premature default: the
    # fold records what happened and the S-code names the crime — value is
    # never silently clamped away (same philosophy as signed balances).
    assert accounts["requesterR"].refunded_in_ucr == 21_000
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs == 500_000
    print("S8: premature and receiptless defaults convicted; declared direction binds")


def test_verifier_clean_and_convicting() -> None:
    import io

    from chambers.kernel import verify as verify_mod

    ledger, bank, escrow, receipt = _paid_judgement()
    bank.release(escrow, 100_000, receipt, tick=5)
    artifact = ledger.to_jsonl()

    buf = io.StringIO()
    assert verify_mod.verify(artifact, out=buf) == 0
    assert "CLEAN" in buf.getvalue()

    tampered = artifact.replace('"amount_ucr":100000', '"amount_ucr":900000')
    assert tampered != artifact
    buf2 = io.StringIO()
    assert verify_mod.verify(tampered, out=buf2) == 1
    assert "CONVICTED" in buf2.getvalue()

    assert verify_mod.verify("not json\n", out=io.StringIO()) == 2
    print("verifier: clean receipt passes, tampered receipt convicts, garbage refused")


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"\nall {len(fns)} settlement tests passed")


if __name__ == "__main__":
    _run_all()
