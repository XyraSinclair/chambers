"""charge-views/1 lane (VIEWS-SPEC.md).

The load-bearing test is parity (§V.5): the view under the legacy-default
policy reproduces the fold's embedded leakage_class/incident BIT FOR BIT
over every FROZEN corpus file — bound to the frozen expected.json bytes,
not to the current reference implementation, so drift in either direction
is a red test. Then: admissibility (W1), input well-formedness (W2),
all-or-nothing refusal, domain voidness, and escalate-never-retract for
arbitrary admissible policies.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.views import (
    LEGACY_DEFAULT_POLICY,
    policy_admissible,
    policy_sha256,
    view,
    view_bytes,
)

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE_GLOB = os.path.join(HERE, "ledger_traces", "*.expected.json")


def _policy(**overrides):
    p = json.loads(json.dumps(LEGACY_DEFAULT_POLICY))
    p.update(overrides)
    return p


class TestParityLaw(unittest.TestCase):
    """§V.5 — the migration proof, against frozen bytes."""

    def test_corpus_is_present(self):
        # A parity suite over zero files is a silent lie.
        self.assertGreaterEqual(len(glob.glob(TRACE_GLOB)), 10)

    def test_default_view_reproduces_frozen_fold_labels(self):
        checked_accounts = 0
        for path in sorted(glob.glob(TRACE_GLOB)):
            with open(path) as fh:
                expected = json.load(fh)
            fold = expected["fold"]
            report = view(fold, LEGACY_DEFAULT_POLICY)
            self.assertNotIn("refused", report, path)
            self.assertEqual(len(report["accounts"]), len(fold["accounts"]), path)
            frozen = {
                json.dumps(a["key"]): a for a in fold["accounts"]
            }
            for row in report["accounts"]:
                fa = frozen[json.dumps(row["key"])]
                self.assertEqual(row["class"], fa["leakage_class"], path)
                self.assertEqual(row["incident"], fa["incident"], path)
                checked_accounts += 1
        self.assertGreater(checked_accounts, 0)

    def test_report_account_order_matches_fold_order(self):
        for path in sorted(glob.glob(TRACE_GLOB)):
            with open(path) as fh:
                fold = json.load(fh)["fold"]
            report = view(fold, LEGACY_DEFAULT_POLICY)
            self.assertEqual(
                [r["key"] for r in report["accounts"]],
                [a["key"] for a in fold["accounts"]],
                path,
            )


class TestAdmissibility(unittest.TestCase):
    """§V.2 — W1 and the all-or-nothing refusal."""

    GOOD_FOLD = {
        "accounts": [
            {
                "key": ["exp", "a", "b"],
                "cumulative_mbits": 10,
                "demanded_mbits": 10,
                "subject_entropy_mbits": 1000,
            }
        ]
    }

    def test_default_policy_is_admissible(self):
        self.assertTrue(policy_admissible(LEGACY_DEFAULT_POLICY))

    def _refuses_w1(self, policy):
        report = view(self.GOOD_FOLD, policy)
        self.assertIn("refused", report)
        self.assertEqual(len(report["refused"]), 1)
        self.assertTrue(report["refused"][0].startswith("W1 sha256:"))
        self.assertNotIn("accounts", report)  # all-or-nothing: no partials

    def test_non_monotone_boundaries_refuse(self):
        p = _policy()
        p["classes"][1]["max_permille"] = 50  # not strictly increasing
        self._refuses_w1(p)

    def test_duplicate_labels_refuse(self):
        p = _policy(terminal_label="unsafe")
        self._refuses_w1(p)

    def test_void_label_reserved(self):
        self._refuses_w1(_policy(terminal_label="void"))

    def test_boolean_permille_refuses(self):
        p = _policy()
        p["classes"][0]["max_permille"] = True
        self._refuses_w1(p)

    def test_unknown_field_refuses(self):
        self._refuses_w1(_policy(extra="x"))

    def test_missing_field_refuses(self):
        p = _policy()
        del p["incident_permille"]
        self._refuses_w1(p)

    def test_empty_domains_refuse(self):
        self._refuses_w1(_policy(domains=[]))
        self._refuses_w1(_policy(domains=[[]]))

    def test_wrong_spec_refuses(self):
        self._refuses_w1(_policy(spec="charge-views/2"))

    def test_non_dict_policy_refuses(self):
        self._refuses_w1(["not", "a", "policy"])


class TestInputWellFormedness(unittest.TestCase):
    """§V.3 — W2 and the all-or-nothing refusal."""

    def _refuses_w2(self, fold):
        report = view(fold, LEGACY_DEFAULT_POLICY)
        self.assertIn("refused", report)
        self.assertEqual(len(report["refused"]), 1)
        self.assertTrue(report["refused"][0].startswith("W2 sha256:"))

    def test_missing_accounts(self):
        self._refuses_w2({})

    def test_unparseable_key(self):
        self._refuses_w2(
            {"accounts": [{"key": "exp", "cumulative_mbits": 0,
                           "demanded_mbits": 0, "subject_entropy_mbits": 1}]}
        )

    def test_boolean_sum_refuses_whole_input(self):
        # ONE bad account refuses the WHOLE view — no partial reports.
        good = {"key": ["exp", "a", "b"], "cumulative_mbits": 5,
                "demanded_mbits": 5, "subject_entropy_mbits": 100}
        bad = dict(good, key=["exp", "a", "c"], cumulative_mbits=True)
        self._refuses_w2({"accounts": [good, bad]})

    def test_both_bad_names_both(self):
        report = view({}, _policy(spec="nope"))
        self.assertEqual(
            [c.split()[0] for c in report["refused"]], ["W1", "W2"]
        )

    def test_extra_fold_fields_ignored(self):
        fold = {"accounts": [{
            "key": ["exp", "a", "b"], "cumulative_mbits": 5,
            "demanded_mbits": 5, "subject_entropy_mbits": 100,
            "ceiling_mbits": 1, "leakage_class": "reconstructed",
            "incident": True, "conflicted": True, "granted_lease_mbits": 9,
        }]}
        report = view(fold, LEGACY_DEFAULT_POLICY)
        self.assertNotIn("refused", report)
        # The view reads the sums, not the embedded interpretation:
        self.assertEqual(report["accounts"][0]["class"], "negligible")
        self.assertEqual(report["accounts"][0]["incident"], False)


class TestDomains(unittest.TestCase):
    """§V.3/§V.4 — the attention-demo lie made unrepresentable."""

    FOLD = {
        "accounts": [
            {"key": ["attention", "recv", "sender"], "cumulative_mbits": 900,
             "demanded_mbits": 900, "subject_entropy_mbits": 1000},
            {"key": ["exp", "a", "b"], "cumulative_mbits": 900,
             "demanded_mbits": 900, "subject_entropy_mbits": 1000},
        ]
    }

    def test_out_of_domain_is_void(self):
        report = view(self.FOLD, _policy(name="exp-only", domains=[["exp"]]))
        by_kind = {r["key"][0]: r for r in report["accounts"]}
        self.assertEqual(by_kind["attention"]["class"], "void")
        self.assertIsNone(by_kind["attention"]["incident"])
        self.assertEqual(by_kind["exp"]["class"], "reconstructed")
        self.assertEqual(by_kind["exp"]["incident"], True)

    def test_legacy_null_domain_labels_everything(self):
        report = view(self.FOLD, LEGACY_DEFAULT_POLICY)
        self.assertTrue(all(r["class"] != "void" for r in report["accounts"]))


class TestArithmetic(unittest.TestCase):
    """§V.3 — §1.5 edges reproduced exactly."""

    def _row(self, cum, dem, s, policy=None):
        fold = {"accounts": [{"key": ["exp", "a", "b"], "cumulative_mbits": cum,
                              "demanded_mbits": dem, "subject_entropy_mbits": s}]}
        return view(fold, policy or LEGACY_DEFAULT_POLICY)["accounts"][0]

    def test_zero_entropy_first_class_and_incident(self):
        # s=0: c=0, 0 <= 0 -> first class; dem*1000 >= 0 -> incident True.
        row = self._row(0, 0, 0)
        self.assertEqual(row["class"], "negligible")
        self.assertEqual(row["incident"], True)

    def test_fraction_capped_at_one(self):
        # cum >> s still lands via c = min(cum, s): 1000*1000 <= 800*1000 is
        # False -> terminal, NOT an overflow past the vocabulary.
        row = self._row(10**9, 0, 1000)
        self.assertEqual(row["class"], "reconstructed")

    def test_inclusive_boundaries(self):
        s = 1000
        self.assertEqual(self._row(50, 0, s)["class"], "negligible")
        self.assertEqual(self._row(51, 0, s)["class"], "bounded")
        self.assertEqual(self._row(800, 0, s)["class"], "unsafe")
        self.assertEqual(self._row(801, 0, s)["class"], "reconstructed")

    def test_incident_threshold_inclusive(self):
        self.assertEqual(self._row(0, 800, 1000)["incident"], True)
        self.assertEqual(self._row(0, 799, 1000)["incident"], False)


class TestEscalateNeverRetract(unittest.TestCase):
    """§V.2 — monotonicity is structural for EVERY admissible policy."""

    POLICIES = [
        LEGACY_DEFAULT_POLICY,
        _policy(name="two-class",
                classes=[{"label": "lo", "max_permille": 100},
                         {"label": "hi", "max_permille": 900}],
                terminal_label="top", incident_permille=1),
        _policy(name="tight",
                classes=[{"label": "ok", "max_permille": 1}],
                terminal_label="not-ok", incident_permille=999),
    ]

    def _class_index(self, policy, label):
        order = [c["label"] for c in policy["classes"]] + [policy["terminal_label"]]
        return order.index(label)

    def test_class_nondecreasing_in_cumulative(self):
        for policy in self.POLICIES:
            prev = -1
            for cum in range(0, 1201, 40):
                fold = {"accounts": [{"key": ["exp", "a", "b"],
                                      "cumulative_mbits": cum,
                                      "demanded_mbits": 0,
                                      "subject_entropy_mbits": 1000}]}
                label = view(fold, policy)["accounts"][0]["class"]
                idx = self._class_index(policy, label)
                self.assertGreaterEqual(idx, prev, policy["name"])
                prev = idx

    def test_class_nonincreasing_in_entropy(self):
        # Register min-resolution can only LOWER entropy; class must only rise.
        for policy in self.POLICIES:
            prev = None
            for s in range(2000, 99, -100):
                fold = {"accounts": [{"key": ["exp", "a", "b"],
                                      "cumulative_mbits": 500,
                                      "demanded_mbits": 0,
                                      "subject_entropy_mbits": s}]}
                label = view(fold, policy)["accounts"][0]["class"]
                idx = self._class_index(policy, label)
                if prev is not None:
                    self.assertGreaterEqual(idx, prev, policy["name"])
                prev = idx


class TestSerialization(unittest.TestCase):
    def test_view_bytes_is_canonical_and_deterministic(self):
        fold = {"accounts": [{"key": ["exp", "a", "b"], "cumulative_mbits": 5,
                              "demanded_mbits": 5, "subject_entropy_mbits": 100}]}
        b1 = view_bytes(fold, LEGACY_DEFAULT_POLICY)
        b2 = view_bytes(fold, LEGACY_DEFAULT_POLICY)
        self.assertEqual(b1, b2)
        parsed = json.loads(b1)
        self.assertEqual(parsed["spec"], "charge-views/1")
        self.assertEqual(parsed["policy_sha256"],
                         policy_sha256(LEGACY_DEFAULT_POLICY))
        # Canonical form: no spaces, sorted keys.
        self.assertNotIn(" ", b1)


class TestGoldenViewsCorpus(unittest.TestCase):
    """views_traces/ must replay bit-for-bit: from each input file alone,
    the computed report equals the committed expected bytes (what a second
    implementation written from VIEWS-SPEC.md would be held to)."""

    VIEWS_GLOB = os.path.join(HERE, "views_traces", "*.input.json")

    def test_corpus_is_present(self):
        self.assertGreaterEqual(len(glob.glob(self.VIEWS_GLOB)), 6)

    def test_replay_bit_for_bit(self):
        from chambers.kernel.events import canonical_json

        for in_path in sorted(glob.glob(self.VIEWS_GLOB)):
            with open(in_path) as fh:
                pair = json.load(fh)
            exp_path = in_path.replace(".input.json", ".expected.json")
            with open(exp_path) as fh:
                frozen_bytes = fh.read()
            computed = canonical_json(view(pair["fold"], pair["policy"])) + "\n"
            self.assertEqual(computed, frozen_bytes, in_path)

    def test_emitter_is_deterministic(self):
        import tempfile

        from chambers.kernel import emit_views_traces as evt

        with tempfile.TemporaryDirectory() as tmp:
            n = evt.emit(tmp)
            self.assertEqual(n, 6)
            for name in os.listdir(tmp):
                with open(os.path.join(tmp, name)) as fh:
                    fresh = fh.read()
                with open(os.path.join(HERE, "views_traces", name)) as fh:
                    committed = fh.read()
                self.assertEqual(fresh, committed, name)

    def test_parity_scenario_is_anchored_to_frozen_ledger_corpus(self):
        # The parity input's fold must BE the frozen forged-overspend fold —
        # bytes that predate this spec — not a reconstruction.
        with open(os.path.join(HERE, "views_traces",
                               "parity-forged-overspend.input.json")) as fh:
            pair = json.load(fh)
        with open(os.path.join(HERE, "ledger_traces",
                               "forged-overspend.expected.json")) as fh:
            frozen = json.load(fh)["fold"]
        self.assertEqual(pair["fold"], frozen)


if __name__ == "__main__":
    unittest.main()
