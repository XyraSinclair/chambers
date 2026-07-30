"""Emit golden traces for `egress-accountant/1`.

    python3 -m chambers.conformance.emit_traces

Builds a corpus of accountant scenarios — the five D1 lanes at the accountant
level, the SPEC §4 worked micro-example, and a seeded property-random fan — then
replays each through the reference accountant to capture the expected Decision
stream, and writes one golden-trace JSON per scenario into `traces/`.

The traces are the contract. The independent Rust implementation must reproduce
every `expected` stream bit-for-bit from `ops` alone.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List

from .reference import (
    CapacityEstimate,
    CompositionKey,
    EgressAccountant,
    EstimatorAttestation,
    vex_estimate,
)

SPEC = "egress-accountant/1"
TRACES = Path(__file__).resolve().parent / "traces"


def _est(independence: str = "adversarial_review", worst_case: bool = True) -> EstimatorAttestation:
    return EstimatorAttestation(
        estimator_id="indep",
        independence=independence,
        method="static_schema_bound",
        worst_case_over_secrets=worst_case,
    )


def _key_obj(k: CompositionKey) -> list:
    return [k.subject, k.query_family, k.audience]


def _estimate_obj(e: CapacityEstimate) -> dict:
    return {
        "enum_value_mbits": e.enum_value_mbits,
        "ordering_mbits": e.ordering_mbits,
        "field_presence_mbits": e.field_presence_mbits,
        "text_mbits": e.text_mbits,
        "side_channel_mbits": e.side_channel_mbits,
        "channel": e.channel,
    }


def _estimator_obj(a: EstimatorAttestation) -> dict:
    return {
        "estimator_id": a.estimator_id,
        "independence": a.independence,
        "method": a.method,
        "worst_case_over_secrets": a.worst_case_over_secrets,
    }


class TraceBuilder:
    """Accumulates ops and replays them through a fresh reference accountant to
    capture the authoritative expected stream."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.ops: List[dict] = []
        self.acc = EgressAccountant()
        self.expected: List[dict] = []

    def register(self, key: CompositionKey, subject_entropy_mbits: int, ceiling_mbits: int) -> None:
        self.acc.register(key, subject_entropy_mbits, ceiling_mbits)
        self.ops.append(
            {
                "op": "register",
                "key": _key_obj(key),
                "subject_entropy_mbits": subject_entropy_mbits,
                "ceiling_mbits": ceiling_mbits,
            }
        )

    def charge(self, key: CompositionKey, estimate: CapacityEstimate, estimator: EstimatorAttestation, tick: int) -> None:
        d = self.acc.charge(key, estimate, estimator, tick)
        self.ops.append(
            {
                "op": "charge",
                "tick": tick,
                "key": _key_obj(key),
                "estimate": _estimate_obj(estimate),
                "estimator": _estimator_obj(estimator),
            }
        )
        self.expected.append(d.as_json_obj())

    def to_json(self) -> dict:
        return {"spec": SPEC, "name": self.name, "ops": self.ops, "expected": self.expected}


# ---- the five D1 lanes, at the accountant level ----


def lane_a_honest() -> TraceBuilder:
    b = TraceBuilder("lane-a-honest")
    k = CompositionKey("wolfden-in-Meridian", "reachability", "cardinal-offensive")
    b.register(k, subject_entropy_mbits=4_096_000, ceiling_mbits=800_000)
    b.charge(k, vex_estimate(3, 40), _est(), tick=1)
    return b


def lane_c_extraction() -> TraceBuilder:
    b = TraceBuilder("lane-c-extraction")
    k = CompositionKey("wolfden-in-Meridian:patch-diff-2026-06", "reachability", "cardinal-offensive")
    b.register(k, subject_entropy_mbits=512_000, ceiling_mbits=120_000)
    for tick in range(1, 7):
        b.charge(k, vex_estimate(4, 8), _est(), tick=tick)
    return b


def lane_e_self_interested() -> TraceBuilder:
    b = TraceBuilder("lane-e-self-interested")
    k = CompositionKey("wolfden-in-Meridian", "reachability", "cardinal-offensive")
    b.register(k, subject_entropy_mbits=4_096_000, ceiling_mbits=800_000)
    b.charge(k, vex_estimate(3, 40), _est(independence="self_interested", worst_case=False), tick=1)
    return b


def lane_estimator_variants() -> TraceBuilder:
    """All three inadmissibility reasons, in order, plus one admissible tail."""
    b = TraceBuilder("estimator-variants")
    k = CompositionKey("subj", "family", "aud")
    b.register(k, subject_entropy_mbits=1_000_000, ceiling_mbits=800_000)
    b.charge(k, vex_estimate(3, 40), _est(independence="self_interested"), tick=1)
    b.charge(k, vex_estimate(3, 40), _est(independence="mystery_class"), tick=2)
    b.charge(k, vex_estimate(3, 40), _est(worst_case=False), tick=3)
    b.charge(k, vex_estimate(3, 40), _est(), tick=4)  # admissible — should emit, demand only now moves
    return b


def worked_example() -> TraceBuilder:
    """SPEC §4 — incident fires on the accepted path; newly_incident on exactly
    the transition charge; class walks unsafe -> reconstructed."""
    b = TraceBuilder("worked-example-spec-4")
    k = CompositionKey("s", "f", "a")
    b.register(k, subject_entropy_mbits=100_000, ceiling_mbits=1_000_000)
    est = CapacityEstimate(0, 0, 0, 80_000, 0, channel="unit")  # total 80_000
    b.charge(k, est, _est(), tick=1)
    b.charge(k, est, _est(), tick=2)
    return b


def exact_ceiling() -> TraceBuilder:
    """An emission whose bits exactly equal remaining is admitted, then blocks."""
    b = TraceBuilder("exact-ceiling")
    k = CompositionKey("s", "f", "a")
    est = vex_estimate(3, 40)  # some fixed total
    b.register(k, subject_entropy_mbits=4_096_000, ceiling_mbits=est.total_mbits)
    b.charge(k, est, _est(), tick=1)  # exactly fills -> emit + block
    b.charge(k, est, _est(), tick=2)  # blocked
    return b


def multi_key_independence() -> TraceBuilder:
    """Two keys accumulate independently; interleaved charges must not bleed."""
    b = TraceBuilder("multi-key-independence")
    k1 = CompositionKey("subjA", "reach", "aud")
    k2 = CompositionKey("subjB", "reach", "aud")
    b.register(k1, 512_000, 200_000)
    b.register(k2, 512_000, 200_000)
    for tick in range(1, 5):
        b.charge(k1, vex_estimate(4, 8), _est(), tick=tick)
        b.charge(k2, vex_estimate(3, 4), _est(), tick=tick)
    return b


# ---- property-random fan (seeded, deterministic) ----


def random_traces(n: int, seed: int = 20260704) -> List[TraceBuilder]:
    rng = random.Random(seed)
    out: List[TraceBuilder] = []
    independences = ["operator", "role_separated", "adversarial_review", "self_interested", "bogus_class"]
    for i in range(n):
        b = TraceBuilder(f"random-{i:03d}")
        n_keys = rng.randint(1, 3)
        keys = [CompositionKey(f"s{i}_{j}", rng.choice(["reach", "presence", "flow"]), f"aud{rng.randint(0,2)}")
                for j in range(n_keys)]
        for k in keys:
            entropy = rng.choice([64_000, 128_000, 512_000, 1_000_000, 4_096_000])
            ceiling = rng.randint(20_000, entropy)
            b.register(k, entropy, ceiling)
        for tick in range(1, rng.randint(3, 12)):
            k = rng.choice(keys)
            est = CapacityEstimate(
                enum_value_mbits=rng.choice([0, 1000, 1585, 2000]),
                ordering_mbits=rng.choice([0, 4585, 6585, 15000]),
                field_presence_mbits=rng.choice([0, 2000]),
                text_mbits=8000 * rng.choice([0, 4, 8, 16, 40]),
                side_channel_mbits=rng.choice([0, 1000]),
                channel="rnd",
            )
            indep = rng.choice(independences)
            worst = rng.random() > 0.15
            b.charge(k, est, _est(independence=indep, worst_case=worst), tick=tick)
        out.append(b)
    return out


def all_builders() -> List[TraceBuilder]:
    named = [
        lane_a_honest(),
        lane_c_extraction(),
        lane_e_self_interested(),
        lane_estimator_variants(),
        worked_example(),
        exact_ceiling(),
        multi_key_independence(),
    ]
    return named + random_traces(24)


def main() -> None:
    TRACES.mkdir(parents=True, exist_ok=True)
    for old in TRACES.glob("*.json"):
        old.unlink()
    manifest: Dict[str, int] = {}
    for b in all_builders():
        obj = b.to_json()
        path = TRACES / f"{b.name}.json"
        path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest[b.name] = len(b.expected)
    (TRACES / "MANIFEST.json").write_text(
        json.dumps({"spec": SPEC, "traces": manifest}, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    total = sum(manifest.values())
    print(f"emitted {len(manifest)} traces, {total} charge decisions -> {TRACES}")


if __name__ == "__main__":
    main()
