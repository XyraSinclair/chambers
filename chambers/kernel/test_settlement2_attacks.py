"""The decentralized-oracle attack register, applied to charge-settlement/2
(FRAMEWORKS.md F9 — imported as an adversarial lane).

charge-settlement/2's attestation game is a bonded Schelling oracle; these
are its known predators (p+ε bribery — Buterin 2015; lazy/copycat
equilibria; griefing contests; top-lane capture). Each test names one
attack and asserts what the mechanism actually does with it, in one of
three honest verdicts:

  PREVENTED — the artifact mechanically refuses/convicts the move;
  PRICED    — the move works but carries a computable cost the artifact
              records (bond at risk, slash to the harmed party);
  RECORDED  — the move works, costs the attacker nothing in-protocol,
              and the artifact's only power is to make it visible (L5).

Nothing here is aspiration: where the answer is "the mechanism cannot
stop this," the test asserts exactly that, and SETTLEMENT-SPEC §11 names
it. The load-bearing arithmetic: a bribed attested-lane quorum is
recoverable-from by ONE hard platform log, and the payer's indemnity is
Σ slashed bonds — full indemnity iff quorum × min_bond ≥ escrow amount,
which is therefore the bond-sizing rule for bribery-sensitive escrows.

Run: python3 chambers/kernel/test_settlement2_attacks.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from events import event_id  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402
from settlement import (  # noqa: E402
    OutcomeCondition,
    SettlementIssuer,
    SettlementRefused,
    attest_outcome,
    audit_settlement_codes,
    conservation_identity,
    resolve_bond,
    settlement_fold_full,
)

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
KEY = ("exp", "srcA", "readerR")


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _stage(cond: OutcomeCondition, escrow_ucr: int = 50_000,
           funded=("arbiter1", "arbiter2", "arbiter3", "platformX")):
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="srcA_chamber", ledger=ledger)
    meter.register(KEY, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(KEY, CapacityEstimate(10_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    charge_id = next(
        eid for eid, p in getattr(ledger, "_events").items()
        if p.get("kind") == "charge" and p.get("accepted") is True
    )
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 500_000, tick=0)
    for who in funded:
        bank.deposit(who, 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=escrow_ucr,
                      charge_keys=[KEY], expires_tick=100, tick=2, outcome=cond)
    return ledger, bank, esc, charge_id


def _release_payload(esc, charge_id, att_ids, tick, seq=90, amount=None):
    return {"kind": "release", "escrow_id": esc.id,
            "amount_ucr": amount if amount is not None else esc.amount_ucr,
            "charge_ids": [charge_id], "issuer": "bank", "seq": seq,
            "tick": tick, "attestation_ids": att_ids}


def _conserved(ledger):
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs, (lhs, rhs)


# ---- attack 1: p+ε bribery of the attested lane ----

def test_bribed_quorum_is_overturned_by_one_hard_log_and_indemnity_is_sum_of_bonds() -> None:
    """PRICED. A briber can buy a full attested-lane quorum (identity and
    payments are L5 — the mechanism cannot see the bribe). What the
    artifact guarantees: ONE platform log overturns the unanimous bribed
    quorum — the leaning release convicts, every bribed bond becomes
    slashable to the harmed payer. Indemnity = quorum × bond; the test
    pins the arithmetic on both sides of the full-indemnity boundary.
    Spec consequence (§11): bribery-sensitive escrows size
    min_bond_ucr ≥ amount / quorum."""
    # Under-collateralized: 3 × 5,000 < 50,000 — bribery profits even
    # after every bond is slashed. The artifact records, prices, and
    # leaves a 35,000 hole the spec table names.
    cond = OutcomeCondition(metric="m", lane="attested", quorum=3,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)
    atts = [attest_outcome(ledger, esc, f"arbiter{i}", "occurred", "attested",
                           "role_separated", 5_000, tick=20)
            for i in (1, 2, 3)]
    # the bribed quorum hardens; the issuer (honest at its view) releases
    rid = _forge(ledger, _release_payload(esc, charge_id, [a.id for a in atts], tick=31))
    assert f"S9 {rid}" not in audit_settlement_codes(ledger)  # clean at this view
    # one hard log arrives
    attest_outcome(ledger, esc, "platformX", "not_occurred", "platform_log",
                   "role_separated", 5_000, tick=35,
                   evidence="platform:duration:0s")
    codes = audit_settlement_codes(ledger)
    assert f"S9 {rid}" in codes  # verdict escalates: the payment leaned on falsehood
    # every bribed bond is now slashable to the payer
    for a in atts:
        resolve_bond(ledger, a, "payerP", "slash", 5_000, tick=36)
    accounts, _e, _b = settlement_fold_full(ledger)
    indemnity = accounts["payerP"].slashed_in_ucr
    assert indemnity == 3 * 5_000
    assert indemnity < esc.amount_ucr  # the named hole: 15,000 < 50,000
    _conserved(ledger)

    # Fully-collateralized twin: bond floor = amount / quorum → indemnity
    # covers the escrow exactly. Same attack, whole payer.
    cond2 = OutcomeCondition(metric="m", lane="attested", quorum=3,
                             min_independence="role_separated",
                             min_bond_ucr=17_000, contest_ticks=10)
    ledger2, bank2, esc2, charge_id2 = _stage(cond2, escrow_ucr=51_000)
    atts2 = [attest_outcome(ledger2, esc2, f"arbiter{i}", "occurred", "attested",
                            "role_separated", 17_000, tick=20)
             for i in (1, 2, 3)]
    _forge(ledger2, _release_payload(esc2, charge_id2, [a.id for a in atts2], tick=31))
    attest_outcome(ledger2, esc2, "platformX", "not_occurred", "platform_log",
                   "role_separated", 17_000, tick=35)
    for a in atts2:
        resolve_bond(ledger2, a, "payerP", "slash", 17_000, tick=36)
    accounts2, _e2, _b2 = settlement_fold_full(ledger2)
    assert accounts2["payerP"].slashed_in_ucr == 51_000 == esc2.amount_ucr
    _conserved(ledger2)


# ---- attack 2: lazy / copycat attestation ----

def test_copycat_attestors_share_the_slash() -> None:
    """PRICED. An attestor who copies another's claim without observing is
    mechanically indistinguishable (L5). The price the artifact attaches:
    the copy carries the SAME bond and the same strict-override exposure —
    when the hard log lands, both the original and the copy are slashed.
    Laziness is not free-riding; it is co-signing."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=2,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)
    original = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                              "role_separated", 5_000, tick=20)
    copycat = attest_outcome(ledger, esc, "arbiter2", "occurred", "attested",
                             "role_separated", 5_000, tick=21)  # copied, unobserved
    attest_outcome(ledger, esc, "platformX", "not_occurred", "platform_log",
                   "role_separated", 5_000, tick=25)
    for a in (original, copycat):
        resolve_bond(ledger, a, "payerP", "slash", 5_000, tick=26)
    accounts, _e, _b = settlement_fold_full(ledger)
    assert accounts["payerP"].slashed_in_ucr == 10_000
    assert accounts["arbiter1"].available_ucr == accounts["arbiter2"].available_ucr == 95_000
    _conserved(ledger)


# ---- attack 3: griefing contests ----

def test_party_contest_is_prevented_by_demotion() -> None:
    """PREVENTED. The payer (who profits from blocking: expiry refunds
    them) contests their own escrow's outcome. The artifact demotes any
    party's attestation to class `party`; under a role_separated floor it
    neither counts toward quorum NOR qualifies as a contest. The payer
    veto exists only in configurations that declare it (party floors =
    both-parties-sign semantics, chosen at lock time)."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=1,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)
    att = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    # the payer's contest, declared under the grandest class they can type
    _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id,
        "claim": "not_occurred", "lane": "attested",
        "independence": "adversarial_review", "evidence": "",
        "bond_ucr": 5_000, "attestor": "payerP", "seq": 1, "tick": 21})
    rid = _forge(ledger, _release_payload(esc, charge_id, [att.id], tick=31))
    assert f"S9 {rid}" not in audit_settlement_codes(ledger)  # not blocked
    _conserved(ledger)


def test_unbacked_ghost_contest_does_not_block() -> None:
    """PREVENTED. A contest is an attestation: it needs the independence
    floor, the bond floor, and a BACKED bond. A ghost's free
    `not_occurred` neither blocks the quorum nor convicts anyone."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=1,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)
    att = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id,
        "claim": "not_occurred", "lane": "attested",
        "independence": "role_separated", "evidence": "",
        "bond_ucr": 5_000, "attestor": "ghostG", "seq": 1, "tick": 21})
    rid = _forge(ledger, _release_payload(esc, charge_id, [att.id], tick=31))
    codes = audit_settlement_codes(ledger)
    assert f"S9 {rid}" not in codes   # quorum stands
    assert "S1 ghostG" in codes       # the ghost convicts itself instead
    _conserved(ledger)


def test_funded_griefer_blocks_at_bond_risk() -> None:
    """PRICED. A funded, role-separated griefer CAN block payment with an
    equal-lane contest (contested ≠ convicted: no slash for accusation).
    The price arrives when better evidence lands: a platform log
    affirming `occurred` strictly overrides the contest, the griefer's
    bond is slashed — to the PAYEE, the party the false `not_occurred`
    would have harmed — and the quorum stands again."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=1,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)
    att = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    griefer = attest_outcome(ledger, esc, "arbiter2", "not_occurred", "attested",
                             "role_separated", 5_000, tick=21)
    rid1 = _forge(ledger, _release_payload(esc, charge_id, [att.id], tick=31, seq=90))
    assert f"S9 {rid1}" in audit_settlement_codes(ledger)  # blocked — payment frozen
    # no slash is possible yet: accusation is not conviction
    try:
        resolve_bond(ledger, griefer, "workerW", "slash", 5_000, tick=32)
        raise AssertionError("slashed on equal-lane accusation")
    except SettlementRefused:
        pass
    # better evidence affirms the outcome
    attest_outcome(ledger, esc, "platformX", "occurred", "platform_log",
                   "role_separated", 5_000, tick=33)
    resolve_bond(ledger, griefer, "workerW", "slash", 5_000, tick=34)
    accounts, _e, _b = settlement_fold_full(ledger)
    assert accounts["workerW"].slashed_in_ucr == 5_000  # griefing paid the payee
    # and a release leaning on the PLATFORM attestation clears
    plat_id = next(e for e, p in getattr(ledger, "_events").items()
                   if p.get("kind") == "outcome_attestation"
                   and p.get("attestor") == "platformX")
    rid2 = _forge(ledger, _release_payload(esc, charge_id, [plat_id], tick=44, seq=91))
    assert f"S9 {rid2}" not in audit_settlement_codes(ledger)
    _conserved(ledger)


# ---- attack 4: capital over-commitment ----

def test_overcommitted_attestor_unbacks_all_their_attestations() -> None:
    """PREVENTED (escalation direction). Backing is an aggregate fold
    fact, not per-attestation: an attestor who bonds past their balance
    goes S1-negative and EVERY attestation they have outstanding stops
    counting — including ones that looked good before the over-commit.
    Verdicts only worsen as facts arrive; capital cannot be reused
    across simultaneous bonds."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=1,
                            min_independence="role_separated",
                            min_bond_ucr=60_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)  # arbiter1 has 100,000
    esc2 = bank.escrow(payer="payerP", payee="workerW", amount_ucr=10_000,
                       charge_keys=[KEY], expires_tick=100, tick=3, outcome=cond)
    a1 = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                        "role_separated", 60_000, tick=20)
    rid1 = _forge(ledger, _release_payload(esc, charge_id, [a1.id], tick=31, seq=90))
    assert f"S9 {rid1}" not in audit_settlement_codes(ledger)  # backed, counts
    # the same capital is bonded again on a second escrow (60k + 60k > 100k)
    a2 = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc2.id, "claim": "occurred",
        "lane": "attested", "independence": "role_separated", "evidence": "",
        "bond_ucr": 60_000, "attestor": "arbiter1", "seq": 2, "tick": 21})
    codes = audit_settlement_codes(ledger)
    assert "S1 arbiter1" in codes          # overdrawn
    assert f"S9 {rid1}" in codes           # and the FIRST release is now unbacked too
    _conserved(ledger)


# ---- attack 5: flip-flop and retroactive escalation ----

def test_self_contest_blocks_and_late_contest_escalates_a_paid_release() -> None:
    """RECORDED, by design. (a) An attestor's own later `not_occurred`
    contests their earlier `occurred` — self-contradiction blocks the
    quorum (an attestor updating against themselves SHOULD stop the
    payment question). (b) Payment finality is NOT a protocol claim: a
    qualifying contest that merges after a release retroactively
    escalates the release's verdict. Value is not unwound — the artifact
    records that the payment leaned on since-contested evidence; the
    bond-slash path, not the release, is the remedy (SPEC §11)."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=1,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)
    att = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    rid = _forge(ledger, _release_payload(esc, charge_id, [att.id], tick=31))
    assert f"S9 {rid}" not in audit_settlement_codes(ledger)  # paid, clean
    # the same arbiter recants (equal lane, own bond)
    attest_outcome(ledger, esc, "arbiter1", "not_occurred", "attested",
                   "role_separated", 5_000, tick=40)
    codes = audit_settlement_codes(ledger)
    assert f"S9 {rid}" in codes  # escalation-only: the record now shows the lean
    # equal lane: the recanted original is still not slashable (no strict override)
    try:
        resolve_bond(ledger, att, "payerP", "slash", 5_000, tick=41)
        raise AssertionError("slashed on equal-lane self-contradiction")
    except SettlementRefused:
        pass
    _conserved(ledger)


# ---- attack 6: top-lane capture ----

def test_payer_owned_platform_is_demoted_but_third_party_capture_is_L5() -> None:
    """Half PREVENTED, half RECORDED. A platform log submitted BY the
    payer is demoted to `party` like any party attestation — a
    payer-owned platform cannot veto its own escrow under a
    role_separated floor. A captured THIRD-PARTY platform is the L5
    residue: nothing outranks the top lane, so its false `not_occurred`
    blocks payment until expiry (the declared refund floor) and can
    slash honest attested bonds. The artifact's whole power there is
    that the capture is a permanent, attributable, transferable fact —
    choose platform attestors the way you choose lease issuers."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=1,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond)
    att = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    # payer submits a "platform log" under their own account name
    _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id,
        "claim": "not_occurred", "lane": "platform_log",
        "independence": "role_separated", "evidence": "totally-real-log",
        "bond_ucr": 5_000, "attestor": "payerP", "seq": 1, "tick": 21})
    rid = _forge(ledger, _release_payload(esc, charge_id, [att.id], tick=31))
    assert f"S9 {rid}" not in audit_settlement_codes(ledger)  # demotion holds
    # third-party capture: platformX lies — blocked is blocked (L5, named)
    attest_outcome(ledger, esc, "platformX", "not_occurred", "platform_log",
                   "role_separated", 5_000, tick=32)
    codes = audit_settlement_codes(ledger)
    assert f"S9 {rid}" in codes  # the artifact records; it cannot adjudicate above the top lane
    _conserved(ledger)


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"oracle attack register: {len(fns)} attacks exercised")
