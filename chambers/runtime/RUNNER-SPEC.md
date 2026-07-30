# runtime-r2/1 — the deterministic runner (RUNNER-SPEC)

*Normative. RUNTIME.md rung R2, first artifact: the runner + the
output-hash conformance lane. R2 is the first rung a STRANGER's data can
honestly ride, because reproduction is a check they can perform, not a
trust they must extend.*

## 0. What R2 claims — and refuses to claim

An R2 receipt claims exactly this: **the run was a pure function of a
content-addressed bundle** — anyone who re-executes the same bytes gets
the same output hash. It does NOT claim the operator's host could not
see the plaintext (that is R3), and it does NOT prevent exfiltration —
a worker that phones home leaks without disturbing its own determinism.
RUNTIME.md's own words: *what* it did with the plaintext is pinned even
if *seeing* it wasn't prevented. The claim class on the receipt is
`reproducible_local` and nothing above it (`ENVIRONMENT_LAWS`:
receipts describe observed configuration, not perfect isolation).

**Corollary, stated once and bluntly: an LLM call can never ride R2.**
Temperature 0 is a knob, not a determinism guarantee across service
builds. R2 workers are deterministic PROGRAMS — the projections,
filters, estimator harnesses, and verifiers AROUND the model. A workflow
containing an LLM step rides R2 only by pinning the model's recorded
outputs as bundle inputs and making everything around them re-checkable.

## 1. The bundle — a run's whole world, content-addressed

A bundle is a directory:

    manifest.json      the canonical description (below)
    entry.py           the program
    inputs/...         every input file, read-only

    manifest = {"spec": "runtime-r2/1",
                "entry_sha256": <sha256 of entry.py bytes>,
                "inputs": {relpath: sha256, ...},
                "interpreter": "python3",     # DECLARED, not pinned (§4)
                "timeout_s": <uint>}

`bundle_id = sha256 of the canonical JSON of the manifest` — the same
canonical-bytes discipline as every chambers artifact. The runner
verifies every hash BEFORE executing: "the inputs were what the receipt
says" is checked, not assumed. Extra files, missing files, or any hash
mismatch refuse the run (fail closed; nothing executes).

## 2. Execution — the hermetic discipline

The entry runs as `python3 -I entry.py` with: an EMPTY environment (no
inherited variables), stdin closed, working directory = an ephemeral
copy of the bundle, and a hard timeout from the manifest. The program
reads `inputs/`, writes exactly one file `output`; the receipt's
`output_sha256` is the sha256 of those bytes. stdout/stderr are
discarded — they are not part of the claim.

`-I` (isolated mode) ignores all `PYTHON*` environment variables —
including `PYTHONHASHSEED` — so **hash randomization stays ON and
differs per process**. This is deliberate and load-bearing: a program
whose output depends on set/dict-hash iteration order is nondeterministic,
and the fresh seed per execution turns the double-run (§3) into a live
probe for exactly that class of bug. Clock, randomness, network,
environment: none are blocked by syscall (macOS-honest, §4); all are
CAUGHT by the discipline that follows.

## 3. Issuance — deterministic or no receipt

The runner executes the bundle **twice, in two fresh ephemeral copies,
two fresh processes**. A receipt is issued only if both runs exit 0
within the timeout and their output hashes are byte-identical. Anything
else — nonzero exit, timeout, output mismatch, missing output — refuses
issuance with a named reason. There is no "receipt with a warning";
value-grade claims fail closed, the house law.

    receipt = {"kind": "run_receipt", "spec": "runtime-r2/1",
               "claim_class": "reproducible_local",
               "bundle_id": ..., "output_sha256": ...,
               "runs": 2, "exit_code": 0,
               "interpreter_declared": "python3",
               "runner": <runner id string>}

All values integers or strings; `receipt_id = sha256 of canonical JSON`.
The double-run is the ISSUER's diligence, not the proof — the proof is
§5: anyone re-runs.

## 4. Honest limits, named

* **The interpreter is DECLARED, not pinned.** `python3` names a family,
  not bytes. A different CPython could in principle produce different
  output for the same bundle; the golden corpus (§6) constrains bundles
  to the stable core where this does not happen, and full pinning —
  content-addressed rootfs/toolchain (`rootfsHash`, `baseImageHash`) —
  is R2's OWED second artifact, a Nix/OCI build, named not faked.
* **No syscall sandbox.** Network, clock, and filesystem escape are not
  blocked (macOS-honest); they are deterrable only because using them
  nondeterministically fails issuance, and using them deterministically
  does not disturb the R2 claim (§0). Confidentiality is R3's rung.
* **Double-run is probabilistic evidence against nondeterminism**, not
  proof: a program keyed on something stable across the two runs but not
  across hosts (locale files, /usr/lib bytes) passes issuance and fails
  the stranger's re-run — which is the system working: the RE-RUN is the
  check, issuance is diligence.
* **Timeout is wall-clock**, hence host-dependent: a slow host can fail
  a bundle a fast host passes. Refusal is not conviction.

## 5. The stranger's check

`verify(bundle_dir, receipt)`: recompute the bundle id from bytes,
re-execute once, compare output hash. Exit 0 = REPRODUCED, 1 =
DIVERGED/refused, 2 = malformed. This is the whole point of the rung:
the receipt travels with the bundle, and trust in the operator is
replaced by fifteen seconds of compute.

## 6. The conformance lane

Golden bundles (frozen, content-addressed, in `bundles/`):

* `match_card` — the matchmaker's card projection: profile.json in,
  the 13-bit card projection out. The FIRST R2 workload is deliberately
  the party story's: the projection step that feeds the metered
  emission is exactly the deterministic shell around the LLM that §0
  says can ride this rung.
* `rank_items` — a deterministic ranking (the metered sort's comparator
  tier): items in, sorted order out.

The lane pins bundle ids and receipt ids (byte-stable forever), and
asserts the refusals: a flipped input bit fails hash verification
before execution; a clock-keyed entry and a hash-order-keyed entry
both fail issuance on output mismatch; a receipt against tampered
output DIVERGES under `verify`.

## 7. Receipts meet the court

A run receipt is an ordinary payload: POST it to a chamber-node and it
merges, content-addressed, into the same CRDT court as charges and
settlements (unknown kinds are inert to the frozen folds; X0 substrate
discipline covers future receipt-kind equivocation when receipts gain
actor/seq identity — /2 work, named). The consumer story: an outcome
escrow's attestor cites a run receipt id as evidence; a covenant's
destruction attestation carries one (RUNTIME.md §stateful, "the ledger
proves the model died" — at R2, "died" means the destruction run is
re-executable). Wiring those flows is not /1 scope.
