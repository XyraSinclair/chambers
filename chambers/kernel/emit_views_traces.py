"""Emit the golden views corpus for charge-views/1 (VIEWS-SPEC.md).

Deterministic: no randomness, no clocks. Each scenario writes:

    views_traces/<name>.input.json      canonical {fold, policy} pair
    views_traces/<name>.expected.json   canonical report or refusal

The expected values are computed by the Python reference (views.py). A
second implementation, written from VIEWS-SPEC.md alone, reproduces every
expected file bit-for-bit from the input file.

The parity scenario deliberately reuses a FROZEN fold from the ledger
corpus (forged-overspend), so the views corpus is anchored to bytes that
predate this spec — the migration proof in corpus form.

Run: python3 chambers/kernel/emit_views_traces.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.events import canonical_json  # noqa: E402
from chambers.kernel.views import LEGACY_DEFAULT_POLICY, view  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "views_traces")


def _policy(**overrides):
    p = json.loads(json.dumps(LEGACY_DEFAULT_POLICY))
    p.update(overrides)
    return p


def _frozen_fold(name: str):
    with open(os.path.join(HERE, "ledger_traces", name + ".expected.json")) as fh:
        return json.load(fh)["fold"]


MIXED_FOLD = {
    "accounts": [
        {"key": ["attention", "recv1", "sender9"], "cumulative_mbits": 900,
         "demanded_mbits": 900, "subject_entropy_mbits": 1000},
        {"key": ["exp", "chamberA", "readerB"], "cumulative_mbits": 260,
         "demanded_mbits": 810, "subject_entropy_mbits": 1000},
    ]
}

EDGE_FOLD = {
    "accounts": [
        {"key": ["exp", "capped", "reader"], "cumulative_mbits": 10**9,
         "demanded_mbits": 0, "subject_entropy_mbits": 1000},
        {"key": ["exp", "zero-entropy", "reader"], "cumulative_mbits": 0,
         "demanded_mbits": 0, "subject_entropy_mbits": 0},
    ]
}

CUSTOM_POLICY = _policy(
    name="strict-two-class",
    classes=[
        {"label": "tolerable", "max_permille": 100},
        {"label": "excessive", "max_permille": 600},
    ],
    terminal_label="breach",
    incident_permille=500,
)

NONMONOTONE_POLICY = _policy(name="broken")
NONMONOTONE_POLICY["classes"][1]["max_permille"] = 50  # ties the first boundary

BOOLEAN_SUM_FOLD = {
    "accounts": [
        {"key": ["exp", "a", "b"], "cumulative_mbits": 5,
         "demanded_mbits": 5, "subject_entropy_mbits": 100},
        {"key": ["exp", "a", "c"], "cumulative_mbits": True,
         "demanded_mbits": 0, "subject_entropy_mbits": 100},
    ]
}


def scenarios():
    yield "parity-forged-overspend", _frozen_fold("forged-overspend"), LEGACY_DEFAULT_POLICY
    yield "domain-void-attention", MIXED_FOLD, _policy(name="exp-only", domains=[["exp"]])
    yield "custom-vocabulary", MIXED_FOLD, CUSTOM_POLICY
    yield "edge-cap-and-zero-entropy", EDGE_FOLD, LEGACY_DEFAULT_POLICY
    yield "malformed-policy-nonmonotone", MIXED_FOLD, NONMONOTONE_POLICY
    yield "malformed-fold-boolean-sum", BOOLEAN_SUM_FOLD, LEGACY_DEFAULT_POLICY


def emit(out_dir: str = OUT) -> int:
    os.makedirs(out_dir, exist_ok=True)
    count = 0
    for name, fold, policy in scenarios():
        pair = {"name": name, "spec": "charge-views/1",
                "fold": fold, "policy": policy}
        with open(os.path.join(out_dir, name + ".input.json"), "w") as fh:
            fh.write(canonical_json(pair) + "\n")
        with open(os.path.join(out_dir, name + ".expected.json"), "w") as fh:
            fh.write(canonical_json(view(fold, policy)) + "\n")
        count += 1
    return count


if __name__ == "__main__":
    n = emit()
    print(f"emitted {n} views traces to {OUT}")
