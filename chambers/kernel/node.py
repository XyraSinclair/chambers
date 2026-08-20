"""chamber-node/1 — the minimum real endpoint of the protocol.

    python3 -m chambers.kernel.node [--host 127.0.0.1] [--port 8799]
                                        [--state PATH] [--max-body BYTES]

One process, stdlib only, five verbs. This is the machine the math has
been promising: a node with an OPEN WRITE endpoint whose security model
is a theorem list rather than an auth layer.

  POST /v1/events      body = jsonl event lines -> merged into the ledger
  GET  /v1/ledger      the canonical artifact (id-sorted jsonl)
  GET  /v1/fold        KERNEL-SPEC §3.3 canonical fold (information)
  GET  /v1/audit       audit codes + clean flag
  GET  /v1/settlement  value accounts, escrows, conservation identity
  GET  /v1/verify      the full stranger's verdict (both layers)
  GET  /v1/health      liveness + event count

WHY the write endpoint needs no permission:

  * Event identity is CONTENT-ADDRESSED and recomputed at parse — you
    cannot forge someone else's fact without its exact bytes, and
    replaying bytes is a no-op (merge is union by id: idempotent,
    commutative, associative — the CRDT laws, proven monotone in
    ChargeKernel/Monotone.lean).
  * The fold and audit are TOTAL: malformed, Byzantine, or hostile facts
    do not corrupt state — they CONVICT their issuer (I-codes) or are
    quarantined by minimum-resolution. Posting garbage evidence against
    yourself is permitted, and it is exactly that: evidence.
  * Verdicts only escalate as facts arrive (merge_escalates, incident
    latch) — an attacker cannot post their way into a CLEANER court.
  * Value FAILS CLOSED: a release convicts unless its exact work receipt
    exists and the touching court is clean (S-codes). New garbage can
    freeze value flows (that is the design: dirt blocks payment on the
    dirty keys); it cannot mint or move a microcredit.
  * OUTCOME facts (charge-settlement/2) obey the same discipline: an
    outcome-gated release convicts without a hardened, uncontested,
    bonded quorum (S9); bonds are locked by the fold and slashed only by
    strictly better evidence (S10). POSTing a contest can freeze a
    payment on the contested question; it cannot take anyone's bond.

What open-write does NOT protect, named:

  * DISK/SPAM: anyone can grow the ledger. --max-body caps a request;
    total-size policy is a deployment decision, not protocol.
  * READ PRIVACY: by default this node serves the whole artifact to
    anyone. charge-scope/1 (SCOPE-SPEC.md) adds reader-scoped views:
    GET /v1/head (Merkle set root + ingestion-log root), GET /v1/scope
    (the touches-closure of a key set, each event with a membership
    proof), GET /v1/consistency (append-only proof against a remembered
    head — a node that rewrites its serving history cannot produce one).
    Run with --scoped-only to suppress the whole-court views; keys then
    act as bearer capabilities (you must know the exact key strings).
    Heads are UNSIGNED (identity is L5); scoped responses prove
    inclusion, not completeness — but seq density leaves withholding
    evidence (SCOPE-SPEC §5).
  * AVAILABILITY: one process, no replication. Merge two nodes' state
    files with `Ledger.merge` at any time — that IS the replication
    protocol; nothing here needs consensus because nothing here is a
    register: the state is a grow-only set.

Persistence is CRDT merge-on-persist (union with whatever is on disk,
then atomic tmp+rename) — the pattern proven in the lifetime ledger of
chamber.py (private): concurrent writers cannot silently erase each other's facts.
"""
from __future__ import annotations

import argparse
import http.server
import io
import json
import os
import socketserver
import threading
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

from . import findings as findings_registry  # noqa: E402
from .ledger import Ledger, fold_canonical  # noqa: E402  (KERNEL-SPEC §3.3)
from . import scope as scope_mod  # noqa: E402
from .settlement import conservation_identity, settlement_fold_canonical_v2  # noqa: E402
from . import verify as verify_mod  # noqa: E402


class NodeState:
    """The whole node: one grow-only ledger, one node-local ingestion log
    (charge-scope/1 consistency proofs), one lock, one file + sidecar."""

    def __init__(self, state_path: Optional[str] = None) -> None:
        self.lock = threading.Lock()
        self.state_path = state_path
        self.ledger = Ledger()
        self.ingestion: List[str] = []  # event ids, first-adoption order
        if state_path and os.path.exists(state_path):
            text = open(state_path, encoding="ascii").read()
            if text.strip():
                self.ledger = Ledger.from_jsonl(text)
        # hydrate the ingestion log: sidecar order first (filtered to
        # known events), then any events the sidecar missed, id-sorted —
        # deterministic across restarts.
        known = set(self.ledger.payloads().keys())
        log_path = self._log_path()
        adopted = set()  # tracks self.ingestion; rebuilding it per line was
        if log_path and os.path.exists(log_path):  # quadratic (2.9s at 20k events)
            for line in open(log_path, encoding="ascii"):
                eid = line.strip()
                if eid in known and eid not in adopted:
                    self.ingestion.append(eid)
                    adopted.add(eid)
        self.ingestion.extend(sorted(known - adopted))

    def _log_path(self) -> Optional[str]:
        return self.state_path + ".log" if self.state_path else None

    def ingest(self, body: str) -> dict:
        """Parse -> merge -> persist. Raises ValueError on unparseable
        input; state is untouched in that case (parse happens on a fresh
        Ledger before any merge). Newly adopted events append to the
        ingestion log in id-sorted order (deterministic per POST)."""
        try:
            incoming = Ledger.from_jsonl(body) if body.strip() else Ledger()
        except Exception as exc:
            raise ValueError(f"unparseable events: {exc}") from None
        with self.lock:
            before_ids = set(self.ledger.payloads().keys())
            self.ledger.merge(incoming)
            after_ids = set(self.ledger.payloads().keys())
            self.ingestion.extend(sorted(after_ids - before_ids))
            self._persist_locked()
            return {
                "posted_events": incoming.event_count(),
                "new_events": len(after_ids) - len(before_ids),
                "total_events": len(after_ids),
            }

    def _persist_locked(self) -> None:
        if not self.state_path:
            return
        merged = self.ledger
        if os.path.exists(self.state_path):
            on_disk = open(self.state_path, encoding="ascii").read()
            if on_disk.strip():
                merged = merged.merge(Ledger.from_jsonl(on_disk))
        # a concurrent writer's facts join the log too (merge-on-persist)
        merged_ids = set(merged.payloads().keys())
        seen = set(self.ingestion)
        self.ingestion.extend(sorted(merged_ids - seen))
        os.makedirs(os.path.dirname(os.path.abspath(self.state_path)), exist_ok=True)
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="ascii") as fh:
            fh.write(merged.to_jsonl())
        os.replace(tmp, self.state_path)
        log_path = self._log_path()
        tmp_log = log_path + ".tmp"
        with open(tmp_log, "w", encoding="ascii") as fh:
            fh.write("".join(eid + "\n" for eid in self.ingestion))
        os.replace(tmp_log, log_path)

    # ---- read views (each takes the lock only to snapshot) ----

    def snapshot(self) -> Ledger:
        with self.lock:
            return self.ledger.copy()

    def snapshot_with_log(self):
        with self.lock:
            return self.ledger.copy(), list(self.ingestion)


def make_handler(state: NodeState, max_body: int, scoped_only: bool = False):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "chamber-node/1"

        def _send(self, code: int, payload, content_type="application/json") -> None:
            body = (
                payload
                if isinstance(payload, (bytes,))
                else (
                    payload
                    if isinstance(payload, str)
                    else json.dumps(payload, sort_keys=True, indent=1)
                ).encode("utf-8")
            )
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):  # quiet by default
            pass

        def do_GET(self) -> None:
            url = urlparse(self.path)
            route, query = url.path, parse_qs(url.query)
            led, ingestion = state.snapshot_with_log()

            # charge-scope/1 surfaces — served in every mode
            if route == "/v1/health":
                self._send(200, {"ok": True, "events": led.event_count()})
                return
            if route == "/v1/head":
                head = scope_mod.set_head(led)
                head["log_size"] = len(ingestion)
                head["log_root"] = scope_mod.merkle_root(ingestion)
                self._send(200, head)
                return
            if route == "/v1/scope":
                raw = (query.get("keys") or [None])[0]
                try:
                    keys = json.loads(raw) if raw else None
                    assert isinstance(keys, list) and keys and all(
                        isinstance(k, list) and k and all(isinstance(s, str) for s in k)
                        for k in keys
                    )
                except Exception:
                    self._send(400, {"error": "keys must be a JSON array of "
                                              "key string-lists, e.g. "
                                              '[["exp","srcA","readerR"]]'})
                    return
                self._send(200, scope_mod.scope_response(led, keys))
                return
            if route == "/v1/consistency":
                try:
                    first = int((query.get("first") or [""])[0])
                except ValueError:
                    self._send(400, {"error": "first must be an integer"})
                    return
                n = len(ingestion)
                if not (0 < first <= n):
                    self._send(400, {"error": f"first must be in 1..{n}"})
                    return
                self._send(200, {
                    "first": first,
                    "second": n,
                    "proof": scope_mod.consistency_proof(ingestion, first),
                    "second_log_root": scope_mod.merkle_root(ingestion),
                })
                return

            if scoped_only:
                self._send(404, {"error": "scoped-only node: whole-court views "
                                          "are not served (SCOPE-SPEC §3)"})
                return

            # whole-court views
            if route == "/v1/ledger":
                self._send(200, led.to_jsonl(), content_type="text/plain; charset=ascii")
            elif route == "/v1/fold":
                self._send(200, fold_canonical(led))
            elif route == "/v1/audit":
                # the family set is registry data (findings.FAMILIES,
                # node_audit flag); the wire key per family is
                # chamber-node/1 transport naming and lives here.
                wire_key = {"I": "codes", "X": "x_codes",
                            "C": "c_codes", "P": "p_codes"}
                by_family = {
                    wire_key[fam.prefix]:
                        findings_registry.family_codes(fam.prefix, led)
                    for fam in findings_registry.node_audit_families()
                }
                clean = not any(by_family.values())
                self._send(200, {"clean": clean, **by_family})
            elif route == "/v1/settlement":
                lhs, rhs = conservation_identity(led)
                self._send(200, {
                    "settlement": settlement_fold_canonical_v2(led),
                    "conservation": {"accounted": lhs, "deposits": rhs, "holds": lhs == rhs},
                })
            elif route == "/v1/verify":
                buf = io.StringIO()
                code = verify_mod.verify(led.to_jsonl(), out=buf)
                self._send(200, {"exit_code": code, "clean": code == 0,
                                 "report": buf.getvalue()})
            else:
                self._send(404, {"error": "no such endpoint"})

        def do_POST(self) -> None:
            if self.path != "/v1/events":
                self._send(404, {"error": "no such endpoint"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length > max_body:
                self._send(413, {"error": f"body exceeds max {max_body} bytes"})
                return
            body = self.rfile.read(length).decode("utf-8", errors="strict")
            try:
                result = state.ingest(body)
            except ValueError as exc:
                self._send(400, {"error": str(exc)})
                return
            self._send(200, result)

    return Handler


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(host: str, port: int, state_path: Optional[str], max_body: int,
          scoped_only: bool = False) -> ThreadingHTTPServer:
    state = NodeState(state_path)
    server = ThreadingHTTPServer((host, port), make_handler(state, max_body, scoped_only))
    server.node_state = state  # type: ignore[attr-defined]
    return server


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--state", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".chamber", "node", "ledger.jsonl"))
    ap.add_argument("--max-body", type=int, default=4 * 1024 * 1024)
    ap.add_argument("--scoped-only", action="store_true",
                    help="serve only scoped views (charge-scope/1): "
                         "head/scope/consistency/health + POST events")
    args = ap.parse_args(argv)

    server = serve(args.host, args.port, args.state, args.max_body, args.scoped_only)
    n = server.node_state.ledger.event_count()  # type: ignore[attr-defined]
    mode = "SCOPED-ONLY" if args.scoped_only else "open views"
    print(f"chamber-node/1 on http://{args.host}:{args.port}  "
          f"state={os.path.normpath(args.state)}  events={n}  [{mode}]")
    print("POST /v1/events | GET /v1/{head,scope,consistency,health"
          + ("}" if args.scoped_only else ",ledger,fold,audit,settlement,verify}"))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
