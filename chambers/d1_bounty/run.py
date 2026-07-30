"""Runnable D1 scenarios + court-file writer.

    python3 -m chambers.d1_bounty.run

Five lanes exercise the load-bearing claims of the build decision:

  A. honest finding -> accepted, heldback, regression window clean -> zero-touch payout
  B. shipped fix regresses inside the window -> clawback (settlement slashed)
  C. verification-as-extraction: repeated per-build probes against the sealed
     patch diff trip the structured-bits ceiling (leakage stays bounded) while
     cumulative refused DEMAND crosses UNSAFE -> incident; never reconstructed
  D. oracle capture (author == worker beneficial entity) -> oracle inadmissible,
     no zero-touch path, human fallback
  E. self_interested estimator -> emission refused before the oracle ever runs
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, List, Tuple

from .bounty import (
    ConflictOfInterestCheck,
    EvaluatorOracle,
    PriceSchedule,
    SchedulePoint,
    SettlementPayoutAuthorization,
)
from .egress import (
    CapacityEstimate,
    EstimatorAttestation,
    Ledger,
    bits_to_mbits,
    enum_value_mbits,
    ordering_mbits,
    repro_text_mbits,
    sha,
)
from .engine import BountyLane, SealedArtifact, Submission


RUBRIC_HASH = sha("severity+reproducibility-rubric-v1")
MODEL_HASH = sha("corvid-checkpoint-2026-07")
PREDICATE_HASH = sha("accepted VEX reachability on actively-exploited CVE")


def _role_separated_estimator() -> EstimatorAttestation:
    return EstimatorAttestation(
        estimator_id="independent-estimator",
        independence="adversarial_review",
        method="static_schema_bound",
        worst_case_over_secrets=True,
    )


def _clean_oracle(worker_entity: str, author_entity: str = "fenwick-foundation") -> EvaluatorOracle:
    return EvaluatorOracle(
        oracle_id="oracle-vex-v1",
        model_class_hash=MODEL_HASH,
        rubric_hash=RUBRIC_HASH,
        determinism="deterministic",
        role="adversarial_review",
        conflict_check=ConflictOfInterestCheck(author_entity, worker_entity),
        appeal_path="human_steward",
    )


def _schedule(holdback: float = 0.4, window: int = 3) -> PriceSchedule:
    return PriceSchedule(
        schedule_id="sched-vex-v1",
        rubric_hash=RUBRIC_HASH,
        points=(
            SchedulePoint(0.50, 4_000),
            SchedulePoint(0.80, 12_000),
            SchedulePoint(0.90, 20_000),
        ),
        holdback_fraction=holdback,
        regression_window_ticks=window,
    )


def _authorization(schedule_id: str, per_payout: int = 25_000, window_cap: int = 50_000) -> SettlementPayoutAuthorization:
    return SettlementPayoutAuthorization(
        authorization_id="auth-1",
        authorized_by="human:meridian-psirt-lead",
        oracle_id="oracle-vex-v1",
        schedule_id=schedule_id,
        match_predicate_hash=PREDICATE_HASH,
        per_payout_ceiling=per_payout,
        window_ceiling=window_cap,
        valid_within_ticks=(0, 1000),
    )


def _lane(
    lane_id: str,
    worker_entity: str,
    ceiling_bits: float,
    oracle: EvaluatorOracle,
    artifact: SealedArtifact | None = None,
) -> BountyLane:
    sched = _schedule()
    return BountyLane(
        lane_id=lane_id,
        artifact=artifact
        or SealedArtifact("wolfden-in-Meridian", secret_source="<sealed crown-jewel TLS source>", structural_entropy_bits=4096.0),
        audience="cardinal-offensive",
        query_family="reachability",
        oracle=oracle,
        schedule=sched,
        authorization=_authorization(sched.schedule_id),
        ceiling_bits=ceiling_bits,
        worker_beneficial_entity=worker_entity,
    )


def _vex_estimate(k_paths: int, repro_bytes: int, estimator: EstimatorAttestation) -> CapacityEstimate:
    return CapacityEstimate(
        enum_value_mbits=enum_value_mbits(3),
        ordering_mbits=ordering_mbits(k_paths),
        field_presence_mbits=bits_to_mbits(2.0),
        text_mbits=repro_text_mbits(repro_bytes),
        side_channel_mbits=bits_to_mbits(1.0),
        channel="vex_verdict",
    )


# ---- the five lanes ----


def lane_a_honest() -> BountyLane:
    est = _role_separated_estimator()
    lane = _lane("A-honest", "cardinal-offensive", ceiling_bits=800.0, oracle=_clean_oracle("cardinal-offensive"))
    lane.run([
        Submission("wolfden CVE reachable in gateway firmware", claimed_reachable=True, true_reachable=True,
                   repro_replays=True, estimate=_vex_estimate(3, 40, est), estimator=est),
    ])
    lane.close_regression_window("A-honest-f1", regressed=False, tick=10)
    return lane


def lane_b_regressed() -> BountyLane:
    est = _role_separated_estimator()
    lane = _lane("B-regressed", "cardinal-offensive", ceiling_bits=800.0, oracle=_clean_oracle("cardinal-offensive"))
    lane.run([
        Submission("wolfden CVE reachable, patch shipped", claimed_reachable=True, true_reachable=True,
                   repro_replays=True, estimate=_vex_estimate(3, 40, est), estimator=est),
    ])
    lane.close_regression_window("B-regressed-f1", regressed=True, tick=10)
    return lane


def lane_c_extraction() -> BountyLane:
    """Verification-as-extraction. The campaign does not target the whole
    4096-bit source tree — it targets the PATCH DIFF: the localized ~512-bit
    structural secret whose reconstruction weaponizes the CVE. Each per-build
    probe looks safe; composition over the (subject × family × audience) key
    accumulates. The ceiling trips after the first probe (leakage stays
    bounded), while cumulative DEMAND — refused attempts included — crosses the
    UNSAFE fraction of the diff's entropy and latches the incident flag: the
    audience kept asking for reconstruction-grade capacity even after refusal."""
    est = _role_separated_estimator()
    diff = SealedArtifact(
        "wolfden-in-Meridian:patch-diff-2026-06",
        secret_source="<sealed pre/post-patch diff of the vulnerable TLS state machine>",
        structural_entropy_bits=512.0,
    )
    lane = _lane("C-extraction", "cardinal-offensive", ceiling_bits=120.0,
                 oracle=_clean_oracle("cardinal-offensive"), artifact=diff)
    subs = []
    for _ in range(6):
        subs.append(
            Submission("per-build reachability probe", claimed_reachable=True, true_reachable=True,
                       repro_replays=True, estimate=_vex_estimate(4, 8, est), estimator=est)
        )
    lane.run(subs)
    return lane


def lane_d_capture() -> BountyLane:
    # oracle author entity == worker beneficial entity -> conflicted -> inadmissible
    est = _role_separated_estimator()
    captured = _clean_oracle("cardinal-offensive", author_entity="cardinal-offensive")
    lane = _lane("D-capture", "cardinal-offensive", ceiling_bits=800.0, oracle=captured)
    lane.run([
        Submission("wolfden CVE reachable", claimed_reachable=True, true_reachable=True,
                   repro_replays=True, estimate=_vex_estimate(3, 40, est), estimator=est),
    ])
    return lane


def lane_e_self_interested() -> BountyLane:
    bad_est = EstimatorAttestation(
        estimator_id="corvid-itself",
        independence="self_interested",
        method="declared",
        worst_case_over_secrets=False,
    )
    lane = _lane("E-self-interested", "cardinal-offensive", ceiling_bits=800.0, oracle=_clean_oracle("cardinal-offensive"))
    lane.run([
        Submission("wolfden CVE reachable (self-metered)", claimed_reachable=True, true_reachable=True,
                   repro_replays=True, estimate=_vex_estimate(3, 40, bad_est), estimator=bad_est),
    ])
    return lane


ALL_LANES = [lane_a_honest, lane_b_regressed, lane_c_extraction, lane_d_capture, lane_e_self_interested]


# ---- court file ----


def _to_data(v: Any) -> Any:
    if is_dataclass(v):
        return asdict(v)
    return v


def _courtfile_root() -> Path:
    return Path(__file__).resolve().parent / "out" / "court"


def persist_courtfile(lane: BountyLane) -> Path:
    out = _courtfile_root() / lane.lane_id
    out.mkdir(parents=True, exist_ok=True)
    audit = lane._accountant.ledger.audit()
    assert audit == [], f"charge-kernel ledger audit findings: {audit}"
    with (out / "ledger.jsonl").open("w", encoding="utf-8") as fh:
        for e in lane.ledger:
            fh.write(json.dumps(_to_data(e), sort_keys=True) + "\n")
    (out / "charge_kernel_ledger.jsonl").write_text(
        lane._accountant.ledger.to_jsonl(),
        encoding="utf-8",
    )
    with (out / "findings.jsonl").open("w", encoding="utf-8") as fh:
        for f in lane.findings:
            fh.write(json.dumps(_to_data(f), sort_keys=True) + "\n")
    (out / "egress_report.json").write_text(
        json.dumps({"lane_id": lane.lane_id, "rows": lane._accountant.report()}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "receipt.json").write_text(
        json.dumps(_to_data(lane.account), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def validate_courtfile(path: Path) -> Tuple[bool, str]:
    base = Path(path)
    for name in ("ledger.jsonl", "charge_kernel_ledger.jsonl", "findings.jsonl", "egress_report.json", "receipt.json"):
        if not (base / name).exists():
            return False, f"missing {name}"
    # verify the ledger hash chain
    prev = None
    rows = [json.loads(l) for l in (base / "ledger.jsonl").read_text().splitlines() if l.strip()]
    if not rows:
        return False, "empty ledger"
    for i, e in enumerate(rows, 1):
        expect = sha(f"{e['seq']}:{e['actor']}:{e['action']}:{e['detail']}:{e['parent']}")
        if e.get("detail_hash") != expect:
            return False, f"bad ledger hash at row {i}"
        if i == 1 and e["parent"] is not None:
            return False, "first parent must be null"
        if i > 1 and e["parent"] != prev:
            return False, f"chain break at row {i}"
        prev = e["seq"]
    receipt = json.loads((base / "receipt.json").read_text())
    if not receipt.get("what_it_cannot_promise"):
        return False, "receipt missing non-empty caveats"
    kernel_ledger = Ledger.from_jsonl((base / "charge_kernel_ledger.jsonl").read_text())
    audit = kernel_ledger.audit()
    if audit:
        return False, f"charge-kernel audit findings: {audit}"
    return True, f"court file ok: ledger={len(rows)} kernel_events={kernel_ledger.event_count()}"


def main() -> None:
    print("D1 — third-party security research over sealed vendor artifacts (runnable slice)\n")
    for build in ALL_LANES:
        lane = build()
        out = persist_courtfile(lane)
        ok, msg = validate_courtfile(out)
        print(f"=== lane {lane.lane_id} ===")
        for f in lane.findings:
            settled = f.settlement.status if f.settlement else "—"
            print(f"  finding {f.finding_id}: egress_allowed={f.egress_allowed} accepted={f.accepted} "
                  f"score={f.oracle_score:.2f} settle={settled} payout={f.payout_path}")
            print(f"      {f.accept_reason}")
        rows = lane._accountant.report()
        for r in rows:
            print(f"  egress: cum={r['cumulative_bits']}/{r['ceiling_bits']} "
                  f"demanded={r['demanded_bits']} (frac {r['demanded_fraction']}) class={r['class']} "
                  f"blocked={r['blocked']} incident={r['incident']}")
        print(f"  charge-kernel audit: clean ({lane._accountant.ledger.event_count()} events)")
        print(f"  who was paid: {lane.account.who_was_paid}")
        print(f"  court file [{'OK' if ok else 'FAIL'}]: {msg}  ({out})\n")


if __name__ == "__main__":
    main()
