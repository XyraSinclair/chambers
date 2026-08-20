"""charge-views/1 — interpretation out of the timeless fold (VIEWS-SPEC.md).

A view is a PURE function (fold bytes, policy bytes) -> report | refusal.
No ledger events, no new kinds, no imports from ledger.py: this is a
derived layer over the fold a verifier already recomputes from bytes.

The delegation it implements: charge-ledger/1's embedded `leakage_class`
and `incident` are henceforth DEFINED as this view applied with
LEGACY_DEFAULT_POLICY — provable bit-for-bit over every frozen corpus
(the parity law, VIEWS-SPEC §V.5; pinned by test_views.py against the
frozen expected.json bytes, not against the reference implementation).

All-or-nothing discipline (the F1 lesson): a malformed policy (W1) or a
malformed fold input (W2) refuses the ENTIRE view. No partial reports.

Integer-only: cross-multiplication, no division, no floats anywhere.
"""
from __future__ import annotations

import hashlib
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from events import canonical_json, is_uint as _is_uint

SPEC = "charge-views/1"

# The legacy-default policy: byte-for-byte the boundaries of
# egress-accountant/1 §1.5 and charge-ledger/1 §3.2's 800‰ incident line.
# `domains: None` = every key (the legacy fold labels every account —
# including the attention keys where the label is void in meaning; that
# is exactly the behavior the parity law must reproduce).
LEGACY_DEFAULT_POLICY: Dict[str, Any] = {
    "spec": SPEC,
    "name": "legacy-default",
    "domains": None,
    "classes": [
        {"label": "negligible", "max_permille": 50},
        {"label": "bounded", "max_permille": 250},
        {"label": "material", "max_permille": 500},
        {"label": "unsafe", "max_permille": 800},
    ],
    "terminal_label": "reconstructed",
    "incident_permille": 800,
}

_POLICY_FIELDS = {
    "spec", "name", "domains", "classes", "terminal_label", "incident_permille",
}


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("ascii")).hexdigest()


def policy_sha256(policy: Dict[str, Any]) -> str:
    """Content id of a policy: sha256 hex of its canonical bytes."""
    return _sha256_hex(canonical_json(policy))


def policy_admissible(policy: Any) -> bool:
    """VIEWS-SPEC §V.2. Any failure -> the whole view refuses (W1)."""
    if not isinstance(policy, dict):
        return False
    if set(policy.keys()) != _POLICY_FIELDS:
        return False
    if policy["spec"] != SPEC:
        return False
    if not isinstance(policy["name"], str) or not policy["name"]:
        return False
    domains = policy["domains"]
    if domains is not None:
        if not isinstance(domains, list) or not domains:
            return False
        for prefix in domains:
            if not isinstance(prefix, list) or not prefix:
                return False
            if not all(isinstance(x, str) for x in prefix):
                return False
    classes = policy["classes"]
    if not isinstance(classes, list) or not classes:
        return False
    labels: List[str] = []
    prev: Optional[int] = None
    for c in classes:
        if not isinstance(c, dict) or set(c.keys()) != {"label", "max_permille"}:
            return False
        if not isinstance(c["label"], str) or not c["label"]:
            return False
        if not _is_uint(c["max_permille"]):
            return False
        if prev is not None and c["max_permille"] <= prev:
            return False  # strictly increasing — monotonicity is structural
        prev = c["max_permille"]
        labels.append(c["label"])
    terminal = policy["terminal_label"]
    if not isinstance(terminal, str) or not terminal:
        return False
    labels.append(terminal)
    if len(set(labels)) != len(labels):
        return False
    if "void" in labels:
        return False  # reserved output vocabulary (§V.4)
    if not _is_uint(policy["incident_permille"]):
        return False
    return True


def _fold_accounts(fold: Any) -> Optional[List[Dict[str, Any]]]:
    """VIEWS-SPEC §V.3 input well-formedness. None -> refuse whole view (W2)."""
    if not isinstance(fold, dict) or not isinstance(fold.get("accounts"), list):
        return None
    out: List[Dict[str, Any]] = []
    for acct in fold["accounts"]:
        if not isinstance(acct, dict):
            return None
        key = acct.get("key")
        if not isinstance(key, list) or not all(isinstance(x, str) for x in key):
            return None
        row = {"key": key}
        for f in ("cumulative_mbits", "demanded_mbits", "subject_entropy_mbits"):
            v = acct.get(f)
            if not _is_uint(v):
                return None
            row[f] = v
        out.append(row)
    return out


def _in_domain(key: List[str], domains: Optional[List[List[str]]]) -> bool:
    if domains is None:
        return True
    return any(key[: len(p)] == p for p in domains)


def _classify(cum: int, s: int, policy: Dict[str, Any]) -> str:
    """Exactly §1.5's arithmetic, generalized: cap the fraction at 1,
    integer cross-multiplication, first satisfied boundary wins."""
    c = min(cum, s)
    for cls in policy["classes"]:
        if c * 1000 <= cls["max_permille"] * s:
            return cls["label"]
    return policy["terminal_label"]


def view(fold: Any, policy: Any) -> Dict[str, Any]:
    """The charge-views/1 computation. Returns the report dict, or the
    refusal dict {"spec": ..., "refused": [...]} — never a partial."""
    refused: List[str] = []
    if not policy_admissible(policy):
        # The subject hashes whatever bytes were offered as a policy —
        # a refusal must still name its evidence.
        try:
            phash = policy_sha256(policy)
        except (TypeError, ValueError):
            phash = _sha256_hex(repr(policy))
        refused.append("W1 sha256:" + phash)
    accounts = _fold_accounts(fold)
    if accounts is None:
        try:
            fhash = _sha256_hex(canonical_json(fold))
        except (TypeError, ValueError):
            fhash = _sha256_hex(repr(fold))
        refused.append("W2 sha256:" + fhash)
    if refused:
        return {"spec": SPEC, "refused": sorted(set(refused))}

    rows: List[Dict[str, Any]] = []
    for acct in accounts:
        key = acct["key"]
        cum = acct["cumulative_mbits"]
        dem = acct["demanded_mbits"]
        s = acct["subject_entropy_mbits"]
        if _in_domain(key, policy["domains"]):
            cls: Any = _classify(cum, s, policy)
            incident: Any = dem * 1000 >= policy["incident_permille"] * s
        else:
            cls = "void"
            incident = None
        rows.append(
            {
                "key": key,
                "class": cls,
                "incident": incident,
                "cumulative_mbits": cum,
                "demanded_mbits": dem,
                "subject_entropy_mbits": s,
            }
        )
    rows.sort(key=lambda r: canonical_json(r["key"]))  # fold order: canonical key bytes ascending
    return {
        "spec": SPEC,
        "policy_name": policy["name"],
        "policy_sha256": policy_sha256(policy),
        "accounts": rows,
    }


def view_bytes(fold: Any, policy: Any) -> str:
    """Canonical serialization of the report or refusal (§V.4)."""
    return canonical_json(view(fold, policy))
