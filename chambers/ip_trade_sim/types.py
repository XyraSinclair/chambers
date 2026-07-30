"""Frozen data model for the confidential IP-trade simulation.

Mirrors docs/primitives/iptrade.ts (and negotiation.ts,
pricing.ts) in runnable Python. Stdlib only. This file is the CONTRACT the
engine and strategies code against; keep field names stable.

Vocabulary anchor: there is no boolean `verified`. A VerificationVerdict carries
a proven / trusted / unprovable partition. A capability RESULT can be proven;
a METHOD claim (causality, novelty, transfer) lands in `unprovable`.
"""
from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


def sha(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()[:24]


# ---- what a lab holds ----

CarrierClass = str  # static_checkpoint | lora_adapter | curated_dataset | teacher_outputs | hosted_service | pure_recipe


@dataclass
class ResultClaim:
    """A verifiable RESULT: 'this asset scores >= score on benchmark'. Verifying
    it releases one symbol from the closed result-verdict codebook; the charge
    is the alphabet's derived capacity (codebook.py), not a per-claim estimate."""
    benchmark: str
    true_score: float          # ground truth (hidden from everyone but the sim)
    claimed_score: float       # what the owner asserts (may be honest or inflated)


@dataclass
class Technique:
    """One piece of tradeable IP. `secret_payload` is the crown jewel; nobody
    should reconstruct it from observation alone — the accountant enforces that."""
    id: str
    owner: str                 # Lab id
    name: str
    capability_area: str       # e.g. 'long_context', 'rl_from_ai_feedback', 'inference_efficiency'
    carrier: CarrierClass
    secret_payload: str        # the method/recipe/weights, hidden
    entropy_bits: float        # total info to fully reconstruct the secret
    claims: List[ResultClaim] = field(default_factory=list)
    # unprovable-by-construction properties (only owner knows the truth):
    true_transfers: bool = True     # does the technique transfer to another base?
    true_novel: bool = True         # is it genuinely novel vs public art?
    # per-probe leakage: bits leaked by a bounded black-box probe of n queries
    probe_leak_per_query_bits: float = 0.05
    method_reveal_fraction: float = 1.0  # fraction of entropy leaked if method is revealed

    def binding_byte_hash(self) -> str:
        return sha(self.secret_payload)

    def binding_capability_hash(self) -> str:
        # The commitment must not be grid-searchable: benchmark names are
        # public and true scores live on a small grid near the public claimed
        # score, so an unsalted hash hands every courtfile reader the exact
        # true scores by brute force. Key it on the high-entropy secret
        # payload (production: a dedicated salt revealed only to the settling
        # counterparty, who bought the reveal).
        return sha(self.secret_payload + "||" +
                   "|".join(f"{c.benchmark}:{round(c.true_score,4)}" for c in self.claims))


@dataclass
class Lab:
    id: str
    name: str
    beneficial_entity: str
    portfolio: List[Technique] = field(default_factory=list)
    credits: int = 0
    # how much this lab cares about each capability area (0..1 stake weight)
    area_stakes: Dict[str, float] = field(default_factory=dict)
    # policy knobs a human can adjust (see hooks):
    reserve_floor_credits: int = 0          # min payment to accept selling a look/technique
    max_leak_fraction_before_block: float = 0.5   # block observation past this frac of entropy
    tradeable: Dict[str, bool] = field(default_factory=dict)  # technique_id -> may we trade it at all

    def best_score(self, area: str, benchmark: str) -> float:
        best = 0.0
        for t in self.portfolio:
            if t.capability_area != area:
                continue
            for c in t.claims:
                if c.benchmark == benchmark:
                    best = max(best, c.true_score)
        return best


# ---- verification: the proven/trusted/unprovable partition ----

VerificationTrustClass = str  # trustless | threshold_ttp | single_ttp | tee_vendor_root | reputational_only


@dataclass
class ClaimResult:
    """One claim's charged codebook release, structured. Control flow and
    downstream strategies read THESE symbols; the human-facing strings in
    VerificationVerdict are rendered from them (free post-processing of an
    already-charged symbol), never parsed."""
    benchmark: str
    claimed_score: float
    symbol: str                # holds | not_met | blocked


@dataclass
class TrustRoot:
    kind: VerificationTrustClass
    feasibility: str            # practical_now | practical_small | research_horizon
    degrades_to: str            # explicit_unprovable | named_lower_trust | block
    compromise_leaks: str


@dataclass
class VerificationVerdict:
    technique_id: str
    plan: str                   # tee_replication | third_party_audit | mutual_verifier_run | none
    trust_root: TrustRoot
    claim_results: List[ClaimResult] = field(default_factory=list)
    proven: List[str] = field(default_factory=list)
    trusted: List[str] = field(default_factory=list)
    unprovable: List[str] = field(default_factory=list)
    state: str = "verified_partitioned"   # the only success state; never a bool


# ---- pricing / negotiation ----

@dataclass
class PriceDistribution:
    """A committed distribution over prices. Only the commitment crosses a
    boundary; parameters stay home. side: 'bid' (to acquire) | 'ask' (to sell)."""
    holder: str
    side: str
    lo: int
    hi: int
    commitment_hash: str = ""

    def commit(self, salt: str) -> "PriceDistribution":
        self.commitment_hash = sha(f"{self.holder}:{self.side}:{self.lo}:{self.hi}:{salt}")
        return self


@dataclass
class PriceCross:
    """Sim ground truth. Only `outcome` and `cleared_price` may be persisted
    to shared surfaces; draws and reserve are party-private inputs."""
    technique_id: str
    bid_draw: int
    ask_draw: int
    reserve: int
    outcome: str                # cleared | no_cross
    cleared_price: Optional[int] = None
    counterparty_learns: str = "outcome_and_cleared_price"


@dataclass
class Settlement:
    technique_id: str
    regime: str                 # operator_adjudicated | tee_coresident_escrow | onchain_hashlock | optimistic_with_dispute
    price: int
    verified_binding: str
    delivered_binding: Optional[str] = None
    state: str = "awaiting_verdict"   # -> priced -> delivering -> settled | disputed | aborted


# ---- ledger / receipt ----

@dataclass
class LedgerEntry:
    seq: int
    at_tick: int
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
    """The interpretability receipt: honest negative space is first-class."""
    lane_id: str
    what_crossed: List[str] = field(default_factory=list)
    what_did_not_cross: List[str] = field(default_factory=list)
    who_was_paid: List[str] = field(default_factory=list)
    what_it_cannot_promise: List[str] = field(default_factory=list)


# ---- strategy + human-handle interfaces (implemented in strategies.py / hooks) ----

@dataclass
class Appraisal:
    """One lab's private estimate of another lab's technique, formed ONLY from
    what it was allowed to observe (verdicts + metered probes)."""
    technique_id: str
    appraiser: str
    est_value_credits: int
    confidence: float
    rationale: str
    bits_spent: float           # leakage this appraisal cost


# a human handle: called at decision points; returns possibly-adjusted policy or a veto
HumanHook = Callable[[str, dict], dict]  # (decision_point, context) -> {"veto": bool, ...overrides}


def null_hook(decision_point: str, context: dict) -> dict:
    return {}
