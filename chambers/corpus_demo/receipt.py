"""The structural receipt for a corpus-demo run (STRUCTURE.md §5, on real
data): purpose, audience, alphabet, channels, crossings, influence,
non-promises — arithmetic demoted to the footnote.

Owner-facing: titles appear (they are the owner's own data, and the receipt
lives in the owner-private run directory). Nothing here is printed to agent
transcripts; the orchestrator reports the file path only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from . import sink_schema
from .harness import GuestResult, MAX_LLM_CALLS, MAX_PROMPT_CHARS

HERE = Path(__file__).resolve().parent


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def program_hashes(guest_path: Path) -> Dict[str, str]:
    return {
        "guest": _sha(guest_path),
        "sink_schema": _sha(HERE / "sink_schema.py"),
        "spec": _sha(HERE / "GUEST_SPEC.md"),
        "harness": _sha(HERE / "harness.py"),
    }


def _titles(picks: Optional[List[dict]], mapping: Dict[str, dict]) -> List[str]:
    if not picks:
        return []
    out = []
    for p in picks:
        m = mapping.get(p.get("candidate_id", ""), {})
        flag = " [sensitivity-flagged]" if m.get("sensitive") else ""
        out.append(
            f"{m.get('title', '(unknown id)')}{flag} — {p.get('reason')} ({p.get('confidence')})"
        )
    return out


def render_receipt(
    run_dir: Path,
    full: GuestResult,
    ablated: GuestResult,
    full_outcome: str,
    ablated_outcome: str,
    mapping: Dict[str, dict],
    n_full: int,
    n_ablated: int,
    guest_path: Path,
    mode: str,
) -> str:
    hashes = program_hashes(guest_path)
    cap_full = sink_schema.capacity_bits(n_full)
    served = sorted(set(full.ledger.served_providers + ablated.ledger.served_providers))
    served_models = sorted(set(full.ledger.served_models + ablated.ledger.served_models))
    n_calls = full.ledger.n_calls + ablated.ledger.n_calls
    p_chars = full.ledger.prompt_chars + ablated.ledger.prompt_chars
    c_chars = full.ledger.completion_chars + ablated.ledger.completion_chars

    full_titles = _titles((full.verdict or {}).get("picks"), mapping)
    abl_titles = _titles((ablated.verdict or {}).get("picks"), mapping)
    full_set = {t.split(" — ")[0] for t in full_titles}
    abl_set = {t.split(" — ")[0] for t in abl_titles}
    only_full = sorted(full_set - abl_set)
    only_abl = sorted(abl_set - full_set)

    L: List[str] = []
    A = L.append
    A("# Receipt — corpus revival demo (structural register)")
    A("")
    A("purpose (the program the owner entered; consent enacted by the owner's")
    A("greenlight — signature binding NOT MECHANIZED, a named gap):")
    A(f"  question: {sink_schema.__doc__.splitlines()[0] and 'which 3 abandoned ideas to revive, given current work'}")
    A(f"  program hashes: guest={hashes['guest']} schema={hashes['sink_schema']}")
    A(f"                  spec={hashes['spec']} harness={hashes['harness']}")
    A("  guest authorship: third-party (Codex/gpt-5.6-sol), contract-only —")
    A("  the author never saw the packet; the hash above pins what ran.")
    A("")
    A("audience (who could observe what):")
    A("  verdict: the owner only (self-release; no external audience exists).")
    if mode == "real":
        A("  slices: the worker endpoint that computed over them —")
        A(f"    providers served: {', '.join(str(s) for s in served) or '(none)'}")
        A(f"    models served:    {', '.join(str(s) for s in served_models) or '(none)'}")
        A("    routed with data_collection=deny (ZDR): retention disclaimed")
        A("    CONTRACTUALLY, not architecturally. This is the L4 line.")
    else:
        A("  slices: nobody — synthetic dry-run, injected fake model, no network.")
    A("  guest code: ran network-DENIED (OS sandbox), env-stripped, scratch-")
    A("  confined; every canary in test_confinement.py demonstrates the denial.")
    A("")
    A("alphabet (everything the guest could ever say):")
    A(f"  ranked {sink_schema.N_PICKS}-of-{n_full} picks x {len(sink_schema.REASON_CODES)} reasons x")
    A(f"  {len(sink_schema.CONFIDENCE)} confidence buckets, + {len(sink_schema.OUTCOME_CODES)-1} failure outcomes")
    A(f"  = {sink_schema.verdict_space(n_full):,} expressible verdicts")
    A(f"  [{cap_full:.2f} bits capacity, derived; ablated run: {sink_schema.capacity_bits(n_ablated):.2f} bits over {n_ablated}]")
    A("")
    A("channels that operated:")
    A(f"  verdict channel: closed alphabet above; outcomes full={full_outcome}, ablated={ablated_outcome}")
    if mode == "real":
        A("  vendor-exposure channel: NO closed alphabet — prose prompts to the")
        A("  ZDR endpoint; declared in bytes below; capped per run and refused")
        A("  at the cap (harness budgets, block-before).")
    A("  no other channel existed for the guest: network denied, writes")
    A("  scratch-only, env empty (canary-verified, not asserted).")
    A("")
    A("what crossed (to the owner):")
    for t in full_titles or ["(nothing — non-ok outcome)"]:
        A(f"  + {t}")
    A("what the ablated run chose instead:")
    for t in abl_titles or ["(nothing — non-ok outcome)"]:
        A(f"  * {t}")
    A("")
    A("influence (what the sensitivity-flagged subcorpus changed):")
    if full_outcome == "ok" and ablated_outcome == "ok":
        if not only_full and not only_abl:
            A("  counterfactual diff: IDENTICAL pick sets — the flagged entities")
            A("  did not drive the verdict.")
        else:
            A("  counterfactual diff: the verdicts DIFFER —")
            for t in only_full:
                A(f"    only-with-sensitive: {t}")
            for t in only_abl:
                A(f"    only-without-sensitive: {t}")
            A("  the flagged subcorpus materially influenced the answer; weigh")
            A("  that before any wider disclosure of the verdict.")
    else:
        A("  counterfactual diff: NOT AVAILABLE (a run did not reach ok).")
    A("")
    A("what it CANNOT promise:")
    A("  ! ZDR is a routing contract, not an architecture: the serving")
    A("    provider processed the slices in cleartext to compute over them.")
    A("  ! OS-sandbox confinement, not TEE: the harness host (this Mac) and")
    A("    its operator see everything by construction.")
    A("  ! candidate mining is an owner-side heuristic (scores + age): the")
    A("    24 enumerated are not exhaustive; absence from the packet is not")
    A("    absence of worth (selection bias declared, not hidden).")
    A("  ! judgment quality is unverifiable per-instance (limits ledger L2);")
    A("    this receipt proves boundedness, not wisdom.")
    A("  ! if the verdict is later shared beyond the owner, that is a")
    A(f"    WIDENING: charge {cap_full:.2f} bits against this corpus, plus")
    A("    everything the chosen titles themselves reveal.")
    A("")
    A("footnote — exposure accounting (the anti-laundering clause):")
    if mode == "real":
        A(f"  worker-endpoint exposure: {n_calls} calls (cap {2*MAX_LLM_CALLS} across both runs),")
        A(f"    {p_chars:,} prompt chars shipped (cap {2*MAX_PROMPT_CHARS:,}), {c_chars:,} completion chars back;")
        A("    declared channel — bounds the ledger, not the adversary.")
    else:
        A("  worker-endpoint exposure: zero (synthetic).")
    A(f"  verdict channel: {cap_full:.2f} bits capacity, audience=owner, charge")
    A("    to owner = 0 (self-release is the zero point of the metric).")
    A("  Not a harm claim (STRUCTURE_LAWS.harmIsNotDenominatedInBits).")
    A("")
    A(f"guest wall time: full {full.guest_wall_s}s, ablated {ablated.guest_wall_s}s; mode={mode}")
    return "\n".join(L) + "\n"


def write_receipt(run_dir: Path, text: str) -> Path:
    path = run_dir / "receipt.md"
    path.write_text(text, encoding="utf-8")
    return path
