"""The paid-judgement work economy, end to end — one artifact, two layers.

    python3 -m chambers.kernel.demo_work_economy [--out DIR]

The smallest complete instance of the thesis: a requester PAYS for
bounded cognitive work over two private worlds, and the payment is
inseparable from the meter.

  1. Two chambers register exposure accounts and lease budgets to a node.
  2. The requester deposits 500,000 ucr; the house escrows 120,000 toward
     the agent's operator, bound to the requester's two exposure accounts,
     release conditional on a CLEAN court.
  3. A guest agent observes both silos (metered), then emits one typed
     judgement toward the requester — charged ATOMICALLY against both
     members (the emission is not separable from its inputs).
  4. The house releases 100,000 ucr against the emission's charge events —
     the work receipt — and refunds the remaining 20,000 after expiry.
  5. Everything lands in ONE jsonl artifact. The verifier re-derives the
     information fold, the value fold, both verdicts, and conservation,
     with no access to any of the code above.
  6. TAMPER CHECK: flip one payment amount in the artifact and the same
     verifier convicts it (the id changes, the release orphans, S2 fires).

Exit nonzero if any step deviates. No floats anywhere.
"""
from __future__ import annotations

import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from accountant import CapacityEstimate, EstimatorAttestation, exposure_key  # noqa: E402
from leases import LeaseIssuer  # noqa: E402
from ledger import Ledger  # noqa: E402
from session import MediationSession  # noqa: E402
from settlement import SettlementIssuer, conservation_identity, settlement_fold  # noqa: E402
import verify as verify_mod  # noqa: E402

TOR = EstimatorAttestation("indep", "adversarial_review", "static_schema_bound", True)


def build_economy() -> Ledger:
    ledger = Ledger()
    members = ["chamberA", "chamberB"]

    # 1 — accounts and leases (the information authorities)
    lessor = LeaseIssuer(issuer="issuerOfRecord", ledger=ledger)
    leases = {}
    for m in members:
        k = exposure_key(m, "guestAgent")
        lessor.register(k, subject_entropy_mbits=100_000, ceiling_mbits=50_000)
        leases[k] = lessor.grant(k, node="node1", amount_mbits=50_000, expires_tick=100)
    req_keys = []
    for m in members:
        k = exposure_key(m, "requesterR")
        lessor.register(k, subject_entropy_mbits=100_000, ceiling_mbits=8_000)
        leases[k] = lessor.grant(k, node="node1", amount_mbits=8_000, expires_tick=100)
        req_keys.append(k)

    # 2 — the value authority
    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    bank.deposit("requesterR", 500_000, tick=0)
    escrow = bank.escrow(
        payer="requesterR", payee="agentOperator", amount_ucr=120_000,
        charge_keys=req_keys, expires_tick=100, tick=1, required_clean=True,
    )

    # 3 — the metered work
    sess = MediationSession("node1", "guestAgent", "requesterR", members, leases, ledger)
    r1 = sess.observe("chamberA", CapacityEstimate(20_000, 0, 0, 0, 0, "read"), TOR, tick=2)
    r2 = sess.observe("chamberB", CapacityEstimate(20_000, 0, 0, 0, 0, "read"), TOR, tick=3)
    emit = sess.emit(CapacityEstimate(4_000, 500, 0, 0, 0, "judgement"), TOR, tick=4)
    assert r1.decision.accepted and r2.decision.accepted and emit.accepted

    # 4 — payment against the work receipt; refund after expiry
    receipt = [r.event_id for r in emit.results]
    bank.release(escrow, 100_000, receipt, tick=5)
    bank.refund(escrow, 20_000, tick=101)
    return ledger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    default_out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".chamber", "work_economy"
    )
    ap.add_argument("--out", default=default_out)
    args = ap.parse_args(argv)

    ledger = build_economy()
    artifact = ledger.to_jsonl()

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "paid_judgement.jsonl")
    with open(path, "w", encoding="ascii") as fh:
        fh.write(artifact)

    # 5 — the stranger's check, run on the bytes, not on our objects
    buf = io.StringIO()
    code = verify_mod.verify(artifact, out=buf)
    print(buf.getvalue())
    assert code == 0, "honest economy must verify CLEAN"

    accounts, _ = settlement_fold(ledger)
    lhs, rhs = conservation_identity(ledger)
    assert accounts["agentOperator"].available_ucr == 100_000
    assert accounts["requesterR"].available_ucr == 400_000
    assert lhs == rhs == 500_000

    # 6 — tamper: pay the operator 900,000 instead of 100,000
    tampered = artifact.replace('"amount_ucr":100000', '"amount_ucr":900000')
    assert tampered != artifact, "tamper probe failed to change anything"
    buf2 = io.StringIO()
    code2 = verify_mod.verify(tampered, out=buf2)
    tail = [l for l in buf2.getvalue().splitlines() if l.startswith(("CONVICTED", "  S", "  I"))]
    print("tampered artifact verdict:")
    for line in tail:
        print(" ", line)
    assert code2 == 1, "tampered artifact must be convicted"

    print(f"\nartifact: {path} ({ledger.event_count()} events)")
    print("work economy: metered, paid, conserved, verifiable, tamper-evident")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
