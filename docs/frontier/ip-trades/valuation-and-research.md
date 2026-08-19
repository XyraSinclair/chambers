# Heterogeneous valuation and the estimated lane

Synthesis of a 56-agent deep pass on the two hard truths of IP trading: **value
is not a scalar**, and **the unprovable can be estimated**. All three design
debates resolved to synthesis at high confidence. Raw result:
`docs/autoresearch/` journal for run `wf_1a542b2c-284` (archived reasoning).

Method: 7 mechanism families and 6 novelty/OOD estimators characterized with
real theory and failure modes; 6 real-party personas (the priceless-yet-
barterable lab, the cash-poor attribution-driven researcher, the signaling-averse
lab, the antitrust/export-controlled one, the common-value winner's-curse setting,
the reputation-driven community); a fit matrix; an adversarial reality-check; four
judged designs; three debates; a completeness critic that caught real bugs in our
own code.

## Truth 1 — value is not a scalar

The current sampled-cross assumes scalar monetary value. Real parties don't have
one:

- **Priceless** — exclusivity itself is the moat; the owner won't sell at any
  monetary price, yet might barter for one specific complement.
- **Barter-only** — will trade IP-for-IP but not for cash (cash-poor, or
  unwilling to signal a spend/valuation).
- **Monetary** — a reservation price.
- **Attribution** — a researcher gives a technique near-free for citation /
  co-authorship / priority.

**Ruling (priceless-as-type vs infinite-reserve → synthesis):** a tagged
`Valuation` union, *not* a lexicographic scalar and *not* price=∞. Modeling
priceless as a huge number invites a mechanism to "meet the price" the owner
would never accept, and a finite ∞-proxy **leaks the owner's position**. So
priceless is `excluded_from_monetary_clearing` — a distinct branch. Shipped to
`iptrade.ts` as `Valuation` + `RefusalReceipt`.

**Fatal flaw, named not hidden:** the tag is uncertifiable cheap talk. A seller
can tag priceless to force a counterparty to disclose a complement in barter, or
privately hold a finite reserve. Mitigation (partial): put the bond on the
*resourced* party, publish a `priorityCommit` regardless of sale, and emit a
`RefusalReceipt` — which is itself discoverable evidence that contact occurred.
The substrate records the declaration and its non-verifiability; it does not
pretend to know the owner's true type.

## Truth 2 — the unprovable can be estimated

Cryptography marks novelty/transfer *unprovable*. A research substrate (Scry:
live SQL over papers/OpenAlex — verified returning real arXiv papers) can
*estimate* out-of-distribution-ness with evidence and calibrated confidence.
That is a fourth epistemic lane: **estimated**, between trusted and unprovable.

**The single sharpest mechanism move (`estimatesArePriceInputsNeverPayoffCliffs`):**
demote the OOD read from a binary unlock to a **continuous price haircut that
informs a human price**. Gaming a haircut is bounded; gaming a discontinuous
gate is catastrophic. The estimate **never promotes** to proven/trusted.

**Ruling (embedding vs structured evidence → synthesis):** the estimate is a
role-split contestable exhibit — `retrieval_prior` (cheap, informs search) vs
`valuation_gating` (feeds price) — carrying method, a named `NoveltyRoot`
(VRF-pinned corpus snapshot + ensemble-median embedder, committed *before*
negotiation to kill snapshot/embedder shopping), a confidence *interval*, and
citations.

**Ruling (research-before-price vs metered-probe → synthesis):** discriminate by
`EstimateProvenance` — a `corpus_relative` estimate is shared and one-time (no
per-buyer redistribution leakage); a `buyer_conditioned` deep read **debits the
buyer's leakage and cost budget**, because the closest-prior-art citation *is a
scoop map*. Shipped to `iptrade.ts` as `OodEstimate` / `NoveltyRoot` /
`EstimateProvenance`.

**The calibration-OOD paradox, typed as a non-claim.** The calibration set is by
definition known-novel/known-derivative pairs — *not* the frontier technique. And
a true crown jewel's nearest *public* prior art is far precisely because the real
prior art is *secret*. So **sparse prior art means UNKNOWN, not novel** — and
obscure phrasing reads sparse too. This was a real bug in our `novelty.py`
(sparse → confident 0.85); now sparse → OOD ≈ 0.50, confidence crushed to 0.20,
paradox flagged. Fixed and verified.

## The fatal flaws the pass refused to bury

- **The mechanism transfers surplus AWAY from the cash-poor indie it claims to
  shield.** Distribution-shaping rewards the party with more compute and better
  counterparty models; the winner's-curse correction is controlled by the
  cursing party; the estimator's confidence favors the well-resourced. Naming
  this is mandatory; a substrate that quietly taxes the weak is not one we
  would ship.
- **The winner's curse is real and the sampled cross amplifies it** for
  common-value IP. The estimated lane is the *fix* — it converts private
  common-value into a shared evidenced prior that shrinks the curse — but only
  if the shared signal is exogenous and non-manipulable (hence the VRF pin).
- **Everything is still bilateral.** Barter rings, combinatorial bundles
  (exposure problem: win X, its complement Y fails, you hold a standalone-wor\
  thless asset), and competing bidders are unbuilt.
- **The research substrate is not neutral** — it sees every technique it scores;
  it is a threat surface we hardened the crypto verifier against but not this.
- **Cost incidence is unfunded** — nobody pays for the enclave runs or the Scry
  tokens; for the cash-poor researcher, verification/estimation cost can exceed
  the trade.

## First wedge (build target)

A **barter-fairness oracle**: a two-party technique↔technique swap with **no
scalar price**, gated by a metered, dual-submitted, calibration-backed OOD
estimate. Both parties independently describe *both* techniques to the real
`novelty.py` ScryBackend; each query **debits the leakage accountant** on
(technique, observer) — wiring `novelty.py` into `leakage.py` so describing-to-
estimate counts against the budget; the swap clears only if both OOD reads and
both leakage budgets are within bounds. It makes both truths real at once.

## Bottom line

Value became a type, not a number. The unprovable became estimable — as a
bounded, metered, never-promoting, cliff-free price input, honest about the one
regime (crown jewels) where the estimate cannot be trusted. And the substrate
now names the surplus-transfer, bilateralism, and non-neutral-substrate problems
it does not solve, rather than letting a confidence number stand in for honesty.
