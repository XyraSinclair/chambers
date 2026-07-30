from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from .scenario import build_labs, build_rich_labs
from .types import HumanHook


def _normalize_identifier(value: Any) -> str:
    return str(value or "").strip().lower()


def _safe_input(prompt: str, default: str) -> str:
    try:
        raw = input(prompt)
    except EOFError:
        return default
    text = raw.strip()
    return text if text else default


def _build_alias_map() -> Dict[str, set]:
    aliases: Dict[str, set] = {}
    for builder in (build_labs, build_rich_labs):
        for lab in builder():
            for technique in lab.portfolio:
                identifiers = {_normalize_identifier(technique.id), _normalize_identifier(technique.name)}
                for identifier in identifiers:
                    aliases.setdefault(identifier, set()).update(identifiers)
    return aliases


_ALIASES = _build_alias_map()


def _context_identifiers(context: dict) -> set:
    identifiers = {_normalize_identifier(context.get("technique"))}
    expanded = set(identifiers)
    for identifier in list(identifiers):
        expanded.update(_ALIASES.get(identifier, set()))
    return {identifier for identifier in expanded if identifier}


def _matches_target(context: dict, target: Any) -> bool:
    wanted = {_normalize_identifier(target)}
    expanded = set(wanted)
    for identifier in list(wanted):
        expanded.update(_ALIASES.get(identifier, set()))
    return bool(_context_identifiers(context) & {identifier for identifier in expanded if identifier})


def _coerce_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def interactive_hook(decision_point: str, context: dict) -> dict:
    technique = str(context.get("technique", "technique"))
    seller = str(context.get("seller", "seller"))

    if decision_point == "set_reserve":
        default_reserve = _coerce_int(context.get("default_reserve"))
        default_text = str(default_reserve if default_reserve is not None else 0)
        reserve = _safe_input(
            f"[set_reserve] {seller} reserve for {technique} [{default_text}]: ",
            default_text,
        )
        parsed = _coerce_int(reserve)
        return {"reserve": parsed if parsed is not None else (default_reserve or 0)}

    if decision_point == "approve_settlement":
        price = _coerce_int(context.get("price"))
        default = "y"
        answer = _safe_input(
            f"[approve_settlement] approve {technique} at {price if price is not None else '?'} credits? [Y/n]: ",
            default,
        )
        return {"veto": answer.lower() not in {"y", "yes"}}

    if decision_point == "consider_reveal":
        default = "y"
        answer = _safe_input(
            f"[consider_reveal] allow {seller} to offer {technique}? [Y/n]: ",
            default,
        )
        return {"veto": answer.lower() not in {"y", "yes"}}

    return {}


def scripted_hook(policy: Optional[dict]) -> HumanHook:
    policy = policy or {}
    withhold = list(policy.get("withhold") or [])
    reserve_overrides = policy.get("reserve") if isinstance(policy.get("reserve"), dict) else {}
    veto_settlement_over = _coerce_int(policy.get("veto_settlement_over"))

    def hook(decision_point: str, context: dict) -> dict:
        try:
            if decision_point == "consider_reveal":
                for target in withhold:
                    if _matches_target(context, target):
                        return {"veto": True}
                return {}

            if decision_point == "set_reserve":
                for target, reserve in reserve_overrides.items():
                    if _matches_target(context, target):
                        parsed = _coerce_int(reserve)
                        if parsed is not None:
                            return {"reserve": parsed}
                return {}

            if decision_point == "approve_settlement":
                price = _coerce_int(context.get("price"))
                if veto_settlement_over is not None and price is not None and price > veto_settlement_over:
                    return {"veto": True}
                return {}
        except Exception:
            return {}
        return {}

    return hook


class _RecordingHook:
    def __init__(self, base_hook: HumanHook) -> None:
        self._base_hook = base_hook
        self.records = []

    def __call__(self, decision_point: str, context: dict) -> dict:
        context_copy = copy.deepcopy(context)
        try:
            response = dict(self._base_hook(decision_point, context) or {})
            error = None
        except Exception as exc:
            response = {}
            error = str(exc)
        self.records.append(
            {
                "decision_point": decision_point,
                "context": context_copy,
                "response": copy.deepcopy(response),
                "error": error,
            }
        )
        return response


def recording_hook(base_hook: Optional[HumanHook] = None) -> HumanHook:
    return _RecordingHook(base_hook or scripted_hook({}))
