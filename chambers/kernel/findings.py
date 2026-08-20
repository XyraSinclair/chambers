"""The findings registry — every verdict family, enumerated exactly once.

Before this module the roster of verdict families lived in four
hand-synchronized joins (the verifier, chamber-node/1's ``/v1/audit``,
the S4/S8 value gate, the Rust twin) and they had drifted — the exact
defect docs/SPECS.md § "Coverage and the court, stated exactly" records.
This table is the single Python-side enumeration: per family its code
prefix, defining identifier, implementation coverage, and which joins it
is a member of. Consumers derive their joins from the membership flags,
so "add a finding family" is one row plus its implementation, and every
exclusion is recorded data with its reason instead of implicit code.

MECHANICAL GUARANTEE. The joins below reproduce the pre-registry joins
byte-for-byte: frozen corpora, served responses, and verifier output are
unchanged. The recorded exclusions are historical fact — each join
predates the families it excludes — and their reconciliation is the
queued versioned change named in SPECS.md; this module changes where the
roster lives, never what any surface verdicts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class FindingFamily:
    prefix: str            # the code prefix ("I", "S", …)
    spec: str              # the versioned identifier that defines the codes
    defined_in: str        # the spec document (and part) of record
    rust: bool             # implemented in the rust_ledger twin
    settlement_court: bool  # joins the S4/S8 dirty-court stream
    node_audit: bool       # served by chamber-node/1 GET /v1/audit
    note: str = ""         # the recorded reason for any exclusion


FAMILIES: Tuple[FindingFamily, ...] = (
    FindingFamily(
        prefix="I", spec="charge-ledger/1",
        defined_in="KERNEL-SPEC.md (the grow-only ledger layer)",
        rust=True, settlement_court=True, node_audit=True,
    ),
    FindingFamily(
        prefix="S", spec="charge-settlement/1+2",
        defined_in="SETTLEMENT-SPEC.md §3 + §9 + the S11/S12 split extension",
        rust=True, settlement_court=False, node_audit=False,
        note="S-codes are the value gate's OUTPUT, never its input; "
             "/v1/audit serves the information layer — S arrives via "
             "/v1/verify and /v1/settlement.",
    ),
    FindingFamily(
        prefix="X", spec="charge-substrate/1",
        defined_in="KERNEL-SPEC.md Part II (the X0 law)",
        rust=False, settlement_court=False, node_audit=True,
        note="Excluded from the S4 court as historical fact: the "
             "charge-settlement joins predate charge-substrate/1 and no "
             "versioned spec has amended them; inclusion is queued "
             "(SPECS.md, reserved charge-settlement/3).",
    ),
    FindingFamily(
        prefix="C", spec="charge-covenant/1",
        defined_in="COVENANT-SPEC.md (join amended by its §4)",
        rust=False, settlement_court=True, node_audit=True,
    ),
    FindingFamily(
        prefix="P", spec="charge-provenance/1",
        defined_in="KERNEL-SPEC.md Part III (join amended by its P.6)",
        rust=False, settlement_court=True, node_audit=True,
    ),
    FindingFamily(
        prefix="A", spec="charge-identity/1+2",
        defined_in="IDENTITY-SPEC.md",
        rust=True, settlement_court=False, node_audit=False,
        note="Excluded from the S4 court as historical fact: an A2-forged "
             "charge convicts in the verifier but does not dirty the value "
             "gate today; reconciliation queued with charge-settlement/3.",
    ),
    FindingFamily(
        prefix="V", spec="charge-attribution/1+2",
        defined_in="ATTRIBUTION-SPEC.md (join amended by its V.7)",
        rust=False, settlement_court=True, node_audit=False,
        note="V joins the S4 court (ATTRIBUTION-SPEC V.7) but not "
             "/v1/audit's information view; it arrives via /v1/verify.",
    ),
)


def family_findings(prefix: str, ledger) -> List[Tuple[str, str, str]]:
    """The (code, subject, prose) triples for one family. Late imports:
    settlement/covenant/identity/attribution import this module."""
    if prefix == "I":
        return ledger.audit_findings()
    if prefix == "S":
        from .settlement import audit_settlement_findings
        return audit_settlement_findings(ledger)
    if prefix == "X":
        return ledger.substrate_findings()
    if prefix == "C":
        from .covenant import covenant_findings
        return covenant_findings(ledger)
    if prefix == "P":
        return ledger.provenance_findings()
    if prefix == "A":
        from .identity import identity_findings
        return identity_findings(ledger)
    if prefix == "V":
        from .attribution import attribution_findings
        return attribution_findings(ledger)
    raise ValueError(f"unknown finding family prefix: {prefix!r}")


def family_codes(prefix: str, ledger) -> List[str]:
    """The sorted, deduplicated ``"<code> <subject>"`` strings for one
    family — the conformance surface two implementations bind on."""
    if prefix == "I":
        return ledger.audit_codes()
    if prefix == "S":
        from .settlement import audit_settlement_codes
        return audit_settlement_codes(ledger)
    if prefix == "X":
        return ledger.substrate_codes()
    if prefix == "C":
        from .covenant import covenant_codes
        return covenant_codes(ledger)
    if prefix == "P":
        return ledger.provenance_codes()
    if prefix == "A":
        from .identity import identity_codes
        return identity_codes(ledger)
    if prefix == "V":
        from .attribution import attribution_codes
        return attribution_codes(ledger)
    raise ValueError(f"unknown finding family prefix: {prefix!r}")


def court_findings(ledger) -> List[Tuple[str, str, str]]:
    """The S4/S8 dirty-court stream: the concatenated findings of every
    family whose ``settlement_court`` flag is set, in registry order
    (I, C, P, V today — byte-identical to the join it replaced)."""
    out: List[Tuple[str, str, str]] = []
    for fam in FAMILIES:
        if fam.settlement_court:
            out.extend(family_findings(fam.prefix, ledger))
    return out


def node_audit_families() -> Tuple[FindingFamily, ...]:
    """The families chamber-node/1's GET /v1/audit serves (the wire key
    each maps to is transport naming and lives in node.py)."""
    return tuple(f for f in FAMILIES if f.node_audit)


def verdict_codes(ledger) -> List[Tuple[str, List[str]]]:
    """Every family's codes in registry order — the stranger's full
    verdict (verify.py's join)."""
    return [(f.prefix, family_codes(f.prefix, ledger)) for f in FAMILIES]
