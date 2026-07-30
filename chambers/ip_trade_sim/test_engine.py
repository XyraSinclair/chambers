from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from chambers.kernel import Ledger as KernelLedger

from . import courtfile, strategies
from .engine import run_lane
from .leakage import LeakageAccountant, method_reveal_bits
from .types import Lab, ResultClaim, Technique


def _make_lab(lab_id: str, stakes: dict, portfolio=None, reserve: int = 500) -> Lab:
    portfolio = portfolio or []
    return Lab(
        id=lab_id,
        name=lab_id,
        beneficial_entity=f"be:{lab_id}",
        portfolio=portfolio,
        credits=50000,
        area_stakes=stakes,
        reserve_floor_credits=reserve,
        max_leak_fraction_before_block=0.45,
        tradeable={technique.id: True for technique in portfolio},
    )


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._court_dirs = []

    def tearDown(self) -> None:
        for path in self._court_dirs:
            shutil.rmtree(path, ignore_errors=True)

    def _track_courtfile(self, result) -> None:
        if result.courtfile_dir:
            self._court_dirs.append(Path(result.courtfile_dir))

    def test_overclaimed_technique_fails_verification_no_settlement(self) -> None:
        buyer = _make_lab("buyer_overclaim", {"data_curation": 1.0})
        seller = _make_lab(
            "seller_overclaim",
            {"data_curation": 0.8},
            [
                Technique(
                    id="seller_data",
                    owner="seller_overclaim",
                    name="DedupeMax",
                    capability_area="data_curation",
                    carrier="curated_dataset",
                    secret_payload="dedupe::max",
                    entropy_bits=50.0,
                    claims=[ResultClaim("MMLU-lift", true_score=0.041, claimed_score=0.050)],
                    true_transfers=True,
                    true_novel=True,
                )
            ],
        )
        accountant = LeakageAccountant()
        result = run_lane(buyer, seller, accountant, strategies, seed="test-overclaim")
        self._track_courtfile(result)

        self.assertEqual(len(result.outcomes), 1)
        outcome = result.outcomes[0]
        self.assertIsNone(outcome.settlement)
        self.assertEqual(outcome.appraisal.est_value_credits, 0)
        self.assertTrue(any("NOT met" in line for line in outcome.verdict.proven))

    def test_matching_buyer_frontier_means_no_trade(self) -> None:
        buyer_own = Technique(
            id="buyer_ctx",
            owner="buyer_same",
            name="Own frontier ctx",
            capability_area="long_context",
            carrier="static_checkpoint",
            secret_payload="ctx::own",
            entropy_bits=40.0,
            claims=[ResultClaim("RULER-128k", true_score=0.91, claimed_score=0.91)],
        )
        buyer = _make_lab("buyer_same", {"long_context": 1.0}, [buyer_own])
        seller = _make_lab(
            "seller_same",
            {"long_context": 0.6},
            [
                Technique(
                    id="seller_ctx",
                    owner="seller_same",
                    name="Comparable ctx",
                    capability_area="long_context",
                    carrier="static_checkpoint",
                    secret_payload="ctx::seller",
                    entropy_bits=40.0,
                    claims=[ResultClaim("RULER-128k", true_score=0.91, claimed_score=0.90)],
                )
            ],
        )
        accountant = LeakageAccountant()
        result = run_lane(buyer, seller, accountant, strategies, seed="test-same-frontier")
        self._track_courtfile(result)

        outcome = result.outcomes[0]
        self.assertEqual(outcome.appraisal.est_value_credits, 0)
        self.assertIsNone(outcome.settlement)
        self.assertEqual(outcome.blocked_reason, "no_marginal_value")

    def test_leakage_accountant_blocks_unsafe_overprobe(self) -> None:
        technique = Technique(
            id="probe_target",
            owner="seller",
            name="Probe target",
            capability_area="long_context",
            carrier="static_checkpoint",
            secret_payload="secret::probe",
            entropy_bits=10.0,
            claims=[],
        )
        accountant = LeakageAccountant()
        accountant.register(technique, "buyer", 0.5)
        allowed, state = accountant.observe("probe_target", "buyer", "black_box_probe", 4.0, 1, note="first probe")
        self.assertTrue(allowed)
        allowed, state = accountant.observe("probe_target", "buyer", "black_box_probe", 5.0, 2, note="too much")
        self.assertFalse(allowed)
        self.assertTrue(state.blocked)
        self.assertTrue(state.incident)

    def test_leakage_kernel_ledger_records_charge_and_refusal(self) -> None:
        technique = Technique(
            id="kernel_target",
            owner="seller",
            name="Kernel target",
            capability_area="long_context",
            carrier="static_checkpoint",
            secret_payload="secret::kernel",
            entropy_bits=10.0,
            claims=[],
        )
        accountant = LeakageAccountant()
        accountant.register(technique, "buyer", 0.5)
        allowed, _ = accountant.observe("kernel_target", "buyer", "black_box_probe", 4.0, 1, note="first probe")
        self.assertTrue(allowed)
        allowed, state = accountant.observe("kernel_target", "buyer", "black_box_probe", 5.0, 2, note="too much")
        self.assertFalse(allowed)
        self.assertTrue(state.blocked)

        self.assertEqual(accountant.ledger.audit(), [])
        charge_events = [event for event in accountant.ledger.events() if event.get("kind") == "charge"]
        self.assertTrue(
            any(
                event.get("channel") == "black_box_probe"
                and event.get("accepted") is True
                and event.get("debit_mbits") == 4000
                for event in charge_events
            )
        )
        self.assertTrue(
            any(
                event.get("reason_class") == "REFUSED_CEILING"
                and event.get("demand_mbits") == 5000
                and event.get("debit_mbits") == 0
                for event in charge_events
            )
        )
        replayed = KernelLedger.from_jsonl(accountant.ledger.to_jsonl())
        self.assertEqual(replayed.audit(), [])

    def test_paid_reveal_reaches_full_knowledge_legitimately(self) -> None:
        technique = Technique(
            id="paid_reveal_target",
            owner="seller",
            name="Paid reveal target",
            capability_area="rl_from_ai_feedback",
            carrier="curated_dataset",
            secret_payload="secret::paid",
            entropy_bits=10.0,
            claims=[],
        )
        accountant = LeakageAccountant()
        accountant.register(technique, "buyer", 0.4)
        allowed, state = accountant.observe("paid_reveal_target", "buyer", "result_verdict", 1.0, 1, note="verdict")
        self.assertTrue(allowed)
        allowed, state = accountant.observe(
            "paid_reveal_target",
            "buyer",
            "method_reveal_paid",
            method_reveal_bits(technique),
            2,
            note="settled reveal",
        )
        self.assertTrue(allowed)
        self.assertEqual(state.fraction, 1.0)
        self.assertFalse(state.incident)
        self.assertEqual(state.debits[-1].channel, "method_reveal_paid")

    def test_courtfile_validates_after_run(self) -> None:
        buyer = _make_lab("buyer_court", {"long_context": 1.0})
        seller = _make_lab(
            "seller_court",
            {"long_context": 0.5},
            [
                Technique(
                    id="seller_tradeable",
                    owner="seller_court",
                    name="Tradeable context lift",
                    capability_area="long_context",
                    carrier="static_checkpoint",
                    secret_payload="ctx::tradeable",
                    entropy_bits=80.0,
                    claims=[
                        ResultClaim("RULER-128k", true_score=0.95, claimed_score=0.94),
                        ResultClaim("LongBench", true_score=0.77, claimed_score=0.76),
                    ],
                    true_transfers=True,
                    true_novel=True,
                )
            ],
            reserve=400,
        )
        accountant = LeakageAccountant()
        result = run_lane(buyer, seller, accountant, strategies, seed="test-courtfile")
        self._track_courtfile(result)

        self.assertTrue(result.courtfile_dir)
        ok, message = courtfile.validate_ip_courtfile(result.courtfile_dir)
        self.assertTrue(ok, message)
        self.assertTrue(Path(result.courtfile_dir, "ledger.jsonl").exists())
        self.assertTrue(Path(result.courtfile_dir, "charge_kernel_ledger.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
