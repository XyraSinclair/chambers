from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List

from .codebook import RESULT_VERDICT
from .engine import LaneResult, TradeOutcome


def _lane_leakage_rows(result: LaneResult, accountant: Any) -> List[dict]:
    technique_ids = {outcome.technique_id for outcome in result.outcomes}
    lane_prefix = f"valuation:{result.lane_id}:"
    rows: List[dict] = []
    for row in accountant.report():
        technique = str(row.get("technique", ""))
        observer = str(row.get("observer", ""))
        if technique in technique_ids or technique.startswith(lane_prefix):
            if observer in {result.buyer, result.seller}:
                rows.append(dict(row))
    rows.sort(key=lambda row: (str(row.get("technique", "")), str(row.get("observer", ""))))
    return rows


def _append_lines(lines: List[str], title: str, items: Iterable[str]) -> None:
    lines.append(title)
    wrote = False
    for item in items:
        wrote = True
        lines.append(f"- {item}")
    if not wrote:
        lines.append("- (none)")


def _render_negotiation(lines: List[str], outcome: TradeOutcome) -> None:
    transcript = outcome.negotiation
    if transcript is None:
        lines.append("Price debate: not reached.")
        return

    lines.append(
        f"Price debate: {len(transcript.rounds)} round(s), "
        f"{transcript.bits_leaked_by_negotiation:.2f} bits leaked through bargaining."
    )
    if transcript.rounds:
        lines.append("")
        lines.append("| Round | Ask Commit | Bid Commit | Overlap | Bits |")
        lines.append("| --- | --- | --- | --- | ---: |")
        for round_ in transcript.rounds:
            lines.append(
                f"| {round_.round_index} | {round_.seller_commitment_hash} | "
                f"{round_.buyer_commitment_hash} | {'yes' if round_.overlap else 'no'} | "
                f"{round_.seller_bits + round_.buyer_bits:.2f} |"
            )
    if transcript.final_cross is None:
        lines.append("")
        lines.append("Final cross: none.")
        return

    cross = transcript.final_cross
    lines.append("")
    if cross.cleared_price is None:
        lines.append(
            f"Final cross: {cross.outcome}. (Draws and reserve are party-private inputs; not published.)"
        )
    else:
        lines.append(
            f"Final cross: cleared at {cross.cleared_price} credits."
        )


# Structural contracts of the sim's non-codebook channels. These operated;
# the receipt must name them in the receipt PROPER, not the footnote — the
# declared pool dwarfs the derived pool in this sim and hiding it would be
# the original theater with the sign flipped. DRIFT GUARD: any channel not
# registered here (or a future second codebook channel) gets the honest
# "contract unknown" line below, never a guessed one — a wrong contract on
# a receipt is worse than an admitted gap.
_DECLARED_CHANNEL_CONTRACTS = {
    "black_box_probe": "NO closed alphabet — declared estimate per probe, honest tripwire not theorem",
    "black_box_probe_REFUSED": "refusal marker — the probe was refused before crossing; the refusal event itself is ledgered",
    "price_round": "NO closed alphabet — commitment round; declared 3.0-bit estimate per round",
    "cleared_price": "NO closed alphabet — the cleared price itself; declared estimate",
    "method_reveal_paid": "full method crosses after settlement (see widenings); declared entropy",
}
_UNREGISTERED_CONTRACT = "unregistered channel — structural contract UNKNOWN (receipt defect: register it)"


def structural_receipt_lines(result: LaneResult, accountant: Any) -> List[str]:
    """The receipt in the structural register (STRUCTURE.md §5): purpose,
    audience, every channel that operated, crossings, exposure standings,
    influence, non-promises — bit arithmetic demoted to the footnote, but
    every channel and every non-negligible exposure named in the receipt
    proper. Shared by the console transcript and the markdown narrative so
    the two surfaces cannot drift."""
    acc = result.account
    # The sim has a single verdict channel; if the engine grows more, thread
    # the codebook through LaneResult rather than widening this constant.
    cb = RESULT_VERDICT
    rows = _lane_leakage_rows(result, accountant)
    lines: List[str] = []

    lines.append("purpose (the program both parties entered; consent signatures NOT")
    lines.append("MECHANIZED in this sim — same named-gap status as influence below):")
    lines.append(
        f"  buyer {result.buyer} appraises seller {result.seller}'s portfolio for trade,"
    )
    lines.append(
        f"  via attested results ({cb.name!r} codebook), metered black-box probes,"
    )
    lines.append("  and a commitment-based price debate — every channel named below.")

    lines.append("audience (who could observe):")
    lines.append(
        f"  {result.buyer} (buyer) and {result.seller} (seller); the doubly-sealed"
    )
    lines.append(
        "  enclave verifier saw both sides' inputs (named again under non-promises)."
    )

    # Every channel that actually operated this lane, from the ledger rows —
    # read off the run, not restated from intent.
    operated: List[str] = []
    for row in rows:
        for channel, _bits in row.get("debits", []):
            if channel not in operated:
                operated.append(channel)
    lines.append("channels that operated (each with its structural contract):")
    if cb.name in operated or not operated:
        lines.append(
            f"  {cb.name} = {{{', '.join(cb.symbols)}}}"
            f"  [closed alphabet; {cb.capacity_bits:.2f} bits/use, derived]"
        )
    for channel in operated:
        if channel == cb.name:
            continue
        contract = _DECLARED_CHANNEL_CONTRACTS.get(channel, _UNREGISTERED_CONTRACT)
        lines.append(f"  {channel}: {contract}")

    widenings = [
        (
            f"paid method reveal of {o.technique_id} to {result.buyer} after settlement"
            f" — alphabet leg widened from {cb.name!r} to the full method, one-way;"
            f" settlement price {o.settlement.price} credits bundles the reveal; the"
            f" reveal is charged on its own account, so the verdict-channel ceiling"
            f" is not retroactively widened"
        )
        for o in result.outcomes
        if o.settlement is not None
    ]
    lines.append("context widenings (priced, one-way; consent NOT MECHANIZED — see purpose):")
    for w in widenings or ["(none)"]:
        lines.append(f"  * {w}")

    lines.append("what crossed:")
    for x in acc.what_crossed or ["(nothing)"]:
        lines.append(f"  + {x}")
    lines.append("what did NOT cross:")
    for x in acc.what_did_not_cross or ["(nothing)"]:
        lines.append(f"  - {x}")
    lines.append("who was paid:")
    for x in acc.who_was_paid or ["(no one)"]:
        lines.append(f"  $ {x}")

    flagged = [row for row in rows if str(row.get("class")) != "negligible"]
    lines.append("exposure standings a counterparty must see (everything above negligible):")
    if flagged:
        for row in flagged:
            marks = ""
            if row.get("blocked"):
                marks += ", further charges blocked"
            if row.get("incident"):
                marks += ", INCIDENT flagged"
            lines.append(
                f"  ! {row['observer']} holds {row['cumulative_bits']} of"
                f" {row['entropy_bits']} entropy bits ({row['class']}{marks})"
                f" of {row['technique']}"
            )
    else:
        lines.append("  (none above negligible)")

    lines.append("influence (what the sensitive inputs changed):")
    lines.append(
        "  counterfactual influence view: NOT RUN in this simulation — a named"
    )
    lines.append(
        "  gap (STRUCTURE.md §5, item 5), not a waived one; the live chamber's"
    )
    lines.append("  paired-silo diff is the real mechanism.")

    lines.append("what it CANNOT promise:")
    for x in acc.what_it_cannot_promise:
        lines.append(f"  ! {x}")

    lines.append("footnote — composition budget (the anti-laundering clause):")
    lines.append("  per (target, observer) account: observation charges / block-ceiling,")
    lines.append("  with consented post-settlement reveals split out (they are widenings,")
    lines.append("  not observation-budget spend) and declared entropy for scale:")
    for row in rows:
        reveal_bits = sum(
            bits for channel, bits in row.get("debits", []) if channel == "method_reveal_paid"
        )
        observed = round(float(row["cumulative_bits"]) - reveal_bits, 3)
        reveal_note = f" + {reveal_bits} reveal (consented widening)" if reveal_bits else ""
        lines.append(
            f"    {row['technique']} @ {row['observer']}:"
            f" {observed}/{row['ceiling_bits']} bits{reveal_note}"
            f" (entropy {row['entropy_bits']}, {row['class']})"
        )
    lines.append(
        "  derived charges (closed alphabets) are exact ceilings; declared charges"
    )
    lines.append(
        "  (probes, reveals, negotiation) are honest estimates — on declared"
    )
    lines.append(
        "  channels the budget bounds the LEDGER, not the adversary (CALCULUS.md"
    )
    lines.append(
        "  §6 provisos). Refusal happens BEFORE the crossing. Not a harm claim"
    )
    lines.append("  (STRUCTURE_LAWS.harmIsNotDenominatedInBits).")
    return lines


def render_report(result: LaneResult, accountant: Any) -> str:
    lines: List[str] = []
    lines.append(f"# IP Trade Narrative: {result.lane_id}")
    lines.append("")
    lines.append(f"Buyer `{result.buyer}` evaluated seller `{result.seller}` under bounded observation.")
    if result.courtfile_validation:
        lines.append(f"Courtfile validation: {result.courtfile_validation}.")
    lines.append("")

    for outcome in result.outcomes:
        lines.append(f"## {outcome.technique_id} [{outcome.area}]")
        lines.append("")
        _append_lines(lines, "Verified results:", outcome.verdict.proven)
        lines.append("")
        _append_lines(lines, "Trusted assumptions:", outcome.verdict.trusted)
        lines.append("")
        _append_lines(lines, "Still unprovable:", outcome.verdict.unprovable)
        lines.append("")

        if outcome.appraisal is None:
            lines.append("Appraisal: none.")
        else:
            lines.append(
                f"Appraisal: {outcome.appraisal.est_value_credits} credits at "
                f"{outcome.appraisal.confidence:.2f} confidence; "
                f"{outcome.appraisal.bits_spent:.2f} bits spent on extra probing."
            )
            lines.append(f"Rationale: {outcome.appraisal.rationale}")
        lines.append("")

        _render_negotiation(lines, outcome)
        lines.append("")

        if outcome.settlement is not None:
            lines.append(
                f"Settlement: {outcome.settlement.state} at {outcome.settlement.price} credits via "
                f"{outcome.settlement.regime}."
            )
            lines.append(
                f"Realized value: {outcome.realized_value_credits}; buyer regret: {outcome.buyer_regret_credits}."
            )
        else:
            lines.append(f"Settlement: none. Blocked reason: {outcome.blocked_reason or 'n/a'}.")
        lines.append("")

    lines.append("## Receipt (structural register — STRUCTURE.md §5)")
    lines.append("")
    lines.append("```text")
    lines.extend(structural_receipt_lines(result, accountant))
    lines.append("```")
    lines.append("")

    lines.append("## Leakage Tally (footnote detail)")
    lines.append("")
    leakage_rows = _lane_leakage_rows(result, accountant)
    if leakage_rows:
        lines.append("| Technique | Observer | Bits | Fraction | Class | Blocked | Incident |")
        lines.append("| --- | --- | ---: | ---: | --- | --- | --- |")
        for row in leakage_rows:
            lines.append(
                f"| {row['technique']} | {row['observer']} | {row['cumulative_bits']} | "
                f"{row['fraction']:.3f} | {row['class']} | {row['blocked']} | {row['incident']} |"
            )
    else:
        lines.append("No leakage rows recorded.")
    lines.append("")
    return "\n".join(lines)


def write_report(result: LaneResult, accountant: Any, path: Any) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_report(result, accountant) + "\n", encoding="utf-8")
    return out_path
