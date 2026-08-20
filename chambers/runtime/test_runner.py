"""runtime-r2/1 as a standing lane — RUNNER-SPEC's claims, executed:

  * the golden bundles are byte-stable (bundle + receipt + output ids
    pinned forever) and REPRODUCE under the stranger's verify;
  * a flipped input bit refuses BEFORE execution and diverges under
    verify; drifted bundles (extra/missing inputs) refuse;
  * nondeterminism fails issuance with certainty: a pid-keyed entry and
    a clock-keyed entry both get NO receipt (deterministic or nothing);
  * legitimate determinism survives -I hash randomization (sorted(set)
    is fine — the discipline catches order-DEPENDENCE, not set use);
  * a receipt at a different claim class is malformed — evidence at its
    class and nothing above it;
  * a run receipt merges into the CRDT court as an inert, content-
    addressed payload: the frozen folds ignore it, audit stays clean,
    merge stays idempotent (RUNNER-SPEC §7).
"""
from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from chambers.runtime import runner as R  # noqa: E402
from chambers.kernel.events import canonical_json, event_id  # noqa: E402
from chambers.kernel.ledger import Ledger  # noqa: E402

BUNDLES = os.path.join(HERE, "bundles")

GOLDEN = {
    "match_card": {
        "bundle": "sha256:23fa6051bc0ba33e2c1e66d1e4a02ce16fc8e8693b94c6dc16badb8d029f8c69",
        "receipt": "sha256:a1d963b486804513a316b0260b8c515952b7c759e1878482628cf603c8bc0d09",
        "output": "sha256:d2dddd81312958aaa5c596a05d73dea2ed3b8442d2c0aca1623659891d3530cc",
    },
    "rank_items": {
        "bundle": "sha256:4cb9ea19b9b0df3f759695a40588ee727a4eacb8a4dc2f5d576e569692413034",
        "receipt": "sha256:736f70c5183a87cb8ea648015094642678304e6e23a3a6caed669a64268ce2fc",
        "output": "sha256:34fcba8fb81c397c1ef04fc76548a514365d1a661da3e6fa39d7628d1b6a85c7",
    },
}


def _copy_bundle(name: str, dst: str) -> str:
    out = os.path.join(dst, name)
    shutil.copytree(os.path.join(BUNDLES, name), out)
    return out


def _scratch_bundle(dst: str, entry_src: str, timeout_s: int = 20) -> str:
    d = os.path.join(dst, "scratch")
    os.makedirs(os.path.join(d, "inputs"))
    with open(os.path.join(d, "entry.py"), "w", encoding="ascii") as fh:
        fh.write(entry_src)
    with open(os.path.join(d, "inputs", "x.json"), "w", encoding="ascii") as fh:
        fh.write("{}")
    m = R.make_manifest(d, timeout_s=timeout_s)
    with open(os.path.join(d, "manifest.json"), "w", encoding="ascii") as fh:
        json.dump(m, fh, sort_keys=True, separators=(",", ":"))
    return d


def test_golden_bundles_issue_and_reproduce_byte_stable() -> None:
    for name, want in GOLDEN.items():
        d = os.path.join(BUNDLES, name)
        _manifest, bid = R.check_bundle(d)
        assert bid == want["bundle"], f"{name}: bundle id drifted"
        receipt = R.run(d)
        assert R.receipt_id(receipt) == want["receipt"], f"{name}: receipt drifted"
        assert receipt["output_sha256"] == want["output"]
        assert receipt["claim_class"] == "reproducible_local"
        buf = io.StringIO()
        assert R.verify(d, receipt, out=buf) == 0
        assert buf.getvalue().startswith("REPRODUCED")
    print(f"golden bundles: {len(GOLDEN)} issue + reproduce, ids pinned")


def test_flipped_input_bit_refuses_before_execution_and_diverges() -> None:
    with tempfile.TemporaryDirectory(prefix="r2_tamper_") as tmp:
        d = _copy_bundle("match_card", tmp)
        honest_receipt = R.run(d)
        p = os.path.join(d, "inputs", "profile.json")
        text = open(p, encoding="utf-8").read()
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text.replace("bouldering", "bouldering!"))
        try:
            R.run(d)
            raise AssertionError("tampered bundle must refuse")
        except R.RunRefused as exc:
            assert "hash mismatch" in str(exc)
        buf = io.StringIO()
        assert R.verify(d, honest_receipt, out=buf) == 1
        assert buf.getvalue().startswith("DIVERGED")


def test_input_drift_refuses() -> None:
    with tempfile.TemporaryDirectory(prefix="r2_drift_") as tmp:
        d = _copy_bundle("rank_items", tmp)
        with open(os.path.join(d, "inputs", "smuggled.txt"), "w") as fh:
            fh.write("hello")
        try:
            R.check_bundle(d)
            raise AssertionError("extra input must refuse")
        except R.RunRefused as exc:
            assert "extra" in str(exc)


def test_nondeterminism_gets_no_receipt() -> None:
    """The issuance law with CERTAIN witnesses: pid differs between the
    two fresh processes; the monotonic clock strictly advances."""
    entries = {
        "pid-keyed": "import os\nopen('output','w').write(str(os.getpid()))\n",
        "clock-keyed": "import time\nopen('output','w').write(str(time.monotonic_ns()))\n",
    }
    for label, src in entries.items():
        with tempfile.TemporaryDirectory(prefix="r2_nondet_") as tmp:
            d = _scratch_bundle(tmp, src)
            try:
                R.run(d)
                raise AssertionError(f"{label}: nondeterministic entry must refuse")
            except R.RunRefused as exc:
                assert "nondeterministic" in str(exc), (label, str(exc))
    print("nondeterminism refused: pid-keyed + clock-keyed, no receipt")


def test_legitimate_set_use_survives_hash_randomization() -> None:
    src = ("names = {'gamma','alpha','beta','delta'}\n"
           "open('output','w').write(','.join(sorted(names)))\n")
    with tempfile.TemporaryDirectory(prefix="r2_set_") as tmp:
        d = _scratch_bundle(tmp, src)
        receipt = R.run(d)  # two processes, two hash seeds, same bytes
        assert receipt["output_sha256"] == R.run(d)["output_sha256"]


def test_wrong_claim_class_is_malformed() -> None:
    d = os.path.join(BUNDLES, "rank_items")
    receipt = dict(R.run(d))
    receipt["claim_class"] = "tee_quote"  # a promotion the verifier must refuse
    buf = io.StringIO()
    assert R.verify(d, receipt, out=buf) == 2
    assert "nothing above it" in buf.getvalue()


def test_entry_failure_and_missing_output_refuse() -> None:
    cases = {
        "exits nonzero": "raise SystemExit(3)\n",
        "wrote no": "pass\n",
    }
    for needle, src in cases.items():
        with tempfile.TemporaryDirectory(prefix="r2_fail_") as tmp:
            d = _scratch_bundle(tmp, src)
            try:
                R.run(d)
                raise AssertionError("must refuse")
            except R.RunRefused as exc:
                assert needle in str(exc) or "exited" in str(exc)


def test_receipt_merges_into_the_court_inert() -> None:
    receipt = R.run(os.path.join(BUNDLES, "match_card"))
    led = Ledger()
    led._add_payload(event_id(receipt), receipt)
    led._add_payload(event_id(receipt), receipt)  # idempotent
    assert led.event_count() == 1
    assert led.audit_codes() == []          # inert to the frozen folds
    assert led.fold() == {}
    merged = Ledger.from_jsonl(led.to_jsonl())
    assert merged.to_jsonl() == led.to_jsonl()
    assert canonical_json(receipt) in led.to_jsonl()


def test_cli_round_trip() -> None:
    with tempfile.TemporaryDirectory(prefix="r2_cli_") as tmp:
        rp = os.path.join(tmp, "receipt.json")
        d = os.path.join(BUNDLES, "rank_items")
        assert R.main(["run", d, "--receipt", rp]) == 0
        assert R.main(["verify", d, rp]) == 0
        assert R.main(["verify", os.path.join(BUNDLES, "match_card"), rp]) == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
    print("runtime-r2 lane green")
