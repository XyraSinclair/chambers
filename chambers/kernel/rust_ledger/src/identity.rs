use std::cmp::Ordering;
use std::collections::BTreeSet;
use std::sync::OnceLock;

use crate::{as_string, canonical_json, kind, obj_get, sha512, Json, Ledger};

pub const KEY_PREFIX: &str = "ed25519:";

const FE_BASE: u128 = 1u128 << 51;
const FE_MASK_U64: u64 = (1u64 << 51) - 1;
const FE_MASK_U128: u128 = FE_BASE - 1;
const FE_P: [u64; 5] = [
    FE_MASK_U64 - 18,
    FE_MASK_U64,
    FE_MASK_U64,
    FE_MASK_U64,
    FE_MASK_U64,
];
const L_LE: [u8; 32] = [
    0xed, 0xd3, 0xf5, 0x5c, 0x1a, 0x63, 0x12, 0x58, 0xd6, 0x9c, 0xf7, 0xa2, 0xde, 0xf9, 0xde, 0x14,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10,
];
const P_MINUS_2_LE: [u8; 32] = [
    0xeb, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x7f,
];
const P_PLUS_3_OVER_8_LE: [u8; 32] = [
    0xfe, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x0f,
];
const P_MINUS_1_OVER_4_LE: [u8; 32] = [
    0xfb, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x1f,
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Fe([u64; 5]);

impl Fe {
    fn zero() -> Self {
        Self([0; 5])
    }

    fn one() -> Self {
        Self::from_u64(1)
    }

    fn from_u64(n: u64) -> Self {
        Self::from_wide([n as u128, 0, 0, 0, 0])
    }

    fn from_wide(mut h: [u128; 5]) -> Self {
        for _ in 0..3 {
            for i in 0..4 {
                let carry = h[i] >> 51;
                h[i] &= FE_MASK_U128;
                h[i + 1] = h[i + 1].wrapping_add(carry);
            }
            let carry = h[4] >> 51;
            h[4] &= FE_MASK_U128;
            h[0] = h[0].wrapping_add(carry * 19);
        }

        let mut out = Self([
            h[0] as u64,
            h[1] as u64,
            h[2] as u64,
            h[3] as u64,
            h[4] as u64,
        ]);
        while cmp_limbs(&out.0, &FE_P) != Ordering::Less {
            out = Self(raw_sub_ge(&out.0, &FE_P));
        }
        out
    }

    fn normalize(self) -> Self {
        Self::from_wide([
            self.0[0] as u128,
            self.0[1] as u128,
            self.0[2] as u128,
            self.0[3] as u128,
            self.0[4] as u128,
        ])
    }

    fn add(self, rhs: Self) -> Self {
        Self::from_wide([
            self.0[0] as u128 + rhs.0[0] as u128,
            self.0[1] as u128 + rhs.0[1] as u128,
            self.0[2] as u128 + rhs.0[2] as u128,
            self.0[3] as u128 + rhs.0[3] as u128,
            self.0[4] as u128 + rhs.0[4] as u128,
        ])
    }

    fn sub(self, rhs: Self) -> Self {
        let a = self.normalize();
        let b = rhs.normalize();
        if cmp_limbs(&a.0, &b.0) != Ordering::Less {
            Self(raw_sub_ge(&a.0, &b.0))
        } else {
            let diff = raw_sub_ge(&b.0, &a.0);
            if diff == [0; 5] {
                Self::zero()
            } else {
                Self(raw_sub_ge(&FE_P, &diff))
            }
        }
    }

    fn neg(self) -> Self {
        Self::zero().sub(self)
    }

    fn mul(self, rhs: Self) -> Self {
        let f0 = self.0[0] as u128;
        let f1 = self.0[1] as u128;
        let f2 = self.0[2] as u128;
        let f3 = self.0[3] as u128;
        let f4 = self.0[4] as u128;
        let g0 = rhs.0[0] as u128;
        let g1 = rhs.0[1] as u128;
        let g2 = rhs.0[2] as u128;
        let g3 = rhs.0[3] as u128;
        let g4 = rhs.0[4] as u128;
        let g1_19 = g1 * 19;
        let g2_19 = g2 * 19;
        let g3_19 = g3 * 19;
        let g4_19 = g4 * 19;

        Self::from_wide([
            f0 * g0 + f1 * g4_19 + f2 * g3_19 + f3 * g2_19 + f4 * g1_19,
            f0 * g1 + f1 * g0 + f2 * g4_19 + f3 * g3_19 + f4 * g2_19,
            f0 * g2 + f1 * g1 + f2 * g0 + f3 * g4_19 + f4 * g3_19,
            f0 * g3 + f1 * g2 + f2 * g1 + f3 * g0 + f4 * g4_19,
            f0 * g4 + f1 * g3 + f2 * g2 + f3 * g1 + f4 * g0,
        ])
    }

    fn square(self) -> Self {
        self.mul(self)
    }

    fn pow(self, exp_le: &[u8]) -> Self {
        let mut out = Self::one();
        let mut base = self;
        for byte in exp_le {
            for bit in 0..8 {
                if ((byte >> bit) & 1) == 1 {
                    out = out.mul(base);
                }
                base = base.square();
            }
        }
        out
    }

    fn inv(self) -> Self {
        self.pow(&P_MINUS_2_LE)
    }

    fn from_bytes_255(bytes: &[u8; 32]) -> Option<Self> {
        let mut limbs = [0u64; 5];
        for bit in 0..255 {
            if ((bytes[bit / 8] >> (bit % 8)) & 1) == 1 {
                limbs[bit / 51] |= 1u64 << (bit % 51);
            }
        }
        if cmp_limbs(&limbs, &FE_P) == Ordering::Less {
            Some(Self(limbs))
        } else {
            None
        }
    }

    fn to_bytes(self) -> [u8; 32] {
        let n = self.normalize();
        let mut out = [0u8; 32];
        for bit in 0..255 {
            if ((n.0[bit / 51] >> (bit % 51)) & 1) == 1 {
                out[bit / 8] |= 1 << (bit % 8);
            }
        }
        out
    }

    fn is_zero(self) -> bool {
        self.normalize().0 == [0; 5]
    }

    fn is_odd(self) -> bool {
        (self.to_bytes()[0] & 1) == 1
    }
}

fn cmp_limbs(a: &[u64; 5], b: &[u64; 5]) -> Ordering {
    for i in (0..5).rev() {
        match a[i].cmp(&b[i]) {
            Ordering::Equal => {}
            ord => return ord,
        }
    }
    Ordering::Equal
}

fn raw_sub_ge(a: &[u64; 5], b: &[u64; 5]) -> [u64; 5] {
    let mut out = [0u64; 5];
    let mut borrow = 0i128;
    for i in 0..5 {
        let mut v = a[i] as i128 - b[i] as i128 - borrow;
        if v < 0 {
            v += FE_BASE as i128;
            borrow = 1;
        } else {
            borrow = 0;
        }
        out[i] = v as u64;
    }
    debug_assert_eq!(borrow, 0);
    out
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Point {
    x: Fe,
    y: Fe,
}

impl Point {
    fn identity() -> Self {
        Self {
            x: Fe::zero(),
            y: Fe::one(),
        }
    }

    fn add(self, rhs: Self) -> Self {
        let d = edwards_d();
        let x1x2 = self.x.mul(rhs.x);
        let y1y2 = self.y.mul(rhs.y);
        let k = d.mul(x1x2).mul(y1y2);
        let x_num = self.x.mul(rhs.y).add(rhs.x.mul(self.y));
        let y_num = y1y2.add(x1x2);
        Self {
            x: x_num.mul(Fe::one().add(k).inv()),
            y: y_num.mul(Fe::one().sub(k).inv()),
        }
    }

    fn on_curve(self) -> bool {
        let x2 = self.x.square();
        let y2 = self.y.square();
        y2.sub(x2)
            .sub(Fe::one())
            .sub(edwards_d().mul(x2).mul(y2))
            .is_zero()
    }

    fn encode(self) -> [u8; 32] {
        let mut out = self.y.to_bytes();
        if self.x.is_odd() {
            out[31] |= 0x80;
        }
        out
    }
}

fn edwards_d() -> Fe {
    static D: OnceLock<Fe> = OnceLock::new();
    *D.get_or_init(|| Fe::from_u64(121665).neg().mul(Fe::from_u64(121666).inv()))
}

fn sqrt_m1() -> Fe {
    static I: OnceLock<Fe> = OnceLock::new();
    *I.get_or_init(|| Fe::from_u64(2).pow(&P_MINUS_1_OVER_4_LE))
}

fn base_point() -> Point {
    static B: OnceLock<Point> = OnceLock::new();
    *B.get_or_init(|| {
        let by = Fe::from_u64(4).mul(Fe::from_u64(5).inv());
        let mut bx = xrecover(by).expect("base point x exists");
        if bx.is_odd() {
            bx = bx.neg();
        }
        Point { x: bx, y: by }
    })
}

fn xrecover(y: Fe) -> Option<Fe> {
    let y2 = y.square();
    let xx = y2
        .sub(Fe::one())
        .mul(edwards_d().mul(y2).add(Fe::one()).inv());
    let mut x = xx.pow(&P_PLUS_3_OVER_8_LE);
    if !x.square().sub(xx).is_zero() {
        x = x.mul(sqrt_m1());
    }
    if !x.square().sub(xx).is_zero() {
        return None;
    }
    Some(x)
}

fn decode_point(bytes: &[u8]) -> Option<Point> {
    if bytes.len() != 32 {
        return None;
    }
    let mut y_bytes = [0u8; 32];
    y_bytes.copy_from_slice(bytes);
    let sign = y_bytes[31] >> 7;
    y_bytes[31] &= 0x7f;
    let y = Fe::from_bytes_255(&y_bytes)?;
    let mut x = xrecover(y)?;
    if u8::from(x.is_odd()) != sign {
        x = x.neg();
    }
    if x.is_zero() && sign == 1 {
        return None;
    }
    let pt = Point { x, y };
    if pt.on_curve() {
        Some(pt)
    } else {
        None
    }
}

fn scalar_mult(point: Point, scalar_le: &[u8; 32]) -> Point {
    let mut q = Point::identity();
    let mut p = point;
    for bit in 0..256 {
        if ((scalar_le[bit / 8] >> (bit % 8)) & 1) == 1 {
            q = q.add(p);
        }
        p = p.add(p);
    }
    q
}

fn clamp_scalar(bytes: &[u8]) -> [u8; 32] {
    let mut out = [0u8; 32];
    out.copy_from_slice(&bytes[..32]);
    out[0] &= 248;
    out[31] &= 63;
    out[31] |= 64;
    out
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct Big {
    limbs: Vec<u32>,
}

impl Big {
    fn zero() -> Self {
        Self { limbs: Vec::new() }
    }

    fn from_le_bytes(bytes: &[u8]) -> Self {
        let mut limbs = Vec::with_capacity((bytes.len() + 3) / 4);
        for chunk in bytes.chunks(4) {
            let mut buf = [0u8; 4];
            buf[..chunk.len()].copy_from_slice(chunk);
            limbs.push(u32::from_le_bytes(buf));
        }
        let mut out = Self { limbs };
        out.trim();
        out
    }

    fn trim(&mut self) {
        while self.limbs.last() == Some(&0) {
            self.limbs.pop();
        }
    }

    fn cmp(&self, rhs: &Self) -> Ordering {
        match self.limbs.len().cmp(&rhs.limbs.len()) {
            Ordering::Equal => {
                for i in (0..self.limbs.len()).rev() {
                    match self.limbs[i].cmp(&rhs.limbs[i]) {
                        Ordering::Equal => {}
                        ord => return ord,
                    }
                }
                Ordering::Equal
            }
            ord => ord,
        }
    }

    fn shl1(&mut self) {
        let mut carry = 0u64;
        for limb in &mut self.limbs {
            let v = ((*limb as u64) << 1) | carry;
            *limb = v as u32;
            carry = v >> 32;
        }
        if carry != 0 {
            self.limbs.push(carry as u32);
        }
    }

    fn add_small(&mut self, n: u32) {
        let mut carry = n as u64;
        let mut i = 0;
        while carry != 0 {
            if i == self.limbs.len() {
                self.limbs.push(0);
            }
            let v = self.limbs[i] as u64 + carry;
            self.limbs[i] = v as u32;
            carry = v >> 32;
            i += 1;
        }
    }

    fn add_assign(&mut self, rhs: &Self) {
        if self.limbs.len() < rhs.limbs.len() {
            self.limbs.resize(rhs.limbs.len(), 0);
        }
        let mut carry = 0u64;
        for i in 0..self.limbs.len() {
            let r = rhs.limbs.get(i).copied().unwrap_or(0) as u64;
            let v = self.limbs[i] as u64 + r + carry;
            self.limbs[i] = v as u32;
            carry = v >> 32;
        }
        if carry != 0 {
            self.limbs.push(carry as u32);
        }
    }

    fn sub_assign(&mut self, rhs: &Self) {
        debug_assert!(self.cmp(rhs) != Ordering::Less);
        let mut borrow = 0i64;
        for i in 0..self.limbs.len() {
            let r = rhs.limbs.get(i).copied().unwrap_or(0) as i64;
            let mut v = self.limbs[i] as i64 - r - borrow;
            if v < 0 {
                v += 1i64 << 32;
                borrow = 1;
            } else {
                borrow = 0;
            }
            self.limbs[i] = v as u32;
        }
        debug_assert_eq!(borrow, 0);
        self.trim();
    }

    fn reduce_once(&mut self, modulus: &Self) {
        if self.cmp(modulus) != Ordering::Less {
            self.sub_assign(modulus);
        }
    }

    fn to_le_32(&self) -> [u8; 32] {
        let mut out = [0u8; 32];
        for (i, limb) in self.limbs.iter().enumerate() {
            let start = i * 4;
            if start >= 32 {
                break;
            }
            out[start..start + 4].copy_from_slice(&limb.to_le_bytes());
        }
        out
    }
}

fn group_order() -> Big {
    Big::from_le_bytes(&L_LE)
}

fn reduce_mod_l(bytes_le: &[u8]) -> [u8; 32] {
    let modulus = group_order();
    let mut out = Big::zero();
    for bit in (0..bytes_le.len() * 8).rev() {
        out.shl1();
        if ((bytes_le[bit / 8] >> (bit % 8)) & 1) == 1 {
            out.add_small(1);
        }
        out.reduce_once(&modulus);
    }
    out.to_le_32()
}

fn scalar_less_than_l(bytes: &[u8; 32]) -> bool {
    Big::from_le_bytes(bytes).cmp(&group_order()) == Ordering::Less
}

fn scalar_add_mod(a: &[u8; 32], b: &[u8; 32]) -> [u8; 32] {
    let modulus = group_order();
    let mut out = Big::from_le_bytes(a);
    out.add_assign(&Big::from_le_bytes(b));
    while out.cmp(&modulus) != Ordering::Less {
        out.sub_assign(&modulus);
    }
    out.to_le_32()
}

fn scalar_mul_mod(a: &[u8; 32], b: &[u8; 32]) -> [u8; 32] {
    let modulus = group_order();
    let mut acc = Big::zero();
    let mut addend = Big::from_le_bytes(&reduce_mod_l(a));
    for bit in 0..256 {
        if ((b[bit / 8] >> (bit % 8)) & 1) == 1 {
            acc.add_assign(&addend);
            while acc.cmp(&modulus) != Ordering::Less {
                acc.sub_assign(&modulus);
            }
        }
        addend.shl1();
        while addend.cmp(&modulus) != Ordering::Less {
            addend.sub_assign(&modulus);
        }
    }
    acc.to_le_32()
}

pub fn keypair(seed: &[u8]) -> Result<([u8; 32], [u8; 32]), &'static str> {
    if seed.len() != 32 {
        return Err("Ed25519 seed must be exactly 32 bytes");
    }
    let h = sha512(seed);
    let a = clamp_scalar(&h[..32]);
    let pubkey = scalar_mult(base_point(), &a).encode();
    let mut seed_out = [0u8; 32];
    seed_out.copy_from_slice(seed);
    Ok((seed_out, pubkey))
}

pub fn sign(seed: &[u8], message: &[u8]) -> Option<[u8; 64]> {
    if seed.len() != 32 {
        return None;
    }
    let h = sha512(seed);
    let a = clamp_scalar(&h[..32]);
    let prefix = &h[32..];
    let pubkey = scalar_mult(base_point(), &a).encode();

    let mut r_input = Vec::with_capacity(prefix.len() + message.len());
    r_input.extend_from_slice(prefix);
    r_input.extend_from_slice(message);
    let r = reduce_mod_l(&sha512(&r_input));
    let r_point = scalar_mult(base_point(), &r).encode();

    let mut k_input = Vec::with_capacity(32 + 32 + message.len());
    k_input.extend_from_slice(&r_point);
    k_input.extend_from_slice(&pubkey);
    k_input.extend_from_slice(message);
    let k = reduce_mod_l(&sha512(&k_input));
    let s = scalar_add_mod(&r, &scalar_mul_mod(&k, &a));

    let mut out = [0u8; 64];
    out[..32].copy_from_slice(&r_point);
    out[32..].copy_from_slice(&s);
    Some(out)
}

pub fn verify_sig(pubkey: &[u8], message: &[u8], sig: &[u8]) -> bool {
    if pubkey.len() != 32 || sig.len() != 64 {
        return false;
    }
    let Some(a) = decode_point(pubkey) else {
        return false;
    };
    let Some(r) = decode_point(&sig[..32]) else {
        return false;
    };
    let mut s = [0u8; 32];
    s.copy_from_slice(&sig[32..]);
    if !scalar_less_than_l(&s) {
        return false;
    }

    let mut k_input = Vec::with_capacity(32 + 32 + message.len());
    k_input.extend_from_slice(&sig[..32]);
    k_input.extend_from_slice(pubkey);
    k_input.extend_from_slice(message);
    let k = reduce_mod_l(&sha512(&k_input));
    let left = scalar_mult(base_point(), &s);
    let right = r.add(scalar_mult(a, &k));
    left == right
}

pub fn key_author(pubkey: &[u8; 32]) -> String {
    format!("{KEY_PREFIX}{}", hex_lower(pubkey))
}

pub fn signed_bytes(payload: &Json) -> Vec<u8> {
    match payload {
        Json::Object(fields) => {
            let mut body = fields.clone();
            body.remove("sig");
            canonical_json(&Json::Object(body)).into_bytes()
        }
        _ => canonical_json(payload).into_bytes(),
    }
}

pub fn sign_event(payload: &Json, seed: &[u8]) -> Result<Json, String> {
    let (_, pubkey) = keypair(seed).map_err(str::to_string)?;
    let expected = key_author(&pubkey);
    let author = author_of(payload);
    if author != Some(expected.as_str()) {
        return Err(format!(
            "payload author {:?} is not this key's id {:?}",
            author, expected
        ));
    }
    let mut out = match payload {
        Json::Object(fields) => fields.clone(),
        _ => return Err("payload must be an object".to_string()),
    };
    out.remove("sig");
    let unsigned = Json::Object(out.clone());
    let sig = sign(seed, &signed_bytes(&unsigned)).ok_or_else(|| "sign failed".to_string())?;
    out.insert("sig".to_string(), Json::String(hex_lower(&sig)));
    Ok(Json::Object(out))
}

pub fn author_of(payload: &Json) -> Option<&str> {
    let field = author_field(kind(payload)?)?;
    as_string(obj_get(payload, field))
}

pub fn identity_codes(ledger: &Ledger) -> Vec<String> {
    let mut codes = BTreeSet::new();
    for event in ledger.event_values() {
        let Some(author) = author_of(&event.value) else {
            continue;
        };
        match key_of(author) {
            KeyClaim::Legacy => {}
            KeyClaim::IllFormed => {
                codes.insert(format!("A1 {author}"));
            }
            KeyClaim::Key(pubkey) => {
                let Some(sig_hex) = as_string(obj_get(&event.value, "sig")) else {
                    codes.insert(format!("A1 {author}"));
                    continue;
                };
                let Some(sig) = decode_hex_array::<64>(sig_hex) else {
                    codes.insert(format!("A1 {author}"));
                    continue;
                };
                if !verify_sig(&pubkey, &signed_bytes(&event.value), &sig) {
                    codes.insert(format!("A2 {author}"));
                }
            }
        }
    }
    codes.into_iter().collect()
}

fn author_field(kind: &str) -> Option<&'static str> {
    match kind {
        "register" | "lease" | "covenant" => Some("issuer"),
        "charge" => Some("node"),
        "deposit" | "escrow" | "release" | "refund" => Some("issuer"),
        "outcome_attestation" => Some("attestor"),
        "default_resolution" | "bond_resolution" => Some("submitter"),
        "reviewer_seat" => Some("reviewer"),
        _ => None,
    }
}

enum KeyClaim {
    Legacy,
    IllFormed,
    Key([u8; 32]),
}

fn key_of(author: &str) -> KeyClaim {
    let Some(hex) = author.strip_prefix(KEY_PREFIX) else {
        return KeyClaim::Legacy;
    };
    match decode_hex_array::<32>(hex) {
        Some(key) => KeyClaim::Key(key),
        None => KeyClaim::IllFormed,
    }
}

fn decode_hex_array<const N: usize>(s: &str) -> Option<[u8; N]> {
    if s.len() != N * 2 {
        return None;
    }
    let mut out = [0u8; N];
    let bytes = s.as_bytes();
    for i in 0..N {
        let hi = hex_value(bytes[i * 2])?;
        let lo = hex_value(bytes[i * 2 + 1])?;
        out[i] = (hi << 4) | lo;
    }
    Some(out)
}

/// Lowercase hex only. Strictness is load-bearing (IDENTITY-SPEC §1/§3):
/// tolerant decoding gives one key several author strings and one
/// signature several event ids; fact identity is (author, kind, seq),
/// so case-aliases would split seq-spaces past X0.
fn hex_value(b: u8) -> Option<u8> {
    match b {
        b'0'..=b'9' => Some(b - b'0'),
        b'a'..=b'f' => Some(b - b'a' + 10),
        _ => None,
    }
}

fn hex_lower(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        out.push(HEX[(b >> 4) as usize] as char);
        out.push(HEX[(b & 0x0f) as usize] as char);
    }
    out
}
