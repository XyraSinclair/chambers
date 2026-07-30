"""charge-scope/1 — reader-scoped views with transparency-log proofs
(SCOPE-SPEC.md; FRAMEWORKS F2 imported for E2).

The node used to serve the whole artifact to anyone — "point it at
courts, not secrets" was a warning. This module makes scoping a
mechanism with theorems behind it (Merkle/CT membership and consistency
proofs; SUNDR-style fork detectability):

  * SET ROOT — an RFC6962-shaped Merkle tree over the id-sorted event
    ids (the canonical artifact order). Jobs: cross-node convergence
    checking (federation is merge; equal sets ⟺ equal roots) and
    per-event MEMBERSHIP proofs for scoped views. Recomputable by any
    stranger from the artifact bytes alone — ids are already content
    hashes, so committing to ids commits to bytes.
  * INGESTION LOG — the node's own append-only serving history (event
    ids in first-adoption order), same tree shape. Job: CONSISTENCY
    proofs — a reader who remembers yesterday's head can demand proof
    that today's court extends it; a node that rewrites or forks its
    serving history cannot produce one (fork consistency: two readers
    comparing heads detect equivocation).
  * SCOPE CLOSURE — the deterministic "touches" rule mapping a key set
    to the events a scoped reader is served, extending the S4 vocabulary
    the settlement audit already uses.

What this deliberately does NOT claim (SCOPE-SPEC §5): heads are
UNSIGNED (binding a head to a node identity is L5, like every identity
here); a scoped response proves everything served IS in the court, not
that nothing in-scope was withheld — but the kernel's own fact-identity
discipline makes silent omission leave arithmetic gaps (charge_seq and
issuer seq are dense), and verify_scope reports those gaps.
"""
from __future__ import annotations

import bisect
import hashlib
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from events import canonical_json, event_id
from ledger import Ledger

# ---- RFC 6962-shaped hashing (domain-separated) ----

def _leaf_hash(data: str) -> bytes:
    return hashlib.sha256(b"\x00" + data.encode("ascii")).digest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def _largest_pow2_lt(n: int) -> int:
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def merkle_root(items: Sequence[str]) -> str:
    """MTH over the item list (RFC 6962 §2.1). Empty tree = sha256("")."""
    def mth(lo: int, hi: int) -> bytes:
        n = hi - lo
        if n == 0:
            return hashlib.sha256(b"").digest()
        if n == 1:
            return _leaf_hash(items[lo])
        k = _largest_pow2_lt(n)
        return _node_hash(mth(lo, lo + k), mth(lo + k, hi))
    return mth(0, len(items)).hex()


def inclusion_proof(items: Sequence[str], index: int) -> List[str]:
    """Audit path for items[index] (RFC 6962 §2.1.1), hex-encoded."""
    def path(m: int, lo: int, hi: int) -> List[bytes]:
        n = hi - lo
        if n <= 1:
            return []
        k = _largest_pow2_lt(n)
        def mth(a: int, b: int) -> bytes:
            nn = b - a
            if nn == 1:
                return _leaf_hash(items[a])
            kk = _largest_pow2_lt(nn)
            return _node_hash(mth(a, a + kk), mth(a + kk, b))
        if m < k:
            return path(m, lo, lo + k) + [mth(lo + k, hi)]
        return path(m - k, lo + k, hi) + [mth(lo, lo + k)]
    return [h.hex() for h in path(index, 0, len(items))]


def verify_inclusion(item: str, index: int, tree_size: int,
                     proof: Sequence[str], root: str) -> bool:
    """RFC 9162 §2.1.3.2, exactly."""
    if not (0 <= index < tree_size):
        return False
    fn, sn = index, tree_size - 1
    try:
        path = [bytes.fromhex(p) for p in proof]
    except (ValueError, TypeError):
        return False
    r = _leaf_hash(item)
    for p in path:
        if sn == 0:
            return False
        if (fn & 1) == 1 or fn == sn:
            r = _node_hash(p, r)
            if (fn & 1) == 0:
                while (fn & 1) == 0 and fn != 0:
                    fn >>= 1
                    sn >>= 1
        else:
            r = _node_hash(r, p)
        fn >>= 1
        sn >>= 1
    return sn == 0 and r.hex() == root


def consistency_proof(items: Sequence[str], first: int) -> List[str]:
    """RFC 6962 §2.1.2 PROOF(first, D[n]) with n = len(items)."""
    n = len(items)
    if not (0 < first <= n):
        raise ValueError("first must be in 1..len(items)")
    if first == n:
        return []

    def mth(a: int, b: int) -> bytes:
        nn = b - a
        if nn == 1:
            return _leaf_hash(items[a])
        kk = _largest_pow2_lt(nn)
        return _node_hash(mth(a, a + kk), mth(a + kk, b))

    def subproof(m: int, lo: int, hi: int, b: bool) -> List[bytes]:
        nn = hi - lo
        if m == nn:
            return [] if b else [mth(lo, hi)]
        k = _largest_pow2_lt(nn)
        if m <= k:
            return subproof(m, lo, lo + k, b) + [mth(lo + k, hi)]
        return subproof(m - k, lo + k, hi, False) + [mth(lo, lo + k)]

    return [h.hex() for h in subproof(first, 0, n, True)]


def verify_consistency(first: int, second: int, first_root: str,
                       second_root: str, proof: Sequence[str]) -> bool:
    """RFC 9162 §2.1.4.2, exactly."""
    if first == second:
        return first_root == second_root and not proof
    if not (0 < first < second):
        return False
    try:
        path = [bytes.fromhex(p) for p in proof]
    except (ValueError, TypeError):
        return False
    # If first is an exact power of 2, prepend first_root.
    if first & (first - 1) == 0:
        try:
            path = [bytes.fromhex(first_root)] + path
        except (ValueError, TypeError):
            return False
    if not path:
        return False
    fn, sn = first - 1, second - 1
    while fn & 1:
        fn >>= 1
        sn >>= 1
    fr = sr = path[0]
    for c in path[1:]:
        if sn == 0:
            return False
        if (fn & 1) == 1 or fn == sn:
            fr = _node_hash(c, fr)
            sr = _node_hash(c, sr)
            if (fn & 1) == 0:
                while (fn & 1) == 0 and fn != 0:
                    fn >>= 1
                    sn >>= 1
        else:
            sr = _node_hash(sr, c)
        fn >>= 1
        sn >>= 1
    return sn == 0 and fr.hex() == first_root and sr.hex() == second_root


# ---- heads ----

def set_head(ledger: Ledger) -> Dict[str, Any]:
    """The set commitment: tree over id-sorted event ids."""
    ids = sorted(getattr(ledger, "_events").keys())
    return {"tree_size": len(ids), "set_root": merkle_root(ids)}


# ---- the scope closure (SCOPE-SPEC §2) ----

def _key_of(p: Dict[str, Any]) -> Optional[Tuple[str, ...]]:
    k = p.get("key")
    if isinstance(k, list) and all(isinstance(s, str) for s in k):
        return tuple(k)
    return None


def scope_closure(events: Dict[str, Dict[str, Any]],
                  keys: Iterable[Sequence[str]]) -> List[str]:
    """The deterministic 'touches' closure for a key set K, extending the
    S4 vocabulary. Returns id-sorted event ids.

      L0  register/lease/charge whose key ∈ K
      L1  escrows with any charge_key ∈ K
      L2  release/refund/default_resolution/outcome_attestation whose
          escrow_id ∈ L1
      L3  bond_resolution whose attestation_id ∈ L2
      REF events referenced by in-scope charge_ids / attestation_ids
          (present-in-court only), so in-scope conviction arms are
          recomputable — a referenced off-key charge arrives carrying
          its own key; the reader sees exactly why S3 convicts.

    Deposits are EXCLUDED by design: a scoped reader gets the flow bound
    to its keys, not any account's total wealth (SCOPE-SPEC §5)."""
    K: Set[Tuple[str, ...]] = {tuple(k) for k in keys}
    out: Set[str] = set()
    escrow_ids: Set[str] = set()
    attestation_ids: Set[str] = set()
    ref_ids: Set[str] = set()

    for eid, p in events.items():
        kind = p.get("kind")
        if kind in ("register", "lease", "charge") and _key_of(p) in K:
            out.add(eid)
        elif kind == "escrow":
            cks = p.get("charge_keys")
            if isinstance(cks, list) and any(
                isinstance(k, list) and tuple(k) in K for k in cks
            ):
                out.add(eid)
                escrow_ids.add(eid)

    for eid, p in events.items():
        kind = p.get("kind")
        if kind in ("release", "refund", "default_resolution",
                    "outcome_attestation") and p.get("escrow_id") in escrow_ids:
            out.add(eid)
            if kind == "outcome_attestation":
                attestation_ids.add(eid)
            for cid in (p.get("charge_ids") or []):
                if isinstance(cid, str):
                    ref_ids.add(cid)
            for aid in (p.get("attestation_ids") or []):
                if isinstance(aid, str):
                    ref_ids.add(aid)

    for eid, p in events.items():
        if p.get("kind") == "bond_resolution" and p.get("attestation_id") in attestation_ids:
            out.add(eid)

    for rid in ref_ids:
        if rid in events:
            out.add(rid)

    return sorted(out)


def scope_response(ledger: Ledger, keys: Sequence[Sequence[str]]) -> Dict[str, Any]:
    """Build the served scope: in-scope events + membership proofs against
    the set head. The head commits to the WHOLE court; proofs bind each
    served event to it."""
    events = getattr(ledger, "_events")
    all_ids = sorted(events.keys())
    head = {"tree_size": len(all_ids), "set_root": merkle_root(all_ids)}
    in_scope = scope_closure(events, keys)
    proofs = {}
    for eid in in_scope:
        idx = bisect.bisect_left(all_ids, eid)
        proofs[eid] = {"index": idx,
                       "path": inclusion_proof(all_ids, idx)}
    return {
        "head": head,
        "keys": [list(k) for k in keys],
        "events": [events[eid] for eid in in_scope],  # id-sorted order
        "proofs": proofs,
    }


# ---- the scoped reader's verifier (SCOPE-SPEC §4) ----

def verify_scope(response: Dict[str, Any]) -> List[str]:
    """Everything a scoped reader can check from the response alone.
    Returns problems (empty = verified). Checks:

      1. every served event's id recomputes from its canonical bytes;
      2. every served event carries a valid membership proof against the
         head (so everything served IS in the committed court);
      3. every served event is actually in the claimed scope closure
         (the server cannot pad the view with off-scope facts);
      4. omission evidence: within the scope, per-lease charge_seq and
         per-(actor, kind) settlement seq values are dense 1..max —
         a gap is a hole the server must explain (SCOPE-SPEC §5: this
         is evidence, not proof, of withholding).
    """
    problems: List[str] = []
    head = response.get("head") or {}
    tree_size = head.get("tree_size")
    set_root = head.get("set_root")
    events_list = response.get("events") or []
    proofs = response.get("proofs") or {}
    keys = [tuple(k) for k in (response.get("keys") or [])]

    served: Dict[str, Dict[str, Any]] = {}
    for p in events_list:
        eid = event_id(p)
        served[eid] = p
        pr = proofs.get(eid)
        if not isinstance(pr, dict):
            problems.append(f"no membership proof for {eid}")
            continue
        if not verify_inclusion(eid, pr.get("index", -1), tree_size,
                                pr.get("path", []), set_root):
            problems.append(f"membership proof FAILED for {eid}")

    # 3 — the served set must be exactly the closure of K over itself
    # (a padded off-scope event would not be reproduced by the closure).
    expected = set(scope_closure(served, keys))
    extra = set(served) - expected
    for eid in sorted(extra):
        problems.append(f"off-scope event served: {eid}")

    # 4 — seq density (omission evidence).
    charge_seqs: Dict[str, List[int]] = {}
    actor_seqs: Dict[Tuple[str, str], List[int]] = {}
    for eid, p in served.items():
        kind = p.get("kind")
        if kind == "charge":
            s = p.get("charge_seq")
            if isinstance(s, int) and not isinstance(s, bool):
                charge_seqs.setdefault(str(p.get("lease_id")), []).append(s)
        elif kind in ("release", "refund", "escrow", "default_resolution",
                      "outcome_attestation", "bond_resolution"):
            actor_field = {"default_resolution": "submitter",
                           "bond_resolution": "submitter",
                           "outcome_attestation": "attestor"}.get(kind, "issuer")
            s = p.get("seq")
            if isinstance(s, int) and not isinstance(s, bool):
                actor_seqs.setdefault(
                    (str(p.get(actor_field)), str(kind)), []).append(s)
    for lease_id, seqs in sorted(charge_seqs.items()):
        missing = sorted(set(range(1, max(seqs) + 1)) - set(seqs))
        if missing:
            problems.append(
                f"charge_seq gap on lease {lease_id}: missing {missing} "
                f"(withheld or never served — demand an explanation)")
    for (actor, kind), seqs in sorted(actor_seqs.items()):
        missing = sorted(set(range(1, max(seqs) + 1)) - set(seqs))
        if missing:
            # settlement seqs are per (actor, kind) across ALL keys; a gap
            # may be out-of-scope activity — report as a note, not a hole.
            problems.append(
                f"note: {kind} seq gap for {actor!r}: {missing} "
                f"(may be out-of-scope activity by the same actor)")

    return problems


def scope_is_verified(response: Dict[str, Any]) -> bool:
    """True iff verify_scope finds no HARD problems (notes allowed)."""
    return all(p.startswith("note:") for p in verify_scope(response))
