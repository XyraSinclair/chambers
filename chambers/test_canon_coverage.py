"""The Book coverage map names every typed canon law exactly once.

The appendix in ``docs/BOOK.md`` is the human-readable accounting surface
for the ``*_LAWS`` consts in ``docs/primitives/*.ts``. This lane makes its
denominator, subsection metadata, and per-key coverage mechanically binding.
"""
import pathlib
import re
import unicodedata

REPO = pathlib.Path(__file__).resolve().parent.parent
PRIMITIVES = REPO / "docs" / "primitives"
BOOK = REPO / "docs" / "BOOK.md"

LAW_EXPORT_RE = re.compile(
    r"^export\s+const\s+([A-Z][A-Z0-9_]*_LAWS)\s*=\s*\{"
    r"(?P<body>.*?)^\}\s+as\s+const;\s*$",
    re.MULTILINE | re.DOTALL,
)
LAW_EXPORT_NAME_RE = re.compile(
    r"^export\s+const\s+([A-Z][A-Z0-9_]*_LAWS)\b", re.MULTILINE
)
LAW_KEY_RE = re.compile(
    r"^([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*(?:true|false)\s*,?\s*$"
)
DENOMINATOR_RE = re.compile(
    r"\*\*(\d+) keys across (\d+) `\*_LAWS` consts\*\*"
)
BOOK_HEADER_RE = re.compile(
    r"^\*\*([A-Z][A-Z0-9_]*_LAWS) "
    r"\(([^,()]+\.ts), (\d+)(?: keys)?(?:;[^)]*)?\)\*\*\s*$",
    re.MULTILINE,
)
BOOK_LAW_HEADER_CANDIDATE_RE = re.compile(
    r"^\*\*[^\n]*_LAWS[^\n]*\*\*\s*$", re.MULTILINE
)
BOLD_SUBSECTION_RE = re.compile(r"^\*\*[^\n]+\*\*\s*$", re.MULTILINE)
CAMEL_WORD_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+"
)
GRAMMAR_WORDS = {"a", "an", "the", "is", "are"}
KEYLESS_BOOK_ROWS = {
    "CALCULUS.md L4, monotone widening (no `*_LAWS` key)"
}

# These rows deliberately state a stronger or differently phrased proposition
# than the compact TypeScript identifier. Freeze both sides rather than weaken
# exact matching for the other 133 laws.
PARAPHRASED_ROWS = {
    ("CALCULUS_LAWS", "gatesArePublicOrCharged"):
        "gates are public-only or charged (L5)",
    ("CALCULUS_LAWS", "refusalsSimulatable"):
        "refusals simulatable or charged",
    ("COALITION_LAWS", "leakageIsReaderRelative"):
        "leakage is reader-relative, never a scalar",
    ("COALITION_LAWS", "exposureAccountsAreSourceByReader"):
        "exposure accounts are keyed (source × reader), lifetime",
    ("CORE_LAWS", "receiptsNameNonClaims"):
        "evidence artifacts name non-claims",
    ("ENTROPY_LAWS", "releaseGateIsConjunctionOfNumericAndOrdinal"):
        "release gate is the conjunction of numeric accountant and ordinal gate",
    ("ENVIRONMENT_LAWS", "receiptsDescribeObservedConfigurationNotPerfectIsolation"):
        "evidence artifacts describe observed configuration, not perfect isolation",
    ("IPTRADE_LAWS", "estimationChannelIsMeteredBecauseClosestPriorArtIsAScoopMap"):
        "estimation channel is metered (closest prior art is a scoop map)",
    ("IPTRADE_LAWS", "cryptographicReceiptsAreNotSelfEnforcingContracts"):
        "cryptographic evidence artifacts are not self-enforcing contracts",
    ("IPTRADE_LAWS", "everythingHereIsBilateralMultilateralBarterRingsUnbuilt"):
        "everything here is bilateral; barter rings unbuilt",
    ("MEDIATION_LAWS", "requesterIsAReader"):
        "the requester is a reader, not a privileged sink",
    ("MEDIATION_LAWS", "poolClaimsAreAchievedNotHoped"):
        "pool claims state the set achieved, never hoped",
    ("MEDIATION_LAWS", "poolsNeverMoveContent"):
        "pools never move content or authority",
}


def _without_typescript_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


def _parse_typescript_laws() -> tuple[dict[str, tuple[str, list[str]]], list[str]]:
    laws = {}
    errors = []
    for path in sorted(PRIMITIVES.glob("*.ts")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"cannot read {path.relative_to(REPO)}: {error}")
            continue

        discovered = LAW_EXPORT_NAME_RE.findall(text)
        parsed = []
        for match in LAW_EXPORT_RE.finditer(text):
            name = match.group(1)
            parsed.append(name)
            keys = []
            body = _without_typescript_comments(match.group("body"))
            for line_number, line in enumerate(body.splitlines(), 1):
                stripped = line.strip()
                if not stripped:
                    continue
                key_match = LAW_KEY_RE.fullmatch(stripped)
                if key_match is None:
                    errors.append(
                        f"malformed {name} entry in {path.name} body line "
                        f"{line_number}: {stripped!r}"
                    )
                    continue
                keys.append(key_match.group(1))

            duplicate_keys = sorted(
                key for key in set(keys) if keys.count(key) > 1
            )
            if duplicate_keys:
                errors.append(
                    f"duplicate keys in {name}: {', '.join(duplicate_keys)}"
                )
            if name in laws:
                errors.append(f"duplicate TypeScript const: {name}")
            else:
                laws[name] = (path.name, keys)

        if discovered != parsed:
            errors.append(
                f"unparsed or malformed law export in {path.name}: "
                f"discovered={discovered}, parsed={parsed}"
            )
    return laws, errors


def _parse_book_coverage() -> tuple[
    dict[str, tuple[str, int, list[str]]], int, int, list[str]
]:
    errors = []
    try:
        text = BOOK.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return {}, 0, 0, [f"cannot read docs/BOOK.md: {error}"]

    appendix_heading = "## Appendix — coverage map"
    if text.count(appendix_heading) != 1:
        return {}, 0, 0, [
            f"expected one {appendix_heading!r} heading, found "
            f"{text.count(appendix_heading)}"
        ]
    appendix = text.split(appendix_heading, 1)[1]
    next_heading = re.search(r"^##\s+", appendix, re.MULTILINE)
    if next_heading is not None:
        appendix = appendix[:next_heading.start()]

    denominators = DENOMINATOR_RE.findall(appendix)
    if len(denominators) != 1:
        errors.append(
            "expected one bold law denominator in the coverage appendix, "
            f"found {len(denominators)}"
        )
        expected_keys = expected_consts = 0
    else:
        expected_keys, expected_consts = map(int, denominators[0])

    headers = list(BOOK_HEADER_RE.finditer(appendix))
    header_candidates = BOOK_LAW_HEADER_CANDIDATE_RE.findall(appendix)
    if len(header_candidates) != len(headers):
        errors.append(
            "unparsed or malformed BOOK law header: "
            f"candidates={header_candidates}, parsed="
            f"{[match.group(0) for match in headers]}"
        )

    subsections = list(BOLD_SUBSECTION_RE.finditer(appendix))
    coverage = {}
    keyless_rows = set()
    for header in headers:
        name, filename, declared_count = header.groups()
        end = next(
            (
                subsection.start()
                for subsection in subsections
                if subsection.start() > header.start()
            ),
            len(appendix),
        )
        rows = []
        for line in appendix[header.end():end].splitlines():
            if not line.startswith("- "):
                continue
            if " → " not in line:
                errors.append(f"BOOK row under {name} lacks →: {line!r}")
                continue
            prose = line[2:].split(" → ", 1)[0].strip()
            if "(no `*_LAWS` key)" in prose:
                keyless_rows.add(prose)
            else:
                rows.append(prose)
        if name in coverage:
            errors.append(f"duplicate BOOK subsection: {name}")
        else:
            coverage[name] = (filename, int(declared_count), rows)

    if keyless_rows != KEYLESS_BOOK_ROWS:
        errors.append(
            "BOOK keyless rows changed: "
            f"expected={sorted(KEYLESS_BOOK_ROWS)}, actual={sorted(keyless_rows)}"
        )
    return coverage, expected_keys, expected_consts, errors


def _canonical_words(words: list[str]) -> str:
    canonical = []
    for word in words:
        word = word.lower()
        if word in GRAMMAR_WORDS:
            continue
        if word == "onchain":
            canonical.extend(("on", "chain"))
            continue
        if (
            len(word) > 3
            and word.endswith("s")
            and not word.endswith(("ss", "us", "is"))
        ):
            word = word[:-1]
        canonical.append(word)
    return " ".join(canonical)


def _normalize_key(key: str) -> str:
    return _canonical_words(CAMEL_WORD_RE.findall(key))


def _normalize_prose(prose: str) -> str:
    prose = re.sub(
        r"\((?:L\d+(?:\s*[–-]\s*L?\d+)?)(?:\s*,\s*L?\d+)*\)",
        " ",
        prose,
        flags=re.IGNORECASE,
    )
    prose = re.sub(r"\(recorded\s+`(?:true|false)`\)", " ", prose)
    prose = unicodedata.normalize("NFKD", prose.replace("`", ""))
    return _canonical_words(re.findall(r"[A-Za-z]+|\d+", prose))


def test_book_coverage_matches_typed_canon() -> None:
    typescript, typescript_errors = _parse_typescript_laws()
    book, expected_keys, expected_consts, book_errors = _parse_book_coverage()
    errors = typescript_errors + book_errors

    typescript_names = set(typescript)
    book_names = set(book)
    missing_sections = sorted(typescript_names - book_names)
    extra_sections = sorted(book_names - typescript_names)
    if missing_sections:
        errors.append("BOOK missing const subsections: " + ", ".join(missing_sections))
    if extra_sections:
        errors.append("BOOK has unknown const subsections: " + ", ".join(extra_sections))

    total_keys = sum(len(keys) for _, keys in typescript.values())
    total_rows = sum(len(rows) for _, _, rows in book.values())
    if expected_consts != len(typescript):
        errors.append(
            f"BOOK denominator says {expected_consts} consts, TypeScript has "
            f"{len(typescript)}"
        )
    if expected_keys != total_keys:
        errors.append(
            f"BOOK denominator says {expected_keys} keys, TypeScript has {total_keys}"
        )
    if total_rows != total_keys:
        errors.append(f"BOOK has {total_rows} law rows, TypeScript has {total_keys} keys")

    paraphrase_matches = 0
    for (name, key), prose in PARAPHRASED_ROWS.items():
        typescript_entry = typescript.get(name)
        book_entry = book.get(name)
        if typescript_entry is None or key not in typescript_entry[1]:
            errors.append(f"stale paraphrase key: {name}.{key}")
        if book_entry is None or book_entry[2].count(prose) != 1:
            occurrences = 0 if book_entry is None else book_entry[2].count(prose)
            errors.append(
                f"stale paraphrase row for {name}.{key}: {prose!r} "
                f"occurs {occurrences} times"
            )
        if (
            typescript_entry is not None
            and key in typescript_entry[1]
            and book_entry is not None
            and book_entry[2].count(prose) == 1
        ):
            paraphrase_matches += 1
    if paraphrase_matches != len(PARAPHRASED_ROWS):
        errors.append(
            f"matched {paraphrase_matches} of {len(PARAPHRASED_ROWS)} "
            "frozen paraphrases"
        )

    matched_rows = 0
    for name in sorted(typescript_names & book_names):
        typescript_file, keys = typescript[name]
        book_file, declared_count, rows = book[name]
        if book_file != typescript_file:
            errors.append(
                f"{name} header names {book_file}, TypeScript const is in "
                f"{typescript_file}"
            )
        if declared_count != len(keys):
            errors.append(
                f"{name} header says {declared_count} keys, TypeScript has {len(keys)}"
            )
        if len(rows) != len(keys):
            errors.append(f"{name} has {len(rows)} BOOK rows and {len(keys)} keys")

        allowed = {
            key: prose
            for (const_name, key), prose in PARAPHRASED_ROWS.items()
            if const_name == name
        }
        exact_keys = [key for key in keys if key not in allowed]
        exact_rows = [row for row in rows if row not in allowed.values()]
        normalized_keys = {}
        normalized_rows = {}
        for key in exact_keys:
            normalized_keys.setdefault(_normalize_key(key), []).append(key)
        for row in exact_rows:
            normalized_rows.setdefault(_normalize_prose(row), []).append(row)

        for normalized, originals in normalized_keys.items():
            if len(originals) > 1:
                errors.append(
                    f"{name} keys collide after normalization {normalized!r}: "
                    + ", ".join(originals)
                )
        for normalized, originals in normalized_rows.items():
            if len(originals) > 1:
                errors.append(
                    f"{name} rows collide after normalization {normalized!r}: "
                    + "; ".join(originals)
                )

        unmatched_keys = sorted(set(normalized_keys) - set(normalized_rows))
        unmatched_rows = sorted(set(normalized_rows) - set(normalized_keys))
        for normalized in unmatched_keys:
            errors.append(
                f"unmatched TypeScript key in {name}: "
                f"{normalized_keys[normalized][0]} -> {normalized!r}"
            )
        for normalized in unmatched_rows:
            errors.append(
                f"unmatched BOOK row in {name}: "
                f"{normalized_rows[normalized][0]!r} -> {normalized!r}"
            )
        matched_rows += len(set(normalized_keys) & set(normalized_rows)) + len(allowed)

    if matched_rows != total_keys:
        errors.append(f"matched {matched_rows} of {total_keys} TypeScript keys")
    if matched_rows != total_rows:
        errors.append(f"matched {matched_rows} of {total_rows} BOOK rows")

    assert errors == [], "canon coverage drift:\n- " + "\n- ".join(errors)
