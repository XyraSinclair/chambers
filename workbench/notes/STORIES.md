# Grounding stories — where the math touches people

The discipline: every story must (a) bind to specific kernel accounts and
settlement flows — named keys, named events — and (b) expose at least one
thing the protocol **cannot yet express**, entered in the gap register at
the bottom. A story that only flatters the protocol is marketing; a story
that only breaks it is a paper. These do both, on purpose.

Status: working document. Sources: operator seed narratives, the lead's
protocol-binding pass, and two independent consult reports (generative and
adversarial-mechanism lenses) — merged, with disagreements kept visible.

---

## Story 1 — The party

**Cast & private worlds.** Alice hosts a hundred-person party and runs
Cupid, a matchmaking agent built by a third-party developer she does not
particularly trust. Bob and Charlie each uploaded private worlds months
ago — notes, message archives, half-organized interests. Bob has hard
never-reveals: the divorce, the diagnosis, the money. He's relaxed about
almost everything else. Neither Bob nor Charlie could *list* their own
preferences — personalities are multidimensional and beliefs are
circumstantial; the honest state of a person is "I don't know what I want,
but I'll know it when it's across the table."

**The run.** Cupid is admitted to the exact tuple (Bob's chamber,
Charlie's chamber) — a `MediationSession`. It reads across both silos
(metered observation), computes fit *inside* the boundary — common
obsessions, complementary conversational styles, one live disagreement
worth having — and emits two typed intro cards: one toward Bob (carrying
information about Charlie and about the tuple), one toward Charlie. Alice
never sees the cards. Alice never learns the match happened — "Bob met
Charlie" is itself a fact about both of them.

**The meter.**
- Observation: `exposure_key(bob_chamber, cupid)` and
  `exposure_key(charlie_chamber, cupid)` — the agent-as-reader lifetime
  accounts. Ceilings here are the answer to "how much of me can this
  developer's code ever see, cumulatively, across every party forever."
  A refusal is not an error page; it is *the agent literally cannot see
  that much of you*.
- Emission: the card toward Bob charges `exposure_key(charlie_chamber,
  bob)` — Bob is a reader of Charlie's world now — **atomically** with
  every member the card carries information about. Refused on any account
  ⟹ no card, no partial debits, demand recorded (the attempt was real).
- Bob's never-reveals: partitioned into a sub-source that is **never
  leased**. Unregistered-for-Cupid is the zero ceiling; there is no
  account against which a read could even be charged. What the meter
  honestly does NOT do: prevent *inference* of the divorce from the
  ten thousand facts Bob did allow. Bits are an upper-bound tripwire,
  not a harm proof — Gap G2, and it stays named in the card UI, not
  buried.
- The multidimensionality point is the design, not a problem: the
  protocol never needs a representation of Bob's personality. Arbitrary
  richness stays inside; only typed, capacity-capped judgements leave.
  General-purpose *inside*, bounded *across*.

**The money.** Alice deposits; per raised card the house escrows ~50¢
(`escrow.charge_keys` = exactly the exposure accounts the card touches,
`required_clean = true`). Release references the card's charge events —
the work receipt — so Alice pays iff the metered emission actually
happened and the touching court is clean. The $5 success fee ("they
talked >15 minutes about the fermentation thing") is **Gap G1**: release
conditional on a real-world outcome needs an attested outcome event —
same posture as estimator attestation (declared attester, independence
class, convicted-if-equivocating), never a protocol-verified truth. The
counterfactual form ("talked *because of* the card") should likely be
REFUSED as unoperationalizable — price the observable, not the
counterfactual.

**What it feels like when it works.** Bob gets one card: "Someone here
ferments things and owns a Prophet-5. There's a live disagreement about
natural wine you'd enjoy. West balcony." Underneath it, four lines: what
was read (in bits, against his ceilings), what crossed to whom, what it
cost Alice, and a receipt hash he can hand to any verifier.

*Full ledger depth — every row of this story as a numbered event, the
attention-pricing invariant, and the G1/G6 build order — in
`stories/party-matchmaker.md`.*

---

## Story 2 — The candidate who cannot be seen looking

**Cast & private worlds.** Dana is a staff engineer, employed, quietly
open to exactly the right thing. Broadcasting that fact would damage her.
Her chamber holds the real resume: what she actually built, what she
actually wants, what she'd actually move for. Recruiters run query agents
against a pool of such chambers.

**The run.** A recruiter's agent is admitted per-candidate-tuple with a
typed query family ("would anyone here move for staff+ infra, remote,
>$X?"). Every probe is charged against
`composition_key(dana_chamber, hiring_probe, recruiter_firm)` — the
**lifetime** join key. The dangerous attack is not one query; it is the
same firm probing weekly for a year and reconstructing her situation by
accumulation. That is precisely what the composition account meters, and
what the incident latch flags: refusals accrue demand; a campaign of
refused probes still shows up as extraction pressure.
Non-matches are **byte-constant denials** — "no match" must be the same
bytes whether Dana doesn't exist, isn't looking, or refused; anything
else is a presence channel (charged as field_presence if ever allowed).

**The money.** Recruiter deposits; small escrow per probe (pay-to-ask —
this is also the spam throttle); larger escrow released against the
verified-mutual-interest emission. The placement fee (the real money) is
Gap G1 again — outcome attestation, here with a natural attester pair:
both sides of the hire.

**Gap exposed.** G3: *reader identity*. "recruiter_firm" as audience
string is honest bookkeeping but a Sybil firm fragments its lifetime
account across shells. The coalition audit makes the fragmentation
*visible under a declared ownership hypothesis*; it cannot make it
impossible. Priced, not solved — and the story shows why the price is
worth stating on the receipt.

---

## Story 3 — The second opinion

**Cast & private worlds.** Elena has a scary ambiguous scan and a
twenty-year records history. She wants a world-class second opinion
without her insurer, employer, or anyone's training corpus learning a
thing. A specialist consortium operates diagnostic agents.

**The run.** The agent enters Elena's records chamber alone (tuple of
one plus the consortium's reference base). It emits a typed differential:
ranked candidate diagnoses from a fixed vocabulary, an urgency ordinal,
a recommended-next-test enum. Every component is enum/ordering-charged at
schema ceiling; free prose is *not in the schema*.

**The meter's honest limit is the star here.** The entire emission might
be 40 bits. One of those bits — "malignancy plausible" — is worth more
than Elena's whole music library. **Bits are not harm (G2)**: the numeric
accountant is the necessary floor, and the release gate must stay a
CONJUNCTION of the meter and an ordinal review (the entropy.ts law). The
story that sells chambers to Elena is not "only 40 bits crossed"; it is
"here is the enumerated list of every party who can ever see any of
those bits, with lifetime ceilings, and the insurer is not on it — and
if a coalition of readers ever assembles your file, the audit shows the
assembly."

**The money.** Flat consult fee escrowed, released against the emission
receipt. No outcome contingency — medicine is exactly where pay-per-
outcome corrupts the judgement. The pricing degrees of freedom belong
OUTSIDE the protocol, and this story is why that boundary is right.

---

## Story 4 — The founder dating problem

**Cast.** Fatima (technical, has a half-built prototype and a
non-compete she worries about) and Greg (distribution, capital, a
reputation for suing former partners — which is itself private context
*about him* held by others). Cofounder matching is the highest-stakes
trust decision either will make this decade, made today on vibes.

**The run.** Mutual evaluation as *two* mediation sessions with opposite
requester directions — the judgement toward Fatima about Greg draws on
Greg's chamber AND on third-party chambers holding experience-of-Greg
(the ex-partner's world: source = ex-partner's chamber, reader = Fatima).
This is the first story where the interesting content is *reputational* —
private context about a person held by someone else.

**Gap exposed.** G4: the subject/owner split. `exposure_key` prices the
*owner's* loss (the ex-partner's world leaking). Greg is the *subject* of
that information and holds no account in the flow at all. Defamation,
consent-of-the-subject, contested facts — the protocol currently has no
subject-indexed account and no contested-fact state. Honest status:
unmodeled. The story is buildable today only in the degenerate form where
all evidence about Greg comes from Greg.

---

## Story 5 — The one that must fail (today)

**Cast.** Hana wants an agent to read her entire life corpus and
ghostwrite a memoir — "use everything, make it sing, reveal nothing I'd
regret."

**Why the protocol refuses.** The output is open prose at book length.
Prose is charged at its byte ceiling (the exfiltration-honest rule):
~80,000 words ≈ 3.8 × 10⁹ millibits — orders of magnitude past any sane
ceiling on any account. The numeric meter's honest verdict is that an
open-prose channel of that size *is* her private world leaving, and
"I'd regret" is not a predicate the kernel can evaluate (G2, G5). The
ordinal/prose release gate (fixed house projections, selection charged
at log₂K) exists precisely because free prose cannot be metered
content-wise — and at memoir scale even that collapses to "publish, with
eyes open."

**The honest product answer**: chambers can host the *drafting* (nothing
leaves), and meter *excerpt-sized* releases one decision at a time. The
protocol's refusal to pretend otherwise is a feature; this story is the
fence line, and every real system should be able to point at its fence.

---

## Story 6 — The gardener (strangers improving each other's codebases)

**Cast & private worlds.** Maya's solo-maintained repo hides a latent
pool deadlock; Ravi's startup fixed that deadlock's twin months ago and
runs a naive backoff Maya solved in 2024. Neither shows the other their
code. A third-party **gardener** agent is leased into both chambers.

**The run.** The gardener sweeps both repos (metered observation against
each `(repo → gardener_vendor)` lifetime account — "how much of my
codebase can this vendor ever see"); its call graphs and defect
hypotheses stay silo-local (in-chamber richness is free). The find —
"Ravi's fix-pattern resolves Maya's deadlock class" — is a coalitional
derivative naming both silos. Maya is offered the **hint** (typed offer
card, ~20 bits charged to `(ravi_repo → maya)`: the shape of Ravi's fix
IS information about Ravi's engineering) and re-derives the concrete
patch *inside her own chamber* — licensed latent formation, rights row
3. The literal diff was also for sale at its raw-byte ceiling, ~1000×
the price; almost nobody buys the patch. The price gradient teaching
agents to compress is the codebook thesis observed in the wild.

**The money — G1 never bites, second confirmation.** Pay-on-green:
Maya's CI runs the fix inside her chamber as METERED WORK, the suite's
verdict is a ChargeEvent, and the escrow releases against exactly that
receipt under a clean court. Mechanical oracle, no attestation theater —
same closure as Story 8's pay-on-repro. Wedges should be *chosen* for
mechanical oracles. The release disburses a **source royalty to Ravi**
(the derivative's provenance named his silo — G14 as economics), and the
same sweep sells Maya's backoff wisdom back to him: every codebase in
the garden is simultaneously mine and customer.

**Honest limits.** Tests-green is not correctness (G2's engineering
cousin — the escrow buys "her suite passed," never "the bug is gone");
gaming weak suites is priced by track record (L5); declared coverage
statements at escrow time (G9-shaped) would make the weakness legible.

*Full ledger depth: `stories/gardener.md`.*

---

## Story 7 — The guardian at the bell (attention as fiduciary duty)

**Cast & private worlds.** Noor is a surgeon. Her **guardian** — a
third-party agent under her declared policy — is the ISSUER of every
attention account keyed to her (`("att", noor, sender, epoch)`), holding
deep read leases over her most private data: what she ignores, what she
opens twice, when she can be interrupted.

**The run.** Three delivery channels at three unit prices
(interrupt-now / digest / roundup), and — the deeper move — **framing
features are metered capacity**: urgency markers, red banners, alarm
verbs are schema dimensions the sender pays for. Adrenaline costs. The
guardian re-frames admitted content into Noor's shape as in-chamber work
(what framing works for her is private; senders never learn it), and
delivery receipts are batched to padded cadence — the bell does not echo
her state (G15 applied to attention).

**The money — retroactive appreciation as settlement.** Each admitted
ring escrows base price + framing premium. At epoch close Noor one-taps
glad / neutral / noise: an OutcomeAttestation in its cleanest form (the
attester owns the experience and is not the payee; counterfactuals
refused per doctrine). Glad → premium mostly returns, sender's future
price drifts down. Noise → premium forfeits to NOOR at a declared
multiple and the sender's price rises — the guardian's admission policy
learns at the sender's expense. The system deliberately chills toward
quiet; pay-after-value for attention, judged by the only party entitled
to judge it.

**Whose agent is it — asked of the ledger.** The adtech failure mode
(gatekeeper paid by senders) is checkable from the fold: the guardian's
income may flow only from Noor's side, every fee is a ledgered flow, and
"does its revenue correlate with admitted volume?" is a query, not
journalism — G9 extended to **fiduciary legibility**. The guardian is
the highest-trust vendor in the stack (it reads everything, emits almost
nothing); fold-legible fiduciary structure is why it can exist.

**Honest limits.** Appreciation is manipulable (mood, glad-bait) — the
tap prices future access, it does not certify truth; the chill toward
under-delivery is a chosen bias (on-call channels can invert it); the
guardian's model of Noor is bounded latent formation, and leaving the
vendor is G7's export.

*Full ledger depth: `stories/attention-guardian.md`.*

---

## Story 8 — Frontier labs: IP mediation at the top of the market

**Cast.** Halcyon and Meridian, frontier AI labs. Since the GPT-4
technical report disclosed — in its own words — no architecture, data,
or training-method details, the recipes are private capital with no
market infrastructure. Halcyon holds a data-curation pipeline and
negative results worth their weight in compute; Meridian holds an
inference stack and dangerous-capability evals whose elicitation methods
are themselves capability uplift. The recipe never crosses — only
judgements about the recipe cross.

**Three deals, ascending intimacy.** (1) *The duplication check*: "are we
sitting on the same unpublished result?" — today unaskable (asking leaks
that you have something in the neighborhood); here one atomic
`kind="overlap"` judgement, ~1,585 mbits each way, and if the answer is
"distinct" each lab learned almost nothing — that is the product. (2)
*The technique trade*: sketch → **mediated reproduction in a third,
attested enclave neither lab can read** (`latentCustody=
escrowed_full_latent`) → license, each stage an escrow releasing against
the prior stage's charge events; full transfer on settlement is a new
consented account, never a ceiling raise. (3) *The safety-eval exchange*:
results and thresholds cross as enums; elicitation methods live in a
never-leased sub-source (G5 doing real safety work); the regulator is a
third READER with its own exposure accounts, and the court file is the
compliance artifact.

**Why this is the wedge — the oracle gap closes by construction.** "Pay
on repro" needs no outcome attestation: the reproduction verdict IS a
ChargeEvent, so license-scale escrow releases against `charge_ids` all
the way down — G1 never bites. Compute credits are honest deposit
backing (an issuable liability of a named issuer — unlike G11's
un-issued equity). Settlement clears through an EntropyPool because the
*direction of dependence between frontier labs* is itself market-moving
information. Verification-as-extraction (monthly sketch-probes as a
distillation campaign) is exactly what the lifetime composition account
meters — d1_bounty's VEX shape with more zeros. And Sybil is weak
terrain for the attacker: readers here are few, named, and
self-identifying — the (source × reader) key at its strongest.

**Gap exposed — G13.** Declared entropy depreciates: a technique's
`subject_entropy_mbits` is its delta over PUBLIC knowledge, and the
algorithmic-progress literature puts efficiency-technique half-lives
under a year (corpus-confirmed: "Algorithmic progress in language
models," 2024). Re-declaring downward today hits I7 quarantine; missing
is an owner-signed, monotone-down re-declaration event — same escalation
direction the merge laws already prove. Corollary: the estimator for
these deals is an arXiv-reading institution, and `adversarial_review`
independence stops being a nicety — the seller wants the delta
overstated, the buyer understated (G8 at its most acute).

*Full ledger depth, all three deals, and the adversarial analysis:
`stories/frontier-lab-ip-mediation.md`.*

---

## Story 9 — The coagent economy: orchestration at scale

**Cast.** A pension fund wants one judgement — which of forty biotech
startups deserves a term sheet — whose answer lives across forty private
trial chambers, twelve experts' private pattern-libraries, and two
hospital systems. **Aster**, an orchestrator agent, convenes it while
holding no privileged access at all: it reads only typed, metered
judgements, charged against its own accounts like any reader. Its power
is compositional, not informational.

**The supply chain.** Leaf sessions emit typed verdicts; the synthesis
session consumes them and emits one ranked shortlist toward the fund —
which now carries startup #17's information *two hops* from its chamber.
The law the chain needs is ledger-computable: **an emission's atomic
charge set is the provenance closure of the judgements it consumed** —
every original source charges the terminal reader. The data-processing
inequality makes this honest: downstream can never carry more than
crossed the first hop, so charging first-hop capacity at every hop is a
sound upper bound, and DPI licenses tightening without under-charging.
"The emission is not separable from its inputs" extends to *not
separable from its ancestry* (G14).

**The money.** Cascade escrows: fund → Aster → every leaf, each bound to
its session's keys with declared expiry defaults. Three proven laws
compose for free: conservation is arithmetic over the one merged ledger
(tree depth irrelevant); **anti-holdup composes** — a bankrupt
orchestrator cannot strand a hundred subcontractors, each self-serves
its S8 default (what makes subcontracting safe for the weak side); and
two hundred agents produce ONE auditable artifact, because the court
file is a fold, not a transcript.

**The meta-economy.** Estimators, canonicality reviewers, and settlement
issuers are themselves paid agents whose work is typed, chambered,
metered: the L3 estimator-probe becomes a standing bounty (demonstrate
achieved > charged, collect from the estimator's bond — red-teaming as a
job); an issuer's ledgered refusal history is the reputation surface the
Ethereum test demands. The recursion is the design working: the economy
audits its own infrastructure with the same six event kinds.

**Gaps exposed.** G14 — provenance closure as an audit family, not an
orchestrator's discipline (a new I-code walking the graph the ledger
already stores; no new event kinds). G15 — the topology channel: who was
convened against whom broadcasts the fund's interests to every ledger
holder; direction is the EntropyPool trick applied to session
*visibility* (batch, pad, state the achieved anonymity set), declared
and priced, never "unlinkable."

*Full ledger depth: `stories/coagent-economy.md`.*

---

## Consult findings (independent lenses, merged)

*This section holds the two subagent reports' surviving findings after
lead review — attacks on the mechanism, deeper reframings, and their
costs. Disagreements retained.*

### From the adversarial mechanism-design consult

**Adopted and already shipped.**
- **Silent holdup** was the sharpest finding: in settlement/1 as first
  drafted, only the issuer could release/refund, no code convicted
  inaction, and selective stalling was indistinguishable from prudence.
  *Lead correction on the proposed fix*: the consult's sketch resolved
  expiries inside the fold via `tick_now`, which would have broken the
  CRDT law (the fold must be a pure function of the event set). Shipped
  instead as **permissionless `default_resolution` events** (SPEC §1.5,
  S8): every escrow declares its expiry fate at lock time; after expiry
  anyone — the payee is the point — submits the declared default; the
  audit polices timing, receipts, and clean court. Exit rights follow:
  no issuer can hold value hostage past a declared horizon.

**Adopted into the register (design queue).**
- **Contingent outcomes (G1), resolved design**: bonded, independence-
  classed outcome attestation (the estimator posture) + timeout default
  so no human adjudicator can deadlock the system + hard platform logs
  overriding bonded rulings when they exist (better evidence convicts —
  the S-code relationship to the fold, again). **Counterfactuality is
  refused**: "would not have talked otherwise" has no operationalizable
  form. The checkable proxy is a *ledger* fact: "this agent originated
  the first contact leading to a qualifying conversation." And the
  15-minute metric is named for what it is — presence, not engagement;
  Goodhart priced openly ("sustained mutual connection," never
  "worthwhile match").
- **Attention ≠ leakage economically (G6, sharpened)**: structurally
  similar accounts, opposite intent. Leakage ceilings exist to bound
  harm — paying people more for more exposure inverts the ceiling into
  an adverse-selection engine. Attention is legitimately market-clearing
  on the recipient's side. Design consequence: **multi-payee escrows,
  keyed per payee** — the recipient's cut clears only against the
  recipient's own attention-debit account, never against the operator's
  leakage charge. (pricing.ts's "owner is paid for attention spent" is
  currently an unimplemented aspiration; this makes it a settlement
  fact.)
- **Estimator economic capture (G8, new)**: admissibility checks a
  declared independence *class*, not economic independence — a requester
  can retain a "role_separated" estimator that systematically
  under-counts for their traffic, and the audit has no independent
  ground truth (I2 gates on the very debits the estimator declared).
  Cheapest honest lever: a declared `estimator_payer` field; refuse
  admissibility when the estimator's payer is the escrow's requester.
  Shell-company capture stays L5, like identity everywhere else.
- **Fee legibility (G9, new)**: pricing stays above the protocol, but
  fee *schedules* should be ledgered, declared events an escrow's split
  references — a stranger recomputes the house's cut from the artifact
  alone.

**Verified with a lead correction.**
- **Demand-griefing** (flooding refused oversized estimates to trip a
  target's incident latch at zero cost) is real *within* an admitted
  relationship, but the consult overstated the perimeter: charges must
  bind to a lease held by the charging node (I4), so only agents the
  key's owner ADMITTED can accrue demand against it. Admission is the
  moat; within it, a submission bond proportional to declared estimate
  (intro_clearing's pay-to-attempt pattern) is the right port.
- **Judgement shading** (operator manufactures matches; S-codes price
  flow, not honesty) — correct, and it is *why* G1's outcome attestation
  matters: judgement quality gets priced after the fact by realized
  outcomes, never policed at emission time.

**The Ethereum-ness verdict (adopted as doctrine).** Global consensus
would be the worst outcome here — a chain that must see every read event
is a surveillance ledger. Ethereum's actual promise to users is three
properties: *nobody freezes your funds unilaterally, nobody holds
unauditable discretion, the rules are legible before you transact*.
Consensus was its implementation strategy, not the goal. This stack gets
all three from leases + CRDT merge + declared expiry defaults —
S8 delivered the first; issuer competition with ledgered refusals and
declared fee schedules are the remaining two.

### From the generative story consult

Full report: `stories/consult-storyweaver.md` — seven stories traced
through the FULL type stack (AutonomyEnvelope, CanonicalityReview,
WideningEvent, latentCustody, EntropyPool), with intro_clearing's real
numbers. Surviving findings beyond the lead's five stories:

- **The felt bottleneck is attention, not millibits** — in every story
  the first thing a user experiences is interruption volume and reviewer
  fatigue. Convergent with the adversarial consult's G6, and it prices
  the cost honestly: first-class attention accounts mean a SECOND
  global-cap proof (attention leases), real Lean work.
- **Being reviewed and rejected costs the applicant** — reviewer-memory
  charges never refund, so a rejected grant applicant burns the same
  permanent lifetime ledger space against that officer as a funded one.
  The sharpest honest-but-uncomfortable fact in the stack; it belongs in
  the user-facing story, not hidden.
- **The kernel never observes the physical world** (its framing of G1):
  the honest move TODAY for the $5 bonus is refund-at-expiry — which the
  shipped `default_on_expiry="refund_to_payer"` now does by declared
  default. Its medical story sharpens G1 further: for clinical outcomes,
  the outcome-verifier would need MORE exposure than the work it prices
  — some outcome conditions should be refused even after attestation
  exists, and the receipt should say "a second opinion was rendered,"
  never "it mattered."
- **Grantmaker's drift (G10, new)**: nothing models the READER's
  judgment reliability — forty individually-clean bilateral mediations
  can be silently unfair in aggregate; the ledger has no vocabulary for
  criteria drift. Meters leakage and value, not judgment quality. Named,
  not improvised at.
- **Equity-shaped value (G11, new)**: "2% of whatever this becomes" is a
  claim on a future, un-issued asset — not a deposit any issuer can
  honestly declare. Cofounder matching prices the introduction, not the
  upside; multi-issuer/redemption stays out of /1 on purpose.
- **Preference formation (G12, new)**: `ReaderModel` reads existing
  facts; there is no transform for preferences the subject has never
  articulated ("15% less for remote, never said aloud"). Matching what
  is legible outruns matching what is true, and the court file cannot
  see the difference.
- **The refusal worth adopting as doctrine**: general-purpose
  personality representation is a NON-GOAL. Closed-vocabulary,
  schema-bound chambers are the design, not a limitation — the moment a
  chamber holds an open high-dimensional preference model, log₂-style
  charging breaks (ceilings absurd or estimation unattested).
  "Understands you as a whole person" is precisely what the protocol
  should refuse to know; richness lives inside, judgements cross typed.
  This caps ambition in dating/hiring pitches and is worth that price.
- **Held as conjecture, not promoted**: credit-and-exposure-share-one-
  measure (coalition.ts) — both consults brushed it; the one-decisive-
  bit-outprices-a-megabyte edge keeps it a conjecture, per its own flag.

### Synthesis — where the two consults converge

Both lenses independently landed on the same two build items, which
therefore lead the queue:

1. **G1 — outcome attestation** — SHIPPED 2026-07-06 as
   `charge-settlement/2` (SETTLEMENT-SPEC Part II; S9/S10; 12-scenario
   golden corpus; Lean bond conservation; served by the node). The merged
   design survived contact intact: bonded, independence-classed
   attestation events under the evidence-lane discipline; outcomes size
   payments and NEVER gate disclosure (normative, §6); unprovable-lane
   conditions have no lane and settle flat-fee; timeout defaults hold in
   both directions (unattested expiry refunds the payer, a quorum-holding
   payee defaults to release past a silent issuer); platform logs
   strictly override bonded rulings (slash to the harmed party) while
   equal-lane contest blocks payment and slashes nobody — contested is
   not convicted; counterfactual metrics refused (no lane can express
   one) — the checkable proxy stays first-contact attribution, a ledger
   fact named in the metric label. Clinical-style conditions remain
   refused outright: no outcome block, flat fee.
2. **G6 — attention as first-class**, merged design: attention accounts
   keyed (recipient × agent) with the recipient as fee-beneficiary via
   multi-payee per-payee-keyed escrows; refundable-if-ignored windows;
   priced at a second global-cap proof in Lean.

---

## The gap register

| # | Gap | Exposed by | Honest status | Direction |
|---|-----|-----------|----------------|-----------|
| G1 | **Contingent-on-outcome settlement** — release gated on a real-world event ($5 if they talk; placement fee on hire) | 1, 2 | CLOSED 2026-07-06 by `charge-settlement/2`: bonded, independence-classed, contest-hardened `outcome_attestation` quorums gate release (S9); bonds conserve and slash only under strictly better evidence (S10); counterfactuals inexpressible by construction | Residues, named: the metric is a presence proxy (Goodhart priced openly); equal-lane platform disputes settle by expiry default; attestor Sybil = G3, attestor economic capture = G8 — both L5 |
| G2 | **Bits are not harm** — one bit can be catastrophic; N bits can be trivia; regret is not a predicate | 1, 3, 5 | Named limit (SPEC §7); ordinal review is the other half of the release conjunction | Keep as conjunction, never fold into the meter; surface per-fact sensitivity as *partitioning* (never-lease sub-sources), not weights |
| G3 | **Reader identity / Sybil fragmentation** — lifetime accounts reset under shell identities | 2 | Coalition audit makes it visible under declared hypotheses; cannot prevent | L5 forever; make the price visible on every receipt |
| G4 | **Subject ≠ owner** — reputational facts: information *about* X held *by* Y; X has no account | 4 | Unmodeled | Needs design: subject-indexed shadow accounts or consent-of-subject gates; do not improvise |
| G5 | **Never-reveal as predicate** — "these facts, never" vs numeric ceilings | 1, 5 | Approximated by never-leased sub-sources (zero ceiling by non-registration) | Partitioning discipline now; predicate gates only with the ordinal layer |
| G6 | **Attention as a first-class account** — the recipient's notice is the scarce resource the notifier spends | 1, 2 | Exists in intro_clearing as sim-level books, not kernel accounts | Promote: attention accounts with recipient-as-fee-beneficiary; the 50¢ IS the attention price |
| G7 | **Revocation / exit** — Bob leaves; what dies with him | all | CLOSED both halves: value-side by S8 (declared expiry defaults — no issuer strands funds); authority-side 2026-07-06 by `charge-covenant/1` (cease/cap self-restrictions, content-addressed grandfathering, value fails closed on covenant-broken authority — the Bob-leaves story is a passing test) | Residue: the portability workflow (export → re-attach under a new house, cumulative intact) is implied by the data model, never exercised; residue statements are prose by theorem (one-way widening) |
| G8 | **Estimator economic capture** — independence class declared, economic independence unchecked; the audit has no ground truth against a systematically under-counting estimator | consult | Unchecked | Declared `estimator_payer` field; inadmissible when payer == the paying requester; shells stay L5 |
| G9 | **Fee legibility** — no mechanism forces fee disclosure before escrow | consult | Pricing deliberately above protocol | Ledgered `fee_schedule` events that escrow splits must reference |
| G10 | **Reader judgment quality** — criteria drift, fatigue, halo effects; N clean bilateral runs, silently unfair aggregate | consult (grantmaking) | Partial vocabulary now: review-audit/1 prices judge PROCESS (coherence receipts, zero owner leakage); the F5 design pass (2026-07-09, frontier/judgement-markets/) prices judge OUTPUT by correlated agreement with the redundancy metered openly — viable below the moat line only, KILLED above it (the owner's ceilings refuse the audit reader; the mechanism cannot buy honesty with the owner's secrets) | Seat with the battery, bonus with CA on low-sensitivity couplings (peer_sim runs it); aggregate fairness audits stay ABOVE the protocol; score-bound escrows await a report event kind (/3) |
| G11 | **Equity-shaped value** — claims on future un-issued assets ("2% of what this becomes") | consult (cofounder) | Out of /1 by declared non-claim (multi-issuer, redemption) | Stays out until multi-issuer netting exists; price introductions, not upside |
| G12 | **Preference formation** — facts the subject never articulated cannot be read; legible outruns true, invisibly | consult (hiring, cofounder) | Unmodeled; partially answered by doctrine (richness stays inside; elicitation is in-chamber work, not a crossing) | In-chamber elicitation transforms whose OUTPUTS are ordinary metered judgements; the crossing never widens |
| G13 | **Entropy depreciation** — declared entropy is a delta over public knowledge, which moves; re-declaring downward hits I7 quarantine | 8 | Min-resolution accepts the lower figure (conservative) but convicts the account as conflicted forever | Owner-signed, monotone-DOWN re-declaration event (same escalation direction the merge laws prove); lease expiry priced to publication velocity as named estimator discipline |
| G14 | **Provenance closure** — chained judgements carry source information downstream; the terminal reader's charge is orchestrator discipline, not law | 9 | Ledger-computable today (leaf charges name their sources); DPI makes first-hop-capacity-per-hop a sound upper bound | New audit family: reconstruct the closure from an emission's consumed judgements, convict a coupled set that dropped a source — "not separable from its ancestry" |
| G15 | **The topology channel** — session graph, tuple membership, escrow shapes broadcast who is interested in whom | 9 | Unpriced metadata; assume it leaks | EntropyPool trick applied to session visibility: batch formation to cadence, pad the convened set, state the achieved anonymity set on the receipt |
| G16 | **Provenance-closure charging** — a derived fact's emission must charge its TRANSITIVE ancestry, not just the session tuple | moats frontier (M4) | **SHIPPED 2026-07-06** as `charge-provenance/1` (KERNEL-SPEC Part III): `derivation` events + P1 (dropped ancestor) / P2 (closure undercount vs the integer max-flow DPI bound, full min-cut incl. parallel paths) / P3 (orphaned derivation) on a separate `p_codes` surface; value fails closed (P-codes join the dirty court); 17-test lane, multi-hop P1 load-bearing; frozen corpora untouched; supersedes G14; X0 covered its fact identity free | Named residues: emission binding rides a declared `channel` convention, so UNDECLARED emissions are invisible to P1/P2 (same trust class as G8 estimator undercount); non-`exp` couplings out of scope; P3's resolution set awaits G18's tombstone kind |
| G17 | **The moat residual statement** — the one honest external sentence ("reader r consumed X of Y mbits I ever ceded; residual Z; a budget fact, not a secrecy fact") has no receipt schema | moats frontier (M3) | Pure fold arithmetic today, recomputable by a stranger, but uncarried | Compile `MoatResidualStatement` from the fold with mandatory caveat codes (bits-not-harm, reader-identity-claimed, denominator-depreciates) and the G13 vintage; a projection, never a stored authority |
| G18 | **Ancestry retention** — nothing forbids GC'ing an artifact that sits in a later derived fact's provenance closure; retention protects claims, not ancestry | moats frontier (M1) | Partially carried (tombstone discipline protects claims) | `retentionOutlivesTheDerivationsItFeeds`: an artifact reachable from any live provenance closure is tombstonable but not droppable — one law, one check (closure ⊆ retained-or-tombstoned) |
| G4+ | **Subject ≠ owner, ESCALATED** — a moat over third-party facts (reputational/diligence) is not just unmodeled, it is a compliance liability: the subject has no account and no erasure verb, so a right-to-be-forgotten request has nowhere to land | moats frontier (adversary f) | Liability, not merely a gap | Subject-indexed shadow accounts or consent-at-ingest gates before any such moat is built; do not improvise (the register's standing G4 warning, now load-bearing) |
| G19 | **Slash override referent** — an S10 slash's justifying override was found by SCAN, not by NAME, leaving two sanctioned de-escalation precedents where one would do | fable review (F3, SETTLEMENT-SPEC §11) | **SHIPPED 2026-07-07** as SPEC §9 S10.4 named referent: a slash MAY carry additive optional `override_attestation_id`; when present the naming BINDS (the court judges the cited referent — a qualifying-but-unnamed override does not save the slash; junk names convict totally); when absent the scan applies verbatim, so every historical event keeps its bytes and verdict. Both implementations, one shared per-candidate predicate each (scan and named modes cannot drift); corpus scenario `g19-named-override-referent` pins the 4-way verdict incl. literal referent-arrival; honest `resolve_bond` refuses a bad citation live | Residue: naming is MAY, not MUST — a /3 court could require it and delete the scan entirely; deferred until a real consumer wants the stricter court |
| G20 | **Split-rule legibility** — when a pot lands on a fact that five consumed upstream judgements built, who gets what share is ad-hoc percentages; first-contact attribution (the G1 proxy) is the degenerate last-touch case | FRAMEWORKS F6; the alpha story (an idea carrying 1/8000 of a win) | **SHIPPED 2026-07-08** as `charge-attribution/1` (ATTRIBUTION-SPEC.md, `attribution.py`, V1–V5 on a separate `v_codes` surface; frozen corpora untouched): the split is exact-integer Shapley over the DPI carrying capacity the P-codes already charge — the characteristic function is a ledger fact, counterfactuals stay inexpressible — allocated by largest remainder, conserved by theorem (`Attribution.lean`: `alloc_conserves`, `walk_efficiency`, floor-only rule proven leaky axiom-free); a misdeclared split convicts from bytes (mismatch, non-conservation, phantom beneficiary, dropped contributor, unauditable report); the 1/8000-of-$100M story pays exactly $12,500.000000 as a passing test and an `rfl`; depth is not dilution in shares | Residue CLOSED same day (Part II, S11/S12): split-bound escrows disburse only along the recomputed rows and the stiffed contributor collects her own row after expiry permissionlessly; V findings joined the dirty court, source-precise. Still named: capacity is the proxy (Goodhart priced openly — quality pricing is the oracle layer's); declared reuse only (P.7's trust class); NMAX=12 arity refusal; Rust-twin parity for V/S11/S12 owed; outcome-conditioned split pots refused, not designed (/3) |

**Adopted doctrine (from the consults):** general-purpose personality
representation is a non-goal — chambers stay closed-vocabulary and
schema-bound; "understands you as a whole person" is what the protocol
refuses to know. And the Ethereum test is three properties — no
unilateral freeze (S8, shipped), no unauditable discretion (issuer
competition + ledgered refusals, owed), legible rules before transacting
(ledgered fee schedules, owed) — never global consensus, which would
surveil the very worlds this exists to protect.

The register is the build queue's raw input. Nothing here is a secret
shame; each row is a named, priced, deliberately-not-lied-about edge of
the protocol.
