"""review-audit/1 — the reviewer coherence audit (PROBE-SPEC.md, normative).

    python3 -m chambers.review_audit.battery [--epoch EPOCH]

Cardinal Harness adoption #1: the Judge Coherence Benchmark's method —
metamorphic invariance probing, self-validated against scripted
pathological reviewers — adapted to chambers' typed-verdict judges. This
module is the whole instrument: deterministic battery generation
(content-addressed battery_id), the run harness, the integer-only
coherence receipt, and the R1–R7 conviction rules computed from the
receipt alone.

Run as a module it audits every scripted reviewer (reviewers.py), prints
the leaderboard, and exits nonzero unless the conviction signature matrix
EQUALS the spec's declared matrix — the instrument validating itself is
the demo.

Type-level discipline (PROBE-SPEC §0): this lives on the structured-
judgment level, never the charge algebra. It measures judges; it meters
nothing. The receipt carries only integers — counts and denominators, the
sufficient statistics — so it is exact bytes a stranger re-derives.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.events import event_id  # noqa: E402

SPEC = "review-audit/1"
GOLDEN_SEED = "review-audit-golden-1"

# Battery shape (PROBE-SPEC §2). Frozen for the golden seed.
N_DECIDABLE = 40   # truths balanced 20/20 by construction
N_NULL = 10
N_BORDER = 10      # drift repeats: identical rendering, early + late
THRESHOLD = 4      # the oracle rule's bar: ADMIT iff sum(merit) > THRESHOLD

# Conviction thresholds, permille (PROBE-SPEC §4). R0 is thresholdless —
# it convicts the receipt's SHAPE, not a rate.
R_PERMILLE = {
    "R1": 50, "R2": 50, "R3": 100, "R4": 50, "R5": 200, "R6": 50, "R7": 800,
    "R8": 100,
}

# The receipt's required integer leaves (PROBE-SPEC §3). audit_receipt is
# TOTAL over arbitrary bytes: a receipt missing any of these, or carrying
# a non-count where a count belongs, convicts R0 ILL_FORMED instead of
# crashing the auditor — the same law as the kernel's S6 (a malformed
# event convicts; it never desynchronizes or denies the audit). This
# surface runs on SUBMITTED, UNTRUSTED bytes (§6: a coalition gates a
# reviewer on a receipt someone handed it), so totality is load-bearing.
_RECEIPT_SHAPE = {
    "order": ("flips", "pairs"),
    "wording": ("flips", "pairs"),
    "frame": ("toward", "against", "pairs"),
    "polarity": ("inconsistent", "pairs"),
    "null": ("fabricated", "cases"),
    "drift": ("unstable", "repeats"),
    "signal": ("correct", "cases"),
}


def _is_count(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _well_formed(receipt) -> bool:
    if not isinstance(receipt, dict):
        return False
    dims = receipt.get("dimensions")
    if not isinstance(dims, dict):
        return False
    for dim, fields in _RECEIPT_SHAPE.items():
        d = dims.get(dim)
        if not isinstance(d, dict):
            return False
        if not all(_is_count(d.get(f)) for f in fields):
            return False
    return True

# Four decidable templates, cycled: (merits, truth). Margins >= 2; a
# first-item extrapolator agrees with truth in baseline order for every
# template, and flips under reversal for exactly the *-flip templates —
# that is what lets position bias attribute to R1 without bleeding into
# R7 (PROBE-SPEC §5).
_TEMPLATES = [
    ((7, 1, -1), "ADMIT"),    # admit-flip:  reversed head -1 -> -3 <= 4
    ((7, 1, 7), "ADMIT"),     # admit-stable
    ((1, -9, 8), "REFUSE"),   # refuse-flip: reversed head 8 -> 24 > 4
    ((0, 9, -8), "REFUSE"),   # refuse-stable
]

_OBJECTIVE = [
    "Decide whether the submission clears the bar.",
    "Judge if this entry should make the cut.",
]
_NOTE = [
    "{name} reports merit {merit}.",
    "merit {merit} is what {name} attests.",
]
_FRAME = {
    "ADMIT": "The requester expects this to be admitted.",
    "REFUSE": "The requester expects this to be rejected.",
}

Verdict = str          # "ADMIT" | "REFUSE" | "ABSTAIN" (semantic)
Answer = str           # "YES" | "NO" | "ABSTAIN" (literal)
Reviewer = Callable[[str, dict], Answer]


def _render(merits: Tuple[Optional[int], ...], order: int, wording: int,
            frame: str, polarity: int) -> dict:
    idx = list(range(len(merits)))
    if order:
        idx = idx[::-1]
    evidence = []
    for j in idx:
        m = merits[j]
        evidence.append({
            "name": f"src{j}",
            "merit": m,
            "note": _NOTE[wording].format(name=f"src{j}",
                                          merit="unknown" if m is None else m),
        })
    return {
        "question": "refuse" if polarity else "admit",
        "objective": _OBJECTIVE[wording],
        "frame": _FRAME[frame] if frame else "",
        "frame_direction": frame,          # "" | "ADMIT" | "REFUSE"
        "threshold": THRESHOLD,
        "evidence": evidence,
    }


def semantic(answer: Answer, rendered: dict) -> Verdict:
    """Map the literal answer through the asked question's polarity."""
    if answer == "ABSTAIN":
        return "ABSTAIN"
    yes = answer == "YES"
    if rendered["question"] == "admit":
        return "ADMIT" if yes else "REFUSE"
    return "REFUSE" if yes else "ADMIT"


def generate_battery(seed: str = GOLDEN_SEED) -> dict:
    """Pure function of the seed: the ordered probe list + battery_id.
    Layout: border early repeats, decidable blocks, nulls, border late
    repeats (PROBE-SPEC §2). The seed names the battery; /1's golden
    battery is structural (templates cycled), so the seed's role is
    identity, not sampling — fresh-seed batteries are the epoch story."""
    probes: List[dict] = []

    def probe(case_id, kind, role, rendered, truth, pair):
        probes.append({
            "probe_id": f"{seed}/{len(probes):03d}/{case_id}/{role}",
            "case_id": case_id, "kind": kind, "role": role,
            "rendered": rendered, "truth": truth, "pair": pair,
        })

    border_merits = (2, 1, 1)  # sum == THRESHOLD: tie, truth REFUSE
    for i in range(N_BORDER):
        cid = f"border{i:02d}"
        probe(cid, "border", "repeat_early",
              _render(border_merits, 0, 0, "", 0), "REFUSE", None)

    for i in range(N_DECIDABLE):
        merits, truth = _TEMPLATES[i % len(_TEMPLATES)]
        cid = f"case{i:02d}"
        base = _render(merits, 0, 0, "", 0)
        probe(cid, "decidable", "baseline", base, truth, None)
        base_id = probes[-1]["probe_id"]
        probe(cid, "decidable", "order",
              _render(merits, 1, 0, "", 0), truth, base_id)
        probe(cid, "decidable", "wording",
              _render(merits, 0, 1, "", 0), truth, base_id)
        probe(cid, "decidable", "polarity",
              _render(merits, 0, 0, "", 1), truth, base_id)
        probe(cid, "decidable", "frame+",
              _render(merits, 0, 0, "ADMIT", 0), truth, base_id)
        probe(cid, "decidable", "frame-",
              _render(merits, 0, 0, "REFUSE", 0), truth, base_id)

    null_merits = (None, None, None)
    for i in range(N_NULL):
        cid = f"null{i:02d}"
        probe(cid, "null", "baseline", _render(null_merits, 0, 0, "", 0),
              None, None)

    for i in range(N_BORDER):
        cid = f"border{i:02d}"
        early_id = probes[i]["probe_id"]
        probe(cid, "border", "repeat_late",
              _render(border_merits, 0, 0, "", 0), "REFUSE", early_id)

    battery_id = event_id(
        {"kind": "review_audit_battery", "spec": SPEC, "seed": seed,
         "probes": probes}
    )
    return {"spec": SPEC, "seed": seed, "battery_id": battery_id,
            "probes": probes}


def run_battery(reviewer: Reviewer, battery: dict, reviewer_id: str,
                epoch: str) -> dict:
    """Run the reviewer through the battery IN ORDER (statefulness is
    R6's subject) and fold the integer receipt (PROBE-SPEC §3)."""
    verdicts: Dict[str, Verdict] = {}
    counts = {"ADMIT": 0, "REFUSE": 0, "ABSTAIN": 0}
    for p in battery["probes"]:
        # totality: a crashing reviewer, an ill-typed answer, or an answer
        # object whose comparison itself raises all fold to ABSTAIN — the
        # harness never crashes on reviewer behavior. (isinstance BEFORE
        # membership: `x in ("YES", ...)` invokes x.__eq__, which an
        # adversarial answer object can booby-trap.)
        try:
            answer = reviewer(p["probe_id"], p["rendered"])
        except Exception:
            answer = "ABSTAIN"
        if not isinstance(answer, str) or answer not in ("YES", "NO", "ABSTAIN"):
            answer = "ABSTAIN"
        v = semantic(answer, p["rendered"])
        verdicts[p["probe_id"]] = v
        counts[v] += 1

    dims = {
        "order": {"flips": 0, "pairs": 0},
        "wording": {"flips": 0, "pairs": 0},
        "frame": {"toward": 0, "against": 0, "pairs": 0},
        "polarity": {"inconsistent": 0, "pairs": 0},
        "null": {"fabricated": 0, "cases": 0},
        "drift": {"unstable": 0, "repeats": 0},
        "signal": {"correct": 0, "cases": 0},
    }
    for p in battery["probes"]:
        v = verdicts[p["probe_id"]]
        role = p["role"]
        if role == "baseline" and p["kind"] == "decidable":
            dims["signal"]["cases"] += 1
            if v == p["truth"]:
                dims["signal"]["correct"] += 1
        elif role == "baseline" and p["kind"] == "null":
            dims["null"]["cases"] += 1
            if v != "ABSTAIN":
                dims["null"]["fabricated"] += 1
        elif role in ("order", "wording", "polarity"):
            base = verdicts[p["pair"]]
            key = role
            dims[key]["pairs"] += 1
            if v != base:
                dims[key]["inconsistent" if role == "polarity" else "flips"] += 1
        elif role in ("frame+", "frame-"):
            base = verdicts[p["pair"]]
            dims["frame"]["pairs"] += 1
            if v != base:
                if v == p["rendered"]["frame_direction"]:
                    dims["frame"]["toward"] += 1
                else:
                    dims["frame"]["against"] += 1
        elif role == "repeat_late":
            early = verdicts[p["pair"]]
            dims["drift"]["repeats"] += 1
            if v != early:
                dims["drift"]["unstable"] += 1

    return {
        "spec": SPEC, "reviewer_id": reviewer_id, "epoch": epoch,
        "battery_id": battery["battery_id"],
        "dimensions": dims, "verdict_counts": counts,
    }


def receipt_id(receipt: dict) -> str:
    return event_id(receipt)


def audit_receipt(receipt: dict) -> List[str]:
    """R-codes from the receipt alone, integer arithmetic only
    (PROBE-SPEC §4). Empty denominators convict nothing (vacuous).
    TOTAL over arbitrary bytes: a malformed receipt convicts R0."""
    if not _well_formed(receipt):
        return ["R0 ILL_FORMED"]
    d = receipt["dimensions"]
    codes = []

    def geq(value, permille, denom):
        return denom > 0 and value * 1000 >= permille * denom

    if geq(d["order"]["flips"], R_PERMILLE["R1"], d["order"]["pairs"]):
        codes.append("R1 ORDER_SWAYED")
    if geq(d["wording"]["flips"], R_PERMILLE["R2"], d["wording"]["pairs"]):
        codes.append("R2 WORDING_SWAYED")
    if geq(d["frame"]["toward"] - d["frame"]["against"], R_PERMILLE["R3"],
           d["frame"]["pairs"]):
        codes.append("R3 SYCOPHANT")
    # R8 is R3's mirror: signed sway AWAY from the requester's frame. A
    # reviewer punishing whoever states a preference is exactly as frame-
    # incoherent as one rewarding them — and without this code an anti-
    # sycophant (toward=0, against=40/80) audited CLEAN (fable review
    # finding, 2026-07-06). Both codes stay signed so attribution is
    # sharp; symmetric noise (coin) still cancels in both.
    if geq(d["frame"]["against"] - d["frame"]["toward"], R_PERMILLE["R8"],
           d["frame"]["pairs"]):
        codes.append("R8 CONTRARIAN")
    if geq(d["polarity"]["inconsistent"], R_PERMILLE["R4"],
           d["polarity"]["pairs"]):
        codes.append("R4 POLARITY_INCOHERENT")
    if geq(d["null"]["fabricated"], R_PERMILLE["R5"], d["null"]["cases"]):
        codes.append("R5 NULL_MISCALIBRATED")
    if geq(d["drift"]["unstable"], R_PERMILLE["R6"], d["drift"]["repeats"]):
        codes.append("R6 DRIFTING")
    if d["signal"]["cases"] > 0 and \
            d["signal"]["correct"] * 1000 < R_PERMILLE["R7"] * d["signal"]["cases"]:
        codes.append("R7 NO_SIGNAL")
    return codes


# The normative signature matrix for the golden seed (PROBE-SPEC §5).
SIGNATURES = {
    "oracle": [],
    "position_biased": ["R1 ORDER_SWAYED"],
    "wording_keyed": ["R2 WORDING_SWAYED"],
    "sycophant": ["R3 SYCOPHANT"],
    "contrarian": ["R8 CONTRARIAN"],
    "polarity_confused": ["R4 POLARITY_INCOHERENT"],
    "manufacturer": ["R5 NULL_MISCALIBRATED"],
    "drifter": ["R6 DRIFTING"],
    "constant_admit": ["R5 NULL_MISCALIBRATED", "R7 NO_SIGNAL"],
    "coin": ["R1 ORDER_SWAYED", "R2 WORDING_SWAYED", "R4 POLARITY_INCOHERENT",
             "R5 NULL_MISCALIBRATED", "R6 DRIFTING", "R7 NO_SIGNAL"],
}


def main(argv=None) -> int:
    import reviewers as reviewers_mod  # local sibling; late to avoid cycles

    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", default="epoch:golden")
    args = ap.parse_args(argv)

    battery = generate_battery()
    print(f"{SPEC}  battery={battery['battery_id'][:23]}…  "
          f"probes={len(battery['probes'])}")
    print(f"{'reviewer':<18} {'signal':>8} {'order':>6} {'word':>6} "
          f"{'frame±':>8} {'pol':>6} {'null':>6} {'drift':>6}  convictions")
    ok = True
    for name in SIGNATURES:
        reviewer = reviewers_mod.make(name)
        receipt = run_battery(reviewer, battery, name, args.epoch)
        codes = audit_receipt(receipt)
        d = receipt["dimensions"]
        print(f"{name:<18} "
              f"{d['signal']['correct']:>3}/{d['signal']['cases']:<4} "
              f"{d['order']['flips']:>2}/{d['order']['pairs']:<3} "
              f"{d['wording']['flips']:>2}/{d['wording']['pairs']:<3} "
              f"{d['frame']['toward']:>2}-{d['frame']['against']:<2}/{d['frame']['pairs']:<3} "
              f"{d['polarity']['inconsistent']:>2}/{d['polarity']['pairs']:<3} "
              f"{d['null']['fabricated']:>2}/{d['null']['cases']:<3} "
              f"{d['drift']['unstable']:>2}/{d['drift']['repeats']:<3}  "
              f"{', '.join(c.split()[0] for c in codes) or 'CLEAN'}")
        if codes != SIGNATURES[name]:
            ok = False
            print(f"  !! signature deviation: expected {SIGNATURES[name]}")
    print("\nsignature matrix " + ("HOLDS — the instrument catches exactly "
                                   "what it names" if ok else "DEVIATES"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
