# Cognitive work markets — tight stories, ranked by buildability

A market is buildable today exactly where three things hold at once:

1. **Typed channel** — the deliverable survives compression into a small
   codebook (bounded capacity, leakage true by construction).
2. **Cheap gate** — a verifier whose verdict costs less than the work and
   whose own decision doesn't leak (public-data-only, or metered).
3. **Locked-out demand** — a buyer who cannot get the answer any other way
   (the data is private, the expert is scarce, or the aggregation doesn't
   exist).

Drop any leg and you have either research or slop.

Register (primitives/STRUCTURE.md, 2026-07-13): what leg 1 sells is
structural, not arithmetic. The codebook's promise to a buyer is
"nothing outside this finite set of sentences is expressible about the
counterparty's private world" — the alphabet is the object; its bit-size
is a footnote-grade composition budget. Pitches, receipts, and contracts
lead with purpose, audience, alphabet, and the counterfactual diff; a
pitch that leads with a bit number is theater (L1's word-tax lesson,
generalized). Nobody buys bits; people buy scoped rights and legible
receipts.

Ranked below from buildable-now to frontier, each with the story, the
gate, and the binding limit.

## 1. Bounded diligence attestation (the chamber, live)

**Story.** An investor pays for six bounded questions against a founder's
private work record. The founder's confined agent answers through the fixed
card schema; the investor gets calibrated buckets plus one drill-down;
the founder gets counterfactual-diff review before anything releases.

**Gate.** Envelope rejection on question shape (public-only, leak-free),
two preflight reviewers, owner release review, paired-silo egress diffs.

**Binding limit.** Free-text card fields blow the codebook; no
cross-question adaptive budget yet; demand tested at N=0 real requesters.
Adversarial-review addition: the packet is founder-curated, so the realistic
first payer is likely the FOUNDER (credibility signaling), not the investor
— whose free alternative is a call plus reference checks. Until one real
requester runs it, treat the buyer side as unknown, not assumed. This is
the reference implementation — every market below reuses its skeleton.

## 2. Private reference checks (hiring)

**Story.** A candidate can't show their last employer's repos. Their agent
answers "does the record show recovery after stalled work?" from private
history, releasing only bucketed evidence cards. Employers get signal that
resumes can't fake; candidates never expose a single artifact.

**Gate.** Same as 1, plus the candidate controls the packet (selection bias
is disclosed as a scope limitation card, not hidden).

**Binding limit.** The candidate curates their own evidence — the market
needs the *counter-signal card to be mandatory* and the buyer to price
curation in. Defamation/legal surface if answers go negative. Buildable
now; trust story is the work.

## 3. Committed alpha attestation (public oracle — strongest math)

**Story.** A researcher claims their private signal predicts returns. They
commit a hash of signal outputs today; in 90 days a neutral harness scores
the commitment against public prices and releases one number: IC bucket.
The signal never leaves their machine. Buyers pay for the attestation
stream, then for the signal.

**Gate.** Exact and public — returns are an oracle nobody controls. The
only real gate is the **registration ledger**: every commitment is charged
against a per-identity budget so you can't fire 500 signals and reveal the
one that hit. Honest scope: the underlying problem is selective inference /
multiple comparisons — the odometer supplies the per-identity charging
mechanism, not a family-wise-error guarantee, and sybil identities (L3)
bite hardest exactly here.

**Binding limit.** Statistical power and incumbents, not math: a 90-day IC
bucket poorly separates a mediocre signal from a good one, and buyers
already have a cheaper instrument (paper-trade the researcher for a
quarter; Numerai runs the hosted version). The surviving niche — researcher
refuses everyone's infra AND buyer accepts a low-power bucket — is real but
thin; five buyer conversations settle whether it clears before more code.

## 4. Two-sided confidential consults (expert judgment)

**Story.** A startup wants a named security researcher's read on their
codebase; neither side will disclose (code is secret, the expert's playbook
is their livelihood). The expert's methodology runs as a confined worker
over the client's packet in a chamber neither controls; out comes a typed
verdict: severity buckets, evidence cards, next-step. Expert paid per
verdict; playbook never copied; code never seen by a human.

**Gate.** Dual confinement (both inputs sealed), typed verdict, and —
because judgment has no oracle — a **stake**: the expert escrows against a
later-audited sample of their verdicts. This is where the settlement kernel
(conservation, escrow, S-audits) stops being theory.

**Binding limit.** Verdict quality is unverifiable per-instance; the
staking/reputation loop needs repeated games and real participants. Also
the worker model is rented — see limit L4.

## 5. Clean-room overlap verdicts (IP mediation)

**Story.** Two labs suspect a patent/codebase overlap. Full discovery is
mutually assured destruction. Each seals a corpus into a chamber; a
confined agent answers exactly one question — "overlap: none / narrow /
substantial, with N bucketed loci" — and both sides get counterfactual-diff
review before release. Litigation avoided for the price of a demo.

**Gate.** Paired-silo diffs run per-party: each side sees what the verdict
would have been without their crown jewels, so consent is informed.

**Binding limit.** The useful verdict and the strategic leak are close in
capacity — an adversarial corpus can try to exfiltrate through the verdict
alphabet. Needs the capacity odometer *proven over the verdict schema*
before adversarial parties would sign.

## 6. Attention gating (the decision is the product)

**Story.** Your agent reads your firehose. Third parties pay a bond for one
bounded slot of your attention iff their pitch clears your gate; bond burns
on rejection. Spam becomes economically self-limiting.

**Gate.** The gate itself — which is why the **simulatability law** is
load-bearing here: rejection must be predictable from the public envelope,
or every bounce leaks your private preferences one bit at a time.

**Binding limit.** We have not audited any gate for
private-data-independence. Until that law is checkable, this market leaks
by construction.

## 7. Cohort aggregates (real DP, weakest per-unit demand)

**Story.** Fifty seed-stage founders contribute private telemetry; the
market sells "median ships/week, p90 stall-recovery time" with a provable
ε. The one market where classical differential privacy applies cleanly —
numeric aggregates, neighboring-worlds semantics, composable budget.

**Binding limit.** Cold start (aggregates are worthless at N=5) and
per-unit willingness-to-pay. Build it as a free layer on top of markets
1–2, not standalone.

## The limits ledger — what we cannot currently sell

- **L1: Open-ended prose from private data.** "Write me a memo" is the
  biggest market and an unbounded channel. No codebook, no guarantee. This
  is the frontier, not the product. Everything above works because it
  refuses this. Standing self-audit: the LIVE chamber demo currently sells
  metered prose (~11.5 kbits per release by its own 48-bits/word ledger,
  vs the ~13-bit codebook story) — it demonstrates the odometer posture,
  not the codebook posture, and the pitch must never conflate the two.
  Resolution register (STRUCTURE.md): both postures pitch structurally,
  at two honesty levels — codebook products lead with the alphabet;
  odometer products (metered prose has NO closed alphabet) lead with
  audience, purpose, counterfactual diff, and the meter, and must say
  the no-closed-alphabet part out loud. Metered prose stays a priced,
  named exception, never the story.
- **L2: Per-instance judgment quality.** Where there's no public oracle
  (markets 4, 6), quality is only enforceable in the repeated game —
  staking + audited samples. The settlement kernel is proven; it has zero
  participants. One repeated buyer-seller pair is worth more than any
  further theorem.
- **L3: Cross-identity adaptivity.** Budgets are per-passcode. A sybil
  requester with k identities gets k budgets. No current answer beyond
  pricing (make identities cost money) — say so in every contract.
- **L4: The rented worker.** Confinement is local-OS; the model API sees
  the packet. Honest posture today: the packet's counterparty risk includes
  the model vendor. Upgrade path: local weights, then TEEs. Do not paper
  over this.
- **L5: Pricing.** Attribution math (Shapley, conservation) is proven;
  what a verdict is *worth* is discovered only by markets 1–3 clearing at
  a real price. No theorem substitutes.

## The one-line frontier

Sell verdicts, not prose: today's buildable markets are exactly those whose
deliverable fits a small codebook and carries either a public oracle (3, 7)
or a stakeable reviewer (1, 2, 4, 5). Every expansion of the codebook is a
priced, metered widening — never a default. What the buyer holds is a
bounded computation right; what the seller keeps is everything the
alphabet cannot say.
