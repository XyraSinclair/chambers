"""chamber-node/1 as a standing lane — every open-write security claim in
the module header, exercised over REAL HTTP against a live node:

  * honest artifact POSTs clean and every read view matches the library;
  * replay is a no-op (union by id — idempotent ingest);
  * a Byzantine fact is ACCEPTED and CONVICTED (evidence, not corruption)
    and the node stays healthy;
  * garbage is refused with state untouched;
  * persistence survives restart, and merge-on-persist unions with a
    concurrent writer's facts instead of erasing them;
  * concurrent POSTs from many threads land as the exact union.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel import node as node_mod  # noqa: E402
from chambers.kernel.demo_work_economy import build_economy  # noqa: E402
from chambers.kernel.emit_ledger_traces import fold_canonical  # noqa: E402
from chambers.kernel.events import event_id  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402


def _start(state_path=None):
    server = node_mod.serve("127.0.0.1", 0, state_path, 4 * 1024 * 1024)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _get(base, path):
    with urllib.request.urlopen(base + path) as r:
        return json.loads(r.read()) if "json" in r.headers["Content-Type"] else r.read().decode()


def _post(base, path, body: str):
    req = urllib.request.Request(base + path, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_honest_artifact_round_trips_and_all_views_match_library() -> None:
    server, base = _start()
    try:
        econ = build_economy()
        artifact = econ.to_jsonl()
        code, res = _post(base, "/v1/events", artifact)
        assert code == 200 and res["new_events"] == econ.event_count()

        assert _get(base, "/v1/ledger") == artifact
        assert _get(base, "/v1/fold") == fold_canonical(econ)
        audit = _get(base, "/v1/audit")
        assert audit["clean"] and audit["codes"] == []
        st = _get(base, "/v1/settlement")
        assert st["conservation"]["holds"]
        v = _get(base, "/v1/verify")
        assert v["clean"] and v["exit_code"] == 0

        # replay: union by id is idempotent
        code, res2 = _post(base, "/v1/events", artifact)
        assert code == 200 and res2["new_events"] == 0
        assert res2["total_events"] == econ.event_count()
    finally:
        server.shutdown()


def test_byzantine_fact_is_accepted_and_convicted_node_stays_healthy() -> None:
    server, base = _start()
    try:
        econ = build_economy()
        _post(base, "/v1/events", econ.to_jsonl())

        # forge an overspend against an existing lease (KERNEL-SPEC I3 shape)
        events = getattr(econ, "_events")
        lease_p = next(p for p in events.values() if p.get("kind") == "lease")
        forged = {
            "kind": "charge", "key": lease_p["key"], "node": lease_p["node"],
            "lease_id": event_id(lease_p), "charge_seq": 999, "tick": 50,
            "channel": "c", "estimate_total_mbits": 999999, "estimator_id": "e",
            "estimator_independence": "adversarial_review", "estimator_worst_case": True,
            "accepted": True, "reason_class": "EMITTED", "reason_detail": "x",
            "demand_mbits": 999999, "debit_mbits": 999999,
        }
        line = json.dumps(forged, sort_keys=True, separators=(",", ":")) + "\n"
        code, res = _post(base, "/v1/events", line)
        assert code == 200 and res["new_events"] == 1  # evidence admitted

        audit = _get(base, "/v1/audit")
        assert not audit["clean"] and audit["codes"]  # ...and convicted
        assert _get(base, "/v1/health")["ok"]  # node unharmed
        assert _get(base, "/v1/verify")["exit_code"] == 1
    finally:
        server.shutdown()


def test_garbage_refused_state_untouched() -> None:
    server, base = _start()
    try:
        econ = build_economy()
        _post(base, "/v1/events", econ.to_jsonl())
        before = _get(base, "/v1/health")["events"]
        code, res = _post(base, "/v1/events", "this is not jsonl\n")
        assert code == 400 and "unparseable" in res["error"]
        assert _get(base, "/v1/health")["events"] == before
    finally:
        server.shutdown()


def test_persistence_and_merge_on_persist() -> None:
    with tempfile.TemporaryDirectory(prefix="node_state_") as d:
        state = os.path.join(d, "ledger.jsonl")
        econ = build_economy()

        server, base = _start(state)
        try:
            _post(base, "/v1/events", econ.to_jsonl())
        finally:
            server.shutdown()

        # a CONCURRENT writer appends its own fact directly to disk
        other = Ledger()
        other._add_payload(
            event_id({"kind": "register", "key": ["exp", "x", "y"],
                      "subject_entropy_mbits": 1000, "ceiling_mbits": 100,
                      "issuer": "someoneElse"}),
            {"kind": "register", "key": ["exp", "x", "y"],
             "subject_entropy_mbits": 1000, "ceiling_mbits": 100,
             "issuer": "someoneElse"},
        )
        disk = Ledger.from_jsonl(open(state).read())
        disk.merge(other)
        open(state, "w").write(disk.to_jsonl())

        # restart: node hydrates BOTH histories; a new POST must not erase
        # the concurrent writer's fact (merge-on-persist, not snapshot).
        server, base = _start(state)
        try:
            assert _get(base, "/v1/health")["events"] == econ.event_count() + 1
            _post(base, "/v1/events", econ.to_jsonl())  # replay, no-op
            persisted = Ledger.from_jsonl(open(state).read())
            assert persisted.event_count() == econ.event_count() + 1
        finally:
            server.shutdown()


def test_outcome_economy_served_end_to_end() -> None:
    """E1 over real HTTP: a /2 outcome artifact POSTs in; the settlement
    view serves the bond states; a contest POSTED to the open-write
    endpoint escalates the verdict (blocks the payment question) without
    taking anyone's bond — then the golden adversarial artifact convicts."""
    here = os.path.dirname(os.path.abspath(__file__))
    traces = os.path.join(here, "settlement2_traces")
    server, base = _start()
    try:
        artifact = open(os.path.join(traces, "honest-outcome-flow.ledger.jsonl"),
                        encoding="ascii").read()
        code, res = _post(base, "/v1/events", artifact)
        assert code == 200 and res["new_events"] > 0
        st = _get(base, "/v1/settlement")
        assert st["conservation"]["holds"]
        assert st["settlement"]["bonds"], "bond states must be served"
        assert all(b["remaining_ucr"] == 0 for b in st["settlement"]["bonds"])
        v = _get(base, "/v1/verify")
        assert v["clean"] and v["exit_code"] == 0
        assert "charge-settlement/2" in v["report"]

        # merge in the golden S9/S10 crime scene: verdict only escalates
        bad = open(os.path.join(traces, "s10-bond-crimes.ledger.jsonl"),
                   encoding="ascii").read()
        code, _ = _post(base, "/v1/events", bad)
        assert code == 200
        v2 = _get(base, "/v1/verify")
        assert v2["exit_code"] == 1 and "S10" in v2["report"]
        assert _get(base, "/v1/health")["ok"]
        assert _get(base, "/v1/settlement")["conservation"]["holds"]
    finally:
        server.shutdown()


def test_concurrent_posts_land_as_exact_union() -> None:
    server, base = _start()
    try:
        econ = build_economy()
        lines = econ.to_jsonl().splitlines(keepends=True)
        chunks = [
            "".join(lines[i::4]) for i in range(4)
        ]
        threads = [threading.Thread(target=_post, args=(base, "/v1/events", c))
                   for c in chunks for _ in range(3)]  # each chunk posted 3x
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert _get(base, "/v1/health")["events"] == econ.event_count()
        assert _get(base, "/v1/ledger") == econ.to_jsonl()
    finally:
        server.shutdown()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
    print("node lane green")
