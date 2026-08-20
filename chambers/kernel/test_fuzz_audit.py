"""Detector-completeness fuzz lane for charge-ledger/1 audit (ASSURANCE L3).

Two directions, both load-bearing:

  SOUNDNESS (no false positives): randomly generated HONEST multi-node
  deployments — many keys, leases partitioned across nodes, mixed
  accepted/refused/inadmissible charges, session restarts — must audit
  CLEAN, and their fold must respect every ceiling.

  COMPLETENESS (no missed crimes): every Byzantine mutation class the
  protocol claims to detect is injected into an honest ledger and MUST be
  convicted with its expected I-code. A detector that cannot be shown to
  fire is not a detector.

Probe integrity: every mutation asserts that it actually changed the event
set before asserting detection — a vacuous injection must fail the test,
not pass it. Convergence: audit verdicts are recomputed after a seeded
3-shard shuffle-merge and must be identical (the verdict is a function of
the set, not the order).

Deterministic: fixed seeds only. Run:
  python3 chambers/kernel/test_fuzz_audit.py
"""
from __future__ import annotations

import os
import random
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import (  # noqa: E402
    Accountant,
    CapacityEstimate,
    EstimatorAttestation,
    composition_key,
)
from chambers.kernel.events import ChargeEvent, RegisterEvent, event_id  # noqa: E402
from chambers.kernel.leases import LeaseIssuer  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
SELFISH = EstimatorAttestation("selfmeter", "self_interested", "m", True)

HONEST_SEEDS = range(20)
MUTATION_SEEDS = range(8)


def gen_honest(seed: int) -> Ledger:
    """A random honest multi-node deployment. Every rule an honest node
    follows is followed: leases sum <= ceiling, only the leased node
    charges, seq is per-(node,lease) monotone from 1, tick <= expiry,
    decisions come from a hydrating accountant per lease."""
    rng = random.Random(seed)
    ledger = Ledger()
    n_keys = rng.randint(1, 4)
    for k in range(n_keys):
        key = composition_key(f"subj{k}", rng.choice(["reach", "diff", "rank"]), f"aud{k % 2}")
        entropy = rng.randint(50, 500) * 1000
        ceiling = rng.randint(10, entropy // 1000) * 1000
        issuer = LeaseIssuer(issuer=f"owner{k}", ledger=ledger)
        issuer.register(key, entropy, ceiling)
        remaining = ceiling
        n_leases = rng.randint(1, 3)
        for ln in range(n_leases):
            if remaining <= 0:
                break
            amount = rng.randint(1, remaining)
            remaining -= amount
            expires = rng.randint(20, 60)
            lease = issuer.grant(key, node=f"node{ln}", amount_mbits=amount, expires_tick=expires)
            # the node's honest accountant over this lease, possibly with a
            # "restart" (fresh Accountant hydrated by replaying its own facts —
            # here modeled by continuing seq/tick correctly).
            acc = Accountant()
            acc.register(key, entropy, amount)
            seq = 1
            tick = 0
            for _ in range(rng.randint(1, 6)):
                tick += rng.randint(1, 3)
                if tick > expires:
                    break  # honest node refuses to charge an expired lease
                estimator = SELFISH if rng.random() < 0.15 else TOR
                est = CapacityEstimate(rng.randint(0, amount + 2000), 0, 0, 0, 0, "c")
                dec = acc.charge(key, est, estimator, tick)
                ledger.add(
                    ChargeEvent.from_decision(key, f"node{ln}", lease.id, seq, tick, est, estimator, dec)
                )
                seq += 1
    return ledger


def _leases_of(ledger: Ledger) -> List[dict]:
    return [p for p in ledger.events() if p.get("kind") == "lease"]


def _charges_of(ledger: Ledger) -> List[dict]:
    return [p for p in ledger.events() if p.get("kind") == "charge"]


def _forge(ledger: Ledger, payload: dict) -> None:
    before = ledger.event_count()
    ledger._add_payload(event_id(payload), payload)
    assert ledger.event_count() == before + 1, "mutation did not inject a new fact"


def _charge_like(lease: dict, **over) -> dict:
    p = {
        "kind": "charge", "key": list(lease["key"]), "node": lease["node"],
        "lease_id": event_id(lease), "charge_seq": 900, "tick": 1, "channel": "z",
        "estimate_total_mbits": 1000, "estimator_id": "e",
        "estimator_independence": "adversarial_review", "estimator_worst_case": True,
        "accepted": True, "reason_class": "EMITTED", "reason_detail": "emitted_debited",
        "demand_mbits": 1000, "debit_mbits": 1000,
    }
    p.update(over)
    return p


# each mutation: name -> (inject(ledger, rng), expected_code)

def m_overspend(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, estimate_total_mbits=10**9,
                                demand_mbits=10**9, debit_mbits=10**9))


def m_foreign_node(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, node="evilNode"))


def m_late_tick(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, tick=lease["expires_tick"] + rng.randint(1, 99)))


def m_unknown_lease(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, lease_id="sha256:" + "f" * 64))


def m_key_mismatch(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, key=["comp", "otherSubject", "q", "a"]))


def m_negative_debit(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, debit_mbits=-rng.randint(1, 10**6)))


def m_bad_seq(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, charge_seq=0))


def m_bad_reason(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, reason_class="REFUSED_VIBES", accepted=False,
                                debit_mbits=0))


def m_inconsistent_accept(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, _charge_like(lease, accepted=False, reason_class="REFUSED_CEILING",
                                reason_detail="would_exceed_ceiling", debit_mbits=1000))


def m_rogue_lease(ledger: Ledger, rng: random.Random) -> None:
    _forge(ledger, {
        "kind": "lease", "key": ["comp", "ghost", "q", "a"], "lease_seq": 1,
        "node": "nX", "amount_mbits": 10, "issuer": "nobody", "expires_tick": 9,
    })


def m_impostor_issuer(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    _forge(ledger, {
        "kind": "lease", "key": list(lease["key"]), "lease_seq": 777,
        "node": "nX", "amount_mbits": 1, "issuer": "impostor",
        "expires_tick": 9,
    })


def m_register_conflict(ledger: Ledger, rng: random.Random) -> None:
    reg = rng.choice([p for p in ledger.events() if p.get("kind") == "register"])
    _forge(ledger, {
        "kind": "register", "key": list(reg["key"]),
        "subject_entropy_mbits": max(1, reg["subject_entropy_mbits"] // 2),
        "ceiling_mbits": max(0, reg["ceiling_mbits"] // 2),
        "issuer": reg["issuer"],
    })


def m_equivocation(ledger: Ledger, rng: random.Random) -> None:
    charge = rng.choice(_charges_of(ledger))
    twin = dict(charge)
    twin["channel"] = charge.get("channel", "c") + "_twin"  # same identity, different bytes
    _forge(ledger, twin)


def m_overgrant(ledger: Ledger, rng: random.Random) -> None:
    lease = rng.choice(_leases_of(ledger))
    reg = next(p for p in ledger.events()
               if p.get("kind") == "register" and p["key"] == lease["key"])
    _forge(ledger, {
        "kind": "lease", "key": list(lease["key"]), "lease_seq": 888,
        "node": "nY", "amount_mbits": reg["ceiling_mbits"] + 1,
        "issuer": reg["issuer"], "expires_tick": 9,
    })


MUTATIONS: List[Tuple[str, object, str]] = [
    ("overspend", m_overspend, "I3"),
    ("foreign_node", m_foreign_node, "I4"),
    ("late_tick", m_late_tick, "I4"),
    ("unknown_lease", m_unknown_lease, "I4"),
    ("key_mismatch", m_key_mismatch, "I4"),
    ("negative_debit", m_negative_debit, "I6"),
    ("bad_seq", m_bad_seq, "I6"),
    ("bad_reason", m_bad_reason, "I6"),
    ("inconsistent_accept", m_inconsistent_accept, "I6"),
    ("rogue_lease", m_rogue_lease, "I5"),
    ("impostor_issuer", m_impostor_issuer, "I5"),
    ("register_conflict", m_register_conflict, "I7"),
    ("equivocation", m_equivocation, "I8"),
    ("overgrant", m_overgrant, "I1"),
]


def _shuffled_verdict(ledger: Ledger, rng: random.Random) -> List[str]:
    """Recompute the verdict after a 3-shard shuffle-merge — the verdict
    must be a function of the set, not of arrival order."""
    lines = ledger.to_jsonl().strip().splitlines()
    rng.shuffle(lines)
    shards = [Ledger.from_jsonl("\n".join(lines[i::3])) for i in range(3)]
    rng.shuffle(shards)
    merged = shards[0].copy()
    for s in shards[1:]:
        merged.merge(s)
    return merged.audit_codes()


def test_honest_runs_audit_clean() -> None:
    total_events = 0
    for seed in HONEST_SEEDS:
        ledger = gen_honest(seed)
        assert ledger.event_count() > 0
        total_events += ledger.event_count()
        codes = ledger.audit_codes()
        assert codes == [], f"seed {seed}: false positives {codes}"
        for key, acct in ledger.fold().items():
            assert acct.cumulative_mbits <= acct.ceiling_mbits, (seed, key)
        assert _shuffled_verdict(ledger, random.Random(seed * 7 + 1)) == []
    print(f"soundness: {len(list(HONEST_SEEDS))} honest deployments "
          f"({total_events} events) audit clean, order-independent")


def test_every_mutation_class_detected() -> None:
    fired = 0
    for name, inject, code in MUTATIONS:
        for seed in MUTATION_SEEDS:
            ledger = gen_honest(seed)
            baseline = ledger.audit_codes()
            assert baseline == [], f"seed {seed} not clean before mutation"
            inject(ledger, random.Random(seed * 1000 + 13))
            codes = ledger.audit_codes()
            hit = [c for c in codes if c.startswith(code + " ")]
            assert hit, f"{name} (seed {seed}): expected {code}, got {codes}"
            # the verdict survives shuffle-merge (conviction is order-free)
            reshuffled = _shuffled_verdict(ledger, random.Random(seed * 31 + 5))
            assert reshuffled == codes, f"{name} (seed {seed}): verdict order-dependent"
            fired += 1
    print(f"completeness: {len(MUTATIONS)} mutation classes x "
          f"{len(list(MUTATION_SEEDS))} seeds = {fired} convictions, all correct codes")


def _run_all() -> None:
    test_honest_runs_audit_clean()
    test_every_mutation_class_detected()
    print("\nfuzz lane green")


if __name__ == "__main__":
    _run_all()
