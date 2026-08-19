from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from . import strategies
from .agents import AgentStrategies, assert_reasoner_context_safe, deterministic_reasoner
from .engine import run_lane
from .hooks import scripted_hook
from .leakage import LeakageAccountant
from .scenario import build_rich_labs


def _outcome_by_id(result, technique_id: str):
    for outcome in result.outcomes:
        if outcome.technique_id == technique_id:
            return outcome
    return None


def _result_signature(result):
    return [
        (
            outcome.technique_id,
            outcome.appraisal.est_value_credits if outcome.appraisal else None,
            outcome.cross.outcome if outcome.cross else None,
            outcome.settlement.price if outcome.settlement else None,
            outcome.realized_value_credits,
            outcome.buyer_regret_credits,
            outcome.blocked_reason,
        )
        for outcome in result.outcomes
    ]


class RichScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self._court_dirs = []

    def tearDown(self) -> None:
        for path in self._court_dirs:
            shutil.rmtree(path, ignore_errors=True)

    def _track(self, *results) -> None:
        for result in results:
            if result.courtfile_dir:
                self._court_dirs.append(Path(result.courtfile_dir))

    def test_rich_scenario_exhibits_intended_lessons(self) -> None:
        a, b = build_rich_labs()
        accountant = LeakageAccountant()
        ab = run_lane(a, b, accountant, strategies, seed="rich-AB")
        ba = run_lane(b, a, accountant, strategies, seed="rich-BA")
        self._track(ab, ba)

        self.assertEqual(_outcome_by_id(ab, "B_ctx").blocked_reason, "no_marginal_value")
        self.assertEqual(_outcome_by_id(ba, "A_ctx").blocked_reason, "no_marginal_value")

        overclaimed = _outcome_by_id(ba, "A_data")
        self.assertIsNotNone(overclaimed)
        self.assertIsNone(overclaimed.settlement)
        self.assertTrue(any("NOT met" in line for line in overclaimed.verdict.proven))

        complementary = _outcome_by_id(ab, "B_rl")
        self.assertIsNotNone(complementary)
        self.assertIsNotNone(complementary.settlement)
        self.assertEqual(complementary.settlement.state, "settled")

        regret_case = _outcome_by_id(ab, "B_data")
        self.assertIsNotNone(regret_case)
        self.assertIsNotNone(regret_case.settlement)
        self.assertGreater(regret_case.buyer_regret_credits or 0, 0)

        all_outcomes = ab.outcomes + ba.outcomes
        self.assertTrue(any(outcome.settlement for outcome in all_outcomes))
        self.assertTrue(any(outcome.blocked_reason == "no_marginal_value" for outcome in all_outcomes))
        self.assertTrue(any(any("NOT met" in line for line in outcome.verdict.proven) for outcome in all_outcomes))
        self.assertTrue(any((outcome.buyer_regret_credits or 0) > 0 for outcome in all_outcomes))

    def test_scripted_hook_withhold_and_veto_block(self) -> None:
        hook = scripted_hook({"withhold": ["B_rl"], "veto_settlement_over": 1})
        a, b = build_rich_labs()
        accountant = LeakageAccountant()
        ab = run_lane(a, b, accountant, strategies, hook=hook, seed="hook-AB")
        ba = run_lane(b, a, accountant, strategies, hook=hook, seed="hook-BA")
        self._track(ab, ba)

        self.assertIsNone(_outcome_by_id(ab, "B_rl"))
        self.assertTrue(any("withheld from trade" in item for item in ab.account.what_did_not_cross))

        vetoed = _outcome_by_id(ba, "A_eff")
        self.assertIsNotNone(vetoed)
        self.assertEqual(vetoed.blocked_reason, "human_veto")
        self.assertIsNone(vetoed.settlement)

    def test_agent_strategies_deterministic_reasoner_matches_baseline(self) -> None:
        a1, b1 = build_rich_labs()
        accountant1 = LeakageAccountant()
        baseline_ab = run_lane(a1, b1, accountant1, strategies, seed="match-AB")
        baseline_ba = run_lane(b1, a1, accountant1, strategies, seed="match-BA")
        self._track(baseline_ab, baseline_ba)

        a2, b2 = build_rich_labs()
        accountant2 = LeakageAccountant()
        agent_strategies = AgentStrategies(reasoner=deterministic_reasoner)
        agent_ab = run_lane(a2, b2, accountant2, agent_strategies, seed="match-AB")
        agent_ba = run_lane(b2, a2, accountant2, agent_strategies, seed="match-BA")
        self._track(agent_ab, agent_ba)

        self.assertEqual(_result_signature(baseline_ab), _result_signature(agent_ab))
        self.assertEqual(_result_signature(baseline_ba), _result_signature(agent_ba))

    def test_reasoner_context_excludes_secret_payload_and_true_score(self) -> None:
        contexts = []

        def capture_reasoner(context: dict) -> dict:
            contexts.append(context)
            return deterministic_reasoner(context)

        a, b = build_rich_labs()
        accountant = LeakageAccountant()
        result = run_lane(a, b, accountant, AgentStrategies(reasoner=capture_reasoner), seed="context-AB")
        self._track(result)

        self.assertTrue(contexts)
        for context in contexts:
            assert_reasoner_context_safe(context)
            payload = json.dumps(context, sort_keys=True)
            self.assertNotIn("secret_payload", payload)
            self.assertNotIn("true_score", payload)


if __name__ == "__main__":
    unittest.main()
