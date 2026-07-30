# charge-covenant/1 — issuer self-restrictions, audited

**Version:** `charge-covenant/1`
**Status:** normative for the covenant layer. Extends `KERNEL-SPEC.md`
(event identity, the lease vocabulary) and is read by
`SETTLEMENT-SPEC.md`'s dirty-court law (§4 below). Reference
implementation `covenant.py`; standing lane `test_covenant.py`. Design
source: design consult (2026-07-05, private) §4 (E5).

## 0. Why — the exit story's other half

The stack's most-proven theorem, one-way widening, reads from the
user's side as "you can never leave." G7 closed the VALUE half of exit
(S8: no issuer strands funds). This spec closes the AUTHORITY half:
**future authority must be refusable, in the artifact, checkably.**
Revocation decomposes:

- **tenor** — every lease already expires (`expires_tick`);
- **covenant** — the issuer's declared self-restriction on its own
  future issuance (this spec);
- **residue** — the honest statement of what stays exposed forever
  (a declared field; it cannot be enforced away, only named — that is
  one-way widening speaking, not a design failure).

A covenant binds ONLY its own issuer's authority. It is a self-worn
handcuff whose key is thrown into the court: violation of ANY
well-formed covenant convicts, so the strictest binds, merge only
escalates, and un-covenanting is impossible by construction.

## 1. The covenant event

```jsonc
{ "kind": "covenant",
  "issuer": "bobChamber",           // the self-restricting authority
  "key": ["exp", "srcBob", "readerR"],
  "action": "cease_lease_issuance", // or "cap_lease_total"
  "horizon_tick": 30,               // cease: no lease may outlive this
  "cap_mbits": 0,                   // cap: Σ non-grandfathered lease amounts ≤ this
  "except_lease_ids": ["sha256:…"], // GRANDFATHERED authority, by content id
  "residue": "readerR retains everything already emitted; widening is one-way",
  "seq": 1,                         // issuer-local; X0 owns equivocation
  "tick": 5 }
```

Exactly one of `horizon_tick` (int) / `cap_mbits` (uint) per action.
`except_lease_ids` (optional, list of event ids) **grandfathers**
outstanding authority BY NAME in the covenant's own bytes: "these named
grants survive; nothing else, ever" — the residue statement's
mechanical twin. Tenor drains the survivors. Fact identity costs this
spec nothing: covenants carry `(issuer, seq)`, so X0 (KERNEL-SPEC
Part II) convicts equivocation — the substrate law's first dividend.

Semantics:

- **cease_lease_issuance** — no non-grandfathered lease by this issuer
  on this key may have `expires_tick > horizon_tick`.
- **cap_lease_total** — Σ `amount_mbits` over non-grandfathered leases
  by this issuer on this key stays ≤ `cap_mbits`. With the default
  grandfathering, the cap prices NEW authority; `cap_mbits: 0` is the
  wind-down ("no new authority, ever").

## 2. The audit — C-codes

Separate verdict surface (`c_codes`), same discipline as every code
family: sorted, deduplicated `"<code> <subject>"`, total over
adversarial content. The frozen I/S conformance surfaces move by zero
bytes (covenant-free artifacts produce empty `c_codes`).

| code | subject | emitted when |
| --- | --- | --- |
| C1 | lease event id | a non-grandfathered lease outlives some cease covenant's `horizon_tick` on its (issuer, key) |
| C2 | canonical key JSON | Σ non-grandfathered lease amounts by the issuer on the key exceed some cap covenant's `cap_mbits` |
| C3 | covenant event id | malformed covenant: non-string issuer/residue, bad key, unknown action, missing/mistyped horizon or cap, bad `seq`, non-string-list exceptions |

A covenant with an action this audit does not understand is malformed
(C3) — and §4 makes every C-code, including future ones, fail closed
for value.

## 3. Honest fronts

- `declare_covenant` (the issuer's own act): validates the vocabulary;
  by default auto-grandfathers every outstanding lease that would
  violate the new covenant (cease: those outliving the horizon; cap:
  all of them), naming each id in the event. An EXPLICIT exception list
  (possibly empty) grandfathers less — the audit then convicts the
  un-exempted history immediately, which is a legitimate recorded
  self-indictment, not an error.
- `LeaseIssuer.grant` refuses any grant that would violate the issuer's
  own covenants in its ledger (a new grant is never grandfathered — its
  id exists in no covenant's bytes). A dishonest issuer forges past
  this and convicts itself; the covenant is evidence either way.

## 4. Value fails closed against broken covenants

Covenant findings join the dirty-court stream that S4/S8 police
releases against (`settlement._court_findings`). Subject mapping for
"touches" (SETTLEMENT-SPEC §3): C1's subject is a lease id (the lease's
key); C2's subject is a key. **Any future C-code touches every key
set** — value against authority broken in ways the audit cannot parse
never moves. Refunds are untouched: exit never strands money (S8's law
is not weakened by this spec — the two compose).

## 5. What this deliberately does NOT claim

- **Residue enforcement.** `residue` is prose. What has crossed has
  crossed; one-way widening is a theorem, and this spec refuses to
  pretend otherwise.
- **Cross-issuer bans.** A covenant binds its issuer. A SECOND issuer
  claiming the same key is I5/I7's business (poison registration,
  foreign lease), not a covenant's.
- **Charge-time enforcement.** Charges against a grandfathered lease
  remain valid until tenor drains it — the covenant is a promise about
  issuance, not a retroactive revocation of decisions already priced
  (decisions are final; the kernel never re-litigates).
- **Identity.** `issuer` is a declared string, as everywhere (L5).
- **Covenant liveness.** Nothing forces an issuer to covenant; the
  MARKET does (a chamber that cannot show an exit covenant is a chamber
  strangers price accordingly). The monitorability design law is
  satisfied trivially: both covenant forms are safety properties over
  the event set.
