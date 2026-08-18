"""Offline tests for the confined guest's model-boundary behavior."""

from __future__ import annotations

import json
import unittest

from . import guest


class ScriptedLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, prompt, max_tokens=1024):
        self.calls.append((prompt, max_tokens))
        if not self.replies:
            raise AssertionError("unexpected LLM call")
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply


def packet():
    return {
        "question": "Which three ideas are most worth reviving now?",
        "context": (
            "Building privacy-bounded Chambers with guardians, constrained sinks, "
            "audit trails, and useful matching over private context."
        ),
        "candidates": [
            {
                "id": "opaque-a",
                "title": "Private collaborator matching",
                "slice": "Match collaborators near private notes through a Chamber.",
            },
            {
                "id": "opaque-b",
                "title": "Consent receipt ledger",
                "slice": "A reusable audit asset recording permissions and releases.",
            },
            {
                "id": "opaque-c",
                "title": "Weekend demand probe",
                "slice": "A cheap prototype can validate buyer demand in two days.",
            },
            {
                "id": "opaque-d",
                "title": "Garden planner",
                "slice": "Seasonal planting reminders for a home vegetable garden.",
            },
            {
                "id": "opaque-e",
                "title": "Old compiler sketch",
                "slice": "A novel notation for small experimental languages.",
            },
        ],
    }


class ParsingTests(unittest.TestCase):
    def test_embedded_fenced_json_is_recovered(self):
        reply = "analysis first\n```json\n{\"ranking\":[{\"label\":\"C3\"},{\"label\":\"C1\"}]}\n```"
        parsed = guest._parse_entries(
            reply,
            {"C1", "C2", "C3"},
            {"opaque-a": "C1", "opaque-b": "C2", "opaque-c": "C3"},
        )
        self.assertEqual([item["label"] for item in parsed], ["C3", "C1"])

    def test_plain_text_recovery_deduplicates_and_preserves_order(self):
        parsed = guest._parse_entries(
            "1. C2 — strongest\n2. C1 — next\nC2 repeated",
            {"C1", "C2", "C3"},
            {},
        )
        self.assertEqual([item["label"] for item in parsed], ["C2", "C1"])

    def test_packet_id_outside_current_shortlist_is_rejected(self):
        parsed = guest._parse_entries(
            '{"ranking":[{"candidate_id":"opaque-c"},{"candidate_id":"opaque-a"}]}',
            {"C1", "C2"},
            {"opaque-a": "C1", "opaque-b": "C2", "opaque-c": "C3"},
        )
        self.assertEqual([item["label"] for item in parsed], ["C1"])

    def test_echoed_input_container_is_not_accepted_as_ranking(self):
        parsed = guest._parse_entries(
            '{"shortlist":[{"label":"C1","title":"echo"}]}',
            {"C1", "C2", "C3"},
            {},
            ("ranking", "picks"),
        )
        self.assertEqual(parsed, [])


class RunTests(unittest.TestCase):
    def assertConforming(self, verdict, source_packet):
        self.assertEqual(set(verdict), {"picks"})
        self.assertEqual(len(verdict["picks"]), 3)
        ids = {candidate["id"] for candidate in source_packet["candidates"]}
        picked = []
        for pick in verdict["picks"]:
            self.assertEqual(
                set(pick), {"candidate_id", "reason", "confidence"}
            )
            self.assertIn(pick["candidate_id"], ids)
            self.assertIn(pick["reason"], guest._REASON_CODES)
            self.assertIn(pick["confidence"], guest._CONFIDENCE)
            picked.append(pick["candidate_id"])
        self.assertEqual(len(set(picked)), 3)

    def test_screen_then_comparative_rank_and_map_reason_prose(self):
        model = ScriptedLLM(
            [
                json.dumps(
                    {
                        "screen": [
                            {"label": "C1", "score": 96, "reason_text": "fit"},
                            {"label": "C2", "score": 91, "reason_text": "fit"},
                            {"label": "C3", "score": 88, "reason_text": "test"},
                            {"label": "C5", "score": 45, "reason_text": "novel"},
                            {"label": "C4", "score": 10, "reason_text": "weak"},
                        ]
                    }
                ),
                "preface\n```json\n"
                + json.dumps(
                    {
                        "comparisons": [
                            {"winner": "C1", "loser": "C2", "why": "closer fit"}
                        ],
                        "ranking": [
                            {
                                "label": "C1",
                                "reason_text": "Specific synergy with bounded Chambers and private context.",
                                "confidence": "high",
                            },
                            {
                                "label": "C3",
                                "reason_text": "A cheap quick experiment validates demand in days.",
                                "confidence": "medium",
                            },
                            {
                                "label": "C2",
                                "reason_text": "It supplies the missing complementary audit asset.",
                                "confidence": "medium",
                            },
                        ],
                    }
                )
                + "\n```",
            ]
        )
        source = packet()
        verdict = guest.run(source, model)
        self.assertConforming(verdict, source)
        self.assertEqual(
            [pick["candidate_id"] for pick in verdict["picks"]],
            ["opaque-a", "opaque-c", "opaque-b"],
        )
        self.assertEqual(
            [pick["reason"] for pick in verdict["picks"]],
            ["synergy_with_chambers", "cheap_to_validate", "complementary_asset"],
        )
        self.assertEqual(len(model.calls), 2)

    def test_malformed_screen_is_retried_once(self):
        source = packet()
        model = ScriptedLLM(
            [
                "not usable",
                '{"screen":[{"label":"C2","score":99},{"label":"C1","score":90},'
                '{"label":"C3","score":80}]}',
                '{"ranking":[{"label":"C2","reason_text":"complementary missing piece",'
                '"confidence":"high"},{"label":"C1","reason_text":"bounded Chambers",'
                '"confidence":"medium"},{"label":"C3","reason_text":"cheap validation",'
                '"confidence":"low"}]}',
            ]
        )
        verdict = guest.run(source, model)
        self.assertConforming(verdict, source)
        self.assertEqual(verdict["picks"][0]["candidate_id"], "opaque-b")
        self.assertEqual(len(model.calls), 3)
        self.assertIn("prior screening answer was unusable", model.calls[1][0])

    def test_total_model_failure_degrades_to_deterministic_verdict(self):
        source = packet()
        # Both screen attempts and both ranking attempts fail or return garbage.
        model = ScriptedLLM(
            [RuntimeError("offline"), "still garbage", None, "also garbage"]
        )
        first = guest.run(source, model)
        self.assertConforming(first, source)
        self.assertTrue(all(pick["confidence"] == "low" for pick in first["picks"]))

        second_model = ScriptedLLM(
            [RuntimeError("offline"), "still garbage", None, "also garbage"]
        )
        self.assertEqual(first, guest.run(source, second_model))
        self.assertLessEqual(len(model.calls), guest._MAX_CALLS)
        self.assertLessEqual(
            sum(len(prompt) for prompt, _ in model.calls), guest._MAX_PROMPT_CHARS
        )

    def test_partial_first_ranking_survives_worse_retry(self):
        source = packet()
        model = ScriptedLLM(
            [
                '{"screen":[{"label":"C1","score":90},{"label":"C2","score":80},'
                '{"label":"C3","score":70}]}',
                '{"ranking":[{"label":"C2","reason_text":"missing complementary asset",'
                '"confidence":"high"}]}',
                "retry is malformed",
            ]
        )
        verdict = guest.run(source, model)
        self.assertConforming(verdict, source)
        self.assertEqual(verdict["picks"][0]["candidate_id"], "opaque-b")
        self.assertEqual(verdict["picks"][0]["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
