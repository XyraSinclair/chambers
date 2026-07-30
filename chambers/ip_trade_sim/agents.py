from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

from . import economics, strategies
from .leakage import LeakageAccountant, black_box_probe_bits
from .types import Appraisal, HumanHook, Lab, ResultClaim, Technique, VerificationVerdict


Reasoner = Callable[[dict], dict]
_FORBIDDEN_CONTEXT_KEYS = {"secret_payload", "true_score"}


def _proven_scores(verdict: VerificationVerdict) -> Dict[str, float]:
    """Structured read of charged symbols; never parse the rendered prose."""
    return {cr.benchmark: cr.claimed_score
            for cr in verdict.claim_results if cr.symbol == "holds"}


def _buyer_portfolio_summary(buyer: Lab) -> dict:
    frontier: Dict[str, Dict[str, float]] = {}
    for technique in buyer.portfolio:
        area = frontier.setdefault(technique.capability_area, {})
        for claim in technique.claims:
            current = area.get(claim.benchmark, 0.0)
            area[claim.benchmark] = max(current, claim.true_score)
    return {
        "lab_id": buyer.id,
        "stakes": dict(buyer.area_stakes),
        "frontier": frontier,
    }


def assert_reasoner_context_safe(value: Any, path: str = "context") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_CONTEXT_KEYS:
                raise AssertionError(f"{path} contains forbidden key {key!r}")
            assert_reasoner_context_safe(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_reasoner_context_safe(item, f"{path}[{index}]")
        return
    if isinstance(value, (Technique, ResultClaim)):
        raise AssertionError(f"{path} contains internal simulation objects")


def build_reasoner_context(
    buyer: Lab,
    technique: Technique,
    verdict: VerificationVerdict,
    accountant: LeakageAccountant,
) -> dict:
    remaining_bits = 0.0
    try:
        remaining_bits = accountant.state(technique.id, buyer.id).remaining_bits()
    except KeyError:
        remaining_bits = 0.0

    context = {
        "technique": {
            "id": technique.id,
            "name": technique.name,
            "capability_area": technique.capability_area,
            "carrier": technique.carrier,
        },
        "verdict": {
            "proven": list(verdict.proven),
            "trusted": list(verdict.trusted),
            "unprovable": list(verdict.unprovable),
        },
        "buyer_portfolio": _buyer_portfolio_summary(buyer),
        "proven_result_bounds": [
            {"benchmark": benchmark, "score_floor": score}
            for benchmark, score in _proven_scores(verdict).items()
        ],
        "remaining_leakage_bits": round(remaining_bits, 6),
    }
    assert_reasoner_context_safe(context)
    return context


def _buyer_from_summary(summary: Mapping[str, Any]) -> Lab:
    lab_id = str(summary.get("lab_id", "buyer"))
    frontier = summary.get("frontier", {})
    portfolio: List[Technique] = []
    if isinstance(frontier, dict):
        for area, benchmarks in frontier.items():
            if not isinstance(benchmarks, dict):
                continue
            claims = []
            for benchmark, best_score in benchmarks.items():
                try:
                    score = float(best_score)
                except (TypeError, ValueError):
                    continue
                claims.append(
                    ResultClaim(
                        benchmark=str(benchmark),
                        true_score=score,
                        claimed_score=score,
                    )
                )
            portfolio.append(
                Technique(
                    id=f"frontier:{lab_id}:{area}",
                    owner=lab_id,
                    name=f"{lab_id} frontier {area}",
                    capability_area=str(area),
                    carrier="pure_recipe",
                    secret_payload=f"frontier::{lab_id}::{area}",
                    entropy_bits=1.0,
                    claims=claims,
                )
            )
    return Lab(
        id=lab_id,
        name=lab_id,
        beneficial_entity=f"be:{lab_id}",
        portfolio=portfolio,
        credits=0,
        area_stakes={str(key): float(value) for key, value in dict(summary.get("stakes", {})).items()},
        tradeable={},
    )


def _technique_from_context(context: Mapping[str, Any]) -> Technique:
    technique = dict(context.get("technique", {}))
    claims = []
    for row in context.get("proven_result_bounds", []):
        if not isinstance(row, dict):
            continue
        benchmark = str(row.get("benchmark", ""))
        try:
            score = float(row.get("score_floor", 0.0))
        except (TypeError, ValueError):
            continue
        claims.append(
            ResultClaim(
                benchmark=benchmark,
                true_score=score,
                claimed_score=score,
            )
        )
    return Technique(
        id=str(technique.get("id", "observed-technique")),
        owner="seller",
        name=str(technique.get("name", "observed technique")),
        capability_area=str(technique.get("capability_area", "unknown")),
        carrier=str(technique.get("carrier", "pure_recipe")),
        secret_payload="sealed::not-visible-to-reasoner",
        entropy_bits=1.0,
        claims=claims,
        true_transfers=True,
        true_novel=True,
        probe_leak_per_query_bits=0.0,
        method_reveal_fraction=0.0,
    )


def deterministic_reasoner(context: dict) -> dict:
    assert_reasoner_context_safe(context)
    if not context.get("proven_result_bounds"):
        return {
            "est_value_credits": 0,
            "confidence": 0.2,
            "rationale": "no proven result survived the leakage budget; cannot justify value",
        }

    buyer = _buyer_from_summary(context.get("buyer_portfolio", {}))
    technique = _technique_from_context(context)
    proven_scores = {
        str(row["benchmark"]): float(row["score_floor"])
        for row in context.get("proven_result_bounds", [])
        if isinstance(row, dict) and "benchmark" in row and "score_floor" in row
    }
    breakdown = economics.valuation_breakdown(buyer, technique, proven_scores)
    est = economics.marginal_value(buyer, technique, proven_scores)
    confidence = 0.45 + 0.10 * min(3, len(proven_scores))

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
    return {
        "est_value_credits": max(0, int(est)),
        "confidence": max(0.0, min(0.95, confidence)),
        "rationale": rationale,
    }


def _extract_json_payload(raw: str) -> Optional[dict]:
    text = raw.strip()
    if not text:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def codex_reasoner(context: dict, timeout_seconds: float = 8.0) -> dict:
    assert_reasoner_context_safe(context)
    fallback = deterministic_reasoner(context)
    reasoner_bin = os.environ.get("IP_TRADE_REASONER_BIN", "")
    codex_bin = Path(reasoner_bin) if reasoner_bin else None
    if codex_bin is None or not codex_bin.exists():
        return fallback

    prompt = {
        "mode": "bounded_ip_trade_appraisal",
        "instructions": (
            "Estimate the buyer's value for the technique using only the provided "
            "bounded observation context. Return strict JSON with keys "
            "est_value_credits, confidence, rationale."
        ),
        "context": context,
    }
    try:
        completed = subprocess.run(
            [str(codex_bin), "exec"],
            input=json.dumps(prompt, sort_keys=True),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return fallback

    if completed.returncode != 0:
        return fallback

    payload = _extract_json_payload(completed.stdout)
    if payload is None:
        return fallback
    try:
        return {
            "est_value_credits": max(0, int(payload["est_value_credits"])),
            "confidence": max(0.0, min(0.95, float(payload["confidence"]))),
            "rationale": str(payload["rationale"]),
        }
    except (KeyError, TypeError, ValueError):
        return fallback


class AgentStrategies:
    def __init__(self, reasoner: Optional[Reasoner] = None) -> None:
        self.reasoner = reasoner or deterministic_reasoner
        self.observation_contexts: List[dict] = []

    def _reason(self, context: dict) -> dict:
        try:
            payload = dict(self.reasoner(context) or {})
            return {
                "est_value_credits": max(0, int(payload.get("est_value_credits", 0))),
                "confidence": max(0.0, min(0.95, float(payload.get("confidence", 0.2)))),
                "rationale": str(payload.get("rationale", "")),
            }
        except Exception:
            return deterministic_reasoner(context)

    def appraise(
        self,
        buyer: Lab,
        seller: Lab,
        technique: Technique,
        verdict: VerificationVerdict,
        accountant: LeakageAccountant,
        tick: int,
        hook: HumanHook,
        ledger,
    ) -> Appraisal:
        context = build_reasoner_context(buyer, technique, verdict, accountant)
        self.observation_contexts.append(copy.deepcopy(context))
        reasoning = self._reason(context)

        est = int(reasoning["est_value_credits"])
        confidence = float(reasoning["confidence"])
        rationale = str(reasoning["rationale"])
        bits_spent = 0.0

        probe_n = 20
        probe_bits = black_box_probe_bits(technique, probe_n)
        if est > 0:
            ok, _ = accountant.observe(
                technique.id,
                buyer.id,
                "black_box_probe",
                probe_bits,
                tick,
                note=f"{probe_n}-query confidence probe",
            )
            if ok:
                bits_spent += probe_bits
                confidence = min(0.95, confidence + 0.2)
                ledger.add(tick, buyer.id, "probe", f"{technique.id} n={probe_n} bits={probe_bits}")

        return Appraisal(
            technique_id=technique.id,
            appraiser=buyer.id,
            est_value_credits=est,
            confidence=confidence,
            rationale=rationale,
            bits_spent=bits_spent,
        )

    def seller_ask(self, seller: Lab, technique: Technique, reserve: int, hook: HumanHook):
        return strategies.seller_ask(seller, technique, reserve, hook)

    def buyer_bid(self, buyer: Lab, seller: Lab, technique: Technique, appraisal, hook: HumanHook):
        return strategies.buyer_bid(buyer, seller, technique, appraisal, hook)
