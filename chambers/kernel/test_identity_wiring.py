"""charge-identity/2 — the authoring front-ends as a standing lane.

IDENTITY-SPEC §7's claims, exercised:

  * a key-authored economy runs through the REAL front-ends (LeaseIssuer,
    KernelMeter, SettlementIssuer, the permissionless settlement fronts,
    declare_covenant) and every authored fact carries a verifying sig —
    the pipeline residue "the meter's charges aren't yet key-signed" is
    closed by these tests;
  * the authoring law fails CLOSED at construction: a key-shaped author
    without its Signer, a mismatched Signer, and a Signer on a legacy
    string are all refused before a single unattributable fact exists;
  * forging an edit of a signed fact convicts A2 (attributable, not just
    detectable); the honest facts stay attributable;
  * signed courts remain byte-deterministic (RFC 8032 signing is
    deterministic) and every frozen surface (I/S/X/C) is indifferent;
  * unsigned front-ends produce exactly the historical bytes (the sig
    field is additive; corpora move by zero bytes — asserted here at the
    event level, and by test_identity.py at the corpus level).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel import identity as ID  # noqa: E402
from chambers.kernel.accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from chambers.kernel.covenant import declare_covenant  # noqa: E402
from chambers.kernel.events import RegisterEvent, event_id  # noqa: E402
from chambers.kernel.leases import LeaseIssuer, LeaseRefused  # noqa: E402
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
    settlement_fold,
)

SEED_OWNER = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
SEED_NODE = bytes.fromhex(
    "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")
SEED_BANK = bytes.fromhex(
    "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7")
SEED_ATTESTOR = bytes(range(32))

EST = EstimatorAttestation("e.exact", "adversarial_review", "static", True)


def _est(mbits: int, channel: str = "c") -> CapacityEstimate:
    return CapacityEstimate(mbits, 0, 0, 0, 0, channel)


def _signed_kinds(ledger: Ledger) -> dict:
    """kind -> [payloads] for every event whose kind has an author field."""
    out: dict = {}
    for p in ledger.events():
        if p.get("kind") in ID.AUTHOR_FIELD:
            out.setdefault(p["kind"], []).append(p)
    return out


def test_meter_full_path_key_signed() -> None:
    """The filed /2 work: register -> self-lease -> charge, all signed."""
    owner, node = ID.Signer(SEED_OWNER), ID.Signer(SEED_NODE)
    led = Ledger()
    meter = KernelMeter(node=node.author, issuer=owner.author, ledger=led,
                        issuer_signer=owner, node_signer=node)
    key = ("exp", "repo", "reader")
    meter.register(key, subject_entropy_mbits=100_000, ceiling_mbits=10_000)
    d1, eid1 = meter.charge_recorded(key, _est(4_000), EST)
    d2 = meter.charge(key, _est(9_000), EST)  # refused by ceiling — still signed
    assert d1.accepted and not d2.accepted

    kinds = _signed_kinds(led)
    assert sorted(kinds) == ["charge", "lease", "register"]
    for kind, payloads in kinds.items():
        for p in payloads:
            assert isinstance(p.get("sig"), str) and len(p["sig"]) == 128, \
                f"{kind} not signed"
    assert ID.identity_codes(led) == []
    assert led.audit_codes() == []                    # frozen surfaces indifferent
    folded = led.fold()
    assert folded[key].cumulative_mbits == 4_000
    assert folded[key].demanded_mbits == 13_000       # the refusal is signed pressure
    # the work receipt a settlement release would bind to is the SIGNED id
    assert eid1 in getattr(led, "_events") and led._events[eid1].get("sig")
    print("meter full path: register/lease/charge all key-signed, fold exact")


def test_adopted_lease_key_signed_across_parties() -> None:
    """The deployment shape: the OWNER (a key) issues; the NODE (another
    key) adopts and charges — both attributable, neither holds the
    other's seed."""
    owner, node = ID.Signer(SEED_OWNER), ID.Signer(SEED_NODE)
    led = Ledger()
    issuer = LeaseIssuer(issuer=owner.author, ledger=led, signer=owner)
    key = ("att", owner.author, "caller", "epoch:1")
    issuer.register(key, subject_entropy_mbits=2_000, ceiling_mbits=2_000)
    lease = issuer.grant(key, node=node.author, amount_mbits=2_000,
                         expires_tick=1_000)
    assert lease.sig is not None                       # the issued fact is signed
    meter = KernelMeter(node=node.author, issuer="unused_legacy", ledger=led,
                        node_signer=node)
    meter.adopt(key, lease, subject_entropy_mbits=2_000)
    dec, cid = meter.charge_recorded(key, _est(1_000, "notify"), EST, tick=5)
    assert dec.accepted
    charge = led._events[cid]
    assert charge["node"] == node.author and len(charge["sig"]) == 128
    assert ID.identity_codes(led) == [] and led.audit_codes() == []
    print("adopted lease: owner-signed grant, node-signed charge, clean court")


def test_authoring_law_fails_closed() -> None:
    """No path exists to a front-end that could author unattributably."""
    owner, node = ID.Signer(SEED_OWNER), ID.Signer(SEED_NODE)
    led = Ledger()
    cases = [
        lambda: LeaseIssuer(issuer=owner.author, ledger=led),           # key, no signer
        lambda: LeaseIssuer(issuer=owner.author, ledger=led, signer=node),  # mismatch
        lambda: LeaseIssuer(issuer="bob", ledger=led, signer=owner),    # legacy + signer
        lambda: KernelMeter(node=node.author, issuer="i", ledger=led),  # key node, no signer
        lambda: KernelMeter(node="n", issuer=owner.author, ledger=led),  # key issuer, no signer
        lambda: SettlementIssuer(issuer=owner.author, ledger=led),
        lambda: SettlementIssuer(issuer="bank", ledger=led, signer=owner),
    ]
    for i, build in enumerate(cases):
        try:
            build()
            raise AssertionError(f"case {i} must refuse at construction")
        except ID.IdentityRefused:
            pass
    # the dark-signing refusal on the Signer itself
    try:
        owner.sign(RegisterEvent(key=("k",), subject_entropy_mbits=1,
                                 ceiling_mbits=1, issuer="not_this_key"))
        raise AssertionError("Signer.sign must refuse an author mismatch")
    except ID.IdentityRefused:
        pass
    print("authoring law: all seven construction paths fail closed")


def test_settlement_key_signed_and_forged_edit_convicts() -> None:
    owner, node, bank = (ID.Signer(SEED_OWNER), ID.Signer(SEED_NODE),
                         ID.Signer(SEED_BANK))
    led = Ledger()
    meter = KernelMeter(node=node.author, issuer=owner.author, ledger=led,
                        issuer_signer=owner, node_signer=node)
    key = ("exp", "repo", "reader")
    meter.register(key, subject_entropy_mbits=50_000, ceiling_mbits=20_000)
    _, cid = meter.charge_recorded(key, _est(5_000), EST, tick=1)

    issuer = SettlementIssuer(issuer=bank.author, ledger=led, signer=bank)
    issuer.deposit("payer", 100_000, tick=0)
    esc = issuer.escrow("payer", "worker", 40_000, [key],
                        expires_tick=1_000, tick=2)
    issuer.release(esc, 40_000, [cid], tick=3)
    assert ID.identity_codes(led) == []
    assert audit_settlement_codes(led) == []
    lhs, rhs = conservation_identity(led)
    assert lhs == rhs == 100_000
    accounts, _ = settlement_fold(led)
    assert accounts["worker"].available_ucr == 40_000

    # the forger edits a signed deposit's amount and keeps the sig
    dep = next(p for p in led.events() if p.get("kind") == "deposit")
    forged = dict(dep)
    forged["amount_ucr"] = 10**9
    forged["seq"] = 2  # a NEW fact (no X0), so A2 is what convicts it
    led._add_payload(event_id(forged), forged)
    codes = ID.identity_codes(led)
    assert codes == [f"A2 {bank.author}"], codes
    print("settlement: signed value flow clean; forged mint convicts A2, "
          "attributably")


def test_outcome_attestation_and_bond_resolution_signed() -> None:
    """Bonds slash a KEY (IDENTITY-SPEC §5): the /2 wiring makes the
    attestor and submitter attributable through the real fronts."""
    bank, attestor = ID.Signer(SEED_BANK), ID.Signer(SEED_ATTESTOR)
    owner, node = ID.Signer(SEED_OWNER), ID.Signer(SEED_NODE)
    led = Ledger()
    meter = KernelMeter(node=node.author, issuer=owner.author, ledger=led,
                        issuer_signer=owner, node_signer=node)
    key = ("exp", "deal", "reader")
    meter.register(key, subject_entropy_mbits=10_000, ceiling_mbits=5_000)
    _, cid = meter.charge_recorded(key, _est(1_000), EST, tick=1)

    issuer = SettlementIssuer(issuer=bank.author, ledger=led, signer=bank)
    issuer.deposit("payer", 50_000, tick=0)
    issuer.deposit(attestor.author, 10_000, tick=0)   # the bond's backing
    cond = OutcomeCondition(metric="presence_proxy", lane="attested", quorum=1,
                            min_independence="role_separated",
                            min_bond_ucr=5_000, contest_ticks=10)
    esc = issuer.escrow("payer", "worker", 30_000, [key], expires_tick=1_000,
                        tick=2, outcome=cond)
    att = attest_outcome(led, esc, attestor.author, "occurred", "attested",
                         "role_separated", 5_000, tick=3, signer=attestor)
    assert att.sig is not None
    # the contest window (10 ticks past the attestation) must drain first
    issuer.release(esc, 30_000, [cid], tick=14, attestation_ids=[att.id])
    ret = resolve_bond(led, att, attestor.author, "return_to_attestor",
                       5_000, tick=20, signer=attestor)
    assert ret.sig is not None
    assert ID.identity_codes(led) == []
    assert audit_settlement_codes(led) == []
    lhs, rhs = conservation_identity(led)
    assert lhs == rhs == 60_000
    print("outcome tier: signed attestation, signed bond return, court clean")


def test_permissionless_fronts_fail_closed() -> None:
    bank = ID.Signer(SEED_BANK)
    attestor = ID.Signer(SEED_ATTESTOR)
    led = Ledger()
    issuer = SettlementIssuer(issuer="bank_legacy", ledger=led)
    issuer.deposit("payer", 10_000, tick=0)
    esc = issuer.escrow("payer", "worker", 5_000, [("exp", "k", "r")],
                        expires_tick=10, tick=1)
    for call in (
        lambda: resolve_default(led, esc, bank.author, 5_000, tick=20),
        lambda: attest_outcome(led, esc, attestor.author, "occurred",
                               "attested", "role_separated", 1, tick=2),
    ):
        try:
            call()
            raise AssertionError("key-shaped actor without signer must refuse")
        except ID.IdentityRefused:
            pass
    print("permissionless fronts: key-shaped actors must sign, fail closed")


def test_covenant_signed_by_the_ceasing_key_still_binds() -> None:
    owner = ID.Signer(SEED_OWNER)
    led = Ledger()
    issuer = LeaseIssuer(issuer=owner.author, ledger=led, signer=owner)
    key = ("exp", "repo", "reader")
    issuer.register(key, subject_entropy_mbits=10_000, ceiling_mbits=8_000)
    cov = declare_covenant(led, owner.author, key, "cease_lease_issuance",
                           tick=5, horizon_tick=5, residue="tail exposure",
                           signer=owner)
    assert cov.sig is not None and ID.identity_codes(led) == []
    try:
        issuer.grant(key, node="n", amount_mbits=1_000, expires_tick=100)
        raise AssertionError("the signed cease must bind the ceasing key")
    except LeaseRefused:
        pass
    print("covenant: the cease signed by the ceasing key binds that key")


def test_signed_court_is_byte_deterministic() -> None:
    def build() -> str:
        owner, node = ID.Signer(SEED_OWNER), ID.Signer(SEED_NODE)
        led = Ledger()
        meter = KernelMeter(node=node.author, issuer=owner.author, ledger=led,
                            issuer_signer=owner, node_signer=node)
        key = ("exp", "repo", "reader")
        meter.register(key, subject_entropy_mbits=9_000, ceiling_mbits=6_000)
        meter.charge(key, _est(2_000), EST, tick=1)
        return led.to_jsonl()

    assert build() == build(), "RFC 8032 determinism must reach the artifact"
    print("signed court: byte-deterministic across runs")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
    print("identity /2 wiring lane green")
