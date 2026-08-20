"""Federation is merge — two live nodes converge using ONLY their public
endpoints. No sync protocol, no consensus, no new code: GET one node's
/v1/ledger and POST it to the other. Because the state is a grow-only
content-addressed set, bidirectional exchange IS replication, order
doesn't matter, repetition is free, and both nodes end at the exact same
bytes — the CRDT laws (Monotone.lean) as an operational property of real
HTTP processes.

Also pins the adversarial shape: a Byzantine fact posted to ONE node
propagates like any fact and CONVICTS on both — federation spreads
evidence, not corruption.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel import node as node_mod  # noqa: E402
from chambers.kernel.demo_work_economy import build_economy  # noqa: E402
from chambers.kernel.events import event_id  # noqa: E402


def _start():
    server = node_mod.serve("127.0.0.1", 0, None, 4 * 1024 * 1024)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _get(base, path):
    with urllib.request.urlopen(base + path) as r:
        return json.loads(r.read()) if "json" in r.headers["Content-Type"] else r.read().decode()


def _post(base, body: str):
    req = urllib.request.Request(base + "/v1/events", data=body.encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def _sync(src_base, dst_base):
    """The entire federation protocol."""
    _post(dst_base, _get(src_base, "/v1/ledger"))


def test_two_nodes_converge_by_public_endpoints_alone() -> None:
    a_srv, a = _start()
    b_srv, b = _start()
    try:
        econ = build_economy()
        lines = econ.to_jsonl().splitlines(keepends=True)
        # disjoint-ish halves, one to each node (overlap is harmless: union)
        _post(a, "".join(lines[0::2]))
        _post(b, "".join(lines[1::2]))
        assert _get(a, "/v1/ledger") != _get(b, "/v1/ledger")

        # one round-trip of the two-line protocol
        _sync(a, b)
        _sync(b, a)

        la, lb = _get(a, "/v1/ledger"), _get(b, "/v1/ledger")
        assert la == lb == econ.to_jsonl(), "nodes must converge to the exact artifact"
        assert _get(a, "/v1/audit")["clean"] and _get(b, "/v1/audit")["clean"]
        assert _get(a, "/v1/settlement")["conservation"]["holds"]
        assert _get(b, "/v1/settlement") == _get(a, "/v1/settlement")

        # idempotence: syncing again changes nothing
        _sync(a, b)
        _sync(b, a)
        assert _get(a, "/v1/ledger") == la and _get(b, "/v1/ledger") == lb
        print("two nodes converged byte-identically over public HTTP alone")
    finally:
        a_srv.shutdown()
        b_srv.shutdown()


def test_byzantine_fact_propagates_as_evidence_not_corruption() -> None:
    a_srv, a = _start()
    b_srv, b = _start()
    try:
        econ = build_economy()
        artifact = econ.to_jsonl()
        _post(a, artifact)
        _post(b, artifact)

        # forge an overspend and post it to node A only
        events = getattr(econ, "_events")
        lease_p = next(p for p in events.values() if p.get("kind") == "lease")
        forged = {
            "kind": "charge", "key": lease_p["key"], "node": lease_p["node"],
            "lease_id": event_id(lease_p), "charge_seq": 777, "tick": 60,
            "channel": "c", "estimate_total_mbits": 888888, "estimator_id": "e",
            "estimator_independence": "adversarial_review", "estimator_worst_case": True,
            "accepted": True, "reason_class": "EMITTED", "reason_detail": "x",
            "demand_mbits": 888888, "debit_mbits": 888888,
        }
        _post(a, json.dumps(forged, sort_keys=True, separators=(",", ":")) + "\n")
        assert not _get(a, "/v1/audit")["clean"]
        assert _get(b, "/v1/audit")["clean"]  # B hasn't heard yet

        _sync(a, b)  # federation spreads the EVIDENCE
        audit_b = _get(b, "/v1/audit")
        assert not audit_b["clean"] and audit_b["codes"] == _get(a, "/v1/audit")["codes"]
        # both nodes healthy, both convict identically, value fails closed
        assert _get(a, "/v1/health")["ok"] and _get(b, "/v1/health")["ok"]
        assert _get(a, "/v1/verify")["exit_code"] == _get(b, "/v1/verify")["exit_code"] == 1
        print("byzantine fact propagated as identical convictions on both nodes")
    finally:
        a_srv.shutdown()
        b_srv.shutdown()


if __name__ == "__main__":
    test_two_nodes_converge_by_public_endpoints_alone()
    test_byzantine_fact_propagates_as_evidence_not_corruption()
    print("federation lane green")
