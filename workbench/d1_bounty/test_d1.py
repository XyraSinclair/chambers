"""Per-lane invariants + unit checks for the D1 bounty slice.

    python3 -m pytest workbench/d1_bounty/ -q
    python3 -m unittest workbench.d1_bounty.test_d1 -v

The lane tests pin the five labelled behaviours of run.py; the unit tests pin
the two places the handoff was explicitly skeptical about: the incident/ceiling
coupling in the egress accountant, and `close_regression_window`'s standing-
authorization window accounting.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from .bounty import (
    ConflictOfInterestCheck,
    EvaluatorOracle,
    PriceSchedule,
    SchedulePoint,
    SettlementPayoutAuthorization,
)
from .egress import (
    UNSAFE,
    CapacityEstimate,
    CompositionKey,
    EgressAccountant,
    EstimatorAttestation,
    bits_to_mbits,
    enum_value_bits,
    enum_value_mbits,
    estimate_total_bits,
    ordering_bits,
    ordering_mbits,
    repro_text_bits,
    repro_text_mbits,
)
from .engine import BountyLane, SealedArtifact, Submission
from .run import (
    _authorization,
    _clean_oracle,
    _role_separated_estimator,
    _schedule,
    _vex_estimate,
    lane_a_honest,
    lane_b_regressed,
    lane_c_extraction,
    lane_d_capture,
    lane_e_self_interested,
    persist_courtfile,
    validate_courtfile,
)


# ---- the five lanes, as labelled ----


class TestLaneInvariants(unittest.TestCase):
    def test_lane_a_honest_releases_zero_touch(self):
        lane = lane_a_honest()
        f = lane.findings[0]
        self.assertTrue(f.egress_allowed)
        self.assertTrue(f.accepted)
        self.assertIsNotNone(f.settlement)
        self.assertEqual(f.settlement.status, "released")
        self.assertEqual(f.payout_path, "zero_touch")
        # zero-touch means the standing authorization is named on the settlement
        self.assertEqual(f.settlement.authorization_id, lane.authorization.authorization_id)
        # the receipt reflects final state, not the pre-window snapshot
        self.assertEqual(len(lane.account.who_was_paid), 1)
        self.assertIn("zero_touch", lane.account.who_was_paid[0])
        self.assertIn(f.settlement.recipient, lane.account.who_was_paid[0])

    def test_lane_b_regression_claws_back(self):
        lane = lane_b_regressed()
        f = lane.findings[0]
        self.assertEqual(f.settlement.status, "slashed")
        self.assertEqual(f.payout_path, "none")
        # no one paid, and the refreshed receipt says so
        self.assertEqual(lane.account.who_was_paid, ["no one yet (all heldback, clawed back, or refused)"])

    def test_lane_c_blocks_flags_incident_never_reconstructs(self):
        lane = lane_c_extraction()
        st = lane._accountant.state(lane.key())
        self.assertTrue(st.blocked)
        self.assertTrue(st.incident)
        # the incident is about DEMAND, not leakage: what actually crossed
        # stays under the ceiling and far from reconstruction
        # Exact integer millibit accounting replaced the old epsilon edge.
        self.assertLess(st.cumulative_mbits, st.ceiling_mbits)
        self.assertLess(st.fraction, 1.0)
        self.assertNotEqual(st.leakage_class, "reconstructed")
        self.assertGreaterEqual(st.demanded_fraction, UNSAFE)
        # exactly one probe crossed; every later one was refused
        accepted = [f for f in lane.findings if f.egress_allowed]
        refused = [f for f in lane.findings if not f.egress_allowed]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(refused), 5)
        for f in refused:
            self.assertFalse(f.accepted)
            self.assertIn("refused by egress accountant", f.accept_reason)

    def test_lane_d_oracle_capture_falls_back_to_human(self):
        lane = lane_d_capture()
        ok, why = lane.oracle.is_admissible()
        self.assertFalse(ok)
        self.assertIn("capture", why)
        f = lane.findings[0]
        self.assertTrue(f.egress_allowed)      # egress is not the failing gate here
        self.assertFalse(f.accepted)           # no zero-touch acceptance path
        self.assertEqual(f.payout_path, "human_fallback")
        self.assertIsNone(f.settlement)        # nothing settles without an admissible oracle

    def test_lane_e_self_interested_estimator_refused_before_oracle(self):
        lane = lane_e_self_interested()
        f = lane.findings[0]
        self.assertFalse(f.egress_allowed)
        self.assertFalse(f.accepted)
        self.assertEqual(f.oracle_score, 0.0)
        # the oracle never ran: no oracle_score entry in the ledger
        self.assertFalse(any(e.action == "oracle_score" for e in lane.ledger))
        # and an inadmissible estimate meters nothing — neither leakage nor demand
        st = lane._accountant.state(lane.key())
        self.assertEqual(st.cumulative_bits, 0.0)
        self.assertEqual(st.demanded_bits, 0.0)
        self.assertFalse(st.incident)


# ---- egress accountant: incident/ceiling coupling (handoff skepticism #2) ----


def _estimator() -> EstimatorAttestation:
    return EstimatorAttestation("indep", "adversarial_review", "static_schema_bound", True)


def _estimate(bits_text_bytes: int = 8, k_paths: int = 4) -> CapacityEstimate:
    return CapacityEstimate(
        enum_value_mbits=enum_value_mbits(3),
        ordering_mbits=ordering_mbits(k_paths),
        field_presence_mbits=bits_to_mbits(2.0),
        text_mbits=repro_text_mbits(bits_text_bytes),
        side_channel_mbits=bits_to_mbits(1.0),
        channel="vex_verdict",
    )


class TestEgressAccountant(unittest.TestCase):
    def _fresh(self, entropy: float, ceiling: float):
        acc = EgressAccountant()
        key = CompositionKey.of("subject", "family", "audience")
        acc.register(key, entropy, ceiling)
        return acc, key

    def test_demand_accrues_on_refusals_and_latches_incident(self):
        # ceiling small, entropy small: refusals keep accruing demand until UNSAFE
        acc, key = self._fresh(entropy=512.0, ceiling=120.0)
        per = _estimate().total_mbits  # 73.17 bits, charged as 73170 millibits
        for tick in range(1, 7):
            allowed, st, reason = acc.charge(key, _estimate(), _estimator(), tick)
        self.assertTrue(st.blocked)
        self.assertTrue(st.incident)
        self.assertEqual(st.demanded_mbits, 6 * per)
        self.assertLess(st.cumulative_mbits, bits_to_mbits(120.0))
        # incident latched exactly once, on the attempt that crossed UNSAFE
        incident_msgs = [d for d in st.debits if not d.accepted]
        self.assertEqual(len(incident_msgs), 5)

    def test_incident_does_not_fire_when_demand_stays_safe(self):
        # big subject: the same refused campaign is over-ceiling but nowhere
        # near reconstruction — a budget trip, not an incident
        acc, key = self._fresh(entropy=4096.0, ceiling=120.0)
        for tick in range(1, 7):
            _, st, _ = acc.charge(key, _estimate(), _estimator(), tick)
        self.assertTrue(st.blocked)
        self.assertFalse(st.incident)

    def test_incident_fires_even_on_accepted_path(self):
        # a ceiling misconfigured above the UNSAFE line must still flag
        acc, key = self._fresh(entropy=100.0, ceiling=1000.0)
        allowed, st, reason = acc.charge(key, _estimate(), _estimator(), 1)
        self.assertTrue(allowed)
        _, st, reason = acc.charge(key, _estimate(), _estimator(), 2)
        self.assertTrue(st.incident)
        self.assertIn("INCIDENT", reason)

    def test_exact_ceiling_blocks_further_emissions(self):
        # The ceiling is the exact integer charge expressed back in bits at
        # the register boundary; no epsilon is needed for equality.
        acc, key = self._fresh(entropy=4096.0, ceiling=estimate_total_bits(_estimate()))
        allowed, st, _ = acc.charge(key, _estimate(), _estimator(), 1)
        self.assertTrue(allowed)
        self.assertTrue(st.blocked)
        allowed, st, reason = acc.charge(key, _estimate(), _estimator(), 2)
        self.assertFalse(allowed)
        self.assertIn("blocked", reason)

    def test_inadmissible_estimators_refused(self):
        cases = [
            EstimatorAttestation("x", "self_interested", "declared", True),
            EstimatorAttestation("x", "unheard_of_class", "declared", True),
            EstimatorAttestation("x", "operator", "declared", False),  # not worst-case
        ]
        for est in cases:
            acc, key = self._fresh(entropy=512.0, ceiling=800.0)
            allowed, st, _ = acc.charge(key, _estimate(), est, 1)
            self.assertFalse(allowed)
            self.assertEqual(st.demanded_mbits, 0)

    def test_capacity_math(self):
        self.assertAlmostEqual(enum_value_bits(3), 1.584962500721156)
        self.assertAlmostEqual(ordering_bits(4), 4.584962500721156)
        self.assertEqual(ordering_bits(1), 0.0)
        self.assertEqual(repro_text_bits(8), 64.0)
        self.assertEqual(enum_value_mbits(3), 1585)
        self.assertEqual(ordering_mbits(4), 4585)
        self.assertEqual(repro_text_mbits(8), 64000)
        self.assertEqual(_estimate().total_mbits, 73170)


# ---- close_regression_window accounting (handoff skepticism #1) ----


def _multi_lane(n: int) -> BountyLane:
    est = _role_separated_estimator()
    lane = BountyLane(
        lane_id="W-window",
        artifact=SealedArtifact("subj", "<sealed>", structural_entropy_bits=100_000.0),
        audience="researchers",
        query_family="reachability",
        oracle=_clean_oracle("researchers"),
        schedule=_schedule(),
        authorization=_authorization(_schedule().schedule_id),  # per=25k, window=50k
        ceiling_bits=100_000.0,
        worker_beneficial_entity="researchers",
    )
    lane.run([
        Submission(f"finding {i}", claimed_reachable=True, true_reachable=True,
                   repro_replays=True, estimate=_vex_estimate(3, 40, est), estimator=est)
        for i in range(1, n + 1)
    ])
    return lane


class TestRegressionWindowAccounting(unittest.TestCase):
    def test_window_ceiling_gates_third_release(self):
        # each accepted finding is worth 20k; window ceiling is 50k:
        # f1, f2 release zero-touch (40k spent); f3 exceeds -> human fallback
        lane = _multi_lane(3)
        for fid in ("W-window-f1", "W-window-f2", "W-window-f3"):
            lane.close_regression_window(fid, regressed=False, tick=10)
        f1, f2, f3 = lane.findings
        self.assertEqual(f1.payout_path, "zero_touch")
        self.assertEqual(f2.payout_path, "zero_touch")
        self.assertEqual(f3.payout_path, "human_fallback")
        self.assertEqual(f3.settlement.status, "released")   # released, by a human
        self.assertIsNone(f3.settlement.authorization_id)    # not under the standing auth
        # window_spent counts only zero-touch releases
        self.assertEqual(lane.window_spent, 40_000)
        # and the refreshed receipt names all three payees
        self.assertEqual(len(lane.account.who_was_paid), 3)

    def test_unknown_finding_id_is_a_noop(self):
        lane = _multi_lane(1)
        before = len(lane.ledger)
        lane.close_regression_window("no-such-finding", regressed=False, tick=10)
        self.assertEqual(len(lane.ledger), before)

    def test_authorization_covers_edges(self):
        auth = _authorization("sched-vex-v1")
        ok, _ = auth.covers("oracle-vex-v1", "sched-vex-v1", auth.match_predicate_hash, 20_000, 0, 500)
        self.assertTrue(ok)
        # outside time window
        ok, why = auth.covers("oracle-vex-v1", "sched-vex-v1", auth.match_predicate_hash, 20_000, 0, 2000)
        self.assertFalse(ok)
        # a rubric change is a new oracle
        ok, why = auth.covers("oracle-vex-v2", "sched-vex-v1", auth.match_predicate_hash, 20_000, 0, 500)
        self.assertFalse(ok)
        self.assertIn("new oracle", why)
        # per-payout ceiling
        ok, _ = auth.covers("oracle-vex-v1", "sched-vex-v1", auth.match_predicate_hash, 26_000, 0, 500)
        self.assertFalse(ok)

    def test_low_score_never_settles(self):
        est = _role_separated_estimator()
        lane2 = BountyLane(
            lane_id="W-low",
            artifact=SealedArtifact("subj", "<sealed>", structural_entropy_bits=100_000.0),
            audience="researchers",
            query_family="reachability",
            oracle=_clean_oracle("researchers"),
            schedule=_schedule(),
            authorization=_authorization(_schedule().schedule_id),
            ceiling_bits=100_000.0,
            worker_beneficial_entity="researchers",
        )
        lane2.run([
            Submission("inflated claim", claimed_reachable=True, true_reachable=False,
                       repro_replays=True, estimate=_vex_estimate(3, 40, est), estimator=est),
        ])
        f = lane2.findings[0]
        self.assertEqual(f.oracle_score, 0.05)
        self.assertFalse(f.accepted)
        self.assertIsNone(f.settlement)
        self.assertIn("below any payable schedule point", f.accept_reason)


# ---- court file: hash chain + tamper detection ----


class TestCourtFile(unittest.TestCase):
    def test_roundtrip_and_tamper_detection(self):
        lane = lane_a_honest()
        out = persist_courtfile(lane)
        ok, msg = validate_courtfile(out)
        self.assertTrue(ok, msg)

        with tempfile.TemporaryDirectory() as td:
            tampered = Path(td) / "lane"
            shutil.copytree(out, tampered)
            rows = [json.loads(l) for l in (tampered / "ledger.jsonl").read_text().splitlines()]
            rows[2]["detail"] = "history, rewritten"
            (tampered / "ledger.jsonl").write_text(
                "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n"
            )
            ok, msg = validate_courtfile(tampered)
            self.assertFalse(ok)
            self.assertIn("bad ledger hash", msg)

    def test_receipt_must_name_non_claims(self):
        lane = lane_a_honest()
        out = persist_courtfile(lane)
        receipt = json.loads((out / "receipt.json").read_text())
        self.assertTrue(receipt["what_it_cannot_promise"])
        # The old asserted-accounting caveat is discharged; estimator bounds
        # remain the named caveat outside the integer kernel.
        self.assertFalse(any("ASSERTED" in c for c in receipt["what_it_cannot_promise"]))
        self.assertTrue(any("integer-millibit" in c for c in receipt["what_it_cannot_promise"]))


if __name__ == "__main__":
    unittest.main()
