"""Codebooks: finite verdict alphabets whose capacity is DERIVED, never declared.

This is the calculus (primitives/CALCULUS.md §2) touching running code. A
codebook closes the observable alphabet of one release channel: every symbol a
counterparty can ever see — verdicts, rejections, errors — is enumerated, and
the charge is log2 of the alphabet size. The charge needs no analysis of the
worker, the question, or the corpus: an observer who sees one of |symbols|
outcomes learns at most log2 |symbols| bits about ANYTHING, malicious judge
included. (Min-capacity: this ceiling bounds multiplicative g-leakage for
every gain function g.)

Contrast with the declared channels in leakage.py (black-box probes, method
reveals, prior-art localization): those estimate what an interaction reveals
and are honest tripwires, not theorems. A codebook charge is exact by
construction; that difference is surfaced in the cut-bound report.

The `blocked` symbol is special: the accountant refuses the charge when the
budget is exhausted, yet the observer still sees that blockage happened. This
is sound to leave uncharged ONLY because blockage is a function of the public
charge ledger alone (simulatable from public data — CALCULUS.md L5); the
canary test asserts exactly that.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Codebook:
    """A closed release alphabet. capacity is a property, not a field: it can
    never drift from the symbol list."""

    name: str
    symbols: Tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.symbols) < 2:
            raise ValueError(f"codebook {self.name!r} needs >= 2 symbols to carry a verdict")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError(f"codebook {self.name!r} has duplicate symbols")

    @property
    def capacity_bits(self) -> float:
        return math.log2(len(self.symbols))

    def require(self, symbol: str) -> str:
        """Closed-alphabet enforcement (CALCULUS.md L6): a symbol outside the
        codebook is a side channel, and it is a bug, not a policy question."""
        if symbol not in self.symbols:
            raise ValueError(
                f"symbol {symbol!r} is not in codebook {self.name!r} {self.symbols}; "
                "an un-enumerated outcome is an unmetered side channel"
            )
        return symbol


# One claim's attested result verification, as the buyer observes it.
# `blocked` is in the alphabet because the buyer can see that verification
# stopped; it is charged 0 (see module docstring and the canary test).
RESULT_VERDICT = Codebook("result_verdict", ("holds", "not_met", "blocked"))
