"""Run the IP-trade simulation and print a readable transcript + leakage report.

    python3 -m chambers.ip_trade_sim.run
"""
from __future__ import annotations

from . import strategies
from .engine import run_lane
from .leakage import LeakageAccountant
from .report import structural_receipt_lines
from .scenario import build_labs


def _print_lane(res, accountant):
    print(f"\n{'='*70}\nLANE  {res.lane_id}\n{'='*70}")
    for o in res.outcomes:
        print(f"\n  ◆ {o.technique_id}  [{o.area}]")
        print(f"    verdict.proven:     {o.verdict.proven}")
        print(f"    verdict.unprovable: {o.verdict.unprovable}")
        if o.appraisal:
            print(f"    appraisal:  value={o.appraisal.est_value_credits} conf={o.appraisal.confidence:.2f} "
                  f"bits_spent={o.appraisal.bits_spent:.2f}")
            print(f"                {o.appraisal.rationale}")
        if o.cross:
            # operator god-view keeps outcome+price only; draws/reserve are
            # party-private inputs even on this console, for surface hygiene
            print(f"    price cross: {o.cross.outcome}"
                  + (f"  -> {o.cross.cleared_price}" if o.cross.cleared_price else ""))
        if o.settlement:
            print(f"    SETTLEMENT: {o.settlement.state} @ {o.settlement.price} ({o.settlement.regime})")
    print(f"\n  --- Receipt, structural register ({res.lane_id}) — STRUCTURE.md §5 ---")
    for line in structural_receipt_lines(res, accountant):
        print(f"   {line}")


def main():
    a, b = build_labs()
    accountant = LeakageAccountant()

    print("Confidential IP-trade simulation")
    print(f"  {a.name} ({a.id}) stakes: {a.area_stakes}")
    print(f"  {b.name} ({b.id}) stakes: {b.area_stakes}")

    # each lab is the buyer in one lane, appraising the other's portfolio
    r1 = run_lane(a, b, accountant, strategies, seed="AB")
    r2 = run_lane(b, a, accountant, strategies, seed="BA")
    _print_lane(r1, accountant)
    _print_lane(r2, accountant)

    print(f"\n{'='*70}\nLEAKAGE REPORT (bits each observer accumulated about each technique)\n{'='*70}")
    for row in accountant.report():
        flag = "  ⚠ INCIDENT" if row["incident"] else ("  [blocked]" if row["blocked"] else "")
        print(f"  {row['observer']} learned {row['cumulative_bits']}/{row['entropy_bits']} bits "
              f"({row['fraction']*100:.0f}%, {row['class']}) of {row['technique']}{flag}")
        print(f"      channels: {row['debits']}")

    cb = accountant.cut_bound()
    print(f"\n{'='*70}\nPROTOCOL CUT BOUND (CALCULUS.md §6)\n{'='*70}")
    print(f"  derived (codebook releases, exact by construction): {cb['derived_bits']} bits")
    print(f"  declared (probes/reveals, honest estimates):        {cb['declared_bits']} bits")
    print(f"  total crossing the silo boundary:                   {cb['total_bits']} bits")

    audit = accountant.ledger.audit()
    if audit:
        raise RuntimeError(f"charge-kernel ledger audit findings: {audit}")
    print(f"\ncharge-kernel audit: clean ({accountant.ledger.event_count()} events)")
    print(f"\nFinal credits: {a.name}={a.credits}  {b.name}={b.credits}")


if __name__ == "__main__":
    main()
