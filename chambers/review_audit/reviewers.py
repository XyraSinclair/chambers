"""The scripted reviewers — the instrument's self-validation cast
(PROBE-SPEC §5). Each pathology is the oracle except for exactly ONE
behavioral deviation, so a conviction attributes to the code naming it.
These are not caricatures for show: each is a failure mode observed in
real LLM judges (cardinal-harness `tests/judge_bench.rs` precedent).

Reviewers answer the LITERAL question asked ("YES"/"NO"/"ABSTAIN" to
admit-this? / refuse-this?); the harness maps answers to semantic
verdicts. Stateful reviewers (drifter) carry their own counters — the
harness feeds probes in battery order and passes only (probe_id,
rendered), never position metadata.
"""
from __future__ import annotations

import hashlib
from typing import Optional


def _answer(verdict: Optional[str], rendered: dict) -> str:
    """Answer the asked question from a semantic verdict."""
    if verdict is None or verdict == "ABSTAIN":
        return "ABSTAIN"
    if rendered["question"] == "admit":
        return "YES" if verdict == "ADMIT" else "NO"
    return "YES" if verdict == "REFUSE" else "NO"


def _oracle_verdict(rendered: dict) -> str:
    merits = [e["merit"] for e in rendered["evidence"]]
    if any(m is None for m in merits):
        return "ABSTAIN"
    return "ADMIT" if sum(merits) > rendered["threshold"] else "REFUSE"


def oracle():
    """Reads the semantic fields only; invariant under everything."""
    def review(probe_id: str, rendered: dict) -> str:
        return _answer(_oracle_verdict(rendered), rendered)
    return review


def position_biased():
    """Extrapolates the whole tuple from its FIRST item — the primacy
    judge. Honest whenever the head happens to be representative."""
    def review(probe_id: str, rendered: dict) -> str:
        head = rendered["evidence"][0]["merit"]
        if head is None:
            return _answer("ABSTAIN", rendered)
        n = len(rendered["evidence"])
        v = "ADMIT" if head * n > rendered["threshold"] else "REFUSE"
        return _answer(v, rendered)
    return review


def wording_keyed():
    """Keys on the surface phrasing: the re-worded rendering of the same
    semantics gets the opposite verdict. (Abstentions stay abstentions —
    it is sway, not fabrication.)"""
    def review(probe_id: str, rendered: dict) -> str:
        v = _oracle_verdict(rendered)
        if v != "ABSTAIN" and rendered["objective"].startswith("Judge"):
            v = "REFUSE" if v == "ADMIT" else "ADMIT"
        return _answer(v, rendered)
    return review


def sycophant():
    """Echoes the requester's framed desire whenever a frame is present;
    honest when nobody is watching."""
    def review(probe_id: str, rendered: dict) -> str:
        if rendered["frame_direction"]:
            return _answer(rendered["frame_direction"], rendered)
        return _answer(_oracle_verdict(rendered), rendered)
    return review


def contrarian():
    """Flips AWAY from the requester's framed desire whenever a frame is
    present — the anti-sycophant. Exactly as frame-incoherent as the
    sycophant, in the mirrored direction; before R8 existed this reviewer
    audited CLEAN (fable review finding, 2026-07-06), which is why the
    cast now includes it: one scripted pathology per signed direction."""
    def review(probe_id: str, rendered: dict) -> str:
        if rendered["frame_direction"]:
            flipped = ("REFUSE" if rendered["frame_direction"] == "ADMIT"
                       else "ADMIT")
            return _answer(flipped, rendered)
        return _answer(_oracle_verdict(rendered), rendered)
    return review


def polarity_confused():
    """Judges correctly but answers the admit-question no matter which
    question was asked — the literalist that never re-reads the prompt."""
    def review(probe_id: str, rendered: dict) -> str:
        v = _oracle_verdict(rendered)
        if v == "ABSTAIN":
            return "ABSTAIN"
        return "YES" if v == "ADMIT" else "NO"  # as if question == admit
    return review


def manufacturer():
    """Never abstains: on no-signal cases it fabricates a confident
    ADMIT. Honest wherever evidence exists."""
    def review(probe_id: str, rendered: dict) -> str:
        v = _oracle_verdict(rendered)
        return _answer("ADMIT" if v == "ABSTAIN" else v, rendered)
    return review


def drifter():
    """Criteria loosen mid-stream: ties (Σ == threshold) are refused
    early, admitted after enough probes have gone by. Everything with a
    real margin stays honest — the drift is exactly at the border."""
    seen = {"n": 0}

    def review(probe_id: str, rendered: dict) -> str:
        seen["n"] += 1
        merits = [e["merit"] for e in rendered["evidence"]]
        if any(m is None for m in merits):
            return _answer("ABSTAIN", rendered)
        s = sum(merits)
        if s == rendered["threshold"]:
            v = "ADMIT" if seen["n"] > 100 else "REFUSE"
        else:
            v = "ADMIT" if s > rendered["threshold"] else "REFUSE"
        return _answer(v, rendered)
    return review


def constant_admit():
    """Admits everything, content unread. Perfectly coherent — and
    caught by the calibration and signal codes, which is the whole
    reason coherence alone is never the score."""
    def review(probe_id: str, rendered: dict) -> str:
        return _answer("ADMIT", rendered)
    return review


def coin():
    """Deterministic noise: the answer is a hash parity of the probe id.
    Incoherent on every unsigned dimension; NOT a sycophant — symmetric
    noise cancels in the signed frame statistic, and that asymmetry is
    part of what the matrix validates."""
    def review(probe_id: str, rendered: dict) -> str:
        h = hashlib.sha256(("coin-v1/" + probe_id).encode("ascii")).digest()
        return "YES" if h[0] % 2 == 0 else "NO"
    return review


_FACTORY = {
    "oracle": oracle,
    "position_biased": position_biased,
    "wording_keyed": wording_keyed,
    "sycophant": sycophant,
    "contrarian": contrarian,
    "polarity_confused": polarity_confused,
    "manufacturer": manufacturer,
    "drifter": drifter,
    "constant_admit": constant_admit,
    "coin": coin,
}


def make(name: str):
    """A FRESH instance per call (stateful reviewers must not leak state
    across runs)."""
    return _FACTORY[name]()
