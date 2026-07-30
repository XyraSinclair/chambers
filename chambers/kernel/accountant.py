"""The decision core of charge-kernel/2: egress-accountant/1 semantics,
generalized over keys.

This module is a faithful port of `chambers/conformance/SPEC.md` §1–§2
with ONE generalization: the account key is any tuple of strings, not only
the (subject, query_family, audience) CompositionKey. Two adapters are
provided:

    composition_key(subject, query_family, audience)   # egress-accountant/1
    exposure_key(source_chamber, reader_entity)        # coalition.ts ExposureAccount

Everything else — admissibility, the A/B/C/D/E charge steps, integer-only
millibit arithmetic, leakage classes, incident latching on uncapped demand —
is the SPEC, unchanged. Conformance to the golden traces in
`../conformance/traces/` is enforced by test_kernel.py; if this file and
SPEC.md ever disagree, SPEC.md wins and this file is the bug.

No floating point exists anywhere in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

Key = Tuple[str, ...]

# ---- constants (SPEC §1.3, §1.5) ----

VALID_INDEPENDENCE = ("operator", "role_separated", "adversarial_review")

NEGLIGIBLE_PERMILLE = 50
BOUNDED_PERMILLE = 250
MATERIAL_PERMILLE = 500
UNSAFE_PERMILLE = 800

REASON_EMITTED = "emitted_debited"
REASON_SELF_INTERESTED = "self_interested_estimator"
REASON_UNKNOWN_INDEP = "unknown_independence_class"
REASON_NOT_WORST_CASE = "estimate_not_worst_case"
REASON_BLOCKED = "budget_already_blocked"
REASON_CEILING = "would_exceed_ceiling"

# Kernel-level extension (NOT part of egress-accountant/1): the reason an
# individually-solvent account reports when an atomic coupled charge was
# refused because a sibling account refused. See Accountant.charge_coupled.
REASON_COUPLED = "coupled_refusal"

_ESTIMATE_FIELDS = (
    "enum_value_mbits",
    "ordering_mbits",
    "field_presence_mbits",
    "text_mbits",
    "side_channel_mbits",
)


def composition_key(subject: str, query_family: str, audience: str) -> Key:
    """egress-accountant/1 CompositionKey, tagged."""
    return ("comp", subject, query_family, audience)


def exposure_key(source_chamber: str, reader_entity: str) -> Key:
    """coalition.ts ExposureAccount key: (source × reader), lifetime scope."""
    return ("exp", source_chamber, reader_entity)


@dataclass(frozen=True)
class CapacityEstimate:
    """Attested integer charge, already reduced to millibits (SPEC §1.2).

    SPEC §1.2 declares every component `int >= 0` and §5 assigns validation
    to the boundary, not the decision steps. In the live kernel THIS is the
    boundary: a negative component would *credit* the meter (demand shrinks,
    budget un-spends), so construction refuses it outright. bool is excluded
    explicitly because Python bools are ints.
    """

    enum_value_mbits: int
    ordering_mbits: int
    field_presence_mbits: int
    text_mbits: int
    side_channel_mbits: int
    channel: str

    def __post_init__(self) -> None:
        for name in _ESTIMATE_FIELDS:
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ValueError(f"CapacityEstimate.{name} must be an int >= 0, got {v!r}")

    @property
    def total_mbits(self) -> int:
        return (
            self.enum_value_mbits
            + self.ordering_mbits
            + self.field_presence_mbits
            + self.text_mbits
            + self.side_channel_mbits
        )


@dataclass(frozen=True)
class EstimatorAttestation:
    estimator_id: str
    independence: str
    method: str
    worst_case_over_secrets: bool


def admissibility(estimator: EstimatorAttestation) -> Tuple[bool, Optional[str]]:
    """SPEC §1.3 — ordered checks; first failure supplies the reason."""
    if estimator.independence == "self_interested":
        return False, REASON_SELF_INTERESTED
    if estimator.independence not in VALID_INDEPENDENCE:
        return False, REASON_UNKNOWN_INDEP
    if not estimator.worst_case_over_secrets:
        return False, REASON_NOT_WORST_CASE
    return True, None


def leakage_class(cumulative_mbits: int, subject_entropy_mbits: int) -> str:
    """SPEC §1.5 — integer cross-multiplication, fraction capped at 1."""
    c = min(cumulative_mbits, subject_entropy_mbits)
    s = subject_entropy_mbits
    if c * 1000 <= NEGLIGIBLE_PERMILLE * s:
        return "negligible"
    if c * 1000 <= BOUNDED_PERMILLE * s:
        return "bounded"
    if c * 1000 <= MATERIAL_PERMILLE * s:
        return "material"
    if c * 1000 <= UNSAFE_PERMILLE * s:
        return "unsafe"
    return "reconstructed"


@dataclass
class AccountState:
    """SPEC §1.4 CompositionState, key-generic."""

    key: Key
    subject_entropy_mbits: int
    ceiling_mbits: int
    cumulative_mbits: int = 0
    demanded_mbits: int = 0
    blocked: bool = False
    incident: bool = False


@dataclass(frozen=True)
class Decision:
    """SPEC §2.3 — the full observable output of one charge."""

    accepted: bool
    reason_class: str
    reason_detail: str
    cumulative_mbits: int
    demanded_mbits: int
    blocked: bool
    incident: bool
    leakage_class: str
    newly_incident: bool


class Accountant:
    """SPEC §2 operations over per-key AccountState.

    In the distributed protocol a node instantiates one Accountant whose
    ceilings are its LEASES (leases.py); the same class with the key's true
    ceiling is the single-node accountant. The decision function is identical
    in both roles — that identity is the design.
    """

    def __init__(self) -> None:
        self._states: Dict[Key, AccountState] = {}

    def register(self, key: Key, subject_entropy_mbits: int, ceiling_mbits: int) -> AccountState:
        """SPEC §2.1 — idempotent create; existing state returned unchanged."""
        if subject_entropy_mbits <= 0:
            raise ValueError("subject_entropy_mbits must be > 0")
        if ceiling_mbits < 0:
            raise ValueError("ceiling_mbits must be >= 0")
        existing = self._states.get(key)
        if existing is not None:
            return existing
        state = AccountState(
            key=key,
            subject_entropy_mbits=subject_entropy_mbits,
            ceiling_mbits=ceiling_mbits,
        )
        self._states[key] = state
        return state

    def state(self, key: Key) -> AccountState:
        return self._states[key]

    def has(self, key: Key) -> bool:
        return key in self._states

    def charge(
        self,
        key: Key,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: int,
    ) -> Decision:
        """SPEC §2.2 — steps A..E, in order, first return wins."""
        state = self._states[key]

        # Step A — estimator admissibility.
        admissible, reason = admissibility(estimator)
        if not admissible:
            return Decision(
                accepted=False,
                reason_class="REFUSED_ESTIMATOR",
                reason_detail=reason or "",
                cumulative_mbits=state.cumulative_mbits,
                demanded_mbits=state.demanded_mbits,
                blocked=state.blocked,
                incident=state.incident,
                leakage_class=leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
                newly_incident=False,
            )

        # Step B — accrue demand, evaluate incident on UNCAPPED demand.
        bits = estimate.total_mbits
        state.demanded_mbits += bits
        newly_incident = (not state.incident) and (
            state.demanded_mbits * 1000 >= UNSAFE_PERMILLE * state.subject_entropy_mbits
        )
        if newly_incident:
            state.incident = True

        # Step C — already blocked.
        if state.blocked:
            return Decision(
                accepted=False,
                reason_class="REFUSED_BLOCKED",
                reason_detail=REASON_BLOCKED,
                cumulative_mbits=state.cumulative_mbits,
                demanded_mbits=state.demanded_mbits,
                blocked=True,
                incident=state.incident,
                leakage_class=leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
                newly_incident=newly_incident,
            )

        # Step D — would exceed the ceiling.
        remaining = max(0, state.ceiling_mbits - state.cumulative_mbits)
        if bits > remaining:
            state.blocked = True
            return Decision(
                accepted=False,
                reason_class="REFUSED_CEILING",
                reason_detail=REASON_CEILING,
                cumulative_mbits=state.cumulative_mbits,
                demanded_mbits=state.demanded_mbits,
                blocked=True,
                incident=state.incident,
                leakage_class=leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
                newly_incident=newly_incident,
            )

        # Step E — emit.
        state.cumulative_mbits += bits
        if state.cumulative_mbits >= state.ceiling_mbits:
            state.blocked = True
        return Decision(
            accepted=True,
            reason_class="EMITTED",
            reason_detail=REASON_EMITTED,
            cumulative_mbits=state.cumulative_mbits,
            demanded_mbits=state.demanded_mbits,
            blocked=state.blocked,
            incident=state.incident,
            leakage_class=leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
            newly_incident=newly_incident,
        )

    def charge_coupled(
        self,
        keys: "list[Key] | Tuple[Key, ...]",
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: int,
    ) -> "Dict[Key, Decision]":
        """One estimate charged against several accounts ATOMICALLY — debit
        all or none. Kernel-level extension; single-key `charge` remains the
        exact SPEC and never produces REFUSED_COUPLED.

        Why this exists: an emission that carries information about k members
        must clear all k exposure accounts. Charging them one at a time is
        separable in the failure direction — members 1..j-1 keep their debits
        when member j refuses, so the ledger states leakage that never flowed
        and repeated failed emissions grief the requester's accounts. Here:

          Step A  once (same estimator for the one emission).
          Step B  on EVERY account — the attempt carried real extraction
                  pressure toward every member, so demand accrues and the
                  incident latch may fire on each, exactly as SPEC.
          Step C/D as predicates on every account. Accounts that would refuse
                  are "guilty": they get their true SPEC reason, and a
                  ceiling-guilty account latches blocked (the demand really
                  did exceed its remaining — SPEC step D).
          Step E  only if NO account is guilty, applied to every account.
                  Otherwise no account is debited; innocent accounts return
                  REFUSED_COUPLED with state unchanged beyond step B.

        Keys must be distinct and registered. Returns {key: Decision} in the
        given key order.
        """
        keys = list(keys)
        if len(set(keys)) != len(keys):
            raise ValueError("coupled charge keys must be distinct")
        for key in keys:
            if key not in self._states:
                raise KeyError(key)

        # Step A — one estimator, one admissibility verdict for all accounts.
        admissible, reason = admissibility(estimator)
        if not admissible:
            out: Dict[Key, Decision] = {}
            for key in keys:
                state = self._states[key]
                out[key] = Decision(
                    accepted=False,
                    reason_class="REFUSED_ESTIMATOR",
                    reason_detail=reason or "",
                    cumulative_mbits=state.cumulative_mbits,
                    demanded_mbits=state.demanded_mbits,
                    blocked=state.blocked,
                    incident=state.incident,
                    leakage_class=leakage_class(
                        state.cumulative_mbits, state.subject_entropy_mbits
                    ),
                    newly_incident=False,
                )
            return out

        bits = estimate.total_mbits

        # Step B — accrue demand and evaluate the incident latch on every account.
        newly: Dict[Key, bool] = {}
        for key in keys:
            state = self._states[key]
            state.demanded_mbits += bits
            ni = (not state.incident) and (
                state.demanded_mbits * 1000 >= UNSAFE_PERMILLE * state.subject_entropy_mbits
            )
            if ni:
                state.incident = True
            newly[key] = ni

        # Steps C/D — evaluated as predicates over ALL accounts before any debit.
        guilty: Dict[Key, Tuple[str, str]] = {}
        for key in keys:
            state = self._states[key]
            if state.blocked:
                guilty[key] = ("REFUSED_BLOCKED", REASON_BLOCKED)
            elif bits > max(0, state.ceiling_mbits - state.cumulative_mbits):
                guilty[key] = ("REFUSED_CEILING", REASON_CEILING)

        out = {}
        if guilty:
            for key in keys:
                state = self._states[key]
                if key in guilty:
                    reason_class, reason_detail = guilty[key]
                    if reason_class == "REFUSED_CEILING":
                        state.blocked = True  # SPEC step D latch — the demand truly exceeded it
                else:
                    reason_class, reason_detail = "REFUSED_COUPLED", REASON_COUPLED
                out[key] = Decision(
                    accepted=False,
                    reason_class=reason_class,
                    reason_detail=reason_detail,
                    cumulative_mbits=state.cumulative_mbits,
                    demanded_mbits=state.demanded_mbits,
                    blocked=state.blocked,
                    incident=state.incident,
                    leakage_class=leakage_class(
                        state.cumulative_mbits, state.subject_entropy_mbits
                    ),
                    newly_incident=newly[key],
                )
            return out

        # Step E — all accounts accept; debit every one.
        for key in keys:
            state = self._states[key]
            state.cumulative_mbits += bits
            if state.cumulative_mbits >= state.ceiling_mbits:
                state.blocked = True
            out[key] = Decision(
                accepted=True,
                reason_class="EMITTED",
                reason_detail=REASON_EMITTED,
                cumulative_mbits=state.cumulative_mbits,
                demanded_mbits=state.demanded_mbits,
                blocked=state.blocked,
                incident=state.incident,
                leakage_class=leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
                newly_incident=newly[key],
            )
        return out
