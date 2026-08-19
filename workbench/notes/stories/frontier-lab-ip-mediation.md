# Story 8 — Frontier labs: IP mediation at the top of the market

*Full-depth companion to STORIES.md §8. Grounding literature confirmed
against the Scry academic corpus (OpenAlex), 2026-07-05: "Algorithmic
progress in language models" (2024 — pre-training algorithmic efficiency
has historically doubled on a sub-year cadence, i.e. a private technique's
edge is a fast-depreciating asset); the speculative-decoding and
model-merging/weight-averaging literatures (the archetypal discrete,
transferable, benchmarkable techniques); "Emergent Abilities of Large
Language Models" (2022 — capability surprise as the safety-side trade
object). The industry fact that frames everything: since roughly the
GPT-4 technical report — which disclosed, in its own words, no
architecture, hardware, data, or training-method details — frontier labs
stopped publishing the recipes. The information is now PRIVATE CAPITAL,
and there is no market infrastructure for trading it. That absence is
this story's market.*

---

## Cast & private worlds

**Halcyon** and **Meridian**, two frontier labs. Halcyon's chamber holds
its pretraining stack: a data-curation pipeline (the crown jewel), a
distributed-training trick worth ~1.4× MFU, negative results on three
architecture variants everyone else is still burning compute on.
Meridian's chamber holds an inference-time stack: a speculative-decoding
variant, a KV-cache scheme, and a dangerous-capability eval suite with
elicitation methods they will never share (the methods are themselves
capability uplift).

Never-reveals on both sides are structural, not itemized: **the recipe
never crosses — only judgements about the recipe cross.** Each lab also
holds the industry's most explosive meta-fact as an unregistered
sub-source: which of its published benchmarks were, internally,
disappointments.

Three deal shapes, in ascending intimacy:

## Deal 1 — The duplication check (freedom-to-operate without disclosure)

Both labs suspect they independently discovered the same unpublished
attention-variant result. If true, both are wasting a patent race and one
of them is sitting on a redundant trade secret; if false, each is
over-estimating the other. Today this question is *unaskable* — asking it
leaks that you have something in the neighborhood.

**The run.** A guest agent (built by neither lab; canonicality-reviewed)
is admitted to the exact 2-tuple. It reads both technique descriptions
in-chamber and emits ONE typed judgement toward both requesters
atomically: `kind="overlap"`, value from {substantially_same, distinct,
partially_overlapping} — log₂3 ≈ 1,585 mbits against each lab's exposure
account, plus the presence channel. Nothing else crosses. If the answer
is "distinct," each lab has learned almost nothing about the other's
technique — that is the *product*, not a limitation.

**The meter.** `exposure_key(halcyon_pretraining, meridian)` and its
mirror, lifetime scope. The atomic emission is load-bearing exactly as in
the party story: a judgement about overlap is inseparable from both
inputs; the first refusal blocks it entirely.

**The money.** Flat fee each, escrowed, released against the emission
receipt, `required_clean=true`. Boring on purpose — the value here is
that the question became askable at ~1.6 kmbits, not that the pricing is
clever.

## Deal 2 — The technique trade (where the oracle gap CLOSES)

Meridian wants to know whether Halcyon's data-curation pipeline would
improve *Meridian's* runs before paying license-scale money. This is the
$5-if-they-talk problem at nine orders of magnitude — and here, uniquely,
the current protocol can already express it, because **the contingent
outcome is itself in-chamber metered work**.

**The staged run.**
1. *Sketch.* Halcyon's chamber emits a schema-bound characterization
   (technique class from a fixed vocabulary, applicability enum, claimed
   effect-size bucket) — a few thousand millibits against
   `exposure_key(halcyon_pretraining, meridian)`. Escrow₁ releases
   against this emission's charge events.
2. *Mediated reproduction.* The guest agent carries the full recipe into
   a THIRD chamber — a rented, attested training enclave neither lab can
   read — and runs it against a Meridian-supplied proxy corpus and
   baseline. `latentCustody="escrowed_full_latent"`: no Meridian human
   ever sees the recipe; no Halcyon human ever sees Meridian's baseline
   internals. What emits toward Meridian is a typed repro verdict:
   effect-size bucket, confidence ordinal, applicability caveat enum —
   charged at schema ceiling against
   `exposure_key(halcyon_pretraining, meridian)` AND
   `exposure_key(meridian_evalstack, halcyon)` atomically (the verdict
   carries information about both stacks; neither side is a privileged
   sink).
3. *License.* Escrow₂ — the license-scale money — releases against the
   repro verdict's charge events. **`charge_ids` all the way down: "pay
   on repro" needs no outcome oracle, no attestation lane, no G1
   machinery, because the outcome IS a ChargeEvent.** This is the
   protocol's best-fitting domain, and the reason to build the wedge
   here first.
4. *Full transfer on settlement* is a new consented account —
   `composition_key(halcyon_curation, method_reveal_paid, meridian)`
   with its own ceiling the reveal exactly fills — never an in-place
   raise (the min-resolution audit law; same pattern ip_trade_sim
   shipped).

**The money's unit is honest here too:** ucr deposits backed by *compute
credits* — unlike the cofounder story's un-issued equity (G11), compute
credits are exactly what a deposit models: a declared, issuable liability
of a named issuer. Frontier labs already denominate value in it.
Settlement clears through an `EntropyPool` batched to epoch: a
timestamped exact-amount license payment would itself leak which lab
needed whose technique — the *direction of dependence between frontier
labs is market-moving information*, so the anonymity set is stated
honestly ("k=3 this epoch") and priced.

## Deal 3 — The safety-eval exchange (asymmetric never-reveals, third reader)

Meridian's dangerous-capability evals would genuinely improve Halcyon's
pre-deployment testing. Meridian will share *results and thresholds*,
never *elicitation methods* — the methods are capability uplift (the
emergent-abilities literature is precisely about capability arriving as
a surprise; elicitation is where the surprise lives). And both labs'
regulator wants evidence the exchange happened.

**The run.** Eval verdicts cross as enum/ordinal judgements; elicitation
lives in a never-leased sub-source (zero ceiling by non-registration —
G5's partitioning discipline doing real safety work). The regulator is a
THIRD reader with its own exposure accounts against both labs: it
receives the fact-of-exchange and threshold-conformance buckets — a few
hundred millibits — not the evals themselves. The court file is the
compliance artifact: a stranger-verifiable receipt that the exchange
happened, at what capacity, touching whom. **Byte-for-byte, this is
d1_bounty's VEX shape** — typed verdicts about a sealed artifact, charged
at adversarial max — which means the conformance corpus already exercises
this deal's accounting.

---

## The meter under adversarial pressure

**Verification-as-extraction is THE attack here.** Meridian could run
Deal 2's sketch stage against Halcyon monthly forever — each individually
cheap, jointly a distillation campaign reconstructing the pipeline. This
is exactly what the lifetime `(source × reader)` composition account
exists for: demand accrues on refusals too, the incident latch fires on
uncapped demand, and the campaign becomes a *ledgered fact* Halcyon's
next pricing round can read. The egress-accountant was built on this
shape; the frontier-lab version is the same algebra with more zeros.

**The human-head channel runs at maximum intensity.** Researchers move
between these specific labs at industry-maximum rates, and a competent
engineer who sees "your technique composes with something shaped like Y"
can often rebuild Y unmetered. The protocol's honest posture (L5, priced
not proven) has a concrete institutional analog the industry already
runs: clean-room/clean-team protocols. Chambers make the clean team
*mechanical and auditable*; they do not extend it into anyone's memory.

**Sybil is WEAK terrain for the attacker here** — a rare inversion.
Story 7's shell-acquirer attack fails against frontier-lab counterparties
because the reader identity is thick: there are single-digit entities
whose repro verdicts matter, their beneficial ownership is public, and a
shell "startup" requesting mediated access to a pretraining stack is
self-identifying. The (source × reader) key is at its strongest exactly
where each reader is few, named, and heavily capitalized.

## What this story exposes (the new gap)

**G13 — declared entropy depreciates, and the ledger cannot say so.**
A technique's `subject_entropy_mbits` is meaningful only as its delta
over PUBLIC knowledge — the reader-model baseline is, literally, arXiv.
And that baseline moves fast: the algorithmic-progress result puts
efficiency-technique half-lives under a year. Two consequences the
protocol cannot yet express:

1. *Depreciation.* When a third party publishes your secret's
   neighborhood, your declared entropy is stale-high: ceilings derived
   from it are too generous and leakage classes too lenient. Re-declaring
   downward today hits I7 quarantine (min-resolution *accepts* the lower
   figure — the conservative direction — but marks the account
   conflicted forever). Missing: a versioned re-declaration event, owner-
   signed, monotone-down, that does not convict. Monotone-down matters:
   it is the same escalation direction the merge laws already prove, so
   the Lean story extends rather than reopens.
2. *Expiry pricing.* Lease `expires_tick` should be priced to
   publication velocity — a lease on curation-pipeline exposure that
   outlives the technique's expected public half-life is mispriced by
   construction. That is an estimator-layer discipline (declared, above
   the protocol), but the spec should name it.

Corollary worth stating plainly: **the estimator for frontier-lab deals
must be an arXiv-reading institution.** Declaring delta-over-public-
knowledge IS a literature review with a signature; estimator independence
(G8's economic capture, acute here — the seller wants the delta
overstated, the buyer understated) is the whole ballgame, and
"adversarial_review" independence class stops being a nicety and becomes
the only admissible class either side should accept.

## Why this is the wedge

Ranked against every other story: the counterparties are few, sophisticated,
already denominate value in compute, already run clean-team institutions
the chamber mechanizes, are structurally strong against Sybil, and — the
decisive property — their contingent outcomes (repro, eval conformance)
are *in-chamber metered work*, so the deepest missing rung (G1) never
bites. The mediated-reproduction enclave (Deal 2, stage 2) is the TEE/
verified-execution frontier (#6) — real, priced, and the only piece of
new infrastructure the deal actually needs.
