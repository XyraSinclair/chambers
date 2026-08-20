from __future__ import annotations

import contextlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from chambers import chamber
from chambers import check_court_file
from chambers.kernel import Ledger as KernelLedger


def _canonical_jsonl(rows):
    return "\n".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        for row in rows
    ) + "\n"


class _ContextPacketMixin:
    """Zero-tool cutover (2026-07-10): every CourtFileWriter embeds the
    owner-approved context packet. Provide a real packet, route the
    production loader at it, and pre-warm the cache exactly like
    preflight_self_check does at startup — a test that later reassigns
    chamber.WORKSPACE keeps the startup-cached packet, as a live run would."""

    def setUp(self) -> None:
        self._packet_workspace = Path(tempfile.mkdtemp(prefix="chamber_ws_")).resolve()
        packet = self._packet_workspace / "approved-context.txt"
        packet.write_text("Kernel-meter fixture context packet.\n", encoding="utf-8")
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
        chamber.context_packet_text()  # validate once, cache — startup-shaped

    def tearDown(self) -> None:
        for name, value in self._old_packet_globals.items():
            setattr(chamber, name, value)
        shutil.rmtree(self._packet_workspace, ignore_errors=True)


class ChamberKernelMeterTests(_ContextPacketMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        # Every CourtFileWriter charges the persistent lifetime ledger;
        # tests must NEVER write the real one (found polluted by exactly
        # this on 2026-07-05: six pytest-run entities in the repo state dir).
        self._lifetime_tmp = Path(tempfile.mkdtemp(prefix="chamber_lt_"))
        self._old_lifetime_path = chamber.LIFETIME_LEDGER_PATH
        chamber.LIFETIME_LEDGER_PATH = self._lifetime_tmp / "lifetime.jsonl"

    def tearDown(self) -> None:
        chamber.LIFETIME_LEDGER_PATH = self._old_lifetime_path
        shutil.rmtree(self._lifetime_tmp, ignore_errors=True)
        super().tearDown()

    def _record(self, run_id: str = "kerneltest") -> chamber.RunRecord:
        return chamber.RunRecord(
            run_id=run_id,
            created_at="2026-07-05T12:00:00+00:00",
            requester="tester",
            task=chamber.build_wrapped_task(chamber.DEFAULT_DEMO_QUESTION),
            max_words=64,
            question=chamber.DEFAULT_DEMO_QUESTION,
            status="approved",
            approved_answer="Judgment: bounded fake answer for the kernel-meter court file.",
            receipt=["release reviewed", "owner approved disclosure"],
        )

    def test_court_writer_emits_audit_clean_kernel_ledger_and_convicts_corruption(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_kernel_writer_"))
        try:
            rec = self._record()
            run_dir = root / rec.run_id
            writer = chamber.CourtFileWriter(rec, run_dir)
            writer.finalize(rec)

            ledger_path = run_dir / "charge_kernel_ledger.jsonl"
            self.assertTrue(ledger_path.exists())
            ledger = KernelLedger.from_jsonl(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger.audit(), [])
            self.assertGreater(ledger.event_count(), 2)
            self.assertEqual(ledger.to_jsonl(), ledger_path.read_text(encoding="utf-8"))

            emissions = [
                json.loads(line)
                for line in (run_dir / "emissions.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(emissions)
            self.assertTrue(all("chargedMillibits" in row["leakage"] for row in emissions))
            self.assertEqual(check_court_file.main(["check_court_file.py", str(run_dir)]), 0)

            rows = [
                json.loads(line)
                for line in ledger_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            charge = next(row for row in rows if row.get("kind") == "charge" and row.get("accepted") is True)
            charge["debit_mbits"] += 1
            corrupted = KernelLedger.from_jsonl(_canonical_jsonl(rows))
            findings = corrupted.audit()
            self.assertTrue(findings)
            self.assertTrue(any("I6" in finding for finding in findings), findings)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_fake_codex_end_to_end_run_persists_reauditable_kernel_ledger(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_kernel_e2e_"))
        old = {
            "RUNS_DIR": chamber.RUNS_DIR,
            "STATE_DIR": chamber.STATE_DIR,
            "PASSCODE_STATE_PATH": chamber.PASSCODE_STATE_PATH,
            "STATE": chamber.STATE,
            "WORKSPACE": chamber.WORKSPACE,
            "FAKE_CODEX": chamber.FAKE_CODEX,
            "AUTOMATIC": chamber.AUTOMATIC,
            "KEEP_RAW_ARTIFACTS": chamber.KEEP_RAW_ARTIFACTS,
        }
        try:
            chamber.STATE_DIR = root / ".chamber"
            chamber.RUNS_DIR = chamber.STATE_DIR / "runs"
            chamber.PASSCODE_STATE_PATH = chamber.STATE_DIR / "passcode_state.json"
            chamber.STATE = chamber.ChamberState()
            chamber.WORKSPACE = root / "workspace"
            chamber.WORKSPACE.mkdir(parents=True)
            chamber.FAKE_CODEX = True
            chamber.AUTOMATIC = True
            chamber.KEEP_RAW_ARTIFACTS = True
            chamber.RUNS_DIR.mkdir(parents=True)

            rec = self._record("fakee2e")
            rec.status = "queued"
            with chamber.STATE.lock:
                chamber.STATE.records[rec.run_id] = rec

            with (root / "stdout.txt").open("w", encoding="utf-8") as stdout:
                with contextlib.redirect_stdout(stdout):
                    chamber.process_run(rec.run_id)

            finished = chamber.STATE.get(rec.run_id)
            self.assertIsNotNone(finished)
            self.assertEqual(finished.status, "approved")
            run_dir = chamber.RUNS_DIR / rec.run_id
            ledger_text = (run_dir / "charge_kernel_ledger.jsonl").read_text(encoding="utf-8")
            ledger = KernelLedger.from_jsonl(ledger_text)
            self.assertEqual(ledger.audit(), [])
            self.assertEqual(ledger.to_jsonl(), ledger_text)
            self.assertEqual(check_court_file.main(["check_court_file.py", str(run_dir)]), 0)
        finally:
            for name, value in old.items():
                setattr(chamber, name, value)
            shutil.rmtree(root, ignore_errors=True)


class CourtReplicationTests(_ContextPacketMixin, unittest.TestCase):
    """CHAMBER_NODE_URL: a finalized run's court replicates to a live
    chamber-node and becomes stranger-auditable over HTTP; a dead node
    costs a warning ledger entry, never a run (fail-soft)."""

    def setUp(self) -> None:
        super().setUp()
        self._lifetime_tmp = Path(tempfile.mkdtemp(prefix="chamber_lt_"))
        self._old_lifetime_path = chamber.LIFETIME_LEDGER_PATH
        chamber.LIFETIME_LEDGER_PATH = self._lifetime_tmp / "lifetime.jsonl"
        self._old_node_url = chamber.NODE_URL

    def tearDown(self) -> None:
        chamber.LIFETIME_LEDGER_PATH = self._old_lifetime_path
        chamber.NODE_URL = self._old_node_url
        shutil.rmtree(self._lifetime_tmp, ignore_errors=True)
        super().tearDown()

    def _record(self) -> chamber.RunRecord:
        return chamber.RunRecord(
            run_id="repltest",
            created_at="2026-07-05T12:00:00+00:00",
            requester="tester",
            task=chamber.build_wrapped_task(chamber.DEFAULT_DEMO_QUESTION),
            max_words=64,
            question=chamber.DEFAULT_DEMO_QUESTION,
            status="approved",
            approved_answer="Judgment: bounded fake answer for replication.",
            receipt=["release reviewed"],
        )

    def test_finalized_court_lands_on_live_node(self) -> None:
        import json as _json
        import threading
        import urllib.request
        from chambers.kernel import node as node_mod

        server = node_mod.serve("127.0.0.1", 0, None, 4 * 1024 * 1024)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        chamber.NODE_URL = base
        root = Path(tempfile.mkdtemp(prefix="chamber_repl_"))
        try:
            rec = self._record()
            writer = chamber.CourtFileWriter(rec, root / rec.run_id)
            writer.finalize(rec)
            with urllib.request.urlopen(base + "/v1/health") as r:
                health = _json.loads(r.read())
            self.assertEqual(health["events"], writer.kernel_ledger.event_count())
            with urllib.request.urlopen(base + "/v1/audit") as r:
                self.assertTrue(_json.loads(r.read())["clean"])
            rows = [_json.loads(l) for l in
                    (root / rec.run_id / "ledger.jsonl").read_text().splitlines() if l.strip()]
            self.assertTrue(any(x.get("action") == "court_replicated_to_node" for x in rows))
        finally:
            server.shutdown()
            shutil.rmtree(root, ignore_errors=True)

    def test_dead_node_is_fail_soft(self) -> None:
        import json as _json
        chamber.NODE_URL = "http://127.0.0.1:1"  # nothing listens here
        root = Path(tempfile.mkdtemp(prefix="chamber_repl_dead_"))
        try:
            rec = self._record()
            writer = chamber.CourtFileWriter(rec, root / rec.run_id)
            writer.finalize(rec)  # must NOT raise
            self.assertTrue(writer.finalized)
            rows = [_json.loads(l) for l in
                    (root / rec.run_id / "ledger.jsonl").read_text().splitlines() if l.strip()]
            self.assertTrue(any(x.get("action") == "court_replication_failed" for x in rows))
        finally:
            shutil.rmtree(root, ignore_errors=True)


class LifetimeExposureAccountTests(_ContextPacketMixin, unittest.TestCase):
    """The cross-run accumulation gate (coalition.ts ExposureAccount law):
    a passcode holder's charges accumulate in ONE persistent pair account
    across runs, so fresh per-run ceilings cannot be composed past the
    lifetime budget. Found by the first real dogfood run (2026-07-05)."""

    def _fresh_writer(self, root: Path, run_id: str) -> chamber.CourtFileWriter:
        rec = chamber.RunRecord(
            run_id=run_id,
            created_at="2026-07-05T12:00:00+00:00",
            requester="tester",
            task=chamber.build_wrapped_task(chamber.DEFAULT_DEMO_QUESTION),
            max_words=chamber.DEFAULT_MAX_WORDS,
            question=chamber.DEFAULT_DEMO_QUESTION,
            status="approved",
        )
        return chamber.CourtFileWriter(rec, root / run_id)

    def test_lifetime_account_accumulates_across_runs_and_refuses(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="chamber_lifetime_"))
        old_path = chamber.LIFETIME_LEDGER_PATH
        old_budget = chamber.LIFETIME_BUDGET_RUNS
        try:
            chamber.LIFETIME_LEDGER_PATH = root / "lifetime_exposure_ledger.jsonl"
            chamber.LIFETIME_BUDGET_RUNS = 1  # lifetime == one run ceiling
            per_run = chamber.chamber_run_ceiling_mbits(chamber.DEFAULT_MAX_WORDS)

            def emit_units(writer: chamber.CourtFileWriter, n: int):
                accepted, last_error = 0, ""
                for i in range(n):
                    try:
                        writer.record_emission(
                            surface="requester_result",
                            kind="answer_field",
                            projected_precision="managed",
                            actor_id="principal_worker_agent",
                            detail={"i": i},
                            risk_classes=[],
                        )
                        accepted += 1
                    except RuntimeError as e:
                        last_error = str(e)
                        break
                return accepted, last_error

            # Run 1: fresh run account AND fresh lifetime account, EQUAL
            # ceilings (budget = 1 run). The lifetime account is charged
            # first, so at the boundary it is the one that refuses.
            unit = chamber.CHAMBER_ANSWER_FIELD_MBITS
            w1 = self._fresh_writer(root, "run1")
            n1, err1 = emit_units(w1, per_run // unit + 5)
            self.assertGreater(n1, 0)
            self.assertIn("lifetime exposure account", err1)

            # Run 2: the run account is BRAND NEW (full per-run ceiling) —
            # before the gate this bought a second full budget. Now the
            # lifetime account carries run 1's cumulative and refuses the
            # FIRST emission.
            w2 = self._fresh_writer(root, "run2")
            n2, err2 = emit_units(w2, 3)
            self.assertEqual(n2, 0, "fresh run account bypassed the lifetime gate")
            self.assertIn("lifetime exposure account", err2)

            # The persistent ledger replays audit-clean for a stranger and
            # folds to ONE pair account with cumulative <= lifetime ceiling.
            text = chamber.LIFETIME_LEDGER_PATH.read_text(encoding="utf-8")
            ledger = KernelLedger.from_jsonl(text)
            self.assertEqual(ledger.audit(), [])
            self.assertEqual(ledger.to_jsonl(), text)
            accounts = ledger.fold()
            self.assertEqual(len(accounts), 1)
            (key, acct), = accounts.items()
            self.assertIn(chamber._lifetime_reader_entity(), list(key))
            self.assertLessEqual(acct.cumulative_mbits, acct.ceiling_mbits)
            self.assertGreater(acct.cumulative_mbits, 0)
        finally:
            chamber.LIFETIME_LEDGER_PATH = old_path
            chamber.LIFETIME_BUDGET_RUNS = old_budget
            shutil.rmtree(root, ignore_errors=True)


class CourtFileExactByteIntegrityTests(_ContextPacketMixin, unittest.TestCase):
    """The court file is EVIDENCE. After finalize, check_court_file.py must
    convict post-finalization tampering, not merely re-parse the story:

      1. byte tampering of a requester-visible artifact — including tampering
         that is a semantic no-op for the JSON parser (exact raw-byte
         integrity is the law; semantic parsing is a separate, weaker check);
      2. review-row tampering (a verdict flip) in reviews.jsonl;
      3. deletion of a recorded requester-visible artifact file;
      4. an unrecorded file planted into the court directory;
      5. a coordinated edit of an artifact AND its unauthenticated sibling
         hash records (artifacts.jsonl row, release_docket.json
         candidateArtifactHash). Locally-consistent forgeries cannot be
         demanded impossible self-authentication from attacker-editable
         siblings alone: this attack is convicted against an EXTERNALLY
         SUPPLIED expected manifest root — the durable trust anchor a
         counterparty captured at finalization — passed as
         `--expect-manifest-root sha256:<hex>`. Internal consistency and
         anchored exact integrity are distinct verdicts, so the anchored
         contract is pinned three ways: clean court + correct root passes,
         clean court + wrong root is rejected (the root is verified, never
         decoratively accepted), tampered court + correct root is rejected.

    Manifest-root convention (the anchored contract):
      entries  = [{"fileName": f.name, "sha256": sha256_bytes(f bytes)}
                  for every regular file directly under run_dir,
                  sorted by fileName]
      root     = sha256_json(entries)          # repo-canonical JSON hash
      CLI      = check_court_file.py <run_dir> [--expect-manifest-root <root>]
    """

    def setUp(self) -> None:
        super().setUp()
        self._lifetime_tmp = Path(tempfile.mkdtemp(prefix="chamber_lt_"))
        self._old_lifetime_path = chamber.LIFETIME_LEDGER_PATH
        chamber.LIFETIME_LEDGER_PATH = self._lifetime_tmp / "lifetime.jsonl"

    def tearDown(self) -> None:
        chamber.LIFETIME_LEDGER_PATH = self._old_lifetime_path
        shutil.rmtree(self._lifetime_tmp, ignore_errors=True)
        super().tearDown()

    APPROVED_ANSWER = "Judgment: bounded fake answer for the byte-integrity court file."

    def _finalized_court(self, root: Path) -> Path:
        rec = chamber.RunRecord(
            run_id="bytecourt",
            created_at="2026-07-05T12:00:00+00:00",
            requester="tester",
            task=chamber.build_wrapped_task(chamber.DEFAULT_DEMO_QUESTION),
            max_words=64,
            question=chamber.DEFAULT_DEMO_QUESTION,
            status="approved",
            approved_answer=self.APPROVED_ANSWER,
            receipt=["release reviewed", "owner approved disclosure"],
        )
        run_dir = root / rec.run_id
        writer = chamber.CourtFileWriter(rec, run_dir)
        answer_path = run_dir / "approved_answer.txt"
        answer_path.write_text(rec.approved_answer + "\n", encoding="utf-8")
        writer.record_artifact(
            answer_path,
            kind="release_candidate",
            visibility="requester_visible",
            redaction_state="public_minimized",
            actor_id="principal_system",
        )
        writer.note_release_candidate(answer_path, released_fields=["$.answer"], redacted_fields=[])
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
                rationale="release review: bounded answer only",
            )
        writer.finalize(rec)
        return run_dir

    def _manifest_root(self, run_dir: Path) -> str:
        entries = [
            {"fileName": path.name, "sha256": chamber.sha256_bytes(path.read_bytes())}
            for path in sorted(run_dir.iterdir(), key=lambda p: p.name)
            if path.is_file()
        ]
        return chamber.sha256_json(entries)

    def _assert_ok(self, run_dir: Path, *extra: str) -> None:
        argv = ["check_court_file.py", str(run_dir), *extra]
        try:
            code = check_court_file.main(argv)
        except SystemExit as exc:
            self.fail(
                f"verifier rejected a court file it must accept (argv tail={argv[1:]}): exit {exc.code}"
            )
        self.assertEqual(code, 0)

    def _assert_rejected(self, run_dir: Path, *extra: str) -> None:
        argv = ["check_court_file.py", str(run_dir), *extra]
        with self.assertRaises(SystemExit) as ctx:
            check_court_file.main(argv)
        self.assertEqual(ctx.exception.code, 1)

    def test_semantically_invisible_byte_tamper_of_receipt_is_rejected(self) -> None:
        """Trailing whitespace appended to receipt.json parses to the
        IDENTICAL JSON value — semantic checks stay green — but the raw bytes
        no longer match the sha256 recorded for the requester-visible receipt
        artifact. Exact raw-byte integrity must convict what semantic parsing
        cannot see."""
        root = Path(tempfile.mkdtemp(prefix="chamber_bytecourt_"))
        try:
            run_dir = self._finalized_court(root)
            self._assert_ok(run_dir)
            receipt_path = run_dir / "receipt.json"
            original = receipt_path.read_bytes()
            tampered = original + b"\n \n"
            self.assertEqual(json.loads(tampered), json.loads(original))
            self.assertNotEqual(tampered, original)
            receipt_path.write_bytes(tampered)
            self._assert_rejected(run_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_tampered_release_candidate_artifact_bytes_are_rejected(self) -> None:
        """Rewriting the released answer file after finalization must be
        convicted: artifacts.jsonl, the ledger's artifact_written detailHash,
        and release_docket.json candidateArtifactHash all still commit to the
        original bytes."""
        root = Path(tempfile.mkdtemp(prefix="chamber_bytecourt_"))
        try:
            run_dir = self._finalized_court(root)
            self._assert_ok(run_dir)
            answer_path = run_dir / "approved_answer.txt"
            answer_path.write_text(
                "Judgment: the attacker's preferred answer.\n", encoding="utf-8"
            )
            self._assert_rejected(run_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_tampered_review_row_verdict_is_rejected(self) -> None:
        """Flipping one release review's verdict in reviews.jsonl (ids and
        every other row byte-identical, so today's referential checks stay
        green) must be convicted. The evidence exists in the intact court:
        the ledger's review_submitted detailHash commits to
        {label, stage, verdict}. Verdict edits in either direction launder
        the review record; integrity is direction-agnostic."""
        root = Path(tempfile.mkdtemp(prefix="chamber_bytecourt_"))
        try:
            run_dir = self._finalized_court(root)
            self._assert_ok(run_dir)
            reviews_path = run_dir / "reviews.jsonl"
            lines = reviews_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            tampered_line = lines[1].replace('"verdict": "allow"', '"verdict": "block"', 1)
            self.assertNotEqual(tampered_line, lines[1])
            self.assertEqual(
                json.loads(tampered_line)["id"], json.loads(lines[1])["id"]
            )
            reviews_path.write_text("\n".join([lines[0], tampered_line]) + "\n", encoding="utf-8")
            self._assert_rejected(run_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_missing_recorded_requester_visible_artifact_is_rejected(self) -> None:
        """Deleting the released answer file must be convicted: its
        artifacts.jsonl row, ledger entry, and release_docket
        candidateArtifactId all still swear the artifact exists."""
        root = Path(tempfile.mkdtemp(prefix="chamber_bytecourt_"))
        try:
            run_dir = self._finalized_court(root)
            self._assert_ok(run_dir)
            (run_dir / "approved_answer.txt").unlink()
            self._assert_rejected(run_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_unrecorded_planted_file_is_rejected(self) -> None:
        """A file planted into the finalized court directory — present on the
        requester-visible surface but absent from every artifact record —
        must be convicted. The court file is a closed exhibit list, not a
        directory that happens to contain one."""
        root = Path(tempfile.mkdtemp(prefix="chamber_bytecourt_"))
        try:
            run_dir = self._finalized_court(root)
            self._assert_ok(run_dir)
            (run_dir / "planted_disclosure.txt").write_text(
                "smuggled requester-visible content\n", encoding="utf-8"
            )
            self._assert_rejected(run_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_consistent_artifact_and_manifest_edit_fails_against_trusted_root(self) -> None:
        """The coordinated attack: rewrite the released answer AND recompute
        every sibling hash record that stores its digest in the clear
        (artifacts.jsonl row, release_docket.json candidateArtifactHash), so
        the local court is self-consistent. Attacker-editable siblings cannot
        self-authenticate, so conviction comes from the externally supplied
        trusted root captured at finalization. The anchored contract is
        pinned three ways so the root is verified, not decoratively accepted.
        (Unanchored behavior on this forgery is deliberately unasserted:
        internal-consistency conviction via ledger detailHash is legitimate
        but not required.)"""
        root = Path(tempfile.mkdtemp(prefix="chamber_bytecourt_"))
        try:
            run_dir = self._finalized_court(root)
            self._assert_ok(run_dir)
            trusted_root = self._manifest_root(run_dir)

            # Clean court verifies against the root a counterparty captured.
            self._assert_ok(run_dir, "--expect-manifest-root", trusted_root)
            # A wrong root on the clean court must be rejected.
            wrong_root = chamber.sha256_json(["not-the-court-manifest"])
            self.assertNotEqual(wrong_root, trusted_root)
            self._assert_rejected(run_dir, "--expect-manifest-root", wrong_root)

            answer_path = run_dir / "approved_answer.txt"
            old_sha = chamber.sha256_bytes(answer_path.read_bytes())
            answer_path.write_text(
                "Judgment: the attacker's preferred answer.\n", encoding="utf-8"
            )
            new_sha = chamber.sha256_bytes(answer_path.read_bytes())
            for sibling in ("artifacts.jsonl", "release_docket.json"):
                sibling_path = run_dir / sibling
                text = sibling_path.read_text(encoding="utf-8")
                self.assertIn(old_sha, text, sibling)
                sibling_path.write_text(text.replace(old_sha, new_sha), encoding="utf-8")

            # The locally-consistent forgery must fail exact integrity
            # against the pre-tamper trust anchor.
            self._assert_rejected(run_dir, "--expect-manifest-root", trusted_root)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
