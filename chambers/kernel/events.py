"""Content-addressed ledger events for charge-kernel/2.

Every fact in the distributed ledger is an immutable event with a canonical
JSON encoding and a sha256 id derived from that encoding. Merge is union by
id; two events with the same id MUST be byte-identical (ledger.py enforces
this). Nothing here is ever mutated or deleted — the ledger is grow-only,
which is what makes merge a CRDT join and replay deterministic.

Integer-only discipline: events carry integer millibits exclusively. The
estimator's floats died before the event was born.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

from accountant import CapacityEstimate, Decision, EstimatorAttestation, Key


def canonical_json(payload: Dict[str, Any]) -> str:
    """Deterministic encoding: sorted keys, tight separators, ASCII."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def event_id(payload: Dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("ascii")).hexdigest()


def is_uint(v: Any) -> bool:
    """KERNEL-SPEC §0 integer discipline: a non-negative int that is not a
    bool (Python's bool subclasses int — the exact trap the spec warns
    about). The one shared validity predicate; every kernel module that
    guards adversarial payloads imports this rather than re-deriving it."""
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _key_list(key: Key) -> list:
    return list(key)


@dataclass(frozen=True)
class RegisterEvent:
    """The key's owner declares the account: entropy and TRUE ceiling.

    Exactly one registration is canonical per key; the key's owner (the
    source chamber) is the single issuer of record. A conflicting
    registration is NOT a fatal merge error — that would let one poison
    event deny audit forever. The fold quarantines conflicts conservatively
    (minimum entropy and ceiling — severity only escalates) and audit
    reports them as I7 findings (ledger.py).
    """

    key: Key
    subject_entropy_mbits: int
    ceiling_mbits: int
    issuer: str  # the owning chamber / its signing identity
    # charge-identity/1: ADDITIVE, serialized only when present — every
    # unsigned event keeps its exact historical bytes (frozen corpora
    # unmoved). Set by identity.Signer.sign(); covered by the event id.
    sig: Optional[str] = None

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "register",
            "key": _key_list(self.key),
            "subject_entropy_mbits": self.subject_entropy_mbits,
            "ceiling_mbits": self.ceiling_mbits,
            "issuer": self.issuer,
        }
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class LeaseEvent:
    """The key's issuer grants a node a slice of the ceiling.

    The global invariant lives here: for any key, the sum of granted lease
    amounts never exceeds the registered ceiling (leases.py refuses to issue
    past it). A node may only ACCEPT charges against a lease it holds, with
    the lease amount as its local ceiling — therefore the sum of accepted
    bits across all nodes is <= ceiling under ANY interleaving, with no
    coordination at charge time. Leases expire by tick; they are never
    retroactively revoked (decisions already made against them stand).
    """

    key: Key
    lease_seq: int  # issuer-local sequence number, unique per key
    node: str
    amount_mbits: int
    issuer: str
    expires_tick: int
    sig: Optional[str] = None  # charge-identity/1: additive, see RegisterEvent

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "lease",
            "key": _key_list(self.key),
            "lease_seq": self.lease_seq,
            "node": self.node,
            "amount_mbits": self.amount_mbits,
            "issuer": self.issuer,
            "expires_tick": self.expires_tick,
        }
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class DerivationEvent:
    """charge-provenance/1 (KERNEL-SPEC Part III) — the ancestry edge.

    The deriving chamber declares: fact `derived` was produced from the
    facts in `consumed` (content ids — ledger event ids or other derived
    fact ids), and this hop can carry at most `hop_capacity_mbits` of the
    consumed material into the derived fact. The declaration is what the
    P-audit convicts against: an emission of `derived` must couple charges
    on the exposure keys of every source in the transitive closure (P1),
    at the min-cut DPI bound the declared capacities imply (P2), and a
    consumed id that resolves to nothing is an orphaned ancestry (P3).

    Carries no value and no leakage; the fold ignores it. Fact identity
    is X0's for free: (issuer, "derivation", seq) equivocation convicts
    with no code added here.
    """

    derived: str
    consumed: Tuple[str, ...]
    hop_capacity_mbits: int
    issuer: str
    seq: int
    tick: int

    def payload(self) -> Dict[str, Any]:
        return {
            "kind": "derivation",
            "derived": self.derived,
            "consumed": list(self.consumed),
            "hop_capacity_mbits": self.hop_capacity_mbits,
            "issuer": self.issuer,
            "seq": self.seq,
            "tick": self.tick,
        }

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class ChargeEvent:
    """One local, FINAL charge decision, bound to the lease it spent against.

    Decisions are facts: merging never re-litigates them. A refused decision
    (estimator, lease-ceiling, blocked) is as final as an emit. `demand_mbits`
    is the admissible demand this event contributed (0 for REFUSED_ESTIMATOR),
    `debit_mbits` the accepted leakage (0 unless EMITTED) — the two monotone
    counters of the SPEC, carried per-event so the global fold is a plain sum
    over a set.

    FACT IDENTITY. `charge_seq` is the node-local, per-lease, strictly
    monotone sequence number of this charge (1, 2, 3, …). It exists because
    content addressing alone conflates "same bytes" with "same fact": two
    REAL charges with identical fields (a session restart replays the same
    estimate at the same local tick) would hash to one id, and union-by-id
    would silently drop one — an UNDERCOUNT of leakage, the dishonest
    direction. With (node, lease_id, charge_seq) in the payload, distinct
    facts have distinct ids by construction, and two different events
    claiming the same (node, lease_id, charge_seq) are an equivocation the
    audit flags (I8). `tick` is thereby freed to be a pure declared clock
    label in the lease issuer's domain (checked against lease expiry, I4).
    """

    key: Key
    node: str
    lease_id: str
    charge_seq: int
    tick: int
    channel: str
    estimate_total_mbits: int
    estimator_id: str
    estimator_independence: str
    estimator_worst_case: bool
    accepted: bool
    reason_class: str
    reason_detail: str
    demand_mbits: int
    debit_mbits: int
    sig: Optional[str] = None  # charge-identity/1: additive, see RegisterEvent

    @staticmethod
    def from_decision(
        key: Key,
        node: str,
        lease_id: str,
        charge_seq: int,
        tick: int,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        decision: Decision,
    ) -> "ChargeEvent":
        admissible = decision.reason_class != "REFUSED_ESTIMATOR"
        return ChargeEvent(
            key=key,
            node=node,
            lease_id=lease_id,
            charge_seq=charge_seq,
            tick=tick,
            channel=estimate.channel,
            estimate_total_mbits=estimate.total_mbits,
            estimator_id=estimator.estimator_id,
            estimator_independence=estimator.independence,
            estimator_worst_case=estimator.worst_case_over_secrets,
            accepted=decision.accepted,
            reason_class=decision.reason_class,
            reason_detail=decision.reason_detail,
            demand_mbits=estimate.total_mbits if admissible else 0,
            debit_mbits=estimate.total_mbits if decision.accepted else 0,
        )

    def payload(self) -> Dict[str, Any]:
        d = asdict(self)
        d["key"] = _key_list(self.key)
        d["kind"] = "charge"
        if d.get("sig") is None:
            d.pop("sig", None)  # unsigned bytes stay exactly historical
        return d

    @property
    def id(self) -> str:
        return event_id(self.payload())
