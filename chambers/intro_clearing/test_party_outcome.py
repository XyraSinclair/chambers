"""Standing tests for the party lane — intro_clearing's consumer fee legs
on charge-settlement/2 (SETTLEMENT-SPEC Part II).

    python3 -m unittest chambers.intro_clearing.test_party_outcome -v

The party-matchmaker story (docs/stories/
party-matchmaker.md) as ledger arithmetic, on the REAL kernel settlement:

  * 50 cents unconditional-to-raise: escrow + release bound to the exact
    delivery ring's charge event id.
  * $5 on outcome: a /2 OUTCOME escrow (default refund_to_payer), released
    only on a bonded, contest-hardened platform_log attestation of the
    qualifying call, with the release referencing the first-contact card's
    charge event id (first-contact attribution as the ledger fact).

Paths pinned: honest (talk -> $5 releases), silent (no talk -> $5 refunds
the payer at expiry, mechanically), lying (a false below-lane attestation
is slashed by the platform log's strict override; a forged release
leaning on it is convicted S9), and the named limit (a false TOP-lane
platform log can be contested — payment blocked — but never slashed:
equal-lane contest is not conviction). Conservation is asserted across
every path, including the recorded-crime one.

The outcome metric prices PRESENCE on a qualifying call, not engagement
and not causation: "talked BECAUSE of the card" has no settlement lane
and cannot be expressed — pinned below.
"""
from __future__ import annotations

import unittest

from chambers.kernel import (
    OutcomeAttestationEvent,
    OutcomeCondition,
    ReleaseEvent,
    SettlementRefused,
    attest_outcome,
    audit_settlement_codes,
    conservation_identity,
    resolve_bond,
    resolve_default,
    settlement_fold_full,
)

from . import run_clearing
from .intro_clearing import (
    LawViolation,
    OUTCOME_CONTEST_TICKS,
    OUTCOME_FEE_UCR,
    OUTCOME_LANE,
    OUTCOME_METRIC,
    OUTCOME_MIN_BOND_UCR,
    PARTY_OWNER_ENDOWMENT_UCR,
    RAISE_PRICE_UCR,
)
from .test_intro_clearing import file_and_run, make_house, pair_chambers


def party_house():
    house = make_house(pair_chambers())
    house.open_party_lane()
    return house


class PartyLaneTests(unittest.TestCase):

    def _assert_kernel_clean(self, house):
        self.assertEqual(house.kernel_ledger.audit(), [])
        self.assertEqual(audit_settlement_codes(house.kernel_ledger), [])
        self._assert_conserved(house)

    def _assert_conserved(self, house):
        lhs, rhs = conservation_identity(house.kernel_ledger)
        self.assertEqual(lhs, rhs, "kernel conservation identity broken")
        self.assertTrue(house.ledger.conserved(),
                        "CreditMicros book lost or minted micros")

    # -- the honest path: they talked ---------------------------------------

    def test_honest_path_talk_releases_five_dollars(self):
        house = party_house()
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual(att.outcome, "cleared")

        # Leg 1 — two rings, each 50 cents, each release bound to the exact
        # ring charge event (value moved iff the metered ring moved).
        rings = house.party["rings"]
        self.assertEqual(len(rings), 2)
        events = getattr(house.kernel_ledger, "_events")
        for ring in rings:
            release = events[ring["releaseId"]]
            self.assertEqual(release["charge_ids"], [ring["ringChargeId"]])
            escrow = events[ring["escrowId"]]
            self.assertEqual(escrow["charge_keys"], [ring["ringKey"]])
            self.assertEqual(ring["priceUcr"], RAISE_PRICE_UCR)

        # Leg 2 — the $5 escrows are locked, bound to the intro cards'
        # metered exposure accounts, defaulting to refund_to_payer.
        legs = house.party["contingent"][att.attempt_id]
        self.assertEqual(sorted(legs), ["ch_a", "ch_b"])
        for reader, source in (("ch_a", "ch_b"), ("ch_b", "ch_a")):
            esc = legs[reader]["escrow"]
            self.assertEqual(esc.payer, f"owner:{reader}")
            self.assertEqual(esc.payee, "worker:w_h")
            self.assertEqual(esc.amount_ucr, OUTCOME_FEE_UCR)
            self.assertEqual(esc.default_on_expiry, "refund_to_payer")
            self.assertEqual(esc.outcome.metric, OUTCOME_METRIC)
            self.assertEqual(esc.outcome.lane, OUTCOME_LANE)
            reader_entity = house.chambers[reader].owner_entity
            self.assertEqual(list(esc.charge_keys),
                             [("exp", source, reader_entity)])

        # The call happened: the platform posts bonded platform_log facts,
        # the contest window passes, the $5 releases against the
        # first-contact card's charge event id, bonds return.
        house.party_attest_call(
            att.attempt_id,
            evidence="platform:call:duration_seventeen_minutes")
        releases = house.party_settle_outcome(att.attempt_id)
        self.assertEqual(len(releases), 2)
        for rel, reader in zip(releases, sorted(legs)):
            self.assertEqual(list(rel.charge_ids),
                             [legs[reader]["introChargeId"]])

        accounts, escrows, bonds = settlement_fold_full(house.kernel_ledger)
        self.assertEqual(accounts["worker:w_h"].available_ucr,
                         2 * OUTCOME_FEE_UCR)
        # Each owner paid one raise, received one raise, and paid the $5.
        for cid in ("ch_a", "ch_b"):
            self.assertEqual(accounts[f"owner:{cid}"].available_ucr,
                             PARTY_OWNER_ENDOWMENT_UCR - OUTCOME_FEE_UCR)
        self.assertTrue(all(e.remaining_ucr == 0 for e in escrows.values()))
        self.assertTrue(all(b.remaining_ucr == 0 for b in bonds.values()))
        self._assert_kernel_clean(house)

        view = house.party_court_view()
        self.assertTrue(view["conservation"]["holds"])
        self.assertEqual(view["settlementAuditCodes"], [])
        self.assertTrue(all(leg["status"] == "released"
                            for leg in view["contingent"]
                            [att.attempt_id].values()))
        self.assertTrue(any(gap["key"] == "creditMicrosBooksAreSimLocal"
                            for gap in view["gaps"]))

    # -- the silent path: no talk, the payer keeps the money ---------------

    def test_no_talk_refunds_payer_after_expiry(self):
        house = party_house()
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        self.assertEqual(att.outcome, "cleared")

        # Not before expiry: the anti-holdup clause waits.
        with self.assertRaises(SettlementRefused):
            legs = house.party["contingent"][att.attempt_id]
            resolve_default(house.kernel_ledger, legs["ch_a"]["escrow"],
                            submitter="owner:ch_a",
                            amount_ucr=OUTCOME_FEE_UCR, tick=house.tick)

        house.party_expire_refund(att.attempt_id)
        accounts, escrows, _bonds = settlement_fold_full(house.kernel_ledger)
        # The raise legs net to zero for a symmetric pair; the $5 is back.
        for cid in ("ch_a", "ch_b"):
            self.assertEqual(accounts[f"owner:{cid}"].available_ucr,
                             PARTY_OWNER_ENDOWMENT_UCR)
        self.assertEqual(accounts["worker:w_h"].available_ucr, 0,
                         "no talk: the matchmaker earns nothing")
        self.assertTrue(all(e.remaining_ucr == 0 for e in escrows.values()))
        self._assert_kernel_clean(house)
        view = house.party_court_view()
        self.assertTrue(all(leg["status"] == "refunded"
                            for leg in view["contingent"]
                            [att.attempt_id].values()))

    # -- the lying path: a false attestation, slashed by the platform log ---

    def test_false_attestation_slashed_by_platform_log_override(self):
        house = party_house()
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        legs = house.party["contingent"][att.attempt_id]
        esc = legs["ch_a"]["escrow"]
        bank = house.party["bank"]
        bank.deposit("arbiter:colluding", 1_000_000, house.tick)

        # The honest front refuses a below-lane claim live (it could never
        # count toward a platform_log quorum)...
        with self.assertRaises(SettlementRefused):
            attest_outcome(house.kernel_ledger, esc, "arbiter:colluding",
                           "occurred", "attested", "role_separated",
                           OUTCOME_MIN_BOND_UCR, tick=house.tick + 1)
        # ...so the colluder forges the fact straight into the open court.
        forged = OutcomeAttestationEvent(
            escrow_id=esc.id, claim="occurred", lane="attested",
            independence="role_separated", evidence="we swear they talked",
            bond_ucr=OUTCOME_MIN_BOND_UCR, attestor="arbiter:colluding",
            seq=1, tick=house.tick + 1)
        house.kernel_ledger.add(forged)

        # The honest issuer still refuses to release against it live...
        with self.assertRaises(SettlementRefused):
            bank.release(esc, OUTCOME_FEE_UCR,
                         [legs["ch_a"]["introChargeId"]],
                         tick=house.tick + 10, attestation_ids=[forged.id])
        # ...and a forged release leaning on it is convicted after merge.
        forged_release = ReleaseEvent(
            escrow_id=esc.id, amount_ucr=1_000,
            charge_ids=(legs["ch_a"]["introChargeId"],),
            issuer="house_bank", seq=90, tick=house.tick + 10,
            attestation_ids=(forged.id,))
        house.kernel_ledger.add(forged_release)
        codes = audit_settlement_codes(house.kernel_ledger)
        self.assertIn(f"S9 {forged_release.id}", codes)
        self._assert_conserved(house)  # the crime moved value; identity holds

        # The platform log outranks the lie: not_occurred, strictly above.
        override = attest_outcome(
            house.kernel_ledger, esc, house.party["platform"],
            "not_occurred", "platform_log", "role_separated",
            OUTCOME_MIN_BOND_UCR, tick=house.tick + 11,
            evidence="platform:call:none_between_these_parties")
        # The false bond is now slashable — to the party the lie would have
        # harmed (the payer), derived from declared data, not chosen.
        resolve_bond(house.kernel_ledger, forged, "owner:ch_a", "slash",
                     OUTCOME_MIN_BOND_UCR, tick=house.tick + 12)
        accounts, _escrows, bonds = settlement_fold_full(house.kernel_ledger)
        self.assertEqual(accounts["owner:ch_a"].slashed_in_ucr,
                         OUTCOME_MIN_BOND_UCR)
        self.assertEqual(bonds[forged.id].remaining_ucr, 0)
        # ...and never returnable.
        with self.assertRaises(SettlementRefused):
            resolve_bond(house.kernel_ledger, forged, "arbiter:colluding",
                         "return_to_attestor", 1, tick=house.tick + 40)
        # The platform's own bond returns after its window (nothing
        # outranks a platform log).
        resolve_bond(house.kernel_ledger, override, house.party["platform"],
                     "return_to_attestor", OUTCOME_MIN_BOND_UCR,
                     tick=override.tick + OUTCOME_CONTEST_TICKS + 1)

        # No talk was proven, so at expiry the remainders refund the payers.
        expiry = esc.expires_tick
        resolve_default(house.kernel_ledger, esc, submitter="owner:ch_a",
                        amount_ucr=OUTCOME_FEE_UCR - 1_000, tick=expiry + 1)
        resolve_default(house.kernel_ledger, legs["ch_b"]["escrow"],
                        submitter="owner:ch_b", amount_ucr=OUTCOME_FEE_UCR,
                        tick=expiry + 1)
        _accounts, escrows, _bonds = settlement_fold_full(house.kernel_ledger)
        self.assertTrue(all(e.remaining_ucr == 0 for e in escrows.values()))
        # The forged release stands convicted forever; conservation holds
        # anyway — the artifact records the crime instead of hiding it.
        codes = audit_settlement_codes(house.kernel_ledger)
        self.assertEqual(codes, [f"S9 {forged_release.id}"])
        self._assert_conserved(house)

    # -- the named limit: a false TOP-lane platform log ----------------------

    def test_false_platform_log_blocked_by_contest_never_slashed(self):
        house = party_house()
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        legs = house.party["contingent"][att.attempt_id]
        esc_a = legs["ch_a"]["escrow"]
        bank = house.party["bank"]

        # The platform lies at the top lane on both legs.
        lies = house.party_attest_call(att.attempt_id, claim="occurred",
                                       evidence="fabricated log line")
        # A second platform's log contests ch_a's leg at the SAME lane.
        bank.deposit("platform:second_operator", 1_000_000, house.tick)
        contest = attest_outcome(
            house.kernel_ledger, esc_a, "platform:second_operator",
            "not_occurred", "platform_log", "role_separated",
            OUTCOME_MIN_BOND_UCR, tick=house.tick + 1,
            evidence="platform:call:absent_from_this_log")
        # Payment on the contested leg is blocked live (ch_a settles first
        # in sorted order, so nothing releases).
        with self.assertRaises(SettlementRefused):
            house.party_settle_outcome(att.attempt_id)
        # Equal-lane contest is not conviction: neither bond is slashable.
        for a, submitter in ((lies[0], "owner:ch_a"),
                             (contest, "worker:w_h")):
            with self.assertRaises(SettlementRefused):
                resolve_bond(house.kernel_ledger, a, submitter, "slash",
                             OUTCOME_MIN_BOND_UCR, tick=house.tick + 20)
        # All bonds return after their windows; the escrows refund at
        # expiry. Blocked payment, no minted guilt, everything conserved.
        for a in list(lies) + [contest]:
            resolve_bond(house.kernel_ledger, a, a.attestor,
                         "return_to_attestor", a.bond_ucr,
                         tick=a.tick + OUTCOME_CONTEST_TICKS + 1)
        house.party_expire_refund(att.attempt_id)
        self._assert_kernel_clean(house)

    # -- counterfactuals have no lane -----------------------------------------

    def test_counterfactual_metric_unexpressible(self):
        # The declared condition names the observable proxy for what it is:
        # presence on a qualifying first-contact call, not engagement, not
        # "talked because of the card".
        self.assertEqual(OUTCOME_METRIC, "first_contact_qualifying_call_15min")
        # There is no counterfactual lane in the settlement vocabulary: an
        # escrow condition cannot even be CONSTRUCTED over one.
        with self.assertRaises(ValueError):
            OutcomeCondition(metric="talked_because_of_the_card",
                             lane="counterfactual", quorum=1,
                             min_independence="role_separated",
                             min_bond_ucr=1, contest_ticks=1)
        # ...and no attestation can be posted on one, live.
        house = party_house()
        result = file_and_run(house, "w_h")
        att = result["attempts"][0]
        esc = house.party["contingent"][att.attempt_id]["ch_a"]["escrow"]
        with self.assertRaises(SettlementRefused):
            attest_outcome(house.kernel_ledger, esc, house.party["platform"],
                           "occurred", "counterfactual", "role_separated",
                           OUTCOME_MIN_BOND_UCR, tick=house.tick + 1)

    # -- lane hygiene ---------------------------------------------------------

    def test_lane_must_open_before_windows_and_only_once(self):
        house = party_house()
        with self.assertRaises(LawViolation):
            house.open_party_lane()
        # Without the lane, resolution surfaces refuse coherently.
        plain = make_house(pair_chambers())
        with self.assertRaises(LawViolation):
            plain.party_attest_call("att-NOPE")
        with self.assertRaises(LawViolation):
            plain.party_court_view()

    def test_lane_off_means_zero_settlement_events(self):
        plain = make_house(pair_chambers())
        file_and_run(plain, "w_h")
        kinds = {p.get("kind") for p in plain.kernel_ledger.events()}
        self.assertFalse(kinds & {"deposit", "escrow", "release", "refund",
                                  "outcome_attestation", "bond_resolution",
                                  "default_resolution"})

    # -- the full scenario, end to end ----------------------------------------

    def test_party_scenario_demo_runs_validates_and_is_deterministic(self):
        import shutil
        import tempfile
        from pathlib import Path

        house = run_clearing.build_party_house()
        acts = run_clearing.run_party_scenario(house)
        checks = run_clearing.party_self_checks(house, acts)
        failures = [(name, detail) for name, ok, detail in checks if not ok]
        self.assertEqual(failures, [])

        tmp = Path(tempfile.mkdtemp(prefix="party_lane_test_"))
        try:
            run_clearing.persist_party(house, acts, tmp)
            ok, msg = run_clearing.validate_party_dir(tmp)
            self.assertTrue(ok, msg)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        fresh = run_clearing.build_party_house()
        fresh_acts = run_clearing.run_party_scenario(fresh)
        self.assertEqual(
            run_clearing.render_party_court_file(fresh, fresh_acts),
            run_clearing.render_party_court_file(house, acts))


if __name__ == "__main__":
    unittest.main()
