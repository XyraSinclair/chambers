"""The D1 egress accountant -- verification-as-extraction, priced.

D1's central friction (CANON open-frontier #12): the same typed output that a
vendor pays a research agent to produce -- a VEX reachability verdict, a minimal
repro -- is a channel that carries source structure out of the sealed enclave.
Confidential computing seals the source *from the host* and does zero output
accounting. This module is the output accounting.

The accountant now charges through `charge-kernel/2`: every decision is made in
integer millibits by `KernelMeter`, every charge/refusal is recorded in a
kernel `Ledger`, and `ledger.audit()` re-derives the court-grade facts. The old
NOT-counterparty-compilable label is discharged for the accounting core: D1 no
longer performs floating-point arithmetic in the charge/ceiling/incident path.

Honest caveats remain. Bits are an upper-bound channel capacity, a conservative
tripwire. Staying under budget PROVES NOTHING; crossing it forces owner review.
The estimator still uses `log2` and byte ceilings outside the decision path,
then reduces each component to integer millibits. Its reproducibility rule is
documented here under SPEC section 0: Python `round(bits * 1000)`, i.e.
round-half-to-even / banker's rounding. The kernel only sees the resulting
integers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from chambers.kernel import (
    KernelMeter,
    MeterRefused,
    CapacityEstimate,
    EstimatorAttestation,
    composition_key,
    Ledger,
)


def sha(s: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()[:24]


# ---- estimator helpers: floats are estimator-local, never account-local ----

UNSAFE_PERMILLE = 800
UNSAFE = UNSAFE_PERMILLE / 1000.0


def bits_to_mbits(bits: float) -> int:
    """Estimator boundary: SPEC section 0 permits floats only before this line.

    Python's `round` is round-half-to-even ("banker's rounding"). That is the
    D1 estimator's documented reproducibility rule; accounting receives only
    the returned integer millibits.
    """
    return round(bits * 1000)


def mbits_to_bits(mbits: int) -> float:
    """Presentation-only conversion for reports, logs, and tests."""
    return mbits / 1000.0


def estimate_total_bits(estimate: CapacityEstimate) -> float:
    """Presentation-only total in bits."""
    return mbits_to_bits(estimate.total_mbits)


def enum_value_bits(n_legal_states: int) -> float:
    """log2 of the verdict's legal choice space, e.g. {reachable, not-present,
    needs-human} => log2(3)."""
    return math.log2(max(1, n_legal_states))


def enum_value_mbits(n_legal_states: int) -> int:
    return bits_to_mbits(enum_value_bits(n_legal_states))


def ordering_bits(k_reported_paths: int) -> float:
    """log2(k!) over reported call-path permutations: an agent can encode secret
    bits purely in the ORDER it lists otherwise-innocuous call paths."""
    if k_reported_paths <= 1:
        return 0.0
    return math.log2(math.factorial(k_reported_paths))


def ordering_mbits(k_reported_paths: int) -> int:
    return bits_to_mbits(ordering_bits(k_reported_paths))


def repro_text_bits(max_bytes: int) -> float:
    """A minimal repro is charged at its byte ceiling * 8, NOT its honest
    information content. The agent's claim that the repro is 'small' is exactly
    the claim an exfiltrating agent would also make."""
    return 8.0 * max(0, max_bytes)


def repro_text_mbits(max_bytes: int) -> int:
    return bits_to_mbits(repro_text_bits(max_bytes))


# ---- composition key: the adversary's join key, not the run id ----


@dataclass(frozen=True)
class CompositionKey:
    """subject x queryFamily x audience: N per-build reachability probes each
    look safe, but they accumulate over THIS join key and reconstruct the
    control-flow graph. Keyed on what the adversary can correlate."""

    subject_hash: str
    query_family_hash: str
    audience_hash: str

    @staticmethod
    def of(subject: str, query_family: str, audience: str) -> "CompositionKey":
        return CompositionKey(sha(subject), sha(query_family), sha(audience))

    def as_tuple(self) -> Tuple[str, str, str]:
        return (self.subject_hash, self.query_family_hash, self.audience_hash)

    def kernel_key(self) -> Tuple[str, ...]:
        return composition_key(self.subject_hash, self.query_family_hash, self.audience_hash)


@dataclass
class EgressDebit:
    tick: int
    channel: str
    mbits: int
    accepted: bool
    note: str

    @property
    def bits(self) -> float:
        return mbits_to_bits(self.mbits)


@dataclass
class CompositionState:
    """Presentation view over the kernel account for one CompositionKey.

    The load-bearing counters are integer millibits copied from
    `Ledger.fold()` / the kernel account after each decision. Bit and fraction
    properties exist only for existing reports, tests, and human-readable logs.
    """

    key: CompositionKey
    subject_entropy_mbits: int
    ceiling_mbits: int
    cumulative_mbits: int = 0
    demanded_mbits: int = 0
    debits: List[EgressDebit] = field(default_factory=list)
    blocked: bool = False
    incident: bool = False
    leakage_class: str = "negligible"

    @property
    def subject_entropy_bits(self) -> float:
        return mbits_to_bits(self.subject_entropy_mbits)

    @property
    def ceiling_bits(self) -> float:
        return mbits_to_bits(self.ceiling_mbits)

    @property
    def cumulative_bits(self) -> float:
        return mbits_to_bits(self.cumulative_mbits)

    @property
    def demanded_bits(self) -> float:
        return mbits_to_bits(self.demanded_mbits)

    @property
    def fraction(self) -> float:
        if self.subject_entropy_mbits <= 0:
            return 1.0
        return min(1.0, self.cumulative_mbits / self.subject_entropy_mbits)

    @property
    def demanded_fraction(self) -> float:
        if self.subject_entropy_mbits <= 0:
            return 1.0
        return min(1.0, self.demanded_mbits / self.subject_entropy_mbits)

    def remaining_mbits(self) -> int:
        return max(0, self.ceiling_mbits - self.cumulative_mbits)

    def remaining_bits(self) -> float:
        return mbits_to_bits(self.remaining_mbits())


class EgressAccountant:
    """D1 adapter around `KernelMeter`.

    Public API is preserved: register with bit-denominated D1 inputs; charge a
    kernel `CapacityEstimate`; return `(allowed, state, reason)`. The only
    boundary conversions are register-time bit floats to integer millibits.
    """

    def __init__(self) -> None:
        self.ledger = Ledger()
        self._meter = KernelMeter(node="d1-bounty", issuer="d1-bounty", ledger=self.ledger)
        self._states: Dict[Tuple[str, str, str], CompositionState] = {}

    def register(
        self,
        key: CompositionKey,
        subject_entropy_bits: float,
        ceiling_bits: float,
    ) -> CompositionState:
        subject_entropy_mbits = bits_to_mbits(subject_entropy_bits)
        ceiling_mbits = bits_to_mbits(ceiling_bits)
        kernel_key = key.kernel_key()
        try:
            self._meter.register(kernel_key, subject_entropy_mbits, ceiling_mbits)
        except MeterRefused:
            raise
        k = key.as_tuple()
        if k not in self._states:
            self._states[k] = CompositionState(
                key=key,
                subject_entropy_mbits=subject_entropy_mbits,
                ceiling_mbits=ceiling_mbits,
            )
        return self._refresh_state(key)

    def state(self, key: CompositionKey) -> CompositionState:
        return self._refresh_state(key)

    def charge(
        self,
        key: CompositionKey,
        estimate: CapacityEstimate,
        estimator: EstimatorAttestation,
        tick: int,
    ) -> Tuple[bool, CompositionState, str]:
        """Attempt to emit one typed finding. Returns (allowed, state, reason)."""
        decision = self._meter.charge(key.kernel_key(), estimate, estimator, tick=tick)
        st = self._refresh_state(key)
        reason = self._human_reason(decision=decision, estimator=estimator)
        st.debits.append(self._debit_from_decision(tick, estimate, decision_class=decision.reason_class, reason=reason))
        return (decision.accepted, st, reason)

    def report(self) -> List[dict]:
        folded = self.ledger.fold()
        out = []
        for st in self._states.values():
            acct = folded[st.key.kernel_key()]
            fraction = min(1.0, acct.cumulative_mbits / acct.subject_entropy_mbits)
            demanded_fraction = min(1.0, acct.demanded_mbits / acct.subject_entropy_mbits)
            out.append(
                {
                    "subject_hash": st.key.subject_hash,
                    "query_family_hash": st.key.query_family_hash,
                    "audience_hash": st.key.audience_hash,
                    "cumulative_mbits": acct.cumulative_mbits,
                    "demanded_mbits": acct.demanded_mbits,
                    "ceiling_mbits": acct.ceiling_mbits,
                    "subject_entropy_mbits": acct.subject_entropy_mbits,
                    "cumulative_bits": round(mbits_to_bits(acct.cumulative_mbits), 3),
                    "demanded_bits": round(mbits_to_bits(acct.demanded_mbits), 3),
                    "ceiling_bits": mbits_to_bits(acct.ceiling_mbits),
                    "subject_entropy_bits": mbits_to_bits(acct.subject_entropy_mbits),
                    "fraction": round(fraction, 3),
                    "demanded_fraction": round(demanded_fraction, 3),
                    "class": acct.leakage_class,
                    "blocked": st.blocked,
                    "incident": acct.incident,
                    "debits": [(d.channel, round(d.bits, 3), d.accepted) for d in st.debits],
                }
            )
        return out

    def _refresh_state(self, key: CompositionKey) -> CompositionState:
        st = self._states[key.as_tuple()]
        kernel_key = key.kernel_key()
        acct = self.ledger.fold()[kernel_key]
        local = self._meter.account(kernel_key)
        st.subject_entropy_mbits = acct.subject_entropy_mbits
        st.ceiling_mbits = acct.ceiling_mbits
        st.cumulative_mbits = acct.cumulative_mbits
        st.demanded_mbits = acct.demanded_mbits
        st.blocked = local.blocked
        st.incident = acct.incident
        st.leakage_class = acct.leakage_class
        return st

    def _human_reason(self, decision, estimator: EstimatorAttestation) -> str:
        incident_suffix = (
            " (INCIDENT: cumulative demand projects reconstruction — verification-as-extraction)"
            if decision.newly_incident
            else ""
        )
        if decision.reason_class == "EMITTED":
            return "emitted; debited" + incident_suffix
        if decision.reason_class == "REFUSED_BLOCKED":
            return "composition budget already blocked" + incident_suffix
        if decision.reason_class == "REFUSED_CEILING":
            return "refused: would exceed structured-bits ceiling" + incident_suffix
        if decision.reason_class == "REFUSED_ESTIMATOR":
            return self._estimator_refusal_reason(decision.reason_detail, estimator)
        return f"{decision.reason_class}: {decision.reason_detail}" + incident_suffix

    def _estimator_refusal_reason(self, detail: str, estimator: EstimatorAttestation) -> str:
        if detail == "self_interested_estimator":
            return "self_interested estimator: the paid agent may not meter its own leak"
        if detail == "unknown_independence_class":
            return f"unknown independence class: {estimator.independence}"
        if detail == "estimate_not_worst_case":
            return "estimate must be a worst-case bound over all schema-consistent secrets"
        return detail

    def _debit_from_decision(
        self,
        tick: int,
        estimate: CapacityEstimate,
        decision_class: str,
        reason: str,
    ) -> EgressDebit:
        if decision_class == "EMITTED":
            return EgressDebit(tick, estimate.channel, estimate.total_mbits, True, reason)
        if decision_class == "REFUSED_ESTIMATOR":
            channel = estimate.channel + "_REFUSED_ESTIMATOR"
        elif decision_class == "REFUSED_BLOCKED":
            channel = estimate.channel + "_REFUSED_BLOCKED"
        else:
            channel = estimate.channel + "_REFUSED"
        return EgressDebit(tick, channel, 0, False, reason)
