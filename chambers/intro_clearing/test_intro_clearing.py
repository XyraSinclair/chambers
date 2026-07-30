"""Narrow tests for the purpose-blind introduction clearing slice.

    python3 -m unittest chambers.intro_clearing.test_intro_clearing -v

Each test pins one law from intro_clearing.INTRO_CLEARING_LAWS to observable
behavior: what crossed, what was withheld, who was paid, who was slashed.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from . import run_clearing
from .intro_clearing import (
    ADVISORY_PROSE_CEILING_MILLIBITS,
    BUCKET_MILLIBITS,
    DECLARED_SOURCE_ENTROPY_MBITS,
    DENIAL_PAYLOAD,
    HOUSE_FEE_SIDE,
    LawViolation,
    ORDINAL_MILLIBITS,
    PRESENCE_MILLIBITS,
    RATIONALE_CANDIDATE_COUNT,
    RATIONALE_CHAR_CAP,
    RoleSeparationError,
    TAG_MILLIBITS,
    TAGS_SCHEMA_CEILING_MILLIBITS,
    WORKER_ENDOWMENT,
    WORKER_FEE_SIDE,
    WORKER_STAKE,
    Chamber,
    ClearingHouse,
    ExposureBook,
    MatchCard,
    coalition_audit,
    counting_worker,
    honest_worker,
    identity_millibits,
    overreach_worker,
    quoting_worker,
    rationale_candidates,
    sha256_hex,
    static_scan,
)

BASE_SCOPE = ("offers", "needs", "excludes")
FEE = 6_000
WORKER_FLOAT = WORKER_ENDOWMENT - WORKER_STAKE  # liquid balance after stake


def pair_chambers(policy_a="release_all", policy_b="release_all",
                  attention_a=3, attention_b=3, ordinal_b=0):
    """A strong two-sided match (score 4): rust founders x infra funder."""
    a = Chamber(
        chamber_id="ch_a", owner_entity="entity:a",
        contact_handle="alpha@pair.example",
        offers=frozenset({"systems_rust", "distributed_systems"}),
        needs=frozenset({"grant_funding", "gtm"}),
        excludes=frozenset(),
        context_notes=("alpha keeps a quiet notebook of pilot partners and "
                       "unpublished road maps for the runtime"),
        reserve_micros=800, attention_budget=attention_a,
        reviewer_policy=policy_a)
    b = Chamber(
        chamber_id="ch_b", owner_entity="entity:b",
        contact_handle="bravo@pair.example",
        offers=frozenset({"grant_funding", "gtm"}),
        needs=frozenset({"systems_rust", "distributed_systems"}),
        excludes=frozenset(),
        context_notes=("bravo trust funds infrastructure teams and keeps its "
                       "diligence memos entirely private"),
        reserve_micros=1_200, attention_budget=attention_b,
        reviewer_policy=policy_b, rationale_ordinal=ordinal_b)
    return a, b


def make_house(chambers, workers=(("w_h", "entity:hive", honest_worker),),
               exposure_budget=None, reviewer_memory_budget=None,
               read_budget=3, expires=99, grants=True):
    kwargs = {}
    if exposure_budget is not None:
        kwargs["exposure_budget"] = exposure_budget
    if reviewer_memory_budget is not None:
        kwargs["reviewer_memory_budget"] = reviewer_memory_budget
    house = ClearingHouse(**kwargs)
    for chamber in chambers:
        house.enroll(chamber)
    for worker_id, entity, fn in workers:
        house.register_worker(worker_id, entity, fn)
    if grants:
        for chamber in chambers:
            for worker_id, _, _ in workers:
                house.issue_grant(chamber.chamber_id, worker_id, BASE_SCOPE,
                                  read_budget=read_budget, expires_tick=expires)
    return house


def file_and_run(house, worker_id, fee=FEE):
    for cid in sorted(house.chambers):
        house.file_intent(cid, fee)
    return house.run_window(lambda a, b: worker_id)


class ClearingTests(unittest.TestCase):

    def _assert_conserved(self, house):
        self.assertTrue(house.ledger.conserved(),
                        "settlement ledger lost or minted micros")

    # -- happy path ---------------------------------------------------------

    def test_cleared_pair_settles_and_crosses(self):
        house = make_house(pair_chambers())
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause), ("cleared", "mutual_release"))

        for cid, other in (("ch_a", "ch_b"), ("ch_b", "ch_a")):
            payloads = house.mailboxes[cid]
            self.assertEqual(len(payloads), 1)
            card = json.loads(payloads[0])
            self.assertEqual(card["kind"], "introduction")
            self.assertEqual(card["counterpartHandle"],
                             house.chambers[other].contact_handle)
            self.assertIn(card["fitBucket"], ("med", "high"))
            # Ordinal gate: what crossed is the house candidate the source
            # (default ordinal) selected, never the worker's advisory prose.
            self.assertEqual(card["rationale"], rationale_candidates(
                tuple(card["offersMatched"]), tuple(card["needsMatched"]),
                card["fitBucket"])[0])
            self.assertNotEqual(card["rationale"],
                                att.cards_proposed[cid].rationale)

        balances = house.ledger.accounts
        self.assertEqual(balances["worker:w_h"],
                         WORKER_FLOAT + 2 * WORKER_FEE_SIDE)
        self.assertEqual(balances["house"], 2 * HOUSE_FEE_SIDE)
        for name, amount in balances.items():
            if name.startswith("escrow:"):
                self.assertEqual(amount, 0, f"{name} not refunded")
        kinds = [e["kind"] for e in house.crossings.entries]
        self.assertEqual(kinds.count("introduction"), 2)
        self.assertEqual(kinds.count("denial"), 0)
        for cid in ("ch_a", "ch_b"):
            rows = result["ownerFiles"][cid]["attemptsVisibleToOwner"]
            self.assertEqual([r["outcome"] for r in rows], ["cleared"])
        # Rationale: every window receipt now carries the audit-clean kernel
        # court file without changing the public exposure millibit totals.
        kernel = result["receipt"]["kernelLedger"]
        expected_mbits = (BUCKET_MILLIBITS + PRESENCE_MILLIBITS
                          + identity_millibits(2) + 4 * TAG_MILLIBITS
                          + ORDINAL_MILLIBITS)
        self.assertEqual(kernel["auditFindings"], [])
        self.assertEqual(
            kernel["courtFile"]["ch_b->entity:a"]["cumulative_mbits"],
            expected_mbits)
        self.assertEqual(
            kernel["courtFile"]["ch_b->entity:a"]["ceiling_mbits"],
            DECLARED_SOURCE_ENTROPY_MBITS)
        self.assertIn("mem:ch_a->reviewer:ch_a:prime",
                      kernel["courtFile"])
        self._assert_conserved(house)

    # -- denial constancy and silent non-outcomes ---------------------------

    def test_denials_byte_constant_across_causes(self):
        # Three different non-clearing causes; one indistinguishable payload.
        no_match = make_house([
            Chamber("ch_a", "entity:a", "a@x.example",
                    frozenset({"biostatistics"}), frozenset({"climate_modeling"}),
                    frozenset(), "quiet alpha notes", 500, 3),
            Chamber("ch_b", "entity:b", "b@x.example",
                    frozenset({"gtm"}), frozenset({"zk_proofs"}),
                    frozenset(), "quiet bravo notes", 500, 3)])
        vetoed = make_house([
            Chamber("ch_a", "entity:a", "a@x.example",
                    frozenset({"formal_verification"}), frozenset({"zk_proofs"}),
                    frozenset({"defense_adjacent"}), "quiet alpha notes", 500, 3),
            Chamber("ch_b", "entity:b", "b@x.example",
                    frozenset({"zk_proofs", "defense_adjacent"}),
                    frozenset({"formal_verification"}),
                    frozenset(), "quiet bravo notes", 500, 3)])
        scanned = make_house(pair_chambers(),
                             workers=(("w_c", "entity:count", counting_worker),))

        causes, payloads = [], []
        for house, wid in ((no_match, "w_h"), (vetoed, "w_h"), (scanned, "w_c")):
            result = file_and_run(house, wid)
            causes.append(result["attempts"][0].cause)
            for delivered in result["deliveries"].values():
                payloads.extend(delivered)
        self.assertEqual(causes, ["no_coincidence", "vetoed", "scan_violation"])
        self.assertEqual(len(payloads), 6)
        self.assertEqual({sha256_hex(p) for p in payloads},
                         {sha256_hex(DENIAL_PAYLOAD)})

    def test_near_miss_produces_no_artifact(self):
        house = make_house([
            Chamber("ch_a", "entity:a", "a@x.example",
                    frozenset({"biostatistics"}), frozenset({"climate_modeling"}),
                    frozenset(), "quiet alpha notes", 500, 3),
            Chamber("ch_b", "entity:b", "b@x.example",
                    frozenset({"climate_modeling"}), frozenset({"biostatistics"}),
                    frozenset(), "quiet bravo notes", 500, 3)])
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause), ("no_card", "near_miss"))
        owner_bytes = json.dumps(result["ownerFiles"])
        self.assertNotIn("near_miss", owner_bytes)
        for cid in ("ch_a", "ch_b"):
            self.assertEqual(
                result["ownerFiles"][cid]["attemptsVisibleToOwner"], [])
            self.assertEqual(result["deliveries"][cid], [DENIAL_PAYLOAD])
        self.assertEqual(house.attention.spent, {"ch_a": 0, "ch_b": 0})
        self.assertEqual(house.ledger.accounts["worker:w_h"], WORKER_FLOAT)
        self._assert_conserved(house)

    # -- review gates: redaction subset, decline, mutuality ------------------

    def test_release_is_subset_of_reviewed(self):
        house = make_house(pair_chambers(policy_b="mask:gtm"))
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual(att.outcome, "cleared")
        self.assertEqual(att.decisions["ch_b"], "redact")

        proposed = att.cards_proposed["ch_a"]
        approved = att.cards_approved["ch_a"]
        self.assertLess(set(approved.offers_matched), set(proposed.offers_matched))

        delivered = json.loads(house.mailboxes["ch_a"][0])
        self.assertEqual(delivered["offersMatched"], ["grant_funding"])
        self.assertNotIn("gtm", json.dumps(delivered))
        # The rationale is re-rendered from the APPROVED fields, so the
        # redacted tag never appears and no mask marker betrays that a
        # redaction happened at all.
        self.assertEqual(delivered["rationale"], rationale_candidates(
            ("grant_funding",), ("distributed_systems", "systems_rust"),
            "high")[0])

    def test_ordinal_gate_bounds_prose_channel(self):
        # The candidate set is fixed-size, digit-free, capped, and total.
        for fields in ((("grant_funding", "gtm"),
                        ("systems_rust", "distributed_systems")),
                       ((), ())):
            candidates = rationale_candidates(fields[0], fields[1], "med")
            self.assertEqual(len(candidates), RATIONALE_CANDIDATE_COUNT)
            for text in candidates:
                self.assertFalse(any(ch.isdigit() for ch in text))
                self.assertLessEqual(len(text), RATIONALE_CHAR_CAP)
        # An ordinal outside the set is a law violation at enrollment.
        with self.assertRaises(LawViolation):
            Chamber("ch_x", "entity:x", "x@x.example",
                    frozenset({"gtm"}), frozenset({"zk_proofs"}), frozenset(),
                    "quiet notes", 500, 3, "release_all",
                    rationale_ordinal=RATIONALE_CANDIDATE_COUNT)

        # A source that picks the minimal projection crosses no tag names in
        # prose, while the structured fields still cross in full and the
        # selection itself is charged.
        house = make_house(pair_chambers(ordinal_b=3))
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual(att.outcome, "cleared")
        self.assertEqual(att.ordinals, {"ch_a": 0, "ch_b": 3})
        delivered = json.loads(house.mailboxes["ch_a"][0])  # source: ch_b
        self.assertEqual(delivered["rationale"], rationale_candidates(
            tuple(delivered["offersMatched"]), tuple(delivered["needsMatched"]),
            "high")[3])
        self.assertIn("matches your filed intent", delivered["rationale"])
        self.assertNotIn("grant_funding", delivered["rationale"])
        self.assertEqual(sorted(delivered["offersMatched"]),
                         ["grant_funding", "gtm"])
        charged = house.exposure.charged[("ch_b", "entity:a")]
        self.assertEqual(charged,
                         BUCKET_MILLIBITS + PRESENCE_MILLIBITS
                         + identity_millibits(2) + 4 * TAG_MILLIBITS
                         + ORDINAL_MILLIBITS)
        # Each owner's file records its own selection and nothing about the
        # counterparty's.
        rows = result["ownerFiles"]["ch_b"]["attemptsVisibleToOwner"]
        self.assertEqual(rows[0]["yourRationaleOrdinal"], 3)
        self.assertNotIn("yourCounterpartOrdinal", json.dumps(rows))

    def test_decline_blocks_both_directions_but_attention_was_sold(self):
        house = make_house(pair_chambers(policy_b="decline_all"))
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause), ("denied", "review_declined"))
        for cid in ("ch_a", "ch_b"):
            self.assertEqual(result["deliveries"][cid], [DENIAL_PAYLOAD])
        # One side released, the other declined; each owner sees only its own.
        files = result["ownerFiles"]
        self.assertEqual(
            files["ch_a"]["attemptsVisibleToOwner"][0]["yourReviewerDecision"],
            "release")
        self.assertEqual(
            files["ch_b"]["attemptsVisibleToOwner"][0]["yourReviewerDecision"],
            "decline")
        # Fees and attention settled although nothing crossed.
        self.assertEqual(house.ledger.accounts["worker:w_h"],
                         WORKER_FLOAT + 2 * WORKER_FEE_SIDE)
        self.assertEqual(house.attention.spent, {"ch_a": 1, "ch_b": 1})
        self._assert_conserved(house)

    # -- worker misconduct: grants, scans, slashing --------------------------

    def test_overreach_is_slashed_and_fails_closed(self):
        house = make_house(pair_chambers(),
                           workers=(("w_o", "entity:over", overreach_worker),))
        result = file_and_run(house, "w_o")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "grant_violation"))
        self.assertEqual(att.access_logs["ch_b"],
                         [{"section": "contextNotes", "granted": False}])
        self.assertEqual(house.ledger.accounts["stake:w_o"], 0)
        self.assertEqual(house.ledger.accounts["slash_pool"], WORKER_STAKE)
        self.assertTrue(house.workers["w_o"]["slashed"])
        self.assertEqual(house.ledger.accounts["worker:w_o"], WORKER_FLOAT)
        for cid in ("ch_a", "ch_b"):
            self.assertEqual(result["deliveries"][cid], [DENIAL_PAYLOAD])
        self._assert_conserved(house)

    def test_quoting_worker_blocked_by_verbatim_scan(self):
        house = make_house(pair_chambers(),
                           workers=(("w_q", "entity:quote", quoting_worker),),
                           grants=False)
        house.issue_grant("ch_a", "w_q", BASE_SCOPE, 3, 99)
        house.issue_grant("ch_b", "w_q", BASE_SCOPE + ("contextNotes",), 4, 99)
        result = file_and_run(house, "w_q")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "scan_violation"))
        scan_steps = [s for s in att.trace if s["gate"] == "static_scan"]
        self.assertIn("verbatim_span", scan_steps[0]["cause"])
        self.assertTrue(house.workers["w_q"]["slashed"])
        # Scan fires before fee settlement: misconduct earns nothing.
        self.assertEqual(house.ledger.accounts["worker:w_q"], WORKER_FLOAT)

    def test_counting_worker_blocked_by_digit_scan(self):
        house = make_house(pair_chambers(),
                           workers=(("w_c", "entity:count", counting_worker),))
        result = file_and_run(house, "w_c")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "scan_violation"))
        scan_steps = [s for s in att.trace if s["gate"] == "static_scan"]
        self.assertIn("digits_in_rationale", scan_steps[0]["cause"])
        self.assertTrue(house.workers["w_c"]["slashed"])

    def test_static_scan_units(self):
        def card(rationale, tags=("grant_funding",)):
            return MatchCard(source_chamber="ch_b", reader_chamber="ch_a",
                             fit_bucket="med", offers_matched=tuple(tags),
                             needs_matched=(), rationale=rationale)
        notes = "the bravo trust keeps its diligence memos entirely private"
        self.assertEqual(static_scan(card("A clean mediated sentence."), notes), [])
        self.assertTrue(any("digits" in v for v in
                            static_scan(card("Ranked 1 of 12."), notes)))
        self.assertTrue(any("verbatim_span" in v for v in
                            static_scan(card("they keeps its diligence memos "
                                             "safe"), notes)))
        self.assertTrue(any("covert" in v for v in
                            static_scan(card("clean\u200btext"), notes)))
        self.assertTrue(any("outside_vocabulary" in v for v in
                            static_scan(card("Clean.", tags=("astrology",)),
                                        notes)))

    # -- regression: the two bugs fixed in this tranche ----------------------

    def test_expired_grant_fails_closed_without_slash(self):
        # Regression: GrantedView construction failure used to hit an unbound
        # local in the exception handler AND slash a worker that never ran.
        house = make_house(pair_chambers(), grants=False)
        house.issue_grant("ch_a", "w_h", BASE_SCOPE, 3, expires_tick=0)
        house.issue_grant("ch_b", "w_h", BASE_SCOPE, 3, expires_tick=0)
        result = file_and_run(house, "w_h")  # window runs at tick 1
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "grant_unusable"))
        self.assertEqual(house.ledger.accounts["stake:w_h"], WORKER_STAKE)
        self.assertFalse(house.workers["w_h"]["slashed"])
        for cid in ("ch_a", "ch_b"):
            self.assertEqual(result["deliveries"][cid], [DENIAL_PAYLOAD])
        self._assert_conserved(house)

    def test_intent_refile_across_windows(self):
        # Regression: intent ids used to collide across windows, so a second
        # file_intent for the same chamber exploded on the escrow account.
        house = make_house(pair_chambers())
        first_ids = {cid: house.file_intent(cid, FEE).intent_id
                     for cid in sorted(house.chambers)}
        house.run_window(lambda a, b: "w_h")
        second_ids = {cid: house.file_intent(cid, FEE).intent_id
                      for cid in sorted(house.chambers)}
        house.run_window(lambda a, b: "w_h")
        for cid in first_ids:
            self.assertNotEqual(first_ids[cid], second_ids[cid])
        kinds = [e["kind"] for e in house.crossings.entries]
        self.assertEqual(kinds.count("introduction"), 4)
        self._assert_conserved(house)

    # -- fail-closed resource gates ------------------------------------------

    def test_exposure_budget_refuses_second_window(self):
        house = make_house(pair_chambers(), exposure_budget=20_000)
        first = file_and_run(house, "w_h")
        self.assertEqual(first["attempts"][0].outcome, "cleared")
        charged_before = dict(house.exposure.charged)

        second = file_and_run(house, "w_h")
        att = second["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "exposure_budget"))
        intro_count = sum(1 for e in house.crossings.entries
                          if e["kind"] == "introduction")
        self.assertEqual(intro_count, 2, "second window must not cross")
        for key, value in charged_before.items():
            if key[0].startswith("ch_"):
                self.assertEqual(house.exposure.charged[key], value,
                                 "refused crossing must not charge exposure")
        # Fees and attention settled twice: paid work, refused disclosure.
        self.assertEqual(house.ledger.accounts["worker:w_h"],
                         WORKER_FLOAT + 4 * WORKER_FEE_SIDE)
        self.assertEqual(house.attention.spent, {"ch_a": 2, "ch_b": 2})
        self._assert_conserved(house)

    def test_attention_exhaustion_fails_closed(self):
        house = make_house(pair_chambers(attention_a=0, attention_b=0))
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "attention_exhausted"))
        self.assertEqual(
            sum(1 for e in house.crossings.entries if e["kind"] == "introduction"),
            0)
        self.assertFalse(any(e["memo"].startswith("attention purchase")
                             for e in house.ledger.entries))
        # Worker fee still settled at scan-pass, before the attention gate.
        self.assertEqual(house.ledger.accounts["worker:w_h"],
                         WORKER_FLOAT + 2 * WORKER_FEE_SIDE)
        self.assertTrue(any(ev["granted"] is False
                            for ev in house.attention.events))
        self._assert_conserved(house)

    # -- reviewer memory: the human head, ledgered ----------------------------

    def _per_review(self, chambers: int) -> int:
        return (BUCKET_MILLIBITS + PRESENCE_MILLIBITS
                + identity_millibits(chambers)
                + TAGS_SCHEMA_CEILING_MILLIBITS
                + ADVISORY_PROSE_CEILING_MILLIBITS + ORDINAL_MILLIBITS)

    def test_reviewer_memory_rotation_then_fail_closed(self):
        # Budget fits exactly one review per reviewer: prime takes window
        # one, relief takes window two, window three finds the bench
        # exhausted and fails closed BEFORE anything is shown to anyone.
        per_review = self._per_review(2)
        house = make_house(pair_chambers(),
                           reviewer_memory_budget=per_review + 1_000)
        first = file_and_run(house, "w_h")
        second = file_and_run(house, "w_h")
        third = file_and_run(house, "w_h")

        self.assertEqual(first["attempts"][0].outcome, "cleared")
        self.assertEqual(first["attempts"][0].reviewers,
                         {"ch_a": "reviewer:ch_a:prime",
                          "ch_b": "reviewer:ch_b:prime"})
        self.assertEqual(second["attempts"][0].outcome, "cleared")
        self.assertEqual(second["attempts"][0].reviewers,
                         {"ch_a": "reviewer:ch_a:relief",
                          "ch_b": "reviewer:ch_b:relief"})
        att = third["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "reviewer_memory_exhausted"))
        self.assertEqual(att.reviewers, {})
        for cid in ("ch_a", "ch_b"):
            self.assertEqual(third["deliveries"][cid], [DENIAL_PAYLOAD])
        # Attention was still sold and the worker still paid in window three:
        # the head gate sits after fees and attention, like every refusal.
        self.assertEqual(house.attention.spent, {"ch_a": 3, "ch_b": 3})
        self.assertEqual(house.ledger.accounts["worker:w_h"],
                         WORKER_FLOAT + 6 * WORKER_FEE_SIDE)
        charged = house.reviewer_memory.charged
        self.assertEqual(charged[("ch_a", "reviewer:ch_a:prime")], per_review)
        self.assertEqual(charged[("ch_b", "reviewer:ch_b:relief")], per_review)
        self._assert_conserved(house)

    def test_reviewer_memory_charges_are_irrevocable_on_decline(self):
        house = make_house(pair_chambers(policy_b="decline_all"))
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual(att.outcome, "denied")
        per_review = self._per_review(2)
        # The declining reviewer saw the artifacts before declining; the
        # charge stands although nothing crossed in either direction.
        self.assertEqual(
            house.reviewer_memory.charged[("ch_b", "reviewer:ch_b:prime")],
            per_review)
        self.assertEqual(
            house.reviewer_memory.charged[("ch_a", "reviewer:ch_a:prime")],
            per_review)
        self.assertEqual(
            sum(1 for e in house.crossings.entries
                if e["kind"] == "introduction"), 0)

    def test_reviewer_memory_itemizes_artifacts_and_schedule(self):
        house = make_house(pair_chambers())
        result = file_and_run(house, "w_h")
        self.assertEqual(result["attempts"][0].outcome, "cleared")
        entries = house.reviewer_memory.entries
        self.assertEqual(len(entries), 2)
        for entry in entries:
            kinds = [a["kind"] for a in entry["artifactsSeen"]]
            self.assertEqual(kinds, ["proposed_card_structured",
                                     "advisory_worker_rationale",
                                     "candidate_set"])
            for artifact in entry["artifactsSeen"]:
                self.assertEqual(len(artifact["sha256"]), 64)
            self.assertEqual(entry["millibitsCeiling"], self._per_review(2))
        receipt_block = result["receipt"]["reviewerMemory"]
        self.assertEqual(receipt_block["perReviewCeilingMillibits"],
                         self._per_review(2))
        self.assertEqual(sum(receipt_block["schedule"].values()),
                         self._per_review(2))
        self.assertTrue(all(row["memoryNotRevocable"]
                            for row in receipt_block["accounts"]))
        own_bench = result["ownerFiles"]["ch_a"]["reviewerMemoryOwnBench"]
        self.assertEqual([row["reviewerEntity"] for row in own_bench],
                         ["reviewer:ch_a:prime"])

    # -- coalition audit: the sybil undercount, measured ----------------------

    def test_coalition_audit_unit(self):
        book = ExposureBook(default_budget=20_000)
        book.charge("src", "e_one", 15_000, "intro", 1)
        book.charge("src", "e_two", 15_000, "intro", 2)
        book.charge("lone", "e_solo", 25_000, "intro", 3)   # over on its own
        book.charge("mix", "e_loud", 25_000, "intro", 4)    # over on its own
        book.charge("mix", "e_soft", 1_000, "intro", 5)
        audit = coalition_audit(book, {"e_one": "coal", "e_two": "coal",
                                       "e_loud": "coal_two",
                                       "e_soft": "coal_two"})
        rows = {(r["sourceChamber"], r["hypothesizedEntity"]): r
                for r in audit["mergedAccounts"]}
        finding_keys = {(r["sourceChamber"], r["hypothesizedEntity"])
                        for r in audit["undercountFindings"]}

        # The invisible undercount: both constituents under, merged over.
        self.assertEqual(finding_keys, {("src", "coal")})
        self.assertEqual(rows[("src", "coal")]["millibitsCharged"], 30_000)
        self.assertEqual(
            rows[("src", "coal")]["effectiveBudgetUnderFragmentation"], 40_000)
        self.assertTrue(rows[("src", "coal")]["constituentsAllUnderBudget"])
        # A declared account already over budget is visible to the declared
        # view — alone or inside a coalition, it is not an undercount finding.
        self.assertTrue(rows[("lone", "e_solo")]["overBudgetIfOneEntity"])
        self.assertFalse(rows[("mix", "coal_two")]["constituentsAllUnderBudget"])
        # Unmapped entities pass through unchanged.
        self.assertIn(("lone", "e_solo"), rows)
        self.assertTrue(audit["auditNonClaims"])

    def test_sybil_fronts_cross_while_merged_would_refuse(self):
        src = Chamber("ch_src", "entity:src", "grants@src.example",
                      frozenset({"grant_funding", "gtm"}),
                      frozenset({"systems_rust", "distributed_systems"}),
                      frozenset(), "quiet notes about a rolling grants program",
                      500, 4)
        east = Chamber("ch_twin_east", "entity:east", "east@front.example",
                       frozenset({"systems_rust", "distributed_systems"}),
                       frozenset({"grant_funding", "gtm"}),
                       frozenset(), "small team notes about runtime tooling",
                       500, 3)
        west = Chamber("ch_twin_west", "entity:west", "west@front.example",
                       frozenset({"systems_rust", "distributed_systems"}),
                       frozenset({"grant_funding", "gtm"}),
                       frozenset(), "small crew notes about runtime tooling",
                       500, 3)
        house = make_house([src, east, west], exposure_budget=20_000)

        house.file_intent("ch_src", FEE)
        house.file_intent("ch_twin_east", FEE)
        first = house.run_window(lambda a, b: "w_h")
        house.file_intent("ch_src", FEE)
        house.file_intent("ch_twin_west", FEE)
        second = house.run_window(lambda a, b: "w_h")

        # The gate, blind to ownership, cleared both crossings; every
        # DECLARED account is under budget.
        self.assertEqual(first["attempts"][0].outcome, "cleared")
        self.assertEqual(second["attempts"][0].outcome, "cleared")
        self.assertTrue(all(not r["overBudget"]
                            for r in house.exposure.snapshot()))

        audit = coalition_audit(house.exposure,
                                {"entity:east": "entity:one_owner",
                                 "entity:west": "entity:one_owner"})
        per_card = (BUCKET_MILLIBITS + PRESENCE_MILLIBITS
                    + identity_millibits(3) + 4 * TAG_MILLIBITS
                    + ORDINAL_MILLIBITS)
        findings = audit["undercountFindings"]
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding["sourceChamber"], "ch_src")
        self.assertEqual(finding["hypothesizedEntity"], "entity:one_owner")
        self.assertEqual(finding["declaredEntities"],
                         ["entity:east", "entity:west"])
        self.assertEqual(finding["millibitsCharged"], 2 * per_card)
        self.assertGreater(finding["millibitsCharged"], 20_000)
        self.assertTrue(finding["constituentsAllUnderBudget"])
        # The honest-single-entity counterfactual: with the first charge on
        # the books, the second identical card would have tripped the very
        # same accounting gate that refused nothing here.
        self.assertTrue(house.exposure.would_exceed("ch_src", "entity:east",
                                                    per_card))
        self._assert_conserved(house)

    # -- structural refusals --------------------------------------------------

    def test_role_separation_raises(self):
        house = make_house(pair_chambers(),
                           workers=(("w_x", "entity:a", honest_worker),))
        for cid in sorted(house.chambers):
            house.file_intent(cid, FEE)
        with self.assertRaises(RoleSeparationError):
            house.run_window(lambda a, b: "w_x")

    def test_no_grant_no_run(self):
        house = make_house(pair_chambers(), grants=False)
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual((att.outcome, att.cause),
                         ("failed_closed", "grant_missing"))
        self.assertEqual(att.access_logs, {})
        self.assertEqual(house.ledger.accounts["stake:w_h"], WORKER_STAKE)

    # -- the full demo: persistence, validation, determinism ------------------

    def test_demo_courtfiles_validate_and_self_checks_pass(self):
        house = run_clearing.build_house()
        results = run_clearing.run_demo(house)
        tmp = Path(tempfile.mkdtemp(prefix="intro_clearing_test_"))
        try:
            window_dirs = run_clearing.persist_windows(house, results, tmp)
            self.assertEqual(len(window_dirs), 6)
            for wdir in window_dirs:
                ok, msg = run_clearing.validate_window_dir(wdir)
                self.assertTrue(ok, f"{wdir.name}: {msg}")
            self.assertTrue((tmp / "run_summary.json").exists())
            ok, msg = run_clearing.validate_coalition_audit(tmp)
            self.assertTrue(ok, msg)
            # Rationale: the run-level JSONL artifact is what third parties
            # merge and re-audit, so the demo validator must cover it.
            ok, msg = run_clearing.validate_kernel_ledger(tmp)
            self.assertTrue(ok, msg)
            checks = run_clearing.self_checks(house, results, window_dirs)
            failures = [(name, detail) for name, ok, detail in checks if not ok]
            self.assertEqual(failures, [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_demo_is_deterministic(self):
        house_a = run_clearing.build_house()
        first = run_clearing.run_demo(house_a)
        house_b = run_clearing.build_house()
        second = run_clearing.run_demo(house_b)
        self.assertEqual([r["courtFile"] for r in first],
                         [r["courtFile"] for r in second])
        self.assertEqual(run_clearing.build_coalition_audit(house_a),
                         run_clearing.build_coalition_audit(house_b))


if __name__ == "__main__":
    unittest.main()
