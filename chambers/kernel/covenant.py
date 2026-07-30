"""charge-covenant/1 — declared self-restrictions the audit enforces
against the issuer's OWN later authority (COVENANT-SPEC.md; E5).

The exit story's missing half. G7 established that past receipts stand
and value cannot be stranded (S8); what remained was FUTURE AUTHORITY
MUST BE REFUSABLE — when Bob leaves, the chamber must be able to bind
its own hands about ever leasing his exposure again, in the artifact,
where a stranger can check it. Revocation decomposes as:

    tenor     — leases already expire (expires_tick, existing law);
    covenant  — the issuer's declared self-restriction (THIS module);
    residue   — the honest statement of what remains exposed forever
                (a declared field; one-way widening is a theorem, so
                the residue is named, never claimed away).

Two covenant actions in /1, both chosen because their violation is a
plain integer/comparison fact over the event set:

    cease_lease_issuance  — no lease on the key, by this issuer, may
                            outlive `horizon_tick` (C1 convicts).
    cap_lease_total       — Σ lease amounts on the key, by this issuer,
                            stays ≤ `cap_mbits` (C2 convicts). A cap at
                            the already-granted total is "no new
                            authority, ever".

Covenants only TIGHTEN: violation of ANY well-formed covenant convicts,
so the strictest binds, merge escalates, and no later event can loosen
an earlier promise — un-covenanting is impossible by construction, the
same one-way-ness as widening. Outstanding authority is GRANDFATHERED
by content-addressed id in the covenant's own bytes ("these named
grants survive; nothing else, ever"); tenor drains it.

Fact identity arrives free: covenants carry (issuer, seq), so X0
(KERNEL-SPEC Part II) convicts equivocation with no code here — the
first dividend of the substrate law.

Verdict surface: `c_codes` — separate from the frozen I/S surfaces,
same discipline. Settlement integration: covenant findings join the
dirty-court stream, so value against covenant-broken authority FAILS
CLOSED (C1 touches its lease's key, C2 its key; future C-codes touch
everything — SETTLEMENT-SPEC §3's fail-closed law, inherited).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from accountant import Key
from events import canonical_json, event_id
from identity import Signer, require_signer
from ledger import Ledger, _is_uint

COVENANT_ACTIONS = ("cease_lease_issuance", "cap_lease_total")


class CovenantRefused(Exception):
    pass


@dataclass(frozen=True)
class CovenantEvent:
    """The issuer's self-restriction, declared into the court. `residue`
    is the honest exit statement — what stays exposed no matter what —
    prose by design: one-way widening means it cannot be enforced away,
    only named.

    `except_lease_ids` GRANDFATHERS outstanding authority by
    content-addressed id: the covenant's own bytes name exactly which
    grants survive it ("these, and nothing else, ever"); tenor drains
    them. A covenant is therefore declarable at any moment of a key's
    life — history is named, never overpromised away."""

    issuer: str
    key: Key
    action: str
    residue: str
    seq: int
    tick: int
    horizon_tick: Optional[int] = None  # cease_lease_issuance
    cap_mbits: Optional[int] = None     # cap_lease_total
    except_lease_ids: Tuple[str, ...] = ()
    # charge-identity/1: ADDITIVE, serialized only when present — unsigned
    # covenants keep exact historical bytes. A cease signed by the ceasing
    # key binds THAT key (IDENTITY-SPEC §5).
    sig: Optional[str] = None

    def payload(self) -> Dict[str, Any]:
        p: Dict[str, Any] = {
            "kind": "covenant", "issuer": self.issuer,
            "key": list(self.key), "action": self.action,
            "residue": self.residue, "seq": self.seq, "tick": self.tick,
        }
        if self.horizon_tick is not None:
            p["horizon_tick"] = self.horizon_tick
        if self.cap_mbits is not None:
            p["cap_mbits"] = self.cap_mbits
        if self.except_lease_ids:
            p["except_lease_ids"] = list(self.except_lease_ids)
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


# ---- audit ----

def _covenant_well_formed(p: Dict[str, Any]) -> bool:
    seq = p.get("seq")
    key = p.get("key")
    if not (
        isinstance(p.get("issuer"), str)
        and isinstance(key, list) and key
        and all(isinstance(s, str) for s in key)
        and p.get("action") in COVENANT_ACTIONS
        and isinstance(p.get("residue"), str)
        and _is_uint(seq) and seq >= 1
    ):
        return False
    exc = p.get("except_lease_ids", [])
    if not (isinstance(exc, list) and all(isinstance(s, str) for s in exc)):
        return False
    if p["action"] == "cease_lease_issuance":
        h = p.get("horizon_tick")
        return isinstance(h, int) and not isinstance(h, bool)
    cap = p.get("cap_mbits")
    return _is_uint(cap)


def _covenants_on(
    events: Dict[str, Dict[str, Any]]
) -> Dict[Tuple[str, Tuple[str, ...]], List[Dict[str, Any]]]:
    """(issuer, key) -> the well-formed covenants binding it. Violation
    of ANY covenant convicts, so the strictest always binds and no later
    covenant can loosen an earlier one — the one-way law without even a
    min()."""
    out: Dict[Tuple[str, Tuple[str, ...]], List[Dict[str, Any]]] = {}
    for _eid, p in events.items():
        if p.get("kind") == "covenant" and _covenant_well_formed(p):
            out.setdefault((p["issuer"], tuple(p["key"])), []).append(p)
    return out


def covenant_findings(ledger: Ledger) -> List[Tuple[str, str, str]]:
    """C1..C3 as (code, subject, prose). Total over adversarial content.

    C1  lease event id  — a non-grandfathered lease outlives some cease
        covenant's horizon on its (issuer, key)
    C2  canonical key JSON — Σ non-grandfathered lease amounts by the
        issuer on the key exceed some cap covenant's cap
    C3  covenant event id — malformed covenant
    """
    findings: List[Tuple[str, str, str]] = []
    events = getattr(ledger, "_events")

    for eid, p in events.items():
        if p.get("kind") == "covenant" and not _covenant_well_formed(p):
            findings.append(("C3", eid, f"C3 malformed covenant {eid}"))

    covenants = _covenants_on(events)
    if not covenants:
        return findings

    leases: Dict[Tuple[str, Tuple[str, ...]], List[Tuple[str, Dict[str, Any]]]] = {}
    for eid, p in events.items():
        if p.get("kind") != "lease":
            continue
        key = p.get("key")
        issuer = p.get("issuer")
        if not (isinstance(key, list) and all(isinstance(s, str) for s in key)
                and isinstance(issuer, str)):
            continue
        ident = (issuer, tuple(key))
        if ident in covenants:
            leases.setdefault(ident, []).append((eid, p))

    for ident, covs in covenants.items():
        for cov in covs:
            grandfathered = set(cov.get("except_lease_ids", []))
            if cov["action"] == "cease_lease_issuance":
                horizon = cov["horizon_tick"]
                for eid, p in leases.get(ident, []):
                    if eid in grandfathered:
                        continue
                    exp = p.get("expires_tick")
                    if (isinstance(exp, int) and not isinstance(exp, bool)
                            and exp > horizon):
                        findings.append((
                            "C1", eid,
                            f"C1 lease {eid} outlives covenant horizon "
                            f"{horizon} (expires {exp})",
                        ))
            else:
                total = sum(
                    p["amount_mbits"]
                    for eid, p in leases.get(ident, [])
                    if eid not in grandfathered and _is_uint(p.get("amount_mbits"))
                )
                if total > cov["cap_mbits"]:
                    findings.append((
                        "C2", canonical_json(list(ident[1])),
                        f"C2 issuer {ident[0]!r} granted {total} "
                        f"non-grandfathered mbits on "
                        f"{canonical_json(list(ident[1]))} past covenant "
                        f"cap {cov['cap_mbits']}",
                    ))

    return findings


def covenant_codes(ledger: Ledger) -> List[str]:
    """Conformance surface: sorted, deduplicated '<code> <subject>'."""
    return sorted({f"{c} {s}" for c, s, _ in covenant_findings(ledger)})


# ---- the honest issuer's front ----

def declare_covenant(
    ledger: Ledger,
    issuer: str,
    key: Key,
    action: str,
    tick: int,
    horizon_tick: Optional[int] = None,
    cap_mbits: Optional[int] = None,
    residue: str = "",
    except_lease_ids: Optional[Sequence[str]] = None,
    signer: Optional[Signer] = None,
) -> CovenantEvent:
    """Declare a self-restriction, GRANDFATHERING history by name: with
    `except_lease_ids=None` (the default) every outstanding lease by
    this issuer on this key that would violate the new covenant is
    exempted BY CONTENT-ADDRESSED ID in the covenant's own bytes — the
    surviving authority is enumerated, tenor drains it, and nothing else
    is ever issued. Pass an explicit list (possibly empty) to grandfather
    less: the audit then convicts the un-exempted history immediately,
    which is a legitimate self-indictment, not an error."""
    signer = require_signer(issuer, signer, "covenant issuer")
    if action not in COVENANT_ACTIONS:
        raise CovenantRefused(f"action must be one of {COVENANT_ACTIONS}")
    key = tuple(key)
    events = getattr(ledger, "_events")
    if action == "cease_lease_issuance":
        if not (isinstance(horizon_tick, int) and not isinstance(horizon_tick, bool)):
            raise CovenantRefused("cease covenant needs an integer horizon_tick")
        cap_mbits = None
    else:
        if not _is_uint(cap_mbits):
            raise CovenantRefused("cap covenant needs a uint cap_mbits")
        horizon_tick = None
    if except_lease_ids is None:
        exempt: List[str] = []
        for eid, p in events.items():
            if (p.get("kind") == "lease" and p.get("issuer") == issuer
                    and isinstance(p.get("key"), list) and tuple(p["key"]) == key):
                exp = p.get("expires_tick")
                if action == "cease_lease_issuance":
                    if (isinstance(exp, int) and not isinstance(exp, bool)
                            and exp > horizon_tick):
                        exempt.append(eid)
                else:
                    exempt.append(eid)  # a cap binds NEW authority only
        except_lease_ids = sorted(exempt)
    else:
        except_lease_ids = sorted(set(except_lease_ids))
    top = 0
    for _eid, p in events.items():
        if p.get("kind") == "covenant" and p.get("issuer") == issuer:
            s = p.get("seq")
            if _is_uint(s):
                top = max(top, s)
    ev = CovenantEvent(
        issuer=issuer, key=key, action=action, residue=residue,
        seq=top + 1, tick=tick,
        horizon_tick=horizon_tick, cap_mbits=cap_mbits,
        except_lease_ids=tuple(except_lease_ids),
    )
    if signer is not None:
        ev = signer.sign(ev)
    ledger.add(ev)
    return ev


def grant_violates_covenants(
    events: Dict[str, Dict[str, Any]],
    issuer: str,
    key: Key,
    amount_mbits: int,
    expires_tick: int,
) -> Optional[str]:
    """The honest lease issuer's pre-grant check (used by LeaseIssuer):
    the reason a NEW grant would break this issuer's own covenants, or
    None. A new grant is never grandfathered (its id does not appear in
    any covenant's exceptions), so every covenant binds it."""
    covs = _covenants_on(events).get((issuer, tuple(key)))
    if not covs:
        return None
    for cov in covs:
        if cov["action"] == "cease_lease_issuance":
            if expires_tick > cov["horizon_tick"]:
                return (f"covenant: lease issuance on this key ceased beyond "
                        f"tick {cov['horizon_tick']} (grant expires {expires_tick})")
        else:
            grandfathered = set(cov.get("except_lease_ids", []))
            existing = sum(
                p["amount_mbits"] for eid, p in events.items()
                if p.get("kind") == "lease" and p.get("issuer") == issuer
                and isinstance(p.get("key"), list) and tuple(p["key"]) == tuple(key)
                and eid not in grandfathered and _is_uint(p.get("amount_mbits"))
            )
            if existing + amount_mbits > cov["cap_mbits"]:
                return (f"covenant: cap {cov['cap_mbits']} mbits of "
                        f"non-grandfathered authority; {existing} out, "
                        f"{amount_mbits} more would exceed it")
    return None
