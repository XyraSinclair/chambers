# charge-ledger/1 — the distributive layer, counterparty-compilable

**Version:** `charge-ledger/1`
**Status:** normative. This document, not any one program, is the authority
for the ledger fold and audit of `charge-kernel/2`. It extends
`../conformance/SPEC.md` (`egress-accountant/1`), which remains the authority
for the per-account decision function; nothing here re-specifies it.

The claim this document makes checkable:

> Given the same ledger artifact (a jsonl file of events), two independently
> written implementations compute the **same global accounts** (the fold) and
> the **same audit verdict** (the finding codes), byte-for-byte.

An implementer MUST be able to produce a conforming fold+audit from this file
alone, with no access to any reference source. The decision function that
*produced* the charges is out of scope here (it is `egress-accountant/1`);
this document specifies what a **stranger** does with the merged facts:
recompute the accounts, and convict liars.

Everything below is exact integer arithmetic and string comparison. There is
no floating point anywhere in a conforming implementation.

---

## 0. Canonical JSON and event identity

**Canonical JSON** of a JSON object is the serialization with:

- object keys sorted by Unicode code point (byte-wise ascending on UTF-8),
- separators `,` and `:` with no whitespace,
- all non-ASCII characters escaped (`\uXXXX`, lowercase hex, UTF-16 code
  units for astral characters) — the output is pure ASCII,
- integers serialized in base 10 with no leading zeros, `-` only for
  negatives; no floats occur in any legal event,
- strings with the minimal JSON escapes (`\"`, `\\`, `\b`, `\f`, `\n`, `\r`,
  `\t`, and `\uXXXX` for other control characters and all non-ASCII),
- booleans as `true`/`false`.

(This matches Python `json.dumps(payload, sort_keys=True,
separators=(",", ":"), ensure_ascii=True)`.)

**Event id** := the string `"sha256:"` + lowercase hex SHA-256 of the
canonical JSON, encoded as ASCII bytes.

Ids are **derived, never trusted**: a parser recomputes every id from
content. Two events with the same id MUST be byte-identical in canonical
form; encountering the same id with differing bytes is a hard error
(content addressing violated) — the only condition under which parsing or
merging fails. Every other malformation is a *finding*, not an error: an
auditor that can be crashed by an adversarial event is itself a
vulnerability (see §4, I-codes).

**Integer discipline.** Where this document says **uint**, it means: the
JSON value is a number that is an integer `>= 0`. JSON `true`/`false` are
booleans, not numbers, and never satisfy uint. (Implementations in languages
where booleans are integers must exclude them explicitly.) Where it says
**int**, it means a JSON integer of either sign. Implementations MUST use at
least signed 64-bit integers; legal corpora keep every sum and product below
2^62.

---

## 1. The ledger artifact (jsonl wire format)

A ledger is a **set of events**. Its canonical serialization is:

- one canonical-JSON event payload per line, `\n`-separated,
- lines sorted by event id, ascending byte-wise (note: ids are recomputed
  from the line's content, not stored),
- a trailing `\n` after the last line iff the ledger is non-empty,
- blank lines ignored on input.

Equal ledgers produce byte-equal artifacts. Merge of two ledgers is set
union by event id (with the byte-equality check of §0). Union is idempotent,
commutative, associative; fold and audit are functions of the set, so any
gossip order converges.

## 2. Event kinds

Every event payload has a `"kind"` field: `"register"`, `"lease"`, or
`"charge"`. Unknown kinds are ignored by fold and audit (forward
compatibility), but still occupy their id in the set.

### 2.1 register

```jsonc
{ "kind": "register",
  "key": ["exp", "chamberA", "agentZ"],   // list of strings
  "subject_entropy_mbits": 100000,        // int > 0 for well-formedness
  "ceiling_mbits": 60000,                 // uint
  "issuer": "chamberA" }                  // string
```

### 2.2 lease

```jsonc
{ "kind": "lease",
  "key": ["exp", "chamberA", "agentZ"],
  "lease_seq": 1,                          // issuer-local sequence
  "node": "n1",                            // the ONLY node that may charge it
  "amount_mbits": 30000,                   // uint
  "issuer": "chamberA",
  "expires_tick": 100 }                    // int, issuer clock domain
```

### 2.3 charge

```jsonc
{ "kind": "charge",
  "key": ["exp", "chamberA", "agentZ"],
  "node": "n1",
  "lease_id": "sha256:…",                  // id of the lease spent against
  "charge_seq": 1,                         // uint >= 1; node-local per lease
  "tick": 3,                               // int, issuer clock domain
  "channel": "read",
  "estimate_total_mbits": 10000,           // uint
  "estimator_id": "e", "estimator_independence": "adversarial_review",
  "estimator_worst_case": true,
  "accepted": true,
  "reason_class": "EMITTED",               // see §4 I6 for the legal set
  "reason_detail": "emitted_debited",
  "demand_mbits": 10000,                   // uint; see I6 consistency
  "debit_mbits": 10000 }                   // uint; see I6 consistency
```

`REASONS` := { `EMITTED`, `REFUSED_ESTIMATOR`, `REFUSED_BLOCKED`,
`REFUSED_CEILING`, `REFUSED_COUPLED` }.

---

## 3. The fold — global accounts

### 3.1 Registration resolution

Group all `register` events by `key` (compare keys as string lists,
element-wise). Per key:

- **well-formed** register := `subject_entropy_mbits` is an int `> 0`
  (not a boolean) AND `ceiling_mbits` is uint. Well-formedness is decided by
  these two fields ONLY: a register with a missing or non-string `issuer` is
  still well-formed; its issuer simply contributes nothing to
  `issuers(key)`. (Clarified after the first independent implementation
  flagged the ambiguity.)
- If no well-formed register exists for the key: the key gets **no
  account** (its leases and charges still feed audit, §4).
- Otherwise the resolved account parameters are the **field-wise minimum
  over the well-formed registers**:
  `entropy := min(subject_entropy_mbits)`, `ceiling := min(ceiling_mbits)`.
- `issuers(key)` := the set of `issuer` strings of the well-formed registers.
- `conflicted(key)` := true iff (the well-formed registers do not all have
  identical canonical bytes) OR (at least one malformed register exists for
  the key).

Minimum-resolution is deliberate: under set union, adding registrations can
only *lower* entropy and ceiling, which only *escalates* leakage class,
incident, and ceiling findings. Merge escalates; it never retracts.

### 3.2 Account sums

Per key with an account:

- `cumulative_mbits` := Σ `debit_mbits` over charges with that key where
  `debit_mbits` is uint (non-uint contributions are ignored here and
  convicted in audit).
- `demanded_mbits` := Σ `demand_mbits` over charges with that key where
  `demand_mbits` is uint.
- `granted_lease_mbits` := Σ `amount_mbits` over leases with that key where
  `amount_mbits` is uint.
- `leakage_class` := exactly `egress-accountant/1` §1.5 applied to
  (`cumulative_mbits`, `entropy`).
- `incident` := `demanded_mbits * 1000 >= 800 * entropy`.

> **Interpretation delegated (charge-views/1, 2026-07-08).** The two
> fields above remain normative FOR BYTES — every frozen corpus and
> every port binds to them unchanged. Their MEANING is delegated to
> `VIEWS-SPEC.md`: they are DEFINED as the view under the legacy-default
> policy (provably, bit-for-bit, over every frozen corpus — the §V.5
> parity law). Class vocabularies and incident thresholds are policy;
> policy versions; this fold does not. Any future fold version keeps
> only the integer sums.

### 3.3 Canonical fold serialization (for conformance)

The fold of a ledger serializes as the canonical JSON of:

```jsonc
{ "accounts": [ /* sorted by canonical JSON of "key", byte-wise ascending */
  { "key": [...],
    "subject_entropy_mbits": n, "ceiling_mbits": n,
    "cumulative_mbits": n, "demanded_mbits": n, "granted_lease_mbits": n,
    "leakage_class": "…", "incident": b, "conflicted": b } ] }
```

## 4. The audit — codes and subjects

The audit verdict is a **sorted, deduplicated list of strings**, each
`"<code> <subject>"` (single space). Sorting is byte-wise ascending.
Subjects are canonical identifiers:

| code | subject | emitted when |
| --- | --- | --- |
| I1 | canonical JSON of the key | `granted_lease_mbits > ceiling` for an account |
| I2 | canonical JSON of the key | `cumulative_mbits > ceiling` for an account |
| I3 | lease event id | Σ uint `debit_mbits` of charges referencing the lease `> amount_mbits` (checked only when `amount_mbits` is uint). A charge is excluded from the sum ONLY when its `lease_id` resolves to no lease event; charges with other I4 violations (key/node mismatch, post-expiry tick) still count toward the sum. (Clarified after the first independent implementation flagged the ambiguity.) |
| I4 | charge event id | any of: `lease_id` matches no lease event in the ledger (further I4 checks and the I3 sum then skip this charge); charge `key` ≠ lease `key`; charge `node` ≠ lease `node`; both `tick` and `expires_tick` are ints (not booleans) and `tick > expires_tick` |
| I5 | lease event id | the lease's key has no account (§3.1), OR the lease's `issuer` ∉ `issuers(key)` |
| I6 | charge event id | see below |
| I7 | canonical JSON of the key | a malformed register exists for the key, OR no well-formed register exists, OR the well-formed registers conflict (§3.1). A register whose key is UNPARSEABLE (missing, non-list, or non-string elements) forms no account and convicts I7 with the canonical JSON of the raw key value as subject — named, never silently neutralized |
| I8 | canonical JSON of `[node, lease_id, charge_seq]` | two charge events with **different ids** carry the same (`node`, `lease_id`, `charge_seq`), with missing `node`/`lease_id` read as `""`; checked only when `charge_seq` is uint |

**I6 — charge well-formedness.** For each charge:

1. If `demand_mbits`, `debit_mbits`, `estimate_total_mbits` are not all
   uint → I6.
2. If `charge_seq` is not uint or is `< 1` → I6.
3. If `reason_class` ∉ `REASONS` → I6.
4. Only if checks 1–3 all passed: let `T := estimate_total_mbits`.
   - `accepted` must be JSON `true` exactly when
     `reason_class == "EMITTED"` (and not-`true` otherwise) → else I6;
   - `debit_mbits` must equal `T` if `EMITTED`, else `0` → else I6;
   - `demand_mbits` must equal `0` if `REFUSED_ESTIMATOR`, else `T` →
     else I6.

Multiple I6 violations in one charge produce one deduplicated entry (the
verdict is a set). A clean ledger's verdict is the empty list.

**Totality.** The audit never fails on adversarial content. The only fatal
condition anywhere in this specification is the same-id-different-bytes
check of §0.

---

## 5. Golden ledger artifacts

`ledger_traces/` holds the conformance corpus. Each case is two files:

- `<name>.ledger.jsonl` — the artifact (§1),
- `<name>.expected.json` — canonical JSON:

```jsonc
{ "spec": "charge-ledger/1",
  "name": "<name>",
  "fold": { "accounts": [ … ] },     // exactly §3.3
  "audit_codes": [ "I2 …", "I3 …" ]  // exactly §4
}
```

**Conformance:** an implementation parses each `.ledger.jsonl`, computes
fold and audit, and MUST match `fold` and `audit_codes` byte-for-byte
(canonical serialization compared as strings, or structural equality of the
parsed forms — they are equivalent for canonical JSON). Any divergence is a
conformance failure reported with the case name and the first differing
field. Implementations MUST also verify that re-serializing the parsed
ledger reproduces the input artifact byte-for-byte (id-sorted canonical
lines) — this checks the canonical JSON writer against §0–§1.

## 5.5 Key discipline (conventions, not conformance)

Keys are OPAQUE non-empty string lists to every rule in this document:
the fold groups by element-wise equality and nothing here parses their
contents. Conforming implementations MUST NOT attach semantics to key
elements. This section is therefore a *registry of conventions* for
issuers — normative for what keys mean, invisible to conformance — pinned
now because keys are cheap and migrations are not:

- `["exp", source, reader]` — pair-LIFETIME exposure (coalition.ts
  ExposureAccount). Lifetime because information is never unlearned.
- `["comp", subject, query_family, audience]` — composition accounts
  (egress-accountant/1), lifetime for the same reason.
- `["att", receiver, sender, epoch]` — attention accounts. The EPOCH
  element is deliberate: a renewable resource keys its accounts by
  period instead of bolting decay onto the kernel. **The key schema is
  where a resource's temporal physics is declared** — lifetime keys for
  irreversible resources, epoch keys for renewable ones. Units for
  non-information resources live in the estimator attestation, exactly
  where `log2` lives for bits; leakage-class labels are void off the
  information families.
- Reserved: subject-tagged triples (information *about* X, held *by* Y,
  read *by* Z — e.g. `["subj", subject, holder, reader]`). Today's pair
  families are the special case subject = source. Not yet issued
  anywhere; reserved so the first reference-check implementation does
  not improvise a shape (stories/reference-check.md, gap G4).

New resource families MUST add a row here before first issuance.

## 6. What this does not specify

- **The decision function** — `egress-accountant/1` (SPEC.md) owns it.
- **Estimation** — floats live in attested estimators, outside every
  conforming component (SPEC.md §0).
- **Signatures / identity** — `node` and `issuer` are claims; the audit
  cross-checks their consistency and cannot authenticate them. Byzantine
  *prevention* is out of scope by design (PROTOCOL.md non-claims).
- **Liveness, transport, gossip schedules** — the fold is a function of the
  set; how the set converges is deployment.

---

# Part II — charge-substrate/1: the X0 law

**Status:** normative for every layer that lives in this artifact,
including layers that do not exist yet. Frozen surfaces are untouched:
X0 is a SEPARATE verdict list (`x_codes`); `audit_codes()` (§4) and the
settlement `s_codes` bind to their corpora exactly as before.

## X0 — fact identity at the substrate

The same-bytes-≠-same-fact lesson has now been learned separately by two
layers (`charge_seq`/I8 in the information layer; `seq`/S5 in the
settlement layer) and would be relearned by every future kind. Promoted
to substrate law:

> Every event kind that carries a `seq` MUST name its author in one of
> the **authoring fields**, priority-ordered: `issuer`, `submitter`,
> `attestor` — the first present string is the actor. Two events with
> different ids claiming the same `(actor, kind, seq)`, `seq` uint, are
> an **X0 equivocation**, whatever their kind — including kinds the
> auditor does not understand.

Subject: canonical JSON of `[actor, kind, seq]` (the S5 subject shape).
Verdict surface: sorted, deduplicated `"X0 <subject>"` strings
(`Ledger.substrate_codes()`), reported ALONGSIDE the I- and S-codes by
the verifier and the node, never folded into them.

Consequences:

- **I8 and S5 become instances.** They remain normative for their layers
  (their corpora are frozen); X0 is the generalization new layers
  inherit for free. On every existing kind the X0 actor coincides with
  the layer code's authoring field, so X0 introduces no new judgment —
  only new coverage.
- **Future kinds get equivocation detection at genesis.** A
  `schema_registration` (E4), an issuer `covenant` (E5), or any kind not
  yet imagined is covered the moment it carries `(author, seq)` — no new
  audit arm to write, no lesson to relearn.
- **Kinds without `seq` are exempt** — `register` conflicts are I7's
  quarantine business; `charge` identity is I8's `(node, lease_id,
  charge_seq)`. X0 does not retro-legislate them.

---

# Part III — charge-provenance/1: closure charging (P-codes)

**Status:** normative. Frozen surfaces are untouched: the P-codes are a
SEPARATE verdict list (`p_codes`, `Ledger.provenance_codes()`); the §4
`audit_codes()`, the settlement `s_codes`, `x_codes`, and `c_codes` bind
to their corpora exactly as before. A ledger with no `derivation` events
and no provenance-declared emissions has an empty P verdict — which is
why the frozen corpora cannot be disturbed.

The law this part makes checkable (G16; the M4 gap of the moat
register): **an emission of a derived fact charges the fact's transitive
ancestry, atomically and at the data-processing-inequality bound.**
Without it, every internal derivation hop washes a source out of the
charge set — the compounding move and the laundering move are the same
move. With it, depth is not dilution: a source three hops behind the
emitted fact is charged exactly as if it were one hop behind, and
dropping it from the coupling is convictable from bytes.

## P.1 The `derivation` event kind

```jsonc
{ "kind": "derivation",
  "derived": "sha256:…",            // content id of the derived fact
  "consumed": ["sha256:…", "…"],    // direct ancestors, by content id
  "hop_capacity_mbits": 12000,      // uint: declared capacity of THIS hop
  "issuer": "chamberA",             // the deriving chamber
  "seq": 7,                         // uint >= 1, issuer-local
  "tick": 40 }                      // int, issuer clock domain
```

The fold ignores the kind (§2 forward compatibility); it carries no
value and no leakage. `hop_capacity_mbits` is the issuer's declared
bound on how many millibits of the consumed set this derivation can
carry into `derived` — the DPI input, declared exactly where every other
capacity in this stack is declared (by the party the audit will convict
against its own declaration). **Fact identity is already covered:**
`derivation` carries `(issuer, seq)`, so X0 (Part II) convicts
equivocation with no code added here — the second dividend of the
substrate law, after covenants.

## P.2 Resolution and the provenance graph

A string `c` **resolves** iff it is (a) the event id of any event in the
ledger, or (b) the `derived` string of some `derivation` event. (When a
tombstone kind ships — G18's ancestry-retention law — its commitments
join clause (a); **no tombstone kind exists in this artifact today**,
and that gap is named, not papered over.)

The **provenance closure** of a fact id `d` is the least set containing
`d` and closed under: if `f` is in the closure and some `derivation` has
`derived == f`, every string element of its `consumed` is in the
closure. Cycles are legal adversarial content and terminate by
visited-set; multiple derivations of the same fact union their
ancestries. The closure is reflexive — `d` itself is a member.

**Source anchors.** A closure member that resolves to a ledger event
whose `key` field is a list of exactly three strings with first element
`"exp"` anchors the **source** `key[1]`. This is the one place a layer
of this artifact attaches semantics to a key family: charge-provenance/1
is hereby normative over the `["exp", source, reader]` convention row of
§5.5 (which remains invisible to charge-ledger/1 conformance). Events of
any kind anchor — a `register`, `lease`, or `charge` on an exposure key
all name the same source; anchoring the union is the escalating
direction. Closure members that resolve but carry no exposure key
contribute no source. `sources(d)` := the set of anchored sources.

## P.3 Declared emissions and the coupling

An **emission of derived fact `d`** is a charge event with
`reason_class == "EMITTED"` whose `channel` is exactly the string
`"derived:" + d`. The channel field is where an estimate already names
what crosses; a provenance-honest orchestrator names the derived fact's
content id there (`CapacityEstimate(channel="derived:sha256:…")` flows
through `charge_coupled` unchanged — every coupled sibling inherits it).

The **emission coupling** of a charge is the set of all charge events in
the ledger agreeing with it on `(node, tick, channel)` — exactly the
fields every sibling of one `charge_coupled` call shares while differing
on key, lease, and `charge_seq`. Grouping compares raw JSON values (via
canonical serialization), so malformed fields group somewhere instead of
crashing anything.

Per coupling with channel `"derived:" + d`:

- the **exp-emissions** are its EMITTED members whose `key` is a
  well-formed exposure triple; each names a **reader** `key[2]`;
- the **declared emission capacity** `E` := the maximum uint
  `estimate_total_mbits` over the exp-emissions (maximum, not first —
  adversarially mixed estimates resolve in the escalating direction);
- a coupling with no exp-emissions, or whose `d` has an empty
  `sources(d)`, produces no P1/P2 findings.

## P.4 The DPI bound

For a source `s` and derived fact `d`, the **DPI bound** is

> `bound(s, d, E)` := `min(E, maxflow(s → d))`

over the flow network: one node per closure fact id; one split node pair
per `derivation` in the closure with internal capacity
`hop_capacity_mbits` (a non-uint capacity is **unbounded** — malforming
a declaration must never shrink an obligation); edges consumed-fact →
derivation → derived-fact otherwise unbounded; a super-source with
unbounded edges to every anchor of `s`; sink `d`. Unbounded capacities
are instantiated at `E` (sound, because only `min(E, flow)` is ever
compared: any cut of instantiated edges already has capacity ≥ E).
Integer max-flow; no floats exist anywhere in this Part.

The bound is the worst case the declarations admit: emitting `E`
millibits of a fact whose ancestry can carry `maxflow` millibits of `s`
leaks at most `min` of the two — and the meter charges the worst case,
as everywhere. Overpaying is legal; the bound is a floor.

## P.5 The P-codes

Verdict surface: sorted, deduplicated `"<code> <subject>"` strings
(`provenance_codes()`), same discipline as every other family. Total
over adversarial content — nothing in this Part raises.

| code | subject | convicts when |
| --- | --- | --- |
| P1 | canonical JSON of `["exp", s, r]` | **dropped ancestor.** Some coupling's exp-emission toward reader `r` emits derived fact `d` with `s ∈ sources(d)`, and the coupling contains NO EMITTED charge on key `["exp", s, r]` |
| P2 | canonical JSON of `["exp", s, r]` | **closure undercount.** The coupled EMITTED charges on `["exp", s, r]` exist but their summed uint `debit_mbits` is `< bound(s, d, E)` — the dishonest direction, priced exactly |
| P3 | derivation event id | **orphaned derivation.** The event's `consumed` is not a list, or some element fails to resolve (P.2) — ancestry that cannot be walked cannot be charged |

Notes, in the register's discipline:

- P1's subject is the **uncharged key itself** — the finding names the
  account that should have been debited, which is also what lets
  settlement map it (P.6). The emitter's own key is not special: if
  `a ∈ sources(d)`, the emission charge on `["exp", a, r]` satisfies its
  own P1 row, and its debit `E ≥ bound` satisfies P2.
- An empty `consumed` list is a legal root claim ("derived from
  nothing"), inert for every check — not an orphan.
- Like I4/I5, a P finding can be RESOLVED by merging in the missing
  fact (the coupled charge, the consumed event): findings are functions
  of the set, and the set growing toward completeness is the honest
  direction. The FOLD's monotonicity (leakage class, incident) is
  untouched — P-codes never feed it.

## P.6 Settlement interaction (fail closed)

P findings join the dirty-court stream `_court_findings` exactly as
covenant C-codes did: a `required_clean` release against keys a P
finding touches is convicted (S4/S8). P1 and P2 subjects ARE keys, so
they map precisely; **P3 and any future P-code fall to the fail-closed
default and touch everything** — an artifact whose ancestry cannot be
resolved does not move value past a clean-court gate. The frozen
settlement corpora contain no derivation events and no provenance
channels; their verdicts are byte-identical.

## P.7 Non-claims (the honest subset)

This Part convicts liars against their own declarations; it does not
manufacture declarations. Named, not implied:

1. **Undeclared emissions are invisible.** An EMITTED charge whose
   channel does not name its derived fact escapes P1/P2 — the same
   trust class as an undercounting estimator (G8): the estimator
   attestation, not the kernel, is the anchor for "the channel names
   what crossed". The conviction surface binds every DECLARED
   derivation emission; making declaration itself compulsory needs an
   estimator-independence story the stack does not yet have.
2. **Non-exposure emissions are out of scope.** A derived-fact emission
   coupled only to non-`exp` keys produces no P findings; provenance
   charging is defined over the exposure family only in /1.
3. **Capacity declarations are claims.** `hop_capacity_mbits` is
   declared by the deriving chamber; a chamber that over-declares
   capacity raises its own obligations (self-harm), one that
   under-declares is lying in the direction estimator honesty already
   guards. The DPI bound is exact over the declarations, not over
   physics.
4. **No tombstone kind exists yet** (P.2); until G18 ships, deletion
   below a live closure is expressible only as absence, which P3
   convicts — conservative, and named.
