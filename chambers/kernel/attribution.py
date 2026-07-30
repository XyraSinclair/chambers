"""charge-attribution/1 — the split rule as a recomputable fact (V-codes).

ATTRIBUTION-SPEC.md is normative. The law: when a pot is split across the
sources of a derived fact's ancestry, the split is a declared rule computed
from facts already in the artifact — and a misdeclared split convicts from
bytes.

The game (SPEC V.2): players are the anchored sources of the fact's
provenance closure (KERNEL-SPEC P.2); the characteristic function is the
DPI carrying capacity v(S) = min(E, maxflow(coalition anchors -> d)) over
the P.4 network — the same quantity the P-codes charge, priced from the
other direction. Exact integer Shapley (SPEC V.3): subset-weight
numerators summing to n!*v(N); largest-remainder allocation with
ascending-source-id tie-break; conservation is by construction and
machine-checked in the abstract (lean/ChargeKernel/Attribution.lean).

Integer-only discipline: no float exists anywhere in this module. Total
on adversarial content: nothing here raises on any event soup.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from math import factorial
from typing import Any, Dict, List, Optional, Tuple

from events import canonical_json, event_id
from ledger import Ledger, _dpi_maxflow, _is_uint

#: SPEC V.2 — reports over more sources than this are unauditable in
#: bounded work (2^n max-flows) and convict V5: denial-of-audit refusal.
NMAX = 12

#: The one method /1 recomputes. Any other method string convicts V5.
METHOD = "shapley_dpi/1"

DERIVED_CHANNEL_PREFIX = Ledger.DERIVED_CHANNEL_PREFIX


# ---- the pure calculus (SPEC V.3) ----

def shapley_numerators(n: int, v_by_mask: List[int]) -> List[int]:
    """Exact Shapley numerators over an n-player game given as a list of
    2^n coalition values (index = bitmask). num[i] = sum over S not
    containing i of |S|!(n-1-|S|)!(v(S+i) - v(S)). For monotone v the
    numerators are non-negative naturals and sum to n! * v(full)."""
    fact = [factorial(k) for k in range(n + 1)]
    nums = [0] * n
    for mask in range(1 << n):
        s = bin(mask).count("1")
        w = fact[s] * fact[n - 1 - s] if s < n else 0
        if w == 0:
            continue
        vm = v_by_mask[mask]
        for i in range(n):
            if not (mask >> i) & 1:
                nums[i] += w * (v_by_mask[mask | (1 << i)] - vm)
    return nums


def allocate(pot: int, nums: List[int]) -> List[int]:
    """Largest-remainder division of a non-negative integer pot by
    non-negative integer weights with positive sum. Returns integer
    payouts summing to pot exactly; ties on remainders break toward the
    LOWEST index (callers pass sources in ascending lexicographic order,
    so the rule is deterministic across implementations). Each payout is
    within one unit of the unrounded share (the quota property)."""
    d = sum(nums)
    floors = [pot * x // d for x in nums]
    rems = [pot * x % d for x in nums]
    k = sum(rems) // d  # exact: d divides sum(rems); k < len(nums)
    out = list(floors)
    for i in sorted(range(len(nums)), key=lambda i: (-rems[i], i))[:k]:
        out[i] += 1
    return out


# ---- the game over the artifact (SPEC V.2) ----

def _coupling_exp_emissions(
    events: Dict[str, Dict[str, Any]], node: Any, tick: Any, channel: str
) -> List[Dict[str, Any]]:
    """The exp-emissions of the (node, tick, channel) coupling — P.3's
    grouping, verbatim: EMITTED charges on that channel agreeing on the
    raw JSON values of node and tick, whose key is an exposure triple."""
    gk = canonical_json([node, tick, channel])
    out = []
    for p in events.values():
        if p.get("kind") != "charge" or p.get("reason_class") != "EMITTED":
            continue
        if p.get("channel") != channel:
            continue
        if canonical_json([p.get("node"), p.get("tick"), channel]) != gk:
            continue
        k = p.get("key")
        if (isinstance(k, list) and len(k) == 3
                and all(isinstance(x, str) for x in k) and k[0] == "exp"):
            out.append(p)
    return out


def _game(
    ledger: Ledger, derived: str, node: Any, tick: Any
) -> Optional[Tuple[List[str], List[int], int]]:
    """Compute the SPEC V.2 game for an emission of `derived` at the
    (node, tick) coupling. Returns (sources ascending, numerators, E),
    or None when the game is unauditable (no exp-emissions, or arity
    over NMAX)."""
    events = getattr(ledger, "_events")
    channel = DERIVED_CHANNEL_PREFIX + derived
    exp_emissions = _coupling_exp_emissions(events, node, tick, channel)
    if not exp_emissions:
        return None
    emission_cap = max(
        (p["estimate_total_mbits"] for p in exp_emissions
         if _is_uint(p.get("estimate_total_mbits"))),
        default=0,
    )
    sources_map, used_derivs = ledger.provenance_closure(derived)
    sources = sorted(sources_map)
    n = len(sources)
    if n > NMAX:
        return None
    if n == 0:
        return [], [], emission_cap
    v_by_mask = [0] * (1 << n)
    for mask in range(1, 1 << n):
        anchors: set = set()
        for i in range(n):
            if (mask >> i) & 1:
                anchors |= sources_map[sources[i]]
        v_by_mask[mask] = _dpi_maxflow(
            "", derived, anchors, used_derivs, emission_cap
        )
    return sources, shapley_numerators(n, v_by_mask), emission_cap


def recomputed_shares(
    ledger: Ledger, derived: str, node: Any, tick: Any, pot_ucr: int
) -> Optional[List[Dict[str, Any]]]:
    """The honest share rows for a report: positive-numerator sources
    with their (share_bps, payout_ucr) pairs, both by the V.3 allocation.
    None when the game is unauditable; [] when no coalition carries
    anything (D = 0 — no positive pot is honestly splittable)."""
    game = _game(ledger, derived, node, tick)
    if game is None:
        return None
    sources, nums, _cap = game
    if sum(nums) == 0:
        return []
    payouts = allocate(pot_ucr, nums)
    bps = allocate(10000, nums)
    return [
        {"source": s, "share_bps": bps[i], "payout_ucr": payouts[i]}
        for i, s in enumerate(sources)
        if nums[i] > 0
    ]


# ---- the report event (SPEC V.1) ----

@dataclass(frozen=True)
class AttributionReportEvent:
    """charge-attribution/1 — the split claim the V-audit recomputes.

    Carries no value and no leakage; the fold ignores it. The report
    deliberately carries no numerators or flow values — every derivable
    quantity it could carry is an equivocation surface, and the audit
    derives them all. Fact identity is X0's for free:
    (issuer, "attribution_report", seq) equivocation convicts with no
    code added here.
    """

    derived: str
    node: str
    coupling_tick: int
    pot_ucr: int
    shares: Tuple[Tuple[str, int, int], ...]  # (source, share_bps, payout_ucr)
    issuer: str
    seq: int
    tick: int

    def payload(self) -> Dict[str, Any]:
        return {
            "kind": "attribution_report",
            "derived": self.derived,
            "coupling": {"node": self.node, "tick": self.coupling_tick},
            "pot_ucr": self.pot_ucr,
            "method": METHOD,
            "shares": [
                {"source": s, "share_bps": b, "payout_ucr": u}
                for (s, b, u) in self.shares
            ],
            "issuer": self.issuer,
            "seq": self.seq,
            "tick": self.tick,
        }

    @property
    def id(self) -> str:
        return event_id(self.payload())


def compile_report(
    ledger: Ledger,
    derived: str,
    node: str,
    coupling_tick: int,
    pot_ucr: int,
    issuer: str,
    seq: int,
    tick: int,
) -> AttributionReportEvent:
    """The honest reporter (SPEC V.5): recompute the game with the same
    functions the audit uses and emit a report that verifies clean by
    construction. Raises ValueError where an honest actor must refuse —
    an unauditable game, or a positive pot no coalition carries (the
    audit never raises; this is the honest-path mirror of V5/V2)."""
    if not _is_uint(pot_ucr):
        raise ValueError("pot_ucr must be a uint")
    rows = recomputed_shares(ledger, derived, node, coupling_tick, pot_ucr)
    if rows is None:
        raise ValueError(
            "unauditable game: no exp-emissions at that coupling, "
            f"or more than NMAX={NMAX} sources"
        )
    if not rows and pot_ucr > 0:
        raise ValueError(
            "no coalition carries anything (D = 0): a positive pot "
            "cannot be honestly split by shapley_dpi/1"
        )
    return AttributionReportEvent(
        derived=derived,
        node=node,
        coupling_tick=coupling_tick,
        pot_ucr=pot_ucr,
        shares=tuple(
            (str(r["source"]), int(r["share_bps"]), int(r["payout_ucr"]))
            for r in rows
        ),
        issuer=issuer,
        seq=seq,
        tick=tick,
    )


# ---- the V-audit (SPEC V.4) ----

def _att_subject(derived: Any, source: Any) -> str:
    return canonical_json(["att", derived, source])


def _parse_rows(shares: Any) -> Optional[List[Tuple[str, int, int]]]:
    """Well-formed share rows or None. A row is a dict with a string
    source and uint share_bps / payout_ucr; anything else is V5."""
    if not isinstance(shares, list):
        return None
    out: List[Tuple[str, int, int]] = []
    for row in shares:
        if not isinstance(row, dict):
            return None
        s, b, u = row.get("source"), row.get("share_bps"), row.get("payout_ucr")
        if not (isinstance(s, str) and _is_uint(b) and _is_uint(u)):
            return None
        out.append((s, b, u))
    return out


def attribution_findings(ledger: Ledger) -> List[Tuple[str, str, str]]:
    """V1-V5 (ATTRIBUTION-SPEC V.4). Total: never raises on adversarial
    content. Integer-only. Findings are functions of the event set —
    merge order and jsonl round-trips cannot move them."""
    findings: List[Tuple[str, str, str]] = []
    events = getattr(ledger, "_events")

    for eid in sorted(events):
        p = events[eid]
        if p.get("kind") != "attribution_report":
            continue

        derived = p.get("derived")
        pot = p.get("pot_ucr")
        coupling = p.get("coupling")
        rows = _parse_rows(p.get("shares"))
        auditable = True

        # ---- V5: what cannot be recomputed cannot be believed ----
        if p.get("method") != METHOD:
            findings.append(
                ("V5", eid,
                 f"V5 report {eid} declares method {p.get('method')!r}; "
                 f"/1 recomputes only {METHOD!r}")
            )
            auditable = False
        if not isinstance(derived, str):
            findings.append(
                ("V5", eid, f"V5 report {eid} has a non-string derived fact")
            )
            auditable = False
        if not _is_uint(pot):
            findings.append(
                ("V5", eid, f"V5 report {eid} has a non-uint pot_ucr")
            )
            auditable = False
        if not isinstance(coupling, dict):
            findings.append(
                ("V5", eid, f"V5 report {eid} has an unparsable coupling")
            )
            auditable = False
        if rows is None:
            findings.append(
                ("V5", eid, f"V5 report {eid} has unparsable shares")
            )
        elif len({s for s, _, _ in rows}) != len(rows):
            findings.append(
                ("V5", eid, f"V5 report {eid} names a source twice")
            )
            auditable = False

        # ---- V2: pure report arithmetic — never goes dark ----
        if rows is not None and _is_uint(pot):
            if sum(u for _, _, u in rows) != pot:
                findings.append(
                    ("V2", eid,
                     f"V2 report {eid} payouts sum to "
                     f"{sum(u for _, _, u in rows)} != pot {pot}")
                )
            if rows and sum(b for _, b, _ in rows) != 10000:
                findings.append(
                    ("V2", eid,
                     f"V2 report {eid} share_bps sum to "
                     f"{sum(b for _, b, _ in rows)} != 10000")
                )

        if not auditable or rows is None:
            continue

        # ---- the game ----
        want = recomputed_shares(
            ledger, derived, coupling.get("node"), coupling.get("tick"), pot
        )
        if want is None:
            findings.append(
                ("V5", eid,
                 f"V5 report {eid} is unauditable: no exp-emissions at "
                 f"its coupling, or more than NMAX={NMAX} sources")
            )
            continue
        want_by_source = {r["source"]: r for r in want}
        sources_map, _derivs = ledger.provenance_closure(derived)

        declared = {s: (b, u) for s, b, u in rows}
        for s in sorted(declared):
            b, u = declared[s]
            if s not in sources_map:
                findings.append(
                    ("V3", _att_subject(derived, s),
                     f"V3 report {eid} pays {s!r}, which is not a source "
                     f"of {derived}")
                )
                continue
            w = want_by_source.get(s)
            wb, wu = (w["share_bps"], w["payout_ucr"]) if w else (0, 0)
            if (b, u) != (wb, wu):
                findings.append(
                    ("V1", _att_subject(derived, s),
                     f"V1 report {eid} declares ({b} bps, {u} ucr) for "
                     f"{s!r}; recomputation gives ({wb} bps, {wu} ucr)")
                )
        for s in sorted(want_by_source):
            if s not in declared:
                findings.append(
                    ("V4", _att_subject(derived, s),
                     f"V4 report {eid} drops contributor {s!r} "
                     f"(recomputed {want_by_source[s]['payout_ucr']} ucr)")
                )
    return findings


def attribution_codes(ledger: Ledger) -> List[str]:
    """Conformance surface for the V-codes: sorted, deduplicated
    '<code> <subject>' strings, same discipline as every family."""
    return sorted({f"{c} {s}" for c, s, _ in attribution_findings(ledger)})
