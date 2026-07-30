# charge-scope/1 — reader-scoped views with transparency proofs

**Version:** `charge-scope/1`
**Status:** normative for the scoped-serving layer. Extends
`KERNEL-SPEC.md` (`charge-ledger/1`, which owns event identity and the
artifact wire format) and reads `SETTLEMENT-SPEC.md`'s event vocabulary.
Reference implementation: `scope.py`; served by `node.py`; standing lane
`test_scope.py`. Design source: FRAMEWORKS.md F2 (Certificate-
Transparency verifiable logs; SUNDR fork consistency) — imported for E2.

## 0. Why, and what is actually claimed

A chamber-node serves a court. Until /scope, it served the WHOLE court
to anyone — tolerable for a single coalition's shared court, wrong the
moment one node hosts many keys ("point it at courts, not secrets" was a
warning, not a mechanism). charge-scope/1 makes the warning a mechanism
with two theorem-backed properties and two honest refusals:

**Claimed:**

1. **Everything served is in the court.** Every event in a scoped
   response carries a Merkle membership proof against a head that
   commits to the entire event set. The server cannot invent facts for
   one reader that are not in the artifact it is committed to.
2. **The serving history cannot be rewritten.** The node maintains an
   append-only ingestion log; a reader who remembers any earlier head
   can demand a consistency proof. A node that rewrote or reordered its
   history cannot produce one (RFC 6962/9162 machinery; SUNDR's fork-
   consistency property: readers who compare heads detect equivocation
   on first contact).

**Refused, named:**

3. **Completeness is not proven.** A scoped response proves inclusion,
   not exhaustiveness: the server may withhold in-scope events. The
   kernel's own fact-identity discipline is the counterweight — dense
   sequence numbers (`charge_seq` per lease; `seq` per (actor, kind))
   make withholding leave arithmetic gaps the scoped verifier REPORTS
   (§4). Gap-free withholding of an entire suffix remains possible and
   is detected only by cross-checking heads with other readers/nodes
   (property 2 makes systematic per-reader worlds a provable fork).
   Range/completeness proofs (sorted-key trees) are /2 material.
4. **Heads are unsigned.** Binding a head to a node identity is the
   same L5 frontier as binding an issuer string to a party. Two readers
   comparing heads out-of-band get fork detection without any PKI; a
   deployment that wants transferable proof of a node's equivocation
   adds signatures at the transport layer (E8), not here.

## 1. Commitments

Hashing is RFC 6962-shaped, domain-separated, over ASCII bytes:

```
leaf(x)      = SHA-256(0x00 || x)
node(l, r)   = SHA-256(0x01 || l || r)
MTH([])      = SHA-256("")
MTH(D[n])    = node(MTH(D[0:k]), MTH(D[k:n])), k = largest power of 2 < n
```

Leaves are event id strings (`"sha256:…"`). Event ids are already the
SHA-256 of an event's canonical bytes (KERNEL-SPEC §1), so committing to
ids commits to content.

Two trees, two jobs:

- **Set tree** — leaves = the event ids in canonical artifact order
  (byte-wise sorted). `set_root` is a pure function of the event SET:
  two federated nodes hold the same court iff their set roots are equal
  (convergence checking is one hash comparison). Membership proofs for
  scoped views are audit paths in this tree.
- **Ingestion log** — leaves = event ids in THIS NODE's first-adoption
  order (node-local truth; unaffected by merge semantics). Append-only:
  new events append in id-sorted order per ingestion batch, and the
  order is persisted (a sidecar of the state file) across restarts.
  Consistency proofs are taken in this tree.

## 2. The head

```jsonc
{ "tree_size": 41,            // |event set|
  "set_root":  "hex…",        // MTH over id-sorted ids
  "log_size":  41,            // ingestion log length (== tree_size)
  "log_root":  "hex…" }       // MTH over ingestion order
```

Served at `GET /v1/head`. Unsigned (§0.4).

## 3. The scope closure

For a requested key set K (charge-ledger keys, lists of strings), the
served closure is deterministic and extends the "touches" vocabulary
SETTLEMENT-SPEC §3 already defines:

```
L0   register / lease / charge events whose key ∈ K
L1   escrow events with any charge_keys member ∈ K
L2   release / refund / default_resolution / outcome_attestation
     events whose escrow_id ∈ L1
L3   bond_resolution events whose attestation_id ∈ L2
REF  events referenced by in-scope charge_ids / attestation_ids and
     present in the court — so every in-scope conviction arm (S3's
     off-key receipt, S9's off-escrow attestation) is recomputable
     from the served bytes; the referenced event carries its own key
     and the reader sees exactly why the audit convicts.
```

**Deposits are excluded by design.** A scoped reader is entitled to the
flow bound to its keys, never to any account's total wealth. The corollary
is stated plainly: a scoped view supports the INFORMATION verdict on K
and receipt-checking of the value flow bound to K; global value verdicts
(S1 solvency, the conservation identity) require the full artifact.
Scoped views are court files, not solvency audits.

Endpoints:

```
GET /v1/scope?keys=<canonical JSON array of key lists>
  -> { "head": {…§2…}, "keys": […],
       "events": [ …payloads, id-sorted… ],
       "proofs": { "<eid>": { "index": i, "path": ["hex…", …] } } }

GET /v1/consistency?first=<m>
  -> { "first": m, "second": n, "proof": ["hex…", …],
       "second_log_root": "hex…" }
```

A node started with `--scoped-only` serves ONLY: `POST /v1/events`,
`GET /v1/health`, `/v1/head`, `/v1/scope`, `/v1/consistency`. The
whole-court views (`/v1/ledger`, `/v1/fold`, `/v1/audit`,
`/v1/settlement`, `/v1/verify`) return 404. Keys then function as
bearer capabilities: requesting a scope requires knowing the exact key
strings. Key guessability is a deployment property (key strings with
entropy), named not solved.

## 4. The scoped reader's verification (`verify_scope`)

From the response alone, with no other access:

1. every served event's id recomputes from its canonical bytes;
2. every served event's membership proof verifies against the head
   (RFC 9162 §2.1.3.2, implemented exactly);
3. the served set equals the closure of K over itself — a response
   padded with off-scope events fails (the server cannot leak extra
   facts to a reader and call it a scope);
4. **omission evidence**: within the scope, `charge_seq` per lease must
   be dense 1..max — a gap is reported as a hard problem ("withheld or
   never served — demand an explanation"). Settlement `seq` gaps per
   (actor, kind) are reported as notes (the same actor's out-of-scope
   activity legitimately consumes seq values).

Consistency across time: the reader remembers `(log_size, log_root)`
and verifies growth with `/v1/consistency` (RFC 9162 §2.1.4.2,
implemented exactly). Both proof algorithms are brute-force
cross-checked in the standing lane for every (index, size) and every
(m, n) pair up to 33, with tamper cases.

## 5. Non-claims, consolidated

- **No completeness proof** (§0.3) — inclusion + seq-density evidence +
  fork consistency; not exhaustiveness. /2 direction: sorted-key range
  proofs or a sparse Merkle map.
- **No signatures** (§0.4) — head-to-identity binding is L5/E8.
- **Scope ≠ solvency** (§3) — global value verdicts need the artifact.
- **The topology channel stands** (G15): the head commits to the WHOLE
  court, so proof shapes and tree size leak court cardinality to every
  scoped reader; the closure leaks how many settlement events touch K.
  Assume the metadata leaks; EntropyPool-style padding is G15's open
  design, not this spec's claim.
- **Scoped-only is serving discipline, not access control.** A key
  string is a capability only as guessable as its entropy; real reader
  authentication is the same L5 frontier as every identity here.
