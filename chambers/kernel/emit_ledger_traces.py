"""Emit the golden ledger corpus for charge-ledger/1 (KERNEL-SPEC.md §5).

Deterministic: no randomness, no clocks. Each scenario builds a ledger —
honest ones through the real kernel API, adversarial ones by injecting
forged payloads exactly the way a Byzantine node would — and writes:

    ledger_traces/<name>.ledger.jsonl     the artifact (id-sorted canonical lines)
    ledger_traces/<name>.expected.json    canonical fold + audit codes

The expected values are computed by the Python reference (ledger.py). The
point of the corpus is that a SECOND implementation, written from
KERNEL-SPEC.md alone, reproduces every expected file bit-for-bit.

Run: python3 chambers/kernel/emit_ledger_traces.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from accountant import (  # noqa: E402
    Accountant,
    CapacityEstimate,
    EstimatorAttestation,
    composition_key,
    exposure_key,
)
from events import ChargeEvent, LeaseEvent, RegisterEvent, canonical_json, event_id  # noqa: E402
from leases import LeaseIssuer  # noqa: E402
from ledger import Ledger, fold_canonical  # noqa: E402  (re-exported: test_kernel.py replays through this module)
from meter import KernelMeter  # noqa: E402
from session import MediationSession  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ledger_traces")

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
SELFISH = EstimatorAttestation("selfmeter", "self_interested", "m", True)


def _est(total: int, channel: str = "c") -> CapacityEstimate:
    return CapacityEstimate(total, 0, 0, 0, 0, channel)


def _forge(ledger: Ledger, payload: dict) -> str:
    """Inject a raw payload the way a Byzantine node would."""
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _charge_payload(key, node, lease_id, seq, tick, total, *, accepted=True,
                    reason="EMITTED", detail="emitted_debited", demand=None,
                    debit=None, channel="c") -> dict:
    return {
        "kind": "charge", "key": list(key), "node": node, "lease_id": lease_id,
        "charge_seq": seq, "tick": tick, "channel": channel,
        "estimate_total_mbits": total, "estimator_id": "e",
        "estimator_independence": "adversarial_review", "estimator_worst_case": True,
        "accepted": accepted, "reason_class": reason, "reason_detail": detail,
        "demand_mbits": total if demand is None else demand,
        "debit_mbits": (total if accepted else 0) if debit is None else debit,
    }


# ---- scenarios ----

def s_empty() -> Ledger:
    return Ledger()


def s_honest_single_node() -> Ledger:
    ledger = Ledger()
    m = KernelMeter(node="n1", issuer="ownerA", ledger=ledger)
    key = composition_key("subjectS", "reachability", "cardinal")
    m.register(key, subject_entropy_mbits=512000, ceiling_mbits=120000)
    m.charge(key, CapacityEstimate(1585, 4585, 2000, 64000, 1000, "vex_verdict"), TOR, tick=1)
    m.charge(key, _est(50000, "vex_verdict"), TOR, tick=2)   # would exceed -> REFUSED_CEILING
    m.charge(key, _est(1000, "vex_verdict"), TOR, tick=3)    # blocked
    m.charge(key, _est(1000, "vex_verdict"), SELFISH, tick=4)  # REFUSED_ESTIMATOR
    return ledger


def s_honest_two_node_partition() -> Ledger:
    ledger = Ledger()
    issuer = LeaseIssuer(issuer="chamberA", ledger=ledger)
    key = exposure_key("chamberA", "agentZ")
    issuer.register(key, subject_entropy_mbits=100000, ceiling_mbits=60000)
    l1 = issuer.grant(key, node="n1", amount_mbits=30000, expires_tick=100)
    l2 = issuer.grant(key, node="n2", amount_mbits=30000, expires_tick=100)
    est = _est(10000)
    for node, lease in (("n1", l1), ("n2", l2)):
        acc = Accountant()
        acc.register(key, 100000, lease.amount_mbits)
        for tick in range(4):
            dec = acc.charge(key, est, TOR, tick)
            ledger.add(ChargeEvent.from_decision(key, node, lease.id, tick + 1, tick, est, TOR, dec))
    return ledger


def s_honest_mediation_coupled() -> Ledger:
    ledger = Ledger()
    issuer = LeaseIssuer(issuer="issuerOfRecord", ledger=ledger)
    members = ["chamberA", "chamberB"]
    leases = {}
    for mname in members:
        k = exposure_key(mname, "guestAgent")
        issuer.register(k, 100000, 50000)
        leases[k] = issuer.grant(k, "node1", 50000, 100)
    for mname, budget in (("chamberA", 10000), ("chamberB", 3000)):
        k = exposure_key(mname, "requesterR")
        issuer.register(k, 100000, budget)
        leases[k] = issuer.grant(k, "node1", budget, 100)
    sess = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    sess.observe("chamberA", _est(20000, "read"), TOR, tick=1)
    sess.emit(_est(5000, "judgement"), TOR, tick=2)   # B guilty, A REFUSED_COUPLED
    sess.emit(_est(2000, "judgement"), TOR, tick=3)   # B blocked, A coupled again
    return ledger


def s_forged_overspend() -> Ledger:
    ledger = s_honest_two_node_partition()
    key = exposure_key("chamberA", "agentZ")
    lease_p = next(p for p in ledger.events() if p.get("kind") == "lease" and p["node"] == "n1")
    _forge(ledger, _charge_payload(key, "n1", event_id(lease_p), 99, 50, 999999))
    return ledger


def s_foreign_node_spend() -> Ledger:
    ledger = s_honest_two_node_partition()
    key = exposure_key("chamberA", "agentZ")
    lease_p = next(p for p in ledger.events() if p.get("kind") == "lease" and p["node"] == "n1")
    _forge(ledger, _charge_payload(key, "nEvil", event_id(lease_p), 1, 5, 1000))
    return ledger


def s_expired_lease_charge() -> Ledger:
    ledger = s_honest_two_node_partition()
    key = exposure_key("chamberA", "agentZ")
    lease_p = next(p for p in ledger.events() if p.get("kind") == "lease" and p["node"] == "n2")
    _forge(ledger, _charge_payload(key, "n2", event_id(lease_p), 77, 500, 1000))
    return ledger


def s_unknown_lease_charge() -> Ledger:
    ledger = s_honest_single_node()
    key = composition_key("subjectS", "reachability", "cardinal")
    _forge(ledger, _charge_payload(key, "n1", "sha256:" + "0" * 64, 1, 1, 1000))
    return ledger


def s_lease_key_mismatch() -> Ledger:
    ledger = s_honest_two_node_partition()
    other = exposure_key("chamberB", "agentZ")
    lease_p = next(p for p in ledger.events() if p.get("kind") == "lease" and p["node"] == "n1")
    _forge(ledger, _charge_payload(other, "n1", event_id(lease_p), 5, 5, 1000))
    return ledger


def s_rogue_lease() -> Ledger:
    ledger = s_honest_single_node()
    # lease for an unregistered key AND a lease from a non-issuer for a
    # registered key: two distinct I5 convictions.
    unreg = composition_key("ghost", "q", "a")
    _forge(ledger, {
        "kind": "lease", "key": list(unreg), "lease_seq": 1, "node": "nX",
        "amount_mbits": 5000, "issuer": "nobody", "expires_tick": 10,
    })
    reg = composition_key("subjectS", "reachability", "cardinal")
    _forge(ledger, {
        "kind": "lease", "key": list(reg), "lease_seq": 9, "node": "nX",
        "amount_mbits": 1, "issuer": "impostor", "expires_tick": 10,
    })
    return ledger


def s_malformed_charges() -> Ledger:
    ledger = s_honest_two_node_partition()
    key = exposure_key("chamberA", "agentZ")
    lease_p = next(p for p in ledger.events() if p.get("kind") == "lease" and p["node"] == "n1")
    lid = event_id(lease_p)
    # negative debit (tries to un-spend)
    _forge(ledger, _charge_payload(key, "n1", lid, 50, 6, 10000, debit=-999999))
    # zero/invalid charge_seq
    _forge(ledger, _charge_payload(key, "n1", lid, 0, 7, 100, accepted=False,
                                   reason="REFUSED_BLOCKED", detail="budget_already_blocked"))
    # unknown reason class
    _forge(ledger, _charge_payload(key, "n1", lid, 51, 8, 100, accepted=False,
                                   reason="REFUSED_VIBES", detail="x"))
    # accepted flag disagrees with reason; debit inconsistent with refusal
    _forge(ledger, _charge_payload(key, "n1", lid, 52, 9, 100, accepted=True,
                                   reason="REFUSED_CEILING", detail="would_exceed_ceiling",
                                   debit=100))
    return ledger


def s_registration_poison() -> Ledger:
    ledger = s_honest_two_node_partition()
    key = exposure_key("chamberA", "agentZ")
    ledger.add(RegisterEvent(key, 100000, 50000, "chamberA"))     # conflicting ceiling
    _forge(ledger, {                                              # malformed entropy
        "kind": "register", "key": list(key),
        "subject_entropy_mbits": 0, "ceiling_mbits": 60000, "issuer": "chamberA",
    })
    return ledger


def s_equivocation() -> Ledger:
    ledger = s_honest_two_node_partition()
    key = exposure_key("chamberA", "agentZ")
    lease_p = next(p for p in ledger.events() if p.get("kind") == "lease" and p["node"] == "n2")
    lid = event_id(lease_p)
    _forge(ledger, _charge_payload(key, "n2", lid, 7, 11, 1000))
    _forge(ledger, _charge_payload(key, "n2", lid, 7, 11, 2000))  # same seq, different fact
    return ledger


def s_orphan_facts_only() -> Ledger:
    # charges and leases with NO registration at all: no accounts, only convictions
    ledger = Ledger()
    key = composition_key("phantom", "q", "a")
    lease_payload = {
        "kind": "lease", "key": list(key), "lease_seq": 1, "node": "nX",
        "amount_mbits": 100, "issuer": "nobody", "expires_tick": 5,
    }
    lid = _forge(ledger, lease_payload)
    _forge(ledger, _charge_payload(key, "nX", lid, 1, 9, 50))  # tick past expiry too
    return ledger


def s_spec_ambiguity_issuer() -> Ledger:
    # Pins KERNEL-SPEC §3.1's clarified reading (flagged by the first
    # independent implementation): well-formedness is decided by
    # subject_entropy_mbits + ceiling_mbits ONLY. A register with a
    # non-string issuer, and one with NO issuer field at all, are both
    # well-formed — the account exists (fold shows the field-wise min of
    # both), but issuers(key) is empty, so the honest-looking lease is
    # convicted I5. An implementation that treats either register as
    # malformed produces no account and a different fold.
    ledger = Ledger()
    key = composition_key("subjectP", "reachability", "cardinal")
    _forge(ledger, {
        "kind": "register", "key": list(key),
        "subject_entropy_mbits": 512000, "ceiling_mbits": 90000, "issuer": 7,
    })
    _forge(ledger, {
        "kind": "register", "key": list(key),
        "subject_entropy_mbits": 400000, "ceiling_mbits": 120000,
    })
    _forge(ledger, {
        "kind": "lease", "key": list(key), "lease_seq": 1, "node": "n1",
        "amount_mbits": 50000, "issuer": "ownerA", "expires_tick": 100,
    })
    return ledger


def s_spec_ambiguity_i3_i4() -> Ledger:
    # Pins KERNEL-SPEC §4's clarified I3×I4 interaction (flagged by the
    # first independent implementation): a charge is excluded from a
    # lease's I3 overspend sum ONLY when its lease_id resolves to no lease
    # event. Charges with other I4 findings still count.
    #   lease A (15): clean 10 + node-mismatch 10  -> 20 > 15 -> I3 fires
    #   lease B (15): clean 10 + unresolved-lease_id 1000 -> sum 10 -> no I3
    #   lease C (15): clean 10 + post-expiry 10    -> 20 > 15 -> I3 fires
    ledger = Ledger()
    issuer = LeaseIssuer(issuer="ownerA", ledger=ledger)
    key = composition_key("subjectQ", "reachability", "cardinal")
    issuer.register(key, subject_entropy_mbits=512000, ceiling_mbits=100000)
    la = event_id(issuer.grant(key, node="n1", amount_mbits=15, expires_tick=50).payload())
    lb = event_id(issuer.grant(key, node="n2", amount_mbits=15, expires_tick=50).payload())
    lc = event_id(issuer.grant(key, node="n3", amount_mbits=15, expires_tick=5).payload())
    # lease A: clean charge, then a node-mismatch charge (I4) that still counts
    _forge(ledger, _charge_payload(key, "n1", la, 1, 1, 10))
    _forge(ledger, _charge_payload(key, "nEvil", la, 2, 1, 10))
    # lease B: clean charge, then a charge whose lease_id resolves to nothing
    _forge(ledger, _charge_payload(key, "n2", lb, 1, 1, 10))
    _forge(ledger, _charge_payload(key, "n2", "sha256:" + "0" * 64, 2, 1, 1000))
    # lease C: clean charge, then a post-expiry charge (I4) that still counts
    _forge(ledger, _charge_payload(key, "n3", lc, 1, 1, 10))
    _forge(ledger, _charge_payload(key, "n3", lc, 2, 9, 10))
    return ledger


SCENARIOS = [
    ("empty", s_empty),
    ("honest-single-node", s_honest_single_node),
    ("honest-two-node-partition", s_honest_two_node_partition),
    ("honest-mediation-coupled", s_honest_mediation_coupled),
    ("forged-overspend", s_forged_overspend),
    ("foreign-node-spend", s_foreign_node_spend),
    ("expired-lease-charge", s_expired_lease_charge),
    ("unknown-lease-charge", s_unknown_lease_charge),
    ("lease-key-mismatch", s_lease_key_mismatch),
    ("rogue-lease", s_rogue_lease),
    ("malformed-charges", s_malformed_charges),
    ("registration-poison", s_registration_poison),
    ("equivocation", s_equivocation),
    ("orphan-facts-only", s_orphan_facts_only),
    ("spec-ambiguity-issuer", s_spec_ambiguity_issuer),
    ("spec-ambiguity-i3-i4", s_spec_ambiguity_i3_i4),
]


def emit() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, build in SCENARIOS:
        ledger = build()
        artifact = ledger.to_jsonl()
        expected = canonical_json({
            "spec": "charge-ledger/1",
            "name": name,
            "fold": fold_canonical(ledger),
            "audit_codes": ledger.audit_codes(),
        })
        with open(os.path.join(OUT, f"{name}.ledger.jsonl"), "w", encoding="ascii") as fh:
            fh.write(artifact)
        with open(os.path.join(OUT, f"{name}.expected.json"), "w", encoding="ascii") as fh:
            fh.write(expected + "\n")
        n_codes = len(ledger.audit_codes())
        print(f"{name}: {ledger.event_count()} events, {n_codes} audit codes")
    print(f"\n{len(SCENARIOS)} golden ledgers in {OUT}")


if __name__ == "__main__":
    emit()
