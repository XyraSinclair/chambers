"""charge-substrate/1 (X0) as a standing lane — KERNEL-SPEC Part II; E6.

The law: two events with different ids claiming the same
(actor, kind, seq) are an equivocation, WHATEVER their kind — including
kinds this auditor has never heard of. I8 and S5 become instances;
future layers inherit fact identity at genesis. The load-bearing test
here is the unknown-kind one: an event family invented after this code
was written is already covered.

Run: python3 chambers/kernel/test_substrate_x0.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from events import canonical_json, event_id  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402
from settlement import SettlementIssuer, audit_settlement_codes  # noqa: E402

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
KEY = ("exp", "srcA", "readerR")


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def test_unknown_future_kind_gets_equivocation_detection_for_free() -> None:
    """THE point of X0: a kind invented after this auditor was written
    (here: a fictional issuer covenant) is covered the moment it carries
    (author, seq). No new audit arm, no relearned lesson."""
    ledger = Ledger()
    for residue in ("none", "everything"):  # same (issuer, kind, seq), different bytes
        _forge(ledger, {"kind": "covenant", "issuer": "houseH", "seq": 4,
                        "tick": 1, "residue": residue})
    codes = ledger.substrate_codes()
    subject = canonical_json(["houseH", "covenant", 4])
    assert codes == [f"X0 {subject}"], codes
    # and the LAYER audits, which know nothing of covenants, stay silent
    assert ledger.audit_codes() == []
    assert audit_settlement_codes(ledger) == []


def test_x0_covers_settlement_kinds_alongside_s5() -> None:
    """On existing kinds the X0 actor coincides with the layer code's
    authoring field: an S5 settlement equivocation is an X0 finding with
    the SAME subject — instance, not divergence."""
    ledger = Ledger()
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 10_000, tick=0)
    for amount in (1, 2):  # two deposits claim (bank, deposit, seq=7)
        _forge(ledger, {"kind": "deposit", "account": "x", "amount_ucr": amount,
                        "issuer": "bank", "seq": 7, "tick": 1})
    subject = canonical_json(["bank", "deposit", 7])
    assert f"X0 {subject}" in ledger.substrate_codes()
    assert f"S5 {subject}" in audit_settlement_codes(ledger)
    # submitter- and attestor-authored kinds resolve their actor correctly
    for amt in (1, 2):
        _forge(ledger, {"kind": "bond_resolution", "attestation_id": "sha256:" + "9" * 64,
                        "amount_ucr": amt, "direction": "slash",
                        "submitter": "subS", "seq": 3, "tick": 2})
    for bond in (5, 6):
        _forge(ledger, {"kind": "outcome_attestation", "escrow_id": "sha256:" + "8" * 64,
                        "claim": "occurred", "lane": "attested",
                        "independence": "role_separated", "evidence": "",
                        "bond_ucr": bond, "attestor": "attA", "seq": 2, "tick": 3})
    codes = ledger.substrate_codes()
    assert f"X0 {canonical_json(['subS', 'bond_resolution', 3])}" in codes
    assert f"X0 {canonical_json(['attA', 'outcome_attestation', 2])}" in codes


def test_pure_information_artifacts_have_no_x0_surface() -> None:
    """charge events carry charge_seq, not seq (I8 owns their identity);
    register carries no seq (I7 owns conflicts); leases carry lease_seq.
    A pure information-layer artifact has an empty X0 verdict — which is
    also why the frozen information corpus cannot be disturbed."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="chambers", ledger=ledger)
    meter.register(KEY, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(KEY, CapacityEstimate(1_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    meter.charge(KEY, CapacityEstimate(1_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    assert ledger.substrate_codes() == []
    assert ledger.audit_codes() == []


def test_same_bytes_are_one_fact_not_an_equivocation() -> None:
    """Union-by-id: replaying identical bytes is the same fact; X0 fires
    only on DIFFERENT ids claiming one (actor, kind, seq)."""
    ledger = Ledger()
    p = {"kind": "covenant", "issuer": "houseH", "seq": 1, "tick": 1, "residue": "none"}
    _forge(ledger, dict(p))
    _forge(ledger, dict(p))  # no-op by id
    assert ledger.substrate_codes() == []
    assert ledger.event_count() == 1


def test_authoring_priority_is_deterministic() -> None:
    """A (hypothetical) kind carrying BOTH issuer and submitter resolves
    its actor by the declared priority: issuer wins. Two events agreeing
    on issuer but differing on submitter still equivocate."""
    ledger = Ledger()
    for sub in ("s1", "s2"):
        _forge(ledger, {"kind": "weird", "issuer": "I", "submitter": sub,
                        "seq": 9, "tick": 1})
    subject = canonical_json(["I", "weird", 9])
    assert ledger.substrate_codes() == [f"X0 {subject}"]


def test_malformed_seq_or_actor_is_exempt_not_crashing() -> None:
    """Total over adversarial content: non-uint seq, non-string authors,
    and missing fields contribute nothing and crash nothing."""
    ledger = Ledger()
    for junk in (
        {"kind": "covenant", "issuer": "h", "seq": -1, "tick": 1},
        {"kind": "covenant", "issuer": "h", "seq": "one", "tick": 1},
        {"kind": "covenant", "issuer": 7, "seq": 1, "tick": 1},
        {"kind": 5, "issuer": "h", "seq": 1, "tick": 1},
        {"kind": "covenant", "seq": 1, "tick": 1},
    ):
        _forge(ledger, junk)
    assert ledger.substrate_codes() == []


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"charge-substrate/1 (X0): {len(fns)} tests green")
