"""The research substrate: estimate how out-of-distribution a technique is.

Cryptography (iptrade.ts) marks novelty/transfer UNPROVABLE. But a research
substrate can ESTIMATE out-of-distribution-ness vs public prior art, with
evidence, citations, and calibrated confidence. That is a third epistemic lane
between proven and unprovable: ESTIMATED. It never becomes a proof — it is
evidence-backed, gameable, and carries its caveats.

Backends are pluggable:
  - ScryBackend queries the real hosted literature substrate (SQL-over-HTTPS over
    papers/OpenAlex; the "all of arXiv searchable, good SQL" surface).
  - OfflineBackend is deterministic from the description — the sim and tests never
    depend on the network.

An estimate feeds the valuation haircut: high OOD (little prior art) => plausibly
novel => less discount on the "novelty" the buyer cannot verify cryptographically;
low OOD (crowded neighborhood) => the technique is probably not the moat it claims.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from .leakage import estimate_localization_bits


@dataclass
class NoveltyEstimate:
    technique_id: str
    ood_score: float                     # 0..1, higher = more out-of-distribution / novel
    prior_art_density: int               # how crowded the neighborhood is
    prior_art_examples: List[str] = field(default_factory=list)  # citeable titles
    method: str = "unknown"
    confidence: float = 0.3
    gameability_caveat: str = ""
    epistemic_lane: str = "estimated"    # never 'proven'
    backend: str = "offline"


class NoveltyBackend(Protocol):
    def prior_art(self, keywords: str, limit: int) -> "PriorArt": ...


@dataclass
class PriorArt:
    density: int
    examples: List[str]
    ok: bool
    note: str = ""


# ---- offline deterministic backend (default; no network) ----

# a tiny canned prior-art landscape keyed on capability vocabulary. Deterministic
# so tests/sim are reproducible; NOT a real corpus.
_CANNED = {
    "speculative": 42, "decode": 40, "medusa": 12, "attention": 380, "sparse": 210,
    "rotary": 55, "rlaif": 28, "constitutional": 18, "preference": 160, "dedup": 34,
    "curriculum": 46, "distill": 190, "long context": 120, "ring": 25,
}


class OfflineBackend:
    def prior_art(self, keywords: str, limit: int) -> PriorArt:
        kw = keywords.lower()
        density = 0
        hits = []
        for term, n in _CANNED.items():
            if term in kw:
                density += n
                hits.append(f"prior art on '{term}' (~{n} works)")
        # unknown vocabulary reads as sparse (plausibly novel) — but that is exactly
        # the gameable part: obscure phrasing looks novel offline.
        if density == 0:
            density = 1
            hits.append("no close prior art in canned landscape (obscure phrasing looks novel — gameable)")
        return PriorArt(density=density, examples=hits[:limit], ok=True, note="offline canned landscape")


# ---- real Scry backend ----

class ScryBackend:
    def __init__(self, timeout_s: float = 20.0):
        self.timeout_s = timeout_s
        self.key = self._load_key()

    @staticmethod
    def _load_key() -> Optional[str]:
        if os.environ.get("SCRY_API_KEY"):
            return os.environ["SCRY_API_KEY"]
        path = os.path.expanduser("~/.scry/.env")
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SCRY_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            return None
        return None

    def prior_art(self, keywords: str, limit: int) -> PriorArt:
        if not self.key:
            return PriorArt(0, [], ok=False, note="no SCRY_API_KEY")
        # SQL string literals are SINGLE-quoted; escape embedded quotes. (json.dumps
        # would emit double quotes, which SQL reads as an identifier — a 400.)
        lit = "'" + keywords.replace("'", "''") + "'"
        sql = ("SELECT title FROM scry.search_federated("
               + lit + ", NULL, ARRAY['paper'], "
               + str(int(limit)) + ", 2) LIMIT " + str(int(limit)))
        req = urllib.request.Request(
            "https://api.scry.io/v1/scry/query",
            data=sql.encode(),
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "text/plain",
                     "X-Scry-Max-Wait": str(int(self.timeout_s))},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            return PriorArt(0, [], ok=False, note=f"scry error: {type(e).__name__}")
        rows = body.get("rows", []) or []
        examples = [r[0] for r in rows if r and r[0]][:limit]
        return PriorArt(density=len(rows), examples=examples, ok=True, note="scry search_federated(paper)")


def _ood_from_density(density: int) -> "tuple[float, bool]":
    """Map prior-art density to (ood_score, sparse_is_ambiguous).

    CRITICAL honesty (the calibration-OOD paradox): sparse prior art does NOT
    mean novel. For a true crown jewel the nearest PUBLIC prior art is far
    precisely because the real prior art is SECRET/unpublished — and obscure
    phrasing also reads sparse. So density<=1 is UNKNOWN, flagged ambiguous, and
    its confidence must be crushed downstream — never a confident 0.85.
    Dense neighborhoods are the only regime where a low-OOD read is trustworthy.
    """
    if density <= 1:
        return (0.50, True)      # unknown, not novel — ambiguity flagged
    if density <= 5:
        return (0.55, True)
    if density <= 20:
        return (0.45, False)
    if density <= 60:
        return (0.30, False)
    return (0.15, False)


def _meter_estimate(
    technique_id: str,
    observer: Optional[str],
    accountant,
    estimate: NoveltyEstimate,
) -> NoveltyEstimate:
    if accountant is None or not observer:
        return estimate
    bits = estimate_localization_bits(estimate.prior_art_examples, estimate.prior_art_density)
    ok, _ = accountant.observe(
        technique_id,
        observer,
        "buyer_conditioned_estimate",
        bits,
        0,
        note=f"novelty estimate via {estimate.backend} localized prior art",
    )
    if ok:
        return estimate
    estimate.prior_art_examples = []
    estimate.gameability_caveat = (
        "estimation withheld by leakage budget: closest-prior-art citations are a scoop map. "
        + estimate.gameability_caveat
    )
    return estimate


def estimate_novelty(technique_id: str, description: str, keywords: str,
                     backend: Optional[NoveltyBackend] = None, limit: int = 25,
                     accountant=None, observer: Optional[str] = None) -> NoveltyEstimate:
    """Produce an ESTIMATED novelty/OOD assessment. Falls back to offline on any
    backend failure, lowering confidence and noting it."""
    used = backend or OfflineBackend()
    pa = used.prior_art(keywords, limit)
    backend_name = type(used).__name__
    if not pa.ok:
        # fall back to offline, honestly de-rating confidence
        off = OfflineBackend().prior_art(keywords, limit)
        ood, ambiguous = _ood_from_density(off.density)
        estimate = NoveltyEstimate(
            technique_id=technique_id, ood_score=ood,
            prior_art_density=off.density, prior_art_examples=off.examples,
            method="prior_art_density", confidence=0.20,
            gameability_caveat="offline fallback (real substrate unavailable: " + pa.note + "); "
                               + ("sparse prior art is UNKNOWN not novel — real prior art may be secret" if ambiguous else "uncalibrated"),
            backend="offline_fallback")
        return _meter_estimate(technique_id, observer, accountant, estimate)
    ood, ambiguous = _ood_from_density(pa.density)
    # base confidence by backend, then CRUSH it when the read is ambiguous (sparse)
    conf = 0.55 if backend_name == "ScryBackend" else 0.35
    if ambiguous:
        conf = min(conf, 0.20)   # a high-OOD read over sparse prior art is not trustworthy
    caveat = ("density is corpus-coverage-dependent and gamed by novel phrasing; "
              "embedding + citation-graph + reproduction evidence needed for higher confidence. "
              "UNCALIBRATED: no Brier backtest yet — treat confidence as provisional.")
    if ambiguous:
        caveat = ("SPARSE PRIOR ART = UNKNOWN, NOT NOVEL: a crown jewel's real prior art is often "
                  "secret/unpublished, and obscure phrasing also reads sparse. Do not price a novelty "
                  "premium on this. " + caveat)
    estimate = NoveltyEstimate(
        technique_id=technique_id, ood_score=ood,
        prior_art_density=pa.density, prior_art_examples=pa.examples,
        method="prior_art_density", confidence=conf,
        gameability_caveat=caveat, backend=backend_name)
    return _meter_estimate(technique_id, observer, accountant, estimate)
