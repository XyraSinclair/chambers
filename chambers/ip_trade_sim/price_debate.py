from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Protocol, Tuple

from .leakage import LeakageAccountant
from .types import Lab, PriceCross, PriceDistribution, Technique


# Per-round declared charge, per side (adversarial-review fix: the old 0.18
# was a fig leaf while raw bands crossed in plaintext). What actually crosses
# per round now: the shared overlap bit (1.0) plus the mediator's band-step
# guidance, which is a coarse function of the counterparty's band center
# (declared upper bound 2.0). Raw bands never leave the silo; only
# commitments are persisted.
PRICE_ROUND_BITS = 3.0
# A cleared price is a genuine paid crossing: a function of both parties'
# draws, revealed to both. Declared upper bound on what it says about the
# counterparty's valuation position.
CLEARED_PRICE_BITS = 6.0
# The valuation shadow's declared entropy: sized so a full 4-round debate
# plus a cleared cross (4*3 + 6 = 18) fits, and a pathological re-run trips
# the ceiling. A modeling knob, declared-public at registration.
VALUATION_ENTROPY_BITS = 24.0
MIN_BAND_WIDTH = 60
MAX_NEGOTIATION_ROUNDS = 4


class LedgerLike(Protocol):
    def add(self, tick: int, actor: str, action: str, detail: str) -> object:
        ...


CrossFn = Callable[[int, int, int, int, int, str, str], PriceCross]


@dataclass
class NegotiationRound:
    """The PERSISTED round record (types.py contract: 'only the commitment
    crosses a boundary; parameters stay home'). Raw bands and the numeric gap
    are party-private inputs and deliberately absent — a courtfile reader
    sees commitments, the overlap bit, and the charges."""
    round_index: int
    seller_commitment_hash: str
    buyer_commitment_hash: str
    overlap: bool
    seller_bits: float
    buyer_bits: float


@dataclass
class NegotiationTranscript:
    technique_id: str
    rounds: List[NegotiationRound] = field(default_factory=list)
    final_cross: Optional[PriceCross] = None
    walked_away: bool = False
    bits_leaked_by_negotiation: float = 0.0


def _band_center(lo: int, hi: int) -> float:
    return (lo + hi) / 2.0


def _band_width(lo: int, hi: int) -> int:
    return max(0, hi - lo)


def _bands_overlap(ask_lo: int, ask_hi: int, bid_lo: int, bid_hi: int) -> bool:
    return ask_lo <= bid_hi


def _valuation_shadow(holder: Lab, lane_id: str, technique: Technique) -> Technique:
    return Technique(
        id=f"valuation:{lane_id}:{holder.id}:{technique.id}",
        owner=holder.id,
        name=f"{holder.id} valuation for {technique.id}",
        capability_area=f"valuation:{technique.capability_area}",
        carrier="pure_recipe",
        secret_payload=f"{holder.id}:{lane_id}:{technique.id}:valuation",
        entropy_bits=VALUATION_ENTROPY_BITS,
        claims=[],
        true_transfers=True,
        true_novel=True,
        probe_leak_per_query_bits=0.0,
        method_reveal_fraction=0.0,
    )


def _step_seller_band(lo: int, hi: int, target_center: float, reserve: int) -> Tuple[int, int]:
    center = _band_center(lo, hi)
    width = max(MIN_BAND_WIDTH, _band_width(lo, hi))
    half_width = max(MIN_BAND_WIDTH / 2.0, width * 0.36)
    new_center = center + (target_center - center) * 0.45
    if new_center > center:
        new_center = center
    new_lo = max(reserve, int(round(new_center - half_width)))
    new_hi = max(new_lo, int(round(new_center + half_width)))
    return new_lo, new_hi


def _step_buyer_band(lo: int, hi: int, target_center: float) -> Tuple[int, int]:
    center = _band_center(lo, hi)
    width = max(MIN_BAND_WIDTH, _band_width(lo, hi))
    half_width = max(MIN_BAND_WIDTH / 2.0, width * 0.36)
    new_center = center + (target_center - center) * 0.45
    if new_center < center:
        new_center = center
    new_lo = max(0, int(round(new_center - half_width)))
    new_hi = max(new_lo, int(round(new_center + half_width)))
    return new_lo, new_hi


def negotiate_price(
    lane_id: str,
    technique: Technique,
    buyer: Lab,
    seller: Lab,
    bid: PriceDistribution,
    ask: PriceDistribution,
    reserve: int,
    accountant: LeakageAccountant,
    tick: int,
    ledger: LedgerLike,
    cross_fn: CrossFn,
    seed: str,
    max_rounds: int = MAX_NEGOTIATION_ROUNDS,
) -> Tuple[NegotiationTranscript, int]:
    transcript = NegotiationTranscript(technique_id=technique.id)
    buyer_shadow = _valuation_shadow(buyer, lane_id, technique)
    seller_shadow = _valuation_shadow(seller, lane_id, technique)
    accountant.register(buyer_shadow, seller.id, 1.0)
    accountant.register(seller_shadow, buyer.id, 1.0)

    ask_lo, ask_hi = ask.lo, ask.hi
    bid_lo, bid_hi = bid.lo, bid.hi

    for round_index in range(1, max_rounds + 1):
        ask_round = PriceDistribution(seller.id, "ask", ask_lo, ask_hi).commit(
            salt=f"{lane_id}:{technique.id}:ask:r{round_index}"
        )
        bid_round = PriceDistribution(buyer.id, "bid", bid_lo, bid_hi).commit(
            salt=f"{lane_id}:{technique.id}:bid:r{round_index}"
        )

        # CHARGE BEFORE PUBLISH (adversarial-review fix: the old order
        # appended round content to the transcript and ledger before the
        # walkaway check, so refused charges still crossed). A refused charge
        # publishes nothing content-bearing.
        seller_ok, _ = accountant.observe(
            seller_shadow.id,
            buyer.id,
            "price_round",
            PRICE_ROUND_BITS,
            tick,
            note=f"round {round_index} overlap bit + band-step guidance",
        )
        buyer_ok, _ = accountant.observe(
            buyer_shadow.id,
            seller.id,
            "price_round",
            PRICE_ROUND_BITS,
            tick,
            note=f"round {round_index} overlap bit + band-step guidance",
        )
        if not seller_ok or not buyer_ok:
            transcript.walked_away = True
            ledger.add(
                tick,
                "consortium",
                "price_walkaway",
                f"{technique.id} valuation leakage budget exhausted during negotiation",
            )
            tick += 1
            return transcript, tick

        seller_bits = PRICE_ROUND_BITS
        buyer_bits = PRICE_ROUND_BITS
        transcript.bits_leaked_by_negotiation += seller_bits + buyer_bits
        overlap = _bands_overlap(ask_lo, ask_hi, bid_lo, bid_hi)
        transcript.rounds.append(
            NegotiationRound(
                round_index=round_index,
                seller_commitment_hash=ask_round.commitment_hash,
                buyer_commitment_hash=bid_round.commitment_hash,
                overlap=overlap,
                seller_bits=seller_bits,
                buyer_bits=buyer_bits,
            )
        )
        # raw bands and gap stay in-silo; the shared ledger carries the
        # charged overlap bit and the commitments only
        ledger.add(
            tick,
            "consortium",
            "price_round",
            (
                f"{technique.id} r={round_index} overlap={overlap} "
                f"ask_commit={ask_round.commitment_hash} bid_commit={bid_round.commitment_hash} "
                f"bits={seller_bits + buyer_bits:.2f}"
            ),
        )
        tick += 1

        if overlap:
            # a cleared price is a real crossing for BOTH sides — charge it
            # before the cross is computed or published
            cross_seller_ok, _ = accountant.observe(
                seller_shadow.id, buyer.id, "cleared_price", CLEARED_PRICE_BITS,
                tick, note="clearing price reveal",
            )
            cross_buyer_ok, _ = accountant.observe(
                buyer_shadow.id, seller.id, "cleared_price", CLEARED_PRICE_BITS,
                tick, note="clearing price reveal",
            )
            if not cross_seller_ok or not cross_buyer_ok:
                transcript.walked_away = True
                ledger.add(
                    tick,
                    "consortium",
                    "price_walkaway",
                    f"{technique.id} valuation leakage budget refused the clearing-price reveal",
                )
                tick += 1
                return transcript, tick
            transcript.bits_leaked_by_negotiation += 2 * CLEARED_PRICE_BITS
            seed_material = (
                f"{seed}:{technique.id}:r{round_index}:"
                f"{ask_round.commitment_hash}:{bid_round.commitment_hash}"
            )
            cross = cross_fn(bid_lo, bid_hi, ask_lo, ask_hi, reserve, technique.id, seed_material)
            transcript.final_cross = cross
            # draws and reserve are party-private inputs; only the outcome
            # and the cleared price may be published
            ledger.add(
                tick,
                "consortium",
                "price_cross",
                f"{technique.id} {cross.outcome}"
                + (f" price={cross.cleared_price}" if cross.cleared_price is not None else ""),
            )
            tick += 1
            return transcript, tick

        if round_index == max_rounds:
            break

        target_center = (_band_center(ask_lo, ask_hi) + _band_center(bid_lo, bid_hi)) / 2.0
        ask_lo, ask_hi = _step_seller_band(ask_lo, ask_hi, target_center, reserve)
        bid_lo, bid_hi = _step_buyer_band(bid_lo, bid_hi, target_center)

    transcript.walked_away = True
    ledger.add(
        tick,
        "consortium",
        "price_walkaway",
        f"{technique.id} no overlap after {max_rounds} rounds",
    )
    tick += 1
    return transcript, tick
