"""The 50-cent notification — attention as the kernel's second key family.

    python3 -m chambers.kernel.demo_attention_notify [--out DIR]

The party story's Act 3 (stories/party-matchmaker.md), executable. The
design consult (2026-07-05, private)'s claim, tested by building it: the kernel's account
was never "an information account" — it is a bounded write into a
protected party's world, where the protected party is the lease issuer.
Attention is the second instantiation: protected party = the RECEIVER,
write = occupancy of their focus, and the temporal physics lives in the
KEY — exposure keys are lifetime (information is never unlearned),
attention keys carry an EPOCH (attention regenerates; fresh account per
epoch, monotone within it). Zero kernel changes; this file is the proof.

The flow, per notification:
  1. ATTENTION charge first — ("att", receiver, sender, epoch), unit =
     micro-interrupts, declared in the estimator attestation exactly
     where log2 lives for bits. Bob's epoch budget is the spam ceiling
     HE issued.
  2. EXPOSURE charge second — the card's content leaks Charlie to Bob,
     charged against (charlie_chamber -> bob) lifetime.
  3. Settlement: the 50 cents releases against the ATTENTION charge
     event id, payee = BOB — recipient-as-fee-beneficiary (gap register
     G6). Ringing the bell pays the bell's owner, provably for that ring.

Ordering is the safety argument: attention-refusal happens BEFORE any
exposure charge, so a notification Bob's budget refuses leaks NOTHING
about Charlie — the spam ceiling protects the third party's privacy, not
just the receiver's focus. Exposure-refusal after attention accepted
over-counts one interrupt: the safe direction.

HONEST LIMITS, named:
  * Cross-unit atomicity does not exist: charge_coupled couples ONE
    estimate across same-unit accounts; micro-interrupts and millibits
    are different units, so steps 1-2 are sequenced, not atomic. The
    over-count direction is chosen deliberately. A two-unit coupled
    charge is real future kernel work, not something this demo fakes.
  * The attention unit is declared, not observed — nothing certifies a
    human actually attended. The receiver is the issuer, so the lie
    hurts only its teller.
  * leakage_class labels are void on attention keys (they denominate
    entropy, which attention does not have). The ceilings, refusals,
    demand accrual, and conservation are the real semantics here — one
    more argument for moving class labels out of the timeless fold.

Exit nonzero if any step deviates. No floats anywhere.
"""
from __future__ import annotations

import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel.accountant import CapacityEstimate, exposure_key  # noqa: E402
from chambers.kernel.attention_node import ATTN_ESTIMATOR, CARD_ESTIMATOR, att_key  # noqa: E402
from chambers.kernel.leases import LeaseIssuer  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.meter import KernelMeter  # noqa: E402
from chambers.kernel.settlement import SettlementIssuer, conservation_identity, settlement_fold  # noqa: E402
from chambers.kernel import verify as verify_mod  # noqa: E402

# The card's information content: topic facet (6 bits) + strength bucket
# (2) + why-safe line (5) = 13 bits = 13,000 mbits (party-matchmaker.md).
CARD_MBITS = 13_000
# One notification = 1000 micro-interrupts (the unit's meaning lives in
# the attestation id, exactly where log2 lives for bits). The estimator
# attestations and att_key now live canonically in attention_node.py —
# the served surface — and are imported above; the epoch-in-the-key
# regeneration story is unchanged.
INTERRUPT_UNITS = 1_000


def build(epoch: str = "epoch:2026-07-05") -> Ledger:
    ledger = Ledger()

    # -- authorities ------------------------------------------------------
    # Bob issues his own attention: 5 notifications' worth this epoch.
    bob = LeaseIssuer(issuer="bob", ledger=ledger)
    a_key = att_key("bob", "alice_mediator", epoch)
    # entropy is meaningless for attention; register the minimum honest
    # value (= ceiling) and rely on ceilings/refusals, not class labels.
    bob.register(a_key, subject_entropy_mbits=5 * INTERRUPT_UNITS,
                 ceiling_mbits=5 * INTERRUPT_UNITS)

    # Charlie's chamber issues Charlie's exposure to Bob (lifetime).
    charlie = LeaseIssuer(issuer="charlie_chamber", ledger=ledger)
    x_key = exposure_key("charlie_chamber", "bob")
    charlie.register(x_key, subject_entropy_mbits=400_000, ceiling_mbits=100_000)

    # One mediator node holds leases from BOTH authorities. The meter's
    # own issuer is unused here — both leases arrive from real external
    # issuers (Bob for attention, Charlie's chamber for exposure), which
    # is the deployment shape, not the sim shortcut (KernelMeter.adopt;
    # served live by attention_node.py).
    meter = KernelMeter(node="mediator_node", issuer="unused_self_issuer", ledger=ledger)

    meter.adopt(a_key,
                bob.grant(a_key, node="mediator_node",
                          amount_mbits=5 * INTERRUPT_UNITS, expires_tick=1000),
                subject_entropy_mbits=5 * INTERRUPT_UNITS)
    meter.adopt(x_key,
                charlie.grant(x_key, node="mediator_node",
                              amount_mbits=100_000, expires_tick=1000),
                subject_entropy_mbits=400_000)

    # -- value ------------------------------------------------------------
    bank = SettlementIssuer(issuer="houseEscrow", ledger=ledger)
    bank.deposit("alice", 5_000_000, tick=0)  # $5.00 at 1M ucr = $1

    # -- notifications until Bob's epoch budget says no --------------------
    tick, sent, refused_at = 1, 0, None
    for i in range(8):  # try more than the budget admits
        # 1) attention first: may Bob's bell ring?
        attn, attn_charge_id = meter.charge_recorded(
            a_key, CapacityEstimate(INTERRUPT_UNITS, 0, 0, 0, 0, "notify"),
            ATTN_ESTIMATOR, tick=tick)
        if not attn.accepted:
            refused_at = i
            break
        # 2) exposure second: the card's content leaks Charlie to Bob.
        card = meter.charge(x_key,
                            CapacityEstimate(CARD_MBITS, 0, 0, 0, 0, "match_card"),
                            CARD_ESTIMATOR, tick=tick + 1)
        assert card.accepted, "exposure ceiling sized to admit every rung the epoch admits"
        # 3) the 50 cents, bound to THIS ring, paid to the bell's owner.
        escrow = bank.escrow(payer="alice", payee="bob", amount_ucr=500_000,
                             charge_keys=[a_key], expires_tick=1000, tick=tick + 2)
        bank.release(escrow, 500_000, [attn_charge_id], tick=tick + 3)
        sent += 1
        tick += 4

    assert sent == 5, f"epoch budget promised 5 notifications, delivered {sent}"
    assert refused_at == 5, "sixth ring must be refused"

    # The refused attempt leaked NOTHING about Charlie: exposure cumulative
    # is exactly 5 cards.
    folded = ledger.fold()
    assert folded[tuple(x_key)].cumulative_mbits == 5 * CARD_MBITS
    # ...but the extraction pressure was recorded: attention demand > ceiling.
    assert folded[tuple(a_key)].demanded_mbits == 6 * INTERRUPT_UNITS
    assert folded[tuple(a_key)].cumulative_mbits == 5 * INTERRUPT_UNITS

    # -- regeneration: a fresh epoch is a fresh account --------------------
    a2 = att_key("bob", "alice_mediator", "epoch:2026-07-06")
    bob.register(a2, subject_entropy_mbits=5 * INTERRUPT_UNITS,
                 ceiling_mbits=5 * INTERRUPT_UNITS)
    meter.adopt(a2,
                bob.grant(a2, node="mediator_node",
                          amount_mbits=5 * INTERRUPT_UNITS, expires_tick=2000),
                subject_entropy_mbits=5 * INTERRUPT_UNITS)
    fresh = meter.charge(a2, CapacityEstimate(INTERRUPT_UNITS, 0, 0, 0, 0, "notify"),
                         ATTN_ESTIMATOR, tick=tick)
    assert fresh.accepted, "a new epoch regenerates the budget — no decay machinery needed"

    return ledger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    default_out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".chamber", "attention_notify"
    )
    ap.add_argument("--out", default=default_out)
    args = ap.parse_args(argv)

    ledger = build()
    artifact = ledger.to_jsonl()

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "attention_notify.jsonl")
    with open(path, "w", encoding="ascii") as fh:
        fh.write(artifact)

    # The stranger's check, on the bytes.
    buf = io.StringIO()
    code = verify_mod.verify(artifact, out=buf)
    print(buf.getvalue())
    assert code == 0, "honest notification economy must verify CLEAN"

    accounts, _ = settlement_fold(ledger)
    lhs, rhs = conservation_identity(ledger)
    assert accounts["bob"].available_ucr == 5 * 500_000, "the bell's owner was paid per ring"
    assert accounts["alice"].available_ucr == 5_000_000 - 5 * 500_000
    assert lhs == rhs == 5_000_000

    # Tamper: inflate one attention charge's debit; the artifact convicts.
    tampered = artifact.replace('"debit_mbits":1000,', '"debit_mbits":999999,', 1)
    assert tampered != artifact, "tamper probe failed to change anything"
    buf2 = io.StringIO()
    code2 = verify_mod.verify(tampered, out=buf2)
    tail = [l for l in buf2.getvalue().splitlines() if l.startswith(("CONVICTED", "  S", "  I"))]
    print("tampered artifact verdict:")
    for line in tail:
        print(" ", line)
    assert code2 == 1, "tampered artifact must be convicted"

    print(f"\nartifact: {path} ({ledger.event_count()} events)")
    print("attention economy: 5 rings paid to the bell's owner, the 6th refused")
    print("before anything about Charlie leaked; fresh epoch regenerates; conserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
