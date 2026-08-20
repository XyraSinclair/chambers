"""Tests for charge-kernel/2.

Three families:
  1. CONFORMANCE — the generalized accountant replays every golden trace in
     ../conformance/traces/ and matches `expected` bit-for-bit. This proves
     the kernel did not drift from egress-accountant/1 while generalizing the
     key (and that the /2 hardening moved no SPEC bit).
  2. DISTRIBUTIVE PROPERTIES — merge is idempotent/commutative/associative;
     the fold is order-independent and TOTAL under adversarial content; the
     global cap holds under partition; the wire format round-trips.
  3. ADVERSARIAL / HONESTY — every hole closed in /2 has a regression test:
     fact-identity (no dedup undercount), honest lease resumption, atomic
     emission, registration-poison quarantine, node binding, lease expiry,
     equivocation, negative-millibit injection.

Run: python3 -m pytest chambers/kernel/test_kernel.py -q
 or: python3 chambers/kernel/test_kernel.py   (plain-assert fallback)
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import (  # type: ignore  # noqa: E402
    Accountant,
    CapacityEstimate,
    EstimatorAttestation,
    composition_key,
    exposure_key,
)
from chambers.kernel.events import ChargeEvent, LeaseEvent, RegisterEvent, event_id
from chambers.kernel.leases import LeaseIssuer, LeaseRefused
from chambers.kernel.ledger import Ledger, MergeConflict
from chambers.kernel.meter import KernelMeter, MeterRefused
from chambers.kernel.session import MediationSession, SessionRefused

HERE = os.path.dirname(os.path.abspath(__file__))
TRACES = os.path.join(HERE, "..", "conformance", "traces")

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)


def _est(total: int, channel: str = "c") -> CapacityEstimate:
    return CapacityEstimate(total, 0, 0, 0, 0, channel)


# ---- 1. conformance ----

def _estimate(d: dict) -> CapacityEstimate:
    return CapacityEstimate(
        enum_value_mbits=d["enum_value_mbits"],
        ordering_mbits=d["ordering_mbits"],
        field_presence_mbits=d["field_presence_mbits"],
        text_mbits=d["text_mbits"],
        side_channel_mbits=d["side_channel_mbits"],
        channel=d.get("channel", "x"),
    )


def _estimator(d: dict) -> EstimatorAttestation:
    return EstimatorAttestation(
        estimator_id=d["estimator_id"],
        independence=d["independence"],
        method=d.get("method", "x"),
        worst_case_over_secrets=d["worst_case_over_secrets"],
    )


def _replay(trace: dict) -> List[dict]:
    acc = Accountant()
    out: List[dict] = []
    for op in trace["ops"]:
        if op["op"] == "register":
            k = composition_key(*op["key"])
            acc.register(k, op["subject_entropy_mbits"], op["ceiling_mbits"])
        elif op["op"] == "charge":
            k = composition_key(*op["key"])
            dec = acc.charge(k, _estimate(op["estimate"]), _estimator(op["estimator"]), op.get("tick", 0))
            out.append(
                {
                    "accepted": dec.accepted,
                    "reason_class": dec.reason_class,
                    "reason_detail": dec.reason_detail,
                    "cumulative_mbits": dec.cumulative_mbits,
                    "demanded_mbits": dec.demanded_mbits,
                    "blocked": dec.blocked,
                    "incident": dec.incident,
                    "leakage_class": dec.leakage_class,
                    "newly_incident": dec.newly_incident,
                }
            )
    return out


def test_conformance_golden_traces() -> None:
    files = [f for f in os.listdir(TRACES) if f.endswith(".json") and f != "MANIFEST.json"]
    assert files, "no golden traces found"
    checked = 0
    for fname in sorted(files):
        with open(os.path.join(TRACES, fname), "r", encoding="utf-8") as fh:
            trace = json.load(fh)
        actual = _replay(trace)
        expected = trace["expected"]
        assert len(actual) == len(expected), f"{fname}: length {len(actual)} != {len(expected)}"
        for i, (a, e) in enumerate(zip(actual, expected)):
            for field_name, ev in e.items():
                assert a[field_name] == ev, f"{fname}[{i}].{field_name}: {a[field_name]} != {ev}"
        checked += 1
    print(f"conformance: {checked} golden traces matched bit-for-bit")


# ---- 2. distributive properties ----

def _demo_ledger() -> Ledger:
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
        for tick in range(4):  # 4*10000 = 40000 > 30000 lease: some refuse
            dec = acc.charge(key, est, TOR, tick)
            ledger.add(
                ChargeEvent.from_decision(key, node, lease.id, tick + 1, tick, est, TOR, dec)
            )
    return ledger


def test_merge_is_crdt() -> None:
    a = _demo_ledger()
    b = _demo_ledger()  # same facts, independently reconstructed
    # idempotent
    n = a.event_count()
    a.copy().merge(a)
    assert a.event_count() == n
    # commutative + associative: fold is identical regardless of merge order
    m1 = a.copy().merge(b.copy())
    m2 = b.copy().merge(a.copy())
    assert m1.fold() == m2.fold()
    assert m1.to_jsonl() == m2.to_jsonl()
    print(f"merge CRDT: {a.event_count()} events, order-independent fold")


def test_global_cap_holds_under_partition() -> None:
    ledger = _demo_ledger()
    accts = ledger.fold()
    key = exposure_key("chamberA", "agentZ")
    acct = accts[key]
    # two nodes, 30000 lease each, tried 40000 each; global accepted must be
    # <= ceiling 60000 by lease partition, NOT 80000.
    assert acct.cumulative_mbits <= acct.ceiling_mbits == 60000
    assert acct.cumulative_mbits == 60000  # both nodes fill their leases exactly
    assert ledger.audit() == []
    print(f"global cap: cumulative {acct.cumulative_mbits} <= ceiling {acct.ceiling_mbits}")


def test_issuer_refuses_to_overgrant() -> None:
    ledger = Ledger()
    issuer = LeaseIssuer(issuer="chamberA", ledger=ledger)
    key = exposure_key("chamberA", "agentZ")
    issuer.register(key, 100000, 50000)
    issuer.grant(key, "n1", 40000, 100)
    try:
        issuer.grant(key, "n2", 20000, 100)  # 40000+20000 > 50000
        assert False, "expected over-grant refusal"
    except LeaseRefused:
        pass
    print("issuer refuses over-grant (global cap by construction)")


def test_jsonl_roundtrip_and_gossip_convergence() -> None:
    ledger = _demo_ledger()
    text = ledger.to_jsonl()
    back = Ledger.from_jsonl(text)
    assert back.event_count() == ledger.event_count()
    assert back.fold() == ledger.fold()
    assert back.to_jsonl() == text  # byte-deterministic artifact
    # shard the lines three ways, gossip in two different orders
    lines = text.strip().splitlines()
    shards = [Ledger.from_jsonl("\n".join(lines[i::3])) for i in range(3)]
    g1 = shards[0].copy().merge(shards[1]).merge(shards[2])
    g2 = shards[2].copy().merge(shards[0]).merge(shards[1])
    assert g1.to_jsonl() == g2.to_jsonl() == text
    assert g1.audit() == []
    print(f"wire format: {len(lines)} lines round-trip; 3-shard gossip converges")


# ---- 3. adversarial / honesty regressions ----

def test_negative_estimate_rejected() -> None:
    # a negative component would CREDIT the meter; the boundary refuses it
    try:
        CapacityEstimate(-1, 0, 0, 0, 0, "c")
        assert False, "expected ValueError for negative millibits"
    except ValueError:
        pass
    try:
        CapacityEstimate(0, 0, True, 0, 0, "c")  # bool is not an int here
        assert False, "expected ValueError for bool millibits"
    except ValueError:
        pass
    print("negative/bool millibit components refused at the boundary")


def test_forged_negative_debit_caught() -> None:
    ledger = _demo_ledger()
    key = exposure_key("chamberA", "agentZ")
    lease_payload = next(p for p in ledger.events() if p.get("kind") == "lease")
    before = ledger.fold()[key].cumulative_mbits
    forged = ChargeEvent(
        key=key, node="n1", lease_id=event_id(lease_payload), charge_seq=77, tick=5,
        channel="c", estimate_total_mbits=10000, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=10000, debit_mbits=-999999,  # tries to UN-spend the budget
    )
    ledger.add(forged)
    after = ledger.fold()[key].cumulative_mbits
    assert after == before, "negative debit must not reduce the fold"
    findings = ledger.audit()
    assert any("I6" in f for f in findings), findings
    print("forged negative debit: fold unmoved, audit flags I6")


def _session_fixture(agent_budget: Dict[str, int], requester_budget: Dict[str, int]):
    """issuer + leases for a 2-member tuple; returns (ledger, leases)."""
    ledger = Ledger()
    issuer = LeaseIssuer(issuer="issuerOfRecord", ledger=ledger)
    leases: Dict = {}
    for m, amt in agent_budget.items():
        k = exposure_key(m, "guestAgent")
        issuer.register(k, 100000, amt)
        leases[k] = issuer.grant(k, "node1", amt, 100)
    for m, amt in requester_budget.items():
        k = exposure_key(m, "requesterR")
        issuer.register(k, 100000, amt)
        leases[k] = issuer.grant(k, "node1", amt, 100)
    return ledger, leases


def test_distinct_facts_do_not_collapse() -> None:
    # Two REAL charges with identical fields (session restart, same estimate,
    # same local tick) must remain two ledger facts. In /1 they hashed to one
    # id and merge silently dropped one — an undercount of leakage.
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture({m: 30000 for m in members}, {})
    key = exposure_key("chamberA", "guestAgent")

    s1 = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    s1.observe("chamberA", _est(10000), TOR)

    s2 = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    s2.observe("chamberA", _est(10000), TOR)  # identical estimate, fresh session

    acct = ledger.fold()[key]
    assert acct.cumulative_mbits == 20000, acct  # NOT 10000
    assert ledger.audit() == []
    print("fact identity: identical charges from two sessions both counted (20000)")


def test_lease_resumption_prevents_honest_double_spend() -> None:
    # A restarted session hydrates prior spend from the ledger; the API can
    # no longer walk an honest node into an I3 violation.
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture({m: 30000 for m in members}, {})
    key = exposure_key("chamberA", "guestAgent")

    s1 = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    r1 = s1.observe("chamberA", _est(20000), TOR)
    assert r1.decision.accepted

    s2 = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    r2 = s2.observe("chamberA", _est(20000), TOR)  # only 10000 remains on the lease
    assert not r2.decision.accepted
    assert r2.decision.reason_class == "REFUSED_CEILING"

    acct = ledger.fold()[key]
    assert acct.cumulative_mbits == 20000
    assert ledger.audit() == []
    print("honest resumption: restarted session refuses past the lease remainder")


def test_atomic_emission_no_partial_debit() -> None:
    # Asymmetric requester budgets: A can absorb the judgement, B cannot.
    # The refused emission must leave A UNDEBITED (no phantom leakage in the
    # court file) while demand accrues on both (the attempt was real).
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture({}, {"chamberA": 10000, "chamberB": 3000})
    sess = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)

    emit = sess.emit(_est(5000, "judgement"), TOR)  # 5000 > B's 3000
    assert not emit.accepted
    assert emit.decision.reason_class == "REFUSED_CEILING"  # B, the guilty member
    by_member = {r.member: r.decision for r in emit.results}
    assert by_member["chamberB"].reason_class == "REFUSED_CEILING"
    assert by_member["chamberA"].reason_class == "REFUSED_COUPLED"

    accts = ledger.fold()
    a = accts[exposure_key("chamberA", "requesterR")]
    b = accts[exposure_key("chamberB", "requesterR")]
    assert a.cumulative_mbits == 0 and b.cumulative_mbits == 0  # all-or-none
    assert a.demanded_mbits == 5000 and b.demanded_mbits == 5000  # demand is honest

    # B latched blocked (SPEC step D); a further attempt refuses on B as
    # BLOCKED and still leaves A undebited.
    emit2 = sess.emit(_est(2000, "judgement"), TOR)
    assert not emit2.accepted
    assert {r.member: r.decision.reason_class for r in emit2.results} == {
        "chamberA": "REFUSED_COUPLED",
        "chamberB": "REFUSED_BLOCKED",
    }
    assert ledger.fold()[exposure_key("chamberA", "requesterR")].cumulative_mbits == 0
    assert ledger.audit() == []
    print("atomic emission: refused emission debits nothing, demand accrues everywhere")


def test_registration_poison_is_quarantined_not_fatal() -> None:
    # In /1, one conflicting RegisterEvent made every fold() raise forever —
    # a one-event denial-of-audit. Now: fold is total, resolves to the
    # conservative minimum, marks the account conflicted, and audit reports.
    ledger = _demo_ledger()
    key = exposure_key("chamberA", "agentZ")
    ledger.add(RegisterEvent(key, 100000, 50000, "chamberA"))  # ceiling 50000 < 60000

    accts = ledger.fold()  # must NOT raise
    acct = accts[key]
    assert acct.conflicted
    assert acct.ceiling_mbits == 50000  # min: severity can only escalate
    findings = ledger.audit()
    assert any("I7" in f for f in findings), findings
    assert any("I2" in f for f in findings), findings  # 60000 spent > 50000 min ceiling
    print("registration poison: fold total, conservative minimum, audited as I7")


def test_same_id_different_bytes_is_merge_conflict() -> None:
    ledger = Ledger()
    ledger._add_payload("sha256:deadbeef", {"kind": "charge", "x": 1})
    try:
        ledger._add_payload("sha256:deadbeef", {"kind": "charge", "x": 2})
        assert False, "expected MergeConflict"
    except MergeConflict:
        pass
    print("same id, different bytes: MergeConflict (content addressing enforced)")


def test_node_binding_enforced_and_audited() -> None:
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture({m: 30000 for m in members}, {})
    # an honest session on the WRONG node refuses to construct
    try:
        MediationSession("nodeEvil", "guestAgent", "requesterR", members, leases, ledger)
        assert False, "expected SessionRefused for foreign lease"
    except SessionRefused:
        pass
    # a Byzantine node writing a charge against a foreign lease is audited
    key = exposure_key("chamberA", "guestAgent")
    lease = leases[key]
    forged = ChargeEvent(
        key=key, node="nodeEvil", lease_id=lease.id, charge_seq=1, tick=5,
        channel="c", estimate_total_mbits=1000, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=1000, debit_mbits=1000,
    )
    ledger.add(forged)
    findings = ledger.audit()
    assert any("I4" in f and "nodeEvil" in f for f in findings), findings
    print("node binding: foreign lease refused live, forged spend audited as I4")


def test_lease_expiry_enforced_and_audited() -> None:
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture({m: 30000 for m in members}, {})
    sess = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    # honest session refuses to charge past expiry (leases expire at tick 100)
    try:
        sess.observe("chamberA", _est(1000), TOR, tick=101)
        assert False, "expected SessionRefused for expired lease"
    except SessionRefused:
        pass
    # a liar that charges anyway is audited
    key = exposure_key("chamberA", "guestAgent")
    lease = leases[key]
    forged = ChargeEvent(
        key=key, node="node1", lease_id=lease.id, charge_seq=9, tick=500,
        channel="c", estimate_total_mbits=1000, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=1000, debit_mbits=1000,
    )
    ledger.add(forged)
    findings = ledger.audit()
    assert any("I4" in f and "expiry" in f for f in findings), findings
    print("lease expiry: live charge refused, late forged charge audited as I4")


def test_equivocation_detected() -> None:
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture({m: 30000 for m in members}, {})
    key = exposure_key("chamberA", "guestAgent")
    lease = leases[key]

    def fact(total: int) -> ChargeEvent:
        return ChargeEvent(
            key=key, node="node1", lease_id=lease.id, charge_seq=7, tick=3,
            channel="c", estimate_total_mbits=total, estimator_id="e",
            estimator_independence="adversarial_review", estimator_worst_case=True,
            accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
            demand_mbits=total, debit_mbits=total,
        )

    ledger.add(fact(1000))
    ledger.add(fact(2000))  # same (node, lease, seq), different content
    findings = ledger.audit()
    assert any("I8" in f for f in findings), findings
    print("equivocation: two facts claiming one (node, lease, seq) audited as I8")


def test_audit_catches_forged_overspend() -> None:
    ledger = _demo_ledger()
    key = exposure_key("chamberA", "agentZ")
    lease_payload = next(p for p in ledger.events() if p.get("kind") == "lease")
    forged = ChargeEvent(
        key=key, node=lease_payload["node"], lease_id=event_id(lease_payload),
        charge_seq=99, tick=99, channel="c",
        estimate_total_mbits=999999, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=999999, debit_mbits=999999,
    )
    ledger.add(forged)
    findings = ledger.audit()
    assert any("I3" in f for f in findings) or any("I2" in f for f in findings), findings
    print(f"audit catches forgery: {len(findings)} finding(s)")


def test_mediation_session_charges_both_sides() -> None:
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture(
        {m: 50000 for m in members}, {m: 8000 for m in members}
    )
    sess = MediationSession(
        node="node1", agent_entity="guestAgent", requester_entity="requesterR",
        tuple_members=members, leases=leases, ledger=ledger,
    )
    r1 = sess.observe("chamberA", _est(20000, "read"), TOR)
    r2 = sess.observe("chamberB", _est(20000, "read"), TOR)
    assert r1.decision.accepted and r2.decision.accepted
    emit = sess.emit(CapacityEstimate(4000, 500, 0, 0, 0, "judgement"), TOR)  # 4500 typed bits
    assert emit.accepted, emit.decision
    cf = sess.court_file()
    # requester exposure charged on BOTH members (emission not separable)
    for m in members:
        assert cf[exposure_key(m, "requesterR")]["cumulative_mbits"] == 4500
        assert cf[exposure_key(m, "guestAgent")]["cumulative_mbits"] == 20000
    assert ledger.audit() == []
    print("mediation session: observation and emission both charged; court file clean")


def test_emission_refused_when_requester_ceiling_hit() -> None:
    members = ["chamberA", "chamberB"]
    ledger, leases = _session_fixture(
        {m: 50000 for m in members}, {m: 3000 for m in members}  # tiny emission budget
    )
    sess = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    sess.observe("chamberA", _est(10000, "r"), TOR)
    emit = sess.emit(_est(5000, "j"), TOR)  # 5000 > 3000
    assert not emit.accepted
    assert emit.decision.reason_class == "REFUSED_CEILING"
    # atomicity: neither requester account was debited
    for m in members:
        assert ledger.fold()[exposure_key(m, "requesterR")].cumulative_mbits == 0
    assert ledger.audit() == []
    print("emission refused when requester exposure ceiling would be crossed")


def test_kernel_meter_full_path_and_restart() -> None:
    # The meter must exercise the FULL distributive path (register -> lease
    # -> seq'd charge events) and survive a restart without double-spending.
    ledger = Ledger()
    key = composition_key("subjectS", "reachability", "audienceA")

    m1 = KernelMeter(node="sim", issuer="ownerO", ledger=ledger)
    m1.register(key, subject_entropy_mbits=100000, ceiling_mbits=30000)
    d1 = m1.charge(key, _est(20000), TOR)
    assert d1.accepted

    # restart: a fresh meter over the same ledger hydrates prior spend
    m2 = KernelMeter(node="sim", issuer="ownerO", ledger=ledger)
    m2.register(key, subject_entropy_mbits=100000, ceiling_mbits=30000)
    d2 = m2.charge(key, _est(20000), TOR)  # only 10000 remains
    assert not d2.accepted and d2.reason_class == "REFUSED_CEILING"

    acct = ledger.fold()[key]
    assert acct.cumulative_mbits == 20000
    assert ledger.audit() == []
    assert m2.court_file()[key]["cumulative_mbits"] == 20000

    # zero-ceiling registration is refused (an unregistered key emits nothing)
    try:
        m2.register(composition_key("s2", "q", "a"), 1000, 0)
        assert False, "expected MeterRefused"
    except MeterRefused:
        pass
    print("kernel meter: full event path, restart-safe, audit clean")


def test_audit_codes_canonical() -> None:
    # audit_codes is the conformance surface: stable codes + canonical
    # subjects, sorted and deduplicated.
    ledger = _demo_ledger()
    assert ledger.audit_codes() == []
    key = exposure_key("chamberA", "agentZ")
    lease_payload = next(p for p in ledger.events() if p.get("kind") == "lease")
    forged = ChargeEvent(
        key=key, node=lease_payload["node"], lease_id=event_id(lease_payload),
        charge_seq=99, tick=99, channel="c",
        estimate_total_mbits=999999, estimator_id="e",
        estimator_independence="adversarial_review", estimator_worst_case=True,
        accepted=True, reason_class="EMITTED", reason_detail="emitted_debited",
        demand_mbits=999999, debit_mbits=999999,
    )
    ledger.add(forged)
    codes = ledger.audit_codes()
    assert codes == sorted(set(codes))
    assert any(c.startswith("I2 ") for c in codes), codes
    assert any(c.startswith("I3 ") for c in codes), codes
    # subjects are canonical: I2 carries the key as canonical JSON, I3 the lease id
    i2 = [c for c in codes if c.startswith("I2 ")][0]
    assert i2 == 'I2 ["exp","chamberA","agentZ"]', i2
    print(f"audit codes canonical: {codes}")


def test_ledger_trace_corpus_replays() -> None:
    # The golden ledger corpus (KERNEL-SPEC.md §5) must replay bit-for-bit
    # from the artifacts alone: parse jsonl -> fold + audit_codes -> compare
    # to expected; re-serialization must reproduce the artifact bytes.
    from chambers.kernel import emit_ledger_traces as elt

    traces_dir = os.path.join(HERE, "ledger_traces")
    names = sorted(
        f[: -len(".ledger.jsonl")]
        for f in os.listdir(traces_dir)
        if f.endswith(".ledger.jsonl")
    )
    assert len(names) >= 14, names
    from chambers.kernel.events import canonical_json

    for name in names:
        with open(os.path.join(traces_dir, f"{name}.ledger.jsonl"), encoding="ascii") as fh:
            artifact = fh.read()
        with open(os.path.join(traces_dir, f"{name}.expected.json"), encoding="ascii") as fh:
            expected = json.load(fh)
        ledger = Ledger.from_jsonl(artifact)
        assert ledger.to_jsonl() == artifact, f"{name}: reserialization not byte-identical"
        assert elt.fold_canonical(ledger) == expected["fold"], f"{name}: fold diverges"
        assert ledger.audit_codes() == expected["audit_codes"], f"{name}: audit diverges"
    print(f"ledger corpus: {len(names)} golden ledgers replay bit-for-bit")


def test_nonstring_issuer_cannot_authorize_leases() -> None:
    # Regression (caught by the first counterparty implementation + the
    # spec-ambiguity-issuer corpus case): KERNEL-SPEC §3.1 — a register with
    # a missing or non-string issuer is still well-formed but contributes
    # NOTHING to issuers(key). Before the fix, ledger.py kept the raw value
    # (or a "" default) in the issuer set, so a forged lease echoing the
    # same non-string issuer — or an empty-string issuer against a
    # missing-issuer register — evaded I5, and two deviant registers of
    # mixed types crashed the auditor on sort. All three must convict/parse.
    from chambers.kernel.events import event_id

    key = ["comp", "evader", "reachability", "cardinal"]

    def _ledger(register_extra: dict, lease_issuer) -> Ledger:
        reg = {
            "kind": "register", "key": key,
            "subject_entropy_mbits": 1000, "ceiling_mbits": 1000,
            **register_extra,
        }
        lease = {
            "kind": "lease", "key": key, "lease_seq": 1, "node": "n1",
            "amount_mbits": 10, "issuer": lease_issuer, "expires_tick": 99,
        }
        lines = "".join(
            _canonical_line(p) for p in (reg, lease)
        )
        return Ledger.from_jsonl(lines)

    def _canonical_line(payload: dict) -> str:
        from chambers.kernel.events import canonical_json
        return canonical_json(payload) + "\n"

    # forged lease echoes the non-string issuer -> must still be I5
    led = _ledger({"issuer": 7}, 7)
    assert any(c.startswith("I5") for c in led.audit_codes()), led.audit_codes()
    # empty-string lease issuer against a missing-issuer register -> I5
    led = _ledger({}, "")
    assert any(c.startswith("I5") for c in led.audit_codes()), led.audit_codes()
    # mixed-type deviant registers must not crash the auditor
    reg2 = {
        "kind": "register", "key": key,
        "subject_entropy_mbits": 900, "ceiling_mbits": 900, "issuer": 7,
    }
    reg3 = {
        "kind": "register", "key": key,
        "subject_entropy_mbits": 800, "ceiling_mbits": 800,
    }
    text = "".join(_canonical_line(p) for p in (reg2, reg3))
    led = Ledger.from_jsonl(text)
    led.audit_codes()  # must not raise
    account = led.fold()[tuple(key)]
    assert account.ceiling_mbits == 800  # field-wise min: both well-formed
    assert account.subject_entropy_mbits == 800
    print("non-string issuers authorize nothing; auditor survives mixed types")


def test_lean_golden_traces_reemit_identical() -> None:
    # The mechanical model-code binding (ASSURANCE L4): emit_lean_traces.py
    # transcribes accountant.py's OBSERVED behavior into GoldenTraces.lean,
    # which replays by rfl inside Lean. This test pins the Python half of
    # that loop: re-emission must be byte-identical to the committed
    # artifacts. If accountant.py's behavior drifts, THIS goes red here;
    # if the Lean model drifts, `lake build` goes red there. (The lane is
    # live: a corrupted golden value was shown to stop the Lean build.)
    from chambers.kernel import emit_lean_traces as elt

    committed = {}
    for path in (elt.JSON_OUT, elt.LEAN_OUT):
        with open(path, "rb") as fh:
            committed[path] = fh.read()
    elt.emit()
    for path, before in committed.items():
        with open(path, "rb") as fh:
            assert fh.read() == before, f"{path}: re-emission not byte-identical"
    print("lean golden traces re-emit byte-identical (json + generated .lean)")


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"\nall {len(fns)} kernel tests passed")


if __name__ == "__main__":
    _run_all()
