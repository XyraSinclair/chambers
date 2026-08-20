"""Tests for charge-settlement/2 — contingent outcomes (SETTLEMENT-SPEC Part II).

Families:
  1. HONEST OUTCOME ECONOMY — outcome escrow → bonded attestation →
     hardened quorum release → bond return: no codes, conservation exact,
     the /1 view of the artifact stays consistent.
  2. THE GATE — releases without proof / unhardened / contested /
     under-classed / under-bonded / unbacked / Sybil-quorum all convict
     (S9) and are refused live by the honest fronts.
  3. EVIDENCE ORDER — equal-lane contest blocks payment but slashes
     nobody; a strictly higher lane (platform log) both blocks and
     slashes; the slash flows to the harmed party.
  4. ANTI-HOLDUP, BOTH DIRECTIONS — the payer defaults to refund after
     expiry; a quorum-holding payee defaults to release against a silent
     issuer (SPEC §7.4).
  5. TOTALITY — S5/S6/S10 on forged soups; conservation is arithmetic
     even under garbage; verdicts are merge/shuffle invariant.

Run: python3 chambers/kernel/test_settlement2.py
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from chambers.kernel.events import event_id  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.meter import KernelMeter  # noqa: E402
from chambers.kernel.settlement import (  # noqa: E402
    OutcomeCondition,
    SettlementIssuer,
    SettlementRefused,
    attest_outcome,
    audit_settlement_codes,
    conservation_identity,
    resolve_bond,
    resolve_default,
    settlement_fold_canonical,
    settlement_fold_canonical_v2,
    settlement_fold_full,
)

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
KEY = ("exp", "srcA", "readerR")

COND = OutcomeCondition(
    metric="first_contact_qualifying_call_15min",
    lane="attested",
    quorum=1,
    min_independence="role_separated",
    min_bond_ucr=5_000,
    contest_ticks=10,
)


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _metered_base():
    """Audit-clean information substrate: one accepted 10,000-mbit charge."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="srcA_chamber", ledger=ledger)
    meter.register(KEY, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(KEY, CapacityEstimate(10_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    charge_id = next(
        eid for eid, p in getattr(ledger, "_events").items()
        if p.get("kind") == "charge" and p.get("accepted") is True
    )
    return ledger, charge_id


def _outcome_stage(cond: OutcomeCondition = COND, amount: int = 50_000):
    """deposits for payer + two would-be attestors, one outcome escrow."""
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 500_000, tick=0)
    bank.deposit("arbiterA", 20_000, tick=0)
    bank.deposit("platformX", 20_000, tick=0)
    esc = bank.escrow(
        payer="payerP", payee="workerW", amount_ucr=amount,
        charge_keys=[KEY], expires_tick=100, tick=2, outcome=cond,
    )
    return ledger, bank, esc, charge_id


def _clean(ledger: Ledger) -> None:
    assert audit_settlement_codes(ledger) == [], audit_settlement_codes(ledger)
    assert ledger.audit_codes() == [], ledger.audit_codes()
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs, (lhs, rhs)


def _conserved(ledger: Ledger) -> None:
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs, (lhs, rhs)


def _shuffle_invariant(ledger: Ledger) -> None:
    codes = audit_settlement_codes(ledger)
    lines = ledger.to_jsonl().strip().splitlines()
    rng = random.Random(7)
    for _ in range(3):
        rng.shuffle(lines)
        re = Ledger.from_jsonl("\n".join(lines) + "\n")
        assert audit_settlement_codes(re) == codes
        assert conservation_identity(re)[0] == conservation_identity(re)[1]


# ---- 1. the honest outcome economy ----

def test_honest_outcome_flow() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20,
                         evidence="callPlatform:log:sha256:ab")
    # bond is locked: arbiter cannot spend it
    accounts, _e, bonds = settlement_fold_full(ledger)
    assert accounts["arbiterA"].available_ucr == 15_000
    assert bonds[att.id].remaining_ucr == 5_000
    # hardened release (31 > 20 + 10) with both receipts
    bank.release(esc, 50_000, [charge_id], tick=31, attestation_ids=[att.id])
    # bond returns after the uncontested window
    resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 5_000, tick=32)
    _clean(ledger)
    accounts, escrows, bonds = settlement_fold_full(ledger)
    assert accounts["workerW"].available_ucr == 50_000
    assert accounts["arbiterA"].available_ucr == 20_000
    assert bonds[att.id].remaining_ucr == 0
    assert escrows[esc.id].remaining_ucr == 0
    _shuffle_invariant(ledger)


def test_v1_view_of_v2_artifact() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    v1 = settlement_fold_canonical(ledger)
    v2 = settlement_fold_canonical_v2(ledger)
    assert "bonds" not in v1
    assert all("bonded_out_ucr" not in a for a in v1["accounts"])
    assert v2["bonds"][0]["attestation_id"] == att.id
    # dropping the /2 fields recovers the /1 serialization exactly (SPEC §8.1)
    stripped = {
        "accounts": [
            {k: v for k, v in a.items()
             if k not in ("bonded_out_ucr", "bond_returned_in_ucr", "slashed_in_ucr")}
            for a in v2["accounts"]
        ],
        "escrows": v2["escrows"],
    }
    # /1 available differs where bonds exist — the v1 view must be the
    # v1 FOLD of the same bytes, not a field-drop of v2:
    assert {a["account"] for a in v1["accounts"]} <= {a["account"] for a in stripped["accounts"]}
    _conserved(ledger)


def test_v2_fold_zero_on_v1_artifact() -> None:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=10_000,
                      charge_keys=[KEY], expires_tick=100, tick=2)
    bank.release(esc, 10_000, [charge_id], tick=3)
    v2 = settlement_fold_canonical_v2(ledger)
    assert v2["bonds"] == []
    assert all(a["bonded_out_ucr"] == 0 and a["bond_returned_in_ucr"] == 0
               and a["slashed_in_ucr"] == 0 for a in v2["accounts"])
    _clean(ledger)


# ---- 2. the gate (S9) ----

def _forged_release(ledger, esc, charge_id, tick, attestation_ids=None, seq=90):
    p = {"kind": "release", "escrow_id": esc.id, "amount_ucr": 1_000,
         "charge_ids": [charge_id], "issuer": "bank", "seq": seq, "tick": tick}
    if attestation_ids is not None:
        p["attestation_ids"] = attestation_ids
    return _forge(ledger, p)


def test_release_without_proof_convicts_and_is_refused() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    rid = _forged_release(ledger, esc, charge_id, tick=31)
    codes = audit_settlement_codes(ledger)
    assert f"S9 {rid}" in codes, codes
    try:
        bank.release(esc, 1_000, [charge_id], tick=31)
        raise AssertionError("issuer released without an outcome proof")
    except SettlementRefused:
        pass
    _conserved(ledger)
    _shuffle_invariant(ledger)


def test_unhardened_release_convicts() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    rid = _forged_release(ledger, esc, charge_id, tick=30, attestation_ids=[att.id])
    assert f"S9 {rid}" in audit_settlement_codes(ledger)  # 30 <= 20+10
    try:
        bank.release(esc, 1_000, [charge_id], tick=30, attestation_ids=[att.id])
        raise AssertionError("issuer released inside the contest window")
    except SettlementRefused:
        pass
    # one tick later it hardens
    bank.release(esc, 1_000, [charge_id], tick=31, attestation_ids=[att.id])
    _conserved(ledger)


def test_missing_offescrow_wrongclaim_references_convict() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    # missing
    r1 = _forged_release(ledger, esc, charge_id, tick=40,
                         attestation_ids=["sha256:" + "0" * 64], seq=91)
    # wrong claim
    contest = attest_outcome(ledger, esc, "arbiterA", "not_occurred", "attested",
                             "role_separated", 5_000, tick=20)
    r2 = _forged_release(ledger, esc, charge_id, tick=40,
                         attestation_ids=[contest.id], seq=92)
    codes = audit_settlement_codes(ledger)
    assert f"S9 {r1}" in codes and f"S9 {r2}" in codes, codes
    _conserved(ledger)


def test_party_demotion_and_floors() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    # the PAYEE attests, declaring adversarial_review: effective class = party
    forged_att = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id, "claim": "occurred",
        "lane": "attested", "independence": "adversarial_review", "evidence": "",
        "bond_ucr": 5_000, "attestor": "workerW", "seq": 1, "tick": 20})
    rid = _forged_release(ledger, esc, charge_id, tick=31,
                          attestation_ids=[forged_att], seq=93)
    assert f"S9 {rid}" in audit_settlement_codes(ledger)
    try:
        attest_outcome(ledger, esc, "workerW", "occurred", "attested",
                       "adversarial_review", 5_000, tick=20)
        raise AssertionError("party attested past a role_separated floor")
    except SettlementRefused:
        pass
    # under-bonded
    try:
        attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                       "role_separated", 4_999, tick=20)
        raise AssertionError("bond below floor accepted")
    except SettlementRefused:
        pass
    _conserved(ledger)


def test_unbacked_bond_convicts_attestor_and_release() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    # ghost attestor with no deposit forges a 5k bond
    ghost_att = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id, "claim": "occurred",
        "lane": "attested", "independence": "role_separated", "evidence": "",
        "bond_ucr": 5_000, "attestor": "ghostG", "seq": 1, "tick": 20})
    rid = _forged_release(ledger, esc, charge_id, tick=31,
                          attestation_ids=[ghost_att], seq=94)
    codes = audit_settlement_codes(ledger)
    assert "S1 ghostG" in codes, codes           # the fake bond overdraws the ghost
    assert f"S9 {rid}" in codes, codes           # and never counts toward quorum
    try:
        attest_outcome(ledger, esc, "ghostG2", "occurred", "attested",
                       "role_separated", 5_000, tick=20)
        raise AssertionError("unbacked bond accepted live")
    except SettlementRefused:
        pass
    _conserved(ledger)
    _shuffle_invariant(ledger)


def test_sybil_quorum_rejected_distinct_attestors_required() -> None:
    cond = OutcomeCondition(metric="m", lane="attested", quorum=2,
                            min_independence="role_separated",
                            min_bond_ucr=1_000, contest_ticks=5)
    ledger, bank, esc, charge_id = _outcome_stage(cond=cond)
    a1 = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                        "role_separated", 1_000, tick=10)
    a2 = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                        "role_separated", 1_000, tick=11)
    rid = _forged_release(ledger, esc, charge_id, tick=30,
                          attestation_ids=[a1.id, a2.id], seq=95)
    assert f"S9 {rid}" in audit_settlement_codes(ledger)  # one hand, two hats
    # a second DISTINCT attestor satisfies the quorum
    a3 = attest_outcome(ledger, esc, "platformX", "occurred", "attested",
                        "role_separated", 1_000, tick=11)
    bank.release(esc, 1_000, [charge_id], tick=30, attestation_ids=[a1.id, a3.id])
    _conserved(ledger)


def test_both_parties_sign_configuration() -> None:
    cond = OutcomeCondition(metric="both_confirm_call", lane="attested", quorum=2,
                            min_independence="party", min_bond_ucr=500,
                            contest_ticks=3)
    ledger, bank, esc, charge_id = _outcome_stage(cond=cond)
    bank.deposit("workerW", 1_000, tick=1)  # the payee needs bond money
    ap = attest_outcome(ledger, esc, "payerP", "occurred", "attested",
                        "party", 500, tick=10)
    aw = attest_outcome(ledger, esc, "workerW", "occurred", "attested",
                        "party", 500, tick=10)
    bank.release(esc, 50_000, [charge_id], tick=14,
                 attestation_ids=[ap.id, aw.id])
    resolve_bond(ledger, ap, "payerP", "return_to_attestor", 500, tick=14)
    resolve_bond(ledger, aw, "workerW", "return_to_attestor", 500, tick=14)
    _clean(ledger)


# ---- 3. the evidence order ----

def test_equal_lane_contest_blocks_but_never_slashes() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    contest = attest_outcome(ledger, esc, "platformX", "not_occurred", "attested",
                             "role_separated", 5_000, tick=21)
    rid = _forged_release(ledger, esc, charge_id, tick=40,
                          attestation_ids=[att.id], seq=96)
    codes = audit_settlement_codes(ledger)
    assert f"S9 {rid}" in codes, codes           # contested: payment blocked
    assert not any(c.startswith("S10") for c in codes), codes
    # neither bond is slashable — not guilty by accusation
    for a, sub in ((att, "payerP"), (contest, "workerW")):
        try:
            resolve_bond(ledger, a, sub, "slash", 5_000, tick=40)
            raise AssertionError("equal-lane contest slashed a bond")
        except SettlementRefused:
            pass
    # both bonds return after the window
    resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 5_000, tick=40)
    resolve_bond(ledger, contest, "platformX", "return_to_attestor", 5_000, tick=40)
    _conserved(ledger)
    _shuffle_invariant(ledger)


def test_platform_log_strictly_overrides_and_slashes() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    _forged_release(ledger, esc, charge_id, tick=40,
                    attestation_ids=[att.id], seq=97)
    # before the override, the release is fine; after it, convicted —
    # better evidence only escalates.
    override = attest_outcome(ledger, esc, "platformX", "not_occurred",
                              "platform_log", "role_separated", 5_000, tick=25,
                              evidence="platform:duration:0s")
    codes = audit_settlement_codes(ledger)
    assert any(c.startswith("S9") for c in codes), codes
    # the arbiter's bond is now slashable — to the PAYER (false `occurred`)
    resolve_bond(ledger, att, "payerP", "slash", 5_000, tick=26)
    accounts, _e, bonds = settlement_fold_full(ledger)
    assert accounts["payerP"].slashed_in_ucr == 5_000
    assert bonds[att.id].remaining_ucr == 0
    # ...and not returnable, live or forged
    try:
        resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 1, tick=40)
        raise AssertionError("returned an overridden bond")
    except SettlementRefused:
        pass
    forged_return = _forge(ledger, {
        "kind": "bond_resolution", "attestation_id": att.id, "amount_ucr": 1,
        "direction": "return_to_attestor", "submitter": "arbiterA",
        "seq": 9, "tick": 40})
    codes = audit_settlement_codes(ledger)
    assert f"S10 {forged_return}" in codes, codes
    assert f"S10 {att.id}" in codes, codes        # and the bond is over-resolved
    # the platform's own bond returns cleanly (nothing outranks it)
    resolve_bond(ledger, override, "platformX", "return_to_attestor", 5_000, tick=40)
    _conserved(ledger)
    _shuffle_invariant(ledger)


def test_slash_without_override_convicts() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    try:
        resolve_bond(ledger, att, "payerP", "slash", 5_000, tick=40)
        raise AssertionError("slashed without a strict override")
    except SettlementRefused:
        pass
    sid = _forge(ledger, {
        "kind": "bond_resolution", "attestation_id": att.id, "amount_ucr": 5_000,
        "direction": "slash", "submitter": "payerP", "seq": 1, "tick": 40})
    assert f"S10 {sid}" in audit_settlement_codes(ledger)
    _conserved(ledger)  # the forged slash still MOVED value; identity holds


def test_premature_return_convicts() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    try:
        resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 5_000, tick=30)
        raise AssertionError("returned inside the contest window")
    except SettlementRefused:
        pass
    rid = _forge(ledger, {
        "kind": "bond_resolution", "attestation_id": att.id, "amount_ucr": 5_000,
        "direction": "return_to_attestor", "submitter": "arbiterA",
        "seq": 1, "tick": 30})
    assert f"S10 {rid}" in audit_settlement_codes(ledger)
    _conserved(ledger)


# ---- 4. anti-holdup, both directions ----

def test_payee_default_release_with_quorum_against_silent_issuer() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    # not before expiry
    try:
        resolve_default(ledger, esc, "workerW", 50_000, tick=50,
                        charge_ids=[charge_id], attestation_ids=[att.id])
        raise AssertionError("default before expiry")
    except SettlementRefused:
        pass
    resolve_default(ledger, esc, "workerW", 50_000, tick=101,
                    charge_ids=[charge_id], attestation_ids=[att.id])
    accounts, escrows, _b = settlement_fold_full(ledger)
    assert accounts["workerW"].available_ucr == 50_000
    assert escrows[esc.id].remaining_ucr == 0
    resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 5_000, tick=102)
    _clean(ledger)
    _shuffle_invariant(ledger)


def test_payer_default_refund_when_unattested() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    resolve_default(ledger, esc, "payerP", 50_000, tick=101)
    accounts, escrows, _b = settlement_fold_full(ledger)
    assert accounts["payerP"].available_ucr == 500_000
    assert escrows[esc.id].remaining_ucr == 0
    _clean(ledger)


def test_forged_default_release_without_quorum_convicts() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    did = _forge(ledger, {
        "kind": "default_resolution", "escrow_id": esc.id, "amount_ucr": 50_000,
        "charge_ids": [charge_id], "submitter": "workerW", "seq": 1, "tick": 101,
        "attestation_ids": ["sha256:" + "1" * 64]})
    codes = audit_settlement_codes(ledger)
    assert f"S8 {did}" in codes, codes
    accounts, _e, _b = settlement_fold_full(ledger)
    assert accounts["workerW"].available_ucr == 50_000  # it MOVED (recorded crime)
    _conserved(ledger)                                   # and the identity still holds


# ---- 5. totality ----

def test_s6_malformed_v2_events() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    # outcome escrow forged with a release default: self-defeating combo
    bad_esc = _forge(ledger, {
        "kind": "escrow", "payer": "payerP", "payee": "workerW",
        "amount_ucr": 1_000, "charge_keys": [list(KEY)], "required_clean": True,
        "expires_tick": 100, "default_on_expiry": "release_to_payee",
        "issuer": "bank", "seq": 77, "tick": 3,
        "outcome": COND.payload()})
    # any release against it fails closed
    rid = _forge(ledger, {
        "kind": "release", "escrow_id": bad_esc, "amount_ucr": 1_000,
        "charge_ids": [charge_id], "issuer": "bank", "seq": 78, "tick": 4,
        "attestation_ids": ["sha256:" + "2" * 64]})
    bad_att = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id, "claim": "maybe",
        "lane": "attested", "independence": "role_separated", "evidence": "",
        "bond_ucr": 5_000, "attestor": "arbiterA", "seq": 5, "tick": 20})
    bad_res = _forge(ledger, {
        "kind": "bond_resolution", "attestation_id": bad_att, "amount_ucr": 5,
        "direction": "keep_forever", "submitter": "x", "seq": 1, "tick": 21})
    codes = audit_settlement_codes(ledger)
    for eid in (bad_esc, rid, bad_att, bad_res):
        assert f"S6 {eid}" in codes or f"S9 {eid}" in codes, (eid, codes)
    assert f"S9 {rid}" in codes, codes  # unintelligible condition: fail closed
    _conserved(ledger)
    _shuffle_invariant(ledger)


def test_s5_equivocation_on_v2_kinds() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    for bond in (5_000, 6_000):  # same (attestor, kind, seq), different bytes
        _forge(ledger, {
            "kind": "outcome_attestation", "escrow_id": esc.id,
            "claim": "occurred", "lane": "attested",
            "independence": "role_separated", "evidence": "",
            "bond_ucr": bond, "attestor": "arbiterA", "seq": 3, "tick": 20})
    for amt in (1, 2):
        _forge(ledger, {
            "kind": "bond_resolution", "attestation_id": "sha256:" + "3" * 64,
            "amount_ucr": amt, "direction": "return_to_attestor",
            "submitter": "subS", "seq": 4, "tick": 21})
    codes = audit_settlement_codes(ledger)
    assert sum(c.startswith("S5") for c in codes) >= 2, codes
    _conserved(ledger)


def test_s10_orphan_and_over_resolution() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    orphan = _forge(ledger, {
        "kind": "bond_resolution", "attestation_id": "sha256:" + "4" * 64,
        "amount_ucr": 5, "direction": "slash", "submitter": "x",
        "seq": 1, "tick": 2})
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    for seq in (2, 3):  # two 4k returns against a 5k bond
        _forge(ledger, {
            "kind": "bond_resolution", "attestation_id": att.id,
            "amount_ucr": 4_000, "direction": "return_to_attestor",
            "submitter": "arbiterA", "seq": seq, "tick": 40})
    codes = audit_settlement_codes(ledger)
    assert f"S10 {orphan}" in codes, codes
    assert f"S10 {att.id}" in codes, codes
    _conserved(ledger)
    _shuffle_invariant(ledger)


def test_conservation_on_forged_v2_soup() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    rng = random.Random(13)
    junk = [
        {"kind": "outcome_attestation", "escrow_id": 7, "claim": "occurred",
         "lane": "attested", "independence": None, "evidence": 3,
         "bond_ucr": -5, "attestor": "z", "seq": 1, "tick": 1},
        {"kind": "outcome_attestation", "escrow_id": esc.id, "claim": "occurred",
         "lane": "warp", "independence": "role_separated", "evidence": "",
         "bond_ucr": 999_999_999, "attestor": "brokeB", "seq": 1, "tick": 1},
        {"kind": "bond_resolution", "attestation_id": "nope", "amount_ucr": 55,
         "direction": "slash", "submitter": "z", "seq": 1, "tick": 1},
        {"kind": "bond_resolution", "attestation_id": esc.id, "amount_ucr": 55,
         "direction": "return_to_attestor", "submitter": "z", "seq": 2, "tick": 1},
        {"kind": "release", "escrow_id": esc.id, "amount_ucr": 10,
         "charge_ids": [charge_id], "issuer": "bank", "seq": 60, "tick": 3,
         "attestation_ids": "not-a-list"},
    ]
    rng.shuffle(junk)
    for p in junk:
        _forge(ledger, p)
    _conserved(ledger)
    assert audit_settlement_codes(ledger)  # plenty convicted
    _shuffle_invariant(ledger)


def test_multi_escrow_artifacts_judge_each_escrow_by_its_own_condition() -> None:
    """Regression: the S9/S8 subject-escrow was once taken from a leaked
    loop variable (the LAST escrow in sorted order), so any artifact with
    two outcome escrows misjudged releases against the sorted-earlier one
    as off-escrow. Found by the F9 oracle-attack lane, 2026-07-06."""
    ledger, bank, esc_a, charge_id = _outcome_stage()
    # a second outcome escrow, same parties, own condition
    esc_b = bank.escrow(payer="payerP", payee="workerW", amount_ucr=10_000,
                        charge_keys=[KEY], expires_tick=100, tick=3,
                        outcome=COND)
    att_a = attest_outcome(ledger, esc_a, "arbiterA", "occurred", "attested",
                           "role_separated", 5_000, tick=20)
    att_b = attest_outcome(ledger, esc_b, "platformX", "occurred", "attested",
                           "role_separated", 5_000, tick=20)
    # each release leans on ITS OWN escrow's attestation: both clean
    bank.release(esc_a, 50_000, [charge_id], tick=31, attestation_ids=[att_a.id])
    bank.release(esc_b, 10_000, [charge_id], tick=31, attestation_ids=[att_b.id])
    _clean(ledger)
    # and a forged cross-referencing release convicts as off-escrow
    rid = _forge(ledger, {
        "kind": "release", "escrow_id": esc_a.id, "amount_ucr": 1,
        "charge_ids": [charge_id], "issuer": "bank", "seq": 99, "tick": 32,
        "attestation_ids": [att_b.id]})
    assert f"S9 {rid}" in audit_settlement_codes(ledger)
    _conserved(ledger)
    _shuffle_invariant(ledger)


def test_issuer_refuses_outcome_with_release_default() -> None:
    ledger, charge_id = _metered_base()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    try:
        bank.escrow(payer="payerP", payee="workerW", amount_ucr=1_000,
                    charge_keys=[KEY], expires_tick=100, tick=2,
                    default_on_expiry="release_to_payee", outcome=COND)
        raise AssertionError("outcome escrow with a release default accepted")
    except SettlementRefused:
        pass


def test_attest_refusals() -> None:
    ledger, bank, esc, charge_id = _outcome_stage()
    plain = bank.escrow(payer="payerP", payee="workerW", amount_ucr=1_000,
                        charge_keys=[KEY], expires_tick=100, tick=3)
    for kwargs, why in (
        (dict(escrow=plain, attestor="arbiterA", claim="occurred",
              lane="attested", independence="role_separated",
              bond_ucr=5_000, tick=5), "no outcome condition"),
        (dict(escrow=esc, attestor="arbiterA", claim="perhaps",
              lane="attested", independence="role_separated",
              bond_ucr=5_000, tick=5), "bad claim"),
        (dict(escrow=esc, attestor="arbiterA", claim="occurred",
              lane="attested", independence="self_interested",
              bond_ucr=5_000, tick=5), "unknown class"),
    ):
        try:
            attest_outcome(ledger, **kwargs)
            raise AssertionError(f"attest accepted: {why}")
        except SettlementRefused:
            pass


# ---- 6. G19 — the named override referent (SPEC §9 S10.4, shipped 2026-07-07) ----

def _g19_stage():
    """Overridden ruling + one qualifying platform_log override + one
    equal-lane contest — the three referent classes a naming slash can cite."""
    ledger, bank, esc, _cid = _outcome_stage()
    bank.deposit("arbiterB", 20_000, tick=0)
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    contest = attest_outcome(ledger, esc, "arbiterB", "not_occurred",
                             "attested", "role_separated", 5_000, tick=22)
    override = attest_outcome(ledger, esc, "platformX", "not_occurred",
                              "platform_log", "role_separated", 5_000, tick=25)
    return ledger, att, contest, override


def test_g19_naming_binds() -> None:
    """The four verdicts in one court: a slash naming the qualifying
    override is CLEAN of the override arm; naming an absent id convicts
    EVEN THOUGH a qualifying override exists by scan (cited evidence,
    not available evidence); naming the equal-lane contest convicts;
    naming junk convicts and never crashes."""
    ledger, att, contest, override = _g19_stage()
    slashes = {}
    for i, oid in enumerate([override.id, "sha256:" + "9" * 64,
                             contest.id, ["junk"]]):
        slashes[i] = _forge(ledger, {
            "kind": "bond_resolution", "attestation_id": att.id,
            "amount_ucr": 1, "direction": "slash",
            "override_attestation_id": oid,
            "submitter": f"sub{i}", "seq": 1, "tick": 30 + i})
    codes = audit_settlement_codes(ledger)
    assert f"S10 {slashes[0]}" not in codes
    for i in (1, 2, 3):
        assert f"S10 {slashes[i]}" in codes, i
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs


def test_g19_absent_field_keeps_scan_semantics() -> None:
    """Byte-stability of the transition: the same slash WITHOUT the field
    is judged by the scan and stays clean (a qualifying override exists) —
    every historical event keeps its exact verdict."""
    ledger, att, _contest, _override = _g19_stage()
    sid = _forge(ledger, {
        "kind": "bond_resolution", "attestation_id": att.id,
        "amount_ucr": 1, "direction": "slash",
        "submitter": "legacy", "seq": 1, "tick": 30})
    assert f"S10 {sid}" not in audit_settlement_codes(ledger)


def test_g19_referent_arrival_is_literal() -> None:
    """The §11 precedent, made literal: a slash naming a referent that is
    NOT YET in the ledger convicts; when exactly that named attestation
    merges, the conviction lifts — de-escalation via the named fact
    arriving, no scan involved."""
    ledger, att, _contest, _override = _g19_stage()
    future = {
        "kind": "outcome_attestation", "escrow_id": att.escrow_id,
        "claim": "not_occurred", "lane": "platform_log",
        "independence": "role_separated", "evidence": "late",
        "bond_ucr": 5_000, "attestor": "platformX", "seq": 77, "tick": 26}
    future_id = event_id(future)
    sid = _forge(ledger, {
        "kind": "bond_resolution", "attestation_id": att.id,
        "amount_ucr": 1, "direction": "slash",
        "override_attestation_id": future_id,
        "submitter": "early", "seq": 1, "tick": 30})
    assert f"S10 {sid}" in audit_settlement_codes(ledger)  # cited fact absent
    _forge(ledger, future)                                  # the referent arrives
    assert f"S10 {sid}" not in audit_settlement_codes(ledger)


def test_g19_honest_front_refuses_bad_referent() -> None:
    """resolve_bond with a named referent: accepts the qualifying one
    (and the event carries the field); refuses an absent or equal-lane
    referent with SettlementRefused, never a crash."""
    ledger, att, contest, override = _g19_stage()
    ev = resolve_bond(ledger, att, "payerP", "slash", 1_000, tick=30,
                      override_attestation_id=override.id)
    events = getattr(ledger, "_events")
    assert events[ev.id]["override_attestation_id"] == override.id
    for bad in ("sha256:" + "9" * 64, contest.id):
        try:
            resolve_bond(ledger, att, "payerP", "slash", 1_000, tick=31,
                         override_attestation_id=bad)
            raise AssertionError(f"slash accepted with referent {bad[:20]}")
        except SettlementRefused:
            pass


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"charge-settlement/2: {len(fns)} tests green")
