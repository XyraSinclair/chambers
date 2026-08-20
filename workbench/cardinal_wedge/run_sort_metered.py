"""The metered sort — cardinal-harness's output priced by the kernel.

    python3 -m workbench.cardinal_wedge.run_sort_metered [--out DIR] [--n N]

Cardinal Harness (the open-source `cardinal-harness` crate) sorts items by eliciting pairwise
judgements. That is exactly the channel this kernel was built to price: a
ranking of n items whose sources are private carries log2(n!) bits about
those sources, adversarial-max — `CapacityEstimate.ordering_mbits`, the
`orderingBits` the estimator probe already smuggles secrets through
(d1_bounty). This wedge runs the LEGITIMATE consumer of that channel end
to end:

  1. n items, each owned by a source chamber, exposed to one ranker
     (reader). Registered as exposure accounts `(exp, item_owner, ranker)`.
  2. The ranker does pairwise reads — each comparison is a metered
     OBSERVATION charge against the two items' source accounts (reading
     two private items to compare them leaks about both).
  3. The final ranking is ONE ATOMIC COUPLED EMISSION of log2(n!)
     ordering-millibits against ALL n source accounts (the sorted list is
     information about every source; charge_coupled = all-or-none, so a
     ranking that would bust any one source's ceiling emits nothing).
  4. Settlement: the requester deposits, escrows against the emission's
     charge keys, and releases the fee against the emission's charge event
     ids — pay for the ranking iff the ranking was actually metered.
  5. One jsonl artifact a stranger re-audits; conservation; tamper-convict.

THE RANKING ORACLE IS PLUGGABLE, MOCKED HERE. Cardinal-harness needs live
LLM calls (OpenRouter) to elicit real pairwise judgements; this demo uses
a deterministic comparator so it is HERMETIC (no network, no key, no
flake) and the METERING is the point being proven, not the sort quality.
In production the comparator is `cardinal sort`; the kernel side is
identical. What this demonstrates is the exact claim from the mapping
report: the kernel already prices cardinal's output, and coupled emission
is the correct shape for it. Honest limit: a real cardinal run would also
CHARGE for the model's reasoning trace as side-channel; that is estimator
work above this boundary, named not faked.

No floats in any decision path; log2(n!) is computed at the attested
estimator boundary and rounded to integer millibits (documented rule).
"""
from __future__ import annotations

import argparse
import io
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from chambers.kernel.accountant import CapacityEstimate, EstimatorAttestation, exposure_key  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.meter import KernelMeter  # noqa: E402
from chambers.kernel.settlement import SettlementIssuer, conservation_identity, settlement_fold  # noqa: E402
from chambers.kernel import verify as verify_mod  # noqa: E402

RANKER = "cardinal_ranker_v1"

# Per-comparison observation: reading two items to compare them. A pairwise
# ratio judgement resolves ~1 bit of order per item read; charge that as
# enum capacity on each source (attested-flat, the honest floor).
COMPARE_ENUM_MBITS = 1_000

OBS_ESTIMATOR = EstimatorAttestation(
    "cardinal.pairwise_read.flat_v1", "adversarial_review", "declared_flat", True
)
RANK_ESTIMATOR = EstimatorAttestation(
    "cardinal.ordering.log2_factorial_v1", "adversarial_review",
    "log2_factorial_round_half_even", True
)


def ordering_mbits(n: int) -> int:
    """Attested-estimator boundary: log2(n!) bits -> integer millibits,
    round-half-to-even. This is the ONLY float in the file, and it never
    touches a decision path — the kernel sees the integer."""
    if n < 2:
        return 0
    bits = math.lgamma(n + 1) / math.log(2.0)  # log2(n!) without overflow
    return round(bits * 1000.0)


def _mock_cardinal_sort(items):
    """Deterministic stand-in for `cardinal sort`. Returns (ranking,
    comparisons): ranking is item ids best-first; comparisons is the list
    of (i, j) pairs 'read' to produce it. A merge-sort's comparison set is
    a realistic O(n log n) read pattern — far fewer than n^2, which is
    cardinal's whole active-planning point."""
    comparisons = []

    def key(x):
        return x["score"]

    # record the comparisons an actual sort performs
    import functools

    def cmp(a, b):
        comparisons.append((a["id"], b["id"]))
        return -1 if key(a) > key(b) else (1 if key(a) < key(b) else 0)

    ranking = sorted(items, key=functools.cmp_to_key(cmp))
    return [x["id"] for x in ranking], comparisons


def _ceiling_mbits(n: int) -> int:
    """Per-source ceiling as a DECLARED bound, not a vibe: the item's
    share of the one coupled ordering emission (log2(n!) lands on every
    source) plus a sound bound on its pairwise-read observations — no
    single item can appear in more comparisons than the sort performs,
    and a comparison sort performs at most n*(ceil(log2 n)+1). The
    previous hardcoded 200,000 was silently BELOW log2(n!) from n≈50,
    so the demo's own assertion crashed on legal --n (fable review
    finding, 2026-07-06)."""
    read_bound = n * (max(1, math.ceil(math.log2(n))) + 1) * COMPARE_ENUM_MBITS
    return ordering_mbits(n) + read_bound


def build(n: int = 6) -> Ledger:
    if n < 2:
        raise ValueError(
            "a metered ranking needs at least 2 items: log2(n!) of "
            f"n={n} carries no ordering information and an escrow "
            "binds to at least one metered account")
    ledger = Ledger()
    # n private items, each its own source chamber, one ranker as reader.
    items = [{"id": f"item{i}", "owner": f"owner{i}", "score": (i * 37) % n}
             for i in range(n)]
    keys = {it["id"]: exposure_key(it["owner"], RANKER) for it in items}

    meter = KernelMeter(node="ranker_node", issuer=RANKER, ledger=ledger)
    ceiling = _ceiling_mbits(n)
    for it in items:
        # ceiling: declared bound covering the reads + this item's share
        # of the ordering emission; the coupling is what makes a too-tight
        # ceiling refuse the WHOLE ranking, not silently drop one source.
        meter.register(keys[it["id"]], subject_entropy_mbits=2 * ceiling,
                       ceiling_mbits=ceiling)

    # 2 — pairwise reads, each a metered observation on both sources
    ranking, comparisons = _mock_cardinal_sort(items)
    tick = 1
    for a, b in comparisons:
        est = CapacityEstimate(COMPARE_ENUM_MBITS, 0, 0, 0, 0, "pairwise_read")
        meter.charge(keys[a], est, OBS_ESTIMATOR, tick=tick)
        meter.charge(keys[b], est, OBS_ESTIMATOR, tick=tick)
        tick += 1

    # 3 — the ranking: ONE atomic coupled emission of log2(n!) ordering
    #     millibits against every source
    rank_est = CapacityEstimate(0, ordering_mbits(n), 0, 0, 0, "ranking")
    all_keys = [keys[it["id"]] for it in items]
    decisions = meter.charge_coupled(all_keys, rank_est, RANK_ESTIMATOR, tick=tick)
    assert all(d.accepted for d in decisions.values()), "ranking emission must clear all sources"
    emission_tick = tick

    # collect the emission's charge event ids (the work receipt)
    receipt = [
        eid for eid, p in getattr(ledger, "_events").items()
        if p.get("kind") == "charge" and p.get("channel") == "ranking"
        and p.get("tick") == emission_tick and p.get("accepted") is True
    ]
    assert len(receipt) == n, "one ranking charge per source"

    # 4 — settlement: pay for the ranking against its receipt
    bank = SettlementIssuer(issuer="rank_bank", ledger=ledger)
    bank.deposit("requester", 1_000_000, tick=0)
    escrow = bank.escrow(payer="requester", payee=RANKER, amount_ucr=250_000,
                         charge_keys=all_keys, expires_tick=10_000, tick=emission_tick + 1)
    bank.release(escrow, 250_000, receipt, tick=emission_tick + 2)

    ledger._ranking_result = ranking  # for the demo printout only
    return ledger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".chamber", "cardinal_sort"))
    args = ap.parse_args(argv)
    if args.n < 2:
        ap.error("--n must be >= 2: a ranking of fewer than 2 items "
                 "carries no ordering information")

    ledger = build(args.n)
    artifact = ledger.to_jsonl()
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "sort_metered.jsonl")
    with open(path, "w", encoding="ascii") as fh:
        fh.write(artifact)

    buf = io.StringIO()
    code = verify_mod.verify(artifact, out=buf)
    print(buf.getvalue())
    assert code == 0, "honest metered sort must verify CLEAN"

    accounts, _ = settlement_fold(ledger)
    lhs, rhs = conservation_identity(ledger)
    assert accounts[RANKER].available_ucr == 250_000, "ranker paid for the ranking"
    assert lhs == rhs == 1_000_000

    # tamper: inflate the ranker's payment; the artifact convicts
    tampered = artifact.replace('"amount_ucr":250000', '"amount_ucr":900000')
    assert tampered != artifact
    buf2 = io.StringIO()
    code2 = verify_mod.verify(tampered, out=buf2)
    tail = [l for l in buf2.getvalue().splitlines() if l.startswith(("CONVICTED", "  S"))]
    print("tampered verdict:")
    for line in tail:
        print(" ", line)
    assert code2 == 1, "tampered artifact must be convicted"

    print(f"\nranking: {getattr(ledger, '_ranking_result', [])}")
    print(f"ordering charge: log2({args.n}!) = {ordering_mbits(args.n)} mbits, "
          f"coupled across {args.n} sources")
    print(f"artifact: {path} ({ledger.event_count()} events)")
    print("cardinal's output priced by the kernel: read → coupled-emit → settle, verifiable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
