"""The cut bound against a malicious judge (CALCULUS.md §6, ship-path step 1).

The claim under test: a judge with full silo access and adversarial intent can
exfiltrate at most the DERIVED capacity charged on the releases it emits —
plus nothing — because its only degree of freedom is which codebook symbol
crosses, and the accountant blocks releases before the ceiling regardless of
strategy. The canary is a planted secret bitstring; the malicious judge
encodes it greedily into verdict symbols; the decoder recovers what it can;
the recovered bits can never exceed the charged bits, and past the ceiling
nothing but 'blocked' crosses.

Also asserted: blockage is simulatable from the public charge transcript
alone (CALCULUS.md L5) — which is the precondition for charging 'blocked'
at zero.

stdlib-only unittest by design: this suite is a landing-gate check on the
landing gate (read-only worktree, no third-party packages) and part of the
counterparty-compilable posture — anyone with a Python can run the bound.
"""
from __future__ import annotations

import math
import unittest

from .codebook import RESULT_VERDICT, Codebook
from .leakage import LeakageAccountant, bits_to_mbits
from .types import ResultClaim, Technique


SECRET = "1011001110001011"  # the canary: 16 bits of crown-jewel payload


def make_technique(n_claims: int, entropy_bits: float = 40.0) -> Technique:
    return Technique(
        id="t_canary", owner="seller", name="canary technique",
        capability_area="long_context", carrier="pure_recipe",
        secret_payload=SECRET, entropy_bits=entropy_bits,
        claims=[ResultClaim(f"bench_{i}", true_score=1.0, claimed_score=0.9)
                for i in range(n_claims)],
    )


def malicious_judge_run(ceiling_fraction: float, n_claims: int):
    """The judge ignores the benchmarks entirely and encodes SECRET bits into
    the holds/not_met choice — the strongest exfiltration strategy available
    through a 2-of-3 usable alphabet. Returns (transcript, accountant, tech).
    The transcript is exactly what the buyer-side observer sees: a symbol
    sequence."""
    acct = LeakageAccountant()
    tech = make_technique(n_claims)
    acct.register(tech, "buyer", ceiling_fraction)
    transcript = []
    for i in range(n_claims):
        bit = SECRET[i % len(SECRET)]
        symbol, _ = acct.release(
            tech.id, "buyer", RESULT_VERDICT,
            "holds" if bit == "1" else "not_met",
            tick=i, note="malicious encode",
        )
        transcript.append(symbol)
    return transcript, acct, tech


def decode(transcript) -> str:
    """The colluding observer's decoder: holds=1, not_met=0, blocked=end."""
    out = []
    for s in transcript:
        if s == "blocked":
            break
        out.append("1" if s == "holds" else "0")
    return "".join(out)


class CutBoundTests(unittest.TestCase):
    def assertClose(self, a: float, b: float, abs_tol: float = 1e-9) -> None:
        self.assertTrue(
            math.isclose(a, b, abs_tol=abs_tol),
            f"{a!r} !~ {b!r} (abs_tol={abs_tol})",
        )

    def test_derived_charge_is_log2_alphabet(self):
        self.assertClose(RESULT_VERDICT.capacity_bits, math.log2(3))

    def test_closed_alphabet_rejects_novel_symbols(self):
        with self.assertRaisesRegex(ValueError, "side channel"):
            RESULT_VERDICT.require("holds_but_barely")
        with self.assertRaises(ValueError):
            Codebook("degenerate", ("only",))  # a 1-symbol alphabet carries no verdict
        acct = LeakageAccountant()
        tech = make_technique(1)
        acct.register(tech, "buyer", 0.5)
        with self.assertRaisesRegex(ValueError, "never chosen by a judge"):
            acct.release(tech.id, "buyer", RESULT_VERDICT, "blocked", tick=0)
        # a codebook without a refusal symbol fails at the door, not at the
        # first budget refusal mid-run
        with self.assertRaisesRegex(ValueError, "no 'blocked' symbol"):
            acct.release(tech.id, "buyer", Codebook("pair", ("yes", "no")), "yes", tick=0)

    def test_charges_round_up_never_down(self):
        from .leakage import bits_to_mbits_charge
        self.assertEqual(bits_to_mbits_charge(math.log2(11)), 3460)  # half-even would give 3459
        self.assertEqual(bits_to_mbits_charge(math.log2(3)), 1585)

    def test_malicious_judge_cannot_beat_charged_capacity(self):
        transcript, acct, tech = malicious_judge_run(ceiling_fraction=0.9, n_claims=16)
        recovered = decode(transcript)
        st = acct.state(tech.id, "buyer")
        # Every recovered bit rides a symbol that was charged log2(3) > 1 bit:
        # exfiltration never exceeds the meter. This is the cut bound observed.
        self.assertLessEqual(len(recovered) * 1.0, st.cumulative_bits + 1e-9)
        self.assertClose(st.cumulative_bits, len(recovered) * math.log2(3), abs_tol=0.01)

    def test_block_fires_before_ceiling_and_only_blocked_crosses_after(self):
        # ceiling = 10% of 40 bits = 4 bits -> floor(4 / log2(3)) = 2 releases fit.
        transcript, acct, tech = malicious_judge_run(ceiling_fraction=0.10, n_claims=16)
        st = acct.state(tech.id, "buyer")
        delivered = [s for s in transcript if s != "blocked"]
        self.assertEqual(len(delivered), 2)
        self.assertEqual(set(transcript[2:]), {"blocked"})
        self.assertTrue(st.blocked)
        # the accountant never let cumulative pass the ceiling — block-before, not block-after
        self.assertLessEqual(st.cumulative_mbits, st.ceiling_mbits)
        # and the recoverable canary is capped by the same arithmetic, judge strategy irrelevant
        self.assertEqual(len(decode(transcript)), 2)

    def test_blockage_is_simulatable_from_public_transcript(self):
        """L5: charging 'blocked' at 0 bits is sound only if blockage is a
        function of public data. Precision (adversarial-review fix): the inputs
        are alphabet capacity, ceiling, and count of prior accepted releases.
        The ceiling derives from entropy_bits, which IS secret-derived — it is
        public only because registration explicitly publishes it as a declared
        parameter (kernel RegisterEvent + leakage report; see register()). That
        one-time disclosure is the stated price of leak-free refusals; GIVEN it,
        a public simulator must match the accountant exactly."""
        transcript, acct, tech = malicious_judge_run(ceiling_fraction=0.10, n_claims=16)
        per_release_mbits = bits_to_mbits(RESULT_VERDICT.capacity_bits)
        ceiling_mbits = bits_to_mbits(tech.entropy_bits * 0.10)
        spent = 0
        predicted = []
        for _ in range(16):
            if spent + per_release_mbits <= ceiling_mbits:
                predicted.append("deliver")
                spent += per_release_mbits
            else:
                predicted.append("blocked")
        actual = ["blocked" if s == "blocked" else "deliver" for s in transcript]
        self.assertEqual(actual, predicted)

    def test_cut_bound_report_separates_derived_from_declared(self):
        transcript, acct, tech = malicious_judge_run(ceiling_fraction=0.9, n_claims=4)
        # add one declared-channel observation for contrast
        acct.observe(tech.id, "buyer", "black_box_probe", 2.0, tick=99, note="probe")
        cb = acct.cut_bound()
        self.assertClose(cb["derived_bits"], 4 * math.log2(3), abs_tol=0.01)
        self.assertClose(cb["declared_bits"], 2.0, abs_tol=0.01)
        self.assertEqual(cb["total_mbits"], cb["derived_mbits"] + cb["declared_mbits"])
        self.assertEqual(cb["edges"][0]["technique"], tech.id)

    def test_cut_bound_is_fed_by_the_kernel_ledger_not_presentation_lists(self):
        """Pool membership comes from the estimator on each ChargeEvent, so a
        charge whose presentation Debit was never appended still counts, and a
        second codebook lands in the derived pool with no registry edit."""
        acct = LeakageAccountant()
        tech = make_technique(2)
        acct.register(tech, "buyer", 0.9)
        second = Codebook("second_verdict", ("a", "b", "c", "d", "blocked"))
        acct.release(tech.id, "buyer", RESULT_VERDICT, "holds", tick=0)
        acct.release(tech.id, "buyer", second, "a", tick=1)
        # sabotage the presentation layer: wipe the Debit lists entirely
        for st in acct._states.values():
            st.debits.clear()
        cb = acct.cut_bound()
        self.assertClose(cb["derived_bits"], math.log2(3) + math.log2(5), abs_tol=0.01)
        self.assertEqual(cb["declared_mbits"], 0)

    def test_capability_binding_commitment_is_not_grid_searchable(self):
        """A courtfile reader knows benchmarks and the public claimed scores; the
        commitment must not fall to a grid search over plausible true scores
        (adversarial-review finding: it did, before salting)."""
        tech = make_technique(1)
        stored = tech.binding_capability_hash()
        from .types import sha
        for guess in [round(0.5 + i * 0.001, 4) for i in range(1000)]:
            unsalted_guess = sha(f"bench_0:{guess}")
            self.assertNotEqual(unsalted_guess, stored)
        # while the legitimate counterparty (who bought the payload) can verify
        self.assertEqual(tech.binding_capability_hash(), stored)


if __name__ == "__main__":
    unittest.main()
