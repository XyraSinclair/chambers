"""Owner-side packet builder: enumerate abandoned-idea candidates from the
private corpus, with the paired ablated packet for the counterfactual run.

Owner-trusted code. The enumeration IS the alphabet construction: the guest
can only ever name candidates enumerated here, so the ideas themselves never
leave the owner's side except as bounded slices to the metered worker
endpoint. Candidate IDs are salted per run; the id->entity mapping stays in
the owner-private run directory.

Privacy discipline for operating agents: NEVER print slice or title content
to a transcript. Everything owner-facing goes through files under the run
directory (.chamber/, gitignored).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DB_PATH = Path(
    os.environ.get(
        "CORPUS_DB",
        Path.home() / "projects/archive/p1-xyra-sh/corpus/db/corpus_v3.db",
    )
)

N_CANDIDATES = 24
SLICE_CHARS = 1000
CUTOFF_DATE = "2026-01-01"  # "abandoned" = no activity since well before now
MIN_WORDS = 150

QUESTION = (
    "Which three of these abandoned ideas are most worth reviving now, "
    "given what the owner is currently building?"
)

# Owner-authored context anchor. This text ships to the worker endpoint with
# every screening/ranking prompt — same exposure class as the slices.
CONTEXT = (
    "The owner is building Scry Chambers: a private-compute substrate where "
    "third-party agents do bounded cognitive work over people's private "
    "context without carrying it away — closed release alphabets, metered "
    "disclosure, counterfactual review, and receipts. Current focus: a "
    "concrete demo of the full loop over a real private corpus, and finding "
    "the first real requesters for bounded-diligence chambers."
)


@dataclass(frozen=True)
class Candidate:
    entity_id: int
    salted_id: str
    title: str
    slice_text: str
    date: str
    sensitive: bool
    score: float


def _clean(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:limit]


def mine_candidates(db_path: Path = DB_PATH, salt: str = "") -> List[Candidate]:
    """Top-N old, high-originality/ambition entities with sensitivity marks."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            """
            SELECT e.id, COALESCE(e.title,'(untitled)'), e.text, COALESCE(e.date,''),
                   AVG(j.numeric_value) AS score,
                   EXISTS(
                     SELECT 1 FROM sensitivity_flags sf
                     WHERE sf.entity_id = e.id AND sf.status != 'false_positive'
                   ) AS sensitive
            FROM entities e
            JOIN judgements j ON j.entity_id = e.id
            JOIN attributes a ON a.id = j.attribute_id
            WHERE a.name IN ('originality','intellectual_ambition','foundationalness')
              AND e.date < ?
              AND e.word_count >= ?
              AND e.text IS NOT NULL
            GROUP BY e.id
            HAVING COUNT(DISTINCT a.name) >= 2
            ORDER BY score DESC
            LIMIT ?
            """,
            (CUTOFF_DATE, MIN_WORDS, N_CANDIDATES * 3),
        ).fetchall()
    finally:
        conn.close()

    # Dedupe near-identical titles (same conversation re-ingested), keep best.
    seen_titles: Dict[str, bool] = {}
    picked: List[Tuple] = []
    for row in rows:
        key = _clean(str(row[1]).lower(), 80)
        if key in seen_titles:
            continue
        seen_titles[key] = True
        picked.append(row)
        if len(picked) == N_CANDIDATES:
            break

    out: List[Candidate] = []
    for i, (eid, title, text, date, score, sensitive) in enumerate(picked):
        sid = "c" + hashlib.sha256(f"{salt}:{eid}".encode()).hexdigest()[:8]
        out.append(
            Candidate(
                entity_id=int(eid),
                salted_id=sid,
                title=_clean(str(title), 120),
                slice_text=_clean(str(text), SLICE_CHARS),
                date=str(date)[:10],
                sensitive=bool(sensitive),
                score=float(score or 0.0),
            )
        )
    return out


def build_packets(run_dir: Path, db_path: Path = DB_PATH) -> Dict[str, object]:
    """Write full + ablated packets and the owner-private mapping.

    Returns summary counts only — safe to print. Slice text never returns.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    salt_file = run_dir / "salt.txt"
    if not salt_file.exists():
        salt_file.write_text(os.urandom(16).hex(), encoding="utf-8")
    salt = salt_file.read_text(encoding="utf-8").strip()

    cands = mine_candidates(db_path, salt=salt)
    if len(cands) < 4:
        raise RuntimeError(f"only {len(cands)} candidates mined — packet too thin")

    def packet_of(cs: List[Candidate]) -> Dict[str, object]:
        return {
            "question": QUESTION,
            "context": CONTEXT,
            "candidates": [
                {"id": c.salted_id, "title": c.title, "slice": c.slice_text}
                for c in cs
            ],
        }

    full = packet_of(cands)
    ablated_members = [c for c in cands if not c.sensitive]
    ablated = packet_of(ablated_members)

    (run_dir / "packet_full.json").write_text(json.dumps(full), encoding="utf-8")
    (run_dir / "packet_ablated.json").write_text(json.dumps(ablated), encoding="utf-8")
    mapping = {
        c.salted_id: {
            "entity_id": c.entity_id,
            "title": c.title,
            "date": c.date,
            "sensitive": c.sensitive,
            "score": round(c.score, 4),
        }
        for c in cands
    }
    (run_dir / "owner_mapping.json").write_text(
        json.dumps(mapping, indent=2), encoding="utf-8"
    )
    return {
        "n_full": len(cands),
        "n_ablated": len(ablated_members),
        "n_sensitive": sum(1 for c in cands if c.sensitive),
        "slice_chars_total": sum(len(c.slice_text) for c in cands),
    }
