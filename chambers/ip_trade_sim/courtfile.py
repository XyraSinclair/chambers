from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from chambers.kernel import Ledger as KernelLedger

from .types import sha


def _repo_chamber_root() -> Path:
    # CHAMBER_COURT_ROOT lets a confined run (read-only worktree, e.g. the
    # read-only CI sandbox) direct court files to writable ground.
    override = os.environ.get("CHAMBER_COURT_ROOT")
    if override:
        return Path(override) / "ip_trades"
    return Path(__file__).resolve().parents[1] / ".chamber" / "ip_trades"


def lane_courtfile_dir(lane_id: str) -> Path:
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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path.name} contains a non-object row")
        rows.append(value)
    return rows


def _lane_leakage_rows(result: Any, accountant: Any) -> List[Dict[str, Any]]:
    technique_ids = {outcome.technique_id for outcome in result.outcomes}
    lane_prefix = f"valuation:{result.lane_id}:"
    rows: List[Dict[str, Any]] = []
    for row in accountant.report():
        technique = str(row.get("technique", ""))
        observer = str(row.get("observer", ""))
        if technique in technique_ids or technique.startswith(lane_prefix):
            if observer in {result.buyer, result.seller}:
                rows.append(dict(row))
    return rows


def persist_ip_courtfile(result: Any, accountant: Any) -> Path:
    out_dir = lane_courtfile_dir(result.lane_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    kernel_audit = accountant.ledger.audit()
    assert kernel_audit == [], f"charge-kernel ledger audit findings: {kernel_audit}"

    ledger_rows = [_to_data(entry) for entry in result.ledger]
    verdict_rows = []
    negotiation_rows = []
    settlement_rows = []

    for outcome in result.outcomes:
        verdict_rows.append(
            {
                "lane_id": result.lane_id,
                "technique_id": outcome.technique_id,
                "verdict": _to_data(outcome.verdict),
            }
        )
        if getattr(outcome, "negotiation", None) is not None:
            negotiation = _to_data(outcome.negotiation)
            # the transcript's final_cross carries party-private draws and
            # reserve; the persisted view keeps only what legitimately crossed
            if isinstance(negotiation, dict) and isinstance(negotiation.get("final_cross"), dict):
                fc = negotiation["final_cross"]
                negotiation["final_cross"] = {
                    "technique_id": fc.get("technique_id"),
                    "outcome": fc.get("outcome"),
                    "cleared_price": fc.get("cleared_price"),
                    "counterparty_learns": fc.get("counterparty_learns"),
                }
            negotiation_rows.append(
                {
                    "lane_id": result.lane_id,
                    "technique_id": outcome.technique_id,
                    "negotiation": negotiation,
                }
            )
        if outcome.settlement is not None:
            # the persisted cross is REDACTED to what legitimately crossed:
            # draws and reserve are party-private inputs; realized value and
            # regret are functions of the buyer's private valuation and stay
            # out of the shared court record entirely
            cross = outcome.cross
            settlement_rows.append(
                {
                    "lane_id": result.lane_id,
                    "technique_id": outcome.technique_id,
                    "verdict": _to_data(outcome.verdict),
                    "cross": {
                        "technique_id": cross.technique_id,
                        "outcome": cross.outcome,
                        "cleared_price": cross.cleared_price,
                        "counterparty_learns": cross.counterparty_learns,
                    },
                    "settlement": _to_data(outcome.settlement),
                }
            )

    _write_jsonl(out_dir / "ledger.jsonl", ledger_rows)
    _write_jsonl(out_dir / "verdicts.jsonl", verdict_rows)
    _write_jsonl(out_dir / "negotiations.jsonl", negotiation_rows)
    _write_jsonl(out_dir / "settlements.jsonl", settlement_rows)
    (out_dir / "charge_kernel_ledger.jsonl").write_text(
        accountant.ledger.to_jsonl(),
        encoding="utf-8",
    )
    _write_json(out_dir / "leakage_report.json", {"lane_id": result.lane_id, "rows": _lane_leakage_rows(result, accountant)})
    _write_json(out_dir / "receipt.json", _to_data(result.account))
    return out_dir


def validate_ip_courtfile(path: Any) -> Tuple[bool, str]:
    try:
        base = Path(path)
        if not base.is_dir():
            return False, f"missing courtfile dir: {base}"

        required = [
            "ledger.jsonl",
            "charge_kernel_ledger.jsonl",
            "verdicts.jsonl",
            "negotiations.jsonl",
            "leakage_report.json",
            "receipt.json",
            "settlements.jsonl",
        ]
        for name in required:
            if not (base / name).exists():
                return False, f"missing {name}"

        ledger = _load_jsonl(base / "ledger.jsonl")
        kernel_text = (base / "charge_kernel_ledger.jsonl").read_text(encoding="utf-8")
        kernel_ledger = KernelLedger.from_jsonl(kernel_text)
        verdicts = _load_jsonl(base / "verdicts.jsonl")
        _negotiations = _load_jsonl(base / "negotiations.jsonl")
        settlements = _load_jsonl(base / "settlements.jsonl")
        leakage_payload = _load_json(base / "leakage_report.json")
        receipt = _load_json(base / "receipt.json")

        if not ledger:
            return False, "ledger.jsonl is empty"

        previous_seq = None
        seen_seqs = set()
        for idx, entry in enumerate(ledger, start=1):
            seq = entry.get("seq")
            parent = entry.get("parent")
            if seq in seen_seqs:
                return False, f"duplicate ledger seq at row {idx}: {seq}"
            expected_hash = sha(
                f"{entry.get('seq')}:{entry.get('actor')}:{entry.get('action')}:"
                f"{entry.get('detail')}:{entry.get('parent')}"
            )
            if entry.get("detail_hash") != expected_hash:
                return False, f"bad ledger hash at row {idx}"
            if idx == 1:
                if parent is not None:
                    return False, "first ledger parent must be null"
            else:
                if parent != previous_seq:
                    return False, f"ledger chain break at row {idx}"
            previous_seq = seq
            seen_seqs.add(seq)

        if not verdicts:
            return False, "verdicts.jsonl is empty"

        for idx, row in enumerate(settlements, start=1):
            verdict = row.get("verdict")
            cross = row.get("cross")
            settlement = row.get("settlement")
            if not isinstance(verdict, dict) or not verdict.get("technique_id"):
                return False, f"settlements.jsonl:{idx} missing verdict"
            if not isinstance(cross, dict) or cross.get("outcome") != "cleared":
                return False, f"settlements.jsonl:{idx} must reference a cleared cross"
            if not isinstance(settlement, dict) or not settlement.get("technique_id"):
                return False, f"settlements.jsonl:{idx} missing settlement payload"

        leakage_rows = leakage_payload.get("rows") if isinstance(leakage_payload, dict) else leakage_payload
        if not isinstance(leakage_rows, list):
            return False, "leakage_report.json rows must be a list"
        for idx, row in enumerate(leakage_rows, start=1):
            fraction = float(row.get("fraction", 0.0))
            incident = bool(row.get("incident", False))
            debits = row.get("debits", [])
            if not isinstance(debits, list):
                return False, f"leakage row {idx} debits must be a list"
            channels = [entry[0] for entry in debits if isinstance(entry, list) and entry]
            if fraction >= 0.8 and "method_reveal_paid" not in channels and not incident:
                return False, f"leakage row {idx} crossed unsafe fraction without an incident flag"

        caveats = receipt.get("what_it_cannot_promise")
        if not isinstance(caveats, list) or not caveats:
            return False, "receipt.json must include non-empty caveats"

        kernel_audit = kernel_ledger.audit()
        if kernel_audit:
            return False, f"charge-kernel audit findings: {kernel_audit}"

        return True, (
            f"court file ok: ledger={len(ledger)} verdicts={len(verdicts)} "
            f"settlements={len(settlements)} leakage_rows={len(leakage_rows)} "
            f"kernel_events={kernel_ledger.event_count()}"
        )
    except Exception as exc:
        return False, f"court file invalid: {exc}"
