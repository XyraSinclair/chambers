"""Reference accountant for `egress-accountant/1` — the counterparty-compilable
core, in exact integer millibits.

This module is the REFERENCE implementation of conformance/SPEC.md. It is the
authority the golden traces are emitted from and the yardstick the independent
Rust implementation is measured against. It contains NO floating point in the
decision path (§0). The only floats in this file live in `estimate_mbits`
below — the ESTIMATOR — which is explicitly out of the compiled core (§7): it
turns log2/byte-ceilings into attested integer millibits and is documented so a
second estimator can reproduce the same integers.

Keep this file faithful to SPEC.md line by line; if they ever disagree, SPEC.md
wins and this file is the bug.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

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


# ---- data model (SPEC §1) ----


@dataclass(frozen=True)
class CompositionKey:
    subject: str
    query_family: str
    audience: str

    def as_tuple(self) -> Tuple[str, str, str]:
        return (self.subject, self.query_family, self.audience)


@dataclass(frozen=True)
class CapacityEstimate:
    enum_value_mbits: int
    ordering_mbits: int
    field_presence_mbits: int
    text_mbits: int
    side_channel_mbits: int
    channel: str = "vex_verdict"

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

    def admissibility(self) -> Tuple[bool, str]:
        # SPEC §1.3 — ordered; first failing check supplies the reason.
        if self.independence == "self_interested":
            return (False, REASON_SELF_INTERESTED)
        if self.independence not in VALID_INDEPENDENCE:
            return (False, REASON_UNKNOWN_INDEP)
        if not self.worst_case_over_secrets:
            return (False, REASON_NOT_WORST_CASE)
        return (True, "")


@dataclass
class CompositionState:
    key: CompositionKey
    subject_entropy_mbits: int
    ceiling_mbits: int
    cumulative_mbits: int = 0
    demanded_mbits: int = 0
    blocked: bool = False
    incident: bool = False


@dataclass(frozen=True)
class Decision:
    accepted: bool
    reason_class: str  # EMITTED | REFUSED_ESTIMATOR | REFUSED_BLOCKED | REFUSED_CEILING
    reason_detail: str
    cumulative_mbits: int
    demanded_mbits: int
    blocked: bool
    incident: bool
    leakage_class: str
    newly_incident: bool

    def as_json_obj(self) -> dict:
        return {
            "accepted": self.accepted,
            "reason_class": self.reason_class,
            "reason_detail": self.reason_detail,
            "cumulative_mbits": self.cumulative_mbits,
            "demanded_mbits": self.demanded_mbits,
            "blocked": self.blocked,
            "incident": self.incident,
            "leakage_class": self.leakage_class,
            "newly_incident": self.newly_incident,
        }


# ---- leakage class: integer cross-multiplication, no division (SPEC §1.5) ----


def leakage_class(cumulative_mbits: int, subject_entropy_mbits: int) -> str:
    c = min(cumulative_mbits, subject_entropy_mbits)  # cap the fraction at 1
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


# ---- the accountant (SPEC §2) ----


class EgressAccountant:
    def __init__(self) -> None:
        self._states: Dict[Tuple[str, str, str], CompositionState] = {}

    def register(self, key: CompositionKey, subject_entropy_mbits: int, ceiling_mbits: int) -> CompositionState:
        k = key.as_tuple()
        if k not in self._states:  # idempotent create — never resets (SPEC §2.1)
            self._states[k] = CompositionState(key, subject_entropy_mbits, ceiling_mbits)
        return self._states[k]

    def state(self, key: CompositionKey) -> CompositionState:
        return self._states[key.as_tuple()]

    def charge(
        self,
        key: CompositionKey,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: int,
    ) -> Decision:
        st = self._states[key.as_tuple()]

        # Step A — estimator admissibility (no counter moves) (SPEC §2.2.A)
        ok, reason = estimator.admissibility()
        if not ok:
            return Decision(
                accepted=False,
                reason_class="REFUSED_ESTIMATOR",
                reason_detail=reason,
                cumulative_mbits=st.cumulative_mbits,
                demanded_mbits=st.demanded_mbits,
                blocked=st.blocked,
                incident=st.incident,
                leakage_class=leakage_class(st.cumulative_mbits, st.subject_entropy_mbits),
                newly_incident=False,
            )

        # Step B — accrue demand, evaluate incident on UNCAPPED demand (SPEC §2.2.B)
        bits = estimate.total_mbits
        st.demanded_mbits += bits
        newly_incident = (not st.incident) and (
            st.demanded_mbits * 1000 >= UNSAFE_PERMILLE * st.subject_entropy_mbits
        )
        if newly_incident:
            st.incident = True

        # Step C — already blocked (SPEC §2.2.C)
        if st.blocked:
            return Decision(
                accepted=False,
                reason_class="REFUSED_BLOCKED",
                reason_detail=REASON_BLOCKED,
                cumulative_mbits=st.cumulative_mbits,
                demanded_mbits=st.demanded_mbits,
                blocked=True,
                incident=st.incident,
                leakage_class=leakage_class(st.cumulative_mbits, st.subject_entropy_mbits),
                newly_incident=newly_incident,
            )

        # Step D — would exceed the ceiling (strict >) (SPEC §2.2.D)
        remaining = max(0, st.ceiling_mbits - st.cumulative_mbits)
        if bits > remaining:
            st.blocked = True
            return Decision(
                accepted=False,
                reason_class="REFUSED_CEILING",
                reason_detail=REASON_CEILING,
                cumulative_mbits=st.cumulative_mbits,
                demanded_mbits=st.demanded_mbits,
                blocked=True,
                incident=st.incident,
                leakage_class=leakage_class(st.cumulative_mbits, st.subject_entropy_mbits),
                newly_incident=newly_incident,
            )

        # Step E — emit (SPEC §2.2.E)
        st.cumulative_mbits += bits
        if st.cumulative_mbits >= st.ceiling_mbits:
            st.blocked = True
        return Decision(
            accepted=True,
            reason_class="EMITTED",
            reason_detail=REASON_EMITTED,
            cumulative_mbits=st.cumulative_mbits,
            demanded_mbits=st.demanded_mbits,
            blocked=st.blocked,
            incident=st.incident,
            leakage_class=leakage_class(st.cumulative_mbits, st.subject_entropy_mbits),
            newly_incident=newly_incident,
        )


# ---- the estimator: the one place floats live (SPEC §0, §7) ----
#
# This is NOT part of the compiled core. It converts real-valued information
# estimates into attested integer millibits by a documented rule:
#   millibits = round-half-to-even( 1000 * bits )
# A second, independent estimator that adopts the same rule reproduces the same
# integers; the accountant never depends on that — it only ever sees integers.


def _mbits(bits: float) -> int:
    """Banker's rounding of 1000*bits to an integer millibit. Documented so the
    rounding rule itself is reproducible; still outside the compiled core."""
    return round(1000.0 * bits)


def estimate_enum_value_mbits(n_legal_states: int) -> int:
    return _mbits(math.log2(max(1, n_legal_states)))


def estimate_ordering_mbits(k_reported: int) -> int:
    if k_reported <= 1:
        return 0
    return _mbits(math.log2(math.factorial(k_reported)))


def estimate_text_mbits(max_bytes: int) -> int:
    # a repro is charged at its byte ceiling * 8 bits, exactly (no float needed)
    return 8000 * max(0, max_bytes)


def vex_estimate(k_paths: int, repro_bytes: int, channel: str = "vex_verdict") -> CapacityEstimate:
    """The D1 VEX-verdict estimate, in integer millibits — the same shape as
    d1_bounty.run._vex_estimate, but quantized at the estimator boundary."""
    return CapacityEstimate(
        enum_value_mbits=estimate_enum_value_mbits(3),
        ordering_mbits=estimate_ordering_mbits(k_paths),
        field_presence_mbits=2000,
        text_mbits=estimate_text_mbits(repro_bytes),
        side_channel_mbits=1000,
        channel=channel,
    )
