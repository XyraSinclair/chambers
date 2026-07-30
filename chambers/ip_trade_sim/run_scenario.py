from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from . import strategies
from .agents import AgentStrategies, codex_reasoner, deterministic_reasoner
from .engine import run_lane
from .hooks import interactive_hook, recording_hook, scripted_hook
from .leakage import LeakageAccountant
from .report import render_report, write_report
from .scenario import build_rich_labs


def _load_policy(path: Optional[str]) -> dict:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("policy file must contain a JSON object")
    return payload


def _choose_hook(args: argparse.Namespace):
    if args.interactive:
        return recording_hook(interactive_hook)
    policy = _load_policy(args.policy)
    return recording_hook(scripted_hook(policy))


def _choose_strategies(args: argparse.Namespace):
    if args.agent_codex:
        return AgentStrategies(reasoner=codex_reasoner)
    if args.agent:
        return AgentStrategies(reasoner=deterministic_reasoner)
    return strategies


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the richer IP-trade scenario.")
    parser.add_argument("--rich", action="store_true", help="Explicitly select the richer scenario.")
    parser.add_argument("--interactive", action="store_true", help="Prompt on stdin for reveal, reserve, and settlement gates.")
    parser.add_argument("--policy", help="Path to a JSON policy file for scripted hooks.")
    parser.add_argument("--agent", action="store_true", help="Use AgentStrategies with the deterministic reasoner.")
    parser.add_argument("--agent-codex", action="store_true", help="Use AgentStrategies with the codex reasoner stub.")
    args = parser.parse_args(argv)

    scenario_builder = build_rich_labs
    trade_strategies = _choose_strategies(args)
    hook = _choose_hook(args)
    a, b = scenario_builder()
    accountant = LeakageAccountant()

    results = [
        run_lane(a, b, accountant, trade_strategies, hook=hook, seed="rich-AB"),
        run_lane(b, a, accountant, trade_strategies, hook=hook, seed="rich-BA"),
    ]

    rendered = []
    for result in results:
        if result.courtfile_dir:
            report_path = Path(result.courtfile_dir) / "report.md"
        else:
            report_path = Path("chambers/.chamber/ip_trades") / result.lane_id / "report.md"
        write_report(result, accountant, report_path)
        rendered.append(render_report(result, accountant))

    print("\n\n".join(rendered))
    audit = accountant.ledger.audit()
    if audit:
        raise RuntimeError(f"charge-kernel ledger audit findings: {audit}")
    print(f"\ncharge-kernel audit: clean ({accountant.ledger.event_count()} events)")
    print(f"\nFinal credits: {a.name}={a.credits}  {b.name}={b.credits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
