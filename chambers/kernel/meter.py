"""KernelMeter — the single-node convenience form of charge-kernel/2.

Most consumers of the kernel are not multi-node: a simulation, a single
chamber runtime, a bounty engine. What they need is "register an account,
charge it, and leave a court-grade event trail" without hand-wiring issuer,
lease, hydration, and sequence numbers. KernelMeter is that wrapper, and it
deliberately runs the FULL distributive path rather than a shortcut:

    register(key, entropy, ceiling)
        -> RegisterEvent by this meter's issuer
        -> one self-granted lease for the full ceiling to this node
        -> local accountant hydrated from the ledger's replay of that lease

    charge(key, estimate, estimator)
        -> exact SPEC decision, ChargeEvent bound to the lease, seq'd

so every meter run produces a mergeable, auditable jsonl ledger artifact —
the same object a genuinely distributed deployment gossips. A stranger runs
`Ledger.audit()` over the artifact and re-derives every number. There is one
accounting path in this codebase, not a "lite" one for sims.

The meter is a SINGLE-node authority: issuer and node are the same party.
That is honest for a sim or a local runtime (the party charging is the party
whose ceiling it is); the multi-node trust story lives in leases.py/session.py.

Ceiling raises: the kernel's audit resolves conflicting registrations to the
MINIMUM ceiling, so an account's ceiling cannot be raised in place — by
design (a raise would retract severity under merge). Consent to reveal more
(a paid method reveal, a settlement) is modeled as a NEW account under a new
key, registered with its own ceiling — see ip_trade_sim for the pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .accountant import (
    Accountant,
    CapacityEstimate,
    Decision,
    EstimatorAttestation,
    Key,
)
from .events import ChargeEvent, LeaseEvent
from .identity import Signer, require_signer
from .leases import LeaseIssuer
from .ledger import Ledger

# A meter's self-granted lease never expires on its own authority; expiry
# discipline is a multi-node concern (session.py). Large, explicit, integer.
NEVER_EXPIRES_TICK = 2**62


class MeterRefused(Exception):
    pass


@dataclass
class KernelMeter:
    """One node's complete, auditable metering front-end.

    node:   the executing node id (also the lease holder).
    issuer: the issuing authority id recorded on registrations and leases.
    ledger: the shared, mergeable ledger every fact is written to. May be
            shared with other meters/sessions; hydration makes that safe.
    """

    node: str
    issuer: str
    ledger: Ledger
    accountant: Accountant = field(default_factory=Accountant)
    clock: int = 0
    # charge-identity/2 (IDENTITY-SPEC §7): the meter authors under TWO
    # ids — `issuer` on registrations/leases, `node` on charges — so it
    # takes two signers. Fail-closed: a key-shaped id without its signer
    # refuses at construction.
    issuer_signer: Optional[Signer] = None
    node_signer: Optional[Signer] = None
    _issuer: LeaseIssuer = field(init=False)
    _leases: Dict[Key, LeaseEvent] = field(default_factory=dict)
    _next_seq: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.node_signer = require_signer(self.node, self.node_signer, "meter node")
        self._issuer = LeaseIssuer(
            issuer=self.issuer, ledger=self.ledger, signer=self.issuer_signer
        )

    # ---- registration ----

    def register(
        self,
        key: Key,
        subject_entropy_mbits: int,
        ceiling_mbits: int,
    ) -> None:
        """Idempotent: register the account, self-grant the full ceiling as
        one lease, hydrate the local accountant from the ledger's replay.

        ceiling_mbits must be > 0: a lease must have positive amount. A key
        you never want to emit on needs no account at all — refusing to
        register IS the zero ceiling."""
        if key in self._leases:
            return
        if ceiling_mbits <= 0:
            raise MeterRefused(
                "KernelMeter needs ceiling_mbits > 0 (an unregistered key already emits nothing)"
            )
        self._issuer.register(key, subject_entropy_mbits, ceiling_mbits)
        lease = self._issuer.grant(
            key, node=self.node, amount_mbits=ceiling_mbits, expires_tick=NEVER_EXPIRES_TICK
        )
        self._leases[key] = lease
        state = self.accountant.register(
            key, subject_entropy_mbits=subject_entropy_mbits, ceiling_mbits=ceiling_mbits
        )
        usage = self.ledger.lease_usage(lease.id)
        self._next_seq[lease.id] = usage.hydrate(state, lease.amount_mbits, subject_entropy_mbits)

    def adopt(self, key: Key, lease: LeaseEvent, subject_entropy_mbits: int) -> None:
        """Wire an EXTERNALLY-issued lease into this meter — the tail of
        register() without the self-grant. This is the deployment shape:
        the account's issuer of record is another party (the receiver for
        attention keys, the source chamber for exposure keys); this node
        merely holds a lease addressed to it and runs an unmodified
        accountant whose local ceiling is the LEASE amount (leases.py's
        global-cap partition). Hydration replays every prior charge bound
        to the lease, so adoption is restart-safe. Idempotent per key —
        one lease per key per meter lifetime (a renewed budget is a new
        key: the epoch pattern)."""
        if key in self._leases:
            return
        if lease.node != self.node:
            raise MeterRefused(
                f"lease is addressed to node {lease.node!r}, not this node {self.node!r}"
            )
        state = self.accountant.register(
            key, subject_entropy_mbits=subject_entropy_mbits, ceiling_mbits=lease.amount_mbits
        )
        self._leases[key] = lease
        usage = self.ledger.lease_usage(lease.id)
        self._next_seq[lease.id] = usage.hydrate(state, lease.amount_mbits, subject_entropy_mbits)

    def has(self, key: Key) -> bool:
        return key in self._leases

    def lease_for(self, key: Key) -> Optional[LeaseEvent]:
        """The lease this meter would spend for the key (None if none)."""
        return self._leases.get(key)

    def account(self, key: Key):
        """The local AccountState (read it, never mutate it)."""
        return self.accountant.state(key)

    # ---- charging ----

    def _resolve_tick(self, tick: Optional[int]) -> int:
        if tick is None:
            self.clock += 1
            return self.clock
        self.clock = max(self.clock, tick)
        return tick

    def _record(
        self,
        key: Key,
        tick: int,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        decision: Decision,
    ) -> str:
        lease = self._leases[key]
        seq = self._next_seq[lease.id]
        self._next_seq[lease.id] = seq + 1
        event = ChargeEvent.from_decision(
            key=key,
            node=self.node,
            lease_id=lease.id,
            charge_seq=seq,
            tick=tick,
            estimate=estimate,
            estimator=estimator,
            decision=decision,
        )
        if self.node_signer is not None:
            event = self.node_signer.sign(event)
        return self.ledger.add(event)

    def charge(
        self,
        key: Key,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: Optional[int] = None,
    ) -> Decision:
        """One SPEC charge against the key's account; the decision is
        recorded as a ChargeEvent whatever it was (refusals are facts)."""
        return self.charge_recorded(key, estimate, estimator, tick)[0]

    def charge_recorded(
        self,
        key: Key,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: Optional[int] = None,
    ) -> Tuple[Decision, str]:
        """charge() plus the recorded ChargeEvent's ledger id — the exact
        work receipt a settlement release binds to (SETTLEMENT-SPEC: value
        moves iff metered work moved, referenced by event id)."""
        if key not in self._leases:
            raise MeterRefused(f"key not registered with this meter: {key}")
        t = self._resolve_tick(tick)
        decision = self.accountant.charge(key, estimate, estimator, t)
        eid = self._record(key, t, estimate, estimator, decision)
        return decision, eid

    def charge_coupled(
        self,
        keys: List[Key],
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: Optional[int] = None,
    ) -> Dict[Key, Decision]:
        """Atomic multi-account charge (see Accountant.charge_coupled);
        every per-key decision is recorded."""
        for key in keys:
            if key not in self._leases:
                raise MeterRefused(f"key not registered with this meter: {key}")
        t = self._resolve_tick(tick)
        decisions = self.accountant.charge_coupled(keys, estimate, estimator, t)
        for key in keys:
            self._record(key, t, estimate, estimator, decisions[key])
        return decisions

    # ---- receipts ----

    def court_file(self) -> Dict[Key, dict]:
        """The fold restricted to this meter's keys — the receipt a stranger
        recomputes from the merged ledger."""
        touched = set(self._leases.keys())
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
