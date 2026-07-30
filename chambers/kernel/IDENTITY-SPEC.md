# charge-identity/1 — self-certifying key-authors (IDENTITY-SPEC)

*Normative. The attributability unlock: the gap between "forgery is
detectable as equivocation" and "forgery is attributable to a party."
Until this spec, every issuer was an unauthenticated string — a bond
that slashes a string slashes nobody. Identity is now the key, exactly
Ethereum's move.*

## 1. Key-shaped author ids

An author id MAY be self-certifying:

    ed25519:<64 lowercase hex chars>        (the 32-byte public key)

Any string not of this shape is a LEGACY author: /1 imposes nothing on
it (the frozen corpora carry only legacy authors and move by zero
bytes). A string that begins `ed25519:` but is not a well-formed key id
is NOT legacy — it is a key-shaped claim that fails, and every event it
authors convicts A1. There is no registry, no binding event, no
first-seen rule: the id commits to the key by construction, which is
what makes it CRDT-safe (nothing about identity depends on merge
order).

Well-formed means EXACTLY 64 lowercase hex characters — uppercase or
mixed-case hex is ill-formed and convicts A1. This is load-bearing,
not pedantry: a case-tolerant verifier gives one key several distinct
author strings, and because fact identity is (author, kind, seq), a
signer equivocating across its own case-aliases would never meet X0.
One key, one id. (Named and closed 2026-07-09; the pre-fix reference
accepted case-aliases via hex-decoding tolerance.)

## 2. The author of an event

Each kind declares ONE author field (`identity.AUTHOR_FIELD`):

    register, lease, covenant ................ issuer
    charge ................................... node
    deposit, escrow, release, refund ......... issuer
    outcome_attestation ...................... attestor
    default_resolution, bond_resolution ...... submitter
    reviewer_seat ............................ reviewer

Kinds outside this map are outside /1's mandate; a `sig` on them is
inert bytes. New kinds join the map by spec revision.

## 3. The signature

A key-authored event MUST carry `sig`: 128 LOWERCASE hex chars, the
RFC 8032 Ed25519 signature over the CANONICAL JSON BYTES of the payload
with the `sig` field removed (`identity.signed_bytes`). Any other
encoding — uppercase, mixed case, whitespace — is ill-formed and
convicts A1, even if the underlying bytes would verify. Because event
identity is the sha256 of the canonical payload WITH sig, a signed fact
remains content-addressed; because Ed25519 signing is deterministic, an
honest signer produces exactly one encoding of each fact — and the
verifier accepts exactly one, or a re-encoded copy of a fact would mint
a second event id for the same semantics.

Verification is STRICT: `s >= L` rejected (one valid s per signature —
the malleability guard), off-curve and non-canonical point encodings
rejected, everything total (adversarial bytes return false, never
crash).

## 4. Convictions — A-codes (separate surface, frozen surfaces unmoved)

    A1 <author>   key-authored event with missing or ill-formed sig
    A2 <author>   sig present but fails verification

`identity_codes(ledger)` is the conformance surface, sorted and
deduplicated, mirroring S/X/C/P. The stranger's verifier folds A-codes
into its verdict: a court containing an unattributable key-authored
fact is CONVICTED, not trusted.

What A-codes deliberately do NOT do: quarantine the author's other
events (one bad sig does not poison attributable facts), or convict
legacy authors (opt-in is the migration path — a coalition that wants
mandatory attribution simply refuses to lease/escrow against legacy
names, no protocol change needed).

## 5. What this converts from named gap to mechanics

- **Bonds (S9/S10)**: an attestor who is a key answers with a key;
  slashing is attributable.
- **Covenants (C-codes)**: a cease signed by the ceasing key binds THAT
  key — "the issuer's own later events" is now a cryptographic phrase.
- **Scope heads, run receipts**: signable the moment their kinds join
  the author map (/2).
- **The economic-refusal law**: a malicious signer CAN emit two valid
  signatures over the same content (nonce freedom), producing two event
  ids — and gains nothing, because fact identity is (author, kind, seq)
  and X0 convicts the duplication. The existing substrate law was the
  missing half of this spec all along.

## 6. Honest limits, named

- **Key custody is not key meaning.** A key proves continuity of
  control, not personhood, uniqueness, or non-delegation. Sybil
  resistance remains L5/G3 — priced, not solved here.
- **No rotation in /1.** A compromised key is a compromised identity;
  rotation (old key covenants its succession to a new key) is /2,
  named. Until then: the mitigation is the same as Ethereum's — new
  key, new identity, migrate authority explicitly.
- **Legacy coexistence is a policy choice per coalition**, not a
  protocol default. /1 refuses to hard-deprecate strings because the
  frozen corpora are law.
- **Performance**: pure-Python verification is a few ms per event —
  protocol-reference speed. The Rust twin's port (with a vetted
  library or a from-spec implementation against these same RFC
  vectors) is owed and named.

## 7. /2 — the authoring front-ends (shipped 2026-07-08)

Nothing new on the wire: §1–§5 already define what a signed event IS
and what convicts. /2 is the AUTHORING DISCIPLINE, wired through every
issuer front-end (`LeaseIssuer`, `KernelMeter`, `SettlementIssuer`,
`resolve_default`, `attest_outcome`, `resolve_bond`,
`declare_covenant`):

- A front-end constructed with a `Signer` signs every fact it authors;
  the event id then covers the signature (§3).
- The law fails CLOSED at construction (`identity.require_signer`): a
  key-shaped author without its Signer is refused (it could only emit
  A1-convicted facts); a Signer whose key is not the author is refused
  (A2 by construction); a Signer on a legacy author is refused (inert
  bytes dressed as attribution).
- `KernelMeter` authors under TWO ids — `issuer` on registrations and
  leases, `node` on charges — and takes two signers. Refusals are
  charges too: a REFUSED decision is signed by the same node key.
- The `sig` field is ADDITIVE on every event dataclass, serialized only
  when present: unsigned front-ends produce exactly their historical
  bytes, and the frozen corpora move by zero bytes.

Standing lane: `test_identity_wiring.py`. The composed pipeline
(`chambers/pipeline/`) runs fully key-authored: issuers, mediator
node, and escrow authority are all keys; a tampered signature byte
convicts on the A-surface.

What /2 wiring deliberately does NOT claim, named:

- **Settlement ACCOUNT names stay petnames** (payer/payee/account
  strings) in the settlement issuer's namespace — a key-id account with
  no account-holder signature on any value fact would be attribution
  theater. Account-holder-signed value intents are a /3 design row.
- **`derivation` and scope-head kinds remain outside the author map**
  (§2: kinds join by spec revision).
- **Rotation is still open** (§6) — /2 here is the authoring wiring,
  not the rotation covenant.
- **The Rust twin still verifies I/S surfaces only**; its A-code port
  (Ed25519 from-spec against the same RFC vectors) stays owed.
- **attention-node's HTTP front door** accepts what parties post;
  signing there is the parties' client-side duty. The node's OWN meter
  can now sign; wiring a deployment key into it is E8 work.
