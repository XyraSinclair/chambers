"""The negotiation lane state machine.

Flow per candidate technique the buyer might want from the seller:
  register leakage budget  ->  verify RESULT (attested, partitioned verdict)
  ->  buyer appraises under metered observation  ->  seller asks / buyer bids
  ->  jointly-seeded sampled price cross  ->  settle if cleared+tradeable+reserve
  ->  paid method reveal (the only legitimate full-knowledge crossing).

Every step debits the leakage accountant and appends to the ledger. Human hooks
fire at policy points (reserve, reveal approval, trade veto). The verdict never
carries a boolean 'verified' — only proven/trusted/unprovable.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from . import courtfile, economics, price_debate
from .codebook import RESULT_VERDICT
from .leakage import LeakageAccountant, method_reveal_bits
from .types import (Appraisal, ClaimResult, Lab, LedgerEntry, PlainAccount,
                    PriceCross, Settlement, Technique, TrustRoot,
                    VerificationVerdict, HumanHook, null_hook, sha)


TEE_ROOT = TrustRoot(
    kind="tee_vendor_root", feasibility="practical_now",
    degrades_to="explicit_unprovable",
    compromise_leaks="a leaked NVIDIA/CPU-vendor attestation key or a new microarchitectural side channel exposes the in-enclave eval",
)


@dataclass
class TradeOutcome:
    technique_id: str
    area: str
    verdict: VerificationVerdict
    appraisal: Optional[Appraisal]
    negotiation: Optional[price_debate.NegotiationTranscript]
    cross: Optional[PriceCross]
    settlement: Optional[Settlement]
    realized_value_credits: Optional[int] = None
    buyer_regret_credits: Optional[int] = None
    blocked_reason: Optional[str] = None


@dataclass
class LaneResult:
    lane_id: str
    buyer: str
    seller: str
    outcomes: List[TradeOutcome] = field(default_factory=list)
    ledger: List[LedgerEntry] = field(default_factory=list)
    account: PlainAccount = None  # type: ignore
    courtfile_dir: Optional[str] = None
    courtfile_validation: Optional[str] = None


class Ledger:
    def __init__(self) -> None:
        self.entries: List[LedgerEntry] = []
        self._seq = 0

    def add(self, tick: int, actor: str, action: str, detail: str) -> LedgerEntry:
        parent = self.entries[-1].seq if self.entries else None
        e = LedgerEntry(self._seq, tick, actor, action, detail, parent).finalize()
        self.entries.append(e)
        self._seq += 1
        return e


def verify_result(technique: Technique, buyer: Lab, accountant: LeakageAccountant,
                  tick: int, ledger: Ledger) -> VerificationVerdict:
    """Attested RESULT verification inside a (simulated) confidential enclave.
    Proves score claims (cheap leakage, debited); method properties are unprovable."""
    claim_results, proven, trusted, unprovable = [], [], [], []
    trusted.append(f"eval ran under {TEE_ROOT.kind} attestation ({TEE_ROOT.feasibility}); trusts hardware vendor")
    for i, claim in enumerate(technique.claims):
        # the enclave checks the claimed score against the true score; the buyer
        # observes ONLY a codebook symbol. The charge is the alphabet's derived
        # capacity, and the NOT-met arm names no numbers: the claimed score is
        # already the seller's public assertion, but the true score is silo
        # content and printing it would be an unmetered side channel.
        holds = claim.true_score + 1e-9 >= claim.claimed_score
        symbol, st = accountant.release(
            technique.id, buyer.id, RESULT_VERDICT,
            "holds" if holds else "not_met",
            tick, note=f"verdict on {claim.benchmark}",
        )
        claim_results.append(ClaimResult(claim.benchmark, claim.claimed_score, symbol))
        if symbol == "blocked":
            unprovable.append(f"{claim.benchmark}: not evaluated — leakage budget blocked further observation")
            ledger.add(tick, buyer.id, "verify_blocked", f"{technique.id} {claim.benchmark}")
            continue
        # human-facing strings are RENDERED from the charged symbol; nothing
        # downstream may parse them back (control flow reads claim_results)
        if symbol == "holds":
            proven.append(f"{claim.benchmark} >= {claim.claimed_score:.3f} (attested)")
        else:
            proven.append(f"{claim.benchmark} claim NOT met (attested against claimed {claim.claimed_score:.3f})")
        ledger.add(tick, buyer.id, "verify_result",
                   f"{technique.id} {claim.benchmark} symbol={symbol} charged_bits={RESULT_VERDICT.capacity_bits:.3f}")
    # method-level properties are never provable at model scale in 2026
    unprovable.append("technique novelty vs public art: unprovable")
    unprovable.append("causal attribution of the lift (vs more compute/data): unprovable")
    unprovable.append("transfer to a different base model: unprovable without a full re-run")
    return VerificationVerdict(technique_id=technique.id, plan="tee_replication",
                               trust_root=TEE_ROOT, claim_results=claim_results,
                               proven=proven, trusted=trusted, unprovable=unprovable)


def sampled_cross(bid_lo: int, bid_hi: int, ask_lo: int, ask_hi: int, reserve: int,
                  technique_id: str, seed_material: str) -> PriceCross:
    """Seeded midpoint draw. Clears iff bid_draw >= ask_draw >= reserve.
    Honesty note (adversarial review): this is NOT grind-proof — the salts are
    deterministic public strings, there is no commit-reveal ordering, and the
    commitments are never verified against openings, so a party choosing its
    band can grind the draw. Fine for a deterministic sim; a real deployment
    needs commit-then-reveal with verified openings."""
    rnd = random.Random(int(sha(seed_material)[7:19], 16))
    bid_draw = rnd.randint(min(bid_lo, bid_hi), max(bid_lo, bid_hi))
    ask_draw = rnd.randint(min(ask_lo, ask_hi), max(ask_lo, ask_hi))
    if bid_draw >= ask_draw and ask_draw >= reserve:
        price = (bid_draw + ask_draw) // 2  # midpoint clearing
        return PriceCross(technique_id, bid_draw, ask_draw, reserve, "cleared", price)
    return PriceCross(technique_id, bid_draw, ask_draw, reserve, "no_cross", None)


def run_lane(buyer: Lab, seller: Lab, accountant: LeakageAccountant, strategies,
             hook: HumanHook = null_hook, seed: str = "lane") -> LaneResult:
    lane_id = f"lane:{buyer.id}->{seller.id}"
    ledger = Ledger()
    ledger.add(0, "system", "lane_open", lane_id)
    res = LaneResult(lane_id=lane_id, buyer=buyer.id, seller=seller.id)
    crossed: List[str] = []
    not_crossed: List[str] = []
    paid: List[str] = []
    tick = 1

    for technique in seller.portfolio:
        area = technique.capability_area
        # buyer only pursues areas it has stake in
        if buyer.area_stakes.get(area, 0.0) <= 0.0:
            # the REASON (buyer's stake support set) is buyer-private; the
            # shared receipt states only the uncharged fact "never observed"
            not_crossed.append(f"{technique.name}: not pursued by buyer (private policy); never observed")
            continue

        # seller policy: is this technique tradeable at all? human hook can veto/adjust.
        h = hook("consider_reveal", {"lane": lane_id, "seller": seller.id, "technique": technique.name,
                                     "area": area, "carrier": technique.carrier})
        tradeable = seller.tradeable.get(technique.id, True) and not h.get("veto", False)
        if not tradeable:
            not_crossed.append(f"{technique.name}: seller withheld from trade (policy/veto)")
            ledger.add(tick, seller.id, "withhold", technique.id)
            continue

        accountant.register(technique, buyer.id, buyer.max_leak_fraction_before_block)
        ledger.add(tick, "system", "verify_open", technique.id)
        verdict = verify_result(technique, buyer, accountant, tick, ledger)
        tick += 1

        appraisal = strategies.appraise(buyer, seller, technique, verdict, accountant, tick, hook, ledger)
        res_outcome = TradeOutcome(technique.id, area, verdict, appraisal, None, None, None)
        tick += 1

        if appraisal is None or appraisal.est_value_credits <= 0:
            # Three different facts, three different labels — the receipt must
            # not conflate them, and it reads charged SYMBOLS, never strings:
            #   fraud (a claim's paid verdict was not_met),
            #   budget-block (no claim got a verdict at all),
            #   honest no-fit (verified; buyer's private valuation declined).
            claim_failed = any(cr.symbol == "not_met" for cr in verdict.claim_results)
            all_blocked = bool(verdict.claim_results) and all(
                cr.symbol == "blocked" for cr in verdict.claim_results)
            if claim_failed:
                not_crossed.append(f"{technique.name}: FAILED verification (claimed > true); no offer")
                res_outcome.blocked_reason = "failed_verification"
            elif all_blocked:
                not_crossed.append(f"{technique.name}: verification stopped by leakage budget; no offer")
                res_outcome.blocked_reason = "verification_budget_blocked"
            else:
                # the buyer's frontier position is buyer-private; say only
                # that the buyer declined
                not_crossed.append(f"{technique.name}: verified; buyer declined to bid (private valuation)")
                res_outcome.blocked_reason = "no_marginal_value"
            res.outcomes.append(res_outcome)
            continue

        # reserve: seller floor (human-adjustable)
        rh = hook("set_reserve", {"lane": lane_id, "seller": seller.id, "technique": technique.name,
                                  "default_reserve": seller.reserve_floor_credits})
        reserve = int(rh.get("reserve", seller.reserve_floor_credits))

        ask = strategies.seller_ask(seller, technique, reserve, hook)
        bid = strategies.buyer_bid(buyer, seller, technique, appraisal, hook)
        transcript, tick = price_debate.negotiate_price(
            lane_id=lane_id,
            technique=technique,
            buyer=buyer,
            seller=seller,
            bid=bid,
            ask=ask,
            reserve=reserve,
            accountant=accountant,
            tick=tick,
            ledger=ledger,
            cross_fn=sampled_cross,
            seed=seed,
        )
        res_outcome.negotiation = transcript
        res_outcome.cross = transcript.final_cross
        cross = transcript.final_cross

        if transcript.walked_away or cross is None:
            not_crossed.append(f"{technique.name}: negotiation walked away before a clearing cross")
            res_outcome.blocked_reason = "negotiation_walkaway"
            res.outcomes.append(res_outcome)
            continue

        if cross.outcome != "cleared":
            not_crossed.append(
                f"{technique.name}: price did not cross (bid {cross.bid_draw} vs ask {cross.ask_draw}, reserve {reserve})"
            )
            res_outcome.blocked_reason = "no_price_cross"
            res.outcomes.append(res_outcome)
            continue

        # final human gate before a real content reveal
        gh = hook("approve_settlement", {"lane": lane_id, "technique": technique.name,
                                         "price": cross.cleared_price, "buyer": buyer.id})
        if gh.get("veto", False):
            not_crossed.append(f"{technique.name}: settlement vetoed by human at price {cross.cleared_price}")
            res_outcome.blocked_reason = "human_veto"
            res.outcomes.append(res_outcome)
            continue

        # settle: atomic swap, then the paid method reveal (the legitimate full crossing)
        price = int(cross.cleared_price)
        settlement = Settlement(technique.id, regime="tee_coresident_escrow", price=price,
                                verified_binding=technique.binding_capability_hash())
        # paid reveal debits the accountant but is legitimate (past the ceiling, by payment)
        accountant.observe(technique.id, buyer.id, "method_reveal_paid",
                           method_reveal_bits(technique), tick, note=f"paid reveal @ {price}")
        settlement.delivered_binding = technique.binding_capability_hash()
        settlement.state = "settled" if settlement.delivered_binding == settlement.verified_binding else "disputed"
        buyer.credits -= price
        seller.credits += price
        realized_scores = {claim.benchmark: claim.true_score for claim in technique.claims}
        realized_value = economics.realized_value(buyer, technique, realized_scores)
        regret = max(0, appraisal.est_value_credits - realized_value)
        res_outcome.settlement = settlement
        res_outcome.realized_value_credits = realized_value
        res_outcome.buyer_regret_credits = regret
        # realized_value and regret are functions of the buyer's PRIVATE
        # valuation: they stay on the in-memory outcome (sim ground truth,
        # buyer-side reporting) and never enter the shared receipt or ledger.
        crossed.append(
            f"{technique.name}: SETTLED @ {price} credits "
            f"(delivered==verified: {settlement.state=='settled'})"
        )
        paid.append(f"{seller.name} +{price} for {technique.name}")
        ledger.add(tick, "consortium", "settle", f"{technique.id} price={price} state={settlement.state}")
        tick += 1
        res.outcomes.append(res_outcome)

    res.ledger = ledger.entries
    res.account = PlainAccount(
        lane_id=lane_id,
        what_crossed=crossed,
        what_did_not_cross=not_crossed,
        who_was_paid=paid,
        what_it_cannot_promise=[
            "verified results, not methods — novelty/causality/transfer are unprovable",
            "trusts the TEE hardware vendor; a vendor-key or side-channel compromise breaks the eval seal",
            "the enclave that ran the eval is a doubly-sealed verifier that saw both sides' inputs",
            "cryptographic receipts are not self-enforcing contracts across jurisdictions",
        ],
    )
    court_dir = courtfile.persist_ip_courtfile(res, accountant)
    ok, message = courtfile.validate_ip_courtfile(court_dir)
    res.courtfile_dir = str(court_dir)
    res.courtfile_validation = message
    if not ok:
        ledger.add(tick, "system", "courtfile_invalid", message)
        res.ledger = ledger.entries
    return res
