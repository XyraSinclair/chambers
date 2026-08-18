"""Pins the REQUESTER BUNDLE contract. RED by design until implemented.

The requester walks away from a run with ONE portable artifact:
`requester_bundle.zip`, written into run_dir by `CourtFileWriter.finalize`.
It contains exactly the requester-visible released surface and nothing else,
and it is verifiable offline by a stranger with a pure-stdlib checker plus
one out-of-band trust anchor.

Contract pinned here (the implementer's spec):

Bundle (emitted by finalize):
  - run_dir / "requester_bundle.zip", byte-deterministic: identical inputs
    (same RunRecord fields, same artifact bytes, fresh lifetime ledger)
    yield identical ZIP bytes. Fixed zip metadata, no timestamps in members.
  - Approved member set, exactly:
      approved_public_artifact.json, receipt.json,
      charge_kernel_ledger.jsonl, manifest.json
  - Rejected/error member set, exactly the same minus
    approved_public_artifact.json (no approved content in a rejected shape).
  - manifest.json: {"version": 1, "entries": [{"fileName", "sha256"}...]},
    strictly sorted by fileName, covering every member except itself,
    sha256 = "sha256:<64 lowercase hex>" of the member's raw bytes.
  - Bundle root (trust anchor, delivered out of band, never inside the
    bundle): "sha256:<64 lowercase hex>" of the COMPLETE
    requester_bundle.zip FILE BYTES. The anchor authenticates the exact
    artifact the requester holds: a ZIP comment, prepended bytes, a
    central-directory metadata change, or a member reorder all change the
    root even when every member's bytes survive — a member-row hash does
    not satisfy the exact-bundle contract. finalize exposes it as
    `writer.requester_bundle_root`, persists it on the RunRecord as
    `rec.requester_bundle_root` (a dataclass field, so save_record's
    record.json carries it and the owner can still transmit the anchor
    after a Chamber restart), and the finalized requester verification
    surface displays it. Before finalize there is no root.
  - No owner-private, reviewer, or worker material — not as members, not
    inside member bytes.

Checker (new module chambers/check_requester_bundle.py):
  - PURE STDLIB: must not import chamber, chambers.kernel, or anything
    outside the standard library (the verifier stays independent of the
    writer, and portable).
  - CLI/main(argv) like check_court_file: exit 0 on pass, SystemExit(1)
    with a message on any violation.
      check_requester_bundle.py <bundle.zip> --expect-bundle-root sha256:<hex>
    The root is REQUIRED — externally supplied, verified, never decorative —
    and it is the SHA-256 of the complete ZIP file bytes, so the checker
    authenticates the exact container, not a canonicalized member listing.
  - Rejects: wrong root; member byte tamper; duplicate member names;
    path-traversal member names; symlink-like zip entries; extra members
    (planted, unrecorded); missing members; malformed manifest; and receipt
    accounting totals inconsistent with the REPLAYED charge ledger.
  - Replay law (pure JSONL parse, no kernel import): for
    receipt.accounting.kernelAccountKey,
      runCumulativeMillibits == sum(debit_mbits over kind=="charge" events
                                    with that key and accepted == true)
      runCeilingMillibits    == that key's register event ceiling_mbits
      runCumulativeMillibits <= runCeilingMillibits

Receipt accounting (receipt.json, written by finalize BEFORE close):
  receipt["accounting"] = {
    "kernelAccountKey": [...],            # run account key
    "runCumulativeMillibits": int,        # includes the charge for these
                                          # very fields — charged before close
    "runCeilingMillibits": int,           # == chamber_run_ceiling_mbits(max_words)
    "lifetimeAccountKey": [...],
    "lifetimeCumulativeMillibits": int,   # >= run cumulative
    "estimatorId": str,                   # CHAMBER_ESTIMATOR.estimator_id
    "estimatorIndependence": str,         # CHAMBER_ESTIMATOR.independence
    "estimatorWorstCaseOverSecrets": bool # the worst-case caveat
  }
  The accounting disclosure is itself a requester-visible emission: an
  emissions.jsonl row with surface "receipt", kind "receipt_accounting",
  charged through both kernel gates before receipt.json is written.

Requester result surface (pure helper — the HTTP route wires it later):
  chamber.render_requester_verification(rec, finalized) -> str (HTML
  fragment). When finalized: shows run cumulative millibits, run ceiling,
  lifetime cumulative millibits, estimator id, the worst-case caveat, the
  bundle root anchor (from rec.requester_bundle_root), and a download link
  to requester_bundle.zip. When not finalized: NO bundle download link and
  NO root.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest import mock

from chambers import chamber
from chambers import check_court_file
from chambers.kernel import (
    KernelMeter,
    Ledger as KernelLedger,
    composition_key,
)

BUNDLE_NAME = "requester_bundle.zip"
BUNDLE_MANIFEST_NAME = "manifest.json"
APPROVED_MEMBERS = {
    "approved_public_artifact.json",
    "receipt.json",
    "charge_kernel_ledger.jsonl",
    BUNDLE_MANIFEST_NAME,
}
REJECTED_MEMBERS = APPROVED_MEMBERS - {"approved_public_artifact.json"}

# Names that must NEVER appear as bundle members: owner/reviewer/worker
# material and the court's own private exhibits.
FORBIDDEN_MEMBER_NAMES = {
    "grant.json",
    "transform.json",
    "run.json",
    "environment_recipe.json",
    "artifacts.jsonl",
    "reviews.jsonl",
    "emissions.jsonl",
    "run_claims.jsonl",
    "release_docket.json",
    "ledger.jsonl",
    "court_manifest.json",
    "approved_answer.txt",
    "worker_notes.txt",
}

APPROVED_ANSWER = "Judgment: bounded requester-bundle fixture answer."
APPROVED_ARTIFACT_BYTES = (
    json.dumps(
        {
            "answer": APPROVED_ANSWER,
            "basis": "Fixture basis for the requester bundle contract.",
            "why_not_higher": "Fixture calibration up.",
            "why_not_lower": "Fixture calibration down.",
            "recommended_followup_facet": "",
            "evidence_cards": [],
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    + "\n"
).encode("utf-8")

REVIEWER_SENTINEL = "PRIVATE-REVIEWER-SENTINEL release rationale"
WORKER_SENTINEL = "PRIVATE-WORKER-SENTINEL raw scratch note"


def _checker():
    """The contract module. Its absence is a FAILURE of the contract, not a
    skip: these tests are the spec for chambers/check_requester_bundle.py."""
    try:
        from chambers import check_requester_bundle
    except ImportError as exc:
        raise AssertionError(
            "missing contract module chambers/check_requester_bundle.py "
            f"(pure-stdlib requester bundle checker): {exc}"
        )
    return check_requester_bundle


def _zip_members(zip_path: Path) -> List[str]:
    with zipfile.ZipFile(zip_path) as zf:
        return zf.namelist()


def _zip_read_all(zip_path: Path) -> Dict[str, bytes]:
    with zipfile.ZipFile(zip_path) as zf:
        return {info.filename: zf.read(info) for info in zf.infolist()}


def _manifest_bytes_for(members: List[Tuple[str, bytes]]) -> bytes:
    """The bundle-manifest convention, computed test-side as the oracle."""
    entries = [
        {"fileName": name, "sha256": chamber.sha256_bytes(data)}
        for name, data in sorted(members, key=lambda item: item[0])
        if name != BUNDLE_MANIFEST_NAME
    ]
    return (
        json.dumps(
            {"version": 1, "entries": entries},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _zip_file_root(zip_path: Path) -> str:
    """The trust-anchor convention: SHA-256 of the complete ZIP file bytes.
    Anything that changes the artifact — a comment, prepended bytes,
    central-directory metadata, member order — changes the root, even when
    every member's bytes are untouched."""
    return chamber.sha256_bytes(zip_path.read_bytes())


def _write_zip(
    zip_path: Path,
    members: List[Tuple[str, bytes]],
    *,
    symlink_names: frozenset = frozenset(),
) -> None:
    """Deterministic zip writer for fixtures: fixed timestamps, stored (no
    compression), members written in the given order."""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, data in members:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            if name in symlink_names:
                info.external_attr = 0o120777 << 16  # S_IFLNK | 0777
            zf.writestr(info, data)


CONTEXT_PACKET_SENTINEL = (
    "Approved context packet fixture: repository history evidence lines for "
    "the bounded reviewability question.\n"
)


class _LifetimeIsolationMixin:
    """Every CourtFileWriter charges the persistent lifetime ledger; tests
    must NEVER write the real one (repo state dir found polluted by exactly
    this on 2026-07-05). Since the zero-tool cutover, every CourtFileWriter
    also embeds the owner-approved context packet, so this mixin provides a
    real packet in a temp workspace and routes the PRODUCTION loader at it —
    no cache seeding, the validation path runs for real every test."""

    def setUp(self) -> None:
        self._lifetime_tmp = Path(tempfile.mkdtemp(prefix="chamber_lt_"))
        self._old_lifetime_path = chamber.LIFETIME_LEDGER_PATH
        chamber.LIFETIME_LEDGER_PATH = self._lifetime_tmp / "lifetime.jsonl"
        self._packet_workspace = Path(tempfile.mkdtemp(prefix="chamber_ws_")).resolve()
        packet = self._packet_workspace / "approved-context.txt"
        packet.write_text(CONTEXT_PACKET_SENTINEL, encoding="utf-8")
        self._old_packet_globals = {
            "WORKSPACE": chamber.WORKSPACE,
            "CONTEXT_PACKET_PATH_RAW": chamber.CONTEXT_PACKET_PATH_RAW,
            "_CONTEXT_PACKET_TEXT": chamber._CONTEXT_PACKET_TEXT,
            "_CONTEXT_PACKET_SHA256": chamber._CONTEXT_PACKET_SHA256,
        }
        chamber.WORKSPACE = self._packet_workspace
        chamber.CONTEXT_PACKET_PATH_RAW = str(packet)
        chamber._CONTEXT_PACKET_TEXT = None
        chamber._CONTEXT_PACKET_SHA256 = ""

    def tearDown(self) -> None:
        for name, value in self._old_packet_globals.items():
            setattr(chamber, name, value)
        shutil.rmtree(self._packet_workspace, ignore_errors=True)
        chamber.LIFETIME_LEDGER_PATH = self._old_lifetime_path
        shutil.rmtree(self._lifetime_tmp, ignore_errors=True)


def _record(run_id: str, status: str) -> chamber.RunRecord:
    rec = chamber.RunRecord(
        run_id=run_id,
        created_at="2026-07-10T12:00:00+00:00",
        requester="tester",
        task=chamber.build_wrapped_task(chamber.DEFAULT_DEMO_QUESTION),
        max_words=64,
        question=chamber.DEFAULT_DEMO_QUESTION,
        status=status,
        receipt=["release reviewed", "owner approved disclosure"],
    )
    if status == "approved":
        rec.approved_answer = APPROVED_ANSWER
    if status == "error":
        rec.error = "run_error"
    return rec


def _finalized_run(
    root: Path,
    *,
    status: str = "approved",
    run_id: str = "bundlefix",
    with_reviews: bool = False,
    with_private_note: bool = False,
) -> Tuple[Path, "chamber.CourtFileWriter", chamber.RunRecord]:
    rec = _record(run_id, status)
    run_dir = root / rec.run_id
    writer = chamber.CourtFileWriter(rec, run_dir)
    if status == "approved":
        (run_dir / "approved_public_artifact.json").write_bytes(APPROVED_ARTIFACT_BYTES)
    if with_reviews:
        for label, reviewer in (
            ("release_a", "principal_reviewer_release_a"),
            ("release_b", "principal_reviewer_release_b"),
        ):
            writer.record_review(
                label=label,
                stage="release",
                reviewer_id=reviewer,
                verdict="allow",
                risk="low",
                saw={"sawRawPrivateData": False, "dataClasses": [], "granularity": "aggregate"},
                unsafe_field_paths=[],
                rationale=REVIEWER_SENTINEL,
            )
    if with_private_note:
        note_path = run_dir / "worker_notes.txt"
        note_path.write_text(WORKER_SENTINEL + "\n", encoding="utf-8")
        writer.record_artifact(
            note_path,
            kind="worker_notes",
            visibility="owner_private",
            redaction_state="raw",
            actor_id="principal_worker_agent",
        )
    writer.finalize(rec)
    return run_dir, writer, rec


class RequesterBundleEmissionTests(_LifetimeIsolationMixin, unittest.TestCase):
    """finalize emits requester_bundle.zip: exact released member set,
    rejected shape omits approved content, no private material, and
    identical inputs give identical bytes."""

    def test_finalize_emits_bundle_with_exact_released_member_set(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_bundle_"))
        try:
            run_dir, writer, _rec = _finalized_run(root, status="approved")
            bundle = run_dir / BUNDLE_NAME
            self.assertTrue(
                bundle.exists(),
                "finalize must emit requester_bundle.zip into run_dir",
            )
            members = _zip_read_all(bundle)
            self.assertEqual(set(members), APPROVED_MEMBERS)

            # The emitted bundle is internally consistent with its own
            # manifest: every non-manifest member's raw bytes hash to the
            # recorded sha256, strictly sorted, version 1.
            manifest = json.loads(members[BUNDLE_MANIFEST_NAME])
            self.assertEqual(manifest["version"], 1)
            names = [entry["fileName"] for entry in manifest["entries"]]
            self.assertEqual(names, sorted(names))
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(set(names), APPROVED_MEMBERS - {BUNDLE_MANIFEST_NAME})
            for entry in manifest["entries"]:
                self.assertEqual(
                    chamber.sha256_bytes(members[entry["fileName"]]),
                    entry["sha256"],
                    f"manifest sha256 mismatch for {entry['fileName']}",
                )

            # finalize exposes the out-of-band trust anchor: SHA-256 of the
            # complete emitted ZIP file bytes — the exact-bundle contract.
            expected_root = _zip_file_root(bundle)
            self.assertEqual(
                getattr(writer, "requester_bundle_root", None),
                expected_root,
                "finalize must set writer.requester_bundle_root to the "
                "SHA-256 of the complete requester_bundle.zip file bytes",
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejected_shape_omits_approved_content(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_bundle_"))
        try:
            run_dir, _writer, _rec = _finalized_run(
                root, status="rejected", run_id="bundlerej"
            )
            bundle = run_dir / BUNDLE_NAME
            self.assertTrue(
                bundle.exists(),
                "a rejected run still yields a bundle (receipt + ledger + manifest)",
            )
            members = _zip_read_all(bundle)
            self.assertEqual(set(members), REJECTED_MEMBERS)
            for name, data in members.items():
                self.assertNotIn(
                    APPROVED_ANSWER.encode("utf-8"),
                    data,
                    f"approved content leaked into rejected bundle member {name}",
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_bundle_excludes_private_reviewer_and_worker_material(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_bundle_"))
        try:
            run_dir, _writer, _rec = _finalized_run(
                root,
                status="approved",
                run_id="bundlepriv",
                with_reviews=True,
                with_private_note=True,
            )
            bundle = run_dir / BUNDLE_NAME
            self.assertTrue(bundle.exists())
            members = _zip_read_all(bundle)
            self.assertEqual(set(members), APPROVED_MEMBERS)
            self.assertFalse(set(members) & FORBIDDEN_MEMBER_NAMES)
            for name, data in members.items():
                for sentinel in (REVIEWER_SENTINEL, WORKER_SENTINEL):
                    self.assertNotIn(
                        sentinel.encode("utf-8"),
                        data,
                        f"private material leaked into bundle member {name}",
                    )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_identical_inputs_yield_identical_zip_bytes(self) -> None:
        """Byte determinism is the contract, not a nicety: a counterparty
        re-deriving the bundle from the same court must land on the same
        root. Fresh lifetime ledger per build == identical inputs."""

        def build() -> bytes:
            lt = Path(tempfile.mkdtemp(prefix="chamber_lt_det_"))
            old = chamber.LIFETIME_LEDGER_PATH
            root = Path(tempfile.mkdtemp(prefix="chamber_bundle_det_"))
            try:
                chamber.LIFETIME_LEDGER_PATH = lt / "lifetime.jsonl"
                run_dir, _writer, _rec = _finalized_run(
                    root, status="approved", run_id="bundledet"
                )
                bundle = run_dir / BUNDLE_NAME
                self.assertTrue(bundle.exists())
                return bundle.read_bytes()
            finally:
                chamber.LIFETIME_LEDGER_PATH = old
                shutil.rmtree(root, ignore_errors=True)
                shutil.rmtree(lt, ignore_errors=True)

        first = build()
        second = build()
        self.assertEqual(
            first,
            second,
            "identical inputs must yield byte-identical requester_bundle.zip "
            "(fixed zip metadata; no wall-clock in bundled members)",
        )

    def test_bundle_root_is_persisted_on_run_record(self) -> None:
        """The anchor must survive a Chamber restart: the owner transmits it
        out of band, possibly long after the writer object is gone. finalize
        pins it on the RunRecord, and it must be a dataclass FIELD so
        save_record's rec.to_dict() (record.json) round-trips it."""
        root = Path(tempfile.mkdtemp(prefix="chamber_bundle_"))
        try:
            run_dir, writer, rec = _finalized_run(
                root, status="approved", run_id="bundlerec"
            )
            expected_root = _zip_file_root(run_dir / BUNDLE_NAME)
            self.assertEqual(
                getattr(rec, "requester_bundle_root", None),
                expected_root,
                "finalize must persist the zip-bytes bundle root on the "
                "RunRecord (rec.requester_bundle_root)",
            )
            self.assertEqual(
                rec.to_dict().get("requester_bundle_root"),
                expected_root,
                "requester_bundle_root must be a RunRecord dataclass field "
                "so record.json (save_record) carries it across restarts",
            )
            self.assertFalse(
                getattr(_record("bundlepre", "queued"), "requester_bundle_root", ""),
                "an unfinalized record must carry no bundle root",
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)


class ReceiptAccountingTests(_LifetimeIsolationMixin, unittest.TestCase):
    """receipt.json exposes the charged accounting block, and the accounting
    disclosure itself is charged through the kernel BEFORE close."""

    def _accounting(self, run_dir: Path) -> Dict:
        receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
        self.assertIn(
            "accounting",
            receipt,
            "receipt.json must expose an accounting block "
            "(run/lifetime millibits, ceiling, estimator attestation)",
        )
        return receipt["accounting"]

    def test_receipt_exposes_run_lifetime_and_estimator_accounting(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_receipt_"))
        try:
            run_dir, _writer, rec = _finalized_run(
                root, status="approved", run_id="receiptacct"
            )
            acct = self._accounting(run_dir)
            self.assertEqual(
                acct["runCeilingMillibits"],
                chamber.chamber_run_ceiling_mbits(rec.max_words),
            )
            self.assertGreater(acct["runCumulativeMillibits"], 0)
            self.assertLessEqual(
                acct["runCumulativeMillibits"], acct["runCeilingMillibits"]
            )
            self.assertGreaterEqual(
                acct["lifetimeCumulativeMillibits"], acct["runCumulativeMillibits"]
            )
            self.assertEqual(acct["estimatorId"], chamber.CHAMBER_ESTIMATOR.estimator_id)
            self.assertEqual(
                acct["estimatorIndependence"], chamber.CHAMBER_ESTIMATOR.independence
            )
            self.assertIs(acct["estimatorWorstCaseOverSecrets"], True)
            self.assertEqual(acct["kernelAccountKey"], list(_writer.kernel_key))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_receipt_accounting_is_charged_before_close(self) -> None:
        """Two pins. (1) The accounting disclosure is a requester-visible
        emission of its own: emissions.jsonl carries surface "receipt",
        kind "receipt_accounting". (2) The reported run cumulative equals
        the FINAL folded cumulative of the run account in the sealed
        charge_kernel_ledger.jsonl — i.e. the number already includes its
        own charge, so it was charged before close, not narrated after."""
        root = Path(tempfile.mkdtemp(prefix="chamber_receipt_"))
        try:
            run_dir, writer, _rec = _finalized_run(
                root, status="approved", run_id="receiptcharge"
            )
            emissions = [
                json.loads(line)
                for line in (run_dir / "emissions.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertTrue(
                any(
                    row.get("surface") == "receipt"
                    and row.get("kind") == "receipt_accounting"
                    for row in emissions
                ),
                "the receipt accounting disclosure must be charged as its own "
                "requester-visible emission (surface=receipt, "
                "kind=receipt_accounting)",
            )
            acct = self._accounting(run_dir)
            ledger = KernelLedger.from_jsonl(
                (run_dir / "charge_kernel_ledger.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(ledger.audit(), [])
            accounts = ledger.fold()
            run_account = accounts[writer.kernel_key]
            self.assertEqual(
                acct["runCumulativeMillibits"],
                run_account.cumulative_mbits,
                "receipt accounting must equal the sealed ledger's folded "
                "cumulative (charged before close)",
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)


class RenderRequesterVerificationTests(_LifetimeIsolationMixin, unittest.TestCase):
    """The pure requester-facing verification surface:
    chamber.render_requester_verification(rec, finalized) -> HTML str.
    The HTTP route wires it later (covered by the existing fake e2e)."""

    def test_finalized_view_exposes_accounting_and_bundle_download(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_render_"))
        try:
            run_dir, _writer, rec = _finalized_run(
                root, status="approved", run_id="renderfin"
            )
            acct = json.loads(
                (run_dir / "receipt.json").read_text(encoding="utf-8")
            )["accounting"]
            render = getattr(chamber, "render_requester_verification", None)
            self.assertIsNotNone(
                render,
                "missing pure helper chamber.render_requester_verification"
                "(rec, finalized) -> str",
            )
            html_out = render(rec, True)
            self.assertIsInstance(html_out, str)
            for token, label in (
                (str(acct["runCumulativeMillibits"]), "run cumulative millibits"),
                (str(acct["runCeilingMillibits"]), "run ceiling millibits"),
                (
                    str(acct["lifetimeCumulativeMillibits"]),
                    "lifetime cumulative millibits",
                ),
                (acct["estimatorId"], "estimator id"),
            ):
                self.assertIn(
                    token, html_out, f"finalized view must show the {label}"
                )
            self.assertIn(
                "worst-case",
                html_out.lower(),
                "finalized view must state the estimator's worst-case caveat",
            )
            self.assertIn(
                BUNDLE_NAME,
                html_out,
                "finalized view must link the requester bundle download",
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_finalized_view_shows_the_bundle_root_anchor(self) -> None:
        """The owner reads the anchor OFF this surface to transmit it out of
        band — render is pure over rec, so this also forces the root to live
        on the RunRecord, not on the (restart-mortal) writer."""
        root = Path(tempfile.mkdtemp(prefix="chamber_render_"))
        try:
            run_dir, _writer, rec = _finalized_run(
                root, status="approved", run_id="renderroot"
            )
            expected_root = _zip_file_root(run_dir / BUNDLE_NAME)
            render = getattr(chamber, "render_requester_verification", None)
            self.assertIsNotNone(render)
            html_out = render(rec, True)
            self.assertIn(
                expected_root,
                html_out,
                "finalized view must display the zip-bytes bundle root so the "
                "owner can transmit the required out-of-band anchor",
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_unfinalized_view_offers_no_bundle_download(self) -> None:
        rec = _record("renderpend", "queued")
        # Even a root somehow present on the record must not surface early:
        # an unfinalized court has no sealed bytes, so no link and no anchor.
        stray_root = chamber.sha256_bytes(b"anchor-not-yet-earned")
        rec.requester_bundle_root = stray_root
        render = getattr(chamber, "render_requester_verification", None)
        self.assertIsNotNone(
            render,
            "missing pure helper chamber.render_requester_verification"
            "(rec, finalized) -> str",
        )
        html_out = render(rec, False)
        self.assertIsInstance(html_out, str)
        self.assertNotIn(
            BUNDLE_NAME,
            html_out,
            "the bundle download link must not exist before finalize",
        )
        self.assertNotIn(
            stray_root,
            html_out,
            "the bundle root anchor must not exist before finalize",
        )


class _BundleFixtureMixin:
    """Hand-built clean-bundle fixtures plus checker assertion helpers,
    shared by the contract tests below and the snapshot/anti-vacuity
    additions further down."""

    RUN_ID = "checkerfix"
    CEILING_MBITS = 64_000  # comfortably above one answer-field charge (16k mbits)

    def _clean_members(self, *, approved: bool = True) -> List[Tuple[str, bytes]]:
        """A minimal, internally consistent bundle built to convention:
        a real (audit-clean, canonical) charge ledger with one register and
        one accepted charge, and a receipt whose accounting replays it."""
        key = composition_key(
            "chamber_local_demo", f"run:{self.RUN_ID}", "principal_requester"
        )
        ledger = KernelLedger()
        meter = KernelMeter(
            node="chamber.py", issuer="chamber_local_demo", ledger=ledger
        )
        meter.register(
            key,
            subject_entropy_mbits=self.CEILING_MBITS * 4,
            ceiling_mbits=self.CEILING_MBITS,
        )
        decision = meter.charge(
            key,
            chamber.chamber_capacity_estimate(
                channel="answer_field",
                text_mbits=chamber.CHAMBER_ANSWER_FIELD_MBITS,
            ),
            chamber.CHAMBER_ESTIMATOR,
        )
        assert decision.accepted
        receipt = {
            "releaseId": f"release_{self.RUN_ID}_1",
            "noPerfectSecrecyClaim": True,
            "caveats": [
                {
                    "code": "not_semantic_proof",
                    "text": "Process evidence, not a privacy proof.",
                }
            ],
            "accounting": {
                "kernelAccountKey": list(key),
                "runCumulativeMillibits": decision.cumulative_mbits,
                "runCeilingMillibits": self.CEILING_MBITS,
                "lifetimeAccountKey": [
                    "chamber_local_demo",
                    "passcode:fixture0000",
                    "principal_requester",
                ],
                "lifetimeCumulativeMillibits": decision.cumulative_mbits,
                "estimatorId": chamber.CHAMBER_ESTIMATOR.estimator_id,
                "estimatorIndependence": chamber.CHAMBER_ESTIMATOR.independence,
                "estimatorWorstCaseOverSecrets": True,
            },
        }
        members: List[Tuple[str, bytes]] = []
        if approved:
            members.append(
                ("approved_public_artifact.json", APPROVED_ARTIFACT_BYTES)
            )
        members.append(
            (
                "receipt.json",
                (
                    json.dumps(
                        receipt, ensure_ascii=False, sort_keys=True, indent=2
                    )
                    + "\n"
                ).encode("utf-8"),
            )
        )
        members.append(
            ("charge_kernel_ledger.jsonl", ledger.to_jsonl().encode("ascii"))
        )
        members.append((BUNDLE_MANIFEST_NAME, _manifest_bytes_for(members)))
        return members

    def _build(
        self,
        root: Path,
        members: List[Tuple[str, bytes]],
        *,
        symlink_names: frozenset = frozenset(),
    ) -> Tuple[Path, str]:
        zip_path = root / BUNDLE_NAME
        _write_zip(zip_path, members, symlink_names=symlink_names)
        return zip_path, _zip_file_root(zip_path)

    def _remanifest(
        self, members: List[Tuple[str, bytes]]
    ) -> List[Tuple[str, bytes]]:
        """Recompute manifest.json over the (possibly mutated) members —
        the coordinated forger's move, so only deeper checks can convict."""
        without = [m for m in members if m[0] != BUNDLE_MANIFEST_NAME]
        return without + [(BUNDLE_MANIFEST_NAME, _manifest_bytes_for(without))]

    def _assert_ok(self, zip_path: Path, expect_root: str) -> None:
        checker = _checker()
        argv = [
            "check_requester_bundle.py",
            str(zip_path),
            "--expect-bundle-root",
            expect_root,
        ]
        try:
            code = checker.main(argv)
        except SystemExit as exc:
            self.fail(
                f"checker rejected a bundle it must accept: exit {exc.code}"
            )
        self.assertEqual(code, 0)

    def _assert_rejected(self, zip_path: Path, expect_root: str) -> None:
        checker = _checker()
        argv = [
            "check_requester_bundle.py",
            str(zip_path),
            "--expect-bundle-root",
            expect_root,
        ]
        with self.assertRaises(SystemExit) as ctx:
            checker.main(argv)
        self.assertEqual(ctx.exception.code, 1)


class CheckRequesterBundleContractTests(_BundleFixtureMixin, unittest.TestCase):
    """The pure-stdlib checker, specified against HAND-BUILT bundles so the
    verifier is pinned to the convention, not to the writer. The externally
    supplied root is required and verified; every rejection class in the
    contract gets a self-consistent forgery where possible, so the check
    that convicts is the one under test."""

    def test_checker_is_pure_stdlib(self) -> None:
        """The verifier must never import the writer or the kernel: a
        stranger runs it with nothing but Python."""
        checker = _checker()
        source = Path(checker.__file__).read_text(encoding="utf-8")
        for banned in ("chambers", "import chamber", "from chamber", "kernel"):
            self.assertNotIn(
                banned,
                source,
                f"check_requester_bundle.py must be pure stdlib (found {banned!r})",
            )

    def test_accepts_clean_approved_bundle_with_correct_root(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            zip_path, anchor = self._build(root, self._clean_members())
            self._assert_ok(zip_path, anchor)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_accepts_clean_rejected_shape_bundle(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            zip_path, anchor = self._build(
                root, self._clean_members(approved=False)
            )
            self._assert_ok(zip_path, anchor)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_wrong_root_on_clean_bundle(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            zip_path, anchor = self._build(root, self._clean_members())
            wrong = chamber.sha256_json(["not-the-bundle-root"])
            self.assertNotEqual(wrong, anchor)
            self._assert_rejected(zip_path, wrong)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_member_byte_tamper(self) -> None:
        """Tampered member, stale manifest, ORIGINAL root: both the manifest
        check and the anchor can convict; the bundle must not pass."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = self._clean_members()
            _zip_path, anchor = self._build(root, members)
            tampered = [
                (name, data + b"\n \n" if name == "receipt.json" else data)
                for name, data in members
            ]
            zip_path = root / "tampered.zip"
            _write_zip(zip_path, tampered)
            self._assert_rejected(zip_path, anchor)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_same_members_different_container(self) -> None:
        """The exact-bundle law. Every member's bytes survive — so the
        manifest, the closed set, and the replay all still pass, and any
        member-row root is UNCHANGED — but the ZIP the requester holds is
        not the ZIP that was finalized. A ZIP comment is the minimal such
        forgery; only a root over the complete file bytes can convict."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            zip_path, anchor = self._build(root, self._clean_members())
            self._assert_ok(zip_path, anchor)
            commented = root / "commented.zip"
            commented.write_bytes(zip_path.read_bytes())
            with zipfile.ZipFile(commented, "a") as zf:
                zf.comment = b"same members, different container"
            self.assertEqual(
                _zip_read_all(zip_path),
                _zip_read_all(commented),
                "fixture error: the container tamper must leave every "
                "member's bytes identical",
            )
            self.assertNotEqual(
                zip_path.read_bytes(),
                commented.read_bytes(),
                "fixture error: the container tamper must change the file bytes",
            )
            self._assert_rejected(commented, anchor)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_duplicate_member_names(self) -> None:
        """Zip allows duplicate names; extraction order is reader-dependent,
        so duplicates are an ambiguity attack. Convicted regardless of root."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = self._clean_members()
            _zip_path, anchor = self._build(root, members)
            receipt = next(m for m in members if m[0] == "receipt.json")
            zip_path = root / "dup.zip"
            _write_zip(zip_path, members + [receipt])
            self._assert_rejected(zip_path, anchor)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_path_traversal_member_name(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = self._clean_members() + [
                ("../escape.json", b"{}\n")
            ]
            zip_path = root / "traversal.zip"
            _write_zip(zip_path, members)
            # Even a root recomputed over the hostile zip must not save it.
            self._assert_rejected(zip_path, _zip_file_root(zip_path))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_symlink_like_member(self) -> None:
        """An expected member name carried as a symlink entry, manifest and
        root recomputed over its bytes: only the entry-type check convicts."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = [
                (
                    ("approved_public_artifact.json", b"receipt.json")
                    if name == "approved_public_artifact.json"
                    else (name, data)
                )
                for name, data in self._clean_members()
            ]
            members = self._remanifest(members)
            zip_path = root / "symlink.zip"
            _write_zip(
                zip_path,
                members,
                symlink_names=frozenset({"approved_public_artifact.json"}),
            )
            self._assert_rejected(zip_path, _zip_file_root(zip_path))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_extra_unrecorded_member(self) -> None:
        """A planted member with manifest left stale but root recomputed to
        cover it: the closed-inventory law (manifest covers exactly the
        non-manifest members) must convict."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = self._clean_members() + [
                ("planted_disclosure.txt", b"smuggled\n")
            ]
            zip_path = root / "planted.zip"
            _write_zip(zip_path, members)
            self._assert_rejected(zip_path, _zip_file_root(zip_path))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_missing_member(self) -> None:
        """Dropping the charge ledger (manifest still lists it, root
        recomputed over the survivors): both the manifest law and the
        required-member law must convict."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = [
                m
                for m in self._clean_members()
                if m[0] != "charge_kernel_ledger.jsonl"
            ]
            zip_path = root / "missing.zip"
            _write_zip(zip_path, members)
            self._assert_rejected(zip_path, _zip_file_root(zip_path))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_malformed_manifest(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            for bad_manifest in (
                b"not json at all\n",
                json.dumps({"version": 999, "entries": []}).encode("utf-8"),
                json.dumps({"version": 1, "entries": [{"fileName": "receipt.json"}]}).encode("utf-8"),
            ):
                members = [
                    (
                        (BUNDLE_MANIFEST_NAME, bad_manifest)
                        if name == BUNDLE_MANIFEST_NAME
                        else (name, data)
                    )
                    for name, data in self._clean_members()
                ]
                zip_path = root / "badmanifest.zip"
                _write_zip(zip_path, members)
                self._assert_rejected(zip_path, _zip_file_root(zip_path))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_receipt_totals_inconsistent_with_replayed_ledger(self) -> None:
        """The fully coordinated forgery: bump runCumulativeMillibits in the
        receipt, recompute manifest AND root so every byte-integrity check
        passes. Only the REPLAY of the charge ledger (sum of accepted
        debit_mbits for the named account) can convict — that replay is the
        checker's reason to exist."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = self._clean_members()
            forged: List[Tuple[str, bytes]] = []
            for name, data in members:
                if name == "receipt.json":
                    receipt = json.loads(data)
                    receipt["accounting"]["runCumulativeMillibits"] += 1
                    data = (
                        json.dumps(
                            receipt, ensure_ascii=False, sort_keys=True, indent=2
                        )
                        + "\n"
                    ).encode("utf-8")
                forged.append((name, data))
            forged = self._remanifest(forged)
            zip_path = root / "forgedtotals.zip"
            _write_zip(zip_path, forged)
            self._assert_rejected(zip_path, _zip_file_root(zip_path))
        finally:
            shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# Durable finalization. Terminal rec.status alone is NOT proof that finalize
# reached its final _write_manifest seal: an interrupted finalize leaves
# requester_bundle.zip (and a record.json already carrying the anchor) on
# disk with NO court_manifest.json, and a restart converts any nonterminal
# record to status="error" — also terminal. The requester surface and the
# bundle download must key availability on the durable seal, never on
# status alone; and nothing may write into a court after it is sealed.
# ---------------------------------------------------------------------------


class _ChamberGlobalsMixin(_LifetimeIsolationMixin):
    """Redirect chamber's persistent globals (STATE_DIR/RUNS_DIR/STATE) into
    a temp root so route, restart, and worker-loop tests never touch the repo
    court state, and always restore them."""

    def setUp(self) -> None:
        super().setUp()
        self._globals_tmp = Path(tempfile.mkdtemp(prefix="chamber_globals_"))
        self._old_globals = {
            "STATE_DIR": chamber.STATE_DIR,
            "RUNS_DIR": chamber.RUNS_DIR,
            "STATE": chamber.STATE,
        }
        chamber.STATE_DIR = self._globals_tmp / ".chamber"
        chamber.RUNS_DIR = chamber.STATE_DIR / "runs"
        chamber.RUNS_DIR.mkdir(parents=True)
        chamber.STATE = chamber.ChamberState()

    def tearDown(self) -> None:
        for name, value in self._old_globals.items():
            setattr(chamber, name, value)
        shutil.rmtree(self._globals_tmp, ignore_errors=True)
        super().tearDown()

    # -- fixtures ----------------------------------------------------------

    def _production_court(
        self, run_id: str, status: str, *, interrupt_before_manifest: bool
    ) -> Tuple[Path, chamber.RunRecord]:
        """A court built the production way: record.json saved BEFORE
        finalize (as STATE.add/update do), then CourtFileWriter.finalize.
        With interrupt_before_manifest, finalize dies at the exact seam
        under test — after the bundle write and the record.json refresh,
        before the court_manifest.json seal."""
        rec = _record(run_id, status)
        with contextlib.redirect_stdout(io.StringIO()):
            chamber.save_record(rec)
            run_dir = chamber.RUNS_DIR / run_id
            writer = chamber.CourtFileWriter(rec, run_dir)
            if status == "approved":
                (run_dir / "approved_public_artifact.json").write_bytes(
                    APPROVED_ARTIFACT_BYTES
                )
            if interrupt_before_manifest:
                real = chamber.CourtFileWriter._write_manifest
                def dying(_writer_self) -> None:
                    raise RuntimeError("simulated crash before the manifest seal")
                chamber.CourtFileWriter._write_manifest = dying
                try:
                    with self.assertRaises(RuntimeError):
                        writer.finalize(rec)
                finally:
                    chamber.CourtFileWriter._write_manifest = real
            else:
                writer.finalize(rec)
        # Fixture sanity: the interrupted shape is exactly the gap scenario.
        self.assertTrue((run_dir / BUNDLE_NAME).is_file())
        saved = json.loads((run_dir / "record.json").read_text(encoding="utf-8"))
        self.assertTrue(saved.get("requester_bundle_root"))
        self.assertEqual(
            (run_dir / check_court_file.COURT_MANIFEST_NAME).exists(),
            not interrupt_before_manifest,
        )
        return run_dir, rec

    def _restart(self) -> None:
        """Simulate a Chamber restart: fresh in-memory state, then the real
        production hydration path."""
        chamber.STATE = chamber.ChamberState()
        with contextlib.redirect_stdout(io.StringIO()):
            chamber.load_saved_records()

    def _assert_court_integrity(self, run_dir: Path, context: str) -> None:
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                check_court_file.verify_exact_integrity(run_dir, None)
        except SystemExit:
            self.fail(f"{context}: {err.getvalue().strip()}")


class _FakeSocket:
    """Just enough socket for BaseHTTPRequestHandler: rfile from the raw
    request bytes, response bytes captured via sendall (wbufsize=0 makes the
    handler write through socketserver._SocketWriter → sendall)."""

    def __init__(self, raw_request: bytes) -> None:
        self._rfile = io.BytesIO(raw_request)
        self.captured = bytearray()

    def makefile(self, mode: str, *args, **kwargs):
        return self._rfile

    def sendall(self, data: bytes) -> None:
        self.captured += bytes(data)

    def close(self) -> None:
        pass


def _http_get(path: str) -> Tuple[int, bytes]:
    """Drive the PRODUCTION Handler.do_GET (routing, finalized derivation,
    file serving) without a live server. Returns (status_code, body)."""
    raw = (
        f"GET {path} HTTP/1.1\r\nHost: chamber.test\r\nConnection: close\r\n\r\n"
    ).encode("ascii")
    sock = _FakeSocket(raw)
    with contextlib.redirect_stderr(io.StringIO()):  # request log lines
        chamber.Handler(sock, ("127.0.0.1", 0), None)
    response = bytes(sock.captured)
    head, sep, body = response.partition(b"\r\n\r\n")
    if not sep:
        raise AssertionError(f"malformed HTTP response: {response!r}")
    status_code = int(head.split(b"\r\n", 1)[0].split()[1])
    return status_code, body


def _http_post(path: str, form: Dict[str, str]) -> Tuple[int, bytes]:
    """Drive the PRODUCTION Handler.do_POST the same way _http_get drives
    do_GET: real routing, real form parsing, no live server."""
    payload = urllib.parse.urlencode(form).encode("utf-8")
    raw = (
        f"POST {path} HTTP/1.1\r\nHost: chamber.test\r\nConnection: close\r\n"
        f"Content-Type: application/x-www-form-urlencoded\r\n"
        f"Content-Length: {len(payload)}\r\n\r\n"
    ).encode("ascii") + payload
    sock = _FakeSocket(raw)
    with contextlib.redirect_stderr(io.StringIO()):  # request log lines
        chamber.Handler(sock, ("127.0.0.1", 0), None)
    response = bytes(sock.captured)
    head, sep, body = response.partition(b"\r\n\r\n")
    if not sep:
        raise AssertionError(f"malformed HTTP response: {response!r}")
    status_code = int(head.split(b"\r\n", 1)[0].split()[1])
    return status_code, body


class DurableFinalizationGateTests(_ChamberGlobalsMixin, unittest.TestCase):
    """The requester result surface and the bundle download must be gated on
    the durable court seal (court_manifest.json written by the final
    _write_manifest), not on terminal status: status is set and persisted
    before the seal exists, and a restart mints terminal status="error" for
    every interrupted run."""

    # Pre-crash statuses covering both roads to "terminal without a seal":
    # already-approved when finalize died, and nonterminal (restart converts
    # it to error).
    PRE_CRASH_STATUSES = ("approved", "running_worker")

    def test_download_route_requires_the_durable_seal(self) -> None:
        for status in self.PRE_CRASH_STATUSES:
            with self.subTest(pre_crash_status=status):
                run_id = f"unsealed{status.replace('_', '')}"
                run_dir, _rec = self._production_court(
                    run_id, status, interrupt_before_manifest=True
                )
                self._restart()
                rec = chamber.STATE.get(run_id)
                self.assertIsNotNone(rec)
                self.assertIn(
                    rec.status,
                    {"approved", "rejected", "error"},
                    "fixture: status must be terminal after restart",
                )
                self.assertTrue((run_dir / BUNDLE_NAME).is_file())
                code, _body = _http_get(f"/r/{run_id}/{BUNDLE_NAME}")
                self.assertEqual(
                    code,
                    404,
                    "an unsealed bundle (court_manifest.json absent) must not "
                    "be served, even though rec.status is terminal and "
                    "requester_bundle.zip exists on disk",
                )

    def test_result_page_withholds_bundle_and_root_without_the_seal(self) -> None:
        for status in self.PRE_CRASH_STATUSES:
            with self.subTest(pre_crash_status=status):
                run_id = f"unsealedpage{status.replace('_', '')}"
                self._production_court(
                    run_id, status, interrupt_before_manifest=True
                )
                self._restart()
                rec = chamber.STATE.get(run_id)
                self.assertTrue(
                    rec.requester_bundle_root,
                    "fixture: the interrupted record carries the anchor",
                )
                code, body = _http_get(f"/r/{run_id}")
                self.assertEqual(code, 200)
                self.assertNotIn(
                    BUNDLE_NAME.encode("utf-8"),
                    body,
                    "the result page must not offer the bundle download while "
                    "the durable court seal is absent",
                )
                self.assertNotIn(
                    rec.requester_bundle_root.encode("utf-8"),
                    body,
                    "the result page must not display a bundle root for an "
                    "unsealed court — an anchor over unsealed bytes "
                    "authenticates nothing",
                )

    def test_sealed_court_stays_available_after_restart(self) -> None:
        """Positive control: a genuinely finalized court (manifest present)
        keeps serving the result surface and the exact sealed bundle bytes."""
        run_id = "sealedavail"
        run_dir, _rec = self._production_court(
            run_id, "approved", interrupt_before_manifest=False
        )
        self._restart()
        rec = chamber.STATE.get(run_id)
        self.assertEqual(rec.status, "approved")
        expected_root = _zip_file_root(run_dir / BUNDLE_NAME)
        code, body = _http_get(f"/r/{run_id}")
        self.assertEqual(code, 200)
        self.assertIn(BUNDLE_NAME.encode("utf-8"), body)
        self.assertIn(expected_root.encode("utf-8"), body)
        code, body = _http_get(f"/r/{run_id}/{BUNDLE_NAME}")
        self.assertEqual(code, 200)
        self.assertEqual(
            body,
            (run_dir / BUNDLE_NAME).read_bytes(),
            "the download must serve the exact sealed bundle bytes",
        )


class LegacyLoadHydrationTests(_ChamberGlobalsMixin, unittest.TestCase):
    """Legacy hydration (record.json predating the anchor field) may
    re-derive the anchor ONLY from a sealed court: minting a root over an
    unsealed bundle launders interrupted bytes into a trust anchor."""

    def _strip_root_from_record(self, run_dir: Path) -> None:
        data = json.loads((run_dir / "record.json").read_text(encoding="utf-8"))
        data.pop("requester_bundle_root", None)
        chamber.write_json(run_dir / "record.json", data)

    def test_load_does_not_mint_anchor_from_unsealed_bundle(self) -> None:
        run_id = "legacyunsealed"
        run_dir, _rec = self._production_court(
            run_id, "approved", interrupt_before_manifest=True
        )
        self._strip_root_from_record(run_dir)
        self._restart()
        rec = chamber.STATE.get(run_id)
        self.assertIsNotNone(rec)
        self.assertFalse(
            rec.requester_bundle_root,
            "load_saved_records must not mint a bundle root from an UNSEALED "
            "bundle (court_manifest.json absent): the bytes were never "
            "finalized, so there is no anchor to re-derive",
        )

    def test_load_rederives_anchor_from_sealed_legacy_court(self) -> None:
        """Positive control: a sealed legacy court (manifest present and
        consistent, record.json merely predating the field) re-derives the
        anchor from the sealed bundle bytes."""
        run_id = "legacysealed"
        run_dir, _rec = self._production_court(
            run_id, "approved", interrupt_before_manifest=False
        )
        # Simulate the legacy writer: record.json without the field, court
        # re-sealed over the edited bytes so it stays internally consistent.
        self._strip_root_from_record(run_dir)
        manifest = {
            "version": check_court_file.COURT_MANIFEST_VERSION,
            "entries": check_court_file.court_manifest_entries(run_dir),
        }
        (run_dir / check_court_file.COURT_MANIFEST_NAME).write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        self._assert_court_integrity(run_dir, "fixture: legacy court must be sealed")
        self._restart()
        rec = chamber.STATE.get(run_id)
        self.assertEqual(
            rec.requester_bundle_root,
            _zip_file_root(run_dir / BUNDLE_NAME),
            "a sealed legacy court re-derives the anchor from the sealed "
            "bundle bytes on the owner's own disk",
        )


    def test_legacy_hydration_reads_root_from_manifest_not_current_bytes(self) -> None:
        """Finalization-review finding: the committed hash IS the anchor.
        court_manifest.json already committed requester_bundle.zip's
        file-bytes hash at finalization; hydration that re-hashes whatever
        bytes currently sit at that path launders any post-seal tamper into
        a trust anchor the owner then transmits as truth."""
        run_id = "legacytamper"
        run_dir, _rec = self._production_court(
            run_id, "approved", interrupt_before_manifest=False
        )
        # Legacy shape: record.json predates the field; court re-sealed over
        # the edited bytes so the fixture is internally consistent.
        self._strip_root_from_record(run_dir)
        manifest = {
            "version": check_court_file.COURT_MANIFEST_VERSION,
            "entries": check_court_file.court_manifest_entries(run_dir),
        }
        (run_dir / check_court_file.COURT_MANIFEST_NAME).write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        self._assert_court_integrity(run_dir, "fixture: legacy court must be sealed")
        committed = next(
            entry["sha256"]
            for entry in manifest["entries"]
            if entry["fileName"] == BUNDLE_NAME
        )
        bundle = run_dir / BUNDLE_NAME
        self.assertEqual(
            committed,
            _zip_file_root(bundle),
            "fixture: the sealed manifest commits the bundle's file-bytes hash",
        )
        # Post-seal tamper: the manifest is NOT resealed — exactly the case
        # the anchor exists to catch.
        bundle.write_bytes(bundle.read_bytes() + b"post-seal tamper")
        tampered = _zip_file_root(bundle)
        self.assertNotEqual(
            tampered, committed, "fixture: the tamper must change the hash"
        )
        self._restart()
        rec = chamber.STATE.get(run_id)
        self.assertEqual(
            rec.requester_bundle_root,
            committed,
            "legacy hydration must take the anchor from the hash COMMITTED "
            "for requester_bundle.zip in court_manifest.json — the seal "
            "already authenticated it",
        )
        self.assertNotEqual(
            rec.requester_bundle_root,
            tampered,
            "hydration hashed the current (tampered) bundle bytes: that "
            "mints a trust anchor for bytes finalize never sealed",
        )


class SealedCourtImmutabilityTests(_ChamberGlobalsMixin, unittest.TestCase):
    """Once _write_manifest seals the court, ANY later byte in run_dir is
    tampering by definition — including chamber's own bookkeeping."""

    def test_process_run_exception_seals_error_status_inside_the_court(self) -> None:
        """A worker exception must land status="error" on the record BEFORE
        CourtFileWriter.finalize seals the court, so the sealed record.json
        is exact and no post-seal write ever happens. Driven through the
        production wiring (owner_loop -> process_run -> finally: finalize);
        today owner_loop patches status=error in AFTER the seal, breaking
        the court's exact-byte integrity."""
        old_automatic = chamber.AUTOMATIC
        old_run_codex = chamber.run_codex
        rec = _record("errseal", "queued")
        rec.status = "queued"

        def exploding_run_codex(*args, **kwargs):
            raise RuntimeError("simulated worker crash mid-run")

        try:
            chamber.AUTOMATIC = True  # no owner prompts may block the loop
            chamber.run_codex = exploding_run_codex
            with chamber.STATE.lock:
                chamber.STATE.records[rec.run_id] = rec
            chamber.save_record(rec)
            with contextlib.redirect_stdout(io.StringIO()):
                chamber.STATE.q.put(rec.run_id)
                worker = threading.Thread(target=chamber.owner_loop, daemon=True)
                worker.start()
                chamber.STATE.q.join()
                chamber.STATE.shutdown = True
                worker.join(timeout=30)
            self.assertFalse(worker.is_alive(), "owner_loop did not stop")
        finally:
            chamber.AUTOMATIC = old_automatic
            chamber.run_codex = old_run_codex

        final = chamber.STATE.get(rec.run_id)
        self.assertEqual(final.status, "error")
        run_dir = chamber.RUNS_DIR / rec.run_id
        self.assertTrue(
            (run_dir / check_court_file.COURT_MANIFEST_NAME).exists(),
            "the errored run's court must still be sealed",
        )
        sealed_record = json.loads(
            (run_dir / "record.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sealed_record.get("status"),
            "error",
            "record.json inside the court must carry status=error",
        )
        self._assert_court_integrity(
            run_dir,
            "status=error must be decided BEFORE finalize seals the court; "
            "a post-seal record.json rewrite is tampering with the sealed "
            "court",
        )

    def test_add_followup_leaves_the_sealed_parent_court_intact(self) -> None:
        """The one safe drill-down is requested AFTER the parent court is
        sealed — the feature must work without writing into the sealed
        court. Today add_followup's save_record(parent) rewrites the sealed
        record.json."""
        run_id = "sealparent"
        run_dir, rec = self._production_court(
            run_id, "approved", interrupt_before_manifest=False
        )
        self._assert_court_integrity(run_dir, "fixture: parent court must be sealed")
        with chamber.STATE.lock:
            chamber.STATE.records[rec.run_id] = rec
        child, msg = chamber.STATE.add_followup(
            run_id,
            "counter_signal",
            task="fixture drill-down task",
            question="fixture drill-down question",
        )
        self.assertIsNotNone(child, f"the drill-down itself must still work: {msg}")
        self._assert_court_integrity(
            run_dir,
            "add_followup must not mutate the sealed parent court "
            "(record.json rewrite after _write_manifest breaks the seal)",
        )

    def test_finalize_refreshes_preexisting_record_json_inside_the_seal(self) -> None:
        """Positive control pinning the refresh seam: when record.json
        exists before finalize (the production shape), the sealed court
        carries the finalize-only fields — anchor and charged accounting —
        and remains byte-exact."""
        run_id = "sealrefresh"
        run_dir, rec = self._production_court(
            run_id, "approved", interrupt_before_manifest=False
        )
        sealed_record = json.loads(
            (run_dir / "record.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sealed_record.get("requester_bundle_root"),
            _zip_file_root(run_dir / BUNDLE_NAME),
        )
        self.assertEqual(
            sealed_record.get("receipt_accounting"), rec.receipt_accounting
        )
        self.assertTrue(sealed_record.get("receipt_accounting"))
        self._assert_court_integrity(
            run_dir, "the refreshed record.json must be covered by the seal"
        )


class StaleSealTmpTests(_LifetimeIsolationMixin, unittest.TestCase):
    """The seal is published atomically via a fixed tmp name; a crashed
    earlier attempt leaves that tmp in run_dir. A retry must clear it BEFORE
    inventorying the court — otherwise the sealed manifest lists a file the
    atomic rename then removes, and the sealer has minted an invalid seal."""

    def test_finalize_seals_cleanly_over_a_stale_manifest_tmp(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_bundle_"))
        try:
            rec = _record("staletmp", "approved")
            run_dir = root / rec.run_id
            writer = chamber.CourtFileWriter(rec, run_dir)
            (run_dir / "approved_public_artifact.json").write_bytes(
                APPROVED_ARTIFACT_BYTES
            )
            stale = run_dir / (check_court_file.COURT_MANIFEST_NAME + ".tmp")
            stale.write_text('{"torn": true}\n', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                writer.finalize(rec)
            self.assertFalse(
                stale.exists(), "the stale tmp must not survive the seal"
            )
            err = io.StringIO()
            try:
                with contextlib.redirect_stderr(err):
                    check_court_file.verify_exact_integrity(run_dir, None)
            except SystemExit:
                self.fail(
                    "a stale court_manifest.json.tmp poisoned the retry seal: "
                    + err.getvalue().strip()
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)


class CheckerSnapshotTests(_BundleFixtureMixin, unittest.TestCase):
    """The checker's verdict must be computed over ONE immutable byte
    snapshot: hash-the-path then reopen-the-path is a TOCTOU seam where the
    parsed bytes are not the authenticated bytes."""

    def test_checker_hashes_and_parses_one_immutable_snapshot(self) -> None:
        """Swap the file at the path right after its first read (the root
        hash). Today the checker reopens the path and parses the SWAPPED
        zip — proof that its verdict is not a function of the authenticated
        bytes. A single-snapshot checker parses what it hashed and accepts
        the clean bundle."""
        real_read_bytes = pathlib.Path.read_bytes
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            zip_path, anchor = self._build(root, self._clean_members())
            hostile_path = root / "hostile.zip"
            _write_zip(
                hostile_path,
                self._clean_members() + [("planted_disclosure.txt", b"smuggled\n")],
            )
            hostile_bytes = hostile_path.read_bytes()
            target = os.fspath(zip_path)
            fired = {"swapped": False}

            def racing_read_bytes(path_self):
                data = real_read_bytes(path_self)
                if not fired["swapped"] and os.fspath(path_self) == target:
                    fired["swapped"] = True
                    with open(target, "wb") as fh:
                        fh.write(hostile_bytes)
                return data

            checker = _checker()
            argv = [
                "check_requester_bundle.py",
                str(zip_path),
                "--expect-bundle-root",
                anchor,
            ]
            pathlib.Path.read_bytes = racing_read_bytes
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    code = checker.main(argv)
            except SystemExit:
                self.fail(
                    "the checker parsed bytes it never authenticated: the "
                    "path was swapped between the root hash and the zip "
                    "parse, and the verdict followed the swapped file. Hash "
                    "and parse ONE immutable byte snapshot."
                )
            finally:
                pathlib.Path.read_bytes = real_read_bytes
            self.assertEqual(code, 0)
            self.assertTrue(
                fired["swapped"],
                "fixture: the swap hook must have fired on the first read",
            )
        finally:
            pathlib.Path.read_bytes = real_read_bytes
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_duplicate_member_names_with_recomputed_root(self) -> None:
        """Anti-vacuity companion to the original duplicate test (which
        supplies the ORIGINAL zip's root, so the root check convicts before
        duplicate detection is ever reached). Here the root is recomputed
        over the duplicated zip, so ONLY duplicate detection can convict."""
        root = Path(tempfile.mkdtemp(prefix="chamber_chk_"))
        try:
            members = self._clean_members()
            receipt = next(m for m in members if m[0] == "receipt.json")
            zip_path = root / "dup.zip"
            _write_zip(zip_path, members + [receipt])
            self._assert_rejected(zip_path, _zip_file_root(zip_path))
        finally:
            shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# Live-smoke regressions on the owner surface (observed 2026-07-10 on the
# run-4 deployment). RED by design until chamber.py is fixed. Driven through
# the PRODUCTION Handler via _FakeSocket — no live server, no network.
#
# Leak: chamber runs under launchd with stderr captured to a log file, and
# Handler.log_message writes BaseHTTPRequestHandler.log_request's requestline
# verbatim — so every GET /owner?owner=SECRET deposits the live owner
# approval capability into a 0644 log. Logs must keep method/path/status and
# drop the query.
#
# Copy: the owner dashboard unconditionally claims "Automatic clean-path
# mode is ON ..." even when CHAMBER_AUTOMATIC=0 (the run-4 rendered contract
# pins CHAMBER_AUTOMATIC=0), telling the owner releases self-publish when
# they in fact wait for manual approval.
# ---------------------------------------------------------------------------

OWNER_LOG_SECRET = "ownersecret-0f9c2a41d8b7e6a5c4d3b2a19"


class OwnerSurfaceRegressionTests(_ChamberGlobalsMixin, unittest.TestCase):
    def _owner_get(self, *, automatic: bool) -> Tuple[int, str, str]:
        """GET /owner?owner=<secret> through the production Handler with the
        owner token pinned and AUTOMATIC forced. Returns (status, body,
        stderr) — stderr is exactly what launchd would capture to the log."""
        raw = (
            f"GET /owner?owner={OWNER_LOG_SECRET} HTTP/1.1\r\n"
            "Host: chamber.test\r\nConnection: close\r\n\r\n"
        ).encode("ascii")
        sock = _FakeSocket(raw)
        err = io.StringIO()
        with mock.patch.object(chamber, "OWNER_TOKEN", OWNER_LOG_SECRET), \
                mock.patch.object(chamber, "AUTOMATIC", automatic), \
                contextlib.redirect_stderr(err):
            chamber.Handler(sock, ("127.0.0.1", 0), None)
        response = bytes(sock.captured)
        head, sep, body = response.partition(b"\r\n\r\n")
        self.assertTrue(sep, f"malformed HTTP response: {response!r}")
        status = int(head.split(b"\r\n", 1)[0].split()[1])
        return status, body.decode("utf-8", errors="replace"), err.getvalue()

    def test_request_log_never_carries_owner_query_or_secret(self) -> None:
        status, _body, logged = self._owner_get(automatic=True)
        self.assertEqual(
            status, 200, "fixture: a valid owner token must reach the dashboard"
        )
        self.assertNotIn(
            OWNER_LOG_SECRET, logged,
            "GET /owner?owner=<secret> writes the owner token to stderr via "
            "log_request(requestline); under launchd that stderr is a log "
            "file, so any log reader steals the live approval capability",
        )
        self.assertNotIn(
            "owner=", logged,
            "the query must be redacted from request logs entirely — no "
            "param names or values, this token or any future one",
        )
        # Redaction must not lobotomize the log: keep the operational signal.
        self.assertIn("GET", logged, "request log must retain the method")
        self.assertIn("/owner", logged, "request log must retain the path")
        self.assertRegex(logged, r"\b200\b", "request log must retain the status")

    def test_owner_dashboard_reports_manual_mode_when_automatic_off(self) -> None:
        status, body, _logged = self._owner_get(automatic=False)
        self.assertEqual(status, 200)
        self.assertNotIn(
            "Automatic clean-path mode is ON", body,
            "with CHAMBER_AUTOMATIC=0 the dashboard must not claim automatic "
            "mode is ON — the owner reads this line to know whether releases "
            "wait for their approval",
        )
        self.assertIn(
            "manual", body.lower(),
            "with CHAMBER_AUTOMATIC=0 the dashboard must state that run and "
            "release publication wait for MANUAL owner approval",
        )

    def test_owner_dashboard_still_reports_automatic_mode_when_on(self) -> None:
        # Positive control: the fix must branch on the mode, not delete the
        # mode line.
        status, body, _logged = self._owner_get(automatic=True)
        self.assertEqual(status, 200)
        self.assertIn(
            "automatic", body.lower(),
            "with CHAMBER_AUTOMATIC=1 the dashboard still describes the "
            "automatic clean-path mode",
        )


# ---------------------------------------------------------------------------
# Independent finalization review, actionable finding A: SEALED IMPLIES
# TERMINAL must hold even when the error-REPORTING path itself faults.
# process_run's except-block prints the traceback BEFORE it decides
# status="error"; if that print raises (BrokenPipeError — launchd log pipe
# gone — is the live shape), the status decision is skipped while the
# finally-block still seals the court, minting an immutable court whose
# record.json says the run is still in flight. KeyboardInterrupt (a
# BaseException the except-chain deliberately re-raises) reaches the same
# finally-seal with the same nonterminal record. The seal is the last writer:
# finalize must backstop any nonterminal record to a terminal error BEFORE
# sealing. All tests drive the production code directly — no threads, no
# queue joins, nothing to hang.
# ---------------------------------------------------------------------------


class SealedImpliesTerminalTests(_ChamberGlobalsMixin, unittest.TestCase):
    def _sealed_record(self, run_dir: Path) -> Dict:
        manifest = run_dir / check_court_file.COURT_MANIFEST_NAME
        self.assertTrue(
            manifest.exists(),
            "a crashed run's court must still be sealed (pinned elsewhere); "
            "without the seal this test has nothing to inspect",
        )
        return json.loads((run_dir / "record.json").read_text(encoding="utf-8"))

    def _enqueue_production_record(self, run_id: str) -> chamber.RunRecord:
        rec = _record(run_id, "queued")
        with chamber.STATE.lock:
            chamber.STATE.records[rec.run_id] = rec
        with contextlib.redirect_stdout(io.StringIO()):
            chamber.save_record(rec)
        return rec

    def test_broken_pipe_during_error_reporting_still_seals_terminal_error(self) -> None:
        rec = self._enqueue_production_record("brokenpipe")

        def exploding_run_codex(*args, **kwargs):
            raise RuntimeError("simulated worker crash mid-run")

        def flaky_print(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            if "Traceback" in text or "simulated worker crash" in text:
                raise BrokenPipeError("stderr pipe gone under launchd")
            # every other print in the window is swallowed quietly

        with mock.patch.object(chamber, "run_codex", exploding_run_codex), \
                mock.patch.object(chamber, "AUTOMATIC", True), \
                mock.patch.object(chamber, "print", flaky_print, create=True), \
                contextlib.redirect_stdout(io.StringIO()):
            try:
                chamber.process_run(rec.run_id)
            except BrokenPipeError:
                pass  # the escape is owner_loop's problem; the court must already be safe

        run_dir = chamber.RUNS_DIR / rec.run_id
        sealed = self._sealed_record(run_dir)
        self.assertEqual(
            sealed.get("status"),
            "error",
            "the traceback print raised BrokenPipeError before the "
            "status='error' decision, and the finally-seal then froze a "
            "nonterminal record.json: finalize must backstop the record to "
            "terminal error before sealing",
        )
        # No sealed-bytes / hydrated-memory contradiction after a restart.
        self._restart()
        hydrated = chamber.STATE.get(rec.run_id)
        self.assertEqual(
            hydrated.status,
            sealed.get("status"),
            "hydrated status must equal the sealed record.json status — a "
            "sealed-nonterminal court forces load_saved_records into an "
            "in-memory error it can never persist (save_record refuses "
            "post-seal writes)",
        )
        self._assert_court_integrity(
            run_dir, "the sealed court must stay byte-exact through restart"
        )

    def test_keyboard_interrupt_escape_still_seals_terminal_error(self) -> None:
        rec = self._enqueue_production_record("kbdescape")

        def interrupted_run_codex(*args, **kwargs):
            raise KeyboardInterrupt

        with mock.patch.object(chamber, "run_codex", interrupted_run_codex), \
                mock.patch.object(chamber, "AUTOMATIC", True), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                # Direct call: the BaseException must still propagate (the
                # operator's Ctrl-C is not swallowed) — and nothing hangs.
                chamber.process_run(rec.run_id)

        sealed = self._sealed_record(chamber.RUNS_DIR / rec.run_id)
        self.assertEqual(
            sealed.get("status"),
            "error",
            "KeyboardInterrupt bypasses the except-Exception error decision "
            "but not the finally-seal: the sealed record.json must still be "
            "terminal error, not a frozen in-flight status",
        )

    def test_finalize_backstops_a_nonterminal_record_to_error(self) -> None:
        # The seam pinned directly: finalize is the LAST writer inside the
        # seal, so it is the only place that can guarantee sealed==terminal.
        rec = _record("backstop", "running_worker")
        run_dir = chamber.RUNS_DIR / rec.run_id
        with contextlib.redirect_stdout(io.StringIO()):
            chamber.save_record(rec)  # production shape: record.json precedes finalize
            writer = chamber.CourtFileWriter(rec, run_dir)
            writer.finalize(rec)
        sealed = self._sealed_record(run_dir)
        self.assertEqual(
            sealed.get("status"),
            "error",
            "finalize sealed a nonterminal record verbatim: any rec.status "
            "outside {approved, rejected, error} at seal time must be "
            "backstopped to error inside the seal",
        )
        self.assertEqual(
            rec.status,
            "error",
            "the in-memory record must carry the same backstopped status "
            "as the sealed bytes",
        )


# ---------------------------------------------------------------------------
# Pre-redeploy operational tranche (test-only). Under run4, chamber runs
# supervised by launchd: stdout is a NON-TTY log file, restarts are routine,
# and the state dir accretes history. Two live risks, one adjacent seam:
#   (1) main()'s startup banner prints the raw OWNER_TOKEN and PASSCODE —
#       every supervised restart deposits both live credentials into the
#       out log. The banner must withhold secret values and direct the
#       operator to the explicit ask (run4 show-owner-url / the mode-0600
#       secrets file) instead.
#   (2) load_saved_records raises on the first corrupt/torn record.json,
#       bricking startup for every OTHER court on disk. One torn file must
#       be warned about and skipped; its neighbors must still hydrate.
#   (3) owner_loop's catch prints the traceback BEFORE persisting
#       status="error" — the same fallible-reporting inversion process_run
#       had: a BrokenPipeError on that print loses the error verdict.
# ---------------------------------------------------------------------------

BANNER_OWNER_SENTINEL = "ownertok-banner-3f81c2d94ab07e65"
BANNER_PASSCODE_SENTINEL = "passcode-banner-91d4e7a2c8b3f650"


class _ImmediateFakeServer:
    """ThreadingHTTPServer stand-in: binds nothing, serves nothing."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def serve_forever(self) -> None:
        return

    def shutdown(self) -> None:
        return


class StartupOperationalTests(_ChamberGlobalsMixin, unittest.TestCase):
    def test_startup_banner_withholds_secrets_on_non_tty_stdout(self) -> None:
        out = io.StringIO()  # isatty() False — exactly launchd's stdout shape
        self.assertFalse(out.isatty(), "fixture: captured stdout must be non-TTY")
        with mock.patch.object(chamber, "preflight_self_check", lambda: None), \
                mock.patch.object(chamber, "ThreadingHTTPServer", _ImmediateFakeServer), \
                mock.patch.object(chamber.signal, "signal", lambda *a: None), \
                mock.patch.object(chamber, "owner_loop", lambda: None), \
                mock.patch.object(chamber, "OWNER_TOKEN", BANNER_OWNER_SENTINEL), \
                mock.patch.object(chamber, "PASSCODE", BANNER_PASSCODE_SENTINEL), \
                contextlib.redirect_stdout(out):
            code = chamber.main()
        self.assertEqual(code, 0, "fixture: mocked main() must exit cleanly")
        banner = out.getvalue()
        self.assertIn(
            "running", banner, "fixture: the banner must actually have printed"
        )
        self.assertNotIn(
            BANNER_OWNER_SENTINEL, banner,
            "the startup banner prints the raw OWNER_TOKEN: under launchd "
            "every supervised restart deposits the live approval capability "
            "into run4.app.out.log",
        )
        self.assertNotIn(
            BANNER_PASSCODE_SENTINEL, banner,
            "the startup banner prints the raw PASSCODE: same log, same "
            "leak, second credential",
        )
        self.assertTrue(
            "show-owner-url" in banner or "secrets" in banner.lower(),
            "withholding the values must not strand the operator: the "
            "banner must point at the explicit ask (run4 show-owner-url / "
            "the mode-0600 secrets file)",
        )

    def test_one_torn_record_json_does_not_brick_hydration(self) -> None:
        valid = _record("validrec", "approved")
        with contextlib.redirect_stdout(io.StringIO()):
            chamber.save_record(valid)
        torn_dir = chamber.RUNS_DIR / "cortorn"
        torn_dir.mkdir(parents=True)
        torn = b'{"run_id": "cortorn", "created_at": "2026-07-1'  # torn mid-write
        (torn_dir / "record.json").write_bytes(torn)
        with self.assertRaises(ValueError):
            json.loads(torn)  # fixture: the file is genuinely unparseable
        out_buf, err_buf = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out_buf), \
                    contextlib.redirect_stderr(err_buf):
                chamber.load_saved_records()
        except Exception as exc:
            self.fail(
                "a single torn record.json bricked startup hydration — every "
                f"other court on disk becomes unreachable: {exc!r}"
            )
        self.assertIsNotNone(
            chamber.STATE.get("validrec"),
            "the adjacent valid record must still hydrate",
        )
        self.assertIsNone(
            chamber.STATE.get("cortorn"),
            "the torn record must be skipped, not half-hydrated",
        )
        combined = out_buf.getvalue() + err_buf.getvalue()
        self.assertIn(
            "cortorn", combined,
            "the skip must be warned with the offending run id/path — a "
            "silent skip hides a court the owner believes exists",
        )

    def test_owner_loop_persists_error_before_fallible_print(self) -> None:
        rec = _record("looppersist", "queued")
        with chamber.STATE.lock:
            chamber.STATE.records[rec.run_id] = rec

        def exploding_process_run(run_id):
            raise RuntimeError("simulated dispatch crash")

        def flaky_print(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            if "Traceback" in text or "simulated dispatch crash" in text:
                raise BrokenPipeError("stderr pipe gone under launchd")

        with mock.patch.object(chamber, "process_run", exploding_process_run), \
                mock.patch.object(chamber, "print", flaky_print, create=True):
            chamber.STATE.q.put(rec.run_id)
            worker = threading.Thread(target=chamber.owner_loop, daemon=True)
            worker.start()
            chamber.STATE.q.join()
            chamber.STATE.shutdown = True
            worker.join(timeout=30)
        self.assertFalse(worker.is_alive(), "owner_loop must not hang")
        self.assertEqual(
            chamber.STATE.get(rec.run_id).status,
            "error",
            "owner_loop's catch prints the traceback BEFORE persisting "
            "status='error': when that print raises (BrokenPipeError under "
            "launchd), the error verdict is lost and the record stays "
            "in-flight forever",
        )


# ---------------------------------------------------------------------------
# Zero-tool context-packet cutover (live finding 2026-07-10): process-tree
# inspection during the first real Run 4 proved pooled Codex inherited Pencil
# MCP, node_repl, Computer Use, and code-mode-host children from user config,
# and the read-only sandbox bounds WRITES, not reads. The bound must come
# from the command line (no user config, no rules, every tool class
# disabled) and from the input (exactly one owner-approved <=256KiB UTF-8
# packet embedded in the prompt — no path, no expansion tool).
# ---------------------------------------------------------------------------


class ZeroToolContractTests(_LifetimeIsolationMixin, unittest.TestCase):
    def _packet(self) -> Path:
        return self._packet_workspace / "approved-context.txt"

    def _repoint(self, path: Path) -> None:
        chamber.CONTEXT_PACKET_PATH_RAW = str(path)
        chamber._CONTEXT_PACKET_TEXT = None
        chamber._CONTEXT_PACKET_SHA256 = ""

    def _cmd(self) -> List[str]:
        return chamber.codex_base_cmd(
            cwd=self._packet_workspace,
            sandbox="read-only",
            model="",
            output_path=self._packet_workspace / "out.txt",
            schema_path=None,
        )

    # -- command line: no inherited capability --------------------------------

    def test_codex_command_ignores_user_config_and_rules(self) -> None:
        cmd = self._cmd()
        self.assertIn(
            "--ignore-user-config", cmd,
            "Pencil MCP and friends arrived from user config; every Codex "
            "call must refuse to load it",
        )
        self.assertIn("--ignore-rules", cmd)

    def test_codex_command_disables_every_tool_class(self) -> None:
        cmd = self._cmd()
        disabled = {cmd[i + 1] for i, a in enumerate(cmd[:-1]) if a == "--disable"}
        for feature in (
            "shell_tool",
            "unified_exec",
            "apps",
            "plugins",
            "browser_use",
            "computer_use",
            "code_mode_host",
            "image_generation",
            "multi_agent",
            "hooks",
            "workspace_dependencies",
        ):
            self.assertIn(feature, disabled, f"--disable {feature} is required")
        overrides = {cmd[i + 1] for i, a in enumerate(cmd[:-1]) if a == "-c"}
        self.assertIn(
            "mcp_servers={}", overrides,
            "the root MCP server table must be emptied — --disable alone "
            "does not unregister configured servers",
        )
        self.assertIn("plugins={}", overrides)
        self.assertIn('web_search="disabled"', overrides)

    # -- input: exactly one bounded packet -------------------------------------

    def test_context_packet_rejected_outside_workspace(self) -> None:
        outside = Path(tempfile.mkdtemp(prefix="chamber_outside_"))
        self.addCleanup(shutil.rmtree, outside, True)
        stray = outside / "approved-context.txt"
        stray.write_text("outside the bounded workspace\n", encoding="utf-8")
        self._repoint(stray)
        with self.assertRaises(SystemExit):
            chamber.context_packet_text()

    def test_context_packet_symlink_escape_rejected(self) -> None:
        outside = Path(tempfile.mkdtemp(prefix="chamber_target_"))
        self.addCleanup(shutil.rmtree, outside, True)
        target = outside / "real.txt"
        target.write_text("private bytes beyond the boundary\n", encoding="utf-8")
        link = self._packet_workspace / "escape.txt"
        os.symlink(target, link)
        self._repoint(link)
        with self.assertRaises(SystemExit):
            chamber.context_packet_text()

    def test_context_packet_rejects_non_utf8_empty_and_oversize(self) -> None:
        packet = self._packet()
        packet.write_bytes(b"\xff\xfe not utf-8")
        self._repoint(packet)
        with self.assertRaises(SystemExit):
            chamber.context_packet_text()
        packet.write_text("   \n", encoding="utf-8")
        self._repoint(packet)
        with self.assertRaises(SystemExit):
            chamber.context_packet_text()
        packet.write_text("x" * 32, encoding="utf-8")
        self._repoint(packet)
        with mock.patch.object(chamber, "CONTEXT_PACKET_MAX_BYTES", 16):
            with self.assertRaises(SystemExit):
                chamber.context_packet_text()

    def test_context_packet_bytes_cached_immutable(self) -> None:
        first = chamber.context_packet_text()
        self.assertEqual(first, CONTEXT_PACKET_SENTINEL)
        self._packet().write_text("tampered after first read\n", encoding="utf-8")
        self.assertEqual(
            chamber.context_packet_text(), first,
            "the packet is read once and cached: post-startup file edits "
            "must not reach any later model call",
        )

    # -- prompt: packet embedded, zero-tool contract, no paths -----------------

    def test_worker_prompt_embeds_packet_and_names_no_paths(self) -> None:
        run_dir = Path(tempfile.mkdtemp(prefix="chamber_rundir_"))
        self.addCleanup(shutil.rmtree, run_dir, True)
        pre = {"verdict": "ALLOW", "risk": "low"}
        prompt = chamber.build_worker_prompt("bounded task text", 64, pre, pre, run_dir)
        self.assertIn(
            CONTEXT_PACKET_SENTINEL.strip(), prompt,
            "the packet bytes themselves must be embedded in the prompt",
        )
        self.assertIn(
            "Every optional filesystem, shell, MCP, plugin, app, browser, "
            "network, search, subagent, and image tool class is disabled, "
            "and your process is OS-confined",
            prompt,
            "the prompt must state the honest boundary — capability "
            "OS-confined, not falsely absent",
        )
        self.assertNotIn(
            str(run_dir), prompt,
            "the worker has no tools; a run-dir path in the prompt is a "
            "leftover capability claim",
        )
        self.assertNotIn(str(self._packet_workspace), prompt)

    # -- receipt + env recipe: honest disclosure --------------------------------

    def test_env_recipe_and_receipt_disclose_remote_provider(self) -> None:
        rec = _record("recipepin", "approved")
        root = Path(tempfile.mkdtemp(prefix="chamber_recipe_"))
        self.addCleanup(shutil.rmtree, root, True)
        with mock.patch.object(chamber, "FAKE_CODEX", False), \
                contextlib.redirect_stdout(io.StringIO()):
            writer = chamber.CourtFileWriter(rec, root / rec.run_id)
        recipe = writer.env_recipe
        packet_bytes = chamber.context_packet_text().encode("utf-8")
        self.assertEqual(len(recipe["tools"]), 1, "exactly one model_call tool grant")
        self.assertEqual(recipe["tools"][0]["kind"], "model_call")
        self.assertEqual(recipe["resources"]["maxReadBytes"], len(packet_bytes))
        self.assertEqual(recipe["resources"]["maxScratchBytes"], 0)
        self.assertEqual(
            # sha256_bytes prefixes "sha256:"; the recipe mount hash is bare hex
            recipe["mounts"][0]["globHash"],
            chamber.sha256_bytes(packet_bytes).split(":", 1)[1],
            "the mount must commit to the packet's content hash",
        )
        self.assertTrue(
            recipe["network"]["rawPrivateDataMayTransit"],
            "the recipe must state the provider receives the packet — "
            "claiming otherwise is success-shaped privacy",
        )
        receipt = chamber.release_receipt(_record("receiptpin", "approved"), structured=True)
        joined = " ".join(receipt)
        self.assertIn("remote model provider", joined)
        self.assertIn("bounded", joined)


# ---------------------------------------------------------------------------
# Native launcher boundary (live finding 2026-07-10 #2): with user config
# ignored and every optional feature disabled, the pooled Codex child could
# still open any pathname readable by this user. The bound must come from the
# OS: run_codex launches the real NATIVE Codex under /usr/bin/sandbox-exec
# with a generated deny-by-default Seatbelt profile. These tests are the
# executable contracts for that boundary.
# ---------------------------------------------------------------------------

_SANDBOX_EXEC_AVAILABLE = sys.platform == "darwin" and os.access("/usr/bin/sandbox-exec", os.X_OK)


class SeatbeltConfinementTests(_LifetimeIsolationMixin, unittest.TestCase):
    def _tmpdir(self, prefix: str) -> Path:
        # Seatbelt matches RESOLVED vnode paths, so fixtures must live at
        # their realpath (tempfile hands out /var/... aliases of /private/var).
        made = Path(tempfile.mkdtemp(prefix=prefix))
        self.addCleanup(shutil.rmtree, made, True)
        return Path(os.path.realpath(made))

    def _cat_profile(self, allowed_root: Path) -> Path:
        profile = chamber.seatbelt_profile(
            executable=Path("/bin/cat"),
            install_root=allowed_root,
            invocation_roots=[allowed_root],
            loopback_port=None,
        )
        profile_path = allowed_root / "profile.sb"
        profile_path.write_text(profile, encoding="utf-8")
        return profile_path

    def _sandboxed_cat(self, profile_path: Path, target: Path) -> "subprocess.CompletedProcess[str]":
        return subprocess.run(
            ["/usr/bin/sandbox-exec", "-f", str(profile_path), "/bin/cat", str(target)],
            capture_output=True, text=True, timeout=60,
        )

    # -- positive control: the exact wrapper permits allowlisted reads --------

    @unittest.skipUnless(_SANDBOX_EXEC_AVAILABLE, "requires macOS sandbox-exec")
    def test_wrapper_reads_allowlisted_fixture(self) -> None:
        root = self._tmpdir("chamber_sb_ok_")
        fixture = root / "fixture.txt"
        fixture.write_text("non-sensitive allowlisted fixture\n", encoding="utf-8")
        proc = self._sandboxed_cat(self._cat_profile(root), fixture)
        self.assertEqual(
            proc.returncode, 0,
            f"positive control failed — a broken profile makes every denial "
            f"test vacuous (stderr: {proc.stderr!r})",
        )
        self.assertIn("non-sensitive allowlisted fixture", proc.stdout)

    # -- denial: a fresh random sentinel outside every allowlisted root -------

    @unittest.skipUnless(_SANDBOX_EXEC_AVAILABLE, "requires macOS sandbox-exec")
    def test_wrapper_denies_outside_sentinel_and_leaks_no_bytes(self) -> None:
        root = self._tmpdir("chamber_sb_root_")
        outside = self._tmpdir("chamber_sb_outside_")
        sentinel_value = secrets.token_hex(16)
        sentinel = outside / f"sentinel_{secrets.token_hex(4)}.txt"
        sentinel.write_text(sentinel_value, encoding="utf-8")
        proc = self._sandboxed_cat(self._cat_profile(root), sentinel)
        self.assertNotEqual(proc.returncode, 0, "outside-root read must be denied")
        self.assertNotIn(sentinel_value, proc.stdout)
        self.assertNotIn(sentinel_value, proc.stderr)

    @unittest.skipUnless(_SANDBOX_EXEC_AVAILABLE, "requires macOS sandbox-exec")
    def test_symlink_descendant_cannot_widen_root(self) -> None:
        root = self._tmpdir("chamber_sb_link_")
        outside = self._tmpdir("chamber_sb_target_")
        sentinel_value = secrets.token_hex(16)
        target = outside / "real.txt"
        target.write_text(sentinel_value, encoding="utf-8")
        link = root / "escape.txt"
        os.symlink(target, link)
        proc = self._sandboxed_cat(self._cat_profile(root), link)
        self.assertNotEqual(
            proc.returncode, 0,
            "a symlink planted inside an allowlisted root must not widen "
            "the boundary: Seatbelt evaluates the resolved target",
        )
        self.assertNotIn(sentinel_value, proc.stdout)
        self.assertNotIn(sentinel_value, proc.stderr)

    @unittest.skipUnless(_SANDBOX_EXEC_AVAILABLE, "requires macOS sandbox-exec")
    def test_profile_escapes_quoted_paths(self) -> None:
        parent = self._tmpdir("chamber_sb_q_")
        root = parent / 'evil"dir'
        root.mkdir()
        fixture = root / "fixture.txt"
        fixture.write_text("quoted-root fixture\n", encoding="utf-8")
        profile = chamber.seatbelt_profile(
            executable=Path("/bin/cat"),
            install_root=root,
            invocation_roots=[root],
            loopback_port=None,
        )
        self.assertIn('evil\\"dir', profile, "a double quote in a root must be escaped")
        profile_path = parent / "profile.sb"
        profile_path.write_text(profile, encoding="utf-8")
        proc = self._sandboxed_cat(profile_path, fixture)
        self.assertEqual(
            proc.returncode, 0,
            f"sandbox-exec must parse the escaped profile and allow the "
            f"quoted root (stderr: {proc.stderr!r})",
        )
        self.assertIn("quoted-root fixture", proc.stdout)

    # -- profile generation fail-closed ----------------------------------------

    def test_profile_rejects_widening_roots(self) -> None:
        with self.assertRaises(chamber.ConfinedLaunchError):
            chamber.seatbelt_profile(
                executable=Path("/bin/cat"),
                install_root=Path("/usr/lib"),
                invocation_roots=[Path("/")],
                loopback_port=None,
            )
        with self.assertRaises(chamber.ConfinedLaunchError):
            chamber.seatbelt_profile(
                executable=Path("/bin/cat"),
                install_root=Path("/usr/lib"),
                invocation_roots=[Path.home()],
                loopback_port=None,
            )
        with self.assertRaises(chamber.ConfinedLaunchError):
            # the workspace's PARENT contains the workspace: also refused
            chamber.seatbelt_profile(
                executable=Path("/bin/cat"),
                install_root=Path("/usr/lib"),
                invocation_roots=[chamber.WORKSPACE.parent],
                loopback_port=None,
            )
        with self.assertRaises(chamber.ConfinedLaunchError):
            chamber.seatbelt_profile(
                executable=Path("/bin/cat"),
                install_root=Path("/usr/lib"),
                invocation_roots=[self._packet_workspace],
                loopback_port=None,
            )

    def test_profile_rejects_bad_port_and_unescapable_path(self) -> None:
        root = self._tmpdir("chamber_sb_bad_")
        for port in (0, -1, 65536):
            with self.assertRaises(chamber.ConfinedLaunchError):
                chamber.seatbelt_profile(
                    executable=Path("/bin/cat"),
                    install_root=root,
                    invocation_roots=[root],
                    loopback_port=port,
                )
        with self.assertRaises(chamber.ConfinedLaunchError):
            chamber._sb_path(Path(str(root) + "\nevil"))

    def test_profile_never_names_workspace_or_packet(self) -> None:
        root = self._tmpdir("chamber_sb_clean_")
        profile = chamber.seatbelt_profile(
            executable=Path("/bin/cat"),
            install_root=root,
            invocation_roots=[root],
            loopback_port=4242,
        )
        self.assertNotIn(str(self._packet_workspace), profile)
        self.assertNotIn(str(chamber.WORKSPACE), profile)
        self.assertNotIn(chamber.CONTEXT_PACKET_PATH_RAW, profile)
        self.assertNotIn(str(chamber.CODEXPOOL_DIR), profile)
        self.assertIn('(remote ip "localhost:4242")', profile)
        self.assertIn("(deny default)", profile)

    # -- proxy record validation: fail closed ----------------------------------

    def test_proxy_record_fail_closed(self) -> None:
        missing = self._tmpdir("chamber_cxp_") / "port"
        with self.assertRaises(chamber.ConfinedLaunchError):
            chamber.read_cxp_proxy_record(missing)
        for bad in ("", "not json", "[1,2]", '{"port": "57097", "pid": 1}',
                    '{"port": 0, "pid": 1}', '{"port": 70000, "pid": 1}',
                    '{"port": true, "pid": 1}', '{"port": 57097}',
                    '{"port": 57097, "pid": -4}'):
            record = missing.parent / f"port_{abs(hash(bad))}"
            record.write_text(bad, encoding="utf-8")
            with self.assertRaises(chamber.ConfinedLaunchError, msg=f"must refuse {bad!r}"):
                chamber.read_cxp_proxy_record(record)
        alive_but_wrong = missing.parent / "port_wrong_identity"
        alive_but_wrong.write_text(json.dumps({"port": 57097, "pid": os.getpid()}), encoding="utf-8")
        with self.assertRaises(chamber.ConfinedLaunchError, msg="a live pid that is not the cxp proxy must be refused"):
            chamber.read_cxp_proxy_record(alive_but_wrong)
        dead = missing.parent / "port_dead_pid"
        dead.write_text(json.dumps({"port": 57097, "pid": os.getpid()}), encoding="utf-8")
        with mock.patch.object(chamber, "_pid_alive", return_value=False):
            with self.assertRaises(chamber.ConfinedLaunchError, msg="a dead proxy pid must be refused"):
                chamber.read_cxp_proxy_record(dead)

    def test_proxy_identity_matcher(self) -> None:
        self.assertTrue(chamber._is_cxp_proxy_command(
            "/usr/bin/python3 /Users/xyra/.codexpool/cxp-agent proxy"))
        self.assertFalse(chamber._is_cxp_proxy_command(""))
        self.assertFalse(chamber._is_cxp_proxy_command("sshd: xyra [priv]"))
        self.assertFalse(chamber._is_cxp_proxy_command(
            "/usr/bin/python3 /Users/xyra/.codexpool/cxp-agent status"))
        self.assertFalse(chamber._is_cxp_proxy_command(
            "/usr/bin/python3 /tmp/cxp-agent proxy"),
            "a cxp-agent named script OUTSIDE a codexpool dir is not the proxy")

    # -- placeholder login metadata: zero live credential material -------------

    def test_placeholder_home_contains_no_live_credentials(self) -> None:
        home = self._tmpdir("chamber_ph_") / "codex-home"
        chamber.write_placeholder_codex_home(home)
        auth_path = home / "auth.json"
        self.assertEqual(auth_path.stat().st_mode & 0o777, 0o600)
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        tokens = auth["tokens"]
        self.assertIsNone(auth["OPENAI_API_KEY"])
        self.assertEqual(tokens["access_token"], chamber.PLACEHOLDER_ACCESS_TOKEN)
        self.assertEqual(tokens["refresh_token"], chamber.PLACEHOLDER_REFRESH_TOKEN)
        self.assertEqual(tokens["account_id"], chamber.PLACEHOLDER_ACCOUNT_ID)
        header_b64, payload_b64, _sig = tokens["id_token"].split(".")
        pad = lambda s: s + "=" * (-len(s) % 4)  # noqa: E731
        import base64 as _b64
        header = json.loads(_b64.urlsafe_b64decode(pad(header_b64)))
        payload = json.loads(_b64.urlsafe_b64decode(pad(payload_b64)))
        self.assertEqual(header["alg"], "none", "the placeholder JWT must be unsigned")
        self.assertEqual(payload["sub"], chamber.PLACEHOLDER_SUBJECT)
        self.assertEqual(payload["email"], chamber.PLACEHOLDER_EMAIL)
        # Byte-equality law: every credential-shaped value is one of the fixed
        # placeholder constants — nothing read from the real ~/.codex or the
        # pool can appear here.
        for value in (tokens["access_token"], tokens["refresh_token"], tokens["account_id"]):
            self.assertIn("placeholder", value)

    # -- run_codex argv: sandbox-exec -> native codex, never the shim -----------

    def test_run_codex_argv_starts_sandbox_exec_then_native_codex(self) -> None:
        artifact_dir = self._tmpdir("chamber_argv_")
        fake_native = artifact_dir / "native-codex"
        fake_native.write_bytes(b"\xcf\xfa\xed\xfe fake mach-o")
        fake_native.chmod(0o755)
        captured: Dict[str, object] = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = list(cmd)
            captured["env"] = dict(kwargs.get("env") or {})
            launch_dirs = [p for p in artifact_dir.iterdir() if p.name.endswith(".launch")]
            captured["launch_exists"] = bool(launch_dirs)
            if launch_dirs:
                captured["auth_exists"] = (launch_dirs[0] / "codex-home" / "auth.json").exists()
            return subprocess.CompletedProcess(cmd, 0, stdout='{"verdict": "ALLOW"}', stderr="")

        with mock.patch.object(chamber, "read_cxp_proxy_record",
                               return_value=chamber.CxpProxyRecord(port=45678, pid=os.getpid())), \
                mock.patch.object(chamber, "resolve_native_codex", return_value=fake_native), \
                mock.patch.object(chamber.subprocess, "run", fake_run):
            result = chamber.run_codex(
                kind="preflight_a",
                prompt="contract probe",
                cwd=self._packet_workspace,
                sandbox="read-only",
                model="",
                timeout=30,
                schema={"type": "object"},
                out_prefix="argvpin",
                artifact_dir=artifact_dir,
            )
        cmd = captured["cmd"]
        self.assertEqual(cmd[0], "/usr/bin/sandbox-exec", "argv must START with sandbox-exec")
        self.assertEqual(cmd[1], "-f")
        self.assertEqual(cmd[3], str(fake_native), "the sandboxed target must be the native executable")
        self.assertEqual(cmd[4], "exec")
        joined = " ".join(cmd)
        self.assertNotIn(str(chamber.CODEXPOOL_DIR / "bin"), joined,
                         "the pooled shim must never appear in the child argv")
        self.assertIn("model_provider=codexpool", joined)
        self.assertIn("model_providers.codexpool.base_url=http://127.0.0.1:45678/backend-api/codex", joined)
        env = captured["env"]
        self.assertEqual(env["CODEX_REFRESH_TOKEN_URL_OVERRIDE"], "http://127.0.0.1:45678/oauth/token")
        self.assertIn(".launch", env["CODEX_HOME"], "CODEX_HOME must be the disposable per-invocation home")
        self.assertTrue(captured["launch_exists"], "launch material must exist during the child run")
        self.assertTrue(captured["auth_exists"], "placeholder auth must exist during the child run")
        self.assertTrue(result.ok, result.error)
        profile_path = artifact_dir / "argvpin.sandbox.sb"
        self.assertTrue(profile_path.exists(), "the generated profile persists as a receipt")
        profile_text = profile_path.read_text(encoding="utf-8")
        self.assertIn("(deny default)", profile_text)
        self.assertNotIn(str(self._packet_workspace), profile_text)
        self.assertFalse((artifact_dir / "argvpin.launch").exists(),
                         "per-invocation material must be cleaned after durable capture")

    def test_run_codex_fails_closed_without_proxy_record(self) -> None:
        artifact_dir = self._tmpdir("chamber_closed_")
        missing = artifact_dir / "no-such-port-record"

        def refuse(*args, **kwargs):
            raise AssertionError("no Codex process may start when the proxy record is invalid")

        with mock.patch.object(chamber, "CXP_PORT_RECORD_PATH", missing), \
                mock.patch.object(chamber.subprocess, "run", refuse):
            result = chamber.run_codex(
                kind="preflight_a",
                prompt="fail closed probe",
                cwd=self._packet_workspace,
                sandbox="read-only",
                model="",
                timeout=30,
                schema=None,
                out_prefix="closedpin",
                artifact_dir=artifact_dir,
            )
        self.assertFalse(result.ok)
        self.assertIn("confined launch refused", result.error)

    def test_resolve_native_codex_never_returns_shim(self) -> None:
        try:
            native = chamber.resolve_native_codex()
        except chamber.ConfinedLaunchError:
            self.skipTest("no native codex installed on this machine")
        shim_dir = os.path.realpath(str(chamber.CODEXPOOL_DIR / "bin"))
        self.assertNotEqual(os.path.realpath(str(native.parent)), shim_dir)
        with native.open("rb") as fh:
            self.assertIn(fh.read(4), chamber._MACHO_MAGICS,
                          "the resolved executable must be a native Mach-O binary, not a JS wrapper")


# ---------------------------------------------------------------------------
# Fixed-question mode (live public-front-door finding 2026-07-10 #3): the
# rendered launchd plist sets CHAMBER_FREEFORM_QUESTIONS=0 with one
# CHAMBER_ALLOWED_QUESTION, yet the front page still offered a freeform
# textarea and freeform copy. Fixed mode is an owner contract: the page shows
# exactly the approved question, POST /submit rejects anything else BEFORE a
# passcode use is consumed, and startup fails if fixed mode names no allowed
# question. These are behavior tests against the production Handler and
# preflight — not plist assertions.
# ---------------------------------------------------------------------------

FIXED_MODE_QUESTION = (
    "What does the approved-scope material suggest about verification rigor "
    "and follow-through?"
)


class FixedQuestionModeTests(_ChamberGlobalsMixin, unittest.TestCase):
    PASSCODE = "fixed-mode-test-passcode"

    def _enter_mode(self, *, freeform: bool, questions: Optional[List[str]] = None) -> None:
        questions = questions if questions is not None else [FIXED_MODE_QUESTION]
        presets = [(f"Owner-approved question {i}", q) for i, q in enumerate(questions, start=1)]
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(chamber, "FREEFORM_QUESTIONS", freeform))
        stack.enter_context(mock.patch.object(chamber, "DEMO_QUESTION_PRESETS", presets))
        stack.enter_context(mock.patch.object(chamber, "DEMO_QUESTIONS", list(questions)))
        stack.enter_context(mock.patch.object(chamber, "EXPLICIT_ALLOWED_QUESTIONS", True))
        stack.enter_context(mock.patch.object(chamber, "PASSCODE", self.PASSCODE))
        # PASSCODE_STATE_PATH is derived from STATE_DIR at import time, so the
        # _ChamberGlobalsMixin redirect does not cover it: repoint it too or a
        # consuming submission would write the REPO passcode state.
        stack.enter_context(mock.patch.object(
            chamber, "PASSCODE_STATE_PATH",
            self._globals_tmp / ".chamber" / "passcode_state.json",
        ))

    def _assert_no_consumption(self, context: str) -> None:
        self.assertEqual(chamber.STATE.use_count, 0, context)
        self.assertIsNone(chamber.STATE.first_use_ts, context)
        self.assertFalse(
            chamber.PASSCODE_STATE_PATH.exists(),
            f"{context}: no passcode state may be persisted for a rejected submission",
        )
        self.assertEqual(len(chamber.STATE.records), 0, f"{context}: no run may be created")

    # -- startup contract ------------------------------------------------------

    def test_startup_refuses_fixed_mode_without_explicit_allowed_question(self) -> None:
        self._enter_mode(freeform=False)
        with mock.patch.object(chamber, "EXPLICIT_ALLOWED_QUESTIONS", False):
            with self.assertRaises(SystemExit) as caught:
                with contextlib.redirect_stdout(io.StringIO()):
                    chamber.preflight_self_check()
        self.assertIn(
            "CHAMBER_ALLOWED_QUESTION", str(caught.exception),
            "the startup failure must name the missing knob",
        )

    def test_startup_allows_fixed_mode_with_explicit_allowed_question(self) -> None:
        self._enter_mode(freeform=False)
        with contextlib.redirect_stdout(io.StringIO()):
            chamber.preflight_self_check()  # must not raise

    # -- front page rendering ----------------------------------------------------

    def test_front_page_fixed_mode_shows_exact_question_and_no_freeform_surface(self) -> None:
        self._enter_mode(freeform=False)
        code, body = _http_get("/")
        self.assertEqual(code, 200)
        text = body.decode("utf-8", errors="replace")
        self.assertNotIn("<textarea", text, "fixed mode must not render a freeform textarea")
        self.assertNotIn("in your own words", text)
        self.assertNotIn("Freeform does not mean arbitrary control", text)
        self.assertIn(FIXED_MODE_QUESTION, text, "the exact approved question must be visible")
        self.assertIn(
            f'<input type="hidden" name="question" value="{FIXED_MODE_QUESTION}">', text,
            "the form must submit the exact approved question as a hidden value",
        )
        self.assertIn("only the owner-approved question", text)

    def test_front_page_fixed_mode_multiple_questions_render_fixed_choices(self) -> None:
        second = "What does the record suggest about reliability across ambiguous work?"
        self._enter_mode(freeform=False, questions=[FIXED_MODE_QUESTION, second])
        code, body = _http_get("/")
        self.assertEqual(code, 200)
        text = body.decode("utf-8", errors="replace")
        self.assertNotIn("<textarea", text)
        for question in (FIXED_MODE_QUESTION, second):
            self.assertIn(f'<input type="radio" name="question" value="{question}"', text)

    def test_front_page_freeform_mode_keeps_textarea(self) -> None:
        self._enter_mode(freeform=True)
        code, body = _http_get("/")
        self.assertEqual(code, 200)
        text = body.decode("utf-8", errors="replace")
        self.assertIn("<textarea", text)
        self.assertIn("in your own words", text)

    # -- submission contract ----------------------------------------------------

    def test_fixed_mode_mismatch_rejected_without_passcode_consumption(self) -> None:
        self._enter_mode(freeform=False)
        near_misses = {
            "different in-envelope question": (
                "What does the record suggest about Xyra's reliability under ambiguity?"
            ),
            "trailing punctuation stripped": FIXED_MODE_QUESTION.rstrip("?"),
            "case variant": FIXED_MODE_QUESTION.upper(),
        }
        for label, wrong in near_misses.items():
            with self.subTest(variant=label):
                code, body = _http_post(
                    "/submit", {"passcode": self.PASSCODE, "question": wrong}
                )
                self.assertEqual(
                    code, 400,
                    f"{label}: fixed mode accepts only the exact approved string",
                )
                self.assertIn(b"owner-approved question", body)
                self._assert_no_consumption(label)

    def test_fixed_mode_exact_question_runs_and_consumes_one_use(self) -> None:
        self._enter_mode(freeform=False)
        code, body = _http_post(
            "/submit", {"passcode": self.PASSCODE, "question": FIXED_MODE_QUESTION}
        )
        self.assertEqual(code, 200, body[:400])
        self.assertIn(b"/r/", body)
        self.assertEqual(chamber.STATE.use_count, 1, "exactly one passcode use is consumed")
        self.assertTrue(chamber.PASSCODE_STATE_PATH.exists())
        records = list(chamber.STATE.records.values())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].question, FIXED_MODE_QUESTION)
        self.assertEqual(records[0].status, "queued")

    def test_freeform_mode_still_accepts_bounded_question(self) -> None:
        self._enter_mode(freeform=True)
        question = "What does the record suggest about Xyra's reliability under ambiguity?"
        code, body = _http_post(
            "/submit", {"passcode": self.PASSCODE, "question": question}
        )
        self.assertEqual(code, 200, body[:400])
        self.assertEqual(chamber.STATE.use_count, 1)
        records = list(chamber.STATE.records.values())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].question, question)


if __name__ == "__main__":
    unittest.main()
