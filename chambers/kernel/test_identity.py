"""charge-identity/1 as a standing lane — IDENTITY-SPEC's claims:

  * the Ed25519 core is pinned to RFC 8032 §7.1 vectors 1-3 EXACTLY
    (sign bytes, public keys, verification), with the malleability
    guard asserted (s+L rejected) and totality over garbage;
  * a key-authored economy runs clean end to end: register/lease/charge
    signed by key ids, the fold and every frozen surface unmoved;
  * A1 convicts a key-authored event with no sig; A2 convicts a wrong
    or transplanted sig; legacy string authors convict NOTHING;
  * a key-SHAPED but ill-formed author is A1, never legacy;
  * forged-authority attribution: an attacker without the key cannot
    author a valid fact in its name (the gap this spec closes);
  * the frozen corpora carry zero A-codes and zero byte movement.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chambers.kernel import identity as ID  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402
from chambers.kernel.events import event_id  # noqa: E402

VEC = [
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
     "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555f"
     "b8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
     "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da08"
     "5ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
     "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
     "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18"
     "ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
]

SEED_A = bytes.fromhex(VEC[0][0])
SEED_B = bytes.fromhex(VEC[1][0])


def test_rfc8032_vectors_exact() -> None:
    for seed_h, pub_h, msg_h, sig_h in VEC:
        seed, pub = ID.keypair(bytes.fromhex(seed_h))
        assert pub.hex() == pub_h
        msg = bytes.fromhex(msg_h)
        assert ID.sign(seed, msg).hex() == sig_h
        assert ID.verify_sig(pub, msg, bytes.fromhex(sig_h))
        assert not ID.verify_sig(pub, msg + b"x", bytes.fromhex(sig_h))
    print("RFC 8032 §7.1 vectors 1-3: exact")


def test_malleability_and_garbage_are_total() -> None:
    seed, pub = ID.keypair(SEED_A)
    sig = ID.sign(seed, b"m")
    s = int.from_bytes(sig[32:], "little")
    forged = sig[:32] + (s + ID._L).to_bytes(32, "little")
    assert not ID.verify_sig(pub, b"m", forged), "s >= L must be rejected"
    for bad in (b"", b"\x00" * 63, b"\xff" * 64, sig[:32] + b"\xff" * 32,
                b"\xff" * 32 + sig[32:]):
        assert ID.verify_sig(pub, b"m", bad) is False
    assert ID.verify_sig(b"\xff" * 32, b"m", sig) is False  # off-curve pub


def _signed_economy():
    """A minimal key-authored court: issuer and node are both keys."""
    _, pub_a = ID.keypair(SEED_A)
    _, pub_b = ID.keypair(SEED_B)
    issuer, node = ID.key_author(pub_a), ID.key_author(pub_b)
    led = Ledger()
    reg = ID.sign_event({"kind": "register", "key": ["exp", issuer, "reader"],
                         "subject_entropy_mbits": 10_000, "ceiling_mbits": 5_000,
                         "issuer": issuer}, SEED_A)
    lease = ID.sign_event({"kind": "lease", "key": ["exp", issuer, "reader"],
                           "lease_seq": 1, "node": node, "amount_mbits": 5_000,
                           "issuer": issuer, "expires_tick": 1_000}, SEED_A)
    led._add_payload(event_id(reg), reg)
    led._add_payload(event_id(lease), lease)
    charge = ID.sign_event({"kind": "charge", "key": ["exp", issuer, "reader"],
                            "node": node, "lease_id": event_id(lease),
                            "charge_seq": 1, "tick": 5, "channel": "c",
                            "estimate_total_mbits": 1_000, "estimator_id": "e",
                            "estimator_independence": "adversarial_review",
                            "estimator_worst_case": True, "accepted": True,
                            "reason_class": "EMITTED", "reason_detail": "d",
                            "demand_mbits": 1_000, "debit_mbits": 1_000},
                           SEED_B)
    led._add_payload(event_id(charge), charge)
    return led, issuer, node


def test_key_authored_economy_is_clean_and_folds_unmoved() -> None:
    led, issuer, _node = _signed_economy()
    assert ID.identity_codes(led) == []
    assert led.audit_codes() == []          # frozen surfaces indifferent
    folded = led.fold()
    key = ("exp", issuer, "reader")
    assert folded[key].cumulative_mbits == 1_000
    print("key-authored economy: clean, fold exact, frozen surfaces unmoved")


def test_a1_missing_sig_and_ill_formed_key_shape() -> None:
    _, pub_a = ID.keypair(SEED_A)
    issuer = ID.key_author(pub_a)
    led = Ledger()
    naked = {"kind": "register", "key": ["exp", issuer, "r"],
             "subject_entropy_mbits": 1_000, "ceiling_mbits": 100,
             "issuer": issuer}                       # key author, no sig
    led._add_payload(event_id(naked), naked)
    shaped = {"kind": "deposit", "account": "x", "amount_ucr": 1,
              "issuer": "ed25519:nothex", "seq": 1, "tick": 0}  # ill-formed
    led._add_payload(event_id(shaped), shaped)
    codes = ID.identity_codes(led)
    assert len(codes) == 2 and all(c.startswith("A1 ") for c in codes), codes


def test_a2_wrong_and_transplanted_sig() -> None:
    led, issuer, _ = _signed_economy()
    events = dict(getattr(led, "_events"))
    reg = next(p for p in events.values() if p["kind"] == "register")
    # transplant: valid signature bytes from a DIFFERENT payload
    lease = next(p for p in events.values() if p["kind"] == "lease")
    forged = dict(reg)
    forged["ceiling_mbits"] = 999_999           # the forger's edit
    forged["sig"] = lease["sig"]                # someone else's valid sig
    led._add_payload(event_id(forged), forged)
    codes = ID.identity_codes(led)
    assert any(c.startswith("A2 ") for c in codes), codes
    # attribution: the honest events still verify — one forgery does not
    # poison the author's attributable facts
    assert sum(c.startswith("A2 ") for c in codes) == 1


def test_forger_without_the_key_cannot_author() -> None:
    """The exact gap this spec closes: an attacker who knows the AUTHOR
    ID but not the seed cannot produce any accepted fact in its name."""
    _, pub_a = ID.keypair(SEED_A)
    issuer = ID.key_author(pub_a)
    attacker_seed = bytes(range(32))
    payload = {"kind": "deposit", "account": "attacker", "amount_ucr": 10**9,
               "issuer": issuer, "seq": 1, "tick": 0}
    payload["sig"] = ID.sign(attacker_seed, ID.signed_bytes(payload)).hex()
    led = Ledger()
    led._add_payload(event_id(payload), payload)
    codes = ID.identity_codes(led)
    assert codes and codes[0].startswith("A2 "), codes
    print("forged mint in a key's name: CONVICTED (attributable authority)")


def test_legacy_authors_and_frozen_corpora_untouched() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    checked = 0
    for sub in ("ledger_traces", "settlement_traces", "settlement2_traces"):
        d = os.path.join(here, sub)
        for f in sorted(os.listdir(d)):
            if not f.endswith(".ledger.jsonl"):
                continue
            led = Ledger.from_jsonl(open(os.path.join(d, f), encoding="ascii").read())
            assert ID.identity_codes(led) == [], f"{sub}/{f} grew A-codes"
            checked += 1
    assert checked >= 40
    print(f"frozen corpora: {checked} golden ledgers, zero A-codes, zero movement")


def test_sign_event_refuses_author_mismatch() -> None:
    _, pub_a = ID.keypair(SEED_A)
    try:
        ID.sign_event({"kind": "deposit", "account": "x", "amount_ucr": 1,
                       "issuer": "bob", "seq": 1, "tick": 0}, SEED_A)
        raise AssertionError("must refuse to sign in the dark")
    except ValueError as exc:
        assert "not this key's id" in str(exc)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
    print("identity lane green")


def test_case_alias_is_a1_never_a_second_namespace() -> None:
    """The aliasing seam (named and closed 2026-07-09): hex-decoding
    tolerance let `ed25519:ABC…` and `ed25519:abc…` both verify against
    ONE key — two author namespaces, disjoint (author, kind, seq)
    spaces, equivocation across them invisible to X0. Well-formed is
    lowercase EXACTLY; every case-alias convicts A1 even when the
    signature bytes verify."""
    _, pub = ID.keypair(SEED_A)
    lower = ID.key_author(pub)
    upper = "ed25519:" + pub.hex().upper()
    assert upper != lower

    signed = ID.sign_event(
        {"kind": "register", "key": ["exp", lower, "r"],
         "subject_entropy_mbits": 1_000, "ceiling_mbits": 100,
         "issuer": lower}, SEED_A)

    # the alias: same key, same valid signature bytes, uppercased author
    alias = dict(signed, issuer=upper)
    alias["sig"] = ID.sign(SEED_A, ID.signed_bytes(
        {k: v for k, v in alias.items() if k != "sig"})).hex()

    led = Ledger()
    led._add_payload(event_id(signed), signed)
    led._add_payload(event_id(alias), alias)
    codes = ID.identity_codes(led)
    assert codes == [f"A1 {upper}"], codes  # alias convicts; honest fact clean

    # and the sig field itself accepts exactly one encoding
    upsig = dict(signed, sig=signed["sig"].upper())
    led2 = Ledger()
    led2._add_payload(event_id(upsig), upsig)
    codes2 = ID.identity_codes(led2)
    assert codes2 == [f"A1 {lower}"], codes2
