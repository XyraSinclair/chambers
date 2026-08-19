"""Frozen data model for the D1 slice — mirrors market.ts / pricing.ts /
entropy.ts nouns in runnable Python. Stdlib only. Self-contained on purpose:
this package is the candidate "counterparty-compilable kernel", so it must be
small enough for a second, independent implementation to re-derive and diff
against the golden trace (see golden/).

Vocabulary anchors, kept honest:
- There is no boolean `verified`. Oracle scores price against a pinned rubric;
  method claims stay unprovable.
- Budgets are tripwires, not certificates: exhausting one forces a decision;
  staying under one proves nothing.
- Standing authorizations move PAYOUTS, never content. Content release keeps
  its per-release human owner decision.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


def sha(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()[:24]


# ---- the sealed artifact (the vendor's crown jewel) ----

@dataclass
class SealedArtifact:
    """A vendor source tree / firmware image sealed inside the Chamber.

    Ground truth (which build×site pairs actually reach the vulnerable code)
    is derived deterministically from the id — hidden from every agent, known
    only to the simulation, exactly like `Technique.secret_payload` in
    ip_trade_sim. Nobody should reconstruct the reachability matrix from
    sanctioned outputs alone; the egress accountant enforces that.
    """
    id: str
    vendor: str                 # owning Principal (the PSIRT's Chamber owner)
    name: str
    component: str              # e.g. the embedded wolfden-tls
    entropy_bits: float         # info to reconstruct the sealed source structure
    n_builds: int               # the release train
    n_sites: int                # call sites of the component per build
    vuln_site: int              # ground truth: the site the live CVE reaches
    vuln_from_build: int        # ground truth: build that introduced reachability

    def reachable(self, build: int, site: int) -> bool:
        """Ground truth oracle — 1 structured bit per query, and the thing an
        over-prober is trying to sweep-reconstruct."""
        if not (0 <= build < self.n_builds and 0 <= site < self.n_sites):
            return False
        if site == self.vuln_site:
            return build >= self.vuln_from_build
        # deterministic background reachability (~1/8 of sites), so a sweep
        # is genuinely informative and not all-zeros
        h = hashlib.sha256(f"{self.id}:{build}:{site}".encode()).digest()
        return h[0] < 32


# ---- estimator attestation (entropy.ts EstimatorAttestation) ----

ADMISSIBLE_INDEPENDENCE = ("role_separated", "adversarial_review")


@dataclass
class EstimatorAttestation:
    estimator_id: str
    independence: str           # self_interested |