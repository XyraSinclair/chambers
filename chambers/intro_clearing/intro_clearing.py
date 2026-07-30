"""Purpose-blind introduction clearing house — a chambers vertical slice.

Two sovereign chambers each hold a private dossier. A guest worker, admitted
under typed grants, may score complementarity and draft bounded directional
match cards. Each card is reviewed by the *source* side before it may leave
that side's world. An introduction surfaces only when both directions clear
review, the numeric accountant accepts the structured charge, and the fee has
already cleared the counterparty's attention reserve. Everything else is a
byte-constant denial or silence.

Canon mapping (docs/primitives/CANON.md):
  core.ts       — no grant no run; no crossing without a LedgerEntry; release
                  fields are a reviewed subset of the sink; receipts name
                  non-claims; role separation over beneficial entities.
  matching.ts   — no live near-miss lists; priced introductions clear before
                  they surface; denials are invisible to counterparties;
                  scores and rationales release only as buckets or mediated
                  text; denominator leakage blocks match release.
  pricing.ts    — attention clears above reserve before any card surfaces;
                  owners may sell attention without buying an explanation;
                  failed crosses reveal one bit and still debit composition.
  attention.ts  — every interruption debits the ledger; exhaustion fails
                  closed for disclosure; notification text is itself egress;
                  reviewer memory is the same discipline for the human head:
                  charged as a ceiling before showing, never refunded,
                  rotating to a fresh reviewer until the bench fails closed.
  entropy.ts    — capacity charged at the adversarial maximum; the numeric
                  accountant binds structured channels; the ordinal gate
                  turns the prose channel into a charged selection among
                  fixed house projections (log2 K millibits), so worker
                  prose never crosses; budgets are tripwires, not
                  certificates.
  coalition.ts  — exposure accounts are keyed (source chamber x reader
                  entity), lifetime; sybil undercount risk is named, and
                  coalition_audit measures it under a supplied ownership
                  hypothesis after the fact — it is still not solved, and
                  the audit never gates.

Stdlib only. Deterministic: logical ticks, sha256 ids, sorted iteration,
no wall clock, no randomness.

Exposure and reviewer-memory meters are now views over charge-kernel/2.
Every book charge emits to one mergeable run-level kernel ledger; a stranger
can re-run Ledger.audit() on the JSONL artifact and re-derive the court file.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from itertools import combinations

from chambers.kernel import (
    CapacityEstimate,
    EstimatorAttestation,
    KernelMeter,
    Ledger,
    OutcomeCondition,
    SettlementIssuer,
    attest_outcome,
    audit_settlement_codes,
    conservation_identity,
    exposure_key,
    resolve_bond,
    resolve_default,
    settlement_fold_canonical_v2,
    settlement_fold_full,
)

# ---------------------------------------------------------------------------
# Closed vocabulary and constants
# ---------------------------------------------------------------------------

VOCAB = frozenset({
    "zk_proofs", "applied_cryptography", "systems_rust", "distributed_systems",
    "formal_verification", "compiler_engineering", "grant_funding", "gtm",
    "biostatistics", "open_source_maintenance", "defense_adjacent",
    "climate_modeling",
})

PURPOSE = "purpose_blind_introduction"
DENIAL_PAYLOAD = b"No introduction cleared in this window."
RATIONALE_CHAR_CAP = 320
NGRAM_TOKENS = 4
MASK_CHAR = "▩"  # ▩

# Numeric accountant: structured channels only, charged at adversarial max.
TAG_MILLIBITS = round(math.log2(len(VOCAB)) * 1000)
BUCKET_MILLIBITS = 1000        # released bucket enum {med, high}
PRESENCE_MILLIBITS = 1000      # a counterpart exists and matched
DENIAL_MILLIBITS = 1000        # a window denial is one bit, still debited
REVIEW_EMISSION_MILLIBITS = 1000  # owner learns a pseudonymous attempt existed
DEFAULT_EXPOSURE_BUDGET_MILLIBITS = 64_000

# Ordinal review gate: crossed rationale text is one of K fixed house
# projections of the approved structured fields. The reviewer's selection is
# the ONLY degree of freedom in the prose channel, so the channel's capacity
# is log2(K) millibits — charged whether or not the choice was innocent
# (adversarial max: a colluding reviewer could signal through it).
RATIONALE_CANDIDATE_COUNT = 4
ORDINAL_MILLIBITS = round(math.log2(RATIONALE_CANDIDATE_COUNT) * 1000)

# Reviewer memory: CEILINGS, not measurements. Every seated outbound review
# shows the reviewer the proposed card (structured fields + advisory worker
# prose) and the candidate set; each channel is charged at its schema
# ceiling, independent of content and of the decision taken, so the charge
# itself reveals nothing about what was reviewed. Memory is not revocable:
# these accounts only grow.
PROSE_CEILING_MILLIBITS_PER_CHAR = round(math.log2(96) * 1000)  # printable ASCII + mask glyph
ADVISORY_PROSE_CEILING_MILLIBITS = RATIONALE_CHAR_CAP * PROSE_CEILING_MILLIBITS_PER_CHAR
TAGS_SCHEMA_CEILING_MILLIBITS = 2 * len(VOCAB) * TAG_MILLIBITS
DEFAULT_REVIEWER_MEMORY_BUDGET_MILLIBITS = 9_000_000

# DECLARED, deliberately generous upper bound on a private silo's
# reconstructable structure. This is not measured entropy: tripwire accounts
# registered at this ceiling only block at declared-reconstruction scale, and
# the operative limits remain the book-level budgets.
DECLARED_SOURCE_ENTROPY_MBITS = 10_000_000_000

SCHEMA_CEILING_ATTESTATION = EstimatorAttestation(
    estimator_id="intro_clearing.schema_ceiling",
    independence="operator",
    method="static_schema_bound",
    worst_case_over_secrets=True,
)

# Settlement constants (CreditMicros).
OWNER_ENDOWMENT = 100_000
WORKER_ENDOWMENT = 10_000
WORKER_STAKE = 2_000
WORKER_FEE_SIDE = 500
HOUSE_FEE_SIDE = 250

# ---------------------------------------------------------------------------
# The party lane (charge-settlement/2): the party-matchmaker story's two
# consumer fee legs, wired onto the REAL kernel settlement — the same
# mergeable ledger the exposure meter writes, so one JSONL artifact carries
# charges, escrows, outcome attestations, and bonds, and one stranger-run
# audit (Ledger.audit + audit_settlement_codes) judges all of it.
#
#   leg 1  50 cents, UNCONDITIONAL-TO-RAISE: paid by the side being
#          introduced to the reader whose bell rings. Escrowed against the
#          ring's attention account and released against the ring's exact
#          charge event id — value moved iff the metered ring moved.
#   leg 2  $5 ON OUTCOME: escrowed under a charge-settlement/2 OUTCOME
#          condition (default refund_to_payer — no talk, the payer keeps
#          it, mechanically, at expiry). Released only on a bonded
#          platform_log attestation that the qualifying call occurred,
#          hardened by the contest window. The escrow binds to the intro
#          card's metered exposure account and the release references the
#          card's charge event id: FIRST-CONTACT ATTRIBUTION is the ledger
#          fact — the $5 pays for the exact crossing that constituted
#          first contact, by content-addressed id, and for nothing else.
#
# The metric names the observable proxy, never the aspiration: PRESENCE on
# a qualifying call, not engagement, not enjoyment, and not causation.
# "Talked BECAUSE of the card" has no lane in the settlement vocabulary
# (OUTCOME_LANES) and cannot be expressed — the counterfactual clause is
# refused, not priced.
RAISE_PRICE_UCR = 500_000            # 50 cents in kernel microcredits
OUTCOME_FEE_UCR = 5_000_000          # $5, contingent
OUTCOME_METRIC = "first_contact_qualifying_call_15min"  # presence, not engagement
OUTCOME_LANE = "platform_log"        # only platform-log facts can release
OUTCOME_QUORUM = 1
OUTCOME_MIN_INDEPENDENCE = "role_separated"
OUTCOME_MIN_BOND_UCR = 250_000
OUTCOME_CONTEST_TICKS = 3
OUTCOME_TTL_TICKS = 24               # after this, only the declared refund remains
PARTY_OWNER_ENDOWMENT_UCR = 20_000_000
PARTY_PLATFORM_FUND_UCR = 10_000_000  # bond backing for the call platform
RING_INTERRUPT_UNITS = 1_000

# The attention unit's meaning lives in the attestation id (canonical home:
# chambers/kernel/attention_node.py — same estimator id, same unit).
RING_ESTIMATOR = EstimatorAttestation(
    estimator_id="attention.micro_interrupts.flat_v1",
    independence="operator",
    method="declared_unit_flat",
    worst_case_over_secrets=True,
)

PARTY_LANE_GAPS = [
    {"key": "creditMicrosBooksAreSimLocal",
     "text": "Only the party lane's two consumer legs (the 50-cent raise and "
             "the $5 outcome fee) settle on the kernel. The house's internal "
             "clearing fees — worker fee, house fee, reviewer-attention "
             "purchases at reserve, stakes and slashes — still settle on the "
             "sim-local CreditMicros SettlementLedger (integer, conserved, "
             "but NOT the kernel meter). Same account names, two different "
             "books. Bridging the house books onto kernel microcredits is "
             "open work, named here, not claimed."},
    {"key": "reviewerAttentionIsSimLocal",
     "text": "The reviewer-interrupt AttentionBook is sim-local units; the "
             "kernel ('att', ...) accounts meter only the party lane's "
             "delivery rings."},
    {"key": "presenceNotEngagement",
     "text": "The outcome metric prices presence on a qualifying call, not "
             "engagement, enjoyment, or value realized. A fifteen-minute "
             "call spent complaining about the matchmaker releases the fee."},
    {"key": "counterfactualsRefused",
     "text": "'They talked BECAUSE of the card' is unoperationalizable and "
             "has no settlement lane; it cannot be escrowed, attested, or "
             "released. The contract prices the observable proxy only."},
    {"key": "collusionToDeny",
     "text": "Talk three hours off-platform, generate no platform log, keep "
             "the $10: theft of realized value no mechanism here prevents. "
             "The declared refund default makes it the payer's cheapest "
             "honest-looking move; the fee is calibrated so the lie stays "
             "smaller than the reputation (L5 standing non-claim)."},
    {"key": "identityIsDeclared",
     "text": "Kernel settlement accounts, attestors, and the call platform "
             "are declared names, not authenticated principals — the "
             "standing identity/Sybil non-claim applies to the party lane "
             "unchanged."},
]

INTRO_CLEARING_LAWS = {
    "noGrantNoRun": "core.ts: a worker without a live, purpose-bound grant does not run.",
    "noCrossingWithoutLedgerEntry": "core.ts: every delivered byte has a crossing ledger entry.",
    "releaseIsReviewedSubsetOfSink": "core.ts: released cards are mask/drop subsets of reviewed cards.",
    "roleSeparationOverBeneficialEntities": "core.ts/market.ts: worker entity is disjoint from both owner entities.",
    "receiptsNameNonClaims": "core.ts: every receipt carries the standing non-claims.",
    "pricedIntroductionsClearBeforeSurfacing": "pricing.ts: fee must clear the counterparty reserve before any card surfaces.",
    "attentionSoldWithoutExplanation": "pricing.ts: interruption fees settle even when review declines.",
    "denialsInvisibleToCounterparties": "matching.ts: all non-clearing causes collapse to one constant payload.",
    "noLiveNearMissLists": "matching.ts: sub-threshold pairs produce no artifact visible to any party.",
    "scoresReleaseOnlyAsBuckets": "matching.ts: fit crosses as an enum bucket plus mediated text, never a number.",
    "denominatorLeakageBlocksRelease": "matching.ts/entropy.ts: digits (counts, ranks) are scanned out of crossing text.",
    "everyInterruptionDebitsTheLedger": "attention.ts: reviewer interruptions debit attention units and settle micros.",
    "exhaustionFailsClosedForDisclosure": "attention.ts: no reviewable attention means no disclosure.",
    "numericAccountantBindsStructuredChannels": "entropy.ts: buckets/tags/identity are charged in millibits; prose is bound by the ordinal gate.",
    "ordinalGateBindsProse": "entropy.ts: crossed rationale is a fixed house projection of already-charged fields, selected by the source reviewer; the selection is charged at log2(K) millibits and worker prose never crosses.",
    "reviewerMemoryIsMonotone": "attention.ts/coalition.ts: every artifact shown to a seated reviewer charges a lifetime (source chamber x reviewer entity) memory ceiling before it is shown; nothing is ever refunded; an exhausted reviewer rotates off and an exhausted bench fails closed for disclosure.",
    "budgetsAreTripwiresNotCertificates": "entropy.ts: exposure budgets block releases and flag overruns; they certify nothing.",
    "exposureAccountsAreLifetimePerSourceReader": "coalition.ts: charges accumulate per (source chamber x reader entity) across windows.",
    "coalitionAuditIsHypothetical": "coalition.ts: merged-entity exposure audits run over unverifiable ownership hypotheses; they measure undercount after settlement and never gate a crossing.",
    "paymentSettlesOnOwnerInternalAcceptance": "market.ts: worker fees settle when cards pass scan into review, not on downstream liking.",
    "hiddenOverreachIsSlashable": "market.ts: grant violations and scan violations forfeit the worker stake.",
    "contingentFeesRideTheKernel": "SETTLEMENT-SPEC Part II: the party lane's $5 rides a charge-settlement/2 outcome escrow (default refund_to_payer) released only on a bonded, contest-hardened platform_log attestation; the release references the first-contact card's charge event id.",
    "counterfactualsRefusedNotPriced": "SETTLEMENT-SPEC §7: outcome metrics name observable proxies (presence on a qualifying call); causation has no lane and cannot be expressed.",
}

NON_CLAIMS = [
    {"key": "noPerfectPrivacy",
     "text": "Released buckets, tags, identities, and even byte-constant denials compose into inference across repeated windows. Budgets are tripwires, not certificates."},
    {"key": "verbatimBoundOnly",
     "text": "The span scan bounds literal copying from dossier prose. Paraphrase and semantic leakage are bound only by the ordinal review gate."},
    {"key": "proseNotNumericallyBound",
     "text": "Narrower after the ordinal gate: crossed rationale is a fixed house projection of already-charged fields and the reviewer's selection is charged at log2(K) millibits, so no free prose crosses. Still not numerically bound: template authorship (trusted house), reviewer memory of advisory worker prose, the semantics the tags themselves summarize, and cross-window composition of selections."},
    {"key": "reviewerExposure",
     "text": "Narrower after the reviewer-memory ledger: every pre-release artifact a seated reviewer saw (structured fields, advisory worker prose, the candidate set) is itemized and charged as a millibit ceiling to a lifetime (source chamber x reviewer entity) account; exhausted reviewers rotate off and an exhausted bench fails closed. Still not contained: ceilings are not measurements, memory is not revocable — rotation bounds future accrual only — reviewers may correlate across the sources they serve, and human recall is not a channel the house can audit."},
    {"key": "scriptedJudgment",
     "text": "This run scripts reviewer decisions. It demonstrates the gate topology, not human judgment; in production each decision is a human owner decision."},
    {"key": "sybilUndercountRisk",
     "text": "Exposure accounts are keyed over declared beneficial entities. A reader who fragments identities fragments the account."},
    {"key": "denialConstancyIsBytesOnly",
     "text": "Denial indistinguishability covers payload bytes, not timing or out-of-band behavior."},
    {"key": "trustedHouse",
     "text": "The clearing house, workers, and scans are a trusted, ledgered TCB, not MPC. Purpose strings are checked, not cryptographically enforced. This is a local simulation with no real parties or credits."},
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class GrantViolation(Exception):
    """A worker touched something its grant does not cover."""


class RoleSeparationError(Exception):
    """Worker and reviewer/owner resolve to the same beneficial entity."""


class LawViolation(Exception):
    """An internal invariant broke; the simulation refuses to continue."""


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------

def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def schema_capacity_estimate(
        *,
        channel: str,
        enum_value_mbits: int = 0,
        text_mbits: int = 0,
        side_channel_mbits: int = 0) -> CapacityEstimate:
    """Map intro-clearing schema ceilings into kernel estimate components.

    Tags, buckets, and reviewer ordinals are enum selections. Advisory prose
    and memory schema ceilings are text. Existence, identity, denial, and
    owner-review notifications are charged as side channels.
    """
    return CapacityEstimate(
        enum_value_mbits=enum_value_mbits,
        ordering_mbits=0,
        field_presence_mbits=0,
        text_mbits=text_mbits,
        side_channel_mbits=side_channel_mbits,
        channel=channel,
    )


def letters_token(seed: str, n: int = 6) -> str:
    """Deterministic uppercase-letters-only token (digit-free by construction)."""
    val = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest(), "big")
    out = []
    for _ in range(n):
        val, r = divmod(val, 26)
        out.append(chr(ord("A") + r))
    return "".join(out)


def identity_millibits(pool_size: int) -> int:
    return round(math.log2(max(pool_size, 2)) * 1000)


def verbatim_spans(source_text: str, out_text: str, n: int = NGRAM_TOKENS) -> list:
    """Contiguous n-token spans of source_text appearing verbatim in out_text."""
    toks = source_text.lower().split()
    hay = " ".join(out_text.lower().split())
    hits = []
    for i in range(len(toks) - n + 1):
        span = " ".join(toks[i:i + n])
        if span in hay:
            hits.append(span)
    return hits


# ---------------------------------------------------------------------------
# Principals, dossiers, intents, grants
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Chamber:
    chamber_id: str
    owner_entity: str
    contact_handle: str
    offers: frozenset
    needs: frozenset
    excludes: frozenset
    context_notes: str
    reserve_micros: int
    attention_budget: int
    reviewer_policy: str = "release_all"   # release_all | decline_all | mask:<tag>
    rationale_ordinal: int = 0             # this owner's standing candidate pick
    reviewer_bench: tuple = ("prime", "relief")  # owner's delegates, in seating order

    def __post_init__(self):
        for name, tags in (("offers", self.offers), ("needs", self.needs),
                           ("excludes", self.excludes)):
            bad = set(tags) - VOCAB
            if bad:
                raise LawViolation(f"{self.chamber_id}.{name}: tags outside closed vocabulary: {sorted(bad)}")
        if any(ch.isdigit() for ch in self.contact_handle):
            raise LawViolation(f"{self.chamber_id}: contact handles must be digit-free (denominator defense)")
        if not 0 <= self.rationale_ordinal < RATIONALE_CANDIDATE_COUNT:
            raise LawViolation(f"{self.chamber_id}: rationale ordinal outside the fixed candidate set")
        if not self.reviewer_bench or not all(
                isinstance(name, str) and name for name in self.reviewer_bench):
            raise LawViolation(f"{self.chamber_id}: reviewer bench must name at least one reviewer")

    def section(self, name: str):
        return {
            "offers": self.offers,
            "needs": self.needs,
            "excludes": self.excludes,
            "contextNotes": self.context_notes,
        }[name]


@dataclass(frozen=True)
class MatchIntent:
    """Typed ingress (a Transform, kind=matchIntent). Untrusted requester input:
    only closed-vocabulary tags and integer prices pass validation."""
    intent_id: str
    chamber_id: str
    fee_micros: int

    def __post_init__(self):
        if self.fee_micros <= 0:
            raise LawViolation("intent fee must be positive")


@dataclass(frozen=True)
class Grant:
    grant_id: str
    chamber_id: str
    worker_id: str
    purpose: str
    scope: frozenset            # dossier section names readable by the worker
    read_budget: int            # metered reads per run
    expires_tick: int


class GrantedView:
    """The only path from a worker to a dossier: purpose-bound, scoped,
    metered, expiring, and access-logged."""

    def __init__(self, chamber: Chamber, grant: Grant, tick: int):
        if grant.chamber_id != chamber.chamber_id:
            raise GrantViolation("grant/chamber mismatch")
        if grant.purpose != PURPOSE:
            raise GrantViolation(f"purpose_mismatch:{grant.purpose}")
        if tick > grant.expires_tick:
            raise GrantViolation("grant_expired")
        self._chamber = chamber
        self._grant = grant
        self._tick = tick
        self._reads_left = grant.read_budget
        self.access_log = []

    def read(self, section: str):
        if section not in self._grant.scope:
            self.access_log.append({"section": section, "granted": False})
            raise GrantViolation(f"out_of_scope:{section}")
        if self._reads_left <= 0:
            raise GrantViolation("read_budget_exhausted")
        self._reads_left -= 1
        self.access_log.append({"section": section, "granted": True})
        return self._chamber.section(section)


# ---------------------------------------------------------------------------
# Match cards and the static scan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MatchCard:
    """Bounded directional sink output: describes the SOURCE chamber, to be
    read (if released) by the READER chamber. Buckets and tags, mediated text."""
    source_chamber: str
    reader_chamber: str
    fit_bucket: str                 # "med" | "high" — never a number
    offers_matched: tuple           # source offers meeting reader needs
    needs_matched: tuple            # source needs met by reader offers
    rationale: str

    def __post_init__(self):
        if self.fit_bucket not in ("med", "high"):
            raise LawViolation("fit bucket must be med or high")
        if len(self.rationale) > RATIONALE_CHAR_CAP:
            raise LawViolation("rationale exceeds char cap")


def rationale_candidates(offers_matched, needs_matched, bucket: str) -> tuple:
    """The K fixed house projections of an approved card's structured fields.

    A pure function of channels that are already charged (matched tags,
    bucket) plus fixed public wording, so the candidate TEXT adds no content:
    the only information in the prose channel is WHICH candidate the source
    reviewer selected, and that ordinal is charged at log2(K). Always returns
    exactly RATIONALE_CANDIDATE_COUNT entries, digit-free, under the char cap.
    """
    offers = ", ".join(sorted(offers_matched)) or "an unnamed capability"
    needs = ", ".join(sorted(needs_matched)) or "an unnamed need"
    tail = (f" Fit bucket: {bucket}. House-projected text chosen by the "
            "source reviewer from a fixed candidate set; neither dossier "
            "prose nor worker prose crosses this card.")
    candidates = (
        f"A counterpart offers what you seek ({offers}) and seeks what you "
        f"offer ({needs}).{tail}",
        f"A counterpart offers what you seek ({offers}).{tail}",
        f"A counterpart seeks what you offer ({needs}).{tail}",
        f"A counterpart matches your filed intent.{tail}",
    )
    if len(candidates) != RATIONALE_CANDIDATE_COUNT:
        raise LawViolation("candidate set size drifted from its constant")
    return candidates


def static_scan(card: MatchCard, source_notes: str) -> list:
    """Deterministic defense-in-depth on a card before it may reach review.
    Not a semantic privacy proof; the receipt says so."""
    violations = []
    if any(ch.isdigit() for ch in card.rationale):
        violations.append("digits_in_rationale (denominator/count leakage)")
    for ch in card.rationale:
        if ch != MASK_CHAR and not (32 <= ord(ch) < 127):
            violations.append(f"non_printable_or_covert_char:{ord(ch)}")
            break
    spans = verbatim_spans(source_notes, card.rationale)
    if spans:
        violations.append(f"verbatim_span_from_source_notes:{spans[0]!r}")
    for tag in card.offers_matched + card.needs_matched:
        if tag not in VOCAB:
            violations.append(f"tag_outside_vocabulary:{tag}")
    return violations


# ---------------------------------------------------------------------------
# Guest workers (the admitted algorithms)
# ---------------------------------------------------------------------------

def _fit(view_a: GrantedView, view_b: GrantedView):
    a_offers, a_needs = view_a.read("offers"), view_a.read("needs")
    b_offers, b_needs = view_b.read("offers"), view_b.read("needs")
    a_excl, b_excl = view_a.read("excludes"), view_b.read("excludes")
    if (a_excl & (b_offers | b_needs)) or (b_excl & (a_offers | a_needs)):
        return {"veto": True}
    m1 = a_needs & b_offers      # what B offers A
    m2 = b_needs & a_offers      # what A offers B
    if not m1 or not m2:
        return {"score": 0, "m1": m1, "m2": m2}
    return {"score": len(m1) + len(m2), "m1": m1, "m2": m2}


def _rationale(offers_matched, needs_matched, bucket: str) -> str:
    return (
        "Purpose-blind fit: a counterpart offers what you seek ("
        + ", ".join(sorted(offers_matched))
        + ") and seeks what you offer ("
        + ", ".join(sorted(needs_matched))
        + f"). Fit bucket: {bucket}. Mediated text; no dossier prose crosses this card."
    )


def honest_worker(view_a: GrantedView, view_b: GrantedView, a_id: str, b_id: str):
    fit = _fit(view_a, view_b)
    if fit.get("veto") or fit.get("score", 0) < 3:
        return {"fit": fit, "cards": None}
    bucket = "high" if fit["score"] >= 4 else "med"
    card_to_a = MatchCard(
        source_chamber=b_id, reader_chamber=a_id, fit_bucket=bucket,
        offers_matched=tuple(sorted(fit["m1"])), needs_matched=tuple(sorted(fit["m2"])),
        rationale=_rationale(fit["m1"], fit["m2"], bucket))
    card_to_b = MatchCard(
        source_chamber=a_id, reader_chamber=b_id, fit_bucket=bucket,
        offers_matched=tuple(sorted(fit["m2"])), needs_matched=tuple(sorted(fit["m1"])),
        rationale=_rationale(fit["m2"], fit["m1"], bucket))
    return {"fit": fit, "cards": {a_id: card_to_a, b_id: card_to_b}}


def overreach_worker(view_a: GrantedView, view_b: GrantedView, a_id: str, b_id: str):
    """Adversarial: tries to read dossier prose its grant does not cover."""
    view_b.read("contextNotes")          # raises GrantViolation under scenario scope
    return honest_worker(view_a, view_b, a_id, b_id)


def quoting_worker(view_a: GrantedView, view_b: GrantedView, a_id: str, b_id: str):
    """Adversarial: grant includes contextNotes; smuggles a verbatim span into
    the outbound rationale. Blocked by the static scan."""
    notes_b = view_b.read("contextNotes")
    product = honest_worker(view_a, view_b, a_id, b_id)
    if product["cards"]:
        card = product["cards"][a_id]
        leaked = " ".join(notes_b.split()[:NGRAM_TOKENS + 1])
        product["cards"][a_id] = MatchCard(
            source_chamber=card.source_chamber, reader_chamber=card.reader_chamber,
            fit_bucket=card.fit_bucket, offers_matched=card.offers_matched,
            needs_matched=card.needs_matched,
            rationale=(card.rationale[: RATIONALE_CHAR_CAP - len(leaked) - 2] + " " + leaked))
    return product


def counting_worker(view_a: GrantedView, view_b: GrantedView, a_id: str, b_id: str):
    """Adversarial: embeds a rank/denominator into the rationale. Blocked."""
    product = honest_worker(view_a, view_b, a_id, b_id)
    if product["cards"]:
        card = product["cards"][a_id]
        product["cards"][a_id] = MatchCard(
            source_chamber=card.source_chamber, reader_chamber=card.reader_chamber,
            fit_bucket=card.fit_bucket, offers_matched=card.offers_matched,
            needs_matched=card.needs_matched,
            rationale=card.rationale[: RATIONALE_CHAR_CAP - 20] + " Ranked 1 of 12.")
    return product


# ---------------------------------------------------------------------------
# Ledgers: settlement (CreditMicros), crossings, attention, exposure
# ---------------------------------------------------------------------------

class SettlementLedger:
    def __init__(self):
        self.accounts = {}
        self.entries = []
        self._endowed = 0

    def open(self, name: str, endow: int = 0):
        if name in self.accounts:
            raise LawViolation(f"account exists: {name}")
        self.accounts[name] = endow
        self._endowed += endow

    def transfer(self, debit: str, credit: str, amount: int, memo: str, tick: int):
        if amount < 0:
            raise LawViolation("negative transfer")
        if self.accounts.get(debit, 0) < amount:
            raise LawViolation(f"insufficient funds: {debit} for {memo}")
        self.accounts[debit] -= amount
        self.accounts[credit] = self.accounts.get(credit, 0) + amount
        entry = {"entryId": f"le-{len(self.entries) + 1:04d}", "tick": tick,
                 "debit": debit, "credit": credit, "amountMicros": amount, "memo": memo}
        self.entries.append(entry)
        if sum(self.accounts.values()) != self._endowed:
            raise LawViolation("conservation broken")
        return entry

    def total(self) -> int:
        return sum(self.accounts.values())

    def conserved(self) -> bool:
        return self.total() == self._endowed


class CrossingLedger:
    """No crossing without a LedgerEntry: every byte delivered to a chamber
    is recorded here first."""

    def __init__(self):
        self.entries = []

    def record(self, tick: int, kind: str, reader: str, source_attribution: str,
               payload: bytes):
        entry = {"entryId": f"xl-{len(self.entries) + 1:04d}", "tick": tick,
                 "kind": kind, "readerChamber": reader,
                 "sourceAttribution": source_attribution,
                 "payloadSha256": sha256_hex(payload), "payloadLen": len(payload)}
        self.entries.append(entry)
        return entry


class AttentionBook:
    def __init__(self):
        self.budgets = {}
        self.spent = {}
        self.events = []

    def enroll(self, owner: str, budget: int):
        self.budgets[owner] = budget
        self.spent[owner] = 0

    def interrupt(self, owner: str, tick: int, memo: str) -> bool:
        if self.spent[owner] >= self.budgets[owner]:
            self.events.append({"tick": tick, "owner": owner, "memo": memo,
                                "granted": False, "cause": "attention_exhausted"})
            return False
        self.spent[owner] += 1
        self.events.append({"tick": tick, "owner": owner, "memo": memo, "granted": True})
        return True


class ExposureBook:
    """Lifetime (source chamber x reader entity) capacity accounts, millibits."""

    def __init__(self, default_budget: int = DEFAULT_EXPOSURE_BUDGET_MILLIBITS,
                 meter: KernelMeter | None = None):
        self.default_budget = default_budget
        self.budgets = {}
        self.entries = []
        self._meter = meter or KernelMeter(
            node="intro_clearing", issuer="house", ledger=Ledger())

    def _key(self, source: str, reader_entity: str):
        return (source, reader_entity)

    def _kernel_key(self, source: str, reader_entity: str):
        return exposure_key(source, reader_entity)

    def _ensure_account(self, source: str, reader_entity: str):
        key = self._kernel_key(source, reader_entity)
        if not self._meter.has(key):
            self._meter.register(
                key,
                subject_entropy_mbits=DECLARED_SOURCE_ENTROPY_MBITS,
                ceiling_mbits=DECLARED_SOURCE_ENTROPY_MBITS,
            )
        return key

    def _millibits(self, source: str, reader_entity: str) -> int:
        acct = self._meter.ledger.fold().get(
            self._kernel_key(source, reader_entity))
        return 0 if acct is None else acct.cumulative_mbits

    @property
    def charged(self):
        rows = {}
        for key, acct in self._meter.ledger.fold().items():
            if len(key) == 3 and key[0] == "exp":
                rows[(key[1], key[2])] = acct.cumulative_mbits
        return rows

    def budget(self, source: str, reader_entity: str) -> int:
        return self.budgets.get(self._key(source, reader_entity), self.default_budget)

    def would_exceed(self, source: str, reader_entity: str, millibits: int) -> bool:
        return (self._millibits(source, reader_entity) + millibits
                > self.budget(source, reader_entity))

    def charge(self, source: str, reader_entity: str, millibits: int, memo: str,
               tick: int, estimate: CapacityEstimate | None = None) -> str:
        """Charge the account and return the recorded ChargeEvent's ledger
        id — the exact work receipt a settlement release binds to."""
        if estimate is None:
            estimate = schema_capacity_estimate(
                channel="exposure.side_channel",
                side_channel_mbits=millibits)
        if estimate.total_mbits != millibits:
            raise LawViolation("exposure estimate total does not match charge")
        key = self._ensure_account(source, reader_entity)
        decision, charge_id = self._meter.charge_recorded(
            key, estimate, SCHEMA_CEILING_ATTESTATION, tick=tick)
        assert decision.accepted, decision
        mb = self._millibits(source, reader_entity)
        self.entries.append({"tick": tick, "sourceChamber": source,
                             "readerEntity": reader_entity, "millibits": millibits,
                             "memo": memo,
                             "overBudget": mb > self.budget(source, reader_entity)})
        return charge_id

    def snapshot(self):
        rows = []
        for (source, reader), mb in sorted(self.charged.items()):
            rows.append({"sourceChamber": source, "readerEntity": reader,
                         "millibitsCharged": mb,
                         "budgetMillibits": self.budget(source, reader),
                         "overBudget": mb > self.budget(source, reader),
                         "sybilUndercountRisk": True})
        return rows


class ReviewerMemoryBook:
    """Lifetime (source chamber x reviewer entity) memory accounts, in
    millibit CEILINGS. Strictly monotone: memory is not revocable, so
    nothing here is ever refunded — a declined review, a refused crossing,
    a slashed worker all leave the charge standing. Exhaustion does not
    erase anything either; it only stops that reviewer from being seated
    again for that source."""

    def __init__(self, default_budget: int = DEFAULT_REVIEWER_MEMORY_BUDGET_MILLIBITS,
                 meter: KernelMeter | None = None):
        self.default_budget = default_budget
        self.budgets = {}
        self.entries = []
        self._meter = meter or KernelMeter(
            node="intro_clearing", issuer="house", ledger=Ledger())

    def _key(self, source: str, reviewer: str):
        return (source, reviewer)

    def _kernel_key(self, source: str, reviewer: str):
        return ("mem", source, reviewer)

    def _ensure_account(self, source: str, reviewer: str):
        key = self._kernel_key(source, reviewer)
        if not self._meter.has(key):
            self._meter.register(
                key,
                subject_entropy_mbits=DECLARED_SOURCE_ENTROPY_MBITS,
                ceiling_mbits=DECLARED_SOURCE_ENTROPY_MBITS,
            )
        return key

    def _millibits(self, source: str, reviewer: str) -> int:
        acct = self._meter.ledger.fold().get(self._kernel_key(source, reviewer))
        return 0 if acct is None else acct.cumulative_mbits

    @property
    def charged(self):
        rows = {}
        for key, acct in self._meter.ledger.fold().items():
            if len(key) == 3 and key[0] == "mem":
                rows[(key[1], key[2])] = acct.cumulative_mbits
        return rows

    def budget(self, source: str, reviewer: str) -> int:
        return self.budgets.get(self._key(source, reviewer), self.default_budget)

    def would_exceed(self, source: str, reviewer: str, millibits: int) -> bool:
        return self._millibits(source, reviewer) + millibits > self.budget(source, reviewer)

    def charge(self, source: str, reviewer: str, millibits: int,
               artifacts: list, memo: str, tick: int,
               estimate: CapacityEstimate | None = None):
        if millibits < 0:
            raise LawViolation("reviewer memory never decreases")
        if estimate is None:
            estimate = schema_capacity_estimate(
                channel="reviewer_memory.schema_ceiling",
                text_mbits=millibits)
        if estimate.total_mbits != millibits:
            raise LawViolation("reviewer memory estimate total does not match charge")
        key = self._ensure_account(source, reviewer)
        decision = self._meter.charge(
            key, estimate, SCHEMA_CEILING_ATTESTATION, tick=tick)
        assert decision.accepted, decision
        self.entries.append({"tick": tick, "sourceChamber": source,
                             "reviewerEntity": reviewer,
                             "millibitsCeiling": millibits,
                             "artifactsSeen": list(artifacts),
                             "memo": memo})

    def snapshot(self):
        rows = []
        for (source, reviewer), mb in sorted(self.charged.items()):
            budget = self.budget(source, reviewer)
            rows.append({"sourceChamber": source, "reviewerEntity": reviewer,
                         "millibitsCeilingCharged": mb,
                         "budgetMillibits": budget,
                         "headroomMillibits": budget - mb,
                         "memoryNotRevocable": True})
        return rows


def coalition_audit(exposure: ExposureBook, entity_map: dict) -> dict:
    """Re-score the lifetime (source chamber x DECLARED reader entity) ledger
    under a hypothesis about beneficial ownership (declared -> true entity;
    unmapped entities pass through unchanged).

    Pure audit. The hypothesis is an INPUT — the house cannot verify
    beneficial ownership, so this never gates: everything it re-scores has
    already settled. An undercount finding is a merged account that exceeds
    the single-entity budget while every constituent declared account sits
    under its own budget — exposure invisible to the declared view, visible
    only under the hypothesis. The single-entity budget is the max of the
    constituent budgets (conservative: the budget an honest single reader
    would most generously have been given).
    """
    declared = exposure.snapshot()
    merged = {}
    for row in declared:
        true_entity = entity_map.get(row["readerEntity"], row["readerEntity"])
        slot = merged.setdefault((row["sourceChamber"], true_entity), {
            "millibits": 0, "declaredEntities": [], "budgets": [],
            "constituentOverruns": 0})
        slot["millibits"] += row["millibitsCharged"]
        slot["declaredEntities"].append(row["readerEntity"])
        slot["budgets"].append(row["budgetMillibits"])
        slot["constituentOverruns"] += 1 if row["overBudget"] else 0
    rows = []
    for (source, true_entity), slot in sorted(merged.items()):
        single_budget = max(slot["budgets"])
        rows.append({
            "sourceChamber": source,
            "hypothesizedEntity": true_entity,
            "declaredEntities": sorted(slot["declaredEntities"]),
            "identitiesUsed": len(slot["declaredEntities"]),
            "millibitsCharged": slot["millibits"],
            "singleEntityBudgetMillibits": single_budget,
            "effectiveBudgetUnderFragmentation": sum(slot["budgets"]),
            "overBudgetIfOneEntity": slot["millibits"] > single_budget,
            "constituentsAllUnderBudget": slot["constituentOverruns"] == 0,
        })
    findings = [row for row in rows
                if row["identitiesUsed"] > 1 and row["overBudgetIfOneEntity"]
                and row["constituentsAllUnderBudget"]]
    return {
        "hypothesis": dict(sorted(entity_map.items())),
        "declaredAccounts": declared,
        "mergedAccounts": rows,
        "undercountFindings": findings,
        "auditNonClaims": [
            {"key": "hypothesisNotDiscovery",
             "text": "The ownership grouping is an input. The house cannot "
                     "verify beneficial ownership; declarations remain "
                     "untrusted."},
            {"key": "noRetroGating",
             "text": "Everything this audit re-scores has already settled. "
                     "Budgets remain tripwires, not certificates."},
            {"key": "correlationIsNotProof",
             "text": "Similar dossiers or timing may suggest common "
                     "ownership; this audit asserts nothing about how the "
                     "hypothesis was formed."},
        ],
    }


# ---------------------------------------------------------------------------
# The clearing house
# ---------------------------------------------------------------------------

@dataclass
class Attempt:
    attempt_id: str
    a: str
    b: str
    worker_id: str
    trace: list = field(default_factory=list)
    outcome: str = "pending"      # cleared | denied | no_card | failed_closed
    cause: str = ""
    cards_approved: dict = field(default_factory=dict)   # reader -> MatchCard
    cards_proposed: dict = field(default_factory=dict)   # reader -> MatchCard
    decisions: dict = field(default_factory=dict)        # source -> release|redact|decline
    ordinals: dict = field(default_factory=dict)         # source -> selected candidate index
    reviewers: dict = field(default_factory=dict)        # source -> seated reviewer entity
    access_logs: dict = field(default_factory=dict)      # chamber -> [reads]
    interrupted: set = field(default_factory=set)        # owners whose reviewer worked

    def gate(self, name: str, status: str, cause: str = ""):
        self.trace.append({"gate": name, "status": status, "cause": cause})


class ClearingHouse:
    HOUSE_ENTITY = "entity:house"

    def __init__(self, exposure_budget: int = DEFAULT_EXPOSURE_BUDGET_MILLIBITS,
                 reviewer_memory_budget: int = DEFAULT_REVIEWER_MEMORY_BUDGET_MILLIBITS):
        self.tick = 0
        self.chambers = {}
        self.intents = {}
        self.grants = {}          # (chamber_id, worker_id) -> Grant
        self.workers = {}         # worker_id -> {"entity", "fn", "slashed"}
        self.ledger = SettlementLedger()
        self.crossings = CrossingLedger()
        self.attention = AttentionBook()
        self.kernel_ledger = Ledger()
        self.kernel_meter = KernelMeter(
            node="intro_clearing", issuer="house", ledger=self.kernel_ledger)
        self.exposure = ExposureBook(exposure_budget, self.kernel_meter)
        self.reviewer_memory = ReviewerMemoryBook(
            reviewer_memory_budget, self.kernel_meter)
        self.mailboxes = {}
        self.attempts = []
        self.windows = []
        self.party = None   # opt-in kernel-settled consumer lane; open_party_lane
        self.ledger.open("house")
        self.ledger.open("slash_pool")

    # -- registration ------------------------------------------------------

    def enroll(self, chamber: Chamber):
        if chamber.chamber_id in self.chambers:
            raise LawViolation("chamber already enrolled")
        self.chambers[chamber.chamber_id] = chamber
        self.ledger.open(f"owner:{chamber.chamber_id}", OWNER_ENDOWMENT)
        self.attention.enroll(chamber.chamber_id, chamber.attention_budget)
        self.mailboxes[chamber.chamber_id] = []

    def register_worker(self, worker_id: str, entity: str, fn):
        self.workers[worker_id] = {"entity": entity, "fn": fn, "slashed": False}
        self.ledger.open(f"worker:{worker_id}", WORKER_ENDOWMENT)
        self.ledger.open(f"stake:{worker_id}")
        self.ledger.transfer(f"worker:{worker_id}", f"stake:{worker_id}",
                             WORKER_STAKE, "worker stake posted", self.tick)

    def file_intent(self, chamber_id: str, fee_micros: int) -> MatchIntent:
        if chamber_id in self.intents:
            raise LawViolation("one active intent per chamber in this slice")
        intent = MatchIntent(
            intent_id=f"intent-{letters_token(f'intent:{chamber_id}:t{self.tick}', 5)}",
            chamber_id=chamber_id, fee_micros=fee_micros)
        self.intents[chamber_id] = intent
        self.ledger.open(f"escrow:{intent.intent_id}")
        self.ledger.transfer(f"owner:{chamber_id}", f"escrow:{intent.intent_id}",
                             fee_micros, "intent fee escrowed", self.tick)
        return intent

    def issue_grant(self, chamber_id: str, worker_id: str, scope, read_budget: int,
                    expires_tick: int, purpose: str = PURPOSE) -> Grant:
        grant = Grant(grant_id=f"grant-{letters_token(f'grant:{chamber_id}:{worker_id}:t{self.tick}', 5)}",
                      chamber_id=chamber_id, worker_id=worker_id, purpose=purpose,
                      scope=frozenset(scope), read_budget=read_budget,
                      expires_tick=expires_tick)
        self.grants[(chamber_id, worker_id)] = grant
        return grant

    # -- the party lane: consumer fee legs on charge-settlement/2 ------------

    def open_party_lane(self, platform: str = "platform:calls",
                        owner_fund_ucr: int = PARTY_OWNER_ENDOWMENT_UCR,
                        platform_fund_ucr: int = PARTY_PLATFORM_FUND_UCR):
        """Open the party-matchmaker consumer lane on the REAL kernel
        settlement. Deposits are declared inflows on the SAME mergeable
        ledger the exposure meter writes; from here on every cleared
        introduction carries a 50-cent unconditional raise (escrow+release
        against the ring's charge event) and a $5 outcome escrow (released
        only on a bonded platform_log attestation of the qualifying call,
        refunded to the payer at expiry otherwise). Enroll chambers BEFORE
        opening the lane: only enrolled owners are endowed; an unfunded
        payer's escrow refuses with an overdraft, it does not float."""
        if self.party is not None:
            raise LawViolation("party lane already open")
        bank = SettlementIssuer(issuer="house_bank", ledger=self.kernel_ledger)
        for cid in sorted(self.chambers):
            bank.deposit(f"owner:{cid}", owner_fund_ucr, self.tick)
        bank.deposit(platform, platform_fund_ucr, self.tick)
        self.party = {
            "bank": bank,
            "platform": platform,
            "rings": [],        # unconditional 50-cent raise receipts
            "contingent": {},   # attempt_id -> reader -> contingent leg
        }

    def _ring_key(self, reader: str, window_id: str):
        """The kernel's attention key family: protected party = the reader
        whose bell rings, regeneration = the window epoch in the key."""
        return ("att", reader, "house", window_id)

    def _party_ring(self, reader: str, window_id: str):
        """Ring the reader's bell for one card delivery: an attention charge
        on the kernel meter, BEFORE the exposure charge (the ordering law:
        a refused ring must leak nothing about the third party). The epoch
        budget is sized to the maximum rings a window can produce, so a
        refusal here is an invariant break, not a market event."""
        key = self._ring_key(reader, window_id)
        if not self.kernel_meter.has(key):
            budget = RING_INTERRUPT_UNITS * max(len(self.chambers), 1)
            self.kernel_meter.register(
                key, subject_entropy_mbits=budget, ceiling_mbits=budget)
        decision, ring_id = self.kernel_meter.charge_recorded(
            key,
            CapacityEstimate(RING_INTERRUPT_UNITS, 0, 0, 0, 0, "notify"),
            RING_ESTIMATOR, tick=self.tick)
        if not decision.accepted:
            raise LawViolation(
                f"delivery ring refused past a sized epoch budget: {decision}")
        return key, ring_id

    def _party_raise(self, att: "Attempt", card: MatchCard, reader: str,
                     ring_key, ring_id: str):
        """Leg 1 — 50 cents, unconditional-to-raise. The side being
        introduced pays the bell's owner (recipient-as-fee-beneficiary,
        G6); the release references the ring's exact charge event id, so
        the payment provably paid for that ring and nothing else."""
        bank = self.party["bank"]
        esc = bank.escrow(
            payer=f"owner:{card.source_chamber}", payee=f"owner:{reader}",
            amount_ucr=RAISE_PRICE_UCR, charge_keys=[ring_key],
            expires_tick=self.tick + OUTCOME_TTL_TICKS, tick=self.tick)
        rel = bank.release(esc, RAISE_PRICE_UCR, [ring_id], tick=self.tick)
        self.party["rings"].append({
            "attemptId": att.attempt_id, "reader": reader,
            "payer": f"owner:{card.source_chamber}",
            "payee": f"owner:{reader}",
            "ringKey": list(ring_key), "ringChargeId": ring_id,
            "escrowId": esc.id, "releaseId": rel.id,
            "priceUcr": RAISE_PRICE_UCR,
        })

    def _party_contingent(self, att: "Attempt", intro_charge_ids: dict):
        """Leg 2 — $5 on outcome, one escrow per matched party. The escrow
        binds to the intro card's metered exposure account and its later
        release must reference that card's charge event id: first-contact
        attribution as ledger arithmetic. default_on_expiry is forced to
        refund_to_payer by the kernel (SPEC §7.1): no talk = the payer
        keeps the money, mechanically, with no one's cooperation."""
        bank = self.party["bank"]
        legs = {}
        for reader in sorted(att.cards_approved):
            card = att.cards_approved[reader]
            cond = OutcomeCondition(
                metric=OUTCOME_METRIC,           # presence, not engagement
                lane=OUTCOME_LANE, quorum=OUTCOME_QUORUM,
                min_independence=OUTCOME_MIN_INDEPENDENCE,
                min_bond_ucr=OUTCOME_MIN_BOND_UCR,
                contest_ticks=OUTCOME_CONTEST_TICKS)
            esc = bank.escrow(
                payer=f"owner:{reader}", payee=f"worker:{att.worker_id}",
                amount_ucr=OUTCOME_FEE_UCR,
                charge_keys=[exposure_key(card.source_chamber,
                                          self.chambers[reader].owner_entity)],
                expires_tick=self.tick + OUTCOME_TTL_TICKS, tick=self.tick,
                outcome=cond)
            legs[reader] = {
                "escrow": esc,
                "introChargeId": intro_charge_ids[reader],
                "attestations": [],
                "status": "pending",
            }
        self.party["contingent"][att.attempt_id] = legs

    def _party_legs(self, attempt_id: str) -> dict:
        if self.party is None:
            raise LawViolation("party lane not open")
        legs = self.party["contingent"].get(attempt_id)
        if not legs:
            raise LawViolation(f"no contingent legs for attempt {attempt_id}")
        return legs

    def party_attest_call(self, attempt_id: str, *, claim: str = "occurred",
                          evidence: str = "", attestor: str | None = None,
                          bond_ucr: int = OUTCOME_MIN_BOND_UCR,
                          lane: str = OUTCOME_LANE,
                          independence: str = OUTCOME_MIN_INDEPENDENCE):
        """The call platform posts one bonded, contestable outcome fact per
        contingent leg. The bond is real value locked by the fold itself;
        a false claim is slashable only by strictly better evidence, and
        an equal-lane contest blocks payment without slashing anybody."""
        legs = self._party_legs(attempt_id)
        attestor = attestor or self.party["platform"]
        self.tick += 1
        out = []
        for reader in sorted(legs):
            leg = legs[reader]
            ev = attest_outcome(
                self.kernel_ledger, leg["escrow"], attestor, claim, lane,
                independence, bond_ucr, tick=self.tick, evidence=evidence)
            leg["attestations"].append(ev)
            out.append(ev)
        return out

    def party_settle_outcome(self, attempt_id: str):
        """After the contest window: release each $5 against the intro
        card's charge event id (the first-contact receipt) plus the quorum
        proof, then return the proof's bonds. The kernel refuses this live
        — and convicts it after merge (S9) — without a hardened
        platform_log quorum."""
        legs = self._party_legs(attempt_id)
        bank = self.party["bank"]
        latest = max(a.tick for leg in legs.values()
                     for a in leg["attestations"])
        self.tick = max(self.tick, latest + OUTCOME_CONTEST_TICKS) + 1
        releases = []
        for reader in sorted(legs):
            leg = legs[reader]
            proof = [a for a in leg["attestations"]
                     if a.claim == "occurred" and a.lane == OUTCOME_LANE]
            rel = bank.release(
                leg["escrow"], OUTCOME_FEE_UCR, [leg["introChargeId"]],
                tick=self.tick, attestation_ids=[a.id for a in proof])
            leg["status"] = "released"
            releases.append(rel)
            for a in proof:
                resolve_bond(self.kernel_ledger, a, a.attestor,
                             "return_to_attestor", a.bond_ucr, tick=self.tick)
        return releases

    def party_expire_refund(self, attempt_id: str):
        """No talk: past expiry, ANY party exercises the escrow's declared
        default. With no quorum proof the direction is the refund — the
        payer keeps the $5 without the issuer's cooperation (anti-holdup,
        SPEC §7.4)."""
        legs = self._party_legs(attempt_id)
        expiry = max(leg["escrow"].expires_tick for leg in legs.values())
        self.tick = max(self.tick, expiry) + 1
        events = []
        for reader in sorted(legs):
            leg = legs[reader]
            ev = resolve_default(
                self.kernel_ledger, leg["escrow"], submitter=f"owner:{reader}",
                amount_ucr=OUTCOME_FEE_UCR, tick=self.tick)
            leg["status"] = "refunded"
            events.append(ev)
        return events

    def party_court_view(self) -> dict:
        """Stranger-recomputable view of the party lane: the /2 canonical
        fold, the settlement audit codes, and the conservation identity —
        every number re-derivable from the one JSONL artifact."""
        if self.party is None:
            raise LawViolation("party lane not open")
        lhs, rhs = conservation_identity(self.kernel_ledger)
        contingent = {}
        for attempt_id, legs in sorted(self.party["contingent"].items()):
            contingent[attempt_id] = {
                reader: {
                    "escrowId": leg["escrow"].id,
                    "payer": leg["escrow"].payer,
                    "payee": leg["escrow"].payee,
                    "amountUcr": leg["escrow"].amount_ucr,
                    "expiresTick": leg["escrow"].expires_tick,
                    "metric": leg["escrow"].outcome.metric,
                    "lane": leg["escrow"].outcome.lane,
                    "chargeKeys": [list(k) for k in leg["escrow"].charge_keys],
                    "introChargeId": leg["introChargeId"],
                    "attestationIds": [a.id for a in leg["attestations"]],
                    "status": leg["status"],
                }
                for reader, leg in sorted(legs.items())
            }
        return {
            "platform": self.party["platform"],
            "rings": list(self.party["rings"]),
            "contingent": contingent,
            "settlementV2": settlement_fold_canonical_v2(self.kernel_ledger),
            "settlementAuditCodes": audit_settlement_codes(self.kernel_ledger),
            "conservation": {"lhs": lhs, "rhs": rhs, "holds": lhs == rhs},
            "gaps": PARTY_LANE_GAPS,
        }

    # -- helpers -----------------------------------------------------------

    def _escrow(self, chamber_id: str) -> str:
        return f"escrow:{self.intents[chamber_id].intent_id}"

    def _escrow_balance(self, chamber_id: str) -> int:
        return self.ledger.accounts[self._escrow(chamber_id)]

    def _slash(self, worker_id: str, memo: str):
        stake = self.ledger.accounts[f"stake:{worker_id}"]
        if stake > 0:
            self.ledger.transfer(f"stake:{worker_id}", "slash_pool", stake, memo, self.tick)
        self.workers[worker_id]["slashed"] = True

    def _pair_cost(self, payer: str, counterpart: str) -> int:
        return self.chambers[counterpart].reserve_micros + WORKER_FEE_SIDE + HOUSE_FEE_SIDE

    def _intro_millibits(self, card: MatchCard) -> int:
        tags = len(card.offers_matched) + len(card.needs_matched)
        return (BUCKET_MILLIBITS + PRESENCE_MILLIBITS
                + identity_millibits(len(self.chambers)) + tags * TAG_MILLIBITS
                + ORDINAL_MILLIBITS)

    def _intro_estimate(self, card: MatchCard) -> CapacityEstimate:
        tags = len(card.offers_matched) + len(card.needs_matched)
        return schema_capacity_estimate(
            channel="intro_card",
            enum_value_mbits=(BUCKET_MILLIBITS + tags * TAG_MILLIBITS
                              + ORDINAL_MILLIBITS),
            side_channel_mbits=(PRESENCE_MILLIBITS
                                + identity_millibits(len(self.chambers))),
        )

    def _side_channel_estimate(self, channel: str,
                               millibits: int) -> CapacityEstimate:
        return schema_capacity_estimate(
            channel=channel,
            side_channel_mbits=millibits,
        )

    def _review_memory_schedule(self) -> dict:
        """Per-review memory charge, itemized by channel. Content-independent
        ceilings: seating a reviewer costs the same whatever the card says
        and whatever the reviewer decides, so the charge leaks nothing."""
        return {
            "structuredFieldsCeiling": (BUCKET_MILLIBITS + PRESENCE_MILLIBITS
                                        + identity_millibits(len(self.chambers))),
            "tagsSchemaCeiling": TAGS_SCHEMA_CEILING_MILLIBITS,
            "advisoryProseCeiling": ADVISORY_PROSE_CEILING_MILLIBITS,
            "candidateSetSelectionCapacity": ORDINAL_MILLIBITS,
        }

    def _review_memory_total(self) -> int:
        return sum(self._review_memory_schedule().values())

    def _review_memory_estimate(self) -> CapacityEstimate:
        return schema_capacity_estimate(
            channel="reviewer_memory.schema_ceiling",
            enum_value_mbits=(BUCKET_MILLIBITS + TAGS_SCHEMA_CEILING_MILLIBITS
                              + ORDINAL_MILLIBITS),
            text_mbits=ADVISORY_PROSE_CEILING_MILLIBITS,
            side_channel_mbits=(PRESENCE_MILLIBITS
                                + identity_millibits(len(self.chambers))),
        )

    def _seat_reviewer(self, source: Chamber):
        """First bench reviewer with headroom for a full review, checked
        BEFORE anything is shown. None means the bench is exhausted."""
        total = self._review_memory_total()
        for name in source.reviewer_bench:
            reviewer = f"reviewer:{source.chamber_id}:{name}"
            if not self.reviewer_memory.would_exceed(source.chamber_id,
                                                     reviewer, total):
                return reviewer, total
        return None, total

    def _review_artifacts(self, card: MatchCard) -> list:
        """Itemize what the seated reviewer is shown, hashed not stored.
        Candidates are itemized from the proposed fields (the superset the
        head may absorb); redaction happens after seeing them."""
        candidates = rationale_candidates(card.offers_matched,
                                          card.needs_matched, card.fit_bucket)
        return [
            {"kind": "proposed_card_structured",
             "sha256": sha256_hex(canonical_json({
                 "fitBucket": card.fit_bucket,
                 "offersMatched": list(card.offers_matched),
                 "needsMatched": list(card.needs_matched),
                 "readerChamber": card.reader_chamber}))},
            {"kind": "advisory_worker_rationale",
             "sha256": sha256_hex(card.rationale),
             "chars": len(card.rationale)},
            {"kind": "candidate_set",
             "sha256": sha256_hex(canonical_json(list(candidates))),
             "count": RATIONALE_CANDIDATE_COUNT},
        ]

    def _release_card(self, source: Chamber, card_after: MatchCard):
        """Build the card that may actually cross: structured fields from the
        reviewed card, rationale replaced by the house candidate the source
        reviewer selected. Worker prose ends here — advisory, never crossing.
        A scan hit on house-authored text is an invariant break, not a market
        event, so it refuses loudly instead of failing closed."""
        candidates = rationale_candidates(card_after.offers_matched,
                                          card_after.needs_matched,
                                          card_after.fit_bucket)
        ordinal = source.rationale_ordinal
        release = MatchCard(
            source_chamber=card_after.source_chamber,
            reader_chamber=card_after.reader_chamber,
            fit_bucket=card_after.fit_bucket,
            offers_matched=card_after.offers_matched,
            needs_matched=card_after.needs_matched,
            rationale=candidates[ordinal])
        violations = static_scan(release, source.context_notes)
        if violations:
            raise LawViolation(
                f"house candidate failed its own scan: {violations[0]}")
        return ordinal, release

    # -- one pairwise attempt ----------------------------------------------

    def _attempt(self, a: str, b: str, worker_id: str) -> Attempt:
        att = Attempt(attempt_id=f"att-{letters_token(a + '|' + b + '|' + str(self.tick), 8)}",
                      a=a, b=b, worker_id=worker_id)
        self.attempts.append(att)
        ch_a, ch_b = self.chambers[a], self.chambers[b]
        att.gate("intake", "pass")

        # Role separation over beneficial entities, not ids.
        worker = self.workers[worker_id]
        if worker["entity"] in (ch_a.owner_entity, ch_b.owner_entity, self.HOUSE_ENTITY):
            raise RoleSeparationError(
                f"worker {worker_id} shares a beneficial entity with a party or the house")
        att.gate("role_separation", "pass")

        # Priced introductions clear before they surface: fee >= counterparty
        # reserve, and escrow headroom for the full pair cost, both directions.
        fee_a, fee_b = self.intents[a].fee_micros, self.intents[b].fee_micros
        if (fee_a < ch_b.reserve_micros or fee_b < ch_a.reserve_micros
                or self._escrow_balance(a) < self._pair_cost(a, b)
                or self._escrow_balance(b) < self._pair_cost(b, a)):
            att.gate("reserve_clearing", "stop", "reserve_not_cleared")
            att.outcome, att.cause = "no_card", "reserve_not_cleared"
            return att
        att.gate("reserve_clearing", "pass")

        # No grant, no run.
        grant_a = self.grants.get((a, worker_id))
        grant_b = self.grants.get((b, worker_id))
        if grant_a is None or grant_b is None:
            att.gate("grants_check", "stop", "grant_missing")
            att.outcome, att.cause = "failed_closed", "grant_missing"
            return att
        att.gate("grants_check", "pass")

        # Bounded worker run through metered granted views. A grant that
        # cannot even open (expired, wrong purpose, wrong chamber) fails
        # closed WITHOUT a slash: the worker never ran, so there is no
        # overreach to punish — slashing is for worker conduct only.
        try:
            view_a = GrantedView(ch_a, grant_a, self.tick)
            view_b = GrantedView(ch_b, grant_b, self.tick)
        except GrantViolation as exc:
            att.gate("worker_run", "stop", f"grant_unusable:{exc}")
            att.outcome, att.cause = "failed_closed", "grant_unusable"
            return att
        try:
            product = worker["fn"](view_a, view_b, a, b)
        except GrantViolation as exc:
            att.access_logs = {a: view_a.access_log, b: view_b.access_log}
            att.gate("worker_run", "stop", f"grant_violation:{exc}")
            att.outcome, att.cause = "failed_closed", "grant_violation"
            self._slash(worker_id, f"stake slashed: grant violation in {att.attempt_id}")
            return att
        att.access_logs = {a: view_a.access_log, b: view_b.access_log}
        att.gate("worker_run", "pass")

        # House re-derives fit from its own registry: worker output is untrusted.
        true_fit = self._house_fit(ch_a, ch_b)
        if true_fit.get("veto"):
            att.gate("scoring", "stop", "vetoed_by_exclusion")
            att.outcome, att.cause = "no_card", "vetoed"
            return att
        score = true_fit.get("score", 0)
        if score == 0:
            att.gate("scoring", "stop", "no_coincidence")
            att.outcome, att.cause = "no_card", "no_coincidence"
            return att
        if score < 3:
            att.gate("scoring", "stop", "near_miss")
            att.outcome, att.cause = "no_card", "near_miss"
            return att
        att.gate("scoring", "pass")

        cards = product.get("cards") or {}
        if set(cards) != {a, b}:
            att.gate("carding", "stop", "worker_withheld_cards")
            att.outcome, att.cause = "failed_closed", "worker_withheld_cards"
            self._slash(worker_id, f"stake slashed: withheld cards in {att.attempt_id}")
            return att
        bucket = "high" if score >= 4 else "med"
        for reader, card in sorted(cards.items()):
            source = self.chambers[card.source_chamber]
            ok_tags = (set(card.offers_matched) <= (true_fit["m1"] | true_fit["m2"])
                       and set(card.needs_matched) <= (true_fit["m1"] | true_fit["m2"]))
            if card.fit_bucket != bucket or not ok_tags:
                att.gate("carding", "stop", "worker_output_forged")
                att.outcome, att.cause = "failed_closed", "worker_output_forged"
                self._slash(worker_id, f"stake slashed: forged output in {att.attempt_id}")
                return att
        att.cards_proposed = dict(cards)
        att.gate("carding", "pass")

        # Deterministic static scan, per direction, against SOURCE prose.
        for reader in sorted(cards):
            card = cards[reader]
            violations = static_scan(card, self.chambers[card.source_chamber].context_notes)
            if violations:
                att.gate("static_scan", "stop", violations[0])
                att.outcome, att.cause = "failed_closed", "scan_violation"
                self._slash(worker_id, f"stake slashed: scan violation in {att.attempt_id}")
                return att
        att.gate("static_scan", "pass")

        # Cards passed scan into review: worker fee settles now
        # (owner-internal acceptance), from each side's escrow.
        for side in (a, b):
            self.ledger.transfer(self._escrow(side), f"worker:{worker_id}",
                                 WORKER_FEE_SIDE, f"worker fee {att.attempt_id}", self.tick)
            self.ledger.transfer(self._escrow(side), "house",
                                 HOUSE_FEE_SIDE, f"house fee {att.attempt_id}", self.tick)

        # Attention: each direction interrupts the SOURCE side's reviewer.
        # Exhaustion fails closed for disclosure. The reader side buys the
        # source side's attention at reserve — explanation not included.
        for reader in sorted(cards):
            source = cards[reader].source_chamber
            if not self.attention.interrupt(source, self.tick,
                                            f"outbound review {att.attempt_id}"):
                att.gate("attention", "stop", f"attention_exhausted:{source}")
                att.outcome, att.cause = "failed_closed", "attention_exhausted"
                return att
            att.interrupted.add(source)
            self.ledger.transfer(self._escrow(reader), f"owner:{source}",
                                 self.chambers[source].reserve_micros,
                                 f"attention purchase {att.attempt_id}", self.tick)
        att.gate("attention", "pass")

        # Source-side outbound review. A reviewer must be SEATED before
        # anything is shown: the memory account is checked first, charged
        # second (irrevocably, whatever the decision), and only then does
        # the reviewer see the card. An exhausted bench fails closed.
        approved = {}
        for reader in sorted(cards):
            card = cards[reader]
            source = self.chambers[card.source_chamber]
            seat, memory_total = self._seat_reviewer(source)
            if seat is None:
                att.gate("review", "stop",
                         f"reviewer_memory_exhausted:{source.chamber_id}")
                att.outcome, att.cause = "failed_closed", "reviewer_memory_exhausted"
                return att
            self.reviewer_memory.charge(
                source.chamber_id, seat, memory_total,
                self._review_artifacts(card),
                f"outbound review {att.attempt_id} -> {reader}", self.tick,
                estimate=self._review_memory_estimate())
            att.reviewers[source.chamber_id] = seat
            decision, card_after = self._review_outbound(source, card)
            att.decisions[card.source_chamber] = decision
            if decision != "decline":
                ordinal, release = self._release_card(source, card_after)
                att.ordinals[card.source_chamber] = ordinal
                approved[reader] = release
        if len(att.decisions) < 2 or any(d == "decline" for d in att.decisions.values()):
            att.gate("review", "stop", "review_declined")
            att.outcome, att.cause = "denied", "review_declined"
            return att
        att.gate("review", "pass")

        # Numeric accountant: structured channels charged at adversarial max
        # against the lifetime (source x reader-entity) account. Over budget
        # fails closed before anything is delivered.
        for reader in sorted(approved):
            card = approved[reader]
            reader_entity = self.chambers[reader].owner_entity
            if self.exposure.would_exceed(card.source_chamber, reader_entity,
                                          self._intro_millibits(card)):
                att.gate("accounting", "stop",
                         f"exposure_budget:{card.source_chamber}->{reader_entity}")
                att.outcome, att.cause = "failed_closed", "exposure_budget"
                return att
        att.gate("accounting", "pass")

        att.cards_approved = approved
        att.gate("mutual_gate", "pass")
        att.outcome, att.cause = "cleared", "mutual_release"
        return att

    def _house_fit(self, ch_a: Chamber, ch_b: Chamber):
        if (ch_a.excludes & (ch_b.offers | ch_b.needs)) or \
           (ch_b.excludes & (ch_a.offers | ch_a.needs)):
            return {"veto": True}
        m1 = ch_a.needs & ch_b.offers
        m2 = ch_b.needs & ch_a.offers
        if not m1 or not m2:
            return {"score": 0, "m1": m1, "m2": m2}
        return {"score": len(m1) + len(m2), "m1": m1, "m2": m2}

    def _review_outbound(self, source: Chamber, card: MatchCard):
        """Scripted stand-in for the source owner's human reviewer. The house
        applies drop operations itself, so a released card is a subset of the
        reviewed card by construction — reviewers cannot inject text, and
        since the ordinal gate re-renders the rationale from the approved
        fields, a redacted tag simply never appears (no mask marker: whether
        a redaction happened is itself withheld)."""
        policy = source.reviewer_policy
        if policy == "decline_all":
            return "decline", None
        if policy.startswith("mask:"):
            tag = policy[len("mask:"):]
            if tag in card.offers_matched or tag in card.needs_matched:
                card_after = MatchCard(
                    source_chamber=card.source_chamber, reader_chamber=card.reader_chamber,
                    fit_bucket=card.fit_bucket,
                    offers_matched=tuple(t for t in card.offers_matched if t != tag),
                    needs_matched=tuple(t for t in card.needs_matched if t != tag),
                    rationale=card.rationale)
                return "redact", card_after
        return "release", card

    # -- the clearing window -----------------------------------------------

    def run_window(self, worker_for_pair=None) -> dict:
        self.tick += 1
        window_id = f"w-{letters_token('window:' + str(self.tick), 4)}"
        worker_for_pair = worker_for_pair or (lambda a, b: sorted(self.workers)[0])
        filers = sorted(cid for cid in self.chambers if cid in self.intents)

        window_attempts = []
        for a, b in combinations(filers, 2):
            window_attempts.append(self._attempt(a, b, worker_for_pair(a, b)))

        deliveries = {cid: [] for cid in filers}
        cleared_parties = set()

        # Cleared introductions cross: unblinding + reviewed card, ledgered,
        # charged to the lifetime exposure account.
        for att in window_attempts:
            if att.outcome != "cleared":
                continue
            intro_charge_ids = {}
            for reader in sorted(att.cards_approved):
                card = att.cards_approved[reader]
                counterpart = self.chambers[card.source_chamber]
                # Party lane, leg 1a: the ring comes FIRST (the ordering
                # law — attention before exposure, so a refused ring leaks
                # nothing about the counterpart).
                ring = None
                if self.party is not None:
                    ring = self._party_ring(reader, window_id)
                payload = canonical_json({
                    "kind": "introduction",
                    "counterpartHandle": counterpart.contact_handle,
                    "fitBucket": card.fit_bucket,
                    "offersMatched": list(card.offers_matched),
                    "needsMatched": list(card.needs_matched),
                    "rationale": card.rationale,
                    "receipt": ("Reviewed release; buckets and tags only; "
                                "rationale chosen by the source reviewer "
                                "from a fixed house candidate set of four "
                                "projections, selection charged; no "
                                "perfect-privacy claim; denials are "
                                "uninformative by construction."),
                }).encode("utf-8")
                self.crossings.record(self.tick, "introduction", reader,
                                      card.source_chamber, payload)
                intro_charge_ids[reader] = self.exposure.charge(
                    card.source_chamber,
                    self.chambers[reader].owner_entity,
                    self._intro_millibits(card),
                    f"introduction {att.attempt_id}", self.tick,
                    estimate=self._intro_estimate(card))
                # Party lane, leg 1b: 50 cents released against the exact
                # ring receipt — unconditional-to-raise.
                if self.party is not None:
                    self._party_raise(att, card, reader, ring[0], ring[1])
                self.mailboxes[reader].append(payload)
                deliveries[reader].append(payload)
            # Party lane, leg 2: the $5 outcome escrows, one per matched
            # party, bound to the first-contact card's charge event.
            if self.party is not None:
                self._party_contingent(att, intro_charge_ids)
            cleared_parties.update((att.a, att.b))

        # Owner-side review emissions: an interrupted reviewer means the owner
        # learns a pseudonymous attempt existed. Notification text is itself
        # egress; charge it (tripwire, not gate — the reviewer already knows).
        for att in window_attempts:
            if att.outcome in ("cleared",):
                continue
            for owner in sorted(att.interrupted):
                self.exposure.charge("house", self.chambers[owner].owner_entity,
                                     REVIEW_EMISSION_MILLIBITS,
                                     f"review emission {att.attempt_id}", self.tick,
                                     estimate=self._side_channel_estimate(
                                         "review_emission",
                                         REVIEW_EMISSION_MILLIBITS))

        # Denials are invisible to counterparties: every filer with no cleared
        # introduction receives the SAME constant payload, whatever the cause
        # (near miss, veto, decline, slashed worker, exhausted attention, or
        # nothing scored at all). One bit, still debited.
        for cid in filers:
            if cid in cleared_parties:
                continue
            self.crossings.record(self.tick, "denial", cid, "house", DENIAL_PAYLOAD)
            self.exposure.charge("house", self.chambers[cid].owner_entity,
                                 DENIAL_MILLIBITS, f"window denial {window_id}",
                                 self.tick,
                                 estimate=self._side_channel_estimate(
                                     "window_denial", DENIAL_MILLIBITS))
            self.mailboxes[cid].append(DENIAL_PAYLOAD)
            deliveries[cid].append(DENIAL_PAYLOAD)

        # Escrow remainders refund; intents retire.
        for cid in filers:
            remainder = self._escrow_balance(cid)
            if remainder > 0:
                self.ledger.transfer(self._escrow(cid), f"owner:{cid}",
                                     remainder, "escrow refund at window close", self.tick)
            del self.intents[cid]

        result = self._close_window(window_id, filers, window_attempts, deliveries)
        self.windows.append(result)
        return result

    # -- receipts, owner files, court file ----------------------------------

    def _pseudonym(self, viewer: str, subject: str, window_id: str) -> str:
        # Per-(viewer, subject, window) so pseudonyms cannot be correlated
        # across owner files (coalitional inference defense).
        return "P-" + letters_token(f"pseud:{viewer}:{subject}:{window_id}", 5)

    def _owner_file(self, cid: str, window_id: str, attempts, deliveries) -> dict:
        visible = []
        for att in attempts:
            mine = cid in (att.a, att.b)
            if not mine:
                continue
            counterpart = att.b if att.a == cid else att.a
            if att.outcome == "cleared" or cid in att.interrupted:
                visible.append({
                    "attemptId": att.attempt_id,
                    "counterpart": self._pseudonym(cid, counterpart, window_id),
                    "yourReviewerDecision": att.decisions.get(cid, "not_interrupted"),
                    "yourRationaleOrdinal": att.ordinals.get(cid),
                    "yourReviewSeat": att.reviewers.get(cid),
                    "outcome": "cleared" if att.outcome == "cleared" else "not_cleared",
                })
        return {
            "chamberId": cid,
            "windowId": window_id,
            "attemptsVisibleToOwner": visible,
            "deliveries": [p.decode("utf-8") for p in deliveries.get(cid, [])],
            "attentionSpentUnits": self.attention.spent[cid],
            "attentionBudgetUnits": self.attention.budgets[cid],
            "reviewerMemoryOwnBench": [
                row for row in self.reviewer_memory.snapshot()
                if row["sourceChamber"] == cid],
            "note": ("Counterpart pseudonyms are per-viewer per-window and cannot "
                     "be correlated across owner files. Non-clearing causes are "
                     "collapsed: your own decisions are shown; the counterparty "
                     "side is only 'cleared' or 'not_cleared'."),
        }

    def _render_kernel_key(self, key) -> str:
        if len(key) == 3 and key[0] == "exp":
            return f"{key[1]}->{key[2]}"
        if len(key) == 3 and key[0] == "mem":
            return f"mem:{key[1]}->{key[2]}"
        return ":".join(key)

    def _kernel_court_file(self) -> dict:
        out = {}
        for key, account in sorted(
                self.kernel_meter.court_file().items(),
                key=lambda item: self._render_kernel_key(item[0])):
            out[self._render_kernel_key(key)] = account
        return out

    def _close_window(self, window_id, filers, attempts, deliveries) -> dict:
        causes = {}
        for att in attempts:
            causes[att.cause] = causes.get(att.cause, 0) + 1
        cleared = [att for att in attempts if att.outcome == "cleared"]
        notes_bytes_held = sum(len(self.chambers[c].context_notes.encode("utf-8"))
                               for c in filers)
        kernel_audit = self.kernel_ledger.audit()
        assert kernel_audit == [], kernel_audit
        if kernel_audit:
            raise LawViolation(f"kernel ledger audit findings: {kernel_audit}")
        receipt = {
            "windowId": window_id,
            "tick": self.tick,
            "enrolledChambers": len(self.chambers),
            "intentsFiled": len(filers),
            "pairsScored": len(attempts),
            "introductionsCleared": len(cleared),
            "denialsDelivered": sum(1 for c in filers
                                    if DENIAL_PAYLOAD in deliveries.get(c, [])),
            "attemptCausesHouseAudit": dict(sorted(causes.items())),
            "rationaleChannel": {
                "candidateSetSize": RATIONALE_CANDIDATE_COUNT,
                "ordinalMillibitsPerCard": ORDINAL_MILLIBITS,
                "note": ("Crossed rationale is a fixed house projection of "
                         "already-charged fields; the source reviewer's "
                         "selection is the prose channel's only degree of "
                         "freedom and is charged as a covert-channel "
                         "ceiling."),
            },
            "crossings": list(self.crossings.entries),
            "withheld": {
                "contextNotesSections": {"grantedToScenarioWorker": False,
                                         "bytesHeldNeverCrossed": notes_bytes_held},
                "contactHandles": "crossed only inside cleared introductions",
                "nearMissAndNoCoincidencePairs": sum(
                    causes.get(k, 0) for k in ("near_miss", "no_coincidence")),
                "vetoedPairs": causes.get("vetoed", 0),
                "failedClosedPairs": sum(causes.get(k, 0) for k in (
                    "grant_violation", "grant_unusable", "grant_missing",
                    "scan_violation", "attention_exhausted", "exposure_budget",
                    "reviewer_memory_exhausted",
                    "worker_output_forged", "worker_withheld_cards")),
                "note": ("No live near-miss lists: pairs below threshold produced "
                         "no artifact visible to any party; counts here are house "
                         "audit only and never cross to requesters."),
            },
            "settlement": {
                "conserved": self.ledger.conserved(),
                "totalMicros": self.ledger.total(),
                "entries": list(self.ledger.entries),
                "balances": dict(sorted(self.ledger.accounts.items())),
            },
            "attention": {
                "budgets": dict(sorted(self.attention.budgets.items())),
                "spent": dict(sorted(self.attention.spent.items())),
                "events": list(self.attention.events),
            },
            "exposureAccounts": self.exposure.snapshot(),
            "reviewerMemory": {
                "perReviewCeilingMillibits": self._review_memory_total(),
                "schedule": self._review_memory_schedule(),
                "accounts": self.reviewer_memory.snapshot(),
                "note": ("Ceilings, not measurements: seating a reviewer "
                         "charges the schema maximum of every artifact shown, "
                         "whatever the content or decision. Memory is not "
                         "revocable — rotation bounds future accrual only."),
            },
            "kernelLedger": {
                "events": self.kernel_ledger.event_count(),
                "auditFindings": kernel_audit,
                "courtFile": self._kernel_court_file(),
            },
            "nonClaims": NON_CLAIMS,
            "laws": sorted(INTRO_CLEARING_LAWS),
        }
        owner_files = {cid: self._owner_file(cid, window_id, attempts, deliveries)
                       for cid in filers}
        return {
            "windowId": window_id,
            "attempts": attempts,
            "deliveries": deliveries,
            "receipt": receipt,
            "ownerFiles": owner_files,
            "courtFile": render_court_file(self, window_id, attempts, deliveries, receipt),
        }


# ---------------------------------------------------------------------------
# Court file rendering (audience-tagged)
# ---------------------------------------------------------------------------

def render_court_file(house: ClearingHouse, window_id: str, attempts,
                      deliveries, receipt) -> str:
    L = []
    add = L.append
    add(f"COURT FILE — purpose-blind introduction clearing — window {window_id}")
    add("Audience tags: [HOUSE] audit-only; [OWNER:x] that owner's view; "
        "[CROSSED->x] exact bytes delivered to x.")
    add("")
    add("I. ENROLLMENT AND INTENTS")
    for cid in sorted(house.chambers):
        ch = house.chambers[cid]
        add(f"  [HOUSE] chamber {cid} entity={ch.owner_entity} "
            f"reserve={ch.reserve_micros} attention={ch.attention_budget} "
            f"policy={ch.reviewer_policy}")
    add("")
    add("II. GRANTS (no grant, no run)")
    for (cid, wid), g in sorted(house.grants.items()):
        add(f"  [HOUSE] {g.grant_id}: {cid} -> {wid} purpose={g.purpose} "
            f"scope={sorted(g.scope)} reads<={g.read_budget} expires@t{g.expires_tick}")
    add("")
    add("III. ATTEMPTS (house audit: full causes; owners see less)")
    for att in attempts:
        add(f"  [HOUSE] {att.attempt_id} {att.a}x{att.b} worker={att.worker_id} "
            f"outcome={att.outcome} cause={att.cause}")
        for step in att.trace:
            cause = f" ({step['cause']})" if step["cause"] else ""
            add(f"  [HOUSE]   gate {step['gate']}: {step['status']}{cause}")
        if att.ordinals:
            picks = " ".join(f"{src}=o{o}"
                             for src, o in sorted(att.ordinals.items()))
            add(f"  [HOUSE]   rationale ordinals (candidate set "
                f"{RATIONALE_CANDIDATE_COUNT}, {ORDINAL_MILLIBITS} millibits "
                f"charged per crossing card): {picks}")
        if att.reviewers:
            seats = " ".join(f"{src}={seat}"
                             for src, seat in sorted(att.reviewers.items()))
            add(f"  [HOUSE]   review seats (memory charged before showing, "
                f"irrevocable): {seats}")
        for side in sorted(att.access_logs):
            log = att.access_logs[side]
            reads = ", ".join(("" if r["granted"] else "DENIED:") + r["section"]
                              for r in log) or "none"
            add(f"  [HOUSE]   inputs touched in {side}: {reads}")
    add("")
    add("IV. CROSSINGS (what crossed — every byte ledgered)")
    for entry in receipt["crossings"]:
        add(f"  [HOUSE] {entry['entryId']} kind={entry['kind']} "
            f"reader={entry['readerChamber']} source={entry['sourceAttribution']} "
            f"sha={entry['payloadSha256'][:16]} len={entry['payloadLen']}")
    for cid in sorted(deliveries):
        for payload in deliveries[cid]:
            add(f"  [CROSSED->{cid}] {payload.decode('utf-8')}")
    add("")
    add("V. WITHHELD (what did not cross)")
    w = receipt["withheld"]
    add(f"  [HOUSE] dossier context notes: never granted to the scenario worker; "
        f"{w['contextNotesSections']['bytesHeldNeverCrossed']} bytes held, zero crossed.")
    add(f"  [HOUSE] near-miss / no-coincidence pairs: "
        f"{w['nearMissAndNoCoincidencePairs']} — no artifact visible to any party.")
    add(f"  [HOUSE] vetoed pairs: {w['vetoedPairs']} — the excluding side was never "
        f"interrupted and never learned the pair existed.")
    add(f"  [HOUSE] failed-closed pairs: {w['failedClosedPairs']} — nothing crossed; "
        f"requesters cannot distinguish these from any other non-clearing cause.")
    add("")
    add("VI. ATTENTION AND SETTLEMENT")
    for ev in receipt["attention"]["events"]:
        ok = "debited" if ev["granted"] else "REFUSED (exhausted; fails closed)"
        add(f"  [HOUSE] t{ev['tick']} interrupt {ev['owner']}: {ok} — {ev['memo']}")
    for e in receipt["settlement"]["entries"]:
        add(f"  [HOUSE] {e['entryId']} {e['debit']} -> {e['credit']} "
            f"{e['amountMicros']} ({e['memo']})")
    add(f"  [HOUSE] conservation: totalMicros={receipt['settlement']['totalMicros']} "
        f"conserved={receipt['settlement']['conserved']}")
    add("")
    add("VII. EXPOSURE ACCOUNTS — lifetime (source chamber x reader entity)")
    for row in receipt["exposureAccounts"]:
        flag = " OVER-BUDGET(tripwire)" if row["overBudget"] else ""
        add(f"  [HOUSE] {row['sourceChamber']} -> {row['readerEntity']}: "
            f"{row['millibitsCharged']}/{row['budgetMillibits']} millibits{flag}")
    add("")
    add("VIII. REVIEWER MEMORY — lifetime (source chamber x reviewer entity) ceilings")
    per_review = house._review_memory_total()
    add(f"  [HOUSE] per-review ceiling: {per_review} millibits "
        f"(structured + tags schema max + advisory prose cap + candidate "
        f"selection); charged before showing; never refunded.")
    for row in receipt["reviewerMemory"]["accounts"]:
        seatable = "can seat another review" \
            if row["headroomMillibits"] >= per_review \
            else "CANNOT seat another review"
        add(f"  [HOUSE] {row['sourceChamber']} -> {row['reviewerEntity']}: "
            f"{row['millibitsCeilingCharged']}/{row['budgetMillibits']} "
            f"millibits — {seatable}")
    add("")
    add("IX. CHARGE KERNEL LEDGER — mergeable charge-kernel/2 court file")
    k = receipt["kernelLedger"]
    clean = "audit-clean" if not k["auditFindings"] else "AUDIT FINDINGS"
    add(f"  [HOUSE] events={k['events']} {clean}")
    for key, row in k["courtFile"].items():
        add(f"  [HOUSE] {key}: cumulative={row['cumulative_mbits']} "
            f"demanded={row['demanded_mbits']} "
            f"ceiling={row['ceiling_mbits']} "
            f"class={row['leakage_class']} incident={row['incident']}")
    add("")
    add("X. NON-CLAIMS (what this system refuses to claim)")
    for nc in NON_CLAIMS:
        add(f"  [HOUSE] {nc['key']}: {nc['text']}")
    add("")
    add("XI. OWNER VIEWS (each owner sees only their own file)")
    for cid in sorted(deliveries):
        add(f"  [OWNER:{cid}] see owner file {cid}.json")
    return "\n".join(L)
