"""attention-node/1 as a standing lane — every claim in the module
header, exercised over REAL HTTP against a live node:

  * provisioning IS the open-write endpoint: the receiver's budget, the
    chamber's exposure lease, and the payer's deposit arrive as posted
    facts, and the node adopts its leases from the court;
  * 5 rings deliver and pay the BELL'S OWNER, the 6th is refused with
    ZERO third-party exposure delta (the ordering law, served);
  * a fresh epoch (a new key, posted live) regenerates the budget;
  * an unfunded ring burns nothing; an unprovisioned key records
    nothing; malformed bodies get clean 400s;
  * an exposure refusal after attention over-counts one interrupt and
    pays nobody (the safe direction);
  * restart hydrates the meter from the persisted court (seq continues,
    budget remembered);
  * the whole economy federates into a plain chamber-node/1 and
    verifies CLEAN there — the notify surface emits nothing the base
    protocol cannot audit.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import attention_node as att_mod  # noqa: E402
import node as node_mod  # noqa: E402
from accountant import exposure_key  # noqa: E402
from attention_node import att_key  # noqa: E402
from leases import LeaseIssuer  # noqa: E402
from ledger import Ledger  # noqa: E402
from settlement import SettlementIssuer  # noqa: E402

EPOCH1, EPOCH2 = "epoch:2026-07-05", "epoch:2026-07-06"
RING = 1_000          # interrupt units per notification
CARD = 13_000         # mbits per match card
PRICE = 500_000       # 50 cents


def _start(state_path=None):
    server = att_mod.serve("127.0.0.1", 0, state_path, 4 * 1024 * 1024)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _start_plain():
    server = node_mod.serve("127.0.0.1", 0, None, 4 * 1024 * 1024)
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


def _notify(base, epoch=EPOCH1, units=RING, card_mbits=CARD, price=PRICE,
            payer="alice", receiver="bob", sender="alice_mediator",
            chamber="charlie_chamber"):
    return _post(base, "/v1/notify", json.dumps({
        "attention": {"receiver": receiver, "sender": sender, "epoch": epoch,
                      "interrupt_units": units},
        "exposure": {"chamber": chamber, "card_mbits": card_mbits},
        "payment": {"payer": payer, "price_ucr": price},
    }))


class Provisioner:
    """The parties' side: real issuers writing into a LOCAL ledger whose
    jsonl is then posted to the node's open-write endpoint — provisioning
    is federation, no setup verb exists."""

    def __init__(self) -> None:
        self.ledger = Ledger()
        self.bob = LeaseIssuer(issuer="bob", ledger=self.ledger)
        self.charlie = LeaseIssuer(issuer="charlie_chamber", ledger=self.ledger)
        self.bank = SettlementIssuer(issuer="houseEscrow", ledger=self.ledger)
        self._posted = 0

    def attention_budget(self, epoch: str, rings: int = 5) -> None:
        key = att_key("bob", "alice_mediator", epoch)
        self.bob.register(key, subject_entropy_mbits=rings * RING,
                          ceiling_mbits=rings * RING)
        self.bob.grant(key, node="mediator_node", amount_mbits=rings * RING,
                       expires_tick=100_000)

    def exposure_budget(self, ceiling_mbits: int = 100_000) -> None:
        key = exposure_key("charlie_chamber", "bob")
        self.charlie.register(key, subject_entropy_mbits=400_000,
                              ceiling_mbits=ceiling_mbits)
        self.charlie.grant(key, node="mediator_node", amount_mbits=ceiling_mbits,
                           expires_tick=100_000)

    def deposit(self, account: str, amount_ucr: int) -> None:
        self.bank.deposit(account, amount_ucr, tick=0)

    def post_new_facts(self, base) -> None:
        """POST only what hasn't been posted yet (idempotent anyway)."""
        code, res = _post(base, "/v1/events", self.ledger.to_jsonl())
        assert code == 200
        self._posted = self.ledger.event_count()


def _provision_standard(base, epoch=EPOCH1):
    prov = Provisioner()
    prov.attention_budget(epoch)
    prov.exposure_budget()
    prov.deposit("alice", 5_000_000)
    prov.post_new_facts(base)
    return prov


def test_five_rings_paid_sixth_refused_zero_exposure() -> None:
    server, base = _start()
    try:
        _provision_standard(base)
        receipts = []
        for _ in range(5):
            code, r = _notify(base)
            assert code == 200 and r["delivered"] is True, r
            assert r["payee"] == "bob" and r["paid_ucr"] == PRICE
            for f in ("attention_charge_id", "exposure_charge_id",
                      "escrow_id", "release_id"):
                assert isinstance(r[f], str) and r[f].startswith("sha256:")
            receipts.append(r)
        assert len({r["attention_charge_id"] for r in receipts}) == 5  # distinct facts

        # the 6th ring: refused BEFORE any third-party exposure
        code, r6 = _notify(base)
        assert code == 200 and r6["delivered"] is False
        assert r6["stage"] == "attention_refused"

        view = _get(base, "/v1/attention")
        (acct,) = [a for a in view["accounts"] if a["epoch"] == EPOCH1]
        assert acct["cumulative_mbits"] == 5 * RING
        assert acct["demanded_mbits"] == 6 * RING      # the pressure is recorded
        assert acct["remaining_mbits"] == 0
        assert acct["paid_ucr_by_payee"] == {"bob": 5 * PRICE}

        # settlement: the bell's owner was paid per ring; conservation holds
        st = _get(base, "/v1/settlement")
        assert st["conservation"]["holds"]
        accounts = {a["account"]: a for a in st["settlement"]["accounts"]}
        assert accounts["bob"]["available_ucr"] == 5 * PRICE
        assert accounts["alice"]["available_ucr"] == 5_000_000 - 5 * PRICE

        # the stranger's verdict on the whole served economy
        v = _get(base, "/v1/verify")
        assert v["clean"] and v["exit_code"] == 0
    finally:
        server.shutdown()


def test_exposure_cumulative_is_exactly_five_cards() -> None:
    server, base = _start()
    try:
        _provision_standard(base)
        for _ in range(6):
            _notify(base)
        led = Ledger.from_jsonl(_get(base, "/v1/ledger"))
        folded = led.fold()
        x_key = exposure_key("charlie_chamber", "bob")
        assert folded[x_key].cumulative_mbits == 5 * CARD
        assert folded[x_key].demanded_mbits == 5 * CARD  # the refused ring demanded NOTHING
    finally:
        server.shutdown()


def test_fresh_epoch_regenerates_live() -> None:
    server, base = _start()
    try:
        prov = _provision_standard(base)
        for _ in range(6):
            _notify(base)
        # posting a new epoch's budget to the LIVE node reopens the lane
        prov.attention_budget(EPOCH2)
        prov.post_new_facts(base)
        code, r = _notify(base, epoch=EPOCH2)
        assert code == 200 and r["delivered"] is True, r
        assert _get(base, "/v1/verify")["clean"]
    finally:
        server.shutdown()


def test_unfunded_ring_burns_nothing() -> None:
    server, base = _start()
    try:
        prov = Provisioner()
        prov.attention_budget(EPOCH1)
        prov.exposure_budget()
        prov.deposit("alice", PRICE - 1)  # one microcredit short
        prov.post_new_facts(base)
        before = _get(base, "/v1/health")["events"]
        code, r = _notify(base)
        assert code == 402 and r["stage"] == "funds"
        assert _get(base, "/v1/health")["events"] == before  # recordless
        view = _get(base, "/v1/attention")
        (acct,) = view["accounts"]
        assert acct["demanded_mbits"] == 0  # attention untouched by the unfunded ring
    finally:
        server.shutdown()


def test_unprovisioned_key_records_nothing_and_400s_are_clean() -> None:
    server, base = _start()
    try:
        before = _get(base, "/v1/health")["events"]
        code, r = _notify(base)  # nothing provisioned at all
        assert code == 409 and r["stage"] == "provisioning"
        assert "provision via POST /v1/events" in r["error"] or "registration" in r["error"]
        assert _get(base, "/v1/health")["events"] == before

        for bad in ("not json", json.dumps({}), json.dumps({"attention": {}}),
                    json.dumps({"attention": {"receiver": "b", "sender": "a",
                                              "epoch": "e"},
                                "exposure": {"chamber": "c", "card_mbits": -5},
                                "payment": {"payer": "a", "price_ucr": 1}})):
            code, r = _post(base, "/v1/notify", bad)
            assert code == 400 and "error" in r
        assert _get(base, "/v1/health")["events"] == before
    finally:
        server.shutdown()


def test_exposure_refusal_overcounts_one_interrupt_pays_nobody() -> None:
    server, base = _start()
    try:
        prov = Provisioner()
        prov.attention_budget(EPOCH1, rings=5)
        prov.exposure_budget(ceiling_mbits=2 * CARD)  # admits only 2 cards
        prov.deposit("alice", 5_000_000)
        prov.post_new_facts(base)

        for _ in range(2):
            code, r = _notify(base)
            assert r["delivered"] is True
        code, r3 = _notify(base)
        assert code == 200 and r3["delivered"] is False
        assert r3["stage"] == "exposure_refused"

        view = _get(base, "/v1/attention")
        (acct,) = view["accounts"]
        assert acct["cumulative_mbits"] == 3 * RING     # the over-count, named
        assert acct["paid_ucr_by_payee"] == {"bob": 2 * PRICE}  # ...but unpaid
        st = _get(base, "/v1/settlement")
        assert st["conservation"]["holds"]
        assert _get(base, "/v1/verify")["clean"]
    finally:
        server.shutdown()


def test_restart_hydrates_budget_and_sequence() -> None:
    with tempfile.TemporaryDirectory(prefix="attention_node_") as d:
        state = os.path.join(d, "ledger.jsonl")
        server, base = _start(state)
        try:
            _provision_standard(base)
            for _ in range(3):
                assert _notify(base)[1]["delivered"] is True
        finally:
            server.shutdown()

        server, base = _start(state)  # fresh process, fresh meter
        try:
            for _ in range(2):
                assert _notify(base)[1]["delivered"] is True
            code, r6 = _notify(base)
            assert r6["delivered"] is False and r6["stage"] == "attention_refused"
            v = _get(base, "/v1/verify")
            assert v["clean"], v["report"]  # no I8 equivocation: seq continued
        finally:
            server.shutdown()


def test_federates_clean_into_plain_chamber_node() -> None:
    att_server, att_base = _start()
    plain_server, plain_base = _start_plain()
    try:
        _provision_standard(att_base)
        for _ in range(6):
            _notify(att_base)
        artifact = _get(att_base, "/v1/ledger")
        code, res = _post(plain_base, "/v1/events", artifact)
        assert code == 200 and res["new_events"] > 0
        v = _get(plain_base, "/v1/verify")
        assert v["clean"] and v["exit_code"] == 0
        st = _get(plain_base, "/v1/settlement")
        assert st["conservation"]["holds"]
        assert _get(plain_base, "/v1/ledger") == artifact  # byte-identical court
    finally:
        att_server.shutdown()
        plain_server.shutdown()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
    print("attention-node lane green")
