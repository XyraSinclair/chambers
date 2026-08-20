"""The mergeable ledger of charge-kernel/2.

A Ledger is a grow-only map from event id to event payload. Merge is set
union with a byte-equality conflict check — which makes merge idempotent,
commutative, and associative (a CRDT join), so any gossip/replication order
converges to the same state. The global account view is a deterministic FOLD
over the merged set: plain integer sums of per-event monotone contributions.

What the fold answers (per key):
  - global cumulative accepted mbits (sum of debit_mbits)
  - global demanded mbits (sum of demand_mbits)
  - global leakage class (monotone: merging can only escalate it)
  - global incident (monotone: demanded only grows)
  - lease discipline: sum of granted lease amounts vs the registered ceiling

The fold is TOTAL. It never raises on adversarial content. A Byzantine node
that injects a conflicting registration for a key must not be able to crash
every auditor forever (a one-event denial-of-audit); instead the fold
resolves conflicting registrations CONSERVATIVELY — minimum entropy, minimum
ceiling over the well-formed candidates — and marks the account `conflicted`.
Both minima move severity monotonically under union (smaller entropy can only
escalate the class and the incident; smaller ceiling can only create
over-grant/over-spend findings), so quarantine preserves the honest
direction: merge escalates, never retracts. `audit()` reports the conflict
as a finding (I7) rather than dying on it.

What the fold NEVER does: re-decide. ChargeEvents are final local decisions
made against leases; the fold is bookkeeping over facts, not a replay of
control flow. The global cap theorem needs no fold at all — it holds by lease
partition (see LeaseEvent docstring) — but the fold VERIFIES it, and
`audit()` returns the violations if any implementation lied.

Wire format: `to_jsonl()` / `from_jsonl()` — one canonical-JSON payload per
line, sorted by event id, so a ledger IS a byte-deterministic gossipable
artifact and `from_jsonl(a.to_jsonl())` is the identity.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from accountant import Key, UNSAFE_PERMILLE, leakage_class
from events import (
    ChargeEvent,
    DerivationEvent,
    LeaseEvent,
    RegisterEvent,
    canonical_json,
    event_id,
    is_uint as _is_uint,
)


class MergeConflict(Exception):
    """Same event id, different bytes — content addressing was violated."""


# reason classes a well-formed ChargeEvent may carry (SPEC 2.3 + the kernel's
# coupled extension), with the demand/debit profile each one implies.
# A TUPLE, deliberately: membership tests against a set HASH the probe
# value, so a forged charge with an unhashable reason_class (list/dict)
# crashed audit_codes() and everything joined to the court stream — a
# one-event denial-of-audit (fable review blocking finding, 2026-07-06).
# Tuple membership compares by ==, total over any payload value, and the
# verdict bytes are identical (a non-string reason still convicts I6).
_CHARGE_REASONS = (
    "EMITTED",
    "REFUSED_ESTIMATOR",
    "REFUSED_BLOCKED",
    "REFUSED_CEILING",
    "REFUSED_COUPLED",
)


@dataclass
class GlobalAccount:
    key: Key
    subject_entropy_mbits: int
    ceiling_mbits: int
    cumulative_mbits: int
    demanded_mbits: int
    granted_lease_mbits: int
    leakage_class: str
    incident: bool
    conflicted: bool = False  # conflicting registrations were quarantined (I7)


@dataclass(frozen=True)
class LeaseUsage:
    """Replay of every charge bound to one lease — what an honest node MUST
    hydrate before spending that lease again (session.py and meter.py do).
    Without this, a restarted node re-runs a fresh accountant from zero and
    the API itself walks an honest node into an I3 violation."""

    spent_mbits: int
    demanded_mbits: int
    ceiling_refusal_seen: bool  # a REFUSED_CEILING against this lease latched it
    max_charge_seq: int

    def hydrate(self, state, lease_amount_mbits: int, entropy_mbits: int) -> int:
        """Apply this replay to a freshly-registered AccountState whose
        ceiling is the lease amount. Returns the next charge_seq. The one
        canonical hydration — session.py and meter.py both call it."""
        state.cumulative_mbits = self.spent_mbits
        state.demanded_mbits = self.demanded_mbits
        state.blocked = self.ceiling_refusal_seen or self.spent_mbits >= lease_amount_mbits
        state.incident = self.demanded_mbits * 1000 >= UNSAFE_PERMILLE * entropy_mbits
        return self.max_charge_seq + 1


def _hashable_key(payload: Dict[str, Any]) -> Optional[Key]:
    """The event's account key as a hashable tuple of strings, or None if
    absent or malformed. Every site that GROUPS BY or DICT-KEYS ON a key
    must go through this — a single forged event with a missing key, a
    non-list key, or a nested-list key would otherwise raise
    (KeyError/TypeError: unhashable) and take down the whole fold, the
    one-event denial-of-audit the total-fold discipline forbids. A
    malformed key forms no account; the event is convicted elsewhere."""
    k = payload.get("key")
    if isinstance(k, list) and all(isinstance(s, str) for s in k):
        return tuple(k)
    return None


def _dpi_maxflow(
    source: str,
    sink_fact: str,
    anchors: "set[str]",
    derivations: "List[Tuple[str, Dict[str, Any]]]",
    unbounded_cap: int,
) -> int:
    """Integer max-flow for the DPI bound (KERNEL-SPEC Part III P.4).

    Network: one node per fact id; each derivation is a split node whose
    internal capacity is its declared `hop_capacity_mbits` (non-uint =
    unbounded — malforming a declaration must never shrink an obligation);
    edges consumed-fact -> derivation -> derived-fact otherwise unbounded;
    a super-source feeds every anchor of `source`. Unbounded capacities
    are instantiated at `unbounded_cap` (the emission's declared capacity
    E): sound, because callers only ever use min(E, flow) — any cut made
    of instantiated edges already has capacity >= E. Edmonds-Karp; total
    on cyclic/adversarial graphs; integers only.
    """
    if unbounded_cap <= 0:
        return 0
    cap: Dict[Tuple[str, str], int] = {}

    def _add(u: str, v: str, c: int) -> None:
        cap[(u, v)] = cap.get((u, v), 0) + c
        cap.setdefault((v, u), 0)  # residual arc

    src = ("SRC",)  # unforgeable node names: tuples cannot collide with
    snk = ("F", sink_fact)  # adversarial fact-id strings

    def _fact(f: str):
        return ("F", f)

    for a in anchors:
        _add(src, _fact(a), unbounded_cap)  # type: ignore[arg-type]
    for deid, dp in derivations:
        hop = dp.get("hop_capacity_mbits")
        hop_cap = hop if _is_uint(hop) else unbounded_cap
        din, dout = ("DIN", deid), ("DOUT", deid)
        _add(din, dout, min(hop_cap, unbounded_cap))  # type: ignore[arg-type]
        derived = dp.get("derived")
        if isinstance(derived, str):
            _add(dout, _fact(derived), unbounded_cap)  # type: ignore[arg-type]
        consumed = dp.get("consumed")
        if isinstance(consumed, list):
            for c in consumed:
                if isinstance(c, str):
                    _add(_fact(c), din, unbounded_cap)  # type: ignore[arg-type]

    adj: Dict[Any, List[Any]] = {}
    for (u, v) in cap:
        adj.setdefault(u, []).append(v)

    flow = 0
    while flow < unbounded_cap:
        # BFS for a shortest augmenting path
        parent: Dict[Any, Any] = {src: src}
        queue = [src]
        while queue and snk not in parent:
            u = queue.pop(0)
            for v in adj.get(u, ()):
                if v not in parent and cap[(u, v)] > 0:
                    parent[v] = u
                    queue.append(v)
        if snk not in parent:
            break
        bottleneck = unbounded_cap - flow
        v = snk
        while v != src:
            u = parent[v]
            bottleneck = min(bottleneck, cap[(u, v)])
            v = u
        v = snk
        while v != src:
            u = parent[v]
            cap[(u, v)] -= bottleneck
            cap[(v, u)] += bottleneck
            v = u
        flow += bottleneck
    return flow


def _exp_key(k: Any) -> Optional[Tuple[str, str, str]]:
    """A well-formed exposure triple ["exp", source, reader], or None.
    KERNEL-SPEC P.2's anchor test — shared by the P-audit and
    charge-attribution/1 so the two families cannot drift on what
    counts as a source."""
    if (isinstance(k, list) and len(k) == 3
            and all(isinstance(x, str) for x in k) and k[0] == "exp"):
        return (k[0], k[1], k[2])
    return None


def _walk_closure(
    events: Dict[str, Dict[str, Any]],
    derivs_by_fact: Dict[str, List[Tuple[str, Dict[str, Any]]]],
    d: str,
) -> Tuple[Dict[str, set], List[Tuple[str, Dict[str, Any]]]]:
    """The provenance closure walk (KERNEL-SPEC P.2): anchored sources
    (source -> anchor fact ids) and the derivation edges reached from
    fact id `d`. One walk, two consumers — provenance_findings (P-codes)
    and attribution.py (V-codes) — no drift. Total: cycles terminate by
    visited-set; malformed consumed lists contribute nothing."""
    sources: Dict[str, set] = {}
    used: List[Tuple[str, Dict[str, Any]]] = []
    seen: set = set()
    stack = [d]
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        anchor = events.get(f)
        if anchor is not None:
            ek = _exp_key(anchor.get("key"))
            if ek is not None:
                sources.setdefault(ek[1], set()).add(f)
        for deid, dp in derivs_by_fact.get(f, ()):
            used.append((deid, dp))
            consumed = dp.get("consumed")
            if isinstance(consumed, list):
                for c in consumed:
                    if isinstance(c, str):
                        stack.append(c)
    return sources, used


class Ledger:
    def __init__(self) -> None:
        self._events: Dict[str, Dict[str, Any]] = {}

    # ---- ingestion ----

    def add(self, event: Any) -> str:
        """Ingest any content-addressed event object exposing .payload()
        and .id (RegisterEvent, LeaseEvent, ChargeEvent, DerivationEvent,
        settlement/covenant/identity/attribution kinds alike)."""
        payload = event.payload()
        eid = event.id
        self._add_payload(eid, payload)
        return eid

    def _add_payload(self, eid: str, payload: Dict[str, Any]) -> None:
        existing = self._events.get(eid)
        if existing is not None:
            if canonical_json(existing) != canonical_json(payload):
                raise MergeConflict(f"event id collision with differing bytes: {eid}")
            return  # idempotent
        self._events[eid] = payload

    # ---- CRDT merge ----

    def merge(self, other: "Ledger") -> "Ledger":
        """Union by id. Idempotent, commutative, associative."""
        for eid, payload in other._events.items():
            self._add_payload(eid, payload)
        return self

    def copy(self) -> "Ledger":
        out = Ledger()
        out._events = dict(self._events)
        return out

    def event_count(self) -> int:
        return len(self._events)

    def events(self) -> Iterable[Dict[str, Any]]:
        return self._events.values()

    # ---- wire format ----

    def to_jsonl(self) -> str:
        """Canonical serialization: one canonical-JSON payload per line,
        sorted by event id. Deterministic — equal ledgers give equal bytes."""
        lines = [
            canonical_json(payload)
            for _eid, payload in sorted(self._events.items())
        ]
        return "\n".join(lines) + ("\n" if lines else "")

    @classmethod
    def from_jsonl(cls, text: str) -> "Ledger":
        """Parse a jsonl artifact. Ids are recomputed from content (they are
        derived, never trusted), so a tampered line simply becomes a different
        event — and then fails the audit's referential checks."""
        out = cls()
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            out._add_payload(event_id(payload), payload)
        return out

    # ---- registration resolution (shared by fold and audit) ----

    def _resolve_registers(
        self,
    ) -> Tuple[Dict[Key, Dict[str, Any]], Dict[Key, bool], List[Tuple[str, str, str]]]:
        """Group registrations per key; resolve conflicts conservatively.

        Returns (resolved register-per-key, conflicted flag per key,
        malformed/irresolvable findings as (code, subject, prose) triples).
        Well-formed means entropy > 0 and ceiling >= 0 (both plain non-bool
        ints). Resolution over the well-formed candidates is field-wise
        MINIMUM — monotone escalation under union. Keys with no well-formed
        registration get no account.
        """
        groups: Dict[Key, List[Dict[str, Any]]] = {}
        unparseable: List[Tuple[str, Any]] = []
        for eid, payload in self._events.items():
            if payload.get("kind") == "register":
                gk = _hashable_key(payload)
                if gk is not None:
                    groups.setdefault(gk, []).append(payload)
                else:
                    unparseable.append((eid, payload.get("key")))

        resolved: Dict[Key, Dict[str, Any]] = {}
        conflicted: Dict[Key, bool] = {}
        findings: List[Tuple[str, str, str]] = []
        # A register whose key cannot parse forms no account — but it is
        # CONVICTED, not silently neutralized (the register discipline:
        # named, never dropped). Subject is the canonical JSON of the raw
        # key value, which is always serializable (the payload entered the
        # ledger through canonical_json) and can never collide with a real
        # key's subject in a harmful way (_touches simply never matches it).
        for eid, raw_key in unparseable:
            findings.append(
                ("I7", canonical_json(raw_key),
                 f"I7 unparseable key in registration {eid}")
            )
        for key, plist in groups.items():
            subj = canonical_json(list(key))
            well_formed = [
                p
                for p in plist
                if _is_uint(p.get("ceiling_mbits"))
                and isinstance(p.get("subject_entropy_mbits"), int)
                and not isinstance(p.get("subject_entropy_mbits"), bool)
                and p["subject_entropy_mbits"] > 0
            ]
            for p in plist:
                if p not in well_formed:
                    findings.append(("I7", subj, f"I7 malformed registration for key {key}"))
            if not well_formed:
                findings.append(("I7", subj, f"I7 no well-formed registration for key {key}"))
                continue
            distinct = {canonical_json(p) for p in well_formed}
            is_conflict = len(distinct) > 1
            if is_conflict:
                findings.append(
                    (
                        "I7",
                        subj,
                        f"I7 conflicting registrations for key {key} "
                        f"(resolved to min entropy/ceiling)",
                    )
                )
            resolved[key] = {
                "key": list(key),
                "subject_entropy_mbits": min(p["subject_entropy_mbits"] for p in well_formed),
                "ceiling_mbits": min(p["ceiling_mbits"] for p in well_formed),
                # issuer set is needed for I5. KERNEL-SPEC §3.1: only STRING
                # issuers contribute — a register with a missing or non-string
                # issuer is still well-formed but adds nothing here. (Before
                # this filter, a non-string issuer entered the set raw: two
                # forged registers could crash the auditor on a mixed-type
                # sort, and a forged lease with the same non-string issuer
                # would evade I5. Caught by spec-ambiguity-issuer.)
                "_issuers": sorted(
                    {
                        p["issuer"]
                        for p in well_formed
                        if isinstance(p.get("issuer"), str)
                    }
                ),
            }
            conflicted[key] = is_conflict or len(well_formed) != len(plist)
        return resolved, conflicted, findings

    # ---- deterministic fold ----

    def fold(self) -> Dict[Key, GlobalAccount]:
        resolved, conflicted, _findings = self._resolve_registers()

        accounts: Dict[Key, GlobalAccount] = {}
        for key, reg in resolved.items():
            accounts[key] = GlobalAccount(
                key=key,
                subject_entropy_mbits=reg["subject_entropy_mbits"],
                ceiling_mbits=reg["ceiling_mbits"],
                cumulative_mbits=0,
                demanded_mbits=0,
                granted_lease_mbits=0,
                leakage_class="negligible",
                incident=False,
                conflicted=conflicted[key],
            )

        for payload in self._events.values():
            kind = payload.get("kind")
            if kind == "lease":
                key = _hashable_key(payload)
                if key is not None and key in accounts and _is_uint(payload.get("amount_mbits")):
                    accounts[key].granted_lease_mbits += payload["amount_mbits"]
            elif kind == "charge":
                key = _hashable_key(payload)
                if key is not None and key in accounts:
                    if _is_uint(payload.get("debit_mbits")):
                        accounts[key].cumulative_mbits += payload["debit_mbits"]
                    if _is_uint(payload.get("demand_mbits")):
                        accounts[key].demanded_mbits += payload["demand_mbits"]

        for acct in accounts.values():
            acct.leakage_class = leakage_class(acct.cumulative_mbits, acct.subject_entropy_mbits)
            acct.incident = (
                acct.demanded_mbits * 1000 >= UNSAFE_PERMILLE * acct.subject_entropy_mbits
            )
        return accounts

    # ---- lease replay (honest-node hydration) ----

    def lease_usage(self, lease_id: str) -> LeaseUsage:
        spent = 0
        demanded = 0
        latched = False
        max_seq = 0
        for payload in self._events.values():
            if payload.get("kind") != "charge" or payload.get("lease_id") != lease_id:
                continue
            if _is_uint(payload.get("debit_mbits")):
                spent += payload["debit_mbits"]
            if _is_uint(payload.get("demand_mbits")):
                demanded += payload["demand_mbits"]
            if payload.get("reason_class") == "REFUSED_CEILING":
                latched = True
            seq = payload.get("charge_seq")
            if _is_uint(seq):
                max_seq = max(max_seq, seq)
        return LeaseUsage(
            spent_mbits=spent,
            demanded_mbits=demanded,
            ceiling_refusal_seen=latched,
            max_charge_seq=max_seq,
        )

    # ---- audit ----

    def audit(self) -> List[str]:
        """Human-facing audit: prose findings, empty list = clean."""
        return [prose for _code, _subj, prose in self.audit_findings()]

    def audit_codes(self) -> List[str]:
        """CONFORMANCE surface: the canonical, language-reproducible audit
        verdict. Each finding reduces to `"<code> <subject>"` where the
        subject is a canonical identifier (event id for charges/leases,
        canonical-JSON key for account-level findings, canonical-JSON
        [node, lease_id, seq] for equivocations). Returned sorted and
        deduplicated — two implementations of KERNEL-SPEC must agree on this
        list byte-for-byte."""
        return sorted({f"{code} {subj}" for code, subj, _prose in self.audit_findings()})

    # ---- the substrate law (charge-substrate/1, KERNEL-SPEC Part II) ----

    #: The authoring-field priority, a substrate law: every event kind
    #: that carries a `seq` MUST name its author in one of these fields;
    #: the FIRST present string is the actor. Existing kinds already
    #: comply (issuer for deposit/escrow/release/refund and leases,
    #: submitter for default_resolution/bond_resolution, attestor for
    #: outcome_attestation); future kinds inherit the law by using them.
    AUTHORING_FIELDS = ("issuer", "submitter", "attestor")

    def substrate_findings(self) -> List[Tuple[str, str, str]]:
        """X0 — fact identity at the substrate, for ALL kinds including
        kinds this auditor does not understand (E6; design consult (2026-07-05, private)
        §5). The same-bytes-≠-same-fact lesson was learned separately by
        charge_seq (I8) and settlement seq (S5); X0 is that law promoted
        to genesis: two events with different ids claiming the same
        (actor, kind, seq) — seq a uint, actor the first authoring field
        present — are an equivocation, whatever their kind. I8 and S5
        become instances; a future kind gets equivocation detection for
        free the moment it carries (author, seq).

        Deliberately a SEPARATE surface from audit_findings(): the /1
        conformance corpora bind byte-for-byte to audit_codes() and the
        settlement s_codes; X0 extends the verdict without moving
        anything frozen."""
        findings: List[Tuple[str, str, str]] = []
        seen: Dict[Tuple[str, str, int], str] = {}
        for eid, p in self._events.items():
            seq = p.get("seq")
            if not _is_uint(seq):
                continue
            kind = p.get("kind")
            if not isinstance(kind, str):
                continue
            actor = next(
                (p[f] for f in self.AUTHORING_FIELDS if isinstance(p.get(f), str)),
                None,
            )
            if actor is None:
                continue
            ident = (actor, kind, seq)
            prior = seen.get(ident)
            if prior is not None and prior != eid:
                findings.append((
                    "X0", canonical_json(list(ident)),
                    f"X0 substrate equivocation: two facts claim {ident}",
                ))
            seen[ident] = eid
        return findings

    def substrate_codes(self) -> List[str]:
        """Conformance surface for X0: sorted, deduplicated
        '<code> <subject>' strings, same discipline as audit_codes()."""
        return sorted({f"{c} {s}" for c, s, _ in self.substrate_findings()})

    # ---- charge-provenance/1 (KERNEL-SPEC Part III): P-codes ----

    #: an EMITTED charge declares WHICH derived fact it emits by carrying
    #: the fact's content id in its channel, behind this prefix.
    DERIVED_CHANNEL_PREFIX = "derived:"

    def provenance_findings(self) -> List[Tuple[str, str, str]]:
        """P1/P2/P3 — closure charging (G16; KERNEL-SPEC Part III).

        The law: an emission of a derived fact charges the fact's
        TRANSITIVE ancestry, in the same coupling, at the DPI bound the
        declared hop capacities imply. Depth is not dilution — a source
        three derivation hops behind the emitted fact is charged exactly
        as if it were one hop behind, and dropping it convicts (P1).

        Deliberately a SEPARATE surface (`p_codes`), like X0: the frozen
        corpora bind to audit_codes()/s_codes and carry no derivation
        events and no provenance channels, so their verdicts are
        byte-identical. Total: never raises on adversarial content.
        Integer-only. Findings are functions of the event set — merge
        order and jsonl round-trips cannot move them.
        """
        findings: List[Tuple[str, str, str]] = []
        events = self._events

        # index derivations; fast exit for provenance-free artifacts
        derivs_by_fact: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
        deriv_events: List[Tuple[str, Dict[str, Any]]] = []
        for eid, p in events.items():
            if p.get("kind") == "derivation":
                deriv_events.append((eid, p))
                d = p.get("derived")
                if isinstance(d, str):
                    derivs_by_fact.setdefault(d, []).append((eid, p))
        prefix = self.DERIVED_CHANNEL_PREFIX

        # ---- P3 — orphaned derivation (ancestry that cannot be walked) ----
        derived_facts = set(derivs_by_fact)
        for eid, p in deriv_events:
            consumed = p.get("consumed")
            if not isinstance(consumed, list):
                findings.append(
                    ("P3", eid, f"P3 derivation {eid} has no consumed list")
                )
                continue
            for c in consumed:  # empty list = legal root claim, inert
                if not (isinstance(c, str) and (c in events or c in derived_facts)):
                    findings.append(
                        ("P3", eid,
                         f"P3 derivation {eid} consumes unresolvable id {c!r} "
                         f"(no event, no derived fact, no tombstone)")
                    )
                    break

        # ---- emission couplings: EMITTED charges declaring a derived fact,
        # grouped by the fields every charge_coupled sibling shares ----
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for _eid, p in events.items():
            if p.get("kind") != "charge" or p.get("reason_class") != "EMITTED":
                continue
            ch = p.get("channel")
            if not (isinstance(ch, str) and ch.startswith(prefix)):
                continue
            gk = json.dumps(
                [p.get("node"), p.get("tick"), ch],
                sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            )
            groups.setdefault(gk, []).append(p)
        if not groups:
            return findings

        # closure(d): sources + the derivation edges reached, cached per fact
        closure_cache: Dict[str, Tuple[Dict[str, set], List[Tuple[str, Dict[str, Any]]]]] = {}

        def _closure(d: str) -> Tuple[Dict[str, set], List[Tuple[str, Dict[str, Any]]]]:
            hit = closure_cache.get(d)
            if hit is not None:
                return hit
            out = _walk_closure(events, derivs_by_fact, d)
            closure_cache[d] = out
            return out

        for gk in sorted(groups):
            charges = groups[gk]
            channel = charges[0]["channel"]  # shared by construction of gk
            d = channel[len(prefix):]
            exp_emissions = [p for p in charges if _exp_key(p.get("key"))]
            if not exp_emissions:
                continue  # non-claim 2: provenance charges the exp family only
            sources, used_derivs = _closure(d)
            if not sources:
                continue
            emission_cap = max(
                (p["estimate_total_mbits"] for p in exp_emissions
                 if _is_uint(p.get("estimate_total_mbits"))),
                default=0,
            )
            readers = sorted({_exp_key(p["key"])[2] for p in exp_emissions})
            for r in readers:
                for s in sorted(sources):
                    subj = canonical_json(["exp", s, r])
                    matched = [
                        p for p in exp_emissions
                        if _exp_key(p["key"]) == ("exp", s, r)
                    ]
                    if not matched:
                        findings.append(
                            ("P1", subj,
                             f"P1 dropped ancestor: emission of {d} toward "
                             f"{r!r} has no coupled charge on source {s!r}")
                        )
                        continue
                    paid = sum(
                        p["debit_mbits"] for p in matched
                        if _is_uint(p.get("debit_mbits"))
                    )
                    bound = min(
                        emission_cap,
                        _dpi_maxflow(s, d, sources[s], used_derivs, emission_cap),
                    )
                    if paid < bound:
                        findings.append(
                            ("P2", subj,
                             f"P2 closure undercount: {paid} mbits coupled "
                             f"toward source {s!r} < DPI bound {bound} for "
                             f"emission of {d}")
                        )
        return findings

    def provenance_codes(self) -> List[str]:
        """Conformance surface for the P-codes: sorted, deduplicated
        '<code> <subject>' strings, same discipline as audit_codes()."""
        return sorted({f"{c} {s}" for c, s, _ in self.provenance_findings()})

    def derivations_by_fact(self) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
        """Index of derivation events by their `derived` fact id —
        the same index provenance_findings builds; exposed for
        charge-attribution/1."""
        out: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
        for eid, p in self._events.items():
            if p.get("kind") == "derivation":
                d = p.get("derived")
                if isinstance(d, str):
                    out.setdefault(d, []).append((eid, p))
        return out

    def provenance_closure(
        self, d: str
    ) -> Tuple[Dict[str, set], List[Tuple[str, Dict[str, Any]]]]:
        """Public KERNEL-SPEC P.2 closure of fact id `d`: (anchored
        sources as source -> anchor fact ids, derivation edges reached).
        The exact walk the P-audit runs — charge-attribution/1's game is
        defined over this and nothing else."""
        return _walk_closure(self._events, self.derivations_by_fact(), d)

    def audit_findings(self) -> List[Tuple[str, str, str]]:
        """Verify the invariants the protocol claims. Empty list = clean.

        I1  per key: granted leases <= registered ceiling
        I2  per key: cumulative accepted <= registered ceiling
        I3  per lease: accepted debits against it <= its amount
        I4  every charge binds correctly to its lease: the lease exists, keys
            match, the charging node IS the leased node, and the charge tick
            does not exceed the lease's expiry tick (ticks are declared in
            the issuer's clock domain — a lie here is exactly what this catches)
        I5  every lease references a registered key, and its issuer is a
            registered issuer of that key
        I6  every charge is well-formed: non-negative integers; demand/debit
            consistent with its reason class (an EMITTED debit equals the
            estimate total; refusals debit 0; only REFUSED_ESTIMATOR demands 0);
            charge_seq >= 1
        I7  registrations are unique and well-formed per key (conflicts are
            quarantined by the fold, and reported here)
        I8  no equivocation: (node, lease_id, charge_seq) identifies at most
            one fact
        """
        findings: List[Tuple[str, str, str]] = []
        resolved, _conflicted, reg_findings = self._resolve_registers()
        findings.extend(reg_findings)
        accounts = self.fold()

        leases: Dict[str, Dict[str, Any]] = {}
        for payload in self._events.values():
            if payload.get("kind") == "lease":
                leases[event_id(payload)] = payload

        # I5 — lease -> registration binding.
        for lid, lease in leases.items():
            lkey = _hashable_key(lease)
            reg = resolved.get(lkey) if lkey is not None else None
            if reg is None:
                findings.append(("I5", lid, f"I5 lease {lid} references unregistered key {lkey}"))
            elif lease.get("issuer") not in reg["_issuers"]:
                findings.append(
                    (
                        "I5",
                        lid,
                        f"I5 lease {lid} issuer {lease.get('issuer')!r} is not a "
                        f"registered issuer of {lkey}",
                    )
                )

        # I1 / I2 — per-key ceilings.
        for key, acct in accounts.items():
            subj = canonical_json(list(key))
            if acct.granted_lease_mbits > acct.ceiling_mbits:
                findings.append(("I1", subj, f"I1 over-granted leases on {key}"))
            if acct.cumulative_mbits > acct.ceiling_mbits:
                findings.append(("I2", subj, f"I2 ceiling exceeded on {key}"))

        # I3 / I4 / I6 / I8 — per-charge checks.
        spent_per_lease: Dict[str, int] = {}
        seq_seen: Dict[Tuple[str, str, int], str] = {}
        for eid, payload in self._events.items():
            if payload.get("kind") != "charge":
                continue

            # I6 — well-formedness of the fact itself.
            demand = payload.get("demand_mbits")
            debit = payload.get("debit_mbits")
            total = payload.get("estimate_total_mbits")
            seq = payload.get("charge_seq")
            reason = payload.get("reason_class")
            ok = True
            if not (_is_uint(demand) and _is_uint(debit) and _is_uint(total)):
                findings.append(("I6", eid, f"I6 negative or non-integer millibits in charge {eid}"))
                ok = False
            if not _is_uint(seq) or (isinstance(seq, int) and seq < 1):
                findings.append(("I6", eid, f"I6 missing or invalid charge_seq in charge {eid}"))
                ok = False
            if reason not in _CHARGE_REASONS:
                findings.append(("I6", eid, f"I6 unknown reason_class {reason!r} in charge {eid}"))
                ok = False
            if ok:
                accepted = payload.get("accepted") is True
                if accepted != (reason == "EMITTED"):
                    findings.append(
                        ("I6", eid, f"I6 accepted flag disagrees with reason_class in {eid}")
                    )
                expected_debit = total if reason == "EMITTED" else 0
                expected_demand = 0 if reason == "REFUSED_ESTIMATOR" else total
                if debit != expected_debit:
                    findings.append(
                        ("I6", eid, f"I6 debit {debit} != {expected_debit} for {reason} in {eid}")
                    )
                if demand != expected_demand:
                    findings.append(
                        ("I6", eid, f"I6 demand {demand} != {expected_demand} for {reason} in {eid}")
                    )

            # I8 — equivocation on the fact identity. The dedup key is the
            # canonical-JSON of the identity (also the finding subject), so
            # a forged charge with an unhashable node/lease_id (list/dict)
            # cannot crash the total audit — it canonicalizes and either
            # equivocates or does not, like any other value.
            if _is_uint(seq):
                node = payload.get("node", "")
                lease_ref = payload.get("lease_id", "")
                ident = canonical_json([node, lease_ref, seq])
                prior = seq_seen.get(ident)
                if prior is not None and prior != eid:
                    findings.append(
                        (
                            "I8",
                            ident,
                            f"I8 equivocation: two charges claim node/lease/seq {ident}",
                        )
                    )
                seq_seen[ident] = eid

            # I4 — lease binding.
            lease_id = payload.get("lease_id")
            lease = leases.get(lease_id) if isinstance(lease_id, str) else None
            if lease is None:
                findings.append(("I4", eid, f"I4 charge references unknown lease {lease_id}"))
                continue
            l_key = _hashable_key(lease)
            if l_key is None or list(l_key) != payload.get("key"):
                findings.append(("I4", eid, f"I4 charge key differs from lease key ({lease_id})"))
            if payload.get("node") != lease.get("node"):
                findings.append(
                    (
                        "I4",
                        eid,
                        f"I4 charge by node {payload.get('node')!r} against lease "
                        f"held by {lease.get('node')!r} ({lease_id})",
                    )
                )
            tick = payload.get("tick")
            expires = lease.get("expires_tick")
            if (
                isinstance(tick, int)
                and not isinstance(tick, bool)
                and isinstance(expires, int)
                and not isinstance(expires, bool)
                and tick > expires
            ):
                findings.append(
                    ("I4", eid, f"I4 charge at tick {tick} after lease expiry {expires} ({lease_id})")
                )
            if _is_uint(debit):
                spent_per_lease[lease_id] = spent_per_lease.get(lease_id, 0) + debit

        # I3 — per-lease spend.
        for lease_id, spent in spent_per_lease.items():
            lease = leases.get(lease_id)
            if lease is not None and _is_uint(lease.get("amount_mbits")):
                if spent > lease["amount_mbits"]:
                    findings.append(("I3", lease_id, f"I3 lease overspent ({lease_id})"))

        return findings


def fold_canonical(ledger: "Ledger") -> dict:
    """KERNEL-SPEC §3.3 — the canonical fold serialization. This is the
    wire shape of the fold (the node serves it; the golden ledger corpora
    freeze it), so it lives beside the fold it serializes."""
    accounts = []
    folded = ledger.fold()
    for key in sorted(folded.keys(), key=lambda k: canonical_json(list(k))):
        a = folded[key]
        accounts.append({
            "key": list(key),
            "subject_entropy_mbits": a.subject_entropy_mbits,
            "ceiling_mbits": a.ceiling_mbits,
            "cumulative_mbits": a.cumulative_mbits,
            "demanded_mbits": a.demanded_mbits,
            "granted_lease_mbits": a.granted_lease_mbits,
            "leakage_class": a.leakage_class,
            "incident": a.incident,
            "conflicted": a.conflicted,
        })
    return {"accounts": accounts}
