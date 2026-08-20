"""Lease issuance and spending for charge-kernel/2 — how a ceiling holds
across nodes.

Eventual consistency alone cannot enforce a ceiling: two nodes spending the
same budget concurrently can jointly overspend it and merge will only report
the corpse. The kernel's answer is PARTITION, not consensus: the key's owner
(the source chamber — the party whose secret the ceiling protects, so no
external coordinator is being trusted) issues leases whose amounts never sum
past the ceiling. A node accepts charges ONLY against a live lease it holds,
running an unmodified accountant whose local ceiling is the lease amount.

Global cap theorem (the whole point, stated for the Lean rung):
    sum over leases of amount <= ceiling            (issuer refuses past it)
    per node: accepted debits <= its lease amount   (accountant step D/E)
    => sum of all accepted debits <= ceiling, under ANY interleaving,
       with zero coordination at charge time.

The price of partition is honest: unspent lease remainder is stranded until
expiry (utilization, not safety); expiry needs a tick source (declared,
lamport-ish, not wall-clock-trusted); and a node that lies about its local
accountant is caught by ledger.audit(), after the fact — Byzantine nodes are
detected, not prevented (see PROTOCOL.md non-claims).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .accountant import CapacityEstimate, Decision, EstimatorAttestation, Key
from .covenant import grant_violates_covenants
from .events import ChargeEvent, LeaseEvent, RegisterEvent
from .identity import Signer, require_signer
from .ledger import Ledger


class LeaseSpender:
    """The issuer's counterpart: shared lease-SPENDING core for the
    kernel's two charging front-ends (KernelMeter, MediationSession).
    One implementation of the declared-tick clock, per-lease charge
    sequencing, honest-resumption hydration, charge-identity/2 signed
    recording, and the court-file fold — so the two front-ends cannot
    drift on any of them. A front-end supplies the attributes `node`,
    `clock`, `ledger`, `accountant`, `node_signer`, `_next_seq`, and
    the `_spent_leases()` hook naming the leases it spends."""

    def _spent_leases(self) -> Dict[Key, LeaseEvent]:
        raise NotImplementedError

    # ---- clock (issuer domain: declared ticks, else a local counter) ----

    def _resolve_tick(self, tick: Optional[int]) -> int:
        if tick is None:
            self.clock += 1
            return self.clock
        self.clock = max(self.clock, tick)
        return tick

    # ---- sequencing and honest resumption ----

    def _take_seq(self, lease: LeaseEvent) -> int:
        seq = self._next_seq[lease.id]
        self._next_seq[lease.id] = seq + 1
        return seq

    def _hydrate_lease(
        self, key: Key, lease: LeaseEvent, subject_entropy_mbits: int
    ) -> None:
        """Register the local accountant with the LEASE as the ceiling,
        then replay every prior charge bound to the lease (restart-safe:
        cumulative, demand, the latches, and the next charge_seq)."""
        state = self.accountant.register(
            key,
            subject_entropy_mbits=subject_entropy_mbits,
            ceiling_mbits=lease.amount_mbits,
        )
        usage = self.ledger.lease_usage(lease.id)
        self._next_seq[lease.id] = usage.hydrate(
            state, lease.amount_mbits, subject_entropy_mbits
        )

    # ---- recording ----

    def _record_charge(
        self,
        key: Key,
        lease: LeaseEvent,
        tick: int,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        decision: Decision,
    ) -> str:
        """One ChargeEvent in the shared ledger, whatever the decision
        was (refusals are facts) — signed when the node authors under a
        key (charge-identity/2)."""
        event = ChargeEvent.from_decision(
            key=key,
            node=self.node,
            lease_id=lease.id,
            charge_seq=self._take_seq(lease),
            tick=tick,
            estimate=estimate,
            estimator=estimator,
            decision=decision,
        )
        if self.node_signer is not None:
            event = self.node_signer.sign(event)
        return self.ledger.add(event)

    # ---- evidence ----

    def court_file(self) -> Dict[Key, dict]:
        """The ledger fold restricted to this spender's keys — the
        record a stranger recomputes from the merged ledger."""
        touched = set(self._spent_leases().keys())
        out: Dict[Key, dict] = {}
        for key, acct in self.ledger.fold().items():
            if key in touched:
                out[key] = {
                    "cumulative_mbits": acct.cumulative_mbits,
                    "demanded_mbits": acct.demanded_mbits,
                    "ceiling_mbits": acct.ceiling_mbits,
                    "leakage_class": acct.leakage_class,
                    "incident": acct.incident,
                    "conflicted": acct.conflicted,
                }
        return out


class LeaseRefused(Exception):
    pass


@dataclass
class LeaseIssuer:
    """The key owner's issuing authority. One issuer of record per key.

    charge-identity/2 (IDENTITY-SPEC §7): construct with `signer` when the
    issuer id is a key — every registration and lease is then signed, and
    the constructor refuses the three ways this could go wrong (key author
    without a signer, mismatched signer, signer on a legacy string)."""

    issuer: str
    ledger: Ledger
    signer: Optional[Signer] = None
    _registered: Dict[Key, RegisterEvent] = field(default_factory=dict)
    _granted: Dict[Key, int] = field(default_factory=dict)
    _seq: Dict[Key, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.signer = require_signer(self.issuer, self.signer, "lease issuer")

    def register(self, key: Key, subject_entropy_mbits: int, ceiling_mbits: int) -> RegisterEvent:
        if key in self._registered:
            return self._registered[key]
        ev = RegisterEvent(
            key=key,
            subject_entropy_mbits=subject_entropy_mbits,
            ceiling_mbits=ceiling_mbits,
            issuer=self.issuer,
        )
        if self.signer is not None:
            ev = self.signer.sign(ev)
        self.ledger.add(ev)
        self._registered[key] = ev
        self._granted.setdefault(key, 0)
        self._seq.setdefault(key, 0)
        return ev

    def grant(self, key: Key, node: str, amount_mbits: int, expires_tick: int) -> LeaseEvent:
        """Grant a slice of the remaining ceiling to a node. Refuses to
        over-grant — this refusal IS the global cap enforcement."""
        reg = self._registered.get(key)
        if reg is None:
            raise LeaseRefused("key not registered by this issuer")
        if amount_mbits <= 0:
            raise LeaseRefused("lease amount must be positive")
        granted = self._granted[key]
        if granted + amount_mbits > reg.ceiling_mbits:
            raise LeaseRefused(
                f"would over-grant: {granted} + {amount_mbits} > ceiling {reg.ceiling_mbits}"
            )
        # charge-covenant/1: the issuer's own declared self-restrictions
        # bind its future authority (E5 — the exit story's other half).
        why = grant_violates_covenants(
            self.ledger.payloads(), self.issuer, key,
            amount_mbits, expires_tick,
        )
        if why is not None:
            raise LeaseRefused(why)
        self._seq[key] += 1
        ev = LeaseEvent(
            key=key,
            lease_seq=self._seq[key],
            node=node,
            amount_mbits=amount_mbits,
            issuer=self.issuer,
            expires_tick=expires_tick,
        )
        if self.signer is not None:
            ev = self.signer.sign(ev)
        self.ledger.add(ev)
        self._granted[key] = granted + amount_mbits
        return ev

    def remaining(self, key: Key) -> Optional[int]:
        reg = self._registered.get(key)
        if reg is None:
            return None
        return reg.ceiling_mbits - self._granted[key]
