"""charge-settlement/2 — value bound to metered work (SETTLEMENT-SPEC.md).

The charge ledger meters what LEAVES a private world; this layer meters
what is OWED for it, in the same artifact, under the same discipline:
content-addressed events, union merge, a total fold, and convictions
(S-codes) instead of crashes. Integer microcredits only; pricing is the
value-side analog of estimation and stays outside the protocol.

The binding law (/1): a release references the exact charge events it pays
for, by id, and is convicted if those facts are absent, refused, off-key,
or if the court file touching the escrow's metered accounts is dirty.
Value moves iff metered work moved.

The /2 extension (SPEC Part II): an escrow may declare an OUTCOME
condition ("$5 if they talk 15 minutes"). Release is then additionally
gated on an outcome proof — a quorum of bonded, independence-classed,
contest-hardened `outcome_attestation` events, referenced by id exactly
as work receipts are. Bonds are real value locked by the fold itself;
they return after an uncontested window or are slashed by strictly
better evidence (platform logs beat bonded rulings; equal-lane contest
blocks payment but slashes nobody). Counterfactual metrics have no lane
and cannot be expressed. Outcome conditions gate RELEASES only — never
disclosure; the dependency stays one-way.

Dependency is one-way: settlement reads charge facts; the charge layer
never references value.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from accountant import Key
from attribution import attribution_findings, recomputed_shares
from covenant import covenant_findings
from events import canonical_json, event_id
from identity import Signer, require_signer
from ledger import Ledger, _hashable_key, _is_uint


def _court_findings(ledger: Ledger) -> "List[Tuple[str, str, str]]":
    """The dirty-court stream S4/S8 police releases against: the
    information verdict PLUS charge-covenant/1 (value against
    covenant-broken authority fails closed — SETTLEMENT-SPEC §3;
    COVENANT-SPEC §4) PLUS charge-provenance/1 (value against
    ancestry-laundering emissions fails closed — KERNEL-SPEC Part III
    P.6) PLUS charge-attribution/1 (value near a lying split claim fails
    closed — ATTRIBUTION-SPEC V.7). Frozen corpora carry no covenants,
    no derivations, and no attribution reports, so every join leaves
    their verdicts byte-identical."""
    return (
        ledger.audit_findings()
        + covenant_findings(ledger)
        + ledger.provenance_findings()
        + attribution_findings(ledger)
    )

SETTLEMENT_KINDS = (
    "deposit", "escrow", "release", "refund", "default_resolution",
    "outcome_attestation", "bond_resolution",
)

DEFAULT_DIRECTIONS = ("release_to_payee", "refund_to_payer")

#: ATTRIBUTION-SPEC V.8 — legal expiry defaults for split-bound escrows:
#: per-row permissionless release (F4 safety-shape) or plain refund.
SPLIT_DEFAULT_DIRECTIONS = ("release_by_report", "refund_to_payer")


def _split_well_formed(sp: Any) -> bool:
    """ATTRIBUTION-SPEC V.8: a dict with a string `derived` carrying
    `node` and `coupling_tick` (any JSON — compared canonically)."""
    return (
        isinstance(sp, dict)
        and isinstance(sp.get("derived"), str)
        and "node" in sp
        and "coupling_tick" in sp
    )

# ---- /2 vocabularies (SPEC §7). Tuple order IS the total order. ----

OUTCOME_CLAIMS = ("occurred", "not_occurred")
OUTCOME_LANES = ("attested", "platform_log")
INDEPENDENCE_CLASSES = ("party", "operator", "role_separated", "adversarial_review")
BOND_DIRECTIONS = ("return_to_attestor", "slash")

_OUTCOME_FIELDS = ("metric", "lane", "quorum", "min_independence",
                   "min_bond_ucr", "contest_ticks")

# I-code subjects S4 knows how to map to keys. An unknown code fails closed
# (touches everything) — value release must not outrun the audit's vocabulary.
# charge-covenant/1 codes joined 2026-07-06: C1's subject is a lease id,
# C2's a key; any FUTURE C-code falls to the fail-closed default, so value
# against authority broken in ways this audit cannot parse never moves.
# charge-provenance/1 joined 2026-07-06: P1/P2 subjects ARE the uncharged
# exposure keys; P3 (orphaned derivation — unresolvable ancestry) and any
# future P-code fall to the same fail-closed default.
_KEY_SUBJECT_CODES = {"I1", "I2", "I7", "C2", "P1", "P2"}
_LEASE_SUBJECT_CODES = {"I3", "I5", "C1"}
_CHARGE_SUBJECT_CODES = {"I4", "I6"}


class SettlementRefused(Exception):
    pass


# ---- events ----

@dataclass(frozen=True)
class DepositEvent:
    """Declared inflow: the issuer's liability to `account` grows. Value
    enters the protocol ONLY here — no other event mints."""

    account: str
    amount_ucr: int
    issuer: str
    seq: int
    tick: int
    # charge-identity/1: ADDITIVE, serialized only when present — unsigned
    # events keep their exact historical bytes (frozen corpora unmoved).
    # Set by identity.Signer.sign(); covered by the event id.
    sig: Optional[str] = None

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "deposit", "account": self.account,
            "amount_ucr": self.amount_ucr, "issuer": self.issuer,
            "seq": self.seq, "tick": self.tick,
        }
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class OutcomeCondition:
    """SPEC §7.1 — the declared outcome condition, part of the escrow's
    bytes (hence its id): both parties price it before any work runs.
    `metric` must name the proxy for what it is (presence, first-contact
    attribution) — never the aspiration. There is no counterfactual lane."""

    metric: str
    lane: str
    quorum: int
    min_independence: str
    min_bond_ucr: int
    contest_ticks: int

    def __post_init__(self) -> None:
        if self.lane not in OUTCOME_LANES:
            raise ValueError(f"lane must be one of {OUTCOME_LANES}")
        if self.min_independence not in INDEPENDENCE_CLASSES:
            raise ValueError(f"min_independence must be one of {INDEPENDENCE_CLASSES}")
        if not (_is_uint(self.quorum) and self.quorum >= 1):
            raise ValueError("quorum must be a uint >= 1")
        if not _is_uint(self.min_bond_ucr):
            raise ValueError("min_bond_ucr must be a uint")
        if not _is_uint(self.contest_ticks):
            raise ValueError("contest_ticks must be a uint")
        if not isinstance(self.metric, str):
            raise ValueError("metric must be a string")

    def payload(self) -> Dict[str, Any]:
        return {
            "metric": self.metric, "lane": self.lane, "quorum": self.quorum,
            "min_independence": self.min_independence,
            "min_bond_ucr": self.min_bond_ucr,
            "contest_ticks": self.contest_ticks,
        }


@dataclass(frozen=True)
class SplitCondition:
    """ATTRIBUTION-SPEC V.8 — the split binding, part of the escrow's
    bytes: this pot disburses only along the recomputed shapley_dpi/1
    rows of the named emission. The audit derives the rows from the DAG;
    no report event is consulted on the value path (the report stays the
    legible claim, policed by V-codes)."""

    derived: str
    node: Any
    coupling_tick: Any

    def __post_init__(self) -> None:
        if not isinstance(self.derived, str):
            raise ValueError("split.derived must be a fact id string")

    def payload(self) -> Dict[str, Any]:
        return {
            "derived": self.derived, "node": self.node,
            "coupling_tick": self.coupling_tick,
        }


@dataclass(frozen=True)
class EscrowEvent:
    """A conditional lock of payer value toward a payee, bound to the
    metered accounts (`charge_keys`) the work will run on.

    `default_on_expiry` is the anti-holdup clause (SPEC §1.5): the
    escrow's terminal fate if the issuer goes silent, declared at lock
    time so both parties price it before any work runs.

    `outcome` (/2, SPEC §7.1) is the optional declared outcome condition;
    when present, `default_on_expiry` MUST be refund_to_payer (S6) and
    releases must carry an outcome proof (S9). The key is absent from the
    payload when None — /1 escrow bytes are untouched by /2's existence.

    `split` (ATTRIBUTION-SPEC Part II) binds the pot to the recomputed
    shapley_dpi/1 rows of an emission; disbursements then carry a
    `beneficiary` and are policed by S11/S12. Absent when None — same
    additive discipline."""

    payer: str
    payee: str
    amount_ucr: int
    charge_keys: Tuple[Key, ...]
    required_clean: bool
    expires_tick: int
    default_on_expiry: str
    issuer: str
    seq: int
    tick: int
    outcome: Optional[OutcomeCondition] = None
    split: Optional[SplitCondition] = None
    sig: Optional[str] = None  # charge-identity/1: additive, see DepositEvent

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "escrow", "payer": self.payer, "payee": self.payee,
            "amount_ucr": self.amount_ucr,
            "charge_keys": [list(k) for k in self.charge_keys],
            "required_clean": self.required_clean,
            "expires_tick": self.expires_tick,
            "default_on_expiry": self.default_on_expiry,
            "issuer": self.issuer,
            "seq": self.seq, "tick": self.tick,
        }
        if self.outcome is not None:
            p["outcome"] = self.outcome.payload()
        if self.split is not None:
            p["split"] = self.split.payload()
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class ReleaseEvent:
    """Disburse escrowed value to the payee, against work receipts: the
    charge events being paid for, referenced by content-addressed id.

    Against an outcome-conditioned escrow (/2) the release also carries
    `attestation_ids` — the outcome proof, referenced the same way (SPEC
    §7.5). The key is absent when empty: /1 release bytes unchanged."""

    escrow_id: str
    amount_ucr: int
    charge_ids: Tuple[str, ...]
    issuer: str
    seq: int
    tick: int
    attestation_ids: Tuple[str, ...] = ()
    beneficiary: Optional[str] = None  # ATTRIBUTION-SPEC V.9: the row paid
    sig: Optional[str] = None  # charge-identity/1: additive, see DepositEvent

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "release", "escrow_id": self.escrow_id,
            "amount_ucr": self.amount_ucr,
            "charge_ids": list(self.charge_ids),
            "issuer": self.issuer, "seq": self.seq, "tick": self.tick,
        }
        if self.attestation_ids:
            p["attestation_ids"] = list(self.attestation_ids)
        if self.beneficiary is not None:
            p["beneficiary"] = self.beneficiary
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class RefundEvent:
    """Return escrow remainder to the payer. Needs no work receipt and no
    clean court — returning value to its payer is always safe."""

    escrow_id: str
    amount_ucr: int
    issuer: str
    seq: int
    tick: int
    sig: Optional[str] = None  # charge-identity/1: additive, see DepositEvent

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "refund", "escrow_id": self.escrow_id,
            "amount_ucr": self.amount_ucr, "issuer": self.issuer,
            "seq": self.seq, "tick": self.tick,
        }
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class DefaultResolutionEvent:
    """The anti-holdup clause exercised (SPEC §1.5): after the escrow's
    declared expiry, ANY party — the payee is the point — submits the
    escrow's declared default. The direction comes from the ESCROW, not
    from the submitter; the audit (S8) polices timing and, for
    release-direction defaults, the work receipt and clean court."""

    escrow_id: str
    amount_ucr: int
    charge_ids: Tuple[str, ...]  # required iff the resolution flows to the payee
    submitter: str
    seq: int
    tick: int
    attestation_ids: Tuple[str, ...] = ()  # /2: the quorum proof selects release direction (SPEC §7.4)
    beneficiary: Optional[str] = None  # ATTRIBUTION-SPEC V.10: per-row default
    sig: Optional[str] = None  # charge-identity/1: additive, see DepositEvent

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "default_resolution", "escrow_id": self.escrow_id,
            "amount_ucr": self.amount_ucr,
            "charge_ids": list(self.charge_ids),
            "submitter": self.submitter,
            "seq": self.seq, "tick": self.tick,
        }
        if self.attestation_ids:
            p["attestation_ids"] = list(self.attestation_ids)
        if self.beneficiary is not None:
            p["beneficiary"] = self.beneficiary
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class OutcomeAttestationEvent:
    """SPEC §7.2 — a bonded, contestable outcome fact: the estimator
    posture applied to outcomes. The bond is locked from the attestor's
    account by the fold itself; an unbacked bond convicts its attestor
    (S1) and stops counting toward any quorum (S9). Attesting
    `not_occurred` is the sanctioned contest move, same discipline."""

    escrow_id: str
    claim: str
    lane: str
    independence: str
    evidence: str
    bond_ucr: int
    attestor: str
    seq: int
    tick: int
    sig: Optional[str] = None  # charge-identity/1: additive, see DepositEvent

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "outcome_attestation", "escrow_id": self.escrow_id,
            "claim": self.claim, "lane": self.lane,
            "independence": self.independence, "evidence": self.evidence,
            "bond_ucr": self.bond_ucr, "attestor": self.attestor,
            "seq": self.seq, "tick": self.tick,
        }
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


@dataclass(frozen=True)
class BondResolutionEvent:
    """SPEC §7.3 — permissionless bond resolution. Return is honest only
    after an uncontested window; slash only under a STRICT override
    (better evidence convicts; equal-lane contest is not conviction).
    The slash beneficiary is DERIVED from declared data — the escrow
    party the false claim would have harmed; the submitter chooses
    nothing. The audit (S10) polices every arm."""

    attestation_id: str
    amount_ucr: int
    direction: str
    submitter: str
    seq: int
    tick: int
    # G19 (SPEC §9 S10.4): a slash MAY name its justifying override. The
    # field is ADDITIVE and serialized only when present, so every event
    # that omits it keeps its exact historical bytes (frozen corpora and
    # the Rust port unaffected). When present, the naming BINDS: the
    # audit judges the named referent, not the best override available.
    override_attestation_id: Optional[str] = None
    sig: Optional[str] = None  # charge-identity/1: additive, see DepositEvent

    def payload(self) -> Dict[str, Any]:
        p = {
            "kind": "bond_resolution", "attestation_id": self.attestation_id,
            "amount_ucr": self.amount_ucr, "direction": self.direction,
            "submitter": self.submitter, "seq": self.seq, "tick": self.tick,
        }
        if self.override_attestation_id is not None:
            p["override_attestation_id"] = self.override_attestation_id
        if self.sig is not None:
            p["sig"] = self.sig
        return p

    @property
    def id(self) -> str:
        return event_id(self.payload())


# ---- fold ----

@dataclass
class AccountBalance:
    account: str
    deposited_ucr: int = 0
    locked_out_ucr: int = 0
    released_in_ucr: int = 0
    refunded_in_ucr: int = 0
    # /2 buckets (SPEC §8) — all zero on /1 artifacts.
    bonded_out_ucr: int = 0
    bond_returned_in_ucr: int = 0
    slashed_in_ucr: int = 0

    @property
    def available_ucr(self) -> int:
        """Signed on purpose: a negative value IS the S1 conviction; the
        artifact records the crime rather than clamping it away."""
        return (
            self.deposited_ucr + self.released_in_ucr + self.refunded_in_ucr
            + self.bond_returned_in_ucr + self.slashed_in_ucr
            - self.locked_out_ucr - self.bonded_out_ucr
        )


@dataclass
class EscrowState:
    escrow_id: str
    payload: Dict[str, Any]
    amount_ucr: int = 0
    released_ucr: int = 0
    refunded_ucr: int = 0

    @property
    def remaining_ucr(self) -> int:
        return self.amount_ucr - self.released_ucr - self.refunded_ucr


@dataclass
class BondState:
    """SPEC §8 — where an attestation's bond currently sits."""

    attestation_id: str
    payload: Dict[str, Any]
    amount_ucr: int = 0
    returned_ucr: int = 0
    slashed_ucr: int = 0

    @property
    def remaining_ucr(self) -> int:
        return self.amount_ucr - self.returned_ucr - self.slashed_ucr


def _settlement_events(ledger: Ledger) -> Iterable[Tuple[str, Dict[str, Any]]]:
    for eid, payload in getattr(ledger, "_events").items():
        if payload.get("kind") in SETTLEMENT_KINDS:
            yield eid, payload


def _slash_beneficiary(att_payload: Dict[str, Any],
                       events: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """SPEC §8 — the escrow party a false claim would have harmed:
    payer for a false `occurred`, payee for a false `not_occurred`.
    None when underivable (all-or-nothing: the slash then moves nothing)."""
    escrow_id = att_payload.get("escrow_id")
    ep = events.get(escrow_id) if isinstance(escrow_id, str) else None
    if ep is None or ep.get("kind") != "escrow":
        return None
    claim = att_payload.get("claim")
    if claim == "occurred":
        party = ep.get("payer")
    elif claim == "not_occurred":
        party = ep.get("payee")
    else:
        return None
    return party if isinstance(party, str) else None


def settlement_fold_full(
    ledger: Ledger,
) -> Tuple[Dict[str, AccountBalance], Dict[str, EscrowState], Dict[str, BondState]]:
    """SETTLEMENT-SPEC §2 + §8. Total over adversarial content; non-uint
    amounts contribute nothing (and are convicted by S6); every /2 flow is
    all-or-nothing between a bond and a destination account, so the
    conservation identity stays arithmetic on any event soup."""
    accounts: Dict[str, AccountBalance] = {}
    escrows: Dict[str, EscrowState] = {}
    bonds: Dict[str, BondState] = {}
    events = getattr(ledger, "_events")

    def acct(name: Any) -> Optional[AccountBalance]:
        if not isinstance(name, str):
            return None
        if name not in accounts:
            accounts[name] = AccountBalance(account=name)
        return accounts[name]

    # pass 1: deposits, escrows, and attestation bonds (they create
    # accounts, escrow states, and bond states)
    for eid, p in _settlement_events(ledger):
        kind = p["kind"]
        if kind == "deposit":
            a = acct(p.get("account"))
            if a is not None and _is_uint(p.get("amount_ucr")):
                a.deposited_ucr += p["amount_ucr"]
        elif kind == "escrow":
            payer = acct(p.get("payer"))
            acct(p.get("payee"))
            amount = p.get("amount_ucr")
            st = EscrowState(escrow_id=eid, payload=p)
            # all-or-nothing (as bonds do below): the escrow's remainder
            # exists ONLY when its lock debited a real payer account. A
            # non-string payer with a uint amount would otherwise mint
            # `amount` into the conservation LHS with no offsetting
            # locked_out — the fold must telescope on ANY soup. The
            # malformed escrow is convicted S6.
            if _is_uint(amount) and payer is not None:
                st.amount_ucr = amount
                payer.locked_out_ucr += amount
            escrows[eid] = st
        elif kind == "outcome_attestation":
            attestor = acct(p.get("attestor"))
            bond = BondState(attestation_id=eid, payload=p)
            amount = p.get("bond_ucr")
            # all-or-nothing: a lock with no derivable source account
            # would mint a remainder from nothing (SPEC §8)
            if _is_uint(amount) and attestor is not None:
                bond.amount_ucr = amount
                attestor.bonded_out_ucr += amount
            bonds[eid] = bond

    # pass 2: releases, refunds, default resolutions, bond resolutions.
    # A default resolution flows in the direction the ESCROW declared —
    # for outcome escrows the declared rule is conditional (SPEC §7.4):
    # quorum-proof present = release, else refund. An escrow with a
    # malformed default direction resolves nothing (S2/S6 convict).
    for _eid, p in _settlement_events(ledger):
        kind = p["kind"]
        if kind == "bond_resolution":
            aid = p.get("attestation_id")
            bond = bonds.get(aid) if isinstance(aid, str) else None
            if bond is None:
                continue  # S10 convicts; nothing to sum against
            amount = p.get("amount_ucr")
            if not _is_uint(amount):
                continue  # S6 convicts
            direction = p.get("direction")
            if direction == "return_to_attestor":
                a = acct(bond.payload.get("attestor"))
                if a is not None:  # all-or-nothing (SPEC §8)
                    bond.returned_ucr += amount
                    a.bond_returned_in_ucr += amount
            elif direction == "slash":
                beneficiary = acct(_slash_beneficiary(bond.payload, events))
                if beneficiary is not None:  # all-or-nothing (SPEC §8)
                    bond.slashed_ucr += amount
                    beneficiary.slashed_in_ucr += amount
            # unknown direction: contributes nothing; S6 convicts
            continue
        if kind not in ("release", "refund", "default_resolution"):
            continue
        esid = p.get("escrow_id")
        st = escrows.get(esid) if isinstance(esid, str) else None
        if st is None:
            continue  # S2 convicts; nothing to sum against
        amount = p.get("amount_ucr")
        if not _is_uint(amount):
            continue  # S6 convicts
        if kind == "default_resolution":
            if "outcome" in st.payload:
                ids = p.get("attestation_ids")
                kind = "release" if isinstance(ids, list) and ids else "refund"
            else:
                direction = st.payload.get("default_on_expiry")
                if direction == "release_to_payee":
                    kind = "release"
                elif direction == "refund_to_payer":
                    kind = "refund"
                elif direction == "release_by_report" and "split" in st.payload:
                    # ATTRIBUTION-SPEC V.10: the per-row permissionless
                    # default — a release in all but name, crediting the
                    # event's beneficiary below. On a NON-split escrow the
                    # direction is unresolvable (S6/S2 convict) and moves
                    # nothing.
                    kind = "release"
                else:
                    continue  # unresolvable direction: S2 convicts
        payer = st.payload.get("payer")
        payee = st.payload.get("payee")
        # all-or-nothing: the disbursement counts against the escrow ONLY
        # when it credits a real destination account — else it would drop
        # the escrow remainder with no offsetting account gain and break
        # conservation (the mirror of the escrow-lock case above). A
        # disbursement to a non-string party is convicted by S3/S2.
        if kind == "release":
            # ATTRIBUTION-SPEC V.10: a split escrow's release direction
            # credits the event's beneficiary — same gate, different
            # string; a non-string beneficiary credits nobody and counts
            # nothing (S11 convicts; conservation telescopes unchanged).
            target = p.get("beneficiary") if "split" in st.payload else payee
            a = acct(target)
            if a is not None:
                st.released_ucr += amount
                a.released_in_ucr += amount
        else:
            a = acct(payer)
            if a is not None:
                st.refunded_ucr += amount
                a.refunded_in_ucr += amount

    return accounts, escrows, bonds


def settlement_fold(ledger: Ledger) -> Tuple[Dict[str, AccountBalance], Dict[str, EscrowState]]:
    """The /1-shaped view of the full fold (accounts and escrows only).
    Balances are /2-aware — bonds subtract from `available` — which is
    exactly what a conforming /2 issuer must guard on (SPEC header)."""
    accounts, escrows, _bonds = settlement_fold_full(ledger)
    return accounts, escrows


def settlement_fold_canonical(ledger: Ledger) -> Dict[str, Any]:
    """SETTLEMENT-SPEC §2.1 — the /1 conformance serialization, frozen:
    byte-identical on /1 artifacts forever (the Rust port binds to it)."""
    accounts, escrows = settlement_fold(ledger)
    return {
        "accounts": [
            {
                "account": a.account,
                "deposited_ucr": a.deposited_ucr,
                "locked_out_ucr": a.locked_out_ucr,
                "released_in_ucr": a.released_in_ucr,
                "refunded_in_ucr": a.refunded_in_ucr,
                "available_ucr": a.available_ucr,
            }
            for a in (accounts[k] for k in sorted(accounts))
        ],
        "escrows": [
            {
                "escrow_id": e.escrow_id,
                "amount_ucr": e.amount_ucr,
                "released_ucr": e.released_ucr,
                "refunded_ucr": e.refunded_ucr,
                "remaining_ucr": e.remaining_ucr,
            }
            for e in (escrows[k] for k in sorted(escrows))
        ],
    }


def settlement_fold_canonical_v2(ledger: Ledger) -> Dict[str, Any]:
    """SETTLEMENT-SPEC §8.1 — the /2 conformance serialization: the /1
    account/escrow objects plus the three bond buckets and the bonds
    array. Dropping them recovers the /1 serialization exactly."""
    accounts, escrows, bonds = settlement_fold_full(ledger)
    return {
        "accounts": [
            {
                "account": a.account,
                "deposited_ucr": a.deposited_ucr,
                "locked_out_ucr": a.locked_out_ucr,
                "released_in_ucr": a.released_in_ucr,
                "refunded_in_ucr": a.refunded_in_ucr,
                "bonded_out_ucr": a.bonded_out_ucr,
                "bond_returned_in_ucr": a.bond_returned_in_ucr,
                "slashed_in_ucr": a.slashed_in_ucr,
                "available_ucr": a.available_ucr,
            }
            for a in (accounts[k] for k in sorted(accounts))
        ],
        "escrows": [
            {
                "escrow_id": e.escrow_id,
                "amount_ucr": e.amount_ucr,
                "released_ucr": e.released_ucr,
                "refunded_ucr": e.refunded_ucr,
                "remaining_ucr": e.remaining_ucr,
            }
            for e in (escrows[k] for k in sorted(escrows))
        ],
        "bonds": [
            {
                "attestation_id": b.attestation_id,
                "amount_ucr": b.amount_ucr,
                "returned_ucr": b.returned_ucr,
                "slashed_ucr": b.slashed_ucr,
                "remaining_ucr": b.remaining_ucr,
            }
            for b in (bonds[k] for k in sorted(bonds))
        ],
    }


def conservation_identity(ledger: Ledger) -> Tuple[int, int]:
    """Returns (Σ available + Σ escrow remaining + Σ bond remaining,
    Σ deposits). Equal by arithmetic for ANY event set — the test suite
    asserts it even on forged soups. On /1 artifacts the bond term is
    zero and this is exactly the /1 identity."""
    accounts, escrows, bonds = settlement_fold_full(ledger)
    lhs = (
        sum(a.available_ucr for a in accounts.values())
        + sum(e.remaining_ucr for e in escrows.values())
        + sum(b.remaining_ucr for b in bonds.values())
    )
    rhs = sum(a.deposited_ucr for a in accounts.values())
    return lhs, rhs


# ---- audit ----

# ---- /2 outcome helpers (SPEC §7, §9) ----

def _outcome_condition(escrow_payload: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """('absent', None) | ('ok', block) | ('malformed', None).

    Malformed includes an outcome escrow whose default_on_expiry is not
    refund_to_payer (SPEC §7.1) — the condition would be vacuous at
    expiry, which is exactly the forgery S6 exists to convict."""
    if "outcome" not in escrow_payload:
        return ("absent", None)
    block = escrow_payload.get("outcome")
    if not isinstance(block, dict):
        return ("malformed", None)
    q = block.get("quorum")
    if (
        not isinstance(block.get("metric"), str)
        or block.get("lane") not in OUTCOME_LANES
        or not _is_uint(q) or q < 1
        or block.get("min_independence") not in INDEPENDENCE_CLASSES
        or not _is_uint(block.get("min_bond_ucr"))
        or not _is_uint(block.get("contest_ticks"))
        or escrow_payload.get("default_on_expiry") != "refund_to_payer"
    ):
        return ("malformed", None)
    return ("ok", block)


def _attestation_well_formed(t: Dict[str, Any]) -> bool:
    """SPEC §9 S6 arm for outcome_attestation payloads."""
    seq = t.get("seq")
    return (
        isinstance(t.get("escrow_id"), str)
        and t.get("claim") in OUTCOME_CLAIMS
        and t.get("lane") in OUTCOME_LANES
        and isinstance(t.get("independence"), str)
        and isinstance(t.get("evidence"), str)
        and _is_uint(t.get("bond_ucr"))
        and isinstance(t.get("attestor"), str)
        and _is_uint(seq) and seq >= 1
    )


def _lane_rank(lane: str) -> int:
    return OUTCOME_LANES.index(lane)


def _effective_class_rank(t: Dict[str, Any], escrow_payload: Dict[str, Any]) -> Optional[int]:
    """SPEC §7.1: the declared class, demoted to `party` when the attestor
    IS the payer or payee — the one independence fact the artifact itself
    can check. None = inadmissible (unknown class fails closed)."""
    declared = t.get("independence")
    if declared not in INDEPENDENCE_CLASSES:
        return None
    rank = INDEPENDENCE_CLASSES.index(declared)
    if t.get("attestor") in (escrow_payload.get("payer"), escrow_payload.get("payee")):
        rank = 0
    return rank


def _backed(t: Dict[str, Any], accounts: Dict[str, AccountBalance]) -> bool:
    """SPEC §9 S9.4: the bond is real value at stake — the attestor's /2
    available is non-negative."""
    a = accounts.get(t.get("attestor"))
    return a is not None and a.available_ucr >= 0


def _meets_floors(t: Dict[str, Any], cond: Dict[str, Any],
                  escrow_payload: Dict[str, Any],
                  accounts: Dict[str, AccountBalance]) -> bool:
    """The condition's independence, bond, and backing floors — shared by
    quorum counting (S9.3/4), contest qualification (S9.6), and strict
    override (S10.4)."""
    rank = _effective_class_rank(t, escrow_payload)
    if rank is None or rank < INDEPENDENCE_CLASSES.index(cond["min_independence"]):
        return False
    if t["bond_ucr"] < cond["min_bond_ucr"]:
        return False
    return _backed(t, accounts)


def _contested(t: Dict[str, Any], escrow_id: str, cond: Dict[str, Any],
               escrow_payload: Dict[str, Any],
               attestations: Dict[str, Dict[str, Any]],
               accounts: Dict[str, AccountBalance]) -> bool:
    """S9.6: a well-formed `not_occurred` on the same escrow, lane >= t's,
    meeting the floors. Equal lane blocks; it does not slash."""
    t_rank = _lane_rank(t["lane"])
    for x in attestations.values():
        if x is t or not _attestation_well_formed(x):
            continue
        if x.get("escrow_id") != escrow_id or x.get("claim") != "not_occurred":
            continue
        if _lane_rank(x["lane"]) < t_rank:
            continue
        if _meets_floors(x, cond, escrow_payload, accounts):
            return True
    return False


def _override_context(t: Dict[str, Any],
                      events: Dict[str, Dict[str, Any]]):
    """The precondition for ANY override of t (scan or named): t is
    well-formed and its escrow's outcome condition derives. Returns
    (escrow_payload, cond) or None — when no outcome condition is
    derivable, nothing overrides and every slash convicts (S10.4)."""
    if not _attestation_well_formed(t):
        return None
    escrow_id = t.get("escrow_id")
    ep = events.get(escrow_id) if isinstance(escrow_id, str) else None
    if ep is None or ep.get("kind") != "escrow":
        return None
    status, cond = _outcome_condition(ep)
    if status != "ok":
        return None
    return ep, cond


def _qualifies_as_override(x: Dict[str, Any], t: Dict[str, Any],
                           ep: Dict[str, Any], cond: Dict[str, Any],
                           accounts: Dict[str, AccountBalance]) -> bool:
    """The single per-candidate predicate (S10.4), shared by the scan and
    the G19 named-referent path so the two modes cannot drift: a
    well-formed attestation on the same escrow with the OPPOSITE claim, a
    lane STRICTLY above t's, meeting the condition's floors."""
    return (x is not t
            and _attestation_well_formed(x)
            and x.get("escrow_id") == t.get("escrow_id")
            and x.get("claim") != t["claim"]
            and _lane_rank(x["lane"]) > _lane_rank(t["lane"])
            and _meets_floors(x, cond, ep, accounts))


def _strict_override(t: Dict[str, Any],
                     attestations: Dict[str, Dict[str, Any]],
                     events: Dict[str, Dict[str, Any]],
                     accounts: Dict[str, AccountBalance]) -> bool:
    """S10.4 scan mode: does ANY strict override of t exist?"""
    ctx = _override_context(t, events)
    if ctx is None:
        return False
    ep, cond = ctx
    return any(_qualifies_as_override(x, t, ep, cond, accounts)
               for x in attestations.values())


def _named_override_ok(p: Dict[str, Any], t: Dict[str, Any],
                       attestations: Dict[str, Dict[str, Any]],
                       events: Dict[str, Dict[str, Any]],
                       accounts: Dict[str, AccountBalance]) -> bool:
    """G19 named mode (S10.4): the slash carries `override_attestation_id`
    and is judged on EXACTLY that referent — present in the ledger and
    qualifying. A qualifying override that exists but was not the one
    named does not save the slash: the naming binds. Total on junk (a
    non-string name resolves to nothing and convicts)."""
    oid = p.get("override_attestation_id")
    named = attestations.get(oid) if isinstance(oid, str) else None
    if named is None:
        return False
    ctx = _override_context(t, events)
    if ctx is None:
        return False
    ep, cond = ctx
    return _qualifies_as_override(named, t, ep, cond, accounts)


def _outcome_proof_findings(
    code: str,
    eid: str,
    p: Dict[str, Any],
    escrow_id: str,
    escrow_payload: Dict[str, Any],
    attestations: Dict[str, Dict[str, Any]],
    accounts: Dict[str, AccountBalance],
) -> List[Tuple[str, str, str]]:
    """SPEC §9 S9.1–7, applied to a release (code=S9) or a
    release-direction default resolution (code=S8, mirroring how S8
    carries S3/S4). Fail closed: an unintelligible outcome condition
    convicts EVERY disbursement to the payee."""
    findings: List[Tuple[str, str, str]] = []
    status, cond = _outcome_condition(escrow_payload)
    if status == "absent":
        return findings
    if status == "malformed":
        return [(code, eid,
                 f"{code} {eid} against unintelligible outcome condition")]
    ids = p.get("attestation_ids")
    if not isinstance(ids, list) or not ids:
        return [(code, eid, f"{code} {eid} carries no outcome proof")]
    at_tick = p.get("tick")
    counted: List[str] = []
    for aid in ids:
        t = attestations.get(aid) if isinstance(aid, str) else None
        if t is None:
            findings.append((code, eid, f"{code} {eid} references missing attestation {aid}"))
            continue
        if not _attestation_well_formed(t):
            findings.append((code, eid, f"{code} {eid} references malformed attestation {aid}"))
            continue
        if t["escrow_id"] != escrow_id:
            findings.append((code, eid, f"{code} {eid} references off-escrow attestation {aid}"))
            continue
        if t["claim"] != "occurred":
            findings.append((code, eid, f"{code} {eid} references non-occurred claim {aid}"))
            continue
        if _lane_rank(t["lane"]) < _lane_rank(cond["lane"]):
            findings.append((code, eid, f"{code} {eid} references off-lane attestation {aid}"))
            continue
        rank = _effective_class_rank(t, escrow_payload)
        if rank is None or rank < INDEPENDENCE_CLASSES.index(cond["min_independence"]):
            findings.append((code, eid, f"{code} {eid} references under-classed attestation {aid}"))
            continue
        if t["bond_ucr"] < cond["min_bond_ucr"]:
            findings.append((code, eid, f"{code} {eid} references under-bonded attestation {aid}"))
            continue
        if not _backed(t, accounts):
            findings.append((code, eid, f"{code} {eid} references unbacked attestation {aid}"))
            continue
        att_tick = t.get("tick")
        if (isinstance(at_tick, int) and not isinstance(at_tick, bool)
                and isinstance(att_tick, int) and not isinstance(att_tick, bool)
                and at_tick <= att_tick + cond["contest_ticks"]):
            findings.append((code, eid, f"{code} {eid} inside contest window of {aid}"))
            continue
        if _contested(t, escrow_id, cond, escrow_payload, attestations, accounts):
            findings.append((code, eid, f"{code} {eid} references contested attestation {aid}"))
            continue
        counted.append(t["attestor"])
    if len(counted) != len(set(counted)):
        findings.append((code, eid, f"{code} {eid} outcome proof attestors not distinct"))
    if len(set(counted)) < cond["quorum"]:
        findings.append((code, eid,
                         f"{code} {eid} outcome quorum not met "
                         f"({len(set(counted))}/{cond['quorum']})"))
    return findings


def _charge_key_set(payloads: Sequence[Any]) -> Optional[Tuple[Tuple[str, ...], ...]]:
    """Parse an escrow's charge_keys payload field; None if malformed."""
    if not isinstance(payloads, list) or not payloads:
        return None
    keys = []
    for k in payloads:
        if not isinstance(k, list) or not k or not all(isinstance(s, str) for s in k):
            return None
        keys.append(tuple(k))
    return tuple(keys)


def _touches(finding: Tuple[str, str, str], key_set: set,
             lease_key: Dict[str, tuple], charge_key: Dict[str, tuple]) -> bool:
    """SETTLEMENT-SPEC §3 'touches': map an I-finding's subject back to the
    account keys it is about. Unknown codes touch everything (fail closed).

    charge-attribution/1 joined 2026-07-08 (ATTRIBUTION-SPEC V.7):
    V1/V3/V4 subjects are ["att", derived, source] — they touch every
    exposure key of the named SOURCE among the escrow's charge_keys (a
    lying split claim dirties that contributor's accounts); V2/V5 and
    any future V-code fall to the fail-closed default."""
    code, subj, _prose = finding
    key_jsons = {canonical_json(list(k)) for k in key_set}
    if code in _KEY_SUBJECT_CODES:
        return subj in key_jsons
    if code in _LEASE_SUBJECT_CODES:
        return lease_key.get(subj) in key_set
    if code in _CHARGE_SUBJECT_CODES:
        return charge_key.get(subj) in key_set
    if code == "I8":
        try:
            node_lease_seq = json.loads(subj)
            return lease_key.get(node_lease_seq[1]) in key_set
        except Exception:
            return True
    if code in ("V1", "V3", "V4"):
        try:
            att = json.loads(subj)
            source = att[2]
            return any(
                len(k) == 3 and k[0] == "exp" and k[1] == source
                for k in key_set
            )
        except Exception:
            return True
    return True  # future code: fail closed


def audit_settlement_findings(ledger: Ledger) -> List[Tuple[str, str, str]]:
    """SETTLEMENT-SPEC §3 + §9 — S1..S10 as (code, subject, prose)
    triples. Total: never raises on adversarial content."""
    findings: List[Tuple[str, str, str]] = []
    accounts, escrows, bonds = settlement_fold_full(ledger)
    events = getattr(ledger, "_events")

    # id -> key maps for S3/S4 subject resolution
    lease_key: Dict[str, tuple] = {}
    charge_key: Dict[str, tuple] = {}
    attestations: Dict[str, Dict[str, Any]] = {}
    # Key maps go through _hashable_key, the F2 discipline: a bare
    # isinstance(key, list) gate admits a NESTED-list key, producing a
    # tuple-containing-a-list whose set membership raises in _touches —
    # one forged lease/charge crashed audit_settlement_codes for any
    # artifact holding a required_clean release (fable review blocking
    # finding, 2026-07-06). An unparseable key stays out of the map; the
    # event is already convicted (I5/I4) and the absent entry falls to
    # the existing None branches. Verdict bytes unchanged.
    for eid, p in events.items():
        kind = p.get("kind")
        if kind == "lease":
            hk = _hashable_key(p)
            if hk is not None:
                lease_key[eid] = hk
        elif kind == "charge":
            hk = _hashable_key(p)
            if hk is not None:
                charge_key[eid] = hk
        elif kind == "outcome_attestation":
            attestations[eid] = p

    i_findings = _court_findings(ledger)

    # ---- ATTRIBUTION-SPEC Part II: split-bound escrows (S11/S12) ----
    # The bound rows are RECOMPUTED from the DAG per escrow — no report
    # event is consulted on the value path. None = unauditable game
    # (fail closed toward payees; refund stays open).
    _rows_cache: Dict[str, Optional[List[Dict[str, Any]]]] = {}

    def _bound_rows(esid: str, ep: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        if esid in _rows_cache:
            return _rows_cache[esid]
        sp = ep.get("split")
        rows: Optional[List[Dict[str, Any]]] = None
        if _split_well_formed(sp) and _is_uint(ep.get("amount_ucr")):
            rows = recomputed_shares(
                ledger, sp["derived"], sp.get("node"),
                sp.get("coupling_tick"), ep["amount_ucr"],
            )
        _rows_cache[esid] = rows
        return rows

    def _split_release_findings(
        eid: str, p: Dict[str, Any], esid: str, ep: Dict[str, Any]
    ) -> None:
        """S11 — the row discipline (ATTRIBUTION-SPEC V.9), applied to
        releases and release-direction defaults against split escrows."""
        b = p.get("beneficiary")
        if not isinstance(b, str):
            findings.append(
                ("S11", eid, f"S11 {eid} split disbursement names no beneficiary")
            )
            return
        rows = _bound_rows(esid, ep)
        if rows is None:
            findings.append(
                ("S11", eid,
                 f"S11 {eid} against unauditable split game (fail closed)")
            )
            return
        row = next((r for r in rows if r["source"] == b), None)
        if row is None:
            findings.append(
                ("S11", eid, f"S11 {eid} beneficiary {b!r} has no bound row")
            )
            return
        if p.get("amount_ucr") != row["payout_ucr"]:
            findings.append(
                ("S11", eid,
                 f"S11 {eid} pays {p.get('amount_ucr')} != bound row "
                 f"{row['payout_ucr']} for {b!r}")
            )

    # S1 — overdraft.
    for name in sorted(accounts):
        if accounts[name].available_ucr < 0:
            findings.append(("S1", name, f"S1 account {name!r} overdrawn "
                             f"(available {accounts[name].available_ucr} ucr)"))

    # S2 — escrow over-disbursed.
    for eid in sorted(escrows):
        st = escrows[eid]
        if st.released_ucr + st.refunded_ucr > st.amount_ucr:
            findings.append(("S2", eid, f"S2 escrow {eid} over-disbursed"))

    # S10 — bond over-resolved (subject: the attestation id — the S2 pattern).
    for tid in sorted(bonds):
        b = bonds[tid]
        if b.returned_ucr + b.slashed_ucr > b.amount_ucr:
            findings.append(("S10", tid, f"S10 bond {tid} over-resolved"))

    # per-event checks.
    seq_seen: Dict[Tuple[str, str, int], str] = {}
    for eid, p in events.items():
        kind = p.get("kind")
        if kind not in SETTLEMENT_KINDS:
            continue

        # S6 — well-formedness. (outcome_attestation carries bond_ucr, not
        # amount_ucr — SPEC §9.)
        malformed = False
        amount_field = "bond_ucr" if kind == "outcome_attestation" else "amount_ucr"
        if not _is_uint(p.get(amount_field)):
            malformed = True
        seq = p.get("seq")
        if not _is_uint(seq) or (isinstance(seq, int) and seq < 1):
            malformed = True
        if kind == "deposit" and not isinstance(p.get("account"), str):
            malformed = True
        if kind == "escrow":
            # ATTRIBUTION-SPEC V.8: a split escrow's legal defaults are
            # release_by_report / refund_to_payer; release_by_report on a
            # non-split escrow has no rows to release by; split + outcome
            # is refused (a /3 with its own story), not improvised.
            legal_defaults = (
                SPLIT_DEFAULT_DIRECTIONS if "split" in p else DEFAULT_DIRECTIONS
            )
            if (
                _charge_key_set(p.get("charge_keys")) is None
                or p.get("default_on_expiry") not in legal_defaults
                or not isinstance(p.get("payer"), str)
                or not isinstance(p.get("payee"), str)
            ):
                malformed = True
            elif "split" in p and not _split_well_formed(p.get("split")):
                malformed = True
            elif "split" in p and "outcome" in p:
                malformed = True
            elif "outcome" in p and _outcome_condition(p)[0] == "malformed":
                malformed = True
        if kind in ("release", "refund", "default_resolution") and not isinstance(
            p.get("escrow_id"), str
        ):
            malformed = True
        if kind == "outcome_attestation" and not _attestation_well_formed(p):
            malformed = True
        if kind == "bond_resolution" and (
            not isinstance(p.get("attestation_id"), str)
            or not isinstance(p.get("submitter"), str)
            or p.get("direction") not in BOND_DIRECTIONS
        ):
            malformed = True
        if malformed:
            findings.append(("S6", eid, f"S6 malformed settlement event {eid}"))

        # S5 — fact identity / equivocation. Actor is the authoring field.
        if _is_uint(seq):
            actor_field = {
                "default_resolution": "submitter",
                "bond_resolution": "submitter",
                "outcome_attestation": "attestor",
            }.get(kind, "issuer")
            ident = (str(p.get(actor_field, "")), str(kind), seq)
            prior = seq_seen.get(ident)
            if prior is not None and prior != eid:
                findings.append(
                    ("S5", canonical_json(list(ident)),
                     f"S5 equivocation: two settlement facts claim {ident}")
                )
            seq_seen[ident] = eid

        # ---- S10 — bond resolutions (SPEC §9) ----
        if kind == "bond_resolution":
            aid = p.get("attestation_id")
            t = attestations.get(aid) if isinstance(aid, str) else None
            if t is None:
                findings.append(
                    ("S10", eid, f"S10 bond_resolution {eid} references unknown attestation")
                )
                continue
            direction = p.get("direction")
            override = _strict_override(t, attestations, events, accounts)
            t_escrow = events.get(t.get("escrow_id")) if isinstance(t.get("escrow_id"), str) else None
            if t_escrow is not None and t_escrow.get("kind") != "escrow":
                t_escrow = None
            status, cond = _outcome_condition(t_escrow) if t_escrow is not None else ("absent", None)
            if direction == "return_to_attestor":
                # premature: only when a window is derivable (SPEC §9 S10.3)
                bt, tt = p.get("tick"), t.get("tick")
                if (status == "ok"
                        and isinstance(bt, int) and not isinstance(bt, bool)
                        and isinstance(tt, int) and not isinstance(tt, bool)
                        and bt <= tt + cond["contest_ticks"]):
                    findings.append(
                        ("S10", eid, f"S10 premature bond return {eid} (contest window open)")
                    )
                if override:
                    findings.append(
                        ("S10", eid, f"S10 bond return {eid} despite strict override")
                    )
            elif direction == "slash":
                if "override_attestation_id" in p:
                    # G19 named mode: the naming binds — the audit judges
                    # the cited referent, never the best override available.
                    if not _named_override_ok(p, t, attestations, events,
                                              accounts):
                        findings.append(
                            ("S10", eid,
                             f"S10 slash {eid} names an absent or "
                             f"non-qualifying override")
                        )
                elif not override:
                    findings.append(
                        ("S10", eid, f"S10 slash {eid} without strict override")
                    )
                if _slash_beneficiary(t, events) is None:
                    findings.append(
                        ("S10", eid, f"S10 slash {eid} with underivable beneficiary")
                    )
            continue

        if kind not in ("release", "refund", "default_resolution"):
            continue

        esid = p.get("escrow_id")
        escrow_st = escrows.get(esid) if isinstance(esid, str) else None
        if escrow_st is None:
            findings.append(("S2", eid, f"S2 {kind} {eid} references unknown escrow"))
            if kind == "release":
                # existence/acceptance checks still run without the escrow
                self_contained_release_checks(findings, eid, p, events, None, charge_key)
            continue

        if kind == "refund":
            continue  # refunds need no receipt, no clean court, no expiry gate

        ep = escrow_st.payload
        key_set_t = _charge_key_set(ep.get("charge_keys"))
        key_set = set(key_set_t) if key_set_t else set()

        if kind == "default_resolution":
            # ---- S8 — the anti-holdup clause, policed ----
            tick, expires = p.get("tick"), ep.get("expires_tick")
            premature = (
                isinstance(tick, int) and not isinstance(tick, bool)
                and isinstance(expires, int) and not isinstance(expires, bool)
                and tick <= expires
            )
            if "outcome" in ep:
                # conditional direction (SPEC §7.4): quorum proof present
                # = release, else refund (the declared default).
                if premature:
                    findings.append(
                        ("S8", eid, f"S8 premature default_resolution {eid} (escrow not expired)")
                    )
                ids = p.get("attestation_ids")
                if isinstance(ids, list) and ids:
                    # release-direction: work receipts, clean court, AND the
                    # outcome proof — all reported under S8 (SPEC §9).
                    self_contained_release_checks(
                        findings, eid, p, events, key_set or None, charge_key, code="S8"
                    )
                    if ep.get("required_clean") is True and key_set:
                        for f in i_findings:
                            if _touches(f, key_set, lease_key, charge_key):
                                findings.append(
                                    ("S8", eid,
                                     f"S8 default release {eid} against dirty court ({f[0]} {f[1]})")
                                )
                                break
                    findings.extend(_outcome_proof_findings(
                        "S8", eid, p, escrow_st.escrow_id, ep, attestations, accounts
                    ))
                continue
            direction = ep.get("default_on_expiry")
            legal_defaults = (
                SPLIT_DEFAULT_DIRECTIONS if "split" in ep else DEFAULT_DIRECTIONS
            )
            if direction not in legal_defaults:
                findings.append(
                    ("S2", eid,
                     f"S2 default_resolution {eid} against escrow with unresolvable default")
                )
                continue
            if premature:
                findings.append(
                    ("S8", eid, f"S8 premature default_resolution {eid} (escrow not expired)")
                )
            if direction in ("release_to_payee", "release_by_report"):
                # a release in all but name: receipt + clean-court conditions
                # apply unchanged, reported under S8 (SPEC §3); the per-row
                # default additionally carries the row discipline (S11 —
                # ATTRIBUTION-SPEC V.10, the F4 safety-shape).
                self_contained_release_checks(
                    findings, eid, p, events, key_set or None, charge_key, code="S8"
                )
                if ep.get("required_clean") is True and key_set:
                    for f in i_findings:
                        if _touches(f, key_set, lease_key, charge_key):
                            findings.append(
                                ("S8", eid,
                                 f"S8 default release {eid} against dirty court ({f[0]} {f[1]})")
                            )
                            break
                if direction == "release_by_report":
                    _split_release_findings(eid, p, esid, ep)
            continue

        # ---- release-only checks against the resolved escrow ----
        self_contained_release_checks(findings, eid, p, events, key_set or None, charge_key)

        # S7 — expiry.
        tick, expires = p.get("tick"), ep.get("expires_tick")
        if (isinstance(tick, int) and not isinstance(tick, bool)
                and isinstance(expires, int) and not isinstance(expires, bool)
                and tick > expires):
            findings.append(("S7", eid, f"S7 release {eid} after escrow expiry"))

        # S4 — dirty court on the escrow's keys.
        if ep.get("required_clean") is True and key_set:
            for f in i_findings:
                if _touches(f, key_set, lease_key, charge_key):
                    findings.append(
                        ("S4", eid, f"S4 release {eid} against dirty court ({f[0]} {f[1]})")
                    )
                    break

        # S9 — the outcome proof (SPEC §9), releases only.
        if "outcome" in ep:
            findings.extend(_outcome_proof_findings(
                "S9", eid, p, escrow_st.escrow_id, ep, attestations, accounts
            ))

        # S11 — the split row discipline (ATTRIBUTION-SPEC V.9), releases only.
        if "split" in ep:
            _split_release_findings(eid, p, esid, ep)

    # ---- S12 — split row overdraw (ATTRIBUTION-SPEC V.9): cumulative
    # fold-counted credits per (escrow, beneficiary) vs the bound row.
    # Independent of the per-event exact-row arm so cumulative dishonesty
    # convicts even where per-event checks were evaded. Fail closed: an
    # unauditable or row-less game bounds every beneficiary at zero.
    for esid in sorted(escrows):
        ep = escrows[esid].payload
        if "split" not in ep:
            continue
        rows = _bound_rows(esid, ep)
        row_pay = {r["source"]: r["payout_ucr"] for r in rows} if rows else {}
        by_report_default = (
            ep.get("default_on_expiry") == "release_by_report"
            and "outcome" not in ep
        )
        sums: Dict[str, int] = {}
        for _eid2, p2 in events.items():
            k2 = p2.get("kind")
            if not (k2 == "release" or (k2 == "default_resolution" and by_report_default)):
                continue
            if p2.get("escrow_id") != esid:
                continue
            amt, b = p2.get("amount_ucr"), p2.get("beneficiary")
            if _is_uint(amt) and isinstance(b, str):
                sums[b] = sums.get(b, 0) + amt
        for b in sorted(sums):
            if sums[b] > row_pay.get(b, 0):
                findings.append(
                    ("S12", canonical_json(["split", esid, b]),
                     f"S12 split row overdraw: {sums[b]} ucr credited to "
                     f"{b!r} against escrow {esid} > bound row "
                     f"{row_pay.get(b, 0)}")
                )

    return findings


def self_contained_release_checks(
    findings: List[Tuple[str, str, str]],
    eid: str,
    p: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    key_set: Optional[set],
    charge_key: Dict[str, tuple],
    code: str = "S3",
) -> None:
    """The work receipt: non-empty, every id resolves to an ACCEPTED
    charge, on the escrow's keys when the escrow resolved. Emitted as S3
    for releases, S8 for release-direction default resolutions (SPEC §3)."""
    cids = p.get("charge_ids")
    if not isinstance(cids, list) or not cids:
        findings.append((code, eid, f"{code} release {eid} carries no work receipt"))
        return
    for cid in cids:
        ch = events.get(cid) if isinstance(cid, str) else None
        if ch is None or ch.get("kind") != "charge":
            findings.append((code, eid, f"{code} release {eid} references missing work {cid}"))
            continue
        if ch.get("accepted") is not True:
            findings.append((code, eid, f"{code} release {eid} pays for refused work {cid}"))
            continue
        if key_set is not None and charge_key.get(cid) not in key_set:
            findings.append((code, eid, f"{code} release {eid} pays for off-key work {cid}"))


def audit_settlement(ledger: Ledger) -> List[str]:
    """Human-facing: prose findings. Empty list = clean."""
    return [prose for _c, _s, prose in audit_settlement_findings(ledger)]


def audit_settlement_codes(ledger: Ledger) -> List[str]:
    """Conformance surface: sorted, deduplicated '<code> <subject>'."""
    return sorted({f"{c} {s}" for c, s, _ in audit_settlement_findings(ledger)})


# ---- the honest issuer ----

@dataclass
class SettlementIssuer:
    """The escrow authority's honest front-end (SETTLEMENT-SPEC §4). Mirrors
    LeaseIssuer: partition, not consensus — this issuer refuses live, and a
    forged history is convicted after merge by the S-codes.

    State is recomputed from the ledger on every call: the issuer is
    restart-safe by construction (the same hydration lesson as leases).

    charge-identity/2 (IDENTITY-SPEC §7): construct with `signer` when the
    issuer id is a key — every deposit/escrow/release/refund is then
    signed; the constructor fails closed on the three mismatch cases."""

    issuer: str
    ledger: Ledger
    signer: Optional[Signer] = None

    def __post_init__(self) -> None:
        self.signer = require_signer(self.issuer, self.signer, "settlement issuer")

    def _sign(self, ev):
        return self.signer.sign(ev) if self.signer is not None else ev

    def _next_seq(self, kind: str) -> int:
        top = 0
        for _eid, p in _settlement_events(self.ledger):
            if p.get("kind") == kind and p.get("issuer") == self.issuer:
                seq = p.get("seq")
                if _is_uint(seq):
                    top = max(top, seq)
        return top + 1

    def deposit(self, account: str, amount_ucr: int, tick: int) -> DepositEvent:
        if not (_is_uint(amount_ucr) and amount_ucr > 0):
            raise SettlementRefused("deposit amount must be a positive integer")
        ev = self._sign(
            DepositEvent(account, amount_ucr, self.issuer, self._next_seq("deposit"), tick)
        )
        self.ledger.add(ev)
        return ev

    def escrow(
        self,
        payer: str,
        payee: str,
        amount_ucr: int,
        charge_keys: Sequence[Key],
        expires_tick: int,
        tick: int,
        required_clean: bool = True,
        default_on_expiry: str = "refund_to_payer",
        outcome: Optional[OutcomeCondition] = None,
        split: Optional[SplitCondition] = None,
    ) -> EscrowEvent:
        if not (_is_uint(amount_ucr) and amount_ucr > 0):
            raise SettlementRefused("escrow amount must be a positive integer")
        if not charge_keys:
            raise SettlementRefused("an escrow binds to at least one metered account")
        legal_defaults = (
            SPLIT_DEFAULT_DIRECTIONS if split is not None else DEFAULT_DIRECTIONS
        )
        if default_on_expiry not in legal_defaults:
            raise SettlementRefused(
                f"default_on_expiry must be one of {legal_defaults}"
            )
        if outcome is not None and default_on_expiry != "refund_to_payer":
            raise SettlementRefused(
                "an outcome-conditioned escrow defaults to refund_to_payer "
                "(SPEC §7.1: the payer keeps the money unless the outcome "
                "provably occurred)"
            )
        if outcome is not None and split is not None:
            raise SettlementRefused(
                "split + outcome on one escrow is refused (ATTRIBUTION-SPEC "
                "V.8: outcome-conditioned split pots are a /3, not an "
                "improvisation)"
            )
        accounts, _ = settlement_fold(self.ledger)
        available = accounts[payer].available_ucr if payer in accounts else 0
        if amount_ucr > available:
            raise SettlementRefused(
                f"overdraft: escrow {amount_ucr} > available {available} for {payer!r}"
            )
        ev = self._sign(EscrowEvent(
            payer=payer, payee=payee, amount_ucr=amount_ucr,
            charge_keys=tuple(tuple(k) for k in charge_keys),
            required_clean=required_clean, expires_tick=expires_tick,
            default_on_expiry=default_on_expiry,
            issuer=self.issuer, seq=self._next_seq("escrow"), tick=tick,
            outcome=outcome, split=split,
        ))
        self.ledger.add(ev)
        return ev

    def _release_preflight(
        self,
        escrow: EscrowEvent,
        amount_ucr: int,
        charge_ids: Sequence[str],
        tick: int,
    ) -> None:
        """The release-direction checks shared by release and
        release_split: amount, receipt, expiry, remaining, clean court."""
        if not (_is_uint(amount_ucr) and amount_ucr > 0):
            raise SettlementRefused("release amount must be a positive integer")
        if not charge_ids:
            raise SettlementRefused("a release pays for work: the receipt cannot be empty")
        if tick > escrow.expires_tick:
            raise SettlementRefused("escrow expired; only refund remains")
        _, escrows = settlement_fold(self.ledger)
        st = escrows.get(escrow.id)
        if st is None:
            raise SettlementRefused("unknown escrow (not in this ledger)")
        if amount_ucr > st.remaining_ucr:
            raise SettlementRefused(
                f"over-release: {amount_ucr} > remaining {st.remaining_ucr}"
            )
        events = getattr(self.ledger, "_events")
        key_set = set(escrow.charge_keys)
        for cid in charge_ids:
            ch = events.get(cid)
            if ch is None or ch.get("kind") != "charge":
                raise SettlementRefused(f"work receipt {cid} is not a charge in this ledger")
            if ch.get("accepted") is not True:
                raise SettlementRefused(f"work receipt {cid} was refused; not payable")
            # _hashable_key, not tuple(): a forged charge with a nested-list
            # key crashed this membership test with TypeError where
            # SettlementRefused is the contract (fable review, 2026-07-06).
            ch_key = _hashable_key(ch)
            if ch_key is None or ch_key not in key_set:
                raise SettlementRefused(f"work receipt {cid} is off this escrow's keys")
        if escrow.required_clean:
            lease_key = {e: hk for e, p in events.items()
                         if p.get("kind") == "lease"
                         and (hk := _hashable_key(p)) is not None}
            charge_key = {e: hk for e, p in events.items()
                          if p.get("kind") == "charge"
                          and (hk := _hashable_key(p)) is not None}
            for f in _court_findings(self.ledger):
                if _touches(f, key_set, lease_key, charge_key):
                    raise SettlementRefused(f"court is dirty on escrowed keys: {f[2]}")

    def release(
        self,
        escrow: EscrowEvent,
        amount_ucr: int,
        charge_ids: Sequence[str],
        tick: int,
        attestation_ids: Sequence[str] = (),
    ) -> ReleaseEvent:
        self._release_preflight(escrow, amount_ucr, charge_ids, tick)
        if escrow.outcome is not None:
            _refuse_unless_quorum(self.ledger, escrow, attestation_ids, tick)
        elif attestation_ids:
            raise SettlementRefused("attestation proof against an unconditioned escrow")
        if escrow.split is not None:
            raise SettlementRefused(
                "a split-bound escrow disburses by row: use release_split"
            )
        ev = self._sign(ReleaseEvent(
            escrow_id=escrow.id, amount_ucr=amount_ucr,
            charge_ids=tuple(charge_ids), issuer=self.issuer,
            seq=self._next_seq("release"), tick=tick,
            attestation_ids=tuple(attestation_ids),
        ))
        self.ledger.add(ev)
        return ev

    def release_split(
        self,
        escrow: EscrowEvent,
        beneficiary: str,
        charge_ids: Sequence[str],
        tick: int,
    ) -> ReleaseEvent:
        """ATTRIBUTION-SPEC V.11 — pay one bound row, exactly. The amount
        is COMPUTED from the recomputed rows (callers cannot pass one);
        refuses live what S11/S12 convict after merge: unknown
        beneficiary, unauditable game, an already-paid row."""
        sp = escrow.split
        if sp is None:
            raise SettlementRefused("not a split-bound escrow; use release")
        rows = recomputed_shares(
            self.ledger, sp.derived, sp.node, sp.coupling_tick,
            escrow.amount_ucr,
        )
        if rows is None:
            raise SettlementRefused(
                "the bound game is unauditable (no exp-emissions at the "
                "coupling, or arity over NMAX); only refund remains"
            )
        row = next((r for r in rows if r["source"] == beneficiary), None)
        if row is None:
            raise SettlementRefused(
                f"{beneficiary!r} has no bound row in this escrow's split"
            )
        events = getattr(self.ledger, "_events")
        for _eid, p in events.items():
            if (p.get("kind") in ("release", "default_resolution")
                    and p.get("escrow_id") == escrow.id
                    and p.get("beneficiary") == beneficiary
                    and _is_uint(p.get("amount_ucr"))):
                raise SettlementRefused(
                    f"row {beneficiary!r} already disbursed (rows pay once)"
                )
        self._release_preflight(escrow, row["payout_ucr"], charge_ids, tick)
        ev = self._sign(ReleaseEvent(
            escrow_id=escrow.id, amount_ucr=row["payout_ucr"],
            charge_ids=tuple(charge_ids), issuer=self.issuer,
            seq=self._next_seq("release"), tick=tick,
            beneficiary=beneficiary,
        ))
        self.ledger.add(ev)
        return ev

    def refund(self, escrow: EscrowEvent, amount_ucr: int, tick: int) -> RefundEvent:
        if not (_is_uint(amount_ucr) and amount_ucr > 0):
            raise SettlementRefused("refund amount must be a positive integer")
        _, escrows = settlement_fold(self.ledger)
        st = escrows.get(escrow.id)
        if st is None:
            raise SettlementRefused("unknown escrow (not in this ledger)")
        if amount_ucr > st.remaining_ucr:
            raise SettlementRefused(
                f"over-refund: {amount_ucr} > remaining {st.remaining_ucr}"
            )
        ev = self._sign(RefundEvent(
            escrow_id=escrow.id, amount_ucr=amount_ucr, issuer=self.issuer,
            seq=self._next_seq("refund"), tick=tick,
        ))
        self.ledger.add(ev)
        return ev


# ---- permissionless resolution (the anti-holdup clause, exercised) ----

def _next_actor_seq(ledger: Ledger, kind: str, actor_field: str, actor: str) -> int:
    top = 0
    for _eid, p in _settlement_events(ledger):
        if p.get("kind") == kind and p.get(actor_field) == actor:
            s = p.get("seq")
            if _is_uint(s):
                top = max(top, s)
    return top + 1


def _refuse_unless_quorum(
    ledger: Ledger,
    escrow: EscrowEvent,
    attestation_ids: Sequence[str],
    tick: int,
) -> None:
    """The live mirror of S9 (SPEC §10): raise on the first way the
    presented outcome proof would convict after merge."""
    if not attestation_ids:
        raise SettlementRefused(
            "an outcome-conditioned disbursement carries an outcome proof: "
            "attestation_ids cannot be empty"
        )
    events = getattr(ledger, "_events")
    accounts, _escrows, _bonds = settlement_fold_full(ledger)
    attestations = {e: q for e, q in events.items()
                    if q.get("kind") == "outcome_attestation"}
    pseudo = {"attestation_ids": list(attestation_ids), "tick": tick}
    problems = _outcome_proof_findings(
        "S9", "(live)", pseudo, escrow.id, escrow.payload(), attestations, accounts
    )
    if problems:
        raise SettlementRefused(problems[0][2])


def resolve_default(
    ledger: Ledger,
    escrow: EscrowEvent,
    submitter: str,
    amount_ucr: int,
    tick: int,
    charge_ids: Sequence[str] = (),
    attestation_ids: Sequence[str] = (),
    signer: Optional[Signer] = None,
) -> DefaultResolutionEvent:
    """Exercise an expired escrow's declared default (SPEC §1.5, §7.4).
    NOT an issuer method on purpose: any party may call this — the payee
    against a silent issuer is the point. For an outcome-conditioned
    escrow the declared terminal rule is conditional: presenting
    `attestation_ids` (with `charge_ids`) claims the release direction;
    presenting none claims the refund. The same honest guards the audit
    (S8) would convict are enforced live; a caller that bypasses them by
    forging the event is convicted after merge instead."""
    signer = require_signer(submitter, signer, "default submitter")
    if not (_is_uint(amount_ucr) and amount_ucr > 0):
        raise SettlementRefused("resolution amount must be a positive integer")
    if tick <= escrow.expires_tick:
        raise SettlementRefused(
            f"escrow not expired until tick {escrow.expires_tick}; defaults wait"
        )
    _, escrows = settlement_fold(ledger)
    st = escrows.get(escrow.id)
    if st is None:
        raise SettlementRefused("unknown escrow (not in this ledger)")
    if amount_ucr > st.remaining_ucr:
        raise SettlementRefused(
            f"over-resolution: {amount_ucr} > remaining {st.remaining_ucr}"
        )
    if escrow.outcome is None and attestation_ids:
        raise SettlementRefused("attestation proof against an unconditioned escrow")
    release_direction = (
        (escrow.outcome is not None and bool(attestation_ids))
        or (escrow.outcome is None and escrow.default_on_expiry == "release_to_payee")
    )
    if release_direction:
        if not charge_ids:
            raise SettlementRefused(
                "a release-direction default pays for work: the receipt cannot be empty"
            )
        events = getattr(ledger, "_events")
        key_set = set(escrow.charge_keys)
        for cid in charge_ids:
            ch = events.get(cid)
            if ch is None or ch.get("kind") != "charge":
                raise SettlementRefused(f"work receipt {cid} is not a charge in this ledger")
            if ch.get("accepted") is not True:
                raise SettlementRefused(f"work receipt {cid} was refused; not payable")
            # _hashable_key, not tuple(): same F2 discipline as release —
            # a nested-list charge key must refuse, never TypeError.
            ch_key = _hashable_key(ch)
            if ch_key is None or ch_key not in key_set:
                raise SettlementRefused(f"work receipt {cid} is off this escrow's keys")
        if escrow.required_clean:
            lease_key = {e: hk for e, p in events.items()
                         if p.get("kind") == "lease"
                         and (hk := _hashable_key(p)) is not None}
            charge_key = {e: hk for e, p in events.items()
                          if p.get("kind") == "charge"
                          and (hk := _hashable_key(p)) is not None}
            for f in _court_findings(ledger):
                if _touches(f, key_set, lease_key, charge_key):
                    raise SettlementRefused(f"court is dirty on escrowed keys: {f[2]}")
        if escrow.outcome is not None:
            _refuse_unless_quorum(ledger, escrow, attestation_ids, tick)

    ev = DefaultResolutionEvent(
        escrow_id=escrow.id, amount_ucr=amount_ucr,
        charge_ids=tuple(charge_ids), submitter=submitter,
        seq=_next_actor_seq(ledger, "default_resolution", "submitter", submitter),
        tick=tick,
        attestation_ids=tuple(attestation_ids),
    )
    if signer is not None:
        ev = signer.sign(ev)
    ledger.add(ev)
    return ev


# ---- /2 permissionless outcome machinery (SPEC §10) ----

def attest_outcome(
    ledger: Ledger,
    escrow: EscrowEvent,
    attestor: str,
    claim: str,
    lane: str,
    independence: str,
    bond_ucr: int,
    tick: int,
    evidence: str = "",
    signer: Optional[Signer] = None,
) -> OutcomeAttestationEvent:
    """Any party may attest — admission to the QUORUM is decided by the
    audit against the escrow's declared floors, not by this front. The
    honest guards refuse what S9/S1 would convict after merge. Attesting
    `not_occurred` is the sanctioned contest move (same bond discipline)."""
    signer = require_signer(attestor, signer, "attestor")
    if escrow.outcome is None:
        raise SettlementRefused("escrow declares no outcome condition; nothing to attest")
    if escrow.id not in getattr(ledger, "_events"):
        raise SettlementRefused("unknown escrow (not in this ledger)")
    if claim not in OUTCOME_CLAIMS:
        raise SettlementRefused(f"claim must be one of {OUTCOME_CLAIMS}")
    if lane not in OUTCOME_LANES:
        raise SettlementRefused(f"lane must be one of {OUTCOME_LANES}")
    cond = escrow.outcome
    if OUTCOME_LANES.index(lane) < OUTCOME_LANES.index(cond.lane):
        raise SettlementRefused(
            "attestation lane below the condition's lane; it could never count"
        )
    if independence not in INDEPENDENCE_CLASSES:
        raise SettlementRefused(f"independence must be one of {INDEPENDENCE_CLASSES}")
    effective = (0 if attestor in (escrow.payer, escrow.payee)
                 else INDEPENDENCE_CLASSES.index(independence))
    if effective < INDEPENDENCE_CLASSES.index(cond.min_independence):
        raise SettlementRefused(
            "effective independence class below the condition's floor"
        )
    if not _is_uint(bond_ucr):
        raise SettlementRefused("bond must be a uint")
    if bond_ucr < cond.min_bond_ucr:
        raise SettlementRefused(
            f"bond {bond_ucr} below the condition's floor {cond.min_bond_ucr}"
        )
    accounts, _escrows, _bonds = settlement_fold_full(ledger)
    available = accounts[attestor].available_ucr if attestor in accounts else 0
    if bond_ucr > available:
        raise SettlementRefused(
            f"unbacked bond: {bond_ucr} > available {available} for {attestor!r}"
        )
    ev = OutcomeAttestationEvent(
        escrow_id=escrow.id, claim=claim, lane=lane,
        independence=independence, evidence=evidence,
        bond_ucr=bond_ucr, attestor=attestor,
        seq=_next_actor_seq(ledger, "outcome_attestation", "attestor", attestor),
        tick=tick,
    )
    if signer is not None:
        ev = signer.sign(ev)
    ledger.add(ev)
    return ev


def resolve_bond(
    ledger: Ledger,
    attestation: OutcomeAttestationEvent,
    submitter: str,
    direction: str,
    amount_ucr: int,
    tick: int,
    override_attestation_id: Optional[str] = None,
    signer: Optional[Signer] = None,
) -> BondResolutionEvent:
    """Permissionless bond resolution (SPEC §7.3, §10): return after an
    uncontested window, slash only under a strict override. The honest
    guards mirror S10; forging past them is convicted after merge."""
    signer = require_signer(submitter, signer, "bond submitter")
    if direction not in BOND_DIRECTIONS:
        raise SettlementRefused(f"direction must be one of {BOND_DIRECTIONS}")
    if not (_is_uint(amount_ucr) and amount_ucr > 0):
        raise SettlementRefused("resolution amount must be a positive integer")
    accounts, _escrows, bonds = settlement_fold_full(ledger)
    b = bonds.get(attestation.id)
    if b is None:
        raise SettlementRefused("unknown attestation (not in this ledger)")
    if amount_ucr > b.remaining_ucr:
        raise SettlementRefused(
            f"over-resolution: {amount_ucr} > remaining {b.remaining_ucr}"
        )
    events = getattr(ledger, "_events")
    attestations = {e: q for e, q in events.items()
                    if q.get("kind") == "outcome_attestation"}
    t = events[attestation.id]
    override = _strict_override(t, attestations, events, accounts)
    ep = events.get(attestation.escrow_id)
    if ep is not None and ep.get("kind") != "escrow":
        ep = None
    status, cond = _outcome_condition(ep) if ep is not None else ("absent", None)
    if direction == "return_to_attestor":
        if status == "ok" and tick <= attestation.tick + cond["contest_ticks"]:
            raise SettlementRefused("contest window still open; returns wait")
        if override:
            raise SettlementRefused(
                "bond overridden by strictly better evidence; not returnable"
            )
    else:
        if override_attestation_id is not None:
            # G19: the honest front refuses a slash that names a referent
            # the audit would convict — absent or non-qualifying.
            if not _named_override_ok(
                {"override_attestation_id": override_attestation_id},
                t, attestations, events, accounts,
            ):
                raise SettlementRefused(
                    "named override is absent or non-qualifying; "
                    "a slash is judged on the evidence it cites"
                )
        elif not override:
            raise SettlementRefused(
                "no strict override; a bond is slashed only by better evidence"
            )
    ev = BondResolutionEvent(
        attestation_id=attestation.id, amount_ucr=amount_ucr,
        direction=direction, submitter=submitter,
        seq=_next_actor_seq(ledger, "bond_resolution", "submitter", submitter),
        tick=tick,
        override_attestation_id=(
            override_attestation_id if direction == "slash" else None
        ),
    )
    if signer is not None:
        ev = signer.sign(ev)
    ledger.add(ev)
    return ev
