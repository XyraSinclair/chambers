from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from chambers.kernel import Ledger as KernelLedger

from .leakage import LeakageAccountant, method_reveal_bits
from .novelty import NoveltyBackend, OfflineBackend, estimate_novelty
from .types import Lab, LedgerEntry, PlainAccount, Technique, sha
from .valuation import (BarterOnly, OodEstimate, RefusalReceipt, Valuation,
                        carrier_class_acceptable, novelty_to_ood,
                        ood_midpoint, route_valuation)


MAX_OOD_MIDPOINT_GAP = 0.25


@dataclass(frozen=True)
class TechniqueSubmission:
    description: str
    keywords: str


@dataclass(frozen=True)
class BarterEstimateRecord:
    technique_id: str
    observer: str
    submission: TechniqueSubmission
    estimate: OodEstimate
    leakage_bits_spent: float
    blocked_by_budget: bool


@dataclass(frozen=True)
class DualEstimateAssessment:
    technique_id: str
    owner: str
    records: Tuple[BarterEstimateRecord, BarterEstimateRecord]
    midpoint_gap: float
    interval_overlap: bool
    calibration_backed: bool
    within_bounds: bool


@dataclass
class BarterResult:
    lane_id: str
    left_lab: str
    right_lab: str
    left_technique_id: str
    right_technique_id: str
    cleared: bool = False
    blocked_reason: Optional[str] = None
    refusal_receipts: List[RefusalReceipt] = None  # type: ignore
    assessments: List[DualEstimateAssessment] = None  # type: ignore
    ledger: List[LedgerEntry] = None  # type: ignore
    account: PlainAccount = None  # type: ignore
    courtfile_dir: Optional[str] = None
    courtfile_validation: Optional[str] = None


class Ledger:
    def __init__(self) -> None:
        self.entries: List[LedgerEntry] = []
        self._seq = 0

    def add(self, tick: int, actor: str, action: str, detail: str) -> LedgerEntry:
        parent = self.entries[-1].seq if self.entries else None
        entry = LedgerEntry(self._seq, tick, actor, action, detail, parent).finalize()
        self.entries.append(entry)
        self._seq += 1
        return entry


def _default_submission(technique: Technique) -> TechniqueSubmission:
    keywords = " ".join(
        [
            technique.name.lower(),
            technique.capability_area.replace("_", " "),
            technique.carrier.replace("_", " "),
        ]
    )
    description = (
        f"{technique.name} in {technique.capability_area} carried as {technique.carrier}; "
        f"claims={len(technique.claims)}"
    )
    return TechniqueSubmission(description=description, keywords=keywords)


def _submission_for(
    observer: Lab,
    technique: Technique,
    submissions: Optional[Mapping[Tuple[str, str], TechniqueSubmission]],
) -> TechniqueSubmission:
    if submissions is None:
        return _default_submission(technique)
    return submissions.get((observer.id, technique.id), _default_submission(technique))


def _interval_overlap(left: OodEstimate, right: OodEstimate) -> bool:
    left_lo, left_hi = left.confidence_interval
    right_lo, right_hi = right.confidence_interval
    return max(left_lo, right_lo) <= min(left_hi, right_hi) + 1e-9


def _assess_dual_estimates(
    technique: Technique,
    records: Sequence[BarterEstimateRecord],
) -> DualEstimateAssessment:
    if len(records) != 2:
        raise ValueError(f"expected 2 estimate records for {technique.id}, got {len(records)}")
    left, right = tuple(records)
    midpoint_gap = abs(ood_midpoint(left.estimate) - ood_midpoint(right.estimate))
    interval_overlap = _interval_overlap(left.estimate, right.estimate)
    calibration_backed = (
        left.estimate.calibration_covers_this_regime
        and right.estimate.calibration_covers_this_regime
    )
    within_bounds = (
        interval_overlap
        and midpoint_gap <= MAX_OOD_MIDPOINT_GAP
        and calibration_backed
    )
    return DualEstimateAssessment(
        technique_id=technique.id,
        owner=technique.owner,
        records=(left, right),
        midpoint_gap=midpoint_gap,
        interval_overlap=interval_overlap,
        calibration_backed=calibration_backed,
        within_bounds=within_bounds,
    )


def _register_estimation_budgets(
    accountant: LeakageAccountant,
    techniques: Sequence[Technique],
    observers: Sequence[Lab],
) -> None:
    for technique in techniques:
        for observer in observers:
            accountant.register(
                technique,
                observer.id,
                observer.max_leak_fraction_before_block,
            )


def _barter_receipt(
    lane_id: str,
    left_lab: Lab,
    left_technique: Technique,
    right_lab: Lab,
    right_technique: Technique,
    cleared: bool,
    blocked_reason: Optional[str],
    estimate_crossings: Sequence[str],
) -> PlainAccount:
    what_crossed = list(estimate_crossings)
    what_did_not_cross = [
        "no scalar price crossed",
        "no proof of novelty, causality, or transfer crossed",
    ]
    if cleared:
        what_crossed.extend(
            [
                f"{left_technique.name} crossed in full to {right_lab.name} after barter settlement",
                f"{right_technique.name} crossed in full to {left_lab.name} after barter settlement",
            ]
        )
    else:
        what_did_not_cross.extend(
            [
                f"{left_technique.name} did not fully cross",
                f"{right_technique.name} did not fully cross",
            ]
        )
        if blocked_reason:
            what_did_not_cross.append(f"swap blocked: {blocked_reason}")
    return PlainAccount(
        lane_id=lane_id,
        what_crossed=what_crossed,
        what_did_not_cross=what_did_not_cross,
        who_was_paid=[],
        what_it_cannot_promise=[
            "calibration paradox: a crown jewel can look far from public prior art precisely because the real prior art is secret",
            "valuation tags are cheap talk until backed by a carrier-fit barter or bond",
            "sparse prior art != novel; sparse means unknown and confidence is crushed",
            "the estimated lane never proves novelty, causality, or transfer",
        ],
    )


def run_barter_swap(
    left_lab: Lab,
    left_technique: Technique,
    left_valuation: Valuation,
    right_lab: Lab,
    right_technique: Technique,
    right_valuation: Valuation,
    accountant: LeakageAccountant,
    *,
    backend: Optional[NoveltyBackend] = None,
    submissions: Optional[Mapping[Tuple[str, str], TechniqueSubmission]] = None,
    limit: int = 25,
) -> BarterResult:
    lane_id = f"barter:{left_lab.id}<->{right_lab.id}:{left_technique.id}:{right_technique.id}"
    ledger = Ledger()
    ledger.add(0, "system", "barter_open", lane_id)
    result = BarterResult(
        lane_id=lane_id,
        left_lab=left_lab.id,
        right_lab=right_lab.id,
        left_technique_id=left_technique.id,
        right_technique_id=right_technique.id,
        refusal_receipts=[],
        assessments=[],
        ledger=[],
    )
    used_backend = backend or OfflineBackend()
    tick = 1

    left_route, left_refusal = route_valuation(left_valuation, "barter", asset_id=left_technique.id)
    right_route, right_refusal = route_valuation(right_valuation, "barter", asset_id=right_technique.id)
    for receipt in (left_refusal, right_refusal):
        if receipt is not None:
            result.refusal_receipts.append(receipt)
            ledger.add(
                tick,
                "system",
                "valuation_refusal",
                f"{receipt.asset_id} reason={receipt.reason} note={receipt.note}",
            )
            tick += 1
    if left_route != "barter_match" or right_route != "barter_match":
        result.cleared = False
        result.blocked_reason = "valuation_refusal"
        result.account = _barter_receipt(
            lane_id,
            left_lab,
            left_technique,
            right_lab,
            right_technique,
            False,
            result.blocked_reason,
            ["a refusal receipt crossed; refusal itself is a discoverable contact signal"],
        )
        result.ledger = ledger.entries
        court_dir = persist_barter_courtfile(result, accountant)
        ok, message = validate_barter_courtfile(court_dir)
        result.courtfile_dir = str(court_dir)
        result.courtfile_validation = message
        return result

    if not carrier_class_acceptable(left_valuation, right_technique.carrier):
        receipt = RefusalReceipt(
            asset_id=left_technique.id,
            reason="barter_class_mismatch",
            note=(
                f"{left_technique.name} only accepts {tuple(getattr(left_valuation, 'acceptable_carrier_classes', ()))}, "
                f"not {right_technique.carrier}"
            ),
        )
        result.refusal_receipts.append(receipt)
    if not carrier_class_acceptable(right_valuation, left_technique.carrier):
        receipt = RefusalReceipt(
            asset_id=right_technique.id,
            reason="barter_class_mismatch",
            note=(
                f"{right_technique.name} only accepts {tuple(getattr(right_valuation, 'acceptable_carrier_classes', ()))}, "
                f"not {left_technique.carrier}"
            ),
        )
        result.refusal_receipts.append(receipt)
    if result.refusal_receipts:
        for receipt in result.refusal_receipts:
            ledger.add(
                tick,
                "system",
                "barter_refusal",
                f"{receipt.asset_id} reason={receipt.reason} note={receipt.note}",
            )
            tick += 1
        result.cleared = False
        result.blocked_reason = "barter_class_mismatch"
        result.account = _barter_receipt(
            lane_id,
            left_lab,
            left_technique,
            right_lab,
            right_technique,
            False,
            result.blocked_reason,
            [],
        )
        result.ledger = ledger.entries
        court_dir = persist_barter_courtfile(result, accountant)
        ok, message = validate_barter_courtfile(court_dir)
        result.courtfile_dir = str(court_dir)
        result.courtfile_validation = message
        return result

    _register_estimation_budgets(
        accountant,
        [left_technique, right_technique],
        [left_lab, right_lab],
    )

    estimate_crossings: List[str] = []
    records_by_technique: Dict[str, List[BarterEstimateRecord]] = {
        left_technique.id: [],
        right_technique.id: [],
    }
    for observer in (left_lab, right_lab):
        for technique in (left_technique, right_technique):
            submission = _submission_for(observer, technique, submissions)
            before_bits = accountant.state(technique.id, observer.id).cumulative_bits
            novelty_estimate = estimate_novelty(
                technique_id=technique.id,
                description=submission.description,
                keywords=submission.keywords,
                backend=used_backend,
                limit=limit,
                accountant=accountant,
                observer=observer.id,
            )
            state = accountant.state(technique.id, observer.id)
            spent_bits = max(0.0, state.cumulative_bits - before_bits)
            record = BarterEstimateRecord(
                technique_id=technique.id,
                observer=observer.id,
                submission=submission,
                estimate=novelty_to_ood(
                    novelty_estimate,
                    observer=observer.id,
                    leakage_bits_spent=spent_bits,
                ),
                leakage_bits_spent=spent_bits,
                blocked_by_budget=state.blocked,
            )
            records_by_technique[technique.id].append(record)
            estimate_crossings.append(
                f"{observer.name} got an estimated OOD read on {technique.name} "
                f"(bits {spent_bits:.2f}, blocked={state.blocked})"
            )
            ledger.add(
                tick,
                observer.id,
                "estimate_novelty",
                (
                    f"{technique.id} midpoint={ood_midpoint(record.estimate):.2f} "
                    f"interval={record.estimate.confidence_interval} bits={spent_bits:.2f} "
                    f"blocked={state.blocked}"
                ),
            )
            tick += 1

    left_assessment = _assess_dual_estimates(left_technique, records_by_technique[left_technique.id])
    right_assessment = _assess_dual_estimates(right_technique, records_by_technique[right_technique.id])
    result.assessments = [left_assessment, right_assessment]
    budget_blocked = any(
        record.blocked_by_budget
        for assessment in result.assessments
        for record in assessment.records
    )
    within_bounds = all(assessment.within_bounds for assessment in result.assessments)
    if budget_blocked:
        result.cleared = False
        result.blocked_reason = "estimation_leakage_budget"
        ledger.add(tick, "system", "barter_blocked", result.blocked_reason)
        tick += 1
    elif not within_bounds:
        result.cleared = False
        result.blocked_reason = "ood_out_of_bounds"
        ledger.add(tick, "system", "barter_blocked", result.blocked_reason)
        tick += 1
    else:
        accountant.observe(
            left_technique.id,
            right_lab.id,
            "method_reveal_paid",
            method_reveal_bits(left_technique),
            tick,
            note=f"barter settlement reveal from {left_lab.id} to {right_lab.id}",
        )
        accountant.observe(
            right_technique.id,
            left_lab.id,
            "method_reveal_paid",
            method_reveal_bits(right_technique),
            tick,
            note=f"barter settlement reveal from {right_lab.id} to {left_lab.id}",
        )
        result.cleared = True
        ledger.add(
            tick,
            "consortium",
            "barter_settle",
            f"{left_technique.id}<->{right_technique.id} no_scalar_price",
        )
        tick += 1

    result.account = _barter_receipt(
        lane_id,
        left_lab,
        left_technique,
        right_lab,
        right_technique,
        result.cleared,
        result.blocked_reason,
        estimate_crossings,
    )
    result.ledger = ledger.entries
    court_dir = persist_barter_courtfile(result, accountant)
    ok, message = validate_barter_courtfile(court_dir)
    result.courtfile_dir = str(court_dir)
    result.courtfile_validation = message
    if not ok:
        ledger.add(tick, "system", "courtfile_invalid", message)
        result.ledger = ledger.entries
    return result


def _repo_chamber_root() -> Path:
    # CHAMBER_COURT_ROOT: same override as courtfile.py — confined runs
    # write court files to writable ground, never into the packet tree.
    override = os.environ.get("CHAMBER_COURT_ROOT")
    if override:
        return Path(override) / "ip_trades" / "barter"
    return Path(__file__).resolve().parents[1] / ".chamber" / "ip_trades" / "barter"


def barter_courtfile_dir(lane_id: str) -> Path:
    return _repo_chamber_root() / lane_id


def _to_data(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def _barter_leakage_rows(result: BarterResult, accountant: LeakageAccountant) -> List[Dict[str, Any]]:
    technique_ids = {result.left_technique_id, result.right_technique_id}
    observers = {result.left_lab, result.right_lab}
    rows: List[Dict[str, Any]] = []
    for row in accountant.report():
        if row.get("technique") in technique_ids and row.get("observer") in observers:
            rows.append(dict(row))
    return rows


def persist_barter_courtfile(result: BarterResult, accountant: LeakageAccountant) -> Path:
    out_dir = barter_courtfile_dir(result.lane_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    kernel_audit = accountant.ledger.audit()
    assert kernel_audit == [], f"charge-kernel ledger audit findings: {kernel_audit}"
    _write_jsonl(out_dir / "ledger.jsonl", [_to_data(entry) for entry in result.ledger])
    (out_dir / "charge_kernel_ledger.jsonl").write_text(
        accountant.ledger.to_jsonl(),
        encoding="utf-8",
    )
    _write_jsonl(
        out_dir / "estimates.jsonl",
        [
            {
                "lane_id": result.lane_id,
                "technique_id": assessment.technique_id,
                "assessment": _to_data(assessment),
            }
            for assessment in result.assessments
        ],
    )
    _write_json(
        out_dir / "swap.json",
        {
            "lane_id": result.lane_id,
            "left_lab": result.left_lab,
            "right_lab": result.right_lab,
            "left_technique_id": result.left_technique_id,
            "right_technique_id": result.right_technique_id,
            "cleared": result.cleared,
            "blocked_reason": result.blocked_reason,
            "refusal_receipts": [_to_data(receipt) for receipt in result.refusal_receipts],
            "binding": sha(
                f"{result.left_technique_id}:{result.right_technique_id}:{result.cleared}:{result.blocked_reason}"
            ),
        },
    )
    _write_json(
        out_dir / "leakage_report.json",
        {"lane_id": result.lane_id, "rows": _barter_leakage_rows(result, accountant)},
    )
    _write_json(out_dir / "receipt.json", _to_data(result.account))
    return out_dir


def validate_barter_courtfile(path: Any) -> Tuple[bool, str]:
    try:
        base = Path(path)
        if not base.is_dir():
            return False, f"missing barter courtfile dir: {base}"
        required = [
            "ledger.jsonl",
            "charge_kernel_ledger.jsonl",
            "estimates.jsonl",
            "swap.json",
            "leakage_report.json",
            "receipt.json",
        ]
        for name in required:
            if not (base / name).exists():
                return False, f"missing {name}"
        ledger_rows = [line for line in (base / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        if not ledger_rows:
            return False, "ledger.jsonl is empty"
        kernel_ledger = KernelLedger.from_jsonl(
            (base / "charge_kernel_ledger.jsonl").read_text(encoding="utf-8")
        )
        kernel_audit = kernel_ledger.audit()
        if kernel_audit:
            return False, f"charge-kernel audit findings: {kernel_audit}"
        receipt = json.loads((base / "receipt.json").read_text(encoding="utf-8"))
        caveats = receipt.get("what_it_cannot_promise")
        if not isinstance(caveats, list) or not caveats:
            return False, "receipt.json must include non-empty caveats"
        return True, f"barter court file ok: ledger={len(ledger_rows)} kernel_events={kernel_ledger.event_count()}"
    except Exception as exc:
        return False, f"barter court file invalid: {exc}"
