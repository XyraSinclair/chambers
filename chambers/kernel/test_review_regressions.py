"""Regressions for the fable-review findings (2026-07-06).

An adversarial Fable review of the day's kernel deltas convicted the work
of three real defects — two of them (F1, F2) in the exact classes the
module docstrings advertise immunity from (conservation "arithmetic on
any event soup"; the fold "never raises on adversarial content"). This
lane pins each so it cannot regress. The review is itself an assurance
artifact: like the earlier counterparty exercise that convicted the
reference of a soundness bug, it caught what 224 tests and the whole
adversarial corpus missed — because every corpus scenario used
well-formed string accounts and hashable ids.

Run: python3 chambers/kernel/test_review_regressions.py
"""
from __future__ import annotations

import os
import random
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
)

TOR = EstimatorAttestation("i", "adversarial_review", "m", True)
KEY = ("exp", "srcA", "readerR")


def _forge(ledger: Ledger, p: dict) -> str:
    eid = event_id(p)
    ledger._add_payload(eid, p)
    return eid


# ---- F1 — conservation must hold on ANY soup, non-string accounts included ----

def test_f1_nonstring_account_escrow_conserves_and_convicts() -> None:
    """A forged escrow with a non-string payer once minted its amount into
    the conservation LHS with a FULLY CLEAN audit (1999 == 1000 → False).
    Now: the escrow contributes all-or-nothing, conservation holds, and
    S6 convicts the malformed event."""
    for bad_payer in (None, 123, [], {"x": 1}, True):
        led = Ledger()
        _forge(led, {"kind": "deposit", "account": "alice", "amount_ucr": 1000,
                     "issuer": "bank", "seq": 1, "tick": 0})
        e = _forge(led, {"kind": "escrow", "payer": bad_payer, "payee": "bob",
                         "amount_ucr": 999, "charge_keys": [["exp", "s", "r"]],
                         "required_clean": True, "expires_tick": 100,
                         "default_on_expiry": "refund_to_payer",
                         "issuer": "bank", "seq": 2, "tick": 1})
        lhs, rhs = conservation_identity(led)
        assert lhs == rhs, (bad_payer, lhs, rhs)
        assert f"S6 {e}" in audit_settlement_codes(led), bad_payer


def test_f1_nonstring_payee_release_and_refund_conserve() -> None:
    """The mirror: a disbursement to a non-string party once dropped the
    escrow remainder with no offsetting account gain (500 == 1000 → False).
    Now conservation holds; the disbursement is convicted (S3/S2). BOTH
    disbursement arms pinned — the first cut of this test forged only the
    release despite its name, leaving the refund pairing free to desync
    (fable review round 2, 2026-07-06)."""
    for kind, party_field, bad in [
        ("release", "payee", None), ("release", "payee", 7),
        ("release", "payee", []),
        ("refund", "payer", None), ("refund", "payer", 7),
        ("refund", "payer", []),
    ]:
        led = Ledger()
        _forge(led, {"kind": "deposit", "account": "alice", "amount_ucr": 1000,
                     "issuer": "bank", "seq": 1, "tick": 0})
        escrow_p = {"kind": "escrow", "payer": "alice", "payee": "bob",
                    "amount_ucr": 500, "charge_keys": [["exp", "s", "r"]],
                    "required_clean": False, "expires_tick": 100,
                    "default_on_expiry": "refund_to_payer",
                    "issuer": "bank", "seq": 2, "tick": 1}
        escrow_p[party_field] = bad
        e = _forge(led, escrow_p)
        disb = {"kind": kind, "escrow_id": e, "amount_ucr": 500,
                "issuer": "bank", "seq": 1, "tick": 2}
        if kind == "release":
            disb["charge_ids"] = ["sha256:" + "0" * 64]
        _forge(led, disb)
        lhs, rhs = conservation_identity(led)
        assert lhs == rhs, (kind, bad, lhs, rhs)
        assert audit_settlement_codes(led)  # the crime is named


# ---- F2 — no single forged event may crash any total audit surface ----

def test_f2_unhashable_and_missing_ids_never_crash() -> None:
    targeted = [
        {"kind": "bond_resolution", "attestation_id": [], "amount_ucr": 5,
         "direction": "slash", "submitter": "x", "seq": 1, "tick": 1},
        {"kind": "release", "escrow_id": {}, "amount_ucr": 5,
         "charge_ids": ["sha256:" + "0" * 64], "issuer": "b", "seq": 1, "tick": 1},
        {"kind": "refund", "escrow_id": [1], "amount_ucr": 5, "issuer": "b",
         "seq": 1, "tick": 1},
        {"kind": "register", "subject_entropy_mbits": 100, "ceiling_mbits": 50,
         "issuer": "i"},  # missing key
        {"kind": "register", "key": [["x"]], "subject_entropy_mbits": 100,
         "ceiling_mbits": 50, "issuer": "i"},  # nested-list key
        {"kind": "lease", "node": "n", "lease_seq": 1, "amount_mbits": 10,
         "issuer": "i", "expires_tick": 9},  # missing key
        {"kind": "lease", "key": 5, "node": "n", "lease_seq": 1,
         "amount_mbits": 10, "issuer": "i", "expires_tick": 9},  # non-list key
        {"kind": "charge", "lease_id": [], "key": ["a"], "node": "n",
         "charge_seq": 1, "tick": 1, "channel": "c", "estimate_total_mbits": 1,
         "estimator_id": "e", "estimator_independence": "x",
         "estimator_worst_case": True, "accepted": True,
         "reason_class": "EMITTED", "reason_detail": "x",
         "demand_mbits": 1, "debit_mbits": 1},  # unhashable lease_id -> I8/I4
        {"kind": "charge", "node": {}, "lease_id": {}, "key": ["a"],
         "charge_seq": 1, "tick": 1, "channel": "c", "estimate_total_mbits": 1,
         "estimator_id": "e", "estimator_independence": "x",
         "estimator_worst_case": True, "accepted": True,
         "reason_class": "EMITTED", "reason_detail": "x",
         "demand_mbits": 1, "debit_mbits": 1},  # unhashable node (I8 dedup)
    ]
    for p in targeted:
        led = Ledger()
        _forge(led, dict(p))
        # every total surface must return, never raise
        led.audit_codes()
        led.substrate_codes()
        led.provenance_codes()
        audit_settlement_codes(led)
        lhs, rhs = conservation_identity(led)
        assert lhs == rhs, p


def test_f2_fuzz_totality() -> None:
    """8k multi-event adversarial soups across every audit surface: none
    may raise. (The full sweep was 20k; this is the standing floor.)"""
    rng = random.Random(7)
    junk = [None, True, False, 5, -3, 10 ** 18, [], {}, [1], [["a"]],
            {"a": 1}, "sha256:" + "0" * 64, "x", [["a"], ["b"]], [None]]
    kinds = ["register", "lease", "charge", "deposit", "escrow", "release",
             "refund", "default_resolution", "outcome_attestation",
             "bond_resolution", "derivation", "covenant"]
    fields = ["key", "account", "payer", "payee", "escrow_id",
              "attestation_id", "lease_id", "node", "amount_ucr",
              "amount_mbits", "bond_ucr", "seq", "tick", "issuer",
              "charge_ids", "attestation_ids", "consumed", "derived",
              "hop_capacity_mbits", "charge_keys", "default_on_expiry",
              "direction", "claim", "lane", "independence", "charge_seq",
              "lease_seq", "expires_tick",
              # round 2: the first cut omitted these — reason_class was
              # exactly the field carrying a live crash (fable review)
              "reason_class", "accepted", "channel", "required_clean",
              "outcome", "attestor", "submitter", "debit_mbits",
              "demand_mbits", "estimate_total_mbits"]
    for _ in range(8000):
        led = Ledger()
        for _ in range(rng.randint(1, 3)):
            p = {"kind": rng.choice(kinds)}
            for f in rng.sample(fields, rng.randint(1, 7)):
                p[f] = rng.choice(junk)
            try:
                _forge(led, p)
            except Exception:
                pass
        led.audit_codes()
        led.substrate_codes()
        led.provenance_codes()
        audit_settlement_codes(led)
        lhs, rhs = conservation_identity(led)
        assert lhs == rhs


# ---- round 2 (fable review of the fixes themselves, 2026-07-06) ----
# The reviewer of the F1/F2 fix commits convicted the F2 class STILL OPEN
# through two wire-reachable sites the first lane missed, because (a) the
# junk fuzz omitted reason_class from its field list and (b) junk-only
# soups never exercise the resolved-escrow/release paths. Both pinned
# here, plus the skeleton-mutation fuzz that finds this class by
# construction.

def test_r2_unhashable_reason_class_never_crashes_the_court() -> None:
    """ledger's _CHARGE_REASONS was a SET, so `reason not in SET` HASHED
    the forged value: one wire charge with reason_class {} crashed
    audit_codes() and everything joined to the court stream. Tuple
    membership is total; verdict bytes identical (I6 still convicts)."""
    for bad in ({}, [], [1], {"a": 1}, [["x"]]):
        led = Ledger.from_jsonl(canonical_json(
            {"kind": "charge", "reason_class": bad}) + "\n")
        codes = led.audit_codes()
        assert any(c.startswith("I6") for c in codes), (bad, codes)
        audit_settlement_codes(led)  # joined surfaces return too


def test_r2_nested_list_key_never_crashes_settlement_audit() -> None:
    """settlement's lease_key/charge_key maps gated only isinstance(list),
    admitting nested-list keys as tuple-containing-list values whose set
    membership raised in _touches — one forged lease crashed
    audit_settlement_codes for any artifact with a release. Now the maps
    go through _hashable_key and the malformed event stays convicted."""
    for junk_key in ([["x"]], [None], [1], [["a"], "b"]):
        led = Ledger()
        _forge(led, {"kind": "deposit", "account": "a", "amount_ucr": 1000,
                     "issuer": "b", "seq": 1, "tick": 0})
        e = _forge(led, {"kind": "escrow", "payer": "a", "payee": "w",
                         "amount_ucr": 500, "charge_keys": [["exp", "s", "r"]],
                         "required_clean": True, "expires_tick": 100,
                         "default_on_expiry": "refund_to_payer",
                         "issuer": "b", "seq": 2, "tick": 1})
        _forge(led, {"kind": "lease", "key": junk_key, "node": "n",
                     "lease_seq": 1, "amount_mbits": 10, "issuer": "i",
                     "expires_tick": 9})
        _forge(led, {"kind": "charge", "key": junk_key, "lease_id": "L",
                     "node": "n", "charge_seq": 1, "tick": 1})
        _forge(led, {"kind": "release", "escrow_id": e, "amount_ucr": 100,
                     "charge_ids": ["sha256:" + "0" * 64], "issuer": "b",
                     "seq": 1, "tick": 2})
        codes = audit_settlement_codes(led)
        assert codes, junk_key  # returns AND convicts
        lhs, rhs = conservation_identity(led)
        assert lhs == rhs


def test_r2_live_release_refuses_nested_key_receipt() -> None:
    """The LIVE issuer path: paying against a forged charge whose key is
    a nested list must raise SettlementRefused (the contract), never
    TypeError. Crashed at the `tuple(ch.get('key')) not in key_set`
    membership before the fix."""
    import pytest
    from chambers.kernel.settlement import SettlementRefused
    led = Ledger()
    bank = SettlementIssuer(issuer="bank", ledger=led)
    bank.deposit("p", 10_000, tick=0)
    esc = bank.escrow(payer="p", payee="w", amount_ucr=5_000,
                      charge_keys=[KEY], expires_tick=100, tick=1)
    forged = _forge(led, {"kind": "charge", "key": [["x"]], "accepted": True,
                          "lease_id": "L", "node": "n", "charge_seq": 1,
                          "tick": 1})
    with pytest.raises(SettlementRefused):
        bank.release(esc, 1_000, [forged], tick=2)


def test_r2_unparseable_register_key_convicts_i7() -> None:
    """A register whose key cannot parse forms no account — and is
    CONVICTED (I7, subject = canonical JSON of the raw key), not
    silently neutralized. The first F2 fix dropped it without a finding,
    contradicting _hashable_key's own docstring."""
    for junk_key, subj in [([["a"]], '[["a"]]'), (5, "5"), (None, "null")]:
        led = Ledger()
        p = {"kind": "register", "key": junk_key,
             "subject_entropy_mbits": 100, "ceiling_mbits": 50, "issuer": "i"}
        if junk_key is None:
            del p["key"]
        _forge(led, p)
        assert f"I7 {subj}" in led.audit_codes(), junk_key


def test_r2_skeleton_mutation_fuzz_totality() -> None:
    """The structural upgrade over junk-only soups: build a COHERENT
    meter/escrow/outcome/bond/covenant scenario through the real front
    ends, then (a) mutate every field of every event through the junk
    pool and (b) inject junk events (with real cross-referenced ids)
    around the intact skeleton. Junk-only fuzz can never reach the
    resolved-escrow audit paths where round 2's crashes lived; this
    reaches them by construction. Every total surface must return and
    conservation must hold on every probe. (The review sweep ran 8,103
    probes: 0 crashes, 0 conservation breaks; this is the standing
    floor.)"""
    from chambers.kernel.accountant import CapacityEstimate
    from chambers.kernel.covenant import declare_covenant
    from chambers.kernel.settlement import resolve_bond, resolve_default

    def build_skeleton() -> Ledger:
        led = Ledger()
        m = KernelMeter(node="n1", issuer="c", ledger=led)
        m.register(KEY, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
        _dec, ch_id = m.charge_recorded(
            KEY, CapacityEstimate(10_000, 0, 0, 0, 0, "c"), TOR, tick=1)
        bank = SettlementIssuer(issuer="bank", ledger=led)
        bank.deposit("payerP", 500_000, tick=0)
        bank.deposit("arbiterA", 20_000, tick=0)
        bank.deposit("platformX", 20_000, tick=0)
        esc1 = bank.escrow(payer="payerP", payee="workerW", amount_ucr=30_000,
                           charge_keys=[KEY], expires_tick=100, tick=2)
        bank.release(esc1, 10_000, [ch_id], tick=3)
        bank.refund(esc1, 5_000, tick=4)
        cond = OutcomeCondition("m", "attested", 1, "role_separated", 5_000, 10)
        esc2 = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                           charge_keys=[KEY], expires_tick=90, tick=5,
                           outcome=cond)
        att = attest_outcome(led, esc2, "arbiterA", "occurred", "attested",
                             "role_separated", 5_000, tick=20)
        bank.release(esc2, 20_000, [ch_id], tick=40, attestation_ids=[att.id])
        resolve_bond(led, att, "anyone", "return_to_attestor", 5_000, tick=95)
        resolve_default(led, esc2, "workerW", 10_000, tick=95,
                        charge_ids=[ch_id], attestation_ids=[att.id])
        declare_covenant(led, "c", KEY, "cap_lease_total", tick=6,
                         cap_mbits=50_000)
        return led

    def run_all(led: Ledger) -> None:
        led.audit_codes()
        led.substrate_codes()
        led.provenance_codes()
        audit_settlement_codes(led)
        lhs, rhs = conservation_identity(led)
        assert lhs == rhs, (lhs, rhs)

    skel = build_skeleton()
    run_all(skel)  # baseline green
    base_events = list(getattr(skel, "_events").items())

    junk = [None, True, 5, -3, 10 ** 18, [], {}, [1], [["a"]], [None],
            {"a": 1}, "x", "sha256:" + "0" * 64, 1.5]

    # (a) every field of every skeleton event, through the whole junk pool
    for eid, payload in base_events:
        for field in list(payload.keys()):
            for j in junk:
                led = Ledger()
                for e2, p2 in base_events:
                    if e2 != eid:
                        led._add_payload(e2, dict(p2))
                mut = dict(payload)
                mut[field] = j
                try:
                    _forge(led, mut)
                except Exception:
                    continue  # refused at the door (event_id) — not a soup
                run_all(led)

    # (b) junk events (junk INCLUDING real ids) injected into the skeleton
    rng = random.Random(11)
    kinds = ["register", "lease", "charge", "deposit", "escrow", "release",
             "refund", "default_resolution", "outcome_attestation",
             "bond_resolution", "derivation", "covenant", "zzz_unknown"]
    flds = ["key", "account", "payer", "payee", "escrow_id", "attestation_id",
            "lease_id", "node", "amount_ucr", "amount_mbits", "bond_ucr",
            "seq", "tick", "issuer", "charge_ids", "attestation_ids",
            "charge_keys", "default_on_expiry", "direction", "claim", "lane",
            "charge_seq", "lease_seq", "expires_tick", "required_clean",
            "outcome", "attestor", "submitter", "reason_class", "accepted",
            "channel", "debit_mbits", "demand_mbits", "estimate_total_mbits"]
    junk_plus = junk + [eid for eid, _ in base_events]
    for _ in range(800):
        led = Ledger()
        for e2, p2 in base_events:
            led._add_payload(e2, dict(p2))
        for _ in range(rng.randint(1, 4)):
            p = {"kind": rng.choice(kinds)}
            for f in rng.sample(flds, rng.randint(1, 8)):
                p[f] = rng.choice(junk_plus)
            try:
                _forge(led, p)
            except Exception:
                pass
        run_all(led)


# ---- F3 — the slash de-escalation is the documented referent-arrival face ----

def _outcome_stage():
    led = Ledger()
    m = KernelMeter(node="n1", issuer="c", ledger=led)
    m.register(KEY, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    m.charge(KEY, CapacityEstimate(10_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    bank = SettlementIssuer(issuer="bank", ledger=led)
    bank.deposit("payerP", 500_000, tick=0)
    bank.deposit("arbiterA", 20_000, tick=0)
    bank.deposit("platformX", 20_000, tick=0)
    cond = OutcomeCondition("m", "attested", 1, "role_separated", 5_000, 10)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY], expires_tick=100, tick=2, outcome=cond)
    return led, bank, esc


def test_f3_slash_conviction_lifts_only_when_the_override_referent_arrives() -> None:
    """SPEC §11: a `slash-without-override` conviction lifts when the
    qualifying strict override merges — the SAME monotonicity face as S3's
    missing receipt arriving (a referenced lack cured), not a violation.
    Pinned as characterization so the property is intentional, and so the
    non-oscillation guarantee (grow-only + top-lane) cannot silently
    change: once the top-lane override is present the slash stays clean."""
    led, bank, esc = _outcome_stage()
    att = attest_outcome(led, esc, "arbiterA", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    sid = _forge(led, {"kind": "bond_resolution", "attestation_id": att.id,
                       "amount_ucr": 5_000, "direction": "slash",
                       "submitter": "payerP", "seq": 1, "tick": 40})
    # before the override: convicted for lacking its justifying evidence
    assert f"S10 {sid}" in audit_settlement_codes(led)
    # the override (the referent) arrives → the lack is cured
    attest_outcome(led, esc, "platformX", "not_occurred", "platform_log",
                   "role_separated", 5_000, tick=25)
    assert f"S10 {sid}" not in audit_settlement_codes(led)
    # non-oscillation: adding MORE facts never re-introduces the S10 (the
    # top-lane override is grow-only and unbeatable)
    attest_outcome(led, esc, "arbiterA", "not_occurred", "attested",
                   "role_separated", 5_000, tick=26)
    assert f"S10 {sid}" not in audit_settlement_codes(led)
    lhs, rhs = conservation_identity(led)
    assert lhs == rhs


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"review regressions: {len(fns)} tests green")
