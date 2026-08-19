"""The D1 bounty engine: one cycle, end to end, under the egress accountant.

Gate walk (a compressed `core.ts` Gate sequence):

    grant -> emit(metered) -> oracle_score -> conflict_check -> accept
          -> settle(heldback) -> regression_window -> release | clawback

Everything is ledgered; the run emits a PlainAccount receipt whose negative
space (what did NOT cross, what the system cannot promise) is first-class.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .bounty import (
    CreditSettlement,
    EvaluatorOracle,
    Finding,
    PriceSchedule,
    SettlementPayoutAuthorization,
    score_against_rubric,
)
from .egress import (
    CapacityEstimate,
    CompositionKey,
    EgressAccountant,
    EstimatorAttestation,
    estimate_total_bits,
    sha,
)


@dataclass
class LedgerEntry:
    seq: int
    tick: int
    actor: str
    action: str
    detail: str
    parent: Optional[int]
    detail_hash: str = ""

    def finalize(self) -> "LedgerEntry":
        self.detail_hash = sha(f"{self.seq}:{self.actor}:{self.action}:{self.detail}:{self.parent}")
        return self


@dataclass
class PlainAccount:
    lane_id: str
    what_crossed: List[str] = field(default_factory=list)
    what_did_not_cross: List[str] = field(default_factory=list)
    who_was_paid: List[str] = field(default_factory=list)
    what_it_cannot_promise: List[str] = field(default_factory=list)


@dataclass
class SealedArtifact:
    """The vendor crown jewel. Only `subject` and `structural_entropy_bits` are
    ever visible to the accountant; `secret_source` never crosses."""
    subject: str
    secret_source: str
    structural_entropy_bits: float


@dataclass
class Submission:
    """What the research agent tries to emit and claim, per tick."""
    claim: str
    claimed_reachable: bool
    true_reachable: bool
    repro_replays: bool
    estimate: CapacityEstimate
    estimator: EstimatorAttestation


@dataclass
class BountyLane:
    lane_id: str
    artifact: SealedArtifact
    audience: str                  # the research org accumulating knowledge (the join-key audience)
    query_family: str
    oracle: EvaluatorOracle
    schedule: PriceSchedule
    authorization: SettlementPayoutAuthorization
    ceiling_bits: float
    worker_beneficial_entity: str

    # runtime state
    ledger: List[LedgerEntry] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    account: Optional[PlainAccount] = None
    window_spent: int = 0
    _seq: int = 0
    _accountant: EgressAccountant = field(default_factory=EgressAccountant)
    _settlements: List[CreditSettlement] = field(default_factory=list)

    def _log(self, tick: int, actor: str, action: str, detail: str) -> None:
        parent = self.ledger[-1].seq if self.ledger else None
        self._seq += 1
        self.ledger.append(LedgerEntry(self._seq, tick, actor, action, detail, parent).finalize())

    def key(self) -> CompositionKey:
        return CompositionKey.of(self.artifact.subject, self.query_family, self.audience)

    def run(self, submissions: List[Submission]) -> None:
        key = self.key()
        self._accountant.register(key, self.artifact.structural_entropy_bits, self.ceiling_bits)
        self._log(0, "vendor", "grant", f"admit {self.audience} agent into sealed {self.artifact.subject} (24h grant)")

        ok, why = self.oracle.is_admissible()
        self._log(0, "vendor", "oracle_pin", f"oracle {self.oracle.oracle_id} admissible={ok} ({why})")

        for i, sub in enumerate(submissions):
            tick = i + 1
            self._process(tick, key, sub, oracle_admissible=ok)

        self._finalize_account()

    def _process(self, tick: int, key: CompositionKey, sub: Submission, oracle_admissible: bool) -> None:
        fid = f"{self.lane_id}-f{tick}"

        # 1. meter the emission BEFORE the oracle ever sees it
        allowed, st, egress_reason = self._accountant.charge(key, sub.estimate, sub.estimator, tick)
        self._log(
            tick,
            self.audience,
            "emit_metered",
            f"{sub.estimate.channel} bits={estimate_total_bits(sub.estimate):.2f} allowed={allowed} "
            f"cum={round(st.cumulative_bits,2)}/{st.ceiling_bits} class={st.leakage_class} "
            f"incident={st.incident} :: {egress_reason}",
        )
        if not allowed:
            self.findings.append(
                Finding(fid, self.artifact.subject, sub.claim, 0.0,
                        _null_verdict(sub.claim), False, egress_reason, False,
                        "not scored: emission refused by egress accountant", None, "none")
            )
            return

        # 2. oracle scores what is PROVABLE, not what is asserted
        if not oracle_admissible:
            self.findings.append(
                Finding(fid, self.artifact.subject, sub.claim, 0.0,
                        _null_verdict(sub.claim), True, egress_reason, False,
                        "oracle inadmissible (capture/role) — no zero-touch path; human fallback", None, "human_fallback")
            )
            self._log(tick, "vendor", "accept_blocked", "oracle inadmissible; escalate to human review")
            return

        score, verdict = score_against_rubric(sub.true_reachable, sub.claimed_reachable, sub.repro_replays)
        self._log(tick, self.oracle.oracle_id, "oracle_score", f"{fid} score={score:.2f} proven={list(verdict.proven)}")

        # 3. accept iff the score clears the schedule's lowest payable point
        amount = self.schedule.amount_for(score)
        if amount <= 0:
            self.findings.append(
                Finding(fid, self.artifact.subject, sub.claim, score, verdict, True, egress_reason,
                        False, "score below any payable schedule point — rejected, method never crossed", None, "none")
            )
            self._log(tick, "vendor", "reject", f"{fid} score {score:.2f} below floor; no offer, no method seen")
            return

        # 4. settle heldback, then attempt zero-touch release under the standing authorization
        held = int(round(amount * self.schedule.holdback_fraction))
        settlement = CreditSettlement(
            settlement_id=f"{fid}-settle",
            recipient=self.audience,
            amount=amount,
            heldback_amount=held,
            status="heldback",
            regression_window_ticks=self.schedule.regression_window_ticks,
            opened_tick=tick,
        )
        self._settlements.append(settlement)
        self._log(tick, "vendor", "settle_heldback", f"{fid} amount={amount} held={held} pending regression window")

        finding = Finding(fid, self.artifact.subject, sub.claim, score, verdict, True, egress_reason,
                          True, "accepted; oracle-scored; heldback pending regression window", settlement, "pending")
        self.findings.append(finding)

    def close_regression_window(self, finding_id: str, regressed: bool, tick: int) -> None:
        """Called after the regression window elapses. If the shipped fix
        regressed, the settlement is clawed back; else the held remainder is
        released — zero-touch iff the standing authorization covers it."""
        finding = next((f for f in self.findings if f.finding_id == finding_id), None)
        if finding is None or finding.settlement is None:
            return
        s = finding.settlement
        if regressed:
            s.status = "slashed"
            s.note = "shipped fix regressed inside the window — clawed back"
            finding.payout_path = "none"
            self._log(tick, "vendor", "clawback", f"{finding_id} regressed; settlement slashed")
            self._finalize_account()  # the receipt must reflect the clawback
            return

        covered, why = self.authorization.covers(
            oracle_id=self.oracle.oracle_id,
            schedule_id=self.schedule.schedule_id,
            predicate_hash=self.authorization.match_predicate_hash,
            amount=s.amount,
            window_spent=self.window_spent,
            tick=tick,
        )
        if covered:
            s.status = "released"
            s.authorization_id = self.authorization.authorization_id
            self.window_spent += s.amount
            finding.payout_path = "zero_touch"
            self._log(tick, "authorization", "release_zero_touch", f"{finding_id} released {s.amount} under standing auth")
        else:
            s.status = "released"  # released, but only via a human decision
            finding.payout_path = "human_fallback"
            self._log(tick, "vendor", "release_human_fallback", f"{finding_id} outside authorization ({why}); human released")
        # A settlement's fate changed after run(); the PlainAccount receipt is a
        # statement of final state, so it is recomputed, never left stale.
        self._finalize_account()

    def _finalize_account(self) -> None:
        paid = [
            f"{f.settlement.recipient} — {f.finding_id} ({f.payout_path}, {f.settlement.amount} credits)"
            for f in self.findings
            if f.settlement and f.settlement.status == "released"
        ]
        crossed = [f"typed VEX verdict for {f.claim}" for f in self.findings if f.accepted]
        did_not = [
            "the vendor's sealed source tree (never left the enclave)",
            "any emission that would cross the structured-bits ceiling",
        ]
        for f in self.findings:
            if not f.egress_allowed:
                did_not.append(f"refused emission: {f.claim}")
            elif not f.accepted:
                did_not.append(f"rejected finding (method never crossed): {f.claim}")
        self.account = PlainAccount(
            lane_id=self.lane_id,
            what_crossed=crossed or ["nothing crossed"],
            what_did_not_cross=did_not,
            who_was_paid=paid or ["no one yet (all heldback, clawed back, or refused)"],
            what_it_cannot_promise=[
                "results, not methods — novelty/causality/transfer are unprovable at model scale (2026)",
                "bits are an upper-bound tripwire, not a secrecy proof; staying under budget proves nothing",
                "harm is not linear in bits — a one-bit 'reachable' + tiny repro can be a live weapon (open frontier #4)",
                "trusts the TEE/hardware vendor; a vendor-key or side-channel compromise breaks the seal (#6)",
                "charge-kernel/2 accounting is integer-millibit and audit-backed; "
                "estimator bounds and key canonicalization remain trusted inputs",
                "receipts are not contracts; embargo/export/trade-secret enforcement lives in jurisdiction (#15)",
            ],
        )


def _null_verdict(claim: str):
    from .bounty import VerificationVerdict

    return VerificationVerdict("reachability", proven=(), trusted=(), unprovable=(f"unscored claim: {claim}",))
