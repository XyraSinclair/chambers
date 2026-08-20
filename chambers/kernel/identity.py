"""charge-identity/1 — self-certifying key-authors (IDENTITY-SPEC.md).

The cheapest, deepest attributability gap:
issuers have been unauthenticated strings — forgery was detectable as
equivocation but never ATTRIBUTABLE to a party, which gates the meaning
of every economic surface (a bond that slashes a string slashes nobody).

The move is Ethereum's: identity IS the key. An author id MAY be
    ed25519:<64 hex chars of public key>
and every event authored by a key-shaped id MUST carry `sig` — an
Ed25519 signature (RFC 8032) over the canonical JSON of the payload
WITHOUT the sig field — or convict:

    A1 <author>   key-authored event missing/ill-formed sig
    A2 <author>   sig present but fails verification

Self-certifying means: no registry, no key_binding events, no first-seen
races, no rotation state in /1 — the id commits to the key by
construction, CRDT-native. Legacy string authors stay legal and
unconvicted (frozen corpora carry none of these ids and move by zero
bytes). Key rotation is /2 (a covenant linking old key to new), named
not faked.

The Ed25519 here is pure stdlib, implemented from RFC 8032 and pinned to
its §7.1 test vectors (test_identity.py). Verification is strict:
non-canonical s (>= L) and off-curve/invalid point encodings are
REJECTED — the malleability guard that keeps "same fact, two valid
encodings" impossible for honest signers. A MALICIOUS signer can still
emit two different valid signatures over the same content (nonce choice
is theirs), producing two event ids — economically inert, because fact
identity is (author, kind, seq) and the substrate X0 law convicts the
duplication. Slow-and-exact is the point (a few ms per verify); batch
performance is the Rust twin's job, owed and named.
"""
from __future__ import annotations

import dataclasses
import hashlib
import os
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from events import canonical_json  # noqa: E402

SPEC = "charge-identity/1"
KEY_PREFIX = "ed25519:"

# The declared author field per kind (IDENTITY-SPEC §2). Kinds not in
# this map are outside /1's mandate (their sigs, if any, are inert).
AUTHOR_FIELD = {
    "register": "issuer",
    "lease": "issuer",
    "charge": "node",
    "deposit": "issuer",
    "escrow": "issuer",
    "release": "issuer",
    "refund": "issuer",
    "outcome_attestation": "attestor",
    "default_resolution": "submitter",
    "bond_resolution": "submitter",
    "covenant": "issuer",
    "reviewer_seat": "reviewer",  # pipeline: a seated reviewer's citation
}

# ---- Ed25519 (RFC 8032), pure stdlib, exact ----

_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _sha512(b: bytes) -> bytes:
    return hashlib.sha512(b).digest()


def _inv(x: int) -> int:
    return pow(x, _P - 2, _P)


def _xrecover(y: int) -> Optional[int]:
    xx = (y * y - 1) * _inv(_D * y * y + 1) % _P
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = x * _I % _P
    if (x * x - xx) % _P != 0:
        return None
    return x


def _edwards_add(p: Tuple[int, int], q: Tuple[int, int]) -> Tuple[int, int]:
    x1, y1 = p
    x2, y2 = q
    k = _D * x1 * x2 * y1 * y2 % _P
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + k) % _P
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - k) % _P
    return x3, y3


def _scalarmult(p: Tuple[int, int], e: int) -> Tuple[int, int]:
    q = (0, 1)  # identity
    while e > 0:
        if e & 1:
            q = _edwards_add(q, p)
        p = _edwards_add(p, p)
        e >>= 1
    return q


_BY = 4 * _inv(5) % _P
_BX = _xrecover(_BY)
if _BX is None or _BX % 2 != 0:
    _BX = _P - _BX if _BX is not None else 0  # RFC: base x is even
_B = (_BX, _BY)


def _on_curve(pt: Tuple[int, int]) -> bool:
    x, y = pt
    return (-x * x + y * y - 1 - _D * x * x * y * y) % _P == 0


def _encode_point(pt: Tuple[int, int]) -> bytes:
    x, y = pt
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _decode_point(b: bytes) -> Optional[Tuple[int, int]]:
    if len(b) != 32:
        return None
    n = int.from_bytes(b, "little")
    sign = n >> 255
    y = n & ((1 << 255) - 1)
    if y >= _P:
        return None
    x = _xrecover(y)
    if x is None:
        return None
    if x & 1 != sign:
        x = _P - x
    if x == 0 and sign == 1:
        return None  # non-canonical encoding of the identity's x
    pt = (x, y)
    return pt if _on_curve(pt) else None


def _clamp(h32: bytes) -> int:
    a = int.from_bytes(h32, "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a


def keypair(seed: bytes) -> Tuple[bytes, bytes]:
    """(seed, public_key) from a 32-byte seed. Deterministic."""
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be exactly 32 bytes")
    a = _clamp(_sha512(seed)[:32])
    return seed, _encode_point(_scalarmult(_B, a))


def sign(seed: bytes, message: bytes) -> bytes:
    """RFC 8032 deterministic signature: 64 bytes R||s."""
    h = _sha512(seed)
    a = _clamp(h[:32])
    prefix = h[32:]
    pub = _encode_point(_scalarmult(_B, a))
    r = int.from_bytes(_sha512(prefix + message), "little") % _L
    R = _encode_point(_scalarmult(_B, r))
    k = int.from_bytes(_sha512(R + pub + message), "little") % _L
    s = (r + k * a) % _L
    return R + s.to_bytes(32, "little")


def verify_sig(pub: bytes, message: bytes, sig: bytes) -> bool:
    """Strict verification: canonical s (< L), valid point encodings.
    Total: any malformation returns False, never raises."""
    if len(pub) != 32 or len(sig) != 64:
        return False
    A = _decode_point(pub)
    R = _decode_point(sig[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _L:
        return False  # malleability guard: exactly one valid s encoding
    k = int.from_bytes(_sha512(sig[:32] + pub + message), "little") % _L
    left = _scalarmult(_B, s)
    right = _edwards_add(R, _scalarmult(A, k))
    return left == right


# ---- the protocol surface ----

def key_author(pub: bytes) -> str:
    """The self-certifying author id for a public key."""
    return KEY_PREFIX + pub.hex()


def author_of(payload: dict) -> Optional[str]:
    """The declared author of a payload, or None if the kind is outside
    /1's mandate or the field is not a string."""
    field = AUTHOR_FIELD.get(payload.get("kind"))
    if field is None:
        return None
    v = payload.get(field)
    return v if isinstance(v, str) else None


_HEX_LOWER = frozenset("0123456789abcdef")


def _lower_hex_bytes(s: str, nchars: int) -> Optional[bytes]:
    """The bytes of s iff s is EXACTLY nchars of lowercase hex, else
    None. Strictness is load-bearing: bytes.fromhex's case- and
    whitespace-tolerance would let one key answer to several author
    strings (and one signature to several event ids). Fact identity is
    (author, kind, seq), so an author's own case-aliases split
    seq-spaces past X0 — the aliasing seam this refuses to open."""
    if len(s) != nchars or not all(c in _HEX_LOWER for c in s):
        return None
    return bytes.fromhex(s)


def _key_of(author: str) -> Optional[bytes]:
    """The 32 public-key bytes of a key-shaped author, else None.
    Total over arbitrary strings."""
    if not author.startswith(KEY_PREFIX):
        return None
    key = _lower_hex_bytes(author[len(KEY_PREFIX):], 64)
    return b"" if key is None else key  # ill-formed: A1, never legacy


def signed_bytes(payload: dict) -> bytes:
    """What the signature covers: the canonical JSON of the payload
    WITHOUT its sig field."""
    body = {k: v for k, v in payload.items() if k != "sig"}
    return canonical_json(body).encode("ascii")


def sign_event(payload: dict, seed: bytes) -> dict:
    """Author-side helper: return the payload with `sig` attached. The
    caller is responsible for the author field carrying key_author(pub)
    — sign_event refuses a mismatch rather than sign in the dark."""
    _, pub = keypair(seed)
    author = author_of(payload)
    if author != key_author(pub):
        raise ValueError(
            f"payload author {author!r} is not this key's id {key_author(pub)!r}"
        )
    out = dict(payload)
    out.pop("sig", None)
    out["sig"] = sign(seed, signed_bytes(out)).hex()
    return out


def identity_findings(ledger) -> List[Tuple[str, str, str]]:
    """A-codes over the whole court. Total: adversarial bytes convict,
    never crash. Legacy (non-key) authors are untouched — /1 is opt-in
    by construction and the frozen corpora move by zero bytes."""
    findings: List[Tuple[str, str, str]] = []
    for payload in ledger.events():
        if not isinstance(payload, dict):
            continue
        author = author_of(payload)
        if author is None:
            continue
        key = _key_of(author)
        if key is None:
            continue  # legacy declared name: outside /1
        subj = author[:len(KEY_PREFIX) + 16] + "…"
        sig_hex = payload.get("sig")
        sig = (_lower_hex_bytes(sig_hex, 128)
               if isinstance(sig_hex, str) else None)
        if key == b"" or sig is None:
            findings.append(
                ("A1", author,
                 f"A1 key-authored event by {subj} missing or ill-formed sig")
            )
            continue
        if not verify_sig(key, signed_bytes(payload), sig):
            findings.append(
                ("A2", author,
                 f"A2 signature by {subj} fails verification")
            )
    return findings


def identity_codes(ledger) -> List[str]:
    """Conformance surface: sorted, deduplicated '<code> <subject>'."""
    return sorted({f"{c} {s}" for c, s, _ in identity_findings(ledger)})


# ---- /2: the authoring front-ends (IDENTITY-SPEC §7) ----
#
# Nothing new on the wire: /1 already defines what a signed event IS and
# what convicts. /2 is the authoring discipline — front-ends constructed
# with a Signer sign every fact they author, and constructing one that
# COULD emit an unattributable key-authored fact is refused outright.


class IdentityRefused(Exception):
    pass


class Signer:
    """A key-holder's authoring capability: the seed plus its derived
    self-certifying author id. Deterministic (RFC 8032): the same seed
    over the same bytes yields the same signature, so signed courts stay
    byte-deterministic."""

    __slots__ = ("_seed", "author")

    def __init__(self, seed: bytes) -> None:
        _, pub = keypair(seed)
        self._seed = seed
        self.author = key_author(pub)

    def sign(self, ev):
        """Dataclass form: return a copy of the event with `sig` attached.
        The event's content address then covers the signature (spec §3).
        Refuses an author mismatch rather than sign in the dark."""
        payload = ev.payload()
        author = author_of(payload)
        if author != self.author:
            raise IdentityRefused(
                f"event author {author!r} is not this key's id {self.author!r}"
            )
        sig_hex = sign(self._seed, signed_bytes(payload)).hex()
        return dataclasses.replace(ev, sig=sig_hex)


def require_signer(author, signer: Optional[Signer], role: str) -> Optional[Signer]:
    """The /2 authoring law, fail closed at construction time:

      * a key-shaped author with no Signer would emit A1-convicted facts
        — refuse to build the front-end at all;
      * a Signer whose key is not the author would emit A2 — refuse;
      * a Signer on a legacy author would emit inert bytes dressed as
        attribution — refuse (opt in with the key id as the author, or
        not at all).

    Returns the signer (possibly None) so call sites read as assignment."""
    key_shaped = isinstance(author, str) and author.startswith(KEY_PREFIX)
    if key_shaped and signer is None:
        raise IdentityRefused(
            f"{role} {author[:len(KEY_PREFIX) + 16]}… is key-shaped and MUST "
            "hold its Signer: a key-authored front-end never emits "
            "unattributable facts (IDENTITY-SPEC §7)"
        )
    if signer is not None and not key_shaped:
        raise IdentityRefused(
            f"{role} {author!r} is a legacy string; a Signer on it would emit "
            "inert sigs dressed as attribution — author as the key id or not at all"
        )
    if signer is not None and signer.author != author:
        raise IdentityRefused(
            f"{role} {author[:len(KEY_PREFIX) + 16]}… does not match the "
            f"Signer's key {signer.author[:len(KEY_PREFIX) + 16]}…"
        )
    return signer
