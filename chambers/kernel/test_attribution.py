"""charge-attribution/1 (V-codes) as a standing lane — ATTRIBUTION-SPEC.md;
F6 of the import register, the G20 gap.

The law: when a pot is split across the sources of a derived fact's
ancestry, the split is a declared rule computed from facts already in the
artifact — and a misdeclared split convicts from bytes. The load-bearing
story is the alpha story: a contributor whose ancestry carries 1/8000 of
an emission's capacity is paid exactly 1/8000 of a $100M pot, to the
microcredit, by a rule any stranger recomputes.

Families:
  1. THE CALCULUS — exact-integer Shapley (efficiency, symmetry, null
     player, the brute-force permutation bridge of SPEC V.6.5) and the
     largest-remainder allocation (conservation, quota, determinism, the
     floor-only leak that mirrors Lean's sharp negative).
  2. HONEST REPORTS — compile, ingest, clean V verdict, full verifier
     exit 0; depth is not dilution in shares; the 1/8000 story exact.
  3. CONVICTIONS — V1..V5 each injected the Byzantine way.
  4. SUBSTRATE — totality on junk, shuffle-merge invariance.
  5. FROZEN SURFACES — every frozen corpus has an empty V verdict.

Run: python3 chambers/kernel/test_attribution.py
"""
from __future__ import annotations

import glob
import io
import itertools
import os
import random
import sys
from math import factorial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify as verify_mod  # noqa: E402
from accountant import CapacityEstimate, EstimatorAttestation  # noqa: E402
from attribution import (  # noqa: E402
    NMAX,
    allocate,
    attribution_codes,
    compile_report,
    shapley_numerators,
)
from events import DerivationEvent, canonical_json, event_id  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402

TOR = EstimatorAttestation("indep", "adversarial_review", "m", True)
FACT = "sha256:" + "d" * 64
FA = "sha256:" + "a" * 64
FB = "sha256:" + "b" * 64
K_ALICE = ("exp", "alice", "readerR")
K_BOB = ("exp", "bob", "readerR")

#: $100M with 1 credit = $1 at microcredit resolution.
POT_100M = 100_000_000 * 1_000_000


def _est(total: int, channel: str) -> CapacityEstimate:
    return CapacityEstimate(total, 0, 0, 0, 0, channel)


def _forge(ledger: Ledger, payload: dict) -> str:
    eid = event_id(payload)
    ledger._add_payload(eid, payload)
    return eid


def _meter(ledger: Ledger, keys, ceiling: int = 50_000) -> KernelMeter:
    m = KernelMeter(node="n1", issuer="chamberA", ledger=ledger)
    for k in keys:
        m.register(k, subject_entropy_mbits=1_000_000, ceiling_mbits=ceiling)
    return m


def _register_id(ledger: Ledger, key) -> str:
    return next(
        eid for eid, p in ledger._events.items()
        if p.get("kind") == "register" and p.get("key") == list(key)
    )


def _alpha_economy(alice_cap: int = 1, bob_cap: int = 7999, hops: int = 1):
    """The alpha story: alice's idea and bob's build feed one derived
    fact, with declared carrying capacities alice_cap and bob_cap.
    `hops` > 1 pushes alice the extra derivation hops BEHIND the fact
    (wide intermediate capacity — the depth, not the pipe, varies).
    Returns (ledger, emission_tick)."""
    ledger = Ledger()
    meter = _meter(ledger, [K_ALICE, K_BOB])
    alice_fact = FA
    ledger.add(DerivationEvent(
        derived=alice_fact, consumed=(_register_id(ledger, K_ALICE),),
        hop_capacity_mbits=alice_cap, issuer="chamberA", seq=1, tick=1,
    ))
    for h in range(hops - 1):
        nxt = "sha256:" + ("%02d" % h) * 32
        ledger.add(DerivationEvent(
            derived=nxt, consumed=(alice_fact,),
            hop_capacity_mbits=50_000, issuer="chamberA", seq=2 + h, tick=1,
        ))
        alice_fact = nxt
    ledger.add(DerivationEvent(
        derived=FB, consumed=(_register_id(ledger, K_BOB),),
        hop_capacity_mbits=bob_cap, issuer="chamberA", seq=100, tick=1,
    ))
    ledger.add(DerivationEvent(
        derived=FACT, consumed=(alice_fact, FB),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=101, tick=1,
    ))
    decisions = meter.charge_coupled(
        [K_ALICE, K_BOB], _est(alice_cap + bob_cap, "derived:" + FACT),
        TOR, tick=2)
    assert all(d.accepted for d in decisions.values())
    return ledger, 2


def _brute_force_numerators(n: int, v_by_mask):
    """Permutation-walk Shapley numerators: for every ordering, each
    player's marginal over its predecessor set. The subset-weight
    formula must agree exactly — the SPEC V.6.5 bridge."""
    nums = [0] * n
    for perm in itertools.permutations(range(n)):
        mask = 0
        for i in perm:
            nums[i] += v_by_mask[mask | (1 << i)] - v_by_mask[mask]
            mask |= 1 << i
    return nums


# ---- 1. the calculus ----

def test_shapley_permutation_bridge_and_efficiency() -> None:
    """On random monotone integer games (n <= 5): the subset-weight
    numerators equal the brute-force permutation sums exactly, and sum
    to n! * v(full) — efficiency, the identity the allocator's
    denominator leans on."""
    rng = random.Random(1729)
    for _ in range(40):
        n = rng.randint(1, 5)
        v = [0] * (1 << n)
        for mask in range(1, 1 << n):
            low = max(v[mask & ~(1 << i)] for i in range(n) if (mask >> i) & 1)
            v[mask] = low + rng.randint(0, 7)  # monotone by construction
        nums = shapley_numerators(n, v)
        assert nums == _brute_force_numerators(n, v)
        assert sum(nums) == factorial(n) * v[(1 << n) - 1]
        assert all(x >= 0 for x in nums)


def test_symmetry_and_null_player() -> None:
    """Interchangeable players earn identical numerators; a player whose
    marginal is always zero earns exactly zero."""
    # v = |S| for players 0,1; player 2 contributes nothing
    v = [0] * 8
    for mask in range(8):
        v[mask] = ((mask >> 0) & 1) + ((mask >> 1) & 1)
    nums = shapley_numerators(3, v)
    assert nums[0] == nums[1]
    assert nums[2] == 0


def test_allocate_conserves_quota_and_determinism() -> None:
    """Largest remainder: sum equals the pot exactly on random inputs;
    every payout is floor or floor+1 (quota); remainder ties break to
    the lowest index."""
    rng = random.Random(8128)
    for _ in range(200):
        n = rng.randint(1, 9)
        nums = [rng.randint(0, 50) for _ in range(n)]
        if sum(nums) == 0:
            nums[rng.randrange(n)] = 1
        pot = rng.randint(0, 10**9)
        out = allocate(pot, nums)
        d = sum(nums)
        assert sum(out) == pot
        for x, num in zip(out, nums):
            assert pot * num // d <= x <= pot * num // d + 1
    # ties: three equal weights, pot 10 -> remainders equal, first gets +1
    assert allocate(10, [1, 1, 1]) == [4, 3, 3]


def test_floor_only_rule_leaks() -> None:
    """The sharp negative the Lean file also pins: floors alone lose a
    unit on [1,1,1] at pot 10000 — the remainder arm is load-bearing."""
    assert sum(10000 * x // 3 for x in [1, 1, 1]) == 9999
    assert sum(allocate(10000, [1, 1, 1])) == 10000


# ---- 2. honest reports ----

def test_the_alpha_story_one_eight_thousandth_of_100m() -> None:
    """The register's founding story, exact: alice's idea carries 1 of
    the emission's 8000 mbits; a $100M pot pays her $12,500.000000 —
    12_500_000_000 microcredits, not one more, not one less — and the
    report verifies clean end to end."""
    ledger, tick = _alpha_economy(alice_cap=1, bob_cap=7999)
    report = compile_report(
        ledger, FACT, "n1", tick, POT_100M, issuer="chamberA", seq=1, tick=3)
    shares = dict((s, (b, u)) for s, b, u in report.shares)
    assert shares["alice"] == (1, 12_500_000_000)      # $12,500 exactly
    assert shares["bob"] == (9999, 99_987_500_000_000)
    assert sum(u for _, u in shares.values()) == POT_100M
    ledger.add(report)
    assert attribution_codes(ledger) == []
    assert verify_mod.verify(ledger.to_jsonl(), out=io.StringIO()) == 0


def test_depth_is_not_dilution_in_shares() -> None:
    """A source three derivation hops behind the fact earns exactly the
    share it earns one hop behind — the value-layer echo of the P-law."""
    for hops in (1, 3):
        ledger, tick = _alpha_economy(alice_cap=1, bob_cap=7999, hops=hops)
        report = compile_report(
            ledger, FACT, "n1", tick, POT_100M,
            issuer="chamberA", seq=1, tick=3)
        assert dict((s, u) for s, _, u in report.shares)["alice"] \
            == 12_500_000_000, f"hops={hops}"


def test_honest_reporter_refuses_the_unsplittable() -> None:
    """compile_report raises where the audit would convict: a positive
    pot over a sourceless fact, and an unknown coupling."""
    ledger = Ledger()
    _meter(ledger, [K_ALICE])
    try:
        compile_report(ledger, FACT, "n1", 2, 100, "chamberA", 1, 3)
        assert False, "expected refusal"
    except ValueError:
        pass


# ---- 3. convictions ----

def _honest_report_payload(ledger, tick) -> dict:
    return compile_report(
        ledger, FACT, "n1", tick, POT_100M,
        issuer="chamberA", seq=1, tick=3).payload()


def _codes_with(ledger, payload) -> list:
    _forge(ledger, payload)
    return attribution_codes(ledger)


def test_v1_share_mismatch_convicts() -> None:
    """Shave a microcredit off alice onto bob: sums still conserve (no
    V2), but both rows convict V1 with the recomputed pair named."""
    ledger, tick = _alpha_economy()
    p = _honest_report_payload(ledger, tick)
    p["shares"][0]["payout_ucr"] -= 1  # alice's row (ascending sources)
    p["shares"][1]["payout_ucr"] += 1
    codes = _codes_with(ledger, p)
    assert any(c.startswith("V1 ") and '"alice"' in c for c in codes)
    assert any(c.startswith("V1 ") and '"bob"' in c for c in codes)
    assert not any(c.startswith("V2") for c in codes)


def test_v2_non_conservation_convicts() -> None:
    """A report whose payouts do not exhaust the pot convicts V2 — the
    arm that never goes dark, checked as pure report arithmetic."""
    ledger, tick = _alpha_economy()
    p = _honest_report_payload(ledger, tick)
    p["shares"][1]["payout_ucr"] -= 5  # mint 5 ucr of nothing
    codes = _codes_with(ledger, p)
    assert any(c.startswith("V2 ") for c in codes)


def test_v3_phantom_beneficiary_convicts() -> None:
    """Paying an identity outside the ancestry convicts V3 on the
    (fact, source) subject."""
    ledger, tick = _alpha_economy()
    p = _honest_report_payload(ledger, tick)
    p["shares"][0]["source"] = "mallory"
    codes = _codes_with(ledger, p)
    assert any(c.startswith("V3 ") and '"mallory"' in c for c in codes)
    # alice, no longer declared, is also a dropped contributor
    assert any(c.startswith("V4 ") and '"alice"' in c for c in codes)


def test_v4_dropped_contributor_convicts() -> None:
    """Folding alice's payout into bob's row drops her from the shares:
    V4 names her, V1 names bob's inflated row."""
    ledger, tick = _alpha_economy()
    p = _honest_report_payload(ledger, tick)
    alice = p["shares"].pop(0)
    p["shares"][0]["payout_ucr"] += alice["payout_ucr"]
    p["shares"][0]["share_bps"] += alice["share_bps"]
    codes = _codes_with(ledger, p)
    assert any(c.startswith("V4 ") and '"alice"' in c for c in codes)
    assert any(c.startswith("V1 ") and '"bob"' in c for c in codes)


def test_v5_unknown_method_convicts() -> None:
    ledger, tick = _alpha_economy()
    p = _honest_report_payload(ledger, tick)
    p["method"] = "vibes/1"
    assert any(c.startswith("V5 ") for c in _codes_with(ledger, p))


def test_v5_arity_over_nmax_convicts() -> None:
    """NMAX+1 sources: the game is unauditable in bounded work and the
    report convicts V5 — the denial-of-audit refusal, fail closed."""
    ledger = Ledger()
    keys = [("exp", f"s{i:02d}", "readerR") for i in range(NMAX + 1)]
    meter = _meter(ledger, keys)
    consumed = []
    for i, k in enumerate(keys):
        f = "sha256:" + ("%02x" % i) * 32
        ledger.add(DerivationEvent(
            derived=f, consumed=(_register_id(ledger, k),),
            hop_capacity_mbits=10, issuer="chamberA", seq=1 + i, tick=1))
        consumed.append(f)
    ledger.add(DerivationEvent(
        derived=FACT, consumed=tuple(consumed),
        hop_capacity_mbits=50_000, issuer="chamberA", seq=99, tick=1))
    decisions = meter.charge_coupled(
        keys, _est(1_000, "derived:" + FACT), TOR, tick=2)
    assert all(d.accepted for d in decisions.values())
    p = {
        "kind": "attribution_report", "derived": FACT,
        "coupling": {"node": "n1", "tick": 2}, "pot_ucr": 0,
        "method": "shapley_dpi/1", "shares": [],
        "issuer": "chamberA", "seq": 1, "tick": 3,
    }
    assert any(c.startswith("V5 ") for c in _codes_with(ledger, p))


def test_v5_malformed_fields_convict() -> None:
    """Junk pot, junk coupling, junk shares, duplicate rows — each is a
    V5, and V2 still fires where the arithmetic is checkable."""
    ledger, tick = _alpha_economy()
    good = _honest_report_payload(ledger, tick)
    for mutate in (
        lambda p: p.__setitem__("pot_ucr", "lots"),
        lambda p: p.__setitem__("coupling", "n1@2"),
        lambda p: p.__setitem__("shares", {"alice": 1}),
        lambda p: p.__setitem__("shares", p["shares"] + [p["shares"][0]]),
    ):
        led, tk = _alpha_economy()
        p = dict(_honest_report_payload(led, tk))
        p["shares"] = [dict(r) for r in p["shares"]]
        mutate(p)
        assert any(c.startswith("V5 ") for c in _codes_with(led, p)), good


# ---- 4. substrate ----

def test_total_on_junk_and_merge_invariant() -> None:
    """A report of pure junk raises nothing; findings are functions of
    the event set — shuffled ingestion cannot move them."""
    ledger, tick = _alpha_economy()
    p = _honest_report_payload(ledger, tick)
    p["shares"][0]["payout_ucr"] += 1
    _forge(ledger, p)
    _forge(ledger, {"kind": "attribution_report", "derived": 7,
                    "coupling": None, "pot_ucr": -3, "method": 9,
                    "shares": "nope", "issuer": [], "seq": {}, "tick": 3})
    want = attribution_codes(ledger)
    assert want  # convicted, not crashed
    lines = ledger.to_jsonl().splitlines()
    rng = random.Random(6)
    for _ in range(5):
        rng.shuffle(lines)
        assert attribution_codes(Ledger.from_jsonl("\n".join(lines))) == want


# ---- 5. frozen surfaces ----

def test_every_frozen_corpus_has_an_empty_v_verdict() -> None:
    """v1 outputs on report-free artifacts are unchanged: every frozen
    conformance artifact folds to an empty V verdict, which is why the
    corpora cannot be disturbed by this spec."""
    here = os.path.dirname(os.path.abspath(__file__))
    paths = []
    for d in ("ledger_traces", "settlement_traces", "settlement2_traces"):
        paths.extend(glob.glob(os.path.join(here, d, "*.jsonl")))
    assert len(paths) >= 20, "corpus went missing?"
    for path in paths:
        with open(path, "r", encoding="ascii") as fh:
            led = Ledger.from_jsonl(fh.read())
        assert attribution_codes(led) == [], path


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"  ok {name}")
    print(f"{len(fns)} passed")
