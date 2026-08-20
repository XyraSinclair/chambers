from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple, Union

from .novelty import NoveltyEstimate
from .types import CarrierClass, sha


OfferKind = str  # monetary | barter | attribution
RouteKind = str  # monetary_clear | barter_match | attribution | refuse
RefusalReason = str  # priceless_excluded | competitor_eligibility_block | barter_class_mismatch | tag_unverifiable


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class Monetary:
    reserve: int = 0
    kind: str = field(default="monetary", init=False)


@dataclass(frozen=True)
class BarterOnly:
    acceptable_carrier_classes: Tuple[CarrierClass, ...]
    kind: str = field(default="barter_only", init=False)


@dataclass(frozen=True)
class Attribution:
    terms: str
    priority_commit_hash: str
    kind: str = field(default="attribution", init=False)


@dataclass(frozen=True)
class ExcludedFromMonetaryClearing:
    exclusivity_rationale: str
    kind: str = field(default="excluded_from_monetary_clearing", init=False)


Valuation = Union[Monetary, BarterOnly, Attribution, ExcludedFromMonetaryClearing]


@dataclass(frozen=True)
class RefusalReceipt:
    asset_id: str
    reason: RefusalReason
    discoverable_contact_signal: bool = True
    note: str = ""


@dataclass(frozen=True)
class NoveltyRoot:
    corpus_snapshot_hash: str
    vrf_seed: str
    embedder_ensemble: Tuple[str, ...]
    committed_at: str


@dataclass(frozen=True)
class CorpusRelativeProvenance:
    observer: str = "shared_substrate"
    marginal_redistribution_leakage_bits: float = 0.0
    kind: str = field(default="corpus_relative", init=False)


@dataclass(frozen=True)
class BuyerConditionedProvenance:
    observer_id: str
    leakage_bits_spent: float
    cost_spent_credits: int = 0
    kind: str = field(default="buyer_conditioned", init=False)


EstimateProvenance = Union[CorpusRelativeProvenance, BuyerConditionedProvenance]


@dataclass(frozen=True)
class OodEstimate:
    technique_id: str
    novelty_root: NoveltyRoot
    method: str
    estimator_role: str
    ood_score_vs_corpus: float
    confidence_interval: Tuple[float, float]
    provenance: EstimateProvenance
    evidence_citations: Tuple[str, ...] = field(default_factory=tuple)
    gameability_caveat: str = ""
    calibration_covers_this_regime: bool = True
    backend: str = "offline"


def _receipt(asset_id: str, reason: RefusalReason, note: str) -> RefusalReceipt:
    return RefusalReceipt(asset_id=asset_id, reason=reason, note=note)


def route_valuation(
    asset_valuation: Valuation,
    offer_kind: OfferKind,
    *,
    asset_id: str = "",
) -> Tuple[RouteKind, Optional[RefusalReceipt]]:
    """Route a heterogeneous valuation into the only lane it honestly supports."""
    if isinstance(asset_valuation, ExcludedFromMonetaryClearing):
        if offer_kind == "monetary":
            return (
                "refuse",
                _receipt(
                    asset_id,
                    "priceless_excluded",
                    "excluded_from_monetary_clearing is a categorical no-cash type, not price=inf",
                ),
            )
        return (
            "refuse",
            _receipt(
                asset_id,
                "tag_unverifiable",
                "the exclusivity tag is cheap talk until backed by an explicit barter fit or bond",
            ),
        )

    if isinstance(asset_valuation, Monetary):
        if offer_kind == "monetary":
            return ("monetary_clear", None)
        return (
            "refuse",
            _receipt(
                asset_id,
                "tag_unverifiable",
                "a monetary reserve does not authorize scalar-free barter or attribution by itself",
            ),
        )

    if isinstance(asset_valuation, BarterOnly):
        if offer_kind == "barter":
            return ("barter_match", None)
        return (
            "refuse",
            _receipt(
                asset_id,
                "tag_unverifiable",
                "barter_only may match only through a carrier-class-compatible barter lane",
            ),
        )

    if isinstance(asset_valuation, Attribution):
        if offer_kind == "attribution":
            return ("attribution", None)
        return (
            "refuse",
            _receipt(
                asset_id,
                "tag_unverifiable",
                "attribution terms are not a monetary reserve or barter-fit declaration",
            ),
        )

    raise TypeError(f"unknown valuation type: {type(asset_valuation)!r}")


def novelty_root_for(
    technique_id: str,
    backend_name: str,
    *,
    observer: Optional[str] = None,
) -> NoveltyRoot:
    scope = observer or "shared_substrate"
    return NoveltyRoot(
        corpus_snapshot_hash=sha(f"novelty_root:{backend_name}:corpus"),
        vrf_seed=sha(f"novelty_root:{backend_name}:{scope}:{technique_id}"),
        embedder_ensemble=(backend_name, "prior_art_density"),
        committed_at="2026-07-02T00:00:00Z",
    )


def novelty_to_ood(
    estimate: NoveltyEstimate,
    *,
    observer: Optional[str] = None,
    leakage_bits_spent: float = 0.0,
    cost_spent_credits: int = 0,
) -> OodEstimate:
    confidence = _clamp(estimate.confidence)
    half_width = 0.5 * (1.0 - confidence)
    lo = _clamp(estimate.ood_score - half_width)
    hi = _clamp(estimate.ood_score + half_width)
    sparse_unknown = "SPARSE PRIOR ART = UNKNOWN" in estimate.gameability_caveat
    provenance: EstimateProvenance
    if observer is None:
        provenance = CorpusRelativeProvenance()
    else:
        provenance = BuyerConditionedProvenance(
            observer_id=observer,
            leakage_bits_spent=max(0.0, leakage_bits_spent),
            cost_spent_credits=max(0, int(cost_spent_credits)),
        )
    return OodEstimate(
        technique_id=estimate.technique_id,
        novelty_root=novelty_root_for(
            estimate.technique_id,
            estimate.backend,
            observer=observer,
        ),
        method=estimate.method,
        estimator_role="valuation_gating",
        ood_score_vs_corpus=_clamp(estimate.ood_score),
        confidence_interval=(lo, hi),
        provenance=provenance,
        evidence_citations=tuple(estimate.prior_art_examples),
        gameability_caveat=estimate.gameability_caveat,
        calibration_covers_this_regime=not sparse_unknown,
        backend=estimate.backend,
    )


def ood_confidence(estimate: OodEstimate) -> float:
    lo, hi = estimate.confidence_interval
    return _clamp(1.0 - max(0.0, hi - lo))


def ood_midpoint(estimate: OodEstimate) -> float:
    lo, hi = estimate.confidence_interval
    return _clamp((lo + hi) / 2.0)


def ood_haircut(estimate: OodEstimate) -> float:
    """Continuous haircut only; never a boolean unlock.

    Dense, confident, low-OOD reads discount value. Low-confidence or sparse /
    ambiguous reads relax back toward a neutral 1.0 rather than acting like a
    novelty unlock. The function is piecewise-linear with only clamping at the
    unit interval boundaries, so there is no internal threshold gate.
    """
    confidence = ood_confidence(estimate)
    if not estimate.calibration_covers_this_regime:
        confidence *= 0.5
    crowdedness = 1.0 - ood_midpoint(estimate)
    multiplier = 1.0 - 0.45 * confidence * crowdedness
    multiplier = max(1e-6, min(1.0, multiplier))
    assert 0.0 < multiplier <= 1.0
    return multiplier


def carrier_class_acceptable(
    valuation: Valuation,
    offered_carrier: CarrierClass,
) -> bool:
    if not isinstance(valuation, BarterOnly):
        return False
    return offered_carrier in valuation.acceptable_carrier_classes
