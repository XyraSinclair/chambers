"""Orchestrate the corpus revival demo.

    python3 -m chambers.corpus_demo.run_demo --synthetic
    python3 -m chambers.corpus_demo.run_demo --real

Privacy discipline: this process prints ONLY safe summaries and file paths.
Slices, titles, and verdict content go to files in the owner-private run
directory (.chamber/, gitignored), never to stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import sink_schema
from .harness import GuestResult, run_guest
from .packet import build_packets
from .receipt import render_receipt, write_receipt

HERE = Path(__file__).resolve().parent
RUNS_ROOT = HERE.parent / ".chamber" / "corpus_demo"
GUEST = HERE / "guest" / "guest.py"


def _synthetic_run_dir() -> Path:
    run_dir = RUNS_ROOT / f"synthetic-{int(time.time())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    cands = [
        {
            "id": f"c{i:02d}",
            "title": f"Synthetic idea {i}",
            "slice": f"A synthetic idea about topic {i}: " + ("lorem " * 60),
        }
        for i in range(12)
    ]
    packet = {
        "question": "Which three are most worth reviving?",
        "context": "Synthetic context: owner builds private-compute chambers.",
        "candidates": cands,
    }
    (run_dir / "packet_full.json").write_text(json.dumps(packet), encoding="utf-8")
    ablated = dict(packet, candidates=cands[:9])
    (run_dir / "packet_ablated.json").write_text(json.dumps(ablated), encoding="utf-8")
    mapping = {
        c["id"]: {"title": c["title"], "sensitive": i >= 9, "entity_id": -1}
        for i, c in enumerate(cands)
    }
    (run_dir / "owner_mapping.json").write_text(json.dumps(mapping), encoding="utf-8")
    return run_dir


def _fake_llm(prompt: str, max_tokens: int = 1024) -> str:
    """Deterministic scripted model for the dry run: echoes plausible
    screening/ranking shapes so the guest's parsing paths execute."""
    if "json" in prompt.lower() or "rank" in prompt.lower():
        return (
            '{"ranking": ["c00", "c03", "c07"], "reasons": '
            '["unlocks_current_work", "cheap_to_validate", "synergy_with_chambers"], '
            '"confidence": ["medium", "medium", "low"]}'
        )
    return "c00: 8/10 strong fit\nc03: 7/10 good\nc07: 6/10 plausible"


def _validated_outcome(res: GuestResult, packet_path: Path) -> str:
    if res.outcome != "ok":
        return res.outcome
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    ids = [c["id"] for c in packet["candidates"]]
    problems = sink_schema.validate_verdict(res.verdict, ids)
    return "ok" if not problems else "rejected_schema"


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic", action="store_true")
    mode.add_argument("--real", action="store_true")
    args = ap.parse_args()

    if not GUEST.exists():
        print("guest/guest.py missing — Codex has not delivered yet", file=sys.stderr)
        return 2

    if args.synthetic:
        run_dir = _synthetic_run_dir()
        llm = _fake_llm
        mode_name = "synthetic"
        summary = {"n_full": 12, "n_ablated": 9}
    else:
        run_dir = RUNS_ROOT / f"real-{int(time.time())}"
        summary = build_packets(run_dir)
        llm = None  # harness uses the ZDR client
        mode_name = "real"
    print(f"run_dir: {run_dir}")
    print(f"packet summary: {summary}")

    full = run_guest(run_dir / "packet_full.json", GUEST, llm_fn=llm)
    print(
        f"full run: outcome={full.outcome} calls={full.ledger.n_calls} "
        f"wall={full.guest_wall_s}s err={full.error!r}"
    )
    ablated = run_guest(run_dir / "packet_ablated.json", GUEST, llm_fn=llm)
    print(
        f"ablated run: outcome={ablated.outcome} calls={ablated.ledger.n_calls} "
        f"wall={ablated.guest_wall_s}s err={ablated.error!r}"
    )

    full_outcome = _validated_outcome(full, run_dir / "packet_full.json")
    ablated_outcome = _validated_outcome(ablated, run_dir / "packet_ablated.json")
    print(f"validated outcomes: full={full_outcome} ablated={ablated_outcome}")

    mapping = json.loads((run_dir / "owner_mapping.json").read_text(encoding="utf-8"))
    receipt_text = render_receipt(
        run_dir,
        full,
        ablated,
        full_outcome,
        ablated_outcome,
        mapping,
        n_full=summary["n_full"],
        n_ablated=summary["n_ablated"],
        guest_path=GUEST,
        mode=mode_name,
    )
    receipt_path = write_receipt(run_dir, receipt_text)
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "mode": mode_name,
                "outcomes": {"full": full_outcome, "ablated": ablated_outcome},
                "verdict_full": full.verdict,
                "verdict_ablated": ablated.verdict,
                "exposure": {
                    "calls": full.ledger.n_calls + ablated.ledger.n_calls,
                    "prompt_chars": full.ledger.prompt_chars + ablated.ledger.prompt_chars,
                    "completion_chars": full.ledger.completion_chars
                    + ablated.ledger.completion_chars,
                    "providers": sorted(
                        set(full.ledger.served_providers + ablated.ledger.served_providers)
                    ),
                    "models": sorted(
                        set(full.ledger.served_models + ablated.ledger.served_models)
                    ),
                    "calls_detail": full.ledger.calls + ablated.ledger.calls,
                },
                "errors": {"full": full.error, "ablated": ablated.error},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"receipt: {receipt_path}")
    return 0 if (full_outcome == "ok" and ablated_outcome == "ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
