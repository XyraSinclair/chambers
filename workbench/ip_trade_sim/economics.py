from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping

from .types import Lab, Technique


Normalizer = Callable[[float], float]

TRANSFER_FALSE_VALUE_FACTOR = 0.25
NOVELTY_FALSE_VALUE_FACTOR = 0.85

TRANSFER_PRIOR_BY_CARRIER: Dict[str, float] = {
    "static_checkpoint": 0.80,
    "lora_adapter": 0.76,
    "curated_dataset": 0.62,
    "teacher_outputs": 0.58,
    "hosted_service": 0.45,
    "pure_recipe": 0.35,
}

NOVELTY_PRIOR_BY_CARRIER: Dict[str, float] = {
    "static_checkpoint": 0.72,
    "lora_adapter": 0.64,
    "curated_dataset": 0.78,
    "teacher_outputs": 0.60,
    "hosted_service": 0.52,
    "pure_recipe": 0.48,
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _unit_normalizer(raw: float) -> float:
    return _clamp(raw)


def _score_0_10_normalizer(raw: float) -> float:
    return _clamp(raw / 10.0)


def _ratio_normalizer(full_scale: float) -> Normalizer:
    def normalize(raw: float) -> float:
        if full_scale <= 0:
            return 0.0
        return _clamp(raw / full_scale)

    return normalize


def _delta_normalizer(full_scale: float) -> Normalizer:
    def normalize(raw: float) -> float:
        if full_scale <= 0:
            return 0.0
        return _clamp(max(0.0, raw) / full_scale)

    return normalize


@dataclass(frozen=True)
class BenchmarkEconomics:
    kind: str
    normalizer: Normalizer
    credit_value_per_unit: int


@dataclass(frozen=True)
class BenchmarkContribution:
    benchmark: str
    kind: str
    proven_score: float
    own_best_score: float
    normalized_score: float
    normalized_own_best: float
    lift_units: float
    gross_credits: int


@dataclass(frozen=True)
class ValueBreakdown:
    technique_id: str
    area: str
    stake: float
    contributions: List[BenchmarkContribution] = field(default_factory=list)
    gross_value_credits: int = 0
    stake_adjusted_credits: int = 0
    expected_transfer_multiplier: float = 1.0
    expected_novelty_multiplier: float = 1.0
    expected_value_credits: int = 0
    realized_transfer_multiplier: float = 1.0
    realized_novelty_multiplier: float = 1.0
    realized_value_credits: int = 0


BENCHMARK_REGISTRY: Dict[str, BenchmarkEconomics] = {
    "RULER-128k": BenchmarkEconomics("accuracy_0_1", _unit_normalizer, 24000),
    "LongBench": BenchmarkEconomics("accuracy_0_1", _unit_normalizer, 21000),
    "HH-eval": BenchmarkEconomics("accuracy_0_1", _unit_normalizer, 22000),
    "MT-Bench": BenchmarkEconomics("score_0_10", _score_0_10_normalizer, 18000),
    "tok/s@70B": BenchmarkEconomics("ratio", _ratio_normalizer(4.0), 16000),
    "MMLU-lift": BenchmarkEconomics("delta", _delta_normalizer(0.10), 26000),
}


def benchmark_economics(benchmark: str) -> BenchmarkEconomics:
    if benchmark in BENCHMARK_REGISTRY:
        return BENCHMARK_REGISTRY[benchmark]
    if benchmark.endswith("-lift"):
        return BenchmarkEconomics("delta", _delta_normalizer(0.10), 18000)
    if "tok/s" in benchmark or benchmark.endswith("/s"):
        return BenchmarkEconomics("ratio", _ratio_normalizer(4.0), 15000)
    return BenchmarkEconomics("accuracy_0_1", _unit_normalizer, 15000)


def _expected_transfer_multiplier(technique: Technique) -> float:
    prior = TRANSFER_PRIOR_BY_CARRIER.get(technique.carrier, 0.60)
    return prior + (1.0 - prior) * TRANSFER_FALSE_VALUE_FACTOR


def _expected_novelty_multiplier(technique: Technique) -> float:
    prior = NOVELTY_PRIOR_BY_CARRIER.get(technique.carrier, 0.60)
    return prior + (1.0 - prior) * NOVELTY_FALSE_VALUE_FACTOR


def _realized_transfer_multiplier(technique: Technique) -> float:
    return 1.0 if technique.true_transfers else TRANSFER_FALSE_VALUE_FACTOR


def _realized_novelty_multiplier(technique: Technique) -> float:
    return 1.0 if technique.true_novel else NOVELTY_FALSE_VALUE_FACTOR


def valuation_breakdown(
    buyer: Lab,
    technique: Technique,
    proven_scores: Mapping[str, float],
) -> ValueBreakdown:
    area = technique.capability_area
    stake = _clamp(buyer.area_stakes.get(area, 0.0))
    contributions: List[BenchmarkContribution] = []
    gross_value = 0.0

    for claim in technique.claims:
        if claim.benchmark not in proven_scores:
            continue
        benchmark = claim.benchmark
        spec = benchmark_economics(benchmark)
        proven_score = proven_scores[benchmark]
        own_best = buyer.best_score(area, benchmark)
        normalized_score = spec.normalizer(proven_score)
        normalized_own = spec.normalizer(own_best)
        lift_units = max(0.0, normalized_score - normalized_own)
        gross_credits = int(round(lift_units * spec.credit_value_per_unit))
        contributions.append(
            BenchmarkContribution(
                benchmark=benchmark,
                kind=spec.kind,
                proven_score=proven_score,
                own_best_score=own_best,
                normalized_score=normalized_score,
                normalized_own_best=normalized_own,
                lift_units=lift_units,
                gross_credits=gross_credits,
            )
        )
        gross_value += lift_units * spec.credit_value_per_unit

    stake_adjusted = gross_value * stake
    expected_transfer = _expected_transfer_multiplier(technique)
    expected_novelty = _expected_novelty_multiplier(technique)
    realized_transfer = _realized_transfer_multiplier(technique)
    realized_novelty = _realized_novelty_multiplier(technique)
    expected_value = int(round(stake_adjusted * expected_transfer * expected_novelty))
    realized_value = int(round(stake_adjusted * realized_transfer * realized_novelty))
    return ValueBreakdown(
        technique_id=technique.id,
        area=area,
        stake=stake,
        contributions=contributions,
        gross_value_credits=int(round(gross_value)),
        stake_adjusted_credits=int(round(stake_adjusted)),
        expected_transfer_multiplier=expected_transfer,
        expected_novelty_multiplier=expected_novelty,
        expected_value_credits=max(0, expected_value),
        realized_transfer_multiplier=realized_transfer,
        realized_novelty_multiplier=realized_novelty,
        realized_value_credits=max(0, realized_value),
    )


def marginal_value(
    buyer: Lab,
    technique: Technique,
    proven_scores: Mapping[str, float],
) -> int:
    return valuation_breakdown(buyer, technique, proven_scores).expected_value_credits


def realized_value(
    buyer: Lab,
    technique: Technique,
    scores: Mapping[str, float],
) -> int:
    return valuation_breakdown(buyer, technique, scores).realized_value_credits
