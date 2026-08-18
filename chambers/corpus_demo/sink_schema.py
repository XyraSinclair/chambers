"""The sink: the ONLY thing the guest can ever say, enumerated.

This is the published half of the contract (with GUEST_SPEC.md). The
verdict alphabet is closed: 3 ranked picks from the packet's enumerated
candidate IDs, each with a reason code from a fixed taxonomy and a
bucketed confidence — plus the enumerated failure outcomes. Capacity is
DERIVED from the counts (CALCULUS.md §2); there is nothing to declare.

stdlib-only, wire-canonical: a verdict serializes to exactly one JSON
form (sorted keys, no whitespace variance) so the charge is over
wire-distinguishable encodings.
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Tuple

N_PICKS = 3

REASON_CODES: Tuple[str, ...] = (
    "unlocks_current_work",
    "complementary_asset",
    "market_timing_now",
    "cheap_to_validate",
    "compounding_moat",
    "unique_insight_unexploited",
    "derisked_by_new_tools",
    "synergy_with_chambers",
)

CONFIDENCE: Tuple[str, ...] = ("low", "medium", "high")

# Every observable outcome, failures included (CALCULUS.md L6).
OUTCOME_CODES: Tuple[str, ...] = (
    "ok",
    "rejected_schema",   # guest emitted something outside this file
    "errored_worker",    # guest crashed or exceeded its call budget
    "withheld_owner",    # owner declined release after review
)


def verdict_space(n_candidates: int) -> int:
    """|ranked 3-of-n| x |reasons|^3 x |confidence|^3 + non-ok outcomes."""
    if n_candidates < N_PICKS:
        raise ValueError("packet must enumerate at least N_PICKS candidates")
    ranked = 1
    for i in range(N_PICKS):
        ranked *= n_candidates - i
    return ranked * (len(REASON_CODES) ** N_PICKS) * (len(CONFIDENCE) ** N_PICKS) + (
        len(OUTCOME_CODES) - 1
    )


def capacity_bits(n_candidates: int) -> float:
    return math.log2(verdict_space(n_candidates))


def validate_verdict(verdict: Any, candidate_ids: List[str]) -> List[str]:
    """Return a list of violations; empty list == conforming. Never raises:
    a malformed verdict is the `rejected_schema` symbol, not an exception."""
    problems: List[str] = []
    if not isinstance(verdict, dict):
        return ["verdict is not an object"]
    picks = verdict.get("picks")
    extra = set(verdict.keys()) - {"picks"}
    if extra:
        problems.append(f"unknown top-level keys: {sorted(extra)}")
    if not isinstance(picks, list) or len(picks) != N_PICKS:
        problems.append(f"picks must be a list of exactly {N_PICKS}")
        return problems
    seen_ids = set()
    for i, pick in enumerate(picks):
        if not isinstance(pick, dict):
            problems.append(f"pick[{i}] is not an object")
            continue
        extra = set(pick.keys()) - {"candidate_id", "reason", "confidence"}
        if extra:
            problems.append(f"pick[{i}] unknown keys: {sorted(extra)}")
        cid = pick.get("candidate_id")
        if cid not in candidate_ids:
            problems.append(f"pick[{i}].candidate_id not in enumerated packet IDs")
        elif cid in seen_ids:
            problems.append(f"pick[{i}].candidate_id duplicates an earlier pick")
        else:
            seen_ids.add(cid)
        if pick.get("reason") not in REASON_CODES:
            problems.append(f"pick[{i}].reason not in the fixed taxonomy")
        if pick.get("confidence") not in CONFIDENCE:
            problems.append(f"pick[{i}].confidence not in {CONFIDENCE}")
    return problems


def canonical_verdict_json(verdict: Dict[str, Any]) -> str:
    """One wire form per semantic verdict: rank order preserved (it is
    semantic), keys sorted, separators fixed."""
    return json.dumps(verdict, sort_keys=True, separators=(",", ":"))


def outcome_symbol(code: str) -> str:
    if code not in OUTCOME_CODES:
        raise ValueError(
            f"outcome {code!r} is not enumerated — an un-enumerated outcome "
            "is an unmetered side channel, and it is a bug"
        )
    return code
