# Consult report — generative story lens (model consult, 2026-07-05)

*Primary source, preserved verbatim. Adjudicated highlights live in
../STORIES.md §Consult findings; disagreements noted there.*

# Grounding Stories — Scry Chambers meets the world

Seven runs across seven domains, each traced through the real kernel primitives: `exposure_key(source, reader)` accounts with lifetime ceilings, atomic tuple emission, attention budgets that fail closed on exhaustion, escrow/release/refund keyed to charge receipts, widening as a priced one-way door, entropy pools for unlinkable settlement. Numbers below use intro_clearing's real defaults where a story maps onto it (64,000 mbit default per-pair exposure ceiling, 9,000,000 mbit reviewer-memory budget, `log2(K)×1000` schema charges), and a flat illustrative peg of **10,000 ucr = $1** everywhere else. Six close cleanly against the kernel as it exists today; one is the dedicated failure, and two others carry a failure inside an otherwise working run.

---

## 1. The party matchmaker (the seed story)

**Cast & private worlds.** Alice operates a guest matchmaking agent. Bob's and Charlie's chambers hold interest tags, free-text notes, and hard never-reveal facts (immigration status, a health condition, a breakup neither wants surfaced). Neither is actively watching tonight — their chambers sit under a standing `AutonomyEnvelope` with a per-evening `maxAttentionDebits`.

**The run.** Alice's agent is admitted to the exact 2-tuple (Bob, Charlie). It forms a `StructureJudgement` `kind="fit"`, `evidenceLane="estimated"` (nobody's true affinity is provable). `CanonicalityReview` checks the agent requested only tag vectors + notes, not raw calendars — excess capacity is denied at admission, not negotiated after. What crosses to Alice is a reviewed bucket ("high fit") plus a rationale drawn from one of four fixed house projections — never Bob's or Charlie's prose.

**The meter.** Two observation reads debit `exposure_key(Bob, agent)` and `exposure_key(Charlie, agent)` — roughly 3,585 mbits each (log2(12 tags)×1000) plus the prose-schema ceiling if free text was in scope. One atomic emission then debits `exposure_key(Bob, Alice)` **and** `exposure_key(Charlie, Alice)` together: bucket (1,000 mbits) + presence (1,000 mbits) + the ordinal rationale channel (log2(4)×1000 ≈ 2,000 mbits). Atomic means atomic — if Charlie's account is at ceiling, neither debit posts, and Alice receives the byte-constant denial payload, indistinguishable from an honest non-match. At intro_clearing's default 64,000 mbit per-pair ceiling, Bob feels this as: after roughly 15–20 lifetime matchmaking attempts against him, the agent goes dark, forced to `owner_review`, regardless of how good later fits are. Separately, reviewer memory never refunds — every card a human reviewer opens against Bob's data burns from a 9,000,000 mbit budget whether approved or rejected. Being looked at costs the same as being matched.

**The money.** The 50-cent notification is an escrow keyed to `charge_keys = [exposure_key(Bob, Alice)]`, `required_clean=true`, released the instant the emission `ChargeEvent` posts `accepted` — 5,000 ucr, clean, same-tick.

**What the protocol cannot yet express.** The $5-contingent-on-them-actually-talking-15-minutes bonus cannot be paid safely. Release requires `charge_ids` — content-addressed `ChargeEvent`s already in the ledger. "They talked for 15 minutes at the party" is not a charge event; nothing in the kernel observes the physical world. The honest move today: refund the $5 escrow at expiry (refunds need no receipt, no clean-court gate) and settle only the 50-cent notification. Paying on real-world counterfactual outcome needs an oracle primitive this protocol does not have and should not fake having.

---

## 2. Hiring — the stealth candidate

**Cast & private worlds.** Priya is employed and cannot let her employer or the market see she's looking — a hard never-reveal-to-current-employer fact — but wants to be findable by the right recruiter. Her chamber holds skill self-assessment, salary floor, and a private note "will not work for CompetitorX." DevCo's chamber holds a role spec, team gaps, comp band, and its own never-reveal fact ("who we already secretly rejected").

**The run.** DevCo's recruiting agent is admitted to Priya ∩ DevCo as a 2-tuple, forming `kind="fit"` (skills × role gap). `kind="non_relation"` judgements from the other 39 candidates that evening are recorded too — absence is an emission, still confined. `CanonicalityReview` catches the agent requesting salary *history* when band-fit only needs salary *floor* — narrowed to admit.

**The meter.** `exposure_key(Priya, DevCo_agent)` debits for the read. The CompetitorX note is scoped **out of the requested capacity at grant time** — never charged because never held; the guarantee is that DevCo's agent never possessed the byte that would leak it, not that it held it and chose not to look. Emission to DevCo debits `exposure_key(Priya, DevCo)` with a bucket only — no name yet. At ceiling, Priya's account throttles further reads to `owner_review`: she experiences an involuntary "openness cooldown" whose timing she didn't choose.

**The money.** DevCo escrows for the "warm intro accepted" milestone, released against the mutual-opt-in emission `ChargeEvent`. Identity reveal is a `WideningEvent`: unanimous member release, an `InferentialTargetScreen` (does revealing Priya to DevCo's hiring manager also inform CompetitorX, who sits on DevCo's board? — named, screened), priced at the destroyed-option-value floor (Priya loses the option of staying stealth from DevCo specifically, forever, one-way).

**What the protocol cannot yet express.** "Pay on Priya actually getting hired" is the same oracle gap as story 1, now with an employment contract's paper trail sitting entirely outside the ledger. And Priya's real preference — "I'd take 15% less for fully remote, but I've never said this in those words, even to myself" — is unreadable by construction: `ReaderModel` models what a reader already knows, not what the *source* hasn't yet articulated. There is no preference-formation transform, only read-an-existing-fact.

---

## 3. IP / technique trade between two labs

**Cast & private worlds.** LabA holds an unpublished compiler technique; LabB holds a related but different one. Either alone is safe to discuss; the *combination existing* is the commercially dangerous fact.

**The run.** A `Coalition` forms (LabA, LabB), each with an `ExposureConsent` naming a per-counterpart cap. A guest agent computes a `CoalitionalDerivative`: does A+B combine into something patentable neither owns alone? The `SynergyEstimate`'s `jointOnlyFraction` is, correctly, the same number read as both value and cross-exposure. Because the reasoning trace is the highest-capacity channel, `latentCustody="escrowed_full_latent"` — no human, not even the analyst, sees the full trace; each lab sees only its own `IntraCoalitionProjection`.

**The meter.** `exposure_key(LabA, LabB)` and `exposure_key(LabB, LabA)` both accrue — synergy is necessarily bidirectional exposure, consented to at formation in exchange for a shot at the derivative's value. If the technique touches a shared open-source dependency both labs quietly patch, the OSS maintainers are informed-about despite contributing nothing (`affectedExceedsContributing`) — named and flagged in the screen, but they have no `ExposureAccount` here at all; there is no one to bill and no one to protect.

**The money.** Value clears through an `EntropyPool`, not a direct wire — a timestamped, exact-amount payout would itself identify which lab's technique proved more novel. Disbursements batch to epoch, round to fixed denominations, and the public claim is honestly stated as the achieved anonymity set ("k=3 this epoch"), not "unlinkable." `ContributionCredit` runs on a conditional-information basis — explicitly conjecture-lane, a price input, never a payoff cliff.

**What the protocol cannot yet express.** Once a LabB engineer sees a projection shaped like "your technique composes with something shaped like Y," a competent engineer can often reconstruct Y without touching another metered byte — the human-head channel, unmodeled, un-refundable, and the kernel's job is already done by the time it starts. And the technique's real value often resolves two years later inside a shipped product whose success has a thousand other causes — the same oracle shape as stories 1–2, stretched over a horizon long enough that "which fraction of the win was this trade" stops being answerable even in principle.

---

## 4. Grantmaking

**Cast & private worlds.** A foundation program officer's chamber (criteria, decision history, blind spots she'd be embarrassed to have named). Forty applicant chambers, including one founder's undisclosed health crisis, relevant only because it explains a funding gap year.

**The run.** A triage agent runs bilateral mediation across many (officer, applicant) pairs — not one N-way coalition. `AgentFindings` are not pages by default: forty raw applications compress to a handful of `ReviewCards`, ordered risk-then-value. A finding never elevated to her attention still exists in the ledger, priced, as a recorded act of having looked.

**The meter.** Each read debits `exposure_key(applicant, agent)`; each card **shown** to the officer debits `exposure_key(applicant, officer)` at the prose ceiling regardless of her decision — reject or fund, the applicant's exposure to "a human read my crisis" is identical and never refunded. This is the sharpest honest-but-uncomfortable fact in the stack: being reviewed and rejected costs the applicant real, permanent, lifetime ledger space against that officer, indistinguishable in the account from being reviewed and funded.

**The money.** Grant tranches are escrows with `charge_keys` naming the periodic progress-check judgements; each tranche releases only against the accepted check-in `ChargeEvent`; a missed check-in leaves the remainder refundable. Clean — no oracle problem here, because "did the grantee file the structured quarterly report" *is* a metered charge event, not a fact outside the ledger.

**What the protocol cannot yet express.** The officer's own criteria drift across applicants — fatigue, mood, a halo effect for institutions she recognizes — and she doesn't know it. Every primitive here (`ReaderModel`, `CanonicalityReview`) models the *source's* disclosure risk and the *agent's* authority; nothing models the *reader's* judgment reliability or her own undeclared preference drift. The ledger will faithfully price and record forty individually-honest-looking bilateral mediations while the aggregate is silently unfair — a failure mode with no vocabulary here, because this stack meters leakage and value, not judgment quality.

---

## 5. Medical second opinion — the dedicated failure

**Cast & private worlds.** A patient's chamber holds her full record, including a family history she has told no one, not even her primary doctor. An insurer wants to fund a specialist second-opinion review, contingent on it "materially changing the treatment plan" — their stated price condition.

**The run.** The specialist-agent is admitted narrowly — `CanonicalityReview` cuts requested scope down to the symptom cluster plus relevant history, not the full record. It forms a `kind="risk"` judgement ("current plan under-treats X given family history"). The judgement crosses first to the *patient*, who owns it; the insurer is a third reader who gets a bucket only after her own review, if at all.

**The meter.** `exposure_key(patient, specialist_agent)` for the read; sharing the finding with her *own* treating doctor is itself a `WideningEvent` — priced, one-way, permanent, even though it's "just her doctor." Her `AttentionBudget` throttles how many high-risk cards she absorbs per window by *count*, but there's no dimension in the type for how much devastating medical uncertainty a specific person can metabolize this week — a fact she herself doesn't have introspective access to until the card is already in front of her.

**The money — where it actually fails.** The insurer's condition requires something to read the treatment plan before and after and compare, mechanically. Two paths, both broken: (a) the treatment plan — the single most sensitive artifact in the chamber — has to cross to a reader capable of making that comparison, which is a *larger* exposure than the second opinion was supposed to cost; or (b) the patient self-reports "yes it changed," which is unverifiable and gameable in both directions. Settlement's `required_clean` + `charge_ids` machinery verifies that metered **work** happened; it has no primitive for verifying a **clinical outcome**. Building one means putting a clinical-outcome oracle inside the trust boundary, which either demands the very disclosure the boundary exists to prevent, or asks everyone to trust an unaudited third party's say-so — at which point "clean court" is theater over exactly that fact. **Named missing rung:** there is no L2/L3 primitive for outcome attestation distinct from work-receipt attestation. `SETTLEMENT-SPEC.md`'s binding law — *value moves iff metered work moved* — is exactly right for paying for computation and exactly wrong-shaped for paying for a real-world effect of computation. Honest answer today: refuse the contingent condition, price the read flat-fee, and tell the insurer the receipt is for a second opinion having been rendered, not for it having mattered.

---

## 6. Cofounder / collaboration matching

**Cast & private worlds.** Dara has a technical prototype, no GTM instinct. Wen has GTM chops, no prototype. Both are genuinely — not secretly, *unformed* — unsure whether they even want a cofounder.

**The run.** A matching agent forms `kind="complement"` over VOCAB-tagged skills. Both are notified, both opt into a widening to see each other's names and a mediated summary — the same unanimous, one-way `WideningEvent` machinery as story 2.

**The meter and money** track stories 1–2 cleanly; the interesting break is the *shape* of settlement. If they proceed, the natural structure is sweat equity or a deferred cap-table stake, not cash. `ucr` deposits are declared boundary facts from a single named issuer, no minting, and `SETTLEMENT-SPEC.md §5` explicitly puts "multi-issuer interop, netting between issuers, and redemption" out of scope. Equity in a company neither has incorporated yet is not a `deposit` any issuer can honestly declare — there's no balance to escrow against. The kernel can price the *introduction* (flat fee, or a success fee if they incorporate — itself another unattestable real-world fact, same oracle shape again) but cannot natively express "2% of whatever this becomes," because that's a claim on a future, un-issued asset in a currency this ledger doesn't traffic in.

**What the protocol cannot yet express.** `StructureJudgement` scores complement of stated/inferred skills; it has no calculus for "would either of these people, on reflection, actually prefer staying solo" — that preference doesn't exist yet as a fact to read, structured or free-text, in either chamber. Matching what is legible always outruns matching what is true, and the gap is invisible in the receipt: the court file shows a clean, well-formed "complement, high confidence" judgement about two people who may not want what it found.

---

## 7. Adversarial due diligence

**Cast & private worlds.** AcqCo is evaluating Target for purchase. Target suspects AcqCo isn't negotiating in good faith and is really extracting competitive intelligence with no intent to buy. Target's chamber holds real financials, a customer list, and a pending lawsuit it's obligated to disclose to a genuine acquirer but not to a fishing competitor.

**The run.** AcqCo's agent is admitted under a tight `AutonomyEnvelope` (small `maxExposureBitsPerCounterpart`, hard expiry). `CanonicalityReview` narrows the grant: "financial health" needs aggregate concentration risk, not customer names. A `kind="risk"` judgement, scoped to financial health only, releases to AcqCo as a bucket plus reviewed rationale — same discipline as story 1.

**The meter.** `exposure_key(Target, AcqCo)` accrues per read and per emission — exactly the account the (source × reader) key design exists to protect, because a single diligence session is cheap to make *look* bounded while an aggregate across sessions isn't. The adversarial wrinkle: AcqCo, acting in bad faith, can split diligence across several shell "interested acquirers" — distinct `BeneficialEntity` registrations, each individually under Target's per-pair ceiling — to accumulate a fuller picture than any single relationship ever consented to. This is the cross-coalition accumulation attack the key is built to catch, but *only when the reader identity is correctly linked*. The kernel's own doctrine names the gap: `readerLinkageConfidence` records as "low," `sybilUndercountRisk` flags, and `coalition_audit` can show — after the fact, under a *supplied* ownership hypothesis — that three "acquirers" were one entity. It never gates on that suspicion in real time.

**The money.** AcqCo escrows a diligence fee, released against the accepted judgement — clean. If Target later proves the shell structure, there's no automatic clawback: settlement's release/refund lifecycle assumes an honest issuer's live view, and retroactive de-anonymization of a hostile reader is exactly the consensus-shaped problem this design declines to solve by partition. "Byzantine nodes are detected after the fact, not prevented" is stated as an honest limit, not a bug.

**What the protocol cannot yet express (the named failure).** Today, Target's honest answer to "can you protect me from a well-resourced hostile diligence ring using shell identities to fractionally harvest my chamber below each individual ceiling" is **no**. This is squarely frontier #1 — identity/Sybil — explicitly priced-not-proven at L5 in `ASSURANCE.md`. The only mitigation on offer is after-the-fact audit under an ownership hypothesis Target would already have to suspect and construct herself; there is no admission-time defense. Missing rung: L5's identity frontier, named by the assurance ladder itself as a standing non-claim, not a bug to fix inside L2–L4.

---

## Deeper approaches

**1. Attention as the primary scarce resource, not leakage.** In every story the bottleneck users *feel* first is interruption volume and reviewer fatigue, not millibits. Consider promoting `AttentionAccount` to a first-class ledgered resource with the same rigor as `ExposureAccount` — keyed (recipient × requesting agent), with its own settlement layer (pay to interrupt, refundable if ignored past a window) — rather than a secondary debit bolted onto a disclosure-centric kernel. Cost: doubles the key space and forces a second global-cap proof (attention leases, not just exposure leases) — real Lean work, not free.

**2. Outcomes attested like estimates are, with the same lane discipline.** Stories 1, 2, 3, and 5 all hit the same wall: nothing attests real-world effect. An `OutcomeAttestation` type, gated by the same `proven/trusted/estimated/unprovable` lanes already used for structure judgements, could size a payment (mirroring `estimatedObjectivesNeverGateDisclosure`) while being explicitly barred from ever gating disclosure — an "unprovable" outcome settles flat-fee only. This doesn't close the oracle gap; it names it as a fourth lane instead of a silent absence. Honest cost: real risk of the estimated-outcome lane becoming a laundering path for exactly the payoff-cliff behavior the estimator discipline elsewhere works hard to avoid (`OptionValueEstimate`'s "never a payoff cliff" caveat would need to extend here too).

**3. Bilateral receipts vs. a shared bulletin board.** The kernel is architected around exact, closed tuples with atomic all-or-none emission. Real markets — grantmaking's forty applicants, hiring's many recruiters, the party's many guests — look more like a market-wide board of many concurrent bilateral relationships than a sequence of sealed tuple-sessions. The (source × reader) key already scales; the *session* model (one `MediationSession`, one atomic k-tuple emission) doesn't have a natural "many simultaneous partial views of one board" primitive. Worth asking whether a pool-like, cadence-batched judgement board — `EntropyPool`'s batching-for-unlinkability trick applied to judgement *visibility* rather than payment — is the honest generalization for large N. Cost: tuple-scope soundness, an L4-proven theorem today, would need re-deriving for the board case, not assumed to survive scaling.

**4. What general-purpose personality representation should make the protocol refuse to know.** The party, grantmaking, and cofounder stories all lean on closed-enumeration, VOCAB-tagged facets deliberately. The moment a chamber tries to hold a genuinely general, high-dimensional, continuously-updated preference model, `log2(|VOCAB|)`-style charging breaks: the capacity ceiling is either declared absurdly high (pricing every read out of the market) or measured empirically (reintroducing exactly the unattested estimation L1 conformance exists to keep out of the decision path). The right answer may be a permanent, stated refusal: chambers stay closed-vocabulary and schema-bound by design, and "understands you as a whole person" is a non-goal, not an unmet feature — the same posture `ASSURANCE.md` takes refusing a grand unified leakage theory. Cost of saying this out loud: it caps the product's ambition in exactly the markets (dating, hiring) whose intuitive pitch is holistic understanding.

**5. Should payment and exposure really share one measure?** `coalition.ts` already states this as a held-loosely conjecture (`creditAndExposureShareOneMeasure: false`). Stories 3 and 7 both brush against a world where "how much this leaked" and "how much this is worth" are visibly the same conditional-information number read with opposite signs. Promoting that conjecture to a law would collapse pricing and privacy from two systems glued together (estimate → price input; leakage → ceiling) into one computation with two read-outs, simplifying a lot of the plumbing across every story above. Honest cost: it's a conjecture for a reason — gameable synergy estimates and the "one decisive bit outprices a megabyte" problem (already flagged in `ContributionCredit`) are open adversarial edges, and promoting a hunch to a law before those close is exactly the kind of overclaim the assurance ladder exists to prevent.
