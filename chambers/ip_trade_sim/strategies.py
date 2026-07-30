"""Valuation and pricing strategies (baseline deterministic; Codex deepens).

Appraisal is the "review the other lab's IP against your own portfolio" step:
marginal value = how much this technique beats the buyer's own best in that
area, scaled by the buyer's stake. Crucially it is formed only from ALLOWED
observations (the attested verdict + optionally a few metered probes), so it
respects the leakage budget.
"""
from __future__ import annotations

from typing import Optional

from . import economics
from .leakage import LeakageAccountant, black_box_probe_bits
from .types import Appraisal, Lab, PriceDistribution, Technique, VerificationVerdict, HumanHook


def _proven_scores(verdict: VerificationVerdict) -> dict:
    """Benchmark lower bounds the buyer may rely on: the claims whose charged
    codebook symbol was `holds`. Structured — never parsed out of prose."""
    return {cr.benchmark: cr.claimed_score
            for cr in verdict.claim_results if cr.symbol == "holds"}


def _no_value_rationale(verdict: VerificationVerdict) -> str:
    """Honest three-way label for a zero-value appraisal (adversarial-review
    fix: the old single string blamed the leakage budget even for fraud)."""
    if any(cr.symbol == "not_met" for cr in verdict.claim_results):
        return "a claim failed attestation; cannot justify value"
    if verdict.claim_results and all(cr.symbol == "blocked" for cr in verdict.claim_results):
        return "no verdict obtained: leakage budget blocked verification"
    return "no proven results; cannot justify value"


def appraise(buyer: Lab, seller: Lab, technique: Technique, verdict: VerificationVerdict,
             accountant: LeakageAccountant, tick: int, hook: HumanHook, ledger) -> Optional[Appraisal]:
    proven_scores = _proven_scores(verdict)
    if not proven_scores:
        return Appraisal(technique.id, buyer.id, 0, 0.2, _no_value_rationale(verdict), 0.0)

    breakdown = economics.valuation_breakdown(buyer, technique, proven_scores)
    est = economics.marginal_value(buyer, technique, proven_scores)

    # optionally spend a small metered probe to raise confidence — but only if budget allows
    bits_spent = 0.0
    confidence = 0.45 + 0.10 * min(3, len(proven_scores))
    probe_n = 20
    probe_bits = black_box_probe_bits(technique, probe_n)
    if est > 0:
        ok, st = accountant.observe(technique.id, buyer.id, "black_box_probe", probe_bits, tick,
                                    note=f"{probe_n}-query confidence probe")
        if ok:
            bits_spent += probe_bits
            confidence = min(0.95, confidence + 0.2)
            ledger.add(tick, buyer.id, "probe", f"{technique.id} n={probe_n} bits={probe_bits}")

    pieces = []
    for contribution in breakdown.contributions:
        pieces.append(
            (
                f"{contribution.benchmark} {contribution.normalized_own_best:.3f}->{contribution.normalized_score:.3f} "
                f"(lift {contribution.lift_units:.3f}, {contribution.gross_credits}cr)"
            )
        )
    rationale = (
        f"{'; '.join(pieces)}; stake {breakdown.stake:.2f}; "
        f"expected transfer x{breakdown.expected_transfer_multiplier:.2f}; "
        f"expected novelty x{breakdown.expected_novelty_multiplier:.2f}"
    )
    if est <= 0:
        rationale = "proven capability units do not beat the buyer's own frontier enough to justify value"
    return Appraisal(technique.id, buyer.id, max(0, est), min(0.95, confidence), rationale, bits_spent)


def seller_ask(seller: Lab, technique: Technique, reserve: int, hook: HumanHook) -> PriceDistribution:
    """Seller's private ask: floored at reserve, centered above their opportunity
    cost of losing exclusivity (proxied by their own stake in the area)."""
    stake = seller.area_stakes.get(technique.capability_area, 0.3)
    lo = max(reserve, int(400 + 2000 * stake))
    hi = lo + int(1500 + 3000 * stake)
    return PriceDistribution(seller.id, "ask", lo, hi).commit(salt=f"ask:{technique.id}")


def buyer_bid(buyer: Lab, seller: Lab, technique: Technique, appraisal, hook: HumanHook) -> PriceDistribution:
    """Buyer bids a band under their appraised value (never above it)."""
    v = appraisal.est_value_credits
    lo = int(v * 0.4)
    hi = int(v * 0.9)
    return PriceDistribution(buyer.id, "bid", lo, hi).commit(salt=f"bid:{technique.id}")
