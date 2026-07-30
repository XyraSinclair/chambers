# Consult report — adversarial mechanism-design lens (model consult, 2026-07-05)

*Primary source, preserved verbatim. Adjudicated highlights live in
../STORIES.md §Consult findings — including the adjudicating review's CRDT-purity
correction to the rank-1 fix (shipped as permissionless
default_resolution / S8) and the lease-perimeter correction to the
demand-griefing finding.*

# Adversarial review: Scry Chambers settlement/meter economics

## 1. Incentive attacks on the current protocol

**(a) Silent holdup — the sharpest hole.** In `charge-settlement/1`, only the `issuer` emits `release`/`refund`; the payee has no unilateral claim path. An issuer can simply never act on a clean, fully-metered escrow. S1–S7 only convict *affirmative false claims* — there is no code for "did nothing." A stranger auditing the fold sees `remaining(e) > 0` and reads it as prudence, not stall. This also means **selective refusal** (issuer favors payees who kick back, stalls others) is likewise invisible — nothing distinguishes principled caution from favoritism, because refusal itself is never a ledgered, attested act. [LEAD NOTE: shipped same-day as permissionless default_resolution + S8, with the fold kept a pure function of the event set — the consult's tick_now-in-fold sketch would have broken CRDT purity.]

**(b) Estimator capture, not just self-interest.** Admissibility only checks a self-declared `independence` string; nothing tests *economic* independence. A requester can retain an "operator"/"role_separated" estimator who systematically under-declares `estimate_total_mbits` for that requester's traffic. Every individual charge stays audit-clean (I2 relies on `cumulative_mbits`, computed *from* the falsified debit — the audit has no independent ground truth). Cheap fix: a declared `estimator_payer` field; refuse admissibility when `estimator_payer == requester` of the escrow consuming the estimate. Doesn't catch shell-company capture — consistent with the stack declining to solve identity anywhere else.

**(c) Griefing via demand accrual, at zero cost.** `demand_mbits` accrues on `REFUSED_CEILING` charges (only `REFUSED_ESTIMATOR` zeroes demand) and `incident` is a pure function of demand. So an admitted estimator can flood oversized, never-emitted estimates against a target account, tripping `incident := true` with zero leakage, zero payment — poisoning the human-readable court file. Fix: price submission itself (a small bond proportional to the declared estimate, charged regardless of accept/refuse). [LEAD NOTE: perimeter correction — charges must bind to a lease held by the charging node (I4), so only agents the key's owner ADMITTED can accrue demand; admission is the moat, the bond applies within it.]

**(d) Sybil readers fragmenting exposure accounts.** Confirmed mechanics of frontier #1; one concrete lever not yet in spec: a per-(source,reader) registration bond from the chamber issuer, refundable after dormancy — converts a free multiplier into a linear cost without claiming to solve identity.

**(e) Operator shading judgements toward whoever pays.** Nothing scores judgement *content*, only occurrence. An operator paid per-judgement has first-order incentive to manufacture matches while S1–S7 pass cleanly — they were never designed to price honesty, only information flow. This is why contingent-outcome design matters: judgement quality has to be priced after the fact, via realized outcomes, not policed at emission time.

## 2. The contingent-outcome problem ($5 if they talk 15 min)

Options weighed against "declared, attested, priced, never trusted-verified, convicted after merge": attested outcome oracle (really a third-party declared fact, closer to a `deposit` than an estimate — e.g. a call-platform's duration log from a role-separated issuer); both-parties-sign (cheap, friction-heavy, collusion/spite-gameable); commit-reveal with timeout default (fits existing reflexes, weak to silent collusion); **subjective-but-bonded arbitration** (best fit — a declared attestation, independence-classed, convicted after merge). Recommend bonded ruling + timeout default so no human adjudicator deadlocks the system + hard platform logs overriding bonded rulings when they exist (better evidence convicts).

**Gaming surface of the 15-minute metric:** trivially gameable by mutual arrangement (idle call, both AFK). Duration measures *presence*, not *engagement*; a paid operator optimizes for keeping calls open past threshold. Pure Goodhart — name it: price "sustained mutual connection," never "worthwhile match."

**Counterfactuality** has no operationalizable form — an unobservable potential outcome. The protocol should refuse to claim it prices counterfactual causation. The closest checkable proxy is revealed-preference-under-attribution: no prior contact record before this agent's card (itself a ledgered, exposure-metered fact) — "this agent originated the first contact leading to a qualifying conversation" is a fact about the ledger, not a claim about an alternate timeline.

## 3. Pricing leakage vs. attention — not the same kind of account

Structurally similar, economically opposite: leakage's ceiling exists purely to **bound harm** — paying people more for being exposed more inverts the ceiling into an adverse-selection engine. Attention is a resource whose expenditure has legitimate market-clearing use on the recipient's side. `pricing.ts`'s `SurfacingBid` states the instinct ("the owner is paid for attention spent, independent of the decision they then make") but is not wired into settlement — `intro_clearing`'s fee split has no leg paying the notified party at all. Minimal design: notification escrows lock against TWO charge_keys (operator leakage + a new attention-debit key), releases split per-payee with each cut keyed to its own charge — Bob's cut clears only against Bob's own attention charge.

## 4. What "Ethereum-ness" actually requires

Not global consensus — a chain that must include every private silo's read event is a mass-surveillance ledger, the opposite of the thesis. "Partition, not consensus" is the correct rejection. What the instinct actually reaches for: (1) **issuer neutrality** — competing issuers over one account namespace; refusals as declared, ledgered events so favoritism becomes computable; (2) **portability** — the export→re-attach-under-a-new-house workflow, implied by the data model, never exercised; (3) **exit rights** — require timeout-forced resolution as precondition (else exit is a ledger with money stuck in it); (4) **fee transparency** — ledgered fee_schedule events an escrow's split must reference. Ethereum's actual promise: nobody freezes funds unilaterally, nobody holds unauditable discretion, rules legible before transacting. Consensus was implementation strategy, not the goal.

## 5. Three changes, ranked

1. **Timeout-forced escrow resolution** (default_on_expiry + S8). [SHIPPED, in the permissionless-event form.]
2. **Bonded outcome attestation** (`outcome_attestation` events: attestor, subject_keys, claim, independence, bond_ucr, contest_window; contradictory overlapping claims → both bonds to a disputed escrow pending adjudication — convicted after merge, not guilty by accusation).
3. **Multi-payee escrow, keyed per-payee** (payees: [{payee, amount_ucr, charge_keys}], Σ = total preserved for conservation; S3's key-membership check per payee-slice).
