"""The pipeline — the composed real-life system, one court, one verdict.

    python3 -m workbench.pipeline.run_pipeline [--out DIR]

The operator's scenario, verbatim, as a running machine: Alice writes an
agent that emits structured data over a BOUNDED set of repos; the
mathematical moats bound what her agent can ever learn; a reviewing
agent — seated only on a clean coherence receipt — filters the sketchy
emissions; an attention agent rings the owners' paid bells; every
payment binds to the exact metered work. Nine machines that each ran
alone run HERE as one system over real files on disk, and the
adversaries attack the SEAMS:

  Act 1 — the honest sweep. The scanner (a practical adapter:
     filesystem -> typed finding cards) sweeps Bob's and Carol's repos.
     Cards are schema-bound (path/line/kind/severity — 17 bits, no
     free-text channel). The reviewer reproduces each finding against
     the actual bytes before it may cross: a planted false positive is
     refused and leaks nothing. Each admitted card is an OBSERVATION
     charge against the repo's lifetime moat (what Alice's agent walks
     away with), rings the owner's bell (attention charged against the
     budget the owner issued; the ring fee pays the OWNER), and the
     owner's finding fee releases against the exact observation
     receipt.

  Act 2 — the smuggler. Alice's agent turns greedy: (a) an off-schema
     card smuggling a raw excerpt (the secret string) is refused by the
     reviewer, and the assertion with teeth: THE SECRET APPEARS NOWHERE
     IN THE COURT ARTIFACT; (b) a bulk-exfil card demanding 200,000
     mbits hits the moat itself — REFUSED_CEILING, a recorded fact —
     and Bob's fold cumulative never exceeds the ceiling he declared.
     Layered defense: the reviewer is policy, the moat is arithmetic.

  Act 3 — the spammer and the crooked judge. Two more rings on Bob's
     bell with nothing new to say: the first is admitted (and paid for
     — spam is bounded AND costly to the spammer), the second refused
     by the budget with the demand pressure recorded. Then the seat
     attack: a sycophant candidate reviewer runs the review-audit
     golden battery, its receipt convicts R3 SYCOPHANT, and the seat
     is refused — while the honest reviewer's clean receipt, cited in
     a KEY-SIGNED reviewer_seat fact (charge-identity/1), seats it.

  The verdict: one jsonl artifact; the stranger's verifier says CLEAN
  across every surface (I/S/X/C/P/A); conservation exact; a tampered
  byte convicts. 30+ inline self-checks; exit nonzero on any deviation.

WHAT THE COMPOSITION TEACHES (residues, named):
  * Reviewer-seat gating is POLICY wired to protocol receipts, not
    protocol itself — a coalition that seats an unreceipted reviewer
    gets exactly what it asked for. The receipt makes the choice
    legible; it cannot make it for you.
  * Reviewer refusals are court evidence only as inert payloads; a
    refusal-conviction surface (reviewer accountability for wrongly
    REFUSED work) is an open design row — today only admissions have
    teeth.
  * CLOSED (identity /2, this file): every authored economic fact —
    registrations, leases, charges, deposits, escrows, releases — is
    now KEY-SIGNED through the real front-ends; a tampered signature
    byte convicts A2. The residual seam moves down a level: settlement
    ACCOUNTS (payer/payee names) stay petname strings in the issuer's
    namespace — key-id accounts without account-holder signatures
    would be attribution theater, so the honest form is named (L5).
  * Cross-unit atomicity (interrupt units vs millibits) remains
    sequenced, not atomic — the over-count direction, chosen, as in
    the attention demo.

No floats in any decision path. Every number below is exact.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "chambers", "kernel"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "chambers", "review_audit"))

from accountant import CapacityEstimate, EstimatorAttestation, exposure_key  # noqa: E402
from attention_node import ATTN_ESTIMATOR, att_key  # noqa: E402
from events import canonical_json, event_id  # noqa: E402
import identity as ID  # noqa: E402
from leases import LeaseIssuer  # noqa: E402
from ledger import Ledger  # noqa: E402
from meter import KernelMeter  # noqa: E402
from settlement import SettlementIssuer, conservation_identity, settlement_fold  # noqa: E402
import verify as verify_mod  # noqa: E402

import battery as coherence  # noqa: E402  (review_audit)
import reviewers as pathological  # noqa: E402

FIXTURES = os.path.join(_HERE, "fixtures")
REPOS = {"bobs_service": "bob", "carols_lib": "carol"}

# The card schema: path(3b) + line(10b) + kind(2b) + severity(2b) = 17 bits.
CARD_FIELDS = {"repo", "path", "line", "kind", "severity"}
CARD_MBITS = 17_000
BULK_MBITS = 200_000          # the smuggler's demand
RING_UNITS = 1_000            # micro-interrupts per notification
RING_FEE_UCR = 10_000         # alice -> owner, per ring
FINDING_FEE_UCR = 50_000      # owner -> alice, per admitted finding
EPOCH = "epoch:sweep-1"


# identity /2: every authoring party holds a key. Seeds are deterministic
# derivations (the pipeline stays a pure function of its inputs); in a
# deployment each party generates and keeps their own.
def _seed(name: str) -> bytes:
    return hashlib.sha256(f"pipeline-party:{name}".encode("ascii")).digest()


SIGNER = {name: ID.Signer(_seed(name))
          for name in ("bob", "carol", "houseEscrow", "mediator")}

CARD_ESTIMATOR = EstimatorAttestation(
    "finding_card.schema_v1.enum_sum", "adversarial_review",
    "static_schema_bound", True)

KIND_SEVERITY = {"hardcoded_secret": 3, "sql_concat": 2, "dead_import": 1}

_RULES = [
    ("hardcoded_secret", re.compile(r"=\s*\"sk-live-")),
    ("sql_concat", re.compile(r"execute\(\".*\"\s*\+")),
    ("dead_import", re.compile(r"^import \w+\s+# noqa: F401")),
]

_checks = 0


def check(claim: bool, what: str) -> None:
    global _checks
    assert claim, f"SELF-CHECK FAILED: {what}"
    _checks += 1


def scan(repo_dir: str, repo: str):
    """Alice's agent: the practical adapter. Deterministic regex sweep ->
    schema-bound structured cards. Order: sorted paths, ascending lines."""
    cards = []
    for fname in sorted(os.listdir(repo_dir)):
        if not fname.endswith(".py"):
            continue
        for lineno, line in enumerate(
                open(os.path.join(repo_dir, fname), encoding="utf-8"), 1):
            for kind, rx in _RULES:
                if rx.search(line):
                    cards.append({"repo": repo, "path": fname, "line": lineno,
                                  "kind": kind, "severity": KIND_SEVERITY[kind]})
    return cards


def review(card: dict) -> str:
    """The reviewing agent: filters the sketchy. Runs INSIDE the owner's
    trust domain (it may read the bytes) so its refusals leak nothing.
    Refusal reasons are total and named."""
    extra = set(card) - CARD_FIELDS
    if extra:
        return f"REFUSED off-schema fields {sorted(extra)}"
    if card.get("kind") not in KIND_SEVERITY:
        return "REFUSED unknown kind"
    if card.get("severity") != KIND_SEVERITY[card["kind"]]:
        return "REFUSED severity does not match kind"
    repo_dir = os.path.join(FIXTURES, next(
        d for d, owner in REPOS.items() if owner == card["repo"]))
    try:
        lines = open(os.path.join(repo_dir, card["path"]),
                     encoding="utf-8").read().splitlines()
        line = lines[card["line"] - 1]
    except Exception:
        return "REFUSED path/line does not exist"
    rx = dict(_RULES)[card["kind"]]
    if not rx.search(line):
        return "REFUSED does not reproduce at path:line"
    return "ADMITTED"


def seat_reviewer(candidate, name: str):
    """A reviewer is seated ONLY on a clean review-audit coherence
    receipt for the golden battery. Returns (receipt, codes)."""
    bat = coherence.generate_battery()
    receipt = coherence.run_battery(candidate, bat, name, EPOCH)
    return receipt, coherence.audit_receipt(receipt)


def build(out_dir: str) -> Ledger:
    ledger = Ledger()
    w = print

    # ---- Act 0: the seats and the moats ------------------------------
    w("== Act 0: seats and moats ==")
    sy_receipt, sy_codes = seat_reviewer(pathological.make("sycophant"),
                                         "candidate_sycophant")
    check(any(c.startswith("R3") for c in sy_codes),
          "sycophant candidate convicts R3")
    w(f"  candidate 'sycophant': receipt convicts {[c.split()[0] for c in sy_codes]}"
      f" -> SEAT REFUSED")

    honest_receipt, honest_codes = seat_reviewer(pathological.make("oracle"),
                                                 "pipeline_reviewer")
    check(honest_codes == [], "honest reviewer receipt is clean")
    reviewer_seed = bytes.fromhex(
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    _, reviewer_pub = ID.keypair(reviewer_seed)
    seat = ID.sign_event({
        "kind": "reviewer_seat", "reviewer": ID.key_author(reviewer_pub),
        "coherence_receipt_id": coherence.receipt_id(honest_receipt),
        "battery_id": honest_receipt["battery_id"], "epoch": EPOCH,
    }, reviewer_seed)
    ledger._add_payload(event_id(seat), seat)
    check(ID.identity_codes(ledger) == [], "signed seat verifies (A-codes clean)")
    w(f"  reviewer seated: clean receipt {coherence.receipt_id(honest_receipt)[:23]}…, "
      f"seat KEY-SIGNED under charge-identity/1")

    # The moats: what Alice's agent may EVER learn of each repo. The
    # issuers are KEYS (identity /2): every registration and lease below
    # is signed, so a forged moat is attributable, not merely detectable.
    bob = LeaseIssuer(issuer=SIGNER["bob"].author, ledger=ledger,
                      signer=SIGNER["bob"])
    carol = LeaseIssuer(issuer=SIGNER["carol"].author, ledger=ledger,
                        signer=SIGNER["carol"])
    x_bob = exposure_key("bobs_service", "alice_agent")
    x_carol = exposure_key("carols_lib", "alice_agent")
    bob.register(x_bob, subject_entropy_mbits=400_000, ceiling_mbits=60_000)
    carol.register(x_carol, subject_entropy_mbits=300_000, ceiling_mbits=40_000)
    a_bob = att_key("bob", "alice_agent", EPOCH)
    a_carol = att_key("carol", "alice_agent", EPOCH)
    # bob's repo carries 3 real findings; he budgets one extra ring
    bob.register(a_bob, subject_entropy_mbits=4 * RING_UNITS,
                 ceiling_mbits=4 * RING_UNITS)
    carol.register(a_carol, subject_entropy_mbits=2 * RING_UNITS,
                   ceiling_mbits=2 * RING_UNITS)

    # The mediator node is a key too: every charge it records — admissions
    # AND refusals — is signed by it (the /2 residue, closed).
    mediator = SIGNER["mediator"].author
    meter = KernelMeter(node=mediator, issuer="unused", ledger=ledger,
                        node_signer=SIGNER["mediator"])
    meter.adopt(x_bob, bob.grant(x_bob, mediator, 60_000, 100_000),
                subject_entropy_mbits=400_000)
    meter.adopt(x_carol, carol.grant(x_carol, mediator, 40_000, 100_000),
                subject_entropy_mbits=300_000)
    meter.adopt(a_bob, bob.grant(a_bob, mediator, 4 * RING_UNITS, 100_000),
                subject_entropy_mbits=4 * RING_UNITS)
    meter.adopt(a_carol, carol.grant(a_carol, mediator, 2 * RING_UNITS, 100_000),
                subject_entropy_mbits=2 * RING_UNITS)
    w(f"  moats declared: bobs_service {60_000} mbits lifetime, "
      f"carols_lib {40_000}; bells: bob 4 rings, carol 2 (epoch budgets)")

    bank = SettlementIssuer(issuer=SIGNER["houseEscrow"].author, ledger=ledger,
                            signer=SIGNER["houseEscrow"])
    bank.deposit("bob", 500_000, tick=0)
    bank.deposit("carol", 300_000, tick=0)
    bank.deposit("alice", 100_000, tick=0)

    tick = 10
    x_key = {"bob": x_bob, "carol": x_carol}
    a_key = {"bob": a_bob, "carol": a_carol}

    # ---- Act 1: the honest sweep -------------------------------------
    w("\n== Act 1: the honest sweep ==")
    cards = []
    for repo_dir, owner in sorted(REPOS.items()):
        cards.extend(scan(os.path.join(FIXTURES, repo_dir), owner))
    check(len(cards) == 4, f"scanner found 4 real findings, got {len(cards)}")
    # the planted false positive: claims a dead import in a clean file
    cards.append({"repo": "bob", "path": "queue.py", "line": 3,
                  "kind": "dead_import", "severity": 1})

    admitted, refused = [], []
    for card in cards:
        verdict = review(card)
        (admitted if verdict == "ADMITTED" else refused).append((card, verdict))
    check(len(admitted) == 4 and len(refused) == 1,
          "reviewer admits 4, refuses the planted false positive")
    check("does not reproduce" in refused[0][1], "FP refused for the named reason")
    w(f"  scanner emitted {len(cards)} cards; reviewer admitted {len(admitted)}, "
      f"refused 1 ({refused[0][1]})")

    for card, _ in admitted:
        owner = card["repo"]
        # the observation: what Alice's agent walks away with, on the moat
        obs, obs_id = meter.charge_recorded(
            x_key[owner], CapacityEstimate(CARD_MBITS, 0, 0, 0, 0, "finding_card"),
            CARD_ESTIMATOR, tick=tick)
        check(obs.accepted, "honest card fits the moat")
        # the ring: owner's bell, paid by alice TO the owner (G6)
        ring, ring_id = meter.charge_recorded(
            a_key[owner], CapacityEstimate(RING_UNITS, 0, 0, 0, 0, "notify"),
            ATTN_ESTIMATOR, tick=tick + 1)
        check(ring.accepted, "budgeted ring admitted")
        esc_ring = bank.escrow("alice", owner, RING_FEE_UCR, [a_key[owner]],
                               expires_tick=100_000, tick=tick + 2)
        bank.release(esc_ring, RING_FEE_UCR, [ring_id], tick=tick + 3)
        # the finding fee: owner pays alice against the EXACT work receipt
        esc_fee = bank.escrow(owner, "alice", FINDING_FEE_UCR, [x_key[owner]],
                              expires_tick=100_000, tick=tick + 4)
        bank.release(esc_fee, FINDING_FEE_UCR, [obs_id], tick=tick + 5)
        tick += 6
    w(f"  4 findings crossed: each = observation on the moat + paid ring + "
      f"fee released against the exact receipt")

    # ---- Act 2: the smuggler -----------------------------------------
    w("\n== Act 2: the smuggler ==")
    secret = 'sk-live-9f8e7d6c5b4a3f2e1d0c'
    smuggle = {"repo": "bob", "path": "handlers.py", "line": 6,
               "kind": "hardcoded_secret", "severity": 3,
               "excerpt": f'API_TOKEN = "{secret}"'}
    verdict = review(smuggle)
    check(verdict.startswith("REFUSED off-schema"),
          "excerpt smuggling refused by schema review")
    w(f"  off-schema excerpt card: {verdict}")

    bulk = meter.charge(x_bob, CapacityEstimate(BULK_MBITS, 0, 0, 0, 0, "bulk"),
                        CARD_ESTIMATOR, tick=tick)
    check(not bulk.accepted, "bulk exfil refused by the moat itself")
    w(f"  bulk-exfil demand of {BULK_MBITS} mbits: {bulk.reason_class} "
      f"(the moat is arithmetic, not policy)")
    tick += 1

    # ---- Act 3: the spammer ------------------------------------------
    w("\n== Act 3: the spammer ==")
    spam1, spam1_id = meter.charge_recorded(
        a_bob, CapacityEstimate(RING_UNITS, 0, 0, 0, 0, "notify"),
        ATTN_ESTIMATOR, tick=tick)
    check(spam1.accepted, "fourth ring fits bob's declared budget")
    esc = bank.escrow("alice", "bob", RING_FEE_UCR, [a_bob],
                      expires_tick=100_000, tick=tick + 1)
    bank.release(esc, RING_FEE_UCR, [spam1_id], tick=tick + 2)
    spam2 = meter.charge(a_bob, CapacityEstimate(RING_UNITS, 0, 0, 0, 0, "notify"),
                         ATTN_ESTIMATOR, tick=tick + 3)
    check(not spam2.accepted, "fifth ring refused: the budget is the ceiling")
    w(f"  spam ring 1: admitted and PAID (spam is costly to the spammer); "
      f"spam ring 2: {spam2.reason_class}, demand recorded")
    tick += 4

    # ---- the verdict --------------------------------------------------
    w("\n== the verdict ==")
    folded = ledger.fold()
    check(folded[x_bob].cumulative_mbits == 3 * CARD_MBITS <= 60_000,
          "bob's moat: cumulative exactly three cards, under ceiling")
    check(folded[x_bob].demanded_mbits == 3 * CARD_MBITS + BULK_MBITS,
          "bob's moat: the bulk demand is recorded pressure")
    check(folded[x_carol].cumulative_mbits == CARD_MBITS,
          "carol's moat: one card")
    check(folded[a_bob].cumulative_mbits == 4 * RING_UNITS
          and folded[a_bob].demanded_mbits == 5 * RING_UNITS,
          "bob's bell: 4 rung, 5 demanded")

    accounts, _ = settlement_fold(ledger)
    check(accounts["alice"].available_ucr ==
          100_000 - 5 * RING_FEE_UCR + 4 * FINDING_FEE_UCR,
          "alice: paid 5 rings, earned 4 finding fees")
    check(accounts["bob"].available_ucr ==
          500_000 - 3 * FINDING_FEE_UCR + 4 * RING_FEE_UCR,
          "bob: paid 3 findings, earned 4 rings")
    lhs, rhs = conservation_identity(ledger)
    check(lhs == rhs == 900_000, "conservation exact")

    # identity /2: the court's authored facts are attributable, all of them
    authored = [p for p in ledger.events() if p.get("kind") in ID.AUTHOR_FIELD]
    check(len(authored) >= 40 and all(
        (ID.author_of(p) or "").startswith(ID.KEY_PREFIX)
        and isinstance(p.get("sig"), str) and len(p["sig"]) == 128
        for p in authored),
        "every authored economic fact is key-signed (identity /2)")
    check(ID.identity_codes(ledger) == [], "all signatures verify: A-surface clean")

    artifact = ledger.to_jsonl()
    check(secret not in artifact,
          "THE SECRET APPEARS NOWHERE IN THE COURT ARTIFACT")
    buf = io.StringIO()
    check(verify_mod.verify(artifact, out=buf) == 0,
          "stranger's verifier: CLEAN across I/S/X/C/P/A")
    tampered = artifact.replace('"debit_mbits":17000,', '"debit_mbits":1,', 1)
    buf2 = io.StringIO()
    check(verify_mod.verify(tampered, out=buf2) == 1, "tampered byte convicts")
    # tamper with a SIGNATURE byte: the edited fact fails its author's key
    sig_at = artifact.index('"sig":"') + len('"sig":"')
    flip = "0" if artifact[sig_at] != "0" else "1"
    sig_tampered = artifact[:sig_at] + flip + artifact[sig_at + 1:]
    buf3 = io.StringIO()
    check(verify_mod.verify(sig_tampered, out=buf3) == 1
          and "A" in buf3.getvalue().rsplit("== verdict ==", 1)[1],
          "tampered signature byte convicts on the A-surface")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "pipeline.jsonl")
    with open(path, "w", encoding="ascii") as fh:
        fh.write(artifact)
    w(f"  moats held (bob {folded[x_bob].cumulative_mbits}/60000 mbits, "
      f"demand {folded[x_bob].demanded_mbits} recorded); conservation "
      f"{lhs}=={rhs}; secret absent from artifact; verifier CLEAN; "
      f"tamper CONVICTS (content OR signature byte)")
    w(f"  identity /2: {len(authored)} authored facts, every one key-signed "
      f"(issuers, mediator, escrow authority all keys)")
    w(f"\n  artifact: {path} ({ledger.event_count()} events)")
    w(f"  self-checks passed: {_checks}")
    return ledger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(_HERE, "..", ".chamber", "pipeline"))
    args = ap.parse_args(argv)
    build(args.out)
    print("\nthe pipeline: nine machines, one system, one clean court.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
