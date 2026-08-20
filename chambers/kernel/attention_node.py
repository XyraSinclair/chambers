"""attention-node/1 — E3: attention accounts as a served surface.

    python3 -m chambers.kernel.attention_node [--host 127.0.0.1]
        [--port 8798] [--state PATH] [--node-id mediator_node]
        [--bank houseEscrow] [--max-body BYTES]

chamber-node/1 plus ONE verb. The court stays exactly what it was —
open-write, mergeable, convicting — and the mediator's metering
front-end moves from a demo (demo_attention_notify.py) to a live
endpoint. One POST executes the party story's Act 3 sequence under one
lock:

  POST /v1/notify     funds check -> ATTENTION charge (refuse-first)
                      -> EXPOSURE charge -> escrow + release bound to
                      the exact ring's charge event. Body:
                        {"attention": {"receiver": R, "sender": S,
                                       "epoch": E,
                                       "interrupt_units": 1000?},
                         "exposure":  {"chamber": C, "card_mbits": M,
                                       "channel": "match_card"?},
                         "payment":   {"payer": P, "price_ucr": U}}
  GET  /v1/attention  the court's view of every attention account:
                      budget, demand, remaining, who was paid for the
                      rings (recipient-as-fee-beneficiary, G6).
  plus every chamber-node/1 verb (events/ledger/fold/audit/settlement/
  verify/health), unchanged.

PROVISIONING IS THE OPEN-WRITE ENDPOINT — there is no setup verb.
Parties post their own facts to POST /v1/events, exactly the federation
path: the receiver registers the attention key and grants this node a
lease (their epoch budget IS the spam ceiling they issued); the third
party's chamber registers and leases the exposure key; the bank
deposits the payer's balance. The node ADOPTS any well-formed lease
addressed to its node id straight from the ledger (KernelMeter.adopt),
hydrating from the replay, so provisioning, restart, and federation are
the same code path.

THE ORDERING LAW (the safety argument, demo-proven, now served): the
attention refusal happens BEFORE any exposure charge, so a ring the
receiver's budget refuses leaks NOTHING about the third party — the
spam ceiling protects the third party's privacy, not just the
receiver's focus. An exposure refusal after attention was accepted
over-counts one interrupt and pays nobody: the safe direction, chosen.

WHAT THE RESPONSE IS: a receipt of event ids. The stranger re-derives
every number from GET /v1/verify — nothing in the response is
trust-me.

HONEST LIMITS, named (each with its register entry):
  * IDENTITY IS DECLARED, NOT AUTHENTICATED (L5, ASSURANCE.md): anyone
    can post facts in any issuer's name; a forged deposit or lease is
    the standing identity/Sybil non-claim, not a new hole this surface
    opens. Signatures/TLS/auth are E8 deployment hardening.
  * READ PRIVACY IS E2: this node serves its whole court to anyone.
    Point it at courts, not secrets.
  * PRICE DISCOVERY IS OUT OF SCOPE: the payer declares the price per
    ring; the receiver's lever is the budget they lease (refuse cheap
    bells by not leasing to mediators who ring them). A receiver-priced
    tariff is a schema-catalog question (E4).
  * CARD DELIVERY IS OUT OF BAND: the node meters and settles; the
    card body travels between the parties. The charge's channel field
    names the schema whose estimator priced it.
  * ONE LEASE PER KEY PER METER LIFETIME (KernelMeter.adopt): a
    renewed budget is a NEW key — the epoch pattern is the designed
    regeneration path, and it is exercised below.
  * CROSS-UNIT ATOMICITY DOES NOT EXIST: micro-interrupts and
    millibits are different units, so the two charges are sequenced,
    not atomic (the over-count direction is deliberate; a two-unit
    coupled charge is real future kernel work).
  * A DIRTY COURT BLOCKS PAYMENT on the touched keys (required_clean):
    Byzantine facts merged into the court can freeze the payment lane
    — that is the design; they cannot mint or move a microcredit.
  * THE NODE'S CLOCK counts only its OWN facts (its charges, its
    bank's settlement events): merged foreign ticks cannot fast-forward
    it past the leases it holds (a Byzantine tick would otherwise be a
    freeze lever on this surface).
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Optional, Tuple

from . import node as node_mod  # noqa: E402
from .accountant import CapacityEstimate, EstimatorAttestation, Key, exposure_key  # noqa: E402
from .events import LeaseEvent, event_id, is_uint as _is_uint  # noqa: E402
from .meter import KernelMeter  # noqa: E402
from .settlement import (  # noqa: E402
    SETTLEMENT_KINDS,
    SettlementIssuer,
    SettlementRefused,
    settlement_fold,
)

# The attention unit's meaning lives in the attestation id, exactly where
# log2 lives for bits (demo_attention_notify.py's finding, now canonical
# here — the demo imports these).
ATTN_ESTIMATOR = EstimatorAttestation(
    "attention.micro_interrupts.flat_v1", "operator", "declared_unit_flat", True
)
CARD_ESTIMATOR = EstimatorAttestation(
    "matchcard.schema_v1.enum_sum", "adversarial_review", "static_schema_bound", True
)
DEFAULT_INTERRUPT_UNITS = 1_000
ESCROW_TTL_TICKS = 64  # release happens at tick+3; any ttl > 3 works


def att_key(receiver: str, sender: str, epoch: str) -> Key:
    """The second key family: protected party = the receiver, write =
    occupancy of their focus, regeneration = the epoch in the key."""
    return ("att", receiver, sender, epoch)


def _is_pos(v) -> bool:
    return _is_uint(v) and v > 0


class AttentionNodeState(node_mod.NodeState):
    """chamber-node/1's state plus the mediator roles: one meter (holder
    of adopted leases), one settlement authority, one self-owned clock."""

    def __init__(self, state_path: Optional[str] = None,
                 node_id: str = "mediator_node",
                 bank_issuer: str = "houseEscrow") -> None:
        super().__init__(state_path)
        self.node_id = node_id
        self.meter = KernelMeter(node=node_id, issuer=f"{node_id}.self",
                                 ledger=self.ledger)
        self.bank = SettlementIssuer(issuer=bank_issuer, ledger=self.ledger)
        self.clock = self._own_max_tick()

    # ---- the node's own clock ----

    def _own_max_tick(self) -> int:
        """Max declared tick over THIS node's facts only. Foreign facts
        (merged or hostile) never move our clock — see honest limits."""
        top = 0
        for p in self.ledger.events():
            kind = p.get("kind")
            mine = (
                (kind == "charge" and p.get("node") == self.node_id)
                or (kind in SETTLEMENT_KINDS and p.get("issuer") == self.bank.issuer)
            )
            if mine and _is_uint(p.get("tick")):
                top = max(top, p["tick"])
        return top

    # ---- lease adoption from the open court ----

    def _adopt_locked(self, key: Key, tick: int) -> Optional[str]:
        """Adopt the court's lease for `key` addressed to this node, if the
        meter doesn't hold one yet. Returns an error string (nothing
        recorded) or None on success. Totality: malformed facts are
        skipped, never crash."""
        if not self.meter.has(key):
            resolved, _conflicted, _f = self.ledger._resolve_registers()
            reg = resolved.get(key)
            if reg is None:
                return f"no well-formed registration for key {list(key)}"
            best = None  # (expires_tick, lease_seq, LeaseEvent)
            for eid, p in self.ledger.payloads().items():
                if p.get("kind") != "lease" or tuple(p.get("key", ())) != key:
                    continue
                if p.get("node") != self.node_id:
                    continue
                if not (_is_pos(p.get("amount_mbits")) and _is_uint(p.get("expires_tick"))
                        and _is_pos(p.get("lease_seq")) and isinstance(p.get("issuer"), str)):
                    continue
                lease = LeaseEvent(key=key, lease_seq=p["lease_seq"], node=p["node"],
                                   amount_mbits=p["amount_mbits"], issuer=p["issuer"],
                                   expires_tick=p["expires_tick"])
                if lease.id != eid:
                    continue  # extra/renamed fields: not canonically reconstructible
                cand = (lease.expires_tick, lease.lease_seq, lease)
                if best is None or cand[:2] > best[:2]:
                    best = cand
            if best is None:
                return (f"no lease for key {list(key)} addressed to node "
                        f"{self.node_id!r} — provision via POST /v1/events")
            self.meter.adopt(key, best[2], subject_entropy_mbits=reg["subject_entropy_mbits"])
        lease = self.meter.lease_for(key)
        if lease is not None and tick > lease.expires_tick:
            return (f"lease for key {list(key)} expired at tick {lease.expires_tick} "
                    f"(now {tick}); a renewed budget is a new key")
        return None

    # ---- the verb ----

    def notify(self, req: dict) -> Tuple[int, dict]:
        """One notification: the demo's proven sequence, served. Returns
        (http_status, receipt)."""
        err = _validate(req)
        if err:
            return 400, {"error": err}
        att = req["attention"]
        exp = req["exposure"]
        pay = req["payment"]
        receiver, sender, epoch = att["receiver"], att["sender"], att["epoch"]
        units = att.get("interrupt_units", DEFAULT_INTERRUPT_UNITS)
        channel = exp.get("channel", "match_card")
        a_key = att_key(receiver, sender, epoch)
        x_key = exposure_key(exp["chamber"], receiver)

        with self.lock:
            t = self.clock + 1
            # provisioning (pure reads; nothing recorded on refusal)
            for key, last_tick in ((a_key, t), (x_key, t + 1)):
                err = self._adopt_locked(key, last_tick)
                if err:
                    return 409, {"delivered": False, "stage": "provisioning", "error": err}
            # funds (pure read; an unfunded ring must not burn attention)
            accounts, _ = settlement_fold(self.ledger)
            available = accounts[pay["payer"]].available_ucr if pay["payer"] in accounts else 0
            if pay["price_ucr"] > available:
                return 402, {"delivered": False, "stage": "funds",
                             "error": f"payer {pay['payer']!r} has {available} ucr "
                                      f"available < price {pay['price_ucr']}"}

            # 1) attention first: may the receiver's bell ring?
            attn, attn_id = self.meter.charge_recorded(
                a_key, CapacityEstimate(units, 0, 0, 0, 0, "notify"),
                ATTN_ESTIMATOR, tick=t)
            if not attn.accepted:
                self.clock = t
                self._persist_locked()
                return 200, {"delivered": False, "stage": "attention_refused",
                             "reason_class": attn.reason_class,
                             "attention_charge_id": attn_id,
                             "note": "refusal recorded as demand; zero third-party exposure"}
            # 2) exposure second: the card's content leaks the third party.
            card, card_id = self.meter.charge_recorded(
                x_key, CapacityEstimate(exp["card_mbits"], 0, 0, 0, 0, channel),
                CARD_ESTIMATOR, tick=t + 1)
            if not card.accepted:
                self.clock = t + 1
                self._persist_locked()
                return 200, {"delivered": False, "stage": "exposure_refused",
                             "reason_class": card.reason_class,
                             "attention_charge_id": attn_id,
                             "exposure_charge_id": card_id,
                             "note": "one interrupt over-counted, nobody paid "
                                     "(the safe direction)"}
            # 3) the payment, bound to THIS ring, paid to the bell's owner.
            try:
                escrow = self.bank.escrow(
                    payer=pay["payer"], payee=receiver, amount_ucr=pay["price_ucr"],
                    charge_keys=[a_key], expires_tick=t + 2 + ESCROW_TTL_TICKS,
                    tick=t + 2)
                release = self.bank.release(escrow, pay["price_ucr"], [attn_id],
                                            tick=t + 3)
            except SettlementRefused as exc:
                self.clock = t + 1
                self._persist_locked()
                return 409, {"delivered": False, "stage": "settlement_refused",
                             "error": str(exc),
                             "attention_charge_id": attn_id,
                             "exposure_charge_id": card_id,
                             "note": "charges stand as facts; no value moved"}
            self.clock = t + 3
            self._persist_locked()
            return 200, {"delivered": True,
                         "attention_charge_id": attn_id,
                         "exposure_charge_id": card_id,
                         "escrow_id": escrow.id,
                         "release_id": release.id,
                         "paid_ucr": pay["price_ucr"],
                         "payee": receiver,
                         "tick": t}

    # ---- the view ----

    def attention_view(self) -> dict:
        """The court's fold restricted to the attention family, plus who
        was paid for the rings — everything re-derivable by a stranger."""
        led = self.snapshot()
        events = led.payloads()
        paid: dict = {}
        for p in events.values():
            if p.get("kind") != "release":
                continue
            esc = events.get(p.get("escrow_id"))
            if esc is None or esc.get("kind") != "escrow":
                continue
            if not _is_uint(p.get("amount_ucr")):
                continue
            for k in esc.get("charge_keys", ()):
                k = tuple(k) if isinstance(k, list) else k
                if isinstance(k, tuple) and len(k) == 4 and k[0] == "att":
                    payee = esc.get("payee")
                    if isinstance(payee, str):
                        by_key = paid.setdefault(k, {})
                        by_key[payee] = by_key.get(payee, 0) + p["amount_ucr"]
        out = []
        for key, acct in sorted(led.fold().items()):
            if not (len(key) == 4 and key[0] == "att"):
                continue
            out.append({
                "key": list(key),
                "receiver": key[1], "sender": key[2], "epoch": key[3],
                "ceiling_mbits": acct.ceiling_mbits,
                "cumulative_mbits": acct.cumulative_mbits,
                "demanded_mbits": acct.demanded_mbits,
                "remaining_mbits": acct.ceiling_mbits - acct.cumulative_mbits,
                "paid_ucr_by_payee": paid.get(key, {}),
            })
        return {"node": self.node_id, "accounts": out}


def _validate(req) -> Optional[str]:
    """Total request validation: a clean 400 for every malformed shape."""
    if not isinstance(req, dict):
        return "body must be a JSON object"
    for section, fields in (("attention", ("receiver", "sender", "epoch")),
                            ("exposure", ("chamber",)),
                            ("payment", ("payer",))):
        sec = req.get(section)
        if not isinstance(sec, dict):
            return f"missing object field {section!r}"
        for f in fields:
            if not (isinstance(sec.get(f), str) and sec[f]):
                return f"{section}.{f} must be a non-empty string"
    if not _is_pos(req["attention"].get("interrupt_units", DEFAULT_INTERRUPT_UNITS)):
        return "attention.interrupt_units must be a positive integer"
    if not _is_pos(req["exposure"].get("card_mbits")):
        return "exposure.card_mbits must be a positive integer"
    if not isinstance(req["exposure"].get("channel", "match_card"), str):
        return "exposure.channel must be a string"
    if not _is_pos(req["payment"].get("price_ucr")):
        return "payment.price_ucr must be a positive integer"
    return None


def make_handler(state: AttentionNodeState, max_body: int):
    Base = node_mod.make_handler(state, max_body)

    class Handler(Base):  # type: ignore[misc,valid-type]
        server_version = "attention-node/1"

        def do_GET(self) -> None:
            if self.path == "/v1/attention":
                self._send(200, state.attention_view())
            else:
                super().do_GET()

        def do_POST(self) -> None:
            if self.path != "/v1/notify":
                super().do_POST()
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length > max_body:
                self._send(413, {"error": f"body exceeds max {max_body} bytes"})
                return
            try:
                req = json.loads(self.rfile.read(length).decode("utf-8", errors="strict"))
            except Exception as exc:
                self._send(400, {"error": f"unparseable JSON: {exc}"})
                return
            code, payload = state.notify(req)
            self._send(code, payload)

    return Handler


class ThreadingHTTPServer(node_mod.ThreadingHTTPServer):
    pass


def serve(host: str, port: int, state_path: Optional[str], max_body: int,
          node_id: str = "mediator_node",
          bank_issuer: str = "houseEscrow") -> ThreadingHTTPServer:
    state = AttentionNodeState(state_path, node_id=node_id, bank_issuer=bank_issuer)
    server = ThreadingHTTPServer((host, port), make_handler(state, max_body))
    server.node_state = state  # type: ignore[attr-defined]
    return server


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8798)
    ap.add_argument("--state", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".chamber", "attention_node",
        "ledger.jsonl"))
    ap.add_argument("--node-id", default="mediator_node")
    ap.add_argument("--bank", default="houseEscrow")
    ap.add_argument("--max-body", type=int, default=4 * 1024 * 1024)
    args = ap.parse_args(argv)

    server = serve(args.host, args.port, args.state, args.max_body,
                   node_id=args.node_id, bank_issuer=args.bank)
    st: AttentionNodeState = server.node_state  # type: ignore[attr-defined]
    print(f"attention-node/1 on http://{args.host}:{args.port}  "
          f"node_id={st.node_id}  bank={st.bank.issuer}  "
          f"state={os.path.normpath(args.state)}  events={st.ledger.event_count()}")
    print("POST /v1/notify | GET /v1/attention | + every chamber-node/1 verb")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
