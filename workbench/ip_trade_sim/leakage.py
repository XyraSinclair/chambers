"""The leakage accountant -- the heart of "be really smart about actual IP leakage".

Principle: you must OBSERVE a technique to value it, but every observation leaks
bits toward reconstructing the secret. So meter it. The accountant keys leakage
on (technique, observing_lab) -- the adversary's join key, not the run -- sums it
monotonically, distinguishes cheap RESULT leakage from near-total METHOD leakage,
and BLOCKS further observation before the observer can reconstruct the secret.

This is what makes result-verification the safe primitive and exhibits
verification-as-extraction (over-probing to steal) as a typed, blockable event.

Bits are an upper-bound channel capacity, not a secrecy proof (same honesty rule
as entropy.ts). The accountant is a conservative tripwire.

The accountant now charges through `charge-kernel/2`: every observation
decision is made in integer millibits by `KernelMeter`, every accepted charge
and refusal is recorded in a kernel `Ledger`, and `ledger.audit()` re-derives
the facts. The old NOT-counterparty-compilable label is discharged for the
accounting core by construction.

Honest caveats remain. Bits are upper-bound channel capacity, not proof of what
actually crossed; staying under budget proves nothing. Estimators may still use
floats locally (`log2`, configured bit rates, entropy fractions), but those
floats die at the named boundary `bits_to_mbits`: Python `round(bits * 1000)`,
i.e. round-half-to-even / banker's rounding. The kernel only receives integer
millibits. A paid method reveal after settlement is modeled as a separate
consent/release account, so the pre-settlement observation ceiling is not
retroactively widened.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from chambers.kernel import (
    CapacityEstimate,
    EstimatorAttestation,
    KernelMeter,
    Ledger,
    leakage_class as kernel_leakage_class,
)

from .codebook import Codebook
from .types import Technique


# leakage class thresholds, as a fraction of a technique's entropy
NEGLIGIBLE = 0.05
BOUNDED = 0.25
MATERIAL = 0.50   # past here: the observer could plausibly narrow the secret a lot
UNSAFE = 0.80     # past here: effective reconstruction / theft


def leakage_class(fraction: float) -> str:
    """Legacy presentation helper; accounting uses integer millibits."""
    if fraction <= NEGLIGIBLE:
        return "negligible"
    if fraction <= BOUNDED:
        return "bounded"
    if fraction <= MATERIAL:
        return "material"
    if fraction <= UNSAFE:
        return "unsafe"
    return "reconstructed"


def bits_to_mbits(bits: float) -> int:
    """Estimator boundary: floats are permitted only before this line.

    The reproducibility rule follows the other kernel adapters in this repo:
    round `bits * 1000` with Python's round-half-to-even behavior, then pass
    only that integer millibit value to the charge kernel. Used for
    REGISTRATION parameters (entropy, ceilings).
    """
    if bits < 0:
        raise ValueError(f"leakage bits must be non-negative, got {bits!r}")
    return round(bits * 1000)


def bits_to_mbits_charge(bits: float) -> int:
    """CHARGES round UP (adversarial-review fix: half-even can round a charge
    down, e.g. log2(11) = 3.4594 bits -> 3459 mbits undercharges). Derived
    and declared charges must stay conservative; ceilings keep round-half-even
    so the budget itself is not silently inflated."""
    if bits < 0:
        raise ValueError(f"leakage bits must be non-negative, got {bits!r}")
    return math.ceil(bits * 1000)


def mbits_to_bits(mbits: int) -> float:
    """Presentation-only conversion for reports and legacy bit-facing APIs."""
    return mbits / 1000.0


IP_TRADE_ESTIMATOR = EstimatorAttestation(
    estimator_id="ip_trade_sim.leakage.round_half_even_bits",
    independence="operator",
    method="declared_upper_bound",
    worst_case_over_secrets=True,
)

# Codebook releases carry a stronger attestation: the charge is log2 of a
# closed alphabet, derived in code from the symbol list — there is no operator
# judgment left to be wrong about. worst_case_over_secrets is not a claim
# here, it is a theorem (min-capacity bounds g-leakage for every g).
DERIVED_CODEBOOK_ESTIMATOR = EstimatorAttestation(
    estimator_id="ip_trade_sim.codebook.log2_alphabet",
    independence="operator",
    method="derived_codebook",
    worst_case_over_secrets=True,
)

# Derived-vs-declared pool membership is decided by the ESTIMATOR recorded on
# each kernel ChargeEvent (see cut_bound), never by a hand-maintained channel
# name list — a new codebook can't silently land in the wrong pool.


def leakage_key(technique_id: str, observer: str) -> Tuple[str, str, str]:
    """Kernel account key for the adversary join key (technique, observer)."""
    return ("ip_trade", technique_id, observer)


def paid_reveal_key(technique_id: str, observer: str) -> Tuple[str, str, str]:
    """Separate release-transaction key for a paid post-settlement reveal."""
    return ("ip_trade_paid_reveal", technique_id, observer)


def _estimate(channel: str, mbits: int) -> CapacityEstimate:
    return CapacityEstimate(
        enum_value_mbits=0,
        ordering_mbits=0,
        field_presence_mbits=0,
        text_mbits=0,
        side_channel_mbits=mbits,
        channel=channel,
    )


@dataclass
class Debit:
    tick: int
    channel: str        # result_verdict | black_box_probe | method_reveal | price_round
    mbits: int
    note: str

    @property
    def bits(self) -> float:
        return mbits_to_bits(self.mbits)


@dataclass
class CompositionState:
    """Presentation view over kernel account(s) for one technique/observer."""

    technique_id: str
    observer: str
    entropy_mbits: int
    ceiling_mbits: int
    ceiling_fraction: float           # presentation/policy only
    observation_mbits: int = 0
    cumulative_mbits: int = 0
    demanded_mbits: int = 0
    debits: List[Debit] = field(default_factory=list)
    blocked: bool = False
    incident: bool = False
    leakage_class: str = "negligible"

    @property
    def entropy_bits(self) -> float:
        return mbits_to_bits(self.entropy_mbits)

    @property
    def cumulative_bits(self) -> float:
        return mbits_to_bits(self.cumulative_mbits)

    @property
    def demanded_bits(self) -> float:
        return mbits_to_bits(self.demanded_mbits)

    @property
    def ceiling_bits(self) -> float:
        return mbits_to_bits(self.ceiling_mbits)

    @property
    def fraction(self) -> float:
        return min(1.0, self.cumulative_mbits / self.entropy_mbits) if self.entropy_mbits > 0 else 1.0

    def remaining_mbits(self) -> int:
        return max(0, self.ceiling_mbits - self.observation_mbits)

    def remaining_bits(self) -> float:
        return mbits_to_bits(self.remaining_mbits())


class LeakageAccountant:
    """Enforces: no observation without a debit; block before the ceiling;
    flag an incident if a reveal or over-probe crosses into reconstruction."""

    def __init__(self) -> None:
        self.ledger = Ledger()
        self._meter = KernelMeter(node="ip_trade_sim", issuer="ip_trade_sim", ledger=self.ledger)
        self._states: Dict[Tuple[str, str], CompositionState] = {}

    def key(self, technique_id: str, observer: str) -> Tuple[str, str]:
        return (technique_id, observer)

    def register(self, technique: Technique, observer: str, ceiling_fraction: float) -> CompositionState:
        """Registration is an explicit one-time DISCLOSURE decision: the
        technique's declared entropy_bits and the ceiling enter the kernel
        RegisterEvent and the leakage report as public parameters. Blocked
        schedules are simulatable from public data ONLY because of this —
        entropy is secret-derived, and publishing it (coarsen to a grid if
        that matters) is the price of leak-free refusals (CALCULUS.md L5)."""
        k = self.key(technique.id, observer)
        if k not in self._states:
            entropy_mbits = bits_to_mbits(technique.entropy_bits)
            ceiling_mbits = bits_to_mbits(technique.entropy_bits * ceiling_fraction)
            self._meter.register(leakage_key(technique.id, observer), entropy_mbits, ceiling_mbits)
            self._states[k] = CompositionState(
                technique_id=technique.id, observer=observer,
                entropy_mbits=entropy_mbits,
                ceiling_mbits=ceiling_mbits,
                ceiling_fraction=ceiling_fraction,
            )
        return self._refresh_state(technique.id, observer)

    def state(self, technique_id: str, observer: str) -> CompositionState:
        return self._refresh_state(technique_id, observer)

    def can_observe(self, technique_id: str, observer: str, bits: float) -> bool:
        st = self.state(technique_id, observer)
        return (not st.blocked) and (bits_to_mbits(bits) <= st.remaining_mbits())

    def observe(self, technique_id: str, observer: str, channel: str, bits: float,
                tick: int, note: str = "") -> Tuple[bool, CompositionState]:
        """Attempt an observation. Returns (allowed, state). If it would cross the
        ceiling it is REFUSED (allowed=False) and the state is marked blocked.
        A method_reveal that crosses UNSAFE is allowed only if explicitly a
        paid/settled reveal (channel 'method_reveal_paid'); an unpaid one that
        crosses is refused and flagged as an incident (attempted theft)."""
        mbits = bits_to_mbits_charge(bits)
        estimate = _estimate(channel, mbits)
        if channel == "method_reveal_paid":
            key = self._ensure_paid_reveal_account(technique_id, observer, mbits)
            decision = self._meter.charge(key, estimate, IP_TRADE_ESTIMATOR, tick=tick)
            st = self._refresh_state(technique_id, observer)
            debit_channel = channel if decision.accepted else channel + "_REFUSED"
            debit_mbits = mbits if decision.accepted else 0
            st.debits.append(Debit(tick, debit_channel, debit_mbits, note or "paid method reveal after settlement"))
            return (decision.accepted, st)

        decision = self._meter.charge(
            leakage_key(technique_id, observer),
            estimate,
            IP_TRADE_ESTIMATOR,
            tick=tick,
        )
        st = self._refresh_state(technique_id, observer)
        if decision.accepted:
            st.debits.append(Debit(tick, channel, mbits, note))
        elif decision.reason_class == "REFUSED_BLOCKED":
            st.debits.append(Debit(tick, channel + "_REFUSED_BLOCKED", 0, note or "budget already blocked"))
        else:
            st.debits.append(Debit(tick, channel + "_REFUSED", 0, note or "would exceed ceiling"))
        return (decision.accepted, st)

    def release(self, technique_id: str, observer: str, codebook: Codebook,
                symbol: str, tick: int, note: str = "") -> Tuple[str, CompositionState]:
        """A codebook release: the calculus's one door, in sim form.

        Charges the DERIVED capacity of the closed alphabet — independent of
        which symbol crosses, so the choice of symbol (the judge's one degree
        of freedom, honest or malicious) is already paid for. If the budget
        refuses the charge, the observer receives the codebook's 'blocked'
        symbol and nothing else; blockage is a function of the public charge
        ledger alone, which is why an uncharged 'blocked' is not a side
        channel (CALCULUS.md L5; asserted by test_calculus_bound.py).

        Returns (symbol_the_observer_sees, state).
        """
        if "blocked" not in codebook.symbols:
            # validate at the door, not at first refusal: a codebook without a
            # refusal symbol would work until the budget first says no, then
            # crash mid-run (adversarial-review fix)
            raise ValueError(
                f"codebook {codebook.name!r} has no 'blocked' symbol; the accountant "
                "must be able to refuse a release inside the declared alphabet"
            )
        codebook.require(symbol)
        if symbol == "blocked":
            raise ValueError("'blocked' is emitted by the accountant, never chosen by a judge")
        mbits = bits_to_mbits_charge(codebook.capacity_bits)
        estimate = _estimate(codebook.name, mbits)
        decision = self._meter.charge(
            leakage_key(technique_id, observer),
            estimate,
            DERIVED_CODEBOOK_ESTIMATOR,
            tick=tick,
        )
        st = self._refresh_state(technique_id, observer)
        if decision.accepted:
            st.debits.append(Debit(tick, codebook.name, mbits, note or f"release:{symbol}"))
            return (symbol, st)
        blocked = codebook.require("blocked")
        refused = "_REFUSED_BLOCKED" if decision.reason_class == "REFUSED_BLOCKED" else "_REFUSED"
        st.debits.append(Debit(tick, codebook.name + refused, 0, note or "budget refused release"))
        return (blocked, st)

    def cut_bound(self) -> dict:
        """The protocol's cut bound (CALCULUS.md §6): everything that crossed
        a silo boundary, summed per (technique, observer), split into the
        derived pool (exact by construction) and the declared pool (honest
        estimates).

        Source of truth is the KERNEL LEDGER, not the presentation Debit
        lists (adversarial-review fix: a charge path that skipped the Debit
        append would vanish from a Debit-based report), and derived-pool
        membership is the estimator recorded on each ChargeEvent — a second
        codebook can never silently land in the declared pool."""
        derived_id = DERIVED_CODEBOOK_ESTIMATOR.estimator_id
        per_edge: Dict[Tuple[str, str], Dict[str, int]] = {}
        for event in self.ledger.events():
            if event.get("kind") != "charge" or not event.get("accepted", False):
                continue
            key = event.get("key")
            if not isinstance(key, (list, tuple)) or len(key) != 3:
                continue
            domain, technique_id, observer = key
            if domain not in ("ip_trade", "ip_trade_paid_reveal"):
                continue
            edge = per_edge.setdefault((str(technique_id), str(observer)),
                                       {"derived_mbits": 0, "declared_mbits": 0})
            pool = "derived_mbits" if event.get("estimator_id") == derived_id else "declared_mbits"
            edge[pool] += int(event["debit_mbits"])
        derived_mbits = sum(e["derived_mbits"] for e in per_edge.values())
        declared_mbits = sum(e["declared_mbits"] for e in per_edge.values())
        edges = [
            {"technique": tech, "observer": obs,
             "derived_mbits": e["derived_mbits"], "declared_mbits": e["declared_mbits"]}
            for (tech, obs), e in sorted(per_edge.items())
        ]
        return {
            "derived_mbits": derived_mbits,
            "declared_mbits": declared_mbits,
            "total_mbits": derived_mbits + declared_mbits,
            "derived_bits": round(mbits_to_bits(derived_mbits), 3),
            "declared_bits": round(mbits_to_bits(declared_mbits), 3),
            "total_bits": round(mbits_to_bits(derived_mbits + declared_mbits), 3),
            "edges": edges,
        }

    def report(self) -> List[dict]:
        out = []
        for st in self._states.values():
            st = self._refresh_state(st.technique_id, st.observer)
            out.append({
                "technique": st.technique_id,
                "observer": st.observer,
                "cumulative_mbits": st.cumulative_mbits,
                "demanded_mbits": st.demanded_mbits,
                "ceiling_mbits": st.ceiling_mbits,
                "entropy_mbits": st.entropy_mbits,
                "cumulative_bits": round(st.cumulative_bits, 3),
                "demanded_bits": round(st.demanded_bits, 3),
                "ceiling_bits": st.ceiling_bits,
                "entropy_bits": st.entropy_bits,
                "fraction": round(st.fraction, 3),
                "class": st.leakage_class,
                "blocked": st.blocked,
                "incident": st.incident,
                "debits": [(d.channel, round(d.bits, 3)) for d in st.debits],
            })
        return out

    def _ensure_paid_reveal_account(self, technique_id: str, observer: str, mbits: int) -> Tuple[str, str, str]:
        st = self._states[self.key(technique_id, observer)]
        key = paid_reveal_key(technique_id, observer)
        if not self._meter.has(key):
            self._meter.register(key, st.entropy_mbits, max(1, mbits))
        return key

    def _refresh_state(self, technique_id: str, observer: str) -> CompositionState:
        st = self._states[self.key(technique_id, observer)]
        folded = self.ledger.fold()
        main = folded[leakage_key(technique_id, observer)]
        reveal = folded.get(paid_reveal_key(technique_id, observer))
        reveal_mbits = 0 if reveal is None else reveal.cumulative_mbits
        local_main = self._meter.account(leakage_key(technique_id, observer))
        st.entropy_mbits = main.subject_entropy_mbits
        st.ceiling_mbits = main.ceiling_mbits
        st.observation_mbits = main.cumulative_mbits
        st.cumulative_mbits = main.cumulative_mbits + reveal_mbits
        st.demanded_mbits = main.demanded_mbits
        st.blocked = local_main.blocked
        st.incident = main.incident
        st.leakage_class = kernel_leakage_class(st.cumulative_mbits, st.entropy_mbits)
        return st


# ---- channel leakage models (how many bits each observation costs) ----
#
# Result verdicts no longer appear here: their charge is the DERIVED capacity
# of the closed codebook alphabet (codebook.RESULT_VERDICT), taken through
# LeakageAccountant.release. The models below are the channels that remain
# honest declared estimates: unbounded-alphabet interactions where no
# codebook exists (yet).

def black_box_probe_bits(t: Technique, n_queries: int) -> float:
    """Bounded black-box probing leaks proportionally to query count — the
    distillation/extraction channel. This is what verification-as-extraction
    rides; the accountant caps it."""
    return t.probe_leak_per_query_bits * n_queries


def method_reveal_bits(t: Technique) -> float:
    return t.entropy_bits * t.method_reveal_fraction


def estimate_localization_bits(prior_art_examples: Sequence[str], prior_art_density: int) -> float:
    """Meter how much a closest-prior-art map localizes a secret technique.

    Exact citations are the high-value channel; density is a weaker but still
    real localization cue. This is a conservative tripwire, not a proof.
    """
    citation_count = min(6, len(list(prior_art_examples)))
    citation_bits = 0.75 * citation_count
    density_bits = 0.35 * math.log2(max(2, int(prior_art_density) + 1))
    return 0.5 + citation_bits + density_bits
