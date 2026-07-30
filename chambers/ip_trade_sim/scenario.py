"""Concrete scenarios for the confidential IP-trade simulation."""
from __future__ import annotations

from .types import Lab, ResultClaim, Technique


def _lab(
    lab_id: str,
    name: str,
    beneficial_entity: str,
    area_stakes: dict,
    reserve_floor_credits: int,
    max_leak_fraction_before_block: float,
    portfolio: list,
) -> Lab:
    return Lab(
        id=lab_id,
        name=name,
        beneficial_entity=beneficial_entity,
        portfolio=portfolio,
        credits=50000,
        area_stakes=area_stakes,
        reserve_floor_credits=reserve_floor_credits,
        max_leak_fraction_before_block=max_leak_fraction_before_block,
        tradeable={technique.id: True for technique in portfolio},
    )


def build_labs() -> tuple[Lab, Lab]:
    """The original compact scenario used by run.py."""
    a = _lab(
        lab_id="labA",
        name="OpenMind",
        beneficial_entity="be:openmind",
        area_stakes={
            "long_context": 0.9,
            "inference_efficiency": 0.8,
            "rl_from_ai_feedback": 0.3,
            "data_curation": 0.4,
        },
        reserve_floor_credits=800,
        max_leak_fraction_before_block=0.45,
        portfolio=[
            Technique(
                id="A_ctx",
                owner="labA",
                name="RingLadder attention",
                capability_area="long_context",
                carrier="static_checkpoint",
                secret_payload="ringladder-kernel-v3::block-sparse::rotary-interp",
                entropy_bits=80.0,
                probe_leak_per_query_bits=0.04,
                claims=[
                    ResultClaim("RULER-128k", true_score=0.91, claimed_score=0.90),
                    ResultClaim("LongBench", true_score=0.74, claimed_score=0.73),
                ],
                true_transfers=True,
                true_novel=True,
            ),
            Technique(
                id="A_eff",
                owner="labA",
                name="SpecDecode-XL",
                capability_area="inference_efficiency",
                carrier="lora_adapter",
                secret_payload="speculative-decode::medusa-heads::calibrated",
                entropy_bits=60.0,
                probe_leak_per_query_bits=0.06,
                claims=[ResultClaim("tok/s@70B", true_score=2.3, claimed_score=2.2)],
                true_transfers=True,
                true_novel=False,
            ),
        ],
    )

    b = _lab(
        lab_id="labB",
        name="Cloudsight",
        beneficial_entity="be:cloudsight",
        area_stakes={
            "rl_from_ai_feedback": 0.9,
            "data_curation": 0.85,
            "long_context": 0.7,
            "inference_efficiency": 0.2,
        },
        reserve_floor_credits=1000,
        max_leak_fraction_before_block=0.40,
        portfolio=[
            Technique(
                id="B_rl",
                owner="labB",
                name="Constitutional-RLAIF++",
                capability_area="rl_from_ai_feedback",
                carrier="curated_dataset",
                secret_payload="rlaif::preference-model::constitution-v7",
                entropy_bits=100.0,
                probe_leak_per_query_bits=0.03,
                claims=[
                    ResultClaim("HH-eval", true_score=0.88, claimed_score=0.87),
                    ResultClaim("MT-Bench", true_score=8.4, claimed_score=8.3),
                ],
                true_transfers=True,
                true_novel=True,
            ),
            Technique(
                id="B_data",
                owner="labB",
                name="DedupeGold corpus",
                capability_area="data_curation",
                carrier="curated_dataset",
                secret_payload="semdedup::quality-classifier::mix-weights",
                entropy_bits=70.0,
                probe_leak_per_query_bits=0.05,
                claims=[ResultClaim("MMLU-lift", true_score=0.043, claimed_score=0.05)],
                true_transfers=False,
                true_novel=True,
            ),
        ],
    )
    return a, b


def build_rich_labs() -> tuple[Lab, Lab]:
    """A richer world with deliberate lessons for verification, pricing, and regret."""
    a = _lab(
        lab_id="labA",
        name="OpenMind",
        beneficial_entity="be:openmind",
        area_stakes={
            "long_context": 0.95,
            "inference_efficiency": 0.45,
            "rl_from_ai_feedback": 0.85,
            "data_curation": 0.90,
        },
        reserve_floor_credits=900,
        max_leak_fraction_before_block=0.45,
        portfolio=[
            # Lesson: overlapping frontier. Both labs already have this capability, so
            # result verification succeeds but the buyer rationally values it at zero.
            Technique(
                id="A_ctx",
                owner="labA",
                name="RingLadder attention",
                capability_area="long_context",
                carrier="static_checkpoint",
                secret_payload="ringladder-kernel-v4::block-sparse::rotary-interp",
                entropy_bits=84.0,
                probe_leak_per_query_bits=0.04,
                claims=[
                    ResultClaim("RULER-128k", true_score=0.91, claimed_score=0.91),
                    ResultClaim("LongBench", true_score=0.75, claimed_score=0.75),
                ],
                true_transfers=True,
                true_novel=True,
            ),
            # Lesson: genuinely complementary win-win. Cloudsight wants more tokens
            # per second and is willing to pay for a frontier it does not already own.
            Technique(
                id="A_eff",
                owner="labA",
                name="SpecDecode-XL",
                capability_area="inference_efficiency",
                carrier="lora_adapter",
                secret_payload="speculative-decode::medusa-heads::calibrated-v5",
                entropy_bits=66.0,
                probe_leak_per_query_bits=0.06,
                claims=[ResultClaim("tok/s@70B", true_score=3.9, claimed_score=3.8)],
                true_transfers=True,
                true_novel=True,
            ),
            # Lesson: over-claiming fails attested verification before the buyer can
            # justify a bid, even though the technique name sounds plausible.
            Technique(
                id="A_data",
                owner="labA",
                name="Curriculum Distiller",
                capability_area="data_curation",
                carrier="teacher_outputs",
                secret_payload="curriculum::teacher-ensemble::distill-mix-v2",
                entropy_bits=72.0,
                probe_leak_per_query_bits=0.05,
                claims=[ResultClaim("MMLU-lift", true_score=0.024, claimed_score=0.040)],
                true_transfers=True,
                true_novel=True,
            ),
        ],
    )

    b = _lab(
        lab_id="labB",
        name="Cloudsight",
        beneficial_entity="be:cloudsight",
        area_stakes={
            "long_context": 0.90,
            "inference_efficiency": 1.00,
            "rl_from_ai_feedback": 0.95,
            "data_curation": 0.45,
        },
        reserve_floor_credits=1100,
        max_leak_fraction_before_block=0.40,
        portfolio=[
            # Lesson: overlapping frontier from the other side. OpenMind already has a
            # matching long-context frontier, so there is no gains-from-trade here.
            Technique(
                id="B_ctx",
                owner="labB",
                name="WindowWeave memory",
                capability_area="long_context",
                carrier="static_checkpoint",
                secret_payload="windowweave-kernel-v2::state-compression::rotary-merge",
                entropy_bits=86.0,
                probe_leak_per_query_bits=0.04,
                claims=[
                    ResultClaim("RULER-128k", true_score=0.91, claimed_score=0.91),
                    ResultClaim("LongBench", true_score=0.75, claimed_score=0.75),
                ],
                true_transfers=True,
                true_novel=True,
            ),
            # Lesson: genuinely complementary win-win. OpenMind cares about better RL
            # behavior and this technique cleanly beats its current frontier.
            Technique(
                id="B_rl",
                owner="labB",
                name="Constitutional-RLAIF++",
                capability_area="rl_from_ai_feedback",
                carrier="curated_dataset",
                secret_payload="rlaif::preference-model::constitution-v9",
                entropy_bits=104.0,
                probe_leak_per_query_bits=0.03,
                claims=[
                    ResultClaim("HH-eval", true_score=0.90, claimed_score=0.89),
                    ResultClaim("MT-Bench", true_score=8.6, claimed_score=8.5),
                ],
                true_transfers=True,
                true_novel=True,
            ),
            # Lesson: non-transferability is unprovable pre-purchase. Results look
            # strong enough that OpenMind buys, then ex post regret reveals the miss.
            Technique(
                id="B_data",
                owner="labB",
                name="DedupeGold corpus",
                capability_area="data_curation",
                carrier="curated_dataset",
                secret_payload="semdedup::quality-classifier::mix-weights-v6",
                entropy_bits=74.0,
                probe_leak_per_query_bits=0.05,
                claims=[ResultClaim("MMLU-lift", true_score=0.072, claimed_score=0.070)],
                true_transfers=False,
                true_novel=True,
            ),
        ],
    )
    return a, b
