"""MediationSession — the protocol for incremental third-party work over
private data, with leakage charged on both sides of the boundary.

This is where the kernel meets `mediation.ts`. A guest agent is admitted to
an EXACT tuple of chambers to produce a StructureJudgement. Two facts of the
theory become two charge sites:

  1. OBSERVATION charges.  When the agent reads a member's silo it is
     exposure of that member to the agent-as-reader: the read debits the
     (source=member, reader=agent) exposure account. The node holds a lease
     on that account and runs the kernel accountant; a read that would exceed
     the member's exposure lease is REFUSED, and the agent simply cannot see
     that much of that silo. (Synergy IS cross-exposure — but the cross-terms
     are charged where they become visible: at emission, below.)

  2. EMISSION charges.  When the agent emits the typed judgement toward the
     requester, the requester is a reader too (mediation law: the requester
     is not a privileged sink). A single judgement carries information about
     EVERY member of the tuple, so the emission debits the requester's
     exposure account against every member ATOMICALLY: all accounts accept,
     or none is debited (demand still accrues everywhere — the attempt was
     real). This is the operational form of "the emission is not separable
     from its inputs", now in BOTH directions: a partial emission cannot
     happen, and a refused emission cannot leave phantom debits behind.

Between the two, canonicality review is a gate, not a charge: it decides
admissibility of the agent (requested vs justified capacity) before any lease
is spent. Here it is represented by an admissibility callback; the full
review agent lives above the kernel.

HONEST RESUMPTION. A lease outlives any one session. On construction the
session replays every prior charge bound to its leases (Ledger.lease_usage)
and hydrates the local accountant — cumulative, demand, the blocked latch,
the incident latch, and the next charge_seq. Without this, a restarted node
re-runs from zero and the API itself walks an HONEST node into overspending
its lease (audit I3 would then convict the innocent). With it, honest nodes
cannot violate I3 even across arbitrarily many session restarts.

CLOCK DOMAIN. `tick` is a declared integer label in the LEASE ISSUER's clock
domain — the same domain as `expires_tick`. Callers that have a declared
clock pass it per charge; otherwise the session advances an internal counter.
An honest session refuses to charge a lease past its expiry; a dishonest node
that lies about ticks is exactly what audit I4 catches after merge.

Every accepted or refused step is a ChargeEvent in the shared ledger, so the
session's court file is just the ledger's fold restricted to this session's
keys — evidence a stranger can replay.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .accountant import (
    Accountant,
    CapacityEstimate,
    Decision,
    EstimatorAttestation,
    Key,
    exposure_key,
)
from .events import LeaseEvent
from .identity import Signer, require_signer
from .leases import LeaseSpender
from .ledger import Ledger


class SessionRefused(Exception):
    pass


@dataclass
class ObservationResult:
    member: str
    decision: Decision
    event_id: str


@dataclass
class EmissionResult:
    """The full outcome of one emission attempt: one result per member, in
    tuple order, plus the decisive decision (the first refusal if refused,
    else the last accept)."""

    accepted: bool
    results: List[ObservationResult]
    decision: Decision
    event_id: str


@dataclass
class MediationSession(LeaseSpender):
    """One admitted guest agent working over one exact tuple of chambers.

    node:        the executing node's id. Every lease this session holds MUST
                 be leased to this node (checked at construction) — a session
                 cannot spend another node's lease.
    agent_entity: the guest agent's beneficial-entity id — the READER whose
                 cumulative exposure to each member is what accrues.
    requester_entity: the party the judgement is emitted toward — also a
                 reader, charged on emission.
    tuple_members: the exact k chambers (k >= 2). Order is normalized by the
                 caller; the tuple identity lives in mediation.ts.
    leases:      per (exposure_key) the LeaseEvent this node spends against.
    ledger:      the shared, mergeable ledger every step is written to. Prior
                 charges against these leases are REPLAYED into the local
                 accountant at construction (honest resumption).
    node_signer: charge-identity/2 (IDENTITY-SPEC §7): required when the
                 node id is a key — every recorded charge is then signed;
                 a key-shaped id without its signer refuses at
                 construction (same law as KernelMeter, via the shared
                 LeaseSpender core).
    """

    node: str
    agent_entity: str
    requester_entity: str
    tuple_members: Sequence[str]
    leases: Dict[Key, LeaseEvent]
    ledger: Ledger
    accountant: Accountant = field(default_factory=Accountant)
    clock: int = 0  # last declared tick seen (issuer clock domain)
    node_signer: Optional[Signer] = None
    _next_seq: Dict[str, int] = field(default_factory=dict)  # lease_id -> next charge_seq

    def __post_init__(self) -> None:
        self.node_signer = require_signer(self.node, self.node_signer, "session node")
        if len(self.tuple_members) < 2:
            raise SessionRefused("a mediation tuple needs >= 2 members")

        accounts = self.ledger.fold()
        for key, lease in self.leases.items():
            if lease.node != self.node:
                raise SessionRefused(
                    f"lease for {key} is held by node {lease.node!r}, not {self.node!r}"
                )
            acct = accounts.get(key)
            if acct is None:
                raise SessionRefused(f"no registered account for leased key {key}")
            if acct.conflicted:
                raise SessionRefused(
                    f"registration for {key} is conflicted; refusing to operate on it"
                )

            self._hydrate_lease(key, lease, acct.subject_entropy_mbits)

    Refused = SessionRefused

    def _spent_leases(self) -> Dict[Key, LeaseEvent]:
        return self.leases

    # ---- observation ----

    def observe(
        self,
        member: str,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: Optional[int] = None,
    ) -> ObservationResult:
        """Agent reads `member`'s silo. Charges the agent-as-reader against
        that member's (source=member, reader=agent) exposure account."""
        if member not in self.tuple_members:
            raise SessionRefused(f"{member} is not in this session's tuple")
        key = exposure_key(member, self.agent_entity)
        lease = self.leases.get(key)
        if lease is None:
            raise SessionRefused(f"no lease held for {key}")
        t = self._resolve_tick(tick)
        self._check_live(lease, t)
        decision = self.accountant.charge(key, estimate, estimator, t)
        eid = self._record_charge(key, lease, t, estimate, estimator, decision)
        return ObservationResult(member=member, decision=decision, event_id=eid)

    # ---- emission ----

    def emit(
        self,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: Optional[int] = None,
    ) -> EmissionResult:
        """Agent emits the typed judgement toward the requester: one ATOMIC
        coupled charge of the requester-as-reader against every member.

        All member accounts accept, or none is debited. Demand accrues on
        every account either way — the attempt carried real extraction
        pressure toward every member. Members that would individually refuse
        get their true SPEC reason (and a ceiling refusal latches, per SPEC
        step D); solvent members refused only by the coupling report
        REFUSED_COUPLED with no debit and no latch."""
        keys: List[Key] = []
        for member in self.tuple_members:
            key = exposure_key(member, self.requester_entity)
            if key not in self.leases:
                raise SessionRefused(f"no requester-exposure lease for member {member}")
            keys.append(key)

        t = self._resolve_tick(tick)
        # Atomicity includes liveness: if ANY involved lease is expired,
        # refuse before any state moves.
        for key in keys:
            self._check_live(self.leases[key], t)

        decisions = self.accountant.charge_coupled(keys, estimate, estimator, t)

        results: List[ObservationResult] = []
        decisive: Optional[ObservationResult] = None
        for member, key in zip(self.tuple_members, keys):
            decision = decisions[key]
            eid = self._record_charge(key, self.leases[key], t, estimate, estimator, decision)
            r = ObservationResult(member=member, decision=decision, event_id=eid)
            results.append(r)
            if decisive is None and not decision.accepted and decision.reason_class != "REFUSED_COUPLED":
                decisive = r

        accepted = all(r.decision.accepted for r in results)
        if accepted:
            decisive = results[-1]
        elif decisive is None:
            decisive = results[0]  # e.g. all-REFUSED_ESTIMATOR
        return EmissionResult(
            accepted=accepted,
            results=results,
            decision=decisive.decision,
            event_id=decisive.event_id,
        )
