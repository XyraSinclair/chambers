"""Adversarial estimator-soundness probe — the Feynman lane (ASSURANCE.md L3).

The accountant is proven to ADD correctly (L1/L2/L4). This file asks the
question no proof about the accountant can answer: are the CHARGES big enough?
The estimator makes a physical claim — "this typed channel carries at most N
bits toward reconstructing the sealed subject" — and a physical claim earns an
experiment, not an audit. So we build a real adversary: a steganographic
ENCODER that smuggles a known secret bitstring through each metered channel at
the maximum rate the channel physically permits, and a DECODER that recovers
it. Then we measure:

    achieved_bits  = the secret we could reliably push through and read back
    charged_bits   = what egress.py's estimator billed for that emission

Soundness is `achieved_bits <= charged_bits`: the meter must never undercount a
channel it models. If achieved ever exceeds charged, the estimator lied and
every ceiling above it is theater. The probe drives many random secrets across
many channel sizes and reports the worst-case ratio it could manufacture.

The experiment also draws the honest boundary in executable form: a channel the
estimator does NOT enumerate (`unmodeled_field_choice`) carries real, recoverable
bits at ZERO charge. That is not a bug in the arithmetic — it is the standing
non-claim of the whole stack (CANON open-frontier: the accountant is sound only
over the channels it enumerates; unmodeled channels are uncharged capacity)
made measurable rather than asserted. An estimate you cannot attack is not an
estimate; an estimate whose blind spots you cannot name is a lie.

Deterministic: seeded PRNG, no wall clock. Run:
    python3 -m workbench.d1_bounty.estimator_probe
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from itertools import permutations
from typing import Callable, List, Tuple

from .egress import (
    enum_value_bits,
    ordering_bits,
    repro_text_bits,
)


# ---- a deterministic bit source (no wall clock, no global random) ----


def _bitstream(seed: str, n_bits: int) -> List[int]:
    """n_bits of a deterministic, uniform-looking bitstream from a seed."""
    out: List[int] = []
    counter = 0
    while len(out) < n_bits:
        block = hashlib.sha256(f"{seed}:{counter}".encode()).digest()
        for byte in block:
            for i in range(8):
                out.append((byte >> i) & 1)
                if len(out) >= n_bits:
                    return out
        counter += 1
    return out


def _bits_to_int(bits: List[int]) -> int:
    v = 0
    for b in bits:
        v = (v << 1) | b
    return v


# ---- channel encoders/decoders: each transmits at the channel's physical max ----


@dataclass
class ChannelResult:
    channel: str
    param: int
    achieved_bits: float
    charged_bits: float
    recovered_exactly: bool

    @property
    def sound(self) -> bool:
        # achieved must not exceed charged (a hair of float slack for log2).
        return self.recovered_exactly and self.achieved_bits <= self.charged_bits + 1e-9

    @property
    def tightness(self) -> float:
        if self.charged_bits <= 0:
            return math.inf if self.achieved_bits > 0 else 1.0
        return self.achieved_bits / self.charged_bits


def probe_enum(n_legal_states: int, seed: str) -> ChannelResult:
    """The verdict enum. A malicious agent selects one of n legal values to
    encode secret bits. Physical max = floor(log2(n)) reliably-decodable bits;
    the estimator charges log2(n). Encode -> pick value index; decode -> read
    the index back."""
    usable = max(0, (n_legal_states).bit_length() - 1)  # floor(log2(n))
    secret = _bits_to_int(_bitstream(seed, usable)) if usable else 0
    emitted_value_index = secret  # in [0, 2^usable) ⊆ [0, n)
    recovered = emitted_value_index
    return ChannelResult(
        channel="enum_value",
        param=n_legal_states,
        achieved_bits=float(usable),
        charged_bits=enum_value_bits(n_legal_states),
        recovered_exactly=(recovered == secret),
    )


def probe_ordering(k_paths: int, seed: str) -> ChannelResult:
    """Ordering of k otherwise-innocuous call paths. Physical max =
    floor(log2(k!)) reliably-decodable bits via a permutation index (Lehmer
    code); the estimator charges log2(k!). Encode -> permutation; decode ->
    permutation rank."""
    fact = math.factorial(k_paths)
    usable = max(0, fact.bit_length() - 1)  # floor(log2(k!))
    secret = _bits_to_int(_bitstream(seed, usable)) if usable else 0
    perm_index = secret  # in [0, 2^usable) ⊆ [0, k!)
    # Encode: the perm_index-th permutation of range(k); decode: its rank.
    items = list(range(k_paths))
    perm = _nth_permutation(items, perm_index)
    recovered = _permutation_rank(perm)
    return ChannelResult(
        channel="ordering",
        param=k_paths,
        achieved_bits=float(usable),
        charged_bits=ordering_bits(k_paths),
        recovered_exactly=(recovered == perm_index),
    )


def probe_text(max_bytes: int, seed: str) -> ChannelResult:
    """The 'minimal repro'. Raw bytes are the channel; physical max = 8*bytes.
    The estimator charges exactly 8*bytes. Encode -> the byte payload; decode
    -> read the bytes back."""
    usable = 8 * max_bytes
    secret_bits = _bitstream(seed, usable)
    payload = bytes(
        _bits_to_int(secret_bits[i : i + 8]) for i in range(0, usable, 8)
    )
    recovered_bits: List[int] = []
    for byte in payload:
        for i in range(7, -1, -1):
            recovered_bits.append((byte >> i) & 1)
    return ChannelResult(
        channel="repro_text",
        param=max_bytes,
        achieved_bits=float(usable),
        charged_bits=repro_text_bits(max_bytes),
        recovered_exactly=(recovered_bits == secret_bits),
    )


def probe_enum_amortized(n_legal_states: int, symbols: int, seed: str) -> ChannelResult:
    """The stronger adversary. Per-emission the enum yields floor(log2(n)) bits,
    but across a RUN of `symbols` emissions an arithmetic coder reaches the full
    log2(n) bits/symbol — the estimator's per-emission charge is exactly this
    amortized capacity. Encode a secret integer as base-n digits; recover it;
    achieved = log2(n)*symbols, charged = same. This is where achieved -> charged
    from below and the bound is shown TIGHT, not merely safe."""
    # A secret uniform over n**symbols carries exactly symbols*log2(n) bits.
    space = n_legal_states ** symbols
    usable_bits = max(0, space.bit_length() - 1)
    secret = _bits_to_int(_bitstream(seed, usable_bits)) if usable_bits else 0
    # Encode: base-n digit expansion (the sequence of emitted enum values).
    digits: List[int] = []
    v = secret
    for _ in range(symbols):
        v, d = divmod(v, n_legal_states)
        digits.append(d)
    # Decode: recompose from the emitted digit sequence.
    recovered = 0
    for d in reversed(digits):
        recovered = recovered * n_legal_states + d
    return ChannelResult(
        channel="enum_amortized",
        param=n_legal_states,
        achieved_bits=usable_bits,           # what the run actually carried
        charged_bits=symbols * enum_value_bits(n_legal_states),  # per-emission charge summed
        recovered_exactly=(recovered == secret),
    )


def probe_unmodeled(n_synonyms: int, seed: str) -> ChannelResult:
    """THE HONEST LIMIT, executable. Suppose the emission schema lets the agent
    pick among `n_synonyms` semantically-equivalent field names (or whitespace
    stylings, or key orderings) that the estimator does NOT enumerate. Real
    bits flow and are recoverable; the estimator charges ZERO. This is not an
    arithmetic error — it is uncharged capacity, and the probe exists to keep
    us from ever calling the accountant 'complete'."""
    usable = max(0, (n_synonyms).bit_length() - 1)
    secret = _bits_to_int(_bitstream(seed, usable)) if usable else 0
    recovered = secret
    return ChannelResult(
        channel="unmodeled_field_choice",
        param=n_synonyms,
        achieved_bits=float(usable),
        charged_bits=0.0,  # the estimator has no term for this channel
        recovered_exactly=(recovered == secret),
    )


# ---- Lehmer code: permutation <-> rank, exact and integer-only ----


def _nth_permutation(items: List[int], index: int) -> List[int]:
    items = list(items)
    perm: List[int] = []
    n = len(items)
    for i in range(n, 0, -1):
        f = math.factorial(i - 1)
        pos, index = divmod(index, f)
        perm.append(items.pop(pos))
    return perm


def _permutation_rank(perm: List[int]) -> int:
    perm = list(perm)
    n = len(perm)
    rank = 0
    available = sorted(perm)
    for i in range(n):
        pos = available.index(perm[i])
        rank += pos * math.factorial(n - 1 - i)
        available.pop(pos)
    return rank


# ---- the experiment ----


@dataclass
class ProbeReport:
    modeled: List[ChannelResult]
    unmodeled: List[ChannelResult]

    @property
    def all_modeled_sound(self) -> bool:
        return all(r.sound for r in self.modeled)

    @property
    def worst_modeled_tightness(self) -> float:
        return max((r.tightness for r in self.modeled), default=0.0)

    @property
    def uncharged_bits_demonstrated(self) -> float:
        return max(
            (r.achieved_bits for r in self.unmodeled if r.recovered_exactly),
            default=0.0,
        )


def run_probe(seeds: int = 64) -> ProbeReport:
    """Drive every modeled channel across a range of sizes and many random
    secrets; separately demonstrate the unmodeled channel's uncharged capacity."""
    modeled: List[ChannelResult] = []
    unmodeled: List[ChannelResult] = []
    for s in range(seeds):
        seed = f"probe/{s}"
        for n in (2, 3, 5, 8, 13, 64, 257):
            modeled.append(probe_enum(n, seed + f"/enum/{n}"))
        for k in (2, 3, 4, 5, 6, 8):
            modeled.append(probe_ordering(k, seed + f"/ord/{k}"))
        for b in (1, 2, 4, 16, 64):
            modeled.append(probe_text(b, seed + f"/txt/{b}"))
        # the amortized adversary: non-power-of-2 enums over a long run, where
        # per-emission floor understates and the true rate approaches log2(n).
        for n in (3, 5, 6, 7, 10):
            modeled.append(probe_enum_amortized(n, 40, seed + f"/amort/{n}"))
        for m in (2, 4, 16):
            unmodeled.append(probe_unmodeled(m, seed + f"/unm/{m}"))
    return ProbeReport(modeled=modeled, unmodeled=unmodeled)


def main() -> None:
    report = run_probe()
    n = len(report.modeled)
    unsound = [r for r in report.modeled if not r.sound]
    print(f"estimator-soundness probe: {n} modeled-channel emissions across "
          f"enum/ordering/repro_text")
    print(f"  all recovered exactly and achieved <= charged: "
          f"{report.all_modeled_sound}  ({len(unsound)} violations)")
    print(f"  worst-case tightness achieved/charged: "
          f"{report.worst_modeled_tightness:.4f} (<=1.0 == sound; ~1.0 == tight)")
    if unsound:
        for r in unsound[:5]:
            print(f"  VIOLATION {r.channel}({r.param}): "
                  f"achieved={r.achieved_bits} > charged={r.charged_bits:.4f}")
    demo = report.uncharged_bits_demonstrated
    print(f"  honest limit: an UNMODELED channel carried up to {demo:.0f} "
          f"recoverable bits at ZERO charge — uncharged capacity, named not fixed")


if __name__ == "__main__":
    main()
