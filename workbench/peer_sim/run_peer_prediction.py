"""peer-sim — F5's worked machinery: peer prediction under metered leakage.

The design memo (frontier/judgement-markets/peer-prediction.md) made
three claims this file makes runnable, in exact integers, through the
REAL meter and settlement:

  1. The correlated-agreement score is pure ledger-grade arithmetic
     over reports, and the constant-report strategy scores EXACTLY
     zero — an identity, not an expectation (self-checked over every
     report vector we throw at it).
  2. v0 runs today: on a low-sensitivity coupling the audit judge's
     redundancy is metered openly (`redundancy_mbits` on the receipt),
     fees and the CA bonus settle as ordinary escrows against the
     exact charge receipts, and the stranger's verifier exits CLEAN.
  3. The KILL regime is arithmetic: on a high-sensitivity coupling the
     second reader hits REFUSED_CEILING — the mechanism is refused at
     any price, honesty there stays priced by process receipts, and
     the artifact still verifies CLEAN (a refusal is not a crime).

Reports ride sim-local books (the intro_clearing precedent); the score-
bound escrow needs a report event kind — v1 precondition 1, named in
the memo. No float exists anywhere in this file.

Run: python3 -m workbench.peer_sim.run_peer_prediction
"""
from __future__ import annotations

import io
import os
import sys
from typing import Dict, List, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "chambers", "kernel"))

import verify as verify_mod  # noqa: E402
from accountant import CapacityEstimate, EstimatorAttestation, exposure_key  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402
from settlement import SettlementIssuer, SettlementRefused  # noqa: E402

TOR = EstimatorAttestation("indep-est", "adversarial_review", "m", True)

CHECKS: List[str] = []


def check(name: str, ok: bool) -> None:
    CHECKS.append(name)
    if not ok:
        raise AssertionError(f"self-check failed: {name}")


# ---- 1. the CA score, exact integers (memo §2) ----

def ca_score(r1: List[int], r2: List[int]) -> int:
    """Correlated agreement, multiplied out to stay integer:
    (n-1)·Σ_t match(t)  −  Σ_{t≠t'} match(r1[t], r2[t']).
    Positive for informative correlated reports; EXACTLY zero for any
    constant strategy, by identity."""
    n = len(r1)
    assert len(r2) == n
    diag = sum(1 for t in range(n) if r1[t] == r2[t])
    off = sum(
        1
        for t in range(n)
        for u in range(n)
        if t != u and r1[t] == r2[u]
    )
    return (n - 1) * diag - off


def scene_score_identities() -> None:
    """Memo §2.1: constant strategies score exactly zero, informative
    correlation scores positive, and the anti-correlated pair scores
    negative — arithmetic identities over fixed vectors."""
    latent = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]
    honest2 = list(latent)
    honest2[3] ^= 1  # two honest judges disagree occasionally
    honest2[8] ^= 1
    for reports in (latent, honest2, [0, 1] * 6, [1] * 12, [0] * 12):
        for c in (0, 1):
            check(
                f"constant-{c} scores exactly 0 against {reports[:4]}…",
                ca_score(reports, [c] * len(reports)) == 0,
            )
    check("honest correlated pair scores positive",
          ca_score(latent, honest2) > 0)
    check("anti-correlated pair scores negative",
          ca_score(latent, [1 - x for x in latent]) < 0)


# ---- the metered judging economy ----

ITEM_MBITS = [900, 1100, 800, 1200, 1000, 950, 1050, 900, 1150, 850, 1000, 1100]
LATENT = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]


def _judge_reads(
    meter: KernelMeter, key, mbits: List[int], tick0: int
) -> Tuple[List[str], int, List[str]]:
    """Meter one judge's reads. Returns (accepted charge ids, total
    accepted mbits, refusal reason_classes)."""
    ledger = meter.ledger
    before = set(getattr(ledger, "_events"))
    total = 0
    refusals: List[str] = []
    for i, m in enumerate(mbits):
        d = meter.charge(
            key, CapacityEstimate(m, 0, 0, 0, 0, f"judgement:item{i:02d}"),
            TOR, tick=tick0 + i,
        )
        if d.accepted:
            total += m
        else:
            refusals.append(d.reason_class)
    charge_ids = sorted(
        eid for eid, p in getattr(ledger, "_events").items()
        if eid not in before and p.get("kind") == "charge"
        and p.get("accepted") is True
    )
    return charge_ids, total, refusals


def scene_v0_low_sensitivity(out) -> None:
    """Memo §6 v0: both judges metered, redundancy printed openly, CA
    bonus settles against the exact receipts, verifier CLEAN."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="ownerO", ledger=ledger)
    k1 = exposure_key("ownerO", "judge1")
    k2 = exposure_key("ownerO", "judge2")
    for k in (k1, k2):
        meter.register(k, subject_entropy_mbits=400_000, ceiling_mbits=50_000)

    ids1, spent1, ref1 = _judge_reads(meter, k1, ITEM_MBITS, tick0=10)
    ids2, spent2, ref2 = _judge_reads(meter, k2, ITEM_MBITS, tick0=40)
    check("low-sensitivity: both judges read everything",
          not ref1 and not ref2 and len(ids1) == len(ids2) == len(ITEM_MBITS))

    # reports (sim-local books; v1 precondition 1 named in the memo)
    reports1 = list(LATENT)
    reports2 = list(LATENT)
    reports2[3] ^= 1
    reports2[8] ^= 1
    score = ca_score(reports1, reports2)
    check("v0 honest pair earns a strictly positive score", score > 0)

    # settlement: fees for both judges + the CA bonus, all receipt-bound
    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    FEE1, FEE2, BONUS = 5_000_000, 2_000_000, 3_000_000
    bank.deposit("requesterR", FEE1 + FEE2 + BONUS, tick=100)
    e1 = bank.escrow("requesterR", "judge1", FEE1, [k1], 200, tick=101)
    e2 = bank.escrow("requesterR", "judge2", FEE2, [k2], 200, tick=102)
    eb = bank.escrow("requesterR", "judge1", BONUS, [k1], 200, tick=103)
    bank.release(e1, FEE1, ids1, tick=110)
    bank.release(e2, FEE2, ids2, tick=111)
    if score > 0:  # the v0 bonus rule: strict positivity, else refund
        bank.release(eb, BONUS, ids1, tick=112)
    else:
        bank.refund(eb, BONUS, tick=112)

    rc = verify_mod.verify(ledger.to_jsonl(), out=io.StringIO())
    check("v0 artifact verifies CLEAN end to end", rc == 0)

    print("\n== v0 — the low-sensitivity coupling (memo §6) ==", file=out)
    print(f"  items judged twice : {len(ITEM_MBITS)}", file=out)
    print(f"  primary exposure   : {spent1} mbits -> ['exp','ownerO','judge1']", file=out)
    print(f"  redundancy_mbits   : {spent2} mbits -> ['exp','ownerO','judge2']"
          "   <- the mechanism's own price, printed", file=out)
    print(f"  ca_score (integer) : {score}", file=out)
    print(f"  settled            : fee1 {FEE1} + fee2 {FEE2} + bonus {BONUS} ucr, "
          "all receipt-bound, court CLEAN", file=out)


def scene_kill_high_sensitivity(out) -> None:
    """Memo §4: the moat refuses the redundancy. The ceiling admits one
    judge's reads; the second reader is REFUSED_CEILING mid-batch; the
    mechanism is unavailable at any price; flat fee settles; CLEAN."""
    ledger = Ledger()
    meter = KernelMeter(node="n1", issuer="ownerO", ledger=ledger)
    k1 = exposure_key("ownerO", "judge1")
    k2 = exposure_key("ownerO", "judge2")
    total = sum(ITEM_MBITS)  # 12_000
    # The moat is PER READER, so the kill is the OWNER's registration
    # arithmetic, not an automatic collision: the primary judge is
    # ceilinged at exactly the coupling's needs; the audit reader gets
    # the owner's declared redundancy budget — a sliver. (G5's
    # discipline: refusing to register IS the zero ceiling; a token
    # ceiling is its priced sibling.)
    meter.register(k1, subject_entropy_mbits=16_000, ceiling_mbits=total)
    meter.register(k2, subject_entropy_mbits=16_000, ceiling_mbits=1_900)

    ids1, spent1, ref1 = _judge_reads(meter, k1, ITEM_MBITS, tick0=10)
    check("kill: the primary judge fits the moat", not ref1)
    ids2, spent2, ref2 = _judge_reads(meter, k2, ITEM_MBITS, tick0=40)
    check("kill: the audit judge hits the ceiling",
          any(r == "REFUSED_CEILING" for r in ref2))
    check("kill: the refusal leaks nothing further",
          spent2 <= 1_900)

    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    FEE1, BONUS = 5_000_000, 3_000_000
    bank.deposit("requesterR", FEE1 + BONUS, tick=100)
    e1 = bank.escrow("requesterR", "judge1", FEE1, [k1], 200, tick=101)
    eb = bank.escrow("requesterR", "judge1", BONUS, [k1], 200, tick=102)
    bank.release(e1, FEE1, ids1, tick=110)
    bank.refund(eb, BONUS, tick=111)  # no CA possible: the bonus returns

    rc = verify_mod.verify(ledger.to_jsonl(), out=io.StringIO())
    check("kill-regime artifact verifies CLEAN (a refusal is not a crime)",
          rc == 0)

    print("\n== the KILL regime — the high-sensitivity coupling (memo §4) ==", file=out)
    print(f"  owner's ceilings   : judge1 {total} mbits (the coupling's needs, "
          "exactly); judge2 1900 mbits (the declared redundancy budget)", file=out)
    print(f"  primary judge      : {spent1} mbits, fits", file=out)
    print(f"  audit judge        : REFUSED_CEILING after {spent2} mbits — "
          "the mechanism is unavailable AT ANY PRICE", file=out)
    print(f"  settled            : flat fee {FEE1} ucr on receipts; "
          f"bonus {BONUS} ucr refunded untouched; court CLEAN", file=out)
    print("  honesty here stays priced by process receipts "
          "(review-audit/1), which cost zero owner leakage", file=out)


def main(out=sys.stdout) -> int:
    scene_score_identities()
    scene_v0_low_sensitivity(out)
    scene_kill_high_sensitivity(out)
    print(f"\n{len(CHECKS)} self-checks passed", file=out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
