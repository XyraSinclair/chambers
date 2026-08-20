"""Emit the golden corpus for charge-settlement/2 (SETTLEMENT-SPEC Part II).

Deterministic: no randomness, no clocks. Same discipline as
emit_settlement_traces.py, one spec version up: honest scenarios go
through the real attest_outcome / resolve_bond / resolve_default /
SettlementIssuer APIs; adversarial ones inject forged payloads exactly
the way a Byzantine actor would. Each scenario writes:

    settlement2_traces/<name>.ledger.jsonl    the artifact (id-sorted canonical lines)
    settlement2_traces/<name>.expected.json   canonical /2 settlement fold + S-codes
                                              + I-codes + conservation identity

The /1 corpus (settlement_traces/, 13 scenarios) is FROZEN and untouched:
a /1 counterparty implementation keeps binding to it byte-for-byte. THIS
family is the /2 counterparty target — a second implementation written
from SETTLEMENT-SPEC.md Part II alone must reproduce every expected file
bit-for-bit.

Run: python3 chambers/kernel/emit_settlement2_traces.py
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
    OutcomeCondition,
    SettlementIssuer,
    attest_outcome,
    audit_settlement_codes,
    conservation_identity,
    resolve_bond,
    resolve_default,
    settlement_fold_canonical_v2,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "settlement2_traces")

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


def _stage(cond: OutcomeCondition = COND):
    """Audit-clean substrate + funded payer/attestors + one outcome escrow."""
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
    bank.deposit("arbiterA", 20_000, tick=0)
    bank.deposit("platformX", 20_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=100, tick=2, outcome=cond)
    return ledger, bank, esc, charge_id


# ---- scenarios ----

def s_honest_outcome_flow() -> Ledger:
    """attest → hardened quorum release → bond return: no codes."""
    ledger, bank, esc, charge_id = _stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20,
                         evidence="callPlatform:log:sha256:ab")
    bank.release(esc, 50_000, [charge_id], tick=31, attestation_ids=[att.id])
    resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 5_000, tick=32)
    return ledger


def s_both_parties_sign() -> Ledger:
    """min_independence=party, quorum=2: the consult's both-parties-sign
    option as a configuration."""
    cond = OutcomeCondition(metric="both_confirm_call", lane="attested",
                            quorum=2, min_independence="party",
                            min_bond_ucr=500, contest_ticks=3)
    ledger, bank, esc, charge_id = _stage(cond=cond)
    bank.deposit("workerW", 1_000, tick=1)
    ap = attest_outcome(ledger, esc, "payerP", "occurred", "attested",
                        "party", 500, tick=10)
    aw = attest_outcome(ledger, esc, "workerW", "occurred", "attested",
                        "party", 500, tick=10)
    bank.release(esc, 50_000, [charge_id], tick=14, attestation_ids=[ap.id, aw.id])
    resolve_bond(ledger, ap, "payerP", "return_to_attestor", 500, tick=14)
    resolve_bond(ledger, aw, "workerW", "return_to_attestor", 500, tick=14)
    return ledger


def s_platform_override_slash() -> Ledger:
    """Better evidence convicts: a platform log overrides a bonded ruling;
    the arbiter's bond is slashed to the harmed payer; the escrow settles
    by its declared refund default after expiry. The forged release that
    leaned on the overridden attestation convicts (S9)."""
    ledger, bank, esc, charge_id = _stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    _forge(ledger, {"kind": "release", "escrow_id": esc.id, "amount_ucr": 50_000,
                    "charge_ids": [charge_id], "issuer": "bank", "seq": 90,
                    "tick": 40, "attestation_ids": [att.id]})
    override = attest_outcome(ledger, esc, "platformX", "not_occurred",
                              "platform_log", "role_separated", 5_000, tick=25,
                              evidence="platform:duration:0s")
    resolve_bond(ledger, att, "payerP", "slash", 5_000, tick=26)
    resolve_bond(ledger, override, "platformX", "return_to_attestor", 5_000, tick=40)
    return ledger


def s_payee_default_release() -> Ledger:
    """Anti-holdup for the payee: quorum in hand, issuer silent — the
    permissionless default carries the proof and pays after expiry."""
    ledger, bank, esc, charge_id = _stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    resolve_default(ledger, esc, "workerW", 50_000, tick=101,
                    charge_ids=[charge_id], attestation_ids=[att.id])
    resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 5_000, tick=102)
    return ledger


def s_payer_default_refund() -> Ledger:
    """The declared floor: unattested outcome escrow expires; the payer
    recovers the remainder, no proof needed."""
    ledger, bank, esc, _charge_id = _stage()
    resolve_default(ledger, esc, "payerP", 50_000, tick=101)
    return ledger


def s_s9_gate() -> Ledger:
    """One forged release per S9 arm: no proof; missing reference; wrong
    claim; party demotion (the payee wearing an adversarial_review hat);
    under-bonded; unhardened; Sybil quorum (one attestor, two hats)."""
    cond = OutcomeCondition(metric="m", lane="attested", quorum=2,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    ledger, bank, esc, charge_id = _stage(cond=cond)

    def rel(seq: int, tick: int, ids=None) -> None:
        p = {"kind": "release", "escrow_id": esc.id, "amount_ucr": 1_000,
             "charge_ids": [charge_id], "issuer": "bank", "seq": seq, "tick": tick}
        if ids is not None:
            p["attestation_ids"] = ids
        _forge(ledger, p)

    a1 = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                        "role_separated", 5_000, tick=20)
    a2 = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                        "role_separated", 5_000, tick=21)
    contest = attest_outcome(ledger, esc, "platformX", "not_occurred", "attested",
                             "role_separated", 5_000, tick=22)
    party_att = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id, "claim": "occurred",
        "lane": "attested", "independence": "adversarial_review", "evidence": "",
        "bond_ucr": 5_000, "attestor": "workerW", "seq": 1, "tick": 20})
    under_bonded = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id, "claim": "occurred",
        "lane": "attested", "independence": "role_separated", "evidence": "",
        "bond_ucr": 4_999, "attestor": "platformX", "seq": 9, "tick": 20})
    rel(90, 40)                                    # no proof
    rel(91, 40, ["sha256:" + "0" * 64])            # missing reference
    rel(92, 40, [contest.id])                      # wrong claim
    rel(93, 40, [party_att])                       # under-classed (party demotion)
    rel(94, 40, [under_bonded])                    # under-bonded
    rel(95, 25, [a1.id, a2.id])                    # unhardened (25 <= 20+10 for a1... and Sybil)
    rel(96, 40, [a1.id, a2.id])                    # Sybil quorum: one hand, two hats
    return ledger


def s_s9_unbacked_ghost() -> Ledger:
    """A ghost attestor bonds value it never had: S1 convicts the ghost,
    S9 refuses the quorum, and conservation still balances (the fake bond
    is a recorded negative, not a crash)."""
    ledger, bank, esc, charge_id = _stage()
    ghost = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id, "claim": "occurred",
        "lane": "attested", "independence": "role_separated", "evidence": "",
        "bond_ucr": 5_000, "attestor": "ghostG", "seq": 1, "tick": 20})
    _forge(ledger, {"kind": "release", "escrow_id": esc.id, "amount_ucr": 1_000,
                    "charge_ids": [charge_id], "issuer": "bank", "seq": 90,
                    "tick": 40, "attestation_ids": [ghost]})
    return ledger


def s_equal_lane_contest() -> Ledger:
    """Contested is not convicted: an equal-lane not_occurred blocks the
    quorum (S9 on the forged release) but slashes nobody; both bonds
    return after the window."""
    ledger, bank, esc, charge_id = _stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    contest = attest_outcome(ledger, esc, "platformX", "not_occurred", "attested",
                             "role_separated", 5_000, tick=21)
    _forge(ledger, {"kind": "release", "escrow_id": esc.id, "amount_ucr": 1_000,
                    "charge_ids": [charge_id], "issuer": "bank", "seq": 90,
                    "tick": 40, "attestation_ids": [att.id]})
    resolve_bond(ledger, att, "arbiterA", "return_to_attestor", 5_000, tick=40)
    resolve_bond(ledger, contest, "platformX", "return_to_attestor", 5_000, tick=40)
    return ledger


def s_s10_bond_crimes() -> Ledger:
    """Orphan resolution; premature return; slash without override;
    over-resolution — each forged the way a Byzantine submitter would."""
    ledger, bank, esc, _charge_id = _stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    _forge(ledger, {"kind": "bond_resolution", "attestation_id": "sha256:" + "4" * 64,
                    "amount_ucr": 5, "direction": "slash", "submitter": "x",
                    "seq": 1, "tick": 2})
    _forge(ledger, {"kind": "bond_resolution", "attestation_id": att.id,
                    "amount_ucr": 4_000, "direction": "return_to_attestor",
                    "submitter": "arbiterA", "seq": 1, "tick": 25})
    _forge(ledger, {"kind": "bond_resolution", "attestation_id": att.id,
                    "amount_ucr": 4_000, "direction": "return_to_attestor",
                    "submitter": "arbiterA", "seq": 2, "tick": 40})
    _forge(ledger, {"kind": "bond_resolution", "attestation_id": att.id,
                    "amount_ucr": 1_000, "direction": "slash",
                    "submitter": "payerP", "seq": 1, "tick": 41})
    return ledger


def s_s6_malformed_v2() -> Ledger:
    """Malformed /2 events: an outcome escrow with a release default (the
    self-defeating combo, fail-closed for its releases), a claim outside
    the vocabulary, a direction outside the vocabulary, a bad quorum."""
    ledger, bank, esc, charge_id = _stage()
    bad_esc = _forge(ledger, {
        "kind": "escrow", "payer": "payerP", "payee": "workerW",
        "amount_ucr": 1_000, "charge_keys": [list(KEY)], "required_clean": True,
        "expires_tick": 100, "default_on_expiry": "release_to_payee",
        "issuer": "bank", "seq": 77, "tick": 3, "outcome": COND.payload()})
    _forge(ledger, {"kind": "release", "escrow_id": bad_esc, "amount_ucr": 1_000,
                    "charge_ids": [charge_id], "issuer": "bank", "seq": 78,
                    "tick": 4, "attestation_ids": ["sha256:" + "2" * 64]})
    bad_att = _forge(ledger, {
        "kind": "outcome_attestation", "escrow_id": esc.id, "claim": "maybe",
        "lane": "attested", "independence": "role_separated", "evidence": "",
        "bond_ucr": 5_000, "attestor": "arbiterA", "seq": 5, "tick": 20})
    _forge(ledger, {"kind": "bond_resolution", "attestation_id": bad_att,
                    "amount_ucr": 5, "direction": "keep_forever",
                    "submitter": "x", "seq": 1, "tick": 21})
    _forge(ledger, {
        "kind": "escrow", "payer": "payerP", "payee": "workerW",
        "amount_ucr": 1_000, "charge_keys": [list(KEY)], "required_clean": True,
        "expires_tick": 100, "default_on_expiry": "refund_to_payer",
        "issuer": "bank", "seq": 79, "tick": 5,
        "outcome": {"metric": "m", "lane": "attested", "quorum": 0,
                    "min_independence": "role_separated",
                    "min_bond_ucr": 0, "contest_ticks": 0}})
    return ledger


def s_s5_equivocation_v2() -> Ledger:
    """Two attestations claim the same (attestor, kind, seq) with
    different bytes; likewise two bond resolutions."""
    ledger, bank, esc, _charge_id = _stage()
    for bond in (5_000, 6_000):
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
    return ledger


def s_s8_forged_default_release() -> Ledger:
    """A payee forges a default release with a bogus proof: the value
    MOVES (the fold records the crime), S8 convicts, conservation holds."""
    ledger, bank, esc, charge_id = _stage()
    _forge(ledger, {
        "kind": "default_resolution", "escrow_id": esc.id, "amount_ucr": 50_000,
        "charge_ids": [charge_id], "submitter": "workerW", "seq": 1, "tick": 101,
        "attestation_ids": ["sha256:" + "1" * 64]})
    return ledger


def s_two_escrows_cross_reference() -> Ledger:
    """Two outcome escrows in one artifact; each release leans on its own
    escrow's attestation (clean) and one forged release cross-references
    the other escrow's attestation (off-escrow, S9). Regression scenario
    for the leaked-subject bug found by the F9 attack lane."""
    ledger, bank, esc_a, charge_id = _stage()
    esc_b = bank.escrow(payer="payerP", payee="workerW", amount_ucr=10_000,
                        charge_keys=[KEY], expires_tick=100, tick=3,
                        outcome=COND)
    att_a = attest_outcome(ledger, esc_a, "arbiterA", "occurred", "attested",
                           "role_separated", 5_000, tick=20)
    att_b = attest_outcome(ledger, esc_b, "platformX", "occurred", "attested",
                           "role_separated", 5_000, tick=20)
    bank.release(esc_a, 50_000, [charge_id], tick=31, attestation_ids=[att_a.id])
    bank.release(esc_b, 10_000, [charge_id], tick=31, attestation_ids=[att_b.id])
    _forge(ledger, {"kind": "release", "escrow_id": esc_a.id, "amount_ucr": 1,
                    "charge_ids": [charge_id], "issuer": "bank", "seq": 99,
                    "tick": 32, "attestation_ids": [att_b.id]})
    return ledger


def s_g19_named_override_referent() -> Ledger:
    """G19 (SPEC §9 S10.4 named referent): the naming BINDS. One
    qualifying platform_log override exists; four forged slashes against
    the same overridden ruling differ only in what they cite —
    (a) names the qualifying override: clean of the override arm;
    (b) names an ABSENT id while the qualifying override exists by scan:
        convicts — cited evidence, not available evidence;
    (c) names the equal-lane opposing attestation: convicts (not strictly
        above);
    (d) names junk (a list): resolves to nothing, convicts, never
        crashes.
    Slash amounts are 1 ucr each so the bond never over-resolves; each
    uses a distinct submitter so S5 stays silent. A second implementation
    that keeps scanning when a referent is named diverges on (b)."""
    ledger, bank, esc, _charge_id = _stage()
    bank.deposit("arbiterB", 20_000, tick=0)
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    contest = attest_outcome(ledger, esc, "arbiterB", "not_occurred",
                             "attested", "role_separated", 5_000, tick=22)
    override = attest_outcome(ledger, esc, "platformX", "not_occurred",
                              "platform_log", "role_separated", 5_000, tick=25,
                              evidence="platform:duration:0s")
    named = [override.id, "sha256:" + "9" * 64, contest.id, ["junk"]]
    for i, oid in enumerate(named):
        _forge(ledger, {
            "kind": "bond_resolution", "attestation_id": att.id,
            "amount_ucr": 1, "direction": "slash",
            "override_attestation_id": oid,
            "submitter": f"sub{i}", "seq": 1, "tick": 30 + i})
    return ledger


def s_soup_nonstring_payer_mint() -> Ledger:
    """The F1 soup (fable review, 2026-07-06): forged escrows whose payer
    is not a string once minted their amount into the conservation LHS
    with a fully clean audit (1999 != 1000). The law (SPEC §2, paired
    quantities move all-or-nothing): each such escrow contributes nothing
    anywhere, conservation holds exactly, S6 convicts every forgery. A
    second implementation that folds escrow amounts on uint alone
    reproduces the original bug and diverges here."""
    ledger = Ledger()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("alice", 1_000, tick=0)
    for i, bad_payer in enumerate((None, 123, [], {"x": 1}, True)):
        _forge(ledger, {
            "kind": "escrow", "payer": bad_payer, "payee": "bob",
            "amount_ucr": 999, "charge_keys": [["exp", "s", "r"]],
            "required_clean": True, "expires_tick": 100,
            "default_on_expiry": "refund_to_payer",
            "issuer": "bank", "seq": 2 + i, "tick": 1})
    return ledger


def s_soup_nonstring_party_disbursement() -> Ledger:
    """The disbursement mirror: an escrow whose payee is not a string,
    then a release against it — the disbursement must count toward NO sum
    (it would otherwise drop the escrow remainder with no offsetting
    account gain, 500 != 1000); and a refund against a non-string-payer
    escrow (which never entered the fold). Conservation holds; the S6/S2
    family names each crime."""
    ledger = Ledger()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("alice", 1_000, tick=0)
    esc_a = _forge(ledger, {
        "kind": "escrow", "payer": "alice", "payee": 7, "amount_ucr": 500,
        "charge_keys": [["exp", "s", "r"]], "required_clean": False,
        "expires_tick": 100, "default_on_expiry": "refund_to_payer",
        "issuer": "bank", "seq": 2, "tick": 1})
    _forge(ledger, {
        "kind": "release", "escrow_id": esc_a, "amount_ucr": 500,
        "charge_ids": ["sha256:" + "0" * 64], "issuer": "bank",
        "seq": 3, "tick": 2})
    esc_b = _forge(ledger, {
        "kind": "escrow", "payer": [], "payee": "bob", "amount_ucr": 400,
        "charge_keys": [["exp", "s", "r"]], "required_clean": False,
        "expires_tick": 100, "default_on_expiry": "refund_to_payer",
        "issuer": "bank", "seq": 4, "tick": 1})
    _forge(ledger, {
        "kind": "refund", "escrow_id": esc_b, "amount_ucr": 400,
        "issuer": "bank", "seq": 5, "tick": 2})
    return ledger


def s_soup_unhashable_ids_total() -> Ledger:
    """The F2 kit (fable review rounds 1+2, 2026-07-06): one artifact
    carrying every one-event denial-of-audit shape that once CRASHED a
    total surface — unhashable reason_class (set-membership hashed it),
    nested-list lease/charge keys (key maps admitted them, _touches
    raised), junk escrow_id/attestation_id, an unparseable register key
    (now convicted I7, not silently dropped) — around an intact staged
    escrow + release so the resolved-escrow audit paths (S3/S4/_touches)
    actually execute. Every surface returns; conservation holds; the
    court names each crime. A second implementation must not panic."""
    ledger, bank, esc, charge_id = _stage()
    att = attest_outcome(ledger, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    bank.release(esc, 20_000, [charge_id], tick=31, attestation_ids=[att.id])
    _forge(ledger, {"kind": "charge", "reason_class": {}})
    _forge(ledger, {"kind": "lease", "key": [["x"]], "node": "n1",
                    "lease_seq": 7, "amount_mbits": 10, "issuer": "i",
                    "expires_tick": 9})
    _forge(ledger, {"kind": "charge", "key": [["x"]], "lease_id": "L",
                    "node": "n1", "charge_seq": 9, "tick": 1})
    _forge(ledger, {"kind": "release", "escrow_id": [], "amount_ucr": 5,
                    "charge_ids": ["sha256:" + "0" * 64], "issuer": "bank",
                    "seq": 90, "tick": 2})
    _forge(ledger, {"kind": "bond_resolution", "attestation_id": [],
                    "amount_ucr": 5, "direction": "slash",
                    "submitter": "x", "seq": 91, "tick": 40})
    _forge(ledger, {"kind": "register", "key": [["a"]],
                    "subject_entropy_mbits": 100, "ceiling_mbits": 50,
                    "issuer": "i"})
    return ledger


SCENARIOS = [
    ("honest-outcome-flow", s_honest_outcome_flow),
    ("two-escrows-cross-reference", s_two_escrows_cross_reference),
    ("both-parties-sign", s_both_parties_sign),
    ("platform-override-slash", s_platform_override_slash),
    ("payee-default-release", s_payee_default_release),
    ("payer-default-refund", s_payer_default_refund),
    ("s9-gate", s_s9_gate),
    ("s9-unbacked-ghost", s_s9_unbacked_ghost),
    ("equal-lane-contest", s_equal_lane_contest),
    ("s10-bond-crimes", s_s10_bond_crimes),
    ("s6-malformed-v2", s_s6_malformed_v2),
    ("s5-equivocation-v2", s_s5_equivocation_v2),
    ("s8-forged-default-release", s_s8_forged_default_release),
    # adversarial soups (fable review 2026-07-06): the conservation and
    # totality laws pinned as CORPUS, so the counterparty port cannot
    # reproduce the spec's pre-fix bugs and still conform
    ("g19-named-override-referent", s_g19_named_override_referent),
    ("soup-nonstring-payer-mint", s_soup_nonstring_payer_mint),
    ("soup-nonstring-party-disbursement", s_soup_nonstring_party_disbursement),
    ("soup-unhashable-ids-total", s_soup_unhashable_ids_total),
]


def emit() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, build in SCENARIOS:
        ledger = build()
        artifact = ledger.to_jsonl()
        lhs, rhs = conservation_identity(ledger)
        expected = canonical_json({
            "spec": "charge-settlement/2",
            "name": name,
            "settlement": settlement_fold_canonical_v2(ledger),
            "s_codes": audit_settlement_codes(ledger),
            "audit_codes": ledger.audit_codes(),
            "x_codes": ledger.substrate_codes(),  # charge-substrate/1
            "conservation": [lhs, rhs],
        })
        with open(os.path.join(OUT, f"{name}.ledger.jsonl"), "w", encoding="ascii") as fh:
            fh.write(artifact)
        with open(os.path.join(OUT, f"{name}.expected.json"), "w", encoding="ascii") as fh:
            fh.write(expected + "\n")
        print(f"{name}: {ledger.event_count()} events, "
              f"{len(audit_settlement_codes(ledger))} s-codes, "
              f"{len(ledger.audit_codes())} i-codes")
    print(f"\n{len(SCENARIOS)} golden settlement/2 ledgers in {OUT}")


if __name__ == "__main__":
    emit()
