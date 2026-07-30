from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from .barter import run_barter_swap
from .leakage import LeakageAccountant
from .novelty import NoveltyEstimate
from .types import Lab, ResultClaim, Technique
from .valuation import (BarterOnly, ExcludedFromMonetaryClearing, Monetary,
                        novelty_to_ood, ood_haircut, route_valuation)


def _lab(
    lab_id: str,
    technique: Technique,
    *,
    stakes: dict,
    leak_fraction: float,
) -> Lab:
    return Lab(
        id=lab_id,
        name=lab_id,
        beneficial_entity=f"be:{lab_id}",
        portfolio=[technique],
        credits=50000,
        area_stakes=stakes,
        reserve_floor_credits=0,
        max_leak_fraction_before_block=leak_fraction,
        tradeable={technique.id: True},
    )


def _technique(
    technique_id: str,
    owner: str,
    name: str,
    area: str,
    carrier: str,
    entropy_bits: float,
) -> Technique:
    return Technique(
        id=technique_id,
        owner=owner,
        name=name,
        capability_area=area,
        carrier=carrier,
        secret_payload=f"secret::{technique_id}",
        entropy_bits=entropy_bits,
        claims=[ResultClaim("RULER-128k", true_score=0.90, claimed_score=0.89)],
        true_transfers=True,
        true_novel=True,
    )


class BarterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._court_dirs = []

    def tearDown(self) -> None:
        for path in self._court_dirs:
            shutil.rmtree(path, ignore_errors=True)

    def _track(self, result) -> None:
        if result.courtfile_dir:
            self._court_dirs.append(Path(result.courtfile_dir))

    def test_excluded_from_monetary_clearing_never_monetary_clears(self) -> None:
        route, receipt = route_valuation(
            ExcludedFromMonetaryClearing("hold exclusivity"),
            "monetary",
            asset_id="crown_jewel",
        )
        self.assertEqual(route, "refuse")
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.reason, "priceless_excluded")
        self.assertTrue(receipt.discoverable_contact_signal)

    def test_ood_haircut_is_continuous_and_sparse_reads_relax_toward_one(self) -> None:
        just_below = novelty_to_ood(
            NoveltyEstimate(
                technique_id="t1",
                ood_score=0.49,
                prior_art_density=20,
                prior_art_examples=["example"],
                method="prior_art_density",
                confidence=0.60,
                gameability_caveat="dense enough to calibrate",
                backend="OfflineBackend",
            ),
            observer="labA",
        )
        just_above = novelty_to_ood(
            NoveltyEstimate(
                technique_id="t1",
                ood_score=0.51,
                prior_art_density=20,
                prior_art_examples=["example"],
                method="prior_art_density",
                confidence=0.60,
                gameability_caveat="dense enough to calibrate",
                backend="OfflineBackend",
            ),
            observer="labA",
        )
        dense_crowded = novelty_to_ood(
            NoveltyEstimate(
                technique_id="t2",
                ood_score=0.15,
                prior_art_density=200,
                prior_art_examples=["a", "b", "c"],
                method="prior_art_density",
                confidence=0.55,
                gameability_caveat="crowded neighborhood",
                backend="OfflineBackend",
            ),
            observer="labA",
        )
        sparse_unknown = novelty_to_ood(
            NoveltyEstimate(
                technique_id="t3",
                ood_score=0.50,
                prior_art_density=1,
                prior_art_examples=["no close prior art"],
                method="prior_art_density",
                confidence=0.20,
                gameability_caveat="SPARSE PRIOR ART = UNKNOWN, NOT NOVEL",
                backend="OfflineBackend",
            ),
            observer="labA",
        )

        below_haircut = ood_haircut(just_below)
        above_haircut = ood_haircut(just_above)
        self.assertLess(abs(above_haircut - below_haircut), 0.02)
        self.assertGreater(above_haircut, below_haircut)
        self.assertGreater(ood_haircut(sparse_unknown), ood_haircut(dense_crowded))
        self.assertGreater(ood_haircut(sparse_unknown), 0.90)

    def test_estimation_channel_debits_and_budget_trip_blocks_barter(self) -> None:
        left_technique = _technique(
            "left_low_budget",
            "labA",
            "Obscure Prism",
            "long_context",
            "lora_adapter",
            entropy_bits=8.0,
        )
        right_technique = _technique(
            "right_low_budget",
            "labB",
            "Quiet Ledger",
            "data_curation",
            "curated_dataset",
            entropy_bits=8.0,
        )
        left_lab = _lab("labA", left_technique, stakes={"data_curation": 1.0}, leak_fraction=0.10)
        right_lab = _lab("labB", right_technique, stakes={"long_context": 1.0}, leak_fraction=0.10)
        accountant = LeakageAccountant()

        result = run_barter_swap(
            left_lab,
            left_technique,
            BarterOnly(acceptable_carrier_classes=("curated_dataset",)),
            right_lab,
            right_technique,
            BarterOnly(acceptable_carrier_classes=("lora_adapter",)),
            accountant,
        )
        self._track(result)

        self.assertFalse(result.cleared)
        self.assertEqual(result.blocked_reason, "estimation_leakage_budget")
        self.assertTrue(any(row["blocked"] for row in accountant.report()))
        self.assertTrue(
            any(
                "buyer_conditioned_estimate_REFUSED" in [channel for channel, _bits in row["debits"]]
                for row in accountant.report()
            )
        )

    def test_clean_complementary_barter_clears(self) -> None:
        left_technique = _technique(
            "left_clear",
            "labA",
            "Medusa Decode Mesh",
            "inference_efficiency",
            "lora_adapter",
            entropy_bits=72.0,
        )
        right_technique = _technique(
            "right_clear",
            "labB",
            "Preference Curriculum Dedupe",
            "data_curation",
            "curated_dataset",
            entropy_bits=84.0,
        )
        left_lab = _lab(
            "labA",
            left_technique,
            stakes={"data_curation": 0.9, "inference_efficiency": 0.5},
            leak_fraction=0.45,
        )
        right_lab = _lab(
            "labB",
            right_technique,
            stakes={"inference_efficiency": 0.9, "data_curation": 0.5},
            leak_fraction=0.40,
        )
        accountant = LeakageAccountant()

        result = run_barter_swap(
            left_lab,
            left_technique,
            BarterOnly(acceptable_carrier_classes=("curated_dataset",)),
            right_lab,
            right_technique,
            BarterOnly(acceptable_carrier_classes=("lora_adapter",)),
            accountant,
        )
        self._track(result)

        self.assertTrue(result.cleared)
        self.assertIsNone(result.blocked_reason)
        self.assertEqual(len(result.assessments), 2)
        self.assertTrue(all(assessment.within_bounds for assessment in result.assessments))
        self.assertEqual(accountant.state("left_clear", "labB").fraction, 1.0)
        self.assertEqual(accountant.state("right_clear", "labA").fraction, 1.0)
        self.assertTrue(result.courtfile_dir)
        self.assertIn("ok", result.courtfile_validation)

    def test_carrier_class_mismatch_yields_refusal_receipt(self) -> None:
        left_technique = _technique(
            "left_mismatch",
            "labA",
            "Medusa Decode Mesh",
            "inference_efficiency",
            "lora_adapter",
            entropy_bits=72.0,
        )
        right_technique = _technique(
            "right_mismatch",
            "labB",
            "Preference Curriculum Dedupe",
            "data_curation",
            "curated_dataset",
            entropy_bits=84.0,
        )
        left_lab = _lab("labA", left_technique, stakes={"data_curation": 1.0}, leak_fraction=0.45)
        right_lab = _lab("labB", right_technique, stakes={"inference_efficiency": 1.0}, leak_fraction=0.40)
        accountant = LeakageAccountant()

        result = run_barter_swap(
            left_lab,
            left_technique,
            BarterOnly(acceptable_carrier_classes=("hosted_service",)),
            right_lab,
            right_technique,
            BarterOnly(acceptable_carrier_classes=("lora_adapter",)),
            accountant,
        )
        self._track(result)

        self.assertFalse(result.cleared)
        self.assertEqual(result.blocked_reason, "barter_class_mismatch")
        self.assertTrue(result.refusal_receipts)
        self.assertEqual(result.refusal_receipts[0].reason, "barter_class_mismatch")


if __name__ == "__main__":
    unittest.main()
