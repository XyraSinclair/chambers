"""Run the barter-first wedge for the IP-trade simulation.

    python3 -m chambers.ip_trade_sim.run_barter
"""
from __future__ import annotations

from .barter import run_barter_swap
from .leakage import LeakageAccountant
from .types import Lab, ResultClaim, Technique
from .valuation import (BarterOnly, ExcludedFromMonetaryClearing,
                        route_valuation)


def _lab(
    lab_id: str,
    name: str,
    stakes: dict,
    technique: Technique,
    max_leak_fraction_before_block: float = 0.45,
) -> Lab:
    return Lab(
        id=lab_id,
        name=name,
        beneficial_entity=f"be:{lab_id}",
        portfolio=[technique],
        credits=50000,
        area_stakes=stakes,
        reserve_floor_credits=0,
        max_leak_fraction_before_block=max_leak_fraction_before_block,
        tradeable={technique.id: True},
    )


def _build_demo():
    left_technique = Technique(
        id="A_adapter",
        owner="labA",
        name="Medusa Ladder",
        capability_area="inference_efficiency",
        carrier="lora_adapter",
        secret_payload="medusa::ladder::adapter-v2",
        entropy_bits=72.0,
        claims=[ResultClaim("tok/s@70B", true_score=3.6, claimed_score=3.5)],
        true_transfers=True,
        true_novel=True,
    )
    right_technique = Technique(
        id="B_corpus",
        owner="labB",
        name="Preference Curriculum Mesh",
        capability_area="data_curation",
        carrier="curated_dataset",
        secret_payload="preference::curriculum::mesh-v4",
        entropy_bits=88.0,
        claims=[ResultClaim("MMLU-lift", true_score=0.055, claimed_score=0.050)],
        true_transfers=True,
        true_novel=True,
    )
    left_lab = _lab(
        "labA",
        "Saffron Labs",
        {"inference_efficiency": 0.9, "data_curation": 0.7},
        left_technique,
        max_leak_fraction_before_block=0.45,
    )
    right_lab = _lab(
        "labB",
        "Harbor Research",
        {"inference_efficiency": 0.8, "data_curation": 0.95},
        right_technique,
        max_leak_fraction_before_block=0.40,
    )
    left_valuation = BarterOnly(acceptable_carrier_classes=("curated_dataset",))
    right_valuation = BarterOnly(acceptable_carrier_classes=("lora_adapter",))
    return left_lab, left_technique, left_valuation, right_lab, right_technique, right_valuation


def _print_refusal_demo() -> None:
    excluded = ExcludedFromMonetaryClearing(
        exclusivity_rationale="frontier decode moat retained for exclusivity",
    )
    route, receipt = route_valuation(excluded, "monetary", asset_id="A_exclusive")
    print("ExcludedFromMonetaryClearing demo")
    print(f"  route: {route}")
    if receipt is not None:
        print(f"  refusal: {receipt.reason}  discoverable_contact_signal={receipt.discoverable_contact_signal}")
        print(f"  note: {receipt.note}")


def _print_barter_result(result, accountant) -> None:
    print(f"\n{'='*70}\nBARTER  {result.lane_id}\n{'='*70}")
    print(f"cleared: {result.cleared}  blocked_reason: {result.blocked_reason}")
    for assessment in result.assessments:
        print(f"\n  ◆ {assessment.technique_id}  within_bounds={assessment.within_bounds}")
        print(
            f"    midpoint_gap={assessment.midpoint_gap:.2f} "
            f"interval_overlap={assessment.interval_overlap} "
            f"calibration_backed={assessment.calibration_backed}"
        )
        for record in assessment.records:
            print(
                f"    {record.observer}: midpoint={((record.estimate.confidence_interval[0] + record.estimate.confidence_interval[1]) / 2.0):.2f} "
                f"interval={record.estimate.confidence_interval} "
                f"bits={record.leakage_bits_spent:.2f} blocked={record.blocked_by_budget}"
            )
            print(f"      citations={list(record.estimate.evidence_citations)}")
            print(f"      caveat={record.estimate.gameability_caveat}")
    if result.refusal_receipts:
        print("\n  refusals:")
        for receipt in result.refusal_receipts:
            print(f"    - {receipt.asset_id}: {receipt.reason} ({receipt.note})")

    print("\n  --- PlainAccount receipt ---")
    for item in result.account.what_crossed or ["(nothing)"]:
        print(f"    + {item}")
    for item in result.account.what_did_not_cross or ["(nothing)"]:
        print(f"    - {item}")
    for item in result.account.what_it_cannot_promise:
        print(f"    ! {item}")

    print(f"\n  courtfile: {result.courtfile_dir}")
    print(f"  validation: {result.courtfile_validation}")
    print(f"\n{'='*70}\nLEAKAGE REPORT\n{'='*70}")
    for row in accountant.report():
        if row["technique"] not in {result.left_technique_id, result.right_technique_id}:
            continue
        flag = " [blocked]" if row["blocked"] else ""
        print(
            f"  {row['observer']} learned {row['cumulative_bits']}/{row['entropy_bits']} bits "
            f"({row['fraction']*100:.0f}%, {row['class']}) of {row['technique']}{flag}"
        )
        print(f"      channels: {row['debits']}")
    audit = accountant.ledger.audit()
    if audit:
        raise RuntimeError(f"charge-kernel ledger audit findings: {audit}")
    print(f"\ncharge-kernel audit: clean ({accountant.ledger.event_count()} events)")


def main() -> None:
    _print_refusal_demo()
    left_lab, left_technique, left_valuation, right_lab, right_technique, right_valuation = _build_demo()
    accountant = LeakageAccountant()
    result = run_barter_swap(
        left_lab,
        left_technique,
        left_valuation,
        right_lab,
        right_technique,
        right_valuation,
        accountant,
    )
    _print_barter_result(result, accountant)


if __name__ == "__main__":
    main()
