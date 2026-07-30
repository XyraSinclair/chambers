# charge-settlement — value bound to metered work

**Version:** `charge-settlement/2`
**Status:** normative for the settlement layer. Extends `KERNEL-SPEC.md`
(`charge-ledger/1`), which owns the substrate (canonical JSON, event
identity, jsonl wire, union merge) and the information side (fold, audit
codes I1–I8). Nothing here re-specifies either.

**Layering.** §0–§5 define `charge-settlement/1` and are FROZEN: the /1
golden corpus (`settlement_traces/`, 13 scenarios) and the Rust
counterparty port bind to them byte-for-byte. §6–§11 define the /2
extension — contingent-outcome settlement. Every /1 artifact is a clean
/2 artifact; a /2 verifier applied to a /1 artifact reproduces the /1
verdict exactly. A /1 verifier applied to a /2 artifact sees a
consistent but COARSER view (it ignores the /2 kinds; its own
conservation identity still holds over what it sees) — conforming /2
issuers guard on the /2 fold, which is the one that subtracts bonds.

## 0. Why a settlement layer, and the one law that matters

A charge ledger meters what **leaves** a private world (information, in
millibits). A work *economy* also needs what is **owed** (value). The two
must live in one artifact — otherwise "payment for cognitive work" is an
invoice pointing at a receipt that can be swapped out from under it.

The binding law, the reason this layer exists:

> **Value moves iff metered work moved.** A release of escrowed value
> references the exact charge events it pays for, by content-addressed id,
> and is convicted if those facts are absent, refused, off-key, or if the
> court file for the metered accounts is dirty.

Everything else is conservation bookkeeping, deliberately boring:

- **Unit.** Integer **microcredits** (`ucr`). No floating point anywhere.
  Pricing (fiat conversion, market quotes) is the value-side analog of
  estimation: it happens OUTSIDE the protocol and arrives as declared
  integers, exactly as `log2` lives in the attested estimator.
- **No minting.** Value enters only by `deposit` events declared by an
  **issuer** — the party whose liability the balance is (a clearing house,
  an escrow agent). Deposits are boundary facts, like declared entropy:
  the protocol does not verify the outside money, it conserves what was
  declared. Who the issuer is and why to trust them is L5 (priced, not
  proven), the same honest posture as lease issuers.
- **Partition, not consensus.** An issuer refuses to escrow past an
  account's available balance and refuses to disburse past an escrow's
  remainder — the same authority shape as the lease issuer. A lying issuer
  is *convicted after merge* by the S-codes, not prevented.
- **One-way dependency.** Settlement events reference charge events by id.
  The charge layer never references value. Information accounting stays
  meaningful in a ledger with no money in it; money is meaningless without
  the work receipts it points at.

## 1. Event kinds

All events live in the same ledger artifact as `charge-ledger/1` events and
obey its identity rules (§0–§1 there). Unknown kinds remain ignored by that
spec's fold/audit; symmetrically, this layer's fold/audit ignores every kind
not listed here (it *reads* charge events during S3/S4 checks but folds no
information quantities).

**Fact identity.** Every settlement event carries an issuer-local, strictly
monotone `seq` (per issuer, per kind) — the same lesson as `charge_seq`:
content addressing conflates same-bytes with same-fact; two deposits of the
same amount on the same day are two facts. Equivocation on
(`issuer`, kind, `seq`) is convicted (S5).

### 1.1 deposit — declared inflow

```jsonc
{ "kind": "deposit",
  "account": "requesterR",          // beneficial entity credited
  "amount_ucr": 500000,             // uint
  "issuer": "houseEscrow",          // whose liability this balance is
  "seq": 1,                         // issuer-local, per kind
  "tick": 0 }                       // declared clock label (issuer domain)
```

### 1.2 escrow — a conditional lock of payer value

```jsonc
{ "kind": "escrow",
  "payer": "requesterR",
  "payee": "guestAgentOperator",
  "amount_ucr": 120000,             // uint, locked in full at this event
  "charge_keys": [                  // the metered accounts the work runs on
    ["exp", "chamberA", "requesterR"],
    ["exp", "chamberB", "requesterR"] ],
  "required_clean": true,           // release forbidden if their court is dirty
  "expires_tick": 100,              // issuer clock domain
  "default_on_expiry": "refund_to_payer",  // or "release_to_payee"
  "issuer": "houseEscrow",
  "seq": 1,
  "tick": 1 }
```

The **escrow id** is the event id. `charge_keys` is a non-empty list of
`charge-ledger/1` keys (lists of strings); order is irrelevant to meaning
but part of the bytes (canonical form is whatever the issuer signed up to).

`default_on_expiry` names the escrow's fate if its issuer goes silent —
the anti-holdup clause, declared at lock time so both parties price it
before any work runs. See §1.5.

### 1.3 release — pay the payee, against work receipts

```jsonc
{ "kind": "release",
  "escrow_id": "sha256:…",
  "amount_ucr": 120000,             // uint; cumulative over the escrow ≤ its amount
  "charge_ids": ["sha256:…", "…"],  // non-empty: the work being paid for
  "issuer": "houseEscrow",
  "seq": 1,                          // issuer-local per kind (S5 identity)
  "tick": 7 }
```

### 1.4 refund — return the remainder to the payer

```jsonc
{ "kind": "refund",
  "escrow_id": "sha256:…",
  "amount_ucr": 30000,
  "issuer": "houseEscrow",
  "seq": 1,
  "tick": 101 }
```

### 1.5 default_resolution — the anti-holdup clause

The sharpest attack on /1 as first drafted was **silent holdup**: only the
issuer could emit releases and refunds, no code convicted inaction, so an
issuer could freeze a clean, fully-metered escrow forever — and selective
stalling (favoring payees who kick back) was indistinguishable from
prudence. The fix is NOT a time-dependent fold (the fold must remain a
pure function of the event set — CRDT law) but a **permissionless
resolution event**: after the escrow's declared expiry, ANY party — the
payee is the point — may submit the escrow's declared default. The audit
polices the claim; the issuer stops being a required actor.

```jsonc
{ "kind": "default_resolution",
  "escrow_id": "sha256:…",
  "amount_ucr": 20000,              // ≤ the escrow's remainder
  "charge_ids": ["sha256:…"],       // REQUIRED iff the default is release_to_payee
  "submitter": "agentOperator",     // whoever claims the default; not trusted, audited
  "seq": 1,                         // submitter-local per kind (S5 identity)
  "tick": 101 }                     // must be > the escrow's expires_tick (S8)
```

Semantics: the amount flows in the escrow's declared `default_on_expiry`
direction — to the payee (a release in all but name: the work-receipt and
clean-court conditions of §3 S3/S4 apply unchanged) or to the payer (a
refund in all but name: unconditional). A conforming issuer emits explicit
releases/refunds before expiry; `default_resolution` is the floor under
its silence. (/2 amends the direction rule for outcome-conditioned
escrows: §7.4.)

## 2. The settlement fold

Well-formedness for sums: amounts must be **uint** (as defined in
KERNEL-SPEC §0); non-uint amounts contribute nothing to any sum and are
convicted (S6). A release/refund whose `escrow_id` matches no escrow event
contributes to no escrow's disbursement and is convicted (S2 family, see
§3).

**Paired quantities move all-or-nothing** (as bond sums already do, §8);
this is what makes the conservation identity arithmetic on ANY soup:

* An escrow's `amount(e)` enters the fold — both the escrow's remainder
  AND its payer's `locked_out` — **only when `amount_ucr` is uint AND
  `payer` is a string**. An escrow with a uint amount and a non-string
  payer contributes nothing anywhere (it would otherwise mint `amount`
  into the conservation LHS with no offsetting debit) and is convicted
  S6.
* A disbursement counts toward `released(e)`/`refunded(e)` **only when
  the party it credits is a string** (`payee` for the release direction,
  `payer` for the refund direction); otherwise it contributes to no sum
  (it would otherwise burn the escrow's remainder with no offsetting
  account gain) and is convicted by the S3/S2 family.

Per **escrow** `e` (default resolutions count toward the direction the
escrow DECLARED — the event's submitter does not choose):

```
released(e) := Σ amount_ucr of releases with escrow_id = id(e)
             + Σ amount_ucr of default_resolutions with escrow_id = id(e)
                 where default_on_expiry(e) = "release_to_payee"
refunded(e) := Σ amount_ucr of refunds  with escrow_id = id(e)
             + Σ amount_ucr of default_resolutions with escrow_id = id(e)
                 where default_on_expiry(e) = "refund_to_payer"
remaining(e) := amount(e) - released(e) - refunded(e)     // may be negative only if lied
```

An escrow whose `default_on_expiry` is missing or not one of the two
literals is malformed (S6); default resolutions against it contribute to
no sum (and are convicted via S2's unknown/unresolvable arm).

Per **account** `a` (an account exists iff it appears as a deposit
`account`, an escrow `payer`, or an escrow `payee`):

```
deposited(a)   := Σ deposits with account = a
locked_out(a)  := Σ amount(e) over escrows with payer = a
released_in(a) := Σ released(e) over escrows with payee = a
refunded_in(a) := Σ refunded(e) over escrows with payer = a
available(a)   := deposited(a) + released_in(a) + refunded_in(a) - locked_out(a)
```

`available` is computed in signed arithmetic; a negative value is exactly
the S1 conviction. **Conservation identity** (holds by construction of the
fold, for any event set whatsoever):

```
Σ_a available(a) + Σ_e remaining(e) = Σ deposits
```

Every declared microcredit is, at fold time, in exactly one place:
available to some account, or parked in some escrow's remainder. The
identity is not an honesty assumption — it is arithmetic. Honesty is what
keeps every term non-negative, and the S-codes convict every violation of
that.

### 2.1 Canonical fold serialization (for conformance)

Canonical JSON of:

```jsonc
{ "accounts": [ /* sorted by account string, byte-wise */
    { "account": "…", "deposited_ucr": n, "locked_out_ucr": n,
      "released_in_ucr": n, "refunded_in_ucr": n, "available_ucr": n } ],
  "escrows": [ /* sorted by escrow event id */
    { "escrow_id": "…", "amount_ucr": n, "released_ucr": n,
      "refunded_ucr": n, "remaining_ucr": n } ] }
```

(`available_ucr` and `remaining_ucr` may be negative integers — the
artifact records the crime rather than clamping it away.)

## 3. The settlement audit — S-codes

Same verdict discipline as I-codes: sorted, deduplicated
`"<code> <subject>"` strings; total over adversarial content; the combined
verdict of an artifact is the I-codes and S-codes of the same event set.

| code | subject | emitted when |
| --- | --- | --- |
| S1 | account string | `available(a) < 0` — the issuer escrowed value the account never had |
| S2 | escrow event id, or the release/refund event id when the escrow is unknown | `released(e) + refunded(e) > amount(e)`; or a release/refund references an escrow id absent from the ledger |
| S3 | release event id | the release's `charge_ids` is empty or missing; or a referenced charge id is absent from the ledger; or a referenced event is not a charge; or the charge's `accepted` is not JSON `true`; or the charge's `key` ∉ the escrow's `charge_keys` (checked only when the escrow resolves) |
| S4 | release event id | the escrow resolves, has `required_clean` = `true`, and the ledger's `charge-ledger/1` audit contains a finding whose subject **touches** the escrow's `charge_keys` (see below) |
| S5 | canonical JSON of `[actor, kind, seq]` | two settlement events with different ids claim the same (actor, kind, `seq`), `seq` uint — where actor is the event's authoring field: `issuer` for deposit/escrow/release/refund, `submitter` for default_resolution |
| S6 | event id | malformed settlement event: non-uint `amount_ucr`; missing/invalid `seq` (< 1 or non-uint); escrow with empty or missing `charge_keys`, non-list keys, non-string `payer` or `payee`, or `default_on_expiry` not one of the two literals; release/refund/default_resolution with non-string `escrow_id` |
| S7 | release event id | the escrow resolves, both ticks are ints (bools excluded), and `tick > expires_tick` of the escrow — value disbursed against an expired lock (releases only; `default_resolution` is the sanctioned post-expiry path and S8 owns its timing) |
| S8 | default_resolution event id | the escrow resolves and the resolution is PREMATURE (`tick ≤ expires_tick`, both ints); or the escrow's `default_on_expiry` is `release_to_payee` and the resolution fails the release conditions — S3's work-receipt checks and, when `required_clean`, S4's touching-court check — applied to the resolution event |

**"Touches" for S4.** An I-finding touches `charge_keys` K iff:
its subject is the canonical JSON of a key in K (I1/I2/I7); or its subject
is the id of a lease event whose `key` ∈ K (I3/I5); or its subject is the
id of a charge event whose `key` ∈ K (I4/I6); or it is an I8 finding whose
`[node, lease_id, seq]` names a lease whose `key` ∈ K. Findings that touch
nothing in K do not block the release — a dirty account elsewhere in a
shared ledger is not this escrow's crime. A finding whose code this
specification does not define (a future I-code) **touches every key set**:
value release fails closed against verdicts it does not understand.

**Refunds and work.** A refund needs no work receipt and no clean court —
returning value to its payer is always safe. Expiry does not gate refunds
(S7 is releases only): the whole point of `expires_tick` is that the payer
can recover the remainder after it.

**S11/S12 and the split extension (2026-07-08).** ATTRIBUTION-SPEC Part II
is normative for two further arms on this same surface: an escrow may
carry a `split` block binding its pot to the recomputed shapley_dpi/1
rows of an emission — S11 convicts a disbursement off the rows (missing
beneficiary, phantom row, wrong amount, unauditable game), S12 convicts
cumulative row overdraw; `default_on_expiry` gains the split-only
`release_by_report` literal (per-row permissionless default), and the
dirty-court stream additionally carries charge-attribution/1's V-codes
with source-precise touch. Escrows without a `split` block are untouched
by all of it.

## 4. The honest issuer (informative, mirrors LeaseIssuer)

A conforming honest issuer maintains its own books and **refuses**:

- an escrow when `amount_ucr > available(payer)` at its current view;
- a release/refund when `amount_ucr > remaining(escrow)`;
- a release after the escrow's expiry, or with an empty/cross-key receipt,
  or (when `required_clean`) while the touching court is dirty at its view.

Under those refusals every fold term stays non-negative and no S-code ever
fires — that is the settlement analog of the global cap theorem, proven in
`../lean/ChargeKernel/Settlement.lean` (conservation is arithmetic; the
theorem with content is that honest-issuer traces keep every account and
escrow non-negative under any interleaving).

**Exit rights.** Because resolution after expiry is permissionless
(§1.5), no issuer can hold value hostage past an escrow's declared
horizon: the worst an unresponsive or hostile issuer can do is delay a
party until `expires_tick`. Combined with the portable jsonl artifact,
"take your ledger and leave" is real: every balance is either available,
or in an escrow whose terminal fate and deadline were declared before any
work ran.

## 5. What this deliberately does NOT claim

- **Money-ness.** `ucr` are ledger liabilities of a named issuer, not
  bearer instruments. Multi-issuer interop, netting between issuers, and
  redemption are out of scope of /1.
- **Pricing.** How an escrow amount was quoted (per-millibit rates, flat
  fees, auctions) is above the protocol; the ledger records the agreed
  integers.
- **Signatures / custody.** Events remain unsigned claims cross-checked
  for consistency; authenticating the issuer is the same L5 frontier as
  authenticating nodes, priced not proven.
- **Timeliness.** `tick` is the declared issuer clock, as everywhere else
  in the kernel; S7 convicts declared-late disbursement, not wall-clock
  lateness.

---

# Part II — charge-settlement/2: contingent outcomes

## 6. Why /2, and the extended law

The /1 release condition — work receipt + clean court — prices *flow*:
the payee is paid because metered work moved. It cannot price *realized
value*: "$5 if they actually talk 15 minutes", a placement fee on hire.
Those are facts about the world, and the kernel never observes the
physical world — it conserves what was declared and convicts declared
contradictions. /2 therefore adds exactly one thing: a **declared,
bonded, contestable outcome fact**, and gates release on a quorum of
them. The binding law extends:

> **Value moves iff metered work moved AND, when the escrow declared an
> outcome condition, the declared outcome provably occurred.** A release
> against an outcome-conditioned escrow references BOTH its work
> receipts (`charge_ids`) and its outcome proof (`attestation_ids`), by
> content-addressed id, and is convicted if either is absent, refused,
> off-key, under-classed, under-bonded, unhardened, or contested.

Three refusals, adopted as doctrine and normative here:

- **Counterfactuals are refused.** "They would not have talked
  otherwise" has no operationalizable form — an unobservable potential
  outcome. No /2 lane carries counterfactual semantics; there is no way
  to express one. The checkable proxy is a *ledger* fact — "this agent
  originated the first contact leading to a qualifying conversation" —
  and when a `metric` names such a fact, any stranger can recompute it
  from the artifact and contest a lying attestation.
- **Outcomes size payments; they never gate disclosure.** Outcome
  conditions exist ONLY in the settlement layer. No charge-layer
  admissibility may reference outcome events; emission is charged at
  emission time, unconditionally. (Structural: the dependency remains
  one-way — settlement reads charge facts, never the reverse.)
- **Goodhart is priced openly.** A duration metric measures *presence*,
  not engagement; a paid operator optimizes for keeping calls open.
  `metric` labels MUST name the proxy for what it is ("sustained mutual
  connection"), never the aspiration ("worthwhile match"). Conditions
  with no expressible evidence lane (clinical outcomes, subjective
  satisfaction) get NO outcome block: they settle flat-fee, /1-style.

## 7. Event kinds (/2)

### 7.1 escrow — the optional `outcome` block

An escrow MAY carry an `outcome` field, declared at lock time so both
parties price it before any work runs (it is part of the escrow's bytes,
hence its id):

```jsonc
{ "kind": "escrow", /* …every /1 field, unchanged… */
  "default_on_expiry": "refund_to_payer",   // FORCED for outcome escrows (S6)
  "outcome": {
    "metric": "first_contact_qualifying_call_15min",  // free label; the proxy, named
    "lane": "attested",              // minimum evidence lane: "attested" | "platform_log"
    "quorum": 1,                     // uint >= 1: distinct admissible "occurred" attestations
    "min_independence": "role_separated",  // admissibility floor, §7.2
    "min_bond_ucr": 5000,            // uint: bond floor per counted attestation
    "contest_ticks": 10 } }          // window an attestation must survive before release
```

An outcome-conditioned escrow MUST declare
`default_on_expiry = "refund_to_payer"` — the payer keeps the money
unless the outcome provably occurred. The alternative
(`release_to_payee`) would make the condition vacuous at expiry;
declaring it alongside an outcome block is malformed (S6). The payee is
not thereby hostage to a silent issuer: §7.4.

**Evidence lanes**, totally ordered: `attested` < `platform_log`. An
`attested` fact is a bonded subjective ruling (an arbiter says the call
happened). A `platform_log` fact is a declared hard record (the call
platform's duration log, from a role-separated issuer). Higher lanes
satisfy lower-lane conditions; better evidence beats worse (§9).

**Independence classes**, totally ordered:
`party` < `operator` < `role_separated` < `adversarial_review`.
The vocabulary mirrors the estimator's (§KERNEL `charge-ledger/1`), with
`party` added below `operator`: the payer and payee themselves. The
**effective class** of an attestation is the DECLARED class, demoted to
`party` when its `attestor` string equals the escrow's `payer` or
`payee` — the one independence fact the artifact itself can check.
A declared class outside the vocabulary (including `self_interested`)
is inadmissible, fail closed. Both-parties-sign settlement is therefore
a configuration, not a mechanism: `min_independence: "party"`,
`quorum: 2`.

### 7.2 outcome_attestation — a bonded, contestable outcome fact

```jsonc
{ "kind": "outcome_attestation",
  "escrow_id": "sha256:…",          // the outcome escrow this attests
  "claim": "occurred",              // or "not_occurred" (a contest is an attestation)
  "lane": "attested",               // the evidence lane CLAIMED for this fact
  "independence": "role_separated", // declared class; truth of the declaration is L5
  "evidence": "callPlatform:log:sha256:…",  // free string, part of the bytes
  "bond_ucr": 5000,                 // uint: locked from the attestor's account at fold
  "attestor": "arbiterA",
  "seq": 1,                         // attestor-local, per kind (S5 identity)
  "tick": 42 }
```

The attestation is the estimator posture applied to outcomes: a declared
fact from a named party under a declared independence class, never
trusted-verified, convicted after merge. The bond is what makes it
priceable: `bond_ucr` is locked from the attestor's account by the fold
itself (§8) — an attestor who bonds value they do not have drives their
own account negative and is convicted (S1), and their attestations stop
counting toward any quorum (§9 S9). Attesting `not_occurred` is the
sanctioned contest move and carries the same bond discipline.

### 7.3 bond_resolution — return or slash

```jsonc
{ "kind": "bond_resolution",
  "attestation_id": "sha256:…",
  "amount_ucr": 5000,               // ≤ the bond's remainder
  "direction": "return_to_attestor",  // or "slash"
  "submitter": "arbiterA",          // permissionless; not trusted, audited
  "seq": 1,                         // submitter-local, per kind (S5 identity)
  "tick": 60 }
```

Permissionless, like `default_resolution`. `return_to_attestor` sends
the amount back to the attestor; it is honest only after the contest
window closed with no strict override (§9 S10). `slash` sends the amount
to the party the false claim would have harmed — the escrow's **payer**
for a false `occurred`, its **payee** for a false `not_occurred` (the
beneficiary is DERIVED from declared data; the submitter chooses
nothing) — and is honest only under a strict override: a contradicting
attestation in a STRICTLY higher lane. Equal-lane contradiction blocks
payment (§9) but slashes nobody: **contested is not convicted** — an
accusation freezes the question; only better evidence takes the bond.

### 7.4 default_resolution against an outcome escrow

The /1 rule — the direction comes from the escrow's declared default —
is amended for outcome escrows, whose declared terminal rule is
conditional by construction (§7.1): *quorum-proven release, else
refund*. A `default_resolution` against an outcome escrow flows:

- **release-direction** iff its payload carries a non-empty
  `attestation_ids` list — the submitter (the payee against a silent
  issuer is the point) presents the outcome proof and the work receipts
  (`charge_ids`), and S8 polices both exactly as it polices a release
  (§9); or
- **refund-direction** otherwise — the declared default, unconditional.

Both remain gated on expiry (S8 premature arm, unchanged). The
anti-holdup floor thus holds in BOTH directions: a payer cannot be
stalled out of the remainder, and a quorum-holding payee cannot be
stalled out of payment.

### 7.5 release — the outcome proof

A release against an outcome-conditioned escrow MUST carry
`attestation_ids`: a non-empty list of `outcome_attestation` event ids —
the outcome proof, referenced the same way `charge_ids` references the
work receipt. Against a /1 escrow the field is meaningless and ignored.

## 8. The /2 fold

Everything in §2 stands. Two additions, same discipline (total over
adversarial content; non-uint amounts contribute nothing and are
convicted by S6).

Per **attestation** `t` (a bond state exists for every
`outcome_attestation` event; `amount(t) := bond_ucr` when `bond_ucr` is
uint AND `attestor` is a string — a lock with no deriveable source
account would mint a remainder from nothing — else 0):

```
returned(t) := Σ amount_ucr of bond_resolutions with attestation_id = id(t)
                 and direction = "return_to_attestor"
                 WHERE t's attestor is a string (the credit's destination)
slashed(t)  := Σ amount_ucr of bond_resolutions with attestation_id = id(t)
                 and direction = "slash"
                 WHERE the slash beneficiary is derivable (below)
remaining(t) := amount(t) - returned(t) - slashed(t)   // negative only if lied
```

Every flow is all-or-nothing: a resolution contributes to the bond's
disbursement iff it simultaneously contributes to a destination
account, so the identity below stays arithmetic on any event soup.

A slash's beneficiary is derivable iff the attestation's `escrow_id`
resolves to an escrow event in this ledger, its `claim` is one of the
two literals, and the derived party field (`payer` for `occurred`,
`payee` for `not_occurred`) is a string. An underivable slash
contributes to NO sum — neither the bond's nor any account's (all or
nothing; S10 convicts it). A resolution whose `attestation_id` matches
no attestation likewise contributes nothing (S10). A resolution with a
`direction` outside the two literals contributes nothing (S6).

Per **account** `a`, three new buckets:

```
bonded_out(a)       := Σ amount(t) over attestations with attestor = a
bond_returned_in(a) := Σ returned(t) over attestations with attestor = a
slashed_in(a)       := Σ slashed(t) over attestations whose derived beneficiary = a
available(a)        := deposited(a) + released_in(a) + refunded_in(a)
                       + bond_returned_in(a) + slashed_in(a)
                       - locked_out(a) - bonded_out(a)
```

(An account also exists iff it appears as an `attestor` or as a derived
slash beneficiary.) **Conservation identity (/2)**, arithmetic as ever:

```
Σ_a available(a) + Σ_e remaining(e) + Σ_t remaining(t) = Σ deposits
```

### 8.1 Canonical fold serialization (/2)

The /1 serialization (§2.1) is unchanged and remains the /1 conformance
surface. The /2 surface extends each account object with
`bonded_out_ucr`, `bond_returned_in_ucr`, `slashed_in_ucr` (in canonical
key order) and appends a third top-level array:

```jsonc
{ "accounts": [ /* §2.1 fields + the three /2 buckets */ ],
  "escrows":  [ /* §2.1, unchanged */ ],
  "bonds": [ /* sorted by attestation event id */
    { "attestation_id": "…", "amount_ucr": n, "returned_ucr": n,
      "slashed_ucr": n, "remaining_ucr": n } ] }
```

On a /1 artifact the /2 buckets are all zero and `bonds` is empty; the
/1 serialization of any artifact is recoverable from the /2 one by
dropping them.

## 9. The /2 audit — S9, S10, and the amended arms

Verdict discipline unchanged: sorted, deduplicated `"<code> <subject>"`,
total over adversarial content, combined with I-codes and S1–S8.

**Amended /1 arms** (all vacuous on /1 artifacts):

- **S5** — fact identity extends to the new kinds. Authoring fields:
  `attestor` for `outcome_attestation`, `submitter` for
  `bond_resolution`.
- **S6** — well-formedness extends: an `outcome_attestation` with
  non-string `escrow_id`/`attestor`/`independence`/`evidence`, `claim`
  or `lane` outside their literals, non-uint `bond_ucr`, or bad `seq`;
  a `bond_resolution` with non-string `attestation_id`/`submitter`,
  `direction` outside its literals, non-uint `amount_ucr`, or bad
  `seq`; an escrow whose `outcome` field is present but not an object
  with `metric` (string), `lane` (literal), `quorum` (uint ≥ 1),
  `min_independence` (in the class vocabulary), `min_bond_ucr` (uint),
  `contest_ticks` (uint) — or whose `default_on_expiry` is not
  `refund_to_payer` while `outcome` is present. (For
  `outcome_attestation` the §3 S6 amount check reads `bond_ucr`; the
  kind has no `amount_ucr`.)
- **S8** — a release-direction default resolution (§7.4) against an
  outcome escrow must additionally satisfy the S9 quorum conditions,
  evaluated at the resolution's own `tick`; failures are reported under
  S8, exactly as S8 already carries S3/S4's checks.

**S9 — outcome proof** (subject: the release event id). Emitted, for a
release whose escrow resolves and carries an `outcome` field, when ANY
of the following holds. Fail closed: if the `outcome` field is present
but malformed (S6), EVERY release against that escrow is convicted —
value must not move under a condition the audit cannot read.

1. `attestation_ids` is missing, not a list, or empty — no outcome proof.
2. A referenced id is not a string, is absent from the ledger, is not an
   `outcome_attestation`, is itself malformed (S6), names a different
   escrow, or claims `not_occurred`.
3. A referenced attestation is **under-classed** (its effective
   independence class, §7.1, is below `min_independence`), **off-lane**
   (its `lane` is below the condition's `lane`), or **under-bonded**
   (`bond_ucr` < `min_bond_ucr`).
4. A referenced attestation is **unbacked**: its attestor's /2
   `available` is negative — the bond is not real value at stake.
5. A referenced attestation is **unhardened**: both ticks are ints
   (bools excluded) and the release's `tick` ≤ the attestation's
   `tick` + `contest_ticks` — value moved inside the contest window.
6. A referenced attestation is **contested**: some well-formed
   `outcome_attestation` on the same escrow claims `not_occurred`, in a
   lane ≥ the referenced attestation's lane, and itself meets the
   condition's independence, bond, and backing floors. (Equal lane
   blocks; it does not slash — §7.3.)
7. The referenced attestations that survive 2–6 do not include
   `quorum`-many with pairwise-distinct `attestor` strings.

**S10 — bond resolution** (subject: the resolution event id, except the
over-resolution arm, whose subject is the attestation id — the S2
pattern). Emitted when:

1. `attestation_id` resolves to no `outcome_attestation` in the ledger
   (orphan — contributed nothing to any sum).
2. `returned(t) + slashed(t) > amount(t)` for the attestation —
   over-resolution.
3. Direction `return_to_attestor`: the contest window is still open
   (both ticks ints and resolution `tick` ≤ attestation `tick` +
   `contest_ticks`, the window taken from the attestation's escrow's
   outcome block — no window is derivable when that block is absent or
   malformed, and then the return is NOT premature); or a strict
   override of the attestation exists.
4. Direction `slash`: NO strict override exists. A **strict override**
   of attestation t is a well-formed `outcome_attestation` on the same
   escrow with the opposite `claim`, a lane STRICTLY above t's, meeting
   the escrow condition's independence, bond, and backing floors — when
   no outcome condition is derivable, nothing overrides and every slash
   convicts.
   **Named referent (G19, additive).** A slash MAY carry
   `override_attestation_id`. When the field is PRESENT, the naming
   binds: the slash convicts UNLESS the named value is a string
   resolving to an `outcome_attestation` in the ledger that IS a strict
   override of t (the same per-candidate predicate as the scan — the two
   modes share one definition and cannot drift). A qualifying override
   that exists but was not the one named does NOT save the slash: the
   court judges the evidence the slasher cited. A junk name (non-string,
   unknown id) resolves to nothing and convicts — totality, never a
   crash; S10 owns this arm, S6 is unchanged. When the field is ABSENT
   the scan rule above applies verbatim, so every historical event keeps
   its exact verdict and bytes. Naming turns the §11 referent-arrival
   precedent literal: the conviction lifts exactly when the NAMED fact
   becomes present and backed.
5. A slash whose beneficiary is underivable (§8) — it moved nothing and
   claims otherwise.

**Clock domains, named.** Hardening (S9.5) and window (S10.3) checks
compare the resolution/release `tick` against the attestation's `tick`
plus the escrow's `contest_ticks` — three declared clocks. As with S7,
this is declared-order discipline: the audit convicts declared-early
action, not wall-clock lies; clock honesty is L5, like every tick in
the kernel.

## 10. Honest actors (/2, informative)

The **honest issuer** additionally refuses a release against an outcome
escrow unless the presented `attestation_ids` satisfy S9's conditions
1–7 at its current view and tick.

Two **permissionless** entry points mirror `default_resolution`:

- `attest_outcome` — any party may attest. The honest front refuses:
  an escrow id absent from its ledger, or with no (or a malformed)
  outcome block; a lane below the condition's; an effective class below
  the floor; a bond below the floor; a bond the attestor's /2
  `available` cannot back.
- `resolve_bond` — any party may resolve. The honest front refuses:
  over-resolution; a premature return; a return under a strict
  override; a slash without one.

A dishonest actor bypasses every one of these by forging the event —
and is convicted after merge (S9/S10/S1/S5/S6), which is the entire
security model, unchanged.

## 11. What /2 deliberately does NOT claim

Everything in §5, plus:

- **Attestor identity / Sybil quorums.** `quorum` counts distinct
  attestor STRINGS. Shell attestors are the same L5 frontier as shell
  readers and shell estimators; the artifact prices the bond each shell
  must post and names the classes each declared — it cannot know two
  strings are one hand.
- **Independence truth.** `independence` is declared; the artifact
  checks only the party demotion (§7.1). Economic capture of attestors
  is G8's territory, priced not proven.
- **Equal-lane platform disputes.** Two contradicting `platform_log`
  attestations block the quorum forever (nothing outranks them); the
  escrow then settles by its declared expiry default. That is the
  honest floor, not a deadlock: the money's terminal fate was declared
  before any work ran. Adjudication above the top lane is out of /2.
- **Outcome truth.** The kernel never observes the world. It conserves
  declared value, prices declared facts by bonds, and convicts declared
  contradictions by better declared evidence. Whether they really
  talked for 15 minutes is exactly as far outside the protocol as
  whether the outside money behind a `deposit` exists.
- **Payment finality.** A release's verdict may ESCALATE after value
  moves: a qualifying contest or override that merges later convicts the
  release retroactively (verdicts only escalate — the same law as
  everywhere in the kernel). Value is never unwound; the artifact
  records that the payment leaned on since-contradicted evidence, and
  the bond slash — not the release — is the remedy path. Issuers who
  want stronger practical finality wait longer than `contest_ticks`;
  the protocol sells evidence, not irreversibility.

- **The slash's verdict de-escalates ONLY via a documented precedent
  (monotonicity, made explicit).** An S10 `slash-without-override`
  conviction lifts when a qualifying strict override later merges — an
  event ADDED to the court REMOVES a finding, which looks like a
  monotonicity violation and is not. It is the *same* face of the law as
  S3's missing work receipt clearing when the receipt arrives: the slash
  is convicted for **lacking its justifying evidence**, and the lack is
  cured when that evidence becomes present. Every de-escalation of a
  slash traces to one of the two sanctioned precedents — (a) a
  referenced/required fact arriving (here the override attestation), or
  the deposit precedent (a deposit restoring the override attestor's
  backing so it meets the floor). It does not oscillate in the harmful
  direction: merge is grow-only and `platform_log` is the top lane, so a
  backed top-lane override, once present, cannot be outranked or removed;
  the only re-convictions are escalations (the override's attestor
  over-commits and un-backs it — I-code-style aggregate escalation),
  each itself curable only by the deposit precedent. The kernel's
  "post-your-way-into-a-cleaner-court" prohibition is intact: you cannot
  escape a slash you deserve, only supply the evidence that a slash you
  *did* deserve was in fact justified. **Named tightening (G19, SHIPPED
  2026-07-07):** a slash MAY reference its `override_attestation_id`
  explicitly (§9 S10.4, named referent), turning "an override exists
  (by scan)" into "the named override referent is present" — for a
  naming slash the two precedents collapse into one and the scan is
  gone. Additive optional field: events that omit it keep their exact
  historical bytes and the scan rule, so the frozen /2 corpus and the
  Rust port were unaffected at the transition.

### 11.1 The oracle attack table

The /2 attestation game is a bonded Schelling oracle; its known
predators, with this spec's honest verdict on each. Exercised
mechanically in `test_settlement2_attacks.py` (FRAMEWORKS F9).

| attack | verdict | mechanism |
| --- | --- | --- |
| **p+ε bribery** of an attested-lane quorum | PRICED | The bribe itself is invisible (L5). One hard `platform_log` overturns a unanimous bribed quorum: the leaning release convicts (S9), every bribed bond slashes to the harmed payer (S10). Indemnity = Σ slashed bonds, so **bribery-sensitive escrows size `min_bond_ucr ≥ amount_ucr / quorum`** — below that line the artifact records a named recovery hole. |
| **Lazy / copycat attestation** | PRICED | A copy is indistinguishable from an observation (L5) but carries the full bond and the full override exposure: when better evidence lands, original and copy slash alike. Laziness is co-signing. |
| **Party griefing** (payer contests to force the expiry refund) | PREVENTED under non-party floors | Any party's attestation is demoted to `party` regardless of declared class; under a `role_separated`+ floor it neither counts nor contests. Party floors (`both-parties-sign`) declare the mutual veto deliberately. |
| **Ghost contest** (unbacked `not_occurred`) | PREVENTED | A contest must meet the independence, bond, and BACKING floors; an unbacked contest blocks nothing and convicts its own attestor (S1). |
| **Funded griefing** (qualified equal-lane contest) | PRICED | The contest blocks payment (contested ≠ convicted, no slash for accusation) until better evidence lands — then the griefer's bond slashes to the party their false claim would have harmed, and the quorum stands again. Worst case: the declared expiry default. |
| **Capital over-commitment** (one balance behind many bonds) | PREVENTED | Backing is an aggregate fold fact: over-committing drives the attestor S1-negative and un-backs EVERY outstanding attestation of theirs at once — escalation-only, no per-bond accounting to race. |
| **Top-lane capture** (a lying platform log) | party-owned: PREVENTED · third-party: RECORDED | A payer/payee-submitted "platform log" is demoted like any party attestation. A captured third-party platform can freeze payment to the expiry default and slash honest attested bonds — nothing outranks the top lane; adjudication above it is refused (§11). The capture is a permanent, attributable artifact fact: choose platform attestors as you choose lease issuers (L5). |
| **Retroactive contest** of a paid release | RECORDED, by design | See payment finality above. |
