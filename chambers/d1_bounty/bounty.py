"""Bounty, pinned oracle, standing payout authorization, and settlement.

Mirrors `primitives/market.ts` + `pricing.ts`. The recurring engine of §4 of the
build decision:

    Grant admits the agent -> agent emits a typed Annotation (metered by egress.py)
    -> a PINNED EvaluatorOracle scores it against a fixed rubric
    -> Acceptance on an owner-internal decision, guarded by a ConflictOfInterestCheck
       (oracle capture is the failure mode)
    -> CreditSettlement lands `heldback`
    -> the regression window elapses without the shipped fix regressing
    -> payout releases ZERO-TOUCH under a standing SettlementPayoutAuthorization
       (or is CLAWED BACK if the fix regresses).

Two laws made mechanical:
  - `standingAuthorizationsMovePayoutsNeverContent`: the authorization can release
    MONEY without a human, but never a content disclosure.
  - `anOracleUpgradeIsANewOracle`: the price schedule pins the rubric hash; a
    rubric change is a new oracle and a new schedule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .egress import sha


# ---- verification verdict: no boolean `verified` (iptrade.ts partition) ----


@dataclass(frozen=True)
class VerificationVerdict:
    """proven / trusted / unprovable. A RESULT (call path exists under replay)
    can be proven; a METHOD claim (novelty, transfer, 'only reachable path')
    lands in unprovable. There is deliberately no `verified: bool`."""
    subject: str
    proven: Tuple[str, ...] = ()
    trusted: Tuple[str, ...] = ()
    unprovable: Tuple[str, ...] = ()
    state: str = "verified_partitioned"


# ---- the pinned oracle and its conflict check ----


@dataclass(frozen=True)
class ConflictOfInterestCheck:
    """Oracle capture is the failure mode: the oracle's author must not benefit
    from work scored under it. Checked over BENEFICIAL ENTITIES, not ids — a
    boolean the identity model cannot back is an overclaim, so this may honestly
    return `unprovable`."""
    oracle_author_entity: str
    worker_beneficial_entity: str

    def evaluate(self) -> str:  # "disjoint" | "conflicted" | "unprovable"
        if not self.oracle_author_entity or not self.worker_beneficial_entity:
            return "unprovable"
        return "disjoint" if self.oracle_author_entity != self.worker_beneficial_entity else "conflicted"


@dataclass(frozen=True)
class EvaluatorOracle:
    """A named, pinned evaluator. 'The oracle approved it' is only a payable
    event when the oracle is a hash + a rubric + an appeal path, not a vibe."""
    oracle_id: str
    model_class_hash: str
    rubric_hash: str
    determinism: str                      # deterministic | sampled_majority | best_of_n
    role: str                             # adversarial_review | separate_models | ... (never self_interested)
    conflict_check: ConflictOfInterestCheck
    appeal_path: str = "human_steward"    # none | human_steward | second_oracle

    def is_admissible(self) -> Tuple[bool, str]:
        if self.role == "self_interested":
            return (False, "oracle role is self_interested — role separation required")
        verdict = self.conflict_check.evaluate()
        if verdict == "conflicted":
            return (False, "oracle capture: oracle author and worker share a beneficial entity")
        # 'unprovable' is allowed to proceed but is surfaced honestly downstream.
        return (True, f"conflict_check={verdict}")


# ---- price schedule: score -> credits, holdback, regression window ----


@dataclass(frozen=True)
class SchedulePoint:
    min_score: float
    amount: int          # credit micros (integer units here)


@dataclass(frozen=True)
class PriceSchedule:
    schedule_id: str
    rubric_hash: str                        # binds schedule to ONE rubric version
    points: Tuple[SchedulePoint, ...]
    holdback_fraction: float
    regression_window_ticks: int

    def amount_for(self, score: float) -> int:
        best = 0
        for p in sorted(self.points, key=lambda x: x.min_score):
            if score >= p.min_score:
                best = p.amount
        return best


# ---- standing authorization: the one human act, bound ex-ante ----


@dataclass(frozen=True)
class SettlementPayoutAuthorization:
    """Bound once by a human before work starts, to a specific oracle + schedule
    + match predicate, with per-payout and window ceilings. Lets payouts settle
    zero-touch; anything outside the predicate/ceilings falls back to a human.
    Moves MONEY, never content."""
    authorization_id: str
    authorized_by: str                      # a human principal; a system/operator may not author this
    oracle_id: str
    schedule_id: str
    match_predicate_hash: str
    per_payout_ceiling: int
    window_ceiling: int
    valid_within_ticks: Tuple[int, int]
    revoked: bool = False

    def covers(
        self, oracle_id: str, schedule_id: str, predicate_hash: str, amount: int, window_spent: int, tick: int
    ) -> Tuple[bool, str]:
        if self.revoked:
            return (False, "authorization revoked")
        lo, hi = self.valid_within_ticks
        if not (lo <= tick <= hi):
            return (False, "outside authorization time window")
        if oracle_id != self.oracle_id or schedule_id != self.schedule_id:
            return (False, "oracle/schedule mismatch — a rubric change is a new oracle")
        if predicate_hash != self.match_predicate_hash:
            return (False, "acceptance falls outside the match predicate")
        if amount > self.per_payout_ceiling:
            return (False, "exceeds per-payout ceiling")
        if window_spent + amount > self.window_ceiling:
            return (False, "exceeds window ceiling")
        return (True, "covered")


# ---- settlement lifecycle ----


@dataclass
class CreditSettlement:
    settlement_id: str
    recipient: str
    amount: int
    heldback_amount: int
    status: str                             # heldback | released | slashed | released_partial
    regression_window_ticks: int
    opened_tick: int
    authorization_id: Optional[str] = None  # set iff released zero-touch
    note: str = ""


@dataclass
class Finding:
    """One accepted (or rejected) typed emission and its downstream fate."""
    finding_id: str
    subject: str
    claim: str
    oracle_score: float
    verdict: VerificationVerdict
    egress_allowed: bool
    egress_reason: str
    accepted: bool
    accept_reason: str
    settlement: Optional[CreditSettlement] = None
    payout_path: str = "n/a"                # zero_touch | human_fallback | none


# ---- the pinned rubric scorer (deterministic stand-in for the model oracle) ----


def score_against_rubric(true_reachable: bool, claimed_reachable: bool, repro_replays: bool) -> Tuple[float, VerificationVerdict]:
    """Deterministic rubric: the oracle scores what is PROVABLE by replay, not
    what the agent asserts. A claim that fails replay scores ~0 no matter how
    confidently asserted (verification catches inflated findings without the
    method ever crossing). Method-level claims land in `unprovable`."""
    subject = "reachability"
    if not repro_replays:
        # the repro does not reproduce under the vendor's own build -> not proven
        return 0.0, VerificationVerdict(
            subject,
            proven=(),
            trusted=("static analyzer flagged a candidate path",),
            unprovable=("claim that the path is reachable",),
        )
    if claimed_reachable and true_reachable:
        return 0.92, VerificationVerdict(
            subject,
            proven=("call path exists and reproduces under tee_replication of the build",),
            trusted=("analyzer soundness for the surrounding module",),
            unprovable=("that this is the ONLY reachable path", "that the discovery technique generalizes"),
        )
    if claimed_reachable and not true_reachable:
        # confidently claimed but does not actually reproduce as reachable
        return 0.05, VerificationVerdict(
            subject,
            proven=(),
            trusted=("repro executes but does not reach the vulnerable sink",),
            unprovable=("the asserted reachability",),
        )
    # honestly reported not-present
    return 0.60, VerificationVerdict(
        subject,
        proven=("component is not present on any reachable path in this build",),
        trusted=("build graph completeness",),
        unprovable=("absence in future builds",),
    )
