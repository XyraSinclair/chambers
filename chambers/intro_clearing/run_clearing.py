"""Run the purpose-blind introduction clearing demo end to end.

    python3 -m chambers.intro_clearing.run_clearing [--out DIR] [--full]

Seven chambers (a founder, a grantmaker, a proof-engineering studio, a
cryptography collective, a solo biostatistician, and two near-twin systems
teams) enroll with a clearing house. Six windows tell the whole arc:

  w1  honest worker    one introduction clears both outbound reviews (the
                       grantmaker redacts a tag on the way out); a strong
                       pair killed by an exclusion and a near-miss pair
                       leave no artifact anyone can see; every other filer
                       receives the byte-constant denial.
  w2  quoting worker   smuggles dossier prose into a card -> static scan
      overreach worker blocks it; an out-of-scope read trips the grant;
                       both stakes slashed. Owners see only denials — the
                       attacks are house-audit facts, not market facts.
  w3  counting worker  embeds a rank ("1 of 12") -> digit scan blocks it.
  w4  honest worker    the SAME good match again: reviews release, fees
                       and attention settle — and the lifetime exposure
                       account refuses the crossing. Everyone was paid,
                       nothing crossed, and that is the design.
  w5  honest worker    a fresh chamber under a fresh declared entity clears
  w6  honest worker    against the same grantmaker; then its near-twin does
                       too. Every DECLARED account stays under budget. The
                       coalition audit annex then re-scores the same ledger
                       under the scenario's ownership ground truth (two
                       fronts, one owner — a fact the house cannot verify)
                       and shows the merged account OVER the very budget
                       window four enforced: the sybil undercount, measured
                       and named, not solved and not gated on.

Crossed rationale text is never worker prose: the ordinal review gate has
each source reviewer select one of four fixed house projections rendered
from the approved structured fields, and that selection is charged to the
lifetime exposure accounts as the prose channel's entire capacity. Worker
rationale stays advisory (scanned, slashable, house-audit only).

The human head is ledgered too: every outbound review seats a named
reviewer from the source's bench, and the (source chamber x reviewer
entity) memory account is charged a content-independent CEILING — the
structured fields, the advisory worker prose at its cap, the candidate set
— before anything is shown. Nothing is ever refunded: a decline, a refused
crossing, a slashed worker all leave the charge standing. When a reviewer's
account cannot absorb another review they rotate off; an exhausted bench
fails closed. In this demo blackwood's prime reviewer absorbs windows one
and four and the relief reviewer takes the sybil windows, leaving the bench
saturated: one more blackwood review would fail closed.

Court files, receipts, and per-owner files persist per window under
chambers/.chamber/intro_clearing/, plus a run-level coalition_audit.json
and coalition_annex.txt. Owner files never contain house causes; denials are
one constant payload whatever the reason. Self-checks at the end assert the
slice's laws and exit nonzero on any failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chambers.kernel import (
    Ledger,
    OutcomeAttestationEvent,
    OutcomeCondition,
    SettlementRefused,
    attest_outcome,
    audit_settlement_codes,
    conservation_identity,
    resolve_bond,
    settlement_fold_canonical_v2,
    settlement_fold_full,
)

from .intro_clearing import (
    BUCKET_MILLIBITS,
    DENIAL_PAYLOAD,
    HOUSE_FEE_SIDE,
    NON_CLAIMS,
    ORDINAL_MILLIBITS,
    OUTCOME_CONTEST_TICKS,
    OUTCOME_FEE_UCR,
    OUTCOME_METRIC,
    OUTCOME_MIN_BOND_UCR,
    OWNER_ENDOWMENT,
    PARTY_OWNER_ENDOWMENT_UCR,
    PARTY_PLATFORM_FUND_UCR,
    PRESENCE_MILLIBITS,
    RAISE_PRICE_UCR,
    RATIONALE_CANDIDATE_COUNT,
    TAG_MILLIBITS,
    WORKER_ENDOWMENT,
    WORKER_FEE_SIDE,
    WORKER_STAKE,
    Chamber,
    ClearingHouse,
    canonical_json,
    coalition_audit,
    counting_worker,
    honest_worker,
    identity_millibits,
    overreach_worker,
    quoting_worker,
    rationale_candidates,
    sha256_hex,
)

# The demo house runs a deliberately small lifetime exposure budget so the
# fourth window can demonstrate refusal-by-accumulation: one cleared
# introduction fits, the identical second one does not.
DEMO_EXPOSURE_BUDGET_MILLIBITS = 30_000
# Reviewer memory budget sized so each reviewer absorbs exactly two reviews:
# blackwood's four reviewed windows force a visible rotation at window five.
DEMO_REVIEWER_MEMORY_BUDGET_MILLIBITS = 5_000_000
INTENT_FEE_MICROS = 6_000
GRANT_EXPIRES_TICK = 10
BASE_SCOPE = ("offers", "needs", "excludes")

# Scenario-oracle ground truth for the coalition audit: the two systems
# "teams" are fronts of one beneficial owner. The house never sees this map
# at clearing time and has no way to verify it; the audit takes it as a
# hypothesis and re-scores the settled ledger.
ENTITY_GROUND_TRUTH = {
    "entity:fenwick": "entity:fen_holdings",
    "entity:fairwater": "entity:fen_holdings",
}

# House-audit cause vocabulary that must NEVER appear in owner-visible bytes.
HOUSE_ONLY_CAUSE_TOKENS = (
    "near_miss", "vetoed", "no_coincidence", "scan_violation",
    "grant_violation", "grant_unusable", "grant_missing", "exposure_budget",
    "reserve_not_cleared", "attention_exhausted", "reviewer_memory_exhausted",
    "slash",
)


def demo_chambers() -> list:
    return [
        Chamber(
            chamber_id="ch_arden", owner_entity="entity:arden",
            contact_handle="founders@ardenlabs.example",
            offers=frozenset({"systems_rust", "distributed_systems"}),
            needs=frozenset({"grant_funding", "gtm"}),
            excludes=frozenset(),
            context_notes=(
                "Two founders building a verifiable compute runtime in Rust. "
                "Prior work on distributed consensus at a research lab. Seeking "
                "a lead grant and go to market help for a pilot with three "
                "design partners."),
            reserve_micros=800, attention_budget=3),
        Chamber(
            chamber_id="ch_blackwood", owner_entity="entity:blackwood",
            contact_handle="opencall@blackwoodtrust.example",
            offers=frozenset({"grant_funding", "gtm"}),
            needs=frozenset({"systems_rust", "distributed_systems"}),
            excludes=frozenset(),
            context_notes=(
                "Blackwood Trust runs an open call for infrastructure grants "
                "and hands on go to market support. Quiet fund, no press "
                "releases. Prefers teams with strong systems engineering "
                "backgrounds."),
            reserve_micros=1_200, attention_budget=5,
            reviewer_policy="mask:gtm", rationale_ordinal=1),
        Chamber(
            chamber_id="ch_caldera", owner_entity="entity:caldera",
            contact_handle="studio@caldera.example",
            offers=frozenset({"formal_verification", "compiler_engineering"}),
            needs=frozenset({"zk_proofs", "applied_cryptography"}),
            excludes=frozenset({"defense_adjacent"}),
            context_notes=(
                "Compiler and proof engineering studio exploring zero "
                "knowledge tooling. Will not take defense adjacent work under "
                "any terms."),
            reserve_micros=600, attention_budget=3),
        Chamber(
            chamber_id="ch_dune", owner_entity="entity:dune",
            contact_handle="hello@dunecollective.example",
            offers=frozenset({"zk_proofs", "applied_cryptography", "defense_adjacent"}),
            needs=frozenset({"formal_verification", "open_source_maintenance"}),
            excludes=frozenset(),
            context_notes=(
                "Cryptography collective shipping zero knowledge proof "
                "systems, some previous defense adjacent contracts. Looking "
                "for formal verification partners and open source "
                "maintainers."),
            reserve_micros=700, attention_budget=3),
        Chamber(
            chamber_id="ch_elm", owner_entity="entity:elm",
            contact_handle="elm@fieldnotes.example",
            offers=frozenset({"biostatistics", "open_source_maintenance"}),
            needs=frozenset({"climate_modeling", "applied_cryptography"}),
            excludes=frozenset(),
            context_notes=(
                "Solo biostatistician maintaining open source epidemiology "
                "tooling, curious about climate modeling collaborations and "
                "applied cryptography for health data."),
            reserve_micros=500, attention_budget=3),
        # The sybil pair: near-identical dossiers, two declared entities,
        # one true owner (scenario oracle only). The house holds both
        # dossiers — the correlation is visible, the ownership is not.
        Chamber(
            chamber_id="ch_fenwick", owner_entity="entity:fenwick",
            contact_handle="team@fenwicksystems.example",
            offers=frozenset({"systems_rust", "distributed_systems"}),
            needs=frozenset({"grant_funding", "gtm"}),
            excludes=frozenset(),
            context_notes=(
                "Small systems team building distributed runtime tooling in "
                "Rust, seeking a first infrastructure grant and launch "
                "support."),
            reserve_micros=900, attention_budget=3),
        Chamber(
            chamber_id="ch_fairwater", owner_entity="entity:fairwater",
            contact_handle="team@fairwatercompute.example",
            offers=frozenset({"systems_rust", "distributed_systems"}),
            needs=frozenset({"grant_funding", "gtm"}),
            excludes=frozenset(),
            context_notes=(
                "Small systems group building distributed runtime tooling in "
                "Rust, seeking a first infrastructure grant and launch "
                "help."),
            reserve_micros=900, attention_budget=3),
    ]


def build_house() -> ClearingHouse:
    house = ClearingHouse(
        exposure_budget=DEMO_EXPOSURE_BUDGET_MILLIBITS,
        reviewer_memory_budget=DEMO_REVIEWER_MEMORY_BUDGET_MILLIBITS)
    for chamber in demo_chambers():
        house.enroll(chamber)
    house.register_worker("w_honest", "entity:hive", honest_worker)
    house.register_worker("w_quote", "entity:quotist", quoting_worker)
    house.register_worker("w_count", "entity:countinghouse", counting_worker)
    house.register_worker("w_over", "entity:overreach", overreach_worker)
    for cid in sorted(house.chambers):
        house.issue_grant(cid, "w_honest", BASE_SCOPE, read_budget=3,
                          expires_tick=GRANT_EXPIRES_TICK)
    return house


def run_demo(house: ClearingHouse) -> list:
    results = []

    # Window 1 — the original five file; the honest worker scores all pairs.
    # The sybil pair is enrolled but silent: enrollment is not participation.
    for cid in ("ch_arden", "ch_blackwood", "ch_caldera", "ch_dune", "ch_elm"):
        house.file_intent(cid, INTENT_FEE_MICROS)
    results.append(house.run_window(lambda a, b: "w_honest"))

    # Window 2 — the quoting worker gets the good pair (its grant on the
    # blackwood side deliberately includes contextNotes: the scan, not the
    # scope, is what stops it). The overreach worker gets caldera x dune
    # with NO contextNotes scope: the grant itself stops it.
    house.issue_grant("ch_arden", "w_quote", BASE_SCOPE, read_budget=3,
                      expires_tick=GRANT_EXPIRES_TICK)
    house.issue_grant("ch_blackwood", "w_quote", BASE_SCOPE + ("contextNotes",),
                      read_budget=4, expires_tick=GRANT_EXPIRES_TICK)
    house.issue_grant("ch_caldera", "w_over", BASE_SCOPE, read_budget=3,
                      expires_tick=GRANT_EXPIRES_TICK)
    house.issue_grant("ch_dune", "w_over", BASE_SCOPE, read_budget=3,
                      expires_tick=GRANT_EXPIRES_TICK)
    for cid in ("ch_arden", "ch_blackwood", "ch_caldera", "ch_dune"):
        house.file_intent(cid, INTENT_FEE_MICROS)
    attack_map = {("ch_arden", "ch_blackwood"): "w_quote",
                  ("ch_caldera", "ch_dune"): "w_over"}
    results.append(house.run_window(
        lambda a, b: attack_map.get((a, b), "w_honest")))

    # Window 3 — the counting worker embeds a rank into the good pair.
    house.issue_grant("ch_arden", "w_count", BASE_SCOPE, read_budget=3,
                      expires_tick=GRANT_EXPIRES_TICK)
    house.issue_grant("ch_blackwood", "w_count", BASE_SCOPE, read_budget=3,
                      expires_tick=GRANT_EXPIRES_TICK)
    for cid in ("ch_arden", "ch_blackwood"):
        house.file_intent(cid, INTENT_FEE_MICROS)
    results.append(house.run_window(lambda a, b: "w_count"))

    # Window 4 — honest again, same pair: the lifetime exposure account
    # refuses the second crossing after fees and attention settle.
    for cid in ("ch_arden", "ch_blackwood"):
        house.file_intent(cid, INTENT_FEE_MICROS)
    results.append(house.run_window(lambda a, b: "w_honest"))

    # Windows 5 and 6 — the sybil arc. Each front clears against the same
    # grantmaker in its own window under a fresh DECLARED entity, so every
    # account the gate consults stays under budget. The gate is honest and
    # blind by construction: it cannot see beneficial ownership, only
    # declarations. The coalition audit afterwards measures what that
    # blindness cost.
    for cid in ("ch_blackwood", "ch_fenwick"):
        house.file_intent(cid, INTENT_FEE_MICROS)
    results.append(house.run_window(lambda a, b: "w_honest"))
    for cid in ("ch_blackwood", "ch_fairwater"):
        house.file_intent(cid, INTENT_FEE_MICROS)
    results.append(house.run_window(lambda a, b: "w_honest"))

    return results


# ---------------------------------------------------------------------------
# Persistence and validation
# ---------------------------------------------------------------------------

def default_out_dir() -> Path:
    return Path(__file__).resolve().parents[1] / ".chamber" / "intro_clearing"


def kernel_ledger_path(out_dir: Path) -> Path:
    return Path(out_dir) / "kernel_ledger.jsonl"


def persist_windows(house: ClearingHouse, results: list, out_dir: Path) -> list:
    written = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for res in results:
        wdir = out_dir / res["windowId"]
        (wdir / "owner_files").mkdir(parents=True, exist_ok=True)
        (wdir / "court_file.txt").write_text(res["courtFile"] + "\n",
                                             encoding="utf-8")
        (wdir / "receipt.json").write_text(
            json.dumps(res["receipt"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        for cid, owner_file in sorted(res["ownerFiles"].items()):
            (wdir / "owner_files" / f"{cid}.json").write_text(
                json.dumps(owner_file, indent=2, sort_keys=True) + "\n",
                encoding="utf-8")
        written.append(wdir)
    kernel_audit = house.kernel_ledger.audit()
    assert kernel_audit == [], kernel_audit
    if kernel_audit:
        raise RuntimeError(f"kernel ledger audit findings: {kernel_audit}")
    ledger_path = kernel_ledger_path(out_dir)
    ledger_path.write_text(house.kernel_ledger.to_jsonl(), encoding="utf-8")
    audit = build_coalition_audit(house)
    (out_dir / "coalition_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "coalition_annex.txt").write_text(
        render_coalition_annex(house, results, audit) + "\n", encoding="utf-8")
    summary = {
        "windows": [res["windowId"] for res in results],
        "settlementBalances": dict(sorted(house.ledger.accounts.items())),
        "settlementConserved": house.ledger.conserved(),
        "exposureAccounts": house.exposure.snapshot(),
        "crossingsTotal": len(house.crossings.entries),
        "kernelLedger": {
            "artifact": str(ledger_path),
            "events": house.kernel_ledger.event_count(),
            "auditFindings": kernel_audit,
        },
        "coalitionAudit": {
            "hypothesis": audit["hypothesis"],
            "undercountFindings": audit["undercountFindings"],
        },
        "nonClaims": NON_CLAIMS,
    }
    (out_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return written


def validate_window_dir(wdir: Path):
    """Slice-local court-file validator (pattern follows ip_trade_sim):
    structural checks a stranger can run without trusting the run."""
    try:
        wdir = Path(wdir)
        for name in ("court_file.txt", "receipt.json"):
            if not (wdir / name).exists():
                return False, f"missing {name}"
        receipt = json.loads((wdir / "receipt.json").read_text(encoding="utf-8"))
        court = (wdir / "court_file.txt").read_text(encoding="utf-8")

        non_claims = {row.get("key") for row in receipt.get("nonClaims", [])}
        if "noPerfectPrivacy" not in non_claims or "trustedHouse" not in non_claims:
            return False, "receipt nonClaims must name noPerfectPrivacy and trustedHouse"
        if receipt.get("settlement", {}).get("conserved") is not True:
            return False, "receipt settlement must be conserved"
        kernel = receipt.get("kernelLedger", {})
        if kernel.get("auditFindings") != []:
            return False, "receipt kernel ledger must be audit-clean"
        if not isinstance(kernel.get("events"), int) or kernel["events"] <= 0:
            return False, "receipt kernel ledger must report events"
        if not kernel.get("courtFile"):
            return False, "receipt kernel ledger must include a courtFile"
        if not receipt.get("laws"):
            return False, "receipt must list the laws it ran under"
        for section in ("WITHHELD", "NON-CLAIMS", "CROSSINGS"):
            if section not in court:
                return False, f"court file missing section {section}"

        crossing_shas = {e["payloadSha256"] for e in receipt.get("crossings", [])}
        denial_shas = {e["payloadSha256"] for e in receipt.get("crossings", [])
                       if e["kind"] == "denial"}
        if len(denial_shas) > 1:
            return False, "denials are not byte-constant"
        if denial_shas and denial_shas != {sha256_hex(DENIAL_PAYLOAD)}:
            return False, "denial payload does not match the constant"

        owner_dir = wdir / "owner_files"
        owner_files = sorted(owner_dir.glob("*.json")) if owner_dir.is_dir() else []
        if not owner_files:
            return False, "no owner files persisted"
        for path in owner_files:
            owner = json.loads(path.read_text(encoding="utf-8"))
            for delivered in owner.get("deliveries", []):
                if sha256_hex(delivered) not in crossing_shas:
                    return False, (f"{path.name}: delivered payload has no "
                                   f"crossing ledger entry")
            raw = json.dumps(owner)
            for token in HOUSE_ONLY_CAUSE_TOKENS:
                if token in raw:
                    return False, f"{path.name}: house-only cause token leaked: {token}"
        return True, (f"window ok: crossings={len(crossing_shas)} "
                      f"ownerFiles={len(owner_files)}")
    except Exception as exc:  # pragma: no cover — surfaced as validation failure
        return False, f"invalid window dir: {exc}"


def validate_kernel_ledger(out_dir):
    """Validate the run-level charge-kernel/2 JSONL artifact."""
    try:
        path = kernel_ledger_path(Path(out_dir))
        if not path.exists():
            return False, "missing kernel_ledger.jsonl"
        text = path.read_text(encoding="utf-8")
        ledger = Ledger.from_jsonl(text)
        findings = ledger.audit()
        if findings:
            return False, f"kernel ledger audit findings: {findings}"
        if ledger.to_jsonl() != text:
            return False, "kernel ledger did not round-trip canonically"
        return True, f"kernel ledger ok: events={ledger.event_count()} audit-clean"
    except Exception as exc:  # pragma: no cover — surfaced as validation failure
        return False, f"invalid kernel ledger: {exc}"


# ---------------------------------------------------------------------------
# Coalition audit: the sybil undercount, measured under a hypothesis
# ---------------------------------------------------------------------------

def build_coalition_audit(house: ClearingHouse) -> dict:
    return coalition_audit(house.exposure, ENTITY_GROUND_TRUTH)


def render_coalition_annex(house: ClearingHouse, results: list,
                           audit: dict) -> str:
    fronts = set(audit["hypothesis"])
    L = []
    add = L.append
    add("COALITION AUDIT ANNEX — lifetime exposure under an ownership HYPOTHESIS")
    add(f"Scope: whole run ({', '.join(res['windowId'] for res in results)}).")
    add("Audience tags: [HOUSE] audit-only arithmetic over the settled ledger; "
        "[ORACLE] scenario ground truth the house could not verify at "
        "clearing time.")
    add("This audit re-scores the exposure ledger under a supplied ownership")
    add("hypothesis. It DID NOT GATE any crossing: entity declarations are")
    add("untrusted input, the house has no way to verify beneficial ownership,")
    add("and everything below settled before the audit ran.")
    add("")
    add("I. HYPOTHESIS")
    for declared, true_entity in audit["hypothesis"].items():
        add(f"  [ORACLE] declared {declared} is a front of {true_entity}")
    add("  [HOUSE] the house held near-identical dossiers for these declared "
        "chambers; the correlation was visible, the ownership was not.")
    add("")
    add("II. DECLARED VIEW (the accounts the gate actually consulted)")
    shown = 0
    for row in audit["declaredAccounts"]:
        if row["readerEntity"] not in fronts:
            continue
        shown += 1
        status = "OVER budget" if row["overBudget"] else "under budget"
        add(f"  [HOUSE] {row['sourceChamber']} -> {row['readerEntity']}: "
            f"{row['millibitsCharged']}/{row['budgetMillibits']} millibits — "
            f"{status}")
    add(f"  [HOUSE] ({len(audit['declaredAccounts']) - shown} other declared "
        f"accounts are untouched by the hypothesis)")
    add("")
    add("III. MERGED VIEW (same ledger, hypothesis applied)")
    for row in audit["mergedAccounts"]:
        if row["identitiesUsed"] < 2:
            continue
        verdict = ("OVER the single-entity budget"
                   if row["overBudgetIfOneEntity"] else "still under budget")
        add(f"  [HOUSE] {row['sourceChamber']} -> {row['hypothesizedEntity']} "
            f"via {{{', '.join(row['declaredEntities'])}}}: "
            f"{row['millibitsCharged']} millibits against "
            f"{row['singleEntityBudgetMillibits']} — {verdict}. Fragmenting "
            f"stretched the effective budget to "
            f"{row['effectiveBudgetUnderFragmentation']} millibits "
            f"(x{row['identitiesUsed']}).")
    add("")
    add("IV. FINDINGS (undercount: invisible to every declared account)")
    if not audit["undercountFindings"]:
        add("  [HOUSE] none under this hypothesis.")
    for finding in audit["undercountFindings"]:
        overrun = (finding["millibitsCharged"]
                   - finding["singleEntityBudgetMillibits"])
        add(f"  [HOUSE] {finding['sourceChamber']} disclosed "
            f"{finding['millibitsCharged']} millibits about itself to "
            f"{finding['hypothesizedEntity']} — {overrun} past the "
            f"per-reader budget — while no declared account showed any "
            f"overrun.")
    for res in results:
        for att in res["attempts"]:
            if att.cause != "exposure_budget":
                continue
            stop = next(s["cause"] for s in att.trace if s["status"] == "stop")
            source, reader_entity = stop.split("exposure_budget:", 1)[1].split("->")
            held = house.exposure.charged.get((source, reader_entity), 0)
            add(f"  [HOUSE] parallel: window {res['windowId']} refused "
                f"{source} -> {reader_entity} when its account held {held} "
                f"millibits and the reviewed card priced {held} more "
                f"({held + held} total). The fragmented reader received that "
                f"same volume across two declared accounts.")
    add("")
    add("V. WHAT THIS AUDIT REFUSES TO CLAIM")
    for nc in audit["auditNonClaims"]:
        add(f"  [HOUSE] {nc['key']}: {nc['text']}")
    add("  [HOUSE] sourceSideShadow: under the hypothesis the source also met "
        "one counterparty where it believes it met two — concentration risk "
        "named here, not measured.")
    return "\n".join(L)


def validate_coalition_audit(out_dir):
    """Re-derive the merge from the persisted declared accounts: a stranger
    can check the arithmetic without trusting the run."""
    try:
        base = Path(out_dir)
        for name in ("coalition_audit.json", "coalition_annex.txt"):
            if not (base / name).exists():
                return False, f"missing {name}"
        audit = json.loads((base / "coalition_audit.json")
                           .read_text(encoding="utf-8"))
        annex = (base / "coalition_annex.txt").read_text(encoding="utf-8")
        for marker in ("HYPOTHESIS", "DID NOT GATE"):
            if marker not in annex:
                return False, f"annex missing epistemic marker: {marker}"
        if not audit.get("auditNonClaims"):
            return False, "audit must carry its own non-claims"
        hypothesis = audit.get("hypothesis", {})
        recomputed = {}
        for row in audit.get("declaredAccounts", []):
            true_entity = hypothesis.get(row["readerEntity"], row["readerEntity"])
            key = (row["sourceChamber"], true_entity)
            recomputed[key] = recomputed.get(key, 0) + row["millibitsCharged"]
        merged_rows = audit.get("mergedAccounts", [])
        if len(recomputed) != len(merged_rows):
            return False, "merged account count does not re-derive"
        for row in merged_rows:
            key = (row["sourceChamber"], row["hypothesizedEntity"])
            if recomputed.get(key) != row["millibitsCharged"]:
                return False, f"merged account does not re-derive: {key}"
        for finding in audit.get("undercountFindings", []):
            if not (finding["identitiesUsed"] > 1
                    and finding["overBudgetIfOneEntity"]
                    and finding["constituentsAllUnderBudget"]):
                return False, "finding does not satisfy the undercount definition"
        return True, (f"coalition audit ok: merged={len(merged_rows)} "
                      f"findings={len(audit.get('undercountFindings', []))}")
    except Exception as exc:  # pragma: no cover — surfaced as validation failure
        return False, f"invalid coalition audit: {exc}"


# ---------------------------------------------------------------------------
# Self-checks
# ---------------------------------------------------------------------------

def _intro_mb(house: ClearingHouse, tags: int) -> int:
    return (BUCKET_MILLIBITS + PRESENCE_MILLIBITS
            + identity_millibits(len(house.chambers)) + tags * TAG_MILLIBITS
            + ORDINAL_MILLIBITS)


def self_checks(house: ClearingHouse, results: list, window_dirs: list) -> list:
    checks = []

    def check(name: str, ok: bool, detail: str = ""):
        checks.append((name, bool(ok), detail))

    w1, w2, w3, w4, w5, w6 = results

    check("w1 causes: one cleared, one vetoed, one near-miss, seven silent",
          w1["receipt"]["attemptCausesHouseAudit"] == {
              "mutual_release": 1, "vetoed": 1, "near_miss": 1,
              "no_coincidence": 7})
    check("w2 causes: quote scanned out, overreach tripped, four silent",
          w2["receipt"]["attemptCausesHouseAudit"] == {
              "scan_violation": 1, "grant_violation": 1, "no_coincidence": 4})
    check("w3 causes: rank digits scanned out",
          w3["receipt"]["attemptCausesHouseAudit"] == {"scan_violation": 1})
    check("w4 causes: lifetime exposure budget refused the repeat",
          w4["receipt"]["attemptCausesHouseAudit"] == {"exposure_budget": 1})
    check("w5/w6 causes: each sybil front cleared in its own window",
          w5["receipt"]["attemptCausesHouseAudit"] == {"mutual_release": 1}
          and w6["receipt"]["attemptCausesHouseAudit"] == {"mutual_release": 1})

    intro_payloads = {}
    for res in results:
        for cid, payloads in res["deliveries"].items():
            for payload in payloads:
                if payload != DENIAL_PAYLOAD:
                    intro_payloads.setdefault(cid, []).append(json.loads(payload))
    intro_ticks = [e["tick"] for e in house.crossings.entries
                   if e["kind"] == "introduction"]
    check("six introductions crossed: the w1 pair, then one per sybil window",
          {cid: len(v) for cid, v in intro_payloads.items()}
          == {"ch_arden": 1, "ch_blackwood": 3, "ch_fenwick": 1,
              "ch_fairwater": 1}
          and intro_ticks == [1, 1, 5, 5, 6, 6])
    check("both fronts were introduced to the same grantmaker",
          all(json.loads(house.mailboxes[cid][0].decode("utf-8"))
              ["counterpartHandle"]
              == house.chambers["ch_blackwood"].contact_handle
              for cid in ("ch_fenwick", "ch_fairwater")))

    arden_card = intro_payloads.get("ch_arden", [{}])[0]
    expected_redacted = rationale_candidates(
        ("grant_funding",), ("distributed_systems", "systems_rust"),
        "high")[house.chambers["ch_blackwood"].rationale_ordinal]
    check("release is a subset of review: gtm dropped from arden's card, "
          "rationale re-rendered from approved fields only",
          arden_card.get("offersMatched") == ["grant_funding"]
          and arden_card.get("rationale") == expected_redacted
          and "gtm" not in json.dumps(arden_card))
    blackwood_card = intro_payloads.get("ch_blackwood", [{}])[0]
    check("unredacted direction released in full (four matched tags)",
          len(blackwood_card.get("offersMatched", []))
          + len(blackwood_card.get("needsMatched", [])) == 4)

    prose_bound = True
    for res in results:
        for att in res["attempts"]:
            if att.outcome != "cleared":
                continue
            for reader, release in att.cards_approved.items():
                source = house.chambers[release.source_chamber]
                expected = rationale_candidates(
                    release.offers_matched, release.needs_matched,
                    release.fit_bucket)[source.rationale_ordinal]
                if (release.rationale != expected
                        or release.rationale
                        == att.cards_proposed[reader].rationale):
                    prose_bound = False
    check("ordinal gate: every crossed rationale is the source-selected "
          "house candidate, never worker prose", prose_bound)
    check("selection channel charged and scheduled in every receipt",
          _intro_mb(house, 3)
          - (BUCKET_MILLIBITS + PRESENCE_MILLIBITS
             + identity_millibits(len(house.chambers)) + 3 * TAG_MILLIBITS)
          == ORDINAL_MILLIBITS
          and all(res["receipt"]["rationaleChannel"]["candidateSetSize"]
                  == RATIONALE_CANDIDATE_COUNT
                  and res["receipt"]["rationaleChannel"]
                  ["ordinalMillibitsPerCard"] == ORDINAL_MILLIBITS
                  for res in results))
    check("court file records the ordinal selections and their charge",
          "rationale ordinals" in w1["courtFile"]
          and "rationale ordinals" in w5["courtFile"])

    per_review = sum(w1["receipt"]["reviewerMemory"]["schedule"].values())
    memory = {(r["sourceChamber"], r["reviewerEntity"]):
              r["millibitsCeilingCharged"]
              for r in house.reviewer_memory.snapshot()}
    check("reviewer rotation: blackwood's prime seat exhausted into relief",
          all(res["attempts"][0].reviewers.get("ch_blackwood")
              == "reviewer:ch_blackwood:prime" for res in (w1, w4))
          and all(res["attempts"][0].reviewers.get("ch_blackwood")
                  == "reviewer:ch_blackwood:relief" for res in (w5, w6)))
    check("reviewer memory is irrevocable: four blackwood reviews charged, "
          "three crossings",
          memory.get(("ch_blackwood", "reviewer:ch_blackwood:prime"))
          == 2 * per_review
          and memory.get(("ch_blackwood", "reviewer:ch_blackwood:relief"))
          == 2 * per_review
          and sum(1 for e in house.crossings.entries
                  if e["kind"] == "introduction"
                  and e["sourceAttribution"] == "ch_blackwood") == 3)
    check("per-review ceiling matches its schedule and dwarfs the wire "
          "charge a hundredfold",
          per_review == w1["receipt"]["reviewerMemory"]
          ["perReviewCeilingMillibits"]
          and per_review > 100 * _intro_mb(house, 4))
    check("bench saturated: neither blackwood reviewer can seat another review",
          all(row["headroomMillibits"] < per_review
              for row in house.reviewer_memory.snapshot()
              if row["sourceChamber"] == "ch_blackwood"))
    check("owner files carry only their own bench's memory accounts",
          all(row["sourceChamber"] == cid
              for res in results
              for cid, owner_file in res["ownerFiles"].items()
              for row in owner_file["reviewerMemoryOwnBench"]))
    check("court file renders the reviewer-memory section with seats",
          "REVIEWER MEMORY" in w1["courtFile"]
          and "review seats" in w1["courtFile"])

    denial_shas = {e["payloadSha256"] for e in house.crossings.entries
                   if e["kind"] == "denial"}
    denial_count = sum(1 for e in house.crossings.entries if e["kind"] == "denial")
    check("denials byte-constant across every cause and window",
          denial_shas == {sha256_hex(DENIAL_PAYLOAD)} and denial_count == 11,
          f"count={denial_count}")

    owner_bytes = json.dumps([res["ownerFiles"] for res in results])
    crossed_bytes = " ".join(p.decode("utf-8")
                             for res in results
                             for payloads in res["deliveries"].values()
                             for p in payloads)
    leaked = [t for t in HOUSE_ONLY_CAUSE_TOKENS
              if t in owner_bytes or t in crossed_bytes]
    check("house-audit cause vocabulary absent from all owner-visible bytes",
          not leaked, f"leaked={leaked}")

    check("veto and near-miss left no owner-visible artifact in w1",
          all(w1["ownerFiles"][cid]["attemptsVisibleToOwner"] == []
              for cid in ("ch_caldera", "ch_dune", "ch_elm")))
    check("w2/w3 attacks invisible to owners (denials only, no attempt rows)",
          all(of["attemptsVisibleToOwner"] == []
              for res in (w2, w3) for of in res["ownerFiles"].values()))

    balances = house.ledger.accounts
    check("all three adversarial stakes slashed into the pool",
          balances["stake:w_quote"] == 0 and balances["stake:w_over"] == 0
          and balances["stake:w_count"] == 0
          and balances["slash_pool"] == 3 * WORKER_STAKE
          and all(house.workers[w]["slashed"]
                  for w in ("w_quote", "w_over", "w_count")))
    check("honest worker paid on every scan-pass (w1, w4, w5, w6) — even the refused one",
          balances["worker:w_honest"]
          == WORKER_ENDOWMENT - WORKER_STAKE + 8 * WORKER_FEE_SIDE)
    check("house earned its fee on all four reviewed attempts",
          balances["house"] == 8 * HOUSE_FEE_SIDE)
    check("attention was bought in w4 although nothing crossed",
          any(e["memo"].startswith("attention purchase") and e["tick"] == 4
              for e in house.ledger.entries))
    check("settlement conserved end to end",
          house.ledger.conserved()
          and house.ledger.total()
          == 7 * OWNER_ENDOWMENT + 4 * WORKER_ENDOWMENT)

    kernel_events = [res["receipt"]["kernelLedger"]["events"] for res in results]
    check("kernel ledger is audit-clean and receipts show cumulative events",
          house.kernel_ledger.audit() == []
          and all(res["receipt"]["kernelLedger"]["auditFindings"] == []
                  for res in results)
          and kernel_events == sorted(kernel_events)
          and kernel_events[-1] == house.kernel_ledger.event_count(),
          f"events={kernel_events}")

    exposure = {(r["sourceChamber"], r["readerEntity"]): r["millibitsCharged"]
                for r in house.exposure.snapshot()}
    check("lifetime exposure accounts hold exactly one introduction each way",
          exposure.get(("ch_arden", "entity:blackwood")) == _intro_mb(house, 4)
          and exposure.get(("ch_blackwood", "entity:arden")) == _intro_mb(house, 3),
          f"accounts={exposure}")
    check("no exposure account was charged past its budget by an introduction",
          all(not r["overBudget"] for r in house.exposure.snapshot()))

    redacted_mb = _intro_mb(house, 3)
    check("declared view: each front's account is under budget on its own",
          exposure.get(("ch_blackwood", "entity:fenwick")) == redacted_mb
          and exposure.get(("ch_blackwood", "entity:fairwater")) == redacted_mb
          and redacted_mb <= DEMO_EXPOSURE_BUDGET_MILLIBITS
          and 2 * redacted_mb > DEMO_EXPOSURE_BUDGET_MILLIBITS,
          f"redacted_mb={redacted_mb}")

    audit = build_coalition_audit(house)
    findings = audit["undercountFindings"]
    check("coalition audit: exactly one undercount finding — the fen operation",
          len(findings) == 1
          and findings[0]["sourceChamber"] == "ch_blackwood"
          and findings[0]["hypothesizedEntity"] == "entity:fen_holdings"
          and findings[0]["declaredEntities"] == ["entity:fairwater",
                                                  "entity:fenwick"]
          and findings[0]["millibitsCharged"] == 2 * redacted_mb
          and findings[0]["constituentsAllUnderBudget"],
          f"findings={findings}")
    refused_at = 2 * (exposure.get(("ch_blackwood", "entity:arden")) or 0)
    check("fragmented reader received exactly the volume the honest repeat "
          "reader was refused",
          bool(findings) and findings[0]["millibitsCharged"] == refused_at
          and any(att.cause == "exposure_budget" for att in w4["attempts"]))
    check("the gate never saw the hypothesis: both sybil crossings settled",
          not any(att.cause == "exposure_budget"
                  for res in (w5, w6) for att in res["attempts"]))
    annex = render_coalition_annex(house, results, audit)
    check("annex names its epistemics: hypothesis-supplied, never gated",
          "HYPOTHESIS" in annex and "DID NOT GATE" in annex
          and "hypothesisNotDiscovery" in annex)
    ok, msg = validate_coalition_audit(window_dirs[0].parent)
    check("persisted coalition audit validates (merge re-derived)", ok, msg)

    def _pseud(res, viewer):
        rows = res["ownerFiles"][viewer]["attemptsVisibleToOwner"]
        return rows[0]["counterpart"] if rows else None
    check("counterpart pseudonyms unlinkable across windows (w1 vs w4)",
          _pseud(w1, "ch_arden") is not None
          and _pseud(w4, "ch_arden") is not None
          and _pseud(w1, "ch_arden") != _pseud(w4, "ch_arden"))

    crossing_shas = {e["payloadSha256"] for e in house.crossings.entries}
    check("every mailbox byte has a crossing ledger entry",
          all(sha256_hex(p) in crossing_shas
              for payloads in house.mailboxes.values() for p in payloads))

    for wdir in window_dirs:
        ok, msg = validate_window_dir(wdir)
        check(f"persisted court file validates: {wdir.name}", ok, msg)
    ok, msg = validate_kernel_ledger(window_dirs[0].parent)
    check("persisted kernel ledger validates (audit-clean JSONL)", ok, msg)

    fresh = build_house()
    fresh_results = run_demo(fresh)
    check("deterministic replay: identical court files and coalition annex",
          [r["courtFile"] for r in fresh_results]
          == [r["courtFile"] for r in results]
          and canonical_json([r["receipt"] for r in fresh_results])
          == canonical_json([r["receipt"] for r in results])
          and render_coalition_annex(fresh, fresh_results,
                                     build_coalition_audit(fresh)) == annex)

    return checks


# ---------------------------------------------------------------------------
# The party act — the matchmaker story's fee legs on charge-settlement/2
# ---------------------------------------------------------------------------
#
# A separate small house (its own ledger, so the party artifact is one
# readable court file): Bob and Charlie, guests at a party, each hold a
# chamber; a matchmaking worker clears the same strong introduction in
# three windows, and each window's cleared match carries the two consumer
# fee legs on the REAL kernel settlement:
#
#   50 cents unconditional-to-raise  escrow + release bound to the exact
#                                    delivery ring's charge event id
#   $5 on outcome                    a /2 OUTCOME escrow (default
#                                    refund_to_payer) bound to the intro
#                                    card's exposure charge — the
#                                    first-contact receipt
#
# Act I   they talk 17 minutes: the platform's bonded platform_log fact
#         hardens through the contest window and the $5 releases against
#         the first-contact card's charge id; bonds return.
# Act II  silence: nobody attests; at expiry ANY party exercises the
#         declared default and the $5 refunds the payer, mechanically.
# Act III the lie: a colluding arbiter forges a below-lane "occurred"
#         into the open court; the honest issuer refuses the release live
#         (the forged fact could never satisfy the platform_log quorum);
#         the platform's log strictly overrides and the false bond is
#         SLASHED to the payer it would have harmed; the escrow refunds.
#
# The metric prices PRESENCE on a qualifying call — never engagement,
# never "talked because of the card": counterfactuals have no lane and
# cannot be expressed (asserted in the self-checks).

PARTY_ARBITER_FUND_UCR = 1_000_000
PARTY_GRANT_EXPIRES_TICK = 99


def party_chambers() -> list:
    return [
        Chamber(
            chamber_id="ch_bob", owner_entity="entity:bob",
            contact_handle="bob@party.example",
            offers=frozenset({"systems_rust", "distributed_systems"}),
            needs=frozenset({"grant_funding", "gtm"}),
            excludes=frozenset(),
            context_notes=(
                "Bob uploaded a lot of himself into a personal chamber: "
                "work history, enthusiasms, half formed beliefs, the things "
                "he would say late at night. None of it crosses."),
            reserve_micros=800, attention_budget=8),
        Chamber(
            chamber_id="ch_charlie", owner_entity="entity:charlie",
            contact_handle="charlie@party.example",
            offers=frozenset({"grant_funding", "gtm"}),
            needs=frozenset({"systems_rust", "distributed_systems"}),
            excludes=frozenset(),
            context_notes=(
                "Charlie's chamber holds a decade of grantmaking notes and "
                "private diligence memos. None of it crosses either."),
            reserve_micros=800, attention_budget=8),
    ]


def build_party_house() -> ClearingHouse:
    house = ClearingHouse()  # default budgets fit exactly this three-window arc
    for chamber in party_chambers():
        house.enroll(chamber)
    house.register_worker("w_matchmaker", "entity:matchmaker", honest_worker)
    for cid in sorted(house.chambers):
        house.issue_grant(cid, "w_matchmaker", BASE_SCOPE, read_budget=3,
                          expires_tick=PARTY_GRANT_EXPIRES_TICK)
    house.open_party_lane()
    return house


def run_party_scenario(house: ClearingHouse) -> dict:
    def clear_window():
        for cid in sorted(house.chambers):
            house.file_intent(cid, INTENT_FEE_MICROS)
        res = house.run_window(lambda a, b: "w_matchmaker")
        att = res["attempts"][0]
        assert att.outcome == "cleared", (att.outcome, att.cause)
        return res, att

    acts = {}

    # Act I — they talked seventeen minutes about the matched facet.
    w1, a1 = clear_window()
    attestations = house.party_attest_call(
        a1.attempt_id,
        evidence="platform:call:matched_facet:duration_seventeen_minutes")
    releases = house.party_settle_outcome(a1.attempt_id)
    acts["act1"] = {"window": w1, "attempt": a1,
                    "attestations": attestations, "releases": releases}

    # Act II — silence. No fact, no fee: the declared default refunds.
    w2, a2 = clear_window()
    refunds = house.party_expire_refund(a2.attempt_id)
    acts["act2"] = {"window": w2, "attempt": a2, "refunds": refunds}

    # Act III — the lie, and what the ledger does to it.
    w3, a3 = clear_window()
    legs = house.party["contingent"][a3.attempt_id]
    esc_bob = legs["ch_bob"]["escrow"]
    bank = house.party["bank"]
    bank.deposit("arbiter:colluding", PARTY_ARBITER_FUND_UCR, house.tick)
    house.tick += 1
    forged = OutcomeAttestationEvent(
        escrow_id=esc_bob.id, claim="occurred", lane="attested",
        independence="role_separated", evidence="we swear they talked",
        bond_ucr=OUTCOME_MIN_BOND_UCR, attestor="arbiter:colluding",
        seq=1, tick=house.tick)
    house.kernel_ledger.add(forged)  # merged straight into the open court
    house.tick += 1
    try:
        bank.release(esc_bob, OUTCOME_FEE_UCR,
                     [legs["ch_bob"]["introChargeId"]],
                     tick=house.tick, attestation_ids=[forged.id])
        refusal = None
    except SettlementRefused as exc:
        refusal = str(exc)
    house.tick += 1
    override = attest_outcome(
        house.kernel_ledger, esc_bob, house.party["platform"],
        "not_occurred", "platform_log", "role_separated",
        OUTCOME_MIN_BOND_UCR, tick=house.tick,
        evidence="platform:call:absent_from_this_log")
    house.tick += 1
    slash = resolve_bond(house.kernel_ledger, forged, "owner:ch_bob",
                         "slash", OUTCOME_MIN_BOND_UCR, tick=house.tick)
    house.tick = override.tick + OUTCOME_CONTEST_TICKS + 1
    bond_return = resolve_bond(
        house.kernel_ledger, override, house.party["platform"],
        "return_to_attestor", OUTCOME_MIN_BOND_UCR, tick=house.tick)
    refunds3 = house.party_expire_refund(a3.attempt_id)
    acts["act3"] = {"window": w3, "attempt": a3, "forged": forged,
                    "refusal": refusal, "override": override,
                    "slash": slash, "bondReturn": bond_return,
                    "refunds": refunds3}

    acts["view"] = house.party_court_view()
    return acts


def render_party_court_file(house: ClearingHouse, acts: dict) -> str:
    view = acts["view"]
    L = []
    add = L.append
    add("PARTY COURT FILE — the matchmaker's fee legs on charge-settlement/2")
    add("Audience tags: [HOUSE] audit-only; [STRANGER] re-derivable from the "
        "persisted JSONL artifact alone.")
    add("")
    add("I. THE LANE")
    add(f"  [HOUSE] metric: {OUTCOME_METRIC} — presence on a qualifying "
        f"call, NOT engagement, NOT causation.")
    add(f"  [HOUSE] raise price: {RAISE_PRICE_UCR} ucr unconditional; "
        f"outcome fee: {OUTCOME_FEE_UCR} ucr contingent; bond floor "
        f"{OUTCOME_MIN_BOND_UCR} ucr; contest window "
        f"{OUTCOME_CONTEST_TICKS} ticks; default refund_to_payer.")
    add("")
    add("II. ACT I — THEY TALKED (release)")
    a1 = acts["act1"]
    for att_ev in a1["attestations"]:
        add(f"  [HOUSE] platform_log attestation {att_ev.id[:23]} "
            f"claim=occurred bond={att_ev.bond_ucr} t{att_ev.tick}")
    for rel in a1["releases"]:
        add(f"  [HOUSE] release {rel.id[:23]} {rel.amount_ucr} ucr against "
            f"first-contact charge {rel.charge_ids[0][:23]} t{rel.tick}")
    add("")
    add("III. ACT II — SILENCE (refund, mechanically)")
    for ref in acts["act2"]["refunds"]:
        add(f"  [HOUSE] default_resolution {ref.id[:23]} {ref.amount_ucr} ucr "
            f"refund_to_payer (no quorum proof presented) t{ref.tick}")
    add("")
    add("IV. ACT III — THE LIE (refused, overridden, slashed)")
    a3 = acts["act3"]
    add(f"  [HOUSE] forged below-lane attestation {a3['forged'].id[:23]} "
        f"claim=occurred lane=attested (merged into the open court)")
    add(f"  [HOUSE] honest issuer refused the release live: {a3['refusal']}")
    add(f"  [HOUSE] platform log override {a3['override'].id[:23]} "
        f"claim=not_occurred lane=platform_log")
    add(f"  [HOUSE] slash {a3['slash'].id[:23]}: {OUTCOME_MIN_BOND_UCR} ucr "
        f"of the false bond flows to the harmed payer (owner:ch_bob), "
        f"derived from declared data, not chosen.")
    for ref in a3["refunds"]:
        add(f"  [HOUSE] default_resolution {ref.id[:23]} {ref.amount_ucr} ucr "
            f"refund_to_payer t{ref.tick}")
    add("")
    add("V. RINGS — every raise bound to its ring receipt")
    for ring in view["rings"]:
        add(f"  [HOUSE] {ring['payer']} -> {ring['payee']}: "
            f"{ring['priceUcr']} ucr for ring {ring['ringChargeId'][:23]} "
            f"(release {ring['releaseId'][:23]})")
    add("")
    add("VI. SETTLEMENT FOLD (/2 canonical) — [STRANGER] recomputable")
    for row in view["settlementV2"]["accounts"]:
        add(f"  [STRANGER] {row['account']}: available={row['available_ucr']} "
            f"deposited={row['deposited_ucr']} released_in={row['released_in_ucr']} "
            f"refunded_in={row['refunded_in_ucr']} slashed_in={row['slashed_in_ucr']}")
    cons = view["conservation"]
    add(f"  [STRANGER] conservation: {cons['lhs']} == {cons['rhs']} "
        f"(holds={cons['holds']})")
    codes = view["settlementAuditCodes"]
    add(f"  [STRANGER] settlement audit codes: "
        f"{codes if codes else 'none — artifact clean'}")
    add("")
    add("VII. GAPS AND NON-CLAIMS (what stays sim-local, what stays unpriced)")
    for gap in view["gaps"]:
        add(f"  [HOUSE] {gap['key']}: {gap['text']}")
    return "\n".join(L)


def persist_party(house: ClearingHouse, acts: dict, out_dir) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "party_court_file.txt").write_text(
        render_party_court_file(house, acts) + "\n", encoding="utf-8")
    (out_dir / "party_view.json").write_text(
        json.dumps(acts["view"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (out_dir / "party_ledger.jsonl").write_text(
        house.kernel_ledger.to_jsonl(), encoding="utf-8")


def validate_party_dir(out_dir):
    """A stranger's check: reload the JSONL artifact and re-derive every
    verdict — information audit, settlement audit, conservation, fold."""
    try:
        base = Path(out_dir)
        for name in ("party_court_file.txt", "party_view.json",
                     "party_ledger.jsonl"):
            if not (base / name).exists():
                return False, f"missing {name}"
        text = (base / "party_ledger.jsonl").read_text(encoding="utf-8")
        ledger = Ledger.from_jsonl(text)
        if ledger.to_jsonl() != text:
            return False, "party ledger did not round-trip canonically"
        if ledger.audit():
            return False, f"information audit findings: {ledger.audit()}"
        codes = audit_settlement_codes(ledger)
        if codes:
            return False, f"settlement audit codes: {codes}"
        lhs, rhs = conservation_identity(ledger)
        if lhs != rhs:
            return False, f"conservation identity broken: {lhs} != {rhs}"
        view = json.loads((base / "party_view.json").read_text(encoding="utf-8"))
        if settlement_fold_canonical_v2(ledger) != view["settlementV2"]:
            return False, "persisted fold does not re-derive from the ledger"
        return True, (f"party artifact ok: events={ledger.event_count()} "
                      f"settlement-clean conserved={lhs}")
    except Exception as exc:  # pragma: no cover — surfaced as validation failure
        return False, f"invalid party dir: {exc}"


def party_self_checks(house: ClearingHouse, acts: dict) -> list:
    checks = []

    def check(name: str, ok: bool, detail: str = ""):
        checks.append((name, bool(ok), detail))

    view = acts["view"]
    a1, a2, a3 = acts["act1"], acts["act2"], acts["act3"]
    accounts, escrows, bonds = settlement_fold_full(house.kernel_ledger)
    events = getattr(house.kernel_ledger, "_events")

    check("act I: both $5 legs released to the matchmaker on the platform log",
          accounts["worker:w_matchmaker"].available_ucr == 2 * OUTCOME_FEE_UCR)
    legs1 = house.party["contingent"][a1["attempt"].attempt_id]
    check("act I: each release references its first-contact card's charge id",
          [list(rel.charge_ids) for rel in a1["releases"]]
          == [[legs1[reader]["introChargeId"]] for reader in sorted(legs1)])
    check("act I: outcome escrows bound to the intro exposure accounts",
          all(list(legs1[reader]["escrow"].charge_keys)
              == [("exp", src, house.chambers[reader].owner_entity)]
              for reader, src in (("ch_bob", "ch_charlie"),
                                  ("ch_charlie", "ch_bob"))))
    check("rings: six deliveries, each 50-cent release bound to its exact "
          "ring receipt",
          len(view["rings"]) == 6
          and all(events[r["releaseId"]]["charge_ids"] == [r["ringChargeId"]]
                  and events[r["escrowId"]]["charge_keys"] == [r["ringKey"]]
                  for r in view["rings"]))
    check("act II: silence refunded both payers without anyone's cooperation",
          all(ref.payload()["kind"] == "default_resolution"
              and "attestation_ids" not in ref.payload()
              for ref in a2["refunds"]))
    check("act III: the honest issuer refused the forged-quorum release live",
          bool(a3["refusal"]) and "off-lane" in a3["refusal"])
    check("act III: the false bond was slashed to the harmed payer",
          accounts["owner:ch_bob"].slashed_in_ucr == OUTCOME_MIN_BOND_UCR
          and bonds[a3["forged"].id].remaining_ucr == 0
          and bonds[a3["forged"].id].slashed_ucr == OUTCOME_MIN_BOND_UCR)
    check("act III: the platform's own bond returned after its window",
          bonds[a3["override"].id].returned_ucr == OUTCOME_MIN_BOND_UCR)
    check("final balances are exact ledger arithmetic",
          accounts["owner:ch_bob"].available_ucr
          == PARTY_OWNER_ENDOWMENT_UCR - OUTCOME_FEE_UCR + OUTCOME_MIN_BOND_UCR
          and accounts["owner:ch_charlie"].available_ucr
          == PARTY_OWNER_ENDOWMENT_UCR - OUTCOME_FEE_UCR
          and accounts["arbiter:colluding"].available_ucr
          == PARTY_ARBITER_FUND_UCR - OUTCOME_MIN_BOND_UCR
          and accounts[house.party["platform"]].available_ucr
          == PARTY_PLATFORM_FUND_UCR)
    check("every escrow and bond fully resolved",
          all(e.remaining_ucr == 0 for e in escrows.values())
          and all(b.remaining_ucr == 0 for b in bonds.values()))
    check("artifact is audit-clean end to end (information + settlement)",
          house.kernel_ledger.audit() == []
          and view["settlementAuditCodes"] == [])
    lhs, rhs = conservation_identity(house.kernel_ledger)
    check("conservation identity holds over the whole party",
          lhs == rhs
          and rhs == (2 * PARTY_OWNER_ENDOWMENT_UCR
                      + PARTY_PLATFORM_FUND_UCR + PARTY_ARBITER_FUND_UCR),
          f"lhs={lhs} rhs={rhs}")
    check("leg statuses: released, refunded, refunded",
          [sorted({leg["status"] for leg in view["contingent"][aid].values()})
           for aid in (a1["attempt"].attempt_id, a2["attempt"].attempt_id,
                       a3["attempt"].attempt_id)]
          == [["released"], ["refunded"], ["refunded"]])
    try:
        OutcomeCondition(metric="talked_because_of_the_card",
                         lane="counterfactual", quorum=1,
                         min_independence="role_separated",
                         min_bond_ucr=1, contest_ticks=1)
        counterfactual_refused = False
    except ValueError:
        counterfactual_refused = True
    check("counterfactual metrics are unexpressible (no lane exists)",
          counterfactual_refused)
    check("named gaps ride the artifact (sim-local books, presence-not-"
          "engagement, collusion-to-deny)",
          {gap["key"] for gap in view["gaps"]}
          >= {"creditMicrosBooksAreSimLocal", "presenceNotEngagement",
              "counterfactualsRefused", "collusionToDeny"})
    check("CreditMicros book conserved (the named sim-local residue)",
          house.ledger.conserved())
    return checks


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _window_summary(res) -> str:
    receipt = res["receipt"]
    causes = ", ".join(f"{k}={v}" for k, v in
                       sorted(receipt["attemptCausesHouseAudit"].items()))
    return (f"{receipt['windowId']}  intents={receipt['intentsFiled']} "
            f"pairs={receipt['pairsScored']} cleared={receipt['introductionsCleared']} "
            f"denials={receipt['denialsDelivered']}  [{causes}]")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Purpose-blind introduction clearing demo")
    parser.add_argument("--out", type=Path, default=default_out_dir(),
                        help="court-file output directory")
    parser.add_argument("--full", action="store_true",
                        help="print every window's full court file")
    args = parser.parse_args(argv)

    house = build_house()
    results = run_demo(house)
    window_dirs = persist_windows(house, results, args.out)

    print("PURPOSE-BLIND INTRODUCTION CLEARING — four windows, one arc")
    print("=" * 72)
    for res in results:
        print(_window_summary(res))
    print()

    to_print = results if args.full else (results[0], results[3])
    for res in to_print:
        print(res["courtFile"])
        print()

    audit = build_coalition_audit(house)
    print(render_coalition_annex(house, results, audit))
    print()

    intro_count = sum(1 for e in house.crossings.entries
                      if e["kind"] == "introduction")
    denial_count = sum(1 for e in house.crossings.entries
                       if e["kind"] == "denial")
    notes_bytes = sum(len(ch.context_notes.encode("utf-8"))
                      for ch in house.chambers.values())
    print("RECAP")
    print("=" * 72)
    print(f"  crossed:   {intro_count} introductions (the w1 pair, one "
          f"direction redacted at source, plus one per sybil window), "
          f"{denial_count} byte-constant denials.")
    print(f"  withheld:  {notes_bytes} bytes of dossier prose (zero crossed); "
          f"all scores as numbers; every near-miss, veto, attack, and budget "
          f"refusal — owners cannot tell them apart.")
    print("  reviewed:  every card that reached an owner passed the source "
          "side's outbound review first; releases are drop-subsets, and the "
          "rationale that crossed is a house projection picked by ordinal "
          "(selection charged) — worker prose never crossed.")
    print("  paid:      the honest worker and the house were paid in window "
          "four although nothing crossed — attention and review are the "
          "product; disclosure is not guaranteed.")
    print("  memory:    every seated review charged its reviewer's lifetime "
          "memory account before showing — ceilings, never refunded; "
          "blackwood's bench rotated at window five and is now saturated: "
          "one more blackwood review would fail closed.")
    print(f"  audited:   the settled ledger re-scored under the scenario's "
          f"ownership hypothesis: {len(audit['undercountFindings'])} "
          f"undercount finding — the declared view showed no overrun anywhere "
          f"while one beneficial owner crossed the volume window four "
          f"refused. Measured, not prevented; the gate never saw the "
          f"hypothesis.")
    print("  refuses to claim:")
    for row in NON_CLAIMS:
        print(f"    - {row['key']}")
    print()

    checks = self_checks(house, results, window_dirs)
    print("SELF-CHECKS")
    print("=" * 72)
    failed = 0
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        suffix = f"  ({detail})" if (detail and not ok) else ""
        print(f"  [{mark}] {name}{suffix}")
        failed += 0 if ok else 1
    print()
    ok, msg = validate_kernel_ledger(args.out)
    print(f"kernel ledger: {msg}; artifact={kernel_ledger_path(args.out)}")

    # The party act — the matchmaker story's fee legs on charge-settlement/2.
    party = build_party_house()
    acts = run_party_scenario(party)
    party_dir = args.out / "party"
    persist_party(party, acts, party_dir)
    print()
    print("THE PARTY ACT — 50 cents to raise, $5 on outcome, on the kernel")
    print("=" * 72)
    print(render_party_court_file(party, acts))
    print()
    print("PARTY SELF-CHECKS")
    print("=" * 72)
    p_checks = party_self_checks(party, acts)
    for name, p_ok, detail in p_checks:
        mark = "PASS" if p_ok else "FAIL"
        suffix = f"  ({detail})" if (detail and not p_ok) else ""
        print(f"  [{mark}] {name}{suffix}")
        failed += 0 if p_ok else 1
    p_ok, p_msg = validate_party_dir(party_dir)
    print(f"party artifact: {p_msg}; persisted under {party_dir}")
    total = len(checks) + len(p_checks)
    print(f"court files persisted under: {args.out}")
    print(f"self-checks: {total - failed}/{total} passed")
    return 1 if failed or not ok or not p_ok else 0


if __name__ == "__main__":
    sys.exit(main())
