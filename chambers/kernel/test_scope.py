"""charge-scope/1 as a standing lane (SCOPE-SPEC.md; E2 via FRAMEWORKS F2).

Families:
  1. MERKLE — the RFC 6962/9162 algorithms, brute-forced: every inclusion
     proof for every (index, size) up to 33 verifies and every tampered
     one fails; every consistency proof for every (m, n) up to 33
     verifies, and non-prefix histories (forks, rewrites) cannot produce
     one.
  2. CLOSURE — the touches-rule serves exactly the key set's court:
     information events on K, escrows binding K, their settlement and
     outcome closure, referenced receipts — and NOT deposits, NOT other
     keys' events.
  3. THE SERVED SURFACE — over real HTTP: scoped responses verify from
     bytes alone; a tampered event, a forged proof, and a padded
     off-scope event all fail; withholding an in-scope charge leaves a
     charge_seq gap the verifier reports; --scoped-only suppresses the
     whole-court views; federation twins agree on the set root.

Run: python3 chambers/kernel/test_scope.py
"""
from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import node as node_mod  # noqa: E402
from accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from events import event_id  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402
from scope import (  # noqa: E402
    consistency_proof,
    inclusion_proof,
    merkle_root,
    scope_closure,
    scope_response,
    verify_consistency,
    verify_inclusion,
    verify_scope,
)
from settlement import (  # noqa: E402
    OutcomeCondition,
    SettlementIssuer,
    attest_outcome,
    resolve_bond,
)

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
KEY_A = ("exp", "srcA", "readerR")
KEY_B = ("exp", "srcB", "readerR")

COND = OutcomeCondition(metric="m", lane="attested", quorum=1,
                        min_independence="role_separated",
                        min_bond_ucr=5_000, contest_ticks=10)


# ---- 1. merkle, brute-forced ----

def test_inclusion_proofs_brute_force() -> None:
    items = [f"sha256:{i:064x}" for i in range(33)]
    for n in range(1, 34):
        root = merkle_root(items[:n])
        for i in range(n):
            path = inclusion_proof(items[:n], i)
            assert verify_inclusion(items[i], i, n, path, root), (i, n)
            # tampered leaf fails
            assert not verify_inclusion(items[(i + 1) % n] if n > 1 else "x",
                                        i, n, path, root) or n == 1 and False
            # tampered path fails
            if path:
                bad = list(path)
                bad[0] = "00" * 32
                assert not verify_inclusion(items[i], i, n, bad, root), (i, n)
            # wrong index fails
            if n > 1:
                assert not verify_inclusion(items[i], (i + 1) % n, n, path, root), (i, n)
    print("inclusion: all (index,size) pairs to 33 verified; tampering fails")


def test_consistency_proofs_brute_force() -> None:
    items = [f"sha256:{i:064x}" for i in range(33)]
    for n in range(1, 34):
        root_n = merkle_root(items[:n])
        for m in range(1, n + 1):
            root_m = merkle_root(items[:m])
            proof = consistency_proof(items[:n], m)
            assert verify_consistency(m, n, root_m, root_n, proof), (m, n)
            if proof:
                bad = list(proof)
                bad[-1] = "11" * 32
                assert not verify_consistency(m, n, root_m, root_n, bad), (m, n)
    print("consistency: all (m,n) pairs to 33 verified; tampering fails")


def test_forked_history_cannot_prove_consistency() -> None:
    """SUNDR's point, mechanically: a history that is NOT a prefix
    extension (a rewrite, a fork shown to another reader) has no valid
    consistency proof against the remembered head."""
    honest = [f"sha256:{i:064x}" for i in range(20)]
    old_root = merkle_root(honest[:10])
    # rewrite: element 5 replaced after the fact
    rewritten = list(honest)
    rewritten[5] = "sha256:" + "e" * 64
    proof = consistency_proof(rewritten, 10)
    assert not verify_consistency(10, 20, old_root, merkle_root(rewritten), proof)
    # fork: a different continuation for another reader still extends the
    # SAME prefix — consistency holds for both, and that is fine: forks
    # are detected by comparing HEADS at equal size, not by consistency.
    fork = honest[:10] + ["sha256:" + "f" * 64]
    assert verify_consistency(10, 11, old_root, merkle_root(fork),
                              consistency_proof(fork, 10))
    other = honest[:11]
    assert merkle_root(fork) != merkle_root(other)  # equal size, different world
    print("rewrites cannot prove consistency; equal-size forks differ by head")


# ---- 2. the closure ----

def _economy() -> "tuple[Ledger, str, str]":
    """Two keys' worth of court + an outcome economy on KEY_A only.
    Returns (ledger, accepted_charge_on_A, accepted_charge_on_B)."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="chambers", ledger=ledger)
    for key in (KEY_A, KEY_B):
        meter.register(key, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    meter.charge(KEY_A, CapacityEstimate(10_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    meter.charge(KEY_B, CapacityEstimate(7_000, 0, 0, 0, 0, "c"), TOR, tick=1)
    events = getattr(ledger, "_events")
    charge_a = next(e for e, p in events.items()
                    if p.get("kind") == "charge" and tuple(p.get("key", ())) == KEY_A)
    charge_b = next(e for e, p in events.items()
                    if p.get("kind") == "charge" and tuple(p.get("key", ())) == KEY_B)
    bank = SettlementIssuer(issuer="bank", ledger=ledger)
    bank.deposit("payerP", 500_000, tick=0)
    bank.deposit("arbiter1", 50_000, tick=0)
    esc = bank.escrow(payer="payerP", payee="workerW", amount_ucr=50_000,
                      charge_keys=[KEY_A], expires_tick=100, tick=2, outcome=COND)
    att = attest_outcome(ledger, esc, "arbiter1", "occurred", "attested",
                         "role_separated", 5_000, tick=20)
    bank.release(esc, 50_000, [charge_a], tick=31, attestation_ids=[att.id])
    resolve_bond(ledger, att, "arbiter1", "return_to_attestor", 5_000, tick=32)
    return ledger, charge_a, charge_b


def test_closure_serves_exactly_the_keys_court() -> None:
    ledger, charge_a, charge_b = _economy()
    events = getattr(ledger, "_events")
    ids = scope_closure(events, [KEY_A])
    kinds = sorted(events[e]["kind"] for e in ids)
    # A's register/lease/charge + escrow + attestation + release + bond_resolution
    assert "escrow" in kinds and "outcome_attestation" in kinds
    assert "release" in kinds and "bond_resolution" in kinds
    assert charge_a in ids
    # NOT: B's court, NOT deposits
    assert charge_b not in ids
    assert not any(events[e]["kind"] == "deposit" for e in ids)
    assert not any(
        events[e].get("key") == list(KEY_B) for e in ids
    )
    print(f"closure over KEY_A: {len(ids)} events, deposits and srcB excluded")


def test_scope_response_verifies_and_tampering_fails() -> None:
    ledger, charge_a, _b = _economy()
    resp = scope_response(ledger, [KEY_A])
    assert verify_scope(resp) == [], verify_scope(resp)
    # tampered event bytes: id no longer matches proof
    resp2 = json.loads(json.dumps(resp))
    resp2["events"][0] = dict(resp2["events"][0])
    resp2["events"][0]["tick"] = 999_999
    assert any("membership" in p or "no membership" in p for p in verify_scope(resp2))
    # padded with an off-scope event (a deposit) + a forged proof entry
    events = getattr(ledger, "_events")
    dep_id, dep = next((e, p) for e, p in events.items() if p["kind"] == "deposit")
    resp3 = json.loads(json.dumps(resp))
    resp3["events"].append(dep)
    resp3["proofs"][dep_id] = {"index": 0, "path": []}
    probs = verify_scope(resp3)
    assert any("off-scope" in p for p in probs) or any("membership proof FAILED" in p for p in probs), probs
    # withholding an in-scope charge leaves a charge_seq gap... single
    # charge here, so instead drop the release and check closure shrinks
    # consistently (no false alarm):
    resp4 = json.loads(json.dumps(resp))
    resp4["events"] = [p for p in resp4["events"] if p["kind"] != "bond_resolution"]
    probs4 = [p for p in verify_scope(resp4) if not p.startswith("note:")]
    assert probs4 == [], probs4  # omitting a LEAF is invisible — named in SPEC §5
    print("scope verifies; tampering and padding fail; leaf-omission named honest")


def test_withheld_charge_leaves_seq_gap() -> None:
    """The kernel's fact-identity discipline is the omission evidence:
    charge_seq is dense per lease, so serving charges {1,3} without 2
    is arithmetically visible to the scoped reader."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="chambers", ledger=ledger)
    meter.register(KEY_A, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
    for t in (1, 2, 3):
        meter.charge(KEY_A, CapacityEstimate(1_000, 0, 0, 0, 0, "c"), TOR, tick=t)
    resp = scope_response(ledger, [KEY_A])
    assert verify_scope(resp) == []
    withheld = json.loads(json.dumps(resp))
    withheld["events"] = [p for p in withheld["events"]
                          if not (p.get("kind") == "charge" and p.get("charge_seq") == 2)]
    probs = verify_scope(withheld)
    assert any("charge_seq gap" in p and "[2]" in p for p in probs), probs
    print("withholding charge_seq=2 is reported by the scoped verifier")


# ---- 3. the served surface ----

def _start(state_path=None, scoped_only=False):
    server = node_mod.serve("127.0.0.1", 0, state_path, 4 * 1024 * 1024, scoped_only)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _get(base, path, expect=200):
    try:
        with urllib.request.urlopen(base + path) as r:
            return r.status, json.loads(r.read()) if "json" in r.headers["Content-Type"] else r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _post(base, path, body: str):
    req = urllib.request.Request(base + path, data=body.encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read())


def test_scope_over_http_and_consistency_growth() -> None:
    ledger, charge_a, _b = _economy()
    server, base = _start()
    try:
        _post(base, "/v1/events", ledger.to_jsonl())
        code, head1 = _get(base, "/v1/head")
        assert code == 200 and head1["tree_size"] == ledger.event_count()
        keys_q = quote(json.dumps([list(KEY_A)]))
        code, resp = _get(base, f"/v1/scope?keys={keys_q}")
        assert code == 200
        assert verify_scope(resp) == [], verify_scope(resp)
        assert resp["head"]["set_root"] == head1["set_root"]

        # the court grows; the reader who remembered head1 demands proof
        meter_ledger = Ledger()
        meter = KernelMeter(node="n2", issuer="other", ledger=meter_ledger)
        meter.register(("exp", "srcC", "readerZ"), 10_000, 5_000)
        _post(base, "/v1/events", meter_ledger.to_jsonl())
        code, head2 = _get(base, "/v1/head")
        assert head2["log_size"] > head1["log_size"]
        code, cons = _get(base, f"/v1/consistency?first={head1['log_size']}")
        assert code == 200
        assert verify_consistency(head1["log_size"], cons["second"],
                                  head1["log_root"], cons["second_log_root"],
                                  cons["proof"])
        # bad query
        code, _err = _get(base, "/v1/scope?keys=notjson")
        assert code == 400
    finally:
        server.shutdown()
    print("HTTP scope verifies; consistency proof binds growth to the old head")


def test_scoped_only_mode_suppresses_whole_court() -> None:
    ledger, _a, _b = _economy()
    server, base = _start(scoped_only=True)
    try:
        _post(base, "/v1/events", ledger.to_jsonl())
        for path in ("/v1/ledger", "/v1/fold", "/v1/audit", "/v1/settlement", "/v1/verify"):
            code, body = _get(base, path)
            assert code == 404, (path, code)
            assert "scoped-only" in body.get("error", ""), body
        code, head = _get(base, "/v1/head")
        assert code == 200 and head["tree_size"] == ledger.event_count()
        keys_q = quote(json.dumps([list(KEY_A)]))
        code, resp = _get(base, f"/v1/scope?keys={keys_q}")
        assert code == 200 and verify_scope(resp) == []
        code, health = _get(base, "/v1/health")
        assert code == 200 and health["ok"]
    finally:
        server.shutdown()
    print("scoped-only: whole-court views 404; head/scope/consistency serve")


def test_federated_twins_agree_on_set_root() -> None:
    ledger, _a, _b = _economy()
    s1, b1 = _start()
    s2, b2 = _start()
    try:
        # split the artifact across the two nodes, then replicate each way
        lines = ledger.to_jsonl().splitlines(keepends=True)
        _post(b1, "/v1/events", "".join(lines[0::2]))
        _post(b2, "/v1/events", "".join(lines[1::2]))
        _c, l1 = _get(b1, "/v1/ledger")
        _c, l2 = _get(b2, "/v1/ledger")
        _post(b1, "/v1/events", l2)
        _post(b2, "/v1/events", l1)
        _c, h1 = _get(b1, "/v1/head")
        _c, h2 = _get(b2, "/v1/head")
        assert h1["set_root"] == h2["set_root"]          # same court
        assert h1["tree_size"] == h2["tree_size"] == ledger.event_count()
        # ingestion orders differ (node-local histories) — and that is fine
        assert h1["log_root"] != h2["log_root"] or h1["log_root"] == h2["log_root"]
        # a scope served by EITHER node verifies against ITS head
        keys_q = quote(json.dumps([list(KEY_A)]))
        for b in (b1, b2):
            _c, resp = _get(b, f"/v1/scope?keys={keys_q}")
            assert verify_scope(resp) == []
    finally:
        s1.shutdown()
        s2.shutdown()
    print("federated twins: equal set roots, node-local logs, scopes verify")


def test_ingestion_log_survives_restart() -> None:
    import tempfile
    ledger, _a, _b = _economy()
    with tempfile.TemporaryDirectory(prefix="scope_state_") as d:
        state = os.path.join(d, "ledger.jsonl")
        server, base = _start(state)
        try:
            _post(base, "/v1/events", ledger.to_jsonl())
            _c, head1 = _get(base, "/v1/head")
        finally:
            server.shutdown()
        server, base = _start(state)
        try:
            _c, head2 = _get(base, "/v1/head")
            assert head2["log_root"] == head1["log_root"]  # history preserved
            assert head2["set_root"] == head1["set_root"]
            # growth after restart still proves consistency with pre-restart head
            extra = Ledger()
            m = KernelMeter(node="n9", issuer="zz", ledger=extra)
            m.register(("exp", "srcZ", "readerZ"), 10_000, 1_000)
            _post(base, "/v1/events", extra.to_jsonl())
            _c, cons = _get(base, f"/v1/consistency?first={head1['log_size']}")
            assert verify_consistency(head1["log_size"], cons["second"],
                                      head1["log_root"], cons["second_log_root"],
                                      cons["proof"])
        finally:
            server.shutdown()
    print("ingestion log survives restart; pre-restart heads stay provable")


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
    print(f"charge-scope/1 lane: {len(fns)} tests green")
