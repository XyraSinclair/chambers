# charge-views/1 — interpretation out of the timeless fold (W-codes)

**Status:** normative. Frozen surfaces are untouched: not one byte of any
frozen corpus moves. `charge-ledger/1`'s fold keeps serializing
`leakage_class` and `incident` exactly as before — this spec changes what
those bytes *are*, not what they say: they are the **default view**, one
policy among many, no longer the meaning of the artifact.

The law this spec makes checkable (E7 of the endpoint register):
**class vocabularies and incident thresholds are policy; policy versions;
the timeless conformance surface keeps only the integer sums.** Convicted
independently three times before this spec existed:

1. **dogfood run 1, finding 2** (private log) — under a placeholder entropy declaration
   the ceilings and refusals stayed real while the
   negligible/bounded/material labels went decorative. The sums were
   facts; the labels were an interpretation whose calibration had
   silently failed.
2. **design consult (2026-07-05, private), disagreement 1** — "KERNEL-SPEC §3.2 bakes
   class labels and the incident threshold into the normative fold.
   Thresholds and vocabularies will change; the fold must not."
3. **attention-node demo** — `leakage_class` is void on attention keys:
   it denominates entropy, which attention does not have. A label
   computed where its denominator has no meaning is not conservative,
   it is a lie with a reassuring vocabulary.

## V.0 The delegation, stated exactly

- `charge-ledger/1` §3.2/§3.3 (fold `leakage_class`, `incident`) remain
  **normative for bytes**: every frozen corpus, both Rust ports, and the
  conformance checker bind to them unchanged, forever.
- Their **meaning** is delegated here: the embedded fields are DEFINED as
  `charge-views/1` applied with the **legacy-default policy** (§V.2).
  This is a theorem about the present, not a plan — see the parity law
  (§V.5): for every account of every fold,
  `fold.leakage_class == view(legacy-default).class` and
  `fold.incident == view(legacy-default).incident`, bit for bit, over
  every frozen corpus. The frozen ledger corpora are therefore ALSO the
  views/1 default-policy corpora, at zero bytes moved.
- **Amendment binding future surfaces:** any future fold version
  (`charge-ledger/2+`, and any new kind's fold-shaped summary) MUST NOT
  embed class labels or incident booleans. Integer sums only;
  interpretation arrives via a view with a named policy.

## V.1 The view is a pure function, off the artifact

`view(fold_bytes, policy_bytes) → report | refusal`

No ledger events. No new kinds. A view is computed BY a reader FROM the
fold a verifier already recomputes from bytes — the same trust path as
`charge-verify`. Two readers with different policies disagree about
labels while agreeing about every sum; that disagreement is now visible
and priced instead of smuggled inside the conformance surface.

## V.2 The policy artifact

Canonical JSON (the `canonical_json` of `charge-ledger/1` §2), identified
by `sha256` hex of its canonical bytes (`policy_sha256`).

```jsonc
{
  "spec": "charge-views/1",
  "name": "legacy-default",
  "domains": null,                 // null = every key (legacy); else a
                                   // non-empty list of non-empty string-
                                   // list prefixes, e.g. [["exp"]]
  "classes": [                     // strictly increasing max_permille
    { "label": "negligible", "max_permille": 50 },
    { "label": "bounded",    "max_permille": 250 },
    { "label": "material",   "max_permille": 500 },
    { "label": "unsafe",     "max_permille": 800 }
  ],
  "terminal_label": "reconstructed",
  "incident_permille": 800
}
```

The object above IS the legacy-default policy — byte for byte the
boundaries of `egress-accountant/1` §1.5 and the 800‰ incident line of
`charge-ledger/1` §3.2. Its `policy_sha256` is pinned in the golden
corpus (`views_traces/`).

**Admissibility** (checked before anything else; any failure refuses the
whole view with `W1 sha256:<policy_sha256>` — all-or-nothing, no partial
reports, the F1 lesson):

- `spec` is exactly `"charge-views/1"`; `name` a non-empty string.
- `domains` is `null`, or a non-empty list of non-empty lists of strings.
- `classes` is a non-empty list; every `label` a non-empty string; every
  `max_permille` a uint (not a boolean); `max_permille` strictly
  increasing in list order.
- `terminal_label` a non-empty string. All labels — the class labels and
  the terminal — are pairwise distinct, and none is `"void"` (reserved,
  §V.4).
- `incident_permille` is a uint.
- No other top-level fields (unknown fields malform: a policy is an
  interpretation contract, not an extensible envelope).

Strictly increasing boundaries make **monotonicity structural** rather
than promised: for fixed entropy, the class index is non-decreasing in
`cumulative_mbits`, and `incident` is non-decreasing in
`demanded_mbits`; under register min-resolution (entropy can only fall),
class and incident only escalate. The fold's escalate-never-retract law
survives delegation for EVERY admissible policy, not just the default.

## V.3 The view computation

Input fold: an object `{ "accounts": [...] }` where every account has a
`key` that is a list of strings, and uint `cumulative_mbits`,
`demanded_mbits`, `subject_entropy_mbits`. Anything else — accounts not
a list, an unparseable key, a missing or non-uint sum on ANY account —
refuses the whole view with `W2 sha256:<hex of the input's canonical
bytes>`. Extra account fields (`ceiling_mbits`, `granted_lease_mbits`,
`leakage_class`, `incident`, `conflicted`, anything future) are ignored:
the view reads exactly the three sums it denominates.

Per account, with `cum`, `dem`, `s` the three sums:

- **Domain test** (`domains` non-null): the key is in-domain iff some
  prefix `p ∈ domains` satisfies `key[:len(p)] == p`. Out-of-domain →
  `class := "void"`, `incident := null`. The attention-demo lie is now
  unrepresentable: a label only appears where its denominator applies.
- **Class** (in-domain, or `domains` null): exactly §1.5's arithmetic,
  generalized — `c := min(cum, s)`; the first class in order with
  `c * 1000 <= max_permille * s` wins; no class satisfied →
  `terminal_label`. Integer cross-multiplication, no division; `s = 0`
  lands in the first class (`0 <= 0`), matching the reference fold.
- **Incident** (in-domain): `dem * 1000 >= incident_permille * s`.

## V.4 Report serialization

Canonical JSON of:

```jsonc
{ "spec": "charge-views/1",
  "policy_name": "…",
  "policy_sha256": "…",
  "accounts": [                     /* sorted by canonical JSON of key,
                                       byte-wise ascending — fold order */
    { "key": [...],
      "class": "…" | "void",
      "incident": true | false | null,
      "cumulative_mbits": n, "demanded_mbits": n,
      "subject_entropy_mbits": n } ] }
```

Every label is bound in the same row to the exact integers it was
computed from and, at the top, to the hash of the policy that computed
it. A presented label without its `policy_sha256` is an unsourced claim;
with it, any stranger recomputes the label from the fold in one call.
`"void"` is reserved output vocabulary: no admissible policy can emit it
as a class label, so `"void"` always means "this policy declines to
denominate this key" and never "a policy named a class void".

A refusal serializes as canonical JSON of
`{ "spec": "charge-views/1", "refused": [ "<W-code> <subject>" ] }`
(sorted, deduplicated, single-space — the audit-verdict shape).

## V.5 The parity law (the migration proof)

For every ledger of every frozen corpus (`ledger_traces/*.expected.json`
and every fold any conformant implementation produces):

```
view(fold, legacy-default).accounts[k].class    == fold.accounts[k].leakage_class
view(fold, legacy-default).accounts[k].incident == fold.accounts[k].incident
```

The lane test binds this against the FROZEN corpus bytes directly (not
against the current reference implementation), so drift in either
direction — views or fold — is a red test. This is what "moved out of
the fold without moving a byte" means mechanically: the meaning moved;
the bytes are provably still there under the default policy.

## V.6 W-codes

| code | subject | emitted when |
| --- | --- | --- |
| W1 | `sha256:` + policy_sha256 | the policy fails any §V.2 admissibility check |
| W2 | `sha256:` + hex of the fold input's canonical bytes | the fold input fails §V.3 well-formedness |

Both refuse the ENTIRE view. There is deliberately no W3: views are a
pure derived layer and convict nothing about the ledger — every crime a
ledger can commit is already owned by I/S/X/C/P codes on their own
surfaces. A view failure is a failure of the QUESTION (bad policy, bad
input), never new evidence about the artifact.

## V.7 Residues, named

- **Entropy provenance is not solved here.** A register's
  `subject_entropy_mbits` still arrives with no declared provenance
  (owner judgement vs placeholder — dogfood finding 2's remaining half).
  Views make every label *recomputable and policy-attributed*; they
  cannot make the entropy honest. That is a register-schema question:
  E4's catalog owns the `entropy_provenance` field when it lands, and
  presentation layers MUST NOT render class labels as calibrated until
  a run's registers carry it.
- **Policy distribution is not solved here.** A policy is content-
  addressed but not registered anywhere; "which policies does this
  ecosystem recognize" is E4 catalog work (and lands permissionless and
  forkable, per the binding E4 amendment).
- **`conflicted` stays in the fold.** It is structural (register-set
  disagreement), not interpretive — it survives the delegation test
  that class labels failed.
