"""charge-provenance/1 (P-codes) as a standing lane — KERNEL-SPEC Part III;
G16, the M4 law of the moat register.

The law: an emission of a derived fact charges the fact's TRANSITIVE
ancestry, in the same coupling, at the DPI bound the declared hop
capacities imply. The load-bearing test is the multi-hop one: a source
three derivation hops behind the emitted fact convicts exactly like a
one-hop source — depth is not dilution, and the compounding move and the
laundering move stop being the same move.

Families:
  1. HONEST CLOSURE — derive, emit with the full ancestry coupled: clean,
     and the whole verifier (I/S/X/C/P + conservation) exits 0.
  2. CONVICTIONS — P1/P2/P3 each injected the Byzantine way, including
     the multi-hop P1 and the min-cut/parallel-path P2 arithmetic.
  3. SUBSTRATE — totality on adversarial content, cycles, shuffle-merge
     invariance, X0 covering derivation identity for free.
  4. FROZEN SURFACES — every frozen corpus has an empty P verdict.
  5. SETTLEMENT — P findings join the dirty court: releases fail closed.

Run: python3 chambers/kernel/test_provenance_p.py
"""
from __future__ import annotations

import glob
import io
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify as verify_mod  # noqa: E402
from accountant import CapacityEstimate, EstimatorAttestation, exposure_key  # noqa: E402
from events import DerivationEvent, canonical_json, event_id  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402
from settlement import (  # noqa: E402
    SettlementIssuer,
    SettlementRefused,
    audit_settlement_codes,
)

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
FACT = "sha256:" + "d" * 64          # a derived fact's content id
FACT2 = "sha256:" + "e" * 64
FACT3 = "sha256:" + "f" * 64
K_SELF = ("exp", "chamberA", "readerR")
K_SRC = ("exp", "srcS", "readerR")


def _est(total: int, channel: str) -> CapacityEstimate:
    return CapacityEstimate(total, 0, 0, 0, 0, channel)


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _meter(ledger: Ledger, keys, ceiling: int = 50_000) -> KernelMeter:
    m = KernelMeter(node="n1", issuer="chamberA", ledger=ledger)
    for k in keys:
        m.register(k, subject_entropy_mbits=100_000, ceiling_mbits=ceiling)
    return m


def _register_id(ledger: Ledger, key) -> str:
    """The register event's ledger id — the leaf ancestry anchor."""
    return next(
        eid for eid, p in ledger._events.items()
        if p.get("kind") == "register" and p.get("key") == list(key)
    )


def _emitted(key, node, tick, channel, total, *, debit=None, seq=1) -> dict:
    """A hand-forged EMITTED charge carrying exactly the fields the
    P-audit reads (Byzantine events owe the audit nothing else)."""
    return {
        "kind": "charge", "key": list(key), "node": node, "tick": tick,
        "channel": channel, "reason_class": "EMITTED", "accepted": True,
        "estimate_total_mbits": total,
        "debit_mbits": total if debit is None else debit,
        "demand_mbits": total, "lease_id": "sha256:" + "0" * 64,
        "charge_seq": seq,
    }


# ---- 1. honest closure ----

def test_honest_closure_flow_is_clean_and_fully_verifies() -> None:
    """Derive from a source, emit the derivative with the source's
    exposure coupled: no P finding, and the stranger's one-command
    verifier says CLEAN across every family."""
    ledger = Ledger()
    meter = _meter(ledger, [K_SELF, K_SRC])
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(_register_id(ledger, K_SRC),),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=1, tick=1,
    ))
    decisions = meter.charge_coupled(
        [K_SELF, K_SRC], _est(3_000, "derived:" + FACT), TOR, tick=2)
    assert all(d.accepted for d in decisions.values())
    assert ledger.provenance_codes() == []
    assert verify_mod.verify(ledger.to_jsonl(), out=io.StringIO()) == 0


def test_self_source_emission_is_clean() -> None:
    """The emitter's own key is not special: when the closure's only
    source is the emitter, the emission charge satisfies its own row."""
    ledger = Ledger()
    meter = _meter(ledger, [K_SELF])
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(_register_id(ledger, K_SELF),),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=1, tick=1,
    ))
    assert meter.charge(K_SELF, _est(3_000, "derived:" + FACT), TOR, tick=2).accepted
    assert ledger.provenance_codes() == []


def test_out_of_scope_emissions_are_inert() -> None:
    """Named non-claims stay named: an emission of an underived fact,
    an undeclared channel, and a non-exp coupling produce no P finding."""
    ledger = Ledger()
    meter = _meter(ledger, [K_SELF])
    # underived fact: closure has no sources
    assert meter.charge(K_SELF, _est(1_000, "derived:" + FACT2), TOR, tick=2).accepted
    # undeclared channel over a real derivation (non-claim 1: invisible)
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(_register_id(ledger, K_SELF),),
        hop_capacity_mbits=1_000, issuer="chamberA", seq=1, tick=1,
    ))
    assert meter.charge(K_SELF, _est(1_000, "judgement"), TOR, tick=3).accepted
    # non-exp coupling (non-claim 2)
    _forge(ledger, _emitted(["att", "a", "b"], "n9", 5, "derived:" + FACT, 500))
    assert ledger.provenance_codes() == []


# ---- 2. convictions ----

def test_p1_dropped_ancestor_single_hop() -> None:
    ledger = Ledger()
    meter = _meter(ledger, [K_SELF, K_SRC])
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(_register_id(ledger, K_SRC),),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=1, tick=1,
    ))
    assert meter.charge(K_SELF, _est(3_000, "derived:" + FACT), TOR, tick=2).accepted
    assert ledger.provenance_codes() == [
        f"P1 {canonical_json(list(K_SRC))}"
    ]


def test_p1_multi_hop_depth_is_not_dilution() -> None:
    """THE point of G16: a source THREE derivation hops behind the
    emitted fact convicts exactly like a one-hop source. Every interior
    hop used to wash the source out of the charge set; now the closure
    remembers. A charge at a DIFFERENT tick does not clear it (the
    coupling is atomic); the coupled charge does."""
    ledger = Ledger()
    meter = _meter(ledger, [K_SELF, K_SRC])
    anchor = _register_id(ledger, K_SRC)
    ledger.add(DerivationEvent(derived=FACT, consumed=(anchor,),
                               hop_capacity_mbits=50_000, issuer="chamberA", seq=1, tick=1))
    ledger.add(DerivationEvent(derived=FACT2, consumed=(FACT,),
                               hop_capacity_mbits=50_000, issuer="chamberA", seq=2, tick=1))
    ledger.add(DerivationEvent(derived=FACT3, consumed=(FACT2,),
                               hop_capacity_mbits=50_000, issuer="chamberA", seq=3, tick=1))
    assert meter.charge(K_SELF, _est(3_000, "derived:" + FACT3), TOR, tick=2).accepted
    convicted = [f"P1 {canonical_json(list(K_SRC))}"]
    assert ledger.provenance_codes() == convicted

    # paying the source OUTSIDE the coupling (different tick) is not payment
    assert meter.charge(K_SRC, _est(3_000, "derived:" + FACT3), TOR, tick=9).accepted
    assert ledger.provenance_codes() == convicted

    # the coupled charge (same node, tick, channel) clears it
    assert meter.charge(K_SRC, _est(3_000, "derived:" + FACT3), TOR, tick=2).accepted
    assert ledger.provenance_codes() == []


def test_p2_closure_undercount_convicts() -> None:
    """A coupling that names the source but debits it below the DPI
    bound is the dishonest direction, priced exactly: bound =
    min(emission capacity, max-flow) = 3000, paid 1000."""
    ledger = Ledger()
    anchor = _forge(ledger, {"kind": "register", "key": list(K_SRC),
                             "subject_entropy_mbits": 100_000,
                             "ceiling_mbits": 50_000, "issuer": "srcS"})
    _forge(ledger, DerivationEvent(
        derived=FACT, consumed=(anchor,), hop_capacity_mbits=50_000,
        issuer="chamberA", seq=1, tick=1).payload())
    _forge(ledger, _emitted(K_SELF, "n1", 2, "derived:" + FACT, 3_000))
    _forge(ledger, _emitted(K_SRC, "n1", 2, "derived:" + FACT, 1_000, seq=2))
    assert ledger.provenance_codes() == [
        f"P2 {canonical_json(list(K_SRC))}"
    ]


def test_p2_dpi_bound_is_the_min_cut() -> None:
    """A 1000-mbit hop anywhere on the only s->d path caps the bound at
    1000: paying 1000 against a 3000-mbit emission is exact, not an
    undercount. Squeezing below the cut convicts."""
    def build(paid: int) -> Ledger:
        ledger = Ledger()
        anchor = _forge(ledger, {"kind": "register", "key": list(K_SRC),
                                 "subject_entropy_mbits": 100_000,
                                 "ceiling_mbits": 50_000, "issuer": "srcS"})
        _forge(ledger, DerivationEvent(
            derived=FACT, consumed=(anchor,), hop_capacity_mbits=1_000,
            issuer="chamberA", seq=1, tick=1).payload())
        _forge(ledger, DerivationEvent(
            derived=FACT2, consumed=(FACT,), hop_capacity_mbits=50_000,
            issuer="chamberA", seq=2, tick=1).payload())
        _forge(ledger, _emitted(K_SELF, "n1", 2, "derived:" + FACT2, 3_000))
        _forge(ledger, _emitted(K_SRC, "n1", 2, "derived:" + FACT2, paid, seq=2))
        return ledger

    assert build(1_000).provenance_codes() == []          # bound met exactly
    assert build(500).provenance_codes() == [             # below the cut
        f"P2 {canonical_json(list(K_SRC))}"
    ]


def test_p2_parallel_paths_add_and_malformed_capacity_is_unbounded() -> None:
    """Two disjoint routes of 1000 and 2000 mbits carry 3000 together
    (max-flow, not min-hop); a malformed capacity is UNBOUNDED — lying
    with a non-integer never shrinks an obligation."""
    def build(paid: int, second_cap) -> Ledger:
        ledger = Ledger()
        anchor = _forge(ledger, {"kind": "register", "key": list(K_SRC),
                                 "subject_entropy_mbits": 100_000,
                                 "ceiling_mbits": 50_000, "issuer": "srcS"})
        _forge(ledger, {"kind": "derivation", "derived": FACT,
                        "consumed": [anchor], "hop_capacity_mbits": 1_000,
                        "issuer": "chamberA", "seq": 1, "tick": 1})
        _forge(ledger, {"kind": "derivation", "derived": FACT,
                        "consumed": [anchor], "hop_capacity_mbits": second_cap,
                        "issuer": "chamberA", "seq": 2, "tick": 1})
        _forge(ledger, _emitted(K_SELF, "n1", 2, "derived:" + FACT, 10_000))
        _forge(ledger, _emitted(K_SRC, "n1", 2, "derived:" + FACT, paid, seq=2))
        return ledger

    p2 = [f"P2 {canonical_json(list(K_SRC))}"]
    assert build(3_000, 2_000).provenance_codes() == []   # 1000 + 2000 flow
    assert build(2_500, 2_000).provenance_codes() == p2   # below the sum
    # malformed second hop => unbounded => bound = emission capacity 10000
    assert build(3_000, True).provenance_codes() == p2
    assert build(10_000, "wide").provenance_codes() == []


def test_p3_orphaned_derivation_and_merge_resolution() -> None:
    """Ancestry that cannot be walked cannot be charged: an unresolvable
    consumed id convicts the derivation. Like I4, merging in the missing
    fact RESOLVES it — the set growing toward completeness is the honest
    direction. An empty consumed list is a root claim, not an orphan."""
    missing = {"kind": "register", "key": list(K_SRC),
               "subject_entropy_mbits": 100_000, "ceiling_mbits": 1,
               "issuer": "srcS"}
    ledger = Ledger()
    eid = _forge(ledger, DerivationEvent(
        derived=FACT, consumed=(event_id(missing),), hop_capacity_mbits=5,
        issuer="chamberA", seq=1, tick=1).payload())
    assert ledger.provenance_codes() == [f"P3 {eid}"]

    other = Ledger()
    _forge(other, missing)
    ledger.merge(other)
    assert ledger.provenance_codes() == []

    root = _forge(ledger, {"kind": "derivation", "derived": FACT2,
                           "consumed": [], "hop_capacity_mbits": 5,
                           "issuer": "chamberA", "seq": 2, "tick": 1})
    assert ledger.provenance_codes() == []
    assert root  # inert, present


# ---- 3. substrate discipline ----

def test_total_over_adversarial_content() -> None:
    """The fold's oath holds here: no Byzantine derivation or charge may
    crash the auditor. Malformations convict (P3) or are quarantined in
    the escalating direction; nothing raises."""
    ledger = Ledger()
    junk = [
        {"kind": "derivation"},                                   # everything missing
        {"kind": "derivation", "derived": 7, "consumed": [FACT]},
        {"kind": "derivation", "derived": FACT, "consumed": "no"},
        {"kind": "derivation", "derived": FACT, "consumed": [42]},
        {"kind": "derivation", "derived": FACT, "consumed": [FACT],  # self-cycle
         "hop_capacity_mbits": True, "issuer": 9, "seq": -1, "tick": None},
    ]
    for p in junk:
        _forge(ledger, p)
    # charges with adversarial node/tick/key shapes still group somewhere
    _forge(ledger, _emitted(K_SELF, "n1", [1, {"t": 2}], "derived:" + FACT, 100))
    _forge(ledger, {"kind": "charge", "key": "not-a-list", "node": 5,
                    "tick": 1, "channel": "derived:" + FACT,
                    "reason_class": "EMITTED"})
    codes = ledger.provenance_codes()
    assert codes == ledger.provenance_codes()  # deterministic
    assert all(c.split()[0] in ("P1", "P2", "P3") for c in codes)


def test_cycles_terminate_and_still_convict() -> None:
    """A derivation cycle is legal adversarial content: the closure
    walk terminates and the dropped ancestor inside it still convicts."""
    ledger = Ledger()
    anchor = _forge(ledger, {"kind": "register", "key": list(K_SRC),
                             "subject_entropy_mbits": 100_000,
                             "ceiling_mbits": 50_000, "issuer": "srcS"})
    _forge(ledger, {"kind": "derivation", "derived": FACT,
                    "consumed": [FACT2, anchor], "hop_capacity_mbits": 100,
                    "issuer": "chamberA", "seq": 1, "tick": 1})
    _forge(ledger, {"kind": "derivation", "derived": FACT2,
                    "consumed": [FACT], "hop_capacity_mbits": 100,
                    "issuer": "chamberA", "seq": 2, "tick": 1})
    _forge(ledger, _emitted(K_SELF, "n1", 2, "derived:" + FACT, 3_000))
    assert ledger.provenance_codes() == [f"P1 {canonical_json(list(K_SRC))}"]


def test_shuffle_merge_invariance_and_wire_roundtrip() -> None:
    """The P verdict is a function of the event set: any partition,
    any merge order, and a jsonl round-trip agree byte-for-byte."""
    ledger = Ledger()
    meter = _meter(ledger, [K_SELF, K_SRC])
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(_register_id(ledger, K_SRC),),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=1, tick=1))
    meter.charge(K_SELF, _est(3_000, "derived:" + FACT), TOR, tick=2)
    want = ledger.provenance_codes()
    assert want and want[0].startswith("P1 ")

    payloads = [dict(p) for p in ledger.events()]
    rng = random.Random(16)
    for _ in range(5):
        rng.shuffle(payloads)
        cut = rng.randrange(len(payloads) + 1)
        a, b = Ledger(), Ledger()
        for p in payloads[:cut]:
            a._add_payload(event_id(p), p)
        for p in payloads[cut:]:
            b._add_payload(event_id(p), p)
        assert a.copy().merge(b).provenance_codes() == want
        assert b.copy().merge(a).provenance_codes() == want
    assert Ledger.from_jsonl(ledger.to_jsonl()).provenance_codes() == want


def test_x0_covers_derivation_identity_for_free() -> None:
    """Fact identity was NOT re-legislated: two derivations claiming
    (chamberA, derivation, 1) with different bytes are an X0 substrate
    equivocation; the P family adds no identity code."""
    ledger = Ledger()
    for fact in (FACT, FACT2):
        _forge(ledger, {"kind": "derivation", "derived": fact,
                        "consumed": [], "hop_capacity_mbits": 10,
                        "issuer": "chamberA", "seq": 1, "tick": 1})
    subject = canonical_json(["chamberA", "derivation", 1])
    assert ledger.substrate_codes() == [f"X0 {subject}"]
    assert ledger.provenance_codes() == []


# ---- 4. frozen surfaces ----

def test_every_frozen_corpus_has_an_empty_p_verdict() -> None:
    """v1 outputs on provenance-free artifacts are unchanged: every
    frozen conformance artifact folds to an empty P verdict, which is
    why the corpora cannot be disturbed by this Part."""
    here = os.path.dirname(os.path.abspath(__file__))
    paths = []
    for d in ("ledger_traces", "settlement_traces", "settlement2_traces"):
        paths.extend(glob.glob(os.path.join(here, d, "*.jsonl")))
    assert len(paths) >= 20, "corpus went missing?"
    for path in paths:
        with open(path, "r", encoding="ascii") as fh:
            led = Ledger.from_jsonl(fh.read())
        assert led.provenance_codes() == [], path


# ---- 5. settlement fails closed ----

def _dirty_provenance_economy():
    """An honest metered economy whose emission drops an ancestor:
    requesterR's escrow binds to the emission keys; the P1 dirties them.
    Everything else is clean — the P finding is the ONLY dirt."""
    ledger = Ledger()
    k_self = exposure_key("chamberA", "requesterR")
    k_src = exposure_key("srcS", "requesterR")
    meter = _meter(ledger, [k_self, k_src])
    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    bank.deposit("requesterR", 500_000, tick=0)
    escrow = bank.escrow(payer="requesterR", payee="agentOperator",
                         amount_ucr=120_000, charge_keys=[k_self, k_src],
                         expires_tick=100, tick=1)
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(_register_id(ledger, k_src),),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=1, tick=1))
    # the emission couples ONLY the emitter's key — P1 on the source key
    decision, eid = meter.charge_recorded(
        k_self, _est(3_000, "derived:" + FACT), TOR, tick=2)
    assert decision.accepted
    return ledger, meter, bank, escrow, [eid], k_src


def test_release_fails_closed_on_provenance_dirt() -> None:
    """P findings joined the dirty-court stream: the honest issuer
    refuses live, and a forged release convicts S4 after merge."""
    ledger, _meter_, bank, escrow, receipt, k_src = _dirty_provenance_economy()
    assert ledger.audit_codes() == []            # the P1 is the only dirt
    assert ledger.provenance_codes() == [f"P1 {canonical_json(list(k_src))}"]
    try:
        bank.release(escrow, 100_000, receipt, tick=5)
        raise AssertionError("release moved value against a dirty court")
    except SettlementRefused as exc:
        assert "P1" in str(exc)

    _forge(ledger, {"kind": "release", "escrow_id": escrow.id,
                    "amount_ucr": 100_000, "charge_ids": receipt,
                    "issuer": "houseEscrow", "seq": 2, "tick": 5})
    assert any(c.startswith("S4 ") for c in audit_settlement_codes(ledger))


def test_p3_dirt_fails_closed_on_everything() -> None:
    """P3's subject is a derivation id no key map reaches: it falls to
    the fail-closed default and blocks any required_clean release —
    unresolvable ancestry does not move value. Repairing the orphan
    (and the P1) lets the same release settle clean."""
    ledger, meter, bank, escrow, receipt, k_src = _dirty_provenance_economy()
    # repair the P1 with the COUPLED source charge (same node/tick/channel)
    assert meter.charge(k_src, _est(3_000, "derived:" + FACT), TOR, tick=2).accepted
    assert ledger.provenance_codes() == []
    orphan = {"kind": "derivation", "derived": FACT2,
              "consumed": ["sha256:" + "9" * 64], "hop_capacity_mbits": 1,
              "issuer": "elsewhere", "seq": 1, "tick": 3}
    _forge(ledger, orphan)
    try:
        bank.release(escrow, 100_000, receipt, tick=5)
        raise AssertionError("release moved value past an unresolvable ancestry")
    except SettlementRefused as exc:
        assert "P3" in str(exc)


# ---- 6. the node serves the verdict ----

def test_node_audit_serves_p_codes_and_clean_requires_them_empty() -> None:
    """/v1/audit carries `p_codes` beside the I/X/C surfaces, and `clean`
    is false on provenance dirt alone — a P1-dirty artifact whose every
    frozen surface is spotless."""
    import json
    import threading
    import urllib.request

    import node as node_mod

    ledger, _m, _bank, _escrow, _receipt, k_src = _dirty_provenance_economy()
    server = node_mod.serve("127.0.0.1", 0, None, 4 * 1024 * 1024)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        req = urllib.request.Request(
            base + "/v1/events", data=ledger.to_jsonl().encode(), method="POST")
        with urllib.request.urlopen(req) as r:
            assert r.status == 200
        with urllib.request.urlopen(base + "/v1/audit") as r:
            audit = json.loads(r.read())
        assert audit["p_codes"] == [f"P1 {canonical_json(list(k_src))}"]
        assert audit["codes"] == [] and audit["x_codes"] == [] \
            and audit["c_codes"] == []
        assert audit["clean"] is False
    finally:
        server.shutdown()


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"charge-provenance/1 (P-codes): {len(fns)} tests green")
