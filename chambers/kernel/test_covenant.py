"""charge-covenant/1 as a standing lane (COVENANT-SPEC.md; E5).

The exit story, mechanized. Families:
  1. BOB LEAVES — the full revocation decomposition: tenor (old lease
     drains), covenant (no authority beyond the horizon; the honest
     issuer refuses its own future grants; a forged grant convicts C1),
     residue (declared, carried in the artifact). Past receipts stand.
  2. VALUE FAILS CLOSED — a release against covenant-broken authority is
     refused live and convicted after merge (C1 joins the dirty-court
     stream through the same fail-closed 'touches' law as unknown
     I-codes); refunds stay safe.
  3. ONE-WAY — covenants only tighten (minimum horizon/cap binds);
     merge/shuffle invariant; X0 covers covenant equivocation with no
     code written here.
  4. TOTALITY — malformed covenants convict C3 and crash nothing;
     overpromises are refused live.

Run: python3 chambers/kernel/test_covenant.py
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from chambers.kernel.covenant import (  # noqa: E402
    CovenantRefused,
    covenant_codes,
    declare_covenant,
)
from chambers.kernel.events import canonical_json, event_id  # noqa: E402
from chambers.kernel.leases import LeaseIssuer, LeaseRefused  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.meter import KernelMeter  # noqa: E402
from chambers.kernel.settlement import (  # noqa: E402
    SettlementIssuer,
    SettlementRefused,
    audit_settlement_codes,
    conservation_identity,
)

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
BOB = ("exp", "srcBob", "readerR")
OTHER = ("exp", "srcOther", "readerR")


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _shuffle_invariant(ledger: Ledger) -> None:
    codes = covenant_codes(ledger)
    lines = ledger.to_jsonl().strip().splitlines()
    rng = random.Random(11)
    for _ in range(3):
        rng.shuffle(lines)
        re = Ledger.from_jsonl("\n".join(lines) + "\n")
        assert covenant_codes(re) == codes


def test_bob_leaves_the_full_exit_story() -> None:
    ledger = Ledger()
    lessor = LeaseIssuer(issuer="bobChamber", ledger=ledger)
    lessor.register(BOB, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    lease = lessor.grant(BOB, "node1", 10_000, expires_tick=30)
    # metered work happens under live authority
    meter = KernelMeter(node="node1", issuer="bobChamber", ledger=ledger)
    # (meter self-registers its own lease path; use the lessor's lease via
    # a plain charge through a second meter is out of scope — the point
    # here is authority, so charge through the meter's own path)
    meter.register(OTHER, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(OTHER, CapacityEstimate(1_000, 0, 0, 0, 0, "c"), TOR, tick=1)

    # Bob leaves: the chamber binds its own hands, with the residue named
    cov = declare_covenant(
        ledger, "bobChamber", BOB, "cease_lease_issuance", tick=5,
        horizon_tick=30,
        residue="readerR retains everything already emitted; widening is one-way",
    )
    assert cov.horizon_tick == 30
    assert covenant_codes(ledger) == []          # nothing violated
    # the honest issuer now refuses its own future authority
    try:
        lessor.grant(BOB, "node2", 1_000, expires_tick=60)
        raise AssertionError("granted past own covenant")
    except LeaseRefused as exc:
        assert "covenant" in str(exc)
    # a grant that drains BY the horizon is still fine (tenor does the rest)
    lessor.grant(BOB, "node2", 1_000, expires_tick=30)
    assert covenant_codes(ledger) == []
    # a FORGED post-horizon lease convicts
    forged = _forge(ledger, {
        "kind": "lease", "key": list(BOB), "lease_seq": 99, "node": "nodeEvil",
        "amount_mbits": 1_000, "issuer": "bobChamber", "expires_tick": 999})
    codes = covenant_codes(ledger)
    assert codes == [f"C1 {forged}"], codes
    # past receipts stand: the information audit is unchanged by covenants
    assert ledger.audit_codes() == []
    _shuffle_invariant(ledger)
    print("Bob leaves: tenor drains, covenant refuses, forgery convicts, receipts stand")


def test_cap_covenant_is_wind_down() -> None:
    """cap_mbits caps NON-GRANDFATHERED (i.e. new) authority; cap 0 is
    the wind-down: history survives by name, nothing new ever issues.
    A small non-zero cap is a declared allowance for future authority."""
    ledger = Ledger()
    lessor = LeaseIssuer(issuer="chamber", ledger=ledger)
    lessor.register(BOB, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    old = lessor.grant(BOB, "node1", 10_000, expires_tick=30)
    cov = declare_covenant(ledger, "chamber", BOB, "cap_lease_total", tick=5,
                           cap_mbits=0, residue="no new authority")
    assert cov.except_lease_ids == (old.id,)  # history named, surviving
    assert covenant_codes(ledger) == []
    try:
        lessor.grant(BOB, "node1", 1, expires_tick=30)
        raise AssertionError("granted past own cap")
    except LeaseRefused:
        pass
    forged = _forge(ledger, {
        "kind": "lease", "key": list(BOB), "lease_seq": 98, "node": "nodeEvil",
        "amount_mbits": 5_000, "issuer": "chamber", "expires_tick": 30})
    codes = covenant_codes(ledger)
    assert codes == [f"C2 {canonical_json(list(BOB))}"], codes
    # a declared allowance: cap 6_000 tolerates the forged 5_000 plus 1_000 more
    declare_covenant(ledger, "chamber", BOB, "cap_lease_total", tick=6,
                     cap_mbits=6_000, residue="allowance",
                     except_lease_ids=[old.id])
    # the STRICTER covenant (cap 0) still binds: C2 stands (one-way law)
    assert f"C2 {canonical_json(list(BOB))}" in covenant_codes(ledger)
    _shuffle_invariant(ledger)


def test_value_fails_closed_on_covenant_broken_authority() -> None:
    """A release whose escrow binds to a key with a C1 conviction is
    refused live and convicted after merge (S4); the refund path stays
    safe — the exit never strands money."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="bobChamber", ledger=ledger)
    meter.register(BOB, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(BOB, CapacityEstimate(1_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    charge_id = next(e for e, p in getattr(ledger, "_events").items()
                     if p.get("kind") == "charge" and p.get("accepted") is True)
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 100_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=10_000,
                      charge_keys=[BOB], expires_tick=100, tick=2)
    # clean court: release works
    bank.release(esc, 1_000, [charge_id], tick=3)
    # covenant + forged violating lease dirty the court on BOB's key
    declare_covenant(ledger, "bobChamber", BOB, "cease_lease_issuance",
                     tick=5, horizon_tick=100, residue="r")
    _forge(ledger, {
        "kind": "lease", "key": list(BOB), "lease_seq": 97, "node": "nodeEvil",
        "amount_mbits": 1, "issuer": "bobChamber", "expires_tick": 999})
    try:
        bank.release(esc, 1_000, [charge_id], tick=6)
        raise AssertionError("released against covenant-broken authority")
    except SettlementRefused as exc:
        assert "dirty" in str(exc)
    forged_release = _forge(ledger, {
        "kind": "release", "escrow_id": esc.id, "amount_ucr": 1_000,
        "charge_ids": [charge_id], "issuer": "bank", "seq": 90, "tick": 6})
    s_codes = audit_settlement_codes(ledger)
    assert f"S4 {forged_release}" in s_codes, s_codes
    # the refund path is untouched — exit never strands value
    bank.refund(esc, 8_000, tick=7)
    lhs, rhs = conservation_identity(ledger)
    assert lhs == rhs
    print("value fails closed on covenant-broken authority; refunds stay safe")


def test_covenants_only_tighten() -> None:
    ledger = Ledger()
    lessor = LeaseIssuer(issuer="chamber", ledger=ledger)
    lessor.register(BOB, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    declare_covenant(ledger, "chamber", BOB, "cease_lease_issuance",
                     tick=1, horizon_tick=50, residue="r")
    declare_covenant(ledger, "chamber", BOB, "cease_lease_issuance",
                     tick=2, horizon_tick=80, residue="loosen attempt")
    # the MIN binds: a lease expiring at 60 violates the 50 horizon even
    # though a later covenant said 80
    forged = _forge(ledger, {
        "kind": "lease", "key": list(BOB), "lease_seq": 96, "node": "n",
        "amount_mbits": 1, "issuer": "chamber", "expires_tick": 60})
    assert covenant_codes(ledger) == [f"C1 {forged}"]
    _shuffle_invariant(ledger)


def test_x0_covers_covenant_equivocation_for_free() -> None:
    ledger = Ledger()
    for h in (10, 20):  # same (issuer, covenant, seq), different bytes
        _forge(ledger, {"kind": "covenant", "issuer": "chamber",
                        "key": list(BOB), "action": "cease_lease_issuance",
                        "horizon_tick": h, "residue": "", "seq": 3, "tick": 1})
    subject = canonical_json(["chamber", "covenant", 3])
    assert f"X0 {subject}" in ledger.substrate_codes()
    # and the binding horizon is still the MIN of the two claims
    forged = _forge(ledger, {
        "kind": "lease", "key": list(BOB), "lease_seq": 95, "node": "n",
        "amount_mbits": 1, "issuer": "chamber", "expires_tick": 15})
    assert covenant_codes(ledger) == [f"C1 {forged}"]


def test_grandfathering_names_the_surviving_authority() -> None:
    """A covenant declared mid-life auto-exempts outstanding violators BY
    CONTENT-ADDRESSED ID in its own bytes — the exit statement's
    mechanical twin. The eternal self-lease a KernelMeter holds is the
    hard case: it survives, named; nothing new is ever issued."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="bobChamber", ledger=ledger)
    meter.register(BOB, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(BOB, CapacityEstimate(1_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    self_lease = next(e for e, p in getattr(ledger, "_events").items()
                      if p.get("kind") == "lease")
    cov = declare_covenant(ledger, "bobChamber", BOB, "cease_lease_issuance",
                           tick=5, horizon_tick=10, residue="r")
    assert cov.except_lease_ids == (self_lease,)   # named in the bytes
    assert covenant_codes(ledger) == []            # survives, clean
    # explicit EMPTY exceptions = self-indictment: the audit convicts the
    # history the issuer chose not to grandfather — legitimate, recorded
    declare_covenant(ledger, "bobChamber", BOB, "cease_lease_issuance",
                     tick=6, horizon_tick=10, residue="r",
                     except_lease_ids=[])
    assert covenant_codes(ledger) == [f"C1 {self_lease}"]
    _shuffle_invariant(ledger)


def test_malformed_and_refusals() -> None:
    ledger = Ledger()
    lessor = LeaseIssuer(issuer="chamber", ledger=ledger)
    lessor.register(BOB, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    lessor.grant(BOB, "node1", 10_000, expires_tick=60)
    for kwargs in (
        dict(action="revoke_everything"),                    # unknown action
        dict(action="cease_lease_issuance"),                 # no horizon
        dict(action="cap_lease_total", cap_mbits=-5),        # bad cap
    ):
        try:
            declare_covenant(ledger, "chamber", BOB, tick=5, residue="r", **kwargs)
            raise AssertionError(f"accepted {kwargs}")
        except CovenantRefused:
            pass
    # forged malformed covenants convict C3, crash nothing
    for junk in (
        {"kind": "covenant", "issuer": "chamber", "key": list(BOB),
         "action": "cease_lease_issuance", "residue": "", "seq": 1, "tick": 1},  # no horizon
        {"kind": "covenant", "issuer": "chamber", "key": [],
         "action": "cap_lease_total", "cap_mbits": 5, "residue": "", "seq": 2, "tick": 1},
        {"kind": "covenant", "issuer": 7, "key": list(BOB),
         "action": "cap_lease_total", "cap_mbits": 5, "residue": "", "seq": 3, "tick": 1},
        {"kind": "covenant", "issuer": "chamber", "key": list(BOB),
         "action": "cap_lease_total", "cap_mbits": -5, "residue": "", "seq": 4, "tick": 1},
    ):
        eid = _forge(ledger, junk)
        assert f"C3 {eid}" in covenant_codes(ledger)
    _shuffle_invariant(ledger)


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"charge-covenant/1 lane: {len(fns)} tests green")
